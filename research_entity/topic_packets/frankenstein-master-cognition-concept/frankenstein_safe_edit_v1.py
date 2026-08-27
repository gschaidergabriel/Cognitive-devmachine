"""Deterministic existing-file preservation primitive for Project Frankenstein.

This module is intentionally provider-free.  It does not dispatch models, inspect
secrets, use the network, run Aider, or mint runtime/product credit.

It exists because the first live Frankenstein direct-dispatch on 2026-08-28
produced a destructive whole-file rewrite (reported 672 lines -> 87 lines).  The
first mitigation injected current file contents and rejected very large shrinkage,
but independent review found two additional fail-closed requirements:

* every proposed path must be resolved inside the repository BEFORE any proposed
  path is read or written;
* the exact file preimage shown to/planned against by an editor must still be the
  preimage at write time (TOCTOU/source-drift rejection);
* a multi-file application must restore earlier files when a later write fails;
* for parseable Python files, dropping pre-existing top-level functions/classes is
  rejected by default even when the proposed file remains larger than a simple
  shrink threshold.

The primitive is source-ready only until it is explicitly integrated and executed
at an admitted exact-source scope.  Successful use of this module still does not
prove semantic correctness of an edit.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Callable, Mapping


class SafeEditError(RuntimeError):
    """Base class for deterministic safe-edit rejection."""


class UnsafePath(SafeEditError):
    """A proposed path is outside the repository or otherwise unsafe."""


class StalePreimage(SafeEditError):
    """The file changed after its exact preimage was captured."""


class PreservationViolation(SafeEditError):
    """The proposal violates a declared preservation invariant."""


class PartialWriteError(SafeEditError):
    """A write failed after application began; rollback was attempted."""


@dataclass(frozen=True)
class Preimage:
    rel_path: str
    existed: bool
    sha256: str | None
    content: bytes | None


@dataclass(frozen=True)
class Postimage:
    rel_path: str
    sha256: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_repo_file(repo_root: Path, rel_path: str) -> Path:
    root = repo_root.resolve()
    if not isinstance(rel_path, str) or not rel_path.strip():
        raise UnsafePath("empty or non-string relative path")
    rel = Path(rel_path)
    if rel.is_absolute():
        raise UnsafePath(f"absolute path rejected: {rel_path}")
    full = (root / rel).resolve()
    if full == root:
        raise UnsafePath(f"repository root is not a file target: {rel_path}")
    try:
        full.relative_to(root)
    except ValueError as exc:
        raise UnsafePath(f"path escapes repository: {rel_path}") from exc
    if full.exists() and not full.is_file():
        raise UnsafePath(f"existing target is not a regular file: {rel_path}")
    return full


def validate_block_paths(repo_root: Path, blocks: Mapping[str, str]) -> dict[str, Path]:
    """Validate *all* target paths before any target content is read or written."""
    root = repo_root.resolve()
    if not root.is_dir():
        raise UnsafePath(f"repository root is not a directory: {root}")
    resolved: dict[str, Path] = {}
    normalized_seen: dict[Path, str] = {}
    for rel_path, proposed in blocks.items():
        if not isinstance(proposed, str):
            raise SafeEditError(f"proposed content must be text: {rel_path}")
        full = _resolve_repo_file(root, rel_path)
        previous = normalized_seen.get(full)
        if previous is not None:
            raise UnsafePath(
                f"two proposal paths resolve to the same target: {previous!r}, {rel_path!r}"
            )
        normalized_seen[full] = rel_path
        resolved[rel_path] = full
    if not resolved:
        raise SafeEditError("empty edit proposal")
    return resolved


def snapshot_preimages(repo_root: Path, blocks: Mapping[str, str]) -> dict[str, Preimage]:
    """Capture exact bytes only after every proposed path passed root confinement."""
    paths = validate_block_paths(repo_root, blocks)
    snapshots: dict[str, Preimage] = {}
    for rel_path, full in paths.items():
        if full.exists():
            data = full.read_bytes()
            snapshots[rel_path] = Preimage(rel_path, True, sha256_bytes(data), data)
        else:
            snapshots[rel_path] = Preimage(rel_path, False, None, None)
    return snapshots


def assert_preimages_unchanged(
    repo_root: Path,
    preimages: Mapping[str, Preimage],
) -> None:
    """Reject source drift between planning/snapshot and write time."""
    paths = validate_block_paths(repo_root, {rel: "" for rel in preimages})
    for rel_path, snapshot in preimages.items():
        full = paths[rel_path]
        if snapshot.existed:
            if not full.is_file():
                raise StalePreimage(f"pre-existing file disappeared: {rel_path}")
            current = full.read_bytes()
            current_sha = sha256_bytes(current)
            if current_sha != snapshot.sha256:
                raise StalePreimage(
                    f"preimage changed for {rel_path}: expected {snapshot.sha256}, got {current_sha}"
                )
        elif full.exists():
            raise StalePreimage(f"new-file target appeared after snapshot: {rel_path}")


def _top_level_python_symbols(source: str) -> set[str] | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _looks_like_destructive_truncation(
    old_content: bytes,
    new_content: bytes,
    *,
    min_old_len: int = 200,
    max_shrink_ratio: float = 0.5,
) -> bool:
    if len(old_content) < min_old_len:
        return False
    return len(new_content) < len(old_content) * max_shrink_ratio


def validate_preservation(
    repo_root: Path,
    blocks: Mapping[str, str],
    preimages: Mapping[str, Preimage],
    *,
    allowed_removed_symbols: Mapping[str, set[str]] | None = None,
) -> None:
    """Validate exact preimages plus conservative content-preservation invariants.

    The Python-symbol invariant is deliberately conservative: if the old Python
    file parses, the proposed file must also parse and must retain every old
    top-level function/class unless the caller explicitly names that symbol in
    ``allowed_removed_symbols`` for that exact path.
    """
    paths = validate_block_paths(repo_root, blocks)
    if set(paths) != set(preimages):
        raise SafeEditError("proposal path set does not match captured preimage set")
    assert_preimages_unchanged(repo_root, preimages)
    allowed_removed_symbols = allowed_removed_symbols or {}

    for rel_path, proposed_text in blocks.items():
        snapshot = preimages[rel_path]
        if not snapshot.existed:
            continue
        assert snapshot.content is not None
        proposed_bytes = proposed_text.encode("utf-8")
        if _looks_like_destructive_truncation(snapshot.content, proposed_bytes):
            raise PreservationViolation(f"destructive truncation rejected: {rel_path}")

        if paths[rel_path].suffix == ".py":
            try:
                old_text = snapshot.content.decode("utf-8")
            except UnicodeDecodeError:
                old_text = ""
            old_symbols = _top_level_python_symbols(old_text) if old_text else None
            if old_symbols is not None:
                new_symbols = _top_level_python_symbols(proposed_text)
                if new_symbols is None:
                    raise PreservationViolation(
                        f"parseable Python preimage became syntactically invalid: {rel_path}"
                    )
                allowed = set(allowed_removed_symbols.get(rel_path, set()))
                missing = sorted(old_symbols - new_symbols - allowed)
                if missing:
                    raise PreservationViolation(
                        f"top-level Python symbols disappeared from {rel_path}: {missing}"
                    )


class SafeEditTransaction:
    """Rollback-on-failure multi-file edit bound to exact captured preimages.

    This is not a claim of crash-atomic multi-file filesystem transactions.  It
    provides deterministic pre-write validation and best-effort rollback for
    Python-level write/verification failure.  A future Git-patch integration may
    provide a stronger mutation surface.
    """

    def __init__(
        self,
        repo_root: Path,
        blocks: Mapping[str, str],
        *,
        allowed_removed_symbols: Mapping[str, set[str]] | None = None,
        writer: Callable[[Path, bytes], None] | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.blocks = dict(blocks)
        self.paths = validate_block_paths(self.repo_root, self.blocks)
        self.preimages = snapshot_preimages(self.repo_root, self.blocks)
        self.allowed_removed_symbols = allowed_removed_symbols or {}
        self._writer = writer or (lambda path, data: path.write_bytes(data))
        self._applied = False
        self._committed = False
        self._postimages: dict[str, Postimage] = {}

    def apply(self) -> dict[str, Postimage]:
        if self._applied:
            raise SafeEditError("transaction already applied")
        validate_preservation(
            self.repo_root,
            self.blocks,
            self.preimages,
            allowed_removed_symbols=self.allowed_removed_symbols,
        )

        attempted: list[str] = []
        try:
            for rel_path, proposed in self.blocks.items():
                full = self.paths[rel_path]
                full.parent.mkdir(parents=True, exist_ok=True)
                attempted.append(rel_path)
                self._writer(full, proposed.encode("utf-8"))
            self._postimages = {
                rel: Postimage(rel, sha256_bytes(self.paths[rel].read_bytes()))
                for rel in self.blocks
            }
            self._applied = True
            return dict(self._postimages)
        except Exception as exc:
            self._restore(attempted)
            raise PartialWriteError(f"edit application failed and was rolled back: {exc}") from exc

    def _restore(self, rel_paths: list[str] | None = None) -> None:
        rel_paths = list(rel_paths if rel_paths is not None else self.preimages.keys())
        restore_errors: list[str] = []
        for rel_path in reversed(rel_paths):
            snapshot = self.preimages[rel_path]
            full = self.paths[rel_path]
            try:
                if snapshot.existed:
                    assert snapshot.content is not None
                    full.parent.mkdir(parents=True, exist_ok=True)
                    full.write_bytes(snapshot.content)
                elif full.exists():
                    if full.is_file():
                        full.unlink()
                    else:
                        restore_errors.append(f"non-file appeared at new target: {rel_path}")
            except OSError as exc:
                restore_errors.append(f"{rel_path}: {exc}")
        self._applied = False
        self._postimages = {}
        if restore_errors:
            raise PartialWriteError("rollback incomplete: " + "; ".join(restore_errors))

    def rollback(self) -> None:
        if self._committed:
            raise SafeEditError("committed transaction cannot be rolled back by this object")
        self._restore()

    def commit(self) -> dict[str, Postimage]:
        if not self._applied:
            raise SafeEditError("cannot commit before apply")
        for rel_path, expected in self._postimages.items():
            full = self.paths[rel_path]
            if not full.is_file():
                self._restore()
                raise StalePreimage(f"postimage disappeared before commit: {rel_path}")
            observed = sha256_bytes(full.read_bytes())
            if observed != expected.sha256:
                self._restore()
                raise StalePreimage(
                    f"postimage changed before commit for {rel_path}: expected {expected.sha256}, got {observed}"
                )
        self._committed = True
        return dict(self._postimages)

    def __enter__(self) -> "SafeEditTransaction":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if not self._committed:
            self._restore()
        return False
