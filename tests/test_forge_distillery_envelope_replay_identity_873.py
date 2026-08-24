import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

bridge_spec = importlib.util.spec_from_file_location(
    "bridge_envelope_replay_873", TOOLS / "ingest_forge_accepts_into_distillery.py"
)
bridge = importlib.util.module_from_spec(bridge_spec)
bridge_spec.loader.exec_module(bridge)

helper_spec = importlib.util.spec_from_file_location(
    "replay_identity_873_helper", ROOT / "tests" / "test_forge_distillery_replay_identity_873.py"
)
helper = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(helper)
accepted_row = helper.accepted_row


class EnvelopeReplayIdentity873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, *rows):
        self.eval.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
        )

    def test_delta_id_timestamp_and_narration_replay_is_duplicate(self):
        first_row = accepted_row()
        self.write(first_row)
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]

        replay = accepted_row(
            delta_id="d-envelope-rekeyed",
            evaluated_at="2026-08-25T01:15:00+07:00",
            proposal_hypothesis="new candidate narration only",
            falsifier="new candidate falsifier only",
        )
        self.write(replay)
        second = bridge.ingest(self.eval, self.db)

        self.assertEqual(first["admitted"], 1)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_envelope_rekey_does_not_change_replay_or_measured_identity(self):
        first = accepted_row()
        replay = accepted_row(
            delta_id="d-envelope-rekeyed",
            evaluated_at="2026-08-25T01:16:00+07:00",
            proposal_hypothesis="different candidate narration",
            falsifier="different candidate falsifier",
        )

        self.assertNotIn("delta_id", bridge.execution_replay_identity(first))
        self.assertNotIn("delta_id", bridge.measured_packet(first))
        self.assertNotIn("evaluated_at", bridge.measured_packet(first))
        self.assertEqual(
            bridge.execution_replay_identity(first),
            bridge.execution_replay_identity(replay),
        )
        self.assertEqual(
            bridge.measured_evidence_identity(first),
            bridge.measured_evidence_identity(replay),
        )

    def test_measurement_mutation_conflicts_even_when_delta_id_changes(self):
        self.write(accepted_row())
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]

        mutated = accepted_row(
            delta_id="d-envelope-rekeyed",
            evaluated_at="2026-08-25T01:17:00+07:00",
            relative_improvement_pct=75.0,
        )
        self.write(mutated)
        second = bridge.ingest(self.eval, self.db)

        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 0)
        self.assertEqual(second["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_fresh_rebuilds_emit_identical_training_packet_for_envelope_rekey(self):
        rows = [
            accepted_row(),
            accepted_row(
                delta_id="d-envelope-rekeyed",
                evaluated_at="2026-08-25T01:18:00+07:00",
                proposal_hypothesis="different candidate narration",
                falsifier="different candidate falsifier",
            ),
        ]
        observed = []
        for index, row in enumerate(rows):
            eval_path = self.root / f"eval-{index}.jsonl"
            db_path = self.root / f"distillery-{index}.sqlite3"
            eval_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = bridge.ingest(eval_path, db_path)
            self.assertEqual(result["admitted"], 1)
            con = sqlite3.connect(db_path)
            packet_id, packet_text = con.execute(
                "SELECT id,packet_text FROM knowledge_packets"
            ).fetchone()
            replay_sha, measured_sha = con.execute(
                "SELECT execution_replay_identity_sha256,measured_evidence_sha256 "
                "FROM forge_execution_ingest"
            ).fetchone()
            con.close()
            observed.append(
                (
                    result["packet_ids"],
                    result["accepted_dataset_tokens_counter"],
                    packet_id,
                    packet_text,
                    replay_sha,
                    measured_sha,
                )
            )

        self.assertEqual(observed[0], observed[1])


if __name__ == "__main__":
    unittest.main()
