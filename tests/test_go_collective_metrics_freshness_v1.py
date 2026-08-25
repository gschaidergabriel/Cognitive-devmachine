from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def seed_snapshot(repo: Path, *, epoch: str = "8.77", swarm_ts: str = "2026-08-25T02:00:00+00:00",
                  forge_ts: str = "2026-08-25T02:00:01+00:00", dist_ts: str = "2026-08-25T02:00:02+00:00") -> None:
    write_json(repo / "free swarm/LIVE_METRICS.json", {
        "schema": "CLAY_FREE_SWARM_METRICS/v1", "generated_at": swarm_ts,
        "workers": {"worker_records": 10, "exact_usage_rows": 8, "input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        "deltas": {"accepted": 1},
    })
    write_json(repo / "free swarm/FORGE_LIVE.json", {
        "generated_at": forge_ts, "evaluations": 7, "accepted_deltas": 1,
    })
    write_json(repo / "free swarm/DISTILLERY_LIVE.json", {
        "generated_at": dist_ts, "collected_source_tokens": 300,
        "accepted_packets": 1, "accepted_dataset_tokens": 40,
    })
    write_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "schema_version": epoch, "active_program": "ENTITYOS_HCU",
    })


class CollectiveMetricsFreshnessV1Tests(unittest.TestCase):
    def test_newer_live_input_makes_older_aggregate_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_snapshot(repo)
            snap = metrics.capture_input_snapshot(repo)
            self.assertTrue(snap["ok"])
            candidate = {
                "authority_epoch": "8.77",
                "generated_at": "2026-08-25T02:00:03+00:00",
                "freshness": {"input_watermark": snap["input_watermark"], "snapshot_id": snap["snapshot_id"]},
                "measurement_digest_sha256": "new",
            }
            existing = {
                "authority_epoch": "8.77",
                "generated_at": "2026-08-25T01:00:00+00:00",
                "freshness": {"input_watermark": "2026-08-25T01:00:00+00:00", "snapshot_id": "old"},
                "measurement_digest_sha256": "old",
            }
            decision = metrics.publication_decision(existing, candidate)
            self.assertTrue(decision["allow"])
            self.assertEqual(decision["status"], "NEWER_OR_CHANGED_MEASUREMENT")

    def test_authority_epoch_regression_is_historical_fail_closed(self):
        existing = {
            "authority_epoch": "8.78",
            "freshness": {"input_watermark": "2026-08-25T02:00:02+00:00", "snapshot_id": "newer"},
            "measurement_digest_sha256": "newer",
        }
        candidate = {
            "authority_epoch": "8.77",
            "freshness": {"input_watermark": "2026-08-25T02:00:03+00:00", "snapshot_id": "older-authority"},
            "measurement_digest_sha256": "candidate",
        }
        decision = metrics.publication_decision(existing, candidate)
        self.assertFalse(decision["allow"])
        self.assertEqual(decision["status"], "HISTORICAL_AUTHORITY_EPOCH")

    def test_older_writer_finishing_late_cannot_regress_latest(self):
        existing = {
            "authority_epoch": "8.77",
            "freshness": {"input_watermark": "2026-08-25T02:00:10+00:00", "snapshot_id": "later"},
            "measurement_digest_sha256": "later-digest",
        }
        late_old_writer = {
            "authority_epoch": "8.77",
            "freshness": {"input_watermark": "2026-08-25T02:00:02+00:00", "snapshot_id": "earlier"},
            "measurement_digest_sha256": "earlier-digest",
        }
        decision = metrics.publication_decision(existing, late_old_writer)
        self.assertFalse(decision["allow"])
        self.assertEqual(decision["status"], "OUT_OF_ORDER_OLDER_WRITER")

    def test_same_bounded_inputs_have_identical_snapshot_and_measurement_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_snapshot(repo)
            first = metrics.capture_input_snapshot(repo)
            second = metrics.capture_input_snapshot(repo)
            self.assertEqual(first["snapshot_id"], second["snapshot_id"])
            base = {
                "schema": metrics.SCHEMA, "authority_epoch": first["authority_epoch"],
                "config_sha256": "config", "freshness": {"snapshot_id": first["snapshot_id"]},
                "source_metrics": metrics.source_metrics_from_snapshot(first),
                "aggregate": {"total_tokens": 150}, "anti_goodhart": {"x": True},
                "selection_policy": "PARETO_WITH_HARD_GATES_NO_SINGLE_SCALAR", "runtime_credit_added": 0,
            }
            rerun = json.loads(json.dumps(base))
            self.assertEqual(metrics.stable_measurement_digest(base), metrics.stable_measurement_digest(rerun))

    def test_swarm_forge_distillery_share_one_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_snapshot(repo)
            snap = metrics.capture_input_snapshot(repo)
            source = metrics.source_metrics_from_snapshot(snap)
            self.assertEqual(source["snapshot_id"], snap["snapshot_id"])
            self.assertEqual(source["free_swarm_live_metrics_generated_at"], snap["source_generated_at"]["swarm"])
            self.assertEqual(source["forge_generated_at"], snap["source_generated_at"]["forge"])
            self.assertEqual(source["distillery_generated_at"], snap["source_generated_at"]["distillery"])
            self.assertEqual(source["total_tokens"], 150)
            self.assertEqual(source["forge_evaluations"], 7)
            self.assertEqual(source["distillery_accepted_dataset_tokens"], 40)

    def test_same_watermark_different_snapshot_fails_closed(self):
        existing = {
            "authority_epoch": "8.77",
            "freshness": {"input_watermark": "2026-08-25T02:00:02+00:00", "snapshot_id": "a"},
            "measurement_digest_sha256": "a",
        }
        candidate = {
            "authority_epoch": "8.77",
            "freshness": {"input_watermark": "2026-08-25T02:00:02+00:00", "snapshot_id": "b"},
            "measurement_digest_sha256": "b",
        }
        decision = metrics.publication_decision(existing, candidate)
        self.assertFalse(decision["allow"])
        self.assertEqual(decision["status"], "WATERMARK_COLLISION_DIFFERENT_SNAPSHOT")


if __name__ == "__main__":
    unittest.main()
