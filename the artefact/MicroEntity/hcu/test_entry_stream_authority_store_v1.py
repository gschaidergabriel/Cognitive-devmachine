#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import sqlite3
import unittest

from entry_stream_authority_store_v1 import (
    ADMITTED_STATUS,
    EntryStreamAuthorityError,
    admit_entry_stream_authority,
    build_stream_authority_decision,
    decision_record,
    read_entry_stream_authority_admission,
)


def _db(generation: int = 7) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.commit()
    return db


def _decision(*, stream_id: str = "stream-alpha", decision_id: str = "transport:decision:1", generation: int = 7):
    return build_stream_authority_decision(
        generation=generation,
        authority_namespace="typed-entry-transport:v1",
        authority_decision_id=decision_id,
        source_kind="HUMAN_PROMPT",
        source_id="source-A",
        stream_id=stream_id,
    )


def _registry(decision):
    return {decision.decision_sha256: decision_record(decision)}


class EntryStreamAuthorityStoreTests(unittest.TestCase):
    def test_external_decision_admits_and_reads_back_from_canonical_db(self):
        db = _db()
        decision = _decision()
        admission = admit_entry_stream_authority(
            db,
            decision,
            admitted_stream_authority_decisions=_registry(decision),
            current_generation=7,
        )
        self.assertEqual(admission.status, ADMITTED_STATUS)
        observed = read_entry_stream_authority_admission(
            db,
            current_generation=7,
            source_kind="HUMAN_PROMPT",
            source_id="source-A",
            stream_id="stream-alpha",
        )
        self.assertEqual(observed, admission)

    def test_attacker_chosen_stream_without_external_admission_fails_before_table_write(self):
        db = _db()
        attacker = _decision(stream_id="stream-attacker")
        with self.assertRaisesRegex(
            EntryStreamAuthorityError,
            "STREAM_AUTHORITY_DECISION_NOT_EXTERNALLY_ADMITTED",
        ):
            admit_entry_stream_authority(
                db,
                attacker,
                admitted_stream_authority_decisions={},
                current_generation=7,
            )
        table = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='hcu_entry_stream_authority_admissions'"
        ).fetchone()
        self.assertIsNone(table)

    def test_external_registry_must_match_exact_canonical_decision(self):
        db = _db()
        decision = _decision()
        forged_record = decision_record(decision)
        forged_record["stream_id"] = "stream-other"
        with self.assertRaisesRegex(
            EntryStreamAuthorityError,
            "STREAM_AUTHORITY_EXTERNAL_REGISTRY_MISMATCH",
        ):
            admit_entry_stream_authority(
                db,
                decision,
                admitted_stream_authority_decisions={decision.decision_sha256: forged_record},
                current_generation=7,
            )

    def test_exact_replay_is_idempotent(self):
        db = _db()
        decision = _decision()
        registry = _registry(decision)
        first = admit_entry_stream_authority(
            db,
            decision,
            admitted_stream_authority_decisions=registry,
            current_generation=7,
        )
        second = admit_entry_stream_authority(
            db,
            decision,
            admitted_stream_authority_decisions=registry,
            current_generation=7,
        )
        self.assertEqual(first, second)
        count = db.execute("SELECT COUNT(*) FROM hcu_entry_stream_authority_admissions").fetchone()[0]
        self.assertEqual(count, 1)

    def test_divergent_authority_decision_for_same_stream_scope_fails_closed(self):
        db = _db()
        first = _decision(decision_id="transport:decision:1")
        second = _decision(decision_id="transport:decision:2")
        admit_entry_stream_authority(
            db,
            first,
            admitted_stream_authority_decisions=_registry(first),
            current_generation=7,
        )
        with self.assertRaisesRegex(
            EntryStreamAuthorityError,
            "STREAM_AUTHORITY_ADMISSION_REPLAY_DIVERGENCE",
        ):
            admit_entry_stream_authority(
                db,
                second,
                admitted_stream_authority_decisions=_registry(second),
                current_generation=7,
            )
        count = db.execute("SELECT COUNT(*) FROM hcu_entry_stream_authority_admissions").fetchone()[0]
        self.assertEqual(count, 1)

    def test_stale_generation_fails_and_rolls_back(self):
        db = _db(generation=8)
        decision = _decision(generation=7)
        with self.assertRaisesRegex(
            EntryStreamAuthorityError,
            "STALE_STREAM_AUTHORITY_ADMISSION_GENERATION",
        ):
            admit_entry_stream_authority(
                db,
                decision,
                admitted_stream_authority_decisions=_registry(decision),
                current_generation=7,
            )
        self.assertFalse(db.in_transaction)

    def test_missing_stream_authority_read_fails_with_sequence_specific_code(self):
        db = _db()
        with self.assertRaisesRegex(
            EntryStreamAuthorityError,
            "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE|STREAM_AUTHORITY_ADMISSION_STORE_REQUIRED",
        ):
            read_entry_stream_authority_admission(
                db,
                current_generation=7,
                source_kind="HUMAN_PROMPT",
                source_id="source-A",
                stream_id="stream-alpha",
            )

    def test_stored_admission_tamper_is_detected_on_read(self):
        db = _db()
        decision = _decision()
        admission = admit_entry_stream_authority(
            db,
            decision,
            admitted_stream_authority_decisions=_registry(decision),
            current_generation=7,
        )
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
            EntryStreamAuthorityError,
            "STREAM_AUTHORITY_STORED_ADMISSION_JCS_MISMATCH|STREAM_AUTHORITY_STORED_BYTES_INVALID",
        ):
            read_entry_stream_authority_admission(
                db,
                current_generation=7,
                source_kind="HUMAN_PROMPT",
                source_id="source-A",
                stream_id="stream-alpha",
            )

    def test_foreign_keys_are_required_for_canonical_store_write(self):
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,7)")
        db.commit()
        decision = _decision()
        with self.assertRaisesRegex(EntryStreamAuthorityError, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION"):
            admit_entry_stream_authority(
                db,
                decision,
                admitted_stream_authority_decisions=_registry(decision),
                current_generation=7,
            )

    def test_self_consistent_decision_tamper_without_registry_change_is_not_authority(self):
        db = _db()
        original = _decision()
        forged = _decision(stream_id="stream-forged", decision_id="transport:decision:forged")
        with self.assertRaisesRegex(
            EntryStreamAuthorityError,
            "STREAM_AUTHORITY_DECISION_NOT_EXTERNALLY_ADMITTED",
        ):
            admit_entry_stream_authority(
                db,
                forged,
                admitted_stream_authority_decisions=_registry(original),
                current_generation=7,
            )


if __name__ == "__main__":
    unittest.main()
