#!/usr/bin/env python3
"""Integration regressions for the single admitted J-Space training compiler control gate.

These tests deliberately reuse the existing compiler fixtures. They prove only deterministic
source-path behavior: a non-BASELINE TrainingTrace cannot reach the lower-level compiler unless
its exact JSpaceInferenceBinding has an admitted model-input-control closure, and an admitted
closure digest is carried into emitted row metadata. They create no runtime/model/training or
whole-product credit.
"""
from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from compile_admitted_jspace_training_dataset_v1 import (
    AdmittedTrainingDatasetError,
    compile_admitted_records,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA
from jspace_inference_binding_v1 import SCHEMA as INFERENCE_BINDING_SCHEMA
from jspace_model_input_control_closure_v1 import (
    SCHEMA as CLOSURE_SCHEMA,
    JSpaceModelInputControlClosure,
)
from model_input_control_admission_store_v1 import ADMISSION_SCHEMA as CONTROL_ADMISSION_SCHEMA
from model_input_control_binding_v1 import BINDING_SCHEMA as CONTROL_BINDING_SCHEMA
from test_compile_admitted_jspace_training_dataset_v1 import (
    TRACE_SHA,
    _admission,
    _binding,
    _compile_kwargs,
    _inference_receipt,
    _training_trace,
)


def _closure(trace, binding):
    material = {
        "schema": CLOSURE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "control_admission_schema": CONTROL_ADMISSION_SCHEMA,
        "control_admission_sha256": "b2" * 32,
        "control_binding_schema": CONTROL_BINDING_SCHEMA,
        "control_binding_sha256": "b3" * 32,
        "model_execution_observation_sha256": binding.model_execution_observation_sha256,
        "inference_receipt_schema": INFERENCE_RECEIPT_SCHEMA,
        "inference_receipt_sha256": binding.inference_receipt_sha256,
        "jspace_binding_schema": INFERENCE_BINDING_SCHEMA,
        "jspace_binding_sha256": binding.binding_sha256,
        "generation": trace["generation"],
        "entry_event_sha256": trace["entry_event_sha256"],
        "entry_admission_sha256": trace["entry_admission_sha256"],
        "route_decision_sha256": trace["route_decision_sha256"],
        "grid_plan_sha256": trace["grid_plan_sha256"],
        "cell_id": trace["cell_id"],
        "role": trace["role"],
        "vector_control_packet_sha256": trace["vector_control_packet_sha256"],
        "executor_id": binding.model_execution_executor_id,
        "invocation_id": binding.model_execution_invocation_id,
        "input_sha256": binding.input_sha256,
        "input_size": binding.input_size,
    }
    return JSpaceModelInputControlClosure(
        **material,
        closure_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
    )


def _lower_rows():
    return {
        "train": [{"messages": [], "metadata": {"trace_sha256": TRACE_SHA}}],
        "validation": [],
        "holdout": [],
    }


class AdmittedTrainingControlDeliveryIntegrationTests(unittest.TestCase):
    def test_nonbaseline_without_closure_fails_before_lower_level_compiler(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        kwargs = _compile_kwargs(trace, binding, receipt)
        kwargs["admitted_model_input_control_closures"] = {}

        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as lower_compiler:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_DELIVERY_REJECTED:MODEL_INPUT_CONTROL_CLOSURE_REQUIRED_FOR_NON_BASELINE_TRAINING",
            ):
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    **kwargs,
                )
        lower_compiler.assert_not_called()

    def test_nonbaseline_exact_closure_reaches_single_compiler_and_is_annotated(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        closure = _closure(trace, binding)
        kwargs = _compile_kwargs(trace, binding, receipt)
        kwargs["admitted_model_input_control_closures"] = {
            binding.binding_sha256: closure,
        }

        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
            return_value=_lower_rows(),
        ) as lower_compiler:
            compiled = compile_admitted_records(
                [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                **kwargs,
            )

        lower_compiler.assert_called_once()
        row = next(row for rows in compiled.values() for row in rows)
        self.assertEqual(
            row["metadata"]["model_input_control_closure_sha256"],
            closure.closure_sha256,
        )

    def test_closure_under_wrong_binding_registry_key_cannot_be_laundered(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        closure = _closure(trace, binding)
        kwargs = _compile_kwargs(trace, binding, receipt)
        kwargs["admitted_model_input_control_closures"] = {
            "ef" * 32: closure,
        }

        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as lower_compiler:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_CLOSURE_REQUIRED_FOR_NON_BASELINE_TRAINING",
            ):
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    **kwargs,
                )
        lower_compiler.assert_not_called()

    def test_baseline_remains_nonintervention_and_emits_null_closure_digest(self):
        trace = _training_trace(vector_control_condition="BASELINE")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        kwargs = _compile_kwargs(trace, binding, receipt)

        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
            return_value=_lower_rows(),
        ):
            compiled = compile_admitted_records(
                [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                **kwargs,
            )

        row = next(row for rows in compiled.values() for row in rows)
        self.assertIsNone(row["metadata"]["model_input_control_closure_sha256"])


if __name__ == "__main__":
    unittest.main()
