import sqlite3
import unittest

import test_executor_sequence_lane_binding_v1 as lane_fixture
from entry_stream_authority_store_v1 import (
    admit_entry_stream_authority,
    build_stream_authority_decision,
    decision_record,
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
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute(
            "CREATE TABLE entity_state (id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        self.db.commit()


class ExecutorSequenceLaneAuthorityTests(unittest.TestCase):
    generation = 7

    def setUp(self):
        self.canonical = CanonicalDBFixture()
        self.helper = lane_fixture.ExecutorSequenceLaneBindingTests(methodName="runTest")

    def sources(self, *, stream="stream:alpha", causal="event:1", ingress="ingress:1", invocation="invocation:1"):
        packet = self.helper.entry(causal=causal, ingress=ingress, stream=stream)
        plan = self.helper.plan(packet, route_label=f"route:{causal}")
        input_binding, consumed = self.helper.input_binding(packet, plan, invocation=invocation)
        return packet, plan, input_binding, consumed

    def admit_stream(self, stream="stream:alpha", *, decision_id=None):
        decision = build_stream_authority_decision(
            generation=self.generation,
            authority_namespace="test:canonical-ingress",
            authority_decision_id=decision_id or f"decision:{stream}",
            source_kind="HUMAN_PROMPT",
            source_id=self.helper.source_id,
            stream_id=stream,
        )
        admission = admit_entry_stream_authority(
            self.canonical.db,
            decision,
            admitted_stream_authority_decisions={
                decision.decision_sha256: decision_record(decision)
            },
            current_generation=self.generation,
        )
        return decision, admission

    def authorize(self, packet, plan, input_binding, consumed, *, generation=7):
        return authorize_executor_sequence_lane(
            self.canonical.db,
            packet,
            plan,
            input_binding,
            consumed,
            current_generation=generation,
        )

    def test_exact_canonical_stream_admission_authorizes_lane(self):
        _decision, admission = self.admit_stream()
        packet, plan, input_binding, consumed = self.sources()
        authorized = self.authorize(packet, plan, input_binding, consumed)
        self.assertEqual(
            authorized.stream_authority_admission_sha256,
            admission.admission_sha256,
        )
        self.assertEqual(
            validate_authorized_executor_sequence_lane(
                authorized,
                self.canonical.db,
                packet,
                plan,
                input_binding,
                consumed,
                current_generation=self.generation,
            ),
            authorized.authorization_sha256,
        )

    def test_hash_bound_stream_without_external_canonical_admission_is_projection_only(self):
        packet, plan, input_binding, consumed = self.sources(stream="stream:attacker")
        raw = self.helper.bind(stream="stream:attacker")[-1]
        self.assertEqual(raw.stream_id, "stream:attacker")
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            self.authorize(packet, plan, input_binding, consumed)

    def test_other_admitted_stream_cannot_authorize_packet(self):
        self.admit_stream("stream:other")
        packet, plan, input_binding, consumed = self.sources(stream="stream:alpha")
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            self.authorize(packet, plan, input_binding, consumed)

    def test_stale_entity_generation_fails_closed_on_authority_read(self):
        self.admit_stream()
        packet, plan, input_binding, consumed = self.sources()
        self.canonical.db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        self.canonical.db.commit()
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE:STALE_STREAM_AUTHORITY_READ_GENERATION",
        ):
            self.authorize(packet, plan, input_binding, consumed)

    def test_distinct_events_in_one_admitted_stream_share_lane_but_not_authorization(self):
        self.admit_stream()
        a = self.sources(causal="event:1", ingress="ingress:1", invocation="invocation:1")
        b = self.sources(causal="event:2", ingress="ingress:2", invocation="invocation:2")
        aa = self.authorize(*a)
        bb = self.authorize(*b)
        self.assertEqual(aa.sequence_lane_sha256, bb.sequence_lane_sha256)
        self.assertNotEqual(aa.lane_binding_sha256, bb.lane_binding_sha256)
        self.assertNotEqual(aa.authorization_sha256, bb.authorization_sha256)

    def test_different_independently_admitted_streams_partition_lanes(self):
        self.admit_stream("stream:alpha")
        self.admit_stream("stream:beta")
        a = self.sources(stream="stream:alpha", causal="event:1", ingress="ingress:1")
        b = self.sources(stream="stream:beta", causal="event:2", ingress="ingress:2")
        aa = self.authorize(*a)
        bb = self.authorize(*b)
        self.assertNotEqual(aa.sequence_lane_sha256, bb.sequence_lane_sha256)
        self.assertNotEqual(
            aa.stream_authority_admission_sha256,
            bb.stream_authority_admission_sha256,
        )

    def test_authorization_revalidation_fails_after_canonical_authority_row_removed(self):
        self.admit_stream()
        packet, plan, input_binding, consumed = self.sources()
        authorized = self.authorize(packet, plan, input_binding, consumed)
        self.canonical.db.execute("DELETE FROM hcu_entry_stream_authority_admissions")
        self.canonical.db.commit()
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            validate_authorized_executor_sequence_lane(
                authorized,
                self.canonical.db,
                packet,
                plan,
                input_binding,
                consumed,
                current_generation=self.generation,
            )

    def test_authorized_lane_binds_external_decision_identity(self):
        decision, admission = self.admit_stream(decision_id="decision:trusted-42")
        packet, plan, input_binding, consumed = self.sources()
        authorized = self.authorize(packet, plan, input_binding, consumed)
        self.assertEqual(authorized.stream_authority_decision_sha256, decision.decision_sha256)
        self.assertEqual(authorized.stream_authority_admission_sha256, admission.admission_sha256)
        self.assertEqual(authorized.stream_authority_decision_id, "decision:trusted-42")


if __name__ == "__main__":
    unittest.main()
