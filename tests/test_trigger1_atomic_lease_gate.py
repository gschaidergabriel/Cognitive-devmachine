from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.trigger1_atomic_lease_gate import EXPECTED_EXPERIMENT, validate_claim

RID = "rid_" + "a" * 64
HEAD = "b" * 40
PAYLOAD_SHA = "4cd0e21a9a0795a14ec9aa5f0e7d1abff0492565770e43eafdf1e3e8afed1f33"
TS = f"ts_20260817T063500000000Z__p_{PAYLOAD_SHA}"


def claim(trigger_key: str = RID) -> dict:
    return {
        "schema": "clay-go-experiment-claim/v1",
        "trigger_key": trigger_key,
        "trigger": "go",
        "experiment_name": EXPECTED_EXPERIMENT,
        "claimant_organ": "gpt56sol",
        "claimed_at": "2026-08-24T15:06:00Z",
        "observed_canonical_main": HEAD,
        "intervention_contract": {"mode": "bounded_midlayer_causal"},
        "status": "CLAIMED",
    }


class Trigger1AtomicLeaseGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, obj: dict, name: str | None = None):
        p = self.root / (name or f"{obj.get('trigger_key', RID)}.json")
        p.write_text(json.dumps(obj) + "\n", encoding="utf-8")

    def run_gate(self, body: str | None = None):
        return validate_claim(issue_body=body or f"trigger_key: {RID}\n", claims_root=self.root)

    def test_valid_claim(self):
        self.put(claim())
        r = self.run_gate()
        self.assertTrue(r["pass"])
        self.assertEqual(r["experiment_name"], EXPECTED_EXPERIMENT)
        self.assertEqual(len(r["claim_sha256"]), 64)

    def test_noncanonical_or_multiple_key(self):
        self.assertEqual(self.run_gate("trigger_key: ts_20260824T1506Z__p_abc\n")["reason"], "TRIGGER_KEY_NONCANONICAL")
        self.assertEqual(self.run_gate(f"trigger_key: {RID}\ntrigger_key: {RID}\n")["reason"], "ISSUE_BODY_REQUIRES_EXACTLY_ONE_TRIGGER_KEY")

    def test_impossible_canonical_timestamp_is_noncanonical(self):
        impossible = "ts_20261340T256199999999Z__p_" + PAYLOAD_SHA
        self.assertEqual(
            self.run_gate(f"trigger_key: {impossible}\n")["reason"],
            "TRIGGER_KEY_NONCANONICAL",
        )

    def test_missing_claim(self):
        self.assertEqual(self.run_gate()["reason"], "CANONICAL_ATOMIC_CLAIM_MISSING")

    def test_wrong_experiment(self):
        c = claim(); c["experiment_name"] = "OLDER_TRIGGER1_EXPERIMENT"
        self.put(c)
        self.assertEqual(self.run_gate()["reason"], "CLAIM_EXPERIMENT_MISMATCH")

    def test_existing_result(self):
        self.put(claim())
        (self.root / f"{RID}.result.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(self.run_gate()["reason"], "UNUSUAL_EXPERIMENT_RESULT_ALREADY_EXISTS")

    def test_duplicate_claim(self):
        self.put(claim()); self.put(claim(), "legacy_duplicate.json")
        self.assertEqual(self.run_gate()["reason"], "EXPERIMENT_BUDGET_RACE_VIOLATION")

    def test_legacy_minute_alias_blocks_canonical_timestamp_claim(self):
        self.put(claim(TS))
        legacy = claim("2026-08-17T13-35+07-00__" + PAYLOAD_SHA)
        legacy["experiment_name"] = "HISTORICAL_OTHER_EXPERIMENT"
        self.put(legacy, "2026-08-17T13-35+07-00__" + PAYLOAD_SHA + ".json")
        r = self.run_gate(f"trigger_key: {TS}\n")
        self.assertEqual(r["reason"], "EXPERIMENT_BUDGET_RACE_VIOLATION")
        self.assertEqual(len(r["semantic_duplicate_claims"]), 1)

    def test_legacy_compact_short_hash_alias_blocks_canonical_timestamp_claim(self):
        self.put(claim(TS))
        legacy_key = "20260817T133500+0700_" + PAYLOAD_SHA[:16]
        legacy = claim(legacy_key)
        legacy["experiment_name"] = "HISTORICAL_OTHER_EXPERIMENT"
        self.put(legacy, legacy_key + ".json")
        self.assertEqual(
            self.run_gate(f"trigger_key: {TS}\n")["reason"],
            "EXPERIMENT_BUDGET_RACE_VIOLATION",
        )

    def test_damaged_legacy_alias_filename_still_blocks(self):
        self.put(claim(TS))
        alias = self.root / ("2026-08-17T13-35+07-00__go__" + PAYLOAD_SHA[:12] + ".json")
        alias.write_text("{not-valid-json\n", encoding="utf-8")
        r = self.run_gate(f"trigger_key: {TS}\n")
        self.assertEqual(r["reason"], "EXPERIMENT_BUDGET_RACE_VIOLATION")
        self.assertEqual(r["semantic_duplicate_claims"], [str(alias)])

    def test_invalid_legacy_calendar_or_offset_is_ignored_deterministically(self):
        self.put(claim(TS))
        (self.root / ("2026-99-99T13-35+07-00__go__" + PAYLOAD_SHA[:12] + ".json")).write_text("{bad\n", encoding="utf-8")
        (self.root / ("2026-08-17T13-35+99-99__go__" + PAYLOAD_SHA[:12] + ".json")).write_text("{bad\n", encoding="utf-8")
        self.assertTrue(self.run_gate(f"trigger_key: {TS}\n")["pass"])

    def test_legacy_alias_requires_same_payload_and_time_bucket(self):
        self.put(claim(TS))
        different_payload = claim("2026-08-17T13-35+07-00__" + "d" * 64)
        different_time = claim("2026-08-17T13-36+07-00__" + PAYLOAD_SHA)
        self.put(different_payload, "different-payload.json")
        self.put(different_time, "different-time.json")
        (self.root / "damaged-unrelated.json").write_text("{bad\n", encoding="utf-8")
        self.assertTrue(self.run_gate(f"trigger_key: {TS}\n")["pass"])

    def test_required_fields(self):
        for field, value, reason in [
            ("claimant_organ", "", "CLAIMANT_ORGAN_MISSING"),
            ("claimed_at", "", "CLAIMED_AT_MISSING"),
            ("observed_canonical_main", "", "OBSERVED_MAIN_INVALID"),
            ("intervention_contract", {}, "INTERVENTION_CONTRACT_MISSING"),
        ]:
            with self.subTest(field=field):
                for p in self.root.glob("*"): p.unlink()
                c = claim(); c[field] = value; self.put(c)
                self.assertEqual(self.run_gate()["reason"], reason)


if __name__ == "__main__":
    unittest.main()
