import copy
import unittest

from validate_unified_cognitive_fabric_receipt_v1 import (
    ReceiptError,
    canonical_digest,
    validate_receipt,
)


def d(ch: str) -> str:
    return ch * 64


def base_receipt():
    receipt = {
        "receipt_type": "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
        "phase": "BOOT_BINDING",
        "source": {
            "commit": "d8ff57c2edc4c9eecde99ce1f9b089702d71b1cf",
            "tree": "8865edd1b1bc0195e5c140a77ff9f4611290c2ee",
            "dirty": False,
            "executor": "ubuntu-isolated-executor",
            "runtime_identity": "ubuntu-24.04:x86_64:test-runtime",
            "started_at": "2026-08-23T03:00:00Z",
            "completed_at": "2026-08-23T03:00:01Z",
        },
        "entity": {
            "mini_entity_version": "mini-entity/0.7.0-dev1",
            "entityos_version": "entityos/source-candidate",
            "generation": 277,
        },
        "zero": {
            "identity_digest": d("1"),
            "grf_digest": d("2"),
            "workspace_policy_digest": d("3"),
        },
        "bundled_cognition": {
            "manifest_digest": d("4"),
            "checkpoint_digest": d("5"),
            "tokenizer_digest": d("6"),
            "jspace_profile_digest": d("7"),
            "lens_profile_digest": d("8"),
            "workspace_calibration_digest": d("9"),
            "runtime_identity": "qwen35-08b:q4km:llama.cpp-candidate",
        },
        "workspace": {
            "before_digest": d("a"),
            "after_digest": d("b"),
            "gwt_candidates": [
                {"candidate_ref": "candidate:local:0", "admitted": True, "winner": True},
                {"candidate_ref": "candidate:counter:1", "admitted": True, "winner": False},
            ],
            "jspace_observation_refs": ["jspace:obs:0"],
            "thalamus_decisions": ["gate:admit:local"],
            "hyperposition_refs": ["hp:0"],
            "claycode_refs": ["clay:0"],
            "omega_refs": [],
            "epq_digest": d("c"),
        },
        "inference": {
            "engine_class": "LOCAL_08B",
            "executed": True,
            "jspace_mode": "FULL_LOCAL_LATENT",
            "local_activation_access": True,
            "external_hidden_state_claimed": False,
            "jspace_intervention": {
                "executed": False,
                "implementation_digest": None,
                "calibration_digest": None,
            },
            "packet_digest": d("d"),
            "candidate_result_digest": d("e"),
            "candidate_only": True,
            "epistemic_status": "MEASURED_SUPPORTED",
        },
        "validation": {
            "decision": "ACCEPTED_CANDIDATE",
            "reconciliation_digest": d("f"),
            "candidate_attempted_direct_state_mutation": False,
            "candidate_attempted_direct_effect": False,
            "canonical_write": True,
            "effect_requested": False,
            "effect_admitted": False,
        },
        "authority": {
            "model_is_truth_authority": False,
            "model_is_effect_authority": False,
            "workspace_stability_is_factual_truth": False,
        },
        "boundary": {
            "free_only": True,
            "cost_class": "LOCAL",
            "backend_admitted": True,
            "policy_authority_digest": d("a"),
            "secret_lookup_count": 0,
            "network_attempt_count": 0,
            "first_action_origin": "zero:inference_scheduler",
        },
        "terminal": {
            "status": "DONE",
            "terminal_digest": d("0"),
        },
    }
    receipt["terminal"]["terminal_digest"] = canonical_digest(receipt)
    return receipt


def redigest(receipt):
    receipt["terminal"]["terminal_digest"] = d("0")
    receipt["terminal"]["terminal_digest"] = canonical_digest(receipt)
    return receipt


def block_backend(receipt, cost_class="SUBSCRIPTION"):
    receipt["boundary"]["cost_class"] = cost_class
    receipt["boundary"]["backend_admitted"] = False
    receipt["inference"]["executed"] = False
    receipt["inference"]["candidate_result_digest"] = None
    receipt["inference"]["epistemic_status"] = "NOT_APPLICABLE"
    receipt["validation"]["decision"] = "BLOCKED"
    receipt["validation"]["canonical_write"] = False
    receipt["terminal"]["status"] = "BLOCKED"
    return receipt


class UnifiedCognitiveFabricReceiptTests(unittest.TestCase):
    def test_valid_boot_binding_accepts_current_git_sha1_oids(self):
        receipt = base_receipt()
        result = validate_receipt(receipt)
        self.assertTrue(result["ok"])
        self.assertEqual(result["phase"], "BOOT_BINDING")
        self.assertEqual(len(result["source_tree"]), 40)
        self.assertEqual(result["epistemic_status"], "MEASURED_SUPPORTED")
        self.assertEqual(result["jspace_mode"], "FULL_LOCAL_LATENT")
        self.assertTrue(result["backend_admitted"])

    def test_exact_identity_expectations_reject_stale_manifest(self):
        receipt = base_receipt()
        with self.assertRaisesRegex(ReceiptError, "STALE_BUNDLED_MANIFEST"):
            validate_receipt(receipt, expected_bundled_manifest_digest=d("0"))

    def test_free_only_nonfree_backend_must_be_blocked_before_secret_and_network(self):
        receipt = base_receipt()
        receipt["boundary"]["cost_class"] = "SUBSCRIPTION"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "FREE_ONLY_NONFREE_BACKEND_ADMITTED"):
            validate_receipt(receipt)

        for key, error in (
            ("secret_lookup_count", "FREE_ONLY_SECRET_TOUCH"),
            ("network_attempt_count", "FREE_ONLY_NETWORK_TOUCH"),
        ):
            with self.subTest(key=key):
                receipt = block_backend(base_receipt())
                receipt["boundary"][key] = 1
                redigest(receipt)
                with self.assertRaisesRegex(ReceiptError, error):
                    validate_receipt(receipt)

        receipt = block_backend(base_receipt())
        redigest(receipt)
        self.assertTrue(validate_receipt(receipt)["ok"])

    def test_free_backend_may_use_network_under_free_only(self):
        receipt = base_receipt()
        receipt["boundary"]["cost_class"] = "FREE"
        receipt["boundary"]["network_attempt_count"] = 1
        redigest(receipt)
        self.assertTrue(validate_receipt(receipt)["ok"])

    def test_inference_cannot_execute_without_backend_admission(self):
        receipt = base_receipt()
        receipt["boundary"]["backend_admitted"] = False
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "INFERENCE_EXECUTED_WITHOUT_BACKEND_ADMISSION"):
            validate_receipt(receipt)

    def test_model_and_workspace_cannot_mint_authority(self):
        for key in (
            "model_is_truth_authority",
            "model_is_effect_authority",
            "workspace_stability_is_factual_truth",
        ):
            with self.subTest(key=key):
                receipt = base_receipt()
                receipt["authority"][key] = True
                redigest(receipt)
                with self.assertRaisesRegex(ReceiptError, "AUTHORITY_VIOLATION"):
                    validate_receipt(receipt)

    def test_candidate_only_is_mandatory(self):
        receipt = base_receipt()
        receipt["inference"]["candidate_only"] = False
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "MODEL_RESULT_NOT_CANDIDATE_ONLY"):
            validate_receipt(receipt)

    def test_epistemic_status_required_for_learned_inference(self):
        receipt = base_receipt()
        receipt["inference"].pop("epistemic_status")
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "EPISTEMIC_STATUS_REQUIRED"):
            validate_receipt(receipt)

    def test_nonexecuted_inference_cannot_carry_result_or_epistemic_credit(self):
        receipt = base_receipt()
        receipt["inference"]["executed"] = False
        receipt["boundary"]["backend_admitted"] = False
        receipt["validation"]["canonical_write"] = False
        receipt["validation"]["decision"] = "BLOCKED"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "NONEXECUTED_INFERENCE_RESULT_DIGEST_MUST_BE_NULL"):
            validate_receipt(receipt)

    def test_claude_must_be_compiled_external_without_hidden_state_claim(self):
        receipt = base_receipt()
        receipt["inference"].update(
            {
                "engine_class": "CLAUDE_CODE",
                "jspace_mode": "FULL_LOCAL_LATENT",
                "local_activation_access": True,
                "adapter_version": "claude-code-adapter/v1",
                "capability_profile_digest": d("1"),
            }
        )
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CLAUDE_JSPACE_MODE_MUST_BE_COMPILED_EXTERNAL"):
            validate_receipt(receipt)

        receipt["inference"]["jspace_mode"] = "COMPILED_EXTERNAL"
        receipt["inference"]["local_activation_access"] = False
        receipt["inference"]["external_hidden_state_claimed"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN"):
            validate_receipt(receipt)

    def test_jspace_intervention_requires_latent_access_and_bound_calibration(self):
        receipt = base_receipt()
        receipt["inference"]["jspace_mode"] = "LOCAL_OBSERVE_ONLY"
        receipt["inference"]["jspace_intervention"]["executed"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "JSPACE_INTERVENTION_REQUIRES_FULL_LOCAL_LATENT"):
            validate_receipt(receipt)

        receipt = base_receipt()
        receipt["inference"]["jspace_intervention"]["executed"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "JSPACE_INTERVENTION_IMPLEMENTATION_DIGEST_REQUIRED"):
            validate_receipt(receipt)

        receipt["inference"]["jspace_intervention"]["implementation_digest"] = d("1")
        receipt["inference"]["jspace_intervention"]["calibration_digest"] = d("2")
        redigest(receipt)
        self.assertTrue(validate_receipt(receipt)["ok"])

    def test_gwt_cannot_have_two_winners(self):
        receipt = base_receipt()
        receipt["workspace"]["gwt_candidates"][1]["winner"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "GWT_MULTIPLE_WINNERS"):
            validate_receipt(receipt)

    def test_direct_candidate_authority_attempt_cannot_be_accepted(self):
        receipt = base_receipt()
        receipt["validation"]["candidate_attempted_direct_state_mutation"] = True
        receipt["validation"]["canonical_write"] = False
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "DIRECT_AUTHORITY_ATTEMPT_ACCEPTED"):
            validate_receipt(receipt)

        receipt = base_receipt()
        receipt["validation"]["candidate_attempted_direct_effect"] = True
        receipt["validation"]["effect_requested"] = True
        receipt["validation"]["effect_admitted"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "DIRECT_EFFECT_BYPASS"):
            validate_receipt(receipt)

    def test_canonical_write_requires_accepted_candidate(self):
        receipt = base_receipt()
        receipt["validation"]["decision"] = "REJECTED"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CANONICAL_WRITE_WITHOUT_ACCEPTED_CANDIDATE"):
            validate_receipt(receipt)

    def test_effect_admission_requires_effect_request(self):
        receipt = base_receipt()
        receipt["validation"]["effect_admitted"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "EFFECT_ADMITTED_WITHOUT_REQUEST"):
            validate_receipt(receipt)

    def test_workspace_stability_does_not_upgrade_refuted_candidate(self):
        # Regression-only fusion of the already-consumed
        # WORKSPACE_STABILITY_TRUTH_CONFUSION_MUTATION intervention from #1046.
        baseline = base_receipt()
        receipt = copy.deepcopy(baseline)
        receipt["inference"]["epistemic_status"] = "REFUTED"
        self.assertEqual(receipt["workspace"], baseline["workspace"])
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "UNSUPPORTED_EPISTEMIC_AUTHORITY"):
            validate_receipt(receipt)

    def test_effect_authority_requires_measured_supported_epistemic_status(self):
        receipt = base_receipt()
        receipt["validation"]["effect_requested"] = True
        receipt["validation"]["effect_admitted"] = True
        receipt["validation"]["canonical_write"] = False
        receipt["inference"]["epistemic_status"] = "UNKNOWN"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "UNSUPPORTED_EPISTEMIC_AUTHORITY"):
            validate_receipt(receipt)

    def test_deterministic_only_requires_no_model_execution_or_backend_admission(self):
        receipt = base_receipt()
        receipt["inference"]["engine_class"] = "DETERMINISTIC_ONLY"
        receipt["inference"]["jspace_mode"] = "NONE"
        receipt["inference"]["local_activation_access"] = False
        receipt["inference"]["candidate_result_digest"] = None
        receipt["inference"]["epistemic_status"] = "NOT_APPLICABLE"
        receipt["validation"]["decision"] = "NO_INFERENCE"
        receipt["validation"]["canonical_write"] = False
        receipt["boundary"]["backend_admitted"] = False
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "DETERMINISTIC_ONLY_MUST_NOT_EXECUTE_MODEL"):
            validate_receipt(receipt)

        receipt["inference"]["executed"] = False
        redigest(receipt)
        self.assertTrue(validate_receipt(receipt)["ok"])

    def test_terminal_digest_detects_post_receipt_mutation(self):
        receipt = base_receipt()
        receipt["boundary"]["first_action_origin"] = "tampered"
        with self.assertRaisesRegex(ReceiptError, "TERMINAL_DIGEST_MISMATCH"):
            validate_receipt(receipt)

    def test_nonfinite_json_is_rejected_before_digest_logic(self):
        receipt = base_receipt()
        receipt["telemetry"] = {"score": float("nan")}
        with self.assertRaisesRegex(ReceiptError, "NONFINITE_JSON"):
            validate_receipt(receipt, verify_terminal_digest=False)


if __name__ == "__main__":
    unittest.main()
