#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_conversion_backpressure_872 as bp


class ConversionBackpressure872(unittest.TestCase):
    def test_zero_yield_lowers_only_to_caps(self):
        with tempfile.TemporaryDirectory() as td:
            art = Path(td)
            (art / "distillery").mkdir()
            (art / "forge").mkdir()
            (art / "distillery" / "STATUS.json").write_text(
                json.dumps(
                    {
                        "accepted_dataset_tokens": 0,
                        "forge_evidence_qualified_packets": 0,
                    }
                )
            )
            (art / "forge" / "STATUS.json").write_text(
                json.dumps({"accepted_deltas": 1})
            )
            env = {
                "CLAY_NVIDIA_MAX_CONCURRENCY": "256",
                "CLAY_GROQ_MAX_CONCURRENCY": "2",
            }
            got = bp.apply(art, env)
            self.assertTrue(got["apply_backpressure"])
            self.assertEqual("24", env["CLAY_NVIDIA_MAX_CONCURRENCY"])
            # Never raise an already-lower operator/runtime limit.
            self.assertEqual("2", env["CLAY_GROQ_MAX_CONCURRENCY"])
            self.assertEqual("4", env["CLAY_MISTRAL_MAX_CONCURRENCY"])
            self.assertEqual("2", env["CLAY_OPENROUTER_MAX_CONCURRENCY"])
            self.assertEqual("64", env["CLAY_SWARM_HTTP_THREADS"])
            self.assertFalse(got["runtime_credit_minted"])

    def test_nonzero_qualified_packet_and_tokens_releases(self):
        with tempfile.TemporaryDirectory() as td:
            art = Path(td)
            (art / "distillery").mkdir()
            (art / "distillery" / "STATUS.json").write_text(
                json.dumps(
                    {
                        "accepted_dataset_tokens": 73,
                        "forge_evidence_qualified_packets": 1,
                    }
                )
            )
            env = {"CLAY_NVIDIA_MAX_CONCURRENCY": "31"}
            got = bp.apply(art, env)
            self.assertFalse(got["apply_backpressure"])
            self.assertEqual("31", env["CLAY_NVIDIA_MAX_CONCURRENCY"])
            self.assertEqual({}, got["applied_limits"])

    def test_inconsistent_partial_success_stays_capped(self):
        self.assertTrue(
            bp.decision(
                {
                    "accepted_dataset_tokens": 73,
                    "forge_evidence_qualified_packets": 0,
                }
            )["apply_backpressure"]
        )
        self.assertTrue(
            bp.decision(
                {
                    "accepted_dataset_tokens": 0,
                    "forge_evidence_qualified_packets": 1,
                }
            )["apply_backpressure"]
        )

    def test_db_counters_override_stale_zero_status(self):
        with tempfile.TemporaryDirectory() as td:
            art = Path(td)
            d = art / "distillery"
            d.mkdir()
            (d / "STATUS.json").write_text(
                json.dumps(
                    {
                        "accepted_dataset_tokens": 0,
                        "forge_evidence_qualified_packets": 0,
                    }
                )
            )
            con = sqlite3.connect(d / "distillery.sqlite3")
            con.execute("CREATE TABLE counters(key TEXT PRIMARY KEY, value INTEGER)")
            con.execute("CREATE TABLE knowledge_packets(packet_id TEXT PRIMARY KEY)")
            con.execute(
                "INSERT INTO counters(key,value) VALUES('accepted_dataset_tokens',91)"
            )
            con.execute(
                "INSERT INTO counters(key,value) VALUES('forge_evidence_qualified_packets',1)"
            )
            con.execute("INSERT INTO knowledge_packets(packet_id) VALUES('p1')")
            con.commit()
            con.close()
            got = bp.funnel_snapshot(art)
            self.assertEqual(91, got["accepted_dataset_tokens"])
            self.assertEqual(1, got["forge_evidence_qualified_packets"])
            self.assertEqual(1, got["accepted_packets"])

    def test_invalid_env_value_fails_to_conservative_default_then_cap(self):
        env = {"CLAY_NVIDIA_MAX_CONCURRENCY": "not-an-int"}
        chosen = bp._lower_int_env(env, "CLAY_NVIDIA_MAX_CONCURRENCY", 24, 256)
        self.assertEqual(24, chosen)
        self.assertEqual("24", env["CLAY_NVIDIA_MAX_CONCURRENCY"])


if __name__ == "__main__":
    unittest.main()
