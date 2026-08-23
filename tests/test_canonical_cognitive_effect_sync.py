from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "the artefact" / "blogpost_entity"))
from check_canonical_cognitive_effect_sync import evaluate  # noqa: E402


class CanonicalCognitiveEffectSyncTest(unittest.TestCase):
    def test_rejoined_runtime_has_only_the_two_phase_ucf_effect_gap(self):
        clay = (ROOT / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")
        runtime = (ROOT / "tools" / "clay_profile_pipeline_runtime.py").read_text(encoding="utf-8")
        report = evaluate(clay, runtime)
        self.assertEqual(
            report["missing_runtime_effects"],
            ["pipeline_cognitive_fabric_finalize", "pipeline_cognitive_fabric_prepare"],
            report,
        )
        self.assertTrue(report["exact_expected_ucf_gap"], report)
        self.assertEqual(report["legacy_runtime_effects"], [], report)
        self.assertFalse(report["converged"], report)


if __name__ == "__main__":
    unittest.main()
