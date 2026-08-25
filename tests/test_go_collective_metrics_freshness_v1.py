from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics_freshness.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class CollectiveMetricsFreshnessV1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.artifacts = self.root / "artifacts"
        (self.repo / "free swarm").mkdir(parents=True)
        (self.repo / "research_entity/claycode/autonomous").mkdir(parents=True)
        (self.repo / "research_entity/continuity/go_metrics/worker_records").mkdir(parents=True)
        self.artifacts.mkdir()
        self.write_authority("8.77")
        self.write_live("2026-08-25T02:00:00+00:00", tokens=100, forge=1, packets=0, dataset_tokens=0)
        (self.repo / gate.CONFIG_PATH).write_text(json.dumps({"schema": "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1"}))
        (self.repo / gate.DELTA_LEDGER_PATH).write_text("")
        (self.repo / gate.COLLECTOR_PATH).write_text("# fake collector identity\n")
        (self.artifacts / "lane").mkdir()
        (self.artifacts / "lane/workers.jsonl").write_text('{"usage":{"total_tokens":100}}\n')

    def tearDown(self):
        self.tmp.cleanup()

    def write_authority(self, epoch: str) -> None:
        steering_rel = f"research_entity/claycode/autonomous/SUPERVISOR_STEERING_{epoch.replace('.', '_')}.json"
        (self.repo / gate.INBOX_PATH).write_text(json.dumps({
            "schema_version": epoch,
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "steering": steering_rel,
        }))
        (self.repo / steering_rel).write_text(json.dumps({
            "schema_version": epoch,
            "authority": {"free_only": True, "no_paid_fallback": True},
        }))

    def write_live(self, ts: str, *, tokens: int, forge: int, packets: int, dataset_tokens: int) -> None:
        (self.repo / gate.LIVE_PATHS["swarm"]).write_text(json.dumps({
            "generated_at": ts,
            "workers": {"worker_records": 10, "total_tokens": tokens},
        }))
        (self.repo / gate.LIVE_PATHS["forge"]).write_text(json.dumps({
            "generated_at": ts,
            "evaluations": 12,
            "accepted_deltas": forge,
        }))
        (self.repo / gate.LIVE_PATHS["distillery"]).write_text(json.dumps({
            "generated_at": ts,
            "accepted_packets": packets,
            "accepted_dataset_tokens": dataset_tokens,
        }))

    def base_result(self) -> dict:
        return {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "generated_at": "volatile",
            "aggregate": {"total_tokens": 100},
            "workers": [],
            "runtime_credit_added": 0,
        }

    def test_newer_live_input_marks_aggregate_stale_unmeasured(self):
        snapshot = gate.full_snapshot(self.repo, self.artifacts)
        measured = gate.decorate_result(self.base_result(), snapshot, "2026-08-25T02:00:01+00:00")
        gate.atomic_write(self.repo / gate.OUTPUT_JSON_PATH, json.dumps(measured).encode())
        self.write_live("2026-08-25T02:05:00+00:00", tokens=200, forge=1, packets=0, dataset_tokens=0)
        changed, reason = gate.mark_stale_if_needed(self.repo)
        self.assertTrue(changed)
        self.assertEqual(reason, "LIVE_INPUT_MOVED_AFTER_MEASUREMENT")
        out = json.loads((self.repo / gate.OUTPUT_JSON_PATH).read_text())
        self.assertEqual(out["freshness"]["status"], "STALE_UNMEASURED")
        self.assertEqual(out["aggregate"]["total_tokens"], 100)

    def test_authority_epoch_mismatch_fails_closed(self):
        snapshot = gate.full_snapshot(self.repo, self.artifacts)
        measured = gate.decorate_result(self.base_result(), snapshot)
        gate.atomic_write(self.repo / gate.OUTPUT_JSON_PATH, json.dumps(measured).encode())
        self.write_authority("8.78")
        changed, reason = gate.mark_stale_if_needed(self.repo)
        self.assertTrue(changed)
        self.assertEqual(reason, "AUTHORITY_EPOCH_CHANGED")
        out = json.loads((self.repo / gate.OUTPUT_JSON_PATH).read_text())
        self.assertEqual(out["freshness"]["status"], "STALE_UNMEASURED")
        self.assertEqual(out["freshness"]["current_authority_epoch"], "8.78")

    def test_older_writer_finishing_after_newer_writer_cannot_regress_latest(self):
        old_snapshot = gate.full_snapshot(self.repo, self.artifacts)
        old = gate.decorate_result(self.base_result(), old_snapshot)
        self.write_live("2026-08-25T02:10:00+00:00", tokens=250, forge=1, packets=0, dataset_tokens=0)
        new_snapshot = gate.full_snapshot(self.repo, self.artifacts)
        new = gate.decorate_result(self.base_result(), new_snapshot)
        publish, reason = gate.publication_decision(new, old)
        self.assertFalse(publish)
        self.assertEqual(reason, "REJECT_OUT_OF_ORDER_OLDER_SNAPSHOT")

    def test_same_bounded_inputs_rerun_has_identical_result_digest(self):
        snapshot = gate.full_snapshot(self.repo, self.artifacts)
        first = gate.decorate_result(self.base_result(), snapshot, "2026-08-25T02:00:01+00:00")
        second = gate.decorate_result(self.base_result(), snapshot, "2026-08-25T02:59:59+00:00")
        self.assertNotEqual(first["generated_at"], second["generated_at"])
        self.assertEqual(first["result_digest_sha256"], second["result_digest_sha256"])

    def test_swarm_forge_distillery_share_one_bounded_snapshot_identity(self):
        snapshot = gate.full_snapshot(self.repo, self.artifacts)
        result = gate.decorate_result(self.base_result(), snapshot)
        shared = result["input_snapshot"]["snapshot_id"]
        self.assertEqual(result["live_projection"]["snapshot_id"], shared)
        self.assertEqual(set(result["input_snapshot"]["projection"]), {"swarm", "forge", "distillery"})
        self.assertEqual(result["live_projection"]["swarm"]["total_tokens"], 100)
        self.assertEqual(result["live_projection"]["forge"]["accepted_deltas"], 1)
        self.assertEqual(result["live_projection"]["distillery"]["accepted_dataset_tokens"], 0)

    def test_input_movement_during_collection_fails_closed(self):
        def moving_collector(repo, artifacts):
            self.write_live("2026-08-25T02:03:00+00:00", tokens=150, forge=1, packets=0, dataset_tokens=0)
            return self.base_result(), "md"
        with mock.patch.object(gate, "run_collector", side_effect=moving_collector):
            with self.assertRaisesRegex(gate.FreshnessError, "INPUT_SNAPSHOT_MOVED_DURING_COLLECTION"):
                gate.build_candidate(self.repo, self.artifacts)

    def test_same_snapshot_different_result_digest_is_rejected(self):
        snapshot = gate.full_snapshot(self.repo, self.artifacts)
        first = gate.decorate_result(self.base_result(), snapshot)
        altered = self.base_result()
        altered["aggregate"]["total_tokens"] = 999
        second = gate.decorate_result(altered, snapshot)
        publish, reason = gate.publication_decision(first, second)
        self.assertFalse(publish)
        self.assertEqual(reason, "REJECT_NONDETERMINISTIC_SAME_SNAPSHOT")


if __name__ == "__main__":
    unittest.main()
