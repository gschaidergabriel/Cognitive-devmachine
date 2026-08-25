from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics_fresh_publish.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_fresh_publish", MODULE_PATH)
assert SPEC and SPEC.loader
fresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fresh)


class CollectiveMetricsFreshness877Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.repo = self.root / "repo"
        self.artifacts = self.root / "artifacts"
        (self.repo / "research_entity/claycode/autonomous").mkdir(parents=True)
        (self.repo / "research_entity/continuity/go_metrics/worker_records").mkdir(parents=True)
        (self.repo / "free swarm").mkdir(parents=True)
        (self.artifacts / "run-a").mkdir(parents=True)

        inbox = {
            "schema_version": "8.77",
            "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
        }
        steering = {
            "schema_version": "8.77",
            "program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "authority": {"free_only": True},
        }
        config = {"schema": "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1"}
        (self.repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").write_text(
            json.dumps(inbox), encoding="utf-8"
        )
        (self.repo / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json").write_text(
            json.dumps(steering), encoding="utf-8"
        )
        (self.repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json").write_text(
            json.dumps(config), encoding="utf-8"
        )
        (self.repo / "free swarm/architecture_delta_evaluations.jsonl").write_text("", encoding="utf-8")
        (self.artifacts / "run-a/workers.jsonl").write_text(
            json.dumps({"worker_serial": 1, "provider": "fixture", "model": "fixture", "usage": {"total_tokens": 5}}) + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.td.cleanup()

    def candidate(self, when: str, snapshot: str, epoch: str = "8.77"):
        return {
            "authority_epoch": epoch,
            "generated_at": when,
            "freshness": {
                "status": "FRESH_SHARED_SNAPSHOT",
                "source_snapshot_sha256": snapshot,
            },
        }

    def test_resolve_authority_uses_inbox_selected_matching_steering(self):
        authority = fresh.resolve_authority(self.repo)
        self.assertEqual(authority["authority_epoch"], "8.77")
        self.assertEqual(len(authority["inbox_sha256"]), 64)
        self.assertEqual(len(authority["steering_sha256"]), 64)

    def test_resolve_authority_rejects_epoch_mismatch(self):
        path = self.repo / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json"
        data = json.loads(path.read_text())
        data["schema_version"] = "8.76"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(fresh.FreshnessError, "SUPERVISOR_EPOCH_MISMATCH"):
            fresh.resolve_authority(self.repo)

    def test_shared_snapshot_changes_when_artifact_bytes_change(self):
        authority = fresh.resolve_authority(self.repo)
        one = fresh.snapshot_inputs(self.repo, self.artifacts, authority)
        worker = self.artifacts / "run-a/workers.jsonl"
        worker.write_text(worker.read_text() + json.dumps({"worker_serial": 2}) + "\n", encoding="utf-8")
        two = fresh.snapshot_inputs(self.repo, self.artifacts, authority)
        self.assertNotEqual(one["snapshot_sha256"], two["snapshot_sha256"])

    def test_snapshot_rejects_missing_artifact_root(self):
        authority = fresh.resolve_authority(self.repo)
        with self.assertRaisesRegex(fresh.FreshnessError, "FREE_SWARM_ARTIFACT_ROOT_REQUIRED"):
            fresh.snapshot_inputs(self.repo, self.root / "missing", authority)

    def test_out_of_order_writer_rejected(self):
        existing = self.candidate("2026-08-25T03:00:01+00:00", "a" * 64)
        candidate = self.candidate("2026-08-25T03:00:00+00:00", "b" * 64)
        decision, reason = fresh.publication_decision(existing, candidate)
        self.assertEqual((decision, reason), ("REJECT", "OUT_OF_ORDER_OLDER_WRITER"))

    def test_newer_authority_always_blocks_older_writer(self):
        existing = self.candidate("2026-08-25T02:00:00+00:00", "a" * 64, epoch="8.78")
        candidate = self.candidate("2026-08-25T03:00:00+00:00", "b" * 64, epoch="8.77")
        decision, reason = fresh.publication_decision(existing, candidate)
        self.assertEqual((decision, reason), ("REJECT", "EXISTING_NEWER_AUTHORITY_EPOCH"))

    def test_same_authority_and_snapshot_is_idempotent(self):
        existing = self.candidate("2026-08-25T03:00:00+00:00", "c" * 64)
        candidate = self.candidate("2026-08-25T03:00:05+00:00", "c" * 64)
        decision, reason = fresh.publication_decision(existing, candidate)
        self.assertEqual((decision, reason), ("IDEMPOTENT", "SAME_AUTHORITY_AND_SOURCE_SNAPSHOT"))

    def test_same_authority_new_snapshot_is_publishable(self):
        existing = self.candidate("2026-08-25T03:00:00+00:00", "a" * 64)
        candidate = self.candidate("2026-08-25T03:00:05+00:00", "b" * 64)
        decision, reason = fresh.publication_decision(existing, candidate)
        self.assertEqual((decision, reason), ("PUBLISH", "NEWER_OR_DIFFERENT_ADMISSIBLE_SNAPSHOT"))

    def test_atomic_write_replaces_complete_file(self):
        path = self.root / "out.json"
        path.write_text("old", encoding="utf-8")
        fresh.atomic_write(path, "new\n")
        self.assertEqual(path.read_text(encoding="utf-8"), "new\n")
        self.assertEqual(list(self.root.glob(".out.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
