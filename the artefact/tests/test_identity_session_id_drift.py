import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_gateway import _runtime_ready


class _TerminalProbe:
    def __init__(self):
        self.checked = []
        self.attested = []

    def binding(self, user_id):
        self.checked.append(user_id)
        raise AssertionError("terminal probing must not run after canonical session-id drift")

    def _has_session(self, binding):
        raise AssertionError("terminal probing must not run after canonical session-id drift")

    def _assert_tmux_server_policy(self, binding):
        self.attested.append(binding.user_id)
        raise AssertionError("terminal attestation must not run after canonical session-id drift")


def _router(tmp_path, clerk_map=None):
    db = UnifiedDB(tmp_path / "state.db")
    router = IdentityRouter(
        db,
        clerk_map
        or {
            "clerk_gabriel": "gabriel",
            "clerk_andreas": "andreas",
        },
    )
    return db, router


def _drift_gabriel_session_id(db):
    db.db.execute(
        "UPDATE sessions SET session_id=? WHERE user_id='gabriel'",
        ("session:gabriel:drift",),
    )


def test_resolve_rejects_noncanonical_session_id(tmp_path):
    db, router = _router(tmp_path)
    try:
        _drift_gabriel_session_id(db)
        with pytest.raises(PermissionError, match="canonical session id mismatch"):
            router.resolve("clerk_gabriel")
    finally:
        db.close()


def test_startup_identity_normalization_rejects_existing_noncanonical_session_id(tmp_path):
    db, _ = _router(tmp_path)
    try:
        _drift_gabriel_session_id(db)
        with pytest.raises(PermissionError, match="canonical session id mismatch"):
            IdentityRouter(db, {})
    finally:
        db.close()


def test_startup_identity_normalization_rejects_missing_persisted_session_without_repair(tmp_path):
    db, _ = _router(tmp_path)
    try:
        db.db.execute("DELETE FROM sessions WHERE user_id='gabriel'")
        with pytest.raises(PermissionError, match="exactly one permanent session"):
            IdentityRouter(db, {})
        assert db.db.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id='gabriel'"
        ).fetchone()[0] == 0
    finally:
        db.close()


def test_runtime_readiness_rejects_noncanonical_session_id_before_terminal_probe(tmp_path):
    db, _ = _router(tmp_path)
    try:
        _drift_gabriel_session_id(db)
        terminals = _TerminalProbe()
        assert _runtime_ready(db, terminals) is False
        assert terminals.checked == []
        assert terminals.attested == []
    finally:
        db.close()