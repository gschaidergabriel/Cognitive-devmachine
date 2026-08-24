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


class ReplayIdentityV2Migration873Tests(unittest.TestCase):
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

    def insert_v1_row(self, row, *, variant):
        if variant == "legacy_delta_bound":
            replay_sha = bridge.digest_json(bridge.execution_replay_identity_v1_legacy(row))
            measured_sha = bridge.digest_json(bridge.measured_evidence_identity_v1_legacy(row))
        elif variant == "replay_stable":
            replay_sha = bridge.digest_json(bridge.execution_replay_identity_v1_current(row))
            measured_sha = bridge.digest_json(bridge.measured_evidence_identity_v1_current(row))
        else:
            raise AssertionError(variant)

        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,execution_replay_identity_sha256,measured_evidence_sha256,"
            "packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                bridge.digest_json(row),
                replay_sha,
                measured_sha,
                f"kf-v1-{variant}",
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

    def test_new_rows_are_explicitly_v2(self):
        row = accepted_row()
        self.write(row)
        out = bridge.ingest(self.eval, self.db)
        self.assertEqual(out["admitted"], 1)
        self.assertEqual(bridge.execution_replay_identity(row)["schema"], bridge.REPLAY_IDENTITY_V2)
        self.assertEqual(bridge.measured_evidence_identity(row)["schema"], bridge.MEASURED_IDENTITY_V2)

        con = sqlite3.connect(self.db)
        stored = con.execute(
            "SELECT execution_replay_identity_schema, measured_evidence_identity_schema "
            "FROM forge_execution_ingest"
        ).fetchone()
        con.close()
        self.assertEqual(stored, (bridge.REPLAY_IDENTITY_V2, bridge.MEASURED_IDENTITY_V2))

    def test_legacy_delta_bound_v1_rekey_is_duplicate(self):
        original = accepted_row()
        self.insert_v1_row(original, variant="legacy_delta_bound")

        replay = accepted_row(
            delta_id="renamed-envelope",
            evaluated_at="2026-08-24T16:41:00+00:00",
            proposal_hypothesis="new narration only",
            falsifier="new falsifier only",
        )
        self.write(replay)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 1)
        self.assertEqual(out["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0), 0)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_legacy_delta_bound_v1_measurement_mutation_conflicts(self):
        original = accepted_row()
        self.insert_v1_row(original, variant="legacy_delta_bound")

        mutated = accepted_row(
            delta_id="renamed-envelope",
            evaluated_at="2026-08-24T16:41:01+00:00",
            relative_improvement_pct=75.0,
        )
        self.write(mutated)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_replay_stable_v1_rekey_is_duplicate(self):
        original = accepted_row()
        self.insert_v1_row(original, variant="replay_stable")

        replay = accepted_row(
            delta_id="renamed-envelope",
            evaluated_at="2026-08-24T16:42:00+00:00",
        )
        self.write(replay)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 1)
        self.assertEqual(out["rejected"].get("REPLAY_IDENTITY_CONFLICT", 0), 0)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_replay_stable_v1_measurement_mutation_conflicts(self):
        original = accepted_row()
        self.insert_v1_row(original, variant="replay_stable")

        mutated = accepted_row(
            delta_id="renamed-envelope",
            evaluated_at="2026-08-24T16:42:01+00:00",
            relative_improvement_pct=75.0,
        )
        self.write(mutated)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("REPLAY_IDENTITY_CONFLICT"), 1)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_pre_hash_legacy_row_remains_fail_closed_after_delta_id_rekey(self):
        row = accepted_row()
        con = sqlite3.connect(self.db)
        bridge.ensure_schema(con)
        con.execute(
            "INSERT INTO forge_execution_ingest("
            "evaluation_sha256,packet_id,delta_id,worker_sha,source_repo_head,evaluation_repo_head,admitted_at,approx_tokens"
            ") VALUES(?,?,?,?,?,?,?,?)",
            (
                "9" * 64,
                "kf-pre-hash-existing",
                "old-envelope",
                row["worker_sha"],
                row["source_repo_head"],
                row["evaluation_repo_head"],
                "2026-08-24T00:00:00+00:00",
                123,
            ),
        )
        con.commit()
        con.close()

        row["delta_id"] = "new-envelope"
        self.write(row)
        out = bridge.ingest(self.eval, self.db)

        self.assertEqual(out["admitted"], 0)
        self.assertEqual(out["duplicates"], 0)
        self.assertEqual(out["rejected"].get("LEGACY_REPLAY_IDENTITY_UNRESOLVED"), 1)
        self.assertEqual(out["forge_execution_packets_total"], 1)

    def test_schema_migration_is_additive(self):
        con = sqlite3.connect(self.db)
        con.execute(
            "CREATE TABLE forge_execution_ingest("
            "evaluation_sha256 TEXT PRIMARY KEY, packet_id TEXT NOT NULL UNIQUE, "
            "delta_id TEXT, worker_sha TEXT NOT NULL, source_repo_head TEXT NOT NULL, "
            "evaluation_repo_head TEXT NOT NULL, admitted_at TEXT NOT NULL, approx_tokens INTEGER NOT NULL)"
        )
        con.commit()
        bridge.ensure_schema(con)
        columns = {row[1] for row in con.execute("PRAGMA table_info(forge_execution_ingest)")}
        con.close()
        self.assertIn("execution_replay_identity_sha256", columns)
        self.assertIn("execution_replay_identity_schema", columns)
        self.assertIn("measured_evidence_sha256", columns)
        self.assertIn("measured_evidence_identity_schema", columns)


if __name__ == "__main__":
    unittest.main()
