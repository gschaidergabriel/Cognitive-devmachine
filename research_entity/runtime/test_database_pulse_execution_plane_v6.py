from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.auth_shadow_focus_guard import FocusIntegrityError
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_execution_plane_v6 import (
    DatabasePulseExecutionPlaneV6,
    PulseSpecV6,
    PulseV6Backlog,
    PulseV6IntegrityError,
    PulseV6InvocationConflict,
)
from research_entity.runtime.database_pulse_runtime_v5 import DatabasePulseRuntimeV5


def enable_scheduler(ledger: StateLedger, *, event_id: str = "scheduler-on") -> None:
    ledger.append_event(
        event_id=event_id,
        idem=event_id,
        base_epoch=ledger.epoch,
        event_type="DATABASE_PULSE_SCHEDULER_SET",
        writer="test",
        ops=[{
            "op":"SET","domain":"pulse_control","key":"scheduler",
            "value":{"enabled":True,"reason":"test","authority":"PERSISTED_RUNTIME_CONTROL"},
            "epistemic":"KNOWN","status":"CURRENT",
        }],
        provenance={"test":"v6"},
        source={"actor":"test"},
        execution={"effect":"PULSE_SCHEDULER_STATE_ONLY"},
        committed_at="2026-08-10T04:00:00Z",
    )


def seed_ledger(path: str = ":memory:", *, rows: int = 8) -> StateLedger:
    ledger = StateLedger(path)
    enable_scheduler(ledger)
    ops = []
    for i in range(rows):
        ops.append({
            "op":"SET","domain":"memory","key":f"k{i:04d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN","status":"CURRENT",
        })
    ops.append({
        "op":"SET","domain":"memory","key":"zzzz-critical",
        "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
        "epistemic":"KNOWN","status":"CURRENT",
    })
    ledger.append_event(
        event_id="seed-memory", idem="seed-memory", base_epoch=ledger.epoch,
        event_type="V6_TEST_SEED", writer="test", ops=ops,
        committed_at="2026-08-10T04:00:01Z",
    )
    return ledger


def roots(ledger: StateLedger):
    return ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash


class DatabasePulseExecutionPlaneV6Tests(unittest.TestCase):
    def test_idle_pulse_does_not_churn_semantic_state_and_query_receipt_survives(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            plane = UnifiedDBQueryPlane(ledger)
            prepared = plane.query(QuerySpec(
                query_id="prepared-before-v6-idle",
                domains=("memory",), epistemic=("KNOWN",),
                limit=8, basis_epoch=ledger.epoch,
            ))
            before = roots(ledger)
            receipt = runtime.run_pulse(PulseSpecV6(
                invocation_id="idle-1", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=2,
            ), now="idle-1")
            self.assertEqual(receipt.status, "COMMITTED")
            self.assertEqual(receipt.source_event_count, 0)
            self.assertEqual(before, roots(ledger))
            selected = plane.select_for_assembly(prepared)["selected"]
            self.assertTrue(selected)
            self.assertEqual(
                ledger.conn.execute("SELECT COUNT(*) FROM state WHERE domain='pulse'").fetchone()[0], 0
            )
            self.assertEqual(
                ledger.conn.execute("SELECT COUNT(*) FROM events WHERE event_type='DATABASE_PULSE'").fetchone()[0], 0
            )
        finally:
            ledger.close()

    def test_current_main_semantic_runtime_v5_churns_while_v6_does_not(self):
        semantic = seed_ledger()
        direct = seed_ledger()
        try:
            baseline = DatabasePulseRuntimeV5(semantic)
            sem_before = roots(semantic)
            baseline.run_pulse(PulseSpec(
                pulse_id="semantic-v5", basis_epoch=semantic.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
                reentry_mode="NO_REENTRY",
            ), committed_at="2026-08-10T04:00:02Z")
            self.assertEqual(semantic.epoch, sem_before[0] + 1)
            self.assertNotEqual(semantic.semantic_state_hash, sem_before[1])

            v6 = DatabasePulseExecutionPlaneV6(direct, now="init")
            direct_before = roots(direct)
            v6.run_pulse(PulseSpecV6(
                invocation_id="direct-v6", basis_epoch=direct.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
                reentry_mode="NO_REENTRY",
            ), now="direct-v6")
            self.assertEqual(roots(direct), direct_before)
        finally:
            semantic.close(); direct.close()

    def test_one_180_op_semantic_transaction_is_one_source_event(self):
        ledger = seed_ledger(rows=2)
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            ops = [{
                "op":"SET","domain":"memory","key":f"atomic-{i:04d}",
                "value":{"priority":0.0,"i":i},"epistemic":"KNOWN","status":"CURRENT",
            } for i in range(180)]
            ledger.append_event(
                event_id="atomic-180", idem="atomic-180", base_epoch=ledger.epoch,
                event_type="ATOMIC_180_OP_EVENT", writer="test", ops=ops,
                committed_at="2026-08-10T04:00:03Z",
            )
            semantic_before = roots(ledger)
            self.assertEqual(runtime.pending_event_count(), 1)
            receipt = runtime.run_pulse(PulseSpecV6(
                invocation_id="atomic-pulse", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=16, max_focus=1,
                max_source_events=1, reentry_mode="NO_REENTRY",
            ), now="atomic-pulse")
            self.assertEqual(receipt.source_event_count, 1)
            self.assertEqual(receipt.memory_update_observed_count, 180)
            self.assertEqual(receipt.source_epoch_after, ledger.epoch)
            self.assertEqual(receipt.source_semantic_state_hash_after, ledger.semantic_state_hash)
            self.assertEqual(receipt.backlog_events_after, 0)
            self.assertEqual(roots(ledger), semantic_before)
        finally:
            ledger.close()

    def test_many_events_require_bounded_event_atomic_catchup(self):
        ledger = seed_ledger(rows=2)
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            event_boundaries = []
            for i in range(75):
                ledger.append_event(
                    event_id=f"many-{i:03d}", idem=f"many-{i:03d}", base_epoch=ledger.epoch,
                    event_type="ONE_EVENT", writer="test",
                    ops=[{
                        "op":"SET","domain":"memory","key":f"many-{i:03d}",
                        "value":{"priority":0.0,"i":i},"epistemic":"KNOWN","status":"CURRENT",
                    }], committed_at=f"2026-08-10T04:01:{i%60:02d}Z",
                )
                row = ledger.conn.execute(
                    "SELECT seq,epoch,semantic_state_hash FROM events ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                event_boundaries.append((int(row["seq"]), int(row["epoch"]), str(row["semantic_state_hash"])))

            basis = ledger.epoch
            with self.assertRaises(PulseV6Backlog):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id="must-block", basis_epoch=basis,
                    source_domains=("memory",), max_candidates=16, max_focus=1,
                    max_source_events=32,
                ))

            r1 = runtime.catch_up(
                invocation_id="catch-1", basis_epoch=basis, max_source_events=32, now="catch-1"
            )
            self.assertEqual(r1.source_event_count, 32)
            self.assertEqual(r1.backlog_events_after, 43)
            self.assertEqual(
                (r1.source_event_seq_after, r1.source_epoch_after, r1.source_semantic_state_hash_after),
                event_boundaries[31],
            )
            r2 = runtime.catch_up(
                invocation_id="catch-2", basis_epoch=basis, max_source_events=32, now="catch-2"
            )
            self.assertEqual(r2.source_event_count, 32)
            self.assertEqual(r2.backlog_events_after, 11)
            self.assertEqual(
                (r2.source_event_seq_after, r2.source_epoch_after, r2.source_semantic_state_hash_after),
                event_boundaries[63],
            )
            final = runtime.run_pulse(PulseSpecV6(
                invocation_id="after-catchup", basis_epoch=basis,
                source_domains=("memory",), max_candidates=16, max_focus=1,
                max_source_events=32,
            ), now="after-catchup")
            self.assertEqual(final.source_event_count, 11)
            self.assertEqual(final.backlog_events_after, 0)
            self.assertEqual(
                (final.source_event_seq_after, final.source_epoch_after, final.source_semantic_state_hash_after),
                event_boundaries[-1],
            )
            self.assertEqual(runtime.pending_event_count(), 0)
        finally:
            ledger.close()

    def test_model_candidate_is_execution_receipt_only(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            before = roots(ledger)
            receipt = runtime.run_pulse(PulseSpecV6(
                invocation_id="model", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), model_assistant=lambda ctx: {"hypothesis":"maybe","focus":ctx["focus"][0]["ref"]}, now="model")
            self.assertEqual(receipt.model_call_count, 1)
            row = ledger.conn.execute(
                "SELECT model_candidate_json,model_candidate_hash FROM pulse_execution_receipts_v6 WHERE invocation_id='model'"
            ).fetchone()
            self.assertIsNotNone(row["model_candidate_json"])
            self.assertIsNotNone(row["model_candidate_hash"])
            self.assertEqual(ledger.conn.execute(
                "SELECT COUNT(*) FROM state WHERE domain='pulse' OR domain='pulse_control' AND k='model_candidate'"
            ).fetchone()[0], 0)
            self.assertEqual(before, roots(ledger))
            self.assertEqual(receipt.tool_call_count, 0)
            self.assertEqual(receipt.effect_count, 0)
        finally:
            ledger.close()

    def test_selected_raw_tamper_is_caught_at_focus_use_boundary_between_full_audits(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="prime-shadow", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
                full_audit_every=1000,
            ), now="prime")
            ledger.conn.execute(
                "UPDATE state SET value_json=? WHERE domain='memory' AND k='zzzz-critical'",
                (json.dumps({"fact":"tampered","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0}),),
            )
            ledger.conn.commit()
            with self.assertRaises(FocusIntegrityError):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id="tampered-selected", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                    full_audit_every=1000,
                ), now="tampered-selected")
        finally:
            ledger.close()

    def test_unselected_raw_tamper_is_caught_by_periodic_full_audit(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="audit-prime", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
                full_audit_every=2,
            ), now="audit-prime")
            ledger.conn.execute(
                "UPDATE state SET value_json=? WHERE domain='memory' AND k='k0000'",
                (json.dumps({"fact":"latent-tamper","priority":0.0}),),
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id="periodic-audit", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                    full_audit_every=2,
                ), now="periodic-audit")
        finally:
            ledger.close()

    def test_invocation_is_idempotent_and_spec_reuse_conflicts(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            spec = PulseSpecV6(
                invocation_id="idem", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            )
            first = runtime.run_pulse(spec, now="idem-1")
            state_after = runtime._verify_state()
            second = runtime.run_pulse(spec, now="idem-2")
            self.assertEqual(second.status, "ALREADY_COMMITTED")
            self.assertEqual(second.receipt_hash, first.receipt_hash)
            self.assertEqual(int(runtime._verify_state()["pulse_count"]), int(state_after["pulse_count"]))
            with self.assertRaises(PulseV6InvocationConflict):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id="idem", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=2,
                ))
        finally:
            ledger.close()

    def test_last_known_good_recovers_corrupted_execution_state_only(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            receipt = runtime.run_pulse(PulseSpecV6(
                invocation_id="lkg", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="lkg")
            semantic_before = roots(ledger)
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET last_assembly_hash='CORRUPT' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime._verify_state()
            restored = runtime.recover_last_known_good(now="recover")
            self.assertEqual(restored, receipt.pulse_index)
            self.assertEqual(runtime._verify_state()["last_assembly_hash"], receipt.assembly_hash)
            self.assertEqual(roots(ledger), semantic_before)
        finally:
            ledger.close()

    def test_rank_read_never_builds_or_drops_index_inside_cognitive_pulse(self):
        ledger = seed_ledger(rows=32)
        try:
            runtime = DatabasePulseExecutionPlaneV6(ledger, now="init")
            before = runtime.rank_path.index_exists()
            receipt = runtime.run_pulse(PulseSpecV6(
                invocation_id="rank-read", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=16, max_focus=2,
            ), now="rank-read")
            self.assertEqual(runtime.rank_path.index_exists(), before)
            self.assertIn(receipt.physical_rank_mode, {
                "ONLINE", "ONLINE_PENDING_COMPILE", "ONLINE_PENDING_DECOMPILE", "COMPILED_INDEX"
            })
        finally:
            ledger.close()

    def test_same_invocation_two_connection_race_commits_once_when_wal_family_is_safe(self):
        safety = DatabasePulseExecutionPlaneV6.sqlite_wal_multiwriter_safety()
        if not safety["wal_reset_bug_fixed_family"]:
            self.skipTest(f"SQLite {safety['sqlite_version']} is outside WAL-reset fixed families")
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "v6-race.sqlite")
            seed = seed_ledger(path)
            try:
                runtime = DatabasePulseExecutionPlaneV6(seed, now="init")
                runtime.focus_guard.refresh_and_verify_refs(("memory:zzzz-critical",), now="prebuild-shadow")
                basis = seed.epoch
            finally:
                seed.close()

            barrier = threading.Barrier(2)
            results = []
            errors = []
            lock = threading.Lock()

            def worker(label: str):
                ledger = None
                try:
                    ledger = StateLedger(path)
                    rt = DatabasePulseExecutionPlaneV6(ledger, now=f"init-{label}")
                    barrier.wait(timeout=5)
                    out = rt.run_pulse(PulseSpecV6(
                        invocation_id="same-race", basis_epoch=basis,
                        source_domains=("memory",), max_candidates=8, max_focus=1,
                    ), now=f"race-{label}")
                    with lock:
                        results.append(out)
                except Exception as exc:
                    with lock:
                        errors.append(exc)
                finally:
                    if ledger is not None:
                        ledger.close()

            t1 = threading.Thread(target=worker, args=("a",))
            t2 = threading.Thread(target=worker, args=("b",))
            t1.start(); t2.start(); t1.join(15); t2.join(15)
            self.assertFalse(t1.is_alive() or t2.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual({x.receipt_hash for x in results}, {results[0].receipt_hash})
            self.assertEqual({x.status for x in results}, {"COMMITTED", "ALREADY_COMMITTED"})

            verify = StateLedger(path)
            try:
                self.assertEqual(verify.conn.execute(
                    "SELECT COUNT(*) FROM pulse_execution_receipts_v6 WHERE invocation_id='same-race'"
                ).fetchone()[0], 1)
                self.assertEqual(verify.conn.execute(
                    "SELECT pulse_count FROM pulse_execution_state_v6 WHERE singleton_id=1"
                ).fetchone()[0], 1)
            finally:
                verify.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
