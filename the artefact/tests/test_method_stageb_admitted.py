import time
import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import MethodMemoryManager
from clayverse.method_stageb import (
    AdmittedMethodRetriever,
    ProblemSignatureAdmissionError,
    QUERY_SCHEMA,
    admit_problem_query,
)
from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db, "session:gabriel"


def _episode(db, session_id, label, *, terminal=False):
    user_id = str(db.db.execute("SELECT user_id FROM sessions WHERE session_id=?", (session_id,)).fetchone()[0])
    turn_id = db.append_turn(session_id, user_id, "user", label)
    episode_id = str(uuid.uuid4())
    state = "COMPLETED" if terminal else "OPEN"
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, state),
    )
    if terminal:
        db.db.execute(
            "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), episode_id, None, turn_id, "test-outcome", 1.0, 1, time.time()),
        )
    return turn_id, episode_id


def _record(*, signature, goal_shape, episodes, counterexample_ids=(), status="CANDIDATE"):
    return {
        "problem_signature": signature,
        "preconditions": ["bounded_input"],
        "goal_shape": goal_shape,
        "method_steps": ["generate_competing_mechanisms", "run_discriminator"],
        "invariants": ["facts_remain_evidence_bound"],
        "expected_observations": ["mechanisms_separate_under_test"],
        "falsifiers": ["discriminator_does_not_separate"],
        "failure_modes": ["proxy_match"],
        "scope_limits": ["method_guidance_only"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": list(counterexample_ids),
        "abstraction_version": "v1",
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.75,
        "last_validated_at": None if status == "CANDIDATE" else time.time(),
        "status": status,
    }


def _query(*, turn_id, episode_id, causal_id, generation, signature=None, goal_shape="identify_mechanism", source="structural_analyzer_v1"):
    return {
        "schema": QUERY_SCHEMA,
        "problem_signature": signature or {
            "task_shape": ["diagnose"],
            "evidence_state": ["unknown"],
            "validation_mode": ["falsifier"],
        },
        "goal_shape": goal_shape,
        "provenance": {
            "source": source,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": generation,
            "admission_version": 1,
        },
    }


def _promoted_method(db, session_id, *, signature=None, goal_shape="identify_mechanism", counterexample_ids=()):
    _, e1 = _episode(db, session_id, "source case one", terminal=True)
    _, e2 = _episode(db, session_id, "source case two", terminal=True)
    manager = MethodMemoryManager(db)
    candidate_id = manager.admit(
        "framework_candidate",
        "cross-domain mechanism discriminator",
        _record(
            signature=signature or {
                "task_shape": ["diagnose"],
                "evidence_state": ["unknown"],
                "validation_mode": ["falsifier"],
            },
            goal_shape=goal_shape,
            episodes=[e1, e2],
            counterexample_ids=counterexample_ids,
        ),
        None,
        "gabriel",
        {"source": "stageb-test"},
    )
    promoted = manager.promote(
        candidate_id,
        evaluation="two independent terminal causal episodes support transfer",
        provenance={"source": "stageb-test-promotion"},
    )
    return promoted["promoted_memory_id"]


def test_raw_prompt_is_not_an_admitted_stageb_query():
    with pytest.raises(ProblemSignatureAdmissionError):
        admit_problem_query("why did the server crash and how do I debug it")

    with pytest.raises(ProblemSignatureAdmissionError, match="structural token"):
        admit_problem_query({
            "schema": QUERY_SCHEMA,
            "problem_signature": {"task_shape": ["why did the server crash hard"]},
            "goal_shape": "identify_mechanism",
            "provenance": {
                "source": "structural_analyzer_v1",
                "turn_id": "t",
                "episode_id": "e",
                "causal_id": "c",
                "generation": 1,
                "admission_version": 1,
            },
        })


def test_explicit_raw_query_source_is_rejected():
    with pytest.raises(ProblemSignatureAdmissionError, match="raw-prompt"):
        admit_problem_query({
            "schema": QUERY_SCHEMA,
            "problem_signature": {"task_shape": ["diagnose"]},
            "goal_shape": "identify_mechanism",
            "provenance": {
                "source": "raw_query",
                "turn_id": "t",
                "episode_id": "e",
                "causal_id": "c",
                "generation": 1,
                "admission_version": 1,
            },
        })


def test_admitted_query_digest_is_canonical_and_content_sensitive():
    base = _query(turn_id="turn", episode_id="episode", causal_id="causal", generation=3)
    same_reordered = {
        "goal_shape": base["goal_shape"],
        "provenance": dict(reversed(list(base["provenance"].items()))),
        "problem_signature": dict(reversed(list(base["problem_signature"].items()))),
        "schema": base["schema"],
    }
    first = admit_problem_query(base)
    second = admit_problem_query(same_reordered)
    changed = admit_problem_query(_query(
        turn_id="turn",
        episode_id="episode",
        causal_id="causal",
        generation=3,
        signature={
            "task_shape": ["compare"],
            "evidence_state": ["unknown"],
            "validation_mode": ["falsifier"],
        },
    ))
    assert first.query_sha256 == second.query_sha256
    assert first.query_sha256 != changed.query_sha256
    assert len(first.receipt()["query_sha256"]) == 64


def test_admitted_structural_query_selects_promoted_method_and_preserves_fact_unknown(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        promoted_id = _promoted_method(db, session_id)
        turn_id, episode_id = _episode(db, session_id, "novel target case")
        causal_id = str(uuid.uuid4())
        generation = db.entity_generation()
        query = _query(
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        result = AdmittedMethodRetriever(db).retrieve(
            problem_query=query,
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
            fact_status="UNKNOWN",
        )
        assert [item["memory_id"] for item in result["items"]] == [promoted_id]
        assert result["receipt"]["fact_status"] == "UNKNOWN"
        assert result["receipt"]["fact_status_unchanged"] is True
        assert result["receipt"]["truth_authority"] is False
        assert result["receipt"]["effect_authority"] is False
        assert result["receipt"]["route"] == "method_structural_admitted"
        assert result["receipt"]["query_sha256"] == admit_problem_query(query).query_sha256
        assert result["query_receipt"]["query_sha256"] == result["receipt"]["query_sha256"]
    finally:
        db.close()


def test_structurally_wrong_high_calibration_method_does_not_match(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        right = _promoted_method(db, session_id)
        wrong = _promoted_method(
            db,
            session_id,
            signature={
                "task_shape": ["optimize"],
                "evidence_state": ["known"],
                "validation_mode": ["benchmark"],
            },
            goal_shape="maximize_throughput",
        )
        turn_id, episode_id = _episode(db, session_id, "target")
        causal_id = str(uuid.uuid4())
        generation = db.entity_generation()
        result = AdmittedMethodRetriever(db).retrieve(
            problem_query=_query(
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
            ),
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
            fact_status="UNKNOWN",
        )
        ids = [item["memory_id"] for item in result["items"]]
        assert right in ids
        assert wrong not in ids
    finally:
        db.close()


def test_problem_query_is_bound_to_turn_episode_causal_identity_and_generation(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        _promoted_method(db, session_id)
        turn_id, episode_id = _episode(db, session_id, "target")
        causal_id = str(uuid.uuid4())
        generation = db.entity_generation()
        query = _query(
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        with pytest.raises(ProblemSignatureAdmissionError, match="causal identity"):
            AdmittedMethodRetriever(db).retrieve(
                problem_query=query,
                user_id="gabriel",
                session_id=session_id,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=str(uuid.uuid4()),
                generation=generation,
                fact_status="UNKNOWN",
            )
    finally:
        db.close()


def test_world_assembler_never_calls_raw_query_stageb_without_admitted_signature(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        turn_id, episode_id = _episode(db, session_id, "unfamiliar target")
        causal_id = str(uuid.uuid4())
        assembler = WorldAssembler(db)

        def forbidden_raw_stageb(**kwargs):
            raise AssertionError("raw-query Stage B must not be called")

        assembler.microclay.retrieve_methods = forbidden_raw_stageb
        world = assembler.assemble(
            session_id,
            [],
            query="why did this unfamiliar mechanism fail",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=db.entity_generation(),
        )
        assert world["method_context"] == []
        assert world["retrieval_receipt"]["method_route"] == "DEFERRED_NO_ADMITTED_SIGNATURE"
        assert world["retrieval_receipt"]["fact_status"] == "UNKNOWN"
        assert world["unknowns"][0]["status"] == "FACT_UNKNOWN"
    finally:
        db.close()


def test_world_assembler_accepts_only_admitted_structural_stageb(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        promoted_id = _promoted_method(db, session_id)
        turn_id, episode_id = _episode(db, session_id, "target")
        causal_id = str(uuid.uuid4())
        generation = db.entity_generation()
        query = _query(
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        world = WorldAssembler(db).assemble(
            session_id,
            [],
            query="opaque raw text is Stage A only",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
            method_query=query,
        )
        assert [item["memory_id"] for item in world["method_context"]] == [promoted_id]
        assert world["retrieval_receipt"]["method_route"] == "method_structural_admitted"
        assert world["retrieval_receipt"]["method_truth_authority"] is False
        assert world["retrieval_receipt"]["fact_status"] == "UNKNOWN"
        assert world["retrieval_receipt"]["method_query_sha256"] == admit_problem_query(query).query_sha256
    finally:
        db.close()
