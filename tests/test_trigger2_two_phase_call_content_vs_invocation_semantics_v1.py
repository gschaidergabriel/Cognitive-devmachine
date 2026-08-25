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
    call_content_id: str | None = None,
    output_id: str | None = None,
    launch_id: str | None = None,
    observation_id: str | None = None,
    node_admission_id: str | None = None,
) -> dict:
    body = {
        "schema": SCHEMA,
        "raw_node_result_packet_digest": h(f"packet-{i}"),
        "source_bound_model_call_identity_sha256": call_content_id or h(f"call-content-{i}"),
        "model_output_identity_sha256": output_id or h(f"output-{i}"),
        "abi_v2_receipt_sha256": h(f"abi-{i}"),
        "source_identity_sha256": h("source"),
        "launch_descriptor_sha256": launch_id or h(f"launch-{i}"),
        "executor_observation_sha256": observation_id or h(f"observation-{i}"),
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


def test_two_independent_invocations_may_share_call_content_identity():
    shared_call_content = h("same-call-content-evidence")
    shared_output = h("same-deterministic-output")
    cohort_id = derive_authority_cohort_id(
        [
            member(1, call_content_id=shared_call_content, output_id=shared_output),
            member(2, call_content_id=shared_call_content, output_id=shared_output),
        ],
        expected_member_count=2,
    )
    assert len(cohort_id) == 64


def test_reusing_one_executor_observation_across_two_cells_is_rejected():
    shared_observation = h("one-postcall-observation")
    with pytest.raises(GateError, match="^AUTHORITY_COHORT_EXECUTOR_OBSERVATION_DUPLICATE$"):
        derive_authority_cohort_id(
            [
                member(1, observation_id=shared_observation),
                member(2, observation_id=shared_observation),
            ],
            expected_member_count=2,
        )


def test_reusing_one_launch_descriptor_across_two_cells_is_rejected():
    shared_launch = h("one-precall-launch")
    with pytest.raises(GateError, match="^AUTHORITY_COHORT_LAUNCH_DUPLICATE$"):
        derive_authority_cohort_id(
            [member(1, launch_id=shared_launch), member(2, launch_id=shared_launch)],
            expected_member_count=2,
        )


def test_equal_output_content_does_not_collapse_distinct_invocations():
    shared_output = h("same-output")
    cohort_id = derive_authority_cohort_id(
        [member(1, output_id=shared_output), member(2, output_id=shared_output)],
        expected_member_count=2,
    )
    assert len(cohort_id) == 64


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Remaining membership-provenance discriminator: one admitted membership identity should "
        "not be projected onto two distinct nodes unless an explicit fanout/consumer contract says "
        "so. Remove xfail when the retained two-phase path cross-validates membership-to-node or "
        "raises AUTHORITY_COHORT_NODE_ADMISSION_DUPLICATE."
    ),
)
def test_one_node_admission_identity_cannot_be_projected_onto_two_nodes():
    shared_admission = "member-shared"
    with pytest.raises(GateError, match="^AUTHORITY_COHORT_NODE_ADMISSION_DUPLICATE$"):
        derive_authority_cohort_id(
            [
                member(1, node_admission_id=shared_admission),
                member(2, node_admission_id=shared_admission),
            ],
            expected_member_count=2,
        )
