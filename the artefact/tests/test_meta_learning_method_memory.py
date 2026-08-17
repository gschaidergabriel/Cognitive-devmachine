from __future__ import annotations

import json
import time
import uuid

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError, validate_method_record
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


def test_promoted_record_still_requires_cross_episode_support():
    record = _record(
        signature={"goal": ["recover"], "mechanism": ["stateful"]},
        episodes=["src:one"],
        support_ids=["support:a"],
    )
    record["support_count"] = 1
    record["success_count"] = 1
    with pytest.raises(MethodRecordError, match="single-episode promotion"):
        validate_method_record("framework", record)


def test_ordinary_admission_cannot_mint_promoted_framework(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:a")
    _episode(db, gs, "src:b")
    support = _support(db)
    with pytest.raises(MethodRecordError, match="dedicated promotion lifecycle"):
        MethodMemory(db).admit(
            kind="framework",
            subject="recovery discriminator",
            record=_record(
                signature={"goal": ["recover"], "mechanism": ["stateful"]},
                episodes=["src:a", "src:b"],
                support_ids=support,
            ),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "ordinary-admission"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == 0


def test_candidate_admission_remains_available_but_not_routable(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:a")
    support = _support(db)
    candidate_id = MethodMemory(db).admit(
        kind="framework_candidate",
        subject="candidate recovery discriminator",
        record=_record(
            signature={"goal": ["recover"], "mechanism": ["stateful"]},
            episodes=["src:a"],
            support_ids=support,
            status="CANDIDATE",
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "episode-abstraction"},
    )
    assert candidate_id
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
    assert result["methods"] == []
    assert result["receipt"]["factual_status_unchanged"] == "UNKNOWN"


def test_stage_a_never_serves_raw_method_kind_even_if_present(tmp_path):
    db, gs, _ = _db(tmp_path)
    # This deliberately bypasses MethodMemory admission to prove Stage A fences on kind
    # before any future promotion lifecycle exists.
    db.add_memory("framework", "rareword method", "{}", None, "gabriel", {"source": "raw-fixture"})
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
    assert all(
        item["kind"] not in {"framework", "heuristic", "failure_pattern", "counterexample"}
        for item in result["items"]
    )


def test_low_level_stage_b_requires_explicit_signature(tmp_path):
    db, _, _ = _db(tmp_path)
    with pytest.raises(MethodRecordError, match="explicit problem_signature required"):
        MethodMemory(db).retrieve(
            query="recover state provenance",
            user_id="gabriel",
            evidence_status="UNKNOWN",
            problem_signature=None,
        )


def test_forged_promoted_row_without_promotion_authority_fails_closed(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:a")
    _episode(db, gs, "src:b")
    support = _support(db)
    record = validate_method_record(
        "framework",
        _record(
            signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
            episodes=["src:a", "src:b"],
            support_ids=support,
        ),
    )
    # Simulate a row forged through the generic UnifiedDB surface. A PROMOTED status and
    # old method_memory:v1 admission label alone must not become routing authority.
    db.add_memory(
        "framework",
        "forged promoted framework",
        json.dumps(record, sort_keys=True, separators=(",", ":")),
        None,
        "gabriel",
        {
            "source": "forged-fixture",
            "method_schema_version": 1,
            "admission": "method_memory:v1",
            "user_scope": "gabriel",
            "truth_authority": False,
            "effect_authority": False,
        },
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    with pytest.raises(MethodRecordError, match="dedicated promotion authority"):
        StageBMethodRetrieval(db).retrieve(
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


@pytest.mark.skip(reason="distinct GO unusual experiment already raced/consumed in this macro-cycle")
def test_unusual_structural_lexical_decoy_inversion():
    """Historical proposed discriminator only; fenced from broad current-macrocycle pytest."""
    raise AssertionError("unusual experiment is fenced")


def test_counterexample_memory_can_be_admitted_without_granting_fact_authority(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "src:c")
    support = _support(db)
    counter_id = MethodMemory(db).admit(
        kind="counterexample",
        subject="recovery counterexample",
        record=_record(
            signature={"goal": ["recover"], "mechanism": ["stateful"]},
            episodes=["src:c"],
            support_ids=support,
        ),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "verified-negative-example"},
    )
    assert counter_id
    row = db.db.execute("SELECT provenance FROM durable_memory WHERE memory_id=?", (counter_id,)).fetchone()
    provenance = json.loads(row["provenance"])
    assert provenance["truth_authority"] is False
    assert provenance["effect_authority"] is False


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
