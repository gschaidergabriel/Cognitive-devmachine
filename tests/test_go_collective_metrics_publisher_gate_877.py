from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / "free swarm/go_collective_metrics.py"


class GoCollectiveMetricsPublisherGate877Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "free swarm").mkdir(parents=True)
        (self.repo / "research_entity/claycode/autonomous").mkdir(parents=True)
        (self.repo / "research_entity/continuity/go_metrics").mkdir(parents=True)
        self._write(
            "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json",
            {
                "schema": "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1",
                "code_quality": {"weights": {}, "min_evidence_coverage": 0.6},
                "innovation": {"weights": {}},
                "capability_information_latency": {"measurement_floor_seconds": 0.001},
                "hcu_confidence": {
                    "event": "HCU_TARGET_100_GO",
                    "event_definition": "test fixture",
                    "milestones": [],
                    "initial_research_baseline": {"milestone_probabilities": {}},
                },
                "anti_goodhart": {"fixture": True},
                "selection_policy": {"mode": "PARETO_TEST_ONLY"},
            },
        )
        self._write(
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            {
                "schema_version": "8.77",
                "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            },
        )
        self._write(
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            {"schema_version": "8.77", "program": "ENTITYOS_HCU", "product": "EntityOS"},
        )
        self._write(
            "free swarm/LIVE_METRICS.json",
            {
                "generated_at": "2026-08-25T02:00:00Z",
                "workers": {
                    "worker_records": 6,
                    "exact_usage_rows": 6,
                    "input_tokens": 20,
                    "output_tokens": 10,
                    "total_tokens": 30,
                },
            },
        )
        self._write(
            "free swarm/FORGE_LIVE.json",
            {
                "generated_at": "2026-08-25T02:00:01Z",
                "discovery_hits": 4,
                "evaluations": 3,
                "accepted_deltas": 1,
            },
        )
        self._write(
            "free swarm/DISTILLERY_LIVE.json",
            {
                "generated_at": "2026-08-25T02:00:02Z",
                "collected_source_tokens": 12,
                "collected_chunks": 2,
                "accepted_packets": 0,
                "accepted_dataset_tokens": 0,
            },
        )
        self.out_json = self.repo / "free swarm/GO_COLLECTIVE_METRICS.json"
        self.out_md = self.repo / "free swarm/GO_COLLECTIVE_METRICS.md"
        self.receipt = self.repo / "research_entity/continuity/receipts/COLLECTIVE_METRICS_FRESHNESS_LATEST.json"
        self.out_json.write_text(
            json.dumps(
                {
                    "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
                    "authority_epoch": "8.71",
                    "generated_at": "2026-08-24T13:58:54Z",
                    "source_metrics": {"total_tokens": 7302860},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel: str, value: dict):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    def _run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(CORE_PATH),
                "--repo",
                str(self.repo),
                "--artifacts",
                str(self.repo / "missing-artifacts"),
                "--output-json",
                str(self.out_json),
                "--output-md",
                str(self.out_md),
                "--freshness-receipt",
                str(self.receipt),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_source_has_no_direct_canonical_output_write_bypass(self):
        source = CORE_PATH.read_text(encoding="utf-8")
        self.assertIn("freshness.publish_candidate(", source)
        self.assertNotIn("out_json.write_text(", source)
        self.assertNotIn("out_md.write_text(", source)

    def test_existing_publisher_emits_bound_json_markdown_and_idempotent_replay(self):
        first = self._run()
        self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)

        published = json.loads(self.out_json.read_text(encoding="utf-8"))
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        markdown = self.out_md.read_text(encoding="utf-8")

        self.assertEqual(published["authority_epoch"], "8.77")
        self.assertEqual(published["source_metrics"]["total_tokens"], 30)
        self.assertEqual(published["source_metrics"]["forge_evaluations"], 3)
        self.assertEqual(published["source_metrics"]["distillery_accepted_dataset_tokens"], 0)
        self.assertEqual(published["freshness"]["state"], "FRESH_BOUND_SNAPSHOT")
        self.assertEqual(receipt["schema"], "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1")
        self.assertEqual(receipt["decision"]["action"], "PUBLISH")
        self.assertEqual(receipt["decision"]["current_state"], "HISTORICAL_AUTHORITY")
        snapshot_id = published["freshness"]["snapshot"]["snapshot_id"]
        self.assertIn(snapshot_id, markdown.splitlines()[0])

        first_json = self.out_json.read_bytes()
        first_md = self.out_md.read_bytes()
        second = self._run()
        self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
        replay_receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(replay_receipt["decision"]["action"], "NO_CHANGE")
        self.assertEqual(replay_receipt["decision"]["reason"], "IDEMPOTENT_REPLAY")
        self.assertEqual(self.out_json.read_bytes(), first_json)
        self.assertEqual(self.out_md.read_bytes(), first_md)


if __name__ == "__main__":
    unittest.main()
