#!/usr/bin/env python3
from pathlib import Path
import unittest


class QuiescedPromoterContractTest(unittest.TestCase):
    def setUp(self) -> None:
        here = Path(__file__).resolve().parent
        self.wrapper = (here / "promote_semantic_shadow_quiesced.py").read_text()
        self.base = (here / "promote_semantic_shadow.py").read_text()

    def test_base_anchor_cardinalities_match_wrapper_contract(self) -> None:
        self.assertEqual(self.base.count("GO_AVATAR_EYE_SHADOW_RUNTIME/v2"), 2)
        self.assertEqual(self.base.count("GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1"), 2)
        self.assertEqual(self.base.count("GO_AVATAR_EYE_LIVE_PROMOTION/v1"), 2)
        self.assertEqual(
            self.base.count('shutil.copy2(runtime_report_path, evidence / "prelive.runtime.json")'),
            1,
        )
        self.assertEqual(
            self.base.count('shutil.copy2(matched_report_path, evidence / "prelive.matched_ab.json")'),
            1,
        )

    def test_wrapper_accepts_only_new_evidence_schemas(self) -> None:
        self.assertIn("GO_AVATAR_EYE_SHADOW_RUNTIME/v3", self.wrapper)
        self.assertIn("GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", self.wrapper)
        self.assertIn("GO_AVATAR_EYE_LIVE_PROMOTION/v3", self.wrapper)
        self.assertIn("BASE_PROMOTER_RUNTIME_SCHEMA_ANCHOR_DRIFT", self.wrapper)
        self.assertIn("BASE_PROMOTER_MATCHED_SCHEMA_ANCHOR_DRIFT", self.wrapper)

    def test_runtime_transport_contract_is_fail_closed(self) -> None:
        for marker in (
            'V3_IN_PAGE_AUTONOMOUS_SAMPLER',
            'state_roundtrips_during_measurement',
            'final_payload_roundtrips',
            'measurement window was not transport-decoupled',
            'raise RuntimeError',
        ):
            self.assertIn(marker, self.wrapper)

    def test_quiescence_is_fail_closed(self) -> None:
        for marker in (
            'quiesce = matched.get("quiesce")',
            'futureSchedulersBlocked',
            '"rafCancelAttempts", "timerCancelAttempts"',
            'value < 1',
            'raise RuntimeError',
        ):
            self.assertIn(marker, self.wrapper)

    def test_base_still_contains_hash_rollback_and_http_fences(self) -> None:
        for marker in (
            'EXPECTED_BEFORE_SHA256', 'EXPECTED_AFTER_SHA256', 'EXPECTED_OPEN_PLATE_SHA256',
            'rollback copy failed byte-exact verification',
            'live subject changed after preparation; refusing promotion',
            'post-write hash mismatch', 'HTTP readback mismatch after install; rollback executed',
            'post_live_acceptance',
        ):
            self.assertIn(marker, self.base)


if __name__ == "__main__":
    unittest.main()
