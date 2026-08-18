from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid

DEFAULT_DB_PATH = "/var/lib/clay/wiki.db"

# New table names only. Checked 2026-08-18 against the 105 existing wiki.db
# tables (none named mv_*) before this module was written -- see the M1
# report for the exact list checked. This module never touches the other
# 105 tables or the store.py/UnifiedDB schema.
SCHEMA = """
CREATE TABLE IF NOT EXISTS mv_prestage_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value_json TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS mv_prestage_turns (
    prestage_id TEXT PRIMARY KEY,
    turn_id TEXT,
    session_id TEXT,
    user_id TEXT,
    raw_prompt TEXT NOT NULL,
    world_digest TEXT,
    connected_systems_json TEXT,
    caveman_prompt TEXT NOT NULL,
    tool_selection_json TEXT,
    memory_artefacts_json TEXT,
    outsourced_json TEXT,
    user_intent TEXT,
    watch_out TEXT,
    hypotheses_json TEXT,
    counter_hypotheses_json TEXT,
    prestage_model TEXT,
    prestage_receipt_json TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS mv_prestage_turns_session_idx
    ON mv_prestage_turns(session_id, created_at);

CREATE TABLE IF NOT EXISTS mv_translation_log (
    translation_id TEXT PRIMARY KEY,
    turn_id TEXT,
    prestage_id TEXT,
    caveman_original TEXT NOT NULL,
    german_translation TEXT NOT NULL,
    translator_model TEXT,
    translator_receipt_json TEXT,
    faithfulness_score REAL,
    readability_score REAL,
    judge_model TEXT,
    judge_verdict_json TEXT,
    fabrication_flag INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS mv_eval_runs (
    run_id TEXT PRIMARY KEY,
    iteration INTEGER NOT NULL,
    prompt_version TEXT NOT NULL,
    eval_set_size INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_faithfulness REAL NOT NULL,
    avg_readability REAL NOT NULL,
    fabrication_count INTEGER NOT NULL,
    notes TEXT,
    created_at REAL NOT NULL
);
"""


class PrestageStore:
    """Own connection to the shared wiki.db, own tables only.

    Deliberately does NOT go through clayverse.store.UnifiedDB (that class
    executescript()s the coordinator-owned 87/19-table schema on open,
    which this module has no business touching). SQLite's WAL mode makes a
    second independent connection to the same file safe.
    """

    def __init__(self, db_path: str | None = None):
        self.path = db_path or os.environ.get("CLAYVERSE_DB_PATH", DEFAULT_DB_PATH)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript(SCHEMA)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- the pre-stage's own small persistent state / learning loop --
    def state_get(self, key: str, default=None):
        row = self.db.execute(
            "SELECT value_json FROM mv_prestage_state WHERE key=?", (key,)
        ).fetchone()
        return json.loads(row["value_json"]) if row else default

    def state_set(self, key: str, value) -> None:
        self.db.execute(
            "INSERT INTO mv_prestage_state(key,value_json,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at",
            (key, json.dumps(value, ensure_ascii=False, sort_keys=True), time.time()),
        )
        self.db.commit()

    def record_prestage_turn(self, **fields) -> str:
        prestage_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO mv_prestage_turns(prestage_id,turn_id,session_id,user_id,raw_prompt,"
            "world_digest,connected_systems_json,caveman_prompt,tool_selection_json,"
            "memory_artefacts_json,outsourced_json,user_intent,watch_out,hypotheses_json,"
            "counter_hypotheses_json,prestage_model,prestage_receipt_json,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                prestage_id,
                fields.get("turn_id"),
                fields.get("session_id"),
                fields.get("user_id"),
                fields["raw_prompt"],
                fields.get("world_digest"),
                json.dumps(fields.get("connected_systems", {}), ensure_ascii=False, sort_keys=True),
                fields["caveman_prompt"],
                json.dumps(fields.get("tool_selection", []), ensure_ascii=False, sort_keys=True),
                json.dumps(fields.get("memory_artefacts", []), ensure_ascii=False, sort_keys=True),
                json.dumps(fields.get("outsourced", []), ensure_ascii=False, sort_keys=True),
                fields.get("user_intent", ""),
                fields.get("watch_out", ""),
                json.dumps(fields.get("hypotheses", []), ensure_ascii=False, sort_keys=True),
                json.dumps(fields.get("counter_hypotheses", []), ensure_ascii=False, sort_keys=True),
                fields.get("prestage_model"),
                json.dumps(fields.get("prestage_receipt", {}), ensure_ascii=False, sort_keys=True),
                time.time(),
            ),
        )
        self.db.commit()
        return prestage_id

    def record_translation(self, **fields) -> str:
        translation_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO mv_translation_log(translation_id,turn_id,prestage_id,caveman_original,"
            "german_translation,translator_model,translator_receipt_json,faithfulness_score,"
            "readability_score,judge_model,judge_verdict_json,fabrication_flag,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                translation_id,
                fields.get("turn_id"),
                fields.get("prestage_id"),
                fields["caveman_original"],
                fields["german_translation"],
                fields.get("translator_model"),
                json.dumps(fields.get("translator_receipt", {}), ensure_ascii=False, sort_keys=True),
                fields.get("faithfulness_score"),
                fields.get("readability_score"),
                fields.get("judge_model"),
                json.dumps(fields.get("judge_verdict", {}), ensure_ascii=False, sort_keys=True),
                int(bool(fields.get("fabrication_flag", False))),
                time.time(),
            ),
        )
        self.db.commit()
        return translation_id

    def record_eval_run(self, **fields) -> str:
        run_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO mv_eval_runs(run_id,iteration,prompt_version,eval_set_size,pass_rate,"
            "avg_faithfulness,avg_readability,fabrication_count,notes,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                fields["iteration"],
                fields["prompt_version"],
                fields["eval_set_size"],
                fields["pass_rate"],
                fields["avg_faithfulness"],
                fields["avg_readability"],
                fields["fabrication_count"],
                fields.get("notes", ""),
                time.time(),
            ),
        )
        self.db.commit()
        return run_id
