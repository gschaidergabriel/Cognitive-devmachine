#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceReceipt, GLMInferenceResult
from grid10_persistent_agency_v1 import GoalState
from grid10_persistent_scheduler_v1 import SchedulerConfig
from grid10_persistent_scheduler_v2 import PersistentCognitiveSchedulerV2


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
                "synthesis": "scheduler-v2-workspace",
                "preserved_alternatives": ["alt"],
                "disagreements": [],
                "evidence_requests": ["runtime"],
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


class PersistentSchedulerV2Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.db = self.root / "unified.sqlite"
        self.frames = self.root / "frames.jsonl"
        self.config = SchedulerConfig(
            active_interval_seconds=5.0,
            hold_poll_seconds=20.0,
            idle_poll_seconds=30.0,
            trusted_normal_test_fixture=True,
        )

    def tearDown(self):
        self.td.cleanup()

    def scheduler(self, *, fake=None):
        return PersistentCognitiveSchedulerV2(
            self.db,
            self.frames,
            config=self.config,
            inference_fn=fake,
            cognitive_config=CognitiveCycleConfig(thinking_for_deep_roles=False),
        )

    def seed_active(self, scheduler, *, goal_id="g1", now=100.0):
        goal = scheduler.agency.create_goal(
            goal_id=goal_id,
            origin="AUTHENTICATED_USER",
            semantic_goal="continue without a new prompt",
            success_criteria=("next heartbeat occurs",),
            uncertainty=0.2,
            priority=10,
            event_id=f"{goal_id}:create",
            now_ts=now,
        )
        return scheduler.agency.transition_goal(
            goal_id,
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id=f"{goal_id}:activate",
            reason="admitted",
            now_ts=now + 1,
        )

    def _patch(self, scheduler, patch_id, changes):
        base = scheduler.runtime.control_plane.snapshot()
        patch = scheduler.runtime.control_plane.build_patch(
            patch_id=patch_id,
            writer="unit-test",
            writer_kind="EXPERIMENT",
            reason="deterministic scheduler-v2 regression",
            changes=changes,
            base=base,
        )
        receipt = scheduler.runtime.control_plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        return scheduler.runtime.control_plane.snapshot()

    def test_autonomous_active_cycle_reaches_v6_and_ignites_default_workspace(self):
        fake = FakeInference()
        s = self.scheduler(fake=fake)
        self.seed_active(s)
        row = s.cycle_once(
            cycle_id="sched-v2-ignite",
            now_ts=110.0,
            cognitive_context={"goal": "g1"},
        )
        self.assertEqual(row.status, "HEARTBEAT_RAN")
        self.assertEqual(row.heartbeat_tick_id, "sched-v2-ignite:heartbeat")
        self.assertEqual(row.next_tick_not_before, 115.0)
        self.assertEqual(fake.workspace_calls, 1)
        self.assertEqual(len(fake.calls), 10)

        con = sqlite3.connect(str(self.db))
        try:
            v4 = con.execute(
                "SELECT COUNT(*) FROM grid10_cognitive_cycles WHERE tick_id=?",
                (row.heartbeat_tick_id,),
            ).fetchone()[0]
            v6 = con.execute(
                "SELECT workspace_ignited,workspace_ignition_threshold,receipt_json "
                "FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (row.heartbeat_tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(v4, 1)
        self.assertEqual(v6[0], 1)
        self.assertEqual(v6[1], 0.5)
        receipt = json.loads(v6[2])
        self.assertEqual(
            receipt["control_snapshot_digest"],
            receipt["v4_checkpoint_control_snapshot"]["snapshot_digest"],
        )
        self.assertNotIn("candidate-only-text", json.dumps(receipt, sort_keys=True))

    def test_autonomous_cycle_can_compute_specialists_without_workspace_ignition(self):
        fake = FakeInference()
        s = self.scheduler(fake=fake)
        self.seed_active(s)
        changes = {
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
        }
        snapshot = self._patch(s, "sched-v2-subthreshold", changes)
        row = s.cycle_once(
            cycle_id="sched-v2-subthreshold",
            now_ts=110.0,
            cognitive_context={"goal": "g1"},
        )
        self.assertEqual(row.status, "HEARTBEAT_RAN")
        self.assertEqual(fake.workspace_calls, 0)
        self.assertEqual(len(fake.calls), 9)

        con = sqlite3.connect(str(self.db))
        try:
            rec = con.execute(
                "SELECT control_snapshot_digest,workspace_ignited,workspace_ignition_threshold,receipt_json "
                "FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (row.heartbeat_tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(rec[0], snapshot.snapshot_digest)
        self.assertEqual(rec[1], 0)
        self.assertEqual(rec[2], 0.75)
        receipt = json.loads(rec[3])
        controlled = receipt["controlled_cognitive_cycle_receipt"]
        self.assertFalse(controlled["workspace_ignited"])
        self.assertEqual(controlled["gwt_eligible_cell_ids"], [])
        self.assertEqual(
            {x["status"] for x in controlled["cell_execution"]},
            {"IGNITION_BELOW_THRESHOLD"},
        )

    def test_no_inference_function_keeps_autonomous_heartbeat_but_zero_model_calls(self):
        s = self.scheduler(fake=None)
        self.seed_active(s)
        row = s.cycle_once(cycle_id="sched-v2-off", now_ts=110.0)
        self.assertEqual(row.status, "HEARTBEAT_RAN")
        con = sqlite3.connect(str(self.db))
        try:
            raw = con.execute(
                "SELECT receipt_json FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (row.heartbeat_tick_id,),
            ).fetchone()[0]
        finally:
            con.close()
        receipt = json.loads(raw)
        self.assertEqual(
            receipt["controlled_cognitive_cycle_receipt"]["reason"],
            "NO_EXPLICIT_ADMITTED_INFERENCE_FN",
        )
        self.assertEqual(
            receipt["controlled_cognitive_cycle_receipt"]["provider_calls"], 0
        )
        self.assertFalse(receipt["external_effect_executed"])
        self.assertFalse(receipt["canonical_truth_minted"])
        self.assertFalse(receipt["completion_minted"])


if __name__ == "__main__":
    unittest.main()
