import json
import time
import uuid

from clayverse.microclay_retrieval import MicroClayRetrieval, RetrievalCandidate
from clayverse.store import UnifiedDB


def _candidate(memory_id: str, value: str) -> RetrievalCandidate:
    return RetrievalCandidate(
        memory_id=memory_id,
        kind="fact",
        subject=f"route:{memory_id}",
        value=value,
        ts=1.0,
        provenance={"source": "budget-parity-test"},
        baseline_score=1.0,
        adaptive_score=1.0,
        entry_keys=(),
    )


def test_first_candidate_cannot_overrun_budget():
    oversized = _candidate("oversized", ("alpha " * 60).strip())
    small = _candidate("small", "alpha")

    selected, chars = MicroClayRetrieval._pack_candidates(
        [oversized, small], limit=24, budget_chars=256
    )

    assert [item.memory_id for item in selected] == ["small"]
    assert chars == len("alpha")
    assert chars <= 256


def test_shadow_counterfactual_uses_same_budget_pack_as_serving(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("test-user", "Test User")
        session_id = db.ensure_session("test-user", "terminal:test-user")
        turn_id = db.append_turn(session_id, "test-user", "user", "alpha")
        episode_id = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
            (
                episode_id,
                session_id,
                time.time(),
                turn_id,
                0.5,
                "[]",
                None,
                "OPEN",
            ),
        )

        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "oversized",
                "fact",
                "route:oversized",
                ("alpha " * 60).strip(),
                None,
                "test-user",
                100.0,
                json.dumps({"source": "budget-parity-test"}),
            ),
        )
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "small",
                "fact",
                "route:small",
                "alpha",
                None,
                "test-user",
                200.0,
                json.dumps({"source": "budget-parity-test"}),
            ),
        )
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES(?,?,?,?,?)",
            ("subject:route:oversized", 4.0, 1.0, 10, 1.0),
        )
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES(?,?,?,?,?)",
            ("subject:route:small", -2.0, -1.0, 10, 1.0),
        )

        causal_id = str(uuid.uuid4())
        result = MicroClayRetrieval(db).retrieve(
            query="alpha",
            user_id="test-user",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=db.entity_generation(),
            limit=24,
            budget_chars=256,
        )
        receipt_row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids,budget_chars,chars_selected "
            "FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()

        selected_ids = json.loads(receipt_row["selected_memory_ids"])
        shadow_ids = json.loads(receipt_row["shadow_memory_ids"])
        assert selected_ids == ["small"]
        assert shadow_ids == ["small"]
        assert result["receipt"]["shadow_differs"] is False
        assert int(receipt_row["budget_chars"]) == 256
        assert int(receipt_row["chars_selected"]) == len("alpha")
    finally:
        db.close()
