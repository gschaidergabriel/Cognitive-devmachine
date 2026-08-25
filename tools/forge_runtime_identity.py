#!/usr/bin/env python3
"""Exact runtime/source identity envelope for the single Evidence Forge authority.

This module does not create a second Forge or any canonical semantic authority.  It
binds a status writer to the executable bytes, current Git checkout identity and Linux
process generations so a stale pre-fusion process cannot be accepted merely because it
continues to publish ``state=LIVE``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_IDENTITY_SCHEMA = "CLAY_FORGE_RUNTIME_IDENTITY/v1"
STATUS_WRITER_SCHEMA = "CLAY_FORGE_LIVE_STATUS/v2"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _git_text(root: Path, *args: str) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "-C", str(root), *args],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return value or None


def _relative_path(path: Path, root: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def process_generation_identity(pid: int) -> str | None:
    """Return PID + Linux start ticks, which distinguishes PID reuse."""
    if pid <= 0:
        return None
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    # ``comm`` may contain spaces and parentheses.  Everything after its final
    # right parenthesis begins at proc-stat field 3; starttime is field 22.
    right = raw.rfind(")")
    if right < 0:
        return None
    fields = raw[right + 2 :].split()
    if len(fields) <= 19:
        return None
    start_ticks = fields[19]
    if not start_ticks.isdigit():
        return None
    return f"linux-proc:{pid}:{start_ticks}"


def process_generation_is_live(identity: str | None) -> bool:
    if not isinstance(identity, str):
        return False
    parts = identity.split(":")
    if len(parts) != 3 or parts[0] != "linux-proc" or not parts[1].isdigit():
        return False
    return process_generation_identity(int(parts[1])) == identity


def runtime_identity(entrypoint: Path, *, root: Path = ROOT) -> dict[str, Any]:
    entrypoint = entrypoint.resolve()
    root = root.resolve()
    rel = _relative_path(entrypoint, root)
    actual_sha: str | None
    try:
        actual_sha = sha256_file(entrypoint)
    except OSError:
        actual_sha = None

    commit = _git_text(root, "rev-parse", "HEAD")
    tree = _git_text(root, "rev-parse", "HEAD^{tree}")
    committed_blob = _git_text(root, "rev-parse", f"HEAD:{rel}") if rel else None
    worktree_blob = _git_text(root, "hash-object", str(entrypoint)) if rel else None
    entrypoint_matches_commit = bool(
        rel and committed_blob and worktree_blob and committed_blob == worktree_blob
    )
    dirty = _git_text(root, "status", "--porcelain", "--untracked-files=no")
    dirty_state = "UNKNOWN" if dirty is None else ("DIRTY" if dirty else "CLEAN")

    pid = os.getpid()
    supervisor_pid = os.getppid()
    process_identity = process_generation_identity(pid)
    supervisor_identity = process_generation_identity(supervisor_pid)
    verified = bool(
        rel
        and actual_sha
        and commit
        and tree
        and committed_blob
        and entrypoint_matches_commit
        and process_identity
        and supervisor_identity
    )
    return {
        "schema": RUNTIME_IDENTITY_SCHEMA,
        "runtime_entrypoint_path": rel,
        "runtime_entrypoint_sha256": actual_sha,
        "runtime_entrypoint_git_blob": committed_blob,
        "runtime_entrypoint_matches_source_commit": entrypoint_matches_commit,
        "source_commit": commit,
        "source_tree": tree,
        "source_dirty_state": dirty_state,
        "process_pid": pid,
        "process_start_identity": process_identity,
        "supervisor_pid": supervisor_pid,
        "supervisor_generation_or_start_nonce": supervisor_identity,
        "status_writer_schema_version": STATUS_WRITER_SCHEMA,
        "runtime_identity_state": "VERIFIED" if verified else "RUNTIME_IDENTITY_UNVERIFIED",
    }


def validate_status_identity(
    status: dict[str, Any], entrypoint: Path, *, root: Path = ROOT, require_live_process: bool = True
) -> tuple[bool, list[str]]:
    """Validate a Forge status against current expected source and process identity."""
    reasons: list[str] = []
    observed = status.get("runtime_identity")
    if not isinstance(observed, dict):
        return False, ["RUNTIME_IDENTITY_MISSING"]

    expected = runtime_identity(entrypoint, root=root)
    for key in (
        "schema",
        "runtime_entrypoint_path",
        "runtime_entrypoint_sha256",
        "runtime_entrypoint_git_blob",
        "source_commit",
        "source_tree",
        "status_writer_schema_version",
    ):
        if observed.get(key) != expected.get(key):
            reasons.append(f"RUNTIME_IDENTITY_MISMATCH:{key}")

    if observed.get("runtime_entrypoint_matches_source_commit") is not True:
        reasons.append("RUNTIME_ENTRYPOINT_NOT_COMMITTED_SOURCE")
    if observed.get("runtime_identity_state") != "VERIFIED":
        reasons.append("RUNTIME_IDENTITY_NOT_VERIFIED")

    process_identity = observed.get("process_start_identity")
    supervisor_identity = observed.get("supervisor_generation_or_start_nonce")
    if not isinstance(process_identity, str):
        reasons.append("PROCESS_GENERATION_MISSING")
    elif require_live_process and not process_generation_is_live(process_identity):
        reasons.append("PROCESS_GENERATION_NOT_LIVE")
    if not isinstance(supervisor_identity, str):
        reasons.append("SUPERVISOR_GENERATION_MISSING")
    elif require_live_process and not process_generation_is_live(supervisor_identity):
        reasons.append("SUPERVISOR_GENERATION_NOT_LIVE")

    return not reasons, reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Forge LIVE runtime identity")
    ap.add_argument("--entrypoint", type=Path, required=True)
    ap.add_argument("--status", type=Path)
    ap.add_argument("--allow-dead-process", action="store_true")
    args = ap.parse_args()
    if args.status is None:
        print(json.dumps(runtime_identity(args.entrypoint), sort_keys=True))
        return 0
    try:
        status = json.loads(args.status.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "reasons": [f"STATUS_READ_FAILED:{type(exc).__name__}"]}, sort_keys=True))
        return 2
    if not isinstance(status, dict):
        print(json.dumps({"ok": False, "reasons": ["STATUS_OBJECT_REQUIRED"]}, sort_keys=True))
        return 2
    ok, reasons = validate_status_identity(
        status,
        args.entrypoint,
        require_live_process=not args.allow_dead_process,
    )
    print(json.dumps({"ok": ok, "reasons": reasons}, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
