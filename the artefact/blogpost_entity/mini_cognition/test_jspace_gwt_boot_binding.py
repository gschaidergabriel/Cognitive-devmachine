from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from validate_jspace_gwt_boot_binding import ReceiptFault, validate_receipt

H64 = "a" * 64
G40 = "b" * 40


def valid_receipt() -> dict:
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {
            "repository": "gschaidergabriel/clay-global-research-entity",
            "commit_sha": G40,
            "tree_sha": "c" * 40,
            "dirty": False,
            "dirty_state_sha256": None,
        },
        "executor": {"os_name": "Linux", "os_release": "test", "machine": "x86_64", "executor_id": "isolated-fixture"},
        "control": {"free_only": True, "control_version": "4.1+4.2"},
        "prestart": {"generation": 276, "baseline_id": "GEN276_FROZEN"},
        "poststart": {"generation": 277, "checkpoint_id": "boot-277", "observation_boundary_complete": True},
        "bundled_cognition": {
            "engine_id": "bundled-claycog-08b",
            "model_family": "Qwen3.5-0.8B",
            "manifest_sha256": H64,
            "checkpoint_sha256": "1" * 64,
            "tokenizer_sha256": "2" * 64,
            "runtime_identity": "hookable-runtime/v1",
            "runtime_sha256": "3" * 64,
            "jspace_profile": {"state": "PRESENT", "sha256": "4" * 64},
            "lens_profile": {"state": "PRESENT", "sha256": "5" * 64},
            "workspace_calibration_sha256": "6" * 64,
            "steering_calibration": {"state": "ABSENT_UNCALIBRATED", "sha256": None},
            "claycode_contract_version": "v1",
            "grf_contract_version": "R0-R6/v1",
            "hyperposition_contract_version": "v1",
            "compatible_entityos_range": ">=0.1,<0.2",
            "provenance_sha256": "7" * 64,
        },
        "cognitive_fabric": {
            "jspace_mode": "FULL_LOCAL_LATENT",
            "gwt_policy_sha256": "8" * 64,
            "thalamus_policy_sha256": "9" * 64,
            "epq_profile_sha256": "a" * 64,
            "workspace_policy_sha256": "b" * 64,
        },
        "identity_projection": {"zero_identity_sha256": "c" * 64, "grf_projection_sha256": "d" * 64},
        "claude_adapter": {"adapter_version": "candidate-v1", "capability_profile_sha256": "e" * 64, "enabled": False},
        "first_inference": {
            "engine_class": "BUNDLED_LOCAL",
            "engine_id": "bundled-claycog-08b",
            "cost_class": "FREE_LOCAL",
            "capability_receipt_sha256": "f" * 64,
        },
        "first_actions": [
            {"action_id": "a1", "origin": "ZERO", "kind": "workspace_observe", "receipt_sha256": "0" * 64}
        ],
        "first_action_observation_complete": True,
        "credit_boundary": {
            "boot_binding_credit": True,
            "whole_gwt_production_credit": False,
            "model_quality_credit": False,
            "semantic_truth_credit": False,
            "consciousness_credit": False,
            "frank_v01_acceptance_credit": False,
        },
    }


class BootBindingReceiptTests(unittest.TestCase):
    def test_valid_receipt_is_boot_binding_only(self):
        result = validate_receipt(valid_receipt())
        self.assertTrue(result["ok"])
        self.assertEqual(result["credit_scope"], "BOOT_BINDING_ONLY")
        self.assertEqual(result["first_action_count"], 1)

    def test_missing_checkpoint_digest_fails_closed(self):
        receipt = valid_receipt()
        receipt["bundled_cognition"].pop("checkpoint_sha256")
        with self.assertRaisesRegex(ReceiptFault, "checkpoint_sha256"):
            validate_receipt(receipt)

    def test_uncalibrated_profile_must_be_explicit_not_omitted(self):
        receipt = valid_receipt()
        receipt["bundled_cognition"].pop("lens_profile")
        with self.assertRaisesRegex(ReceiptFault, "lens_profile"):
            validate_receipt(receipt)

    def test_uncalibrated_profile_cannot_carry_stale_digest(self):
        receipt = valid_receipt()
        receipt["bundled_cognition"]["lens_profile"] = {"state": "ABSENT_UNCALIBRATED", "sha256": H64}
        with self.assertRaisesRegex(ReceiptFault, "MUST_BE_NULL"):
            validate_receipt(receipt)

    def test_free_only_rejects_paid_first_engine(self):
        receipt = valid_receipt()
        receipt["first_inference"]["engine_class"] = "CLAUDE_CODE"
        receipt["first_inference"]["engine_id"] = "claude-code"
        receipt["first_inference"]["cost_class"] = "SUBSCRIPTION"
        with self.assertRaisesRegex(ReceiptFault, "FREE_ONLY_DENIED"):
            validate_receipt(receipt)

    def test_every_first_action_requires_attributed_origin(self):
        receipt = valid_receipt()
        receipt["first_actions"][0].pop("origin")
        with self.assertRaisesRegex(ReceiptFault, "origin"):
            validate_receipt(receipt)

    def test_secret_named_field_is_rejected_anywhere(self):
        receipt = valid_receipt()
        receipt["claude_adapter"]["api_key"] = "should-not-exist"
        with self.assertRaisesRegex(ReceiptFault, "SECRET_FIELD_FORBIDDEN"):
            validate_receipt(receipt)

    def test_whole_gwt_credit_cannot_be_smuggled_through_receipt(self):
        receipt = valid_receipt()
        receipt["credit_boundary"]["whole_gwt_production_credit"] = True
        with self.assertRaisesRegex(ReceiptFault, "FORBIDDEN_TRUE"):
            validate_receipt(receipt)

    def test_dirty_source_requires_dirty_state_digest(self):
        receipt = valid_receipt()
        receipt["source"]["dirty"] = True
        receipt["source"]["dirty_state_sha256"] = None
        with self.assertRaisesRegex(ReceiptFault, "dirty_state_sha256"):
            validate_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
