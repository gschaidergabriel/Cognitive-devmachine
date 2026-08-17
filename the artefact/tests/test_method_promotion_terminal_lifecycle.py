from __future__ import annotations

import json
import time

import pytest

from clayverse.method_memory import MethodMemory, MethodRecordError, validate_method_record
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    return db, session_id


def _episode(db, session_id, episode_id, *, state="COMPLETED", reentered=True):
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), None, 0.5, "[]", "respond", state),
    )
    if reentered:
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("causal:" + episode_id, episode_id, None, None, "test", 1.0, 1, time.time()),
        )


def _candidate(episodes, support_ids):
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
        "supporting_memory_ids": list(support_ids),
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        # These proposal counters are deliberately NOT promotion authority.
        "support_count": len(episodes),
        "success_count": len(episodes),
        "failure_count": 0,
        "calibration": 0.75,
        "last_validated_at": 0.0,
        "status": "CANDIDATE",
        "limits_method_ids": [],
    }


def _support(db):
    return [
        db.add_memory("fact", "support", "a", None, "gabriel", {"source": "test"}),
        db.add_memory("fact", "support", "b", None, "gabriel", {"source": "test"}),
    ]


def _admit_candidate(db, episodes):
    methods = MethodMemory(db)
    candidate_id = methods.admit(
        kind="framework_candidate",
        subject="causal discriminator",
        record=_candidate(episodes, _support(db)),
        source_turn_id=None,
        user_id="gabriel",
        provenance={"source": "promotion-regression"},
    )
    return methods, candidate_id


def test_terminal_reentered_sources_are_necessary_but_not_method_utility(tmp_path):
    db, session_id = _db(tmp_path)
    _episode(db, session_id, "src:a")
    _episode(db, session_id, "src:b")
    methods, candidate_id = _admit_candidate(db, ["src:a", "src:b"])
    before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]

    with pytest.raises(MethodRecordError, match="at least two distinct validated method uses"):
        methods.promote(
            candidate_memory_id=candidate_id,
            evaluation="two terminal re-entered episodes are not a utility evaluation",
            user_id="gabriel",
            provenance={"source": "held-out-eval", "evaluator": "test"},
        )

    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind IN ('framework','heuristic')").fetchone()[0] == 0


def test_open_or_nonreentered_abstraction_source_blocks_before_utility_gate(tmp_path):
    db, session_id = _db(tmp_path)
    _episode(db, session_id, "src:closed")
    _episode(db, session_id, "src:open", state="OPEN", reentered=False)
    methods, candidate_id = _admit_candidate(db, ["src:closed", "src:open"])
    before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]

    with pytest.raises(MethodRecordError, match="terminal and causally re-entered"):
        methods.promote(
            candidate_memory_id=candidate_id,
            evaluation="open abstraction source must not count",
            user_id="gabriel",
            provenance={"source": "terminal-gate-regression"},
        )

    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework','heuristic')"
    ).fetchone()[0] == 0


def test_repeated_unvalidated_promotion_attempts_do_not_create_partial_rows(tmp_path):
    db, session_id = _db(tmp_path)
    _episode(db, session_id, "src:a")
    _episode(db, session_id, "src:b")
    methods, candidate_id = _admit_candidate(db, ["src:a", "src:b"])
    before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
    for evaluation in ("first unvalidated claim", "second unvalidated claim"):
        with pytest.raises(MethodRecordError, match="at least two distinct validated method uses"):
            methods.promote(
                candidate_memory_id=candidate_id,
                evaluation=evaluation,
                user_id="gabriel",
                provenance={"source": "held-out-eval"},
            )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before


def test_forged_promoted_row_without_receipt_lineage_cannot_route(tmp_path):
    db, session_id = _db(tmp_path)
    _episode(db, session_id, "src:a")
    _episode(db, session_id, "src:b")
    support = _support(db)
    candidate = _candidate(["src:a", "src:b"], support)
    forged = dict(candidate)
    forged["status"] = "PROMOTED"
    forged["last_validated_at"] = time.time()
    forged = validate_method_record("framework", forged)
    db.add_memory(
        "framework",
        "forged",
        json.dumps(forged, sort_keys=True, separators=(",", ":")),
        None,
        "gabriel",
        {
            "source": "forged",
            "admission": "method_memory:v1",
            "user_scope": "gabriel",
            "method_schema_version": 1,
            "truth_authority": False,
            "effect_authority": False,
        },
    )
    with pytest.raises(MethodRecordError, match="verified promotion lineage"):
        MethodMemory(db).retrieve(
            query="verify causal provenance",
            user_id="gabriel",
            evidence_status="UNKNOWN",
            problem_signature={"goal": ["verify"], "mechanism": ["causal", "provenance"]},
        )
