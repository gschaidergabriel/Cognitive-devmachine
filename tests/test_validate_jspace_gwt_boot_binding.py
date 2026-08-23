import unittest

from tools.validate_jspace_gwt_boot_binding import REQUIRED_BINDINGS, validate


def d(ch: str) -> str:
    return ch * 64


def baseline_receipt():
    expected = {key: d(hex((i % 15) + 1)[2:]) for i, key in enumerate(REQUIRED_BINDINGS)}
    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {
            "commit": "a" * 40,
            "tree": "b" * 40,
            "dirty": False,
        },
        "executor": {
            "os": "Ubuntu 24.04",
            "machine_id_digest": d("c"),
            "runner_identity_digest": d("d"),
        },
        "prestart_frozen_baseline": {
            "generation": 276,
            "agentzero_export_head": "e" * 40,
            "receipt_source_short": "bd016bba7",
        },
        "expected_binding": expected,
        "observed_binding": dict(expected),
        "poststart_observation": {
            "first_generation": 277,
            "first_inference_engine_choice": "BUNDLED_08B",
            "first_actions": [
                {"action_id": "a1", "origin": "ZERO", "effect_requested": False},
                {"action_id": "a2", "origin": "HOOK_TIMER", "effect_requested": False},
            ],
        },
        "credits": {
            "binding_identity_credit": "BOUND_OBSERVATION_ONLY",
            "bundled_08b_exact_runtime_credit": 0,
            "jspace_runtime_credit": 0,
            "whole_gwt_production_credit": 0,
            "claude_code_adapter_runtime_credit": 0,
            "canonical_semantics_credit": 0,
        },
        "claim_class": "SOURCE_BOUND_BOOT_OBSERVATION_ONLY",
    }


class BootBindingTests(unittest.TestCase):
    def test_valid_receipt(self):
        self.assertEqual(validate(baseline_receipt()), [])

    def test_digest_alias_poison_tokenizer_fails_closed(self):
        receipt = baseline_receipt()
        receipt["observed_binding"]["tokenizer_digest"] = d("f")
        self.assertIn("BINDING_MISMATCH:tokenizer_digest", validate(receipt))

    def test_workspace_policy_alias_poison_fails_closed(self):
        receipt = baseline_receipt()
        receipt["observed_binding"]["workspace_policy_digest"] = d("f")
        self.assertIn("BINDING_MISMATCH:workspace_policy_digest", validate(receipt))

    def test_missing_lens_presence_mismatch_fails_closed(self):
        receipt = baseline_receipt()
        receipt["expected_binding"]["lens_profile_digest"] = d("1")
        self.assertIn(
            "OPTIONAL_BINDING_PRESENCE_MISMATCH:lens_profile_digest",
            validate(receipt),
        )

    def test_dirty_source_requires_diff_digest(self):
        receipt = baseline_receipt()
        receipt["source"]["dirty"] = True
        self.assertIn("DIRTY_SOURCE_DIFF_DIGEST_REQUIRED", validate(receipt))

    def test_boot_receipt_cannot_grant_runtime_credit(self):
        receipt = baseline_receipt()
        receipt["credits"]["jspace_runtime_credit"] = 1
        self.assertIn(
            "BOOT_BINDING_CANNOT_GRANT_CREDIT:jspace_runtime_credit",
            validate(receipt),
        )

    def test_unknown_origin_fails_closed(self):
        receipt = baseline_receipt()
        receipt["poststart_observation"]["first_actions"][0]["origin"] = "MODEL_GUESSED"
        self.assertIn("ACTION_0_ORIGIN_INVALID", validate(receipt))

    def test_extra_observed_binding_fails_closed(self):
        receipt = baseline_receipt()
        receipt["observed_binding"]["mystery_profile_digest"] = d("2")
        errors = validate(receipt)
        self.assertTrue(any(e.startswith("UNEXPECTED_OBSERVED_BINDINGS:") for e in errors))

    def test_bool_generation_not_accepted_as_int(self):
        receipt = baseline_receipt()
        receipt["poststart_observation"]["first_generation"] = True
        self.assertIn("POSTSTART_FIRST_GENERATION_INVALID", validate(receipt))


if __name__ == "__main__":
    unittest.main()
