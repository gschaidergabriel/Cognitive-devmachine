from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics_freshness.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
fresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fresh)


class GoCollectiveMetricsFreshnessV1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "free swarm").mkdir(parents=True)
        (self.repo / "research_entity/claycode/autonomous").mkdir(parents=True)
        inbox = {
            "schema_version": "8.77",
            "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
        }
        steering = {"schema_version": "8.77", "program": "ENTITYOS_HCU", "product": "EntityOS"}
        self._write("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", inbox)
        self._write("research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json", steering)
        self._surface("LIVE_METRICS.json", "2026-08-25T02:00:00Z", {"workers": {"total_tokens": 10}})
        self._surface("FORGE_LIVE.json", "2026-08-25T02:00:01Z", {"evaluations": 1, "accepted_deltas": 0})
        self._surface("DISTILLERY_LIVE.json", "2026-08-25T02:00:02Z", {"accepted_packets": 0, "accepted_dataset_tokens": 0})

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel: str, value: dict):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    def _surface(self, name: str, generated_at: str, extra: dict):
        value = {"generated_at": generated_at, **extra}
        self._write(f"free swarm/{name}", value)

    def test_shared_snapshot_identity_binds_swarm_forge_distillery(self):
        snap = fresh.build_snapshot(self.repo)
        ids = {row["snapshot_id"] for row in snap["surfaces"]}
        self.assertEqual(ids, {snap["snapshot_id"]})
        self.assertEqual({row["name"] for row in snap["surfaces"]}, {"swarm", "forge", "distillery"})
        self.assertEqual(snap["authority"]["authority_epoch"], "8.77")

    def test_newer_live_input_changes_snapshot_and_prevents_stale_reuse(self):
        older = fresh.build_snapshot(self.repo)
        self._surface("LIVE_METRICS.json", "2026-08-25T02:10:00Z", {"workers": {"total_tokens": 20}})
        newer = fresh.build_snapshot(self.repo)
        self.assertNotEqual(older["snapshot_id"], newer["snapshot_id"])
        self.assertGreater(fresh.parse_ts(newer["max_input_generated_at"]), fresh.parse_ts(older["max_input_generated_at"]))

    def test_authority_epoch_mismatch_fails_closed(self):
        self._write(
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            {"schema_version": "8.76", "program": "ENTITYOS_HCU", "product": "EntityOS"},
        )
        with self.assertRaisesRegex(fresh.FreshnessError, "AUTHORITY_EPOCH_MISMATCH"):
            fresh.build_snapshot(self.repo)

    def test_older_writer_finishing_after_newer_writer_cannot_regress_latest(self):
        old_snapshot = fresh.build_snapshot(self.repo)
        self._surface("LIVE_METRICS.json", "2026-08-25T03:00:00Z", {"workers": {"total_tokens": 30}})
        new_snapshot = fresh.build_snapshot(self.repo)
        candidate = {"schema": "CLAY_GO_COLLECTIVE_METRICS/v1", "authority_epoch": "8.77", "aggregate": {"x": 1}}
        new_decision = fresh.publication_decision(candidate, new_snapshot, None)
        current = fresh.attach_freshness(candidate, new_snapshot, new_decision)
        with self.assertRaisesRegex(fresh.FreshnessError, "OUT_OF_ORDER_INPUT_SNAPSHOT"):
            fresh.publication_decision(candidate, old_snapshot, current)

    def test_same_bounded_inputs_have_identical_digest_and_idempotent_replay(self):
        snap1 = fresh.build_snapshot(self.repo)
        snap2 = fresh.build_snapshot(self.repo)
        self.assertEqual(snap1["snapshot_id"], snap2["snapshot_id"])
        candidate1 = {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "authority_epoch": "8.77",
            "generated_at": "2026-08-25T03:00:00Z",
            "aggregate": {"x": 1},
        }
        candidate2 = dict(candidate1, generated_at="2026-08-25T03:05:00Z")
        d1 = fresh.publication_decision(candidate1, snap1, None)
        current = fresh.attach_freshness(candidate1, snap1, d1)
        d2 = fresh.publication_decision(candidate2, snap2, current)
        self.assertEqual(d1["result_digest_sha256"], d2["result_digest_sha256"])
        self.assertEqual(d2["action"], "NO_CHANGE")
        self.assertEqual(d2["reason"], "IDEMPOTENT_REPLAY")

    def test_same_snapshot_different_semantics_fails_closed(self):
        snap = fresh.build_snapshot(self.repo)
        first = {"schema": "CLAY_GO_COLLECTIVE_METRICS/v1", "authority_epoch": "8.77", "aggregate": {"x": 1}}
        decision = fresh.publication_decision(first, snap, None)
        current = fresh.attach_freshness(first, snap, decision)
        second = {"schema": "CLAY_GO_COLLECTIVE_METRICS/v1", "authority_epoch": "8.77", "aggregate": {"x": 2}}
        with self.assertRaisesRegex(fresh.FreshnessError, "SAME_SNAPSHOT_DIFFERENT_RESULT"):
            fresh.publication_decision(second, snap, current)

    def test_missing_or_unmeasured_surface_fails_closed(self):
        (self.repo / "free swarm/FORGE_LIVE.json").unlink()
        with self.assertRaisesRegex(fresh.FreshnessError, "INPUT_MISSING:forge"):
            fresh.build_snapshot(self.repo)


if __name__ == "__main__":
    unittest.main()
