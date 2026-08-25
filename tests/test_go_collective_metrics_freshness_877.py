from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics", MODULE_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seed_repo(root: Path, epoch: str = "8.77", base: str = "2026-08-25T02:33:48+00:00") -> None:
    write_json(root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
        "schema_version": epoch,
        "product": "EntityOS",
        "integrated_cognition_compute_architecture": "HCU",
    })
    write_json(root / "free swarm/LIVE_METRICS.json", {
        "schema": "CLAY_FREE_SWARM_METRICS/v1",
        "generated_at": base,
        "workers": {
            "worker_records": 10,
            "exact_usage_rows": 8,
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
        },
    })
    write_json(root / "free swarm/FORGE_LIVE.json", {
        "schema": "CLAY_FREE_EVIDENCE_FORGE_STATUS/v1",
        "generated_at": "2026-08-25T02:33:49+00:00",
        "discovery_hits": 50,
        "evaluations": 4,
        "accepted_deltas": 1,
    })
    write_json(root / "free swarm/DISTILLERY_LIVE.json", {
        "state": "LIVE",
        "generated_at": "2026-08-25T02:33:49.500000+00:00",
        "collected_source_tokens": 1000,
        "collected_chunks": 5,
        "accepted_packets": 0,
        "accepted_dataset_tokens": 0,
    })


class GoCollectiveMetricsFreshness877Tests(unittest.TestCase):
    def snapshot(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        seed_repo(root)
        snap = metrics.read_stable_input_snapshot(root)
        self.addCleanup(tmp.cleanup)
        return root, snap

    def test_newer_live_input_marks_legacy_aggregate_stale(self):
        _, snap = self.snapshot()
        legacy = {
            "authority_epoch": "8.77",
            "source_metrics": {
                "free_swarm_live_metrics_generated_at": "2026-08-25T01:00:00+00:00",
                "forge_generated_at": "2026-08-25T01:00:00+00:00",
                "distillery_generated_at": "2026-08-25T01:00:00+00:00",
            },
        }
        self.assertEqual(metrics.classify_existing_aggregate(legacy, snap), "STALE_SUPERSEDED")
        self.assertEqual(metrics.publication_decision(legacy, snap)["action"], "PUBLISH")

    def test_authority_epoch_mismatch_is_historical_not_current(self):
        _, snap = self.snapshot()
        legacy = {
            "authority_epoch": "8.71",
            "source_metrics": {
                "free_swarm_live_metrics_generated_at": "2026-08-25T02:33:48+00:00",
                "forge_generated_at": "2026-08-25T02:33:49+00:00",
                "distillery_generated_at": "2026-08-25T02:33:49.500000+00:00",
            },
        }
        self.assertEqual(metrics.classify_existing_aggregate(legacy, snap), "HISTORICAL_AUTHORITY_EPOCH")

    def test_older_writer_finishing_late_cannot_regress_latest(self):
        _, snap = self.snapshot()
        newer = {
            "authority_epoch": "8.77",
            "freshness": {
                "snapshot_id": "newer-snapshot",
                "input_generated_at": {
                    "swarm": "2026-08-25T03:00:00+00:00",
                    "forge": "2026-08-25T03:00:00+00:00",
                    "distillery": "2026-08-25T03:00:00+00:00",
                },
            },
        }
        decision = metrics.publication_decision(newer, snap)
        self.assertEqual(decision["classification"], "EXISTING_NEWER_OUT_OF_ORDER_FAIL_CLOSED")
        self.assertEqual(decision["action"], "REJECT_FAIL_CLOSED")

    def test_same_bounded_inputs_have_identical_result_digest(self):
        root, snap1 = self.snapshot()
        snap2 = metrics.read_stable_input_snapshot(root)
        self.assertEqual(snap1["snapshot_id"], snap2["snapshot_id"])
        self.assertEqual(metrics.bounded_result_sha256(snap1), metrics.bounded_result_sha256(snap2))

    def test_swarm_forge_distillery_share_one_snapshot_identity(self):
        _, snap = self.snapshot()
        source = metrics.build_bounded_source_metrics(snap)
        ids = {source[name]["snapshot_id"] for name in ("swarm", "forge", "distillery")}
        epochs = {source[name]["authority_epoch"] for name in ("swarm", "forge", "distillery")}
        self.assertEqual(ids, {snap["snapshot_id"]})
        self.assertEqual(epochs, {"8.77"})
        self.assertEqual(source["swarm"]["total_tokens"], 120)
        self.assertEqual(source["forge"]["accepted_deltas"], 1)
        self.assertEqual(source["distillery"]["accepted_dataset_tokens"], 0)

    def test_snapshot_skew_fails_closed(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        seed_repo(root)
        forge = json.loads((root / "free swarm/FORGE_LIVE.json").read_text())
        forge["generated_at"] = "2026-08-25T04:00:00+00:00"
        write_json(root / "free swarm/FORGE_LIVE.json", forge)
        with self.assertRaisesRegex(metrics.FreshnessError, "INPUT_SNAPSHOT_SKEW_EXCEEDED"):
            metrics.read_stable_input_snapshot(root, max_skew_seconds=300)

    def test_embedded_input_authority_mismatch_fails_closed(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        seed_repo(root)
        swarm = json.loads((root / "free swarm/LIVE_METRICS.json").read_text())
        swarm["authority_epoch"] = "8.76"
        write_json(root / "free swarm/LIVE_METRICS.json", swarm)
        with self.assertRaisesRegex(metrics.FreshnessError, "INPUT_AUTHORITY_EPOCH_MISMATCH:swarm"):
            metrics.read_stable_input_snapshot(root)


if __name__ == "__main__":
    unittest.main()
