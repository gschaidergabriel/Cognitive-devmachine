import unittest

from jspace_inference_binding_v1 import (
    JSpaceInferenceBindingError,
    bind_training_trace_to_inference,
    validate_binding,
)
from test_jspace_inference_binding_v1 import JSpaceInferenceBindingTests


class JSpaceInferenceModelCallIdentityTests(unittest.TestCase):
    """Protect the v3 boundary: model_call_id is correlation metadata, never cell authority."""

    def fixture(self):
        helpers = JSpaceInferenceBindingTests(methodName="runTest")
        plan = helpers.grid_plan()
        trace = helpers.training_trace(plan)
        return helpers, plan, trace

    def bind_with_call_id(self, model_call_id):
        helpers, plan, trace = self.fixture()
        receipt = helpers.inference_receipt(trace, model_call_id=model_call_id)
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        return plan, trace, binding

    def test_opaque_call_id_is_retained_as_non_authoritative_correlation(self):
        plan, trace, binding = self.bind_with_call_id("call:opaque:1")
        self.assertEqual(binding.model_call_id, "call:opaque:1")
        self.assertEqual(binding.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(binding.cell_id, trace.cell_id)
        self.assertEqual(binding.role, trace.role)

    def test_cross_cell_shaped_call_id_cannot_move_bound_cell(self):
        helpers, plan, trace = self.fixture()
        relabeled = f"grid10:{plan.plan_sha256}:cell-09:{trace.role}"
        receipt = helpers.inference_receipt(trace, model_call_id=relabeled)
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.model_call_id, relabeled)
        self.assertEqual(binding.cell_id, trace.cell_id)
        self.assertNotEqual(binding.cell_id, "cell-09")

    def test_other_plan_shaped_call_id_cannot_override_bound_plan(self):
        helpers, plan, trace = self.fixture()
        relabeled = f"grid10:{'f' * 64}:{trace.cell_id}:{trace.role}"
        receipt = helpers.inference_receipt(trace, model_call_id=relabeled)
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.model_call_id, relabeled)
        self.assertEqual(binding.grid_plan_sha256, plan.plan_sha256)
        self.assertNotEqual(binding.grid_plan_sha256, "f" * 64)

    def test_empty_call_id_still_fails_basic_receipt_metadata_validation(self):
        helpers, plan, trace = self.fixture()
        receipt = helpers.inference_receipt(trace, model_call_id="")
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "NONEMPTY_STRING_REQUIRED"):
            bind_training_trace_to_inference(trace, receipt, plan)


if __name__ == "__main__":
    unittest.main()
