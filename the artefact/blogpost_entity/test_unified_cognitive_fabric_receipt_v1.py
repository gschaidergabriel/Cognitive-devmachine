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
            "commit": "7028a6f66ac0d61a09487f09caf1b2df417325f4",
            "tree": "8865edd1b1bc0195e5c140a77ff9f4611290c2ee",
            "dirty": False,
            "executor": "ubuntu-isolated-executor",
            "runtime_identity": "ubuntu-24.04:x86_64:test-runtime",
            "environment_digest": d("0"),
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
            "runtime_identity": "qwen35-08b:q4km:hookable-runtime-candidate",
        },
        "calibration": {
            "status": "BOUND_EXACT",
            "architecture_portable": True,
            "geometry_portable": False,
            "checkpoint_digest": d("5"),
            "tokenizer_digest": d("6"),
            "runtime_identity": "qwen35-08b:q4km:hookable-runtime-candidate",
            "lens_profile_digest": d("8"),
            "workspace_calibration_digest": d("9"),
            "workspace_band_measured": False,
            "causal_intervention_measured": False,
            "multi_token_ood_checked": False,
            "simpler_baseline_compared": False,
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
            "packet_digest": d("d"),
            "candidate_result_digest": d("e"),
            "candidate_only": True,
        },
        "validation": {
            "decision": "ACCEPTED_CANDIDATE",
            "reconciliation_digest": d("f"),
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
            "secret_lookup_count": 0,
            "network_attempt_count": 0,
            "first_action_origin": "zero:inference_scheduler",
        },
        "terminal": {"status": "DONE", "terminal_digest": d("0")},
    }
    return redigest(receipt)


def redigest(receipt):
    receipt["terminal"]["terminal_digest"] = d("0")
    receipt["terminal"]["terminal_digest"] = canonical_digest(receipt)
    return receipt


def measured_local_cycle():
    receipt = base_receipt()
    receipt["phase"] = "INFERENCE_CYCLE"
    receipt["calibration"]["status"] = "MEASURED_EXACT"
    for key in (
        "workspace_band_measured",
        "causal_intervention_measured",
        "multi_token_ood_checked",
        "simpler_baseline_compared",
    ):
        receipt["calibration"][key] = True
    return redigest(receipt)


class UnifiedCognitiveFabricReceiptTests(unittest.TestCase):
    def test_boot_binding_accepts_exact_bound_but_not_yet_measured_geometry(self):
        result = validate_receipt(base_receipt())
        self.assertTrue(result["ok"])
        self.assertEqual(result["phase"], "BOOT_BINDING")
        self.assertEqual(result["calibration_status"], "BOUND_EXACT")
        self.assertEqual(len(result["source_tree"]), 40)

    def test_local_jspace_inference_requires_measured_exact_calibration(self):
        receipt = base_receipt()
        receipt["phase"] = "INFERENCE_CYCLE"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "LOCAL_JSPACE_REQUIRES_MEASURED_EXACT_CALIBRATION"):
            validate_receipt(receipt)

        result = validate_receipt(measured_local_cycle())
        self.assertTrue(result["ok"])
        self.assertEqual(result["calibration_status"], "MEASURED_EXACT")

    def test_measured_exact_requires_full_calibration_evidence(self):
        receipt = measured_local_cycle()
        receipt["calibration"]["multi_token_ood_checked"] = False
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "MEASURED_EXACT_WITH_INCOMPLETE_EVIDENCE"):
            validate_receipt(receipt)

    def test_cross_checkpoint_geometry_reuse_is_rejected(self):
        receipt = base_receipt()
        receipt["calibration"]["checkpoint_digest"] = d("a")
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CALIBRATION_CHECKPOINT_MISMATCH"):
            validate_receipt(receipt)

    def test_cross_runtime_geometry_reuse_is_rejected(self):
        receipt = base_receipt()
        receipt["calibration"]["runtime_identity"] = "different-runtime"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CALIBRATION_RUNTIME_MISMATCH"):
            validate_receipt(receipt)

    def test_portable_architecture_does_not_mean_portable_geometry(self):
        receipt = base_receipt()
        receipt["calibration"]["geometry_portable"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "PORTABLE_GEOMETRY_FORBIDDEN"):
            validate_receipt(receipt)

    def test_claude_is_compiled_external_only(self):
        receipt = base_receipt()
        receipt["inference"].update(
            {
                "engine_class": "CLAUDE_CODE",
                "adapter_version": "claude-code-adapter/v1",
                "capability_profile_digest": d("a"),
                "jspace_mode": "FULL_LOCAL_LATENT",
            }
        )
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CLAUDE_JSPACE_MODE_MUST_BE_COMPILED_EXTERNAL"):
            validate_receipt(receipt)

        receipt["inference"]["jspace_mode"] = "COMPILED_EXTERNAL"
        redigest(receipt)
        self.assertTrue(validate_receipt(receipt)["ok"])

    def test_stale_manifest_expectation_is_rejected(self):
        with self.assertRaisesRegex(ReceiptError, "STALE_BUNDLED_MANIFEST"):
            validate_receipt(base_receipt(), expected_bundled_manifest_digest=d("0"))

    def test_free_only_rejects_secret_or_network_touch(self):
        for key in ("secret_lookup_count", "network_attempt_count"):
            with self.subTest(key=key):
                receipt = base_receipt()
                receipt["boundary"][key] = 1
                redigest(receipt)
                with self.assertRaisesRegex(ReceiptError, "FREE_ONLY_EXTERNAL_TOUCH"):
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

    def test_gwt_cannot_have_two_winners(self):
        receipt = base_receipt()
        receipt["workspace"]["gwt_candidates"][1]["winner"] = True
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "GWT_MULTIPLE_WINNERS"):
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
