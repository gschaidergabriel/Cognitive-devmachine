import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ucf", ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py"
)
ucf = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ucf)

D = "a" * 64
E = "b" * 64
F = "c" * 64
G = "d" * 64
H = "e" * 64
I = "f" * 64
J = "1" * 64
K = "2" * 64
L = "3" * 64
M = "4" * 64


def valid_receipt():
    return {
        "schema": ucf.SCHEMA,
        "source": {"commit": "86dcc1fec8add7888773aea0425be3931b5a78f9", "tree": "f630df18c405bbf5567327e02b0eeb66d3f4e737", "dirty": False},
        "runtime": {"mini_entity_version": "mini-entity/ucf-source-candidate", "entityos_version": "entityos/offline-source-candidate", "generation": 276},
        "identity": {"zero_identity_digest": D, "grf_digest": E},
        "bundled_core": {"manifest_digest": F, "checkpoint_digest": G, "tokenizer_digest": H, "jspace_profile_digest": I, "lens_profile_digest": J, "workspace_calibration_digest": K},
        "binding": {"zero_identity_digest": D, "grf_digest": E, "bundled_manifest_digest": F},
        "workspace": {"before_digest": L, "after_digest": M, "gwt_candidates": ["slot:grf", "slot:hyper"], "gwt_winners": ["slot:grf"], "jspace_observation_refs": ["j:layer:12"], "thalamus_gate_decisions": ["admit:slot:grf", "suppress:slot:hyper"], "epq_ref": "epq:1", "hyperposition_ref": "hp:1", "claycode_ref": "clay:1", "omega_ref": "omega:1"},
        "inference": {"engine_class": "local_08b", "inference_packet_digest": D, "candidate_result_digest": E, "candidate_only": True, "adapter_capability_match": True, "provider_observability_claim_supported": True},
        "authority": {"candidate_requested_direct_state_mutation": False, "candidate_requested_direct_effect_mutation": False, "validation_decision": "ACCEPT", "canonical_write_committed": True, "effect_committed": False},
        "execution": {"free_only": True, "lane_cost_class": "LOCAL", "lane_admitted": True, "secret_lookup_count": 0, "network_touch_count": 0, "terminal_result_digest": F},
    }


class ReceiptV1Tests(unittest.TestCase):
    def test_valid_local_08b_receipt(self):
        self.assertTrue(ucf.validate(valid_receipt())["ok"])

    def test_candidate_authority_smuggle_is_rejected(self):
        r = valid_receipt()
        r["authority"]["candidate_requested_direct_state_mutation"] = True
        r["authority"]["candidate_requested_direct_effect_mutation"] = True
        r["authority"]["effect_committed"] = True
        with self.assertRaisesRegex(ucf.ReceiptError, "CANDIDATE_AUTHORITY_SMUGGLE"):
            ucf.validate(r)

    def test_stale_zero_binding_is_rejected(self):
        r = valid_receipt()
        r["binding"]["zero_identity_digest"] = "9" * 64
        with self.assertRaisesRegex(ucf.ReceiptError, "STALE_ZERO_IDENTITY_BINDING"):
            ucf.validate(r)

    def test_claude_capability_mismatch_is_rejected(self):
        r = valid_receipt()
        r["inference"]["engine_class"] = "claude_code"
        r["inference"]["adapter_capability_match"] = False
        r["authority"]["validation_decision"] = "BLOCKED"
        r["authority"]["canonical_write_committed"] = False
        r["execution"]["lane_cost_class"] = "SUBSCRIPTION"
        r["execution"]["lane_admitted"] = False
        with self.assertRaisesRegex(ucf.ReceiptError, "CLAUDE_ADAPTER_CAPABILITY_MISMATCH"):
            ucf.validate(r)

    def test_free_only_nonfree_lane_is_presecret_prenetwork(self):
        r = valid_receipt()
        r["inference"]["engine_class"] = "claude_code"
        r["authority"]["validation_decision"] = "BLOCKED"
        r["authority"]["canonical_write_committed"] = False
        r["execution"]["lane_cost_class"] = "SUBSCRIPTION"
        r["execution"]["lane_admitted"] = False
        r["execution"]["secret_lookup_count"] = 1
        with self.assertRaisesRegex(ucf.ReceiptError, "FREE_ONLY_PRESECRET_PRENETWORK_BREACH"):
            ucf.validate(r)

    def test_gwt_winner_must_have_competed(self):
        r = valid_receipt()
        r["workspace"]["gwt_winners"] = ["slot:never-offered"]
        with self.assertRaisesRegex(ucf.ReceiptError, "GWT_WINNER_NOT_CANDIDATE"):
            ucf.validate(r)


if __name__ == "__main__":
    unittest.main()
