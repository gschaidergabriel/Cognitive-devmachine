#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from grid10_fabric import Fabric
from grid10_cognitive_envelope_control_v1 import AssuranceMode, ProjectionPolicy
from grid10_cognitive_fabric_adapter_v1 import TrustedAxisEvidence, collect_fabric_telemetry
from grid10_cognitive_heartbeat_v1 import CognitiveHeartbeatRuntime, CognitiveHeartbeatStore, HeartbeatConfig
from grid10_cognitive_twin_server_v1 import read_frames
from grid10_assurance_monitors_v1 import (
    AuthorityObservation, ContainmentObservation, GoalContract, GoalRevisionObservation,
    authority_integrity_evidence, containment_margin_evidence, evaluate_goal_mutation,
)
from grid10_executor_governor_v1 import (
    ExecutorMetricReport, ExecutorResultReport, GovernedWorkContract, evaluate_executor_result,
)
from grid10_cognitive_envelope_control_v1 import CompletionMetric, ContextItem


def normal_trusted_axes():
    vals = {
        "authority_integrity": (1.0, ProjectionPolicy.PESSIMISTIC_MIN),
        "goal_lineage_alignment": (0.95, ProjectionPolicy.PESSIMISTIC_MIN),
        "goal_drift_rate": (0.02, ProjectionPolicy.PESSIMISTIC_MAX),
        "containment_margin": (0.90, ProjectionPolicy.PESSIMISTIC_MIN),
        "epistemic_grounding": (0.90, ProjectionPolicy.LOW_CONFIDENCE_BOUND),
        "self_reinforcement_ratio": (0.05, ProjectionPolicy.PESSIMISTIC_MAX),
        "resource_pressure": (0.20, ProjectionPolicy.PESSIMISTIC_MAX),
        "recovery_margin": (0.90, ProjectionPolicy.PESSIMISTIC_MIN),
    }
    return {
        k: TrustedAxisEvidence(k, v, "VERIFIED", (f"test:{k}",), 1.0, policy)
        for k, (v, policy) in vals.items()
    }


class RuntimeAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        root = Path(self.td.name)
        self.fabric = Fabric(root / "fabric.sqlite")
        self.store = CognitiveHeartbeatStore(root / "heartbeat.sqlite")
        self.frames = root / "frames.jsonl"

    def tearDown(self):
        self.td.cleanup()

    def test_adapter_never_invents_authority_integrity(self):
        telemetry = collect_fabric_telemetry(self.fabric)
        self.assertNotIn("authority_integrity", telemetry.variables)

    def test_missing_authority_fails_closed_and_does_not_write(self):
        rt = CognitiveHeartbeatRuntime(self.fabric, self.store, config=HeartbeatConfig(allow_regulator_writes=False))
        result = rt.tick_once(tick_id="t-hold")
        self.assertEqual(result.assurance_mode, AssuranceMode.HOLD)
        self.assertEqual(result.next_action, "HOLD")
        self.assertIsNone(result.regulator_cycle)
        self.assertIsNone(self.fabric.get_regulator("temperature"))

    def test_normal_fixture_produces_replayable_frame(self):
        rt = CognitiveHeartbeatRuntime(self.fabric, self.store, config=HeartbeatConfig(allow_regulator_writes=False))
        result = rt.tick_once(tick_id="t-normal", trusted_axes=normal_trusted_axes())
        self.assertEqual(result.assurance_mode, AssuranceMode.NORMAL)
        frame = json.loads(result.frame_json)
        self.assertEqual(frame["schema"], "COGNITIVE_LOOP_FRAME/v1")
        self.assertEqual(frame["assurance_mode"], "NORMAL")
        self.assertTrue(frame["source_digest"])

    def test_containment_correction_writes_only_through_policy_port(self):
        axes = normal_trusted_axes()
        axes["containment_margin"] = TrustedAxisEvidence(
            "containment_margin", 0.40, "VERIFIED", ("test:containment-hard",), 1.0,
            ProjectionPolicy.PESSIMISTIC_MIN,
        )
        rt = CognitiveHeartbeatRuntime(self.fabric, self.store, config=HeartbeatConfig(allow_regulator_writes=True))
        result = rt.tick_once(tick_id="t-contained", trusted_axes=axes)
        self.assertEqual(result.assurance_mode, AssuranceMode.CONTAINED)
        self.assertIsNotNone(result.regulator_cycle)
        cycle = result.regulator_cycle
        self.assertLessEqual(cycle["applied"], 2)
        self.assertEqual(cycle["requested"], len(result.regulator_proposals))
        row = self.fabric.get_regulator("contain.external_action_concurrency")
        self.assertIsNotNone(row)
        self.assertEqual(float(row["value_real"]), 0.0)
        self.assertEqual(row["writer"], "grid10-assurance-controller")

    def test_frame_journal_reader_ignores_garbage(self):
        self.frames.write_text(
            'garbage\n'+json.dumps({"schema":"COGNITIVE_LOOP_FRAME/v1","frame_id":"f"})+'\n',
            encoding="utf-8",
        )
        frames = read_frames(self.frames)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["frame_id"], "f")

    def test_authority_monitor_requires_complete_observation(self):
        ev = authority_integrity_evidence(AuthorityObservation(
            True, True, None, True, ("test:authority",)
        ))
        self.assertIsNone(ev.value)
        self.assertEqual(ev.evidence_status, "UNKNOWN")

    def test_goal_mutation_rejects_scope_broadening(self):
        contract = GoalContract(
            "g1", 3, frozenset({"root-safe"}), frozenset({"READ_ONLY"}),
            frozenset({"CPU"}), 0.08, ("contract:g1:r3",)
        )
        decision = evaluate_goal_mutation(contract, GoalRevisionObservation(
            "g1", 3, 4, frozenset({"root-safe"}), frozenset({"READ_ONLY","WRITE_EXTERNAL"}),
            frozenset({"CPU"}), 0.02, "VERIFIED", ("goal:g1:r4",)
        ))
        self.assertFalse(decision.admitted)
        self.assertIn("EFFECT_SCOPE_BROADENED", decision.reasons)
        self.assertEqual(decision.goal_lineage_alignment.value, 0.0)

    def test_containment_monitor_is_pessimistic(self):
        ev = containment_margin_evidence(ContainmentObservation(
            candidate_effect_risk=0.10,
            allowed_effect_risk_ceiling=0.25,
            tool_scope_valid=True,
            effect_scope_valid=True,
            reversible=True,
            rollback_ready=False,
            unknown_effect_fraction=0.05,
            provenance=("effect:candidate:1",),
        ))
        self.assertAlmostEqual(ev.value, 0.35)

    def test_executor_done_does_not_override_missing_metrics(self):
        contract = GovernedWorkContract(
            work_id="w1", goal_id="g1", spec_revision=2,
            completion_metrics=(
                CompletionMetric("unit_tests", True, True),
                CompletionMetric("integration_tests", True, True),
                CompletionMetric("target_runtime", True, True),
            ),
            allowed_write_scope=("tools/",), allowed_tool_scope=("python",),
            effect_scope=("SANDBOX",), context_token_budget=1000,
            continuation_checkpoint_ref="checkpoint:w1:r2",
            do_not_repeat_refs=("already:unit-implementation",),
        )
        result = ExecutorResultReport(
            work_id="w1", spec_revision=2, claimed_status="DONE",
            metrics={
                "unit_tests": ExecutorMetricReport(True, ("receipt:unit",), "VERIFIED"),
                "integration_tests": ExecutorMetricReport(False, ("receipt:int",), "VERIFIED"),
            },
            changed_refs=("tools/implemented.py",),
        )
        decision = evaluate_executor_result(
            contract, result,
            context_candidates=(
                ContextItem("ctx:deficits","COMPLETION_DEFICITS",200,1.0,"VERIFIED"),
                ContextItem("ctx:history","DO_NOT_REPEAT",900,0.5,"VERIFIED"),
            ),
        )
        self.assertEqual(decision.status, "CONTINUE_DELTA_ONLY")
        self.assertFalse(decision.verified_complete)
        self.assertEqual(set(decision.deficits), {"integration_tests","target_runtime"})
        self.assertEqual(set(decision.continuation_directive.required_outputs), {"integration_tests","target_runtime"})
        self.assertEqual(tuple(x.ref for x in decision.context_capsule.items), ("ctx:deficits",))


if __name__ == "__main__":
    unittest.main()
