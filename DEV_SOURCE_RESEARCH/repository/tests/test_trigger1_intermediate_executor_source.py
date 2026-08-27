import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "tools" / "trigger1_local_qwen06_intermediate_api_execute.py"


def load_executor():
    spec = importlib.util.spec_from_file_location("trigger1_intermediate", EXECUTOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Trigger1IntermediateExecutorSourceTest(unittest.TestCase):
    def test_nonterminal_contrastive_contract(self):
        m = load_executor()
        self.assertEqual(6, len(m.CONTROLS))
        self.assertEqual(len(m.CONTROLS), len(set(m.CONTROLS)))
        self.assertTrue(all(isinstance(x, int) and 0 <= x < 28 for x in m.CANDIDATE_LAYERS))
        self.assertTrue(set(seed for seed, _ in m.CALIBRATION).isdisjoint(seed for seed, _ in m.HOLDOUT))
        self.assertTrue(set(prompt for _, prompt in m.CALIBRATION).isdisjoint(prompt for _, prompt in m.HOLDOUT))
        self.assertTrue(set(m.POSITIVE_ANCHORS).isdisjoint(m.NEGATIVE_ANCHORS))

        text = EXECUTOR.read_text(encoding="utf-8")
        self.assertIn("model.model.layers[layer].register_forward_hook", text)
        self.assertIn("output_hidden_states=True", text)
        self.assertIn("pmean - nmean", text)
        self.assertNotIn("get_output_embeddings()", text)
        self.assertNotIn("model.model.norm.register_forward_hook", text)
        self.assertIn('"terminal_output_projection_shortcut": False', text)

    def test_local_api_and_zero_provider_contract(self):
        text = EXECUTOR.read_text(encoding="utf-8")
        self.assertIn('ThreadingHTTPServer(("127.0.0.1", 0)', text)
        self.assertIn('"loopback_only": True', text)
        self.assertIn('"zero_provider_billing": True', text)
        self.assertIn('"external_provider_credentials_read": False', text)


if __name__ == "__main__":
    unittest.main()
