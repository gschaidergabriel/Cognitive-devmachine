import unittest
from unittest.mock import patch

from compile_source_revalidated_jspace_training_dataset_v1 import (
    InferenceBindingSourceBundle,
    ModelInputControlClosureSourceBundle,
    SourceRevalidatedTrainingDatasetError,
    compile_source_revalidated_records,
)
from jspace_inference_binding_v1 import JSpaceInferenceBindingError
from jspace_model_input_control_closure_revalidation_v1 import (
    JSpaceModelInputControlClosureRevalidationError,
)
from test_compile_admitted_jspace_training_dataset_v1 import (
    TRACE_SHA,
    _binding,
    _inference_receipt,
    _training_trace,
)


class SourceRevalidatedTrainingDatasetTests(unittest.TestCase):
    def _kwargs(self, trace, binding, receipt, *, controls=None):
        inference_source = InferenceBindingSourceBundle(
            training_trace=object(),
            inference_receipt=receipt,
            grid_plan=object(),
        )
        return {
            "canonical_db": object(),
            "current_generation": 73,
            "inference_binding_source_bundles": {
                binding.binding_sha256: inference_source,
            },
            "model_input_control_source_bundles": controls or {},
            "admitted_training_traces": {},
            "admitted_transition_traces": {},
            "admitted_prototype_traces": {},
            "admitted_grid_plans": {},
            "admitted_vector_control_packets": {},
            "admitted_inference_bindings": {TRACE_SHA: binding},
            "admitted_inference_receipts": {},
            "admitted_bases": {},
        }

    def test_nonbaseline_cannot_compile_without_canonical_control_source_bundle(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.trace_dict",
            return_value=trace,
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_binding_against_sources"
        ) as revalidate_binding, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records"
        ) as compiler:
            with self.assertRaisesRegex(
                SourceRevalidatedTrainingDatasetError,
                "CANONICAL_CONTROL_SOURCE_BUNDLE_REQUIRED_FOR_NON_BASELINE_TRAINING",
            ):
                compile_source_revalidated_records(
                    [(trace, {})],
                    **self._kwargs(trace, binding, receipt),
                )
        revalidate_binding.assert_called_once()
        compiler.assert_not_called()

    def test_baseline_requires_binding_rehydration_then_delegates_without_control_closure(self):
        trace = _training_trace(vector_control_condition="BASELINE")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        expected = {"train": [], "validation": [], "holdout": []}
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.trace_dict",
            return_value=trace,
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_binding_against_sources"
        ) as revalidate_binding, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records",
            return_value=expected,
        ) as compiler:
            observed = compile_source_revalidated_records(
                [(trace, {})],
                **self._kwargs(trace, binding, receipt),
            )
        self.assertEqual(observed, expected)
        revalidate_binding.assert_called_once()
        self.assertEqual(
            compiler.call_args.kwargs["admitted_model_input_control_closures"],
            {},
        )

    def test_correlated_binding_relabel_source_mismatch_blocks_compiler(self):
        trace = _training_trace(vector_control_condition="BASELINE")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.trace_dict",
            return_value=trace,
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_binding_against_sources",
            side_effect=JSpaceInferenceBindingError(
                "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH"
            ),
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records"
        ) as compiler:
            with self.assertRaisesRegex(
                SourceRevalidatedTrainingDatasetError,
                "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_FAILED",
            ):
                compile_source_revalidated_records(
                    [(trace, {})],
                    **self._kwargs(trace, binding, receipt),
                )
        compiler.assert_not_called()

    def test_serialized_training_trace_must_equal_rehydration_source(self):
        trace = _training_trace(vector_control_condition="BASELINE")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        wrong = dict(trace)
        wrong["trace_family_id"] = "episode:wrong-source"
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.trace_dict",
            return_value=wrong,
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_binding_against_sources"
        ) as revalidate_binding, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records"
        ) as compiler:
            with self.assertRaisesRegex(
                SourceRevalidatedTrainingDatasetError,
                "TRAINING_TRACE_SOURCE_BYTES_MISMATCH",
            ):
                compile_source_revalidated_records(
                    [(trace, {})],
                    **self._kwargs(trace, binding, receipt),
                )
        revalidate_binding.assert_not_called()
        compiler.assert_not_called()

    def test_only_freshly_source_revalidated_closure_reaches_retained_compiler(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        raw_closure = object()
        control_binding = object()
        consumed = b"exact-consumed-input"
        canonical_closure = object()
        control_source = ModelInputControlClosureSourceBundle(
            closure=raw_closure,
            control_binding=control_binding,
            consumed_input_bytes=consumed,
        )
        expected = {"train": [], "validation": [], "holdout": []}
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.trace_dict",
            return_value=trace,
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_binding_against_sources"
        ) as revalidate_binding, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_closure_against_canonical_sources",
            return_value=canonical_closure,
        ) as revalidate_closure, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records",
            return_value=expected,
        ) as compiler:
            kwargs = self._kwargs(trace, binding, receipt)
            inference_source = kwargs["inference_binding_source_bundles"][binding.binding_sha256]
            kwargs["model_input_control_source_bundles"] = {
                binding.binding_sha256: control_source,
            }
            observed = compile_source_revalidated_records([(trace, {})], **kwargs)

        self.assertEqual(observed, expected)
        revalidate_binding.assert_called_once_with(
            binding,
            inference_source.training_trace,
            receipt,
            inference_source.grid_plan,
        )
        revalidate_closure.assert_called_once()
        self.assertIs(revalidate_closure.call_args.args[1], raw_closure)
        self.assertIs(revalidate_closure.call_args.args[2], control_binding)
        self.assertEqual(revalidate_closure.call_args.args[3], consumed)
        self.assertIs(revalidate_closure.call_args.args[4], inference_source.grid_plan)
        self.assertIs(revalidate_closure.call_args.args[5], receipt)
        self.assertIs(revalidate_closure.call_args.args[6], binding)
        self.assertEqual(revalidate_closure.call_args.kwargs["current_generation"], 73)
        self.assertEqual(
            compiler.call_args.kwargs["admitted_model_input_control_closures"],
            {binding.binding_sha256: canonical_closure},
        )

    def test_closure_source_revalidation_failure_blocks_retained_compiler(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        control_source = ModelInputControlClosureSourceBundle(
            closure=object(),
            control_binding=object(),
            consumed_input_bytes=b"exact-consumed-input",
        )
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.trace_dict",
            return_value=trace,
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_binding_against_sources"
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_closure_against_canonical_sources",
            side_effect=JSpaceModelInputControlClosureRevalidationError("SOURCE_MISMATCH"),
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records"
        ) as compiler:
            kwargs = self._kwargs(trace, binding, receipt)
            kwargs["model_input_control_source_bundles"] = {
                binding.binding_sha256: control_source,
            }
            with self.assertRaisesRegex(
                SourceRevalidatedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_CLOSURE_SOURCE_REVALIDATION_FAILED",
            ):
                compile_source_revalidated_records([(trace, {})], **kwargs)
        compiler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
