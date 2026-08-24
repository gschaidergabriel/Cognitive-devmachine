import hashlib
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

from compile_admitted_jspace_training_dataset_v1 import (
    AdmittedTrainingDatasetError,
    compile_admitted_records,
)
from entry_canonicalization_v1 import canonicalize
from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA, DatasetAdmission
from jspace_model_input_control_closure_v1 import close_model_input_control_into_jspace, validate_closure
from jspace_training_control_source_revalidation_v1 import TrainingControlSourceContext
from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
from test_execution_store_inference_jspace_chain_v1 import open_db
from test_jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosureTests


class AdmittedJSpaceTrainingControlSourceRevalidationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = JSpaceModelInputControlClosureTests(
            methodName="test_exact_control_delivery_closes_through_inference_and_jspace"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def build(self):
        (
            plan,
            consumed,
            control_binding,
            control_admission,
            inference,
            jspace_binding,
            _trace_packet,
        ) = self.fixture.build_chain()
        closure = close_model_input_control_into_jspace(
            control_binding,
            control_admission,
            consumed,
            plan,
            inference,
            jspace_binding,
        )
        db = open_db(self.fixture.db_path, plan.entity_generation)
        self.addCleanup(db.close)
        context = TrainingControlSourceContext(
            db=db,
            control_binding=control_binding,
            consumed_input_bytes=consumed,
            grid_plan=plan,
            inference_receipt=inference,
            current_generation=plan.entity_generation,
        )
        trace = {
            "schema_version": TRAINING_TRACE_SCHEMA,
            "trace_sha256": jspace_binding.training_trace_sha256,
            "trace_family_id": "episode:compiler-control-source-revalidation:v1",
            "prototype_trace_sha256": jspace_binding.prototype_trace_sha256,
            "generation": jspace_binding.generation,
            "entry_event_sha256": jspace_binding.entry_event_sha256,
            "entry_admission_sha256": jspace_binding.entry_admission_sha256,
            "route_decision_sha256": jspace_binding.route_decision_sha256,
            "grid_plan_sha256": jspace_binding.grid_plan_sha256,
            "cell_id": jspace_binding.cell_id,
            "role": jspace_binding.role,
            "vector_control_packet_sha256": jspace_binding.vector_control_packet_sha256,
            "vector_control_condition": "BASELINE",
            "credit_label": "UNKNOWN",
            "outcome_receipt_sha256": None,
        }
        transition_sha = hashlib.sha256(b"compiler-control-source-transition").hexdigest()
        basis_sha = hashlib.sha256(b"compiler-control-source-basis").hexdigest()
        admission = DatasetAdmission(
            schema=ADMISSION_SCHEMA,
            training_trace_sha256=trace["trace_sha256"],
            transition_trace_sha256=transition_sha,
            prototype_trace_sha256=trace["prototype_trace_sha256"],
            generation=trace["generation"],
            entry_event_sha256=trace["entry_event_sha256"],
            entry_admission_sha256=trace["entry_admission_sha256"],
            route_decision_sha256=trace["route_decision_sha256"],
            grid_plan_sha256=trace["grid_plan_sha256"],
            cell_id=trace["cell_id"],
            role=trace["role"],
            jspace_basis_id="basis:compiler-control-source:v1",
            jspace_basis_sha256=basis_sha,
            vector_control_packet_sha256=trace["vector_control_packet_sha256"],
            vector_control_condition=trace["vector_control_condition"],
            credit_label=trace["credit_label"],
            outcome_receipt_sha256=None,
        )
        transition = {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"}
        kwargs = {
            "admitted_training_traces": {trace["trace_sha256"]: trace},
            "admitted_transition_traces": {transition_sha: transition},
            "admitted_prototype_traces": {trace["prototype_trace_sha256"]: {}},
            "admitted_grid_plans": {plan.plan_sha256: {"schema": plan.schema}},
            "admitted_vector_control_packets": {
                trace["vector_control_packet_sha256"]: "exact-preimage-covered-upstream"
            },
            "admitted_inference_bindings": {trace["trace_sha256"]: jspace_binding},
            "admitted_inference_receipts": {inference.receipt_sha256: asdict(inference)},
            "admitted_bases": {"basis:compiler-control-source:v1": basis_sha},
            "admitted_model_input_control_closures": {
                jspace_binding.binding_sha256: closure
            },
            "model_input_control_source_contexts": {
                jspace_binding.binding_sha256: context
            },
        }
        return trace, transition, admission, closure, jspace_binding, kwargs

    @staticmethod
    def lower_result(trace_sha256):
        return {
            "train": [{"messages": [], "metadata": {"trace_sha256": trace_sha256}}],
            "validation": [],
            "holdout": [],
        }

    def test_compiler_accepts_only_source_revalidated_supplied_closure(self):
        trace, transition, admission, closure, _binding, kwargs = self.build()
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=admission,
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
            return_value=self.lower_result(trace["trace_sha256"]),
        ) as lower:
            compiled = compile_admitted_records([(trace, transition)], **kwargs)
        lower.assert_called_once()
        row = next(row for rows in compiled.values() for row in rows)
        self.assertEqual(
            row["metadata"]["model_input_control_closure_sha256"],
            closure.closure_sha256,
        )

    def test_compiler_rejects_digest_valid_forged_control_admission_before_rows(self):
        trace, transition, admission, closure, binding, kwargs = self.build()
        forged_admission_sha256 = hashlib.sha256(
            b"compiler-forged-control-admission"
        ).hexdigest()
        material = asdict(closure)
        material["control_admission_sha256"] = forged_admission_sha256
        material.pop("closure_sha256")
        forged = replace(
            closure,
            control_admission_sha256=forged_admission_sha256,
            closure_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
        )
        validate_closure(forged)
        kwargs["admitted_model_input_control_closures"] = {
            binding.binding_sha256: forged
        }
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=admission,
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as lower:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_SOURCE_REVALIDATION_REJECTED:.*SOURCE_MISMATCH",
            ):
                compile_admitted_records([(trace, transition)], **kwargs)
        lower.assert_not_called()

    def test_compiler_rejects_supplied_closure_without_source_context_before_rows(self):
        trace, transition, admission, _closure, _binding, kwargs = self.build()
        kwargs["model_input_control_source_contexts"] = {}
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=admission,
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as lower:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_SOURCE_REVALIDATION_REJECTED:MODEL_INPUT_CONTROL_SOURCE_CONTEXT_REQUIRED_FOR_JSPACE_BINDING",
            ):
                compile_admitted_records([(trace, transition)], **kwargs)
        lower.assert_not_called()


if __name__ == "__main__":
    unittest.main()
