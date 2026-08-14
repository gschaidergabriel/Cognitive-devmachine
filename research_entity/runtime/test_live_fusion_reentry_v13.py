from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from live_fusion_reentry_v13 import (
    DeliveryAck,
    LiveDelta,
    LiveFusionBus,
    Resolution,
    WorkerView,
)


class LiveFusionReentryV13Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "live_fusion_v13.jsonl"
        self.bus = LiveFusionBus(self.log)
        self.bus.register_worker(
            WorkerView(
                worker_id="unifieddb-worker",
                branches=("unifieddb",),
                active_keys=("pulse", "record_identity"),
                active_work=("wp-pulse",),
                active_claims=("claim-aba",),
                subscription_revision="u-r1",
                plan_revision="plan-u1",
            )
        )
        self.bus.register_worker(
            WorkerView(
                worker_id="claycode-worker",
                branches=("claycode",),
                active_keys=("parser", "grammar"),
                subscription_revision="c-r1",
                plan_revision="plan-c1",
            )
        )

    def tearDown(self):
        self.tmp.cleanup()

    def delta(
        self,
        event_id: str,
        seq: int,
        payload: dict,
        *,
        conflict: bool = True,
        semantic_keys=("pulse", "record_identity"),
        affected_branches=("unifieddb", "claygraph"),
        affected_work=("wp-pulse",),
        affected_claims=("claim-aba",),
    ) -> LiveDelta:
        return LiveDelta(
            event_id=event_id,
            source="github-main",
            source_seq=seq,
            source_epoch=f"sha-{seq}",
            semantic_keys=tuple(semantic_keys),
            affected_branches=tuple(affected_branches),
            novelty="CONTRADICTS" if conflict else "REFINES",
            impact=0.95 if conflict else 0.70,
            urgency=0.80 if conflict else 0.50,
            conflict=conflict,
            payload=payload,
            provenance_refs=(f"commit:{seq}",),
            causal_origin_epoch=f"origin-{seq}",
            arrival_epoch="arrival-current",
            causal_origin_refs=(f"origin-receipt:{seq}",),
            applicability="CURRENT_MATERIAL",
            affected_work=tuple(affected_work),
            affected_claims=tuple(affected_claims),
        )

    def replan(self, event_id: str, *, subscription="u-r1") -> Resolution:
        return Resolution(
            resolution_id=f"resolution-{event_id}-{subscription}",
            event_id=event_id,
            worker_id="unifieddb-worker",
            subscription_revision=subscription,
            decision="REPLAN",
            prior_plan_revision="plan-u1",
            new_plan_revision="plan-u2",
            basis_event_ids=(event_id,),
            plan_state_hash="state-plan-u2",
        )

    def test_event_id_collision_fails_closed(self):
        event = self.delta("evt-1", 1, {"value": "A"})
        self.assertEqual(self.bus.ingest(event), "INGESTED")
        self.assertEqual(self.bus.ingest(event), "DEDUPED_EVENT_ID")
        with self.assertRaises(ValueError):
            self.bus.ingest(self.delta("evt-1", 1, {"value": "different"}))

    def test_delivery_receipt_and_defer_do_not_release_effect_guard(self):
        self.bus.ingest(self.delta("evt-block", 2, {"counterexample": "ABA"}))
        delivery = self.bus.current_delivery("evt-block", "unifieddb-worker")
        allowed, blockers = self.bus.effect_guard("unifieddb-worker", effect_keys=("pulse",))
        self.assertFalse(allowed)
        self.assertEqual(blockers, ["evt-block"])

        ack = DeliveryAck(
            ack_id="ack-seen",
            delivery_id=delivery.delivery_id,
            event_id="evt-block",
            worker_id="unifieddb-worker",
            subscription_revision="u-r1",
        )
        self.assertEqual(self.bus.ack_delivery(ack), "ACKED")
        self.assertEqual(self.bus.ack_delivery(ack), "ACK_IDEMPOTENT")
        self.assertFalse(self.bus.effect_guard("unifieddb-worker", effect_keys=("pulse",))[0])

        self.assertEqual(
            self.bus.resolve(
                Resolution(
                    resolution_id="resolution-defer",
                    event_id="evt-block",
                    worker_id="unifieddb-worker",
                    subscription_revision="u-r1",
                    decision="DEFER",
                    prior_plan_revision="plan-u1",
                    new_plan_revision="plan-u1",
                    basis_event_ids=(),
                    plan_state_hash="",
                )
            ),
            "RECORDED_OPEN",
        )
        self.assertFalse(self.bus.effect_guard("unifieddb-worker", effect_keys=("pulse",))[0])
        self.assertEqual(self.bus.resolve(self.replan("evt-block")), "RESOLVED")
        self.assertTrue(self.bus.effect_guard("unifieddb-worker", effect_keys=("pulse",))[0])

    def test_subscription_revision_reroutes_sticky_index_only(self):
        self.bus.ingest(self.delta("evt-profile", 3, {"value": "x"}))
        old = self.bus.current_delivery("evt-profile", "claycode-worker")
        self.assertEqual(old.delivery_class, "INDEX_ONLY")
        self.bus.register_worker(
            WorkerView(
                worker_id="claycode-worker",
                branches=("claycode", "unifieddb"),
                active_keys=("parser", "grammar", "pulse"),
                active_work=("wp-pulse",),
                subscription_revision="c-r2",
                plan_revision="plan-c2",
            )
        )
        new = self.bus.current_delivery("evt-profile", "claycode-worker")
        self.assertNotEqual(old.delivery_id, new.delivery_id)
        self.assertEqual(new.delivery_class, "INTERRUPT_NEXT_SAFE_POINT")

    def test_work_overlap_routes_without_branch_or_key_overlap(self):
        self.bus.ingest(
            self.delta(
                "evt-work",
                4,
                {"work": "changed"},
                semantic_keys=("unrelated",),
                affected_branches=("other",),
                affected_work=("wp-pulse",),
                affected_claims=("other-claim",),
            )
        )
        delivery = self.bus.current_delivery("evt-work", "unifieddb-worker")
        self.assertEqual(delivery.delivery_class, "INTERRUPT_NEXT_SAFE_POINT")
        allowed, blockers = self.bus.effect_guard("unifieddb-worker", effect_work=("wp-pulse",))
        self.assertFalse(allowed)
        self.assertEqual(blockers, ["evt-work"])

    def test_replay_preserves_receipt_resolution_and_parent_recovery_lane(self):
        self.bus.ingest(self.delta("evt-replay", 5, {"value": "A"}))
        delivery = self.bus.current_delivery("evt-replay", "unifieddb-worker")
        self.bus.ack_delivery(
            DeliveryAck(
                ack_id="ack-r",
                delivery_id=delivery.delivery_id,
                event_id="evt-replay",
                worker_id="unifieddb-worker",
                subscription_revision="u-r1",
            )
        )
        self.bus.resolve(self.replan("evt-replay"))
        replay = LiveFusionBus.replay(self.log)
        self.assertIn("ack-r", replay.delivery_acks)
        self.assertEqual(replay.pending("unifieddb-worker"), [])
        self.assertEqual(replay.recovery_events, [])

    def test_subscription_snapshot_has_no_registration_tail_gap(self):
        for round_id in range(30):
            bus = LiveFusionBus()
            worker = WorkerView(
                worker_id=f"w-{round_id}",
                branches=("unifieddb",),
                active_keys=("pulse",),
                subscription_revision="r1",
            )
            delta = self.delta(f"evt-race-{round_id}", 100 + round_id, {"r": round_id})
            result = {}
            barrier = threading.Barrier(2)

            def register():
                barrier.wait()
                result["snapshot"] = bus.register_worker(worker)

            def ingest():
                barrier.wait()
                result["status"] = bus.ingest(delta)

            t1 = threading.Thread(target=register)
            t2 = threading.Thread(target=ingest)
            t1.start(); t2.start(); t1.join(); t2.join()
            snapshot = result["snapshot"]
            delivery = bus.current_delivery(delta.event_id, worker.worker_id)
            if delivery.bus_seq <= snapshot.cut_bus_seq:
                self.assertIn(delivery.delivery_id, snapshot.pending_delivery_ids)
            else:
                self.assertGreater(delivery.bus_seq, snapshot.cut_bus_seq)


if __name__ == "__main__":
    unittest.main()
