import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import canonicalize
from jspace_inference_binding_revalidation_v1 import (
    revalidate_binding_against_sources,
)
from jspace_inference_binding_v1 import (
    JSpaceInferenceBinding,
    JSpaceInferenceBindingError,
    bind_training_trace_to_inference,
    validate_binding,
)
from test_jspace_inference_binding_v1 import JSpaceInferenceBindingTests


def rehash(binding: JSpaceInferenceBinding) -> JSpaceInferenceBinding:
    material = asdict(binding)
    material.pop("binding_sha256", None)
    return replace(
        binding,
        binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
    )


class JSpaceInferenceBindingSourceRevalidationTests(unittest.TestCase):
    def fixture(self):
        helpers = JSpaceInferenceBindingTests(methodName="runTest")
        plan = helpers.grid_plan(("critic", "world"))
        trace = helpers.training_trace(plan)
        receipt = helpers.inference_receipt(
            trace,
            model_lanes=("critic", "world"),
        )
        binding = bind_training_trace_to_inference(trace, receipt, plan)
        return plan, trace, receipt, binding

    def test_exact_sources_rederive_persisted_binding(self):
        plan, trace, receipt, binding = self.fixture()
        revalidate_binding_against_sources(binding, trace, receipt, plan)

    def test_pairwise_cell_relabel_is_rejected_against_sources(self):
        plan, trace, receipt, binding = self.fixture()
        forged = rehash(
            replace(
                binding,
                cell_id="cell-03",
                output_producing_cell_id="cell-03",
            )
        )
        # Flat validation alone cannot prove which source minted the paired labels.
        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, receipt, plan)

    def test_pairwise_role_relabel_is_rejected_against_sources(self):
        plan, trace, receipt, binding = self.fixture()
        forged = rehash(
            replace(
                binding,
                role="world",
                model_execution_role="world",
            )
        )
        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, receipt, plan)

    def test_pairwise_invocation_relabel_is_rejected_against_sources(self):
        plan, trace, receipt, binding = self.fixture()
        forged = rehash(
            replace(
                binding,
                model_execution_invocation_id="executor-invocation:forged",
                model_call_id="executor-invocation:forged",
            )
        )
        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, receipt, plan)

    def test_flat_engine_summary_relabel_is_rejected_against_sources(self):
        plan, trace, receipt, binding = self.fixture()
        forged = rehash(
            replace(
                binding,
                resolved_engine_identity="local-hcu-08b-forged",
            )
        )
        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, receipt, plan)


if __name__ == "__main__":
    unittest.main()
