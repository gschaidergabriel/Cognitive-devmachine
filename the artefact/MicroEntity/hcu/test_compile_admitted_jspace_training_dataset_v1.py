import hashlib
import unittest
from unittest.mock import patch

from compile_admitted_jspace_training_dataset_v1 import (
    AdmittedTrainingDatasetError,
    PIPELINE_SCHEMA,
    compile_admitted_records,
    validate_pipeline_evidence,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA, STATUS as INFERENCE_RECEIPT_STATUS
from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA, DatasetAdmission
from jspace_inference_binding_v1 import SCHEMA as INFERENCE_BINDING_SCHEMA, JSpaceInferenceBinding
from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA


TRACE_SHA = "a" * 64
PROTOTYPE_SHA = "b" * 64
TRANSITION_SHA = "c" * 64
ENTRY_EVENT_SHA = "d" * 64
ENTRY_ADMISSION_SHA = "e" * 64
ROUTE_SHA = "1" * 64
GRID_SHA = "2" * 64
VECTOR_SHA = "3" * 64
ENGINE_ID_SHA = "5" * 64
ENGINE_ARTIFACT_SHA = "6" * 64
ENGINE_ADMISSION_SHA = "7" * 64
LOADER_BINDING_SHA = "8" * 64
LEASE_SHA = "9" * 64
LOAD_CONSUMPTION_SHA = "a1" * 32
OUTPUT_SHA = "b1" * 32
MODEL_EXECUTION_RECEIPT_SHA = "d1" * 32
MODEL_EXECUTION_OBSERVATION_SHA = "e1" * 32
INPUT_SHA = "f1" * 32
ROUTER_POLICY_SHA = "a2" * 32
MODEL_EXECUTION_EXECUTOR_ID = "executor:test:1"
MODEL_CALL_ID = "model-call:test:1"
GENERATION = 73
CELL_ID = "cell:critic:0"
ROLE = "critic"
BASIS_ID = "basis:test:admitted"
BASIS_SHA = "c1" * 32
CONTROL_CONDITION = "BASELINE"
ADMITTED_BASES = {BASIS_ID: BASIS_SHA}
ADMITTED_GRID_PLANS = {GRID_SHA: {"schema": "ENTITYOS_HCU_GRID_PLAN/v2"}}
ADMITTED_VECTOR_PACKETS = {VECTOR_SHA: "packet-preimage-covered-by-dedicated-gate-tests"}


def _training_trace(**overrides):
    value = {
        "schema_version": TRAINING_TRACE_SCHEMA,
        "trace_sha256": TRACE_SHA,
        "trace_family_id": "episode:test:admitted",
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


def _inference_receipt(**overrides):
    value = {
        "schema": INFERENCE_RECEIPT_SCHEMA,
        "status": INFERENCE_RECEIPT_STATUS,
        "hash_serialization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "entity_generation": GENERATION,
        "entry_admission_sha256": ENTRY_ADMISSION_SHA,
        "event_sha256": ENTRY_EVENT_SHA,
        "decision_sha256": ROUTE_SHA,
        "router_policy_sha256": ROUTER_POLICY_SHA,
        "engine_identity_sha256": ENGINE_ID_SHA,
        "resolved_engine_identity": "hcu_local_08b",
        "resolved_engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "resolved_engine_artifact_sha256": ENGINE_ARTIFACT_SHA,
        "engine_admission_receipt_sha256": ENGINE_ADMISSION_SHA,
        "engine_load_canonicalization_schema": CANONICALIZATION_SCHEMA,
        "engine_load_loader_binding_sha256": LOADER_BINDING_SHA,
        "engine_load_lease_sha256": LEASE_SHA,
        "engine_load_consumption_receipt_sha256": LOAD_CONSUMPTION_SHA,
        "engine_load_loader_id": "loader:test:1",
        "model_execution_canonicalization_schema": CANONICALIZATION_SCHEMA,
        "model_execution_receipt_sha256": MODEL_EXECUTION_RECEIPT_SHA,
        "model_execution_observation_sha256": MODEL_EXECUTION_OBSERVATION_SHA,
        "model_execution_executor_id": MODEL_EXECUTION_EXECUTOR_ID,
        "model_execution_invocation_id": MODEL_CALL_ID,
        "grid_plan_sha256": GRID_SHA,
        "output_producing_cell_id": CELL_ID,
        "model_execution_role": ROLE,
        "input_sha256": INPUT_SHA,
        "input_size": 11,
        "model_call_id": MODEL_CALL_ID,
        "output_ref": "unifieddb:model-output:test:1",
        "output_sha256": OUTPUT_SHA,
        "output_size": 17,
        "model_lanes": [ROLE],
    }
    value.update(overrides)
    value["receipt_sha256"] = hashlib.sha256(canonicalize(value)).hexdigest()
    return value


def _binding(trace=None, *, inference_receipt=None, **overrides):
    trace = trace or _training_trace()
    inference_receipt = inference_receipt or _inference_receipt()
    payload = {
        "schema": INFERENCE_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
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
        "inference_receipt_schema": INFERENCE_RECEIPT_SCHEMA,
        "inference_receipt_sha256": inference_receipt["receipt_sha256"],
        "engine_identity_sha256": ENGINE_ID_SHA,
        "resolved_engine_identity": "hcu_local_08b",
        "resolved_engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "resolved_engine_artifact_sha256": ENGINE_ARTIFACT_SHA,
        "engine_admission_receipt_sha256": ENGINE_ADMISSION_SHA,
        "engine_load_loader_binding_sha256": LOADER_BINDING_SHA,
        "engine_load_lease_sha256": LEASE_SHA,
        "engine_load_consumption_receipt_sha256": LOAD_CONSUMPTION_SHA,
        "engine_load_loader_id": "loader:test:1",
        "model_execution_receipt_sha256": MODEL_EXECUTION_RECEIPT_SHA,
        "model_execution_observation_sha256": MODEL_EXECUTION_OBSERVATION_SHA,
        "model_execution_executor_id": MODEL_EXECUTION_EXECUTOR_ID,
        "model_execution_invocation_id": MODEL_CALL_ID,
        "output_producing_cell_id": trace["cell_id"],
        "model_execution_role": trace["role"],
        "input_sha256": INPUT_SHA,
        "input_size": 11,
        "model_call_id": MODEL_CALL_ID,
        "output_ref": "unifieddb:model-output:test:1",
        "output_sha256": OUTPUT_SHA,
        "output_size": 17,
    }
    payload.update(overrides)
    payload["binding_sha256"] = hashlib.sha256(canonicalize(payload)).hexdigest()
    return JSpaceInferenceBinding(**payload)


def _compile_kwargs(trace, binding, receipt):
    return {
        "admitted_training_traces": {TRACE_SHA: trace},
        "admitted_transition_traces": {TRANSITION_SHA: {}},
        "admitted_prototype_traces": {PROTOTYPE_SHA: {}},
        "admitted_grid_plans": ADMITTED_GRID_PLANS,
        "admitted_vector_control_packets": ADMITTED_VECTOR_PACKETS,
        "admitted_inference_bindings": {TRACE_SHA: binding},
        "admitted_inference_receipts": {receipt["receipt_sha256"]: receipt},
        "admitted_bases": ADMITTED_BASES,
    }


class AdmittedJSpaceTrainingDatasetTests(unittest.TestCase):
    def test_pipeline_evidence_crossbinds_admission_inference_loader_and_output(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        evidence = validate_pipeline_evidence(trace, _admission(trace), _binding(trace, inference_receipt=receipt))
        self.assertEqual(evidence.schema, PIPELINE_SCHEMA)
        self.assertEqual(evidence.training_trace_sha256, TRACE_SHA)
        self.assertEqual(evidence.transition_trace_sha256, TRANSITION_SHA)
        self.assertEqual(evidence.inference_receipt_sha256, receipt["receipt_sha256"])
        self.assertEqual(evidence.engine_load_consumption_receipt_sha256, LOAD_CONSUMPTION_SHA)
        self.assertEqual(evidence.output_sha256, OUTPUT_SHA)

    def test_stale_v3_inference_fixture_fails_closed(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        with self.assertRaisesRegex(
            AdmittedTrainingDatasetError,
            "JSPACE_INFERENCE_BINDING_REJECTED:JSPACE_INFERENCE_BINDING_INFERENCE_SCHEMA_UNSUPPORTED",
        ):
            validate_pipeline_evidence(
                trace,
                _admission(trace),
                _binding(trace, inference_receipt=receipt, inference_receipt_schema="HCU_INFERENCE_RECEIPT/v3"),
            )

    def test_crossbound_causal_identity_mismatch_fails_closed(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        admission = _admission(trace, route_decision_sha256="ab" * 32)
        with self.assertRaisesRegex(AdmittedTrainingDatasetError, "CAUSAL_BINDING:route_decision_sha256"):
            validate_pipeline_evidence(trace, admission, _binding(trace, inference_receipt=receipt))

    def test_crossbound_vector_packet_mismatch_fails_closed(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        admission = _admission(trace, vector_control_packet_sha256="ab" * 32)
        with self.assertRaisesRegex(AdmittedTrainingDatasetError, "VECTOR_CONTROL_PACKET_BINDING"):
            validate_pipeline_evidence(trace, admission, _binding(trace, inference_receipt=receipt))

    def test_compile_path_requires_exact_admitted_inference_receipt(self):
        trace = _training_trace()
        transition = {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"}
        admission = _admission(trace)
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
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
            compiled = compile_admitted_records([(trace, transition)], **_compile_kwargs(trace, binding, receipt))
        gate.assert_called_once()
        self.assertEqual(
            gate.call_args.kwargs["admitted_vector_control_packets"],
            ADMITTED_VECTOR_PACKETS,
        )
        compiler.assert_called_once_with([dict(trace)], admitted_bases=ADMITTED_BASES)
        metadata = next(row for rows in compiled.values() for row in rows)["metadata"]
        self.assertEqual(metadata["pipeline_schema"], PIPELINE_SCHEMA)
        self.assertEqual(metadata["inference_receipt_sha256"], receipt["receipt_sha256"])
        self.assertEqual(metadata["engine_load_consumption_receipt_sha256"], LOAD_CONSUMPTION_SHA)
        self.assertEqual(metadata["model_output_sha256"], OUTPUT_SHA)

    def test_missing_inference_binding_cannot_reach_lower_level_compiler(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        admission = _admission(trace)
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=admission,
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as compiler:
            with self.assertRaisesRegex(AdmittedTrainingDatasetError, "INFERENCE_BINDING_NOT_ADMITTED_FOR_TRAINING_TRACE"):
                kwargs = _compile_kwargs(trace, _binding(trace, inference_receipt=receipt), receipt)
                kwargs["admitted_inference_bindings"] = {}
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    **kwargs,
                )
        compiler.assert_not_called()

    def test_missing_inference_receipt_cannot_reach_lower_level_compiler(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as compiler:
            kwargs = _compile_kwargs(trace, binding, receipt)
            kwargs["admitted_inference_receipts"] = {}
            with self.assertRaisesRegex(AdmittedTrainingDatasetError, "INFERENCE_RECEIPT_NOT_ADMITTED_FOR_BINDING"):
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    **kwargs,
                )
        compiler.assert_not_called()

    def test_self_consistent_binding_cannot_launder_admitted_receipt_output(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        forged = _binding(trace, inference_receipt=receipt, output_sha256="ab" * 32)
        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as compiler:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "INFERENCE_RECEIPT_BINDING_MISMATCH:output_sha256",
            ):
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    **_compile_kwargs(trace, forged, receipt),
                )
        compiler.assert_not_called()

    def test_duplicate_training_trace_with_conflicting_ancestry_fails_closed(self):
        trace = _training_trace()
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
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
            with self.assertRaisesRegex(AdmittedTrainingDatasetError, "TRAINING_TRACE_ANCESTRY_CONFLICT"):
                kwargs = _compile_kwargs(trace, binding, receipt)
                kwargs["admitted_transition_traces"] = {TRANSITION_SHA: {}, "de" * 32: {}}
                compile_admitted_records(
                    [
                        (trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1", "trace_sha256": TRANSITION_SHA}),
                        (trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1", "trace_sha256": "de" * 32}),
                    ],
                    **kwargs,
                )
        self.assertEqual(gate.call_count, 2)
        compiler.assert_called_once_with([dict(trace)], admitted_bases=ADMITTED_BASES)


if __name__ == "__main__":
    unittest.main()
