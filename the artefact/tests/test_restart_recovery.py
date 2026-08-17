import hashlib
import json

from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.workspace import Workspace


def _episode(db, *, selection=None):
    router = IdentityRouter(db, {})
    session_id = router.db.ensure_session("gabriel", "terminal-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover me")
    episode = Workspace(db).open(session_id, turn_id, "recover me", [])
    if selection is not None:
        Workspace(db).select(episode["episode_id"], selection)
    return session_id, turn_id, episode["episode_id"]


def test_restart_aborts_open_non_effect_episode_and_is_idempotent(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    _, _, episode_id = _episode(db)

    first = recover_incomplete_episodes(db)
    second = recover_incomplete_episodes(db)

    state = db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
    ).fetchone()[0]
    assert state == "RECOVERY_ABORTED_NO_EFFECT"
    assert first["scanned"] == 1
    assert first["reentered_effects"] == 0
    assert first["non_reentered_effects"] == 0
    assert first["aborted_no_effect"] == 1
    assert first["uncertain_effects"] == 0
    assert first["ambiguous_effects"] == 0
    assert second["scanned"] == 0
    assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0


def test_restart_never_replays_selected_effect_without_persisted_outcome(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    _, _, episode_id = _episode(db, selection="request_effect")

    result = recover_incomplete_episodes(db)

    state = db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
    ).fetchone()[0]
    assert state == "RECOVERY_ABORTED_EFFECT_UNCERTAIN"
    assert result["uncertain_effects"] == 1
    assert result["reentered_effects"] == 0
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0


def test_restart_reenters_exactly_one_persisted_verified_effect_outcome_without_reexecution(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    session_id, _, episode_id = _episode(db, selection="request_effect")
    generation = db.session_generation(session_id)
    outcome = {"ok": True, "target": "checkpoint", "boundary": "internal"}
    effect_id = db.record_effect(
        episode_id,
        "gabriel",
        "state.noop",
        "checkpoint",
        generation,
        "VERIFIED",
        None,
        outcome,
    )

    first = recover_incomplete_episodes(db)
    second = recover_incomplete_episodes(db)

    row = db.db.execute(
        "SELECT effect_id,outcome_hash,credit,reentered FROM causal_episodes WHERE episode_id=?",
        (episode_id,),
    ).fetchone()
    expected_hash = hashlib.sha256(json.dumps(outcome, sort_keys=True).encode()).hexdigest()
    assert dict(row) == {
        "effect_id": effect_id,
        "outcome_hash": expected_hash,
        "credit": 1.0,
        "reentered": 1,
    }
    assert first["reentered_effects"] == 1
    assert first["non_reentered_effects"] == 0
    assert second["scanned"] == 0
    assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 1
    assert db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
    ).fetchone()[0] == "RECOVERED_LEGACY_EFFECT_REENTERED"


def test_restart_keeps_denied_effect_as_evidence_without_reentry(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    session_id, _, episode_id = _episode(db, selection="request_effect")
    outcome = {
        "ok": False,
        "denied": True,
        "reason": "entityos_unavailable",
        "target": "x",
        "boundary": "EntityOS",
    }
    effect_id = db.record_effect(
        episode_id,
        "gabriel",
        "entityos.exec",
        "x",
        db.session_generation(session_id),
        "DENIED",
        ["x"],
        outcome,
    )

    result = recover_incomplete_episodes(db)

    row = db.db.execute(
        "SELECT effect_id,credit,reentered,outcome_hash FROM causal_episodes WHERE episode_id=?", (episode_id,)
    ).fetchone()
    assert row["effect_id"] == effect_id
    assert row["credit"] == 0.0
    assert row["reentered"] == 0
    assert row["outcome_hash"]
    assert result["reentered_effects"] == 0
    assert result["non_reentered_effects"] == 1
    assert db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
    ).fetchone()[0] == "RECOVERED_LEGACY_EFFECT_NOT_REENTERED"


def test_restart_fails_closed_on_multiple_effect_records(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    session_id, _, episode_id = _episode(db, selection="request_effect")
    generation = db.session_generation(session_id)
    for target in ("a", "b"):
        db.record_effect(
            episode_id,
            "gabriel",
            "state.noop",
            target,
            generation,
            "VERIFIED",
            None,
            {"ok": True, "target": target, "boundary": "internal"},
        )

    result = recover_incomplete_episodes(db)

    assert result["ambiguous_effects"] == 1
    assert result["reentered_effects"] == 0
    assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
    assert db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
    ).fetchone()[0] == "RECOVERY_ABORTED_AMBIGUOUS_EFFECTS"
