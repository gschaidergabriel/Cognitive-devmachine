from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.trigger1_atomic_lease_gate import EXPECTED_EXPERIMENT, validate_claim


RID = "rid_" + "a" * 64
HEAD = "b" * 40


def claim(trigger_key: str = RID) -> dict:
    return {
        "schema": "clay-go-experiment-claim/v1",
        "trigger_key": trigger_key,
        "trigger": "go",
        "experiment_name": EXPECTED_EXPERIMENT,
        "claimant_organ": "gpt56sol",
        "claimed_at": "2026-08-24T14:50:00Z",
        "observed_canonical_main": HEAD,
        "intervention_contract": {"mode": "bounded_hidden_state_vector_control"},
        "status": "CLAIMED",
    }


class Trigger1AtomicLeaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_claim(self, obj: dict, name: str | None = None) -> Path:
        key = obj.get("trigger_key", RID)
        path = self.root / (name or f"{key}.json")
        path.write_text(json.dumps(obj) + "\n", encoding="utf-8")
        return path

    def test_valid_canonical_claim_passes(self):
        self.write_claim(claim())
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertTrue(result["pass"])
        self.assertEqual(result["reason"], "CANONICAL_ATOMIC_LEASE_ADMITTED")
        self.assertEqual(len(result["claim_sha256"]), 64)

    def test_minute_or_noncanonical_key_fails(self):
        result = validate_claim(issue_body="trigger_key: ts_20260824T1450Z__p_abc\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "TRIGGER_KEY_NONCANONICAL")

    def test_missing_claim_fails_closed(self):
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "CANONICAL_ATOMIC_CLAIM_MISSING")

    def test_wrong_experiment_cannot_borrow_slot(self):
        obj = claim()
        obj["experiment_name"] = "different_intervention"
        self.write_claim(obj)
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "CLAIM_EXPERIMENT_MISMATCH")

    def test_existing_result_blocks_reexecution(self):
        self.write_claim(claim())
        (self.root / f"{RID}.result.json").write_text("{}\n", encoding="utf-8")
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "UNUSUAL_EXPERIMENT_RESULT_ALREADY_EXISTS")

    def test_semantic_duplicate_claim_closes_slot(self):
        self.write_claim(claim())
        self.write_claim(claim(), name="legacy_duplicate_claim.json")
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "EXPERIMENT_BUDGET_RACE_VIOLATION")

    def test_required_claim_fields_are_fail_closed(self):
        for field, expected in [
            ("claimant_organ", "CLAIMANT_ORGAN_MISSING"),
            ("claimed_at", "CLAIMED_AT_MISSING"),
            ("observed_canonical_main", "OBSERVED_MAIN_INVALID"),
            ("intervention_contract", "INTERVENTION_CONTRACT_MISSING"),
        ]:
            with self.subTest(field=field):
                for p in self.root.glob("*"):
                    p.unlink()
                obj = claim()
                obj[field] = "" if field != "intervention_contract" else {}
                self.write_claim(obj)
                result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
                self.assertFalse(result["pass"])
                self.assertEqual(result["reason"], expected)


if __name__ == "__main__":
    unittest.main()
