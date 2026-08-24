import hashlib
import sqlite3
import unittest
from dataclasses import replace

from authorized_executor_sequence_lane_binding_v2 import (
    AuthorizedExecutorSequenceLaneBindingV2Error,
    bind_authorized_executor_sequence_lane_v2,
    validate_authorized_executor_sequence_lane_v2,
)
from entry_stream_authority_binding_v1 import bind_external_stream_authority
from entry_stream_authority_store_v1 import (
    admit_entry_stream_authority,
    build_stream_authority_decision,
    decision_record,
)
from test_executor_sequence_lane_binding_v1 import ExecutorSequenceLaneBindingTests


def h(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def db_for(generation=7):
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.commit()
    return db


class AuthorizedExecutorSequenceLaneV2Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = ExecutorSequenceLaneBindingTests(
            methodName="test_distinct_events_in_same_admitted_stream_share_lane_identity"
        )

    def canonical_stream_authority(self, db, *, stream="thread:alpha", decision_id="stream-decision:alpha"):
        decision = build_stream_authority_decision(
            generation=self.fixture.generation,
            authority_namespace="typed-entry-canonical-stream-registry:v1",
            authority_decision_id=decision_id,
            source_kind="HUMAN_PROMPT",
            source_id=self.fixture.source_id,
            stream_id=stream,
        )
        admission = admit_entry_stream_authority(
            db,
            decision,
            admitted_stream_authority_decisions={
                decision.decision_sha256: decision_record(decision)
            },
            current_generation=self.fixture.generation,
        )
        authority = bind_external_stream_authority(
            generation=self.fixture.generation,
            source_kind="HUMAN_PROMPT",
            source_id=self.fixture.source_id,
            authorized_stream_id=stream,
            authority_kind="CANONICAL_STREAM_REGISTRY",
            authority_ref=decision.authority_decision_id,
            authority_binding_sha256=decision.decision_sha256,
        )
        return decision, admission, authority

    def build(self):
        db = db_for(self.fixture.generation)
        packet = self.fixture.entry(stream="thread:alpha")
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        decision, admission, authority = self.canonical_stream_authority(db)
        binding = bind_authorized_executor_sequence_lane_v2(
            db,
            packet,
            plan,
            input_binding,
            consumed,
            authority,
            current_generation=self.fixture.generation,
        )
        return db, packet, plan, input_binding, consumed, decision, admission, authority, binding

    def test_canonical_db_readback_closes_authorized_lane_without_caller_expected_hash(self):
        db, packet, plan, input_binding, consumed, decision, admission, authority, binding = self.build()
        validate_authorized_executor_sequence_lane_v2(
            db,
            binding,
            packet,
            plan,
            input_binding,
            consumed,
            authority,
            current_generation=self.fixture.generation,
        )
        self.assertEqual(binding.stream_authority_decision_sha256, decision.decision_sha256)
        self.assertEqual(binding.stream_authority_admission_sha256, admission.admission_sha256)
        self.assertEqual(binding.stream_authority_binding_sha256, authority.binding_sha256)

    def test_self_consistent_caller_minted_authority_hash_is_not_canonical_authority(self):
        db = db_for(self.fixture.generation)
        packet = self.fixture.entry(stream="thread:alpha")
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        caller_hash = h("caller-minted-stream-authority")
        authority = bind_external_stream_authority(
            generation=self.fixture.generation,
            source_kind="HUMAN_PROMPT",
            source_id=self.fixture.source_id,
            authorized_stream_id="thread:alpha",
            authority_kind="CANONICAL_STREAM_REGISTRY",
            authority_ref="caller:decision",
            authority_binding_sha256=caller_hash,
        )
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingV2Error,
            "CANONICAL_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            bind_authorized_executor_sequence_lane_v2(
                db,
                packet,
                plan,
                input_binding,
                consumed,
                authority,
                current_generation=self.fixture.generation,
            )

    def test_caller_hash_cannot_override_existing_canonical_decision(self):
        db = db_for(self.fixture.generation)
        packet = self.fixture.entry(stream="thread:alpha")
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        _, _, canonical = self.canonical_stream_authority(db)
        forged = replace(canonical, authority_binding_sha256=h("other-authority"))
        material = dict(forged.__dict__)
        material.pop("binding_sha256")
        from entry_canonicalization_v1 import canonicalize
        forged = replace(forged, binding_sha256=hashlib.sha256(canonicalize(material)).hexdigest())
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingV2Error,
            "STREAM_AUTHORITY_BINDING_NOT_CANONICAL_DECISION",
        ):
            bind_authorized_executor_sequence_lane_v2(
                db,
                packet,
                plan,
                input_binding,
                consumed,
                forged,
                current_generation=self.fixture.generation,
            )

    def test_wrong_registry_reference_cannot_reuse_canonical_decision_hash(self):
        db = db_for(self.fixture.generation)
        packet = self.fixture.entry(stream="thread:alpha")
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        _, _, canonical = self.canonical_stream_authority(db)
        forged = bind_external_stream_authority(
            generation=canonical.generation,
            source_kind=canonical.source_kind,
            source_id=canonical.source_id,
            authorized_stream_id=canonical.stream_id,
            authority_kind="CANONICAL_STREAM_REGISTRY",
            authority_ref="wrong:decision-ref",
            authority_binding_sha256=canonical.authority_binding_sha256,
        )
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingV2Error,
            "STREAM_AUTHORITY_REFERENCE_NOT_CANONICAL_DECISION",
        ):
            bind_authorized_executor_sequence_lane_v2(
                db,
                packet,
                plan,
                input_binding,
                consumed,
                forged,
                current_generation=self.fixture.generation,
            )

    def test_non_registry_authority_kind_is_not_promotable_v2(self):
        db = db_for(self.fixture.generation)
        packet = self.fixture.entry(stream="thread:alpha")
        plan = self.fixture.plan(packet)
        input_binding, consumed = self.fixture.input_binding(packet, plan)
        decision, _, _ = self.canonical_stream_authority(db)
        ingress = bind_external_stream_authority(
            generation=self.fixture.generation,
            source_kind="HUMAN_PROMPT",
            source_id=self.fixture.source_id,
            authorized_stream_id="thread:alpha",
            authority_kind="CANONICAL_INGRESS_CONTROL_PLANE",
            authority_ref=decision.authority_decision_id,
            authority_binding_sha256=decision.decision_sha256,
        )
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingV2Error,
            "STREAM_AUTHORITY_NOT_CANONICAL_REGISTRY_KIND",
        ):
            bind_authorized_executor_sequence_lane_v2(
                db,
                packet,
                plan,
                input_binding,
                consumed,
                ingress,
                current_generation=self.fixture.generation,
            )

    def test_outer_v2_binding_digest_is_revalidated(self):
        db, packet, plan, input_binding, consumed, _, _, authority, binding = self.build()
        forged = replace(binding, executor_id="executor:forged")
        with self.assertRaisesRegex(
            AuthorizedExecutorSequenceLaneBindingV2Error,
            "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2_DIGEST_MISMATCH",
        ):
            validate_authorized_executor_sequence_lane_v2(
                db,
                forged,
                packet,
                plan,
                input_binding,
                consumed,
                authority,
                current_generation=self.fixture.generation,
            )


if __name__ == "__main__":
    unittest.main()
