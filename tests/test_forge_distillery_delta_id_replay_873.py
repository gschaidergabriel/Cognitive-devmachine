import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import ingest_forge_accepts_into_distillery as bridge
from tests.test_forge_distillery_replay_identity_873 import accepted_row


class DeltaIdReplayIdentity873Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.eval = self.root / "eval.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def write(self, *rows):
        self.eval.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )

    def insert_pre_v2_row(self, row):
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,execution_replay_identity_sha256,"
            "execution_replay_identity_schema,measured_evidence_sha256,packet_id,"
            "delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                bridge.digest_json(row),
                bridge.digest_json(bridge.execution_replay_identity_v1(row)),
                None,
                bridge.digest_json(bridge.measured_evidence_identity_v1(row)),
                "kf-pre-v2-existing",
                row["delta_id"],
                row["worker_sha"],
                row["source_repo_head"],
                row["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

    def test_delta_id_only_replay_is_duplicate_and_token_stable(self):
        first_row = accepted_row()
        self.write(first_row)
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]
        packet_ids = list(first["packet_ids"])

        replay = accepted_row(
            delta_id="d-replay-envelope-renamed",
            evaluated_at="2026-08-24T16:31:59+00:00",
        )
        self.assertEqual(
            bridge.digest_json(bridge.execution_replay_identity(first_row)),
            bridge.digest_json(bridge.execution_replay_identity(replay)),
        )
        self.assertEqual(
            bridge.digest_json(bridge.measured_evidence_identity(first_row)),
            bridge.digest_json(bridge.measured_evidence_identity(replay)),
        )

        self.write(replay)
        second = bridge.ingest(self.eval, self.db)

        self.assertEqual(first["admitted"], 1)
        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0), 0)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)

        con = sqlite3.connect(self.db)
        persisted_ids = [row[0] for row in con.execute("SELECT id FROM knowledge_packets ORDER BY id")]
        schemas = [row[0] for row in con.execute("SELECT execution_replay_identity_schema FROM forge_execution_ingest")]
        con.close()
        self.assertEqual(persisted_ids, packet_ids)
        self.assertEqual(schemas, [bridge.REPLAY_IDENTITY_V2])

    def test_delta_id_rekey_with_measurement_mutation_fails_closed(self):
        self.write(accepted_row())
        first = bridge.ingest(self.eval, self.db)
        token_count = first["accepted_dataset_tokens_counter"]

        mutated = accepted_row(
            delta_id="d-replay-envelope-renamed",
            evaluated_at="2026-08-24T16:32:01+00:00",
            relative_improvement_pct=75.0,
        )
        self.write(mutated)
        second = bridge.ingest(self.eval, self.db)

        self.assertEqual(second["admitted"], 0)
        self.assertEqual(second["duplicates"], 0)
        self.assertEqual(second["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(second["accepted_dataset_tokens_counter"], token_count)
        self.assertEqual(second["forge_execution_packets_total"], 1)

    def test_pre_v2_delta_id_rekey_is_recovered_as_duplicate(self):
        original = accepted_row()
        self.insert_pre_v2_row(original)

        replay = accepted_row(
            delta_id="renamed-after-v2-upgrade",
            evaluated_at="2026-08-24T16:33:00+00:00",
            proposal_hypothesis="new envelope narration",
        )
        self.write(replay)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 1)
        self.assertEqual(out["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0), 0)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_pre_v2_delta_id_rekey_with_measurement_mutation_conflicts(self):
        original = accepted_row()
        self.insert_pre_v2_row(original)

        mutated = accepted_row(
            delta_id="renamed-after-v2-upgrade",
            evaluated_at="2026-08-24T16:33:01+00:00",
            relative_improvement_pct=75.0,
        )
        self.write(mutated)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_legacy_collision_cannot_be_evaded_by_delta_id_rekey(self):
        row = accepted_row()
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?)",
            (
                "9" * 64,
                "kf-legacy-existing",
                "legacy-original-delta-id",
                row["worker_sha"],
                row["source_repo_head"],
                row["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

        row["delta_id"] = "new-envelope-id"
        self.write(row)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)
        self.assertEqual(out["forge_execution_packets_total"], 1)


if __name__ == "__main__":
    unittest.main()
