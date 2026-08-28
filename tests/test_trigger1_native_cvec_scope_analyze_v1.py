from __future__ import annotations

from copy import deepcopy
import unittest

from tools import trigger1_native_cvec_scope_analyze_v1 as analyzer


def row(mode: str, primary: list[float], downstream: list[float], logits: dict[str, float]) -> dict:
    prompt_tokens = 5
    return {
        "schema": analyzer.ROW,
        "case_id": "case-1",
        "mode": mode,
        "token_scope": {
            "BASELINE": "NO_INTERVENTION",
            "BROADCAST": "ALL_PROMPT_TOKENS",
            "LAST_TOKEN_ONLY": "LAST_TOKEN_DECODE_ONLY",
        }[mode],
        "prompt_tokens": prompt_tokens,
        "prefix_decode_tokens": prompt_tokens - 1,
        "final_decode_tokens": 1,
        "cvec_set_before_prefix": mode == "BROADCAST",
        "cvec_set_after_prefix": mode == "LAST_TOKEN_ONLY",
        "primary_layer_inp": 21,
        "downstream_layer_inp": 24,
        "primary_activation": primary,
        "downstream_activation": downstream,
        "token_logits": logits,
    }


def positive_payload() -> list[dict]:
    return [
        {"schema": analyzer.HEADER, "native_api": "llama_set_adapter_cvec"},
        row("BASELINE", [1.0, 2.0, 3.0], [2.0, 1.0, 0.0], {"A": 1.0, "B": 0.0, "C": -1.0}),
        row("BROADCAST", [1.5, 2.0, 3.0], [2.8, 1.2, 0.0], {"A": 2.0, "B": 0.1, "C": -1.2}),
        row("LAST_TOKEN_ONLY", [1.5, 2.0, 3.0], [2.4, 1.1, 0.0], {"A": 1.6, "B": 0.05, "C": -1.1}),
    ]


class Trigger1NativeCvecScopeAnalyzeTests(unittest.TestCase):
    def test_localized_scope_and_immediate_actuator_parity_pass(self):
        result = analyzer.analyze(positive_payload())
        self.assertTrue(result["pass"], result["failures"])
        self.assertTrue(result["localized_native_scope_pass"])
        self.assertTrue(result["immediate_actuator_equivalence_pass"])
        self.assertFalse(result["broadcast_full_causal_identity_claimed"])
        self.assertTrue(result["downstream_and_behavioral_parity_are_diagnostics_not_assumptions"])
        self.assertNotEqual(
            result["cases"][0]["downstream_effect_relative_difference_diagnostic_only"],
            0.0,
        )

    def test_cvec_before_prefix_invalidates_last_token_only_claim(self):
        payload = positive_payload()
        payload[-1]["cvec_set_before_prefix"] = True
        result = analyzer.analyze(payload)
        self.assertFalse(result["pass"])
        self.assertFalse(result["localized_native_scope_pass"])
        self.assertIn("LOCALIZED_SCOPE_PROOF_FAILED:case-1", result["failures"])

    def test_final_decode_must_contain_exactly_one_token(self):
        payload = positive_payload()
        payload[-1]["final_decode_tokens"] = 2
        result = analyzer.analyze(payload)
        self.assertFalse(result["pass"])
        self.assertIn("LOCALIZED_SCOPE_PROOF_FAILED:case-1", result["failures"])

    def test_immediate_effect_mismatch_fails_parity_but_does_not_invent_downstream_identity(self):
        payload = positive_payload()
        payload[-1]["primary_activation"] = [1.0, 2.5, 3.0]
        result = analyzer.analyze(payload)
        self.assertFalse(result["pass"])
        self.assertFalse(result["immediate_actuator_equivalence_pass"])
        self.assertIn("IMMEDIATE_ACTUATOR_PARITY_FAILED:case-1", result["failures"])
        self.assertFalse(result["broadcast_full_causal_identity_claimed"])

    def test_missing_mode_fails_closed(self):
        payload = positive_payload()[:-1]
        result = analyzer.analyze(payload)
        self.assertFalse(result["pass"])
        self.assertFalse(result["localized_native_scope_pass"])
        self.assertTrue(any(item.startswith("CASE_MODES_MISSING") for item in result["failures"]))

    def test_native_api_must_be_exact(self):
        payload = deepcopy(positive_payload())
        payload[0]["native_api"] = "other"
        result = analyzer.analyze(payload)
        self.assertFalse(result["pass"])
        self.assertIn("NATIVE_API_MISMATCH", result["failures"])


if __name__ == "__main__":
    unittest.main()
