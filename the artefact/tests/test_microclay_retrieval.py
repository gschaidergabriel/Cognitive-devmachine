import json
import time
import uuid

from clayverse.identity import IdentityRouter
from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db, "session:gabriel"


def test_microclay_starts_at_current_static_baseline_and_persists_receipt(tmp_path):
    db, sid = _db(tmp_path)
    try:
        tid = db.append_turn(sid, "gabriel", "user", "hello")
        world = WorldAssembler(db).assemble(sid, [])
        policy = world["retrieval_policy"]
        assert policy["policy_id"] == "balanced"
        assert policy["limits"] == {
            "own_turn_window": 20,
            "cross_session_limit": 10,
            "memory_limit": 50,
        }
        provenance = json.loads(
            db.db.execute("SELECT provenance FROM turns WHERE turn_id=?", (tid,)).fetchone()[0]
        )
        assert provenance["retrieval_policy"]["controller"] == "microclay-retrieval-v1"
    finally:
        db.close()


def test_explicit_negative_feedback_is_delayed_idempotent_online_credit(tmp_path):
    db, sid = _db(tmp_path)
    try:
        first = db.append_turn(sid, "gabriel", "user", "answer this")
        WorldAssembler(db).assemble(sid, [])
        db.append_turn(sid, "gabriel", "assistant", "bad answer")
        db.append_turn(sid, "gabriel", "user", "falsch, das war nicht richtig")
        world = WorldAssembler(db).assemble(sid, [])
        assert world["retrieval_policy"]["feedback_count"] == 1
        assert world["retrieval_policy"]["policy_id"] == "focused"
        prior = json.loads(
            db.db.execute("SELECT provenance FROM turns WHERE turn_id=?", (first,)).fetchone()[0]
        )
        assert prior["retrieval_feedback"]["source"] == "explicit_next_prompt"
        assert prior["retrieval_feedback"]["reward"] == -0.7

        again = WorldAssembler(db).assemble(sid, [])
        assert again["retrieval_policy"]["policy_id"] == "focused"
        state = json.loads(
            db.db.execute(
                "SELECT value FROM meta WHERE key='microclay.retrieval.v1.gabriel.local'"
            ).fetchone()[0]
        )
        assert state["feedback_count"] == 1
    finally:
        db.close()


def test_corrupt_learning_state_fails_closed_to_baseline(tmp_path):
    db, sid = _db(tmp_path)
    try:
        db.db.execute(
            "INSERT INTO meta(key,value) VALUES(?,?)",
            ("microclay.retrieval.v1.gabriel.local", "{broken"),
        )
        db.append_turn(sid, "gabriel", "user", "hello")
        policy = WorldAssembler(db).assemble(sid, [])["retrieval_policy"]
        assert policy["policy_id"] == "balanced"
        assert policy["state_recovered"] is True
    finally:
        db.close()


def test_local_and_shared_resource_learning_state_are_separate(tmp_path):
    db, sid = _db(tmp_path)
    try:
        db.append_turn(sid, "gabriel", "user", "local prompt")
        WorldAssembler(db).assemble(sid, [])
        db.append_turn(sid, "gabriel", "assistant", "answer")
        db.append_turn(sid, "gabriel", "user", "falsch")
        local = WorldAssembler(db).assemble(sid, [])["retrieval_policy"]
        assert local["feedback_count"] == 1

        db.append_turn(sid, "gabriel", "assistant", "answer2")
        db.append_turn(
            sid,
            "gabriel",
            "user",
            "inspect file:x.py",
            resources=["file:x.py"],
        )
        shared = WorldAssembler(db).assemble(sid, ["file:x.py"])["retrieval_policy"]
        assert shared["bucket"] == "shared"
        assert shared["feedback_count"] == 0
        assert shared["policy_id"] == "balanced"
    finally:
        db.close()


def test_verified_causal_effect_credit_overrides_prompt_heuristic(tmp_path):
    db, sid = _db(tmp_path)
    try:
        first = db.append_turn(sid, "gabriel", "user", "run a checked action")
        WorldAssembler(db).assemble(sid, [])
        episode = str(uuid.uuid4())
        effect = str(uuid.uuid4())
        causal = str(uuid.uuid4())
        now = time.time()
        db.db.execute(
            "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
            (episode, sid, now, first, 0.5, "[]", "request_effect", "COMPLETED"),
        )
        db.db.execute(
            "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (effect, episode, "gabriel", "state.noop", "{}", None, 1, "VERIFIED", "{}", now, now),
        )
        db.db.execute(
            "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
            (causal, episode, effect, first, "hash", 1.0, 1, now),
        )
        db.append_turn(sid, "gabriel", "assistant", "done")
        db.append_turn(sid, "gabriel", "user", "falsch")
        policy = WorldAssembler(db).assemble(sid, [])["retrieval_policy"]
        prior = json.loads(
            db.db.execute("SELECT provenance FROM turns WHERE turn_id=?", (first,)).fetchone()[0]
        )
        assert prior["retrieval_feedback"]["source"] == "causal_effect"
        assert prior["retrieval_feedback"]["reward"] == 1.0
        assert policy["feedback_count"] == 1
    finally:
        db.close()
