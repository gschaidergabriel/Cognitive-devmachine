import hashlib
import unittest

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA
from jspace_inference_binding_v1 import (
    SCHEMA as INFERENCE_BINDING_SCHEMA,
    JSpaceInferenceBinding,
)
from jspace_model_input_control_closure_v1 import (
    SCHEMA as CLOSURE_SCHEMA,
    JSpaceModelInputControlClosure,
)
from jspace_training_control_delivery_gate_v1 import (
    JSpaceTrainingControlDeliveryError,
    require_model_input_control_closure,
)
from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
from model_input_control_admission_store_v1 import ADMISSION_SCHEMA as CONTROL_ADMISSION_SCHEMA
from model_input_control_binding_v1 import BINDING_SCHEMA as CONTROL_BINDING_SCHEMA


TRACE_SHA = "aa" * 32
PROTOTYPE_SHA = "bb" * 32
ENTRY_EVENT_SHA = "cc" * 32
ENTRY_ADMISSION_SHA = "dd" * 32
ROUTE_SHA = "11" * 32
GRID_SHA = "22" * 32
VECTOR_SHA = "33" * 32
INFERENCE_RECEIPT_SHA = "44" * 32
JSPACE_BINDING_SHA = "55" * 32
MODEL_EXECUTION_OBSERVATION_SHA = "66" * 32
INPUT_SHA = "77" * 32
GENERATION = 19
CELL_ID = "cell:critic:0"
ROLE = "critic"
EXECUTOR_ID = "executor:test:control-delivery"
INVOCATION_ID = "invocation:test:control-delivery"


def _trace(*, condition="LESION", vector_sha=VECTOR_SHA):
    return {
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
        "vector_control_packet_sha256": vector_sha,
        "vector_control_condition": condition,
    }


def _binding(*, vector_sha=VECTOR_SHA, binding_sha=JSPACE_BINDING_SHA):
    return JSpaceInferenceBinding(
        schema=INFERENCE_BINDING_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        training_trace_schema=TRAINING_TRACE_SCHEMA,
        training_trace_sha256=TRACE_SHA,
        prototype_trace_sha256=PROTOTYPE_SHA,
        generation=GENERATION,
        entry_event_sha256=ENTRY_EVENT_SHA,
        entry_admission_sha256=ENTRY_ADMISSION_SHA,
        route_decision_sha256=ROUTE_SHA,
        grid_plan_sha256=GRID_SHA,
        cell_id=CELL_ID,
        role=ROLE,
        vector_control_packet_sha256=vector_sha,
        inference_receipt_schema=INFERENCE_RECEIPT_SCHEMA,
        inference_receipt_sha256=INFERENCE_RECEIPT_SHA,
        engine_identity_sha256="88" * 32,
        resolved_engine_identity="hcu_local_08b",
        resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
        resolved_engine_artifact_sha256="99" * 32,
        engine_admission_receipt_sha256="a1" * 32,
        engine_load_loader_binding_sha256="a2" * 32,
        engine_load_lease_sha256="a3" * 32,
        engine_load_consumption_receipt_sha256="a4" * 32,
        engine_load_loader_id="loader:test:1",
        model_execution_receipt_sha256="a5" * 32,
        model_execution_observation_sha256=MODEL_EXECUTION_OBSERVATION_SHA,
        model_execution_executor_id=EXECUTOR_ID,
        model_execution_invocation_id=INVOCATION_ID,
        output_producing_cell_id=CELL_ID,
        model_execution_role=ROLE,
        input_sha256=INPUT_SHA,
        input_size=11,
        model_call_id=INVOCATION_ID,
        output_ref="unifieddb:model-output:test:control-delivery",
        output_sha256="a6" * 32,
        output_size=17,
        binding_sha256=binding_sha,
    )


def _closure(*, vector_sha=VECTOR_SHA, binding_sha=JSPACE_BINDING_SHA):
    material = {
        "schema": CLOSURE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "control_admission_schema": CONTROL_ADMISSION_SCHEMA,
        "control_admission_sha256": "b1" * 32,
        "control_binding_schema": CONTROL_BINDING_SCHEMA,
        "control_binding_sha256": "b2" * 32,
        "model_execution_observation_sha256": MODEL_EXECUTION_OBSERVATION_SHA,
        "inference_receipt_schema": INFERENCE_RECEIPT_SCHEMA,
        "inference_receipt_sha256": INFERENCE_RECEIPT_SHA,
        "jspace_binding_schema": INFERENCE_BINDING_SCHEMA,
        "jspace_binding_sha256": binding_sha,
        "generation": GENERATION,
        "entry_event_sha256": ENTRY_EVENT_SHA,
        "entry_admission_sha256": ENTRY_ADMISSION_SHA,
        "route_decision_sha256": ROUTE_SHA,
        "grid_plan_sha256": GRID_SHA,
        "cell_id": CELL_ID,
        "role": ROLE,
        "vector_control_packet_sha256": vector_sha,
        "executor_id": EXECUTOR_ID,
        "invocation_id": INVOCATION_ID,
        "input_sha256": INPUT_SHA,
        "input_size": 11,
    }
    return JSpaceModelInputControlClosure(
        **material,
        closure_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
    )


class JSpaceTrainingControlDeliveryGateTests(unittest.TestCase):
    def test_baseline_does_not_claim_intervention_delivery(self):
        self.assertIsNone(
            require_model_input_control_closure(_trace(condition="BASELINE"), _binding(), None)
        )

    def test_non_baseline_requires_model_input_control_closure(self):
        with self.assertRaisesRegex(
            JSpaceTrainingControlDeliveryError,
            "MODEL_INPUT_CONTROL_CLOSURE_REQUIRED_FOR_NON_BASELINE_TRAINING",
        ):
            require_model_input_control_closure(_trace(condition="LESION"), _binding(), None)

    def test_exact_non_baseline_delivery_closure_is_admitted(self):
        closure = _closure()
        self.assertEqual(
            require_model_input_control_closure(_trace(), _binding(), closure),
            closure.closure_sha256,
        )

    def test_vector_control_label_cannot_launder_different_delivered_packet(self):
        with self.assertRaisesRegex(
            JSpaceTrainingControlDeliveryError,
            "TRAINING_CONTROL_DELIVERY_MISMATCH:vector_control_packet_sha256",
        ):
            require_model_input_control_closure(
                _trace(vector_sha="c1" * 32),
                _binding(vector_sha="c1" * 32),
                _closure(vector_sha="c2" * 32),
            )

    def test_closure_cannot_bind_a_different_jspace_inference_identity(self):
        with self.assertRaisesRegex(
            JSpaceTrainingControlDeliveryError,
            "TRAINING_CONTROL_DELIVERY_MISMATCH:jspace_binding_sha256",
        ):
            require_model_input_control_closure(
                _trace(),
                _binding(binding_sha="d1" * 32),
                _closure(binding_sha="d2" * 32),
            )


if __name__ == "__main__":
    unittest.main()
