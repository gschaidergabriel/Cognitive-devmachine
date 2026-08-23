#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
CLAY = (HERE / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")
GUARD_PATH = HERE / "check_structured_contract_sync.py"
spec = importlib.util.spec_from_file_location("guard", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class CanonicalUcfTemporalPathTests(unittest.TestCase):
    def test_fetch_execute_writeback_order_is_canonical(self):
        contract = guard.canonical_contract(CLAY)
        self.assertTrue(contract["pre_inference_admission"])
        self.assertTrue(contract["post_inference_validation"])
        self.assertTrue(contract["temporal_order_ok"])
        self.assertTrue(contract["admitted_inference_inputs"])
        self.assertTrue(contract["post_receipt_only_after_inference"])
        self.assertTrue(contract["raw_profile_prompt_bypass_absent"])

    def test_runtime_receipt_cannot_be_smuggled_into_pre_inference_envelope(self):
        poisoned = CLAY.replace(
            'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)',
            'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)\n'
            '  map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)',
        )
        contract = guard.canonical_contract(poisoned)
        self.assertFalse(contract["post_receipt_only_after_inference"])

    def test_post_validation_cannot_move_before_inference(self):
        generated_start = CLAY.index('  let generated = effect("inference_generate",infer)')
        generated_end = CLAY.index('  require generated.ok', generated_start) + len('  require generated.ok\n')
        validate_start = CLAY.index('  // POST-INFERENCE VALIDATION', generated_end)
        gate_start = CLAY.index('  let gate_data = map_new()', validate_start)
        validate_block = CLAY[validate_start:gate_start]
        poisoned = CLAY[:generated_start] + validate_block + CLAY[generated_start:validate_start] + CLAY[gate_start:]
        contract = guard.canonical_contract(poisoned)
        self.assertFalse(contract["temporal_order_ok"])


if __name__ == "__main__":
    unittest.main()
