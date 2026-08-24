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
        "claimed_at": "2026-08-24T15:00:00Z",
        "observed_canonical_main": HEAD,
        "intervention_contract": {"mode": "bounded_intermediate_hidden_state_vector_control"},
        "status": "CLAIMED",
    }


class Trigger1AtomicLeaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_claim(self, obj: dict, name: str | None = None) -> Path:
        path = self.root / (name or f"{obj.get('trigger_key', RID)}.json")
        path.write_text(json.dumps(obj) + "\n", encoding="utf-8")
        return path

    def test_valid_canonical_claim_passes(self):
        self.write_claim(claim())
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertTrue(result["pass"])
        self.assertEqual(result["reason"], "CANONICAL_ATOMIC_LEASE_ADMITTED")
        self.assertEqual(result["experiment_name"], EXPECTED_EXPERIMENT)
        self.assertEqual(len(result["claim_sha256"]), 64)

    def test_noncanonical_key_fails(self):
        result = validate_claim(issue_body="trigger_key: ts_20260824T1500Z__p_abc\n", claims_root=self.root)
        self.assertEqual(result, {"pass": False, "reason": "TRIGGER_KEY_NONCANONICAL"})

    def test_multiple_issue_keys_fail(self):
        body = f"trigger_key: {RID}\ntrigger_key: {RID}\n"
        result = validate_claim(issue_body=body, claims_root=self.root)
        self.assertEqual(result, {"pass": False, "reason": "ISSUE_BODY_REQUIRES_EXACTLY_ONE_TRIGGER_KEY"})

    def test_missing_claim_fails_closed(self):
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "CANONICAL_ATOMIC_CLAIM_MISSING")

    def test_wrong_experiment_cannot_borrow_slot(self):
        obj = claim()
        obj["experiment_name"] = "CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v1"
        self.write_claim(obj)
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "CLAIM_EXPERIMENT_MISMATCH")

    def test_existing_result_blocks_reexecution(self):
        self.write_claim(claim())
        (self.root / f"{RID}.result.json").write_text("{}\n", encoding="utf-8")
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertEqual(result["reason"], "UNUSUAL_EXPERIMENT_RESULT_ALREADY_EXISTS")

    def test_semantic_duplicate_claim_closes_slot(self):
        self.write_claim(claim())
        self.write_claim(claim(), name="legacy_duplicate_claim.json")
        result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
        self.assertEqual(result["reason"], "EXPERIMENT_BUDGET_RACE_VIOLATION")

    def test_required_claim_fields_are_fail_closed(self):
        cases = [
            ("claimant_organ", "", "CLAIMANT_ORGAN_MISSING"),
            ("claimed_at", "", "CLAIMED_AT_MISSING"),
            ("observed_canonical_main", "", "OBSERVED_MAIN_INVALID"),
            ("intervention_contract", {}, "INTERVENTION_CONTRACT_MISSING"),
        ]
        for field, value, expected in cases:
            with self.subTest(field=field):
                for p in self.root.glob("*"):
                    p.unlink()
                obj = claim()
                obj[field] = value
                self.write_claim(obj)
                result = validate_claim(issue_body=f"trigger_key: {RID}\n", claims_root=self.root)
                self.assertEqual(result["reason"], expected)


if __name__ == "__main__":
    unittest.main()
