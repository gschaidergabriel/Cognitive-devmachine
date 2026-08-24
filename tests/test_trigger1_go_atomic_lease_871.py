from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import go_experiment_lease_guard as guard


class Trigger1GoAtomicLease871Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rid = "rid_" + "a" * 64
        self.ts = "ts_20260824T133700000000Z__p_" + "b" * 64
        self.contract = {
            "launcher": "tools/run_trigger1_jspace_10x.py",
            "experiment_name": "TRIGGER1_JSPACE_10X",
            "experiment_contract_sha256": "c" * 64,
            "parallel_lanes": 10,
            "free_only": True,
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _claim(self, key: str | None = None, **changes) -> Path:
        key = key or self.rid
        payload = {
            "schema": guard.CLAIM_SCHEMA,
            "trigger_key": key,
            "trigger": "go",
            "experiment_name": "TRIGGER1_JSPACE_10X",
            "claimant_organ": "test-organ",
            "claimed_at": "2026-08-24T13:37:00Z",
            "observed_canonical_main": "d" * 40,
            "intervention_contract": self.contract,
            "status": "CLAIMED",
        }
        payload.update(changes)
        path = self.root / f"{key}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _validate(self, key: str | None = None, contract=None):
        return guard.validate_claim(
            trigger_key=key or self.rid,
            experiment_name="TRIGGER1_JSPACE_10X",
            expected_intervention_contract=self.contract if contract is None else contract,
            claims_root=self.root,
        )

    def test_canonical_request_id_claim_passes(self) -> None:
        self._claim()
        self.assertTrue(self._validate()["ok"])

    def test_canonical_timestamp_fallback_claim_passes(self) -> None:
        self._claim(self.ts)
        self.assertTrue(self._validate(self.ts)["ok"])

    def test_minute_precision_or_noncanonical_key_fails(self) -> None:
        bad = "ts_20260824T133700Z__p_" + "b" * 64
        self.assertFalse(self._validate(bad)["ok"])

    def test_missing_claim_fails_closed(self) -> None:
        result = self._validate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GO_EXPERIMENT_CANONICAL_CLAIM_MISSING_OR_INVALID")

    def test_contract_mismatch_fails_closed(self) -> None:
        self._claim()
        result = self._validate(contract={**self.contract, "parallel_lanes": 9})
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GO_EXPERIMENT_INTERVENTION_CONTRACT_MISMATCH")

    def test_wrong_experiment_name_fails_closed(self) -> None:
        self._claim(experiment_name="OTHER")
        result = self._validate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GO_EXPERIMENT_NAME_NOT_CLAIMED")

    def test_existing_result_closes_lease(self) -> None:
        self._claim()
        (self.root / f"{self.rid}.result.json").write_text("{}", encoding="utf-8")
        result = self._validate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GO_EXPERIMENT_LEASE_ALREADY_TERMINAL")

    def test_claim_identity_mismatch_fails_closed(self) -> None:
        self._claim(trigger_key="rid_" + "e" * 64)
        result = self._validate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "GO_EXPERIMENT_CLAIM_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
