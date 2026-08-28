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
from grid10_live_control_binding_v1 import ROLE_CONTROL_STEM
from grid10_live_control_binding_v2 import (
    run_control_bound_cognitive_cycle_v2,
    sanitized_control_receipt_v2,
)


class FakeInference:
    """Deterministic fake. No provider/network I/O."""

    def __init__(self):
        self.calls = []

    def __call__(self, messages, *, config):
        self.calls.append((messages, config))
        prompt = messages[-1]["content"]
        is_workspace = "ROLE=workspace/GWT fan-in" in prompt
        role = "workspace"
        if not is_workspace:
            for line in prompt.splitlines():
                if line.startswith("ROLE="):
                    role = line.split("=", 1)[1].strip()
                    break
        if is_workspace:
            content = json.dumps({
                "synthesis": "workspace-secret",
                "preserved_alternatives": [],
                "disagreements": [],
                "evidence_requests": ["receipt"],
                "recommended_action": "OBSERVE",
            })
        else:
            content = json.dumps({
                "candidate": f"candidate-secret:{role}",
                "alternatives": [],
                "evidence_needed": [f"evidence:{role}"],
                "confidence": 0.6,
                "unresolved": False,
            })
        idx = len(self.calls)
        return GLMInferenceResult(
            content=content,
            reasoning_content=None,
            receipt=GLMInferenceReceipt(
                provider="FAKE_NO_NETWORK",
                model_requested="fake",
                model_reported="fake",
                request_digest=f"req-{idx}",
                response_digest=f"resp-{idx}",
                latency_ms=1.0,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                thinking_enabled=bool(config.thinking),
                max_tokens=int(config.max_tokens),
                temperature=float(config.temperature),
                top_p=float(config.top_p),
                finish_reason="stop",
                response_id=f"fake-{idx}",
                secret_recorded=False,
            ),
        )


class LiveControlBindingV2Tests(unittest.TestCase):
    def fixture(self, td: str):
        db = Path(td) / "unified.sqlite"
        return Fabric(db), CognitiveControlPlane(db)

    def patch(self, plane: CognitiveControlPlane, patch_id: str, changes: dict[str, object]):
        base = plane.snapshot()
        patch = plane.build_patch(
            patch_id=patch_id,
            writer="test",
            writer_kind="EXPERIMENT",
            reason="LC-14 GWT ignition consumer test",
            changes=changes,
            base=base,
        )
        receipt = plane.apply_patch(patch)
        self.assertTrue(receipt.accepted, receipt)
        return plane.snapshot()

    def run_cycle(self, fabric, snapshot, fake):
        return run_control_bound_cognitive_cycle_v2(
            tick_id="ignition-test",
            assurance_mode=AssuranceMode.NORMAL,
            controller_action="OBSERVE",
            fabric=fabric,
            context={"goal": "prove GWT gate"},
            control_snapshot=snapshot,
            config=CognitiveCycleConfig(
                max_parallel_specialists=1,
                thinking_for_deep_roles=False,
            ),
            inference_fn=fake,
        )

    def test_default_profile_ignites_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self.fixture(td)
            fake = FakeInference()
            result = self.run_cycle(fabric, plane.snapshot(), fake)
            self.assertTrue(result.workspace_ignited)
            self.assertEqual(result.workspace_ignition_threshold, 0.5)
            self.assertIn(9, result.cycle.workspace.active_cells)
            self.assertEqual(len(fake.calls), 10)  # nine specialists + one GWT workspace
            self.assertTrue(any("ROLE=workspace/GWT fan-in" in m[-1]["content"] for m, _ in fake.calls))

    def test_subthreshold_specialists_compute_but_workspace_is_not_called(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self.fixture(td)
            changes = {f"{stem}.gain": 0.25 for stem in ROLE_CONTROL_STEM.values()}
            changes["grid.workspace_ignition_threshold"] = 0.5
            snapshot = self.patch(plane, "all-subthreshold", changes)
            fake = FakeInference()
            result = self.run_cycle(fabric, snapshot, fake)
            self.assertFalse(result.workspace_ignited)
            self.assertEqual(result.gwt_eligible_cell_ids, ())
            self.assertNotIn(9, result.cycle.workspace.active_cells)
            self.assertEqual(result.cycle.workspace.evidence_requests, ("GWT_NOT_IGNITED",))
            self.assertEqual(len(fake.calls), 9)  # specialist compute still happened
            self.assertFalse(any("ROLE=workspace/GWT fan-in" in m[-1]["content"] for m, _ in fake.calls))
            self.assertTrue(all(c.status == "IGNITION_BELOW_THRESHOLD" for c in result.cycle.cells))

    def test_subthreshold_cell_payload_is_absent_from_workspace_fanin(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self.fixture(td)
            snapshot = self.patch(
                plane,
                "planner-subthreshold",
                {
                    "grid.workspace_ignition_threshold": 0.5,
                    "grid.planning.gain": 0.25,
                },
            )
            fake = FakeInference()
            result = self.run_cycle(fabric, snapshot, fake)
            planner = next(c for c in result.cycle.cells if c.role == "planner")
            self.assertEqual(planner.status, "IGNITION_BELOW_THRESHOLD")
            self.assertEqual(planner.candidate, "")
            self.assertNotIn(planner.cell_id, result.gwt_eligible_cell_ids)
            workspace_prompts = [
                m[-1]["content"] for m, _ in fake.calls
                if "ROLE=workspace/GWT fan-in" in m[-1]["content"]
            ]
            self.assertEqual(len(workspace_prompts), 1)
            self.assertNotIn("candidate-secret:planner", workspace_prompts[0])
            self.assertIn("GWT_ELIGIBLE_CELL_IDS=", workspace_prompts[0])

    def test_receipt_proves_gate_without_model_text(self):
        with tempfile.TemporaryDirectory() as td:
            fabric, plane = self.fixture(td)
            changes = {f"{stem}.gain": 0.1 for stem in ROLE_CONTROL_STEM.values()}
            snapshot = self.patch(plane, "receipt-subthreshold", changes)
            result = self.run_cycle(fabric, snapshot, FakeInference())
            receipt = sanitized_control_receipt_v2(result)
            text = json.dumps(receipt, sort_keys=True)
            self.assertFalse(receipt["workspace_ignited"])
            self.assertEqual(receipt["workspace_ignition_threshold"], 0.5)
            self.assertNotIn("candidate-secret", text)
            self.assertNotIn("workspace-secret", text)
            self.assertFalse(receipt["canonical_truth_minted"])
            self.assertFalse(receipt["external_effect_executed"])
            self.assertFalse(receipt["completion_minted"])


if __name__ == "__main__":
    unittest.main()
