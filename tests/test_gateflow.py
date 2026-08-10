import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gateflow", ROOT / "tools" / "gateflow.py")
gateflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gateflow)

STATE = json.loads((ROOT / "research_entity" / "gateflow" / "GATEFLOW_V1_STATE.json").read_text())
CONVERSION = json.loads(
    (ROOT / "research_entity" / "gateflow" / "GATEFLOW_V1_CONVERSION_WINDOW_2026-08-11.json").read_text()
)


def state_with_conversion():
    state = json.loads(json.dumps(STATE))
    gateflow._apply_conversion_overlay(state, CONVERSION)
    return state


def test_state_is_valid():
    assert gateflow.validate(STATE) == []


def test_risk_metric_is_mandatory():
    mutated = json.loads(json.dumps(STATE))
    mutated["primary_objectives"].remove("risk_retired_per_1m_tokens")
    errors = gateflow.validate(mutated)
    assert any("risk_retired_per_1m_tokens" in e for e in errors)


def test_risk_units_are_deterministic():
    fork = next(e for e in STATE["risk_events"] if e["risk_id"] == "RISK-EFFECT-FORK-CAPABILITY-SHADOW")
    assert gateflow.risk_units(fork) == 3.0
    parser = next(e for e in STATE["risk_events"] if e["risk_id"] == "RISK-CLAYCODE-ANGLE-RELATION-TOKEN-AMBIGUITY")
    assert gateflow.risk_units(parser) == 3.0


def test_normalized_metrics_do_not_invent_denominator():
    metrics = gateflow.compile_metrics(STATE, tokens=None, worker_hours=None)
    assert metrics["risk_retired_per_1m_tokens"] is None
    assert metrics["accepted_gate_weight_delta_per_1m_tokens"] is None


def test_normalized_risk_rate_uses_measured_tokens():
    metrics = gateflow.compile_metrics(STATE, tokens=2_000_000, worker_hours=4)
    assert metrics["risk_retired_per_1m_tokens"] == 6.0
    assert metrics["accepted_gate_weight_delta_per_worker_hour"] == 0.0


def test_current_conversion_window_is_valid_and_separates_merge_from_credit():
    state = state_with_conversion()
    assert gateflow.validate(state) == []
    metrics = gateflow.compile_conversion_metrics(
        state, now="2026-08-11T01:09:00+07:00"
    )
    assert metrics["conversion_population_size"] == 5
    assert metrics["product_main_merged_uncredited_events"] == 4
    assert metrics["target_verified_unmerged_events"] == 1
    assert metrics["observed_product_main_merged_fraction"] == 0.8
    assert metrics["observed_workspace_credited_fraction"] == 0.0
    assert metrics["workspace_staleness_seconds_at_observation"] == 6675.0


def test_incomplete_population_never_becomes_fake_conversion_rate():
    metrics = gateflow.compile_conversion_metrics(
        state_with_conversion(), now="2026-08-11T01:09:00+07:00"
    )
    assert metrics["conversion_population_complete"] is False
    assert metrics["research_to_product_main_conversion_rate"] is None
    assert metrics["research_to_workspace_credit_conversion_rate"] is None


def test_workspace_credit_requires_receipt_and_positive_weight():
    state = state_with_conversion()
    event = state["conversion_events"][0]
    event["current_stage"] = "WORKSPACE_CREDITED"
    event["stage_times"]["WORKSPACE_CREDITED"] = "2026-08-11T01:08:00+07:00"
    errors = gateflow.validate(state)
    assert any("workspace_credit_ref" in e for e in errors)
    assert any("workspace_credited_weight" in e for e in errors)


def test_red_frontier_cannot_claim_receipt_ready():
    mutated = json.loads(json.dumps(STATE))
    mutated["frontier"][0]["freshness"] = "RED"
    mutated["frontier"][0]["state"] = "RECEIPT_READY"
    errors = gateflow.validate(mutated)
    assert any("RED freshness cannot be promotion-ready" in e for e in errors)
