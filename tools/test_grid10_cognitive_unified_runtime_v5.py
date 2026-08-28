#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v5 import build_unified_cognitive_runtime_v5
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult
from grid10_live_control_binding_v1 import ROLE_CONTROL_STEM


class FakeInference:
    def __init__(self):
        self.calls = []

    def __call__(self, messages, *, config):
        self.calls.append((messages, config))
        prompt = messages[-1]["content"]
        is_workspace = "ROLE=workspace/GWT fan-in" in prompt
        if is_workspace:
            content = json.dumps({
                "synthesis": "bounded",
                "preserved_alternatives": ["alt"],
                "disagreements": [],
                "evidence_requests": ["receipt"],
                "recommended_action": "ACT_CANDIDATE",
            })
        else:
            content = json.dumps({
                "candidate": "candidate-only-text",
                "alternatives": ["counter"],
                "evidence_needed": ["runtime"],
                "confidence": 0.5,
                "unresolved": True,
            })
        i = len(self.calls)
        return GLMInferenceResult(
            content=content,
            reasoning_content=None,
            receipt=GLMInferenceReceipt(
                provider="FAKE", model_requested="fake", model_reported="fake",
                request_digest=f"req-{i}", response_digest=f"resp-{i}", latency_ms=1.0,
                prompt_tokens=10, completion_tokens=5, total_tokens=15,
                thinking_enabled=config.thinking, max_tokens=config.max_tokens,
                temperature=config.temperature, top_p=config.top_p, finish_reason="stop",
                response_id=f"fake-{i}", secret_recorded=False,
            ),
        )


class UnifiedRuntimeV5Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"

    def tearDown(self):
        self.td.cleanup()

    def _patch(self, runtime, patch_id, changes):
        base = runtime.control_plane.snapshot()
        patch = runtime.control_plane.build_patch(
            patch_id=patch_id, writer="unit-test", writer_kind="EXPERIMENT",
            reason="deterministic v5 regression", changes=changes, base=base,
        )
        receipt = runtime.control_plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        return runtime.control_plane.snapshot()

    def test_same_latched_snapshot_drives_v4_pulse_and_fake_grid_cycle(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(
            self.db, inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )
        snapshot = self._patch(runtime, "same-frame", {
            "pulse.active_interval_seconds": 0.25,
            "grid.hypothesis.mode": "COMPUTE_OFF",
        })
        cycle = runtime.tick_once(
            tick_id="v5-same-frame", now_ts=100.0,
            trusted_axes=_trusted_normal_axes(), cognitive_context={"goal": "g"},
        )
        self.assertEqual(cycle.next_tick_not_before, 100.25)
        self.assertEqual(cycle.control_epoch, snapshot.control_epoch)
        self.assertEqual(cycle.control_snapshot_digest, snapshot.snapshot_digest)
        self.assertEqual(
            cycle.checkpoint["v4_checkpoint_control_snapshot"]["snapshot_digest"],
            snapshot.snapshot_digest,
        )
        self.assertEqual(cycle.checkpoint["v4_control_snapshot_source"], "provided")
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        self.assertEqual(controlled.control_epoch, snapshot.control_epoch)
        self.assertEqual(controlled.control_snapshot_digest, snapshot.snapshot_digest)
        by_id = {cell.cell_id: cell for cell in controlled.cycle.cells}
        self.assertEqual(by_id[6].status, "NOT_COMPUTED")
        self.assertEqual(len(fake.calls), 9)
        receipt_text = json.dumps(cycle.checkpoint["controlled_cognitive_cycle_receipt"], sort_keys=True)
        self.assertNotIn("candidate-only-text", receipt_text)

        con = sqlite3.connect(str(self.db))
        try:
            row = con.execute(
                "SELECT control_snapshot_digest,receipt_digest FROM grid10_v5_control_bound_receipts WHERE tick_id=?",
                (cycle.tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row[0], snapshot.snapshot_digest)
        self.assertEqual(row[1], cycle.receipt_digest)

    def test_same_latched_snapshot_drives_mechanical_gwt_ignition(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(
            self.db, inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(
                max_parallel_specialists=1,
                thinking_for_deep_roles=False,
            ),
        )
        changes = {f"{stem}.gain": 0.1 for stem in ROLE_CONTROL_STEM.values()}
        changes["grid.workspace_ignition_threshold"] = 0.5
        snapshot = self._patch(runtime, "gwt-subthreshold", changes)
        cycle = runtime.tick_once(
            tick_id="v5-gwt-subthreshold", now_ts=100.0,
            trusted_axes=_trusted_normal_axes(), cognitive_context={"goal": "g"},
        )
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        self.assertEqual(controlled.control_snapshot_digest, snapshot.snapshot_digest)
        self.assertEqual(controlled.workspace_ignition_threshold, 0.5)
        self.assertFalse(controlled.workspace_ignited)
        self.assertEqual(controlled.gwt_eligible_cell_ids, ())
        self.assertNotIn(9, controlled.cycle.workspace.active_cells)
        self.assertEqual(controlled.cycle.workspace.evidence_requests, ("GWT_NOT_IGNITED",))
        self.assertEqual(len(fake.calls), 9)
        self.assertFalse(any(
            "ROLE=workspace/GWT fan-in" in messages[-1]["content"]
            for messages, _ in fake.calls
        ))
        receipt = cycle.checkpoint["controlled_cognitive_cycle_receipt"]
        self.assertFalse(receipt["workspace_ignited"])
        self.assertEqual(receipt["workspace_ignition_threshold"], 0.5)
        self.assertEqual(receipt["control_snapshot_digest"], snapshot.snapshot_digest)

    def test_zero_gain_is_not_compute_off_and_does_not_rewrite_v4_action(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(
            self.db, inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )
        self._patch(runtime, "zero-planning-gain", {"grid.planning.gain": 0.0})
        cycle = runtime.tick_once(
            tick_id="v5-zero-gain", now_ts=100.0,
            trusted_axes=_trusted_normal_axes(), cognitive_context={"goal": "g"},
        )
        self.assertEqual(cycle.raw_next_action, "ACT_CANDIDATE")
        self.assertEqual(cycle.next_action, "ACT_CANDIDATE")
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        planning = next(plan for plan in controlled.cell_plans if plan.role == "planner")
        self.assertTrue(planning.compute)
        self.assertEqual(planning.gain, 0.0)
        self.assertEqual(planning.max_tokens, 32)

    def test_compute_off_is_enforced_only_at_live_cell_binding(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(
            self.db, inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )
        self._patch(runtime, "planning-off", {
            "grid.planning.mode": "COMPUTE_OFF",
            "grid.planning.gain": 1.0,
        })
        cycle = runtime.tick_once(
            tick_id="v5-planning-off", now_ts=100.0,
            trusted_axes=_trusted_normal_axes(), cognitive_context={"goal": "g"},
        )
        self.assertEqual(cycle.next_action, "ACT_CANDIDATE")
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        planning = next(plan for plan in controlled.cell_plans if plan.role == "planner")
        self.assertFalse(planning.compute)
        planner_cell = next(cell for cell in controlled.cycle.cells if cell.role == "planner")
        self.assertEqual(planner_cell.status, "NOT_COMPUTED")

    def test_no_inference_function_means_zero_provider_calls_and_no_implicit_model(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(self.db)
        cycle = runtime.tick_once(
            tick_id="v5-provider-off", now_ts=200.0,
            trusted_axes=_trusted_normal_axes(),
        )
        self.assertIsNone(cycle.controlled_cognitive_cycle)
        receipt = cycle.checkpoint["controlled_cognitive_cycle_receipt"]
        self.assertEqual(receipt["reason"], "NO_EXPLICIT_ADMITTED_INFERENCE_FN")
        self.assertEqual(receipt["provider_calls"], 0)
        self.assertFalse(cycle.checkpoint["external_effect_executed"])
        self.assertFalse(cycle.checkpoint["canonical_truth_minted"])
        self.assertFalse(cycle.checkpoint["completion_minted"])


if __name__ == "__main__":
    unittest.main()
