from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_execution_plane_v5 import PulseSpecV5
from research_entity.runtime.database_pulse_execution_plane_v5_1 import (
    DatabasePulseExecutionPlaneV51,
)
from research_entity.runtime.database_pulse_v0 import DatabasePulseV0, PulseStateError


class DatabasePulseExecutionPlaneV51Tests(unittest.TestCase):
    def _legacy_lag_fixture(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="e1", idem="e1", base_epoch=0, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"a","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="e1",
        )
        e1_epoch = ledger.epoch
        e1_hash = ledger.semantic_state_hash
        from pathlib import Path as _Path
        sql = _Path(__file__).with_name("RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(
            encoding="utf-8"
        )
        ledger.conn.executescript(sql)
        ledger.conn.commit()
        legacy = DatabasePulseV0(ledger.conn)
        legacy.bootstrap(
            entity_id="entity", lineage_id="lineage", source_epoch=e1_epoch,
            graph_epoch=0, now="legacy",
        )
        ledger.append_event(
            event_id="e2", idem="e2", base_epoch=ledger.epoch, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"b","value":2,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="e2",
        )
        return ledger, e1_epoch, e1_hash

    def test_lagging_legacy_u12_epoch_fails_closed_without_explicit_epoch_identity(self):
        ledger, e1_epoch, _ = self._legacy_lag_fixture()
        try:
            self.assertLess(e1_epoch, ledger.epoch)
            with self.assertRaises(PulseStateError) as caught:
                DatabasePulseExecutionPlaneV51(
                    ledger, entity_id="entity", lineage_id="lineage", now="adopt"
                )
            self.assertIn("will not infer StateLedger epoch identity", str(caught.exception))
        finally:
            ledger.close()

    def test_explicit_legacy_stateledger_epoch_assertion_maps_to_exact_event_hash_boundary(self):
        ledger, e1_epoch, e1_hash = self._legacy_lag_fixture()
        try:
            runtime = DatabasePulseExecutionPlaneV51(
                ledger,
                entity_id="entity",
                lineage_id="lineage",
                legacy_source_epoch_is_stateledger_epoch=True,
                now="explicit-adopt",
            )
            state = runtime._state()
            body = runtime._decode_state_clay(state)
            self.assertEqual(int(state["source_epoch"]), e1_epoch)
            self.assertEqual(body["source_semantic_state_hash"], e1_hash)
            self.assertEqual(
                body["mode"], "EXPLICIT_LEGACY_STATELEDGER_EPOCH_ADOPTION_V5_1"
            )
            self.assertEqual(runtime._pending_event_count(), 1)
            out = runtime.run_pulse(
                PulseSpecV5(
                    "forward", basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_candidates=8, max_focus=1, max_source_events=1,
                    reentry_mode="NO_REENTRY",
                ),
                now="forward",
            )
            self.assertEqual(out.source_event_count, 1)
            self.assertEqual(out.source_epoch_after, ledger.epoch)
            self.assertEqual(out.source_semantic_state_hash_after, ledger.semantic_state_hash)
        finally:
            ledger.close()

    def test_aligned_legacy_u12_can_start_new_current_snapshot_without_historical_equivalence_claim(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=0, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"x","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="seed",
        )
        from pathlib import Path as _Path
        ledger.conn.executescript(_Path(__file__).with_name(
            "RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql"
        ).read_text(encoding="utf-8"))
        ledger.conn.commit()
        legacy = DatabasePulseV0(ledger.conn)
        legacy.bootstrap(
            entity_id="entity", lineage_id="lineage", source_epoch=ledger.epoch,
            graph_epoch=0, now="legacy",
        )
        try:
            runtime = DatabasePulseExecutionPlaneV51(
                ledger, entity_id="entity", lineage_id="lineage", now="aligned-adopt"
            )
            body = runtime._decode_state_clay(runtime._state())
            self.assertEqual(
                body["mode"], "ALIGNED_LEGACY_CURRENT_SNAPSHOT_ADOPTION_V5_1"
            )
            self.assertEqual(body["last_source_event_seq"], runtime._max_event_seq())
            self.assertEqual(body["source_semantic_state_hash"], ledger.semantic_state_hash)
            self.assertEqual(runtime._pending_event_count(), 0)
        finally:
            ledger.close()

    def test_two_independent_writers_same_invocation_create_one_pulse_and_one_registry_row(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "v51.sqlite"
            seed = StateLedger(path)
            seed.append_event(
                event_id="seed", idem="seed", base_epoch=0, event_type="TEST", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"critical",
                    "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                    "epistemic":"KNOWN","status":"CURRENT",
                }],
                committed_at="seed",
            )
            init = DatabasePulseExecutionPlaneV51(seed, now="bootstrap")
            epoch = seed.epoch
            seed.close()

            barrier = threading.Barrier(2)
            results = []
            errors = []
            lock = threading.Lock()

            def worker(worker_id: int):
                ledger = None
                try:
                    ledger = StateLedger(path)
                    runtime = DatabasePulseExecutionPlaneV51(
                        ledger, now=f"worker-{worker_id}-open"
                    )
                    spec = PulseSpecV5(
                        "raced-invocation",
                        basis_epoch=epoch,
                        source_domains=("memory",),
                        max_candidates=4,
                        max_focus=1,
                        max_source_events=4,
                        reentry_mode="NO_REENTRY",
                        full_audit_every=64,
                    )
                    barrier.wait(timeout=5)
                    out = runtime.run_pulse(spec, now=f"worker-{worker_id}-run")
                    with lock:
                        results.append(out)
                except Exception as exc:  # failure is test evidence, not swallowed
                    with lock:
                        errors.append(exc)
                finally:
                    if ledger is not None:
                        ledger.close()

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15)
            self.assertTrue(all(not t.is_alive() for t in threads), "writer thread hung")
            self.assertFalse(errors, errors)
            self.assertEqual(len(results), 2)
            self.assertEqual({r.pulse_id for r in results}, {results[0].pulse_id})
            self.assertEqual({r.receipt_hash for r in results}, {results[0].receipt_hash})
            self.assertEqual({r.pulse_index for r in results}, {1})
            self.assertEqual({r.status for r in results}, {"RECORDED", "ALREADY_RECORDED"})

            verify = StateLedger(path)
            try:
                runtime = DatabasePulseExecutionPlaneV51(verify, now="verify")
                self.assertEqual(int(runtime._state()["pulse_count"]), 1)
                self.assertEqual(int(runtime.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_v5_invocations "
                    "WHERE invocation_id='raced-invocation'"
                ).fetchone()[0]), 1)
                self.assertEqual(int(runtime.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_receipts"
                ).fetchone()[0]), 1)
                self.assertEqual(int(runtime.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_checkpoints WHERE pulse_id IS NOT NULL"
                ).fetchone()[0]), 1)
            finally:
                verify.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
