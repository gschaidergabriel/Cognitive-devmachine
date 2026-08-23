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


class UnifiedCognitiveFabricReceiptTests(unittest.TestCase):
    def test_valid_boot_binding_accepts_current_git_sha1_oids(self):
        receipt = base_receipt()
        result = validate_receipt(receipt)
        self.assertTrue(result["ok"])
        self.assertEqual(result["phase"], "BOOT_BINDING")
        self.assertEqual(len(result["source_tree"]), 40)

    def test_exact_identity_expectations_reject_stale_manifest(self):
        receipt = base_receipt()
        with self.assertRaisesRegex(ReceiptError, "STALE_BUNDLED_MANIFEST"):
            validate_receipt(receipt, expected_bundled_manifest_digest=d("0"))

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

    def test_claude_requires_adapter_and_capability_identity(self):
        receipt = base_receipt()
        receipt["inference"]["engine_class"] = "CLAUDE_CODE"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CLAUDE_ADAPTER_VERSION_REQUIRED"):
            validate_receipt(receipt)

        receipt["inference"]["adapter_version"] = "claude-code-adapter/v1"
        redigest(receipt)
        with self.assertRaisesRegex(ReceiptError, "CLAUDE_CAPABILITY_PROFILE_DIGEST_INVALID"):
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
