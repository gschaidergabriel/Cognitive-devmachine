import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA
from jspace_inference_binding_v1 import (
    JSpaceInferenceBinding,
    JSpaceInferenceBindingError,
    SCHEMA,
    validate_binding,
)
from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def rehash(binding: JSpaceInferenceBinding) -> JSpaceInferenceBinding:
    material = asdict(binding)
    material.pop("binding_sha256", None)
    return replace(binding, binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest())


def valid_binding() -> JSpaceInferenceBinding:
    binding = JSpaceInferenceBinding(
        schema=SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        training_trace_schema=TRAINING_TRACE_SCHEMA,
        training_trace_sha256=digest("training"),
        prototype_trace_sha256=digest("prototype"),
        generation=7,
        entry_event_sha256=digest("event"),
        entry_admission_sha256=digest("admission"),
        route_decision_sha256=digest("route"),
        grid_plan_sha256=digest("grid"),
        cell_id="cell-02",
        role="critic",
        vector_control_packet_sha256=digest("vector"),
        inference_receipt_schema=INFERENCE_RECEIPT_SCHEMA,
        inference_receipt_sha256=digest("inference"),
        engine_identity_sha256=digest("engine-id"),
        resolved_engine_identity="local-hcu-08b",
        resolved_engine_class="LOCAL_COGNITION",
        resolved_engine_artifact_sha256=digest("engine-artifact"),
        engine_admission_receipt_sha256=digest("engine-admission"),
        engine_load_loader_binding_sha256=digest("loader-binding"),
        engine_load_lease_sha256=digest("load-lease"),
        engine_load_consumption_receipt_sha256=digest("load-consumption"),
        engine_load_loader_id="loader:1",
        model_execution_receipt_sha256=digest("model-execution-receipt"),
        model_execution_observation_sha256=digest("model-execution-observation"),
        model_execution_executor_id="entityos:hcu:model-executor:1",
        model_execution_invocation_id="executor-invocation:1",
        output_producing_cell_id="cell-02",
        model_execution_role="critic",
        input_sha256=digest("input"),
        input_size=17,
        model_call_id="executor-invocation:1",
        output_ref="unifieddb:model-output:1",
        output_sha256=digest("output"),
        output_size=23,
        binding_sha256="1" * 64,
    )
    return rehash(binding)


class JSpaceInferenceBindingRevalidationTests(unittest.TestCase):
    def test_exact_rehydrated_binding_passes(self):
        validate_binding(valid_binding())

    def test_digest_valid_cell_transplant_fails_closed(self):
        forged = rehash(replace(valid_binding(), output_producing_cell_id="cell-03"))
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "MODEL_EXECUTION_CELL_DOES_NOT_BIND_TRACE_CELL",
        ):
            validate_binding(forged)

    def test_digest_valid_role_transplant_fails_closed(self):
        forged = rehash(replace(valid_binding(), model_execution_role="world"))
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "MODEL_EXECUTION_ROLE_DOES_NOT_BIND_TRACE_ROLE",
        ):
            validate_binding(forged)

    def test_digest_valid_invocation_transplant_fails_closed(self):
        forged = rehash(replace(valid_binding(), model_call_id="caller-relabel"))
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "MODEL_CALL_ID_NOT_EXECUTOR_MINTED_INVOCATION",
        ):
            validate_binding(forged)

    def test_digest_valid_stale_inference_schema_fails_closed(self):
        forged = rehash(replace(valid_binding(), inference_receipt_schema="HCU_INFERENCE_RECEIPT/v3"))
        with self.assertRaisesRegex(
            JSpaceInferenceBindingError,
            "JSPACE_INFERENCE_BINDING_INFERENCE_SCHEMA_UNSUPPORTED",
        ):
            validate_binding(forged)


if __name__ == "__main__":
    unittest.main()
