from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BRIDGE_PATH=ROOT/"tools/ingest_forge_accepts_to_distillery.py"
SPEC=importlib.util.spec_from_file_location("forge_to_distillery_bridge_under_test",BRIDGE_PATH)
assert SPEC is not None and SPEC.loader is not None
BRIDGE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(BRIDGE)


class ConversionFunnelContractTests(unittest.TestCase):
    def text(self,rel:str)->str:
        return (ROOT/rel).read_text(encoding="utf-8")

    def test_modified_python_sources_compile(self):
        for rel in (
            "tools/run_free_evidence_forge_v2.py",
            "tools/ingest_forge_accepts_to_distillery.py",
            "free swarm/update_root_results.py",
        ):
            compile(self.text(rel),rel,"exec")

    def test_forge_v2_uses_runtime_recorded_source_identity_then_strict_validator(self):
        src=self.text("tools/run_free_evidence_forge_v2.py")
        self.assertIn("repo_head_at_prompt",src)
        self.assertIn("_worker_base_commit",src)
        self.assertIn("text_sha256",src)
        self.assertIn("_ORIGINAL_VALIDATE",src)
        self.assertIn('"--3way"',src)
        self.assertIn('"diff","HEAD"',src)
        self.assertIn("MODEL_BASE_COMMIT_MISMATCH_RUNTIME_RECORD",src)
        self.assertIn("PATCH_INVALID_AT_RECORDED_WORKER_BASE",src)
        self.assertIn("VALID_AT_RECORDED_BASE_BUT_NOT_3WAY_APPLICABLE_TO_CURRENT_MAIN",src)
        self.assertIn("v2_three_way_rebased",src)
        self.assertNotIn('"status":"accepted"',src)

    def test_forge_bridge_requires_strict_executable_pass_and_db_crossbind(self):
        src=self.text("tools/ingest_forge_accepts_to_distillery.py")
        self.assertIn('ev.get("status")=="accepted"',src)
        self.assertIn('int(ev.get("reproducible_runs") or 0)>=2',src)
        self.assertIn('int(ev.get("tests_failed") or 0)==0',src)
        self.assertIn('int(ev.get("negative_tests_failed") or 0)==0',src)
        self.assertIn('int(ev.get("static_checks_failed") or 0)==0',src)
        self.assertIn('float(ev.get("relative_improvement_pct") or 0.0)>0.0',src)
        self.assertIn('str(row["state"]).upper()!="ACCEPTED"',src)
        self.assertIn('"acceptance_basis":"EXECUTABLE_FORGE_NOT_MODEL_CONSENSUS"',src)
        self.assertIn('"canonical_truth_credit":False',src)
        self.assertIn('"training_credit":False',src)
        self.assertIn("model_review_scores_applicable",src)

    def _forge_fixture(self,root:Path,state:str="ACCEPTED") -> None:
        forge=root/"forge";forge.mkdir(parents=True)
        con=sqlite3.connect(forge/"forge.sqlite3")
        con.execute("CREATE TABLE candidates(candidate_hash TEXT PRIMARY KEY,proposal_json TEXT,state TEXT,worker_sha TEXT,delta_id TEXT,provider TEXT,model TEXT,role TEXT,evaluated_at TEXT)")
        proposal={"hypothesis":"repair x","mechanism":"add deterministic guard","falsifier":"regression flips","target_files":["x.py"]}
        con.execute("INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?)",("cand-1",json.dumps(proposal),state,"worker-sha","delta-1","openrouter","openrouter/free","falsifier","2026-08-24T00:00:00Z"))
        con.commit();con.close()
        ev={
            "schema":"CLAY_FORGE_DELTA_EVALUATION/v1","status":"accepted","delta_id":"delta-1","worker_sha":"worker-sha",
            "reproducible_runs":2,"tests_passed":2,"tests_failed":0,"negative_tests_passed":1,"negative_tests_failed":0,
            "static_checks_passed":1,"static_checks_failed":0,"benchmark_non_regression":True,
            "relative_improvement_pct":50.0,"metric":"test_pass_rate","proposal_hypothesis":"repair x","falsifier":"regression flips",
        }
        (forge/"architecture_delta_evaluations.jsonl").write_text(json.dumps(ev)+"\n",encoding="utf-8")

    def test_strict_forge_accept_imports_once_without_model_scores(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self._forge_fixture(root,"ACCEPTED")
            first=BRIDGE.ingest(root);second=BRIDGE.ingest(root)
            self.assertEqual(first["imported"],1)
            self.assertEqual(second["imported"],0)
            self.assertEqual(second["already_imported"],1)
            con=sqlite3.connect(root/"distillery/distillery.sqlite3")
            row=con.execute("SELECT intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,metadata_json FROM knowledge_packets").fetchone()
            tokens=con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()[0]
            ingest_rows=con.execute("SELECT COUNT(*) FROM forge_ingest").fetchone()[0]
            con.close()
            self.assertIsNotNone(row);self.assertEqual(tuple(row[:4]),(0.0,0.0,0.0,0.0))
            self.assertGreater(int(row[4]),0);self.assertEqual(tokens,int(row[4]));self.assertEqual(ingest_rows,1)
            meta=json.loads(row[5]);self.assertEqual(meta["acceptance_basis"],"EXECUTABLE_FORGE_NOT_MODEL_CONSENSUS")
            self.assertFalse(meta["canonical_truth_credit"]);self.assertFalse(meta["training_credit"])

    def test_jsonl_accepted_cannot_bypass_nonaccepted_forge_db_state(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self._forge_fixture(root,"PATCH_REJECTED")
            out=BRIDGE.ingest(root)
            self.assertEqual(out["eligible"],1);self.assertEqual(out["imported"],0);self.assertEqual(out["rejected_crossbind"],1)
            con=sqlite3.connect(root/"distillery/distillery.sqlite3")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0],0);con.close()

    def test_live_supervisor_hook_reloads_and_bridges_without_credentials(self):
        src=self.text("free swarm/update_root_results.py")
        self.assertIn('f"{name}.source.binding"',src)
        self.assertIn("run_research_distillery_local.py",src)
        self.assertIn("run_free_evidence_forge_v2.py",src)
        self.assertIn("ingest_forge_accepts_to_distillery.py",src)
        self.assertIn("restart_owner",src)
        self.assertIn("credential-blind",src)
        self.assertNotIn("get_secret",src)
        self.assertNotIn("sudo",src)


if __name__=="__main__":unittest.main()
