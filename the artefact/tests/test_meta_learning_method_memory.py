from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError
from clayverse.method_stage_b import StageBMethodRetrieval
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gs = db.ensure_session("gabriel", "clayverse-gabriel")
    ans = db.ensure_session("andreas", "clayverse-andreas")
    return db, gs, ans


def _episode(db, session_id, episode_id):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", "respond", "COMPLETED"),
    )


def _active(db, user_id, session_id, prompt="novel unresolved problem"):
    turn_id = db.append_turn(session_id, user_id, "user", prompt)
    episode_id = "active:" + uuid.uuid4().hex
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, user_id, turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    return turn_id, episode_id, causal_id, generation


def _record(*, signature, episodes, support_ids, status="PROMOTED", calibration=0.8, limits=None):
    support_count = max(2 if status == "PROMOTED" else 1, len(episodes))
    return {
        "problem_signature": signature,
        "preconditions": ["canonical state is available"],
        "goal_shape": ["restore a valid decision path"],
        "method_steps": ["enumerate alternatives", "derive discriminator", "test cheapest falsifier"],
        "invariants": ["evidence outranks analogy"],
        "expected_observations": ["one mechanism separates under intervention"],
        "falsifiers": ["structural preconditions do not hold"],
        "failure_modes": ["surface similarity hides different causal structure"],
        "scope_limits": ["do not infer facts from the method"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": list(support_ids),
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        "support_count": support_count,
        "success_count": support_count,
        "failure_count": 0,
        "calibration": calibration,
        "last_validated_at": time.time(),
        "status": status,
        "limits_method_ids": list(limits or []),
    }


def _support(db, user_id="gabriel"):
    a = db.add_memory("fact", "test", "support-a", None, user_id, {"source": "test"})
    b = db.add_memory("fact", "test", "support-b", None, user_id, {"source": "test"})
    return [a, b]


def test_promoted_method_rejects_single_episode(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:one")
    support = _support(db)
    record = _record(
        signature={"goal": ["recover"], "mechanism": ["stateful"]},
        episodes=["src:one"],
        support_ids=support,
    )
    record["support_count"] = 1
    record["success_count"] = 1
    with pytest.raises(MethodRecordError, match="single-episode promotion"):
        MethodMemory(db).admit(
            kind="framework",
            subject="recovery discriminator",
            record=record,
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "test"},
        )


def test_stage_a_never_serves_method_memory(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:a")
    _episode(db, gs, "src:b")
    support = _support(db)
    MethodMemory(db).admit(
        kind="framework",
        subject="rareword method",
        record=_record(
            signature={"goal": ["verify"], "mechanism": ["provenance"]},
            episodes=["src:a", "src:b"],
            support_ids=support,
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test"},
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs, "rareword")
    result = MicroClayRetrieval(db).retrieve(
        query="rareword",
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )
    assert all(item["kind"] not in {"framework", "heuristic", "failure_pattern", "counterexample"} for item in result["items"])


def test_unknown_fact_can_return_method_without_becoming_present(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:a")
    _episode(db, gs, "src:b")
    support = _support(db)
    method_id = MethodMemory(db).admit(
        kind="framework",
        subject="causal recovery framework",
        record=_record(
            signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
            episodes=["src:a", "src:b"],
            support_ids=support,
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test"},
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    result = StageBMethodRetrieval(db).retrieve(
        query="what should we do next?",
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
    )
    assert [x["memory_id"] for x in result["methods"]] == [method_id]
    assert result["receipt"]["evidence_status"] == "UNKNOWN"
    assert result["receipt"]["factual_status_unchanged"] == "UNKNOWN"
    assert result["receipt"]["truth_authority"] is False


def test_unusual_structural_lexical_decoy_inversion(tmp_path):
    """Single bounded GO experiment: lexical decoy must lose to structural match."""
    db, gs, _ = _db(tmp_path)
    for eid in ("src:a", "src:b", "src:c", "src:d"):
        _episode(db, gs, eid)
    support = _support(db)
    methods = MethodMemory(db)
    correct = methods.admit(
        kind="framework",
        subject="orthogonal transfer pattern",
        record=_record(
            signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
            episodes=["src:a", "src:b"],
            support_ids=support,
            calibration=0.7,
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "unusual-experiment"},
    )
    decoy = methods.admit(
        kind="framework",
        subject="recover state provenance recovery state provenance",
        record=_record(
            signature={"goal": ["compare"], "mechanism": ["privacy"]},
            episodes=["src:c", "src:d"],
            support_ids=support,
            calibration=0.99,
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "unusual-experiment"},
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs, "recover state provenance")
    result = StageBMethodRetrieval(db).retrieve(
        query="recover state provenance",
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
    )
    ids = [x["memory_id"] for x in result["methods"]]
    assert correct in ids
    assert decoy not in ids


def test_counterexample_can_block_promoted_method(tmp_path):
    db, gs, _ = _db(tmp_path)
    for eid in ("src:a", "src:b", "src:c"):
        _episode(db, gs, eid)
    support = _support(db)
    methods = MethodMemory(db)
    target = methods.admit(
        kind="framework",
        subject="bounded recovery",
        record=_record(
            signature={"goal": ["recover"], "mechanism": ["stateful"]},
            episodes=["src:a", "src:b"],
            support_ids=support,
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test"},
    )
    methods.admit(
        kind="counterexample",
        subject="recovery counterexample",
        record=_record(
            signature={"goal": ["recover"], "mechanism": ["stateful"]},
            episodes=["src:c"],
            support_ids=support,
            limits=[target],
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "test"},
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    result = StageBMethodRetrieval(db).retrieve(
        query="recovery strategy",
        user_id="gabriel",
        session_id=gs,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["recover"], "mechanism": ["stateful"]},
    )
    assert target not in [x["memory_id"] for x in result["methods"]]
    assert result["counterevidence"]


def test_malformed_promoted_record_fails_closed(tmp_path):
    db, gs, _ = _db(tmp_path)
    db.add_memory("framework", "broken", "{}", None, "gabriel", {"source": "corrupt-test"})
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    with pytest.raises(MethodRecordError, match="missing method fields"):
        StageBMethodRetrieval(db).retrieve(
            query="strategy",
            user_id="gabriel",
            session_id=gs,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
            evidence_status="UNKNOWN",
            problem_signature={"goal": ["recover"], "mechanism": ["stateful"]},
        )
