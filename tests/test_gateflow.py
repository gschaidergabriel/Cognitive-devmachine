import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gateflow", ROOT / "tools" / "gateflow.py")
gateflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gateflow)

STATE = json.loads((ROOT / "research_entity" / "gateflow" / "GATEFLOW_V1_STATE.json").read_text())


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
