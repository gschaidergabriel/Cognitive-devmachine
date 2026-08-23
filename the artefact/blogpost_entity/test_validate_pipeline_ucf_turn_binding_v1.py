import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "turn", ROOT / "validate_pipeline_ucf_turn_binding_v1.py"
)
turn = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(turn)
ucf = turn.UCF

D = "1" * 64
E = "2" * 64
F = "3" * 64
G = "4" * 64
H = "5" * 64
I = "6" * 64
J = "7" * 64
K = "8" * 64
L = "9" * 64
M = "a" * 64
N = "b" * 64
O = "c" * 64
P = "d" * 64
Q = "e" * 64


def valid_ucf(inference_packet_digest: str):
    r = {
        "schema": ucf.SCHEMA,
        "source": {"commit": "1234567890abcdef1234567890abcdef12345678", "tree": "abcdef1234567890abcdef1234567890abcdef12", "dirty": False},
        "runtime": {"mini_entity_version": "mini-entity/candidate", "entityos_version": "entityos/candidate", "generation": 41},
        "identity": {"zero_identity_digest": D, "grf_digest": E},
        "bundled_core": {
            "manifest_digest": F,
            "checkpoint_digest": G,
            "tokenizer_digest": H,
            "jspace_profile_digest": I,
            "lens_profile_digest": J,
            "workspace_calibration_digest": K,
        },
        "binding": {
            "zero_identity_digest": D,
            "grf_digest": E,
            "bundled_manifest_digest": F,
            "boot_binding_receipt_digest": L,
        },
        "workspace": {
            "before_digest": M,
            "after_digest": N,
            "gwt_candidates": ["slot:grf", "slot:hyper"],
            "gwt_winners": ["slot:grf"],
            "jspace_observation_refs": ["j:layer:12"],
            "thalamus_gate_decisions": ["admit:slot:grf"],
            "epq_ref": "epq:1",
            "hyperposition_ref": "hp:1",
            "claycode_ref": "clay:1",
            "omega_ref": "omega:1",
        },
        "inference": {
            "engine_class": "local_08b",
            "executed": True,
            "jspace_mode": "LOCAL_OBSERVE_ONLY",
            "local_activation_access": False,
            "external_hidden_state_claimed": False,
            "jspace_intervention": {"executed": False, "implementation_digest": None, "calibration_digest": None},
            "adapter_version": "bundled-08b/v1",
            "capability_profile_digest": O,
            "adapter_contract_digest": P,
            "inference_packet_digest": inference_packet_digest,
            "candidate_result_digest": Q,
            "epistemic_status": "MEASURED_SUPPORTED",
            "candidate_only": True,
            "adapter_capability_match": True,
            "provider_observability_claim_supported": True,
        },
        "authority": {
            "candidate_requested_direct_state_mutation": False,
            "candidate_requested_direct_effect_mutation": False,
            "validation_decision": "ACCEPT",
            "canonical_write_committed": True,
            "effect_committed": False,
        },
        "execution": {
            "free_only": True,
            "lane_cost_class": "LOCAL",
            "lane_admitted": True,
            "policy_authority_digest": J,
            "secret_lookup_count": 0,
            "network_touch_count": 0,
            "terminal_result_digest": K,
        },
        "freshness": {"stale_zero_identity": False, "stale_bundled_manifest": False, "stale_generation": False},
        "receipt_envelope_digest": "0" * 64,
    }
    r["receipt_envelope_digest"] = ucf.canonical_digest(r)
    return r


def valid_binding():
    packet = {
        "schema": turn.PACKET_SCHEMA,
        "generation": 41,
        "profile_snapshot_digest": H,
        "canonical_state_hash": I,
        "packet_hash": J,
        "boot_binding_receipt_digest": L,
        "engine_selection_digest": M,
    }
    packet_digest = turn.canonical_digest(packet)
    ucf_receipt = valid_ucf(packet_digest)
    ucf_digest = ucf_receipt["receipt_envelope_digest"]
    b = {
        "schema": turn.SCHEMA,
        "source": {"commit": ucf_receipt["source"]["commit"], "dirty": False},
        "pipeline": {
            "state_authority": "MiniUnifiedDB",
            "generation_before": 41,
            "profile_snapshot_digest": H,
            "canonical_state_hash": I,
            "packet_hash": J,
        },
        "inference_packet": packet,
        "ucf_receipt": ucf_receipt,
        "gate": {"decision": "ACCEPT", "candidate_result_digest": Q, "ucf_receipt_digest": ucf_digest},
        "commit": {
            "committed": True,
            "generation_after": 42,
            "output_id": "out-1",
            "packet_hash": J,
            "canonical_state_hash": I,
            "ucf_receipt_digest": ucf_digest,
        },
        "binding_envelope_digest": "0" * 64,
    }
    b["binding_envelope_digest"] = turn.canonical_digest(b, omit_key="binding_envelope_digest")
    return b


def redigest(binding):
    binding["binding_envelope_digest"] = "0" * 64
    binding["binding_envelope_digest"] = turn.canonical_digest(binding, omit_key="binding_envelope_digest")
    return binding


class TurnBindingTests(unittest.TestCase):
    def test_valid_committed_turn(self):
        self.assertTrue(turn.validate(valid_binding())["ok"])

    def test_packet_profile_snapshot_must_match_pipeline(self):
        b = valid_binding()
        b["inference_packet"]["profile_snapshot_digest"] = N
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "INFERENCE_PACKET_PROFILE_MISMATCH"):
            turn.validate(b)

    def test_ucf_packet_digest_must_match_exact_packet(self):
        b = valid_binding()
        b["inference_packet"]["engine_selection_digest"] = N
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "UCF_INFERENCE_PACKET_DIGEST_MISMATCH"):
            turn.validate(b)

    def test_ucf_generation_must_match_pipeline_generation(self):
        b = valid_binding()
        b["ucf_receipt"]["runtime"]["generation"] = 40
        b["ucf_receipt"]["receipt_envelope_digest"] = ucf.canonical_digest(b["ucf_receipt"])
        b["gate"]["ucf_receipt_digest"] = b["ucf_receipt"]["receipt_envelope_digest"]
        b["commit"]["ucf_receipt_digest"] = b["ucf_receipt"]["receipt_envelope_digest"]
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "UCF_GENERATION_MISMATCH"):
            turn.validate(b)

    def test_boot_binding_must_match_packet(self):
        b = valid_binding()
        b["ucf_receipt"]["binding"]["boot_binding_receipt_digest"] = N
        b["ucf_receipt"]["receipt_envelope_digest"] = ucf.canonical_digest(b["ucf_receipt"])
        b["gate"]["ucf_receipt_digest"] = b["ucf_receipt"]["receipt_envelope_digest"]
        b["commit"]["ucf_receipt_digest"] = b["ucf_receipt"]["receipt_envelope_digest"]
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "UCF_BOOT_BINDING_MISMATCH"):
            turn.validate(b)

    def test_gate_candidate_digest_must_match_ucf(self):
        b = valid_binding()
        b["gate"]["candidate_result_digest"] = N
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "GATE_CANDIDATE_DIGEST_MISMATCH"):
            turn.validate(b)

    def test_accept_requires_exactly_once_commit_generation(self):
        b = valid_binding()
        b["commit"]["generation_after"] = 43
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "PIPELINE_GENERATION_NOT_EXACTLY_ONCE"):
            turn.validate(b)

    def test_accept_requires_pipeline_commit(self):
        b = valid_binding()
        b["commit"].update(committed=False, generation_after=None, output_id=None, packet_hash=None, canonical_state_hash=None, ucf_receipt_digest=None)
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "ACCEPT_WITHOUT_PIPELINE_COMMIT"):
            turn.validate(b)

    def test_nonaccept_must_not_commit(self):
        b = valid_binding()
        b["ucf_receipt"]["authority"].update(validation_decision="REJECT", canonical_write_committed=False)
        b["ucf_receipt"]["receipt_envelope_digest"] = ucf.canonical_digest(b["ucf_receipt"])
        b["gate"].update(decision="REJECT", ucf_receipt_digest=b["ucf_receipt"]["receipt_envelope_digest"])
        b["commit"]["ucf_receipt_digest"] = b["ucf_receipt"]["receipt_envelope_digest"]
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "NONACCEPT_PIPELINE_COMMIT_FORBIDDEN"):
            turn.validate(b)

    def test_ucf_source_commit_must_match_pipeline_source(self):
        b = valid_binding()
        b["source"]["commit"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "UCF_SOURCE_COMMIT_MISMATCH"):
            turn.validate(b)

    def test_commit_packet_hash_must_match_turn(self):
        b = valid_binding()
        b["commit"]["packet_hash"] = N
        redigest(b)
        with self.assertRaisesRegex(turn.TurnBindingError, "COMMIT_PACKET_HASH_MISMATCH"):
            turn.validate(b)

    def test_binding_envelope_detects_posthoc_mutation(self):
        b = valid_binding()
        b["commit"]["output_id"] = "mutated-after-receipt"
        with self.assertRaisesRegex(turn.TurnBindingError, "BINDING_ENVELOPE_DIGEST_MISMATCH"):
            turn.validate(b)


if __name__ == "__main__":
    unittest.main()
