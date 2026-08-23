from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_canonical_ucf_path import evaluate  # noqa: E402


class CanonicalUcfPathStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")

    def test_current_source_has_temporally_valid_single_fabric_handoff(self):
        report = evaluate(self.source)
        self.assertTrue(report["pass"], report)

    def test_raw_prompt_bypass_regression_fails_closed(self):
        poisoned = self.source.replace(
            'map_set(infer,"system",prepared.system)',
            'map_set(infer,"system",prompt.system)',
            1,
        )
        report = evaluate(poisoned)
        self.assertFalse(report["pass"], report)
        self.assertTrue(report["forbidden_raw_bypasses"]["prompt_system_direct"])
        self.assertFalse(report["required_bindings"]["system_from_prepared"])

    def test_preinference_final_receipt_time_travel_fails_closed(self):
        # Exactly one unusual experiment for this GO: reintroduce a final UCF receipt
        # at the pre-inference boundary. The temporal guard must reject the time-travel.
        poisoned = self.source.replace(
            'map_set(infer,"inference_packet_digest",prepared.inference_packet_digest)',
            'map_set(infer,"inference_packet_digest",prepared.inference_packet_digest)\n'
            '  map_set(infer,"cognitive_fabric_receipt_digest",prepared.inference_packet_digest)',
            1,
        )
        report = evaluate(poisoned)
        self.assertFalse(report["pass"], report)
        self.assertTrue(report["temporal_false_green"]["final_receipt_sent_pre_inference"])

    def test_legacy_one_phase_admit_cannot_reappear(self):
        poisoned = self.source.replace(
            'phase("pipeline_cognitive_fabric_prepare"',
            'phase("pipeline_cognitive_fabric_admit"',
            1,
        )
        report = evaluate(poisoned)
        self.assertFalse(report["pass"], report)
        self.assertTrue(report["temporal_false_green"]["legacy_single_admit_phase"])


if __name__ == "__main__":
    unittest.main()
