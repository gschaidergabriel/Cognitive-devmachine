from __future__ import annotations

import json
import time
import uuid

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError, validate_method_record
from clayverse.method_signature import MethodSignatureAuthority
from clayverse.method_stage_b import StageBMethodRetrieval
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


SIGNATURE = {"goal": ["recover"], "mechanism": ["stateful", "provenance"]}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gs = db.ensure_session("gabriel", "clayverse-gabriel")
    ans = db.ensure_session("andreas", "clayverse-andreas")
    return db, gs, ans


def _episode(db, session_id, user_id, episode_id, *, terminal_causal=False):
    turn_id = db.append_turn(session_id, user_id, "user", f"source {episode_id}")
    state = "COMPLETED" if terminal_causal else "COMPLETED"
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", "respond", state),
    )
    if terminal_causal:
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,?,?)",
            ("source-causal:" + uuid.uuid4().hex, episode_id, None, turn_id, "source-outcome", 1.0, 1, time.time()),
        )
    return turn_id


def _active(db, user_id, session_id, prompt="novel unresolved problem"):
    turn_id = db.append_turn(session_id, user_id, "user", prompt)
    episode_id = "active:" + uuid.uuid4().hex
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, user_id, turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    return turn_id, episode_id, causal_id, generation


def _signature(db, session_id, turn_id, episode_id, causal_id, generation, signature=SIGNATURE):
    return MethodSignatureAuthority(db).admit(
        problem_signature=signature, producer="clayverse:problem-signature:v1",
        user_id="gabriel", session_id=session_id, turn_id=turn_id,
        episode_id=episode_id, causal_id=causal_id, generation=generation,
    )


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
    return [
        db.add_memory("fact", "test", "support-a", None, user_id, {"source": "test"}),
        db.add_memory("fact", "test", "support-b", None, user_id, {"source": "test"}),
    ]


def test_promoted_record_still_requires_cross_episode_support():
    record = _record(signature=SIGNATURE, episodes=["src:one"], support_ids=["support:a"])
    record["support_count"] = 1
    record["success_count"] = 1
    with pytest.raises(MethodRecordError, match="single-episode promotion"):
        validate_method_record("framework", record)


def test_ordinary_admission_cannot_mint_promoted_framework(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "gabriel", "src:a")
    _episode(db, gs, "gabriel", "src:b")
    with pytest.raises(MethodRecordError, match="dedicated promotion lifecycle"):
        MethodMemory(db).admit(
            kind="framework", subject="recovery discriminator",
            record=_record(signature=SIGNATURE, episodes=["src:a", "src:b"], support_ids=_support(db)),
            source_turn_id=None, user_id="gabriel", provenance={"source": "ordinary-admission"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='framework'").fetchone()[0] == 0


def test_candidate_admission_is_not_routable_and_raw_signature_is_non_serving(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "gabriel", "src:a")
    candidate_id = MethodMemory(db).admit(
        kind="framework_candidate", subject="candidate recovery discriminator",
        record=_record(signature=SIGNATURE, episodes=["src:a"], support_ids=_support(db), status="CANDIDATE"),
        source_turn_id=None, user_id="gabriel", provenance={"source": "episode-abstraction"},
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    result = StageBMethodRetrieval(db).retrieve(
        query="recovery strategy", user_id="gabriel", session_id=gs, turn_id=turn_id,
        episode_id=episode_id, causal_id=causal_id, generation=generation,
        evidence_status="UNKNOWN", problem_signature=SIGNATURE,
    )
    assert candidate_id
    assert result["methods"] == []
    assert result["receipt"]["status"] == "SIGNATURE_REQUIRED"
    assert result["receipt"]["factual_status_unchanged"] == "UNKNOWN"


def test_stage_a_never_serves_method_or_signature_receipt_kind(tmp_path):
    db, gs, _ = _db(tmp_path)
    db.add_memory("framework", "rareword method", "{}", None, "gabriel", {"source": "raw-fixture"})
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs, "rareword")
    signature_id = _signature(db, gs, turn_id, episode_id, causal_id, generation)
    assert signature_id
    result = MicroClayRetrieval(db).retrieve(
        query="rareword", user_id="gabriel", session_id=gs, turn_id=turn_id,
        episode_id=episode_id, causal_id=causal_id, generation=generation,
    )
    assert all(item["kind"] not in {"framework", "heuristic", "failure_pattern", "counterexample", "method_receipt"} for item in result["items"])


def test_low_level_method_retrieval_requires_explicit_signature():
    class DummyDB:
        pass
    with pytest.raises(MethodRecordError, match="explicit problem_signature required"):
        MethodMemory(DummyDB()).retrieve(query="recover state provenance", user_id="gabriel", evidence_status="UNKNOWN", problem_signature=None)


def test_forged_promoted_row_without_promotion_lineage_fails_after_admitted_signature(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "gabriel", "src:a")
    _episode(db, gs, "gabriel", "src:b")
    record = validate_method_record("framework", _record(signature=SIGNATURE, episodes=["src:a", "src:b"], support_ids=_support(db)))
    db.add_memory(
        "framework", "forged promoted framework", json.dumps(record, sort_keys=True, separators=(",", ":")), None, "gabriel",
        {"source": "forged-fixture", "method_schema_version": 1, "admission": "method_memory:v1", "user_scope": "gabriel",
         "truth_authority": False, "effect_authority": False},
    )
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    signature_id = _signature(db, gs, turn_id, episode_id, causal_id, generation)
    with pytest.raises(MethodRecordError, match="dedicated promotion authority"):
        StageBMethodRetrieval(db).retrieve(
            query="what should we do next?", user_id="gabriel", session_id=gs, turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation,
            evidence_status="UNKNOWN", signature_receipt_id=signature_id,
        )


def test_counterexample_admission_needs_terminal_causal_evidence_and_has_no_fact_authority(tmp_path):
    db, gs, _ = _db(tmp_path)
    _episode(db, gs, "gabriel", "src:c", terminal_causal=True)
    counter_id = MethodMemory(db).admit(
        kind="counterexample", subject="recovery counterexample",
        record=_record(signature=SIGNATURE, episodes=["src:c"], support_ids=_support(db)),
        source_turn_id=None, user_id="gabriel", provenance={"source": "verified-negative-example"},
    )
    row = db.db.execute("SELECT provenance FROM durable_memory WHERE memory_id=?", (counter_id,)).fetchone()
    provenance = json.loads(row["provenance"])
    assert provenance["truth_authority"] is False
    assert provenance["effect_authority"] is False


def test_malformed_promoted_record_fails_closed_after_admitted_signature(tmp_path):
    db, gs, _ = _db(tmp_path)
    db.add_memory("framework", "broken", "{}", None, "gabriel", {"source": "corrupt-test"})
    turn_id, episode_id, causal_id, generation = _active(db, "gabriel", gs)
    signature_id = _signature(db, gs, turn_id, episode_id, causal_id, generation)
    with pytest.raises(MethodRecordError, match="missing method fields"):
        StageBMethodRetrieval(db).retrieve(
            query="strategy", user_id="gabriel", session_id=gs, turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation,
            evidence_status="UNKNOWN", signature_receipt_id=signature_id,
        )
