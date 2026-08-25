from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "trigger1_native_llamacpp_cvec_scope_logits.cpp"


class NativeCvecScopeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SOURCE.read_text(encoding="utf-8")

    def _last_scope_block(self) -> str:
        marker = "} else {\n                // Strict scope carrier"
        start = self.text.index(marker)
        end = self.text.index("\n            llama_synchronize(ctx);", start)
        return self.text[start:end]

    def test_supported_scope_names_are_versioned_and_explicit(self) -> None:
        self.assertIn('SCOPE_ALL  = "ALL_PROMPT_TOKENS_ONE_SHOT"', self.text)
        self.assertIn('SCOPE_LAST = "LAST_TOKEN_ONLY_SPLIT_PREFILL"', self.text)
        self.assertIn("INTERVENTION_TOKEN_SCOPE_UNSUPPORTED", self.text)

    def test_last_token_scope_decodes_prefix_before_setting_cvec(self) -> None:
        block = self._last_scope_block()
        prefix = block.index("prefix_decode_rc = llama_decode(ctx, prefix_batch);")
        set_cvec = block.index("cvec_rc = set_cvec(ctx, cvec, n_embd, il_start, il_end);")
        final_decode = block.index("final_decode_rc = llama_decode(ctx, final_batch);")
        self.assertLess(prefix, set_cvec)
        self.assertLess(set_cvec, final_decode)

    def test_last_token_scope_final_graph_receives_exactly_one_prompt_token(self) -> None:
        block = self._last_scope_block()
        self.assertIn("final_decode_token_count = 1;", block)
        self.assertIn("llama_batch final_batch = llama_batch_get_one(&tokens.back(), 1);", block)

    def test_last_token_scope_never_marks_prefix_cvec_active(self) -> None:
        block = self._last_scope_block()
        self.assertNotIn("cvec_active_during_prefix = true", block)
        self.assertIn("cvec_active_during_final = true", block)

    def test_split_baseline_uses_identical_partition_without_cvec(self) -> None:
        block = self._last_scope_block()
        # The partition is outside the `has_cvec` conditional: both baseline and
        # intervention decode prefix first and exactly one final token second.
        prefix_if = block.index("if (tokens.size() > 1)")
        cvec_if = block.index("if (has_cvec)")
        final_one = block.index("final_decode_token_count = 1;")
        self.assertLess(prefix_if, cvec_if)
        self.assertLess(cvec_if, final_one)

    def test_observation_binds_scope_partition_and_decode_receipts(self) -> None:
        for required in (
            '"intervention_token_scope"',
            '"decode_partition"',
            '"cvec_active_during_prefix"',
            '"cvec_active_during_final_token"',
            '"prefix_decode_rc"',
            '"final_decode_rc"',
            '"prefix_decode_token_count"',
            '"final_decode_token_count"',
        ):
            self.assertIn(required.replace('"', '\\"'), self.text)


if __name__ == "__main__":
    unittest.main()
