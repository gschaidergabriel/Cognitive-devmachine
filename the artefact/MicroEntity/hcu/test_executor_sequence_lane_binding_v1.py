import hashlib
import unittest
from dataclasses import replace

import executor_sequence_lane_binding_v1 as lane_module
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from executor_sequence_lane_binding_v1 import (
    ExecutorSequenceLaneBindingError,
    bind_executor_sequence_lane,
    validate_executor_sequence_lane_binding,
)
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
)
from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
from xeno_entry_fabric_v1 import ENTRY_SCHEMA, admit_entry


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class ExecutorSequenceLaneBindingTests(unittest.TestCase):
    generation = 7
    source_id = "source:human-ui"
    role = "critic"
    cell_id = "critic.0"
    executor_id = "local-qwen-executor:v1"

    def entry(self, *, causal="event:1", ingress="ingress:1", stream="thread:alpha"):
        payload_sha = h(f"payload:{causal}")
        capability_sha = h("capability-view:7")
        budget = {"max_model_calls": 1, "max_tokens": 512, "max_wall_ms": 2000}
        return admit_entry(
            {
                "schema": ENTRY_SCHEMA,
                "ingress_id": ingress,
                "causal_id": causal,
                "entity_generation": self.generation,
                "source_kind": "HUMAN_PROMPT",
                "source_id": self.source_id,
                "modality": "TEXT",
                "observed_time": None,
                "received_time": "2026-08-24T02:00:00Z",
                "provenance_ref": "conversation:user-message",
                "provenance_sha256": h(f"provenance:{causal}"),
                "capabilities": ["hcu.route"],
                "capability_binding_sha256": capability_sha,
                "parent_id": "conversation:root",
                "stream_id": stream,
                "budget": budget,
                "payload_ref": f"payload:{causal}",
                "payload_sha256": payload_sha,
            },
            current_generation=self.generation,
            expected_capability_binding_sha256=capability_sha,
            admitted_capabilities=["hcu.route"],
            admitted_budget=budget,
        )

    def plan(self, packet, *, engine_label="engine:qwen", route_label="route:1"):
        cell = CellLease(
            cell_id=self.cell_id,
            function=f"MODEL:{self.role}",
            execution_class=ExecutionClass.MODEL,
            model_token_budget=256,
            physical_decoder_lane=0,
        )
        provisional = GridPlan(
            schema=PLAN_SCHEMA,
            canonicalization_schema=CANONICALIZATION_SCHEMA,
            entry_binding_schema=ENTRY_BINDING_SCHEMA,
            plan_sha256="a" * 64,
            ingress_id=packet.ingress_id,
            causal_id=packet.causal_id,
            entity_generation=packet.entity_generation,
            entry_event_sha256=packet.event_sha256,
            entry_admission_sha256=packet.admission_sha256,
            route_event_sha256=h(f"route-event:{route_label}"),
            route_decision_sha256=h(route_label),
            router_policy_sha256=h("router-policy:v1"),
            engine_identity_sha256=h(engine_label),
            resolved_engine_identity=engine_label,
            resolved_engine_class="LOCAL_MODEL",
            resolved_engine_artifact_sha256=h(f"artifact:{engine_label}"),
            capacity_receipt_sha256=h("capacity:local"),
            runtime_profile_id="runtime:local-test",
            mode=HCUMode.GRID10,
            logical_cell_count=1,
            model_call_count=1,
            physical_decoder_limit=1,
            max_wall_ms=2000,
            cells=(cell,),
        )
        digest = hashlib.sha256(canonicalize(grid_plan_material(provisional))).hexdigest()
        return replace(provisional, plan_sha256=digest)

    def control_packet(self):
        return encode_vector(
            (0.25, -0.5, 1.0),
            basis_id="basis:sequence-lane",
            basis_sha256=h("basis:sequence-lane"),
            generation=self.generation,
            role=self.role,
            control_condition="BASELINE",
        )

    def input_binding(self, packet, plan, *, invocation="invocation:1"):
        vector = self.control_packet()
        wire = packet_bytes(vector)
        consumed = b'{"system":"hcu"}\n' + wire + b'\n{"prompt":"solve"}'
        binding = bind_direct_unique_packet_input(
            vector,
            consumed,
            generation=self.generation,
            entry_event_sha256=packet.event_sha256,
            entry_admission_sha256=packet.admission_sha256,
            route_decision_sha256=plan.route_decision_sha256,
            grid_plan_sha256=plan.plan_sha256,
            cell_id=self.cell_id,
            role=self.role,
            executor_id=self.executor_id,
            invocation_id=invocation,
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )
        return binding, consumed

    def bind(self, *, causal="event:1", ingress="ingress:1", stream="thread:alpha", invocation="invocation:1", engine="engine:qwen"):
        packet = self.entry(causal=causal, ingress=ingress, stream=stream)
        plan = self.plan(packet, engine_label=engine, route_label=f"route:{causal}")
        input_binding, consumed = self.input_binding(packet, plan, invocation=invocation)
        lane = bind_executor_sequence_lane(packet, plan, input_binding, consumed)
        return packet, plan, input_binding, consumed, lane

    def test_distinct_events_in_same_admitted_stream_share_lane_identity(self):
        a = self.bind(causal="event:1", ingress="ingress:1", invocation="invocation:1")
        b = self.bind(causal="event:2", ingress="ingress:2", invocation="invocation:2")
        self.assertNotEqual(a[0].event_sha256, b[0].event_sha256)
        self.assertNotEqual(a[1].plan_sha256, b[1].plan_sha256)
        self.assertNotEqual(a[2].binding_sha256, b[2].binding_sha256)
        self.assertEqual(a[4].sequence_lane_sha256, b[4].sequence_lane_sha256)
        validate_executor_sequence_lane_binding(a[4], a[0], a[1], a[2], a[3])
        validate_executor_sequence_lane_binding(b[4], b[0], b[1], b[2], b[3])

    def test_missing_typed_entry_stream_id_fails_closed(self):
        packet = self.entry(stream=None)
        plan = self.plan(packet)
        input_binding, consumed = self.input_binding(packet, plan)
        with self.assertRaisesRegex(ExecutorSequenceLaneBindingError, "EXECUTOR_SEQUENCE_STREAM_ID_REQUIRED"):
            bind_executor_sequence_lane(packet, plan, input_binding, consumed)

    def test_stream_id_is_part_of_lane_identity(self):
        a = self.bind(stream="thread:alpha")
        b = self.bind(stream="thread:beta")
        self.assertNotEqual(a[4].sequence_lane_sha256, b[4].sequence_lane_sha256)

    def test_forged_stream_label_cannot_reuse_admitted_entry_hashes(self):
        packet, plan, input_binding, consumed, _ = self.bind()
        forged_packet = replace(packet, stream_id="thread:forged")
        with self.assertRaisesRegex(ExecutorSequenceLaneBindingError, "ENTRY_PACKET_IDENTITY_MISMATCH"):
            bind_executor_sequence_lane(forged_packet, plan, input_binding, consumed)

    def test_input_binding_cannot_be_transplanted_to_another_grid_parent(self):
        packet, plan, input_binding, consumed, _ = self.bind(causal="event:1", ingress="ingress:1")
        other_packet = self.entry(causal="event:2", ingress="ingress:2")
        other_plan = self.plan(other_packet, route_label="route:event:2")
        with self.assertRaisesRegex(ExecutorSequenceLaneBindingError, "INPUT_GRID_EVENT_IDENTITY_MISMATCH|INPUT_GRID_PLAN_IDENTITY_MISMATCH"):
            bind_executor_sequence_lane(other_packet, other_plan, input_binding, consumed)

    def test_engine_identity_partitions_sequence_lane(self):
        a = self.bind(engine="engine:qwen")
        b = self.bind(engine="engine:other")
        self.assertNotEqual(a[4].sequence_lane_sha256, b[4].sequence_lane_sha256)

    def test_post_binding_input_mutation_fails_source_revalidation(self):
        packet, plan, input_binding, consumed, lane = self.bind()
        with self.assertRaisesRegex(ExecutorSequenceLaneBindingError, "MODEL_INPUT_CONTROL_BINDING_REJECTED"):
            validate_executor_sequence_lane_binding(
                lane,
                packet,
                plan,
                input_binding,
                consumed + b"!",
            )

    def test_self_consistent_outer_relabel_cannot_launder_lane_identity(self):
        packet, plan, input_binding, consumed, lane = self.bind()
        forged = replace(lane, sequence_lane_sha256=h("forged-lane"))
        forged = replace(
            forged,
            binding_sha256=lane_module._canonical_sha256(
                lane_module._material(forged),
                "TEST_OUTER_RESIGN",
            ),
        )
        with self.assertRaisesRegex(ExecutorSequenceLaneBindingError, "EXECUTOR_SEQUENCE_LANE_SOURCE_REVALIDATION_MISMATCH"):
            validate_executor_sequence_lane_binding(forged, packet, plan, input_binding, consumed)


if __name__ == "__main__":
    unittest.main()
