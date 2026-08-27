#!/usr/bin/env python3
"""Fail-closed provider authority gate for the autonomous ClayCode cycle.

This module intentionally uses only the Python standard library. It must run before the
provider-capable autonomous cycle is imported or any secret lookup/provider operation can
occur.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
MIN_AUTHORITY_SCHEMA = Decimal("8.92")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"authority inbox unavailable or malformed: {type(exc).__name__}") from exc
    if not isinstance(raw, dict):
        raise ValueError("authority inbox root must be an object")
    return raw


def _schema_version(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("authority schema_version is missing or invalid") from exc


def evaluate_provider_authority(inbox: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic admission decision without touching credentials/providers."""
    version = _schema_version(inbox.get("schema_version"))
    if version < MIN_AUTHORITY_SCHEMA:
        return {
            "admitted": False,
            "reason": "STALE_AUTHORITY_SCHEMA",
            "schema_version": str(version),
        }

    free_only = inbox.get("free_only")
    frontier = inbox.get("current_frontier")
    if not isinstance(free_only, dict) or not isinstance(frontier, dict):
        return {
            "admitted": False,
            "reason": "MALFORMED_AUTHORITY_FIELDS",
            "schema_version": str(version),
        }

    required = (
        "enabled",
        "no_paid_fallback",
        "together_forbidden",
        "provider_routes_admitted",
        "free_swarm_owner_emergency_stop",
    )
    if any(key not in free_only for key in required):
        return {
            "admitted": False,
            "reason": "INCOMPLETE_AUTHORITY_FIELDS",
            "schema_version": str(version),
        }

    runtime_authority = str(frontier.get("runtime_provider_authority") or "")
    if not runtime_authority:
        return {
            "admitted": False,
            "reason": "MISSING_RUNTIME_PROVIDER_AUTHORITY",
            "schema_version": str(version),
        }

    # Provider-capable autonomous execution is admitted only by an explicit, internally
    # consistent current authority. Any emergency stop, disabled route, paid fallback,
    # Together allowance, or HARD_OFF/QUARANTINE frontier fails closed.
    if free_only.get("enabled") is not True:
        reason = "FREE_ONLY_NOT_ENABLED"
    elif free_only.get("no_paid_fallback") is not True:
        reason = "PAID_FALLBACK_NOT_FORBIDDEN"
    elif free_only.get("together_forbidden") is not True:
        reason = "TOGETHER_NOT_FORBIDDEN"
    elif free_only.get("free_swarm_owner_emergency_stop") is True:
        reason = "OWNER_EMERGENCY_STOP"
    elif free_only.get("provider_routes_admitted") is not True:
        reason = "PROVIDER_ROUTES_NOT_ADMITTED"
    elif "HARD_OFF" in runtime_authority.upper() or "QUARANTIN" in runtime_authority.upper():
        reason = "RUNTIME_PROVIDER_AUTHORITY_BLOCKED"
    else:
        return {
            "admitted": True,
            "reason": "CURRENT_AUTHORITY_EXPLICITLY_ADMITS_PROVIDER_ROUTE",
            "schema_version": str(version),
            "runtime_provider_authority": runtime_authority,
        }

    return {
        "admitted": False,
        "reason": reason,
        "schema_version": str(version),
        "runtime_provider_authority": runtime_authority,
    }


def check_inbox(path: Path = DEFAULT_INBOX) -> dict[str, Any]:
    try:
        return evaluate_provider_authority(_load_json(path))
    except ValueError as exc:
        return {"admitted": False, "reason": str(exc)}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = Path(args[0]).resolve() if args else DEFAULT_INBOX
    decision = check_inbox(path)
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision.get("admitted") is True else 77


if __name__ == "__main__":
    raise SystemExit(main())
