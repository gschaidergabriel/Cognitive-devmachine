from __future__ import annotations

import json
import time
import uuid

import pytest

from clayverse.method_memory import (
    PROMOTION_RECEIPT_SCHEMA,
    MethodMemory,
    MethodRecordError,
    validate_method_receipt,
    validate_method_record,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    sid = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, sid


def _episode(db, sid, episode_id, *, state="COMPLETED", reentered=True):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, sid, time.time(), None, 0.5, "[]", "respond", state),
    )
    if reentered:
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "causal:" + uuid.uuid4().hex,
                episode_id,
                None,
                None,
                "outcome:" + episode_id,
                1.0,
                1,
                time.time(),
            ),
        )


def _record(episodes, support_ids, *, status="CANDIDATE"):
    return {
        "problem_signature": {"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
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
        "support_count": len(episodes),
        "success_count": len(episodes),
        "failure_count": 0,
        "calibration": 0.8,
        "last_validated_at": time.time(),
        "status": status,
        "limits_method_ids": [],
    }


def _candidate(db, sid, *, source_state="COMPLETED", source_reentered=True):
    episodes = ["src:a", "src:b"]
    for episode_id in episodes:
        _episode(
            db,
            sid,
            episode_id,
            state=source_state,
            reentered=source_reentered,
        )
    support_ids = [
        db.add_memory("fact", "support", "a", None, "gabriel", {"source": "test"}),
        db.add_memory("fact", "support", "b", None, "gabriel", {"source": "test"}),
    ]
    candidate_id = MethodMemory(db).admit(
        kind="framework_candidate",
        subject="causal recovery discriminator",
        record=_record(episodes, support_ids),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "lineage-regression"},
    )
    return candidate_id


def _promote(db, candidate_id):
    return MethodMemory(db).promote(
        candidate_memory_id=candidate_id,
        evaluation="terminal causally re-entered source episodes support the bounded method",
        user_id="gabriel",
        provenance={"source": "lineage-regression"},
    )


def test_promotion_receipt_binds_candidate_and_exact_promoted_memory_id(tmp_path):
    db, sid = _db(tmp_path)
    candidate_id = _candidate(db, sid)
    result = _promote(db, candidate_id)

    receipt_row = db.db.execute(
        "SELECT * FROM durable_memory WHERE memory_id=?",
        (result["receipt_memory_id"],),
    ).fetchone()
    promoted_row = db.db.execute(
        "SELECT * FROM durable_memory WHERE memory_id=?",
        (result["promoted_memory_id"],),
    ).fetchone()
    receipt = json.loads(receipt_row["value"])
    receipt_provenance = json.loads(receipt_row["provenance"])
    promoted_provenance = json.loads(promoted_row["provenance"])

    assert receipt["schema"] == PROMOTION_RECEIPT_SCHEMA
    assert receipt["candidate_memory_id"] == candidate_id
    assert receipt["promoted_memory_id"] == result["promoted_memory_id"]
    assert receipt_row["subject"] == f"promotion:{candidate_id}"
    assert receipt_provenance["promoted_memory_id"] == result["promoted_memory_id"]
    assert promoted_provenance["promotion_receipt_id"] == result["receipt_memory_id"]

    retrieved = MethodMemory(db).retrieve(
        query="recover state provenance",
        user_id="gabriel",
        evidence_status="UNKNOWN",
        problem_signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
    )
    assert [item["memory_id"] for item in retrieved["methods"]] == [result["promoted_memory_id"]]
    assert retrieved["factual_status_unchanged"] == "UNKNOWN"


def test_promotion_fails_without_terminal_causal_reentry_and_writes_nothing(tmp_path):
    db, sid = _db(tmp_path)
    candidate_id = _candidate(db, sid, source_state="OPEN", source_reentered=False)
    before = db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework')"
    ).fetchone()[0]
    with pytest.raises(MethodRecordError, match="terminal and causally re-entered"):
        _promote(db, candidate_id)
    after = db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework')"
    ).fetchone()[0]
    assert after == before


def test_duplicate_promotion_and_receipt_reuse_fail_closed(tmp_path):
    db, sid = _db(tmp_path)
    candidate_id = _candidate(db, sid)
    result = _promote(db, candidate_id)
    with pytest.raises(MethodRecordError, match="already has a promotion receipt"):
        _promote(db, candidate_id)

    original = db.db.execute(
        "SELECT * FROM durable_memory WHERE memory_id=?",
        (result["promoted_memory_id"],),
    ).fetchone()
    forged_id = db.add_memory(
        "framework",
        original["subject"],
        original["value"],
        original["source_turn_id"],
        "gabriel",
        json.loads(original["provenance"]),
    )
    assert forged_id != result["promoted_memory_id"]
    with pytest.raises(MethodRecordError, match="promotion receipt provenance mismatch"):
        MethodMemory(db).retrieve(
            query="recover state provenance",
            user_id="gabriel",
            evidence_status="UNKNOWN",
            problem_signature={"goal": ["recover"], "mechanism": ["stateful", "provenance"]},
        )


def test_user_scoped_candidate_cannot_reference_unscoped_global_memory(tmp_path):
    db, sid = _db(tmp_path)
    _episode(db, sid, "src:a")
    _episode(db, sid, "src:b")
    global_support = db.add_memory("fact", "global", "unadmitted", None, None, {"source": "test"})
    own_support = db.add_memory("fact", "own", "admitted", None, "gabriel", {"source": "test"})
    with pytest.raises(MethodRecordError, match="exact user scope"):
        MethodMemory(db).admit(
            kind="framework_candidate",
            subject="unsafe global-reference candidate",
            record=_record(["src:a", "src:b"], [global_support, own_support]),
            source_turn_id=None,
            user_id="gabriel",
            provenance={"source": "lineage-regression"},
        )


def test_nonfinite_method_or_receipt_values_fail_closed():
    record = _record(["src:a", "src:b"], ["support:a", "support:b"], status="PROMOTED")
    record["last_validated_at"] = float("nan")
    with pytest.raises(MethodRecordError, match="last_validated_at"):
        validate_method_record("framework", record)

    with pytest.raises(MethodRecordError, match="method receipt ts"):
        validate_method_receipt({
            "schema": PROMOTION_RECEIPT_SCHEMA,
            "candidate_memory_id": "candidate",
            "promoted_memory_id": "promoted",
            "action": "PROMOTE",
            "source_episode_ids": ["src:a", "src:b"],
            "supporting_memory_ids": [],
            "counterexample_memory_ids": [],
            "evaluation": "bounded",
            "ts": float("nan"),
        })
