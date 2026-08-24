import hashlib
import unittest
from dataclasses import replace

from authorized_executor_sequence_lane_binding_v1 import (
    AuthorizedExecutorSequenceLaneBindingError,
    bind_authorized_executor_sequence_lane,
    validate_authorized_executor_sequence_lane,
)
from entry_stream_authority_binding_v1 import bind_external_stream_authority
from test_executor_sequence_lane_binding_v1 import ExecutorSequenceLaneBindingTests


def h(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class AuthorizedExecutorSequenceLaneTests(unittest.TestCase):
    authority_sha = h("canonical-stream-authority:7")

    def setUp(self):
        self.fixture = ExecutorSequenceLaneBindingTests(
            methodName="test_distinct_events_in_same_admitted_stream_share_lane_identity"
        )

    def build(self, *, packet_stream="thread:alpha", authority_stream="thread:alpha"):
        packet = self.fixture.entry(stream=packet_stream)
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        authority = bind_external_stream_authority(
            generation=self.fixture.generation,
            source_kind="HUMAN_PROMPT",
            source_id=self.fixture.source_id,
            authorized_stream_id=authority_stream,
            authority_kind="CANONICAL_INGRESS_CONTROL_PLANE",
            authority_ref="canonical:stream-registry:7",
            authority_binding_sha256=self.authority_sha,
        )
        binding = bind_authorized_executor_sequence_lane(
            packet,
            plan,
            input_binding,
            consumed,
            authority,
            expected_stream_authority_binding_sha256=self.authority_sha,
        )
        return packet, plan, input_binding, consumed, authority, binding

    def test_exact_external_stream_authority_closes_promotable_lane(self):
        packet, plan, input_binding, consumed, authority, binding = self.build()
        validate_authorized_executor_sequence_lane(
            binding,
            packet,
            plan,
            input_binding,
            consumed,
            authority,
            expected_stream_authority_binding_sha256=self.authority_sha,
        )
        self.assertEqual(binding.stream_authority_binding_sha256, authority.binding_sha256)

    def test_self_consistent_entry_stream_cannot_override_external_stream_authority(self):
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingError,
            "STREAM_AUTHORITY_REJECTED:ENTRY_STREAM_AUTHORITY_STREAM_ID_MISMATCH",
        ):
            self.build(packet_stream="thread:forged", authority_stream="thread:alpha")

    def test_wrong_external_authority_identity_fails_before_lane_promotion(self):
        packet = self.fixture.entry()
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        authority = bind_external_stream_authority(
            generation=self.fixture.generation,
            source_kind="HUMAN_PROMPT",
            source_id=self.fixture.source_id,
            authorized_stream_id="thread:alpha",
            authority_kind="CANONICAL_INGRESS_CONTROL_PLANE",
            authority_ref="canonical:stream-registry:7",
            authority_binding_sha256=self.authority_sha,
        )
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingError,
            "STREAM_AUTHORITY_REJECTED:ENTRY_STREAM_EXTERNAL_AUTHORITY_BINDING_MISMATCH",
        ):
            bind_authorized_executor_sequence_lane(
                packet,
                plan,
                input_binding,
                consumed,
                authority,
                expected_stream_authority_binding_sha256=h("different-authority"),
            )

    def test_authorized_outer_binding_digest_is_revalidated(self):
        packet, plan, input_binding, consumed, authority, binding = self.build()
        forged = replace(binding, executor_id="executor:forged")
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingError,
            "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_DIGEST_MISMATCH",
        ):
            validate_authorized_executor_sequence_lane(
                forged,
                packet,
                plan,
                input_binding,
                consumed,
                authority,
                expected_stream_authority_binding_sha256=self.authority_sha,
            )


if __name__ == "__main__":
    unittest.main()
