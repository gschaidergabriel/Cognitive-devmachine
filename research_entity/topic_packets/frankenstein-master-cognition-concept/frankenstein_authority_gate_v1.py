"""Fail-closed Frankenstein provider authority gate.

Provider-backed Frankenstein code is allowed to load only when BOTH current
control artifacts agree that provider execution is admitted.  The gate is
stdlib-only and must run before provider imports, secret lookup, network, Aider,
or fallback dispatch.
"""
from __future__ import annotations

import json
from pathlib import Path

INBOX_RELATIVE_PATH = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
PROVIDER_ADMISSION_RELATIVE_PATH = Path("research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")


class ProviderAuthorityBlocked(RuntimeError):
    pass


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def provider_authority_state(repo_root: Path) -> dict:
    """Resolve split-brain-safe provider authority from both canonical artifacts.

    Any missing/malformed artifact, HARD_OFF state, contradictory admission, or
    lack of an explicit canonical provider admission fails closed.  Historical
    prose and an Inbox-only mutation can never mint provider execution authority.
    """
    inbox = _read_json(repo_root / INBOX_RELATIVE_PATH)
    canonical = _read_json(repo_root / PROVIDER_ADMISSION_RELATIVE_PATH)
    if inbox is None or canonical is None:
        return {
            "authority_readable": False,
            "authority_coherent": False,
            "provider_routes_admitted": False,
            "together_admitted": False,
            "admitted_provider_names": [],
            "reason": "MISSING_OR_MALFORMED_DUAL_AUTHORITY",
        }

    free_only = inbox.get("free_only")
    providers = canonical.get("providers")
    if not isinstance(free_only, dict) or not isinstance(providers, dict):
        return {
            "authority_readable": True,
            "authority_coherent": False,
            "provider_routes_admitted": False,
            "together_admitted": False,
            "admitted_provider_names": [],
            "reason": "MALFORMED_AUTHORITY_SHAPE",
        }

    inbox_enabled = free_only.get("enabled") is True
    inbox_routes = free_only.get("provider_routes_admitted") is True
    emergency_stop = free_only.get("free_swarm_owner_emergency_stop") is not False
    no_paid_fallback = free_only.get("no_paid_fallback") is not False

    canonical_mode = canonical.get("mode")
    canonical_state = canonical.get("execution_state")
    canonical_hard_off = canonical_state == "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF"
    admitted_provider_names = sorted(
        name for name, spec in providers.items()
        if isinstance(spec, dict) and spec.get("admitted") is True
    )
    # The provider-backed donor contains a fallback cascade, so generic dispatch
    # is safe only when the canonical authority has no denied named provider.
    canonical_all_named_admitted = bool(providers) and all(
        isinstance(spec, dict) and spec.get("admitted") is True
        for spec in providers.values()
    )

    coherent = not (
        (inbox_routes and canonical_hard_off)
        or (inbox_routes and not canonical_all_named_admitted)
        or ((not emergency_stop) and canonical_hard_off)
    )
    provider_routes_admitted = bool(
        coherent
        and inbox_enabled
        and inbox_routes
        and not emergency_stop
        and canonical_mode == "FREE_ONLY"
        and not canonical_hard_off
        and canonical_all_named_admitted
    )

    together_forbidden = free_only.get("together_forbidden") is not False
    remaining_paid = free_only.get("remaining_together_paid_runs_authorized")
    if not isinstance(remaining_paid, int) or isinstance(remaining_paid, bool):
        remaining_paid = 0
    # Paid execution requires an explicit canonical object as well as Inbox
    # admission.  FREE_PROVIDER_ADMISSION/v1 currently contains no such object,
    # therefore Together remains fail-closed even if stale Inbox prose says yes.
    canonical_together = canonical.get("together")
    canonical_together_admitted = (
        isinstance(canonical_together, dict)
        and canonical_together.get("admitted") is True
    )
    together_admitted = bool(
        provider_routes_admitted
        and not no_paid_fallback
        and not together_forbidden
        and remaining_paid > 0
        and canonical_together_admitted
    )

    reason = "ADMITTED" if provider_routes_admitted else (
        "AUTHORITY_SPLIT_BRAIN_FAIL_CLOSED" if not coherent else "PROVIDER_ROUTES_NOT_DUALLY_ADMITTED"
    )
    return {
        "authority_readable": True,
        "authority_coherent": coherent,
        "provider_routes_admitted": provider_routes_admitted,
        "together_admitted": together_admitted,
        "admitted_provider_names": admitted_provider_names,
        "canonical_authority_epoch": canonical.get("authority_epoch"),
        "canonical_execution_state": canonical_state,
        "reason": reason,
    }


def require_provider_routes(caller: str, repo_root: Path) -> dict:
    state = provider_authority_state(repo_root)
    if not state["provider_routes_admitted"]:
        raise ProviderAuthorityBlocked(
            f"{caller}: blocked before provider import/secret lookup/network; "
            f"reason={state.get('reason')}"
        )
    return state
