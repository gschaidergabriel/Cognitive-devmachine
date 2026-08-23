import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import profile_runtime_cognitive_fabric_binding_v1 as binding


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


class FakeRuntime:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _read_only_db(self, value: str):
        if value != str(self.db_path):
            raise AssertionError("wrong db")
        conn = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return conn

    @classmethod
    def _normalize_profile(cls, profile):
        out = json.loads(json.dumps(dict(profile)))
        if out.get("schema") not in {"clay-pipeline-profile/v1", "clay-pipeline-profile/v2"}:
            raise ValueError("BAD_PROFILE_SCHEMA")
        if "inference" not in out and "provider" in out:
            out["inference"] = out.pop("provider")
        out["schema"] = "clay-pipeline-profile/v2"
        return out


class RecordingCompositor:
    def __init__(self):
        self.calls = []

    def build_pre_inference_admission(self, db, **kwargs):
        self.calls.append(kwargs)
        return {"ok": True, "generation": kwargs["entity_generation"]}


class LegacyProfileNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mini.db"
        self.stored_v1 = {
            "schema": "clay-pipeline-profile/v1",
            "profile_id": "legacy",
            "inference": {"kind": "mock"},
            "personality": {"output_contract": {}},
            "sources": [],
            "state_metrics": [],
            "gate": {},
        }
        raw = canonical_json(self.stored_v1)
        self.raw_hash = hashlib.sha256(raw.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER,active_profile TEXT)")
        conn.execute("CREATE TABLE profiles(profile_id TEXT PRIMARY KEY,profile_json TEXT,profile_sha256 TEXT)")
        conn.execute("INSERT INTO entity_state VALUES(1,7,'legacy')")
        conn.execute("INSERT INTO profiles VALUES(?,?,?)", ("legacy", raw, self.raw_hash))
        conn.commit()
        conn.close()
        self.runtime = FakeRuntime(self.db_path)
        normalized = self.runtime._normalize_profile(self.stored_v1)
        normalized["_runtime_profile_snapshot"] = {
            "profile_id": "legacy",
            "profile_hash": self.raw_hash,
        }
        self.payload = {
            "entity_db": str(self.db_path),
            "profile": normalized,
            "data": {
                "compiled": {"canonical_state_hash": "a" * 64, "packet_hash": "b" * 64},
                "prompt": {"system": "s", "user": "{}"},
                "invocation": {
                    "expected_generation": 7,
                    "causal_turn_id": "ct",
                    "task_text": "t",
                    "turn_binding_digest": "c" * 64,
                },
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_legacy_v1_profile_is_compared_after_runtime_normalization(self):
        compositor = RecordingCompositor()
        out = binding.admit_profile_runtime_payload(
            self.runtime, self.payload, compositor_module=compositor
        )
        self.assertTrue(out["ok"])
        self.assertEqual(len(compositor.calls), 1)
        self.assertEqual(compositor.calls[0]["profile"]["schema"], "clay-pipeline-profile/v2")
        self.assertEqual(compositor.calls[0]["profile"], self.runtime._normalize_profile(self.stored_v1))

    def test_raw_profile_hash_still_fences_tamper_before_normalization(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE profiles SET profile_json=? WHERE profile_id='legacy'", (canonical_json({**self.stored_v1, "gate": {"poison": True}}),))
        conn.commit()
        conn.close()
        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "ACTIVE_PROFILE_HASH_MISMATCH",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime, self.payload, compositor_module=RecordingCompositor()
            )


if __name__ == "__main__":
    unittest.main()
