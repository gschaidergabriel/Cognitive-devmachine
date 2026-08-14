#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database_pulse_v0 import (
    DatabasePulseV0,
    PulseIntegrityError,
    PulseStateError,
    PulseStaleEpochError,
)

HERE = Path(__file__).resolve().parent
U12 = (HERE / "RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(encoding="utf-8")
U10_ACCESS = (HERE / "RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql").read_text(encoding="utf-8")
U11_ACCESS = (HERE / "RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql").read_text(encoding="utf-8")
U10_POSSIBILITY = (HERE / "RAE_UNIFIEDDB_V10_POSSIBILITY_COMPILER.sql").read_text(encoding="utf-8")


def memory_pulse(*, possibility: bool = False, semantic: bool = False):
    con = sqlite3.connect(":memory:")
    if possibility:
        con.executescript(U10_POSSIBILITY)
    if semantic:
        con.executescript(U10_ACCESS)
        con.executescript(U11_ACCESS)
    con.executescript(U12)
    pulse = DatabasePulseV0(con)
    pulse.bootstrap(
        entity_id="dr-unterweger-frank-personal-entity",
        lineage_id="test-lineage",
        source_epoch=7 if semantic else 0,
        graph_epoch=9 if semantic else 0,
        now="t0",
    )
    return con, pulse


class DatabasePulseV0Tests(unittest.TestCase):
    def test_zero_model_idle_pulse_is_not_state_transition(self):
        con, pulse = memory_pulse()
        try:
            receipt = pulse.pulse(max_deltas=8, now="t1")
            self.assertEqual(receipt.model_call_count, 0)
            self.assertEqual(receipt.applied_delta_count, 0)
            row = con.execute(
                "SELECT pulse_count,state_transition_count,entity_epoch FROM frank_database_pulse_state"
            ).fetchone()
            self.assertEqual(tuple(row), (1, 0, 1))
        finally:
            con.close()

    def test_bounded_delta_consumption_and_backlog(self):
        con, pulse = memory_pulse()
        try:
            for i in range(5):
                pulse.admit_delta(
                    delta_id=f"d{i}",
                    changed_ref=f"memory:{i}",
                    reason_class="MEMORY_UPDATE",
                    payload={"value": i},
                    source_epoch=1,
                    graph_epoch=1,
                    now=f"a{i}",
                )
            r1 = pulse.pulse(max_deltas=2, now="p1")
            r2 = pulse.pulse(max_deltas=2, now="p2")
            r3 = pulse.pulse(max_deltas=2, now="p3")
            self.assertEqual(
                [(r1.applied_delta_count, r1.backlog_after),
                 (r2.applied_delta_count, r2.backlog_after),
                 (r3.applied_delta_count, r3.backlog_after)],
                [(2, 3), (2, 1), (1, 0)],
            )
            self.assertEqual(
                con.execute("SELECT state_transition_count FROM frank_database_pulse_state").fetchone()[0],
                5,
            )
        finally:
            con.close()

    def test_delta_admission_is_idempotent(self):
        con, pulse = memory_pulse()
        try:
            kwargs = dict(
                delta_id="same",
                changed_ref="self:goal",
                reason_class="STATE_UPDATE",
                payload={"x": 1},
                source_epoch=1,
                graph_epoch=1,
            )
            self.assertTrue(pulse.admit_delta(**kwargs, now="a"))
            self.assertFalse(pulse.admit_delta(**kwargs, now="b"))
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM frank_database_pulse_delta_queue").fetchone()[0], 1
            )
        finally:
            con.close()

    def test_pause_blocks_pulse_and_resume_preserves_lineage(self):
        con, pulse = memory_pulse()
        try:
            lineage = con.execute(
                "SELECT lineage_id FROM frank_database_pulse_state"
            ).fetchone()[0]
            pulse.set_status("PAUSED", now="pause")
            with self.assertRaises(PulseStateError):
                pulse.pulse(now="blocked")
            pulse.set_status("PULSING", now="resume")
            pulse.pulse(now="after")
            self.assertEqual(
                con.execute("SELECT lineage_id FROM frank_database_pulse_state").fetchone()[0], lineage
            )
        finally:
            con.close()

    def test_injected_mid_transaction_fault_rolls_back_every_effect(self):
        con, pulse = memory_pulse(possibility=True)
        try:
            pulse.admit_delta(
                delta_id="fault-delta",
                changed_ref="goal:1",
                reason_class="GOAL_UPDATE",
                payload={"goal": "x"},
                source_epoch=1,
                graph_epoch=1,
                now="a",
            )
            before = tuple(con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone())
            with self.assertRaisesRegex(RuntimeError, "injected fault"):
                pulse.pulse(now="fault", fault_after_apply=True)
            after = tuple(con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone())
            self.assertEqual(before, after)
            self.assertIsNone(
                con.execute(
                    "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue WHERE delta_id='fault-delta'"
                ).fetchone()[0]
            )
            self.assertEqual(con.execute("SELECT COUNT(*) FROM frank_database_pulse_receipts").fetchone()[0], 0)
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM clay_possibility_invalidation_queue").fetchone()[0], 0
            )
        finally:
            con.close()

    def test_u10_possibility_invalidation_is_coupled_to_successful_pulse(self):
        con, pulse = memory_pulse(possibility=True)
        try:
            pulse.admit_delta(
                delta_id="facet",
                changed_ref="capability:vision",
                reason_class="FACET_AVAILABILITY",
                payload={"available": False},
                source_epoch=2,
                graph_epoch=3,
                now="a",
            )
            receipt = pulse.pulse(now="p")
            row = con.execute(
                "SELECT changed_ref,repair_mode,status FROM clay_possibility_invalidation_queue"
            ).fetchone()
            self.assertEqual(tuple(row), ("capability:vision", "FACET_ONLY", "OPEN"))
            self.assertEqual(receipt.applied_delta_count, 1)
        finally:
            con.close()

    def test_corrupt_state_fails_closed_then_recovers_latest_checkpoint(self):
        con, pulse = memory_pulse()
        try:
            pulse.admit_delta(
                delta_id="d", changed_ref="memory:d", reason_class="MEMORY_UPDATE",
                payload={"v": 1}, source_epoch=1, graph_epoch=1, now="a"
            )
            good = pulse.pulse(now="good")
            con.execute(
                "UPDATE frank_database_pulse_state SET state_clay='CORRUPT' WHERE singleton_id=1"
            )
            con.commit()
            with self.assertRaises(PulseIntegrityError):
                pulse.pulse(now="must-not-run")
            recovered_index = pulse.recover_last_known_good(now="recover")
            self.assertEqual(recovered_index, good.pulse_index)
            next_receipt = pulse.pulse(now="post-recovery")
            self.assertEqual(next_receipt.pulse_index, good.pulse_index + 1)
        finally:
            con.close()

    def test_corrupt_delta_payload_fails_closed_without_ack(self):
        con, pulse = memory_pulse()
        try:
            pulse.admit_delta(
                delta_id="tamper", changed_ref="world:x", reason_class="WORLD_UPDATE",
                payload={"v": 1}, source_epoch=1, graph_epoch=1, now="a"
            )
            con.execute(
                "UPDATE frank_database_pulse_delta_queue SET payload_clay='tampered' WHERE delta_id='tamper'"
            )
            con.commit()
            with self.assertRaises(PulseIntegrityError):
                pulse.pulse(now="p")
            self.assertIsNone(
                con.execute(
                    "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue WHERE delta_id='tamper'"
                ).fetchone()[0]
            )
        finally:
            con.close()

    def test_semantic_access_is_bound_only_at_matching_epoch(self):
        con, pulse = memory_pulse(semantic=True)
        try:
            con.execute(
                """INSERT INTO semantic_access_generations
                   (generation_id,source_epoch,graph_epoch,derivation_id,derivation_hash,seed_count,
                    path_count,verification_clay,status,created_at,verified_at,published_at)
                   VALUES('g1',7,9,'d','h',1,1,'{}','CURRENT','t','t','t')"""
            )
            con.execute(
                "INSERT INTO semantic_access_head VALUES('CURRENT','g1',7,9,'h','t')"
            )
            con.commit()
            coherent = pulse.pulse(
                now="coherent", expected_source_epoch=7, expected_graph_epoch=9
            )
            self.assertEqual(coherent.semantic_generation_id, "g1")

            pulse.admit_delta(
                delta_id="epoch-advance", changed_ref="world:new", reason_class="WORLD_UPDATE",
                payload={"new": True}, source_epoch=8, graph_epoch=10, now="a"
            )
            stale = pulse.pulse(now="advance")
            self.assertIsNone(stale.semantic_generation_id)
            state = con.execute(
                "SELECT state_clay FROM frank_database_pulse_state"
            ).fetchone()[0]
            self.assertIn("STALE_FAIL_CLOSED", state)
            with self.assertRaises(PulseStaleEpochError):
                pulse.pulse(now="strict", expected_source_epoch=8, expected_graph_epoch=10)
        finally:
            con.close()

    def test_crash_restart_continuity_on_file_database(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pulse.db"
            con = sqlite3.connect(path)
            con.executescript(U12)
            pulse = DatabasePulseV0(con)
            pulse.bootstrap(entity_id="frank", lineage_id="persistent-lineage", now="boot")
            pulse.admit_delta(
                delta_id="d1", changed_ref="memory:1", reason_class="MEMORY_UPDATE",
                payload={"v": 1}, source_epoch=1, graph_epoch=1, now="a"
            )
            first = pulse.pulse(now="first")
            con.close()

            con2 = sqlite3.connect(path)
            pulse2 = DatabasePulseV0(con2)
            pulse2.bootstrap(entity_id="ignored", lineage_id="ignored", now="restart")
            second = pulse2.pulse(now="second")
            self.assertEqual(second.pulse_index, first.pulse_index + 1)
            self.assertEqual(
                con2.execute("SELECT lineage_id FROM frank_database_pulse_state").fetchone()[0],
                "persistent-lineage",
            )
            con2.close()

    def test_deterministic_replay_same_inputs_same_post_hash(self):
        def replay(now: str) -> str:
            con, pulse = memory_pulse()
            try:
                for i in range(4):
                    pulse.admit_delta(
                        delta_id=f"d{i}", changed_ref=f"r{i}", reason_class="STATE_UPDATE",
                        payload={"i": i}, source_epoch=2, graph_epoch=3, now=f"a{i}"
                    )
                return pulse.pulse(max_deltas=4, now=now).post_state_hash
            finally:
                con.close()

        self.assertEqual(replay("walltime-a"), replay("walltime-b"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
