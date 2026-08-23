import unittest
from dataclasses import replace
from unittest.mock import patch

from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA, DatasetAdmission
from jspace_inference_parent_admission_v1 import JSpaceInferenceParentAdmissionError
from jspace_training_parent_closure_v1 import (
    CLOSURE_SCHEMA,
    JSpaceTrainingParentClosureError,
    require_admitted_training_parent_closure,
)
from jspace_vector_control_parent_admission_v1 import JSpaceVectorControlParentAdmissionError
from test_jspace_inference_parent_admission_v1 import binding_for, h, receipt_with_sha


def admission_for(binding):
    return DatasetAdmission(
        schema=ADMISSION_SCHEMA,
        training_trace_sha256=binding.training_trace_sha256,
        transition_trace_sha256=h("6"),
        prototype_trace_sha256=binding.prototype_trace_sha256,
        generation=binding.generation,
        entry_event_sha256=binding.entry_event_sha256,
        entry_admission_sha256=binding.entry_admission_sha256,
        route_decision_sha256=binding.route_decision_sha256,
        grid_plan_sha256=binding.grid_plan_sha256,
        cell_id=binding.cell_id,
        role=binding.role,
        jspace_basis_id="basis:7",
        jspace_basis_sha256=h("5"),
        vector_control_packet_sha256=binding.vector_control_packet_sha256,
        vector_control_condition="BASELINE",
        credit_label="UNKNOWN",
        outcome_receipt_sha256=None,
    )


class TrainingParentClosureTests(unittest.TestCase):
    def fixtures(self):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        admission = admission_for(binding)
        return receipt, binding, admission

    @patch("jspace_training_parent_closure_v1.require_admitted_vector_control_packet_parent")
    @patch("jspace_training_parent_closure_v1.require_admitted_inference_receipt_parent")
    def test_exact_children_delegate_both_parent_guards_and_close_one_row(self, inference_guard, vector_guard):
        receipt, binding, admission = self.fixtures()
        inference_guard.return_value = receipt
        vector_guard.return_value = object()

        closure = require_admitted_training_parent_closure(
            admission,
            binding,
            admitted_inference_receipts={receipt["receipt_sha256"]: receipt},
            admitted_vector_control_packets={admission.vector_control_packet_sha256: object()},
        )

        self.assertEqual(closure.schema, CLOSURE_SCHEMA)
        self.assertEqual(closure.training_trace_sha256, binding.training_trace_sha256)
        self.assertEqual(closure.inference_receipt_sha256, binding.inference_receipt_sha256)
        self.assertEqual(closure.vector_control_packet_sha256, binding.vector_control_packet_sha256)
        self.assertEqual(closure.grid_plan_sha256, binding.grid_plan_sha256)
        self.assertEqual(closure.vector_control_condition, "BASELINE")
        inference_guard.assert_called_once()
        vector_guard.assert_called_once()

    @patch("jspace_training_parent_closure_v1.require_admitted_vector_control_packet_parent")
    @patch("jspace_training_parent_closure_v1.require_admitted_inference_receipt_parent")
    def test_individually_admitted_parents_cannot_cross_splice_grid_identity(self, inference_guard, vector_guard):
        receipt, binding, admission = self.fixtures()
        inference_guard.return_value = receipt
        vector_guard.return_value = object()
        admission = replace(admission, grid_plan_sha256=h("f"))

        with self.assertRaisesRegex(
            JSpaceTrainingParentClosureError,
            "PARENT_CLOSURE_BINDING_MISMATCH:grid_plan_sha256",
        ):
            require_admitted_training_parent_closure(
                admission,
                binding,
                admitted_inference_receipts={receipt["receipt_sha256"]: receipt},
                admitted_vector_control_packets={admission.vector_control_packet_sha256: object()},
            )

    @patch("jspace_training_parent_closure_v1.require_admitted_vector_control_packet_parent")
    @patch("jspace_training_parent_closure_v1.require_admitted_inference_receipt_parent")
    def test_individually_admitted_parents_cannot_cross_splice_vector_packet_identity(self, inference_guard, vector_guard):
        receipt, binding, admission = self.fixtures()
        inference_guard.return_value = receipt
        vector_guard.return_value = object()
        admission = replace(admission, vector_control_packet_sha256=h("f"))

        with self.assertRaisesRegex(
            JSpaceTrainingParentClosureError,
            "PARENT_CLOSURE_BINDING_MISMATCH:vector_control_packet_sha256",
        ):
            require_admitted_training_parent_closure(
                admission,
                binding,
                admitted_inference_receipts={receipt["receipt_sha256"]: receipt},
                admitted_vector_control_packets={admission.vector_control_packet_sha256: object()},
            )

    @patch("jspace_training_parent_closure_v1.require_admitted_vector_control_packet_parent")
    @patch("jspace_training_parent_closure_v1.require_admitted_inference_receipt_parent")
    def test_inference_parent_rejection_is_fail_closed(self, inference_guard, vector_guard):
        receipt, binding, admission = self.fixtures()
        inference_guard.side_effect = JSpaceInferenceParentAdmissionError("PARENT_MISSING")

        with self.assertRaisesRegex(
            JSpaceTrainingParentClosureError,
            "INFERENCE_PARENT_ADMISSION_REJECTED:PARENT_MISSING",
        ):
            require_admitted_training_parent_closure(
                admission,
                binding,
                admitted_inference_receipts={},
                admitted_vector_control_packets={},
            )
        vector_guard.assert_not_called()

    @patch("jspace_training_parent_closure_v1.require_admitted_vector_control_packet_parent")
    @patch("jspace_training_parent_closure_v1.require_admitted_inference_receipt_parent")
    def test_vector_parent_rejection_is_fail_closed(self, inference_guard, vector_guard):
        receipt, binding, admission = self.fixtures()
        inference_guard.return_value = receipt
        vector_guard.side_effect = JSpaceVectorControlParentAdmissionError("PACKET_MISSING")

        with self.assertRaisesRegex(
            JSpaceTrainingParentClosureError,
            "VECTOR_CONTROL_PARENT_ADMISSION_REJECTED:PACKET_MISSING",
        ):
            require_admitted_training_parent_closure(
                admission,
                binding,
                admitted_inference_receipts={receipt["receipt_sha256"]: receipt},
                admitted_vector_control_packets={},
            )


if __name__ == "__main__":
    unittest.main()
