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
from jspace_causal_training_binding_v1 import (
    JSpaceCausalTrainingBindingError,
    bind_causal_training_evidence,
    validate_binding,
)
from jspace_inference_binding_v1 import bind_training_trace_to_inference
from jspace_training_trace_v1 import build_training_trace
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
from test_jspace_gwt_prototype_v1 import _trace as make_transition_trace


VECTOR = (0.25, -0.5, 1.0, 0.125)


class JSpaceCausalTrainingBindingTests(unittest.TestCase):
    def transition(self, **kwargs):
        return make_transition_trace(vector=VECTOR, trace_id="transition:1", **kwargs)

    def prototype(self, transition=None):
        transition = transition or self.transition()
        cell = CellContribution(
            transition.cell_id,
            transition.role,
            VECTOR,
            0.8,
            0.7,
            0.4,
            0.6,
            0.2,
            1.0,
        )
        return step(
            [cell],
            generation=transition.generation,
            basis_id=transition.jspace_basis_id,
            basis_sha256=transition.jspace_basis_sha256,
            control_condition=transition.falsifier_lesion_condition,
        )

    def training_trace(self, transition=None, **causal_overrides):
        transition = transition or self.transition()
        proto = self.prototype(transition)
        causal = {
            "entry_event_sha256": transition.entry_event_sha256,
            "entry_admission_sha256": transition.entry_admission_sha256,
            "route_decision_sha256": transition.route_decision_sha256,
            "grid_plan_sha256": transition.grid_plan_sha256,
        }
        causal.update(causal_overrides)
        return build_training_trace(
            proto,
            proto.control_packet,
            trace_id="training:1",
            trace_family_id="episode:1",
            **causal,
            jspace_input_vector_ref="entityos:jspace-input:1",
            local_workspace_state_ref="entityos:workspace:1",
            global_jspace_slice_ref="entityos:jspace:slice:1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition=transition.falsifier_lesion_condition,
            credit_label="UNKNOWN",
        )

    def inference_receipt(self, trace, **overrides):
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
            "model_call_id": "call:1",
            "output_ref": "entityos:model-output:1",
            "output_sha256": "d" * 64,
            "output_size": 123,
            "model_lanes": (trace.role,),
        }
        payload.update(overrides)
        receipt_sha256 = hashlib.sha256(canonicalize(payload)).hexdigest()
        return InferenceReceipt(**payload, receipt_sha256=receipt_sha256)

    def evidence(self, transition=None, trace=None):
        transition = transition or self.transition()
        trace = trace or self.training_trace(transition)
        inference = bind_training_trace_to_inference(trace, self.inference_receipt(trace))
        return transition, trace, inference

    def test_exact_transition_training_and_inference_chain_binds(self):
        transition, trace, inference = self.evidence()
        binding = bind_causal_training_evidence(transition, trace, inference)
        validate_binding(binding)
        self.assertEqual(binding.training_trace_sha256, trace.trace_sha256)
        self.assertEqual(binding.transition_trace_sha256, transition.trace_sha256)
        self.assertEqual(binding.inference_binding_sha256, inference.binding_sha256)
        self.assertEqual(binding.engine_load_consumption_receipt_sha256, "c" * 64)
        self.assertEqual(binding.output_sha256, "d" * 64)

    def test_shape_valid_but_false_route_hash_is_rejected_by_exact_transition_binding(self):
        transition = self.transition()
        bad_trace = self.training_trace(transition, route_decision_sha256="e" * 64)
        inference = bind_training_trace_to_inference(bad_trace, self.inference_receipt(bad_trace))
        with self.assertRaisesRegex(
            JSpaceCausalTrainingBindingError,
            "CAUSAL_BINDING_MISMATCH:route_decision_sha256",
        ):
            bind_causal_training_evidence(transition, bad_trace, inference)

    def test_shape_valid_but_false_grid_hash_is_rejected_by_exact_transition_binding(self):
        transition = self.transition()
        bad_trace = self.training_trace(transition, grid_plan_sha256="e" * 64)
        inference = bind_training_trace_to_inference(bad_trace, self.inference_receipt(bad_trace))
        with self.assertRaisesRegex(
            JSpaceCausalTrainingBindingError,
            "CAUSAL_BINDING_MISMATCH:grid_plan_sha256",
        ):
            bind_causal_training_evidence(transition, bad_trace, inference)

    def test_transition_vector_packet_must_match_training_packet_identity(self):
        transition, trace, inference = self.evidence()
        altered_transition = make_transition_trace(
            vector=(0.5, -0.5, 1.0, 0.125),
            trace_id="transition:altered-vector",
        )
        self.assertEqual(altered_transition.entry_event_sha256, transition.entry_event_sha256)
        with self.assertRaisesRegex(
            JSpaceCausalTrainingBindingError,
            "CAUSAL_BINDING_MISMATCH:transition_vector_packet_ref",
        ):
            bind_causal_training_evidence(altered_transition, trace, inference)

    def test_binding_digest_tamper_fails_closed(self):
        transition, trace, inference = self.evidence()
        binding = bind_causal_training_evidence(transition, trace, inference)
        tampered = replace(binding, model_call_id="call:changed")
        with self.assertRaisesRegex(
            JSpaceCausalTrainingBindingError,
            "JSPACE_CAUSAL_TRAINING_BINDING_DIGEST_MISMATCH",
        ):
            validate_binding(tampered)


if __name__ == "__main__":
    unittest.main()
