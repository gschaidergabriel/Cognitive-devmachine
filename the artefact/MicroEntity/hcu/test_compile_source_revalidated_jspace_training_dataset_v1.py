import unittest
from unittest.mock import patch

from compile_source_revalidated_jspace_training_dataset_v1 import (
    ModelInputControlClosureSourceBundle,
    SourceRevalidatedTrainingDatasetError,
    compile_source_revalidated_records,
)
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
    def _kwargs(self, binding, *, bundles=None):
        return {
            "canonical_db": object(),
            "current_generation": 73,
            "model_input_control_source_bundles": bundles or {},
            "admitted_training_traces": {},
            "admitted_transition_traces": {},
            "admitted_prototype_traces": {},
            "admitted_grid_plans": {},
            "admitted_vector_control_packets": {},
            "admitted_inference_bindings": {TRACE_SHA: binding},
            "admitted_inference_receipts": {},
            "admitted_bases": {},
        }

    def test_nonbaseline_cannot_compile_without_canonical_source_bundle(self):
        trace = _training_trace(vector_control_condition="LESION")
        binding = _binding(trace, inference_receipt=_inference_receipt())
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records"
        ) as compiler:
            with self.assertRaisesRegex(
                SourceRevalidatedTrainingDatasetError,
                "CANONICAL_SOURCE_BUNDLE_REQUIRED_FOR_NON_BASELINE_TRAINING",
            ):
                compile_source_revalidated_records(
                    [(trace, {})],
                    **self._kwargs(binding),
                )
        compiler.assert_not_called()

    def test_baseline_can_delegate_without_intervention_source_bundle(self):
        trace = _training_trace(vector_control_condition="BASELINE")
        binding = _binding(trace, inference_receipt=_inference_receipt())
        expected = {"train": [], "validation": [], "holdout": []}
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records",
            return_value=expected,
        ) as compiler:
            observed = compile_source_revalidated_records(
                [(trace, {})],
                **self._kwargs(binding),
            )
        self.assertEqual(observed, expected)
        self.assertEqual(
            compiler.call_args.kwargs["admitted_model_input_control_closures"],
            {},
        )

    def test_only_freshly_source_revalidated_closure_reaches_retained_compiler(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        raw_closure = object()
        control_binding = object()
        consumed = b"exact-consumed-input"
        grid_plan = object()
        canonical_closure = object()
        bundle = ModelInputControlClosureSourceBundle(
            closure=raw_closure,
            control_binding=control_binding,
            consumed_input_bytes=consumed,
            grid_plan=grid_plan,
            inference_receipt=receipt,
        )
        expected = {"train": [], "validation": [], "holdout": []}
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1._require_existing_control_admission"
        ) as predecessor, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_closure_against_canonical_sources",
            return_value=canonical_closure,
        ) as revalidate, patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records",
            return_value=expected,
        ) as compiler:
            observed = compile_source_revalidated_records(
                [(trace, {})],
                **self._kwargs(binding, bundles={binding.binding_sha256: bundle}),
            )

        self.assertEqual(observed, expected)
        predecessor.assert_called_once_with(unittest.mock.ANY, control_binding)
        revalidate.assert_called_once()
        self.assertIs(revalidate.call_args.args[1], raw_closure)
        self.assertIs(revalidate.call_args.args[2], control_binding)
        self.assertEqual(revalidate.call_args.args[3], consumed)
        self.assertIs(revalidate.call_args.args[4], grid_plan)
        self.assertIs(revalidate.call_args.args[5], receipt)
        self.assertIs(revalidate.call_args.args[6], binding)
        self.assertEqual(revalidate.call_args.kwargs["current_generation"], 73)
        self.assertEqual(
            compiler.call_args.kwargs["admitted_model_input_control_closures"],
            {binding.binding_sha256: canonical_closure},
        )

    def test_source_revalidation_failure_blocks_retained_compiler(self):
        trace = _training_trace(vector_control_condition="LESION")
        receipt = _inference_receipt()
        binding = _binding(trace, inference_receipt=receipt)
        bundle = ModelInputControlClosureSourceBundle(
            closure=object(),
            control_binding=object(),
            consumed_input_bytes=b"exact-consumed-input",
            grid_plan=object(),
            inference_receipt=receipt,
        )
        with patch(
            "compile_source_revalidated_jspace_training_dataset_v1._require_existing_control_admission"
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.revalidate_closure_against_canonical_sources",
            side_effect=JSpaceModelInputControlClosureRevalidationError("SOURCE_MISMATCH"),
        ), patch(
            "compile_source_revalidated_jspace_training_dataset_v1.compile_admitted_records"
        ) as compiler:
            with self.assertRaisesRegex(
                SourceRevalidatedTrainingDatasetError,
                "MODEL_INPUT_CONTROL_CLOSURE_SOURCE_REVALIDATION_FAILED",
            ):
                compile_source_revalidated_records(
                    [(trace, {})],
                    **self._kwargs(binding, bundles={binding.binding_sha256: bundle}),
                )
        compiler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
