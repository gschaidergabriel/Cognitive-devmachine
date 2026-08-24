import hashlib
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from entry_canonicalization_v1 import canonicalize
from inference_receipt_v1 import make_inference_receipt
from jspace_inference_binding_revalidation_v1 import revalidate_binding_against_sources
from jspace_inference_binding_v1 import (
    JSpaceInferenceBinding,
    JSpaceInferenceBindingError,
    bind_training_trace_to_inference,
    validate_binding,
)
from model_execution_admission_store_v1 import admit_and_verify_model_execution
from test_execution_store_inference_jspace_chain_v1 import (
    open_db,
    producer_fixture,
    training_trace_for,
)


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def rehash(binding: JSpaceInferenceBinding) -> JSpaceInferenceBinding:
    material = asdict(binding)
    material.pop("binding_sha256", None)
    return replace(
        binding,
        binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
    )


class ExecutionStoreJSpaceSourceRevalidationTests(unittest.TestCase):
    """Exercise source-aware J-Space revalidation on the integrated causal spine.

    The existing integrated regression proves producer construction of
    Typed Entry -> route -> VerifiedEngineAdmission -> loader consumption -> GRID10 ->
    canonical MiniUnifiedDB ModelExecution -> InferenceReceipt/v4 -> J-Space binding/v3.
    This regression closes the persisted/rehydrated boundary by proving that a binding
    which is internally self-consistent and freshly rehashed still cannot relabel the
    scheduler, executor or engine provenance when the exact producer sources are present.

    Deterministic source/test evidence only; no model, runtime, training or truth credit.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.db_path = self.root / "miniunified.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def integrated_binding_fixture(self):
        packet, decision, kwargs, observation = producer_fixture(self.root)
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]

        db = open_db(self.db_path, plan.entity_generation)
        try:
            execution = admit_and_verify_model_execution(
                db,
                plan,
                load,
                observation,
                current_generation=plan.entity_generation,
            )
        finally:
            db.close()

        kwargs["verified_model_execution"] = execution
        kwargs["admitted_verified_model_executions"] = {
            execution.receipt_sha256: asdict(execution)
        }
        inference = make_inference_receipt(decision, **kwargs)
        trace = training_trace_for(packet, decision, kwargs, execution)
        binding = bind_training_trace_to_inference(trace, inference, plan)
        validate_binding(binding)
        return plan, trace, inference, binding

    def test_integrated_binding_rederives_from_exact_sources(self):
        plan, trace, inference, binding = self.integrated_binding_fixture()
        revalidate_binding_against_sources(binding, trace, inference, plan)

    def test_digest_valid_grid_plan_transplant_fails_source_revalidation(self):
        plan, trace, inference, binding = self.integrated_binding_fixture()
        forged = rehash(replace(binding, grid_plan_sha256=digest("forged-grid-plan")))

        # Flat validation cannot know which scheduler source minted the summary field.
        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, inference, plan)

    def test_digest_valid_pairwise_cell_relabel_fails_source_revalidation(self):
        plan, trace, inference, binding = self.integrated_binding_fixture()
        forged = rehash(
            replace(
                binding,
                cell_id="cell-09",
                output_producing_cell_id="cell-09",
            )
        )

        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, inference, plan)

    def test_digest_valid_pairwise_invocation_relabel_fails_source_revalidation(self):
        plan, trace, inference, binding = self.integrated_binding_fixture()
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
            revalidate_binding_against_sources(forged, trace, inference, plan)

    def test_digest_valid_engine_summary_relabel_fails_source_revalidation(self):
        plan, trace, inference, binding = self.integrated_binding_fixture()
        forged = rehash(
            replace(binding, resolved_engine_identity="local-hcu-08b-forged")
        )

        validate_binding(forged)
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_binding_against_sources(forged, trace, inference, plan)


if __name__ == "__main__":
    unittest.main()
