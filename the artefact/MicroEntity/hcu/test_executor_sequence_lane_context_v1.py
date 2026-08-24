import hashlib
import unittest
from dataclasses import replace

from entry_canonicalization_v1 import canonicalize
from executor_sequence_lane_context_v1 import (
    CROSS_EVENT_STREAM,
    INTRA_REQUEST_GRID,
    ExecutorSequenceLaneContextError,
    derive_executor_sequence_lane_context,
    validate_executor_sequence_lane_context,
)
from grid10_scheduler_v1 import grid_plan_material, validate_grid_plan_identity
from model_execution_receipt_v1 import verify_model_execution
from test_model_execution_receipt_v1 import (
    admission_registries,
    grid_plan as base_grid_plan,
    observation,
    verified_load,
)
from xeno_entry_fabric_v1 import ENTRY_SCHEMA, admit_entry


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def entry_packet(*, suffix: str, stream_id: str | None = "stream:episode-1", source_id: str = "user:test"):
    capability_binding = digest("capability-binding")
    return admit_entry(
        {
            "schema": ENTRY_SCHEMA,
            "ingress_id": f"ingress:{suffix}",
            "causal_id": f"causal:{suffix}",
            "entity_generation": 7,
            "source_kind": "HUMAN_PROMPT",
            "source_id": source_id,
            "modality": "TEXT",
            "observed_time": "2026-08-24T03:00:00Z",
            "received_time": f"2026-08-24T03:00:{int(suffix):02d}Z",
            "provenance_ref": f"test:provenance:{suffix}",
            "provenance_sha256": digest(f"provenance:{suffix}"),
            "capabilities": ["hcu.route"],
            "capability_binding_sha256": capability_binding,
            "parent_id": "conversation:test",
            "stream_id": stream_id,
            "budget": {"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 2500},
            "payload_ref": f"test:payload:{suffix}",
            "payload_sha256": digest(f"payload:{suffix}"),
        },
        current_generation=7,
        expected_capability_binding_sha256=capability_binding,
        admitted_capabilities=["hcu.route"],
        admitted_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 2500},
    )


def plan_for(packet):
    base = base_grid_plan()
    provisional = replace(
        base,
        plan_sha256=digest("provisional-sequence-plan"),
        ingress_id=packet.ingress_id,
        causal_id=packet.causal_id,
        entity_generation=packet.entity_generation,
        entry_event_sha256=packet.event_sha256,
        entry_admission_sha256=packet.admission_sha256,
    )
    plan = replace(
        provisional,
        plan_sha256=hashlib.sha256(canonicalize(grid_plan_material(provisional))).hexdigest(),
    )
    validate_grid_plan_identity(plan)
    return plan


def execution_for(plan, *, invocation_id: str):
    load = verified_load(plan)
    obs = replace(observation(plan, load), invocation_id=invocation_id)
    observations, invocations = admission_registries(obs)
    return verify_model_execution(
        plan,
        load,
        obs,
        admitted_model_execution_observations=observations,
        admitted_model_execution_invocations=invocations,
        current_generation=plan.entity_generation,
    )


class ExecutorSequenceLaneContextTests(unittest.TestCase):
    def sources(self, suffix="01", *, stream_id="stream:episode-1", source_id="user:test"):
        packet = entry_packet(suffix=suffix, stream_id=stream_id, source_id=source_id)
        plan = plan_for(packet)
        execution = execution_for(plan, invocation_id=f"invocation:{suffix}")
        return packet, plan, execution

    def test_cross_event_lane_is_deterministic_and_source_revalidates(self):
        packet, plan, execution = self.sources()
        a = derive_executor_sequence_lane_context(
            packet, plan, execution, lane_scope=CROSS_EVENT_STREAM
        )
        b = derive_executor_sequence_lane_context(
            packet, plan, execution, lane_scope=CROSS_EVENT_STREAM
        )
        self.assertEqual(a, b)
        self.assertEqual(
            validate_executor_sequence_lane_context(a, packet, plan, execution),
            a.context_sha256,
        )

    def test_same_admitted_stream_across_distinct_events_has_same_lane_but_distinct_context(self):
        p1, plan1, execution1 = self.sources("01")
        p2, plan2, execution2 = self.sources("02")
        a = derive_executor_sequence_lane_context(
            p1, plan1, execution1, lane_scope=CROSS_EVENT_STREAM
        )
        b = derive_executor_sequence_lane_context(
            p2, plan2, execution2, lane_scope=CROSS_EVENT_STREAM
        )
        self.assertNotEqual(a.entry_event_sha256, b.entry_event_sha256)
        self.assertNotEqual(a.grid_plan_sha256, b.grid_plan_sha256)
        self.assertNotEqual(a.verified_model_execution_sha256, b.verified_model_execution_sha256)
        self.assertEqual(a.lane_key_sha256, b.lane_key_sha256)
        self.assertNotEqual(a.context_sha256, b.context_sha256)

    def test_cross_event_scope_requires_admitted_stream_identity(self):
        packet, plan, execution = self.sources(stream_id=None)
        with self.assertRaisesRegex(
            ExecutorSequenceLaneContextError,
            "EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE:ADMITTED_STREAM_ID_REQUIRED",
        ):
            derive_executor_sequence_lane_context(
                packet, plan, execution, lane_scope=CROSS_EVENT_STREAM
            )

    def test_grid_local_scope_survives_without_stream_but_is_plan_specific(self):
        p1, plan1, execution1 = self.sources("01", stream_id=None)
        p2, plan2, execution2 = self.sources("02", stream_id=None)
        a = derive_executor_sequence_lane_context(
            p1, plan1, execution1, lane_scope=INTRA_REQUEST_GRID
        )
        b = derive_executor_sequence_lane_context(
            p2, plan2, execution2, lane_scope=INTRA_REQUEST_GRID
        )
        self.assertNotEqual(a.lane_key_sha256, b.lane_key_sha256)

    def test_same_stream_label_from_different_source_identity_cannot_alias_lane(self):
        p1, plan1, execution1 = self.sources("01", source_id="user:a")
        p2, plan2, execution2 = self.sources("02", source_id="user:b")
        a = derive_executor_sequence_lane_context(
            p1, plan1, execution1, lane_scope=CROSS_EVENT_STREAM
        )
        b = derive_executor_sequence_lane_context(
            p2, plan2, execution2, lane_scope=CROSS_EVENT_STREAM
        )
        self.assertNotEqual(a.lane_key_sha256, b.lane_key_sha256)

    def test_entry_plan_transplant_fails_closed(self):
        p1, _plan1, _execution1 = self.sources("01")
        _p2, plan2, execution2 = self.sources("02")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneContextError,
            "SEQUENCE_LANE_INGRESS_ID_MISMATCH|SEQUENCE_LANE_ENTRY_EVENT_MISMATCH",
        ):
            derive_executor_sequence_lane_context(
                p1, plan2, execution2, lane_scope=CROSS_EVENT_STREAM
            )

    def test_verified_execution_from_other_plan_fails_closed(self):
        packet, plan, _execution = self.sources("01")
        _p2, _plan2, execution2 = self.sources("02")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneContextError,
            "SEQUENCE_LANE_MODEL_EXECUTION_GRID_MISMATCH",
        ):
            derive_executor_sequence_lane_context(
                packet, plan, execution2, lane_scope=CROSS_EVENT_STREAM
            )

    def test_context_cannot_be_revalidated_against_different_event_even_when_lane_key_matches(self):
        p1, plan1, execution1 = self.sources("01")
        p2, plan2, execution2 = self.sources("02")
        context = derive_executor_sequence_lane_context(
            p1, plan1, execution1, lane_scope=CROSS_EVENT_STREAM
        )
        with self.assertRaisesRegex(
            ExecutorSequenceLaneContextError,
            "EXECUTOR_SEQUENCE_LANE_CONTEXT_SOURCE_REVALIDATION_MISMATCH",
        ):
            validate_executor_sequence_lane_context(context, p2, plan2, execution2)


if __name__ == "__main__":
    unittest.main()
