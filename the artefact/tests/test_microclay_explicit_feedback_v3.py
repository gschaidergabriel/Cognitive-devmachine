import hashlib
import json
import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(
    db,
    memory_id,
    value,
    *,
    subject="topic:shared",
    user_id=None,
    kind="fact",
    ts=None,
    source_turn_id=None,
):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            memory_id,
            kind,
            subject,
            value,
            source_turn_id,
            user_id,
            time.time() - 10.0 if ts is None else ts,
            json.dumps({"source": "explicit-feedback-v3-test"}),
        ),
    )


def _request(db, causal_id):
    row = db.db.execute(
        "SELECT * FROM retrieval_episodes WHERE causal_id=?", (causal_id,)
    ).fetchone()
    assert row is not None
    return row, {
        "retrieval_id": row["retrieval_id"],
        "user_id": row["user_id"],
        "session_id": row["session_id"],
        "turn_id": row["turn_id"],
        "episode_id": row["episode_id"],
        "causal_id": row["causal_id"],
        "generation": int(row["generation"]),
        "query_sha256": row["query_hash"],
        "budget_chars": int(row["budget_chars"]),
        "limit_items": int(row["limit_items"]),
    }


def _apply(organ, request, feedback_class, target=None, source="USER_EXPLICIT"):
    return organ.apply(
        **request,
        feedback_class=feedback_class,
        target_memory_id=target,
        source=source,
    )


def test_complete_miss_teaches_only_correcting_users_exact_memory_shadow_route(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "orchid procedure")
        _add(db, "sibling", "bicycle violet")
        organ = MicroClayExplicitFeedback(db)

        gabriel = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = gabriel.begin("codename")
        assert first["context"]["durable_memory"] == []
        row, request = _request(db, first["causal_id"])
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []

        result = _apply(organ, request, "USER_MISS_TARGET", "target")
        assert result["applied"] is True
        assert result["policy_version"] == 3
        assert result["mode"] == "SHADOW"
        assert result["truth_authority"] is False
        assert result["effect_authority"] is False
        assert result["updated_entrypoints"] == 1

        cue_hash = MicroClayRetrieval._token_key("codename")[4:]
        target_key = organ._route_key("gabriel", cue_hash, "target")
        sibling_key = organ._route_key("gabriel", cue_hash, "sibling")
        andreas_target_key = organ._route_key("andreas", cue_hash, "target")
        learned = db.db.execute(
            "SELECT capital,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (target_key,),
        ).fetchone()
        assert learned is not None
        assert float(learned["capital"]) > 0.0
        assert int(learned["pulls"]) == 1
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (sibling_key,)
        ).fetchone() is None
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (andreas_target_key,)
        ).fetchone() is None

        replay = _apply(organ, request, "USER_MISS_TARGET", "target")
        assert replay["applied"] is False
        assert replay["reason"] == "duplicate_receipt"
        gabriel.abort("feedback-recorded")

        second = gabriel.begin("codename")
        assert second["context"]["durable_memory"] == []
        second_row, _ = _request(db, second["causal_id"])
        assert json.loads(second_row["selected_memory_ids"]) == []
        assert json.loads(second_row["shadow_memory_ids"]) == ["target"]
        gabriel.abort("test-end")

        andreas = TurnLifecycle(db, "andreas", "session:andreas")
        other = andreas.begin("codename")
        assert other["context"]["durable_memory"] == []
        other_row, _ = _request(db, other["causal_id"])
        assert json.loads(other_row["shadow_memory_ids"]) == []
        andreas.abort("test-end")
    finally:
        db.close()


def test_request_provenance_mode_hindsight_and_cross_user_drift_fail_before_learning(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "orchid procedure", user_id="gabriel")
        _add(db, "private-andreas", "private memory", user_id="andreas")
        organ = MicroClayExplicitFeedback(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        begun = life.begin("codename")
        row, request = _request(db, begun["causal_id"])

        bad = dict(request)
        bad["budget_chars"] -= 1
        with pytest.raises(StaleGeneration):
            _apply(organ, bad, "USER_MISS_TARGET", "target")
        with pytest.raises(PermissionError):
            _apply(
                organ,
                request,
                "USER_MISS_TARGET",
                "target",
                source="CLAUDE_INFERRED",
            )
        with pytest.raises(PermissionError):
            _apply(organ, request, "USER_MISS_TARGET", "private-andreas")

        _add(
            db,
            "future-target",
            "future memory",
            subject="topic:future",
            user_id="gabriel",
            ts=float(row["ts"]) + 1.0,
        )
        with pytest.raises(PermissionError, match="did not exist at retrieval time"):
            _apply(organ, request, "USER_MISS_TARGET", "future-target")

        db.db.execute(
            "UPDATE retrieval_policy_state SET mode='ACTIVE',policy_version=? WHERE singleton=1",
            (MicroClayRetrieval.POLICY_VERSION,),
        )
        with pytest.raises(PermissionError):
            _apply(organ, request, "USER_MISS_TARGET", "target")

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        life.abort("test-end")
    finally:
        db.close()


def test_current_turn_control_and_corrupt_replay_are_rejected(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "orchid procedure", user_id="gabriel")
        _add(db, "control", "archive", kind="source_archive", user_id="gabriel")
        _add(db, "other-user", "private", user_id="andreas")
        organ = MicroClayExplicitFeedback(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        begun = life.begin("codename")
        row, request = _request(db, begun["causal_id"])
        _add(
            db,
            "echo",
            "same-turn echo",
            subject="topic:echo",
            user_id="gabriel",
            source_turn_id=row["turn_id"],
            ts=float(row["ts"]) - 1.0,
        )

        with pytest.raises(PermissionError):
            _apply(organ, request, "USER_MISS_TARGET", "control")
        with pytest.raises(PermissionError, match="current-turn echo"):
            _apply(organ, request, "USER_MISS_TARGET", "echo")

        db.db.execute(
            "UPDATE retrieval_episodes SET shadow_memory_ids=? WHERE retrieval_id=?",
            (json.dumps(["other-user"]), row["retrieval_id"]),
        )
        with pytest.raises(StaleGeneration):
            _apply(organ, request, "USER_MISS_TARGET", "target")
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        life.abort("test-end")
    finally:
        db.close()


def test_no_memory_is_calibration_only_and_outer_transaction_rolls_back_atomically(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "orchid procedure", user_id="gabriel")
        organ = MicroClayExplicitFeedback(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        begun = life.begin("nothing")
        _, request = _request(db, begun["causal_id"])

        no_memory = _apply(organ, request, "USER_NO_MEMORY")
        assert no_memory["applied"] is True
        assert no_memory["updated_entrypoints"] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        feedback_before = db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0]

        life.abort("calibration-recorded")
        second = life.begin("codename")
        _, second_request = _request(db, second["causal_id"])
        with pytest.raises(RuntimeError, match="force outer rollback"):
            with db.tx():
                applied = _apply(
                    organ,
                    second_request,
                    "USER_MISS_TARGET",
                    "target",
                )
                assert applied["applied"] is True
                raise RuntimeError("force outer rollback")

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == feedback_before
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        life.abort("test-end")
    finally:
        db.close()
