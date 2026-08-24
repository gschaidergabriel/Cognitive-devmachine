import hashlib
import unittest

from entry_stream_authority_binding_v1 import bind_external_stream_authority
from entry_stream_authority_store_v1 import (
    admit_entry_stream_authority,
    build_stream_authority_decision,
    decision_record,
)
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from jspace_vector_control_v1 import packet_bytes
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from preinvocation_control_admission_store_v2 import (
    PreInvocationControlAdmissionV2Error,
    prepare_preinvocation_control_v2,
    read_preinvocation_control_preparation_v2,
)
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
from test_preinvocation_control_admission_store_v1 import (
    GENERATION,
    PreInvocationControlAdmissionTests,
    h,
)
from xeno_entry_fabric_v1 import ENTRY_SCHEMA, admit_entry


class PreInvocationControlAdmissionV2Tests(PreInvocationControlAdmissionTests):
    """Regression coverage for the v2 canonical-stream-authority predecessor fence."""

    def controlled_entry(self, *, stream_id="thread:episode-1"):
        capability_sha = hashlib.sha256(b"capability-view:preinvocation-v2").hexdigest()
        budget = {"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000}
        return admit_entry(
            {
                "schema": ENTRY_SCHEMA,
                "ingress_id": "ingress:episode-1:step-1",
                "causal_id": "causal:episode-1:step-1",
                "entity_generation": GENERATION,
                "source_kind": "HUMAN_PROMPT",
                "source_id": "source:preinvocation-v2",
                "modality": "TEXT",
                "observed_time": None,
                "received_time": "2026-08-24T03:00:00Z",
                "provenance_ref": "conversation:user-message",
                "provenance_sha256": hashlib.sha256(b"provenance:episode-1:step-1").hexdigest(),
                "capabilities": ["hcu.route"],
                "capability_binding_sha256": capability_sha,
                "parent_id": "conversation:episode-1",
                "stream_id": stream_id,
                "budget": budget,
                "payload_ref": "payload:episode-1:step-1",
                "payload_sha256": hashlib.sha256(b"payload:episode-1:step-1").hexdigest(),
            },
            current_generation=GENERATION,
            expected_capability_binding_sha256=capability_sha,
            admitted_capabilities=["hcu.route"],
            admitted_budget=budget,
        )

    def controlled_plan_for_entry(self, packet, role):
        cells = (
            CellLease(
                "controlled.0",
                f"MODEL:{role}",
                ExecutionClass.MODEL,
                256,
                0,
            ),
        )
        provisional = GridPlan(
            schema=PLAN_SCHEMA,
            canonicalization_schema=CANONICALIZATION_SCHEMA,
            entry_binding_schema=ENTRY_BINDING_SCHEMA,
            plan_sha256=h(30),
            ingress_id=packet.ingress_id,
            causal_id=packet.causal_id,
            entity_generation=packet.entity_generation,
            entry_event_sha256=packet.event_sha256,
            entry_admission_sha256=packet.admission_sha256,
            route_event_sha256=h(33),
            route_decision_sha256=h(34),
            router_policy_sha256=h(35),
            engine_identity_sha256=h(36),
            resolved_engine_identity="hcu_local_08b",
            resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_engine_artifact_sha256=h(37),
            capacity_receipt_sha256=h(38),
            runtime_profile_id="runtime:preinvocation:v2-test",
            mode=HCUMode.GRID10,
            logical_cell_count=1,
            model_call_count=1,
            physical_decoder_limit=1,
            max_wall_ms=1000,
            cells=cells,
        )
        from dataclasses import replace
        return replace(
            provisional,
            plan_sha256=hashlib.sha256(canonicalize(grid_plan_material(provisional))).hexdigest(),
        )

    def controlled_input_for_entry(self, proto, packet, plan, role, *, invocation_id="invocation:episode-1:step-1"):
        consumed = b'{"system":"hcu"}\n' + packet_bytes(proto.control_packet) + b'\n{"prompt":"solve"}'
        binding = bind_direct_unique_packet_input(
            proto.control_packet,
            consumed,
            generation=GENERATION,
            entry_event_sha256=packet.event_sha256,
            entry_admission_sha256=packet.admission_sha256,
            route_decision_sha256=plan.route_decision_sha256,
            grid_plan_sha256=plan.plan_sha256,
            cell_id="controlled.0",
            role=role,
            executor_id="local-qwen-executor:v1",
            invocation_id=invocation_id,
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )
        return binding, consumed

    def canonical_stream_authority(self, packet, *, decision_id="stream-decision:episode-1"):
        decision = build_stream_authority_decision(
            generation=GENERATION,
            authority_namespace="typed-entry-canonical-stream-registry:v1",
            authority_decision_id=decision_id,
            source_kind=packet.source_kind,
            source_id=packet.source_id,
            stream_id=packet.stream_id,
        )
        admission = admit_entry_stream_authority(
            self.db,
            decision,
            admitted_stream_authority_decisions={
                decision.decision_sha256: decision_record(decision)
            },
            current_generation=GENERATION,
        )
        authority = bind_external_stream_authority(
            generation=GENERATION,
            source_kind=packet.source_kind,
            source_id=packet.source_id,
            authorized_stream_id=packet.stream_id,
            authority_kind="CANONICAL_STREAM_REGISTRY",
            authority_ref=decision.authority_decision_id,
            authority_binding_sha256=decision.decision_sha256,
        )
        return decision, admission, authority

    def sources_v2(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace)
        controlled_entry = self.controlled_entry()
        plan = self.controlled_plan_for_entry(controlled_entry, trace.role)
        input_binding, consumed = self.controlled_input_for_entry(
            proto, controlled_entry, plan, trace.role
        )
        decision, admission, authority = self.canonical_stream_authority(controlled_entry)
        return (
            proto,
            trace,
            predecessor_binding,
            controlled_entry,
            plan,
            input_binding,
            consumed,
            decision,
            admission,
            authority,
        )

    def test_v2_preparation_binds_canonical_stream_authority_and_replays_exactly(self):
        (
            _,
            trace,
            predecessor_binding,
            controlled_entry,
            plan,
            input_binding,
            consumed,
            decision,
            admission,
            authority,
        ) = self.sources_v2()
        preparation = prepare_preinvocation_control_v2(
            self.db,
            controlled_entry,
            trace,
            predecessor_binding,
            input_binding,
            consumed,
            plan,
            authority,
            current_generation=GENERATION,
        )
        self.assertEqual(preparation.stream_authority_decision_sha256, decision.decision_sha256)
        self.assertEqual(preparation.stream_authority_admission_sha256, admission.admission_sha256)
        self.assertEqual(preparation.controlled_entry_event_sha256, controlled_entry.event_sha256)
        self.assertEqual(preparation.controlled_invocation_id, input_binding.invocation_id)
        self.assertNotEqual(
            preparation.predecessor_model_invocation_id,
            preparation.controlled_invocation_id,
        )
        reread = read_preinvocation_control_preparation_v2(
            self.db,
            executor_id=input_binding.executor_id,
            invocation_id=input_binding.invocation_id,
        )
        self.assertEqual(reread, preparation)
        replay = prepare_preinvocation_control_v2(
            self.db,
            controlled_entry,
            trace,
            predecessor_binding,
            input_binding,
            consumed,
            plan,
            authority,
            current_generation=GENERATION,
        )
        self.assertEqual(replay, preparation)
        self.assertEqual(
            self.db.execute(
                "SELECT COUNT(*) FROM hcu_preinvocation_control_preparations_v2"
            ).fetchone()[0],
            1,
        )

    def test_v2_rejects_caller_minted_stream_authority_before_preparation_table_exists(self):
        proto, trace = self.predecessor_trace()
        predecessor_binding = self.predecessor_binding(trace)
        controlled_entry = self.controlled_entry()
        plan = self.controlled_plan_for_entry(controlled_entry, trace.role)
        input_binding, consumed = self.controlled_input_for_entry(
            proto, controlled_entry, plan, trace.role
        )
        caller_hash = hashlib.sha256(b"caller-only-stream-authority").hexdigest()
        authority = bind_external_stream_authority(
            generation=GENERATION,
            source_kind=controlled_entry.source_kind,
            source_id=controlled_entry.source_id,
            authorized_stream_id=controlled_entry.stream_id,
            authority_kind="CANONICAL_STREAM_REGISTRY",
            authority_ref="caller:decision",
            authority_binding_sha256=caller_hash,
        )
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionV2Error,
            "AUTHORIZED_SEQUENCE_LANE_REJECTED:CANONICAL_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            prepare_preinvocation_control_v2(
                self.db,
                controlled_entry,
                trace,
                predecessor_binding,
                input_binding,
                consumed,
                plan,
                authority,
                current_generation=GENERATION,
            )
        self.assertIsNone(
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='hcu_preinvocation_control_preparations_v2'"
            ).fetchone()
        )

    def test_v2_existing_controlled_execution_blocks_posthoc_preparation(self):
        (
            _,
            trace,
            predecessor_binding,
            controlled_entry,
            plan,
            input_binding,
            consumed,
            _,
            _,
            authority,
        ) = self.sources_v2()
        self.db.execute(
            "INSERT INTO hcu_model_execution_invocations VALUES(?,?,?,?,?)",
            (
                h(50),
                input_binding.executor_id,
                input_binding.invocation_id,
                GENERATION,
                predecessor_binding.model_execution_observation_sha256,
            ),
        )
        self.db.commit()
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionV2Error,
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_POSTHOC_PREPARATION_FORBIDDEN",
        ):
            prepare_preinvocation_control_v2(
                self.db,
                controlled_entry,
                trace,
                predecessor_binding,
                input_binding,
                consumed,
                plan,
                authority,
                current_generation=GENERATION,
            )

    def test_v2_same_invocation_posthoc_control_is_rejected(self):
        proto, trace = self.predecessor_trace()
        controlled_entry = self.controlled_entry()
        plan = self.controlled_plan_for_entry(controlled_entry, trace.role)
        input_binding, consumed = self.controlled_input_for_entry(
            proto,
            controlled_entry,
            plan,
            trace.role,
            invocation_id="invocation:episode-1:same",
        )
        predecessor_binding = self.predecessor_binding(
            trace,
            invocation_id=input_binding.invocation_id,
        )
        _, _, authority = self.canonical_stream_authority(controlled_entry)
        with self.assertRaisesRegex(
            PreInvocationControlAdmissionV2Error,
            "PREINVOCATION_V1_SOURCE_REJECTED:SAME_INVOCATION_POSTHOC_CONTROL_FORBIDDEN",
        ):
            prepare_preinvocation_control_v2(
                self.db,
                controlled_entry,
                trace,
                predecessor_binding,
                input_binding,
                consumed,
                plan,
                authority,
                current_generation=GENERATION,
            )


if __name__ == "__main__":
    unittest.main()
