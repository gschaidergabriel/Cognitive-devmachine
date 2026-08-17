import json
import sqlite3

from clayverse.identity import IdentityRouter
from clayverse.memory import MemoryManager
from clayverse.store import UnifiedDB


def _table_exists(db, name):
    return db.db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None


def test_compression_has_no_hidden_lossless_turn_ledger(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    router = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = router.resolve("g")
    memory = MemoryManager(db)

    for i in range(45):
        content = "FACT: " + " ".join(f"explicit-{i}-{j}" for j in range(120))
        turn_id = db.append_turn(sid, uid, "user", content)
        memory.extract_explicit(turn_id, uid, content)

    assert memory.compact(sid) > 0
    assert not _table_exists(db, "turn_ledger")
    first = db.all_turns(sid)[0]
    assert first["compression_generation"] > 0

    receipt = db.db.execute(
        "SELECT provenance FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=?",
        (first["turn_id"],),
    ).fetchone()
    provenance = json.loads(receipt["provenance"])
    assert provenance["lossless_source_retained"] is False
    assert len(provenance["source_sha256"]) == 64
    assert provenance["source_bytes"] > 0
    db.close()


def test_schema2_hidden_raw_ledger_is_retired_on_open(tmp_path):
    path = tmp_path / "schema2.db"
    db = UnifiedDB(path)
    router = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = router.resolve("g")
    turn_id = db.append_turn(sid, uid, "user", "ordinary full turn")
    db.close()

    raw = sqlite3.connect(path)
    raw.execute(
        "CREATE TABLE turn_ledger(turn_id TEXT PRIMARY KEY REFERENCES turns(turn_id),raw_content TEXT NOT NULL,raw_sha256 TEXT NOT NULL,recorded_at REAL NOT NULL)"
    )
    raw.execute(
        "INSERT INTO turn_ledger VALUES(?,?,?,?)",
        (turn_id, "ordinary full turn", "0" * 64, 0.0),
    )
    raw.execute(
        "CREATE TRIGGER turn_ledger_no_update BEFORE UPDATE ON turn_ledger BEGIN SELECT RAISE(ABORT,'turn ledger immutable'); END"
    )
    raw.execute("UPDATE meta SET value='2' WHERE key='schema_version'")
    raw.commit()
    raw.close()

    reopened = UnifiedDB(path)
    assert not _table_exists(reopened, "turn_ledger")
    assert reopened.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "3"
    assert reopened.db.execute("SELECT content FROM turns WHERE turn_id=?", (turn_id,)).fetchone()[0] == "ordinary full turn"
    reopened.close()
