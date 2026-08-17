from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from ucm2 import ROOT_MODULE, UCM2  # noqa: E402


V1_SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE objects(
  object_id TEXT PRIMARY KEY,
  root_module TEXT NOT NULL,
  kind TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  version INTEGER NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE edges(
  edge_id TEXT PRIMARY KEY,
  root_module TEXT NOT NULL,
  src TEXT NOT NULL,
  rel TEXT NOT NULL,
  dst TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE events(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  epoch INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  object_id TEXT,
  payload_json TEXT NOT NULL,
  event_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE experiences(
  exp_id TEXT PRIMARY KEY,
  epoch INTEGER NOT NULL,
  actor TEXT NOT NULL,
  observation TEXT NOT NULL,
  prediction TEXT,
  outcome TEXT,
  lesson TEXT,
  claim_class TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_v1(root: Path, *, history: bool = False, epoch_without_event: bool = False) -> Path:
    state = root / "state"
    state.mkdir(parents=True)
    db_path = state / "UCM2.sqlite"
    db = sqlite3.connect(db_path)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(V1_SCHEMA)
        db.execute("INSERT INTO meta VALUES('schema_version','1')")
        db.execute("INSERT INTO meta VALUES('epoch',?)", ("1" if history or epoch_without_event else "0",))
        db.execute(
            "INSERT INTO objects VALUES(?,?,?,?,?,?,?)",
            (
                ROOT_MODULE,
                ROOT_MODULE,
                "clay_machine_key_module",
                "ACTIVE",
                json.dumps({"identity": "ClayMachine2", "role": "unified key module"}),
                1,
                "2026-08-15T00:00:00+00:00",
            ),
        )
        if history:
            db.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?,?,?)",
                (
                    "world.main",
                    ROOT_MODULE,
                    "world_model",
                    "ACTIVE",
                    json.dumps({"main_repo": "legacy"}),
                    1,
                    "2026-08-15T00:00:01+00:00",
                ),
            )
            payload = {"kind": "world_model", "status": "ACTIVE", "version": 1}
            raw = json.dumps([1, "UPSERT", "world.main", payload], sort_keys=True, separators=(",", ":"))
            db.execute(
                "INSERT INTO events(epoch,event_type,object_id,payload_json,event_hash,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (
                    1,
                    "UPSERT",
                    "world.main",
                    json.dumps(payload, sort_keys=True),
                    hashlib.sha256(raw.encode()).hexdigest(),
                    "2026-08-15T00:00:01+00:00",
                ),
            )
        db.commit()
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        db.commit()
    finally:
        db.close()
    return db_path


def expect(code: str, fn) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert str(exc) == code, (str(exc), code)
    else:
        raise AssertionError(f"expected {code}")


def main() -> None:
    with TemporaryDirectory() as tmp:
        base = Path(tmp)

        # Historical v1 state contains lossy events. Opening it under v2 must fail
        # before ALTER/schema relabel or any other database-byte mutation.
        legacy_root = base / "legacy-history"
        legacy_db = make_v1(legacy_root, history=True)
        before = sha256(legacy_db)
        expect("UCM2_V1_HISTORY_NOT_REPLAY_COMPLETE", lambda: UCM2(legacy_root))
        after = sha256(legacy_db)
        assert after == before
        check = sqlite3.connect(f"file:{legacy_db.as_posix()}?mode=ro", uri=True)
        try:
            assert check.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "1"
            assert "prev_hash" not in {r[1] for r in check.execute("PRAGMA table_info(events)")}
        finally:
            check.close()

        # Even missing legacy event rows cannot make a nonzero epoch safe to invent.
        orphan_root = base / "legacy-orphan-epoch"
        orphan_db = make_v1(orphan_root, epoch_without_event=True)
        orphan_before = sha256(orphan_db)
        expect("UCM2_V1_HISTORY_NOT_REPLAY_COMPLETE", lambda: UCM2(orphan_root))
        assert sha256(orphan_db) == orphan_before

        # Root-only epoch-0 v1 contains no semantic history to invent. It can be
        # promoted by creating the v2 replay-complete BOOTSTRAP_ROOT event.
        clean_root = base / "legacy-clean"
        make_v1(clean_root)
        clean = UCM2(clean_root)
        try:
            assert clean.epoch() == 0
            assert clean.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "2"
            assert "prev_hash" in {r[1] for r in clean.db.execute("PRAGMA table_info(events)")}
            stream = clean.event_stream()
            assert len(stream) == 1
            assert stream[0]["event_type"] == "BOOTSTRAP_ROOT"
            assert clean.verify_event_stream(stream) == stream[-1]["event_hash"]
        finally:
            clean.close()

        # Current v2 path remains operational.
        v2 = UCM2(base / "v2")
        try:
            assert v2.upsert("world.main", "world_model", {"fresh": True}) == 1
            assert v2.verify_event_stream() == v2.event_stream()[-1]["event_hash"]
        finally:
            v2.close()

        # Unknown pre-existing schema fails closed instead of being relabelled.
        unknown_root = base / "unknown"
        unknown_root.joinpath("state").mkdir(parents=True)
        unknown_db = unknown_root / "state" / "UCM2.sqlite"
        db = sqlite3.connect(unknown_db)
        db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute("INSERT INTO meta VALUES('schema_version','99')")
        db.commit()
        db.close()
        unknown_before = sha256(unknown_db)
        expect("UCM2_SCHEMA_UNSUPPORTED:99", lambda: UCM2(unknown_root))
        assert sha256(unknown_db) == unknown_before

    print("UCM2_V1_HISTORY_FAIL_CLOSED_PASS")
    print("UCM2_V1_REJECTION_ZERO_DB_MUTATION_PASS")
    print("UCM2_CLEAN_V1_BOOTSTRAP_PROMOTION_PASS")
    print("UCM2_CURRENT_V2_REGRESSION_PASS")


if __name__ == "__main__":
    main()
