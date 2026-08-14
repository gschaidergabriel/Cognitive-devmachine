from __future__ import annotations

import json
import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path

from live_fusion_reentry_v1 import Ack, LiveDelta, LiveFusionBus, WorkerView


def _worker(writer_id: int, count: int, log_path: str) -> None:
    bus = LiveFusionBus(log_path)
    bus.register_worker(
        WorkerView(
            worker_id="unifieddb-worker",
            branches=("unifieddb",),
            active_keys=("pulse", "record_identity"),
        )
    )
    for index in range(count):
        seq = writer_id * 10000 + index
        bus.ingest(
            LiveDelta(
                event_id=f"writer-{writer_id}-evt-{index}",
                source=f"writer-{writer_id}",
                source_seq=index,
                source_epoch=f"sha-{writer_id}-{index}",
                semantic_keys=("pulse", "record_identity"),
                affected_branches=("unifieddb",),
                novelty="REFINES",
                impact=0.70,
                urgency=0.40,
                conflict=False,
                payload={"writer": writer_id, "index": index},
                provenance_refs=(f"writer:{writer_id}",),
                causal_origin_epoch=f"origin-{seq}",
                arrival_epoch="arrival-current",
                causal_origin_refs=(f"origin-receipt:{seq}",),
                applicability="CURRENT_MATERIAL",
            )
        )


def _crash_after_complete_record(log_path: str) -> None:
    bus = LiveFusionBus(log_path)
    bus.register_worker(
        WorkerView(
            worker_id="unifieddb-worker",
            branches=("unifieddb",),
            active_keys=("pulse",),
        )
    )
    bus.ingest(
        LiveDelta(
            event_id="evt-before-crash",
            source="crash-writer",
            source_seq=1,
            source_epoch="sha-crash",
            semantic_keys=("pulse",),
            affected_branches=("unifieddb",),
            novelty="REFINES",
            impact=0.75,
            urgency=0.50,
            conflict=False,
            payload={"complete": True},
            applicability="CURRENT_MATERIAL",
        )
    )
    fd = os.open(log_path, os.O_APPEND | os.O_WRONLY)
    os.write(fd, b'{"schema_version":"1.1","kind":"DELTA_INGEST","payload":')
    os.fsync(fd)
    os.close(fd)
    os._exit(77)


class LiveFusionReentryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "live_fusion.jsonl"
        self.bus = LiveFusionBus(self.log)
        self.bus.register_worker(
            WorkerView(
                worker_id="unifieddb-worker",
                branches=("unifieddb",),
                active_keys=("pulse", "record_identity"),
            )
        )
        self.bus.register_worker(
            WorkerView(
                worker_id="claycode-worker",
                branches=("claycode",),
                active_keys=("parser", "grammar"),
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
        applicability: str = "UNKNOWN",
    ):
        return LiveDelta(
            event_id=event_id,
            source="github-main",
            source_seq=seq,
            source_epoch=f"sha-{seq}",
            semantic_keys=("pulse", "record_identity"),
            affected_branches=("unifieddb", "claygraph"),
            novelty="CONTRADICTS" if conflict else "REFINES",
            impact=0.95 if conflict else 0.70,
            urgency=0.80 if conflict else 0.50,
            conflict=conflict,
            payload=payload,
            provenance_refs=(f"commit:{seq}",),
            causal_origin_epoch=f"origin-{seq}",
            arrival_epoch="arrival-current",
            causal_origin_refs=(f"origin-receipt:{seq}",),
            applicability=applicability,
        )

    def test_exact_event_id_is_deduped(self):
        d = self.delta("evt-1", 1, {"value": "A"})
        self.assertEqual(self.bus.ingest(d), "INGESTED")
        self.assertEqual(self.bus.ingest(d), "DEDUPED_EVENT_ID")
        self.assertEqual(len(self.bus.deltas), 1)
        self.assertEqual(len(self.bus.pending("unifieddb-worker")), 1)

    def test_same_event_id_with_conflicting_content_fails_closed(self):
        self.bus.ingest(self.delta("evt-conflict", 13, {"value": "A"}, conflict=False))
        with self.assertRaisesRegex(ValueError, "event identity conflict"):
            self.bus.ingest(self.delta("evt-conflict", 13, {"value": "B"}, conflict=False))

    def test_content_aba_does_not_cancel_causal_identity(self):
        self.bus.ingest(self.delta("evt-1", 1, {"value": "A"}, conflict=False))
        self.bus.ingest(self.delta("evt-2", 2, {"value": "A"}, conflict=False))
        self.assertEqual(len(self.bus.deltas), 2)
        self.assertEqual(len(self.bus.pending("unifieddb-worker")), 2)
        self.assertEqual(
            self.bus.deltas["evt-1"].payload_hash,
            self.bus.deltas["evt-2"].payload_hash,
        )

    def test_high_impact_conflict_blocks_matching_effect_until_ack(self):
        self.bus.ingest(self.delta("evt-block", 3, {"counterexample": "ABA"}))
        allowed, blockers = self.bus.effect_guard("unifieddb-worker", ("pulse",))
        self.assertFalse(allowed)
        self.assertEqual(blockers, ["evt-block"])
        self.assertEqual(
            self.bus.ack(
                Ack(
                    ack_id="ack-1",
                    event_id="evt-block",
                    worker_id="unifieddb-worker",
                    decision="REPLAN",
                    plan_revision="plan-r2",
                    note="preserve touched record/version/provenance identity",
                )
            ),
            "ACKED",
        )
        allowed, blockers = self.bus.effect_guard("unifieddb-worker", ("pulse",))
        self.assertTrue(allowed)
        self.assertEqual(blockers, [])

    def test_ack_retry_is_idempotent_even_with_transport_ack_id_change(self):
        self.bus.ingest(self.delta("evt-ack", 12, {"value": "A"}, conflict=False))
        first = Ack(
            ack_id="transport-ack-1",
            event_id="evt-ack",
            worker_id="unifieddb-worker",
            decision="NO_CHANGE",
            plan_revision="plan-r4",
            note="already compatible",
        )
        retry = Ack(
            ack_id="transport-ack-2",
            event_id="evt-ack",
            worker_id="unifieddb-worker",
            decision="NO_CHANGE",
            plan_revision="plan-r4",
            note="already compatible",
        )
        self.assertEqual(self.bus.ack(first), "ACKED")
        self.assertEqual(self.bus.ack(retry), "ACK_IDEMPOTENT")
        self.assertEqual(self.bus.acks[("evt-ack", "unifieddb-worker")], first)

    def test_irrelevant_worker_gets_index_only(self):
        self.bus.ingest(self.delta("evt-idx", 4, {"value": "x"}, conflict=False))
        self.assertEqual(self.bus.pending("claycode-worker"), [])
        indexed = self.bus.pending("claycode-worker", include_index_only=True)
        self.assertEqual(len(indexed), 1)
        self.assertEqual(indexed[0].delivery_class, "INDEX_ONLY")

    def test_replay_reconstructs_pending_and_ack_state(self):
        self.bus.ingest(self.delta("evt-1", 5, {"value": "A"}))
        self.bus.ingest(self.delta("evt-2", 6, {"value": "B"}, conflict=False))
        ack = Ack(
            ack_id="ack-r",
            event_id="evt-1",
            worker_id="unifieddb-worker",
            decision="REPLAN",
            plan_revision="plan-r3",
        )
        self.bus.ack(ack)
        replay = LiveFusionBus.replay(self.log)
        self.assertEqual(set(replay.deltas), {"evt-1", "evt-2"})
        self.assertEqual(replay.acks[("evt-1", "unifieddb-worker")], ack)
        self.assertEqual(
            [d.event_id for d in replay.pending("unifieddb-worker")],
            ["evt-2"],
        )
        self.assertEqual(replay.deltas["evt-2"].causal_origin_epoch, "origin-6")
        self.assertEqual(replay.deltas["evt-2"].arrival_epoch, "arrival-current")

    def test_out_of_order_source_event_is_retained_and_routed_as_late(self):
        self.bus.ingest(self.delta("evt-10", 10, {"value": 10}, conflict=False))
        status = self.bus.ingest(self.delta("evt-9", 9, {"value": 9}, conflict=False))
        self.assertEqual(status, "INGESTED_LATE")
        self.assertIn("evt-9", self.bus.deltas)
        self.assertIn("evt-9", [d.event_id for d in self.bus.pending("unifieddb-worker")])
        self.assertEqual(self.bus.deltas["evt-9"].causal_origin_epoch, "origin-9")
        self.assertEqual(self.bus.deltas["evt-9"].arrival_epoch, "arrival-current")

    def test_historically_valid_only_is_preserved_without_plan_churn(self):
        self.bus.ingest(
            self.delta(
                "evt-history",
                11,
                {"late_outcome": "verified"},
                conflict=True,
                applicability="HISTORICALLY_VALID_ONLY",
            )
        )
        self.assertEqual(self.bus.pending("unifieddb-worker"), [])
        indexed = self.bus.pending("unifieddb-worker", include_index_only=True)
        self.assertEqual([d.event_id for d in indexed], ["evt-history"])
        allowed, blockers = self.bus.effect_guard("unifieddb-worker", ("pulse",))
        self.assertTrue(allowed)
        self.assertEqual(blockers, [])

    def test_concurrent_process_writers_preserve_all_complete_records(self):
        process_count = 4
        events_per_process = 12
        processes = [
            multiprocessing.Process(
                target=_worker,
                args=(writer_id, events_per_process, str(self.log)),
            )
            for writer_id in range(process_count)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(20)
            self.assertEqual(process.exitcode, 0)

        for line in self.log.read_text(encoding="utf-8").splitlines():
            json.loads(line)

        replay = LiveFusionBus.replay(self.log)
        expected = {
            f"writer-{writer_id}-evt-{index}"
            for writer_id in range(process_count)
            for index in range(events_per_process)
        }
        self.assertTrue(expected.issubset(set(replay.deltas)))
        self.assertEqual(len(expected), process_count * events_per_process)

    def test_real_process_crash_recovers_completed_records_and_quarantines_torn_tail(self):
        process = multiprocessing.Process(
            target=_crash_after_complete_record,
            args=(str(self.log),),
        )
        process.start()
        process.join(20)
        self.assertEqual(process.exitcode, 77)

        replay = LiveFusionBus.replay(self.log)
        self.assertIn("evt-before-crash", replay.deltas)
        self.assertTrue(
            any(event["kind"] == "TORN_TAIL_IGNORED" for event in replay.recovery_events)
        )


if __name__ == "__main__":
    unittest.main()
