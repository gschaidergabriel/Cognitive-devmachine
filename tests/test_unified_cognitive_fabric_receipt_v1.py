import copy
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
    receipt = {
        "schema": ucf.SCHEMA,
        "source": {
            "commit": "86dcc1fec8add7888773aea0425be3931b5a78f9",
            "tree": "f630df18c405bbf5567327e02b0eeb66d3f4e737",
            "dirty": False,
        },
        "runtime": {
            "mini_entity_version": "mini-entity/ucf-source-candidate",
            "entityos_version": "entityos/offline-source-candidate",
            "generation": 276,
        },
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
            "boot_binding_receipt_digest": G,
        },
        "workspace": {
            "before_digest": L,
            "after_digest": M,
            "gwt_candidates": ["slot:grf", "slot:hyper"],
            "gwt_winners": ["slot:grf"],
            "jspace_observation_refs": ["j:layer:12"],
            "thalamus_gate_decisions": ["admit:slot:grf", "suppress:slot:hyper"],
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
            "jspace_intervention": {
                "executed": False,
                "implementation_digest": None,
                "calibration_digest": None,
            },
            "adapter_version": "bundled-08b-candidate-v1",
            "capability_profile_digest": H,
            "adapter_contract_digest": I,
            "inference_packet_digest": D,
            "candidate_result_digest": E,
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
            "terminal_result_digest": F,
        },
        "freshness": {
            "stale_zero_identity": False,
            "stale_bundled_manifest": False,
            "stale_generation": False,
        },
        "receipt_envelope_digest": "0" * 64,
    }
    receipt["receipt_envelope_digest"] = ucf.canonical_digest(receipt)
    return receipt


def redigest(receipt):
    receipt["receipt_envelope_digest"] = "0" * 64
    receipt["receipt_envelope_digest"] = ucf.canonical_digest(receipt)
    return receipt


def blocked_nonfree(receipt, cost_class="SUBSCRIPTION"):
    receipt["inference"].update(
        engine_class="claude_code",
        executed=False,
        jspace_mode="COMPILED_EXTERNAL",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        adapter_version="claude-code-adapter/v1",
        candidate_result_digest=None,
        epistemic_status="NOT_APPLICABLE",
    )
    receipt["authority"].update(
        validation_decision="BLOCKED",
        canonical_write_committed=False,
        effect_committed=False,
    )
    receipt["execution"].update(lane_cost_class=cost_class, lane_admitted=False)
    return receipt


class ReceiptV1Tests(unittest.TestCase):
    def test_valid_local_08b_receipt(self):
        self.assertTrue(ucf.validate(valid_receipt())["ok"])

    def test_git_sha256_oid_shape_is_admitted(self):
        r = valid_receipt()
        r["source"]["commit"] = "a" * 64
        r["source"]["tree"] = "b" * 64
        redigest(r)
        self.assertTrue(ucf.validate(r)["ok"])

    def test_candidate_authority_smuggle_is_rejected(self):
        r = valid_receipt()
        r["authority"]["candidate_requested_direct_state_mutation"] = True
        with self.assertRaisesRegex(ucf.ReceiptError, "CANDIDATE_AUTHORITY_SMUGGLE"):
            ucf.validate(r)

    def test_stale_zero_binding_is_rejected(self):
        r = valid_receipt()
        r["binding"]["zero_identity_digest"] = "9" * 64
        with self.assertRaisesRegex(ucf.ReceiptError, "STALE_ZERO_IDENTITY_BINDING"):
            ucf.validate(r)

    def test_stale_generation_blocks_admission_execution_and_acceptance(self):
        r = valid_receipt()
        r["freshness"]["stale_generation"] = True
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "STALE_INPUT_AUTHORITY_OR_EXECUTION"):
            ucf.validate(r)

    def test_claude_capability_mismatch_is_rejected(self):
        r = blocked_nonfree(valid_receipt())
        r["inference"]["adapter_capability_match"] = False
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "CLAUDE_ADAPTER_CAPABILITY_MISMATCH"):
            ucf.validate(r)

    def test_claude_must_be_compiled_external_without_hidden_state_claim(self):
        r = valid_receipt()
        r["inference"].update(
            engine_class="claude_code",
            jspace_mode="FULL_LOCAL_LATENT",
            local_activation_access=True,
            adapter_version="claude-code-adapter/v1",
        )
        r["execution"]["lane_cost_class"] = "FREE"
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "CLAUDE_MUST_BE_COMPILED_EXTERNAL"):
            ucf.validate(r)

        r["inference"].update(
            jspace_mode="COMPILED_EXTERNAL",
            local_activation_access=False,
            external_hidden_state_claimed=True,
        )
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN"):
            ucf.validate(r)

    def test_local_jspace_requires_lens_profile(self):
        r = valid_receipt()
        r["bundled_core"]["lens_profile_digest"] = None
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "LOCAL_JSPACE_REQUIRES_LENS_PROFILE"):
            ucf.validate(r)

    def test_full_local_latent_requires_activation_access(self):
        r = valid_receipt()
        r["inference"]["jspace_mode"] = "FULL_LOCAL_LATENT"
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "FULL_LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS"):
            ucf.validate(r)

    def test_jspace_intervention_requires_execution_latent_access_and_calibration(self):
        r = valid_receipt()
        r["inference"].update(
            jspace_mode="LOCAL_OBSERVE_ONLY",
            local_activation_access=False,
        )
        r["inference"]["jspace_intervention"]["executed"] = True
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "INTERVENTION_REQUIRES_FULL_LOCAL_LATENT"):
            ucf.validate(r)

        r = valid_receipt()
        r["inference"].update(jspace_mode="FULL_LOCAL_LATENT", local_activation_access=True)
        r["inference"]["jspace_intervention"]["executed"] = True
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "implementation_digest:TEXT_REQUIRED"):
            ucf.validate(r)

        r["inference"]["jspace_intervention"]["implementation_digest"] = D
        r["inference"]["jspace_intervention"]["calibration_digest"] = E
        redigest(r)
        self.assertTrue(ucf.validate(r)["ok"])

    def test_nonexecuted_inference_carries_no_result_or_epistemic_credit(self):
        r = valid_receipt()
        r["inference"]["executed"] = False
        r["execution"]["lane_admitted"] = False
        r["authority"].update(validation_decision="BLOCKED", canonical_write_committed=False)
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "NONEXECUTED_INFERENCE_RESULT_DIGEST_MUST_BE_NULL"):
            ucf.validate(r)

    def test_workspace_stability_truth_confusion_regression(self):
        # Regression-only fusion of the already consumed go intervention.
        base = valid_receipt()
        r = copy.deepcopy(base)
        r["inference"]["epistemic_status"] = "REFUTED"
        self.assertEqual(r["workspace"], base["workspace"])
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "UNSUPPORTED_EPISTEMIC_AUTHORITY"):
            ucf.validate(r)

    def test_unknown_candidate_cannot_authorize_effect(self):
        r = valid_receipt()
        r["inference"]["epistemic_status"] = "UNKNOWN"
        r["authority"].update(canonical_write_committed=False, effect_committed=True)
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "UNSUPPORTED_EPISTEMIC_AUTHORITY"):
            ucf.validate(r)

    def test_free_only_nonfree_lane_is_presecret_prenetwork_and_unadmitted(self):
        r = blocked_nonfree(valid_receipt())
        redigest(r)
        self.assertTrue(ucf.validate(r)["ok"])

        r = valid_receipt()
        r["execution"]["lane_cost_class"] = "SUBSCRIPTION"
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "FREE_ONLY_NONFREE_LANE_ADMITTED"):
            ucf.validate(r)

        for key, error in (("secret_lookup_count", "FREE_ONLY_SECRET_TOUCH"), ("network_touch_count", "FREE_ONLY_NETWORK_TOUCH")):
            with self.subTest(key=key):
                r = blocked_nonfree(valid_receipt())
                r["execution"][key] = 1
                redigest(r)
                with self.assertRaisesRegex(ucf.ReceiptError, error):
                    ucf.validate(r)

    def test_free_only_does_not_blanket_forbid_admitted_free_network(self):
        r = valid_receipt()
        r["execution"].update(lane_cost_class="FREE", network_touch_count=1)
        redigest(r)
        self.assertTrue(ucf.validate(r)["ok"])

    def test_inference_cannot_execute_without_lane_admission(self):
        r = valid_receipt()
        r["execution"]["lane_admitted"] = False
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "INFERENCE_EXECUTED_WITHOUT_LANE_ADMISSION"):
            ucf.validate(r)

    def test_gwt_winner_must_have_competed_and_be_unique(self):
        r = valid_receipt()
        r["workspace"]["gwt_winners"] = ["slot:never-offered"]
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "GWT_WINNER_NOT_CANDIDATE"):
            ucf.validate(r)

        r = valid_receipt()
        r["workspace"]["gwt_winners"] = ["slot:grf", "slot:hyper"]
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "GWT_MULTIPLE_WINNERS"):
            ucf.validate(r)

    def test_boot_binding_receipt_digest_is_required(self):
        r = valid_receipt()
        r["binding"].pop("boot_binding_receipt_digest")
        redigest(r)
        with self.assertRaisesRegex(ucf.ReceiptError, "boot_binding_receipt_digest:TEXT_REQUIRED"):
            ucf.validate(r)

    def test_envelope_digest_detects_post_receipt_mutation(self):
        r = valid_receipt()
        r["workspace"]["thalamus_gate_decisions"] = ["tampered"]
        with self.assertRaisesRegex(ucf.ReceiptError, "RECEIPT_ENVELOPE_DIGEST_MISMATCH"):
            ucf.validate(r)

    def test_nonfinite_json_is_rejected(self):
        r = valid_receipt()
        r["telemetry"] = {"score": float("nan")}
        with self.assertRaisesRegex(ucf.ReceiptError, "NONFINITE_JSON"):
            ucf.validate(r)


if __name__ == "__main__":
    unittest.main()
