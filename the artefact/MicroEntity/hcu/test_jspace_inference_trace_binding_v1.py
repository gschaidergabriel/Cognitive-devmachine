import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import canonicalize
from global_jspace_gwt_v1 import CellContribution, step
from grid10_scheduler_v1 import CellLease, ExecutionClass, GridPlan, HCUMode, PLAN_SCHEMA
from inference_receipt_v1 import InferenceReceipt, SCHEMA as INFERENCE_SCHEMA, STATUS as INFERENCE_STATUS
from jspace_inference_trace_binding_v1 import (
    JSpaceInferenceBindingError,
    _plan_material,
    bind_inference_observation_trace,
)
from reactive_event_router_v1 import RouteDecision
from xeno_entry_fabric_v1 import EntryPacket


GEN = 7
EVENT = "2" * 64
ADMISSION = "3" * 64
DECISION = "4" * 64
POLICY = "5" * 64
ENGINE_IDENTITY = "6" * 64
ENGINE_ARTIFACT = "7" * 64
CAPACITY = "8" * 64
OUTPUT = "9" * 64
BASIS = "a" * 64


class JSpaceInferenceTraceBindingTests(unittest.TestCase):
    def entry(self):
        return EntryPacket(
            schema="XENO_ENTRY_PACKET/v1",
            ingress_id="ingress:1",
            causal_id="causal:1",
            entity_generation=GEN,
            source_kind="HUMAN_PROMPT",
            source_id="user:test",
            modality="TEXT",
            observed_time=None,
            received_time="2026-08-24T00:00:00.000000Z",
            provenance_ref="test:prompt",
            provenance_sha256="b" * 64,
            capabilities=("hcu.route",),
            capability_binding_sha256="c" * 64,
            parent_id=None,
            stream_id=None,
            budget=(("max_model_calls", 2), ("max_tokens", 512), ("max_wall_ms", 1000)),
            payload_ref="mem:test",
            payload_sha256="d" * 64,
            event_sha256=EVENT,
            admission_sha256=ADMISSION,
        )

    def route(self):
        return RouteDecision(
            status="SELECTIVE_MODEL_ACTIVATION",
            scripts=("generation_check",),
            model_lanes=("critic", "world"),
            zero_projection=False,
            zero_projection_format=None,
            external_provider_dependency=False,
            hash_serialization_schema="RFC8785_JCS_IJSON/v1",
            event_sha256=EVENT,
            entry_admission_sha256=ADMISSION,
            router_policy_sha256=POLICY,
            resolved_engine_identity="hcu_local_08b",
            resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_engine_artifact_sha256=ENGINE_ARTIFACT,
            engine_identity_sha256=ENGINE_IDENTITY,
            decision_sha256=DECISION,
        )

    def plan(self):
        cells = (
            CellLease("cell-00", "RETRIEVE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-01", "PROVENANCE_BUDGET_CHECK", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-02", "MODEL:critic", ExecutionClass.MODEL, 256, 0),
            CellLease("cell-03", "MODEL:world", ExecutionClass.MODEL, 256, 1),
            CellLease("cell-04", "IDLE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-05", "IDLE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-06", "IDLE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-07", "IDLE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-08", "IDLE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-09", "SYNTHESIZE", ExecutionClass.SCRIPT, 0, None),
        )
        plan = GridPlan(
            schema=PLAN_SCHEMA,
            canonicalization_schema="RFC8785_JCS_IJSON/v1",
            entry_binding_schema="ENTITYOS_HCU_ENTRY_ADMISSION_BINDING/v2",
            plan_sha256="1" * 64,
            ingress_id="ingress:1",
            causal_id="causal:1",
            entity_generation=GEN,
            entry_event_sha256=EVENT,
            entry_admission_sha256=ADMISSION,
            route_event_sha256=EVENT,
            route_decision_sha256=DECISION,
            router_policy_sha256=POLICY,
            engine_identity_sha256=ENGINE_IDENTITY,
            resolved_engine_identity="hcu_local_08b",
            resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_engine_artifact_sha256=ENGINE_ARTIFACT,
            capacity_receipt_sha256=CAPACITY,
            runtime_profile_id="test",
            mode=HCUMode.GRID10,
            logical_cell_count=10,
            model_call_count=2,
            physical_decoder_limit=2,
            max_wall_ms=1000,
            cells=cells,
        )
        digest = hashlib.sha256(canonicalize(_plan_material(plan))).hexdigest()
        return replace(plan, plan_sha256=digest)

    def prototype(self):
        cells = [
            CellContribution("cell-02", "critic", (-0.4, 0.9), 0.3, 0.95, 0.7, 0.2, 0.1),
            CellContribution("cell-03", "world", (0.8, 0.1), 0.7, 0.1, 0.2, 0.2, 0.1),
        ]
        return step(cells, generation=GEN, basis_id="basis:test", basis_sha256=BASIS)

    def receipt(self):
        receipt = InferenceReceipt(
            schema=INFERENCE_SCHEMA,
            status=INFERENCE_STATUS,
            hash_serialization_schema="RFC8785_JCS_IJSON/v1",
            entry_binding_schema="ENTITYOS_HCU_ENTRY_ADMISSION_BINDING/v2",
            entity_generation=GEN,
            entry_admission_sha256=ADMISSION,
            event_sha256=EVENT,
            decision_sha256=DECISION,
            router_policy_sha256=POLICY,
            engine_identity_sha256=ENGINE_IDENTITY,
            resolved_engine_identity="hcu_local_08b",
            resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_engine_artifact_sha256=ENGINE_ARTIFACT,
            engine_admission_receipt_sha256="b" * 64,
            engine_load_canonicalization_schema="RFC8785_JCS_IJSON/v1",
            engine_load_loader_binding_sha256="c" * 64,
            engine_load_lease_sha256="d" * 64,
            engine_load_consumption_receipt_sha256="e" * 64,
            engine_load_loader_id="loader:test",
            model_call_id="call:1",
            output_ref="mem:output:1",
            output_sha256=OUTPUT,
            output_size=123,
            model_lanes=("critic", "world"),
            receipt_sha256="1" * 64,
        )
        material = asdict(receipt)
        material.pop("receipt_sha256")
        digest = hashlib.sha256(canonicalize(material)).hexdigest()
        return replace(receipt, receipt_sha256=digest)

    def bind(self, **overrides):
        proto = overrides.pop("prototype_step", self.prototype())
        receipt = overrides.pop("inference_receipt", self.receipt())
        admitted = {receipt.receipt_sha256: asdict(receipt)}
        kwargs = dict(
            entry_packet=self.entry(),
            decision=self.route(),
            grid_plan=self.plan(),
            inference_receipt=receipt,
            admitted_inference_receipts=admitted,
            trace_id="trace:1",
            trace_family_id="episode:1",
            jspace_input_vector_ref="unifieddb:jspace:input:1",
            local_workspace_state_ref="unifieddb:workspace:1",
            global_jspace_slice_ref="unifieddb:jspace:slice:1",
            expected_structured_model_output="schema://entityos/hcu/candidate/v1",
        )
        kwargs.update(overrides)
        return bind_inference_observation_trace(proto, proto.control_packet, **kwargs)

    def test_exact_causal_spine_emits_unknown_credit_bound_to_inference_receipt(self):
        receipt = self.receipt()
        trace = self.bind(
            inference_receipt=receipt,
            admitted_inference_receipts={receipt.receipt_sha256: asdict(receipt)},
        )
        self.assertEqual(trace.credit_label, "UNKNOWN")
        self.assertEqual(trace.outcome_receipt_sha256, receipt.receipt_sha256)
        self.assertEqual(trace.entry_event_sha256, EVENT)
        self.assertEqual(trace.route_decision_sha256, DECISION)
        self.assertIn(OUTPUT, trace.observed_downstream_outcome)

    def test_tampered_inference_receipt_fails_before_trace(self):
        receipt = replace(self.receipt(), output_sha256="a" * 64)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "INFERENCE_RECEIPT_DIGEST_MISMATCH"):
            self.bind(
                inference_receipt=receipt,
                admitted_inference_receipts={receipt.receipt_sha256: asdict(receipt)},
            )

    def test_rehashed_plan_cannot_transplant_different_route(self):
        plan = replace(self.plan(), route_decision_sha256="e" * 64)
        plan = replace(plan, plan_sha256=hashlib.sha256(canonicalize(_plan_material(plan))).hexdigest())
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "CAUSAL_IDENTITY_MISMATCH:plan.route_decision_sha256"):
            self.bind(grid_plan=plan)


if __name__ == "__main__":
    unittest.main()
