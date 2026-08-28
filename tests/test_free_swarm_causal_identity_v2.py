from __future__ import annotations

import hashlib
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from free_swarm_causal_identity_v2 import causal_event_id, derive_identity_pair, logical_source_path

ROW = {
    "schema": "CLAY_FREE_GO_SWARM_WORKER/v1",
    "ts": "2026-08-25T03:00:00+00:00",
    "provider": "groq",
    "model": "example-model",
    "worker_id": 3,
    "worker_serial": 9,
    "repo_head_at_prompt": "a" * 40,
}
TEXT_SHA = hashlib.sha256(b"same worker output").hexdigest()


class CausalIdentityV2Tests(unittest.TestCase):
    def test_artifact_root_relocation_keeps_causal_identity(self):
        a = derive_identity_pair(
            "/mnt/a/artifacts", "/mnt/a/artifacts/go-20260825T030000Z/workers.jsonl", ROW,
            line_no=17, text_sha256=TEXT_SHA, legacy_source_event_id="legacy-a"
        )
        b = derive_identity_pair(
            "/restore/b/artifacts", "/restore/b/artifacts/go-20260825T030000Z/workers.jsonl", ROW,
            line_no=17, text_sha256=TEXT_SHA, legacy_source_event_id="legacy-b"
        )
        self.assertEqual(a["logical_source_path"], "go-20260825T030000Z/workers.jsonl")
        self.assertEqual(a["causal_event_id"], b["causal_event_id"])
        self.assertNotEqual(a["legacy_source_event_id"], b["legacy_source_event_id"])

    def test_different_logical_run_path_changes_identity(self):
        a = causal_event_id(ROW, logical_path="go-a/workers.jsonl", line_no=1, text_sha256=TEXT_SHA)
        b = causal_event_id(ROW, logical_path="go-b/workers.jsonl", line_no=1, text_sha256=TEXT_SHA)
        self.assertNotEqual(a, b)

    def test_different_absolute_line_changes_identity(self):
        a = causal_event_id(ROW, logical_path="go-a/workers.jsonl", line_no=1, text_sha256=TEXT_SHA)
        b = causal_event_id(ROW, logical_path="go-a/workers.jsonl", line_no=2, text_sha256=TEXT_SHA)
        self.assertNotEqual(a, b)

    def test_source_outside_root_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_PATH_OUTSIDE_ARTIFACT_ROOT"):
            logical_source_path("/artifacts/clay", "/tmp/workers.jsonl")

    def test_invalid_digest_and_relative_path_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "TEXT_SHA256_INVALID"):
            causal_event_id(ROW, logical_path="go-a/workers.jsonl", line_no=1, text_sha256="bad")
        with self.assertRaisesRegex(ValueError, "LOGICAL_SOURCE_PATH_INVALID"):
            causal_event_id(ROW, logical_path="../escape/workers.jsonl", line_no=1, text_sha256=TEXT_SHA)


if __name__ == "__main__":
    unittest.main()
