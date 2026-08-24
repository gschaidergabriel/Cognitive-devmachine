#!/usr/bin/env python3
"""Deterministic two-stage patch synthesis support for the Free Swarm.

This module deliberately contains no provider/network code.  It turns a model's
stage-1 target selection into exact source capsules, validates the stage-2 diff
against the same source commit, and can repair only one narrow syntax defect:
incorrect unified-diff hunk counts.  Repair is accepted only when ``git apply
--recount`` succeeds against the exact source and the re-rendered diff then passes
ordinary ``git apply --check`` in a fresh clone.

It does not use fuzzy/3-way application and never promotes model text to authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_TARGET_FILES = 3
MAX_PATCH_BYTES = 250_000
DEFAULT_PER_FILE_CHARS = 18_000
DEFAULT_TOTAL_CHARS = 36_000


def balanced_json_span_after(text: str, marker: str) -> tuple[int, int, dict[str, Any]] | None:
    """Return the exact JSON object span following *marker* without regex parsing."""
    pos = text.find(marker)
    if pos < 0:
        return None
    start = text.find("{", pos + len(marker))
    if start < 0:
        return None
    depth = 0
    in_str = False
    escaped = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start : index + 1])
                except Exception:
                    return None
                if not isinstance(obj, dict):
                    return None
                return start, index + 1, obj
    return None


def architecture_delta(text: str) -> dict[str, Any] | None:
    found = balanced_json_span_after(text, "ARCHITECTURE_DELTA_JSON=")
    return found[2] if found else None


def canonicalize_architecture_delta(text: str, obj: dict[str, Any]) -> str:
    """Replace only the machine-readable delta object, preserving human text."""
    found = balanced_json_span_after(text, "ARCHITECTURE_DELTA_JSON=")
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if found is None:
        suffix = "" if text.endswith("\n") or not text else "\n"
        return text + suffix + "ARCHITECTURE_DELTA_JSON=" + raw + "\n"
    start, end, _ = found
    return text[:start] + raw + text[end:]


def safe_target(raw: str) -> str | None:
    value = str(raw or "").strip()
    if not value or len(value) > 300 or "\x00" in value or "\\" in value:
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or ".git" in path.parts:
        return None
    normalized = path.as_posix()
    if normalized.startswith("./") or normalized in {"", "."}:
        return None
    return normalized


def target_files(obj: dict[str, Any], limit: int = MAX_TARGET_FILES) -> list[str]:
    out: list[str] = []
    values = obj.get("target_files")
    if not isinstance(values, list):
        return out
    for raw in values:
        if not isinstance(raw, str):
            continue
        normalized = safe_target(raw)
        if normalized and normalized not in out:
            out.append(normalized)
        if len(out) >= limit:
            break
    return out


def proposal_complete(obj: dict[str, Any]) -> bool:
    tests = obj.get("test_commands")
    return bool(
        target_files(obj)
        and isinstance(tests, list)
        and any(isinstance(x, str) and x.strip() for x in tests)
        and isinstance(obj.get("falsifier"), str)
        and obj["falsifier"].strip()
    )


def _git(
    cwd: Path,
    *args: str,
    input_text: str | None = None,
    timeout: int = 45,
) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        return 125, "", f"{type(exc).__name__}:{exc}"


def _source_exists(repo: Path, source_head: str) -> tuple[bool, str]:
    if not COMMIT_RE.fullmatch(source_head):
        return False, "SOURCE_HEAD_INVALID"
    rc, _, err = _git(repo, "cat-file", "-e", source_head + "^{commit}")
    return (rc == 0, "" if rc == 0 else "SOURCE_COMMIT_UNAVAILABLE:" + err[-500:])


def _bounded_excerpt(text: str, per_file_chars: int) -> tuple[str, bool]:
    if len(text) <= per_file_chars:
        return text, False
    marker = "\n...[EXACT_SOURCE_TRUNCATED_MIDDLE]...\n"
    half = max(1, (per_file_chars - len(marker)) // 2)
    return text[:half] + marker + text[-half:], True


def rehydrate_targets(
    repo: Path,
    source_head: str,
    targets: list[str],
    *,
    per_file_chars: int = DEFAULT_PER_FILE_CHARS,
    total_chars: int = DEFAULT_TOTAL_CHARS,
) -> dict[str, Any]:
    """Bind declared target paths to exact Git objects and bounded source text."""
    ok, reason = _source_exists(repo, source_head)
    if not ok:
        return {"ok": False, "reason": reason, "source_head": source_head, "files": []}

    normalized: list[str] = []
    for raw in targets[:MAX_TARGET_FILES]:
        value = safe_target(raw)
        if value is None:
            return {
                "ok": False,
                "reason": "UNSAFE_TARGET_PATH",
                "source_head": source_head,
                "files": [],
            }
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        return {
            "ok": False,
            "reason": "NO_SAFE_TARGET_FILES",
            "source_head": source_head,
            "files": [],
        }

    remaining = max(0, int(total_chars))
    records: list[dict[str, Any]] = []
    for rel in normalized:
        rc, blob, _ = _git(repo, "rev-parse", f"{source_head}:{rel}")
        if rc != 0:
            records.append(
                {
                    "path": rel,
                    "state": "ABSENT_AT_SOURCE",
                    "git_blob": None,
                    "sha256": None,
                    "chars_total": 0,
                    "chars_supplied": 0,
                    "truncated": False,
                    "content": "",
                }
            )
            continue

        rc, raw, err = _git(repo, "show", f"{source_head}:{rel}")
        if rc != 0:
            return {
                "ok": False,
                "reason": "SOURCE_READ_FAILED:" + err[-500:],
                "source_head": source_head,
                "files": records,
            }
        if "\x00" in raw:
            return {
                "ok": False,
                "reason": "BINARY_TARGET_NOT_SUPPORTED",
                "source_head": source_head,
                "files": records,
            }

        cap = min(max(1, int(per_file_chars)), remaining) if remaining else 0
        if cap <= 0:
            excerpt = ""
            truncated = True
        else:
            excerpt, truncated = _bounded_excerpt(raw, cap)
        remaining = max(0, remaining - len(excerpt))
        records.append(
            {
                "path": rel,
                "state": "BOUND_TEXT_SOURCE",
                "git_blob": blob.strip(),
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "chars_total": len(raw),
                "chars_supplied": len(excerpt),
                "truncated": truncated,
                "content": excerpt,
            }
        )

    return {
        "ok": True,
        "reason": None,
        "source_head": source_head,
        "files": records,
        "context_complete": all(not row["truncated"] for row in records),
    }


def source_capsule_text(binding: dict[str, Any]) -> str:
    chunks = [
        "EXACT_TARGET_SOURCE_REHYDRATION/v1",
        f"source_head={binding.get('source_head')}",
        "authority=CANDIDATE_INPUT_ONLY",
    ]
    for row in binding.get("files") or []:
        chunks.extend(
            [
                f"\nTARGET path={row.get('path')}",
                f"state={row.get('state')}",
                f"git_blob={row.get('git_blob')}",
                f"sha256={row.get('sha256')}",
                f"chars_total={row.get('chars_total')}",
                f"chars_supplied={row.get('chars_supplied')}",
                f"truncated={str(bool(row.get('truncated'))).lower()}",
                "--- BEGIN EXACT TARGET CONTENT ---",
                str(row.get("content") or ""),
                "--- END EXACT TARGET CONTENT ---",
            ]
        )
    return "\n".join(chunks)


def stage2_prompt(
    protocol: str,
    proposal: dict[str, Any],
    binding: dict[str, Any],
) -> str:
    stable = dict(proposal)
    stable["patch_unified_diff"] = ""
    stable["ready_for_forge"] = False
    proposal_json = json.dumps(
        stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return f"""{protocol}

ENTITYOS/HCU TWO-STAGE PATCH SYNTHESIS — STAGE 2
The stage-1 proposal below is noncanonical candidate input. Produce only the
source-bound implementation delta. Do not change target_files, test_commands,
hypothesis or falsifier. The exact source head is fixed for this synthesis.

Fail-closed rules:
- Modify only the declared target_files.
- Use only exact visible source bytes below for removals/context; never invent old lines.
- A creation target marked ABSENT_AT_SOURCE must use /dev/null on the old side.
- Emit a normal unified diff with exact ---/+++ paths and valid @@ hunk counts.
- No Markdown fence, ellipsis, prose placeholder, rename/copy metadata or binary patch.
- If the supplied exact context is insufficient, keep patch_unified_diff empty and ready_for_forge=false.
- ready_for_forge is only a request for deterministic local preflight; the controller will force it false unless ordinary git apply --check succeeds on the exact source.
- End with DEUTSCHE_ZUSAMMENFASSUNG and one compact ARCHITECTURE_DELTA_JSON line.

STAGE1_PROPOSAL_JSON={proposal_json}

{source_capsule_text(binding)}
"""


def _patch_declared_paths(patch: str) -> tuple[bool, set[str], str]:
    if not patch or len(patch.encode("utf-8", errors="replace")) > MAX_PATCH_BYTES:
        return False, set(), "PATCH_EMPTY_OR_TOO_LARGE"
    paths: set[str] = set()
    forbidden_meta = ("rename from ", "rename to ", "copy from ", "copy to ", "GIT binary patch")
    for line in patch.splitlines():
        if line.startswith(forbidden_meta):
            return False, set(), "PATCH_RENAME_COPY_BINARY_NOT_ALLOWED"
        if line.startswith(("--- ", "+++ ")):
            value = line[4:].split("\t", 1)[0].strip()
            if value == "/dev/null":
                continue
            value = re.sub(r"^[ab]/", "", value)
            normalized = safe_target(value)
            if normalized is None:
                return False, set(), "PATCH_UNSAFE_HEADER_PATH"
            paths.add(normalized)
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) != 4:
                return False, set(), "PATCH_BAD_DIFF_HEADER"
            for value in parts[2:4]:
                value = re.sub(r"^[ab]/", "", value)
                normalized = safe_target(value)
                if normalized is None:
                    return False, set(), "PATCH_UNSAFE_DIFF_PATH"
                paths.add(normalized)
    return (bool(paths), paths, "" if paths else "PATCH_HAS_NO_PATHS")


def _clone_exact(repo: Path, source_head: str, dest: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", "--local", str(repo), str(dest)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=90,
    )
    if proc.returncode != 0:
        return False, "LOCAL_CLONE_FAILED:" + proc.stderr[-500:]
    rc, _, err = _git(dest, "checkout", "--quiet", "--detach", source_head)
    if rc != 0:
        return False, "SOURCE_CHECKOUT_FAILED:" + err[-500:]
    rc, got, err = _git(dest, "rev-parse", "HEAD")
    if rc != 0 or got.strip() != source_head:
        return False, "SOURCE_CHECKOUT_IDENTITY_MISMATCH:" + (got or err)[-500:]
    return True, ""


def _standard_apply_check(repo: Path, source_head: str, patch: str, temp_root: Path) -> tuple[bool, str]:
    dest = temp_root / "check"
    ok, reason = _clone_exact(repo, source_head, dest)
    if not ok:
        return False, reason
    rc, _, err = _git(
        dest,
        "apply",
        "--check",
        "--whitespace=nowarn",
        "-",
        input_text=patch,
    )
    return rc == 0, err[-1200:]


def normalize_patch_against_source(
    repo: Path,
    source_head: str,
    patch: str,
    targets: list[str],
) -> dict[str, Any]:
    """Preflight a patch and narrowly repair bad hunk counts without fuzzy apply."""
    ok, reason = _source_exists(repo, source_head)
    if not ok:
        return {"ok": False, "reason": reason, "repair_mode": "NONE", "patch": patch}

    declared_ok, paths, path_reason = _patch_declared_paths(patch)
    expected = set(targets)
    if not declared_ok:
        return {
            "ok": False,
            "reason": path_reason,
            "repair_mode": "NONE",
            "patch": patch,
        }
    if paths != expected:
        return {
            "ok": False,
            "reason": "PATCH_TARGET_SET_MISMATCH",
            "declared_paths": sorted(paths),
            "expected_paths": sorted(expected),
            "repair_mode": "NONE",
            "patch": patch,
        }

    root = Path(tempfile.mkdtemp(prefix="clay-patch-preflight-"))
    try:
        clean, err = _standard_apply_check(repo, source_head, patch, root)
        if clean:
            return {
                "ok": True,
                "reason": None,
                "repair_mode": "NONE",
                "patch": patch,
                "original_apply_error": None,
            }

        recount_repo = root / "recount"
        cloned, clone_reason = _clone_exact(repo, source_head, recount_repo)
        if not cloned:
            return {
                "ok": False,
                "reason": clone_reason,
                "repair_mode": "NONE",
                "patch": patch,
                "original_apply_error": err,
            }
        rc, _, recount_err = _git(
            recount_repo,
            "apply",
            "--recount",
            "--whitespace=nowarn",
            "-",
            input_text=patch,
        )
        if rc != 0:
            return {
                "ok": False,
                "reason": "PATCH_APPLY_REJECTED",
                "repair_mode": "NONE",
                "patch": patch,
                "original_apply_error": err,
                "recount_apply_error": recount_err[-1200:],
            }

        for rel in targets:
            rc, _, _ = _git(recount_repo, "cat-file", "-e", f"{source_head}:{rel}")
            if rc != 0 and (recount_repo / rel).exists():
                _git(recount_repo, "add", "-N", "--", rel)

        rc, normalized, diff_err = _git(
            recount_repo, "diff", "--no-ext-diff", "--binary", "--", *targets
        )
        if rc != 0 or not normalized.strip():
            return {
                "ok": False,
                "reason": "RECOUNT_NORMALIZATION_EMPTY_OR_FAILED:" + diff_err[-500:],
                "repair_mode": "NONE",
                "patch": patch,
                "original_apply_error": err,
            }

        verify_root = root / "verify"
        verify_root.mkdir()
        clean2, err2 = _standard_apply_check(repo, source_head, normalized, verify_root)
        if not clean2:
            return {
                "ok": False,
                "reason": "RECOUNT_NORMALIZED_PATCH_FAILED_STANDARD_CHECK",
                "repair_mode": "NONE",
                "patch": patch,
                "original_apply_error": err,
                "normalized_apply_error": err2,
            }
        return {
            "ok": True,
            "reason": None,
            "repair_mode": "RECOUNT_NORMALIZED",
            "patch": normalized,
            "original_apply_error": err,
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)
