#!/usr/bin/env python3
from __future__ import annotations

import unittest

from grid10_cognitive_envelope_control_v1 import (
    Alternative,
    AssuranceMode,
    CompletionMetric,
    CompletionObservation,
    ContextItem,
    EnvelopeBand,
    HyperVariable,
    LoopDescriptor,
    ProjectionPolicy,
    RegulatorCommand,
    build_delta_directive,
    build_loop_frame,
    compile_context_capsule,
    evaluate_completion,
    evaluate_envelope,
    validate_regulator_command,
)


class CognitiveEnvelopeTests(unittest.TestCase):
    def test_hyperposition_safety_uses_pessimistic_branch(self):
        variables = {
            "containment_margin": HyperVariable(
                "containment_margin",
                (
                    Alternative(0.90, 0.9, "VERIFIED", ("safe",)),
                    Alternative(0.40, 0.1, "INFERRED", ("risky",)),
                ),
                ProjectionPolicy.PESSIMISTIC_MIN,
            )
        }
        bands = {
            "containment_margin": EnvelopeBand(
                "containment_margin",
                target_min=0.85,
                soft_min=0.70,
                hard_min=0.50,
                safety_relevant=True,
            )
        }
        snap = evaluate_envelope(
            tick_id="t1",
            state_epoch=1,
            variables=variables,
            bands=bands,
        )
        self.assertEqual(snap.assurance_mode, AssuranceMode.CONTAINED)
        self.assertEqual(snap.assessments[0].projected.value, 0.40)

    def test_unknown_hard_invariant_holds(self):
        bands = {
            "authority_integrity": EnvelopeBand(
                "authority_integrity",
                target_min=1.0,
                soft_min=1.0,
                hard_min=1.0,
                hard_invariant=True,
                safety_relevant=True,
            )
        }
        snap = evaluate_envelope(
            tick_id="t2",
            state_epoch=1,
            variables={},
            bands=bands,
        )
        self.assertEqual(snap.assurance_mode, AssuranceMode.HOLD)

    def test_l1_regulator_write_needs_policy_role(self):
        command = RegulatorCommand(
            name="contain.required_margin",
            requested_value=0.82,
            writer="claude",
            writer_role="EXECUTOR",
            expected_version=4,
            reason="make containment looser",
        )
        decision = validate_regulator_command(
            command,
            current_value=0.8,
            current_version=4,
            assurance_mode=AssuranceMode.NORMAL,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "L1_WRITE_REQUIRES_POLICY_AUTHORITY")

    def test_completion_gate_returns_only_missing_metrics(self):
        metrics = [
            CompletionMetric("source_present", True, True),
            CompletionMetric("unit_tests", True, "PASS"),
            CompletionMetric("integration_tests", True, "PASS"),
            CompletionMetric("target_runtime", True, "PASS"),
            CompletionMetric("docs_updated", True, True),
        ]
        observations = [
            CompletionObservation("source_present", True, ("src-receipt",), "VERIFIED"),
            CompletionObservation("unit_tests", "PASS", ("unit-receipt",), "PASS"),
            CompletionObservation("docs_updated", True, ("doc-receipt",), "VERIFIED"),
        ]
        verdict = evaluate_completion("work-1", metrics, observations)
        self.assertFalse(verdict.verified_complete)
        self.assertEqual({d.metric for d in verdict.deficits}, {"integration_tests", "target_runtime"})

        directive = build_delta_directive(
            work_id="work-1",
            goal_id="goal-1",
            spec_revision=7,
            verdict=verdict,
            context_capsule_ref="ctx-7",
            allowed_write_scope=("tools/",),
            allowed_tool_scope=("test",),
            effect_scope=("LOCAL_REVERSIBLE",),
            max_context_tokens=4096,
            continuation_checkpoint_ref="checkpoint-6",
            do_not_repeat_refs=("completed-source-work", "completed-docs-work"),
        )
        self.assertEqual(set(directive.completion_metrics), {"integration_tests", "target_runtime"})
        self.assertEqual(len(directive.exact_delta_to_do), 2)

    def test_context_compiler_respects_budget_without_reordering_priority(self):
        capsule = compile_context_capsule(
            goal_id="g",
            work_id="w",
            token_budget=100,
            candidates=(
                ContextItem("critical", "MUST_KNOW", 70, 1.0, "VERIFIED"),
                ContextItem("counter", "COUNTEREVIDENCE", 30, 0.9, "VERIFIED"),
                ContextItem("background", "BACKGROUND", 80, 0.1, "VERIFIED"),
            ),
        )
        self.assertEqual([x.ref for x in capsule.items], ["critical", "counter"])
        self.assertEqual(capsule.estimated_tokens, 100)
        self.assertEqual(capsule.omitted_refs, ("background",))

    def test_visual_frame_semantic_digest_is_replay_stable(self):
        variables = {
            "authority_integrity": HyperVariable(
                "authority_integrity",
                (Alternative(1.0, 1.0, "VERIFIED", ("auth",)),),
                ProjectionPolicy.PESSIMISTIC_MIN,
            )
        }
        bands = {
            "authority_integrity": EnvelopeBand(
                "authority_integrity",
                target_min=1.0,
                hard_min=1.0,
                hard_invariant=True,
                safety_relevant=True,
            )
        }
        envelope = evaluate_envelope(
            tick_id="tick",
            state_epoch=3,
            variables=variables,
            bands=bands,
        )
        kwargs = dict(
            tick_id="tick",
            state_epoch=3,
            assurance_mode=envelope.assurance_mode,
            loops=(LoopDescriptor("goal", "VERIFY", 0.8, 1000.0, 0.7, 0.9),),
            envelope=envelope,
            regulators={"cog.temperature": {"value": 0.8, "version": 4}},
            hyperposition={"branch_count": 1},
            work={"work_id": "w", "phase": "VERIFY"},
            source_event_refs=("e1", "e2"),
        )
        frame1 = build_loop_frame(timestamp=100.0, **kwargs)
        frame2 = build_loop_frame(timestamp=200.0, **kwargs)
        self.assertEqual(frame1.source_digest, frame2.source_digest)
        self.assertEqual(frame1.frame_id, frame2.frame_id)
        self.assertNotEqual(frame1.timestamp, frame2.timestamp)


if __name__ == "__main__":
    unittest.main()
