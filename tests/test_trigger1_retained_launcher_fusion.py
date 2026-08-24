from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal.sh"


class Trigger1RetainedLauncherFusionTest(unittest.TestCase):
    def test_historical_entrypoint_routes_to_strongest_intermediate_protocol(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("tools/trigger1_local_qwen06_intermediate.sh", text)
        self.assertIn("tools/trigger1_intermediate_promotion_bridge.py", text)
        self.assertNotIn("trigger1_local_qwen06_midlayer_causal_execute.py", text)

    def test_exact_source_identity_fails_closed_across_run(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("tools/git_source_identity_v1.py", text)
        self.assertIn("--require-clean", text)
        self.assertIn("source_identity_stable_across_run", text)
        self.assertIn("BLOCKED_EXACT_SOURCE_CHANGED_DURING_RUN", text)
        self.assertIn('rm -f "$INTERMEDIATE" "$DIRECT"', text)

    def test_compatibility_output_is_explicit_not_a_second_science_lane(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("compatibility_entrypoint", text)
        self.assertIn("effective_executor", text)
        self.assertIn("promotion_bridge", text)
        self.assertIn("trigger1_local_activation_api_result.json", text)


if __name__ == "__main__":
    unittest.main()
