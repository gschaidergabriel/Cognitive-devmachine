#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v5 import (
    _apply_grid_action_controls_v5,
    _grid_control_view_v5,
    build_unified_cognitive_runtime_v5,
)
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult


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
                provider="FAKE",
                model_requested="fake",
                model_reported="fake",
                request_digest=f"req-{i}",
                response_digest=f"resp-{i}",
                latency_ms=1.0,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                thinking_enabled=config.thinking,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                finish_reason="stop",
                response_id=f"fake-{i}",
                secret_recorded=False,
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
            patch_id=patch_id,
            writer="unit-test",
            writer_kind="EXPERIMENT",
            reason="deterministic v5 regression",
            changes=changes,
            base=base,
        )
        receipt = runtime.control_plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        return runtime.control_plane.snapshot()

    def test_zero_gain_is_not_compute_off_but_cannot_clear_salience_gate(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(self.db)
        snapshot = self._patch(runtime, "zero-gain", {"grid.planning.gain": 0.0})
        rows = {row["cell"]: row for row in _grid_control_view_v5(snapshot, "ACT_CANDIDATE")}
        self.assertTrue(rows["planning"]["compute_enabled"])
        self.assertTrue(rows["planning"]["output_enabled"])
        action, reasons, _ = _apply_grid_action_controls_v5(snapshot, "ACT_CANDIDATE")
        self.assertEqual(action, "OBSERVE")
        self.assertTrue(any(x.startswith("GRID_GAIN_BELOW_SALIENCE:") for x in reasons))
        self.assertFalse(any(x.startswith("GRID_MODE_BLOCK:") for x in reasons))

    def test_same_latched_snapshot_drives_pulse_action_and_fake_grid_cycle(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(
            self.db,
            inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )
        snapshot = self._patch(runtime, "same-frame", {
            "pulse.active_interval_seconds": 0.25,
            "grid.hypothesis.mode": "COMPUTE_OFF",
        })
        cycle = runtime.tick_once(
            tick_id="v5-same-frame",
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
            cognitive_context={"goal": "g"},
        )
        self.assertEqual(cycle.next_tick_not_before, 100.25)
        self.assertEqual(cycle.control_epoch, snapshot.control_epoch)
        self.assertEqual(cycle.control_snapshot_digest, snapshot.snapshot_digest)
        self.assertEqual(
            cycle.checkpoint["control_snapshot"]["snapshot_digest"],
            snapshot.snapshot_digest,
        )
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        self.assertEqual(controlled.control_epoch, snapshot.control_epoch)
        self.assertEqual(controlled.control_snapshot_digest, snapshot.snapshot_digest)
        by_id = {cell.cell_id: cell for cell in controlled.cycle.cells}
        self.assertEqual(by_id[6].status, "NOT_COMPUTED")
        self.assertEqual(len(fake.calls), 9)
        receipt_text = json.dumps(
            cycle.checkpoint["controlled_cognitive_cycle_receipt"],
            sort_keys=True,
        )
        self.assertNotIn("candidate-only-text", receipt_text)

    def test_no_inference_function_means_zero_provider_calls_and_no_implicit_model(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(self.db)
        cycle = runtime.tick_once(
            tick_id="v5-provider-off",
            now_ts=200.0,
            trusted_axes=_trusted_normal_axes(),
        )
        self.assertIsNone(cycle.controlled_cognitive_cycle)
        receipt = cycle.checkpoint["controlled_cognitive_cycle_receipt"]
        self.assertEqual(receipt["reason"], "NO_EXPLICIT_ADMITTED_INFERENCE_FN")
        self.assertEqual(receipt["provider_calls"], 0)
        self.assertFalse(cycle.checkpoint["external_effect_executed"])

    def test_compute_off_remains_mode_block_distinct_from_gain(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v5(self.db)
        snapshot = self._patch(
            runtime,
            "compute-off",
            {"grid.planning.mode": "COMPUTE_OFF", "grid.planning.gain": 1.0},
        )
        rows = {row["cell"]: row for row in _grid_control_view_v5(snapshot, "ACT_CANDIDATE")}
        self.assertFalse(rows["planning"]["compute_enabled"])
        action, reasons, _ = _apply_grid_action_controls_v5(snapshot, "ACT_CANDIDATE")
        self.assertEqual(action, "OBSERVE")
        self.assertTrue(any(x.startswith("GRID_MODE_BLOCK:planning") for x in reasons))


if __name__ == "__main__":
    unittest.main()
