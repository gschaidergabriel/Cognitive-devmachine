#!/usr/bin/env python3
"""Fail-closed authority guard for Frankenstein provider orchestration.

This module is intentionally stdlib-only and NEVER imports provider clients, reads
provider secrets, opens network connections, or invokes Aider/Harness.

It is a source primitive for closing the current Supervisor 9.13 boundary.  It is
NOT a complete closure by itself: the existing Bauleiter/Bugfix scripts remain
quarantined until every provider/secret/network/Aider entry path calls an admitted
successor guard *before* those boundaries.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "FRANKENSTEIN_HARD_OFF_GUARD_RECEIPT/v1"
INBOX_REL = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")


def repository_root_from_file() -> Path:
    # .../research_entity/topic_packets/<packet>/<this file> -> repository root
    return Path(__file__).resolve().parents[3]


def load_inbox(repo_root: Path) -> dict[str, Any]:
    path = repo_root / INBOX_REL
    raw = path.read_text(encoding="utf-8")
    value = json.loads(raw)
    if type(value) is not dict:
        raise ValueError("SUPERVISOR_INBOX_NOT_OBJECT")
    return value


def evaluate_provider_authority(inbox: dict[str, Any]) -> dict[str, Any]:
    """Return a non-authorizing decision.

    v1 only proves that a HARD_OFF state blocks before provider-capable code is
    imported.  Any unknown or future authority shape also fails closed.  A future
    explicit authority change therefore requires an admitted successor, rather
    than this old guard silently becoming an execution grant.
    """
    schema_version = inbox.get("schema_version")
    free_only = inbox.get("free_only")
    frontier = inbox.get("current_frontier")

    if type(free_only) is not dict:
        free_only = {}
    if type(frontier) is not dict:
        frontier = {}

    runtime_provider_authority = frontier.get("runtime_provider_authority")
    provider_routes_admitted = free_only.get("provider_routes_admitted")
    together_forbidden = free_only.get("together_forbidden")
    remaining_paid = free_only.get("remaining_together_paid_runs_authorized")

    hard_off_markers = (
        isinstance(runtime_provider_authority, str)
        and "HARD_OFF" in runtime_provider_authority.upper()
    )
    hard_off = (
        provider_routes_admitted is False
        and together_forbidden is True
        and remaining_paid == 0
        and hard_off_markers
    )

    if hard_off:
        reason = "CURRENT_SUPERVISOR_HARD_OFF"
    else:
        reason = "UNKNOWN_OR_NON_HARD_OFF_AUTHORITY_REQUIRES_SUCCESSOR_REVIEW"

    return {
        "schema": SCHEMA,
        "decision": "BLOCK",
        "reason": reason,
        "supervisor_schema_version": schema_version,
        "runtime_provider_authority": runtime_provider_authority,
        "provider_routes_admitted": provider_routes_admitted,
        "together_forbidden": together_forbidden,
        "remaining_together_paid_runs_authorized": remaining_paid,
        "provider_calls": 0,
        "secret_lookups": 0,
        "network_calls": 0,
        "aider_calls": 0,
        "execution_authority_granted": False,
        "closure_scope": "GUARD_PRIMITIVE_ONLY_NOT_WIRED_TO_ALL_EXISTING_CALLERS",
    }


def check(repo_root: Path) -> dict[str, Any]:
    try:
        inbox = load_inbox(repo_root)
        return evaluate_provider_authority(inbox)
    except Exception as exc:  # fail closed; never expose file contents/secrets
        return {
            "schema": SCHEMA,
            "decision": "BLOCK",
            "reason": "AUTHORITY_READ_OR_PARSE_FAILED",
            "error_class": type(exc).__name__,
            "provider_calls": 0,
            "secret_lookups": 0,
            "network_calls": 0,
            "aider_calls": 0,
            "execution_authority_granted": False,
            "closure_scope": "GUARD_PRIMITIVE_ONLY_NOT_WIRED_TO_ALL_EXISTING_CALLERS",
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prove current Frankenstein provider orchestration fails closed before provider-capable imports."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repository_root_from_file(),
        help="Exact repository root. Defaults from this file location; never scans the filesystem root.",
    )
    args = parser.parse_args()
    receipt = check(args.repo_root.resolve())
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    # A BLOCK is the expected safe operational outcome.  Nonzero prevents callers
    # from treating this check as permission to continue into provider code.
    return 78


if __name__ == "__main__":
    raise SystemExit(main())
