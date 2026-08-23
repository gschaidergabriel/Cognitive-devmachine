import unittest
from dataclasses import replace

from global_jspace_gwt_v1 import CellContribution, step
from jspace_training_trace_v1 import (
    JSpaceTrainingTraceError,
    build_training_trace,
    trace_dict,
    validate_training_trace,
)
from jspace_vector_control_v1 import encode_vector


BASIS_SHA256 = "1" * 64


class JSpaceTrainingTraceTests(unittest.TestCase):
    def prototype(self):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        return step(cells, generation=7, basis_id="basis:7", basis_sha256=BASIS_SHA256)

    def packet(self, proto=None, **overrides):
        proto = proto or self.prototype()
        kwargs = dict(
            basis_id=proto.basis_id,
            basis_sha256=BASIS_SHA256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition="BASELINE",
        )
        kwargs.update(overrides)
        return encode_vector(proto.global_vector, **kwargs)

    def build(self, *, proto=None, packet=None, **overrides):
        proto = proto or self.prototype()
        packet = packet or self.packet(proto)
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
        return build_training_trace(proto, packet, **kwargs)

    def test_exact_prototype_and_vector_packet_bind_to_complete_trace(self):
        trace = self.build()
        validate_training_trace(trace)
        material = trace_dict(trace)
        mandatory = {
            "schema_version", "trace_id", "trace_family_id", "generation",
            "entry_event_sha256", "entry_admission_sha256", "route_decision_sha256",
            "grid_plan_sha256", "cell_id", "role", "jspace_basis_id",
            "jspace_input_vector_ref", "jspace_input_codec_version",
            "local_workspace_state_ref", "gwt_competition_set", "gwt_broadcast_gate",
            "global_jspace_slice_ref", "hyperposition_branch_ids",
            "provenance_evidence_class", "resource_budget", "requested_action_class",
            "expected_structured_model_output", "observed_downstream_outcome",
            "falsifier_lesion_condition", "credit_label", "trace_sha256",
        }
        self.assertTrue(mandatory.issubset(material))
        self.assertEqual(material["jspace_input_codec_version"], "JSPACE_VECTOR_CONTROL_ABI/v1")
        self.assertEqual(material["credit_label"], "UNKNOWN")
        self.assertEqual(len(trace.trace_sha256), 64)

    def test_same_inputs_are_deterministic(self):
        self.assertEqual(self.build(), self.build())

    def test_vector_generation_basis_hash_and_role_must_match_prototype(self):
        proto = self.prototype()
        for packet, code in [
            (self.packet(proto, generation=8), "VECTOR_CONTROL_GENERATION_MISMATCH"),
            (self.packet(proto, basis_id="basis:other"), "VECTOR_CONTROL_BASIS_MISMATCH"),
            (self.packet(proto, basis_sha256="7" * 64), "VECTOR_CONTROL_BASIS_SHA256_MISMATCH"),
            (self.packet(proto, role="simulation"), "VECTOR_CONTROL_ROLE_MISMATCH"),
        ]:
            with self.assertRaisesRegex(JSpaceTrainingTraceError, code):
                self.build(proto=proto, packet=packet)

    def test_control_packet_transplant_with_same_metadata_fails_closed(self):
        proto = self.prototype()
        transplanted = encode_vector(
            tuple(reversed(proto.global_vector)),
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition=proto.control_condition,
        )
        self.assertNotEqual(transplanted.packet_sha256, proto.control_packet.packet_sha256)
        with self.assertRaisesRegex(JSpaceTrainingTraceError, "VECTOR_CONTROL_PACKET_TRANSPLANT"):
            self.build(proto=proto, packet=transplanted)

    def test_control_condition_must_match_prototype(self):
        proto = self.prototype()
        wrong_condition = encode_vector(
            proto.global_vector,
            basis_id=proto.basis_id,
            basis_sha256=proto.basis_sha256,
            generation=proto.generation,
            role=proto.winner_role,
            control_condition="SIGN_FLIP",
        )
        with self.assertRaisesRegex(JSpaceTrainingTraceError, "VECTOR_CONTROL_CONDITION_MISMATCH"):
            self.build(proto=proto, packet=wrong_condition)

    def test_nonunknown_credit_requires_outcome_reference_and_provenance_but_not_admission_here(self):
        with self.assertRaisesRegex(JSpaceTrainingTraceError, "NONUNKNOWN_CREDIT_REQUIRES_OUTCOME_RECEIPT_REFERENCE"):
            self.build(credit_label="POSITIVE")
        with self.assertRaisesRegex(JSpaceTrainingTraceError, "NONUNKNOWN_CREDIT_REQUIRES_VERIFIED_OUTCOME_PROVENANCE"):
            self.build(credit_label="POSITIVE", outcome_receipt_sha256="6" * 64)

        # The trace envelope intentionally records a typed reference only. The canonical
        # dataset-admission gate must independently admit and causally bind this receipt
        # before serious training data can be emitted.
        trace = self.build(
            credit_label="POSITIVE",
            outcome_receipt_sha256="6" * 64,
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE_WITH_VERIFIED_OUTCOME",
            observed_downstream_outcome="CLAIMED_TASK_SUCCESS_PENDING_ADMISSION",
        )
        validate_training_trace(trace)
        self.assertEqual(trace.credit_label, "POSITIVE")
        self.assertEqual(trace.outcome_receipt_sha256, "6" * 64)

    def test_trace_digest_tamper_fails_closed(self):
        trace = self.build()
        tampered = replace(trace, observed_downstream_outcome="CHANGED_AFTER_HASH")
        with self.assertRaisesRegex(JSpaceTrainingTraceError, "TRAINING_TRACE_DIGEST_MISMATCH"):
            validate_training_trace(tampered)

    def test_placeholder_causal_receipt_is_rejected(self):
        with self.assertRaisesRegex(JSpaceTrainingTraceError, "PLACEHOLDER_SHA256_FORBIDDEN"):
            self.build(entry_event_sha256="0" * 64)

    def test_trace_family_is_explicit_not_inferred_from_neighbor_rows(self):
        a = self.build(trace_id="trace:a", trace_family_id="episode:A")
        b = self.build(trace_id="trace:b", trace_family_id="episode:B")
        self.assertNotEqual(a.trace_family_id, b.trace_family_id)
        self.assertNotEqual(a.trace_sha256, b.trace_sha256)


if __name__ == "__main__":
    unittest.main()
