import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tools" / "ingest_forge_accepts_into_distillery.py"
HELPERS = ROOT / "tests" / "test_forge_distillery_replay_identity_873.py"

spec = importlib.util.spec_from_file_location("replay_identity_873_helpers", HELPERS)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


class ReplayRestart873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, row):
        self.eval.write_text(json.dumps(row) + "\n", encoding="utf-8")

    def run_bridge_process(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(BRIDGE),
                "--forge-evaluations",
                str(self.eval),
                "--distillery-db",
                str(self.db),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)

    def test_semantic_replay_is_zero_delta_after_process_restart(self):
        first_row = helpers.accepted_row()
        self.write(first_row)
        first = self.run_bridge_process()

        self.assertEqual(first["admitted"], 1)
        self.assertEqual(first["forge_execution_packets_total"], 1)
        first_tokens = first["accepted_dataset_tokens_counter"]
        first_packet_ids = list(first["packet_ids"])

        replay = helpers.accepted_row(
            evaluated_at="2026-08-25T00:00:01+00:00",
            proposal_hypothesis="restart-only candidate narration mutation",
            falsifier="restart-only candidate falsifier mutation",
        )
        self.write(replay)

        # A second CLI invocation is a fresh Python process and reopens the persisted DB.
        second = self.run_bridge_process()

        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], first_tokens)
        self.assertEqual(second["forge_execution_packets_total"], 1)
        self.assertEqual(second["packet_ids"], [])
        self.assertEqual(len(first_packet_ids), 1)


if __name__ == "__main__":
    unittest.main()
