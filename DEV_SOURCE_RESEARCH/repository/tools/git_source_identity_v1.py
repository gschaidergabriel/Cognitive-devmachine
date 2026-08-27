#!/usr/bin/env python3
"""Exact Git source/dirty-state identity for EntityOS/HCU runtime receipts.

Porcelain status alone identifies only path/status shape. It does not bind the bytes of
tracked modifications or untracked source files. This helper binds HEAD/tree plus the
actual tracked diff bytes and content hashes for every non-ignored untracked file without
persisting file contents or provider secrets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

SCHEMA = "CLAY_GIT_SOURCE_IDENTITY/v1"
DIRTY_SCHEMA = "CLAY_GIT_DIRTY_STATE/v1"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_bytes_exact(root: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_SOURCE_IDENTITY_COMMAND_FAILED:{args[0]}:{proc.returncode}")
    return proc.stdout


def git_text_exact(root: Path, *args: str) -> str:
    raw = git_bytes_exact(root, *args).strip()
    if not raw:
        raise RuntimeError(f"GIT_SOURCE_IDENTITY_EMPTY_RESULT:{args[0]}")
    return raw.decode("utf-8", "strict")


def untracked_entry(root: Path, raw_path: bytes) -> dict[str, Any]:
    # Store only a digest of the path, never the path text itself. This still binds
    # identity/order while avoiding accidental disclosure of sensitive filenames.
    path = root / os.fsdecode(raw_path)
    path_sha = hashlib.sha256(raw_path).hexdigest()
    if path.is_symlink():
        payload = os.fsencode(os.readlink(path))
        return {
            "path_sha256": path_sha,
            "kind": "symlink",
            "size": len(payload),
            "content_sha256": hashlib.sha256(payload).hexdigest(),
        }
    if path.is_file():
        return {
            "path_sha256": path_sha,
            "kind": "file",
            "size": path.stat().st_size,
            "content_sha256": sha256_file(path),
        }
    raise RuntimeError(f"UNTRACKED_SOURCE_ENTRY_UNSUPPORTED:{path_sha}")


def dirty_state_manifest(root: Path) -> dict[str, Any]:
    # `git diff HEAD` binds both staged and unstaged tracked changes. Binary mode
    # ensures binary modifications affect the digest too. Ignored files are excluded
    # from the source identity by the same Git exclusion rules used by ls-files.
    tracked_diff = git_bytes_exact(root, "diff", "--binary", "--no-ext-diff", "HEAD", "--")
    untracked_raw = git_bytes_exact(root, "ls-files", "--others", "--exclude-standard", "-z")
    raw_paths = sorted(path for path in untracked_raw.split(b"\0") if path)
    entries = [untracked_entry(root, raw_path) for raw_path in raw_paths]
    return {
        "schema": DIRTY_SCHEMA,
        "tracked_diff_sha256": hashlib.sha256(tracked_diff).hexdigest(),
        "tracked_diff_bytes": len(tracked_diff),
        "untracked_entries": entries,
        "untracked_count": len(entries),
        "dirty": bool(tracked_diff or entries),
    }


def source_identity(root: Path) -> dict[str, Any]:
    root = root.resolve()
    dirty = dirty_state_manifest(root)
    payload = {
        "schema": SCHEMA,
        "repo_head": git_text_exact(root, "rev-parse", "HEAD"),
        "repo_tree": git_text_exact(root, "rev-parse", "HEAD^{tree}"),
        "dirty_state": dirty,
        "dirty_state_sha256": canonical_sha(dirty),
    }
    payload["source_identity_sha256"] = canonical_sha(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    payload = source_identity(Path(args.repo))
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    if args.require_clean and payload["dirty_state"]["dirty"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
