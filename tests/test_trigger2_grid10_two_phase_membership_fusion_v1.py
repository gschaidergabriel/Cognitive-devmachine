from __future__ import annotations

from copy import deepcopy
import hashlib
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from trigger2_grid10_two_phase_membership_fusion_v1 import (
    FusionError,
    NODE_RESULT_SCHEMA,
    PROOF_SCHEMA,
    commit_cross_bound_cohort,
    cross_validate_member_pair,
    digest,
    validate_cohort_cross_binding,
)
from trigger2_node_result_model_call_two_phase_authority_v1 import (
    SCHEMA as TWO_PHASE_SCHEMA,
    canonical_sha256,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def proof(
    idx: int,
    *,
    membership: str | None = None,
    serial: int | None = None,
    generation: int = 7,
    pid: int | None = None,
):
    node = f"x{idx:02d}"
    membership = membership or f"member-{idx:02d}"
    serial = serial or idx
    pid = pid or 5000 + idx
    packet = {
        "schema": NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node,
        "generation": generation,
        "state_epoch": 11,
        "state_digest": h("state"),
        "producer_pid": pid,
        "payload": {"process_pid": pid, "value": f"v{idx}"},
        "s1_write_intent": False,
    }
    core = {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }
    packet["packet_digest"] = digest(core)
    envelope = {
        "schema": PROOF_SCHEMA,
        "node_result_digest": packet["packet_digest"],
        "node_result": packet,
        "source_membership_id": membership,
        "membership_receipt": {
            "membership_id": membership,
            "node_id": node,
            "capability": "reason",
            "generation": generation,
            "serial": serial,
            "valid": 1,
            "healthy": 1,
        },
        "producer_pid": pid,
    }
    envelope["envelope_digest"] = digest(envelope)
    return envelope


def authority(
    idx: int,
    proof_envelope,
    *,
    call: str | None = None,
    output: str | None = None,
    membership: str | None = None,
    serial: int | None = None,
    generation: int = 7,
    launch: str | None = None,
    observation: str | None = None,
):
    node = f"x{idx:02d}"
    membership = membership or proof_envelope["source_membership_id"]
    serial = serial or proof_envelope["membership_receipt"]["serial"]
    body = {
        "schema": TWO_PHASE_SCHEMA,
        "raw_node_result_packet_digest": proof_envelope["node_result_digest"],
        "source_bound_model_call_identity_sha256": call or h(f"call-{idx}"),
        "model_output_identity_sha256": output or h(f"out-{idx}"),
        "abi_v2_receipt_sha256": h(f"abi-{idx}"),
        "source_identity_sha256": h("src"),
        "launch_descriptor_sha256": launch or h(f"launch-{idx}"),
        "executor_observation_sha256": observation or h(f"obs-{idx}"),
        "cohort_plan_id": h("plan"),
        "grid_cell_id": f"cell-{idx:02d}",
        "controller_observed_node_id": node,
        "controller_observed_pid": proof_envelope["producer_pid"],
        "source_node_admission_id": membership,
        "source_node_admission_revision": serial,
        "source_runtime_generation": generation,
        "raw_generation": proof_envelope["node_result"]["generation"],
        "raw_state_epoch": proof_envelope["node_result"]["state_epoch"],
        "raw_state_digest": proof_envelope["node_result"]["state_digest"],
    }
    return {
        **body,
        "authority_envelope_sha256": canonical_sha256(body),
        "model_generated": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": {},
    }


def cohort(n: int = 2):
    proofs = [proof(i) for i in range(1, n + 1)]
    authorities = [authority(i, p) for i, p in enumerate(proofs, 1)]
    return proofs, authorities


def rehash_authority(envelope):
    keys = (
        "schema",
        "raw_node_result_packet_digest",
        "source_bound_model_call_identity_sha256",
        "model_output_identity_sha256",
        "abi_v2_receipt_sha256",
        "source_identity_sha256",
        "launch_descriptor_sha256",
        "executor_observation_sha256",
        "cohort_plan_id",
        "grid_cell_id",
        "controller_observed_node_id",
        "controller_observed_pid",
        "source_node_admission_id",
        "source_node_admission_revision",
        "source_runtime_generation",
        "raw_generation",
        "raw_state_epoch",
        "raw_state_digest",
    )
    envelope["authority_envelope_sha256"] = canonical_sha256(
        {key: envelope.get(key) for key in keys}
    )
    return envelope


def test_valid_pair_and_cohort_cross_binding():
    proofs, authorities = cohort()
    out = validate_cohort_cross_binding(proofs, authorities, expected_member_count=2)
    assert out["member_count"] == 2
    assert len(out["cross_binding_validation_digest"]) == 64
    assert out["canonical_truth"] is False
    assert out["effect_authority"] is False
    assert out["credit_boundary"]["physical_grid10_runtime_credit"] == 0


def test_membership_id_transplant_rejected():
    p = proof(1)
    a = authority(1, p, membership="member-other")
    with pytest.raises(FusionError, match="FUSION_MEMBERSHIP_ADMISSION_ID_MISMATCH"):
        cross_validate_member_pair(p, a)


def test_membership_revision_generation_and_pid_are_cross_bound():
    p = proof(1)
    with pytest.raises(
        FusionError, match="FUSION_MEMBERSHIP_ADMISSION_REVISION_MISMATCH"
    ):
        cross_validate_member_pair(p, authority(1, p, serial=99))

    with pytest.raises(FusionError, match="FUSION_MEMBERSHIP_GENERATION_MISMATCH"):
        cross_validate_member_pair(p, authority(1, p, generation=8))

    changed = deepcopy(authority(1, p))
    changed["controller_observed_pid"] += 1
    rehash_authority(changed)
    with pytest.raises(FusionError, match="FUSION_PROCESS_PID_MISMATCH"):
        cross_validate_member_pair(p, changed)


def test_raw_packet_and_node_are_cross_bound():
    p1 = proof(1)
    p2 = proof(2)
    with pytest.raises(FusionError, match="FUSION_RAW_PACKET_MISMATCH"):
        cross_validate_member_pair(p1, authority(2, p2))

    changed = deepcopy(authority(1, p1))
    changed["controller_observed_node_id"] = "x99"
    rehash_authority(changed)
    with pytest.raises(FusionError, match="FUSION_NODE_ID_MISMATCH"):
        cross_validate_member_pair(p1, changed)


def test_equal_call_content_and_output_allowed_for_independent_invocations():
    proofs, _ = cohort()
    shared_call = h("same-call-content")
    shared_output = h("same-model-output")
    authorities = [
        authority(i, p, call=shared_call, output=shared_output)
        for i, p in enumerate(proofs, 1)
    ]
    out = validate_cohort_cross_binding(proofs, authorities, expected_member_count=2)
    assert out["member_count"] == 2
    assert len({m["source_bound_model_call_identity_sha256"] for m in out["members"]}) == 1


def test_reused_launch_or_executor_observation_remains_invalid_invocation_authority():
    proofs, _ = cohort()
    shared_launch = h("shared-launch")
    authorities = [
        authority(i, p, launch=shared_launch)
        for i, p in enumerate(proofs, 1)
    ]
    with pytest.raises(Exception):
        validate_cohort_cross_binding(proofs, authorities, expected_member_count=2)

    shared_observation = h("shared-observation")
    authorities = [
        authority(i, p, observation=shared_observation)
        for i, p in enumerate(proofs, 1)
    ]
    with pytest.raises(Exception):
        validate_cohort_cross_binding(proofs, authorities, expected_member_count=2)


def test_invalid_pair_fails_before_existing_effect_path_is_called():
    class Fabric:
        called = False

        def atomic_fused_cohort_commit(self, **kwargs):
            self.called = True
            return {"ok": True}

    fabric = Fabric()
    proofs, authorities = cohort()
    authorities[1] = authority(
        2,
        proofs[1],
        membership=proofs[0]["source_membership_id"],
    )
    with pytest.raises(FusionError):
        commit_cross_bound_cohort(
            fabric,
            proof_envelopes=proofs,
            invocation_authority_envelopes=authorities,
            expected_member_count=2,
        )
    assert fabric.called is False


def test_valid_adapter_delegates_exactly_once_to_existing_fused_commit():
    class Fabric:
        n = 0

        def atomic_fused_cohort_commit(self, **kwargs):
            self.n += 1
            assert "envelopes" in kwargs
            return {"ok": True}

    fabric = Fabric()
    proofs, authorities = cohort()
    out = commit_cross_bound_cohort(
        fabric,
        proof_envelopes=proofs,
        invocation_authority_envelopes=authorities,
        expected_member_count=2,
        expected_generation=7,
    )
    assert fabric.n == 1
    assert out["delegated_effect_path"] == "EXISTING_FUSED_FABRIC_ATOMIC_COHORT_COMMIT_ONLY"
    assert out["credit_boundary"]["whole_entityos_runtime_credit"] == 0
