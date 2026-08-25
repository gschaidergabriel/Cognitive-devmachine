import copy
import unittest

from cognitive_process_abi_v1 import (
    CognitiveProcessABIError,
    build_invocation,
    build_result,
    validate_result,
)

D = "a" * 64
E = "b" * 64
F = "c" * 64
G = "d" * 64
H = "e" * 64


def invocation(process_id="AZP-01", target="GRID_SMALL_MODEL", requirement="MIXED"):
    return build_invocation(
        process_id=process_id,
        causal_event_id="event-1",
        admission_id="admission-1",
        work_id=f"work-{process_id}",
        state_generation=4,
        state_epoch=9,
        state_digest=D,
        process_registry_digest=E,
        capability_authority_digest=F,
        source_provenance_digest=G,
        execution_target=target,
        state_requirement=requirement,
        input_payload_ref="db://payload/1",
        input_payload_sha256=H,
        required_capabilities=["COGNITIVE_EXECUTE"],
        durable_data_refs=["db://memory/m1"],
        resource_budget={"tokens_max": 256},
        metadata={"owner_surface": "variable-grid"},
    )


class TestCognitiveProcessABIV1(unittest.TestCase):
    def test_two_process_types_same_executor_and_rejoin_are_stable(self):
        a = invocation("AZP-01")
        b = invocation("AZP-16")
        ra = build_result(
            a,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="RESULT",
            output_payload_ref="mem://r1",
            output_payload_sha256=E,
        )
        rb = build_result(
            b,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="MEASUREMENT",
            output_payload_ref="mem://r2",
            output_payload_sha256=F,
            trace_ref="trace://workspace/2",
            trace_digest=G,
        )
        replay = build_result(
            a,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="RESULT",
            output_payload_ref="mem://r1",
            output_payload_sha256=E,
        )
        self.assertNotEqual(ra.result_id, rb.result_id)
        self.assertEqual(replay.result_id, ra.result_id)
        validate_result(ra.packet, a)
        validate_result(rb.packet, b)

    def test_causal_event_is_distinct_from_admission(self):
        with self.assertRaisesRegex(CognitiveProcessABIError, "MUST_DIFFER"):
            build_invocation(
                process_id="AZP-01",
                causal_event_id="same",
                admission_id="same",
                work_id="w",
                state_generation=0,
                state_epoch=0,
                state_digest=D,
                process_registry_digest=E,
                capability_authority_digest=F,
                source_provenance_digest=G,
                execution_target="NONE",
                state_requirement="EPHEMERAL_ONLY",
                input_payload_ref="x",
                input_payload_sha256=H,
            )

    def test_nested_authority_smuggling_is_rejected(self):
        with self.assertRaisesRegex(CognitiveProcessABIError, "FORBIDDEN_AUTHORITY_FIELD"):
            build_invocation(
                process_id="AZP-01",
                causal_event_id="e",
                admission_id="a",
                work_id="w",
                state_generation=0,
                state_epoch=0,
                state_digest=D,
                process_registry_digest=E,
                capability_authority_digest=F,
                source_provenance_digest=G,
                execution_target="GRID_SMALL_MODEL",
                state_requirement="MIXED",
                input_payload_ref="x",
                input_payload_sha256=H,
                metadata={"nested": {"effect_authority": True}},
            )

    def test_result_cannot_self_grant_canonical_truth(self):
        a = invocation()
        result = build_result(
            a,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="CANDIDATE",
            output_payload_ref="mem://r",
            output_payload_sha256=E,
        )
        packet = copy.deepcopy(result.packet)
        packet["authority_claims"]["canonical_truth"] = True
        with self.assertRaisesRegex(CognitiveProcessABIError, "AUTHORITY_CLAIMS"):
            validate_result(packet, a)

    def test_s1_write_candidate_requires_external_lease_and_never_direct_authority(self):
        a = invocation()
        with self.assertRaises(CognitiveProcessABIError):
            build_result(
                a,
                executor_identity="node-7",
                runtime_identity_digest=D,
                result_class="RESULT",
                output_payload_ref="mem://r",
                output_payload_sha256=E,
                writes_s1_candidate=True,
            )
        result = build_result(
            a,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="RESULT",
            output_payload_ref="mem://r",
            output_payload_sha256=E,
            writes_s1_candidate=True,
            coordinator_lease_ref="s1://lease/9",
            coordinator_lease_digest=F,
        )
        self.assertFalse(result.packet["s1_write_candidate"]["direct_write_authority"])
        validate_result(result.packet, a)

    def test_unknown_requires_explicit_reason(self):
        a = invocation("AZP-16")
        with self.assertRaises(CognitiveProcessABIError):
            build_result(
                a,
                executor_identity="node-7",
                runtime_identity_digest=D,
                result_class="UNKNOWN",
                output_payload_ref="mem://u",
                output_payload_sha256=E,
            )
        result = build_result(
            a,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="UNKNOWN",
            output_payload_ref="mem://u",
            output_payload_sha256=E,
            unknown_reason="measurement unavailable",
        )
        validate_result(result.packet, a)

    def test_claude_code_target_is_explicit_but_non_authoritative(self):
        a = invocation("AZP-05", target="CLAUDE_CODE")
        self.assertEqual(a.packet["execution_target"], "CLAUDE_CODE")
        self.assertFalse(a.packet["authority_claims"]["canonical_truth"])
        self.assertFalse(a.packet["authority_claims"]["effect_authority"])

    def test_state_binding_tamper_is_rejected_on_result(self):
        a = invocation()
        result = build_result(
            a,
            executor_identity="node-7",
            runtime_identity_digest=D,
            result_class="RESULT",
            output_payload_ref="mem://r",
            output_payload_sha256=E,
        )
        packet = copy.deepcopy(result.packet)
        packet["state"]["epoch"] = 10
        with self.assertRaisesRegex(CognitiveProcessABIError, "STATE_BINDING_MISMATCH"):
            validate_result(packet, a)


if __name__ == "__main__":
    unittest.main()
