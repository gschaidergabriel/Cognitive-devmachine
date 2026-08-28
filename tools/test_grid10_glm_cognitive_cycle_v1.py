#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_fabric import Fabric
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig, run_cognitive_cycle, sanitized_receipt
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult


class FakeInference:
    def __init__(self, *, workspace_recommendation: str = "ACT_CANDIDATE"):
        self.calls = []
        self.workspace_recommendation = workspace_recommendation

    def __call__(self, messages, *, config):
        self.calls.append((messages, config))
        is_workspace = "ROLE=workspace/GWT fan-in" in messages[-1]["content"]
        if is_workspace:
            content = json.dumps({
                "synthesis": "bounded synthesis",
                "preserved_alternatives": ["A", "B"],
                "disagreements": ["cell2_vs_cell6"],
                "evidence_requests": ["runtime_receipt"],
                "recommended_action": self.workspace_recommendation,
            })
        else:
            content = json.dumps({
                "candidate": "candidate only",
                "alternatives": ["alt-a", "alt-b"],
                "evidence_needed": ["receipt-x"],
                "confidence": 0.6,
                "unresolved": True,
            })
        idx = len(self.calls)
        receipt = GLMInferenceReceipt(
            provider="FAKE",
            model_requested="glm-4.7-flash",
            model_reported="glm-4.7-flash",
            request_digest=f"req-{idx}",
            response_digest=f"resp-{idx}",
            latency_ms=10.0 + idx,
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30,
            thinking_enabled=config.thinking,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            finish_reason="stop",
            response_id=f"fake-{idx}",
            secret_recorded=False,
        )
        return GLMInferenceResult(content=content, reasoning_content=None, receipt=receipt)


class GLMCognitiveCycleTests(unittest.TestCase):
    def _fabric(self, td: str) -> Fabric:
        return Fabric(Path(td) / "fabric.sqlite")

    def test_normal_mode_is_nine_parallel_specialists_plus_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeInference()
            result = run_cognitive_cycle(
                tick_id="tick-normal",
                assurance_mode=AssuranceMode.NORMAL,
                controller_action="ACT_CANDIDATE",
                fabric=self._fabric(td),
                context={"goal": "g1", "deficits": ["runtime"]},
                config=CognitiveCycleConfig(thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            self.assertEqual(result.workspace.active_cells, tuple(range(10)))
            self.assertEqual(len(result.cells), 9)
            self.assertEqual(len(fake.calls), 10)
            self.assertEqual(result.workspace.effective_action, "ACT_CANDIDATE")
            self.assertTrue(result.workspace.noncanonical)
            self.assertFalse(result.workspace.model_may_authorize_effects)
            self.assertEqual(result.workspace.provider_tokens, 300)

    def test_hold_reduces_compute_and_model_cannot_escape_hold(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeInference(workspace_recommendation="ACT_CANDIDATE")
            result = run_cognitive_cycle(
                tick_id="tick-hold",
                assurance_mode=AssuranceMode.HOLD,
                controller_action="HOLD",
                fabric=self._fabric(td),
                context={"authority_integrity": "UNKNOWN"},
                config=CognitiveCycleConfig(thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            self.assertEqual(result.workspace.effective_action, "HOLD")
            self.assertEqual(result.workspace.model_recommended_action, "ACT_CANDIDATE")
            # state, critic, skeptic, epistemic + workspace = five active logical cells.
            self.assertEqual(result.workspace.active_cells, (0, 3, 6, 7, 9))
            self.assertEqual(len(fake.calls), 5)
            for _, cfg in fake.calls:
                self.assertLessEqual(cfg.temperature, 0.25)
                self.assertLessEqual(cfg.top_p, 0.75)

    def test_receipt_does_not_persist_prompts_or_model_text(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeInference()
            result = run_cognitive_cycle(
                tick_id="tick-receipt",
                assurance_mode=AssuranceMode.CAUTION,
                controller_action="SEARCH",
                fabric=self._fabric(td),
                context={"sensitive_context": "not-for-receipt"},
                config=CognitiveCycleConfig(thinking_for_deep_roles=False),
                inference_fn=fake,
            )
            receipt = sanitized_receipt(result)
            text = json.dumps(receipt, sort_keys=True)
            self.assertNotIn("not-for-receipt", text)
            self.assertNotIn("candidate only", text)
            self.assertNotIn("bounded synthesis", text)
            self.assertFalse(receipt["secret_recorded"])
            self.assertFalse(receipt["prompts_recorded"])
            self.assertFalse(receipt["responses_recorded"])

    def test_context_budget_fails_before_any_provider_call(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeInference()
            with self.assertRaises(ValueError):
                run_cognitive_cycle(
                    tick_id="tick-too-big",
                    assurance_mode=AssuranceMode.NORMAL,
                    controller_action="ACT_CANDIDATE",
                    fabric=self._fabric(td),
                    context={"blob": "x" * 2000},
                    config=CognitiveCycleConfig(max_context_chars=1000),
                    inference_fn=fake,
                )
            self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()
