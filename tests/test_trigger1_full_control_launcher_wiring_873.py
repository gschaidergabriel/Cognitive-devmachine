from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools/trigger1_local_qwen06_midlayer_causal.sh"


class Trigger1FullControlLauncherWiring873Tests(unittest.TestCase):
    def test_retained_launcher_requires_full_control_after_direct_bridge(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        direct = "python3 tools/trigger1_intermediate_promotion_bridge.py"
        full = "python3 tools/trigger1_full_vector_control_bridge.py"
        self.assertIn(direct, text)
        self.assertIn(full, text)
        self.assertLess(text.index(direct), text.index(full))
        self.assertIn('--direct-candidate "$DIRECT"', text)
        self.assertIn('FULL_CONTROL="$OUT_DIR/trigger1_full_vector_control_admission.json"', text)
        self.assertIn("BLOCKED_FULL_VECTOR_CONTROL_EVIDENCE_NOT_ADMITTED", text)
        self.assertIn("rc=6", text)

    def test_source_contract_is_named_in_compatibility_result(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            "TRIGGER1_INTERMEDIATE_FULL_CONTROL_SOURCE_CONTRACT_V1.json",
            text,
        )
        self.assertIn("full_control_bridge", text)


if __name__ == "__main__":
    unittest.main()
