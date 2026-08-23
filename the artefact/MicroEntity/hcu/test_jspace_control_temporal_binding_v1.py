import hashlib
import unittest
from dataclasses import replace

import jspace_control_temporal_binding_v1 as temporal_module
from global_jspace_gwt_v1 import CellContribution, step
from jspace_control_temporal_binding_v1 import (
    JSpaceControlTemporalBindingError,
    bind_predecessor_control_to_successor_invocation,
    validate_jspace_control_temporal_binding,
)
from jspace_training_trace_v1 import build_training_trace
from jspace_vector_control_v1 import encode_vector, packet_bytes
from model_input_control_binding_v1 import bind_direct_unique_packet_input


BASIS_SHA256 = "1" * 64
GENERATION = 7


class JSpaceControlTemporalBindingTests(unittest.TestCase):
    def prototype(self):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        return step(cells, generation=GENERATION, basis_id="basis:7", basis_sha256=BASIS_SHA256)

    def packet(self, proto=None, *, vector=None, **overrides):
        proto = proto or self.prototype()
        kwargs = dict(
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition=proto.control_condition,
        )
        kwargs.update(overrides)
        return encode_vector(proto.global_vector if vector is None else vector, **kwargs)

    def predecessor_trace(self, proto=None, packet=None):
        proto = proto or self.prototype()
        packet = packet or self.packet(proto)
        return build_training_trace(
            proto,
            packet,
            trace_id="trace:episode-1:step-1",
            trace_family_id="episode:1",
            entry_event_sha256="2" * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            jspace_input_vector_ref="unifieddb:jspace-input:step-1",
            local_workspace_state_ref="unifieddb:workspace:step-1",
            global_jspace_slice_ref="unifieddb:jspace-slice:step-1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )

    def consumed(self, packet):
        return b'{"system":"hcu","step":2}\n' + packet_bytes(packet) + b'\n{"prompt":"successor"}'

    def input_binding(self, packet, consumed=None, **overrides):
        consumed = consumed if consumed is not None else self.consumed(packet)
        kwargs = dict(
            generation=GENERATION,
            entry_event_sha256="6" * 64,
            entry_admission_sha256="7" * 64,
            route_decision_sha256="8" * 64,
            grid_plan_sha256="9" * 64,
            cell_id="critic.0",
            role=packet.role,
            executor_id="local-qwen-executor:v1",
            invocation_id="invocation:episode-1:step-2",
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )
        kwargs.update(overrides)
        return bind_direct_unique_packet_input(packet, consumed, **kwargs)

    def temporal(self, *, trace=None, packet=None, input_binding=None, consumed=None, **overrides):
        proto = self.prototype()
        packet = packet or self.packet(proto)
        trace = trace or self.predecessor_trace(proto, packet)
        consumed = consumed if consumed is not None else self.consumed(packet)
        input_binding = input_binding or self.input_binding(packet, consumed)
        kwargs = dict(
            generation=GENERATION,
            predecessor_step_index=1,
            controlled_step_index=2,
            controlled_invocation_id=input_binding.invocation_id,
        )
        kwargs.update(overrides)
        return bind_predecessor_control_to_successor_invocation(
            trace,
            input_binding,
            consumed,
            **kwargs,
        ), trace, input_binding, consumed

    def resign(self, binding):
        return replace(
            binding,
            temporal_binding_sha256=temporal_module._canonical_sha256(
                temporal_module._material(binding),
                "TEST_SELF_CONSISTENT_FORGERY",
            ),
        )

    def test_predecessor_packet_binds_exactly_to_successor_invocation(self):
        binding, trace, input_binding, consumed = self.temporal()
        self.assertEqual(binding.predecessor_step_index, 1)
        self.assertEqual(binding.controlled_step_index, 2)
        self.assertEqual(binding.predecessor_trace_sha256, trace.trace_sha256)
        self.assertEqual(binding.control_packet_sha256, trace.vector_control_packet_sha256)
        self.assertEqual(binding.model_input_control_binding_sha256, input_binding.binding_sha256)
        self.assertEqual(binding.controlled_invocation_id, input_binding.invocation_id)
        validate_jspace_control_temporal_binding(binding, trace, input_binding, consumed)

    def test_same_step_and_skipped_successor_fail_closed(self):
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "TEMPORAL_SUCCESSOR_EXACTLY_ONE_STEP_REQUIRED"):
            self.temporal(controlled_step_index=1)
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "TEMPORAL_SUCCESSOR_EXACTLY_ONE_STEP_REQUIRED"):
            self.temporal(controlled_step_index=3)

    def test_boolean_or_float_step_indices_fail_closed(self):
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "predecessor_step_index:NONNEGATIVE_INTEGER_REQUIRED"):
            self.temporal(predecessor_step_index=True)
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "controlled_step_index:NONNEGATIVE_INTEGER_REQUIRED"):
            self.temporal(controlled_step_index=2.0)

    def test_different_control_packet_cannot_be_transplanted_into_successor(self):
        proto = self.prototype()
        trace_packet = self.packet(proto)
        trace = self.predecessor_trace(proto, trace_packet)
        alternate = self.packet(proto, vector=(0.25, -0.5, 1.0))
        self.assertNotEqual(trace_packet.packet_sha256, alternate.packet_sha256)
        consumed = self.consumed(alternate)
        input_binding = self.input_binding(alternate, consumed)
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "TEMPORAL_CONTROL_PACKET_IDENTITY_MISMATCH"):
            bind_predecessor_control_to_successor_invocation(
                trace,
                input_binding,
                consumed,
                generation=GENERATION,
                predecessor_step_index=1,
                controlled_step_index=2,
                controlled_invocation_id=input_binding.invocation_id,
            )

    def test_controlled_invocation_identity_is_exact(self):
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "CONTROLLED_INVOCATION_ID_MISMATCH"):
            self.temporal(controlled_invocation_id="invocation:episode-1:other")

    def test_temporal_generation_must_match_both_edges(self):
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "TEMPORAL_GENERATION_MISMATCH"):
            self.temporal(generation=GENERATION + 1)

    def test_self_consistent_temporal_digest_cannot_launder_normalization_alias(self):
        binding, trace, input_binding, consumed = self.temporal()
        forged = self.resign(replace(binding, predecessor_trace_sha256=" " + binding.predecessor_trace_sha256))
        with self.assertRaisesRegex(JSpaceControlTemporalBindingError, "predecessor_trace_sha256:NONCANONICAL_SHA256"):
            validate_jspace_control_temporal_binding(forged, trace, input_binding, consumed)

    def test_temporal_digest_tamper_fails_closed(self):
        binding, trace, input_binding, consumed = self.temporal()
        tampered = replace(binding, controlled_step_index=3)
        with self.assertRaises(JSpaceControlTemporalBindingError):
            validate_jspace_control_temporal_binding(tampered, trace, input_binding, consumed)


if __name__ == "__main__":
    unittest.main()
