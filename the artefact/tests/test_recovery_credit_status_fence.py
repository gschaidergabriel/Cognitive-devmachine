import pytest

from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.workspace import Workspace


def _recovered_credit(tmp_path, *, status: str, capability: str, ok: bool) -> float:
    db = UnifiedDB(tmp_path / f"{status}-{capability.replace('.', '-')}.db")
    router = IdentityRouter(db, {})
    session_id = router.db.ensure_session("gabriel", "terminal-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover credit parity")
    episode = Workspace(db).open(session_id, turn_id, "recover credit parity", [])
    Workspace(db).select(episode["episode_id"], "request_effect")
    db.record_effect(
        episode["episode_id"],
        "gabriel",
        capability,
        "checkpoint",
        db.session_generation(session_id),
        status,
        None,
        {"ok": ok, "boundary": "internal", "reason": "recovery_credit_parity_probe"},
    )
    recover_incomplete_episodes(db)
    return float(db.db.execute(
        "SELECT credit FROM causal_episodes WHERE episode_id=?",
        (episode["episode_id"],),
    ).fetchone()[0])


@pytest.mark.parametrize("status", ["DENIED", "FAILED", "STALE_OUTCOME", "UNKNOWN_AFTER_RESTART"])
def test_restart_never_promotes_nonverified_ok_receipt_to_positive_credit(tmp_path, status):
    assert _recovered_credit(tmp_path, status=status, capability="entityos.exec", ok=True) == 0.0


def test_restart_verified_rewarding_effect_keeps_positive_credit(tmp_path):
    assert _recovered_credit(tmp_path, status="VERIFIED", capability="entityos.exec", ok=True) == 1.0


def test_restart_verified_noop_stays_non_rewarding(tmp_path):
    assert _recovered_credit(tmp_path, status="VERIFIED", capability="state.noop", ok=True) == 0.0
