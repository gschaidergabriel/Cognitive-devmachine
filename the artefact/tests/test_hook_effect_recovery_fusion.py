import json

from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _stack(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    IdentityRouter(db, {})
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    bridge = ClayVerseEffectBridge(db, "gabriel", "session:gabriel")
    return db, lifecycle, bridge


def test_effect_bridge_uses_durable_active_turn_generation_and_binds_outcome(tmp_path):
    db, lifecycle, bridge = _stack(tmp_path)
    opened = lifecycle.begin("do the bounded state effect")

    turn = db.db.execute("SELECT provenance FROM turns WHERE turn_id=?", (opened["turn_id"],)).fetchone()
    # Generation is intentionally not duplicated into turn provenance. The effect
    # bridge must consume the authoritative active_turns record written by the hook.
    assert "session_generation" not in json.loads(turn["provenance"])

    result = bridge.request_effect("state.noop", "checkpoint")
    active = db.db.execute(
        "SELECT causal_id,generation,effect_id,outcome,workspace_selected FROM active_turns WHERE session_id='session:gabriel'"
    ).fetchone()
    assert result["verified"] is True
    assert result["causal_id"] == opened["causal_id"] == active["causal_id"]
    assert active["generation"] == opened["generation"]
    assert active["effect_id"] == result["effect_id"]
    assert json.loads(active["outcome"])["ok"] is True
    assert active["workspace_selected"] == 1

    completed = lifecycle.complete("done")
    causal = db.db.execute(
        "SELECT causal_id,effect_id,credit FROM causal_episodes WHERE causal_id=?", (opened["causal_id"],)
    ).fetchone()
    assert completed["effect_id"] == result["effect_id"]
    assert tuple(causal) == (opened["causal_id"], result["effect_id"], 1.0)
    assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0


def test_effect_bridge_denies_replay_when_journal_has_effect_but_active_pointer_is_missing(tmp_path):
    db, lifecycle, bridge = _stack(tmp_path)
    opened = lifecycle.begin("effect once")
    result = bridge.request_effect("state.noop", "first")
    db.db.execute(
        "UPDATE active_turns SET effect_id=NULL,outcome=NULL WHERE session_id='session:gabriel'"
    )

    try:
        bridge.request_effect("state.noop", "second")
    except Exception as exc:
        assert "replay denied" in str(exc)
    else:
        raise AssertionError("second effect unexpectedly admitted")

    assert db.db.execute("SELECT COUNT(*) FROM effects WHERE episode_id=?", (opened["episode_id"],)).fetchone()[0] == 1
    assert result["effect_id"] is not None


def test_restart_recovery_preserves_hook_causal_id_and_retires_active_turn(tmp_path):
    db, lifecycle, bridge = _stack(tmp_path)
    opened = lifecycle.begin("effect then crash")
    result = bridge.request_effect("state.noop", "checkpoint")

    recovered = recover_incomplete_episodes(db)
    assert recovered["reentered_effects"] == 1
    assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
    causal = db.db.execute(
        "SELECT causal_id,effect_id,credit FROM causal_episodes WHERE episode_id=?", (opened["episode_id"],)
    ).fetchall()
    assert [tuple(row) for row in causal] == [(opened["causal_id"], result["effect_id"], 1.0)]

    # The next prompt starts cleanly; it must not create a second causal/abort record
    # for the recovered episode.
    lifecycle.begin("next prompt")
    old_causal_count = db.db.execute(
        "SELECT COUNT(*) FROM causal_episodes WHERE episode_id=?", (opened["episode_id"],)
    ).fetchone()[0]
    old_abort_count = db.db.execute(
        "SELECT COUNT(*) FROM turns WHERE role='system' AND content LIKE 'TURN_ABORTED:%'"
    ).fetchone()[0]
    assert old_causal_count == 1
    assert old_abort_count == 0
