from __future__ import annotations

import hashlib
import json
import time

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.method_validation import CandidateValidation, MethodValidationError, derive_promotion_stats
from clayverse.store import UnifiedDB


def _make_episode(db: UnifiedDB, session_id: str, label: str, ordinal: int):
    turn_id = f"turn:{label}"
    episode_id = f"episode:{label}"
    causal_id = f"causal:{label}"
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (turn_id, session_id, "gabriel", ordinal, time.time(), "user", label, "[]", "[]", "{}"),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id, causal_id


def _activate(db: UnifiedDB, session_id: str, generation: int, identity):
    turn_id, episode_id, causal_id = identity
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )


def _finish_verified(db: UnifiedDB, session_id: str, generation: int, identity):
    turn_id, episode_id, causal_id = identity
    effect_id = f"effect:{episode_id}"
    outcome_hash = hashlib.sha256(f"{episode_id}:verified".encode()).hexdigest()
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            "gabriel",
            "entityos.exec",
            json.dumps({"audit": "held-out-gate"}),
            None,
            generation,
            "VERIFIED",
            json.dumps({"ok": True}),
            time.time(),
            time.time(),
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, effect_id, turn_id, outcome_hash, 1.0, 1, time.time()),
    )
    db.db.execute(
        "UPDATE workspace_episodes SET selected='request_effect',state='COMPLETED' WHERE episode_id=?",
        (episode_id,),
    )
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))


def test_shadow_only_validation_receipts_cannot_promote(tmp_path):
    """Promotion evidence must be held-out/cross-instance, not merely successful SHADOW use."""
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.session_generation(session_id)
    identities = [
        _make_episode(db, session_id, "shadow-a", 1),
        _make_episode(db, session_id, "shadow-b", 2),
    ]
    methods = MethodMemory(db)
    candidate_id = methods.admit(
        kind="framework_candidate",
        subject="shadow evidence cannot promote",
        record={
            "problem_signature": {"goal": ["verify"], "mechanism": ["causal"]},
            "preconditions": ["canonical state is available"],
            "goal_shape": ["separate competing mechanisms"],
            "method_steps": ["run a discriminating intervention"],
            "invariants": ["shadow evidence is not promotion authority"],
            "expected_observations": ["held-out outcome discriminates"],
            "falsifiers": ["held-out transfer fails"],
            "failure_modes": ["shadow self-reinforcement"],
            "scope_limits": ["method is not fact"],
            "source_episode_ids": [identity[1] for identity in identities],
            "supporting_memory_ids": [],
            "counterexample_memory_ids": [],
            "abstraction_version": "v1",
            "support_count": 2,
            "success_count": 2,
            "failure_count": 0,
            "calibration": 1.0,
            "last_validated_at": 0.0,
            "status": "CANDIDATE",
            "limits_method_ids": [],
        },
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "held-out-promotion-gate"},
    )
    validator = CandidateValidation(db)
    for index, identity in enumerate(identities):
        _activate(db, session_id, generation, identity)
        use_id = validator.begin(
            candidate_memory_id=candidate_id,
            user_id="gabriel",
            session_id=session_id,
            turn_id=identity[0],
            episode_id=identity[1],
            causal_id=identity[2],
            generation=generation,
            evidence_status="UNKNOWN",
            problem_signature={"goal": ["verify"], "mechanism": ["causal"]},
            evaluation_mode="SHADOW",
            falsifier_checked=index == 1,
        )
        _finish_verified(db, session_id, generation, identity)
        validator.finalize(candidate_use_receipt_id=use_id)

    candidate_row = db.db.execute(
        "SELECT value FROM durable_memory WHERE memory_id=?", (candidate_id,)
    ).fetchone()
    with pytest.raises(MethodValidationError, match="HELD_OUT"):
        derive_promotion_stats(db.db, candidate_id, json.loads(candidate_row["value"]), "gabriel")

    before = db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0]
    with pytest.raises(MethodRecordError, match="validated candidate-use outcome receipts"):
        methods.promote(
            candidate_memory_id=candidate_id,
            evaluation="shadow-only success is not held-out transfer evidence",
            user_id="gabriel",
            provenance={"source": "held-out-promotion-gate"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == before
