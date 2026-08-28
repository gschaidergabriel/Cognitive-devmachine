#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from frankenstein2_cognitive_control_plane_v1 import CognitiveControlPlane
from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_fabric import Fabric
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult
from grid10_live_control_binding_v1 import (
    run_control_bound_cognitive_cycle,
    sanitized_control_receipt,
)


class FakeInference:
    def __init__(self):
        self.calls = []

    def __call__(self, messages, *, config):
        self.calls.append((messages, config))
        prompt = messages[-1]["content"]
        is_workspace = "ROLE=workspace/GWT fan-in" in prompt
        if is_workspace:
            content = json.dumps({
                "synthesis": "bounded synthesis",
                "preserved_alternatives": ["A"],
                "disagreements": [],
                "evidence_requests": ["receipt"],
                "recommended_action": "ACT_CANDIDATE",
            })
        else:
            content = json.dumps({
                "candidate": "candidate only",
                "alternatives": ["alt"],
                "evidence_needed": ["evidence"],
                "confidence": 0.5,
                "unresolved": True,
            })
        idx = len(self.calls)
        return GLMInferenceResult(
            content=content,
            reasoning_content=None,
            receipt=GLMInferenceReceipt(
                provider="FAKE",
                model_requested="fake",
                model_reported="fake",
                request_digest=f"req-{idx}",
                response_digest=f"resp-{idx}",
                latency_ms=1.0,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                thinking_enabled=config.thinking,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                finish_reason="stop",
                response_id=f"fake-{idx}",
                secret_recorded=False,
            ),
        )


class LiveControlBindingTests(unittest.TestCase):
    def _fixture(self, td: str):
        path = Path(td) / "unified.sqlite"
        return Fabric(path), CognitiveControlPlane(path)

    def _patch(self, plane: CognitiveControlPlane, patch_id: str, changes):
        base = plane.snapshot()
        patch = plane.build_patch(
            patch_id=patch_id,
            writer="test",
            writer_kind="EXPERIMENT",
            reason="deterministic component test",
            changes=changes,
            base=base,
        )
        receipt = plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        return plane.snapshot()

    def test_compute_output_memory_modes_are_mechanically_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self._fixture(td)
            snapshot = self._patch(plane, "modes", {
                "grid.hypothesis.mode": "COMPUTE_OFF",
                "grid.planning.mode": "OUTPUT_OFF",
                "grid.world.mode": "MEMORY_OFF",
            })
            fake = FakeInference()
            result = run_control_bound_cognitive_cycle(
                tick_id="tick-modes",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                fabric=fabric,
                context={"goal": "g"},
                control_snapshot=snapshot,
                config=CognitiveCycleConfig(thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            by_id = {c.cell_id: c for c in result.cycle.cells}
            self.assertEqual(by_id[6].status, "NOT_COMPUTED")
            self.assertEqual(by_id[6].total_tokens, 0)
            self.assertEqual(by_id[4].status, "OUTPUT_OFF")
            self.assertEqual(by_id[4].candidate, "")
            self.assertNotEqual(by_id[5].candidate, "")
            self.assertNotIn(4, result.memory_reentry_eligible_cell_ids)
            self.assertNotIn(5, result.memory_reentry_eligible_cell_ids)
            self.assertNotIn(6, result.memory_reentry_eligible_cell_ids)
            self.assertEqual(len(fake.calls), 9)
            self.assertNotIn(6, result.cycle.workspace.active_cells)

    def test_gain_changes_real_token_budget_and_zero_gain_still_computes(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self._fixture(td)
            snapshot = self._patch(plane, "gain", {
                "grid.goal.gain": 0.25,
                "grid.orientation.gain": 0.0,
            })
            fake = FakeInference()
            result = run_control_bound_cognitive_cycle(
                tick_id="tick-gain",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                fabric=fabric,
                context={"goal": "g"},
                control_snapshot=snapshot,
                config=CognitiveCycleConfig(max_tokens_per_specialist=160, thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            plans = {p.role: p for p in result.cell_plans}
            self.assertTrue(plans["state"].compute)
            self.assertEqual(plans["state"].max_tokens, 32)
            self.assertEqual(plans["goal"].max_tokens, 40)
            goal_configs = [
                cfg for messages, cfg in fake.calls
                if "ROLE=goal" in messages[-1]["content"]
            ]
            self.assertEqual(len(goal_configs), 1)
            self.assertEqual(goal_configs[0].max_tokens, 40)

    def test_midcycle_patch_cannot_change_already_latched_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self._fixture(td)
            latched = plane.snapshot()
            self._patch(plane, "after-latch", {"grid.hypothesis.mode": "COMPUTE_OFF"})
            fake = FakeInference()
            result = run_control_bound_cognitive_cycle(
                tick_id="tick-latched",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                fabric=fabric,
                context={"goal": "g"},
                control_snapshot=latched,
                config=CognitiveCycleConfig(thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            by_id = {c.cell_id: c for c in result.cycle.cells}
            self.assertNotEqual(by_id[6].status, "NOT_COMPUTED")
            self.assertEqual(result.control_epoch, latched.control_epoch)
            self.assertEqual(result.control_snapshot_digest, latched.snapshot_digest)
            self.assertEqual(len(fake.calls), 10)

    def test_receipt_is_text_free_and_binds_control_revision(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self._fixture(td)
            snapshot = plane.snapshot()
            fake = FakeInference()
            result = run_control_bound_cognitive_cycle(
                tick_id="tick-receipt",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                fabric=fabric,
                context={"secretish": "do-not-persist"},
                control_snapshot=snapshot,
                config=CognitiveCycleConfig(thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            receipt = sanitized_control_receipt(result)
            text = json.dumps(receipt, sort_keys=True)
            self.assertNotIn("candidate only", text)
            self.assertNotIn("do-not-persist", text)
            self.assertEqual(receipt["control_epoch"], snapshot.control_epoch)
            self.assertEqual(receipt["control_snapshot_digest"], snapshot.snapshot_digest)
            self.assertFalse(receipt["canonical_truth_minted"])
            self.assertFalse(receipt["external_effect_executed"])


if __name__ == "__main__":
    unittest.main()
