from __future__ import annotations

import json
import time
import uuid

import pytest

from clayverse.effect_journal import EffectIntent, EffectJournal
from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.method_validation import MethodValidationAuthority, MethodValidationError
from clayverse.store import UnifiedDB


SIGNATURE = {"goal": ["recover"], "mechanism": ["causal", "stateful"]}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gs = db.ensure_session("gabriel", "clayverse-gabriel")
    ans = db.ensure_session("andreas", "clayverse-andreas")
    return db, gs, ans


def _terminal_source_episode(db, session_id, user_id, episode_id):
    turn_id = db.append_turn(session_id, user_id, "user", f"source {episode_id}")
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", "respond", "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        ("source-causal:" + uuid.uuid4().hex, episode_id, None, turn_id, "source-outcome", 0.0, 1, time.time()),
    )
    return turn_id


def _candidate(db, session_id):
    _terminal_source_episode(db, session_id, "gabriel", "source:a")
    _terminal_source_episode(db, session_id, "gabriel", "source:b")
    record = {
        "problem_signature": SIGNATURE,
        "preconditions": ["canonical state is present"],
        "goal_shape": ["recover a valid path"],
        "method_steps": ["freeze identity", "compare causal outcome"],
        "invariants": ["method utility is not factual truth"],
        "expected_observations": ["verified task outcome changes under the method"],
        "falsifiers": ["verified task outcome is negative"],
        "failure_modes": ["surface analogy without utility"],
        "scope_limits": ["do not infer facts from method success"],
        "source_episode_ids": ["source:a", "source:b"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        # Deliberately caller-inflated proposal values. Promotion must ignore them.
        "support_count": 100,
        "success_count": 100,
        "failure_count": 0,
        "calibration": 0.99,
        "last_validated_at": time.time(),
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }
    return MethodMemory(db).admit(
        kind="framework_candidate",
        subject="causal recovery method",
        record=record,
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test-abstraction"},
    )


def _active_validation_turn(db, session_id, label):
    turn_id = db.append_turn(session_id, "gabriel", "user", f"validation {label}")
    episode_id = "validation-episode:" + uuid.uuid4().hex
    causal_id = "validation-causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.8, "[]", "request_effect", "SELECTED"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 1, time.time()),
    )
    return turn_id, episode_id, causal_id, generation


def _verified_validation(db, session_id, candidate_id, *, ok, label):
    turn_id, episode_id, causal_id, generation = _active_validation_turn(db, session_id, label)
    authority = MethodValidationAuthority(db)
    use_id = authority.begin_candidate_use(
        candidate_memory_id=candidate_id,
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )
    journal = EffectJournal(db)
    effect_id = journal.begin(
        EffectIntent(
            user_id="gabriel",
            session_id=session_id,
            episode_id=episode_id,
            capability="entityos.echo",
            target="validation",
            argv=None,
            generation=generation,
        )
    )
    journal.complete_verified(
        effect_id,
        outcome={"ok": bool(ok), "result": f"validation-{label}"},
        observation_turn_id=turn_id,
        causal_id=causal_id,
    )
    db.db.execute("UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=?", (episode_id,))
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    result_id = authority.finalize_verified_effect(
        use_receipt_id=use_id,
        effect_id=effect_id,
        user_id="gabriel",
        session_id=session_id,
        generation=generation,
    )
    return result_id, causal_id, episode_id


def test_terminal_causal_sources_and_inflated_candidate_counters_do_not_authorize_promotion(tmp_path):
    db, session_id, _ = _db(tmp_path)
    candidate_id = _candidate(db, session_id)
    with pytest.raises(MethodRecordError, match="at least two distinct validated method uses"):
        MethodMemory(db).promote(
            candidate_memory_id=candidate_id,
            evaluation="caller claims candidate worked",
            user_id="gabriel",
            provenance={"source": "test"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == 0


def test_normal_completion_like_reentry_without_verified_effect_cannot_create_method_utility(tmp_path):
    db, session_id, _ = _db(tmp_path)
    candidate_id = _candidate(db, session_id)
    turn_id, episode_id, causal_id, generation = _active_validation_turn(db, session_id, "completion-only")
    use_id = MethodValidationAuthority(db).begin_candidate_use(
        candidate_memory_id=candidate_id,
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (causal_id, episode_id, None, turn_id, "completion-only", 0.0, 1, time.time()),
    )
    db.db.execute("UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=?", (episode_id,))
    db.db.execute("DELETE FROM active_turns WHERE session_id=?", (session_id,))
    assert use_id
    assert MethodValidationAuthority(db).aggregate(candidate_memory_id=candidate_id, user_id="gabriel")["support_count"] == 0
    with pytest.raises(MethodRecordError, match="at least two distinct validated method uses"):
        MethodMemory(db).promote(
            candidate_memory_id=candidate_id,
            evaluation="normal completion is not reward",
            user_id="gabriel",
            provenance={"source": "test"},
        )


def test_two_distinct_verified_effect_outcomes_derive_promotion_counts_and_calibration(tmp_path):
    db, session_id, _ = _db(tmp_path)
    candidate_id = _candidate(db, session_id)
    positive_id, positive_causal, positive_episode = _verified_validation(db, session_id, candidate_id, ok=True, label="positive")
    negative_id, negative_causal, negative_episode = _verified_validation(db, session_id, candidate_id, ok=False, label="negative")

    aggregate = MethodValidationAuthority(db).promotion_aggregate(candidate_memory_id=candidate_id, user_id="gabriel")
    assert aggregate["validation_receipt_ids"] == [positive_id, negative_id]
    assert aggregate["validation_causal_ids"] == [positive_causal, negative_causal]
    assert aggregate["validation_episode_ids"] == [positive_episode, negative_episode]
    assert aggregate["support_count"] == 2
    assert aggregate["success_count"] == 1
    assert aggregate["failure_count"] == 1
    assert aggregate["calibration"] == 0.5

    promoted = MethodMemory(db).promote(
        candidate_memory_id=candidate_id,
        evaluation="two objective task outcomes",
        user_id="gabriel",
        provenance={"source": "test-promotion"},
    )
    row = db.db.execute("SELECT value,provenance FROM durable_memory WHERE memory_id=?", (promoted["promoted_memory_id"],)).fetchone()
    record = json.loads(row["value"])
    provenance = json.loads(row["provenance"])
    assert record["support_count"] == 2
    assert record["success_count"] == 1
    assert record["failure_count"] == 1
    assert record["calibration"] == 0.5
    assert record["last_validated_at"] == aggregate["last_validated_at"]
    assert provenance["validation_receipt_ids"] == [positive_id, negative_id]

    receipt_row = db.db.execute("SELECT value FROM durable_memory WHERE memory_id=?", (promoted["receipt_memory_id"],)).fetchone()
    receipt = json.loads(receipt_row["value"])
    assert receipt["validation_receipt_ids"] == [positive_id, negative_id]
    assert receipt["derived_support_count"] == 2
    assert receipt["derived_success_count"] == 1
    assert receipt["derived_failure_count"] == 1
    assert receipt["derived_calibration"] == 0.5
    assert receipt["validation_signal_class"] == "VERIFIED_EFFECT_OUTCOME"


def test_replaying_same_validation_causal_instance_does_not_increase_support(tmp_path):
    db, session_id, _ = _db(tmp_path)
    candidate_id = _candidate(db, session_id)
    result_id, _, _ = _verified_validation(db, session_id, candidate_id, ok=True, label="one")
    aggregate = MethodValidationAuthority(db).aggregate(candidate_memory_id=candidate_id, user_id="gabriel")
    assert aggregate["validation_receipt_ids"] == [result_id]
    assert aggregate["support_count"] == 1
    with pytest.raises(MethodRecordError, match="at least two distinct validated method uses"):
        MethodMemory(db).promote(
            candidate_memory_id=candidate_id,
            evaluation="duplicate cannot inflate support",
            user_id="gabriel",
            provenance={"source": "test"},
        )


def test_cross_user_candidate_use_is_denied(tmp_path):
    db, session_id, andreas_session = _db(tmp_path)
    candidate_id = _candidate(db, session_id)
    turn_id = db.append_turn(andreas_session, "andreas", "user", "foreign validation")
    episode_id = "foreign:" + uuid.uuid4().hex
    causal_id = "foreign-causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, andreas_session, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (andreas_session, "andreas", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    with pytest.raises(MethodValidationError, match="crosses user scope"):
        MethodValidationAuthority(db).begin_candidate_use(
            candidate_memory_id=candidate_id,
            user_id="andreas",
            session_id=andreas_session,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )


def test_tampering_validation_result_revokes_promoted_method_at_read_time(tmp_path):
    db, session_id, _ = _db(tmp_path)
    candidate_id = _candidate(db, session_id)
    positive_id, _, _ = _verified_validation(db, session_id, candidate_id, ok=True, label="positive")
    _verified_validation(db, session_id, candidate_id, ok=True, label="second")
    promoted = MethodMemory(db).promote(
        candidate_memory_id=candidate_id,
        evaluation="two verified positives",
        user_id="gabriel",
        provenance={"source": "test"},
    )
    assert promoted["promoted_memory_id"]

    row = db.db.execute("SELECT value FROM durable_memory WHERE memory_id=?", (positive_id,)).fetchone()
    payload = json.loads(row["value"])
    payload["utility"] = 0
    db.db.execute("UPDATE durable_memory SET value=? WHERE memory_id=?", (json.dumps(payload, sort_keys=True), positive_id))

    with pytest.raises(MethodRecordError, match="validation utility drifted"):
        MethodMemory(db).retrieve(
            query="recover state",
            user_id="gabriel",
            evidence_status="UNKNOWN",
            problem_signature=SIGNATURE,
        )
