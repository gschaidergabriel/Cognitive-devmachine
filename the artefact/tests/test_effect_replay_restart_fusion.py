import pytest

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _stack(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    IdentityRouter(db, {})
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    return db, lifecycle


def test_effect_journal_denies_second_effect_for_same_episode_before_execution(tmp_path):
    db, lifecycle = _stack(tmp_path)
    opened = lifecycle.begin("one effect only")
    first = lifecycle.request_effect("state.noop", "first")

    # Simulate the narrow post-journal/pre-active-pointer failure window. The
    # persisted journal is authoritative and must prevent a second effect before
    # any new PENDING record can be created.
    db.db.execute(
        "UPDATE active_turns SET effect_id=NULL,outcome=NULL WHERE session_id='session:gabriel'"
    )
    with pytest.raises(RuntimeError, match="automatic replay denied"):
        lifecycle.request_effect("state.noop", "second")

    effects = db.db.execute(
        "SELECT effect_id,status FROM effects WHERE episode_id=? ORDER BY ts,effect_id",
        (opened["episode_id"],),
    ).fetchall()
    assert [(row["effect_id"], row["status"]) for row in effects] == [(first["effect_id"], "VERIFIED")]


def test_restart_retires_active_turn_after_verified_effect_causal_reentry(tmp_path):
    db, lifecycle = _stack(tmp_path)
    opened = lifecycle.begin("effect then crash before Stop")
    first = lifecycle.request_effect("state.noop", "checkpoint")
    assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 1

    recovered = recover_incomplete_episodes(db)

    assert recovered["scanned"] == 1
    assert recovered["active_turns_closed"] == 1
    assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
    causal = db.db.execute(
        "SELECT causal_id,effect_id,credit FROM causal_episodes WHERE episode_id=?", (opened["episode_id"],)
    ).fetchall()
    assert [tuple(row) for row in causal] == [(opened["causal_id"], first["effect_id"], 0.0)]
    assert db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)
    ).fetchone()[0] == "RECOVERY_CLOSED_AFTER_EFFECT_REENTRY"

    lifecycle.begin("next prompt")
    assert db.db.execute(
        "SELECT COUNT(*) FROM turns WHERE role='system' AND content LIKE 'TURN_ABORTED:%'"
    ).fetchone()[0] == 1


def test_restart_collapses_pending_effect_to_unknown_then_retires_active_turn(tmp_path):
    db, lifecycle = _stack(tmp_path)
    opened = lifecycle.begin("effect boundary interrupted")
    row = lifecycle.active()
    journal = EffectJournal(db)
    effect_id = journal.begin(
        opened["episode_id"],
        "session:gabriel",
        "gabriel",
        "state.noop",
        "checkpoint",
        int(row["generation"]),
    )
    assert db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()[0] == "PENDING"

    recover_incomplete_episodes(db)

    effect = db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
    causal = db.db.execute("SELECT causal_id,effect_id,credit FROM causal_episodes WHERE effect_id=?", (effect_id,)).fetchone()
    assert effect["status"] == "UNKNOWN_AFTER_RESTART"
    assert tuple(causal) == (opened["causal_id"], effect_id, 0.0)
    assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
