from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLAY = ROOT / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay"


class MiniEntityCanonicalUcfPathContractTests(unittest.TestCase):
    def test_canonical_pipeline_cannot_bypass_cognitive_fabric_before_inference(self):
        clay = CLAY.read_text(encoding="utf-8")
        prompt_index = clay.index('phase("pipeline_build_prompt"')
        admit_index = clay.index('phase("pipeline_cognitive_fabric_admit"')
        inference_index = clay.index('effect("inference_generate"')
        self.assertLess(prompt_index, admit_index)
        self.assertLess(admit_index, inference_index)

    def test_inference_consumes_only_admitted_fabric_envelope(self):
        clay = CLAY.read_text(encoding="utf-8")
        self.assertIn('map_set(infer,"inference",admitted.inference)', clay)
        self.assertIn('map_set(infer,"system",admitted.system)', clay)
        self.assertIn('map_set(infer,"user",admitted.user)', clay)
        self.assertIn('map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)', clay)
        self.assertIn('map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)', clay)
        self.assertNotIn('map_set(infer,"inference",profile.inference)', clay)
        self.assertNotIn('map_set(infer,"system",prompt.system)', clay)
        self.assertNotIn('map_set(infer,"user",prompt.user)', clay)

    def test_fabric_receipt_reenters_gate_commit_and_visible_result(self):
        clay = CLAY.read_text(encoding="utf-8")
        self.assertIn('map_set(gate_data,"cognitive_fabric",admitted)', clay)
        self.assertIn('map_set(commit_data,"cognitive_fabric",admitted)', clay)
        self.assertIn('map_set(result,"inference_packet_digest",admitted.inference_packet_digest)', clay)
        self.assertIn('map_set(result,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)', clay)


if __name__ == "__main__":
    unittest.main()
