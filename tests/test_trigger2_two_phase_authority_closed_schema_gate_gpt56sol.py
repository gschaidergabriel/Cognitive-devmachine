from __future__ import annotations

import pytest

from tools.trigger2_node_result_model_call_two_phase_authority_v1 import (
    GateError,
    SCHEMA,
    canonical_sha256,
    validate_authority_envelope,
)


def _valid_authority_envelope() -> dict:
    h = "1" * 64
    body = {
        "schema": SCHEMA,
        "raw_node_result_packet_digest": h,
        "source_bound_model_call_identity_sha256": "2" * 64,
        "model_output_identity_sha256": "3" * 64,
        "abi_v2_receipt_sha256": "4" * 64,
        "source_identity_sha256": "5" * 64,
        "launch_descriptor_sha256": "6" * 64,
        "executor_observation_sha256": "7" * 64,
        "cohort_plan_id": "plan-current",
        "grid_cell_id": "cell-01",
        "controller_observed_node_id": "x01",
        "controller_observed_pid": 9001,
        "source_node_admission_id": "member-current",
        "source_node_admission_revision": 1,
        "source_runtime_generation": 1,
        "raw_generation": 1,
        "raw_state_epoch": 1,
        "raw_state_digest": "8" * 64,
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
            "training_credit": 0,
        },
    }


@pytest.mark.xfail(
    strict=True,
    reason=(
        "current validator hashes the declared authority body but does not yet fail closed "
        "on unknown top-level authority-envelope fields"
    ),
)
def test_unknown_top_level_authority_field_is_rejected_fail_closed() -> None:
    envelope = _valid_authority_envelope()
    original_identity = envelope["authority_envelope_sha256"]

    # Characterize the ambiguity without granting it authority: this field is not part of
    # the current body_keys commitment and therefore must be rejected rather than tolerated.
    envelope["uncommitted_semantic_extension"] = {
        "claims_physical_runtime": True,
        "claims_training_admission": True,
    }

    # The claimed authority identity is deliberately unchanged by the injected field.
    assert envelope["authority_envelope_sha256"] == original_identity

    with pytest.raises(GateError):
        validate_authority_envelope(envelope)
