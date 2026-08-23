import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import SCHEMA as INFERENCE_RECEIPT_SCHEMA, STATUS as INFERENCE_RECEIPT_STATUS
from jspace_inference_binding_v1 import SCHEMA as BINDING_SCHEMA, JSpaceInferenceBinding, validate_binding
from jspace_inference_parent_admission_v1 import (
    JSpaceInferenceParentAdmissionError,
    require_admitted_inference_receipt_parent,
)
from jspace_training_trace_v1 import TRACE_SCHEMA
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA


def h(ch):
    return ch * 64


def receipt_with_sha(**overrides):
    receipt = {
        "schema": INFERENCE_RECEIPT_SCHEMA,
        "status": INFERENCE_RECEIPT_STATUS,
        "hash_serialization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "entity_generation": 7,
        "entry_admission_sha256": h("2"),
        "event_sha256": h("1"),
        "decision_sha256": h("3"),
        "router_policy_sha256": h("4"),
        "engine_identity_sha256": h("5"),
        "resolved_engine_identity": "local:model",
        "resolved_engine_class": "LOCAL_MODEL",
        "resolved_engine_artifact_sha256": h("6"),
        "engine_admission_receipt_sha256": h("7"),
        "engine_load_canonicalization_schema": CANONICALIZATION_SCHEMA,
        "engine_load_loader_binding_sha256": h("8"),
        "engine_load_lease_sha256": h("9"),
        "engine_load_consumption_receipt_sha256": h("a"),
        "engine_load_loader_id": "loader:1",
        "model_execution_canonicalization_schema": CANONICALIZATION_SCHEMA,
        "model_execution_receipt_sha256": h("b"),
        "model_execution_observation_sha256": h("c"),
        "model_execution_executor_id": "executor:1",
        "model_execution_invocation_id": "call:1",
        "grid_plan_sha256": h("d"),
        "output_producing_cell_id": "cell-02",
        "model_execution_role": "world",
        "input_sha256": h("e"),
        "input_size": 11,
        "model_call_id": "call:1",
        "output_ref": "sha256:output",
        "output_sha256": h("1"),
        "output_size": 13,
        "model_lanes": ("world",),
    }
    receipt.update(overrides)
    receipt["receipt_sha256"] = hashlib.sha256(canonicalize(receipt)).hexdigest()
    return receipt


def binding_for(receipt):
    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "training_trace_schema": TRACE_SCHEMA,
        "training_trace_sha256": h("2"),
        "prototype_trace_sha256": h("3"),
        "generation": receipt["entity_generation"],
        "entry_event_sha256": receipt["event_sha256"],
        "entry_admission_sha256": receipt["entry_admission_sha256"],
        "route_decision_sha256": receipt["decision_sha256"],
        "grid_plan_sha256": receipt["grid_plan_sha256"],
        "cell_id": receipt["output_producing_cell_id"],
        "role": receipt["model_execution_role"],
        "vector_control_packet_sha256": h("4"),
        "inference_receipt_schema": INFERENCE_RECEIPT_SCHEMA,
        "inference_receipt_sha256": receipt["receipt_sha256"],
        "engine_identity_sha256": receipt["engine_identity_sha256"],
        "resolved_engine_identity": receipt["resolved_engine_identity"],
        "resolved_engine_class": receipt["resolved_engine_class"],
        "resolved_engine_artifact_sha256": receipt["resolved_engine_artifact_sha256"],
        "engine_admission_receipt_sha256": receipt["engine_admission_receipt_sha256"],
        "engine_load_loader_binding_sha256": receipt["engine_load_loader_binding_sha256"],
        "engine_load_lease_sha256": receipt["engine_load_lease_sha256"],
        "engine_load_consumption_receipt_sha256": receipt["engine_load_consumption_receipt_sha256"],
        "engine_load_loader_id": receipt["engine_load_loader_id"],
        "model_execution_receipt_sha256": receipt["model_execution_receipt_sha256"],
        "model_execution_observation_sha256": receipt["model_execution_observation_sha256"],
        "model_execution_executor_id": receipt["model_execution_executor_id"],
        "model_execution_invocation_id": receipt["model_execution_invocation_id"],
        "output_producing_cell_id": receipt["output_producing_cell_id"],
        "model_execution_role": receipt["model_execution_role"],
        "input_sha256": receipt["input_sha256"],
        "input_size": receipt["input_size"],
        "model_call_id": receipt["model_call_id"],
        "output_ref": receipt["output_ref"],
        "output_sha256": receipt["output_sha256"],
        "output_size": receipt["output_size"],
    }
    sha = hashlib.sha256(canonicalize(material)).hexdigest()
    return JSpaceInferenceBinding(**material, binding_sha256=sha)


class ParentAdmissionTests(unittest.TestCase):
    def test_exact_admitted_parent_passes(self):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        observed = require_admitted_inference_receipt_parent(
            binding,
            {receipt["receipt_sha256"]: receipt},
        )
        self.assertEqual(dict(observed), receipt)

    def test_self_consistent_binding_without_parent_is_rejected(self):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        validate_binding(binding)  # child envelope alone is internally valid
        with self.assertRaisesRegex(JSpaceInferenceParentAdmissionError, "INFERENCE_RECEIPT_PARENT_NOT_ADMITTED"):
            require_admitted_inference_receipt_parent(binding, {})

    def test_byte_distinct_parent_under_claimed_key_is_rejected(self):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        altered = dict(receipt)
        altered["output_ref"] = "sha256:other-output"
        with self.assertRaisesRegex(JSpaceInferenceParentAdmissionError, "INFERENCE_RECEIPT_DIGEST_MISMATCH"):
            require_admitted_inference_receipt_parent(
                binding,
                {receipt["receipt_sha256"]: altered},
            )

    def test_parent_field_transplant_is_rejected_even_with_valid_parent_digest(self):
        receipt = receipt_with_sha()
        binding = binding_for(receipt)
        other = receipt_with_sha(output_ref="sha256:other-output")
        forged = replace(binding, inference_receipt_sha256=other["receipt_sha256"], output_ref=receipt["output_ref"])
        material = asdict(forged)
        material.pop("binding_sha256")
        forged = replace(forged, binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest())
        validate_binding(forged)
        with self.assertRaisesRegex(JSpaceInferenceParentAdmissionError, "INFERENCE_RECEIPT_PARENT_BINDING_MISMATCH:output_ref"):
            require_admitted_inference_receipt_parent(
                forged,
                {other["receipt_sha256"]: other},
            )


if __name__ == "__main__":
    unittest.main()
