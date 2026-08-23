import hashlib
import unittest
from unittest.mock import patch

from compile_admitted_jspace_training_dataset_v1 import (
    AdmittedTrainingDatasetError,
    PIPELINE_SCHEMA,
    compile_admitted_records,
    validate_pipeline_evidence,
)
from entry_canonicalization_v1 import canonicalize
from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA, DatasetAdmission
from jspace_inference_binding_v1 import SCHEMA as INFERENCE_BINDING_SCHEMA, JSpaceInferenceBinding
from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA


TRACE_SHA = "a" * 64
PROTOTYPE_SHA = "b" * 64
TRANSITION_SHA = "c" * 64
ENTRY_EVENT_SHA = "d" * 64
ENTRY_ADMISSION_SHA = "e" * 64
ROUTE_SHA = "1" * 64
GRID_SHA = "2" * 64
VECTOR_SHA = "3" * 64
INFERENCE_SHA = "4" * 64
ENGINE_ID_SHA = "5" * 64
ENGINE_ARTIFACT_SHA = "6" * 64
ENGINE_ADMISSION_SHA = "7" * 64
LOADER_BINDING_SHA = "8" * 64
LEASE_SHA = "9" * 64
LOAD_CONSUMPTION_SHA = "a1" * 32
OUTPUT_SHA = "b1" * 32
GENERATION = 73
CELL_ID = "cell:critic:0"
ROLE = "critic"
BASIS_ID = "basis:test:admitted"
BASIS_SHA = "c1" * 32
CONTROL_CONDITION = "BASELINE"
ADMITTED_BASES = {BASIS_ID: BASIS_SHA}
ADMITTED_GRID_PLANS = {GRID_SHA: {"schema": "ENTITYOS_HCU_GRID_PLAN/v2"}}


def _training_trace(**overrides):
    value = {
        "schema_version": TRAINING_TRACE_SCHEMA,
        "trace_sha256": TRACE_SHA,
        "prototype_trace_sha256": PROTOTYPE_SHA,
        "generation": GENERATION,
        "entry_event_sha256": ENTRY_EVENT_SHA,
        "entry_admission_sha256": ENTRY_ADMISSION_SHA,
        "route_decision_sha256": ROUTE_SHA,
        "grid_plan_sha256": GRID_SHA,
        "cell_id": CELL_ID,
        "role": ROLE,
        "vector_control_packet_sha256": VECTOR_SHA,
        "vector_control_condition": CONTROL_CONDITION,
        "credit_label": "UNKNOWN",
        "outcome_receipt_sha256": None,
    }
    value.update(overrides)
    return value


def _admission(trace=None, **overrides):
    trace = trace or _training_trace()
    value = {
        "schema": ADMISSION_SCHEMA,
        "training_trace_sha256": trace["trace_sha256"],
        "transition_trace_sha256": TRANSITION_SHA,
        "prototype_trace_sha256": trace["prototype_trace_sha256"],
        "generation": trace["generation"],
        "entry_event_sha256": trace["entry_event_sha256"],
        "entry_admission_sha256": trace["entry_admission_sha256"],
        "route_decision_sha256": trace["route_decision_sha256"],
        "grid_plan_sha256": trace["grid_plan_sha256"],
        "cell_id": trace["cell_id"],
        "role": trace["role"],
        "jspace_basis_id": BASIS_ID,
        "jspace_basis_sha256": BASIS_SHA,
        "vector_control_packet_sha256": trace["vector_control_packet_sha256"],
        "vector_control_condition": trace["vector_control_condition"],
        "credit_label": trace["credit_label"],
        "outcome_receipt_sha256": trace["outcome_receipt_sha256"],
    }
    value.update(overrides)
    return DatasetAdmission(**value)


def _binding(trace=None, **overrides):
    trace = trace or _training_trace()
    payload = {
        "schema": INFERENCE_BINDING_SCHEMA,
        "canonicalization_schema": "RFC8785_JCS_IJSON/v1",
        "training_trace_schema": TRAINING_TRACE_SCHEMA,
        "training_trace_sha256": trace["trace_sha256"],
        "prototype_trace_sha256": trace["prototype_trace_sha256"],
        "generation": trace["generation"],
        "entry_event_sha256": trace["entry_event_sha256"],
        "entry_admission_sha256": trace["entry_admission_sha256"],
        "route_decision_sha256": trace["route_decision_sha256"],
        "grid_plan_sha256": trace["grid_plan_sha256"],
        "cell_id": trace["cell_id"],
        "role": trace["role"],
        "vector_control_packet_sha256": trace["vector_control_packet_sha256"],
        "inference_receipt_schema": "HCU_INFERENCE_RECEIPT/v3",
        "inference_receipt_sha256": INFERENCE_SHA,
        "engine_identity_sha256": ENGINE_ID_SHA,
        "resolved_engine_identity": "hcu_local_08b",
        "resolved_engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "resolved_engine_artifact_sha256": ENGINE_ARTIFACT_SHA,
        "engine_admission_receipt_sha256": ENGINE_ADMISSION_SHA,
        "engine_load_loader_binding_sha256": LOADER_BINDING_SHA,
        "engine_load_lease_sha256": LEASE_SHA,
        "engine_load_consumption_receipt_sha256": LOAD_CONSUMPTION_SHA,
        "engine_load_loader_id": "loader:test:1",
        "model_call_id": "model-call:test:1",
        "output_ref": "unifieddb:model-output:test:1",
        "output_sha256": OUTPUT_SHA,
        "output_size": 17,
    }
    payload.update(overrides)
    payload["binding_sha256"] = hashlib.sha256(canonicalize(payload)).hexdigest()
    return JSpaceInferenceBinding(**payload)


class AdmittedJSpaceTrainingDatasetTests(unittest.TestCase):
    def test_pipeline_evidence_crossbinds_admission_inference_loader_and_output(self):
        trace = _training_trace()
        evidence = validate_pipeline_evidence(trace, _admission(trace), _binding(trace))
        self.assertEqual(evidence.schema, PIPELINE_SCHEMA)
        self.assertEqual(evidence.training_trace_sha256, TRACE_SHA)
        self.assertEqual(evidence.transition_trace_sha256, TRANSITION_SHA)
        self.assertEqual(evidence.inference_receipt_sha256, INFERENCE_SHA)
        self.assertEqual(evidence.engine_load_consumption_receipt_sha256, LOAD_CONSUMPTION_SHA)
        self.assertEqual(evidence.output_sha256, OUTPUT_SHA)

    def test_crossbound_causal_identity_mismatch_fails_closed(self):
        trace = _training_trace()
        admission = _admission(trace, route_decision_sha256="ab" * 32)
        with self.assertRaisesRegex(AdmittedTrainingDatasetError, "CAUSAL_BINDING:route_decision_sha256"):
            validate_pipeline_evidence(trace, admission, _binding(trace))

    def test_crossbound_vector_packet_mismatch_fails_closed(self):
        trace = _training_trace()
        admission = _admission(trace, vector_control_packet_sha256="ab" * 32)
        with self.assertRaisesRegex(AdmittedTrainingDatasetError, "VECTOR_CONTROL_PACKET_BINDING"):
            validate_pipeline_evidence(trace, admission, _binding(trace))

    def test_compile_path_invokes_dataset_gate_and_selected_basis_guard(self):
        trace = _training_trace()
        transition = {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"}
        admission = _admission(trace)
        binding = _binding(trace)
        lower = {
            "train": [{"messages": [], "metadata": {"trace_sha256": TRACE_SHA}}],
            "validation": [],
            "holdout": [],
        }
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=admission,
        ) as gate, patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
            return_value=lower,
        ) as compiler:
            compiled = compile_admitted_records(
                [(trace, transition)],
                admitted_training_traces={TRACE_SHA: trace},
                admitted_transition_traces={TRANSITION_SHA: {}},
                admitted_prototype_traces={PROTOTYPE_SHA: {}},
                admitted_grid_plans=ADMITTED_GRID_PLANS,
                admitted_inference_bindings={TRACE_SHA: binding},
                admitted_bases=ADMITTED_BASES,
            )
        gate.assert_called_once_with(
            trace,
            transition,
            admitted_training_traces={TRACE_SHA: trace},
            admitted_transition_traces={TRANSITION_SHA: {}},
            admitted_prototype_traces={PROTOTYPE_SHA: {}},
            admitted_grid_plans=ADMITTED_GRID_PLANS,
            admitted_outcome_receipts=None,
        )
        compiler.assert_called_once_with([dict(trace)], admitted_bases=ADMITTED_BASES)
        metadata = compiled["train"][0]["metadata"]
        self.assertEqual(metadata["pipeline_schema"], PIPELINE_SCHEMA)
        self.assertEqual(metadata["inference_receipt_sha256"], INFERENCE_SHA)
        self.assertEqual(metadata["engine_load_consumption_receipt_sha256"], LOAD_CONSUMPTION_SHA)
        self.assertEqual(metadata["model_output_sha256"], OUTPUT_SHA)

    def test_missing_inference_binding_cannot_reach_lower_level_compiler(self):
        trace = _training_trace()
        admission = _admission(trace)
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=admission,
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as compiler:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "INFERENCE_BINDING_NOT_ADMITTED_FOR_TRAINING_TRACE",
            ):
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    admitted_training_traces={TRACE_SHA: trace},
                    admitted_transition_traces={TRANSITION_SHA: {}},
                    admitted_prototype_traces={PROTOTYPE_SHA: {}},
                    admitted_grid_plans=ADMITTED_GRID_PLANS,
                    admitted_inference_bindings={},
                    admitted_bases=ADMITTED_BASES,
                )
        compiler.assert_not_called()

    def test_duplicate_training_trace_with_conflicting_ancestry_fails_closed(self):
        trace = _training_trace()
        binding = _binding(trace)
        first = _admission(trace)
        second = _admission(trace, transition_trace_sha256="de" * 32)
        lower = {
            "train": [{"messages": [], "metadata": {"trace_sha256": TRACE_SHA}}],
            "validation": [],
            "holdout": [],
        }
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            side_effect=[first, second],
        ) as gate, patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
            return_value=lower,
        ) as compiler:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "TRAINING_TRACE_ANCESTRY_CONFLICT",
            ):
                compile_admitted_records(
                    [
                        (trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1", "trace_sha256": TRANSITION_SHA}),
                        (trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1", "trace_sha256": "de" * 32}),
                    ],
                    admitted_training_traces={TRACE_SHA: trace},
                    admitted_transition_traces={TRANSITION_SHA: {}, "de" * 32: {}},
                    admitted_prototype_traces={PROTOTYPE_SHA: {}},
                    admitted_grid_plans=ADMITTED_GRID_PLANS,
                    admitted_inference_bindings={TRACE_SHA: binding},
                    admitted_bases=ADMITTED_BASES,
                )
        self.assertEqual(gate.call_count, 2)
        compiler.assert_called_once_with([dict(trace)], admitted_bases=ADMITTED_BASES)


if __name__ == "__main__":
    unittest.main()
