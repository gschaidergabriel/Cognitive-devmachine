import json

import pytest

from clayverse.effects import EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def make_lifecycle(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    session_id = db.ensure_session("gabriel", "terminal-gabriel")
    return db, TurnLifecycle(db, "gabriel", session_id)


def persist_noop_without_active_binding(db, lifecycle, target="same-target"):
    opened = lifecycle.begin("effect turn")
    with db.tx() as tx:
        lifecycle.workspace.select_in_tx(opened["episode_id"], "request_effect")
        tx.execute("UPDATE active_turns SET workspace_selected=1 WHERE session_id='session:gabriel'")
    effect_id, outcome = lifecycle.effects.execute(
        EffectRequest("gabriel", "session:gabriel", "state.noop", target, None, opened["generation"]),
        opened["episode_id"],
    )
    assert lifecycle.active()["effect_id"] is None
    return opened, effect_id, outcome


def test_identical_retry_rebinds_final_journal_effect_without_replay(tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    _, effect_id, _ = persist_noop_without_active_binding(db, lifecycle)
    try:
        result = lifecycle.request_effect("state.noop", "same-target")
        assert result["effect_id"] == effect_id
        assert result["outcome"]["recovered"] is True
        assert result["outcome"]["replayed"] is False
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
        assert lifecycle.active()["effect_id"] == effect_id
    finally:
        db.close()


def test_different_retry_is_denied_instead_of_reusing_or_replaying(tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    _, effect_id, _ = persist_noop_without_active_binding(db, lifecycle, target="original")
    try:
        with pytest.raises(TurnLifecycleError, match="different effect already persisted"):
            lifecycle.request_effect("state.noop", "different")
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
        assert db.db.execute("SELECT effect_id FROM effects").fetchone()[0] == effect_id
    finally:
        db.close()


def test_pending_effect_blocks_retry_without_replay(tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    opened = lifecycle.begin("pending effect")
    with db.tx() as tx:
        lifecycle.workspace.select_in_tx(opened["episode_id"], "request_effect")
        tx.execute("UPDATE active_turns SET workspace_selected=1 WHERE session_id='session:gabriel'")
    effect_id = lifecycle.effects.journal.begin(
        opened["episode_id"], "session:gabriel", "gabriel", "state.noop", "pending-target", opened["generation"], None
    )
    try:
        with pytest.raises(TurnLifecycleError, match="outcome pending; automatic replay denied"):
            lifecycle.request_effect("state.noop", "pending-target")
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
        assert db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()[0] == "PENDING"
    finally:
        db.close()


def test_selection_only_crash_is_reconciled_before_first_effect(tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    opened = lifecycle.begin("selection crash")
    with db.tx():
        lifecycle.workspace.select_in_tx(opened["episode_id"], "request_effect")
    assert lifecycle.active()["workspace_selected"] == 0
    try:
        result = lifecycle.request_effect("state.noop", "after-selection-crash")
        assert result["verified"] is True
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
        assert lifecycle.active()["workspace_selected"] == 1
    finally:
        db.close()


def test_stop_can_terminalize_effect_after_binding_crash(tmp_path):
    db, lifecycle = make_lifecycle(tmp_path)
    _, effect_id, _ = persist_noop_without_active_binding(db, lifecycle)
    try:
        result = lifecycle.complete("completed after MCP binding crash")
        assert result["effect_id"] == effect_id
        assert lifecycle.active() is None
        assistant = db.db.execute("SELECT causal_refs FROM turns WHERE role='assistant'").fetchone()
        assert json.loads(assistant["causal_refs"]) == [effect_id]
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    finally:
        db.close()
