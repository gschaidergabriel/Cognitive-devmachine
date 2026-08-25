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
        self._set_snapshot("2026-08-25T02:00:00Z", 10, 1, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel: str, value: dict):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    def _surface(self, name: str, generated_at: str, extra: dict):
        value = {"generated_at": generated_at, **extra}
        self._write(f"free swarm/{name}", value)

    def _set_snapshot(self, base: str, tokens: int, forge_evaluations: int, accepted_dataset_tokens: int):
        base_ts = fresh.parse_ts(base)
        self._surface(
            "LIVE_METRICS.json",
            fresh.iso(base_ts),
            {
                "workers": {
                    "worker_records": 3,
                    "exact_usage_rows": 3,
                    "input_tokens": max(tokens - 3, 0),
                    "output_tokens": min(tokens, 3),
                    "total_tokens": tokens,
                }
            },
        )
        self._surface(
            "FORGE_LIVE.json",
            fresh.iso(base_ts + fresh.dt.timedelta(seconds=1)),
            {"discovery_hits": 2, "evaluations": forge_evaluations, "accepted_deltas": 0},
        )
        self._surface(
            "DISTILLERY_LIVE.json",
            fresh.iso(base_ts + fresh.dt.timedelta(seconds=2)),
            {
                "collected_source_tokens": 11,
                "collected_chunks": 2,
                "accepted_packets": 1 if accepted_dataset_tokens else 0,
                "accepted_dataset_tokens": accepted_dataset_tokens,
            },
        )

    def _candidate(self, **extra) -> dict:
        return {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "authority_epoch": "8.77",
            "generated_at": "2026-08-25T03:00:00Z",
            "aggregate": {"x": 1},
            **extra,
        }

    def test_shared_snapshot_identity_binds_swarm_forge_distillery_and_source_metrics(self):
        snap = fresh.build_snapshot(self.repo)
        ids = {row["snapshot_id"] for row in snap["surfaces"]}
        self.assertEqual(ids, {snap["snapshot_id"]})
        self.assertEqual({row["name"] for row in snap["surfaces"]}, {"swarm", "forge", "distillery"})
        self.assertEqual(snap["authority"]["authority_epoch"], "8.77")
        self.assertLessEqual(snap["snapshot_skew_seconds"], fresh.MAX_SNAPSHOT_SKEW_SECONDS)
        source = snap["source_metrics"]
        self.assertEqual(source["bounded_snapshot_id"], snap["snapshot_id"])
        self.assertEqual(source["swarm_snapshot_id"], snap["snapshot_id"])
        self.assertEqual(source["forge_snapshot_id"], snap["snapshot_id"])
        self.assertEqual(source["distillery_snapshot_id"], snap["snapshot_id"])
        self.assertEqual(source["total_tokens"], 10)
        self.assertEqual(source["forge_evaluations"], 1)
        self.assertEqual(source["distillery_accepted_dataset_tokens"], 0)

    def test_newer_live_input_marks_current_aggregate_stale(self):
        older = fresh.build_snapshot(self.repo)
        first = self._candidate()
        first_decision = fresh.publication_decision(first, older, None)
        current = fresh.attach_freshness(first, older, first_decision)

        self._set_snapshot("2026-08-25T02:10:00Z", 20, 2, 0)
        newer = fresh.build_snapshot(self.repo)
        decision = fresh.publication_decision(self._candidate(), newer, current)
        self.assertEqual(decision["action"], "PUBLISH")
        self.assertEqual(decision["current_state"], "STALE_INPUT_SNAPSHOT")
        self.assertEqual(decision["reason"], "CURRENT_PUBLICATION_STALE_INPUT")

    def test_temporally_unbounded_source_set_fails_closed(self):
        self._surface(
            "LIVE_METRICS.json",
            "2026-08-25T02:10:00Z",
            {"workers": {"worker_records": 4, "exact_usage_rows": 4, "input_tokens": 14, "output_tokens": 6, "total_tokens": 20}},
        )
        with self.assertRaisesRegex(fresh.FreshnessError, "INPUT_SNAPSHOT_SKEW_EXCEEDED"):
            fresh.build_snapshot(self.repo)

    def test_authority_epoch_mismatch_fails_closed(self):
        self._write(
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            {"schema_version": "8.76", "program": "ENTITYOS_HCU", "product": "EntityOS"},
        )
        with self.assertRaisesRegex(fresh.FreshnessError, "AUTHORITY_EPOCH_MISMATCH"):
            fresh.build_snapshot(self.repo)

    def test_older_writer_finishing_after_newer_writer_cannot_regress_latest(self):
        old_snapshot = fresh.build_snapshot(self.repo)
        self._set_snapshot("2026-08-25T03:00:00Z", 30, 3, 0)
        new_snapshot = fresh.build_snapshot(self.repo)
        candidate = self._candidate()
        new_decision = fresh.publication_decision(candidate, new_snapshot, None)
        current = fresh.attach_freshness(candidate, new_snapshot, new_decision)
        with self.assertRaisesRegex(fresh.FreshnessError, "OUT_OF_ORDER_INPUT_SNAPSHOT"):
            fresh.publication_decision(candidate, old_snapshot, current)

    def test_same_bounded_inputs_have_identical_digest_and_idempotent_replay(self):
        snap1 = fresh.build_snapshot(self.repo)
        snap2 = fresh.build_snapshot(self.repo)
        self.assertEqual(snap1["snapshot_id"], snap2["snapshot_id"])
        candidate1 = self._candidate(generated_at="2026-08-25T03:00:00Z")
        candidate2 = self._candidate(generated_at="2026-08-25T03:05:00Z")
        d1 = fresh.publication_decision(candidate1, snap1, None)
        current = fresh.attach_freshness(candidate1, snap1, d1)
        d2 = fresh.publication_decision(candidate2, snap2, current)
        self.assertEqual(d1["result_digest_sha256"], d2["result_digest_sha256"])
        self.assertEqual(d2["action"], "NO_CHANGE")
        self.assertEqual(d2["reason"], "IDEMPOTENT_REPLAY")
        self.assertEqual(d2["current_state"], "CURRENT")

    def test_candidate_stale_source_metrics_are_overwritten_by_bound_snapshot(self):
        snap = fresh.build_snapshot(self.repo)
        candidate = self._candidate(source_metrics={"total_tokens": 999999, "forge_evaluations": 999})
        decision = fresh.publication_decision(candidate, snap, None)
        published = fresh.attach_freshness(candidate, snap, decision)
        self.assertEqual(published["source_metrics"], snap["source_metrics"])
        self.assertEqual(published["source_metrics"]["total_tokens"], 10)
        self.assertEqual(published["source_metrics"]["forge_evaluations"], 1)

    def test_legacy_authority_publication_is_historical_not_current(self):
        snap = fresh.build_snapshot(self.repo)
        legacy = {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "authority_epoch": "8.71",
            "generated_at": "2026-08-24T13:58:54Z",
            "aggregate": {"x": 0},
        }
        decision = fresh.publication_decision(self._candidate(), snap, legacy)
        self.assertEqual(decision["action"], "PUBLISH")
        self.assertEqual(decision["current_state"], "HISTORICAL_AUTHORITY")
        self.assertEqual(decision["reason"], "CURRENT_PUBLICATION_HISTORICAL_AUTHORITY")

    def test_same_snapshot_different_semantics_fails_closed(self):
        snap = fresh.build_snapshot(self.repo)
        first = self._candidate(aggregate={"x": 1})
        decision = fresh.publication_decision(first, snap, None)
        current = fresh.attach_freshness(first, snap, decision)
        second = self._candidate(aggregate={"x": 2})
        with self.assertRaisesRegex(fresh.FreshnessError, "SAME_SNAPSHOT_DIFFERENT_RESULT"):
            fresh.publication_decision(second, snap, current)

    def test_missing_or_unmeasured_surface_fails_closed(self):
        (self.repo / "free swarm/FORGE_LIVE.json").unlink()
        with self.assertRaisesRegex(fresh.FreshnessError, "INPUT_MISSING:forge"):
            fresh.build_snapshot(self.repo)

    def test_lock_file_is_outside_repository(self):
        output = self.repo / "free swarm/GO_COLLECTIVE_METRICS.json"
        lock_path = fresh._lock_path(output)
        self.assertFalse(lock_path.is_relative_to(self.repo))

    def test_publish_replaces_legacy_source_metrics_and_emits_scoped_receipt(self):
        candidate_path = self.repo / "candidate.json"
        candidate_path.write_text(json.dumps(self._candidate(source_metrics={"total_tokens": 1})) + "\n", encoding="utf-8")
        output = self.repo / "published.json"
        output.write_text(json.dumps({"schema": "CLAY_GO_COLLECTIVE_METRICS/v1", "authority_epoch": "8.71"}) + "\n", encoding="utf-8")
        receipt_path = self.repo / "receipt.json"

        receipt = fresh.publish(self.repo, candidate_path, output, receipt_path)
        published = json.loads(output.read_text(encoding="utf-8"))
        stored_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["decision"]["current_state"], "HISTORICAL_AUTHORITY")
        self.assertEqual(published["authority_epoch"], "8.77")
        self.assertEqual(published["source_metrics"]["total_tokens"], 10)
        self.assertEqual(published["freshness"]["snapshot"]["snapshot_id"], published["source_metrics"]["bounded_snapshot_id"])
        self.assertEqual(stored_receipt["scope"], "COLLECTIVE_METRICS_FRESHNESS_AND_BOUND_SNAPSHOT_PUBLICATION_ONLY")
        self.assertEqual(stored_receipt["runtime_credit_added"], 0)

    def test_publish_candidate_binds_json_and_markdown_under_one_decision(self):
        output = self.repo / "published.json"
        output_md = self.repo / "published.md"
        receipt_path = self.repo / "receipt.json"
        receipt = fresh.publish_candidate(
            self.repo,
            self._candidate(),
            output,
            receipt_path,
            output_md_path=output_md,
            markdown_text="# metrics\n",
        )
        published = json.loads(output.read_text(encoding="utf-8"))
        marker = output_md.read_text(encoding="utf-8").splitlines()[0]
        snapshot_id = published["freshness"]["snapshot"]["snapshot_id"]
        result_digest = published["freshness"]["result_digest_sha256"]
        self.assertEqual(receipt["decision"]["action"], "PUBLISH")
        self.assertIn(snapshot_id, marker)
        self.assertIn(result_digest, marker)
        self.assertIn("authority_epoch=8.77", marker)


if __name__ == "__main__":
    unittest.main()
