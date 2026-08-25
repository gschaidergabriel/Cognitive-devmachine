#!/usr/bin/env python3
"""Supervisor-side admission gate for CLAY_FORGE_RUNTIME_IDENTITY/v1.

The verifier is deterministic, local and credential-blind. It grants only a
bounded current-process/source admission signal; it cannot mint canonical truth,
Forge evidence credit, HCU/J-Space/model/training credit, or any real effect.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

VERIFIED = "VERIFIED_EXACT_FORGE_RUNTIME_IDENTITY"
PENDING = "PENDING_FRESH_FORGE_RUNTIME_IDENTITY"
REJECTED = "RUNTIME_IDENTITY_UNVERIFIED"


def _git(root: Path, *args: str) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=4,
        ).strip()
    except Exception:
        return None
    return value or None


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _parse_ts(value: Any) -> float | None:
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.timestamp()
    except Exception:
        return None


def _result(state: str, reason: str, **extra: object) -> dict[str, object]:
    return {
        "schema": "CLAY_FORGE_RUNTIME_IDENTITY_ADMISSION/v1",
        "state": state,
        "reason": reason,
        **extra,
        "credit_boundary": "SUPERVISOR_PROCESS_SOURCE_ADMISSION_ONLY",
    }


def verify_runtime_identity(
    *,
    status_path: Path,
    expectation_path: Path,
    expected_entrypoint: Path,
    repo_root: Path,
    actual_pid: int,
    now: float | None = None,
    max_age_seconds: float = 90.0,
    grace_seconds: float = 60.0,
) -> dict[str, object]:
    now = time.time() if now is None else float(now)
    root = repo_root.resolve()
    entrypoint = expected_entrypoint.resolve()

    try:
        expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _result(REJECTED, f"EXPECTATION_UNREADABLE:{type(exc).__name__}")
    if expectation.get("schema") != "CLAY_FORGE_RUNTIME_EXPECTATION/v1":
        return _result(REJECTED, "EXPECTATION_SCHEMA_MISMATCH")

    try:
        expected_pid = int(expectation.get("pid"))
        spawned_at = float(expectation.get("spawned_at_unix"))
    except (TypeError, ValueError):
        return _result(REJECTED, "EXPECTATION_IDENTITY_INVALID")
    nonce = str(expectation.get("nonce") or "")
    if not nonce:
        return _result(REJECTED, "EXPECTATION_NONCE_MISSING")
    if expected_pid != int(actual_pid):
        return _result(REJECTED, "PROCESS_PID_MISMATCH", expected_pid=expected_pid, actual_pid=int(actual_pid))

    within_grace = now - spawned_at <= grace_seconds
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception as exc:
        if within_grace:
            return _result(PENDING, f"STATUS_NOT_FRESH_YET:{type(exc).__name__}")
        return _result(REJECTED, f"STATUS_UNREADABLE:{type(exc).__name__}")

    status_ts = _parse_ts(status.get("generated_at"))
    if status_ts is None:
        return _result(REJECTED, "STATUS_TIMESTAMP_INVALID")
    if status_ts + 1e-6 < spawned_at:
        if within_grace:
            return _result(PENDING, "STATUS_PREDATES_CURRENT_SPAWN", status_generated_at=status.get("generated_at"))
        return _result(REJECTED, "STATUS_STALE_PRESPAWN", status_generated_at=status.get("generated_at"))
    if now - status_ts > max_age_seconds:
        return _result(REJECTED, "STATUS_TOO_OLD", status_age_seconds=now - status_ts)

    identity = status.get("runtime_identity")
    if not isinstance(identity, dict):
        return _result(REJECTED, "RUNTIME_IDENTITY_MISSING")
    if identity.get("schema") != "CLAY_FORGE_RUNTIME_IDENTITY/v1":
        return _result(REJECTED, "RUNTIME_IDENTITY_SCHEMA_MISMATCH")
    if identity.get("source_identity_admitted") is not True:
        return _result(REJECTED, "PUBLISHER_SOURCE_IDENTITY_NOT_ADMITTED")
    if identity.get("material_sources_match") is not True:
        return _result(REJECTED, "PUBLISHER_MATERIAL_SOURCE_BINDING_NOT_ADMITTED")

    expected_commit = _git(root, "rev-parse", "HEAD")
    expected_tree = _git(root, "rev-parse", "HEAD^{tree}")
    expected_sha256 = _sha256(entrypoint)
    if not expected_commit or not expected_tree or not expected_sha256:
        return _result(REJECTED, "EXPECTED_SOURCE_IDENTITY_UNRESOLVED")

    try:
        published_entrypoint = Path(str(identity.get("runtime_entrypoint_path") or "")).resolve()
    except Exception:
        return _result(REJECTED, "PUBLISHED_ENTRYPOINT_INVALID")
    if published_entrypoint != entrypoint:
        return _result(REJECTED, "ENTRYPOINT_PATH_MISMATCH")
    if identity.get("runtime_entrypoint_sha256") != expected_sha256:
        return _result(REJECTED, "ENTRYPOINT_SHA256_MISMATCH")
    if identity.get("source_commit") != expected_commit:
        return _result(REJECTED, "SOURCE_COMMIT_MISMATCH")
    if identity.get("source_tree") != expected_tree:
        return _result(REJECTED, "SOURCE_TREE_MISMATCH")
    if identity.get("supervisor_generation_or_start_nonce") != nonce:
        return _result(REJECTED, "SUPERVISOR_NONCE_MISMATCH")

    process_generation = str(identity.get("process_generation_identity") or "")
    expected_prefix = f"pid:{actual_pid}:"
    if not process_generation.startswith(expected_prefix):
        return _result(REJECTED, "PROCESS_GENERATION_PID_MISMATCH")

    return _result(
        VERIFIED,
        "EXACT_SOURCE_MATERIAL_PID_NONCE_AND_FRESH_STATUS_MATCH",
        source_commit=expected_commit,
        source_tree=expected_tree,
        runtime_entrypoint_sha256=expected_sha256,
        pid=int(actual_pid),
        process_generation_identity=process_generation,
        supervisor_generation_or_start_nonce=nonce,
        status_generated_at=status.get("generated_at"),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify the single backlog-first Forge runtime identity")
    ap.add_argument("--status", required=True)
    ap.add_argument("--expectation", required=True)
    ap.add_argument("--expected-entrypoint", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--actual-pid", required=True, type=int)
    ap.add_argument("--max-age-seconds", type=float, default=90.0)
    ap.add_argument("--grace-seconds", type=float, default=60.0)
    args = ap.parse_args()
    report = verify_runtime_identity(
        status_path=Path(args.status),
        expectation_path=Path(args.expectation),
        expected_entrypoint=Path(args.expected_entrypoint),
        repo_root=Path(args.repo_root),
        actual_pid=args.actual_pid,
        max_age_seconds=args.max_age_seconds,
        grace_seconds=args.grace_seconds,
    )
    print(json.dumps(report, sort_keys=True))
    if report["state"] == VERIFIED:
        return 0
    if report["state"] == PENDING:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
