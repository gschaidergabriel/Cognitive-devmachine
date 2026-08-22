import unittest

from audit_together_byom_template_v1 import assess_pair

QWEN25_05B = {
    "architectures": ["Qwen2ForCausalLM"],
    "model_type": "qwen2",
    "max_position_embeddings": 32768,
}
QWEN35_08B = {
    "architectures": ["Qwen3_5ForConditionalGeneration"],
    "model_type": "qwen3_5",
    "text_config": {"max_position_embeddings": 262144, "model_type": "qwen3_5_text"},
}


class ByomStaticCompatibilityTests(unittest.TestCase):
    def test_qwen25_05b_vs_qwen35_08b_is_rejected(self):
        out = assess_pair(QWEN25_05B, QWEN35_08B)
        self.assertFalse(out["compatible"])
        self.assertIn("TEMPLATE_NOT_CAUSAL_LM", out["reasons"])
        self.assertIn("ARCHITECTURE_CLASS_MISMATCH", out["reasons"])
        self.assertIn("MODEL_TYPE_MISMATCH", out["reasons"])

    def test_exact_qwen2_architecture_pair_is_admitted_by_static_gate(self):
        out = assess_pair(QWEN25_05B, dict(QWEN25_05B))
        self.assertTrue(out["compatible"])
        self.assertEqual([], out["reasons"])

    def test_custom_non_causal_lm_is_rejected(self):
        out = assess_pair({"architectures": ["Qwen2Model"], "model_type": "qwen2"}, QWEN25_05B)
        self.assertFalse(out["compatible"])
        self.assertIn("CUSTOM_NOT_CAUSAL_LM", out["reasons"])

    def test_ambiguous_architecture_fails_closed(self):
        with self.assertRaises(ValueError):
            assess_pair({"architectures": ["A", "B"], "model_type": "qwen2"}, QWEN25_05B)


if __name__ == "__main__":
    unittest.main()
