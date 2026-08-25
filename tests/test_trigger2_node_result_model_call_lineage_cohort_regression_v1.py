from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_node_result_model_call_lineage_gate_v1.py"
spec = importlib.util.spec_from_file_location("lineage_gate", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)


def d(label: str) -> str:
    return gate.canonical_sha256({"label": label})


def h40(ch: str) -> str:
    return ch * 40


def member(i: int, *, call_id: str | None = None, output_id: str | None = None):
    call_id = call_id or d(f"call-{i}")
    output_id = output_id or d(f"output-{i}")
    authority = {
        "schema": gate.LINEAGE_ENVELOPE_SCHEMA,
        "causal_event_id": f"event-{i}",
        "admission_id": f"admission-{i}",
        "route_decision_identity_sha256": d(f"route-{i}"),
        "resolved_engine_identity_sha256": d(f"engine-{i}"),
        "grid_plan_identity_sha256": d("plan"),
        "grid_cell_id": f"cell-{i}",
        "controller_observed_node_id": f"x{i:02d}",
        "source_membership_id": f"membership-{i}",
        "producer_pid": 1000 + i,
        "runtime_generation": 1,
        "raw_node_result_packet_digest": d(f"packet-{i}"),
        "node_authority_envelope_digest": d(f"node-envelope-{i}"),
        "source_bound_model_call_identity_sha256": call_id,
        "model_output_identity_sha256": output_id,
        "source_identity_sha256": d("source"),
        "source_head_sha": h40("a"),
        "source_tree_sha": h40("b"),
        "controller_lineage_sha256": d(f"controller-lineage-{i}"),
        "model_generated": False,
        "s0_truth": False,
        "effect_authority": False,
    }
    return {
        "schema": gate.SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_ONLY_LINEAGE_COMPONENT",
        "source_bound_model_call_identity_sha256": call_id,
        "model_output_identity_sha256": output_id,
        "node_result_packet_digest": authority["raw_node_result_packet_digest"],
        "node_authority_envelope_digest": authority["node_authority_envelope_digest"],
        "controller_lineage_sha256": authority["controller_lineage_sha256"],
        "grid_plan_identity_sha256": authority["grid_plan_identity_sha256"],
        "grid_cell_id": authority["grid_cell_id"],
        "controller_observed_node_id": authority["controller_observed_node_id"],
        "lineage_authority_envelope": authority,
        "lineage_authority_envelope_digest": gate.canonical_sha256(authority),
    }


def test_distinct_calls_form_valid_cohort():
    out = gate.validate_lineage_bound_cohort([member(1), member(2)], expected_member_count=2)
    assert out["pass"] is True
    assert out["envelope"]["member_count"] == 2


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Current v1 cohort validator checks unique cell/node/packet/envelope identities but "
        "does not yet reject reuse of one exact source_bound_model_call_identity_sha256 "
        "across two distinct node/cell members. Remove xfail when the gate rejects it."
    ),
)
def test_duplicate_exact_model_call_cannot_occupy_two_nodes_or_cells():
    shared_call = d("shared-call")
    with pytest.raises(gate.GateError, match="^LINEAGE_COHORT_DUPLICATE_MODEL_CALL$"):
        gate.validate_lineage_bound_cohort(
            [member(1, call_id=shared_call), member(2, call_id=shared_call)],
            expected_member_count=2,
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Current v1 cohort validator verifies the committed authority-envelope digest but "
        "does not cross-check every top-level cohort projection against that envelope. "
        "Remove xfail when top-level call-reference transplant is rejected."
    ),
)
def test_top_level_call_reference_must_match_committed_authority_envelope():
    item = member(1)
    item["source_bound_model_call_identity_sha256"] = d("transplanted-call")
    with pytest.raises(
        gate.GateError,
        match="^LINEAGE_COHORT_RESULT_CALL_REFERENCE_MISMATCH$",
    ):
        gate.validate_lineage_bound_cohort([item], expected_member_count=1)


def test_identical_model_output_is_allowed_when_exact_calls_are_distinct():
    shared_output = d("same-output")
    out = gate.validate_lineage_bound_cohort(
        [member(1, output_id=shared_output), member(2, output_id=shared_output)],
        expected_member_count=2,
    )
    assert out["pass"] is True
