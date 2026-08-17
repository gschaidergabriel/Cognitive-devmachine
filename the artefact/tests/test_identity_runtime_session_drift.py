import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def _router(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    router = IdentityRouter(
        db,
        {
            "clerk_gabriel": "gabriel",
            "clerk_andreas": "andreas",
        },
    )
    return db, router


def test_resolve_reads_existing_canonical_session_without_mutating(tmp_path):
    db, router = _router(tmp_path)
    try:
        before = db.db.execute(
            "SELECT session_id,terminal_name,generation FROM sessions WHERE user_id='gabriel'"
        ).fetchall()
        assert len(before) == 1

        assert router.resolve("clerk_gabriel") == ("gabriel", "session:gabriel")

        after = db.db.execute(
            "SELECT session_id,terminal_name,generation FROM sessions WHERE user_id='gabriel'"
        ).fetchall()
        assert [tuple(row) for row in after] == [tuple(row) for row in before]
    finally:
        db.close()


def test_resolve_does_not_recreate_deleted_permanent_session(tmp_path):
    db, router = _router(tmp_path)
    try:
        db.db.execute("DELETE FROM sessions WHERE user_id='gabriel'")

        with pytest.raises(PermissionError, match="exactly one permanent session"):
            router.resolve("clerk_gabriel")

        count = db.db.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id='gabriel'"
        ).fetchone()[0]
        assert count == 0
    finally:
        db.close()


def test_resolve_rejects_duplicate_session_rows_instead_of_selecting_one(tmp_path):
    db, router = _router(tmp_path)
    try:
        now = time.time()
        db.db.execute(
            "INSERT INTO sessions(session_id,user_id,created_at,updated_at,generation,terminal_name) "
            "VALUES(?,?,?,?,?,?)",
            (
                "session:gabriel:drift",
                "gabriel",
                now,
                now,
                db.entity_generation(),
                "clayverse-gabriel-drift",
            ),
        )

        with pytest.raises(PermissionError, match="exactly one permanent session"):
            router.resolve("clerk_gabriel")
    finally:
        db.close()


def test_resolve_rejects_stale_session_generation(tmp_path):
    db, router = _router(tmp_path)
    try:
        db.db.execute(
            "UPDATE sessions SET generation=? WHERE user_id='gabriel'",
            (db.entity_generation() + 1,),
        )

        with pytest.raises(PermissionError, match="session generation mismatch"):
            router.resolve("clerk_gabriel")
    finally:
        db.close()


def test_resolve_rejects_runtime_extra_user_without_repairing_state(tmp_path):
    db, router = _router(tmp_path)
    try:
        db.ensure_user("shadow", "Shadow")
        before = db.db.execute(
            "SELECT user_id,display_name,rights,clerk_subject FROM users ORDER BY user_id"
        ).fetchall()

        with pytest.raises(PermissionError, match="exactly two users"):
            router.resolve("clerk_gabriel")

        after = db.db.execute(
            "SELECT user_id,display_name,rights,clerk_subject FROM users ORDER BY user_id"
        ).fetchall()
        assert [tuple(row) for row in after] == [tuple(row) for row in before]
    finally:
        db.close()


def test_resolve_rejects_runtime_equal_rights_drift_without_repairing_state(tmp_path):
    db, router = _router(tmp_path)
    try:
        db.db.execute("UPDATE users SET rights='admin' WHERE user_id='gabriel'")

        with pytest.raises(PermissionError, match="rights mismatch: gabriel"):
            router.resolve("clerk_gabriel")

        rights = db.db.execute(
            "SELECT rights FROM users WHERE user_id='gabriel'"
        ).fetchone()[0]
        assert rights == "admin"
    finally:
        db.close()
