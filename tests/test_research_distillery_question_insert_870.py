from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/run_research_distillery.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_research_distillery_tested", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("distillery module load failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResearchDistilleryQuestionInsert870Tests(unittest.TestCase):
    def test_seed_and_worker_question_match_questions_schema(self) -> None:
        dist = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dist.ARTIFACT_ROOT = root
            dist.DB_PATH = root / "distillery.sqlite3"
            dist.STATUS_PATH = root / "STATUS.json"
            dist.EVENTS_PATH = root / "events.jsonl"
            con = dist.connect()
            try:
                dist.seed(con)
                seeded = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
                self.assertEqual(seeded, len(dist.SEED_QUESTIONS))

                worker_sha = "a" * 64
                question = "How should a worker-derived causal question preserve exact source provenance in EntityOS?"
                self.assertTrue(dist.add_question(con, question, worker_sha=worker_sha, priority=1.25))
                con.commit()
                row = con.execute(
                    "SELECT status,created_at,last_touched,source_worker_sha FROM questions WHERE question=?",
                    (question,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["status"], "OPEN")
                self.assertTrue(row["created_at"])
                self.assertIsNone(row["last_touched"])
                self.assertEqual(row["source_worker_sha"], worker_sha)
            finally:
                con.close()


if __name__ == "__main__":
    unittest.main()
