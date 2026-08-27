#!/usr/bin/env python3
"""Authority-first launcher for quarantined Frankenstein v1 roles.

This file is deliberately standard-library-only at module import time.  It resolves the
existing canonical free-pool provider gate *before* importing or executing either v1 role.
Under current 9.13 HARD_OFF the expected outcome is exit 77 with no provider role import,
no secret lookup by this launcher, no provider network request, and no Aider fallback.

Important scope boundary:
- this is a safe entry point for future use;
- it does NOT make direct invocation/import of the v1 scripts safe;
- it does NOT modify Frank's Harness;
- an admitted gate only authorizes continuation according to the current provider gate;
  downstream code still remains subject to all current authority/economic/provenance laws.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[3]
TOOLS_DIR = REPO_ROOT / "tools"
TOPIC_DIR = THIS_FILE.parent

ROLE_TARGETS = {
    "bauleiter": TOPIC_DIR / "frankenstein_orchestrator_v1.py",
    "bugfix": TOPIC_DIR / "frankenstein_bugfix_v1.py",
}

BLOCK_EXIT = 77


def _load_gate_decision() -> dict[str, Any]:
    """Load only the repository's standard-library authority gate.

    The imported gate is specifically designed to execute before credential lookup,
    provider SDK import, network, Aider, or fallback model selection.
    """
    tools = str(TOOLS_DIR)
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from freepool_fallback_provider_gate_v1 import decision_record  # noqa: PLC0415

    return dict(decision_record())


def evaluate_decision(decision: Mapping[str, Any], role: str) -> dict[str, Any]:
    """Return a non-secret-bearing launch decision.

    Only literal boolean True admits continuation.  Missing, truthy-string, malformed,
    or false values all fail closed.
    """
    if role not in ROLE_TARGETS:
        return {
            "schema": "FRANKENSTEIN_LAUNCH_GATE/v2",
            "role": role,
            "admitted": False,
            "reason": "UNKNOWN_ROLE",
            "required_action": "STOP",
            "provider_calls": 0,
            "secret_lookups_by_launcher": 0,
        }

    admitted = decision.get("admitted") is True
    record = {
        "schema": "FRANKENSTEIN_LAUNCH_GATE/v2",
        "role": role,
        "admitted": admitted,
        "provider_gate_schema": decision.get("schema"),
        "authority_schema_version": decision.get("authority_schema_version"),
        "runtime_provider_authority": decision.get("runtime_provider_authority"),
        "provider_gate_reason": decision.get("reason", "UNKNOWN"),
        "target": str(ROLE_TARGETS[role].relative_to(REPO_ROOT)),
        "provider_calls": 0,
        "secret_lookups_by_launcher": 0,
    }
    if admitted:
        record["required_action"] = "MAY_EXEC_RETAINED_ROLE_SUBJECT_TO_CURRENT_AUTHORITY"
    else:
        record["required_action"] = (
            "STOP_BEFORE_RETAINED_ROLE_IMPORT_SECRET_LOOKUP_PROVIDER_NETWORK_OR_AIDER"
        )
    return record


def _target_for_role(role: str) -> Path:
    target = ROLE_TARGETS[role]
    try:
        resolved = target.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f"retained role target missing: {target}") from exc

    topic = TOPIC_DIR.resolve(strict=True)
    if resolved.parent != topic:
        raise RuntimeError(f"retained role escaped topic directory: {resolved}")
    return resolved


def parse_args(argv: Sequence[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Authority-first entry for quarantined Frankenstein v1 roles."
    )
    parser.add_argument("--role", required=True, choices=sorted(ROLE_TARGETS))
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Print current gate decision and never execute a retained role.",
    )
    args, remainder = parser.parse_known_args(argv)
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    return args, remainder


def main(argv: Sequence[str] | None = None) -> int:
    args, remainder = parse_args(argv)

    # Critical ordering invariant: current authority is resolved before the retained v1
    # role is imported/executed.  This launcher never imports llm/requests/Aider itself.
    decision = _load_gate_decision()
    launch = evaluate_decision(decision, args.role)
    print(json.dumps(launch, sort_keys=True))

    if args.probe:
        return 0 if launch["admitted"] else BLOCK_EXIT
    if not launch["admitted"]:
        return BLOCK_EXIT

    target = _target_for_role(args.role)
    os.execv(sys.executable, [sys.executable, str(target), *remainder])
    raise AssertionError("os.execv unexpectedly returned")


if __name__ == "__main__":
    raise SystemExit(main())
