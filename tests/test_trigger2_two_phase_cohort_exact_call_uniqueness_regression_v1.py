from __future__ import annotations

import hashlib

import pytest

from tools.trigger2_node_result_model_call_two_phase_authority_v1 import (
    SCHEMA,
    GateError,
    canonical_sha256,
    derive_authority_cohort_id,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def member(
    i: int,
    *,
    call_id: str | None = None,
    output_id: str | None = None,
    node_admission_id: str | None = None,
) -> dict:
    body = {
        "schema": SCHEMA,
        "raw_node_result_packet_digest": h(f"packet-{i}"),
        "source_bound_model_call_identity_sha256": call_id or h(f"call-{i}"),
        "model_output_identity_sha256": output_id or h(f"output-{i}"),
        "abi_v2_receipt_sha256": h(f"abi-{i}"),
        "source_identity_sha256": h("source"),
        "launch_descriptor_sha256": h(f"launch-{i}"),
        "executor_observation_sha256": h(f"observation-{i}"),
        "cohort_plan_id": h("plan"),
        "grid_cell_id": f"cell-{i:02d}",
        "controller_observed_node_id": f"x{i:02d}",
        "controller_observed_pid": 7000 + i,
        "source_node_admission_id": node_admission_id or f"member-{i:02d}",
        "source_node_admission_revision": i,
        "source_runtime_generation": 7,
        "raw_generation": 7,
        "raw_state_epoch": 11,
        "raw_state_digest": h("state"),
    }
    return {
        **body,
        "authority_envelope_sha256": canonical_sha256(body),
        "model_generated": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": {
            "model_call_runtime_credit": 0,
            "physical_grid10_runtime_credit": 0,
            "checkpoint_selection_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def test_distinct_exact_calls_form_valid_two_member_cohort():
    cohort_id = derive_authority_cohort_id([member(1), member(2)], expected_member_count=2)
    assert len(cohort_id) == 64


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known source gap from CLAY_TRIGGER2_TWO_PHASE_COHORT_EXACT_CALL_UNIQUENESS_AUDIT/v1: "
        "distinct launch/executor-observation wrappers currently do not make reuse of one exact "
        "source_bound_model_call_identity_sha256 fail closed. Remove xfail when the retained "
        "two-phase cohort reducer raises AUTHORITY_COHORT_MODEL_CALL_DUPLICATE."
    ),
)
def test_one_exact_model_call_cannot_occupy_two_distinct_cells():
    shared_call = h("shared-exact-call")
    with pytest.raises(GateError, match="^AUTHORITY_COHORT_MODEL_CALL_DUPLICATE$"):
        derive_authority_cohort_id(
            [member(1, call_id=shared_call), member(2, call_id=shared_call)],
            expected_member_count=2,
        )


def test_identical_model_output_is_allowed_for_distinct_exact_calls():
    shared_output = h("same-output")
    cohort_id = derive_authority_cohort_id(
        [member(1, output_id=shared_output), member(2, output_id=shared_output)],
        expected_member_count=2,
    )
    assert len(cohort_id) == 64


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Secondary source-provenance gap: one node-admission identity should not be projected "
        "onto two distinct cohort nodes. Remove xfail when the two-phase reducer raises "
        "AUTHORITY_COHORT_NODE_ADMISSION_DUPLICATE or cross-validates admission-to-node identity."
    ),
)
def test_one_node_admission_identity_cannot_occupy_two_distinct_nodes():
    shared_admission = "member-shared"
    with pytest.raises(GateError, match="^AUTHORITY_COHORT_NODE_ADMISSION_DUPLICATE$"):
        derive_authority_cohort_id(
            [
                member(1, node_admission_id=shared_admission),
                member(2, node_admission_id=shared_admission),
            ],
            expected_member_count=2,
        )
