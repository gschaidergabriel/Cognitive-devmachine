from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "trigger1_native_llamacpp_cvec_scope_transport.cpp"


class NativeCvecScopeTransportSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SOURCE.read_text(encoding="utf-8")

    def _split_block(self) -> str:
        start = self.text.index("if (scope == SCOPE_LAST) {")
        end = self.text.index("} else {", start)
        return self.text[start:end]

    def test_uses_pinned_staging_layer_input_api_surface(self) -> None:
        self.assertIn('#include "llama-ext.h"', self.text)
        self.assertIn("llama_set_embeddings_layer_inp", self.text)
        self.assertIn("llama_get_embeddings_layer_inp", self.text)

    def test_split_prefix_precedes_tap_enable_and_cvec_enable(self) -> None:
        block = self._split_block()
        prefix = block.index("prefix_rc = llama_decode(ctx, prefix);")
        tap = block.index("llama_set_embeddings_layer_inp")
        cvec = block.index("llama_set_adapter_cvec")
        final = block.index("final_rc = llama_decode(ctx, final_batch);")
        self.assertLess(prefix, tap)
        self.assertLess(prefix, cvec)
        self.assertLess(tap, final)
        self.assertLess(cvec, final)

    def test_split_final_decode_is_exactly_one_token(self) -> None:
        block = self._split_block()
        self.assertIn("current_decode_tokens = 1;", block)
        self.assertIn("llama_batch final_batch = llama_batch_get_one(&tokens.back(), 1);", block)

    def test_tap_index_is_fail_closed_and_duplicates_are_rejected(self) -> None:
        self.assertIn("TAP_INDEX_OUT_OF_RANGE", self.text)
        self.assertIn("DUPLICATE_TAP_INDEX", self.text)
        self.assertIn("NONEMPTY_TAP_LIST_REQUIRED", self.text)

    def test_raw_tap_file_name_does_not_use_untrusted_case_id(self) -> None:
        start = self.text.index("static std::string tap_path")
        end = self.text.index("static void write_row", start)
        block = self.text[start:end]
        self.assertNotIn("case_id", block)
        self.assertIn("line_no", block)
        self.assertIn("lid", block)

    def test_native_harness_does_not_contain_semantic_probe_or_rank_adjudication(self) -> None:
        lowered = self.text.lower()
        for forbidden in (
            "semantic_probe",
            "probe_score",
            "svd",
            "singular_value",
            "rank_threshold",
            "promotion_pass",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_split_extracts_row_zero_and_all_scope_extracts_final_prompt_row(self) -> None:
        self.assertIn("const size_t row = scope == SCOPE_LAST ? 0 : (tokens.size() - 1);", self.text)

    def test_raw_activation_width_is_exact_model_embedding_width(self) -> None:
        self.assertIn("write_row(path, selected, n_embd);", self.text)
        self.assertIn('\\"float_count\\":" << n_embd', self.text)
        self.assertIn("static_cast<size_t>(n_embd) * sizeof(float)", self.text)


if __name__ == "__main__":
    unittest.main()
