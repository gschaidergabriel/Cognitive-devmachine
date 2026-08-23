import unittest

from jspace_inference_binding_v1 import (
    JSpaceInferenceBindingError,
    bind_training_trace_to_inference,
    validate_binding,
)
from test_jspace_inference_binding_v1 import JSpaceInferenceBindingTests


class JSpaceInferenceModelCallIdentityTests(unittest.TestCase):
    """Protect v4: model_call_id is the executor-minted invocation identity, not caller metadata."""

    def fixture(self):
        helpers = JSpaceInferenceBindingTests(methodName="runTest")
        plan = helpers.grid_plan()
        trace = helpers.training_trace(plan)
        return helpers, plan, trace

    def test_executor_minted_opaque_invocation_is_retained(self):
        helpers, plan, trace = self.fixture()
        receipt = helpers.inference_receipt(
            trace,
            model_execution_invocation_id="exec:opaque:1",
            model_call_id="exec:opaque:1",
        )
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.model_call_id, "exec:opaque:1")
        self.assertEqual(binding.model_execution_invocation_id, "exec:opaque:1")

    def test_caller_relabel_cannot_override_executor_invocation(self):
        helpers, plan, trace = self.fixture()
        receipt = helpers.inference_receipt(trace, model_call_id="caller:laundered:label")
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "MODEL_CALL_ID_NOT_EXECUTOR_MINTED_INVOCATION"):
            bind_training_trace_to_inference(trace, receipt, plan)

    def test_cross_cell_shaped_executor_invocation_cannot_move_bound_cell(self):
        helpers, plan, trace = self.fixture()
        opaque = f"grid10:{plan.plan_sha256}:cell-09:{trace.role}"
        receipt = helpers.inference_receipt(
            trace,
            model_execution_invocation_id=opaque,
            model_call_id=opaque,
        )
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        validate_binding(binding)
        self.assertEqual(binding.model_call_id, opaque)
        self.assertEqual(binding.cell_id, trace.cell_id)
        self.assertNotEqual(binding.cell_id, "cell-09")

    def test_empty_executor_invocation_fails_basic_receipt_metadata_validation(self):
        helpers, plan, trace = self.fixture()
        receipt = helpers.inference_receipt(
            trace,
            model_execution_invocation_id="",
            model_call_id="",
        )
        with self.assertRaisesRegex(JSpaceInferenceBindingError, "NONEMPTY_STRING_REQUIRED"):
            bind_training_trace_to_inference(trace, receipt, plan)


if __name__ == "__main__":
    unittest.main()
