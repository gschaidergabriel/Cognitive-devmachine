import hashlib
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from global_jspace_gwt_v1 import CellContribution, step
from inference_receipt_v1 import make_inference_receipt
from jspace_inference_binding_v1 import bind_training_trace_to_inference, validate_binding
from jspace_model_input_control_closure_v1 import (
    JSpaceModelInputControlClosureError,
    close_model_input_control_into_jspace,
    validate_closure,
)
from jspace_training_trace_v1 import build_training_trace
from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_execution_admission_store_v1 import admit_and_verify_model_execution
from model_input_control_admission_store_v1 import admit_model_input_control_binding
from model_input_control_binding_v1 import bind_direct_unique_packet_input
from test_execution_store_inference_jspace_chain_v1 import (
    ADMITTED_BUDGET,
    GENERATION,
    digest,
    open_db,
    producer_fixture,
)


class JSpaceModelInputControlClosureTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.db_path = self.root / "miniunified.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def prototype(self, execution_role: str, output_cell_id: str):
        cells = [
            CellContribution(
                "cell-00",
                "retrieval",
                (0.2, 0.1, -0.1),
                0.1,
                0.1,
                0.1,
                0.1,
                0.1,
            ),
            CellContribution(
                output_cell_id,
                execution_role,
                (-0.3, 0.9, 0.4),
                0.8,
                0.95,
                0.7,
                0.4,
                0.2,
            ),
        ]
        return step(
            cells,
            generation=GENERATION,
            basis_id="basis:model-input-control-closure:v1",
            basis_sha256=digest("basis:model-input-control-closure:v1"),
        )

    def trace(self, proto, packet, decision, plan, execution):
        return build_training_trace(
            proto,
            packet,
            trace_id="trace:model-input-control-closure:v1",
            trace_family_id="episode:model-input-control-closure:v1",
            entry_event_sha256=plan.entry_event_sha256,
            entry_admission_sha256=plan.entry_admission_sha256,
            route_decision_sha256=decision.decision_sha256,
            grid_plan_sha256=plan.plan_sha256,
            jspace_input_vector_ref="unifieddb:jspace-input:model-input-control-closure:v1",
            local_workspace_state_ref="unifieddb:workspace:model-input-control-closure:v1",
            global_jspace_slice_ref="unifieddb:jspace-slice:model-input-control-closure:v1",
            hyperposition_branch_ids=("branch:control-closure:a", "branch:control-closure:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget=dict(ADMITTED_BUDGET),
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )

    def build_chain(self, *, control_packet_override=None):
        entry, decision, kwargs, observation = producer_fixture(self.root)
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]
        proto = self.prototype(observation.role, observation.output_producing_cell_id)
        trace_packet = proto.control_packet
        input_packet = control_packet_override or trace_packet
        consumed = (
            b'{"system":"hcu"}\n'
            + packet_bytes(input_packet)
            + b'\n{"prompt":"solve with admitted vector control"}'
        )
        observation = replace(
            observation,
            input_sha256=hashlib.sha256(consumed).hexdigest(),
            input_size=len(consumed),
        )

        db = open_db(self.db_path, plan.entity_generation)
        try:
            execution = admit_and_verify_model_execution(
                db,
                plan,
                load,
                observation,
                current_generation=plan.entity_generation,
            )
            control_binding = bind_direct_unique_packet_input(
                input_packet,
                consumed,
                generation=plan.entity_generation,
                entry_event_sha256=plan.entry_event_sha256,
                entry_admission_sha256=plan.entry_admission_sha256,
                route_decision_sha256=plan.route_decision_sha256,
                grid_plan_sha256=plan.plan_sha256,
                cell_id=execution.output_producing_cell_id,
                role=execution.role,
                executor_id=execution.executor_id,
                invocation_id=execution.invocation_id,
                executor_observed_input_sha256=observation.input_sha256,
                executor_observed_input_size=observation.input_size,
            )
            control_admission = admit_model_input_control_binding(
                db,
                control_binding,
                consumed,
                plan,
                current_generation=plan.entity_generation,
            )
        finally:
            db.close()

        local_kwargs = dict(kwargs)
        local_kwargs["verified_model_execution"] = execution
        local_kwargs["admitted_verified_model_executions"] = {
            execution.receipt_sha256: asdict(execution)
        }
        inference = make_inference_receipt(decision, **local_kwargs)
        trace = self.trace(proto, trace_packet, decision, plan, execution)
        jspace_binding = bind_training_trace_to_inference(trace, inference, plan)
        validate_binding(jspace_binding)
        return (
            plan,
            consumed,
            control_binding,
            control_admission,
            inference,
            jspace_binding,
            trace_packet,
        )

    def test_exact_control_delivery_closes_through_inference_and_jspace(self):
        (
            plan,
            consumed,
            control_binding,
            control_admission,
            inference,
            jspace_binding,
            trace_packet,
        ) = self.build_chain()
        closure = close_model_input_control_into_jspace(
            control_binding,
            control_admission,
            consumed,
            plan,
            inference,
            jspace_binding,
        )
        validate_closure(closure)
        self.assertEqual(closure.control_admission_sha256, control_admission.admission_sha256)
        self.assertEqual(closure.control_binding_sha256, control_binding.binding_sha256)
        self.assertEqual(closure.inference_receipt_sha256, inference.receipt_sha256)
        self.assertEqual(closure.jspace_binding_sha256, jspace_binding.binding_sha256)
        self.assertEqual(closure.vector_control_packet_sha256, trace_packet.packet_sha256)
        self.assertEqual(closure.input_sha256, hashlib.sha256(consumed).hexdigest())
        self.assertEqual(closure.grid_plan_sha256, plan.plan_sha256)

    def test_different_exact_input_packet_cannot_be_spliced_into_jspace_trace(self):
        entry, decision, kwargs, observation = producer_fixture(self.root)
        plan = kwargs["grid_plan"]
        wrong_packet = encode_vector(
            (0.1, -0.2, 0.3),
            basis_id="basis:wrong-input-control:v1",
            basis_sha256=digest("basis:wrong-input-control:v1"),
            generation=GENERATION,
            role=observation.role,
        )
        (
            plan,
            consumed,
            control_binding,
            control_admission,
            inference,
            jspace_binding,
            trace_packet,
        ) = self.build_chain(control_packet_override=wrong_packet)
        self.assertNotEqual(control_binding.vector_control_packet_sha256, trace_packet.packet_sha256)
        with self.assertRaisesRegex(
            JSpaceModelInputControlClosureError,
            "CONTROL_CLOSURE_MISMATCH:vector_control_packet_sha256",
        ):
            close_model_input_control_into_jspace(
                control_binding,
                control_admission,
                consumed,
                plan,
                inference,
                jspace_binding,
            )

    def test_serialized_closure_tamper_fails_digest(self):
        (
            plan,
            consumed,
            control_binding,
            control_admission,
            inference,
            jspace_binding,
            _trace_packet,
        ) = self.build_chain()
        closure = close_model_input_control_into_jspace(
            control_binding,
            control_admission,
            consumed,
            plan,
            inference,
            jspace_binding,
        )
        tampered = replace(closure, invocation_id="invocation:other")
        with self.assertRaisesRegex(
            JSpaceModelInputControlClosureError,
            "JSPACE_MODEL_INPUT_CONTROL_CLOSURE_DIGEST_MISMATCH",
        ):
            validate_closure(tampered)


if __name__ == "__main__":
    unittest.main()
