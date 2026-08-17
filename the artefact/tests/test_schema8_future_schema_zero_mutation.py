from __future__ import annotations

import hashlib
import sqlite3

import pytest

from clayverse.store import UnifiedDB


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_future_schema_is_rejected_before_any_clayverse_mutation(tmp_path):
    path = tmp_path / "future.db"
    raw = sqlite3.connect(path)
    try:
        raw.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        raw.execute("INSERT INTO meta(key,value) VALUES('schema_version','9')")
        raw.execute("CREATE TABLE sentinel(value TEXT NOT NULL)")
        raw.execute("INSERT INTO sentinel(value) VALUES('future-state-must-survive')")
        raw.commit()
    finally:
        raw.close()

    before_hash = _sha256(path)
    before_bytes = path.read_bytes()

    with pytest.raises(RuntimeError, match="schema_version 9 is newer than supported 8"):
        UnifiedDB(path)

    assert path.read_bytes() == before_bytes
    assert _sha256(path) == before_hash
    assert not path.with_name(path.name + "-wal").exists()
    assert not path.with_name(path.name + "-shm").exists()

    check = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in check.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        }
        assert tables == {"meta", "sentinel"}
        assert check.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "9"
        assert check.execute("SELECT value FROM sentinel").fetchone()[0] == "future-state-must-survive"
    finally:
        check.close()
