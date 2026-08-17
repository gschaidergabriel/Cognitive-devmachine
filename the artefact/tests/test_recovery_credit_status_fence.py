import pytest

from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.workspace import Workspace


@pytest.mark.parametrize("status", ["DENIED", "FAILED", "STALE_OUTCOME", "UNKNOWN_AFTER_RESTART"])
def test_restart_never_promotes_nonverified_ok_receipt_to_positive_credit(tmp_path, status):
    db = UnifiedDB(tmp_path / "state.db")
    router = IdentityRouter(db, {})
    session_id = router.db.ensure_session("gabriel", "terminal-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover status fence")
    episode = Workspace(db).open(session_id, turn_id, "recover status fence", [])
    Workspace(db).select(episode["episode_id"], "request_effect")

    db.record_effect(
        episode["episode_id"],
        "gabriel",
        "state.noop",
        "checkpoint",
        db.session_generation(session_id),
        status,
        None,
        {"ok": True, "boundary": "internal", "reason": "adversarial_inconsistent_receipt"},
    )

    result = recover_incomplete_episodes(db)

    row = db.db.execute(
        "SELECT credit,reentered FROM causal_episodes WHERE episode_id=?",
        (episode["episode_id"],),
    ).fetchone()
    assert tuple(row) == (0.0, 1)
    assert result["reentered_effects"] == 1


def test_restart_verified_ok_receipt_keeps_positive_credit(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    router = IdentityRouter(db, {})
    session_id = router.db.ensure_session("gabriel", "terminal-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover verified")
    episode = Workspace(db).open(session_id, turn_id, "recover verified", [])
    Workspace(db).select(episode["episode_id"], "request_effect")

    db.record_effect(
        episode["episode_id"],
        "gabriel",
        "state.noop",
        "checkpoint",
        db.session_generation(session_id),
        "VERIFIED",
        None,
        {"ok": True, "boundary": "internal"},
    )

    recover_incomplete_episodes(db)

    credit = db.db.execute(
        "SELECT credit FROM causal_episodes WHERE episode_id=?",
        (episode["episode_id"],),
    ).fetchone()[0]
    assert credit == 1.0
