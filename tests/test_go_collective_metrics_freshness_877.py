from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_freshness.py"
SPEC = importlib.util.spec_from_file_location("go_collective_freshness_877", MODULE_PATH)
assert SPEC and SPEC.loader
fresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fresh)


class GoCollectiveMetricsFreshness877Tests(unittest.TestCase):
    NOW = dt.datetime(2026, 8, 25, 2, 45, tzinfo=dt.timezone.utc)

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.repo = Path(self.td.name)
        (self.repo / "free swarm").mkdir(parents=True)
        (self.repo / "research_entity/claycode/autonomous").mkdir(parents=True)
        self.write(
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            {
                "schema_version": "8.77",
                "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            },
        )
        self.write(
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            {"schema_version": "8.77", "program": "ENTITYOS_HCU", "product": "EntityOS"},
        )
        self.live("2026-08-25T02:44:00+00:00", 100, 5)
        self.forge("2026-08-25T02:44:01+00:00", 12, 1)
        self.distillery("2026-08-25T02:44:02+00:00", 0, 0)

    def tearDown(self):
        self.td.cleanup()

    def write(self, rel: str, value: dict) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    def live(self, ts: str, tokens: int, workers: int) -> None:
        self.write(
            "free swarm/LIVE_METRICS.json",
            {
                "schema": "CLAY_FREE_SWARM_METRICS/v1",
                "generated_at": ts,
                "workers": {"total_tokens": tokens, "worker_records": workers},
            },
        )

    def forge(self, ts: str, evaluations: int, accepted: int) -> None:
        self.write(
            "free swarm/FORGE_LIVE.json",
            {
                "schema": "CLAY_FREE_EVIDENCE_FORGE_STATUS/v1",
                "generated_at": ts,
                "evaluations": evaluations,
                "accepted_deltas": accepted,
            },
        )

    def distillery(self, ts: str, packets: int, tokens: int) -> None:
        self.write(
            "free swarm/DISTILLERY_LIVE.json",
            {
                "state": "LIVE",
                "generated_at": ts,
                "accepted_packets": packets,
                "accepted_dataset_tokens": tokens,
            },
        )

    def snapshot(self):
        return fresh.build_live_snapshot(self.repo, now=self.NOW)

    def result(self, snapshot: dict, value: int = 1) -> dict:
        out = {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "generated_at": self.NOW.isoformat(),
            "authority_epoch": snapshot["authority"]["authority_epoch"],
            "bounded_live_snapshot": snapshot,
            "aggregate": {"x": value},
            "freshness": {"schema": fresh.FRESHNESS_SCHEMA, "status": "FRESH_BOUND_SNAPSHOT"},
        }
        out["result_digest_sha256"] = fresh.deterministic_result_digest(out)
        return out

    def test_shared_snapshot_binds_all_live_funnel_fields(self):
        snap = self.snapshot()
        ids = {row["snapshot_id"] for row in snap["fields"].values()}
        self.assertEqual(ids, {snap["snapshot_id"]})
        self.assertEqual(snap["authority"]["authority_epoch"], "8.77")
        self.assertEqual(snap["fields"]["free_swarm_total_tokens"]["value"], 100)
        self.assertEqual(snap["fields"]["forge_accepted_deltas"]["value"], 1)
        self.assertEqual(snap["fields"]["distillery_accepted_dataset_tokens"]["value"], 0)

    def test_stale_input_fails_closed(self):
        self.live("2026-08-25T00:00:00+00:00", 100, 5)
        with self.assertRaisesRegex(fresh.FreshnessError, "STALE_LIVE_INPUT:swarm"):
            fresh.build_live_snapshot(self.repo, now=self.NOW, max_age_seconds=3600)

    def test_shared_snapshot_skew_fails_closed(self):
        self.live("2026-08-25T02:42:00+00:00", 100, 5)
        with self.assertRaisesRegex(fresh.FreshnessError, "SHARED_SNAPSHOT_SKEW_EXCEEDED"):
            fresh.build_live_snapshot(self.repo, now=self.NOW, max_snapshot_skew_seconds=30)

    def test_authority_epoch_mismatch_fails_closed(self):
        self.write(
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            {"schema_version": "8.76", "program": "ENTITYOS_HCU", "product": "EntityOS"},
        )
        with self.assertRaisesRegex(fresh.FreshnessError, "SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH"):
            self.snapshot()

    def test_out_of_order_writer_is_rejected(self):
        older_snapshot = self.snapshot()
        self.live("2026-08-25T02:44:10+00:00", 101, 5)
        self.forge("2026-08-25T02:44:11+00:00", 13, 1)
        self.distillery("2026-08-25T02:44:12+00:00", 0, 0)
        newer_snapshot = self.snapshot()
        older = self.result(older_snapshot)
        newer = self.result(newer_snapshot)
        self.assertEqual(fresh.publication_decision(newer, older), "REJECT_OUT_OF_ORDER_OLDER_SNAPSHOT")

    def test_identical_snapshot_and_measurement_is_idempotent(self):
        snap = self.snapshot()
        first = self.result(snap, value=7)
        second = json.loads(json.dumps(first))
        second["generated_at"] = "2026-08-25T02:45:59+00:00"
        second["result_digest_sha256"] = fresh.deterministic_result_digest(second)
        self.assertEqual(first["result_digest_sha256"], second["result_digest_sha256"])
        self.assertEqual(fresh.publication_decision(first, second), "IDEMPOTENT_IDENTICAL_RESULT")

    def test_same_snapshot_different_result_fails_closed(self):
        snap = self.snapshot()
        first = self.result(snap, value=7)
        second = self.result(snap, value=8)
        self.assertEqual(fresh.publication_decision(first, second), "REJECT_NONDETERMINISTIC_SAME_SNAPSHOT")

    def test_historical_authority_is_superseded_not_averaged(self):
        snap = self.snapshot()
        candidate = self.result(snap)
        historical = {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "authority_epoch": "8.71",
            "aggregate": {},
        }
        self.assertEqual(fresh.publication_decision(historical, candidate), "PUBLISH_SUPERSEDES_HISTORICAL_AUTHORITY")

    def test_locked_bundle_emits_receipt_and_second_write_is_noop(self):
        snap = self.snapshot()
        result = self.result(snap)
        out_json = self.repo / "free swarm/GO_COLLECTIVE_METRICS.json"
        out_md = self.repo / "free swarm/GO_COLLECTIVE_METRICS.md"
        receipt = self.repo / "free swarm/COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json"
        first = fresh.publish_bundle(
            out_json=out_json,
            out_md=out_md,
            result=result,
            markdown="one\n",
            receipt_path=receipt,
        )
        second = fresh.publish_bundle(
            out_json=out_json,
            out_md=out_md,
            result=result,
            markdown="two\n",
            receipt_path=receipt,
        )
        self.assertEqual(first["decision"], "PUBLISH_NO_EXISTING")
        self.assertEqual(second["decision"], "IDEMPOTENT_IDENTICAL_RESULT")
        self.assertEqual(out_md.read_text(encoding="utf-8"), "one\n")
        self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["snapshot_id"], snap["snapshot_id"])


if __name__ == "__main__":
    unittest.main()
