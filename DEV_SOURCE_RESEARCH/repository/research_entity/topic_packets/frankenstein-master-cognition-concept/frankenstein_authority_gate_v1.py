"""Fail-closed runtime authority gate for Frankenstein provider orchestration.

This module is deliberately stdlib-only. It must be evaluated before importing
provider clients, reading provider key material, invoking Aider, or executing a
quarantined provider-backed Frankenstein implementation.
"""
from __future__ import annotations

import json
from pathlib import Path

INBOX_RELATIVE_PATH = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")


class ProviderAuthorityBlocked(RuntimeError):
    """Raised before any external provider boundary when authority is closed."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def provider_authority_state(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root is not None else _repo_root()
    inbox_path = root / INBOX_RELATIVE_PATH
    try:
        inbox = json.loads(inbox_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "authority_source": str(inbox_path),
            "authority_readable": False,
            "provider_routes_admitted": False,
            "together_admitted": False,
            "reason": f"FAIL_CLOSED_AUTHORITY_UNREADABLE:{type(exc).__name__}",
        }

    free_only = inbox.get("free_only")
    if not isinstance(free_only, dict):
        return {
            "authority_source": str(inbox_path),
            "authority_readable": True,
            "provider_routes_admitted": False,
            "together_admitted": False,
            "reason": "FAIL_CLOSED_FREE_ONLY_BLOCK_MISSING",
            "schema_version": inbox.get("schema_version"),
        }

    enabled = free_only.get("enabled") is True
    explicit_provider_admission = free_only.get("provider_routes_admitted") is True
    emergency_stop = free_only.get("free_swarm_owner_emergency_stop") is True
    provider_routes_admitted = enabled and explicit_provider_admission and not emergency_stop

    together_forbidden = free_only.get("together_forbidden") is not False
    remaining_paid_runs = free_only.get("remaining_together_paid_runs_authorized", 0)
    try:
        remaining_paid_runs = int(remaining_paid_runs)
    except (TypeError, ValueError):
        remaining_paid_runs = 0
    together_admitted = provider_routes_admitted and not together_forbidden and remaining_paid_runs > 0

    if provider_routes_admitted:
        reason = "EXPLICIT_PROVIDER_ROUTE_ADMISSION_PRESENT"
    elif emergency_stop:
        reason = "FREE_SWARM_OWNER_EMERGENCY_STOP"
    elif not explicit_provider_admission:
        reason = "PROVIDER_ROUTES_NOT_EXPLICITLY_ADMITTED"
    else:
        reason = "FREE_ONLY_NOT_ENABLED_FAIL_CLOSED"

    return {
        "authority_source": str(inbox_path),
        "authority_readable": True,
        "schema_version": inbox.get("schema_version"),
        "provider_routes_admitted": provider_routes_admitted,
        "together_admitted": together_admitted,
        "free_swarm_owner_emergency_stop": emergency_stop,
        "remaining_together_paid_runs_authorized": remaining_paid_runs,
        "reason": reason,
    }


def require_provider_routes(caller: str, repo_root: Path | None = None) -> dict:
    state = provider_authority_state(repo_root)
    if not state["provider_routes_admitted"]:
        raise ProviderAuthorityBlocked(
            f"{caller}: external provider orchestration blocked before provider import/secret lookup/network; "
            f"reason={state['reason']} authority={state['authority_source']}"
        )
    return state
