#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_wp04_reward_transition_readiness_v1 as readiness

SUCCESSOR = ROOT / "research_entity/global/FRANK_REWARD_STATE_SUCCESSOR_V1.clay"
REFERENCE = ROOT / "research_entity/experiments/frank_reward_state_reference.py"


def main() -> int:
    source = SUCCESSOR.read_text(encoding="utf-8")
    reference = REFERENCE.read_text(encoding="utf-8")
    report = readiness.audit(source, reference_source=reference)
    summary = report["summary"]
    by_id = {x["obligation_id"]: x["status"] for x in report["obligations"]}

    assert summary["required"] == 21, summary
    assert summary["explicitly_declared"] == 4, summary
    assert summary["missing_exact_definition"] == 17, summary
    assert summary["deterministic_evaluator_ready"] is False
    assert summary["runtime_binding_admitted"] is False
    assert summary["execution_admitted"] is False
    assert summary["effect_authority"] == summary["truth_authority"] == "NONE"

    for key in ("material_admission", "material_learning_weight", "horizon_rates", "phasic_mix_weights"):
        assert by_id[key] == "EXPLICITLY_DECLARED", (key, by_id[key])
    for key in (
        "observed_value", "bounded_update", "bounded_distribution_update",
        "normalize_by_prediction_uncertainty", "robust_mix", "clamp01", "exploration_nudge",
        "tonic_transition", "habituation_transition", "opponent_transition",
        "admitted_events_transition", "last_phasic_transition", "state_epoch_transition",
        "veto_threshold", "brake_threshold", "receipt_projection", "receipt_provenance",
    ):
        assert by_id[key] == "MISSING_EXACT_DEFINITION", (key, by_id[key])

    try:
        readiness.require_evaluator_ready(report)
    except ValueError:
        real_source_execution_gate = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("incomplete real reward semantics reached evaluator-ready state")

    ref = report["reference_evidence"]
    assert ref["present"] is True
    assert ref["classification"] == "RESEARCH_REFERENCE_NONAUTHORITATIVE"
    assert ref["may_fill_missing_authoritative_definitions"] is False
    assert all(ref["signals_concrete_candidate_choices"].values()), ref

    # Positive completeness-control only. These appended declarations demonstrate that the
    # finite checker can close; they are NOT proposed reward semantics and are never executed.
    synthetic_completion = source + r'''
rule observed_value(e,d)=e.utility
rule bounded_update(prediction,value,rate)=prediction
rule bounded_distribution_update(variance,delta)=variance
rule normalize_by_prediction_uncertainty(delta)=delta
rule robust_mix(values,weights)=0
rule clamp01(x)=x
rule exploration_nudge(e)=0
rule tonic(state)=state.tonic
rule habituation(state)=state.habituation
rule opponent(state)=state.opponent
rule admitted_events = admitted_events + 1
rule last_phasic = phasic
rule state_epoch = state_epoch + 1
parameter veto_threshold=-0.18
parameter brake_threshold=-0.22
fn build_reward_plasticity_receipt(x:Unit)->Unit=x
rule provenance = source_ref
'''
    synthetic = readiness.audit(synthetic_completion, reference_source=reference)
    assert synthetic["summary"]["missing_exact_definition"] == 0, synthetic["obligations"]
    assert synthetic["summary"]["deterministic_evaluator_ready"] is True
    readiness.require_evaluator_ready(synthetic)

    missing = [x["obligation_id"] for x in report["obligations"] if x["status"] == "MISSING_EXACT_DEFINITION"]
    output = {
        "status": "PASS_FAIL_CLOSED_INCOMPLETE_EVALUATOR_SEMANTICS",
        "scope": "WP04_FRANK_REWARD_STATEFUL_TRANSITION_READINESS_V1",
        "authoritative_source_sha256": report["authoritative_source_sha256"],
        "reference_source_sha256": ref["source_sha256"],
        "required_obligations": summary["required"],
        "explicitly_declared": summary["explicitly_declared"],
        "missing_exact_definition": summary["missing_exact_definition"],
        "missing_obligations": missing,
        "real_source_execution_gate": real_source_execution_gate,
        "research_reference_authority": "NONE",
        "research_reference_may_fill_gap": False,
        "synthetic_completeness_control": "PASS_NONAUTHORITATIVE_NOT_EXECUTED",
        "runtime_binding_admitted": False,
        "execution_admitted": False,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "readiness_receipt_sha256": report["readiness_receipt_sha256"],
        "promotion": "NONE",
        "interpretation": "The stateful call contract is necessary but not sufficient for an evaluator. Current authoritative reward semantics specify admission and top-level horizon parameters, but 17 deterministic transition/receipt obligations remain undeclared. The older executable Python reference contains candidate numerical choices but has no authority to fill them silently.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
