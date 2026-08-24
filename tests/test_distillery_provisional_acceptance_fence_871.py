from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import tools.run_research_distillery as d
import tools.run_research_distillery_entry as entry


class DistilleryProvisionalAcceptanceFence871Tests(unittest.TestCase):
    def test_provisional_fallback_cannot_increment_accepted_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(d, "ARTIFACT_ROOT", root), \
                 mock.patch.object(d, "DB_PATH", root / "distillery.sqlite3"), \
                 mock.patch.object(d, "STATUS_PATH", root / "STATUS.json"), \
                 mock.patch.object(d, "EVENTS_PATH", root / "events.jsonl"):
                con = d.connect()
                qid = "q-test"
                con.execute(
                    "INSERT INTO questions(id,parent_id,root_problem,question,depth,priority,status,attempts,created_at,last_touched,source_worker_sha) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (qid, None, "root", "Does provisional fallback stay noncanonical?", 0, 1.0, "RESEARCHING", 1, d.now_iso(), d.now_iso(), None),
                )
                aid = con.execute(
                    "INSERT INTO approaches(question_id,signature,summary,search_terms_json,model,created_at) VALUES(?,?,?,?,?,?)",
                    (qid, "test", "test", "[]", "model", d.now_iso()),
                ).lastrowid
                sid = "s-test"
                con.execute(
                    "INSERT INTO source_chunks(id,question_id,approach_id,source_type,source_id,title,url,author,published,license,chunk_sha256,chunk_text,approx_tokens,metadata_json,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sid, qid, aid, "test", "source", "title", "", "", "", "", "a" * 64, "candidate evidence", 4, "{}", d.now_iso()),
                )
                cid = "c-test"
                con.execute(
                    "INSERT INTO candidates(id,question_id,approach_id,synthesizer_provider,synthesizer_model,packet_json,source_chunk_ids_json,input_tokens,output_tokens,created_at,status) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (cid, qid, aid, "openrouter", "openrouter/free", json.dumps({"claim": "candidate"}), json.dumps([sid]), 0, 0, d.now_iso(), "PENDING"),
                )
                votes = [
                    ("nvidia_reviewer", "nvidia", "nvidia/model"),
                    ("fallback_reviewer_1", "openrouter", "openrouter/free"),
                    ("fallback_reviewer_2", "openrouter", "openrouter/free"),
                ]
                for lane, provider, model in votes:
                    con.execute(
                        "INSERT INTO review_votes(candidate_id,lane,provider,model,intrinsic_consistency,grf_compatibility,project_fit,novelty,hard_contradiction,reason,input_tokens,output_tokens,created_at) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (cid, lane, provider, model, 0.95, 0.95, 0.95, 0.95, 0, "", 0, 0, d.now_iso()),
                    )
                con.commit()
                qrow = con.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()

                with mock.patch.object(d, "extract_questions_from_workers", return_value=0), \
                     mock.patch.object(d, "choose_question", return_value=qrow), \
                     mock.patch.object(d, "devise_novel_approach", return_value=(aid, {})), \
                     mock.patch.object(d, "collect_sources", return_value=[sid]), \
                     mock.patch.object(d, "synthesize", return_value=cid), \
                     mock.patch.object(d, "add_decompositions", return_value=0), \
                     mock.patch.object(entry, "provider_is_admitted_free", return_value=True), \
                     mock.patch.object(entry, "_ORIGINAL_REVIEW", return_value=(False, {})):
                    accepted = d.one_cycle(con, [], votes)

                self.assertFalse(accepted)
                self.assertEqual(con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0], 0)
                self.assertEqual(d.counter(con, "accepted_dataset_tokens"), 0)
                self.assertEqual(con.execute("SELECT status FROM candidates WHERE id=?", (cid,)).fetchone()[0], "PROVISIONAL_ACCEPTED")
                self.assertGreaterEqual(d.counter(con, "provisional_review_pass"), 1)
                con.close()


if __name__ == "__main__":
    unittest.main()
