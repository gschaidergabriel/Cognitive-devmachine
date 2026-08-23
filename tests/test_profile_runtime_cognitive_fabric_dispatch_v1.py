#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import clay_profile_pipeline_runtime as runtime_mod
import profile_runtime_cognitive_fabric_binding_v1 as binding


def canonical_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


class RecordingCompositor:
    def __init__(self):
        self.calls = []

    def build_pre_inference_admission(self, db, **kwargs):
        write_blocked = False
        try:
            db.execute("CREATE TABLE dispatched_forbidden_write(x INTEGER)")
        except sqlite3.OperationalError:
            write_blocked = True
        self.calls.append((kwargs, write_blocked))
        return {
            "ok": True,
            "generation": kwargs["entity_generation"],
            "inference": {"kind": "mock", "model": "candidate-only"},
            "system": "system",
            "user": "user",
            "inference_packet_digest": "1" * 64,
            "cognitive_fabric_receipt_digest": "2" * 64,
        }


class RuntimeCognitiveFabricDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "mini.db"
        self.runtime = runtime_mod.ProfilePipelineRuntime(root=self.root)
        self.profile = {
            "schema": "clay-pipeline-profile/v2",
            "profile_id": "p1",
            "inference": {"kind": "mock", "model": "candidate-only"},
            "personality": {"output_contract": {}},
            "sources": [],
            "state_metrics": [],
            "gate": {},
        }
        raw = canonical_json(self.profile)
        self.profile_hash = hashlib.sha256(raw.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER,active_profile TEXT)"
        )
        conn.execute(
            "CREATE TABLE profiles(profile_id TEXT PRIMARY KEY,profile_json TEXT,profile_sha256 TEXT)"
        )
        conn.execute("INSERT INTO entity_state VALUES(1,11,'p1')")
        conn.execute(
            "INSERT INTO profiles VALUES(?,?,?)", ("p1", raw, self.profile_hash)
        )
        conn.commit()
        conn.close()
        self.payload = {
            "entity_db": "mini.db",
            "profile": {
                **self.profile,
                "_runtime_profile_snapshot": {
                    "profile_id": "p1",
                    "profile_hash": self.profile_hash,
                },
            },
            "data": {
                "compiled": {
                    "canonical_state_hash": "a" * 64,
                    "packet_hash": "b" * 64,
                },
                "prompt": {"system": "system", "user": "{}"},
                "invocation": {
                    "expected_generation": 11,
                    "causal_turn_id": "ct11",
                    "task_text": "task",
                    "turn_binding_digest": "c" * 64,
                },
            },
        }
        self.original_compositor = binding.canonical_admission

    def tearDown(self):
        binding.canonical_admission = self.original_compositor
        self.tmp.cleanup()

    def test_retained_runtime_dispatches_single_read_only_admission_bridge(self):
        compositor = RecordingCompositor()
        binding.canonical_admission = compositor
        out = self.runtime.effect("pipeline_cognitive_fabric_admit", self.payload)
        self.assertTrue(out["ok"])
        self.assertEqual(out["generation"], 11)
        self.assertEqual(len(compositor.calls), 1)
        kwargs, write_blocked = compositor.calls[0]
        self.assertTrue(write_blocked)
        self.assertEqual(kwargs["entity_generation"], 11)
        self.assertEqual(kwargs["origin"], binding.BINDING_VERSION)
        self.assertEqual(self.runtime.effect_trace[-1]["kind"], "pipeline_cognitive_fabric_admit")
        self.assertTrue(self.runtime.effect_trace[-1]["ok"])

    def test_binding_fault_fails_closed_at_runtime_effect_boundary(self):
        compositor = RecordingCompositor()
        binding.canonical_admission = compositor
        poisoned = dict(self.payload)
        poisoned["profile"] = dict(self.profile)
        out = self.runtime.effect("pipeline_cognitive_fabric_admit", poisoned)
        self.assertFalse(out["ok"])
        self.assertEqual(out["error_kind"], "ProfileRuntimeCognitiveFabricBindingError")
        self.assertIn("RUNTIME_PROFILE_SNAPSHOT_REQUIRED", out["error"])
        self.assertEqual(compositor.calls, [])
        self.assertEqual(self.runtime.effect_trace[-1]["kind"], "pipeline_cognitive_fabric_admit")
        self.assertFalse(self.runtime.effect_trace[-1]["ok"])


if __name__ == "__main__":
    unittest.main()
