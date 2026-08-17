import hashlib
import json
import time
import uuid

import pytest

from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gabriel_session = db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db, gabriel_session


def _seed_retrieval(db, session_id, *, query="codename", selected=(), shadow=()):
    turn_id = db.append_turn(session_id, "gabriel", "user", query)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    retrieval_id = str(uuid.uuid4())
    now = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, now, turn_id, 0.5, "[]", None, "OPEN"),
    )
    token_hashes = [
        MicroClayRetrieval._token_key(token)[4:]
        for token in sorted(MicroClayRetrieval._tokens(query))
    ]
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    db.db.execute(
        "INSERT INTO retrieval_episodes("
        "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
        "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
        "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            retrieval_id,
            turn_id,
            episode_id,
            causal_id,
            session_id,
            "gabriel",
            db.entity_generation(),
            MicroClayRetrieval.POLICY_VERSION,
            "SHADOW",
            query_hash,
            json.dumps(token_hashes),
            json.dumps(list(selected)),
            json.dumps(list(shadow)),
            "[]",
            12000,
            24,
            0,
            "PRESENT" if selected else "UNKNOWN",
            now,
        ),
    )
    return {
        "retrieval_id": retrieval_id,
        "user_id": "gabriel",
        "session_id": session_id,
        "turn_id": turn_id,
        "episode_id": episode_id,
        "causal_id": causal_id,
        "generation": db.entity_generation(),
        "query_sha256": query_hash,
        "budget_chars": 12000,
        "limit_items": 24,
    }


def _add_memory(
    db,
    memory_id,
    *,
    subject="procedure:orchid",
    value="orchid procedure",
    user_id="gabriel",
    source_turn_id=None,
    kind="fact",
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
            time.time(),
            "{}",
        ),
    )


def test_explicit_complete_miss_teaches_one_shadow_route_idempotently(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        request = _seed_retrieval(db, session_id, query="codename")
        _add_memory(db, "m1")
        organ = MicroClayExplicitFeedback(db)

        first = organ.apply(
            **request,
            feedback_class="USER_MISS_TARGET",
            target_memory_id="m1",
        )
        assert first["applied"] is True
        assert first["mode"] == "SHADOW"
        assert first["truth_authority"] is False
        assert first["effect_authority"] is False
        assert first["updated_entrypoints"] == 1

        cue_hash = MicroClayRetrieval._token_key("codename")[4:]
        route_key = organ._route_key(cue_hash, "procedure:orchid")
        learned = db.db.execute(
            "SELECT capital,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert learned is not None
        assert float(learned["capital"]) > 0.0
        assert int(learned["pulls"]) == 1

        replay = organ.apply(
            **request,
            feedback_class="USER_MISS_TARGET",
            target_memory_id="m1",
        )
        assert replay["applied"] is False
        assert replay["reason"] == "duplicate_receipt"
        assert db.db.execute(
            "SELECT pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()[0] == 1
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1
    finally:
        db.close()


def test_request_identity_and_feedback_source_drift_fail_before_mutation(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        request = _seed_retrieval(db, session_id)
        _add_memory(db, "m1")
        organ = MicroClayExplicitFeedback(db)

        bad = dict(request)
        bad["budget_chars"] = 11999
        with pytest.raises(StaleGeneration):
            organ.apply(
                **bad,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="m1",
            )
        with pytest.raises(PermissionError):
            organ.apply(
                **request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="m1",
                source="CLAUDE_INFERRED",
            )
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()


def test_cross_user_current_turn_control_and_ambiguous_targets_fail_closed(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        request = _seed_retrieval(db, session_id)
        organ = MicroClayExplicitFeedback(db)

        _add_memory(db, "other-user", user_id="andreas")
        with pytest.raises(PermissionError):
            organ.apply(
                **request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="other-user",
            )

        _add_memory(
            db,
            "echo",
            subject="echo:subject",
            source_turn_id=request["turn_id"],
        )
        with pytest.raises(PermissionError):
            organ.apply(
                **request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="echo",
            )

        _add_memory(db, "control", subject="control:subject", kind="source_archive")
        with pytest.raises(PermissionError):
            organ.apply(
                **request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="control",
            )

        _add_memory(db, "a", subject="duplicate:subject")
        _add_memory(db, "b", subject="duplicate:subject")
        with pytest.raises(PermissionError, match="ambiguous subject route"):
            organ.apply(
                **request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="a",
            )

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()


def test_no_memory_records_calibration_without_inventing_route(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        request = _seed_retrieval(db, session_id)
        result = MicroClayExplicitFeedback(db).apply(
            **request,
            feedback_class="USER_NO_MEMORY",
        )
        assert result["applied"] is True
        assert result["target_memory_id"] is None
        assert result["updated_entrypoints"] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        feedback = db.db.execute(
            "SELECT credit,signal_class FROM retrieval_feedback"
        ).fetchone()
        assert float(feedback["credit"]) == 0.0
        assert feedback["signal_class"].startswith(
            "user_explicit:user_no_memory:"
        )
    finally:
        db.close()


def test_explicit_irrelevant_feedback_only_applies_to_served_memory(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        _add_memory(db, "served")
        request = _seed_retrieval(db, session_id, selected=("served",))
        organ = MicroClayExplicitFeedback(db)
        result = organ.apply(
            **request,
            feedback_class="USER_IRRELEVANT",
            target_memory_id="served",
        )
        assert result["applied"] is True
        cue_hash = MicroClayRetrieval._token_key("codename")[4:]
        route_key = organ._route_key(cue_hash, "procedure:orchid")
        learned = db.db.execute(
            "SELECT capital,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert float(learned["capital"]) < 0.0
        assert int(learned["pulls"]) == 1
    finally:
        db.close()


def test_feedback_joins_outer_transaction_and_rolls_back_with_it(tmp_path):
    db, session_id = _db(tmp_path)
    try:
        request = _seed_retrieval(db, session_id)
        _add_memory(db, "m1")
        organ = MicroClayExplicitFeedback(db)

        with pytest.raises(RuntimeError, match="force outer rollback"):
            with db.tx():
                result = organ.apply(
                    **request,
                    feedback_class="USER_MISS_TARGET",
                    target_memory_id="m1",
                )
                assert result["applied"] is True
                assert db.db.execute(
                    "SELECT COUNT(*) FROM retrieval_feedback"
                ).fetchone()[0] == 1
                raise RuntimeError("force outer rollback")

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()
