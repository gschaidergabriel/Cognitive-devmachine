#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import hashlib
import sqlite3
import unittest

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from entry_stream_authority_store_v1 import (
    admit_entry_stream_authority,
    build_stream_authority_decision,
    decision_record,
)
from executor_sequence_lane_authority_closure_v1 import (
    ExecutorSequenceLaneAuthorityClosureError,
    close_executor_sequence_lane_authority,
    revalidate_executor_sequence_lane_authority_closure,
)
from executor_sequence_lane_v1 import (
    BINDING_SCHEMA,
    LANE_SCHEMA,
    ExecutorSequenceLaneBinding,
)


def _sha(value) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _db(generation: int = 7) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.commit()
    return db


def _admit_stream(db: sqlite3.Connection, *, stream_id="stream-alpha", source_id="source-A"):
    decision = build_stream_authority_decision(
        generation=7,
        authority_namespace="typed-entry-transport:v1",
        authority_decision_id=f"transport:{source_id}:{stream_id}",
        source_kind="HUMAN_PROMPT",
        source_id=source_id,
        stream_id=stream_id,
    )
    return admit_entry_stream_authority(
        db,
        decision,
        admitted_stream_authority_decisions={decision.decision_sha256: decision_record(decision)},
        current_generation=7,
    )


def _lane(*, stream_id="stream-alpha", source_id="source-A", executor_id="executor-A", role="planner"):
    lane_material = {
        "schema": LANE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": 7,
        "executor_id": executor_id,
        "source_kind": "HUMAN_PROMPT",
        "source_id": source_id,
        "stream_id": stream_id,
        "role": role,
    }
    sequence_lane_id = _sha(canonicalize(lane_material))
    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_schema": LANE_SCHEMA,
        "generation": 7,
        "executor_id": executor_id,
        "source_kind": "HUMAN_PROMPT",
        "source_id": source_id,
        "stream_id": stream_id,
        "role": role,
        "sequence_lane_id": sequence_lane_id,
        "ingress_id": "ingress-1",
        "causal_id": "causal-1",
        "entry_parent_id": "root",
        "entry_event_sha256": _sha("entry-event"),
        "entry_admission_sha256": _sha("entry-admission"),
        "grid_plan_sha256": _sha("grid-plan"),
        "cell_id": "cell-model",
    }
    provisional = ExecutorSequenceLaneBinding(**material, binding_sha256="1" * 64)
    binding_material = dict(provisional.__dict__)
    binding_material.pop("binding_sha256")
    return replace(provisional, binding_sha256=_sha(canonicalize(binding_material)))


class ExecutorSequenceLaneAuthorityClosureTests(unittest.TestCase):
    def test_admitted_external_stream_closes_existing_lane(self):
        db = _db()
        admission = _admit_stream(db)
        lane = _lane()
        closure = close_executor_sequence_lane_authority(db, lane, current_generation=7)
        self.assertEqual(closure.sequence_lane_id, lane.sequence_lane_id)
        self.assertEqual(closure.lane_binding_sha256, lane.binding_sha256)
        self.assertEqual(closure.stream_authority_admission_sha256, admission.admission_sha256)
        revalidate_executor_sequence_lane_authority_closure(
            db,
            closure,
            lane,
            current_generation=7,
        )

    def test_hash_valid_lane_with_unadmitted_stream_fails_closed(self):
        db = _db()
        _admit_stream(db, stream_id="stream-alpha")
        attacker_lane = _lane(stream_id="stream-attacker")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneAuthorityClosureError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            close_executor_sequence_lane_authority(db, attacker_lane, current_generation=7)

    def test_same_stream_text_under_other_source_is_not_authority(self):
        db = _db()
        _admit_stream(db, stream_id="stream-shared", source_id="source-A")
        other_source_lane = _lane(stream_id="stream-shared", source_id="source-B")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneAuthorityClosureError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            close_executor_sequence_lane_authority(db, other_source_lane, current_generation=7)

    def test_stale_generation_fails_before_positive_closure(self):
        db = _db(generation=8)
        lane = _lane()
        with self.assertRaisesRegex(
            ExecutorSequenceLaneAuthorityClosureError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE|EXECUTOR_SEQUENCE_LANE_GENERATION_MISMATCH",
        ):
            close_executor_sequence_lane_authority(db, lane, current_generation=7)

    def test_outer_closure_tamper_fails_digest_validation(self):
        db = _db()
        _admit_stream(db)
        lane = _lane()
        closure = close_executor_sequence_lane_authority(db, lane, current_generation=7)
        forged = replace(closure, stream_authority_decision_sha256=_sha("forged-decision"))
        with self.assertRaisesRegex(
            ExecutorSequenceLaneAuthorityClosureError,
            "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_DIGEST_MISMATCH",
        ):
            revalidate_executor_sequence_lane_authority_closure(
                db,
                forged,
                lane,
                current_generation=7,
            )

    def test_lane_transplant_cannot_reuse_closure(self):
        db = _db()
        _admit_stream(db)
        lane = _lane(executor_id="executor-A")
        closure = close_executor_sequence_lane_authority(db, lane, current_generation=7)
        other_lane = _lane(executor_id="executor-B")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneAuthorityClosureError,
            "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_SOURCE_REVALIDATION_MISMATCH",
        ):
            revalidate_executor_sequence_lane_authority_closure(
                db,
                closure,
                other_lane,
                current_generation=7,
            )

    def test_stream_authority_db_tamper_breaks_revalidation(self):
        db = _db()
        admission = _admit_stream(db)
        lane = _lane()
        closure = close_executor_sequence_lane_authority(db, lane, current_generation=7)
        row = db.execute(
            "SELECT stream_scope_sha256,admission_jcs FROM hcu_entry_stream_authority_admissions "
            "WHERE admission_sha256=?",
            (admission.admission_sha256,),
        ).fetchone()
        self.assertIsNotNone(row)
        db.execute(
            "UPDATE hcu_entry_stream_authority_admissions SET admission_jcs=? WHERE stream_scope_sha256=?",
            (bytes(row[1]) + b" ", row[0]),
        )
        db.commit()
        with self.assertRaisesRegex(
            ExecutorSequenceLaneAuthorityClosureError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE",
        ):
            revalidate_executor_sequence_lane_authority_closure(
                db,
                closure,
                lane,
                current_generation=7,
            )


if __name__ == "__main__":
    unittest.main()
