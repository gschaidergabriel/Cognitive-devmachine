import time

import pytest

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.recovery import RecoveryIntegrityError, recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle
from clayverse.workspace import Workspace


def test_recovery_preflight_rejects_foreign_causal_identity_before_pending_mutation(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    router = IdentityRouter(db, {})
    session_id = router.db.ensure_session("gabriel", "clayverse-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover causal spine")
    episode = Workspace(db).open(session_id, turn_id, "recover causal spine", [])
    Workspace(db).select(episode["episode_id"], "request_effect")
    generation = db.session_generation(session_id)
    active_causal_id = "causal-active"

    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,NULL,NULL,1,?)",
        (session_id, "gabriel", turn_id, episode["episode_id"], active_causal_id, generation, "[]", time.time()),
    )
    effect_id = EffectJournal(db).begin(
        episode["episode_id"], session_id, "gabriel", "state.noop", "checkpoint", generation
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,0,1,?)",
        ("causal-foreign", episode["episode_id"], None, turn_id, "0" * 64, time.time() - 1),
    )

    before_generation = db.entity_generation()
    with pytest.raises(RecoveryIntegrityError, match="causal identity diverged"):
        recover_incomplete_episodes(db)

    effect = db.db.execute(
        "SELECT status,outcome FROM effects WHERE effect_id=?", (effect_id,)
    ).fetchone()
    causal_ids = [
        row[0]
        for row in db.db.execute(
            "SELECT causal_id FROM causal_episodes WHERE episode_id=? ORDER BY causal_id",
            (episode["episode_id"],),
        ).fetchall()
    ]
    assert tuple(effect) == ("PENDING", None)
    assert causal_ids == ["causal-foreign"]
    assert db.db.execute("SELECT COUNT(*) FROM active_turns WHERE session_id=?", (session_id,)).fetchone()[0] == 1
    assert db.entity_generation() == before_generation


def test_recovery_preflight_rejects_active_session_user_crossbind_without_writing_recovery_turn(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    IdentityRouter(db, {})
    opened = TurnLifecycle(db, "gabriel", "session:gabriel").begin("recover identity spine")

    db.db.execute(
        "UPDATE active_turns SET user_id='andreas' WHERE session_id=?",
        (opened["session_id"],),
    )
    before_generation = db.entity_generation()
    before_turn_count = db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0]

    with pytest.raises(RecoveryIntegrityError, match="session/user identity diverged"):
        recover_incomplete_episodes(db)

    active = db.db.execute(
        "SELECT user_id FROM active_turns WHERE session_id=?", (opened["session_id"],)
    ).fetchone()
    assert active["user_id"] == "andreas"
    assert db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)
    ).fetchone()[0] == "OPEN"
    assert db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == before_turn_count
    assert db.entity_generation() == before_generation


def test_recovery_preflight_rejects_causal_observation_crossbind_before_closure(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    IdentityRouter(db, {})
    opened = TurnLifecycle(db, "gabriel", "session:gabriel").begin("recover causal observation")
    foreign_turn = db.append_turn("session:andreas", "andreas", "user", "foreign observation")
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,0,1,?)",
        (
            opened["causal_id"],
            opened["episode_id"],
            None,
            foreign_turn,
            "0" * 64,
            time.time(),
        ),
    )
    before_generation = db.entity_generation()

    with pytest.raises(RecoveryIntegrityError, match="causal observation identity diverged"):
        recover_incomplete_episodes(db)

    assert db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)
    ).fetchone()[0] == "OPEN"
    assert db.db.execute(
        "SELECT COUNT(*) FROM active_turns WHERE session_id=?", (opened["session_id"],)
    ).fetchone()[0] == 1
    assert db.entity_generation() == before_generation
