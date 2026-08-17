import hashlib
import json
import time

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db, memory_id, value, *, subject, user_id="gabriel", ts=100.0):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def _bind_positive_canonical_outcome(db, turn):
    """Persist the positive causal receipt MicroClay is allowed to consume.

    This is a retrieval-layer fixture, not external execution: it deliberately does
    not use state.noop, which the canonical EffectJournal marks non-rewarding.
    """
    effect_id = f"effect:{turn['causal_id']}"
    now = time.time()
    outcome = json.dumps({"ok": True, "boundary": "test-canonical-receipt"}, sort_keys=True)
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            turn["episode_id"],
            "gabriel",
            "entityos.exec",
            json.dumps({"sha256": "test"}, sort_keys=True),
            None,
            int(turn["generation"]),
            "VERIFIED",
            outcome,
            now,
            now,
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            turn["causal_id"],
            turn["episode_id"],
            effect_id,
            turn["turn_id"],
            hashlib.sha256(outcome.encode()).hexdigest(),
            1.0,
            1,
            now,
        ),
    )


def test_verified_query_alias_opens_shadow_entry_without_changing_served_fact_status(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        first = life.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]] == ["m1"]
        _bind_positive_canonical_outcome(db, first)
        life.complete("done")

        second = life.begin("codename")
        receipt = second["context"]["retrieval_receipt"]
        assert receipt["policy_version"] == 2
        assert receipt["outcome_learning_applied"] == 1
        # SHADOW never changes factual serving authority: lexical Stage A is still UNKNOWN.
        assert second["context"]["durable_memory"] == []
        assert receipt["status"] == "UNKNOWN"

        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (second["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == ["m1"]

        route_key = MicroClayRetrieval._route_key("codename", "procedure:orchid")
        learned = db.db.execute(
            "SELECT capital,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert route_key.startswith("v2:route:")
        assert learned is not None
        assert float(learned["capital"]) > 0.0
        assert int(learned["pulls"]) == 1
        life.abort("test-end")
    finally:
        db.close()


def test_generic_subject_capital_cannot_open_unrelated_shadow_entry(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES(?,?,?,?,?)",
            ("v2:subject:procedure:orchid", 4.0, 1.0, 10, 1.0),
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("completely-unrelated-cue")
        assert result["context"]["durable_memory"] == []
        assert result["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []
        life.abort("test-end")
    finally:
        db.close()


def test_new_alias_route_credit_is_bound_to_rank1_served_evidence(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "top", "orchid procedure", subject="procedure:top", ts=200.0)
        _add(db, "other", "orchid procedure", subject="procedure:other", ts=100.0)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        first = life.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]][:2] == ["top", "other"]
        _bind_positive_canonical_outcome(db, first)
        life.complete("done")

        second = life.begin("codename")
        assert second["context"]["durable_memory"] == []
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (second["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == ["top"]

        top_key = MicroClayRetrieval._route_key("codename", "procedure:top")
        other_key = MicroClayRetrieval._route_key("codename", "procedure:other")
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (top_key,)
        ).fetchone() is not None
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (other_key,)
        ).fetchone() is None
        life.abort("test-end")
    finally:
        db.close()


def test_policy_version_mismatch_forces_shadow_and_ignores_v1_route_capital(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        cue = hashlib.sha256(b"codename").hexdigest()[:16]
        target = hashlib.sha256(b"procedure:orchid").hexdigest()[:16]
        legacy_route_key = f"route:{cue}:{target}"
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES(?,?,?,?,?)",
            (legacy_route_key, 4.0, 1.0, 10, 1.0),
        )
        db.db.execute(
            "UPDATE retrieval_policy_state SET mode='ACTIVE',policy_version=1 WHERE singleton=1"
        )
        organ = MicroClayRetrieval(db)
        assert organ.mode() == "SHADOW"

        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("codename")
        assert result["context"]["durable_memory"] == []
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids,policy_version,mode "
            "FROM retrieval_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert int(row["policy_version"]) == 2
        assert row["mode"] == "SHADOW"
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []
        life.abort("test-end")
    finally:
        db.close()
