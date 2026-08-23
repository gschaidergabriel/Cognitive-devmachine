#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import profile_runtime_cognitive_fabric_binding_v1 as binding


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


class FakeRuntime:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _read_only_db(self, value: str):
        assert value == str(self.db_path)
        conn = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return conn


class RecordingCompositor:
    def __init__(self, mutate=None):
        self.calls = []
        self.mutate = mutate

    def build_pre_inference_admission(self, db, **kwargs):
        write_blocked = False
        try:
            db.execute("CREATE TABLE forbidden_write(x INTEGER)")
        except sqlite3.OperationalError:
            write_blocked = True
        snapshot = kwargs["profile"].get("_runtime_profile_snapshot")
        if not isinstance(snapshot, dict):
            raise ValueError("PROFILE_SNAPSHOT_MISSING")
        self.calls.append((kwargs, write_blocked))
        result = {
            "ok": True,
            "schema": binding.ADMISSION_SCHEMA,
            "generation": kwargs["entity_generation"],
            "canonical_state_hash": kwargs["compiled"]["canonical_state_hash"],
            "packet_hash": kwargs["compiled"]["packet_hash"],
            "inference": {"kind": "local"},
            "system": "s",
            "user": "u",
            "inference_packet_digest": "1" * 64,
            "cognitive_fabric_receipt_digest": "2" * 64,
            "admission_receipt": {
                "authority": "CANDIDATE_INFERENCE_ONLY",
                "real_effect_executed": False,
            },
        }
        if self.mutate is not None:
            result = self.mutate(copy.deepcopy(result))
        return result


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mini.db"
        self.profile = {
            "schema": "clay-pipeline-profile/v2",
            "profile_id": "p1",
            "inference": {"kind": "local"},
            "personality": {"output_contract": {}},
            "sources": [],
            "state_metrics": [],
            "gate": {},
        }
        raw = canonical_json(self.profile)
        self.profile_hash = hashlib.sha256(raw.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER,active_profile TEXT)")
        conn.execute("CREATE TABLE profiles(profile_id TEXT PRIMARY KEY,profile_json TEXT,profile_sha256 TEXT)")
        conn.execute("INSERT INTO entity_state VALUES(1,7,'p1')")
        conn.execute("INSERT INTO profiles VALUES(?,?,?)", ("p1", raw, self.profile_hash))
        conn.commit()
        conn.close()
        self.runtime = FakeRuntime(self.db_path)
        carried_profile = {
            **self.profile,
            "_runtime_profile_snapshot": {
                "profile_id": "p1",
                "profile_hash": self.profile_hash,
            },
        }
        self.payload = {
            "entity_db": str(self.db_path),
            "profile": carried_profile,
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

    def test_delegates_verified_runtime_profile_snapshot_on_read_only_db(self):
        compositor = RecordingCompositor()
        out = binding.admit_profile_runtime_payload(
            self.runtime, self.payload, compositor_module=compositor
        )
        self.assertTrue(out["ok"])
        kwargs, write_blocked = compositor.calls[0]
        self.assertTrue(write_blocked)
        self.assertEqual(kwargs["entity_generation"], 7)
        self.assertEqual(
            kwargs["profile"]["_runtime_profile_snapshot"],
            {"profile_id": "p1", "profile_hash": self.profile_hash},
        )
        persisted = dict(kwargs["profile"])
        persisted.pop("_runtime_profile_snapshot")
        self.assertEqual(persisted, self.profile)
        self.assertEqual(kwargs["origin"], binding.BINDING_VERSION)

    def test_rejects_profile_substitution_before_compositor(self):
        compositor = RecordingCompositor()
        poisoned = dict(self.payload)
        poisoned["profile"] = {**self.payload["profile"], "profile_id": "attacker"}
        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "RUNTIME_PROFILE_NOT_ACTIVE_MINIUNIFIEDDB_PROFILE",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime, poisoned, compositor_module=compositor
            )
        self.assertEqual(compositor.calls, [])

    def test_rejects_missing_runtime_snapshot(self):
        compositor = RecordingCompositor()
        poisoned = dict(self.payload)
        poisoned["profile"] = dict(self.profile)
        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "RUNTIME_PROFILE_SNAPSHOT_REQUIRED",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime, poisoned, compositor_module=compositor
            )
        self.assertEqual(compositor.calls, [])

    def test_rejects_forged_runtime_snapshot_hash(self):
        compositor = RecordingCompositor()
        poisoned = dict(self.payload)
        poisoned["profile"] = {
            **self.profile,
            "_runtime_profile_snapshot": {
                "profile_id": "p1",
                "profile_hash": "f" * 64,
            },
        }
        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "RUNTIME_PROFILE_SNAPSHOT_HASH_MISMATCH",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime, poisoned, compositor_module=compositor
            )
        self.assertEqual(compositor.calls, [])

    def test_rejects_runtime_snapshot_extra_authority_fields(self):
        compositor = RecordingCompositor()
        poisoned = dict(self.payload)
        poisoned["profile"] = {
            **self.profile,
            "_runtime_profile_snapshot": {
                "profile_id": "p1",
                "profile_hash": self.profile_hash,
                "jspace_mode": "FULL_LOCAL_LATENT",
            },
        }
        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "RUNTIME_PROFILE_SNAPSHOT_FIELDS_MISMATCH",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime, poisoned, compositor_module=compositor
            )
        self.assertEqual(compositor.calls, [])

    def test_rejects_corrupt_active_profile_hash(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE profiles SET profile_sha256=?", ("0" * 64,))
        conn.commit()
        conn.close()
        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "ACTIVE_PROFILE_HASH_MISMATCH",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime, self.payload, compositor_module=RecordingCompositor()
            )

    def test_rejects_returned_identity_drift(self):
        def drift(result):
            result["canonical_state_hash"] = "d" * 64
            return result

        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "ADMISSION_CANONICAL_STATE_DRIFT",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime,
                self.payload,
                compositor_module=RecordingCompositor(drift),
            )

    def test_rejects_authority_escalation_and_precommit_final_receipt(self):
        def escalate(result):
            result["admission_receipt"]["authority"] = "CANONICAL_TRUTH"
            return result

        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "ADMISSION_AUTHORITY_ESCALATION",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime,
                self.payload,
                compositor_module=RecordingCompositor(escalate),
            )

        def premature(result):
            result["ucf_runtime_receipt_digest"] = "e" * 64
            return result

        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "PREINFERENCE_FINAL_UCF_RECEIPT_FORBIDDEN",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime,
                self.payload,
                compositor_module=RecordingCompositor(premature),
            )

    def test_rejects_placeholder_or_effect_executed_receipt(self):
        def placeholder(result):
            result["inference_packet_digest"] = "0" * 64
            return result

        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "inference_packet_digest:PLACEHOLDER_REJECTED",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime,
                self.payload,
                compositor_module=RecordingCompositor(placeholder),
            )

        def effect(result):
            result["admission_receipt"]["real_effect_executed"] = True
            return result

        with self.assertRaisesRegex(
            binding.ProfileRuntimeCognitiveFabricBindingError,
            "PREINFERENCE_EFFECT_EXECUTION_FORBIDDEN",
        ):
            binding.admit_profile_runtime_payload(
                self.runtime,
                self.payload,
                compositor_module=RecordingCompositor(effect),
            )


if __name__ == "__main__":
    unittest.main()
