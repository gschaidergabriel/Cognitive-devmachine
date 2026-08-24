from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as flp


class FreeLaneEpochAlignment871Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = tempfile.TemporaryDirectory()
        self.root = Path(self.ctx.name)
        self.old_admission = flp.ADMISSION_PATH
        self.old_provenance = flp.PROVENANCE_PATH
        flp.ADMISSION_PATH = self.root / "admission.json"
        flp.PROVENANCE_PATH = self.root / "provenance.json"

    def tearDown(self) -> None:
        flp.ADMISSION_PATH = self.old_admission
        flp.PROVENANCE_PATH = self.old_provenance
        self.ctx.cleanup()

    def write(self, admission_epoch: str, provenance_epoch: str) -> None:
        flp.ADMISSION_PATH.write_text(
            json.dumps(
                {
                    "schema": flp.ADMISSION_SCHEMA,
                    "authority_epoch": admission_epoch,
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {"admitted": True, "cost_class": "FREE"}
                    },
                }
            ),
            encoding="utf-8",
        )
        flp.PROVENANCE_PATH.write_text(
            json.dumps(
                {
                    "schema": flp.PROVENANCE_SCHEMA,
                    "authority_epoch": provenance_epoch,
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {
                            "allowed_endpoint_host": "openrouter.ai",
                            "allowed_routes": ["openrouter/free"],
                            "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                            "source": "fixture",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def bind(self) -> dict:
        return flp.current_lane_binding(
            "openrouter",
            "fixture-fingerprint",
            "openrouter/free",
            "https://openrouter.ai/api/v1/chat/completions",
            artifacts=self.root,
        )

    def test_exact_871_snapshots_bind(self) -> None:
        self.write("8.71", "8.71")
        result = self.bind()
        self.assertTrue(result["ok"])
        self.assertEqual(result["admission_epoch"], "8.71")
        self.assertEqual(
            result["evidence"]["assertion"],
            "EXACT_ROUTE_ZERO_PROMPT_AND_COMPLETION_PRICE",
        )

    def test_870_admission_plus_871_provenance_fails_closed(self) -> None:
        self.write("8.70", "8.71")
        result = self.bind()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "FREE_LANE_AUTHORITY_EPOCH_MISMATCH")

    def test_871_admission_plus_870_provenance_fails_closed(self) -> None:
        self.write("8.71", "8.70")
        result = self.bind()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "FREE_LANE_AUTHORITY_EPOCH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
