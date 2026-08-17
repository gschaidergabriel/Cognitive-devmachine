from __future__ import annotations

import hashlib
import json
import time

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.method_validation import (
    CandidateValidation,
    MethodValidationError,
    derive_promotion_stats,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.session_generation(session_id)
    return db, session_id, generation


def _make_episode(db, session_id, generation, label, ordinal):
    turn_id = f"turn:{label}"
    episode_id = f"episode:{label}"
    causal_id = f"causal:{label}"
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            turn_id,
            session_id,
            "gabriel",
            ordinal,
            time.time(),
            "user",
            f"validation {label}",
            "[]",
            "[]",
            json.dumps({"source": "validation-test"}),
        ),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id, causal_id


def _activate(db, session_id, generation, turn_id, episode_id, causal_id):
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )


def _finish_formation(db, *, turn_id, episode_id, causal_id):
    """Close candidate-formation provenance without creating method-utility reward."""
    outcome_hash = hashlib.sha256(f"{episode_id}:formation".encode()).hexdigest()
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, None, turn_id, outcome_hash, 0.0, 1, time.time()),
    )
    db.db.execute(
        "UPDATE workspace_episodes SET selected='respond',state='COMPLETED' WHERE episode_id=?",
        (episode_id,),
    )


def _finish_external(db, *, session_id, generation, turn_id, episode_id, causal_id, status):
    effect_id = f"effect:{episode_id}"
    outcome_hash = hashlib.sha256(f"{episode_id}:{status}".encode()).hexdigest()
    credit = 1.0 if status == "VERIFIED" else 0.0
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            "gabriel",
            "entityos.exec",
            json.dumps({"audit": "test"}),
            None,
            generation,
            status,
            json.dumps({"audit": "test", "ok": status == "VERIFIED"}),
            time.time(),
            time.time(),
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, effect_id, turn_id, outcome_hash, credit, 1, time.time()),
    )
    db.db.execute(
        "UPDATE workspace_episodes SET selected='request_effect',state='COMPLETED' WHERE episode_id=?",
        (episode_id,),
    )
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))


def _candidate_record(episodes):
    return {
        "problem_signature": {"goal": ["verify"], "mechanism": ["causal", "provenance"]},
        "preconditions": ["canonical state is available"],
        "goal_shape": ["separate competing mechanisms"],
        "method_steps": ["enumerate alternatives", "test cheapest falsifier"],
        "invariants": ["evidence outranks analogy"],
        "expected_observations": ["one mechanism separates"],
        "falsifiers": ["structural preconditions fail"],
        "failure_modes": ["surface similarity hides causal mismatch"],
        "scope_limits": ["method does not create facts"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        # Deliberately caller-asserted nonsense: promotion statistics must ignore this.
        "support_count": 99,
        "success_count": 99,
        "failure_count": 0,
        "calibration": 0.99,
        "last_validated_at": 0.0,
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }


def _admit_candidate(db, episodes):
    return MethodMemory(db).admit(
        kind="framework_candidate",
        subject="effect-bound causal discriminator",
        record=_candidate_record(episodes),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "candidate-validation-test"},
    )


def _validated_candidate(db, session_id, generation):
    # Formation/provenance episodes are intentionally distinct from held-out validation.
    formation_a = _make_episode(db, session_id, generation, "formation-a", 1)
    formation_b = _make_episode(db, session_id, generation, "formation-b", 2)
    _finish_formation(db, turn_id=formation_a[0], episode_id=formation_a[1], causal_id=formation_a[2])
    _finish_formation(db, turn_id=formation_b[0], episode_id=formation_b[1], causal_id=formation_b[2])

    heldout_a = _make_episode(db, session_id, generation, "heldout-a", 3)
    heldout_b = _make_episode(db, session_id, generation, "heldout-b", 4)
    candidate_id = _admit_candidate(db, [formation_a[1], formation_b[1]])
    validator = CandidateValidation(db)
    use_ids = []
    for index, identity in enumerate((heldout_a, heldout_b)):
        turn_id, episode_id, causal_id = identity
        _activate(db, session_id, generation, turn_id, episode_id, causal_id)
        use_ids.append(
            validator.begin(
                candidate_memory_id=candidate_id,
                user_id="gabriel",
                session_id=session_id,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
                evidence_status="UNKNOWN",
                problem_signature={"goal": ["verify"], "mechanism": ["causal", "provenance"]},
                evaluation_mode="HELD_OUT",
                falsifier_checked=index == 1,
            )
        )
        _finish_external(
            db,
            session_id=session_id,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            status="VERIFIED",
        )
    validation_ids = [validator.finalize(candidate_use_receipt_id=rid) for rid in use_ids]
    return candidate_id, validation_ids


def test_effect_bound_validation_derives_counts_instead_of_trusting_candidate(tmp_path):
    db, session_id, generation = _db(tmp_path)
    candidate_id, validation_ids = _validated_candidate(db, session_id, generation)
    candidate_row = db.db.execute(
        "SELECT value FROM durable_memory WHERE memory_id=?",
        (candidate_id,),
    ).fetchone()
    stats = derive_promotion_stats(db.db, candidate_id, json.loads(candidate_row["value"]), "gabriel")
    assert stats["support_count"] == 2
    assert stats["success_count"] == 2
    assert stats["failure_count"] == 0
    assert stats["calibration"] == 1.0
    assert stats["validation_receipt_ids"] == validation_ids
    assert len(stats["validation_evidence_sha256"]) == 64


def test_promotion_uses_derived_validation_stats_and_revalidates_on_read(tmp_path):
    db, session_id, generation = _db(tmp_path)
    candidate_id, validation_ids = _validated_candidate(db, session_id, generation)
    methods = MethodMemory(db)
    promoted = methods.promote(
        candidate_memory_id=candidate_id,
        evaluation="effect-bound held-out receipts authorize this promotion",
        user_id="gabriel",
        provenance={"source": "candidate-validation-test", "evaluator": "receipt-derived"},
    )
    method_row = db.db.execute(
        "SELECT value,provenance FROM durable_memory WHERE memory_id=?",
        (promoted["promoted_memory_id"],),
    ).fetchone()
    value = json.loads(method_row["value"])
    provenance = json.loads(method_row["provenance"])
    assert value["support_count"] == 2
    assert value["success_count"] == 2
    assert value["failure_count"] == 0
    assert value["calibration"] == 1.0
    assert provenance["validation_receipt_ids"] == validation_ids
    assert len(provenance["validation_evidence_sha256"]) == 64
    assert provenance["truth_authority"] is False
    assert provenance["effect_authority"] is False

    result = methods.retrieve(
        query="verify causal provenance",
        user_id="gabriel",
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["verify"], "mechanism": ["causal", "provenance"]},
    )
    assert [item["memory_id"] for item in result["methods"]] == [promoted["promoted_memory_id"]]
    assert result["factual_status_unchanged"] == "UNKNOWN"

    before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
    with pytest.raises(MethodRecordError, match="already has a promotion receipt"):
        methods.promote(
            candidate_memory_id=candidate_id,
            evaluation="duplicate promotion",
            user_id="gabriel",
            provenance={"source": "candidate-validation-test"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before


def test_normal_claude_completion_is_not_candidate_validation_reward(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _make_episode(db, session_id, generation, "a", 1)
    b = _make_episode(db, session_id, generation, "b", 2)
    candidate_id = _admit_candidate(db, [a[1], b[1]])
    validator = CandidateValidation(db)
    _activate(db, session_id, generation, *a)
    use_id = validator.begin(
        candidate_memory_id=candidate_id,
        user_id="gabriel",
        session_id=session_id,
        turn_id=a[0],
        episode_id=a[1],
        causal_id=a[2],
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["verify"]},
        evaluation_mode="SHADOW",
        falsifier_checked=False,
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (a[2], a[1], None, a[0], hashlib.sha256(b"claude").hexdigest(), 0.0, 1, time.time()),
    )
    db.db.execute("UPDATE workspace_episodes SET selected='respond',state='COMPLETED' WHERE episode_id=?", (a[1],))
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    with pytest.raises(MethodValidationError, match="no external causal effect outcome"):
        validator.finalize(candidate_use_receipt_id=use_id)


def test_validation_use_must_be_registered_on_exact_active_causal_identity(tmp_path):
    db, session_id, generation = _db(tmp_path)
    a = _make_episode(db, session_id, generation, "a", 1)
    b = _make_episode(db, session_id, generation, "b", 2)
    candidate_id = _admit_candidate(db, [a[1], b[1]])
    _activate(db, session_id, generation, *a)
    with pytest.raises(MethodValidationError, match="exact active causal instance"):
        CandidateValidation(db).begin(
            candidate_memory_id=candidate_id,
            user_id="gabriel",
            session_id=session_id,
            turn_id=a[0],
            episode_id=a[1],
            causal_id="causal:forged",
            generation=generation,
            evidence_status="UNKNOWN",
            problem_signature={"goal": ["verify"]},
            evaluation_mode="HELD_OUT",
            falsifier_checked=True,
        )
