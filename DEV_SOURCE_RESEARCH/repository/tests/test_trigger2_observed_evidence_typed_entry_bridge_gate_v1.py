import copy
import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_observed_evidence_typed_entry_bridge_gate_v1.py"
spec = importlib.util.spec_from_file_location("obs_bridge", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

POLICY = {
    "policy_id": "T2_OBSERVED_TYPED_ENTRY_BRIDGE_V1",
    "policy_version": "1",
    "observation_receipt_schema": gate.OBSERVATION_RECEIPT_SCHEMA,
    "instance_envelope_schema": gate.ENVELOPE_SCHEMA,
    "subject_schema": gate.SUBJECT_SCHEMA,
    "fail_closed_if_witness_unlisted": True,
    "canonical_truth_allowed": False,
    "direct_effect_authority": False,
}


@dataclass(frozen=True)
class Packet:
    event_sha256: str
    admission_sha256: str


class FakeEntryFabric:
    ENTRY_SCHEMA = "XENO_ENTRY_PACKET/v1"
    ENTRY_EVENT_IDENTITY_SCHEMA = "ENTITYOS_HCU_ENTRY_EVENT_IDENTITY/v3"
    ENTRY_ADMISSION_IDENTITY_SCHEMA = "ENTITYOS_HCU_ENTRY_ADMISSION_IDENTITY/v3"

    @staticmethod
    def canonicalize(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

    @staticmethod
    def admit_entry(
        entry,
        *,
        current_generation,
        expected_capability_binding_sha256,
        admitted_capabilities,
        admitted_budget,
    ):
        if entry["entity_generation"] != current_generation:
            raise ValueError("STALE_ENTITY_GENERATION")
        if entry["capability_binding_sha256"] != expected_capability_binding_sha256:
            raise ValueError("CAPABILITY_BINDING_MISMATCH")
        if not set(entry["capabilities"]).issubset(set(admitted_capabilities)):
            raise ValueError("CAPABILITY_NOT_ADMITTED")
        for key, value in entry["budget"].items():
            if value > admitted_budget[key]:
                raise ValueError("BUDGET_NOT_ADMITTED")
        event_payload = {
            key: entry[key]
            for key in (
                "causal_id", "source_kind", "source_id", "modality", "observed_time",
                "provenance_ref", "provenance_sha256", "parent_id", "stream_id", "payload_sha256",
            )
        }
        event_sha = hashlib.sha256(FakeEntryFabric.canonicalize(event_payload)).hexdigest()
        admission_payload = {
            "event_sha256": event_sha,
            "entity_generation": entry["entity_generation"],
            "ingress_id": entry["ingress_id"],
            "received_time": entry["received_time"],
            "capabilities": sorted(entry["capabilities"]),
            "capability_binding_sha256": entry["capability_binding_sha256"],
            "budget": entry["budget"],
            "payload_ref": entry["payload_ref"],
        }
        admission_sha = hashlib.sha256(FakeEntryFabric.canonicalize(admission_payload)).hexdigest()
        return Packet(event_sha, admission_sha)


def trusted_entry(causal="causal:e1", ingress="ingress:1", generation=3, payload_sha="b" * 64):
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": ingress,
        "causal_id": causal,
        "entity_generation": generation,
        "source_kind": "TOOL_OUTCOME",
        "source_id": "tool:fixture",
        "modality": "JSON",
        "observed_time": "2026-08-25T00:00:00Z",
        "received_time": "2026-08-25T00:00:01Z",
        "provenance_ref": "admission:fixture",
        "provenance_sha256": "a" * 64,
        "capabilities": [],
        "capability_binding_sha256": "c" * 64,
        "parent_id": None,
        "stream_id": None,
        "budget": {"max_model_calls": 0, "max_tokens": 0, "max_wall_ms": 0},
        "payload_ref": "payload:fixture",
        "payload_sha256": payload_sha,
    }


def make_witness(event_id="e1", witness_id="w1", receipt_id="r1", replay="replay1", entry=None):
    entry = copy.deepcopy(entry or trusted_entry())
    admission_authority = {
        "current_generation": entry["entity_generation"],
        "expected_capability_binding_sha256": entry["capability_binding_sha256"],
        "admitted_capabilities": [],
        "admitted_budget": {"max_model_calls": 0, "max_tokens": 0, "max_wall_ms": 0},
    }
    packet = FakeEntryFabric.admit_entry(entry, **admission_authority)
    return {
        "schema": gate.WITNESS_SCHEMA,
        "status": "CURRENT",
        "event_id": event_id,
        "event_semantic_sha256": "9" * 64,
        "producer_id": "entry-fabric-v1",
        "producer_epoch": "1",
        "entry": entry,
        "admission_authority": admission_authority,
        "expected_entry_event_sha256": packet.event_sha256,
        "expected_entry_admission_sha256": packet.admission_sha256,
        "receipt_id": receipt_id,
        "replay_identity": replay,
        "legacy_receipt_source": "tool:fixture",
        "legacy_receipt_provenance": "admission:fixture",
    }


def authority(witnesses):
    return {
        "schema": gate.AUTHORITY_SCHEMA,
        "status": "SOURCE_AUTHORITY_CANDIDATE_NONPROMOTING",
        "policy": copy.deepcopy(POLICY),
        "policy_canonical_json_sha256": gate._canonical_json_sha256(POLICY),
        "entry_fabric_producer": {
            "producer_id": "entry-fabric-v1",
            "producer_epoch": "1",
            "status": "CURRENT",
            "repo_path": "the artefact/MicroEntity/hcu/xeno_entry_fabric_v1.py",
            "source_git_blob_sha": "1" * 40,
            "entry_schema": "XENO_ENTRY_PACKET/v1",
            "entry_event_identity_schema": "ENTITYOS_HCU_ENTRY_EVENT_IDENTITY/v3",
            "entry_admission_identity_schema": "ENTITYOS_HCU_ENTRY_ADMISSION_IDENTITY/v3",
            "source_lineage": {
                "repository": gate.EXPECTED_REPOSITORY,
                "branch": gate.EXPECTED_BRANCH,
                "source_commit_sha": "2" * 40,
                "source_path": "the artefact/MicroEntity/hcu/xeno_entry_fabric_v1.py",
            },
        },
        "admission_witnesses": witnesses,
        "authority_fences": {
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "training_eligible": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
            "runtime_credit_minted": 0,
            "jspace_runtime_credit_minted": 0,
            "hcu_runtime_credit_minted": 0,
            "entityos_runtime_credit_minted": 0,
        },
    }


def event(event_id="e1", epistemic="OBSERVED"):
    return {"event_id": event_id, "epistemic_type": epistemic}


def bound_transport(witness_id, witness):
    packet = FakeEntryFabric.admit_entry(witness["entry"], **witness["admission_authority"])
    producer = authority({witness_id: witness})["entry_fabric_producer"]
    policy_digest = gate._canonical_json_sha256(POLICY)
    subject = gate._trusted_witness_subject(
        witness_id=witness_id,
        witness=witness,
        packet=packet,
        producer=producer,
        policy_digest=policy_digest,
    )
    subject_sha = hashlib.sha256(FakeEntryFabric.canonicalize(subject)).hexdigest()
    entry = witness["entry"]
    exact = {
        "event_id": witness["event_id"],
        "event_semantic_sha256": witness["event_semantic_sha256"],
        "causal_id": entry["causal_id"],
        "ingress_id": entry["ingress_id"],
        "entity_generation": entry["entity_generation"],
        "source_kind": entry["source_kind"],
        "source_id": entry["source_id"],
        "observed_time": entry["observed_time"],
        "provenance_ref": entry["provenance_ref"],
        "provenance_sha256": entry["provenance_sha256"],
        "payload_ref": entry["payload_ref"],
        "payload_sha256": entry["payload_sha256"],
        "entry_event_sha256": packet.event_sha256,
        "entry_admission_sha256": packet.admission_sha256,
        "admission_witness_sha256": subject_sha,
        "policy_digest": policy_digest,
        "receipt_id": witness["receipt_id"],
        "replay_identity": witness["replay_identity"],
        "source": witness["legacy_receipt_source"],
        "provenance": witness["legacy_receipt_provenance"],
        "admission_witness_id": witness_id,
        "producer_id": producer["producer_id"],
        "producer_epoch": producer["producer_epoch"],
        "producer_source_git_blob_sha": producer["source_git_blob_sha"],
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    receipt = dict(exact)
    receipt["schema"] = gate.OBSERVATION_RECEIPT_SCHEMA
    envelope = dict(exact)
    envelope["schema"] = gate.ENVELOPE_SCHEMA
    return receipt, envelope


def run(row, auth):
    with patch.object(gate, "_load_authority", return_value=auth), patch.object(
        gate, "_verify_entry_fabric_source", return_value=([], {"fixture": True})
    ), patch.object(gate, "_load_entry_fabric", return_value=FakeEntryFabric):
        return gate.adjudicate(row)


def row_for(receipt, envelope, event_id="e1"):
    return {
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": event(event_id),
        "typed_observation_evidence_receipts_evaluator_only": [receipt],
        "typed_observation_admission_envelopes_evaluator_only": [envelope],
    }


def test_non_observed_is_neutral_zero_credit():
    result = gate.adjudicate({
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": event("s1", "SYNTHETIC_PROOF"),
    })
    assert result["pass"] is True and result["observed_event_count"] == 0
    assert result["training_credit_minted"] == 0 and result["canonical_truth_minted"] is False


def test_unlisted_witness_rejects_forged_legacy_receipt():
    witness = make_witness()
    receipt, envelope = bound_transport("w1", witness)
    result = run(row_for(receipt, envelope), authority({}))
    assert result["pass"] is False
    assert any("WITNESS_NOT_ADMITTED" in item for item in result["failures"])


def test_exact_independent_witness_can_pass_component_only():
    witness = make_witness()
    receipt, envelope = bound_transport("w1", witness)
    result = run(row_for(receipt, envelope), authority({"w1": witness}))
    assert result["pass"] is True and result["authenticated_observed_event_count"] == 1
    assert result["canonical_dataset_admission"] is False and result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0 and result["observation_truth_decided"] is False


def test_coherent_candidate_entry_receipt_comutation_cannot_self_authenticate():
    original = make_witness()
    forged = make_witness(
        entry=trusted_entry(causal="causal:attacker", ingress="ingress:attacker", payload_sha="e" * 64)
    )
    forged_receipt, forged_envelope = bound_transport("attacker-witness", forged)
    result = run(row_for(forged_receipt, forged_envelope), authority({"w1": original}))
    assert result["pass"] is False
    assert any("WITNESS_NOT_ADMITTED" in item for item in result["failures"])


def test_binding_mutation_matrix_rejects():
    witness = make_witness()
    receipt, envelope = bound_transport("w1", witness)
    auth = authority({"w1": witness})
    mutations = {
        "entry_admission_sha256": "f" * 64,
        "entry_event_sha256": "f" * 64,
        "ingress_id": "ingress:swap",
        "entity_generation": 4,
        "payload_sha256": "e" * 64,
        "provenance_sha256": "e" * 64,
        "admission_witness_sha256": "e" * 64,
        "event_semantic_sha256": "e" * 64,
        "receipt_id": "other",
        "replay_identity": "other",
    }
    for field, value in mutations.items():
        bad = copy.deepcopy(receipt)
        bad[field] = value
        result = run(row_for(bad, envelope), auth)
        assert result["pass"] is False, field


def test_stale_or_mutated_trusted_witness_recomputation_rejects():
    witness = make_witness()
    receipt, envelope = bound_transport("w1", witness)
    bad = copy.deepcopy(witness)
    bad["entry"]["entity_generation"] = 4
    result = run(row_for(receipt, envelope), authority({"w1": bad}))
    assert result["pass"] is False
    assert any("TRUSTED_WITNESS_RECOMPUTE_FAILED" in item for item in result["failures"])


def test_truth_effect_and_producer_substitution_reject():
    witness = make_witness()
    receipt, envelope = bound_transport("w1", witness)
    auth = authority({"w1": witness})
    receipt["canonical_truth_allowed"] = True
    envelope["direct_effect_authority"] = True
    receipt["producer_id"] = "attacker"
    result = run(row_for(receipt, envelope), auth)
    assert result["pass"] is False
    assert any("CANNOT_MINT_CANONICAL_TRUTH" in item for item in result["failures"])
    assert any("CANNOT_MINT_DIRECT_EFFECT_AUTHORITY" in item for item in result["failures"])
    assert any("PRODUCER_ID_MISMATCH" in item for item in result["failures"])


def test_same_replay_identity_different_subject_rejects():
    witness1 = make_witness("e1", "w1", "r1", "same")
    witness2 = make_witness(
        "e2", "w2", "r2", "same", trusted_entry(causal="causal:e2", ingress="ingress:2")
    )
    witness2["event_semantic_sha256"] = "8" * 64
    receipt1, envelope1 = bound_transport("w1", witness1)
    receipt2, envelope2 = bound_transport("w2", witness2)
    row = {
        "synthetic_event_history_evaluator_only": [event("e1")],
        "synthetic_test_event_evaluator_only": event("e2"),
        "typed_observation_evidence_receipts_evaluator_only": [receipt1, receipt2],
        "typed_observation_admission_envelopes_evaluator_only": [envelope1, envelope2],
    }
    result = run(row, authority({"w1": witness1, "w2": witness2}))
    assert result["pass"] is False
    assert any("REPLAY_ID_REUSED_DIFFERENT_SUBJECT" in item for item in result["failures"])
