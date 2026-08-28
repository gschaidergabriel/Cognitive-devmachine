#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v6 import build_unified_cognitive_runtime_v6
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult


class FakeInference:
    def __init__(self):
        self.calls = []
        self.workspace_calls = 0

    def __call__(self, messages, *, config):
        self.calls.append((messages, config))
        prompt = messages[-1]["content"]
        is_workspace = "ROLE=workspace/GWT fan-in" in prompt
        if is_workspace:
            self.workspace_calls += 1
            content = json.dumps({
                "synthesis": "workspace-bounded",
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


class UnifiedRuntimeV6Tests(unittest.TestCase):
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
            reason="deterministic v6 regression",
            changes=changes,
            base=base,
        )
        receipt = runtime.control_plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        return runtime.control_plane.snapshot()

    def test_same_snapshot_can_run_specialists_without_igniting_workspace(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v6(
            self.db,
            inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )
        low = {
            "grid.orientation.gain": 0.25,
            "grid.retrieval.gain": 0.25,
            "grid.goal.gain": 0.25,
            "grid.critic.gain": 0.25,
            "grid.planning.gain": 0.25,
            "grid.world.gain": 0.25,
            "grid.hypothesis.gain": 0.25,
            "grid.epistemic.gain": 0.25,
            "grid.delegation.gain": 0.25,
            "grid.workspace_ignition_threshold": 0.75,
            "pulse.active_interval_seconds": 0.25,
        }
        snapshot = self._patch(runtime, "subthreshold-grid", low)
        cycle = runtime.tick_once(
            tick_id="v6-subthreshold",
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
            cognitive_context={"goal": "g"},
        )

        self.assertEqual(cycle.next_tick_not_before, 100.25)
        self.assertEqual(cycle.control_snapshot_digest, snapshot.snapshot_digest)
        self.assertEqual(
            cycle.checkpoint["v4_checkpoint_control_snapshot"]["snapshot_digest"],
            snapshot.snapshot_digest,
        )
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        self.assertEqual(controlled.control_snapshot_digest, snapshot.snapshot_digest)
        self.assertFalse(controlled.workspace_ignited)
        self.assertEqual(controlled.gwt_eligible_cell_ids, ())
        self.assertEqual(fake.workspace_calls, 0)
        self.assertEqual(len(fake.calls), 9)
        self.assertEqual(controlled.cycle.workspace.evidence_requests, ("GWT_NOT_IGNITED",))
        self.assertEqual(controlled.cycle.workspace.active_cells, ())
        self.assertTrue(all(cell.status == "IGNITION_BELOW_THRESHOLD" for cell in controlled.cycle.cells))

        receipt = cycle.checkpoint["controlled_cognitive_cycle_receipt"]
        self.assertFalse(receipt["workspace_ignited"])
        self.assertEqual(receipt["gwt_eligible_cell_ids"], [])
        receipt_text = json.dumps(receipt, sort_keys=True)
        self.assertNotIn("candidate-only-text", receipt_text)

        con = sqlite3.connect(str(self.db))
        try:
            row = con.execute(
                "SELECT control_snapshot_digest,workspace_ignited,workspace_ignition_threshold,receipt_digest "
                "FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (cycle.tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row[0], snapshot.snapshot_digest)
        self.assertEqual(row[1], 0)
        self.assertEqual(row[2], 0.75)
        self.assertEqual(row[3], cycle.receipt_digest)

    def test_default_gain_ignites_workspace_and_receipt_records_gate(self):
        fake = FakeInference()
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v6(
            self.db,
            inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )
        cycle = runtime.tick_once(
            tick_id="v6-ignite",
            now_ts=200.0,
            trusted_axes=_trusted_normal_axes(),
            cognitive_context={"goal": "g"},
        )
        controlled = cycle.controlled_cognitive_cycle
        self.assertIsNotNone(controlled)
        assert controlled is not None
        self.assertTrue(controlled.workspace_ignited)
        self.assertEqual(len(controlled.gwt_eligible_cell_ids), 9)
        self.assertEqual(fake.workspace_calls, 1)
        self.assertEqual(len(fake.calls), 10)
        self.assertTrue(cycle.checkpoint["workspace_ignited"])
        self.assertEqual(cycle.checkpoint["workspace_ignition_threshold"], 0.5)

    def test_no_inference_function_means_zero_provider_calls(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v6(self.db)
        cycle = runtime.tick_once(
            tick_id="v6-provider-off",
            now_ts=300.0,
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
