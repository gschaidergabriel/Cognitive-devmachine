import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

REPO = Path(__file__).resolve().parents[1]


class StubBridge(types.ModuleType):
    def __init__(self, root: Path):
        super().__init__("ingest_forge_accepts_into_distillery")
        self.ARTIFACT_ROOT = root
        self.DEFAULT_FORGE_EVAL = root / "forge/evaluations.jsonl"
        self.DEFAULT_DISTILLERY_DB = root / "distillery/distillery.sqlite3"
        self.calls = []

    def ingest(self, forge_evaluations: Path, distillery_db: Path):
        self.calls.append((Path(forge_evaluations), Path(distillery_db)))
        return {
            "schema": "CLAY_FORGE_TO_DISTILLERY_INGEST_RESULT/v2",
            "acceptance_semantics": "EVIDENCE_QUALIFIED_ONLY",
            "forge_eval_path": str(forge_evaluations),
            "distillery_db": str(distillery_db),
            "seen": 1,
            "admitted": 1 if len(self.calls) == 1 else 0,
            "duplicates": 0 if len(self.calls) == 1 else 1,
            "rejected": {},
            "packet_ids": ["kf-test"] if len(self.calls) == 1 else [],
            "accepted_dataset_tokens_counter": 123,
            "forge_execution_packets_total": 1,
            "forge_evidence_qualified_packets_counter": 1,
        }


class LiveBridgeLoopTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.stub = StubBridge(self.root)
        sys.modules["ingest_forge_accepts_into_distillery"] = self.stub
        module_path = REPO / "tools/run_forge_distillery_bridge_loop.py"
        spec = importlib.util.spec_from_file_location("bridge_loop_under_test", module_path)
        self.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(self.mod)

    def tearDown(self):
        sys.modules.pop("ingest_forge_accepts_into_distillery", None)
        self.td.cleanup()

    def test_run_once_writes_bounded_status(self):
        eval_path = self.stub.DEFAULT_FORGE_EVAL
        eval_path.parent.mkdir(parents=True, exist_ok=True)
        eval_path.write_text("{}\n", encoding="utf-8")
        status = self.root / "status.json"
        out = self.mod.run_once(eval_path, self.stub.DEFAULT_DISTILLERY_DB, status)
        saved = json.loads(status.read_text(encoding="utf-8"))
        self.assertEqual(out["admitted"], 1)
        self.assertEqual(saved["accepted_dataset_tokens_counter"], 123)
        self.assertEqual(saved["bridge_loop_schema"], "CLAY_FORGE_DISTILLERY_LIVE_BRIDGE/v2")
        self.assertEqual(saved["acceptance_semantics"], "EVIDENCE_QUALIFIED_ONLY")
        self.assertFalse(saved["network_io"])
        self.assertFalse(saved["canonical_truth"])
        self.assertEqual(saved["jspace_causal_credit"], 0)
        self.assertEqual(saved["training_credit"], 0)

    def test_duplicate_reconciliation_is_forwarded_without_double_credit(self):
        eval_path = self.stub.DEFAULT_FORGE_EVAL
        eval_path.parent.mkdir(parents=True, exist_ok=True)
        eval_path.write_text("{}\n", encoding="utf-8")
        status = self.root / "status.json"
        first = self.mod.run_once(eval_path, self.stub.DEFAULT_DISTILLERY_DB, status)
        second = self.mod.run_once(eval_path, self.stub.DEFAULT_DISTILLERY_DB, status)
        self.assertEqual(first["admitted"], 1)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], first["accepted_dataset_tokens_counter"])
        self.assertEqual(second["forge_evidence_qualified_packets_counter"], 1)

    def test_source_fingerprint_changes_with_append(self):
        p = self.root / "eval.jsonl"
        self.assertEqual(self.mod.source_fingerprint(p), (False, 0, 0))
        p.write_text("{}\n", encoding="utf-8")
        first = self.mod.source_fingerprint(p)
        p.write_text("{}\n{}\n", encoding="utf-8")
        second = self.mod.source_fingerprint(p)
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertNotEqual(first[2], second[2])


class StaticLiveWireTests(unittest.TestCase):
    def test_activation_compiles_and_starts_bridge(self):
        text = (REPO / "tools/activate_6000_free_swarm.sh").read_text(encoding="utf-8")
        self.assertIn("tools/forge_evidence_credit_871.py", text)
        self.assertIn("tools/ingest_forge_accepts_into_distillery.py", text)
        self.assertIn("tools/run_forge_distillery_bridge_loop.py", text)
        self.assertIn("forge-distillery-bridge.pid", text)
        self.assertIn("forge_execution_ingest_status.json", text)

    def test_activation_stops_stale_bridge_on_restart(self):
        text = (REPO / "tools/activate_6000_free_swarm.sh").read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("tools/run_forge_distillery_bridge_loop.py"), 3)
        self.assertIn("SIGTERM", text)
        self.assertIn("SIGKILL", text)

    def test_bridge_loop_has_no_provider_network_client(self):
        text = (REPO / "tools/run_forge_distillery_bridge_loop.py").read_text(encoding="utf-8")
        for forbidden in ("urllib", "requests", "httpx", "api.openai", "integrate.api.nvidia"):
            self.assertNotIn(forbidden, text)
        self.assertIn('"network_io": False', text)
        self.assertIn('"acceptance_semantics": "EVIDENCE_QUALIFIED_ONLY"', text)


if __name__ == "__main__":
    unittest.main()
