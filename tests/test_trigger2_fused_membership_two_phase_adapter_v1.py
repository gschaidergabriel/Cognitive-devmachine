from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from tools.trigger2_fused_membership_two_phase_adapter_v1 import (
    AdapterError,
    EXTENSIONS_SCHEMA,
    PROOF_ENVELOPE_SCHEMA,
    attach_two_phase_authority,
    atomic_fused_two_phase_commit,
    dg,
    validate_two_phase_cohort,
    validate_two_phase_proof_envelope,
)
from tools.trigger2_node_result_model_call_two_phase_authority_v1 import SCHEMA as PHASE_SCHEMA, canonical_sha256


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def raw_packet(i: int) -> dict:
    packet = {
        "schema": "NODE_RESULT/v1",
        "source_kind": "ORDINARY_NODE",
        "source_node_id": f"x{i:02d}",
        "scope": "GLOBAL",
        "generation": 7,
        "state_epoch": 11,
        "state_digest": h("state"),
        "producer_pid": 8000 + i,
        "payload": {"process_pid": 8000 + i, "value": f"obs-{i}"},
        "s1_write_intent": False,
    }
    core = {k: packet[k] for k in packet if k not in ("packet_digest", "s1_write_intent")}
    packet["packet_digest"] = dg(core)
    return packet


def proof_envelope(i: int) -> dict:
    packet = raw_packet(i)
    core = {
        "schema": PROOF_ENVELOPE_SCHEMA,
        "node_result_digest": packet["packet_digest"],
        "node_result": packet,
        "source_membership_id": f"member-{i:02d}",
        "membership_receipt": {
            "membership_id": f"member-{i:02d}",
            "node_id": f"x{i:02d}",
            "capability": "reason",
            "generation": 7,
            "serial": i,
            "valid": 1,
            "healthy": 1,
        },
        "producer_pid": 8000 + i,
    }
    return {**core, "envelope_digest": dg(core)}


def phase_authority(i: int, *, call_id: str | None = None, output_id: str | None = None) -> dict:
    packet = raw_packet(i)
    body = {
        "schema": PHASE_SCHEMA,
        "raw_node_result_packet_digest": packet["packet_digest"],
        "source_bound_model_call_identity_sha256": call_id or h(f"call-{i}"),
        "model_output_identity_sha256": output_id or h(f"output-{i}"),
        "abi_v2_receipt_sha256": h(f"abi-{i}"),
        "source_identity_sha256": h("source"),
        "launch_descriptor_sha256": h(f"launch-{i}"),
        "executor_observation_sha256": h(f"executor-observation-{i}"),
        "cohort_plan_id": h("plan"),
        "grid_cell_id": f"cell-{i:02d}",
        "controller_observed_node_id": f"x{i:02d}",
        "controller_observed_pid": 8000 + i,
        "source_node_admission_id": f"member-{i:02d}",
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
        "credit_boundary": {},
    }


def upgraded(i: int, **phase_kwargs) -> dict:
    return attach_two_phase_authority(proof_envelope(i), phase_authority(i, **phase_kwargs))


def reseal_proof(envelope: dict) -> dict:
    out = deepcopy(envelope)
    core = {k: out[k] for k in out if k != "envelope_digest"}
    out["envelope_digest"] = dg(core)
    return out


def reseal_phase(phase: dict) -> dict:
    out = deepcopy(phase)
    body = {k: out[k] for k in out if k not in (
        "authority_envelope_sha256", "model_generated", "canonical_truth", "effect_authority", "credit_boundary"
    )}
    out["authority_envelope_sha256"] = canonical_sha256(body)
    return out


def test_positive_upgrade_preserves_raw_packet_and_validates_ten_member_cohort():
    bases = [proof_envelope(i) for i in range(1, 11)]
    before_packets = [deepcopy(item["node_result"]) for item in bases]
    values = [attach_two_phase_authority(base, phase_authority(i)) for i, base in enumerate(bases, 1)]
    result = validate_two_phase_cohort(values)
    assert result["pass"] is True
    assert result["member_count"] == 10
    assert [item["node_result"] for item in values] == before_packets
    assert all(item["authority_extensions"]["schema"] == EXTENSIONS_SCHEMA for item in values)


def test_call_content_and_output_may_repeat_across_distinct_invocations():
    shared_call = h("same-call-content")
    shared_output = h("same-output")
    values = [upgraded(i, call_id=shared_call, output_id=shared_output) for i in range(1, 11)]
    assert validate_two_phase_cohort(values)["pass"] is True


def test_phase_admission_id_must_match_membership_receipt():
    base = proof_envelope(1)
    phase = phase_authority(1)
    phase["source_node_admission_id"] = "member-other"
    phase = reseal_phase(phase)
    with pytest.raises(AdapterError, match="^TWO_PHASE_ADMISSION_MEMBERSHIP_ID_MISMATCH$"):
        attach_two_phase_authority(base, phase)


def test_phase_admission_revision_must_match_membership_serial():
    base = proof_envelope(1)
    phase = phase_authority(1)
    phase["source_node_admission_revision"] = 99
    phase = reseal_phase(phase)
    with pytest.raises(AdapterError, match="^TWO_PHASE_ADMISSION_MEMBERSHIP_REVISION_MISMATCH$"):
        attach_two_phase_authority(base, phase)


def test_membership_receipt_node_and_generation_are_cross_validated():
    base = proof_envelope(1)
    base["membership_receipt"]["node_id"] = "x99"
    base = reseal_proof(base)
    with pytest.raises(AdapterError, match="^MEMBERSHIP_RECEIPT_NODE_MISMATCH$"):
        attach_two_phase_authority(base, phase_authority(1))

    base = proof_envelope(1)
    base["membership_receipt"]["generation"] = 8
    base = reseal_proof(base)
    with pytest.raises(AdapterError, match="^MEMBERSHIP_RECEIPT_PACKET_GENERATION_MISMATCH$"):
        attach_two_phase_authority(base, phase_authority(1))


def test_phase_packet_reference_transplant_is_rejected():
    with pytest.raises(AdapterError, match="^TWO_PHASE_RAW_PACKET_BINDING_MISMATCH$"):
        attach_two_phase_authority(proof_envelope(1), phase_authority(2))


def test_extension_tamper_without_reseal_is_rejected():
    value = upgraded(1)
    value["authority_extensions"]["two_phase_model_call_authority"]["grid_cell_id"] = "cell-99"
    with pytest.raises(AdapterError, match="^PROOF_ENVELOPE_DIGEST_MISMATCH$"):
        validate_two_phase_proof_envelope(value)


def test_one_membership_incarnation_projected_onto_two_nodes_rejects_whole_cohort():
    values = [upgraded(i) for i in range(1, 11)]
    phase = deepcopy(values[1]["authority_extensions"]["two_phase_model_call_authority"])
    phase["source_node_admission_id"] = "member-01"
    phase = reseal_phase(phase)
    values[1]["authority_extensions"]["two_phase_model_call_authority"] = phase
    values[1] = reseal_proof(values[1])
    with pytest.raises(AdapterError, match="^TWO_PHASE_ADMISSION_MEMBERSHIP_ID_MISMATCH$"):
        validate_two_phase_cohort(values)


def test_transport_order_does_not_change_validation_digest():
    values = [upgraded(i) for i in range(1, 11)]
    forward = validate_two_phase_cohort(values)
    reverse = validate_two_phase_cohort(list(reversed(values)))
    assert forward["validation_digest_sha256"] == reverse["validation_digest_sha256"]
    assert forward["phase_authority_cohort_validation_sha256"] == reverse["phase_authority_cohort_validation_sha256"]


def test_wrapper_validates_before_delegating_to_existing_fused_coordinator():
    values = [upgraded(i) for i in range(1, 11)]

    class FakeFabric:
        def __init__(self):
            self.calls = 0
            self.seen = None
        def atomic_fused_cohort_commit(self, *, envelopes, marker):
            self.calls += 1
            self.seen = envelopes
            return {"cohort_id": "existing-fused-authority", "marker": marker}

    fake = FakeFabric()
    out = atomic_fused_two_phase_commit(fake, envelopes=values, marker="ok")
    assert fake.calls == 1
    assert fake.seen == values
    assert out["fused_coordinator_receipt"]["cohort_id"] == "existing-fused-authority"
    assert out["adapter_created_second_coordinator_cohort_id"] is False

    bad = deepcopy(values)
    bad[0]["envelope_digest"] = "0" * 64
    fake2 = FakeFabric()
    with pytest.raises(AdapterError, match="^PROOF_ENVELOPE_DIGEST_MISMATCH$"):
        atomic_fused_two_phase_commit(fake2, envelopes=bad, marker="no")
    assert fake2.calls == 0
