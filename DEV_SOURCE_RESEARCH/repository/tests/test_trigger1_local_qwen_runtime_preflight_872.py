from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools/trigger1_local_qwen06_midlayer_causal.sh"
WORKFLOW = ROOT / ".github/workflows/trigger1-v2-local-fastpath-selfhosted.yml"


class Trigger1LocalQwenRuntimePreflight872(unittest.TestCase):
    def test_low_disk_block_binds_before_and_after_headroom(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("BLOCKED_INSUFFICIENT_FREE_DISK_AFTER_BOUNDED_CLEANUP", text)
        self.assertIn("'available_kb_before':int(sys.argv[2])", text)
        self.assertIn("'available_kb_after':int(sys.argv[3])", text)
        self.assertIn('"$BEFORE_KB" "$AFTER_KB"', text)
        self.assertIn("'zero_provider_billing':True", text)
        self.assertIn("'external_provider_credentials_read':False", text)

    def test_active_workflow_uses_current_launcher_and_persists_terminal_receipt(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Require canonical go atomic lease and bind source", text)
        self.assertIn("python3 tools/trigger1_atomic_lease_gate.py", text)
        self.assertIn("bash tools/trigger1_local_qwen06_midlayer_causal.sh", text)
        self.assertIn("trigger1_local_activation_api_result.json", text)
        self.assertIn("CLAY_TRIGGER1_V2_SELFHOSTED_RUNTIME_RECEIPT/v1", text)
        self.assertIn("research_entity/runtime/tool_results", text)

    def test_active_workflow_fails_closed_before_intervention_without_lease(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        lease_step = text.index("Require canonical go atomic lease and bind source")
        experiment_step = text.index("Execute fused nonterminal midlayer causal discriminator")
        self.assertLess(lease_step, experiment_step)
        self.assertIn("TRIGGER1_LEASE_ADMITTED':'true'", text)
        self.assertIn("BLOCKED_CLAIM_MAIN_NOT_ANCESTOR_OF_EXECUTED_SOURCE", text)


if __name__ == "__main__":
    unittest.main()
