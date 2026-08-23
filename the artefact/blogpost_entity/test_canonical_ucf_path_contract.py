from __future__ import annotations

import unittest
from pathlib import Path

SRC = Path(__file__).with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def canonical_ucf_contract(source: str) -> dict[str, bool]:
    prompt_pos = source.find('phase("pipeline_build_prompt"')
    fabric_pos = source.find('phase("pipeline_cognitive_fabric_admit"')
    inference_pos = source.find('effect("inference_generate"')
    return {
        "fabric_present": fabric_pos >= 0,
        "fabric_between_prompt_and_inference": prompt_pos >= 0 and prompt_pos < fabric_pos < inference_pos,
        "admitted_engine": 'map_set(infer,"inference",admitted.inference)' in source,
        "admitted_system": 'map_set(infer,"system",admitted.system)' in source,
        "admitted_user": 'map_set(infer,"user",admitted.user)' in source,
        "packet_digest": 'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)' in source,
        "fabric_digest": 'map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)' in source,
        "fabric_reenters_gate": 'map_set(gate_data,"cognitive_fabric",admitted)' in source,
        "fabric_reenters_commit": 'map_set(commit_data,"cognitive_fabric",admitted)' in source,
        "raw_engine_bypass_absent": 'map_set(infer,"inference",profile.inference)' not in source,
        "raw_system_bypass_absent": 'map_set(infer,"system",prompt.system)' not in source,
        "raw_user_bypass_absent": 'map_set(infer,"user",prompt.user)' not in source,
    }


class CanonicalUCFPathContractTests(unittest.TestCase):
    def assert_contract(self, source: str) -> None:
        failed = [name for name, ok in canonical_ucf_contract(source).items() if not ok]
        self.assertEqual(failed, [])

    def test_current_canonical_source_requires_single_fabric_handoff(self) -> None:
        self.assert_contract(SRC)

    def test_half_bypass_back_to_raw_prompt_user_fails_closed(self) -> None:
        poisoned = SRC.replace(
            'map_set(infer,"user",admitted.user)',
            'map_set(infer,"user",prompt.user)',
            1,
        )
        result = canonical_ucf_contract(poisoned)
        self.assertFalse(result["admitted_user"])
        self.assertFalse(result["raw_user_bypass_absent"])

    def test_fabric_after_inference_fails_order_contract(self) -> None:
        fabric = 'let admitted = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)'
        without = SRC.replace(fabric, 'let admitted = phase("pipeline_cognitive_fabric_DEFERRED",entity_db,source_db,profile,previous,cognition_data)', 1)
        poisoned = without.replace(
            'let generated = effect("inference_generate",infer)',
            'let generated = effect("inference_generate",infer)\n  let late = phase("pipeline_cognitive_fabric_admit",entity_db,source_db,profile,previous,cognition_data)',
            1,
        )
        self.assertFalse(canonical_ucf_contract(poisoned)["fabric_between_prompt_and_inference"])


if __name__ == "__main__":
    unittest.main()
