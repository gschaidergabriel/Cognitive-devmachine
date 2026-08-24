from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "trigger1-local-qwen06-runtime-proof.yml"
LAUNCHER = ROOT / "tools" / "trigger1_local_qwen06_internal_layer_api.sh"
MIDLAYER = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal_execute.py"


class Trigger1RuntimeProofRouteTests(unittest.TestCase):
    def test_runtime_proof_routes_to_nonterminal_launcher(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("bash tools/trigger1_local_qwen06_internal_layer_api.sh", text)
        self.assertNotIn("bash tools/trigger1_local_qwen06_activation_api.sh", text)
        self.assertIn("ACTIVATION_DERIVED_NONTERMINAL_MIDLAYER", text)

    def test_launcher_routes_to_activation_derived_midlayer_executor(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("trigger1_local_qwen06_midlayer_causal_execute.py", text)
        self.assertNotIn("trigger1_local_qwen06_internal_layer_api_execute.py", text)
        self.assertNotIn("trigger1_local_qwen06_activation_api_execute.py", text)

    def test_midlayer_executor_has_nonterminal_independence_guards(self):
        text = MIDLAYER.read_text(encoding="utf-8")
        self.assertIn("activation_only_basis", text)
        self.assertIn("NO_DOWNSTREAM_TRANSFORMER_COMPUTATION", text)
        self.assertIn('"terminal_output_projection_shortcut": False', text)
        self.assertIn('"basis_constructed_without_output_head": True', text)
        self.assertIn("mean internal activation(A)-0.5*(mean internal activation(B)+mean internal activation(C))", text)


if __name__ == "__main__":
    unittest.main()
