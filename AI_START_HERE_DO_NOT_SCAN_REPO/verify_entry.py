#!/usr/bin/env python3
"""Minimal Frankenstein AI entry verifier.

No repository scan. No cwd assumption. No network. No provider call.
The script resolves its entry directory from __file__, checks only declared
contract paths, optionally probes a local durable filesystem write, reads the
known authority inbox path, and emits a bounded installation classification.

NATIVE is deliberately hard to obtain: lifecycle hook firing, cross-session
state and effect/result receipt observation must be supplied as observed facts.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ENTRY_DIR = Path(__file__).resolve().parent
REPO_ROOT = ENTRY_DIR.parent
CONTRACT_PATH = ENTRY_DIR / "INSTALL_CONTRACT.json"
HUMAN_PATH = REPO_ROOT / "HUMAN_READ_THIS" / "README.md"
DEV_PATH = REPO_ROOT / "DEV_SOURCE_RESEARCH" / "README.md"
AUTHORITY_POINTER = REPO_ROOT / "CLAY_EXECUTION_AUTHORITY.md"
SUPERVISOR_INBOX = REPO_ROOT / "research_entity" / "claycode" / "autonomous" / "SUPERVISOR_INBOX.json"

HOST_DEFAULTS = {
    "claude-code": "ADAPTED",
    "codex-cli": "ADAPTED",
    "hermes-agent": "DEGRADED",
    "chatgpt-web": "DEGRADED",
    "claude-web": "DEGRADED",
    "grok-web": "DEGRADED",
    "generic": "BLOCKED",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _known_file_checks() -> dict[str, bool]:
    # Exact declared paths only. Deliberately no walk(), rglob(), glob("**/*") or root scan.
    return {
        "contract": CONTRACT_PATH.is_file(),
        "human_readme": HUMAN_PATH.is_file(),
        "dev_readme": DEV_PATH.is_file(),
        "authority_pointer": AUTHORITY_POINTER.is_file(),
        "supervisor_inbox": SUPERVISOR_INBOX.is_file(),
    }


def _probe_durable_write() -> tuple[bool, str | None]:
    """Bounded local write+fsync+readback+cleanup probe in the entry directory."""
    try:
        fd, raw_path = tempfile.mkstemp(prefix=".frankenstein-entry-probe-", dir=ENTRY_DIR)
        path = Path(raw_path)
        payload = b"FRANKENSTEIN_ENTRY_WRITE_PROBE/v1\n"
        try:
            with os.fdopen(fd, "wb", closefd=True) as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            if path.read_bytes() != payload:
                return False, "readback_mismatch"
            return True, None
        finally:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _git_identity() -> dict[str, Any]:
    try:
        top = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        head = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if top.returncode != 0 or head.returncode != 0:
            return {"observed": False, "error": (top.stderr or head.stderr).strip()[:500]}
        observed_root = Path(top.stdout.strip()).resolve()
        return {
            "observed": True,
            "root_matches_entry_parent": observed_root == REPO_ROOT,
            "root": str(observed_root),
            "head": head.stdout.strip(),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"observed": False, "error": f"{type(exc).__name__}: {exc}"}


def _authority_snapshot() -> dict[str, Any]:
    if not SUPERVISOR_INBOX.is_file():
        return {"observed": False, "reason": "SUPERVISOR_INBOX_MISSING"}
    try:
        data = _read_json(SUPERVISOR_INBOX)
    except (OSError, json.JSONDecodeError) as exc:
        return {"observed": False, "reason": f"SUPERVISOR_INBOX_UNREADABLE:{type(exc).__name__}"}

    free_only = data.get("free_only")
    frontier = data.get("current_frontier")
    return {
        "observed": True,
        "schema_version": data.get("schema_version"),
        "supervisor_delta": data.get("supervisor_delta"),
        "selected_steering": data.get("steering"),
        "free_only": free_only,
        "frontier_present": isinstance(frontier, (dict, str, list)),
        "note": "This is an observed inbox snapshot, not an authority synthesized by this script.",
    }


def _classify(
    host: str,
    checks: dict[str, bool],
    git_identity: dict[str, Any],
    durable_write_observed: bool,
    lifecycle_hook_observed: bool,
    cross_session_state_observed: bool,
    effect_receipt_observed: bool,
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    core_ok = checks["contract"] and checks["human_readme"] and checks["dev_readme"]
    if not core_ok:
        return "BLOCKED", ["required declared entry files missing"]

    default = HOST_DEFAULTS[host]

    # NATIVE is evidence-bearing, not a host-name shortcut.
    if lifecycle_hook_observed and durable_write_observed and cross_session_state_observed and effect_receipt_observed:
        reasons.append("native-evidence quartet explicitly observed")
        return "NATIVE", reasons

    if host in {"claude-code", "codex-cli"}:
        if git_identity.get("observed") and git_identity.get("root_matches_entry_parent"):
            reasons.append("declared entry files + repository identity observed")
            if not lifecycle_hook_observed:
                reasons.append("native lifecycle hook firing not observed")
            return "ADAPTED", reasons
        reasons.append("CLI route present but Git repository identity not fully observed")
        return "DEGRADED", reasons

    if host == "generic" and default == "BLOCKED":
        reasons.append("generic host needs explicit capability evidence")
        return "DEGRADED" if git_identity.get("observed") else "BLOCKED", reasons

    reasons.append(f"{host} default remains {default} until stronger host capabilities are observed")
    return default, reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=sorted(HOST_DEFAULTS), default="generic")
    parser.add_argument("--probe-durable-write", action="store_true")
    parser.add_argument("--lifecycle-hook-observed", action="store_true")
    parser.add_argument("--cross-session-state-observed", action="store_true")
    parser.add_argument("--effect-receipt-observed", action="store_true")
    args = parser.parse_args()

    checks = _known_file_checks()
    contract_valid = False
    contract_schema = None
    if checks["contract"]:
        try:
            contract = _read_json(CONTRACT_PATH)
            contract_schema = contract.get("schema")
            contract_valid = contract_schema == "FRANKENSTEIN_AI_ENTRY_INSTALL_CONTRACT/v1"
        except (OSError, json.JSONDecodeError):
            contract_valid = False
    checks["contract_schema_valid"] = contract_valid

    git_identity = _git_identity()
    durable_write_observed = False
    durable_write_error = None
    if args.probe_durable_write:
        durable_write_observed, durable_write_error = _probe_durable_write()

    classification, reasons = _classify(
        args.host,
        checks,
        git_identity,
        durable_write_observed,
        args.lifecycle_hook_observed,
        args.cross_session_state_observed,
        args.effect_receipt_observed,
    )
    if not contract_valid:
        classification = "BLOCKED"
        reasons.insert(0, "install contract schema missing or invalid")

    result = {
        "schema": "FRANKENSTEIN_AI_ENTRY_VERIFY_RESULT/v1",
        "classification": classification,
        "host": args.host,
        "entry_directory": str(ENTRY_DIR),
        "repository_root": str(REPO_ROOT),
        "cwd": str(Path.cwd()),
        "cwd_used_for_resolution": False,
        "root_scan_performed": False,
        "checks": checks,
        "contract_schema": contract_schema,
        "git_identity": git_identity,
        "durable_write_probe": {
            "requested": args.probe_durable_write,
            "observed": durable_write_observed,
            "error": durable_write_error,
        },
        "observations_supplied": {
            "lifecycle_hook_firing": args.lifecycle_hook_observed,
            "cross_session_state": args.cross_session_state_observed,
            "effect_or_result_receipt": args.effect_receipt_observed,
        },
        "authority_snapshot": _authority_snapshot(),
        "reasons": reasons,
        "promotion_fence": "This verifies an entry/install surface only; it grants zero EntityOS/HCU/J-Space/model/training/runtime credit.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if classification != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
