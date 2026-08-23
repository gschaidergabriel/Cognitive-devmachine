import unittest

from jspace_inference_binding_v1 import (
    JSpaceInferenceBindingError,
    bind_training_trace_to_inference,
    validate_binding,
)
from test_jspace_inference_binding_v1 import JSpaceInferenceBindingTests


class JSpaceInferenceModelCallIdentityTests(unittest.TestCase):
    def fixture(self):
        helpers = JSpaceInferenceBindingTests(methodName="runTest")
        plan = helpers.grid_plan()
        trace = helpers.training_trace(plan)
        return helpers, plan, trace

    def test_exact_grid_plan_cell_role_model_call_identity_binds(self):
        helpers, plan, trace = self.fixture()
        expected = f"grid10:{plan.plan_sha256}:{trace.cell_id}:{trace.role}"
        receipt = helpers.inference_receipt(trace, model_call_id=expected)
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.model_call_id, expected)
        self.assertEqual(binding.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(binding.cell_id, trace.cell_id)
        self.assertEqual(binding.role, trace.role)

    def test_relabel_to_other_grid_cell_fails_closed(self):
        helpers, plan, trace = self.fixture()
        relabeled = f"grid10:{plan.plan_sha256}:cell-09:{trace.role}"
        receipt = helpers.inference_receipt(trace, model_call_id=relabeled)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "INFERENCE_MODEL_CALL_ID_DOES_NOT_BIND_GRID10_CELL_ROLE",
        ):
            bind_training_trace_to_inference(trace, receipt, plan)

    def test_relabel_to_other_plan_fails_closed(self):
        helpers, plan, trace = self.fixture()
        relabeled = f"grid10:{'f' * 64}:{trace.cell_id}:{trace.role}"
        receipt = helpers.inference_receipt(trace, model_call_id=relabeled)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "INFERENCE_MODEL_CALL_ID_DOES_NOT_BIND_GRID10_CELL_ROLE",
        ):
            bind_training_trace_to_inference(trace, receipt, plan)

    def test_opaque_legacy_call_label_fails_closed(self):
        helpers, plan, trace = self.fixture()
        receipt = helpers.inference_receipt(trace, model_call_id="call:1")
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "INFERENCE_MODEL_CALL_ID_DOES_NOT_BIND_GRID10_CELL_ROLE",
        ):
            bind_training_trace_to_inference(trace, receipt, plan)


if __name__ == "__main__":
    unittest.main()
