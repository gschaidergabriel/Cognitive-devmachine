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
    "bridge_training_packet_rebuild_873", TOOLS / "ingest_forge_accepts_into_distillery.py"
)
bridge = importlib.util.module_from_spec(bridge_spec)
bridge_spec.loader.exec_module(bridge)

helper_spec = importlib.util.spec_from_file_location(
    "replay_identity_873_helper", ROOT / "tests" / "test_forge_distillery_replay_identity_873.py"
)
helper = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(helper)
accepted_row = helper.accepted_row


class TrainingPacketRebuildStable873Tests(unittest.TestCase):
    def test_envelope_only_fields_are_not_training_packet_evidence(self):
        first = accepted_row()
        replay = accepted_row(
            delta_id="d-envelope-rekeyed",
            evaluated_at="2026-08-25T01:20:00+07:00",
            proposal_hypothesis="different candidate narration",
            falsifier="different candidate falsifier",
        )

        packet_first = bridge.measured_packet(first)
        packet_replay = bridge.measured_packet(replay)
        self.assertNotIn("delta_id", packet_first)
        self.assertNotIn("evaluated_at", packet_first)
        self.assertEqual(packet_first, packet_replay)
        self.assertEqual(
            bridge.measured_evidence_identity(first),
            bridge.measured_evidence_identity(replay),
        )
        self.assertEqual(
            bridge.execution_replay_identity(first),
            bridge.execution_replay_identity(replay),
        )

    def test_fresh_rebuilds_from_equivalent_envelopes_emit_identical_training_bytes(self):
        rows = [
            accepted_row(),
            accepted_row(
                delta_id="d-envelope-rekeyed",
                evaluated_at="2026-08-25T01:21:00+07:00",
                proposal_hypothesis="different candidate narration",
                falsifier="different candidate falsifier",
            ),
        ]
        observed = []
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            for index, row in enumerate(rows):
                eval_path = root_path / f"eval-{index}.jsonl"
                db_path = root_path / f"distillery-{index}.sqlite3"
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
