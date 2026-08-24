from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools import hcu_jspace_local_activation_probe as probe


CLAIMANT = "gpt56sol-test-organ"
EXPERIMENT = "HCU_JSPACE_LOCAL_ACTIVATION_PATCH_V1"
RID_KEY = "rid_" + "a" * 64
TS_KEY = "ts_20260824T113000123456Z__p_" + "b" * 64


class JSpaceAtomicTriggerKeyGate868Tests(unittest.TestCase):
    def _claim(self, root: Path, trigger_key: str) -> Path:
        claims = root / "research_entity/continuity/go_experiment_claims"
        claims.mkdir(parents=True, exist_ok=True)
        path = claims / f"{trigger_key}.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "clay-go-experiment-claim/v1",
                    "trigger_key": trigger_key,
                    "trigger": "go",
                    "experiment_name": EXPERIMENT,
                    "claimant_organ": CLAIMANT,
                    "claimed_at": "2026-08-24T11:30:00Z",
                    "observed_canonical_main": "0" * 40,
                    "intervention_contract": "offline source-only lease gate regression",
                    "status": "CLAIMED",
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_canonical_rid_key_is_accepted(self) -> None:
        self.assertEqual(probe.validate_canonical_trigger_key(RID_KEY), "IMMUTABLE_REQUEST_ID")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = probe.validate_atomic_claim(
                root, str(self._claim(root, RID_KEY)), CLAIMANT, EXPERIMENT
            )
        self.assertEqual(result["trigger_key_identity"], "IMMUTABLE_REQUEST_ID")
        self.assertFalse(result["create_only_semantics_reverified_by_probe"])
        self.assertFalse(result["semantic_duplicate_race_scan_reverified_by_probe"])

    def test_canonical_timestamp_payload_key_is_accepted(self) -> None:
        self.assertEqual(
            probe.validate_canonical_trigger_key(TS_KEY),
            "TIMESTAMP_PLUS_PAYLOAD_DIGEST",
        )

    def test_legacy_full_hash_key_is_rejected_even_when_filename_and_json_match(self) -> None:
        legacy = "2026-08-17T13-35+07-00__" + "4" * 64
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            claim = self._claim(root, legacy)
            with self.assertRaisesRegex(probe.ProbeRejected, "TRIGGER_KEY_NONCANONICAL"):
                probe.validate_atomic_claim(root, str(claim), CLAIMANT, EXPERIMENT)

    def test_legacy_short_hash_key_is_rejected(self) -> None:
        legacy = "20260817T133500+0700_4cd0e21a9a0795a1"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            claim = self._claim(root, legacy)
            with self.assertRaisesRegex(probe.ProbeRejected, "TRIGGER_KEY_NONCANONICAL"):
                probe.validate_atomic_claim(root, str(claim), CLAIMANT, EXPERIMENT)

    def test_uppercase_or_short_rid_hash_is_rejected(self) -> None:
        for key in ("rid_" + "A" * 64, "rid_" + "a" * 63):
            with self.subTest(key=key):
                with self.assertRaisesRegex(probe.ProbeRejected, "TRIGGER_KEY_NONCANONICAL"):
                    probe.validate_canonical_trigger_key(key)

    def test_invalid_timestamp_is_rejected(self) -> None:
        key = "ts_20261340T256199123456Z__p_" + "b" * 64
        with self.assertRaisesRegex(probe.ProbeRejected, "TRIGGER_KEY_TIMESTAMP_INVALID"):
            probe.validate_canonical_trigger_key(key)

    def test_existing_result_still_blocks_second_intervention(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            claim = self._claim(root, RID_KEY)
            claim.with_name(f"{RID_KEY}.result.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(probe.ProbeRejected, "RESULT_ALREADY_EXISTS"):
                probe.validate_atomic_claim(root, str(claim), CLAIMANT, EXPERIMENT)


if __name__ == "__main__":
    unittest.main()
