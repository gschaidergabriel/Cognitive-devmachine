import json
import unittest

from audit_together_byom_template_v1 import (
    PROVENANCE_KEY,
    assess_pair,
    attest_config_bytes,
    exact_revision,
    hf_config_url,
)

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
        # Regression/replication of the already-consumed #834 unusual falsifier.
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

    def test_exact_revision_and_url_are_fail_closed(self):
        rev = "a" * 40
        self.assertEqual(rev, exact_revision(rev.upper()))
        self.assertEqual(
            f"https://huggingface.co/Qwen/Qwen2.5-0.5B/resolve/{rev}/config.json",
            hf_config_url("Qwen/Qwen2.5-0.5B", rev),
        )
        with self.assertRaises(ValueError):
            exact_revision("main")
        with self.assertRaises(ValueError):
            hf_config_url("not-owner-name", rev)

    def test_exact_config_bytes_bind_model_revision_and_digest(self):
        rev = "b" * 40
        raw = json.dumps(QWEN25_05B, sort_keys=True).encode("utf-8")
        attested = attest_config_bytes("Qwen/Qwen2.5-0.5B", rev, raw)
        provenance = attested[PROVENANCE_KEY]
        self.assertEqual("Qwen/Qwen2.5-0.5B", provenance["model"])
        self.assertEqual(rev, provenance["revision"])
        self.assertEqual(64, len(provenance["config_sha256"]))

    def test_exact_pair_requires_two_sided_provenance(self):
        rev_a, rev_b = "c" * 40, "d" * 40
        raw = json.dumps(QWEN25_05B, sort_keys=True).encode("utf-8")
        custom = attest_config_bytes("Qwen/Qwen2.5-0.5B", rev_a, raw)
        template = attest_config_bytes("Qwen/Qwen2.5-14B", rev_b, raw)
        out = assess_pair(custom, template)
        self.assertTrue(out["compatible"])
        self.assertEqual(rev_a, out["exact_hf_provenance"]["custom"]["revision"])
        self.assertEqual(rev_b, out["exact_hf_provenance"]["template"]["revision"])
        with self.assertRaises(ValueError):
            assess_pair(custom, QWEN25_05B)

    def test_custom_code_configs_are_rejected(self):
        custom = dict(QWEN25_05B, auto_map={"AutoModelForCausalLM": "remote.Model"})
        out = assess_pair(custom, QWEN25_05B)
        self.assertFalse(out["compatible"])
        self.assertIn("CUSTOM_CODE_REQUIRED", out["reasons"])


if __name__ == "__main__":
    unittest.main()
