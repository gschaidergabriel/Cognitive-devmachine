#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest

from frankenstein2_cognitive_control_plane_v1 import CognitiveControlPlane
from grid10_cognitive_control_bound_runtime_v1 import (
    build_control_bound_unified_runtime,
    run_controlled_cognitive_cycle_from_plane,
    sanitized_receipt,
)
from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult


class FakeInference:
    """Deterministic inference stub; never performs provider/network I/O."""

    def __init__(self, *, mutate_plane: CognitiveControlPlane | None = None):
        self.calls: list[tuple[list[dict[str, str]], object]] = []
        self.mutate_plane = mutate_plane
        self._mutated = False
        self._lock = threading.Lock()

    @staticmethod
    def _role(text: str) -> str:
        first = text.splitlines()[0] if text else ""
        return first.split("=", 1)[1] if first.startswith("ROLE=") else "unknown"

    def __call__(self, messages, *, config):
        with self._lock:
            idx = len(self.calls) + 1
            self.calls.append((messages, config))
            if self.mutate_plane is not None and not self._mutated:
                self._mutated = True
                base = self.mutate_plane.snapshot()
                patch = self.mutate_plane.build_patch(
                    patch_id="mid-cycle-hypothesis-gain",
                    writer="test-human",
                    writer_kind="HUMAN",
                    reason="LC-9 mid-cycle patch discriminator",
                    changes={"grid.hypothesis.gain": 2.5},
                    base=base,
                )
                self.mutate_plane.apply_patch(patch)

        prompt = messages[-1]["content"]
        role = self._role(prompt)
        is_workspace = role == "workspace/GWT fan-in"
        if is_workspace:
            content = json.dumps({
                "synthesis": "workspace-secret-synthesis",
                "preserved_alternatives": ["A", "B"],
                "disagreements": ["d1"],
                "evidence_requests": ["runtime-receipt"],
                "recommended_action": "ACT_CANDIDATE",
            })
        else:
            content = json.dumps({
                "candidate": f"candidate-secret:{role}",
                "alternatives": [f"alt:{role}"],
                "evidence_needed": [f"evidence:{role}"],
                "confidence": 0.6,
                "unresolved": True,
            })
        receipt = GLMInferenceReceipt(
            provider="FAKE_NO_NETWORK",
            model_requested="fake",
            model_reported="fake",
            request_digest=f"req-{idx}",
            response_digest=f"resp-{idx}",
            latency_ms=float(idx),
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
        )
        return GLMInferenceResult(content=content, reasoning_content=None, receipt=receipt)


class ControlBoundRuntimeTests(unittest.TestCase):
    def _patch(self, plane: CognitiveControlPlane, patch_id: str, changes: dict[str, object]):
        base = plane.snapshot()
        patch = plane.build_patch(
            patch_id=patch_id,
            writer="test-human",
            writer_kind="HUMAN",
            reason="deterministic component discriminator",
            changes=changes,
            base=base,
        )
        return plane.apply_patch(patch)

    def test_pulse_latches_snapshot_and_uses_live_idle_cadence(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "unified.sqlite"
            _, _, _, plane, runtime, _ = build_control_bound_unified_runtime(db)
            self._patch(plane, "idle-seven", {"pulse.idle_interval_seconds": 7.0})
            expected = plane.snapshot()

            first = runtime.tick_once(
                tick_id="pulse-1",
                now_ts=100.0,
                trusted_axes=_trusted_normal_axes(),
            )
            self.assertEqual(first.control_snapshot.snapshot_digest, expected.snapshot_digest)
            self.assertEqual(first.cadence_control, "pulse.idle_interval_seconds")
            self.assertAlmostEqual(first.cadence_seconds, 7.0)
            self.assertAlmostEqual(first.next_tick_not_before, 107.0)
            self.assertEqual(first.checkpoint["control_snapshot_digest"], expected.snapshot_digest)
            self.assertEqual(first.binding.control_snapshot_digest, expected.snapshot_digest)

            self._patch(plane, "idle-two", {"pulse.idle_interval_seconds": 2.0})
            second = runtime.tick_once(
                tick_id="pulse-2",
                now_ts=107.0,
                trusted_axes=_trusted_normal_axes(),
            )
            self.assertNotEqual(second.control_snapshot.snapshot_digest, expected.snapshot_digest)
            self.assertAlmostEqual(second.cadence_seconds, 2.0)
            self.assertAlmostEqual(second.next_tick_not_before, 109.0)

    def test_grid_modes_are_mechanically_distinct_and_fanin_respects_output_off(self):
        with tempfile.TemporaryDirectory() as td:
            plane = CognitiveControlPlane(Path(td) / "u.sqlite")
            self._patch(
                plane,
                "mode-lesion",
                {
                    "grid.world.mode": "COMPUTE_OFF",
                    "grid.hypothesis.mode": "OUTPUT_OFF",
                    "grid.retrieval.mode": "MEMORY_OFF",
                    "grid.planning.gain": 1.75,
                },
            )
            fake = FakeInference()
            result = run_controlled_cognitive_cycle_from_plane(
                control_plane=plane,
                tick_id="grid-modes",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                context={"goal": "prove mode semantics"},
                config=CognitiveCycleConfig(max_parallel_specialists=1, thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            cells = {c.role: c for c in result.cells}
            self.assertFalse(cells["simulator"].computed)
            self.assertEqual(cells["simulator"].status, "NOT_COMPUTED")
            self.assertTrue(cells["skeptic"].computed)
            self.assertFalse(cells["skeptic"].output_visible)
            self.assertEqual(cells["skeptic"].candidate, "")
            self.assertTrue(cells["memory"].computed)
            self.assertTrue(cells["memory"].output_visible)
            self.assertFalse(cells["memory"].memory_reentry_allowed)
            self.assertAlmostEqual(cells["planner"].control_gain, 1.75)
            self.assertNotIn(5, result.workspace.active_cells)
            self.assertIn(9, result.workspace.active_cells)
            # 8 computed specialists + one workspace. COMPUTE_OFF is a real compute lesion.
            self.assertEqual(len(fake.calls), 9)
            workspace_prompts = [m[-1]["content"] for m, _ in fake.calls if "ROLE=workspace/GWT fan-in" in m[-1]["content"]]
            self.assertEqual(len(workspace_prompts), 1)
            self.assertNotIn("candidate-secret:skeptic", workspace_prompts[0])
            self.assertIn("OUTPUT_OFF", workspace_prompts[0])
            digests = {c.control_snapshot_digest for c in result.cells}
            self.assertEqual(digests, {result.workspace.control_snapshot_digest})

    def test_workspace_ignition_threshold_skips_fanin_compute(self):
        with tempfile.TemporaryDirectory() as td:
            plane = CognitiveControlPlane(Path(td) / "u.sqlite")
            self._patch(plane, "high-ignition", {"grid.workspace_ignition_threshold": 0.9})
            fake = FakeInference()
            result = run_controlled_cognitive_cycle_from_plane(
                control_plane=plane,
                tick_id="grid-no-ignite",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="SEARCH",
                context={"uncertainty": 0.2},
                workspace_ignition_signal=0.2,
                config=CognitiveCycleConfig(max_parallel_specialists=1, thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            self.assertFalse(result.workspace.computed)
            self.assertEqual(result.workspace.status, "NOT_COMPUTED_THRESHOLD")
            self.assertNotIn(9, result.workspace.active_cells)
            self.assertEqual(len(fake.calls), 9)
            self.assertFalse(any("ROLE=workspace/GWT fan-in" in m[-1]["content"] for m, _ in fake.calls))

    def test_mid_cycle_patch_cannot_mix_snapshot_and_next_cycle_adopts_it(self):
        with tempfile.TemporaryDirectory() as td:
            plane = CognitiveControlPlane(Path(td) / "u.sqlite")
            before = plane.snapshot()
            fake = FakeInference(mutate_plane=plane)
            first = run_controlled_cognitive_cycle_from_plane(
                control_plane=plane,
                tick_id="cycle-old",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                context={"case": "LC-9"},
                config=CognitiveCycleConfig(max_parallel_specialists=1, thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            skeptic_first = next(c for c in first.cells if c.role == "skeptic")
            self.assertEqual(first.workspace.control_snapshot_digest, before.snapshot_digest)
            self.assertTrue(all(c.control_snapshot_digest == before.snapshot_digest for c in first.cells))
            self.assertAlmostEqual(skeptic_first.control_gain, 1.0)

            after = plane.snapshot()
            self.assertNotEqual(after.snapshot_digest, before.snapshot_digest)
            self.assertAlmostEqual(after.float("grid.hypothesis.gain"), 2.5)

            second = run_controlled_cognitive_cycle_from_plane(
                control_plane=plane,
                tick_id="cycle-new",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                context={"case": "LC-9-next"},
                config=CognitiveCycleConfig(max_parallel_specialists=1, thinking_for_deep_roles=False),
                inference_fn=FakeInference(),
            )
            skeptic_second = next(c for c in second.cells if c.role == "skeptic")
            self.assertEqual(second.workspace.control_snapshot_digest, after.snapshot_digest)
            self.assertAlmostEqual(skeptic_second.control_gain, 2.5)

    def test_sanitized_receipt_excludes_prompts_and_model_text(self):
        with tempfile.TemporaryDirectory() as td:
            plane = CognitiveControlPlane(Path(td) / "u.sqlite")
            result = run_controlled_cognitive_cycle_from_plane(
                control_plane=plane,
                tick_id="receipt",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                context={"sensitive": "context-secret"},
                config=CognitiveCycleConfig(max_parallel_specialists=1, thinking_for_deep_roles=False),
                inference_fn=FakeInference(),
            )
            receipt = sanitized_receipt(result)
            text = json.dumps(receipt, sort_keys=True)
            self.assertNotIn("context-secret", text)
            self.assertNotIn("candidate-secret", text)
            self.assertNotIn("workspace-secret-synthesis", text)
            self.assertFalse(receipt["prompts_recorded"])
            self.assertFalse(receipt["responses_recorded"])
            self.assertFalse(receipt["secret_recorded"])


if __name__ == "__main__":
    unittest.main()
