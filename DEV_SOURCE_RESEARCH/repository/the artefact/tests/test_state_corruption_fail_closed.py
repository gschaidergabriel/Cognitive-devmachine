import hashlib
import sqlite3

import pytest

from clayverse.store import UnifiedDB


def test_truncated_unifieddb_fails_closed_without_silent_reinitialization(tmp_path):
    """Regression replay of the one bounded GO corruption intervention."""
    path = tmp_path / "state.db"
    db = UnifiedDB(path)
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "terminal-gabriel")
    db.append_turn(session_id, "gabriel", "user", "persisted sentinel")
    _, checkpoint_digest = db.checkpoint("pre-corruption")
    assert len(checkpoint_digest) == 64
    db.close()

    baseline = path.read_bytes()
    assert len(baseline) >= 8192
    damaged = baseline[: len(baseline) // 2]
    path.write_bytes(damaged)
    damaged_digest = hashlib.sha256(damaged).hexdigest()

    with pytest.raises(sqlite3.DatabaseError):
        UnifiedDB(path)

    assert hashlib.sha256(path.read_bytes()).hexdigest() == damaged_digest
    assert path.read_bytes() == damaged
    assert not (tmp_path / "state.db-wal").exists()
    assert not (tmp_path / "state.db-shm").exists()
