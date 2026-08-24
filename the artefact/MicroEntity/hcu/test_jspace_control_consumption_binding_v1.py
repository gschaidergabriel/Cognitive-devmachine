import hashlib
import unittest
from dataclasses import replace

import jspace_control_consumption_binding_v1 as consumption_module
from global_jspace_gwt_v1 import CellContribution, step
from jspace_control_consumption_binding_v1 import (
    JSpaceControlConsumptionBindingError,
    bind_trace_control_to_executor_input,
    validate_jspace_control_consumption_binding,
)
from jspace_training_trace_v1 import build_training_trace
from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_input_control_binding_v1 import bind_direct_unique_packet_input


BASIS_SHA256 = "1" * 64


class JSpaceControlConsumptionBindingTests(unittest.TestCase):
    def prototype(self):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        return step(cells, generation=7, basis_id="basis:7", basis_sha256=BASIS_SHA256)

    def training_trace(self, proto=None, **overrides):
        proto = proto or self.prototype()
        kwargs = dict(
            trace_id="trace:episode-1:step-1",
            trace_family_id="episode:1",
            entry_event_sha256="2" * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            jspace_input_vector_ref="unifieddb:jspace-input:1",
            local_workspace_state_ref="unifieddb:workspace:1",
            global_jspace_slice_ref="unifieddb:jspace-slice:1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )
        kwargs.update(overrides)
        return build_training_trace(proto, proto.control_packet, **kwargs)

    def executor_input_binding(self, proto=None, *, packet=None, **overrides):
        proto = proto or self.prototype()
        packet = packet or proto.control_packet
        consumed = b'{"system":"hcu"}\n' + packet_bytes(packet) + b'\n{"prompt":"solve"}'
        kwargs = dict(
            generation=proto.generation,
            entry_event_sha256="2" * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            cell_id=proto.winner_cell_id,
            role=proto.winner_role,
            executor_id="local-qwen-executor:v1",
            invocation_id="invocation:episode-1:step-1",
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )
        kwargs.update(overrides)
        binding = bind_direct_unique_packet_input(packet, consumed, **kwargs)
        return binding, consumed

    def sources(self):
        proto = self.prototype()
        trace = self.training_trace(proto)
        input_binding, consumed = self.executor_input_binding(proto)
        return proto, trace, input_binding, consumed

    def resign(self, binding):
        return replace(
            binding,
            consumption_binding_sha256=consumption_module._canonical_sha256(
                consumption_module._material(binding),
                "TEST_SELF_CONSISTENT_FORGERY",
            ),
        )

    def test_exact_trace_packet_to_executor_input_binding_is_deterministic(self):
        _, trace, input_binding, consumed = self.sources()
        a = bind_trace_control_to_executor_input(trace, input_binding, consumed)
        b = bind_trace_control_to_executor_input(trace, input_binding, consumed)
        self.assertEqual(a, b)
        self.assertEqual(a.training_trace_sha256, trace.trace_sha256)
        self.assertEqual(a.model_input_control_binding_sha256, input_binding.binding_sha256)
        self.assertEqual(a.invocation_id, input_binding.invocation_id)
        validate_jspace_control_consumption_binding(a, trace, input_binding, consumed)

    def test_causal_envelope_transplant_fails_closed(self):
        proto = self.prototype()
        trace = self.training_trace(proto)
        input_binding, consumed = self.executor_input_binding(proto, entry_event_sha256="6" * 64)
        with self.assertRaisesRegex(
            JSpaceControlConsumptionBindingError,
            "ENTRY_EVENT_IDENTITY_MISMATCH",
        ):
            bind_trace_control_to_executor_input(trace, input_binding, consumed)

    def test_same_metadata_but_different_control_packet_fails_closed(self):
        proto = self.prototype()
        trace = self.training_trace(proto)
        other_packet = encode_vector(
            tuple(reversed(proto.global_vector)),
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition=proto.control_condition,
        )
        self.assertNotEqual(other_packet.packet_sha256, proto.control_packet.packet_sha256)
        input_binding, consumed = self.executor_input_binding(proto, packet=other_packet)
        with self.assertRaisesRegex(
            JSpaceControlConsumptionBindingError,
            "CONTROL_PACKET_IDENTITY_MISMATCH",
        ):
            bind_trace_control_to_executor_input(trace, input_binding, consumed)

    def test_exact_packet_wire_is_bound_not_only_packet_digest(self):
        _, trace, input_binding, consumed = self.sources()
        forged_input_binding = replace(
            input_binding,
            vector_control_packet_jcs_utf8=input_binding.vector_control_packet_jcs_utf8 + "\n",
        )
        with self.assertRaisesRegex(
            JSpaceControlConsumptionBindingError,
            "MODEL_INPUT_CONTROL_BINDING_REJECTED",
        ):
            bind_trace_control_to_executor_input(trace, forged_input_binding, consumed)

    def test_post_binding_executor_input_mutation_fails_revalidation(self):
        _, trace, input_binding, consumed = self.sources()
        binding = bind_trace_control_to_executor_input(trace, input_binding, consumed)
        with self.assertRaisesRegex(
            JSpaceControlConsumptionBindingError,
            "MODEL_INPUT_CONTROL_BINDING_REJECTED",
        ):
            validate_jspace_control_consumption_binding(
                binding,
                trace,
                input_binding,
                consumed + b"!",
            )

    def test_digest_tamper_fails_closed(self):
        _, trace, input_binding, consumed = self.sources()
        binding = bind_trace_control_to_executor_input(trace, input_binding, consumed)
        tampered = replace(binding, invocation_id="invocation:other")
        with self.assertRaisesRegex(
            JSpaceControlConsumptionBindingError,
            "JSPACE_CONTROL_CONSUMPTION_BINDING_DIGEST_MISMATCH",
        ):
            validate_jspace_control_consumption_binding(tampered, trace, input_binding, consumed)

    def test_self_consistent_outer_hash_cannot_relabel_source_invocation(self):
        _, trace, input_binding, consumed = self.sources()
        binding = bind_trace_control_to_executor_input(trace, input_binding, consumed)
        forged = self.resign(replace(binding, invocation_id="invocation:forged"))
        with self.assertRaisesRegex(
            JSpaceControlConsumptionBindingError,
            "JSPACE_CONTROL_CONSUMPTION_SOURCE_REVALIDATION_MISMATCH",
        ):
            validate_jspace_control_consumption_binding(forged, trace, input_binding, consumed)


if __name__ == "__main__":
    unittest.main()
