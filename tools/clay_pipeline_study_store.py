from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS eos_pipeline_study_records(
  output_id TEXT PRIMARY KEY,
  ts REAL NOT NULL,
  generation INTEGER NOT NULL,
  profile_id TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  packet_hash TEXT NOT NULL,
  study_json TEXT NOT NULL,
  rendered_text TEXT NOT NULL,
  UNIQUE(profile_id, generation)
);
CREATE INDEX IF NOT EXISTS idx_eos_pipeline_study_profile_generation
  ON eos_pipeline_study_records(profile_id, generation DESC);
"""


class StudyStoreFault(ValueError):
    pass


def ensure_study_schema(db: sqlite3.Connection) -> None:
    """Install the projection schema without taking ownership of commit/rollback."""
    db.executescript(SCHEMA_SQL)


def load_previous_study_record(db: sqlite3.Connection, profile_id: str, before_generation: int | None = None) -> dict[str, Any] | None:
    if before_generation is None:
        row = db.execute(
            "SELECT study_json FROM eos_pipeline_study_records WHERE profile_id=? ORDER BY generation DESC LIMIT 1",
            (profile_id,),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT study_json FROM eos_pipeline_study_records WHERE profile_id=? AND generation<? ORDER BY generation DESC LIMIT 1",
            (profile_id, int(before_generation)),
        ).fetchone()
    return json.loads(row[0]) if row else None


def insert_study_record(
    db: sqlite3.Connection,
    *,
    output_id: str,
    ts: float,
    generation: int,
    profile_id: str,
    canonical_hash: str,
    packet_hash: str,
    record: Mapping[str, Any],
) -> None:
    """Insert one derived study projection inside the caller's existing transaction.

    This function deliberately never calls commit() or rollback(). The canonical pipeline
    transaction owns output, event-consumption, state-CAS and study-projection atomicity.
    """
    if int(record.get("generation", -1)) != int(generation):
        raise StudyStoreFault("STUDY_GENERATION_MISMATCH")
    rendered = record.get("rendered_text")
    if not isinstance(rendered, str) or not rendered.startswith("```") or not rendered.endswith("```"):
        raise StudyStoreFault("BAD_STUDY_RENDER")
    if not output_id or not canonical_hash or not packet_hash:
        raise StudyStoreFault("MISSING_STUDY_BINDING")
    db.execute(
        "INSERT INTO eos_pipeline_study_records(output_id,ts,generation,profile_id,canonical_hash,packet_hash,study_json,rendered_text) VALUES(?,?,?,?,?,?,?,?)",
        (
            output_id,
            float(ts),
            int(generation),
            str(profile_id),
            str(canonical_hash),
            str(packet_hash),
            json.dumps(dict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            rendered,
        ),
    )


__all__ = [
    "SCHEMA_SQL",
    "StudyStoreFault",
    "ensure_study_schema",
    "insert_study_record",
    "load_previous_study_record",
]
