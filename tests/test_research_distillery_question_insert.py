from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "run_research_distillery.py"
SPEC = importlib.util.spec_from_file_location("run_research_distillery_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
DISTILLERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISTILLERY)


def test_seed_and_worker_question_bind_current_question_schema(tmp_path: Path) -> None:
    old_paths = (
        DISTILLERY.ARTIFACT_ROOT,
        DISTILLERY.DB_PATH,
        DISTILLERY.STATUS_PATH,
        DISTILLERY.EVENTS_PATH,
    )
    DISTILLERY.ARTIFACT_ROOT = tmp_path
    DISTILLERY.DB_PATH = tmp_path / "distillery.sqlite3"
    DISTILLERY.STATUS_PATH = tmp_path / "STATUS.json"
    DISTILLERY.EVENTS_PATH = tmp_path / "events.jsonl"

    con = None
    try:
        con = DISTILLERY.connect()
        DISTILLERY.seed(con)

        seed_count = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        assert seed_count == len(DISTILLERY.SEED_QUESTIONS)

        worker_sha = "a" * 64
        question = (
            "Can deterministic queue admission preserve worker provenance while "
            "keeping untouched questions free of last_touched state?"
        )
        assert DISTILLERY.add_question(con, question, priority=1.25, worker_sha=worker_sha)
        con.commit()

        row = con.execute(
            "SELECT status, created_at, last_touched, source_worker_sha "
            "FROM questions WHERE question=?",
            (question,),
        ).fetchone()
        assert row is not None
        assert row["status"] == "OPEN"
        assert row["created_at"]
        assert row["last_touched"] is None
        assert row["source_worker_sha"] == worker_sha
    finally:
        if con is not None:
            con.close()
        (
            DISTILLERY.ARTIFACT_ROOT,
            DISTILLERY.DB_PATH,
            DISTILLERY.STATUS_PATH,
            DISTILLERY.EVENTS_PATH,
        ) = old_paths
