import sqlite3
import unittest
from dataclasses import replace

import test_executor_sequence_lane_binding_v1 as lane_fixture
from control_plane_stream_authority_v1 import (
    StreamAuthorityError,
    snapshot_human_prompt_stream_authority,
    validate_entry_stream_authority,
)
from executor_sequence_lane_authority_v1 import (
    AuthorizedExecutorSequenceLaneError,
    authorize_executor_sequence_lane,
    validate_authorized_executor_sequence_lane,
)


class CanonicalDBFixture:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute(
            "CREATE TABLE sessions (session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, generation INTEGER NOT NULL)"
        )
        self.db.executemany(
            "INSERT INTO sessions(session_id,user_id,generation) VALUES(?,?,?)",
            (("session:a", "user:a", 7), ("session:b", "user:b", 7)),
        )
        self.live = {"session:a": 7, "session:b": 7}

    def assert_live_generation(self, session_id, generation):
        if self.live.get(session_id) != generation:
            raise RuntimeError("stale generation")


class ExecutorSequenceLaneAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.db = CanonicalDBFixture()
        self.helper = lane_fixture.ExecutorSequenceLaneBindingTests(methodName="runTest")

    def authority(self, *, session_id="session:a", user_id="user:a"):
        return snapshot_human_prompt_stream_authority(
            self.db,
            user_id=user_id,
            session_id=session_id,
            trusted_source_id=self.helper.source_id,
        )

    def sources(self, *, stream="session:a", causal="event:1", ingress="ingress:1", invocation="invocation:1"):
        packet = self.helper.entry(causal=causal, ingress=ingress, stream=stream)
        plan = self.helper.plan(packet, route_label=f"route:{causal}")
        input_binding, consumed = self.helper.input_binding(packet, plan, invocation=invocation)
        return packet, plan, input_binding, consumed

    def test_canonical_session_stream_authorizes_exact_lane(self):
        packet, plan, input_binding, consumed = self.sources()
        authority = self.authority()
        authorized = authorize_executor_sequence_lane(
            packet, plan, input_binding, consumed, authority
        )
        self.assertEqual(authorized.stream_authority_binding_sha256, authority.binding_sha256)
        self.assertEqual(
            validate_authorized_executor_sequence_lane(
                authorized, packet, plan, input_binding, consumed, authority
            ),
            authorized.authorization_sha256,
        )

    def test_attacker_chosen_hash_bound_stream_without_canonical_authority_fails(self):
        packet, plan, input_binding, consumed = self.sources(stream="thread:attacker")
        authority = self.authority()
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "STREAM_AUTHORITY_REJECTED:EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            authorize_executor_sequence_lane(
                packet, plan, input_binding, consumed, authority
            )

    def test_other_canonical_session_authority_cannot_be_transplanted(self):
        packet, plan, input_binding, consumed = self.sources()
        other = self.authority(session_id="session:b", user_id="user:b")
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "STREAM_AUTHORITY_REJECTED:EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SOURCE_ID_MISMATCH|"
            "STREAM_AUTHORITY_REJECTED:EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            authorize_executor_sequence_lane(packet, plan, input_binding, consumed, other)

    def test_stale_canonical_session_generation_fails_before_view_is_created(self):
        self.db.live["session:a"] = 8
        with self.assertRaisesRegex(
            StreamAuthorityError,
            "CANONICAL_SESSION_GENERATION_NOT_LIVE",
        ):
            self.authority()

    def test_digest_valid_authority_relabel_is_rejected(self):
        packet, _plan, _input_binding, _consumed = self.sources()
        authority = self.authority()
        forged = replace(authority, stream_id="thread:forged")
        with self.assertRaisesRegex(
            StreamAuthorityError,
            "STREAM_AUTHORITY_BINDING_DIGEST_MISMATCH",
        ):
            validate_entry_stream_authority(packet, forged)

    def test_generation_change_rebinds_stream_authority(self):
        before = self.authority()
        self.db.db.execute("UPDATE sessions SET generation=8 WHERE session_id='session:a'")
        self.db.live["session:a"] = 8
        after = self.authority()
        self.assertNotEqual(before.binding_sha256, after.binding_sha256)
        self.assertEqual(after.entity_generation, 8)

    def test_distinct_events_in_same_canonical_session_share_lane_but_not_authorization(self):
        a = self.sources(causal="event:1", ingress="ingress:1", invocation="invocation:1")
        b = self.sources(causal="event:2", ingress="ingress:2", invocation="invocation:2")
        authority = self.authority()
        aa = authorize_executor_sequence_lane(*a, authority)
        bb = authorize_executor_sequence_lane(*b, authority)
        self.assertEqual(aa.sequence_lane_sha256, bb.sequence_lane_sha256)
        self.assertNotEqual(aa.lane_binding_sha256, bb.lane_binding_sha256)
        self.assertNotEqual(aa.authorization_sha256, bb.authorization_sha256)

    def test_unsupported_source_kind_cannot_use_human_session_authority(self):
        packet, plan, input_binding, consumed = self.sources()
        forged = replace(packet, source_kind="EXTERNAL_EVENT")
        authority = self.authority()
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "STREAM_AUTHORITY_REJECTED:EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SOURCE_KIND_MISMATCH",
        ):
            authorize_executor_sequence_lane(
                forged, plan, input_binding, consumed, authority
            )


if __name__ == "__main__":
    unittest.main()
