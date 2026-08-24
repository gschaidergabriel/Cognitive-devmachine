#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import sqlite3
import unittest

import executor_sequence_lane_binding_v2 as lane_v2
from entry_stream_authority_store_v1 import (
    admit_entry_stream_authority,
    build_stream_authority_decision,
    decision_record,
)
from executor_sequence_lane_binding_v1 import bind_executor_sequence_lane
from executor_sequence_lane_binding_v2 import (
    AuthorityBackedExecutorSequenceLaneError,
    bind_authority_backed_executor_sequence_lane,
    validate_authority_backed_executor_sequence_lane_binding,
)
from test_executor_sequence_lane_binding_v1 import ExecutorSequenceLaneBindingTests


class AuthorityBackedExecutorSequenceLaneBindingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutorSequenceLaneBindingTests(
            methodName="test_distinct_events_in_same_admitted_stream_share_lane_identity"
        )
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (self.fixture.generation,))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def admit_stream(self, packet, *, decision_id="transport:stream-authority:1"):
        decision = build_stream_authority_decision(
            generation=packet.entity_generation,
            authority_namespace="typed-entry-transport:v1",
            authority_decision_id=decision_id,
            source_kind=packet.source_kind,
            source_id=packet.source_id,
            stream_id=packet.stream_id,
        )
        return admit_entry_stream_authority(
            self.db,
            decision,
            admitted_stream_authority_decisions={decision.decision_sha256: decision_record(decision)},
            current_generation=packet.entity_generation,
        )

    def sources(self, *, causal="event:1", ingress="ingress:1", stream="thread:alpha", invocation="invocation:1", engine="engine:qwen"):
        packet = self.fixture.entry(causal=causal, ingress=ingress, stream=stream)
        plan = self.fixture.plan(packet, engine_label=engine, route_label=f"route:{causal}")
        input_binding, consumed = self.fixture.input_binding(packet, plan, invocation=invocation)
        return packet, plan, input_binding, consumed

    def bind(self, **kwargs):
        packet, plan, input_binding, consumed = self.sources(**kwargs)
        self.admit_stream(packet)
        binding = bind_authority_backed_executor_sequence_lane(
            self.db,
            packet,
            plan,
            input_binding,
            consumed,
        )
        return packet, plan, input_binding, consumed, binding

    def test_v1_grouping_can_exist_without_authority_but_v2_fails_closed(self):
        packet, plan, input_binding, consumed = self.sources()
        projection = bind_executor_sequence_lane(packet, plan, input_binding, consumed)
        self.assertTrue(projection.sequence_lane_sha256)
        with self.assertRaisesRegex(
            AuthorityBackedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            bind_authority_backed_executor_sequence_lane(
                self.db,
                packet,
                plan,
                input_binding,
                consumed,
            )

    def test_attacker_chosen_stream_without_external_admission_is_rejected(self):
        packet, plan, input_binding, consumed = self.sources(stream="thread:attacker")
        with self.assertRaisesRegex(
            AuthorityBackedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            bind_authority_backed_executor_sequence_lane(
                self.db,
                packet,
                plan,
                input_binding,
                consumed,
            )

    def test_distinct_events_share_v2_lane_only_after_same_external_stream_admission(self):
        first_packet, first_plan, first_input, first_consumed = self.sources(
            causal="event:1",
            ingress="ingress:1",
            invocation="invocation:1",
        )
        admission = self.admit_stream(first_packet)
        second_packet, second_plan, second_input, second_consumed = self.sources(
            causal="event:2",
            ingress="ingress:2",
            invocation="invocation:2",
        )
        first = bind_authority_backed_executor_sequence_lane(
            self.db, first_packet, first_plan, first_input, first_consumed
        )
        second = bind_authority_backed_executor_sequence_lane(
            self.db, second_packet, second_plan, second_input, second_consumed
        )
        self.assertEqual(first.stream_authority_admission_sha256, admission.admission_sha256)
        self.assertEqual(first.sequence_lane_sha256, second.sequence_lane_sha256)
        self.assertNotEqual(first.binding_sha256, second.binding_sha256)
        validate_authority_backed_executor_sequence_lane_binding(
            first, self.db, first_packet, first_plan, first_input, first_consumed
        )
        validate_authority_backed_executor_sequence_lane_binding(
            second, self.db, second_packet, second_plan, second_input, second_consumed
        )

    def test_authority_for_alpha_cannot_authorize_beta(self):
        alpha, *_ = self.sources(stream="thread:alpha")
        self.admit_stream(alpha)
        beta_packet, beta_plan, beta_input, beta_consumed = self.sources(stream="thread:beta")
        with self.assertRaisesRegex(
            AuthorityBackedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            bind_authority_backed_executor_sequence_lane(
                self.db,
                beta_packet,
                beta_plan,
                beta_input,
                beta_consumed,
            )

    def test_stream_authority_admission_identity_is_part_of_v2_lane(self):
        packet, plan, input_binding, consumed = self.sources()
        admission = self.admit_stream(packet)
        binding = bind_authority_backed_executor_sequence_lane(
            self.db, packet, plan, input_binding, consumed
        )
        self.assertEqual(binding.stream_authority_admission_sha256, admission.admission_sha256)
        forged = replace(
            binding,
            stream_authority_admission_sha256="1" * 64,
        )
        material = lane_v2._binding_material(forged)
        forged = replace(
            forged,
            binding_sha256=lane_v2._canonical_sha256(material, "TEST_FORGED_V2_BINDING"),
        )
        with self.assertRaisesRegex(
            AuthorityBackedExecutorSequenceLaneError,
            "SOURCE_REVALIDATION_MISMATCH:stream_authority_admission_sha256",
        ):
            validate_authority_backed_executor_sequence_lane_binding(
                forged,
                self.db,
                packet,
                plan,
                input_binding,
                consumed,
            )

    def test_engine_partition_is_preserved_after_stream_authority(self):
        packet_a, plan_a, input_a, consumed_a = self.sources(engine="engine:qwen")
        self.admit_stream(packet_a)
        a = bind_authority_backed_executor_sequence_lane(
            self.db, packet_a, plan_a, input_a, consumed_a
        )
        packet_b, plan_b, input_b, consumed_b = self.sources(engine="engine:other")
        b = bind_authority_backed_executor_sequence_lane(
            self.db, packet_b, plan_b, input_b, consumed_b
        )
        self.assertNotEqual(a.sequence_lane_sha256, b.sequence_lane_sha256)

    def test_stale_generation_stream_authority_cannot_be_read_as_current_lane(self):
        packet, plan, input_binding, consumed = self.sources()
        self.admit_stream(packet)
        self.db.execute("UPDATE entity_state SET generation=8 WHERE id=1")
        self.db.commit()
        with self.assertRaisesRegex(
            AuthorityBackedExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            bind_authority_backed_executor_sequence_lane(
                self.db,
                packet,
                plan,
                input_binding,
                consumed,
            )


if __name__ == "__main__":
    unittest.main()
