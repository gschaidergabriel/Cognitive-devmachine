#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
MODULE = HERE.parent / "Xeno" / "entry_grid10_v1.py"
spec = importlib.util.spec_from_file_location("xeno_entry_grid10_v1", MODULE)
xeno = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = xeno
spec.loader.exec_module(xeno)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def base_entry() -> dict:
    return {
        "schema": xeno.ENTRY_SCHEMA,
        "ingress_kind": "human_prompt",
        "causal_id": "cause-A",
        "entity_generation": 7,
        "provenance": {"source": "user:gabriel", "sha256": digest("source-event-A")},
        "modality": "text",
        "observed_at_ns": 123456789,
        "payload_sha256": digest("hello"),
        "payload_bytes": 5,
        "permission_scopes": ["state.read"],
        "budget": {"max_tokens": 2048, "max_ms": 5000, "max_bytes": 4096},
    }


class XenoEntryGrid10Tests(unittest.TestCase):
    def test_admit_and_compile_exact_grid10(self):
        admitted = xeno.admit_entry(base_entry(), current_generation=7)
        plan = xeno.compile_grid10(admitted, physical_worker_lanes=2)
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(plan.physical_worker_lanes, 2)
        self.assertEqual({c.worker_lane for c in plan.cells}, {0, 1})
        self.assertTrue(all(c.effect_authority is False for c in plan.cells))
        self.assertEqual(plan.causal_id, admitted.causal_id)
        self.assertEqual(plan.entity_generation, 7)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(xeno.XenoEntryError, "STALE_ENTITY_GENERATION"):
            xeno.admit_entry(base_entry(), current_generation=8)

    def test_payload_budget_fails_closed(self):
        raw = base_entry()
        raw["budget"]["max_bytes"] = 4
        with self.assertRaisesRegex(xeno.XenoEntryError, "PAYLOAD_EXCEEDS_ENTRY_BUDGET"):
            xeno.admit_entry(raw, current_generation=7)

    def test_noncanonical_permission_input_fails(self):
        raw = base_entry()
        raw["permission_scopes"] = "state.read"
        with self.assertRaisesRegex(xeno.XenoEntryError, "PERMISSION_SCOPES_SEQUENCE_REQUIRED"):
            xeno.admit_entry(raw, current_generation=7)

    def test_same_entry_replay_is_deterministic(self):
        a = xeno.admit_entry(base_entry(), current_generation=7)
        b = xeno.admit_entry(copy.deepcopy(base_entry()), current_generation=7)
        self.assertEqual(a.entry_id, b.entry_id)
        self.assertEqual(xeno.compile_grid10(a, physical_worker_lanes=2).plan_id,
                         xeno.compile_grid10(b, physical_worker_lanes=2).plan_id)

    def test_causal_identity_changes_entry_and_plan_identity(self):
        raw_a = base_entry()
        raw_b = copy.deepcopy(raw_a)
        raw_b["causal_id"] = "cause-B"
        a = xeno.admit_entry(raw_a, current_generation=7)
        b = xeno.admit_entry(raw_b, current_generation=7)
        self.assertNotEqual(a.entry_id, b.entry_id)
        self.assertNotEqual(xeno.compile_grid10(a).plan_id, xeno.compile_grid10(b).plan_id)

    def test_provenance_changes_entry_and_plan_identity(self):
        raw_a = base_entry()
        raw_b = copy.deepcopy(raw_a)
        raw_b["provenance"]["source"] = "tool:effect-journal"
        raw_b["provenance"]["sha256"] = digest("source-event-B")
        a = xeno.admit_entry(raw_a, current_generation=7)
        b = xeno.admit_entry(raw_b, current_generation=7)
        self.assertNotEqual(a.entry_id, b.entry_id)
        self.assertNotEqual(xeno.compile_grid10(a).plan_id, xeno.compile_grid10(b).plan_id)

    def test_unusual_discriminator_entry_causal_alias_collision(self):
        raw_a = base_entry()
        raw_b = copy.deepcopy(raw_a)
        raw_b["causal_id"] = "cause-B"
        raw_b["provenance"] = {"source": "tool:effect-journal", "sha256": digest("source-event-B")}

        def lesioned_id(raw: dict) -> str:
            payload = {
                "schema": raw["schema"],
                "ingress_kind": raw["ingress_kind"],
                "entity_generation": raw["entity_generation"],
                "modality": raw["modality"],
                "payload_sha256": raw["payload_sha256"],
                "payload_bytes": raw["payload_bytes"],
            }
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            return hashlib.sha256(encoded).hexdigest()

        self.assertEqual(lesioned_id(raw_a), lesioned_id(raw_b))
        self.assertNotEqual(
            xeno.admit_entry(raw_a, current_generation=7).entry_id,
            xeno.admit_entry(raw_b, current_generation=7).entry_id,
        )


if __name__ == "__main__":
    unittest.main()
