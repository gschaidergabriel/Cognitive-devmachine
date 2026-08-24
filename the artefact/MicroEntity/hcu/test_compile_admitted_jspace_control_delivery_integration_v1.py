import unittest
from unittest.mock import patch

from compile_admitted_jspace_training_dataset_v1 import (
    AdmittedTrainingDatasetError,
    compile_admitted_records,
)
from test_compile_admitted_jspace_training_dataset_v1 import (
    ADMITTED_BASES,
    TRACE_SHA,
    _admission,
    _binding,
    _compile_kwargs,
    _inference_receipt,
    _training_trace,
)


CLOSURE_SHA = "f2" * 32


class AdmittedJSpaceControlDeliveryIntegrationTests(unittest.TestCase):
    def test_nonbaseline_without_delivery_closure_cannot_emit_training_rows(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)

        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
        ) as lower_compiler:
            with self.assertRaisesRegex(
                AdmittedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_DELIVERY_REJECTED:"
                "MODEL_INPUT_CONTROL_CLOSURE_REQUIRED_FOR_NON_BASELINE_TRAINING",
            ):
                compile_admitted_records(
                    [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                    **_compile_kwargs(trace, binding, receipt),
                )

        lower_compiler.assert_not_called()

    def test_admitted_delivery_digest_is_bound_into_emitted_row_metadata(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        admitted_closure = object()
        lower_rows = {
            "train": [{"messages": [], "metadata": {"trace_sha256": TRACE_SHA}}],
            "validation": [],
            "holdout": [],
        }
        kwargs = _compile_kwargs(trace, binding, receipt)
        kwargs["admitted_model_input_control_closures"] = {
            binding.binding_sha256: admitted_closure,
        }

        with patch(
            "compile_admitted_jspace_training_dataset_v1.admit_for_training_dataset",
            return_value=_admission(trace),
        ), patch(
            "compile_admitted_jspace_training_dataset_v1.require_model_input_control_closure",
            return_value=CLOSURE_SHA,
        ) as delivery_gate, patch(
            "compile_admitted_jspace_training_dataset_v1.compile_training_traces",
            return_value=lower_rows,
        ) as lower_compiler:
            compiled = compile_admitted_records(
                [(trace, {"schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1"})],
                **kwargs,
            )

        delivery_gate.assert_called_once_with(trace, binding, admitted_closure)
        lower_compiler.assert_called_once_with([dict(trace)], admitted_bases=ADMITTED_BASES)
        metadata = next(row for rows in compiled.values() for row in rows)["metadata"]
        self.assertEqual(metadata["model_input_control_closure_sha256"], CLOSURE_SHA)


if __name__ == "__main__":
    unittest.main()
