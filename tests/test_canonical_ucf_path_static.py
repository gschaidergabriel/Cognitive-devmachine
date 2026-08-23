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

    def test_raw_prompt_bypass_mutation_fails_closed(self):
        poisoned = self.source.replace(
            'map_set(infer,"system",prepared.system)',
            'map_set(infer,"system",prompt.system)',
            1,
        )
        report = evaluate(poisoned)
        self.assertFalse(report["pass"], report)
        self.assertTrue(report["forbidden_raw_bypasses"]["prompt_system_direct"])
        self.assertFalse(report["required_bindings"]["system_from_prepared"])

    def test_final_ucf_receipt_cannot_be_sent_to_inference(self):
        poisoned = self.source.replace(
            'map_set(infer,"inference_packet_digest",prepared.inference_packet_digest)',
            'map_set(infer,"inference_packet_digest",prepared.inference_packet_digest)\n'
            '  map_set(infer,"cognitive_fabric_receipt_digest",prepared.inference_packet_digest)',
            1,
        )
        report = evaluate(poisoned)
        self.assertFalse(report["pass"], report)
        self.assertTrue(report["temporal_false_green"]["final_receipt_sent_pre_inference"])

    def test_finalize_before_gate_commit_fails_closed(self):
        # Ordinary deterministic temporal regression: emulate the superseded ordering.
        finalize_block = '''  let cognition_finalize_data = map_new()\n  map_set(cognition_finalize_data,"prepared",prepared)\n  map_set(cognition_finalize_data,"generated",generated)\n  map_set(cognition_finalize_data,"compiled",compiled)\n  map_set(cognition_finalize_data,"prompt",prompt)\n  map_set(cognition_finalize_data,"gated",gated)\n  map_set(cognition_finalize_data,"committed",committed)\n  let finalized = phase("pipeline_cognitive_fabric_finalize",entity_db,source_db,profile,previous,cognition_finalize_data)\n  require finalized.ok\n\n'''
        poisoned = self.source.replace(finalize_block, "", 1)
        marker = "  let gate_data = map_new()\n"
        poisoned = poisoned.replace(marker, finalize_block + marker, 1)
        report = evaluate(poisoned)
        self.assertFalse(report["pass"], report)
        self.assertTrue(report["temporal_false_green"]["finalize_before_terminal_commit"])

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
