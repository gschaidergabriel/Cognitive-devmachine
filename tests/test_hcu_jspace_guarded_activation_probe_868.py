from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.hcu_jspace_guarded_activation_probe import (
    LeaseGuardRejected,
    find_semantic_duplicate_claims,
    parse_canonical_trigger_key,
    parse_legacy_trigger_key,
)


PAYLOAD = "4cd0e21a9a0795a14ec9aa5f0e7d1abff0492565770e43eafdf1e3e8afed1f33"


class LeaseRaceFenceTests(unittest.TestCase):
    def _write_claim(self, directory: Path, key: str) -> Path:
        path = directory / f"{key}.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "clay-go-experiment-claim/v1",
                    "trigger_key": key,
                    "trigger": "go",
                    "status": "CLAIMED",
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_canonical_rid_and_timestamp_trigger_keys(self) -> None:
        rid = "rid_" + ("a" * 64)
        self.assertEqual(parse_canonical_trigger_key(rid)["kind"], "rid")
        ts = f"ts_20260817T063500000000Z__p_{PAYLOAD}"
        parsed = parse_canonical_trigger_key(ts)
        self.assertEqual(parsed["kind"], "ts")
        self.assertEqual(parsed["utc_stamp"], "20260817T063500000000Z")

    def test_noncanonical_legacy_key_is_not_accepted_as_canonical(self) -> None:
        key = f"2026-08-17T13-35+07-00__{PAYLOAD}"
        with self.assertRaisesRegex(LeaseGuardRejected, "CANONICAL_TRIGGER_KEY_REQUIRED"):
            parse_canonical_trigger_key(key)
        parsed = parse_legacy_trigger_key(key)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["utc_stamp"], "20260817T063500000000Z")

    def test_detects_full_hash_legacy_semantic_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            current_key = f"ts_20260817T063500000000Z__p_{PAYLOAD}"
            current = self._write_claim(directory, current_key)
            legacy = f"2026-08-17T13-35+07-00__{PAYLOAD}"
            self._write_claim(directory, legacy)
            duplicates = find_semantic_duplicate_claims(directory, current, current_key)
            self.assertEqual(duplicates, [f"{legacy}.json"])

    def test_detects_short_hash_compact_legacy_semantic_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            current_key = f"ts_20260817T063500000000Z__p_{PAYLOAD}"
            current = self._write_claim(directory, current_key)
            legacy = f"20260817T133500+0700_{PAYLOAD[:16]}"
            self._write_claim(directory, legacy)
            duplicates = find_semantic_duplicate_claims(directory, current, current_key)
            self.assertEqual(duplicates, [f"{legacy}.json"])

    def test_unrelated_claim_does_not_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            current_key = f"ts_20260817T063500000000Z__p_{PAYLOAD}"
            current = self._write_claim(directory, current_key)
            unrelated = f"2026-08-17T13-36+07-00__{PAYLOAD}"
            self._write_claim(directory, unrelated)
            self.assertEqual(
                find_semantic_duplicate_claims(directory, current, current_key), []
            )


if __name__ == "__main__":
    unittest.main()
