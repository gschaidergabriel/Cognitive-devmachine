import json
import time

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.retrieval import WorldAssembler
from clayverse.store import StaleGeneration, UnifiedDB


def candidate_record():
    return {
        "problem_signature": {
            "goal": ["orchid causal mechanism"],
            "constraint_shape": ["partial observability"],
            "evidence_shape": ["competing explanations"],
        },
        "preconditions": ["two plausible mechanisms remain"],
        "goal_shape": "separate orchid mechanisms",
        "method_steps": ["compare orchid predictions"],
        "invariants": ["method is not a fact"],
        "expected_observations": ["one orchid mechanism loses support"],
        "falsifiers": ["both mechanisms predict the same observation"],
        "failure_modes": ["surface-word match without structural fit"],
        "scope_limits": ["requires competing mechanisms"],
        "source_episode_ids": ["episode:method-source"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        "support_count": 1,
        "success_count": 1,
        "failure_count": 0,
        "calibration": 0.5,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clay-gabriel")
    return db, session_id


def _retrieval_identity(db, session_id, query="orchid mechanism"):
    turn_id = db.append_turn(session_id, "gabriel", "user", query)
    episode_id = "episode:test"
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "ACTIVE"),
    )
    return {
        "query": query,
        "user_id": "gabriel",
        "session_id": session_id,
        "turn_id": turn_id,
        "episode_id": episode_id,
        "causal_id": "causal:test",
        "generation": db.entity_generation(),
    }


def test_stage_a_microclay_excludes_method_memory_even_on_strong_lexical_match(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        method_id = db.add_method_memory(
            "framework_candidate",
            "method:orchid",
            candidate_record(),
            None,
            "gabriel",
            {"source": "episode_abstraction"},
        )
        fact_id = db.add_memory(
            "fact", "topic:orchid", "orchid mechanism evidence", None, "gabriel", {"source": "test"}
        )
        result = MicroClayRetrieval(db).retrieve(**_retrieval_identity(db, session_id))
        selected = {item["memory_id"] for item in result["items"]}
        assert fact_id in selected
        assert method_id not in selected
        assert all(item["kind"] != "framework_candidate" for item in result["items"])
        assert result["receipt"]["candidate_count"] == 1
    finally:
        db.close()


def test_legacy_world_assembly_excludes_method_memory(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        method_id = db.add_method_memory(
            "framework_candidate", "method:orchid", candidate_record(), None, "gabriel", {"source": "test"}
        )
        fact_id = db.add_memory(
            "fact", "topic:orchid", "orchid factual evidence", None, "gabriel", {"source": "test"}
        )
        context = WorldAssembler(db).assemble(session_id, [])
        ids = {item["memory_id"] for item in context["durable_memory"]}
        assert fact_id in ids
        assert method_id not in ids
        assert context["retrieval_receipt"]["mode"] == "LEGACY_COMPATIBILITY"
    finally:
        db.close()


def test_tainted_retrieval_receipt_cannot_replay_method_as_fact(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        method_id = db.add_method_memory(
            "framework_candidate", "method:orchid", candidate_record(), None, "gabriel", {"source": "test"}
        )
        db.add_memory("fact", "topic:orchid", "orchid evidence", None, "gabriel", {"source": "test"})
        identity = _retrieval_identity(db, session_id)
        organ = MicroClayRetrieval(db)
        organ.retrieve(**identity)
        db.db.execute(
            "UPDATE retrieval_episodes SET selected_memory_ids=? WHERE causal_id=?",
            (json.dumps([method_id]), identity["causal_id"]),
        )
        with pytest.raises(StaleGeneration, match="retrieval_epistemic_partition"):
            organ.retrieve(**identity)
    finally:
        db.close()


def test_tainted_retrieval_receipt_cannot_train_fact_policy(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        method_id = db.add_method_memory(
            "framework_candidate", "method:orchid", candidate_record(), None, "gabriel", {"source": "test"}
        )
        db.add_memory("fact", "topic:orchid", "orchid evidence", None, "gabriel", {"source": "test"})
        identity = _retrieval_identity(db, session_id)
        organ = MicroClayRetrieval(db)
        organ.retrieve(**identity)
        db.db.execute(
            "UPDATE retrieval_episodes SET selected_memory_ids=? WHERE causal_id=?",
            (json.dumps([method_id]), identity["causal_id"]),
        )
        before = db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0]
        with pytest.raises(StaleGeneration, match="retrieval_epistemic_partition"):
            organ.credit(
                causal_id=identity["causal_id"],
                generation=identity["generation"],
                credit=1.0,
                signal_class="regression",
            )
        after = db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0]
        assert after == before
    finally:
        db.close()
