import hashlib
import unittest
from dataclasses import replace
from unittest.mock import patch

import jspace_control_execution_binding_v1 as module
from jspace_control_execution_binding_v1 import (
    JSpaceControlExecutionBindingError,
    bind_control_packet_to_verified_execution,
    validate_control_execution_binding,
)
from jspace_training_trace_v1 import TrainingTrace
from model_input_control_binding_v1 import ModelInputControlBinding
from model_execution_receipt_v1 import VerifiedModelExecution


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def trace() -> TrainingTrace:
    return TrainingTrace(
        schema_version="ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1",
        canonicalization_schema="RFC8785_JCS_UTF8/v1",
        trace_id="trace:1",
        trace_family_id="family:1",
        generation=7,
        entry_event_sha256=digest("entry-event"),
        entry_admission_sha256=digest("entry-admission"),
        route_decision_sha256=digest("route"),
        grid_plan_sha256=digest("grid"),
        cell_id="cell-02",
        role="ANALYZE",
        jspace_basis_id="basis:1",
        jspace_basis_sha256=digest("basis"),
        jspace_input_vector_ref="jspace:input:1",
        jspace_input_codec_version="JSPACE_VECTOR_CONTROL_ABI/v1",
        vector_control_packet_sha256=digest("packet"),
        vector_control_packet_jcs_utf8='{"abi_schema":"JSPACE_VECTOR_CONTROL_ABI/v1"}',
        vector_control_condition="BASELINE",
        local_workspace_state_ref="workspace:1",
        gwt_competition_set=(("cell-02", "ANALYZE", 9000),),
        gwt_broadcast_gate=9000,
        global_jspace_slice_ref="jspace:slice:1",
        hyperposition_branch_ids=("branch:1",),
        provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
        resource_budget=(("tokens", 128),),
        requested_action_class="ANALYZE",
        expected_structured_model_output="json",
        observed_downstream_outcome="UNKNOWN",
        outcome_receipt_sha256=None,
        falsifier_lesion_condition="LESION",
        credit_label="UNKNOWN",
        prototype_trace_sha256=digest("prototype"),
        trace_sha256=digest("trace"),
    )


def input_binding() -> ModelInputControlBinding:
    return ModelInputControlBinding(
        schema="HCU_MODEL_INPUT_CONTROL_BINDING/v1",
        canonicalization_schema="RFC8785_JCS_UTF8/v1",
        transform_schema="HCU_MODEL_INPUT_DIRECT_UNIQUE_PACKET_EMBED/v1",
        generation=7,
        entry_event_sha256=digest("entry-event"),
        entry_admission_sha256=digest("entry-admission"),
        route_decision_sha256=digest("route"),
        grid_plan_sha256=digest("grid"),
        cell_id="cell-02",
        role="ANALYZE",
        jspace_basis_id="basis:1",
        jspace_basis_sha256=digest("basis"),
        vector_control_abi="JSPACE_VECTOR_CONTROL_ABI/v1",
        vector_control_packet_sha256=digest("packet"),
        vector_control_packet_jcs_utf8='{"abi_schema":"JSPACE_VECTOR_CONTROL_ABI/v1"}',
        vector_control_condition="BASELINE",
        executor_id="executor:1",
        invocation_id="invocation:1",
        input_sha256=digest("input"),
        input_size=64,
        packet_offset=8,
        binding_sha256=digest("input-binding"),
    )


def verified_execution() -> VerifiedModelExecution:
    return VerifiedModelExecution(
        schema="HCU_VERIFIED_MODEL_EXECUTION/v1",
        canonicalization_schema="RFC8785_JCS_UTF8/v1",
        observation_schema="HCU_MODEL_EXECUTION_OBSERVATION/v1",
        entity_generation=7,
        executor_id="executor:1",
        invocation_id="invocation:1",
        engine_load_consumption_receipt_sha256=digest("load"),
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        engine_artifact_sha256=digest("artifact"),
        grid_plan_sha256=digest("grid"),
        output_producing_cell_id="cell-02",
        role="ANALYZE",
        input_sha256=digest("input"),
        input_size=64,
        output_ref="unifieddb:candidate:1",
        output_sha256=digest("output"),
        output_size=128,
        observation_sha256=digest("observation"),
        receipt_sha256=digest("execution"),
    )


class ControlExecutionBindingTests(unittest.TestCase):
    def setUp(self):
        self.trace = trace()
        self.input = input_binding()
        self.execution = verified_execution()
        self.bytes = b"x" * 64

    def patch_validators(self):
        return patch.multiple(
            module,
            validate_training_trace=lambda value: None,
            validate_model_input_control_binding=lambda value, consumed: None,
            validate_verified_model_execution=lambda value: None,
        )

    def test_exact_sources_bind_deterministically_without_temporal_labels(self):
        with self.patch_validators():
            a = bind_control_packet_to_verified_execution(
                self.trace, self.input, self.execution, self.bytes
            )
            b = bind_control_packet_to_verified_execution(
                self.trace, self.input, self.execution, self.bytes
            )
            self.assertEqual(a, b)
            self.assertFalse(hasattr(a, "predecessor_step_index"))
            self.assertFalse(hasattr(a, "controlled_step_index"))
            self.assertEqual(a.invocation_id, self.execution.invocation_id)
            self.assertEqual(a.verified_model_execution_receipt_sha256, self.execution.receipt_sha256)
            validate_control_execution_binding(a, self.trace, self.input, self.execution, self.bytes)

    def test_execution_invocation_is_owned_by_verified_execution(self):
        forged = replace(self.execution, invocation_id="invocation:forged")
        with self.patch_validators():
            with self.assertRaisesRegex(
                JSpaceControlExecutionBindingError, "EXECUTOR_INVOCATION_MISMATCH"
            ):
                bind_control_packet_to_verified_execution(self.trace, self.input, forged, self.bytes)

    def test_trace_packet_transplant_fails_closed(self):
        forged = replace(self.trace, vector_control_packet_sha256=digest("other-packet"))
        with self.patch_validators():
            with self.assertRaisesRegex(
                JSpaceControlExecutionBindingError, "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH"
            ):
                bind_control_packet_to_verified_execution(forged, self.input, self.execution, self.bytes)

    def test_pairwise_cell_relabel_fails_against_verified_execution(self):
        relabelled_trace = replace(self.trace, cell_id="cell-03")
        relabelled_input = replace(self.input, cell_id="cell-03")
        with self.patch_validators():
            with self.assertRaisesRegex(
                JSpaceControlExecutionBindingError, "INPUT_EXECUTION_CELL_MISMATCH"
            ):
                bind_control_packet_to_verified_execution(
                    relabelled_trace, relabelled_input, self.execution, self.bytes
                )

    def test_input_digest_relabel_fails_against_verified_execution(self):
        forged = replace(self.input, input_sha256=digest("different-input"))
        with self.patch_validators():
            with self.assertRaisesRegex(
                JSpaceControlExecutionBindingError, "EXECUTOR_INPUT_SHA256_MISMATCH"
            ):
                bind_control_packet_to_verified_execution(self.trace, forged, self.execution, self.bytes)

    def test_route_and_admission_ancestry_are_not_free_labels(self):
        cases = (
            (replace(self.input, entry_event_sha256=digest("other-event")), "ENTRY_EVENT_MISMATCH"),
            (
                replace(self.input, entry_admission_sha256=digest("other-admission")),
                "ENTRY_ADMISSION_MISMATCH",
            ),
            (
                replace(self.input, route_decision_sha256=digest("other-route")),
                "ROUTE_DECISION_MISMATCH",
            ),
        )
        with self.patch_validators():
            for forged, code in cases:
                with self.subTest(code=code):
                    with self.assertRaisesRegex(JSpaceControlExecutionBindingError, code):
                        bind_control_packet_to_verified_execution(
                            self.trace, forged, self.execution, self.bytes
                        )

    def test_persisted_binding_is_source_revalidated(self):
        with self.patch_validators():
            binding = bind_control_packet_to_verified_execution(
                self.trace, self.input, self.execution, self.bytes
            )
            tampered_material = replace(binding, executor_id="executor:forged")
            resigned = replace(
                tampered_material,
                binding_sha256=module._canonical_sha256(
                    module._material(tampered_material),
                    "TEST_SELF_CONSISTENT_FORGERY",
                ),
            )
            with self.assertRaisesRegex(
                JSpaceControlExecutionBindingError,
                "JSPACE_CONTROL_EXECUTION_SOURCE_REVALIDATION_MISMATCH",
            ):
                validate_control_execution_binding(
                    resigned, self.trace, self.input, self.execution, self.bytes
                )


if __name__ == "__main__":
    unittest.main()
