import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gateflow", ROOT / "tools" / "gateflow.py")
gateflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gateflow)

STATE_PATH = ROOT / "research_entity" / "gateflow" / "GATEFLOW_V1_STATE.json"
RULES_PATH = ROOT / "research_entity" / "gateflow" / "GATEFLOW_V1_RULES.json"
STATE = json.loads(STATE_PATH.read_text())
RULES = json.loads(RULES_PATH.read_text())


def clone():
    return json.loads(json.dumps(STATE))


def test_state_is_valid():
    assert gateflow.validate(STATE) == []


def test_risk_metric_is_mandatory():
    mutated = clone()
    mutated["primary_objectives"].remove("risk_retired_per_1m_tokens")
    assert any("risk_retired_per_1m_tokens" in e for e in gateflow.validate(mutated))


def test_duplicate_failure_domain_cannot_multiply_credit():
    mutated = clone()
    duplicate = json.loads(json.dumps(mutated["risk_events"][0]))
    duplicate["risk_id"] = "OTHER-ID"
    mutated["risk_events"].append(duplicate)
    assert any("duplicate failure domain" in e for e in gateflow.validate(mutated))


def test_independent_failure_domains_can_share_subcheck():
    f09 = [x for x in STATE["frontier"] if x["work_package"] == "F-V01-09-EFFECT-AUTHORITY"]
    assert len({x["lease_scope"] for x in f09}) >= 2
    assert gateflow.validate(STATE) == []


def test_same_lease_scope_two_implementation_owners_is_rejected():
    mutated = clone()
    first = mutated["frontier"][0]
    duplicate = json.loads(json.dumps(first))
    duplicate["implementation_owner"] = "other/owner#999"
    mutated["frontier"].append(duplicate)
    assert any("WIP violation" in e for e in gateflow.validate(mutated))


def test_risk_units_are_deterministic():
    retired_fork = next(e for e in STATE["risk_events"] if e["risk_id"] == "RISK-EFFECT-FORK-CAPABILITY-SHADOW")
    assert gateflow.risk_units(retired_fork) == 5.0
    blocked_restore = next(e for e in STATE["risk_events"] if e["risk_id"] == "RISK-UNIFIEDDB-SNAPSHOT-GENERATION-RESURRECTION")
    assert gateflow.risk_units(blocked_restore) == 3.0


def test_normalized_metrics_do_not_invent_denominator():
    metrics = gateflow.compile_metrics(STATE, tokens=None, worker_hours=None)
    assert metrics["risk_retired_per_1m_tokens"] is None
    assert metrics["accepted_gate_weight_delta_per_1m_tokens"] is None


def test_normalized_risk_rate_uses_measured_tokens():
    metrics = gateflow.compile_metrics(STATE, tokens=2_000_000, worker_hours=4)
    assert metrics["risk_retired_per_1m_tokens"] == metrics["risk_retired_units"] / 2
    assert metrics["accepted_gate_weight_delta_per_worker_hour"] == 0.0


def test_diff_mapping_hits_effect_and_recovery_surfaces():
    mapped = gateflow.map_paths([
        "runtime/frank_execution_gate.py",
        "tests/frank_effect_exact_v16.py",
        "runtime/vps_unifieddb/recovery.py",
    ], RULES)
    keys = {(x["work_package"], x["subcheck"]) for x in mapped}
    assert ("F-V01-09-EFFECT-AUTHORITY", "presence_execution_generation_effect_fence") in keys
    assert ("F-V01-04-UNIFIEDDB-STATE-CONTINUITY", "state_continuity") in keys
