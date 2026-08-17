from clayverse.integrity import seal, verify_latest
from clayverse.store import UnifiedDB


def test_integrity_seal_survives_clean_reopen(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "terminal-gabriel")
    db.append_turn(sid, "gabriel", "user", "clean persisted state")
    checkpoint_id, state_hash = seal(db, "test-clean")
    assert verify_latest(db) == {
        "checkpoint_id": checkpoint_id,
        "state_hash": state_hash,
        "note": "integrity:v1:test-clean",
    }
    db.close()

    reopened = UnifiedDB(path)
    verified = verify_latest(reopened)
    assert verified["checkpoint_id"] == checkpoint_id
    assert verified["state_hash"] == state_hash
    reopened.close()
