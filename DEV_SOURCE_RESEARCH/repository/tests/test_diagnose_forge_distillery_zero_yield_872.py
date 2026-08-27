import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import diagnose_forge_distillery_zero_yield_872 as diag


def execution_admission(source_head="a" * 40, evaluation_head="c" * 40):
    return {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_identity_admitted": True,
        "source_head": source_head,
        "evaluation_checkout_head": evaluation_head,
        "all_commands_admitted": True,
        "decisions": [{"admitted": True, "reason": "ALLOWLISTED_PYTEST"}],
        "candidate_is_canonical_truth": False,
        "backend": {
            "admitted": True,
            "backend": "bubblewrap_unshare_all",
            "network_namespace": "ISOLATED",
            "secret_environment_inherited": False,
            "host_secret_paths_exposed": False,
        },
    }


def accepted_row(qualified=True, suffix="1"):
    row = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "delta_id": "d-" + suffix,
        "worker_sha": "b" * 64,
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "status": "accepted",
        "relative_improvement_pct": 50.0,
        "reproducible_runs": 2,
        "tests_passed": 4,
        "tests_failed": 0,
        "negative_tests_failed": 0,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "target_blob_identities": {"tools/example.py": "d" * 40},
    }
    if qualified:
        row["execution_admission"] = execution_admission()
    return row


def write_ledger(path, *rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def ensure_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE counters(key TEXT PRIMARY KEY,value INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE knowledge_packets(id TEXT PRIMARY KEY,approx_tokens INTEGER NOT NULL);
    CREATE TABLE forge_execution_ingest(
      evaluation_sha256 TEXT PRIMARY KEY,
      packet_id TEXT NOT NULL UNIQUE,
      approx_tokens INTEGER NOT NULL
    );
    """)
    con.commit()
    con.close()


def add_counter(con, key, value):
    con.execute("INSERT INTO counters(key,value) VALUES(?,?)", (key, value))


def add_forge_packet(con, packet_id="p-forge", tokens=13, digest="e" * 64):
    con.execute("INSERT INTO knowledge_packets(id,approx_tokens) VALUES(?,?)", (packet_id, tokens))
    con.execute(
        "INSERT INTO forge_execution_ingest(evaluation_sha256,packet_id,approx_tokens) VALUES(?,?,?)",
        (digest, packet_id, tokens),
    )


class ZeroYieldDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.ledger = self.root / "forge.jsonl"
        self.db = self.root / "distillery.sqlite3"

    def tearDown(self):
        self.td.cleanup()

    def test_nominal_only_is_explicitly_not_evidence_qualified(self):
        write_ledger(self.ledger, accepted_row(False))
        ensure_db(self.db)
        got = diag.diagnose(self.ledger, self.db)
        self.assertFalse(got["gate_open"])
        self.assertEqual("NOMINAL_ACCEPT_NOT_EVIDENCE_QUALIFIED", got["classification"])
        self.assertEqual(1, got["forge"]["nominal_accepted"])
        self.assertEqual(0, got["forge"]["evidence_qualified_accepted"])

    def test_unrelated_distillery_baseline_does_not_fake_forge_provenance(self):
        write_ledger(self.ledger, accepted_row(False))
        ensure_db(self.db)
        con = sqlite3.connect(self.db)
        con.execute("INSERT INTO knowledge_packets(id,approx_tokens) VALUES('unrelated',200)")
        add_counter(con, "accepted_dataset_tokens", 200)
        add_counter(con, "accepted_packets", 1)
        con.commit()
        con.close()
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("NOMINAL_ACCEPT_NOT_EVIDENCE_QUALIFIED", got["classification"])
        self.assertFalse(got["gate_open"])

    def test_forge_specific_db_evidence_without_qualified_ledger_is_provenance_unbound(self):
        write_ledger(self.ledger, accepted_row(False))
        ensure_db(self.db)
        con = sqlite3.connect(self.db)
        add_forge_packet(con)
        add_counter(con, "forge_execution_packets", 1)
        add_counter(con, "forge_evidence_qualified_packets", 1)
        add_counter(con, "accepted_dataset_tokens", 13)
        add_counter(con, "accepted_packets", 1)
        con.commit()
        con.close()
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("FORGE_LEDGER_DB_PROVENANCE_UNBOUND", got["classification"])
        self.assertFalse(got["gate_open"])

    def test_qualified_accept_without_ingest_is_distinguished(self):
        write_ledger(self.ledger, accepted_row(True))
        ensure_db(self.db)
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("EVIDENCE_QUALIFIED_ACCEPT_NOT_INGESTED", got["classification"])
        self.assertFalse(got["gate_open"])

    def test_partial_ingest_is_distinguished(self):
        write_ledger(self.ledger, accepted_row(True, "1"), accepted_row(True, "2"))
        ensure_db(self.db)
        con = sqlite3.connect(self.db)
        add_forge_packet(con)
        add_counter(con, "accepted_dataset_tokens", 13)
        add_counter(con, "accepted_packets", 1)
        add_counter(con, "forge_execution_packets", 1)
        add_counter(con, "forge_evidence_qualified_packets", 1)
        con.commit()
        con.close()
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("EVIDENCE_QUALIFIED_ACCEPT_PARTIALLY_INGESTED", got["classification"])
        self.assertFalse(got["gate_open"])

    def test_consistent_qualified_packet_with_preexisting_baseline_opens_component_gate(self):
        write_ledger(self.ledger, accepted_row(True))
        ensure_db(self.db)
        con = sqlite3.connect(self.db)
        con.execute("INSERT INTO knowledge_packets(id,approx_tokens) VALUES('unrelated',100)")
        add_forge_packet(con)
        for key, value in [
            ("accepted_dataset_tokens", 113),
            ("accepted_packets", 2),
            ("forge_execution_packets", 1),
            ("forge_evidence_qualified_packets", 1),
        ]:
            add_counter(con, key, value)
        con.commit()
        con.close()
        got = diag.diagnose(self.ledger, self.db)
        self.assertTrue(got["gate_open"])
        self.assertEqual("FORGE_TO_DISTILLERY_DATASET_GATE_OPEN", got["classification"])
        self.assertEqual(0, got["training_credit"])
        self.assertEqual(0, got["jspace_model_runtime_credit"])

    def test_global_token_counter_below_forge_sum_is_inconsistent(self):
        write_ledger(self.ledger, accepted_row(True))
        ensure_db(self.db)
        con = sqlite3.connect(self.db)
        add_forge_packet(con, tokens=13)
        for key, value in [
            ("accepted_dataset_tokens", 12),
            ("accepted_packets", 1),
            ("forge_execution_packets", 1),
            ("forge_evidence_qualified_packets", 1),
        ]:
            add_counter(con, key, value)
        con.commit()
        con.close()
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("TOKEN_LEDGER_INCONSISTENT", got["classification"])
        self.assertFalse(got["gate_open"])

    def test_forge_specific_packet_counter_mismatch_is_inconsistent(self):
        write_ledger(self.ledger, accepted_row(True))
        ensure_db(self.db)
        con = sqlite3.connect(self.db)
        add_forge_packet(con, tokens=13)
        for key, value in [
            ("accepted_dataset_tokens", 13),
            ("accepted_packets", 1),
            ("forge_execution_packets", 0),
            ("forge_evidence_qualified_packets", 1),
        ]:
            add_counter(con, key, value)
        con.commit()
        con.close()
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("FORGE_PACKET_LEDGER_INCONSISTENT", got["classification"])
        self.assertFalse(got["gate_open"])

    def test_missing_db_after_qualified_accept_is_explicit(self):
        write_ledger(self.ledger, accepted_row(True))
        got = diag.diagnose(self.ledger, self.db)
        self.assertEqual("QUALIFIED_ACCEPT_DB_MISSING", got["classification"])
        self.assertFalse(got["gate_open"])


if __name__ == "__main__":
    unittest.main()
