from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "tools" / "trigger1_local_qwen06_intermediate_contrastive_execute.py"


def load_with_stubs():
    protocol = types.ModuleType("trigger1_intermediate_contrastive_protocol")
    protocol.REQUIRED_CONTROLS = (
        "BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR",
        "ORTHOGONAL_SAME_NORM", "PERMUTED_SAME_NORM",
    )
    protocol.CREDIT_SCOPE = "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY"
    sys.modules["trigger1_intermediate_contrastive_protocol"] = protocol
    base = types.ModuleType("trigger1_local_qwen06_activation_api_execute")
    base.MODEL_ID = "Qwen/Qwen3-0.6B"
    base.MODEL_REVISION = "exact-revision"
    sys.modules["trigger1_local_qwen06_activation_api_execute"] = base
    spec = importlib.util.spec_from_file_location("trigger1_intermediate_executor_test_module", EXECUTOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Layers:
    def __init__(self, n: int):
        self.layers = [object() for _ in range(n)]


class Model:
    def __init__(self, n: int):
        self.model = Layers(n)


class Tokenizer:
    def encode(self, text: str, add_special_tokens: bool = False):
        return {"A": [11], "B": [12], " A": [21], " B": [22]}.get(text, [1, 2])


class IntermediateExecutorSourceTests(unittest.TestCase):
    def setUp(self):
        self.m = load_with_stubs()

    def test_candidate_layers_are_intermediate_and_separated(self):
        self.assertEqual((7, 14, 21), self.m.candidate_layers(Model(28)))
        self.assertTrue(all(0 < x < 27 for x in self.m.candidate_layers(Model(28))))

    def test_ab_tokens_are_distinct_singletons(self):
        self.assertEqual({"A": 11, "B": 12}, self.m.resolve_ab_token_ids(Tokenizer()))

    def test_label_remap_changes_output_identity_not_semantic_pole(self):
        a = self.m.prompt_for("5 + 6 = 11.", "A_POS")
        b = self.m.prompt_for("5 + 6 = 11.", "B_POS")
        self.assertIn("true output only A", a)
        self.assertIn("false output only B", a)
        self.assertIn("true output only B", b)
        self.assertIn("false output only A", b)

    def test_source_has_no_terminal_readout_vector_construction(self):
        source = EXECUTOR.read_text(encoding="utf-8")
        self.assertNotIn("get_output_embeddings", source)
        self.assertNotIn("model.model.norm.register_forward_hook", source)
        self.assertIn("protocol.contrastive_direction", source)
        self.assertIn("wrong_layer_delta", source)
        self.assertIn("lesion_delta", source)
        self.assertIn("rescue_delta", source)
        self.assertIn("holdout_used_for_direction_or_layer_gain_selection", source)


if __name__ == "__main__":
    unittest.main()
