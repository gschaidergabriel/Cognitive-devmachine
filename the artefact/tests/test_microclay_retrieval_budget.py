import time
import uuid

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def test_first_candidate_cannot_overrun_retrieval_budget(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        session_id = db.ensure_session("gabriel", "terminal:gabriel")
        turn_id = db.append_turn(session_id, "gabriel", "user", "alpha")
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

        small_id = db.add_memory(
            "fact",
            "memory",
            "alpha beta gamma delta epsilon zeta eta theta iota kappa",
            None,
            "gabriel",
            {"test": "budget-fence-small"},
        )
        oversized_id = db.add_memory(
            "fact",
            "memory",
            ("alpha " * 60).strip(),
            None,
            "gabriel",
            {"test": "budget-fence-oversized"},
        )

        result = MicroClayRetrieval(db).retrieve(
            query="alpha",
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=str(uuid.uuid4()),
            generation=db.entity_generation(),
            limit=24,
            budget_chars=256,
        )

        selected_ids = [item["memory_id"] for item in result["items"]]
        assert oversized_id not in selected_ids
        assert small_id in selected_ids
        assert result["receipt"]["chars_selected"] <= 256
        assert sum(len(item["value"]) for item in result["items"]) <= 256
    finally:
        db.close()
