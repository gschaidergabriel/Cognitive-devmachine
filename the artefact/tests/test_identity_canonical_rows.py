import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def test_clean_boot_creates_exact_canonical_users_and_sessions(tmp_path):
    db=UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db)
    rows=db.db.execute(
        "SELECT user_id,display_name,rights FROM users ORDER BY user_id"
    ).fetchall()
    assert [(row["user_id"],row["display_name"],row["rights"]) for row in rows] == [
        ("andreas","Andreas","equal"),
        ("gabriel","Gabriel","equal"),
    ]
    sessions=db.db.execute(
        "SELECT session_id,user_id,terminal_name FROM sessions ORDER BY user_id"
    ).fetchall()
    assert [tuple(row) for row in sessions] == [
        ("session:andreas","andreas","clayverse-andreas"),
        ("session:gabriel","gabriel","clayverse-gabriel"),
    ]


def test_extra_persisted_user_fails_closed_without_bootstrap_mutation(tmp_path):
    db=UnifiedDB(tmp_path / "unified.db")
    db.db.execute(
        "INSERT INTO users(user_id,display_name) VALUES('mallory','Mallory')"
    )
    with pytest.raises(PermissionError, match="exactly two"):
        IdentityRouter(db)
    rows=db.db.execute("SELECT user_id FROM users ORDER BY user_id").fetchall()
    assert [row["user_id"] for row in rows] == ["mallory"]


def test_empty_user_set_with_persisted_session_fails_closed_without_bootstrap_mutation(tmp_path):
    db=UnifiedDB(tmp_path / "unified.db")
    db.db.execute("PRAGMA foreign_keys=OFF")
    now=time.time()
    db.db.execute(
        "INSERT INTO sessions(session_id,user_id,created_at,updated_at,generation,terminal_name) "
        "VALUES(?,?,?,?,?,?)",
        ("session:ghost","ghost",now,now,db.entity_generation(),"clayverse-ghost"),
    )
    db.db.execute("PRAGMA foreign_keys=ON")

    with pytest.raises(PermissionError, match="empty session set"):
        IdentityRouter(db)

    assert db.db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    assert db.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


def test_canonical_rights_drift_fails_closed(tmp_path):
    db=UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db)
    db.db.execute("UPDATE users SET rights='admin' WHERE user_id='gabriel'")
    with pytest.raises(PermissionError, match="rights mismatch"):
        IdentityRouter(db)


def test_canonical_display_name_drift_fails_closed(tmp_path):
    db=UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db)
    db.db.execute("UPDATE users SET display_name='G' WHERE user_id='gabriel'")
    with pytest.raises(PermissionError, match="display name mismatch"):
        IdentityRouter(db)