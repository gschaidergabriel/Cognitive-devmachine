from __future__ import annotations

import sqlite3

import pytest

from tools.clay_pipeline_study_store import (
    StudyStoreFault,
    ensure_study_schema,
    insert_study_record,
    load_previous_study_record,
)


def record(generation: int, text: str = "```text\nSTATE\n```") -> dict:
    return {
        "schema": "clay-zero-blog-state-box/v1",
        "generation": generation,
        "system_state": {"generation": generation},
        "self_report": {"uncertainty": "UNKNOWN"},
        "deltas": {},
        "evaluation": [],
        "rendered_text": text,
    }


def insert(db: sqlite3.Connection, generation: int, output_id: str) -> None:
    insert_study_record(
        db,
        output_id=output_id,
        ts=float(generation),
        generation=generation,
        profile_id="zero_blog",
        canonical_hash=f"canonical-{generation}",
        packet_hash=f"packet-{generation}",
        record=record(generation),
    )


def test_study_insert_does_not_commit_caller_transaction():
    db = sqlite3.connect(":memory:")
    ensure_study_schema(db)
    db.commit()
    db.execute("BEGIN IMMEDIATE")
    insert(db, 1, "out-1")
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study_records").fetchone()[0] == 1
    db.rollback()
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study_records").fetchone()[0] == 0


def test_previous_record_is_profile_and_generation_scoped():
    db = sqlite3.connect(":memory:")
    ensure_study_schema(db)
    insert(db, 1, "out-1")
    insert(db, 2, "out-2")
    db.commit()
    previous = load_previous_study_record(db, "zero_blog", before_generation=2)
    assert previous is not None
    assert previous["generation"] == 1
    assert load_previous_study_record(db, "other_profile") is None


def test_duplicate_generation_or_output_id_fails_closed():
    db = sqlite3.connect(":memory:")
    ensure_study_schema(db)
    insert(db, 1, "out-1")
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, 1, "out-2")
    db.rollback()


def test_generation_and_binding_mismatches_are_rejected_before_insert():
    db = sqlite3.connect(":memory:")
    ensure_study_schema(db)
    with pytest.raises(StudyStoreFault, match="STUDY_GENERATION_MISMATCH"):
        insert_study_record(
            db,
            output_id="out",
            ts=1.0,
            generation=2,
            profile_id="zero_blog",
            canonical_hash="canonical",
            packet_hash="packet",
            record=record(1),
        )
    with pytest.raises(StudyStoreFault, match="MISSING_STUDY_BINDING"):
        insert_study_record(
            db,
            output_id="out",
            ts=1.0,
            generation=1,
            profile_id="zero_blog",
            canonical_hash="",
            packet_hash="packet",
            record=record(1),
        )
