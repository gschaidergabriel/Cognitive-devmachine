import hashlib
import unittest
from dataclasses import replace

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from global_jspace_gwt_v1 import CellContribution, step
from inference_receipt_v1 import (
    InferenceReceipt,
    SCHEMA as INFERENCE_RECEIPT_SCHEMA,
    STATUS as INFERENCE_RECEIPT_STATUS,
)
from jspace_inference_binding_v1 import (
    JSpaceInferenceBindingError,
    bind_training_trace_to_inference,
    grid10_model_call_id,
    validate_binding,
)
from jspace_training_trace_v1 import build_training_trace
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA

BASIS_SHA256 = "1" * 64


class JSpaceInferenceBindingTests(unittest.TestCase):
    def prototype(self):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        return step(cells, generation=7, basis_id="basis:7", basis_sha256=BASIS_SHA256)

    def training_trace(self):
        proto = self.prototype()
        return build_training_trace(
            proto,
            proto.control_packet,
            trace_id="trace:episode-1:step-1",
            trace_family_id="episode:1",
            entry_event_sha256="2" * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            jspace_input_vector_ref="unifieddb:jspace-input:1",
            local_workspace_state_ref="unifieddb:workspace:1",
            global_jspace_slice_ref="unifieddb:jspace-slice:1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )

    def inference_receipt(self, trace=None, **overrides):
        trace = trace or self.training_trace()
        payload = {
            "schema": INFERENCE_RECEIPT_SCHEMA,
            "status": INFERENCE_RECEIPT_STATUS,
            "hash_serialization_schema": CANONICALIZATION_SCHEMA,
            "entry_binding_schema": ENTRY_BINDING_SCHEMA,
            "entity_generation": trace.generation,
            "entry_admission_sha256": trace.entry_admission_sha256,
            "event_sha256": trace.entry_event_sha256,
            "decision_sha256": trace.route_decision_sha256,
            "router_policy_sha256": "6" * 64,
            "engine_identity_sha256": "7" * 64,
            "resolved_engine_identity": "local-hcu-08b",
            "resolved_engine_class": "LOCAL_COGNITION",
            "resolved_engine_artifact_sha256": "8" * 64,
            "engine_admission_receipt_sha256": "9" * 64,
            "engine_load_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "engine_load_loader_binding_sha256": "a" * 64,
            "engine_load_lease_sha256": "b" * 64,
            "engine_load_consumption_receipt_sha256": "c" * 64,
            "engine_load_loader_id": "loader:1",
            "model_call_id": grid10_model_call_id(
                grid_plan_sha256=trace.grid_plan_sha256,
                cell_id=trace.cell_id,
                role=trace.role,
            ),
            "output_ref": "unifieddb:model-output:1",
            "output_sha256": "d" * 64,
            "output_size": 123,
            "model_lanes": (trace.role,),
        }
        payload.update(overrides)
        receipt_sha256 = hashlib.sha256(canonicalize(payload)).hexdigest()
        return InferenceReceipt(**payload, receipt_sha256=receipt_sha256)

    def test_exact_trace_binds_verified_loader_and_output_chain(self):
        trace = self.training_trace()
        receipt = self.inference_receipt(trace)
        binding = bind_training_trace_to_inference(trace, receipt)
        validate_binding(binding)
        self.assertEqual(binding.inference_receipt_sha256, receipt.receipt_sha256)
        self.assertEqual(binding.engine_load_consumption_receipt_sha256, "c" * 64)
        self.assertEqual(binding.output_sha256, "d" * 64)
        self.assertEqual(binding.role, trace.role)
        self.assertEqual(binding.model_call_id, receipt.model_call_id)

    def test_crossbound_generation_entry_and_route_fail_closed(self):
        trace = self.training_trace()
        cases = [
            ({"entity_generation": trace.generation + 1}, "INFERENCE_GENERATION_MISMATCH"),
            ({"event_sha256": "e" * 64}, "INFERENCE_ENTRY_EVENT_MISMATCH"),
            ({"entry_admission_sha256": "e" * 64}, "INFERENCE_ENTRY_ADMISSION_MISMATCH"),
            ({"decision_sha256": "e" * 64}, "INFERENCE_ROUTE_DECISION_MISMATCH"),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                receipt = self.inference_receipt(trace, **overrides)
                with self.assertRaisesRegex(JSpaceInferenceBindingError, code):
                    bind_training_trace_to_inference(trace, receipt)

    def test_model_lane_must_bind_trace_role(self):
        trace = self.training_trace()
        receipt = self.inference_receipt(trace, model_lanes=("world",))
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "INFERENCE_MODEL_LANE_DOES_NOT_BIND_TRACE_ROLE",
        ):
            bind_training_trace_to_inference(trace, receipt)

    def test_grid10_cell_call_relabel_poison_fails_closed(self):
        trace = self.training_trace()
        wrong_cell_call = grid10_model_call_id(
            grid_plan_sha256=trace.grid_plan_sha256,
            cell_id="cell-relabeled",
            role=trace.role,
        )
        receipt = self.inference_receipt(
            trace,
            model_lanes=(trace.role, "world"),
            model_call_id=wrong_cell_call,
        )
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "INFERENCE_GRID10_MODEL_CALL_BINDING_MISMATCH",
        ):
            bind_training_trace_to_inference(trace, receipt)

    def test_tampered_inference_receipt_digest_fails_before_crossbinding(self):
        trace = self.training_trace()
        receipt = self.inference_receipt(trace)
        tampered = replace(receipt, output_sha256="e" * 64)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "HCU_INFERENCE_RECEIPT_DIGEST_MISMATCH",
        ):
            bind_training_trace_to_inference(trace, tampered)

    def test_binding_digest_tamper_fails_closed(self):
        trace = self.training_trace()
        binding = bind_training_trace_to_inference(trace, self.inference_receipt(trace))
        tampered = replace(binding, output_ref="unifieddb:model-output:changed")
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_DIGEST_MISMATCH",
        ):
            validate_binding(tampered)


if __name__ == "__main__":
    unittest.main()
