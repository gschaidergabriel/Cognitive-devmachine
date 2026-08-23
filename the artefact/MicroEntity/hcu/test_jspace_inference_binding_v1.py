import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from global_jspace_gwt_v1 import CellContribution, step
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
    validate_grid_plan_identity,
)
from inference_receipt_v1 import InferenceReceipt, SCHEMA as INFERENCE_RECEIPT_SCHEMA, STATUS as INFERENCE_RECEIPT_STATUS
from jspace_inference_binding_v1 import JSpaceInferenceBindingError, SCHEMA as JSPACE_INFERENCE_BINDING_SCHEMA, bind_training_trace_to_inference, validate_binding
from jspace_training_trace_v1 import build_training_trace
from model_execution_receipt_v1 import VERIFIED_EXECUTION_SCHEMA
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA

BASIS_SHA256 = "1" * 64
EVENT_SHA256 = "2" * 64
ENTRY_ADMISSION_SHA256 = "3" * 64
ROUTE_DECISION_SHA256 = "4" * 64
MODEL_EXECUTION_RECEIPT_SHA256 = "5" * 64
ROUTER_POLICY_SHA256 = "6" * 64
ENGINE_IDENTITY_SHA256 = "7" * 64
ENGINE_ARTIFACT_SHA256 = "8" * 64
ENGINE_ADMISSION_RECEIPT_SHA256 = "9" * 64
LOADER_BINDING_SHA256 = "a" * 64
LOAD_LEASE_SHA256 = "b" * 64
LOAD_CONSUMPTION_SHA256 = "c" * 64
OUTPUT_SHA256 = "d" * 64
CAPACITY_RECEIPT_SHA256 = "e" * 64
MODEL_EXECUTION_OBSERVATION_SHA256 = hashlib.sha256(b"model-execution-observation").hexdigest()
INPUT_SHA256 = hashlib.sha256(b"model-input").hexdigest()


def canonical_sha256(value) -> str:
    return hashlib.sha256(canonicalize(value)).hexdigest()


class JSpaceInferenceBindingTests(unittest.TestCase):
    def prototype(self):
        cells = [
            CellContribution("cell-00", "retrieval", (0.2, 0.1, -0.1), 0.1, 0.1, 0.1, 0.1, 0.1),
            CellContribution("cell-02", "critic", (-0.3, 0.9, 0.4), 0.8, 0.95, 0.7, 0.4, 0.2),
        ]
        return step(cells, generation=7, basis_id="basis:7", basis_sha256=BASIS_SHA256)

    def grid_plan(self, lanes=("critic",), **overrides):
        cells = [
            CellLease("cell-00", "RETRIEVE", ExecutionClass.SCRIPT, 0, None),
            CellLease("cell-01", "PROVENANCE_BUDGET_CHECK", ExecutionClass.SCRIPT, 0, None),
        ]
        for ordinal, lane in enumerate(lanes):
            cells.append(CellLease(f"cell-{len(cells):02d}", f"MODEL:{lane}", ExecutionClass.MODEL, 256, ordinal))
        while len(cells) < 9:
            cells.append(CellLease(f"cell-{len(cells):02d}", "IDLE", ExecutionClass.SCRIPT, 0, None))
        cells.append(CellLease("cell-09", "SYNTHESIZE", ExecutionClass.SCRIPT, 0, None))
        payload = {
            "schema": PLAN_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "entry_binding_schema": ENTRY_BINDING_SCHEMA,
            "ingress_id": "ingress:jspace-binding:1",
            "causal_id": "causal:jspace-binding:1",
            "entity_generation": 7,
            "entry_event_sha256": EVENT_SHA256,
            "entry_admission_sha256": ENTRY_ADMISSION_SHA256,
            "route_event_sha256": EVENT_SHA256,
            "route_decision_sha256": ROUTE_DECISION_SHA256,
            "router_policy_sha256": ROUTER_POLICY_SHA256,
            "engine_identity_sha256": ENGINE_IDENTITY_SHA256,
            "resolved_engine_identity": "local-hcu-08b",
            "resolved_engine_class": "LOCAL_COGNITION",
            "resolved_engine_artifact_sha256": ENGINE_ARTIFACT_SHA256,
            "capacity_receipt_sha256": CAPACITY_RECEIPT_SHA256,
            "runtime_profile_id": "test:runtime:jspace-binding",
            "mode": HCUMode.GRID10,
            "logical_cell_count": 10,
            "model_call_count": len(lanes),
            "physical_decoder_limit": max(1, min(2, len(lanes))),
            "max_wall_ms": 1000,
            "cells": tuple(cells),
        }
        payload.update(overrides)
        provisional = GridPlan(plan_sha256="1" * 64, **payload)
        plan = replace(provisional, plan_sha256=canonical_sha256(grid_plan_material(provisional)))
        validate_grid_plan_identity(plan)
        return plan

    def training_trace(self, grid_plan=None):
        proto = self.prototype()
        grid_plan = grid_plan or self.grid_plan()
        return build_training_trace(
            proto,
            proto.control_packet,
            trace_id="trace:episode-1:step-1",
            trace_family_id="episode:1",
            entry_event_sha256=EVENT_SHA256,
            entry_admission_sha256=ENTRY_ADMISSION_SHA256,
            route_decision_sha256=ROUTE_DECISION_SHA256,
            grid_plan_sha256=grid_plan.plan_sha256,
            jspace_input_vector_ref="unifieddb:jspace-input:1",
            local_workspace_state_ref="unifieddb:workspace:1",
            global_jspace_slice_ref="unifieddb:jspace-slice:1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": max(1, grid_plan.model_call_count), "max_tokens": 512, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )

    def inference_receipt(self, trace=None, **overrides):
        trace = trace or self.training_trace()
        invocation_id = "executor-invocation:jspace:1"
        payload = {
            "schema": INFERENCE_RECEIPT_SCHEMA,
            "status": INFERENCE_RECEIPT_STATUS,
            "hash_serialization_schema": CANONICALIZATION_SCHEMA,
            "entry_binding_schema": ENTRY_BINDING_SCHEMA,
            "entity_generation": trace.generation,
            "entry_admission_sha256": trace.entry_admission_sha256,
            "event_sha256": trace.entry_event_sha256,
            "decision_sha256": trace.route_decision_sha256,
            "router_policy_sha256": ROUTER_POLICY_SHA256,
            "engine_identity_sha256": ENGINE_IDENTITY_SHA256,
            "resolved_engine_identity": "local-hcu-08b",
            "resolved_engine_class": "LOCAL_COGNITION",
            "resolved_engine_artifact_sha256": ENGINE_ARTIFACT_SHA256,
            "engine_admission_receipt_sha256": ENGINE_ADMISSION_RECEIPT_SHA256,
            "engine_load_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "engine_load_loader_binding_sha256": LOADER_BINDING_SHA256,
            "engine_load_lease_sha256": LOAD_LEASE_SHA256,
            "engine_load_consumption_receipt_sha256": LOAD_CONSUMPTION_SHA256,
            "engine_load_loader_id": "loader:1",
            "model_execution_schema": VERIFIED_EXECUTION_SCHEMA,
            "model_execution_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "model_execution_receipt_sha256": MODEL_EXECUTION_RECEIPT_SHA256,
            "model_execution_observation_sha256": MODEL_EXECUTION_OBSERVATION_SHA256,
            "model_execution_executor_id": "entityos:hcu:model-executor:1",
            "model_execution_invocation_id": invocation_id,
            "grid_plan_sha256": trace.grid_plan_sha256,
            "output_producing_cell_id": trace.cell_id,
            "model_execution_role": trace.role,
            "input_sha256": INPUT_SHA256,
            "input_size": 64,
            "model_call_id": invocation_id,
            "output_ref": "unifieddb:model-output:1",
            "output_sha256": OUTPUT_SHA256,
            "output_size": 123,
            "model_lanes": (trace.role,),
        }
        payload.update(overrides)
        return InferenceReceipt(**payload, receipt_sha256=canonical_sha256(payload))

    def test_exact_trace_binds_grid_cell_verified_loader_execution_and_output_chain(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        receipt = self.inference_receipt(trace)
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.schema, JSPACE_INFERENCE_BINDING_SCHEMA)
        self.assertEqual(binding.inference_receipt_sha256, receipt.receipt_sha256)
        self.assertEqual(binding.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(binding.engine_load_consumption_receipt_sha256, LOAD_CONSUMPTION_SHA256)
        self.assertEqual(binding.model_execution_receipt_sha256, MODEL_EXECUTION_RECEIPT_SHA256)
        self.assertEqual(binding.model_execution_observation_sha256, MODEL_EXECUTION_OBSERVATION_SHA256)
        self.assertEqual(binding.output_sha256, OUTPUT_SHA256)
        self.assertEqual(binding.input_sha256, INPUT_SHA256)
        self.assertEqual(binding.role, trace.role)
        self.assertEqual(binding.cell_id, "cell-02")

    def test_crossbound_generation_entry_and_route_fail_closed(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        cases = [
            ({"entity_generation": trace.generation + 1}, "INFERENCE_GENERATION_MISMATCH"),
            ({"event_sha256": "e" * 64}, "INFERENCE_ENTRY_EVENT_MISMATCH"),
            ({"entry_admission_sha256": "e" * 64}, "INFERENCE_ENTRY_ADMISSION_MISMATCH"),
            ({"decision_sha256": "e" * 64}, "INFERENCE_ROUTE_DECISION_MISMATCH"),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(JSpaceInferenceBindingError, code):
                    bind_training_trace_to_inference(trace, self.inference_receipt(trace, **overrides), plan)

    def test_inference_receipt_schema_authorities_fail_closed(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        cases = [
            ({"entry_binding_schema": "ENTITYOS_HCU_ENTRY_ADMISSION_BINDING/foreign"}, "HCU_INFERENCE_RECEIPT_ENTRY_BINDING_SCHEMA_MISMATCH"),
            ({"engine_load_canonicalization_schema": "FOREIGN_CANONICALIZATION/v1"}, "HCU_INFERENCE_RECEIPT_ENGINE_LOAD_CANONICALIZATION_MISMATCH"),
            ({"model_execution_canonicalization_schema": "FOREIGN_CANONICALIZATION/v1"}, "HCU_INFERENCE_RECEIPT_MODEL_EXECUTION_CANONICALIZATION_MISMATCH"),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(JSpaceInferenceBindingError, code):
                    bind_training_trace_to_inference(trace, self.inference_receipt(trace, **overrides), plan)

    def test_model_lane_must_bind_trace_role(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "INFERENCE_MODEL_LANE_DOES_NOT_BIND_TRACE_ROLE"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace, model_lanes=("world",)), plan)

    def test_training_trace_must_bind_exact_grid_plan(self):
        plan = self.grid_plan()
        other = self.grid_plan(runtime_profile_id="test:runtime:other")
        trace = self.training_trace(plan)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "GRID10_TRAINING_TRACE_PLAN_MISMATCH"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace), other)

    def test_inference_receipt_must_bind_exact_grid_plan(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "INFERENCE_GRID10_PLAN_MISMATCH"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace, grid_plan_sha256="e" * 64), plan)

    def test_training_trace_cell_must_be_exact_model_cell(self):
        plan = self.grid_plan()
        trace = replace(self.training_trace(plan), cell_id="cell-00")
        material = asdict(trace)
        material.pop("trace_sha256")
        material["gwt_competition_set"] = [{"cell_id": cell_id, "role": role, "gate_q": gate_q} for cell_id, role, gate_q in trace.gwt_competition_set]
        material["hyperposition_branch_ids"] = list(trace.hyperposition_branch_ids)
        material["resource_budget"] = {key: value for key, value in trace.resource_budget}
        trace = replace(trace, trace_sha256=canonical_sha256(material))
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "GRID10_MODEL_CELL_DOES_NOT_BIND_TRACE_CELL"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace), plan)

    def test_model_execution_cell_must_bind_trace_cell(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "MODEL_EXECUTION_CELL_DOES_NOT_BIND_TRACE_CELL"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace, output_producing_cell_id="cell-09"), plan)

    def test_model_execution_role_must_bind_trace_role(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "MODEL_EXECUTION_ROLE_DOES_NOT_BIND_TRACE_ROLE"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace, model_execution_role="world"), plan)

    def test_tampered_grid_plan_digest_fails_before_binding(self):
        plan = replace(self.grid_plan(), runtime_profile_id="tampered")
        trace = self.training_trace(self.grid_plan())
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "GRID10_PLAN_DIGEST_MISMATCH"):
            bind_training_trace_to_inference(trace, self.inference_receipt(trace), plan)

    def test_tampered_inference_receipt_digest_fails_before_crossbinding(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        tampered = replace(self.inference_receipt(trace), output_sha256="e" * 64)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "HCU_INFERENCE_RECEIPT_DIGEST_MISMATCH"):
            bind_training_trace_to_inference(trace, tampered, plan)

    def test_binding_digest_tamper_fails_closed(self):
        plan = self.grid_plan()
        trace = self.training_trace(plan)
        binding = bind_training_trace_to_inference(trace, self.inference_receipt(trace), plan)
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "JSPACE_INFERENCE_BINDING_DIGEST_MISMATCH"):
            validate_binding(replace(binding, output_ref="unifieddb:model-output:changed"))

    def test_multilane_v4_explicit_execution_cell_binds(self):
        plan = self.grid_plan(("critic", "world"))
        trace = self.training_trace(plan)
        receipt = self.inference_receipt(trace, model_lanes=("critic", "world"))
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.cell_id, "cell-02")
        self.assertEqual(binding.role, "critic")
        self.assertEqual(binding.model_execution_invocation_id, receipt.model_execution_invocation_id)


if __name__ == "__main__":
    unittest.main()
