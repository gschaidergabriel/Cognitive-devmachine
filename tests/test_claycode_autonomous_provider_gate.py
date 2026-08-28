from __future__ import annotations

import json
from pathlib import Path

from tools.claycode_autonomous_provider_gate import check_inbox, evaluate_provider_authority


def base_inbox() -> dict:
    return {
        "schema_version": "8.92",
        "free_only": {
            "enabled": True,
            "no_paid_fallback": True,
            "together_forbidden": True,
            "provider_routes_admitted": True,
            "free_swarm_owner_emergency_stop": False,
        },
        "current_frontier": {
            "runtime_provider_authority": "FREE_ONLY_CURRENT_ROUTE_ADMITTED"
        },
    }


def test_current_explicit_authority_can_admit():
    d = evaluate_provider_authority(base_inbox())
    assert d["admitted"] is True


def test_owner_emergency_stop_blocks():
    x = base_inbox()
    x["free_only"]["free_swarm_owner_emergency_stop"] = True
    d = evaluate_provider_authority(x)
    assert d["admitted"] is False
    assert d["reason"] == "OWNER_EMERGENCY_STOP"


def test_provider_routes_false_blocks():
    x = base_inbox()
    x["free_only"]["provider_routes_admitted"] = False
    d = evaluate_provider_authority(x)
    assert d["admitted"] is False
    assert d["reason"] == "PROVIDER_ROUTES_NOT_ADMITTED"


def test_hard_off_frontier_blocks_even_if_route_flag_true():
    x = base_inbox()
    x["current_frontier"]["runtime_provider_authority"] = "HARD_OFF_TEST"
    d = evaluate_provider_authority(x)
    assert d["admitted"] is False
    assert d["reason"] == "RUNTIME_PROVIDER_AUTHORITY_BLOCKED"


def test_stale_schema_blocks():
    x = base_inbox()
    x["schema_version"] = "8.91"
    d = evaluate_provider_authority(x)
    assert d["admitted"] is False
    assert d["reason"] == "STALE_AUTHORITY_SCHEMA"


def test_missing_inbox_fails_closed(tmp_path: Path):
    d = check_inbox(tmp_path / "missing.json")
    assert d["admitted"] is False


def test_malformed_inbox_fails_closed(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{bad", encoding="utf-8")
    d = check_inbox(p)
    assert d["admitted"] is False


def test_incomplete_authority_fields_fail_closed():
    x = base_inbox()
    del x["free_only"]["provider_routes_admitted"]
    d = evaluate_provider_authority(x)
    assert d["admitted"] is False
    assert d["reason"] == "INCOMPLETE_AUTHORITY_FIELDS"
