#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_research_distillery as d


class ResearchDistilleryQuestionInsertTests(unittest.TestCase):
    def test_seed_and_worker_question_follow_current_questions_schema(self) -> None:
        old_root = d.ARTIFACT_ROOT
        old_db = d.DB_PATH
        old_status = d.STATUS_PATH
        old_events = d.EVENTS_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                d.ARTIFACT_ROOT = root
                d.DB_PATH = root / "distillery.sqlite3"
                d.STATUS_PATH = root / "STATUS.json"
                d.EVENTS_PATH = root / "events.jsonl"

                con = d.connect()
                try:
                    d.seed(con)
                    seeded = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
                    self.assertEqual(seeded, len(d.SEED_QUESTIONS))

                    worker_sha = "f" * 64
                    question = (
                        "How should a freshly derived worker question preserve source provenance "
                        "without changing the canonical question schema?"
                    )
                    self.assertTrue(d.add_question(con, question, priority=1.7, worker_sha=worker_sha))
                    con.commit()

                    row = con.execute(
                        "SELECT status,created_at,last_touched,source_worker_sha FROM questions WHERE question=?",
                        (question,),
                    ).fetchone()
                    self.assertIsNotNone(row)
                    assert row is not None
                    self.assertEqual(row["status"], "OPEN")
                    self.assertTrue(str(row["created_at"]))
                    self.assertIsNone(row["last_touched"])
                    self.assertEqual(row["source_worker_sha"], worker_sha)
                finally:
                    con.close()
        finally:
            d.ARTIFACT_ROOT = old_root
            d.DB_PATH = old_db
            d.STATUS_PATH = old_status
            d.EVENTS_PATH = old_events

    def test_insert_statement_has_one_value_per_named_column(self) -> None:
        text = (TOOLS / "run_research_distillery.py").read_text(encoding="utf-8")
        self.assertIn(
            "questions(id,parent_id,root_problem,question,depth,priority,status,created_at,source_worker_sha) VALUES(?,?,?,?,?,?, 'OPEN',?,?)",
            text,
        )
        self.assertNotIn("VALUES(?,?,?,?,?,?, 'OPEN',?,?,?)", text)


if __name__ == "__main__":
    unittest.main()
