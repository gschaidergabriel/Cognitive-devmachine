#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from grid10_cognitive_unified_runtime_v3 import (
    build_unified_agency_runtime,
    runtime_authority_receipt,
)


class UnifiedRuntimeV3CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"

    def tearDown(self):
        self.td.cleanup()

    def test_compat_constructor_delegates_to_one_physical_v2_authority(self):
        fabric, heartbeat, agency, runtime, fingerprint = build_unified_agency_runtime(self.db)
        self.assertEqual(Path(fabric.path).resolve(), self.db.resolve())
        self.assertEqual(Path(heartbeat.path).resolve(), self.db.resolve())
        self.assertEqual(Path(agency.path).resolve(), self.db.resolve())
        self.assertEqual(fingerprint.realpath, str(self.db.resolve()))
        self.assertIsNotNone(runtime)

    def test_receipt_is_scoped_and_does_not_restore_duplicate_authority(self):
        fabric, heartbeat, agency, _runtime, _fingerprint = build_unified_agency_runtime(self.db)
        receipt = runtime_authority_receipt(fabric, heartbeat, agency)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["implementation"], "DELEGATES_TO_GRID10_UNIFIED_RUNTIME_V2")
        self.assertFalse(receipt["duplicate_v3_state_authority"])
        self.assertEqual(receipt["physical_grid10_credit"], 0)
        self.assertEqual(receipt["whole_hcu_credit"], 0)


if __name__ == "__main__":
    unittest.main()
