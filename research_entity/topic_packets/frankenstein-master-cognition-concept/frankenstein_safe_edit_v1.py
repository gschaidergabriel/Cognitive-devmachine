"""Fail-closed patch application for Frankenstein edits to existing files.

This module is intentionally provider-independent. It turns a model/tool-produced
unified diff into a bounded local file mutation only when all of these hold:

* the target is one regular UTF-8 file inside the repository;
* the caller binds the exact preimage SHA-256;
* the patch names exactly that file and uses strict unified-diff context;
* every removal/context line matches the current preimage exactly;
* the automated deletion budget is not exceeded;
* the preimage hash is rechecked immediately before atomic replacement.

It exists because a live Frankenstein direct-dispatch attempt on 2026-08-28
replaced a 672-line existing file with an 87-line fabricated stub. A mere
"new file is not less than 50% of old file size" guard is not sufficient for
arbitrary edits. Exact preimage identity plus strict patch context and an
explicit deletion budget make the mutation boundary materially narrower.

This is a source primitive, not runtime/product acceptance and not a provider
authority surface.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

SCHEMA = "FRANKENSTEIN_SAFE_EDIT/v1"
_HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@(?: .*)?$"
)


class SafeEditError(RuntimeError):
    """Base class for fail-closed edit rejection."""


class PathViolation(SafeEditError):
    pass


class SourceChanged(SafeEditError):
    pass


class PatchSyntaxError(SafeEditError):
    pass


class PolicyViolation(SafeEditError):
    pass


@dataclass(frozen=True)
class EditPolicy:
    """Safety policy for unattended edits of an existing file.

    max_deleted_fraction is measured against old logical lines. It is not a
    file-size heuristic: replacements count as deletion+addition, so a rewrite
    that keeps similar byte size can still be rejected. Large refactors should
    be split into smaller patches or escalated outside this unattended path.
    """

    max_deleted_fraction: float = 0.25
    require_preserved_old_line: bool = True

    def validate(self) -> None:
        if not 0.0 <= self.max_deleted_fraction <= 1.0:
            raise PolicyViolation("max_deleted_fraction must be within [0, 1]")


@dataclass(frozen=True)
class EditPlan:
    schema: str
    relative_path: str
    before_sha256: str
    after_sha256: str
    patch_sha256: str
    before_bytes: int
    after_bytes: int
    old_line_count: int
    new_line_count: int
    deleted_old_lines: int
    added_new_lines: int
    context_old_lines: int
    untouched_old_lines: int
    preserved_old_lines: int
    deleted_fraction: float
    after_text: str

    def receipt(self, *, committed: bool) -> dict:
        data = asdict(self)
        data.pop("after_text")
        data["committed"] = committed
        return data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_existing_target(repo_root: Path, relative_path: str) -> Path:
    root = repo_root.resolve()
    rel = Path(relative_path)
    if rel.is_absolute():
        raise PathViolation(f"absolute target path forbidden: {relative_path}")
    target = root / rel
    if target.is_symlink():
        raise PathViolation(f"symlink target forbidden: {relative_path}")
    resolved = target.resolve()
    if resolved == root or root not in resolved.parents:
        raise PathViolation(f"target escapes repository: {relative_path}")
    if not resolved.is_file():
        raise PathViolation(f"existing regular file required: {relative_path}")
    return resolved


def snapshot_sha256(repo_root: Path, relative_path: str) -> str:
    target = _resolve_existing_target(repo_root, relative_path)
    return sha256_bytes(target.read_bytes())


def _patch_path(raw: str) -> str:
    token = raw.strip().split("\t", 1)[0]
    if token == "/dev/null":
        raise PolicyViolation("file creation/deletion is outside existing-file safe-edit v1")
    if token.startswith("a/") or token.startswith("b/"):
        token = token[2:]
    if not token or Path(token).is_absolute() or ".." in Path(token).parts:
        raise PathViolation(f"unsafe patch path: {raw}")
    return Path(token).as_posix()


def _extract_headers_and_hunks(patch_text: str) -> tuple[str, list[tuple[int, int, int, int, list[str]]]]:
    lines = patch_text.splitlines()
    old_header: str | None = None
    new_header: str | None = None
    hunks: list[tuple[int, int, int, int, list[str]]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git ") or line.startswith("index "):
            i += 1
            continue
        if line.startswith("--- "):
            if old_header is not None:
                raise PatchSyntaxError("multiple file patches are forbidden")
            old_header = _patch_path(line[4:])
            i += 1
            if i >= len(lines) or not lines[i].startswith("+++ "):
                raise PatchSyntaxError("missing +++ header after --- header")
            new_header = _patch_path(lines[i][4:])
            i += 1
            if old_header != new_header:
                raise PolicyViolation("renames are forbidden in existing-file safe-edit v1")
            continue
        match = _HUNK_RE.match(line)
        if match:
            old_start = int(match.group("old_start"))
            old_count = int(match.group("old_count") or "1")
            new_start = int(match.group("new_start"))
            new_count = int(match.group("new_count") or "1")
            body: list[str] = []
            i += 1
            while i < len(lines):
                candidate = lines[i]
                if _HUNK_RE.match(candidate) or candidate.startswith("--- "):
                    break
                if candidate == r"\ No newline at end of file":
                    raise PatchSyntaxError("no-newline marker is unsupported in safe-edit v1")
                if not candidate.startswith((" ", "+", "-")):
                    raise PatchSyntaxError(f"invalid unified-diff body line: {candidate!r}")
                body.append(candidate)
                i += 1

            observed_old = sum(1 for item in body if item[:1] in {" ", "-"})
            observed_new = sum(1 for item in body if item[:1] in {" ", "+"})
            if observed_old != old_count or observed_new != new_count:
                raise PatchSyntaxError(
                    f"hunk count mismatch: declared old/new={old_count}/{new_count}, "
                    f"observed={observed_old}/{observed_new}"
                )
            hunks.append((old_start, old_count, new_start, new_count, body))
            continue
        if line.strip() == "":
            i += 1
            continue
        raise PatchSyntaxError(f"unexpected patch line before/after hunks: {line!r}")

    if old_header is None or new_header is None:
        raise PatchSyntaxError("unified diff requires --- and +++ headers")
    if not hunks:
        raise PatchSyntaxError("patch contains no hunks")
    return old_header, hunks


def plan_unified_patch(
    repo_root: Path,
    relative_path: str,
    expected_sha256: str,
    patch_text: str,
    *,
    policy: EditPolicy = EditPolicy(),
) -> EditPlan:
    """Validate and materialize a strict in-memory patch plan without writing."""
    policy.validate()
    target = _resolve_existing_target(repo_root, relative_path)
    before = target.read_bytes()
    before_sha = sha256_bytes(before)
    if before_sha != expected_sha256:
        raise SourceChanged(
            f"preimage SHA-256 mismatch for {relative_path}: expected {expected_sha256}, got {before_sha}"
        )
    try:
        before_text = before.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyViolation("safe-edit v1 supports UTF-8 text files only") from exc
    if "\r\n" in before_text:
        raise PolicyViolation("safe-edit v1 requires LF line endings to preserve byte identity")

    patch_path, hunks = _extract_headers_and_hunks(patch_text)
    normalized_target = Path(relative_path).as_posix()
    if patch_path != normalized_target:
        raise PolicyViolation(
            f"patch target mismatch: declared {patch_path!r}, requested {normalized_target!r}"
        )

    had_final_newline = before_text.endswith("\n")
    source_lines = before_text.splitlines()
    output: list[str] = []
    source_index = 0
    deleted = 0
    added = 0
    context = 0
    untouched = 0

    for old_start, _old_count, _new_start, _new_count, body in hunks:
        hunk_index = old_start - 1
        if hunk_index < source_index:
            raise PatchSyntaxError("overlapping or out-of-order hunks")
        if hunk_index > len(source_lines):
            raise PatchSyntaxError("hunk starts beyond end of source file")

        prefix = source_lines[source_index:hunk_index]
        output.extend(prefix)
        untouched += len(prefix)
        source_index = hunk_index

        for item in body:
            marker, payload = item[0], item[1:]
            if marker in {" ", "-"}:
                if source_index >= len(source_lines):
                    raise PatchSyntaxError("patch consumes beyond end of source file")
                actual = source_lines[source_index]
                if actual != payload:
                    raise PatchSyntaxError(
                        f"strict context mismatch at old line {source_index + 1}: "
                        f"expected {payload!r}, found {actual!r}"
                    )
                source_index += 1
                if marker == " ":
                    output.append(actual)
                    context += 1
                else:
                    deleted += 1
            elif marker == "+":
                output.append(payload)
                added += 1
            else:  # pragma: no cover - parser rejects this first
                raise PatchSyntaxError(f"unknown patch marker {marker!r}")

    suffix = source_lines[source_index:]
    output.extend(suffix)
    untouched += len(suffix)

    old_count = len(source_lines)
    new_count = len(output)
    preserved = old_count - deleted
    deleted_fraction = (deleted / old_count) if old_count else (1.0 if deleted else 0.0)
    if deleted_fraction > policy.max_deleted_fraction:
        raise PolicyViolation(
            f"automated deletion budget exceeded: deleted {deleted}/{old_count} old lines "
            f"({deleted_fraction:.3f}) > {policy.max_deleted_fraction:.3f}"
        )
    if policy.require_preserved_old_line and old_count > 0 and preserved <= 0:
        raise PolicyViolation("whole-file replacement is forbidden: no old line is preserved")

    after_text = "\n".join(output)
    if had_final_newline:
        after_text += "\n"
    after = after_text.encode("utf-8")
    if after == before:
        raise PolicyViolation("patch is a no-op")

    return EditPlan(
        schema=SCHEMA,
        relative_path=normalized_target,
        before_sha256=before_sha,
        after_sha256=sha256_bytes(after),
        patch_sha256=sha256_bytes(patch_text.encode("utf-8")),
        before_bytes=len(before),
        after_bytes=len(after),
        old_line_count=old_count,
        new_line_count=new_count,
        deleted_old_lines=deleted,
        added_new_lines=added,
        context_old_lines=context,
        untouched_old_lines=untouched,
        preserved_old_lines=preserved,
        deleted_fraction=deleted_fraction,
        after_text=after_text,
    )


def commit_plan(repo_root: Path, plan: EditPlan) -> dict:
    """Recheck the exact preimage and atomically install a previously validated plan."""
    if plan.schema != SCHEMA:
        raise PolicyViolation(f"unsupported edit plan schema: {plan.schema}")
    target = _resolve_existing_target(repo_root, plan.relative_path)
    current = target.read_bytes()
    current_sha = sha256_bytes(current)
    if current_sha != plan.before_sha256:
        raise SourceChanged(
            f"target changed after planning: expected {plan.before_sha256}, got {current_sha}"
        )

    payload = plan.after_text.encode("utf-8")
    if sha256_bytes(payload) != plan.after_sha256:
        raise PolicyViolation("plan payload does not match declared after_sha256")

    mode = stat.S_IMODE(target.stat().st_mode)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.safe-edit-", dir=target.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, mode)

        # Recheck after the replacement payload is fully durable but before the
        # atomic rename. Higher-level repository orchestration should still use
        # a single-writer/branch discipline; ordinary filesystems do not provide
        # a content-hash compare-and-swap primitive across arbitrary writers.
        latest_sha = sha256_bytes(target.read_bytes())
        if latest_sha != plan.before_sha256:
            raise SourceChanged(
                f"target changed during commit: expected {plan.before_sha256}, got {latest_sha}"
            )
        os.replace(temp_path, target)
        installed_sha = sha256_bytes(target.read_bytes())
        if installed_sha != plan.after_sha256:
            raise SafeEditError(
                f"post-replace SHA-256 mismatch: expected {plan.after_sha256}, got {installed_sha}"
            )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return plan.receipt(committed=True)
