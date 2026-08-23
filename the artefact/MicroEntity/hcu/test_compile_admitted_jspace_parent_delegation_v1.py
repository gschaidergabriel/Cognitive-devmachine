import unittest
from unittest.mock import patch

from compile_admitted_jspace_training_dataset_v1 import (
    AdmittedTrainingDatasetError,
    _require_admitted_inference_receipt,
)
from jspace_inference_parent_admission_v1 import JSpaceInferenceParentAdmissionError
from test_jspace_inference_parent_admission_v1 import binding_for, receipt_with_sha


class SeriousCompilerInferenceParentDelegationTests(unittest.TestCase):
    @patch("compile_admitted_jspace_training_dataset_v1.require_admitted_inference_receipt_parent")
    def test_compiler_compatibility_adapter_delegates_to_reusable_parent_guard(self, parent_guard):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        registry = {receipt["receipt_sha256"]: receipt}
        parent_guard.return_value = receipt

        observed = _require_admitted_inference_receipt(binding, registry)

        self.assertEqual(observed, receipt)
        parent_guard.assert_called_once_with(binding, registry)

    @patch("compile_admitted_jspace_training_dataset_v1.require_admitted_inference_receipt_parent")
    def test_missing_parent_preserves_compiler_compatibility_error(self, parent_guard):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        parent_guard.side_effect = JSpaceInferenceParentAdmissionError(
            "INFERENCE_RECEIPT_PARENT_NOT_ADMITTED"
        )

        with self.assertRaisesRegex(
            AdmittedTrainingDatasetError,
            "INFERENCE_RECEIPT_NOT_ADMITTED_FOR_BINDING",
        ):
            _require_admitted_inference_receipt(binding, {})

    @patch("compile_admitted_jspace_training_dataset_v1.require_admitted_inference_receipt_parent")
    def test_parent_binding_failure_preserves_compiler_compatibility_prefix(self, parent_guard):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        parent_guard.side_effect = JSpaceInferenceParentAdmissionError(
            "INFERENCE_RECEIPT_PARENT_BINDING_MISMATCH:output_ref"
        )

        with self.assertRaisesRegex(
            AdmittedTrainingDatasetError,
            "INFERENCE_RECEIPT_BINDING_MISMATCH:output_ref",
        ):
            _require_admitted_inference_receipt(binding, {receipt["receipt_sha256"]: receipt})

    @patch("compile_admitted_jspace_training_dataset_v1.require_admitted_inference_receipt_parent")
    def test_new_parent_guard_rejection_fails_closed_without_silent_downgrade(self, parent_guard):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        parent_guard.side_effect = JSpaceInferenceParentAdmissionError(
            "INFERENCE_RECEIPT_ENTRY_BINDING_SCHEMA_MISMATCH"
        )

        with self.assertRaisesRegex(
            AdmittedTrainingDatasetError,
            "INFERENCE_PARENT_ADMISSION_REJECTED:INFERENCE_RECEIPT_ENTRY_BINDING_SCHEMA_MISMATCH",
        ):
            _require_admitted_inference_receipt(binding, {receipt["receipt_sha256"]: receipt})


if __name__ == "__main__":
    unittest.main()
