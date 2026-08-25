from pathlib import Path
import unittest


class TemporalScopeHarnessSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "tools/trigger1_native_llamacpp_temporal_scope.cpp").read_text(encoding="utf-8")

    def test_all_six_scope_arms_are_explicit(self):
        for mode in (
            "BASELINE_SINGLE", "BASELINE_SPLIT", "BROADCAST_SINGLE",
            "BROADCAST_SPLIT", "LAST_TOKEN_ONLY", "PREFIX_ONLY",
        ):
            self.assertIn(f'"{mode}"', self.source)

    def test_prefix_only_clears_with_native_null_data_api(self):
        self.assertIn("llama_set_adapter_cvec(ctx, nullptr, 0, n_embd, il_start, il_end)", self.source)
        self.assertIn('if (mode == "PREFIX_ONLY") clear_rc = clear_cvec();', self.source)

    def test_last_token_only_sets_after_prefix_decode(self):
        prefix = self.source.index("prefix_decode_rc = decode_tokens(ctx, prefix);")
        last_set = self.source.index('if (mode == "LAST_TOKEN_ONLY") set_rc = set_cvec();')
        last_decode = self.source.index("last_decode_rc = decode_tokens(ctx, last);")
        self.assertLess(prefix, last_set)
        self.assertLess(last_set, last_decode)

    def test_broadcast_split_sets_before_prefix_and_remains_for_last(self):
        set_before = self.source.index('if (mode == "BROADCAST_SPLIT" || mode == "PREFIX_ONLY") set_rc = set_cvec();')
        prefix = self.source.index("prefix_decode_rc = decode_tokens(ctx, prefix);")
        last_decode = self.source.index("last_decode_rc = decode_tokens(ctx, last);")
        self.assertLess(set_before, prefix)
        self.assertLess(prefix, last_decode)

    def test_internal_and_behavioral_readouts_are_both_exported(self):
        self.assertIn('downstream_activation', self.source)
        self.assertIn('behavior_target_margin', self.source)
        self.assertIn("llama_get_embeddings_layer_inp", self.source)
        self.assertIn("llama_get_logits_ith(ctx, -1)", self.source)


if __name__ == "__main__":
    unittest.main()
