from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from live_fusion_reentry_v1 import _digest
from live_fusion_reentry_v13 import LiveDelta, LiveFusionBus, ROUTING_VERSION, WorkerView


class LiveFusionCrossVersionReplayTests(unittest.TestCase):
    @staticmethod
    def delta() -> LiveDelta:
        return LiveDelta(
            event_id="evt-historical",
            source="github-main",
            source_seq=1,
            source_epoch="sha-1",
            semantic_keys=("pulse",),
            affected_branches=("unifieddb",),
            novelty="REFINES",
            impact=0.70,
            urgency=0.50,
            conflict=False,
            payload={"value": 1},
            applicability="CURRENT_MATERIAL",
        )

    def test_recorded_delivery_outvotes_changed_router_on_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "live_fusion_v13.jsonl"
            bus = LiveFusionBus(log)
            original_snapshot = bus.register_worker(
                WorkerView(
                    worker_id="claycode-worker",
                    branches=("claycode",),
                    active_keys=("parser",),
                    subscription_revision="c-r1",
                )
            )
            bus.ingest(self.delta())
            original = bus.current_delivery("evt-historical", "claycode-worker")
            self.assertEqual(original.delivery_class, "INDEX_ONLY")
            self.assertEqual(original.routing_version, ROUTING_VERSION)

            original_score = LiveFusionBus._score
            try:
                LiveFusionBus._score = staticmethod(
                    lambda delta, worker: (1.0, "router-B-forces-high-relevance")
                )
                replay = LiveFusionBus.replay(log)
            finally:
                LiveFusionBus._score = original_score

            restored = replay.current_delivery("evt-historical", "claycode-worker")
            self.assertEqual(restored, original)
            self.assertEqual(restored.delivery_class, "INDEX_ONLY")
            self.assertNotEqual(restored.reason, "router-B-forces-high-relevance")
            self.assertEqual(replay.subscription_snapshots, [original_snapshot])

    def test_legacy_v13_delivery_without_routing_version_is_bound_to_v13(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "live_fusion_v13.jsonl"
            bus = LiveFusionBus(log)
            bus.register_worker(
                WorkerView(
                    worker_id="worker",
                    branches=("other",),
                    active_keys=("none",),
                    subscription_revision="r1",
                )
            )
            bus.ingest(self.delta())

            rewritten = []
            for line in log.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if row["kind"] == "DELIVERY_V13":
                    row["payload"].pop("routing_version", None)
                    row["record_hash"] = _digest(
                        {"kind": row["kind"], "payload": row["payload"]}
                    )
                rewritten.append(
                    json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                )
            log.write_text("\n".join(rewritten) + "\n", encoding="utf-8")

            replay = LiveFusionBus.replay(log)
            restored = replay.current_delivery("evt-historical", "worker")
            self.assertEqual(restored.routing_version, ROUTING_VERSION)


if __name__ == "__main__":
    unittest.main()
