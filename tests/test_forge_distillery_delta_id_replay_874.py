import json
from pathlib import Path
import tempfile
import unittest

from tests.test_forge_distillery_replay_identity_873 import accepted_row, bridge


class DeltaIdReplayIdentity874Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, *rows):
        self.eval.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def test_delta_id_is_not_part_of_replay_or_measured_identity(self):
        first = accepted_row(delta_id="candidate-envelope-a")
        replay = accepted_row(delta_id="candidate-envelope-b")
        self.assertNotIn("delta_id", bridge.execution_replay_identity(first))
        self.assertEqual(
            bridge.digest_json(bridge.execution_replay_identity(first)),
            bridge.digest_json(bridge.execution_replay_identity(replay)),
        )
        self.assertEqual(
            bridge.digest_json(bridge.measured_evidence_identity(first)),
            bridge.digest_json(bridge.measured_evidence_identity(replay)),
        )

    def test_delta_id_only_rekey_is_duplicate_and_token_stable(self):
        self.write(accepted_row(delta_id="candidate-envelope-a"))
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]

        replay = accepted_row(
            delta_id="candidate-envelope-b",
            evaluated_at="2026-08-25T01:05:00+07:00",
        )
        self.write(replay)
        second = bridge.ingest(self.eval, self.db)

        self.assertEqual(first["admitted"], 1)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0), 0)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)


if __name__ == "__main__":
    unittest.main()
