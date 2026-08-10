from __future__ import annotations

import concurrent.futures
import tempfile
import unittest
from pathlib import Path

from live_fusion_reentry_v2 import Ack, LiveDelta, LiveFusionBus, WorkerView


class LiveFusionReentryV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "fusion.sqlite"
        self.bus = LiveFusionBus(self.db)
        self.worker = WorkerView(
            worker_id="unifieddb-worker",
            branches=("unifieddb",),
            active_keys=("pulse", "record_identity"),
            active_work=("UDB-PULSE",),
            active_claims=("claim-aba",),
            plan_revision="plan-r1",
            lease_id="lease-1",
            lease_epoch="epoch-1",
        )
        self.bus.register_worker(self.worker)

    def tearDown(self):
        self.tmp.cleanup()

    def delta(self, event_id, seq, payload=None, *, conflict=True, applicability="CURRENT_MATERIAL"):
        return LiveDelta(
            event_id=event_id,
            source="github-main",
            source_seq=seq,
            source_epoch=f"sha-{seq}",
            semantic_keys=("pulse", "record_identity"),
            affected_branches=("unifieddb", "claygraph"),
            affected_work=("UDB-PULSE",),
            affected_claims=("claim-aba",),
            novelty="CONTRADICTS" if conflict else "REFINES",
            impact=0.95 if conflict else 0.70,
            urgency=0.80 if conflict else 0.50,
            conflict=conflict,
            payload=payload or {"value": event_id},
            provenance_refs=(f"commit:{seq}",),
            evidence_class="VERIFIED_TEST_FIXTURE",
            causal_origin_epoch=f"origin-{seq}",
            arrival_epoch="arrival-current",
            causal_origin_refs=(f"origin-receipt:{seq}",),
            applicability=applicability,
        )

    def test_event_id_dedupe_and_payload_collision_fail_closed(self):
        d = self.delta("evt-1", 1, {"value": "A"})
        self.assertEqual(self.bus.ingest(d), "INGESTED")
        self.assertEqual(self.bus.ingest(d), "DEDUPED_EVENT_ID")
        with self.assertRaises(ValueError):
            self.bus.ingest(self.delta("evt-1", 2, {"value": "B"}))
        self.assertEqual(self.bus.snapshot()["events"], 1)

    def test_content_aba_preserves_distinct_event_identity(self):
        self.bus.ingest(self.delta("evt-a1", 1, {"state": "A"}, conflict=False))
        self.bus.ingest(self.delta("evt-a2", 2, {"state": "A"}, conflict=False))
        self.assertEqual(self.bus.snapshot()["events"], 2)
        pending = self.bus.pending("unifieddb-worker")
        self.assertEqual({d.event_id for d in pending}, {"evt-a1", "evt-a2"})

    def test_stale_ack_cannot_clear_current_plan_effect_guard(self):
        d = self.delta("evt-block", 3, {"counterexample": "ABA"})
        self.bus.ingest(d)
        old_delivery = self.bus.pending("unifieddb-worker")[0]
        self.bus.register_worker(
            WorkerView(
                worker_id="unifieddb-worker",
                branches=("unifieddb",),
                active_keys=("pulse", "record_identity"),
                active_work=("UDB-PULSE",),
                active_claims=("claim-aba",),
                plan_revision="plan-r2",
                lease_id="lease-2",
                lease_epoch="epoch-2",
            )
        )
        with self.assertRaises(ValueError):
            self.bus.ack(
                Ack(
                    ack_id="ack-stale",
                    delivery_id=old_delivery.delivery_id,
                    event_id="evt-block",
                    worker_id="unifieddb-worker",
                    decision="ACCEPT",
                    basis_plan_revision="plan-r1",
                    result_plan_revision="plan-r1",
                    lease_id="lease-1",
                    payload_hash=d.normalized().payload_hash,
                )
            )
        allowed, blockers = self.bus.effect_guard("unifieddb-worker", effect_work=("UDB-PULSE",))
        self.assertFalse(allowed)
        self.assertEqual(blockers, ["evt-block"])

    def test_ack_is_bound_to_payload_plan_and_lease(self):
        d = self.delta("evt-ack", 4)
        self.bus.ingest(d)
        delivery = self.bus.pending("unifieddb-worker")[0]
        with self.assertRaises(ValueError):
            self.bus.ack(
                Ack("a0", delivery.delivery_id, d.event_id, self.worker.worker_id, "ACCEPT",
                    self.worker.plan_revision, self.worker.plan_revision, self.worker.lease_id, "wrong")
            )
        ack = Ack(
            ack_id="a1", delivery_id=delivery.delivery_id, event_id=d.event_id,
            worker_id=self.worker.worker_id, decision="REPLAN",
            basis_plan_revision=self.worker.plan_revision, result_plan_revision="plan-r2",
            lease_id=self.worker.lease_id, payload_hash=d.normalized().payload_hash,
        )
        self.assertEqual(self.bus.ack(ack), "ACKED")
        self.assertEqual(self.bus.ack(ack), "ACK_IDEMPOTENT")

    def test_historical_only_is_index_only_and_never_blocks_effect(self):
        self.bus.ingest(self.delta("evt-history", 5, applicability="HISTORICALLY_VALID_ONLY"))
        self.assertEqual(self.bus.pending("unifieddb-worker"), [])
        indexed = self.bus.pending("unifieddb-worker", include_index_only=True)
        self.assertEqual([d.event_id for d in indexed], ["evt-history"])
        self.assertEqual(self.bus.effect_guard("unifieddb-worker", effect_keys=("pulse",)), (True, []))

    def test_out_of_order_source_event_is_retained(self):
        self.bus.ingest(self.delta("evt-10", 10, conflict=False))
        self.assertEqual(self.bus.ingest(self.delta("evt-9", 9, conflict=False)), "INGESTED_LATE")
        self.assertEqual(self.bus.snapshot()["events"], 2)

    def test_crash_restart_reconstructs_durable_pending_state(self):
        self.bus.ingest(self.delta("evt-restart", 11))
        before = self.bus.snapshot()
        restarted = LiveFusionBus(self.db)
        self.assertEqual(restarted.snapshot(), before)
        self.assertEqual([d.event_id for d in restarted.pending("unifieddb-worker")], ["evt-restart"])
        self.assertEqual(restarted.effect_guard("unifieddb-worker", effect_keys=("pulse",))[0], False)

    def test_concurrent_distinct_writers_preserve_all_events(self):
        def write(i):
            return LiveFusionBus(self.db).ingest(self.delta(f"evt-c-{i}", 100 + i, conflict=False))

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            statuses = list(ex.map(write, range(32)))
        self.assertTrue(all(s in {"INGESTED", "INGESTED_LATE"} for s in statuses))
        self.assertEqual(self.bus.snapshot()["events"], 32)

    def test_concurrent_same_event_is_idempotent(self):
        d = self.delta("evt-one", 200, {"same": True}, conflict=False)

        def write(_):
            return LiveFusionBus(self.db).ingest(d)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            statuses = list(ex.map(write, range(16)))
        self.assertEqual(statuses.count("INGESTED"), 1)
        self.assertEqual(statuses.count("DEDUPED_EVENT_ID"), 15)
        self.assertEqual(self.bus.snapshot()["events"], 1)


if __name__ == "__main__":
    unittest.main()
