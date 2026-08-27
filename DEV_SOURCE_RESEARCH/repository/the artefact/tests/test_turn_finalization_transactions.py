import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def make_lifecycle(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    session_id = db.ensure_session("gabriel", "terminal-gabriel")
    return db, TurnLifecycle(db, "gabriel", session_id)


def test_complete_failure_rolls_back_workspace_and_assistant(monkeypatch, tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    opened = lifecycle.begin("hello")
    monkeypatch.setattr(lifecycle.graph, "rebuild_in_tx", lambda: (_ for _ in ()).throw(RuntimeError("projection failure")))
    try:
        with pytest.raises(RuntimeError, match="projection failure"):
            lifecycle.complete("answer")
        assert [row["role"] for row in db.all_turns("session:gabriel")] == ["user"]
        assert lifecycle.active()["turn_id"] == opened["turn_id"]
        ws = db.db.execute("SELECT state,selected FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)).fetchone()
        assert (ws["state"], ws["selected"]) == ("OPEN", None)
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
    finally:
        db.close()


def test_abort_failure_rolls_back_predecessor_retirement(monkeypatch, tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    opened = lifecycle.begin("interrupted")
    monkeypatch.setattr(lifecycle.graph, "rebuild_in_tx", lambda: (_ for _ in ()).throw(RuntimeError("projection failure")))
    try:
        with pytest.raises(RuntimeError, match="projection failure"):
            lifecycle.abort("interrupt")
        assert [row["role"] for row in db.all_turns("session:gabriel")] == ["user"]
        assert lifecycle.active()["turn_id"] == opened["turn_id"]
        state = db.db.execute("SELECT state FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)).fetchone()[0]
        assert state == "OPEN"
    finally:
        db.close()


def test_effectful_complete_requires_existing_causal_reentry(tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    opened = lifecycle.begin("effect turn")
    effect_id = db.record_effect(opened["episode_id"], "gabriel", "state.noop", "test", opened["generation"], "VERIFIED", outcome={"ok": True})
    db.db.execute("UPDATE active_turns SET effect_id=? WHERE session_id='session:gabriel'", (effect_id,))
    try:
        with pytest.raises(TurnLifecycleError, match="effect lacks causal re-entry"):
            lifecycle.complete("must not launder the effect")
        assert [row["role"] for row in db.all_turns("session:gabriel")] == ["user"]
        assert lifecycle.active()["effect_id"] == effect_id
    finally:
        db.close()
