from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 8, 25, 3, 0, tzinfo=UTC)


def sources(at: dt.datetime, *, forge_suffix: str = "b"):
    def item(path: str, digest_char: str, offset: int):
        return {
            "logical_path": path,
            "generated_at": (at + dt.timedelta(seconds=offset)).isoformat(),
            "sha256": digest_char * 64,
        }
    return {
        "free_swarm": item("free swarm/LIVE_METRICS.json", "a", 0),
        "forge": item("free swarm/FORGE_LIVE.json", forge_suffix, 1),
        "distillery": item("free swarm/DISTILLERY_LIVE.json", "c", 2),
    }


def snapshot(at: dt.datetime, *, epoch: str = "8.77", payload: str = "d", forge_suffix: str = "b"):
    return metrics.make_shared_snapshot(
        authority_epoch=epoch,
        sources=sources(at, forge_suffix=forge_suffix),
        collector_payload_sha256=payload * 64,
        now=NOW,
        max_source_age_seconds=3600,
        max_snapshot_skew_seconds=10,
    )


def result(snap: dict, *, epoch: str = "8.77", digest: str = "e"):
    return {
        "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
        "authority_epoch": epoch,
        "generated_at": snap["latest_input_at"],
        "snapshot": snap,
        "result_digest_sha256": digest * 64,
    }


class GoCollectiveMetricsFreshnessV1Tests(unittest.TestCase):
    def test_newer_live_input_marks_existing_aggregate_stale(self):
        older = snapshot(dt.datetime(2026, 8, 25, 2, 40, tzinfo=UTC))
        newer = snapshot(dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC), payload="f")
        self.assertEqual(metrics.classify_existing_freshness(result(older), newer, "8.77"), "STALE")

    def test_authority_epoch_mismatch_is_historical_and_candidate_fails_closed(self):
        old = snapshot(dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC), epoch="8.76")
        current = snapshot(dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC), epoch="8.77")
        self.assertEqual(
            metrics.classify_existing_freshness(result(old, epoch="8.76"), current, "8.77"),
            "HISTORICAL_AUTHORITY_EPOCH",
        )
        self.assertEqual(
            metrics.publication_decision({}, result(old, epoch="8.76"), "8.77"),
            "REJECT_AUTHORITY_EPOCH_MISMATCH",
        )

    def test_out_of_order_writer_cannot_regress_latest(self):
        older = snapshot(dt.datetime(2026, 8, 25, 2, 40, tzinfo=UTC))
        newer = snapshot(dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC), payload="f")
        self.assertEqual(
            metrics.publication_decision(result(newer, digest="1"), result(older, digest="2"), "8.77"),
            "REJECT_OUT_OF_ORDER_WRITER",
        )

    def test_same_bounded_inputs_rerun_is_idempotent(self):
        at = dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC)
        first = snapshot(at, payload="f")
        second = snapshot(at, payload="f")
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(
            metrics.publication_decision(result(first, digest="9"), result(second, digest="9"), "8.77"),
            "IDEMPOTENT",
        )

    def test_swarm_forge_distillery_share_exact_snapshot_identity(self):
        snap = snapshot(dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC), payload="f")
        docs = {
            "free_swarm": {"workers": {"worker_records": 10, "total_tokens": 123}},
            "forge": {"evaluations": 3, "accepted_deltas": 1},
            "distillery": {"accepted_packets": 1, "accepted_dataset_tokens": 7},
        }
        fields = metrics.source_metrics_from_snapshot(snap, docs)
        ids = {fields[name]["snapshot_id"] for name in ("free_swarm", "forge", "distillery")}
        self.assertEqual(ids, {snap["snapshot_id"]})

    def test_same_timestamp_different_snapshot_fails_closed(self):
        at = dt.datetime(2026, 8, 25, 2, 50, tzinfo=UTC)
        first = snapshot(at, payload="f", forge_suffix="b")
        second = snapshot(at, payload="f", forge_suffix="7")
        self.assertNotEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(
            metrics.publication_decision(result(first, digest="1"), result(second, digest="2"), "8.77"),
            "REJECT_SAME_TIME_SNAPSHOT_CONFLICT",
        )

    def test_stale_input_is_rejected_before_snapshot_publication(self):
        with self.assertRaisesRegex(metrics.FreshnessError, "STALE_INPUT"):
            metrics.make_shared_snapshot(
                authority_epoch="8.77",
                sources=sources(dt.datetime(2026, 8, 25, 1, 0, tzinfo=UTC)),
                collector_payload_sha256="d" * 64,
                now=NOW,
                max_source_age_seconds=60,
                max_snapshot_skew_seconds=10,
            )


if __name__ == "__main__":
    unittest.main()
