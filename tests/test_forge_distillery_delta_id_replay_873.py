import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tests.test_forge_distillery_replay_identity_873 import accepted_row, bridge


class DeltaIdReplay873Tests(unittest.TestCase):
    def test_delta_id_only_mutation_does_not_rekey_measured_execution(self):
        first = accepted_row(delta_id="candidate-envelope-a")
        replay = accepted_row(delta_id="candidate-envelope-b")

        self.assertNotIn("delta_id", bridge.execution_replay_identity(first))
        self.assertEqual(
            bridge.execution_replay_identity(first),
            bridge.execution_replay_identity(replay),
        )
        self.assertNotIn("delta_id", bridge.measured_packet(first))
        self.assertEqual(bridge.measured_packet(first), bridge.measured_packet(replay))
        self.assertEqual(
            bridge.measured_evidence_identity(first),
            bridge.measured_evidence_identity(replay),
        )

    def test_delta_id_only_replay_is_duplicate_with_zero_token_delta(self):
        first = accepted_row(delta_id="candidate-envelope-a")
        replay = accepted_row(delta_id="candidate-envelope-b")

        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            eval_path = root_path / "forge.jsonl"
            db_path = root_path / "distillery.sqlite3"

            eval_path.write_text(json.dumps(first) + "\n", encoding="utf-8")
            initial = bridge.ingest(eval_path, db_path)
            initial_tokens = initial["accepted_dataset_tokens_counter"]

            eval_path.write_text(json.dumps(replay) + "\n", encoding="utf-8")
            repeated = bridge.ingest(eval_path, db_path)

            self.assertEqual(initial["admitted"], 1)
            self.assertEqual(repeated["admitted"], 0)
            self.assertEqual(repeated["duplicates"], 1)
            self.assertEqual(repeated["rejected"], {})
            self.assertEqual(repeated["accepted_dataset_tokens_counter"], initial_tokens)
            self.assertEqual(repeated["forge_execution_packets_total"], 1)

    def test_fresh_rebuilds_with_only_delta_id_changed_are_byte_stable(self):
        rows = [
            accepted_row(delta_id="candidate-envelope-a"),
            accepted_row(delta_id="candidate-envelope-b"),
        ]
        observed = []
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            for index, row in enumerate(rows):
                eval_path = root_path / f"forge-{index}.jsonl"
                db_path = root_path / f"distillery-{index}.sqlite3"
                eval_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                result = bridge.ingest(eval_path, db_path)
                self.assertEqual(result["admitted"], 1)

                con = sqlite3.connect(db_path)
                packet_id, packet_text = con.execute(
                    "SELECT id, packet_text FROM knowledge_packets"
                ).fetchone()
                replay_sha, measured_sha = con.execute(
                    "SELECT execution_replay_identity_sha256, measured_evidence_sha256 "
                    "FROM forge_execution_ingest"
                ).fetchone()
                con.close()

                observed.append(
                    (
                        packet_id,
                        packet_text,
                        replay_sha,
                        measured_sha,
                        result["accepted_dataset_tokens_counter"],
                    )
                )

        self.assertEqual(observed[0], observed[1])


if __name__ == "__main__":
    unittest.main()
