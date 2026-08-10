from __future__ import annotations

import json
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_execution_plane_v6 import PulseSpecV6
from research_entity.runtime.database_pulse_execution_plane_v6_4 import (
    DatabasePulseExecutionPlaneV6_4,
)


def seed() -> StateLedger:
    ledger = StateLedger()
    ledger.append_event(
        event_id="scheduler", idem="scheduler", base_epoch=ledger.epoch,
        event_type="DATABASE_PULSE_SCHEDULER_SET", writer="exact-source-probe",
        ops=[{
            "op":"SET","domain":"pulse_control","key":"scheduler",
            "value":{"enabled":True,"authority":"PERSISTED_RUNTIME_CONTROL"},
            "epistemic":"KNOWN","status":"CURRENT",
        }], committed_at="2026-08-10T05:40:00Z",
    )
    ledger.append_event(
        event_id="seed", idem="seed", base_epoch=ledger.epoch,
        event_type="V64_EXACT_SOURCE_SEED", writer="exact-source-probe",
        ops=[
            {"op":"SET","domain":"memory","key":"low",
             "value":{"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
             "epistemic":"KNOWN","status":"CURRENT"},
            {"op":"SET","domain":"memory","key":"zzzz-critical",
             "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
             "epistemic":"KNOWN","status":"CURRENT"},
        ], committed_at="2026-08-10T05:40:01Z",
    )
    return ledger


class V64BoundedExactSourceIntegration(unittest.TestCase):
    def test_sparse_receipts_rank_focus_model_and_replay_recovery(self):
        ledger = seed()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=32, now="init"
            )
            semantic_before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            first = runtime.run_pulse(PulseSpecV6(
                invocation_id="first", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=2, max_focus=1,
                full_audit_every=1000,
            ), model_assistant=lambda ctx: {"claim":"candidate","focus":ctx["focus"][0]["ref"]}, now="first")
            self.assertEqual(first.focus_refs, ("memory:zzzz-critical",))
            row = ledger.conn.execute(
                "SELECT model_candidate_json FROM pulse_execution_receipts_v6 WHERE invocation_id='first'"
            ).fetchone()
            model = json.loads(row[0])
            self.assertEqual(model["epistemic"], "UNKNOWN")
            self.assertEqual(model["authority"], "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
            self.assertFalse(runtime.rank_path.index_exists())

            for i in range(1, 65):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id=f"idle-{i}", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=2, max_focus=1,
                    full_audit_every=1000,
                ), now=f"idle-{i}")
            self.assertEqual(ledger.conn.execute(
                "SELECT COUNT(*) FROM pulse_execution_receipts_v6"
            ).fetchone()[0], 65)
            self.assertEqual(runtime.checkpoint_stats()["pulse"], 2)  # Pulse 32 and 64.
            self.assertEqual(runtime.verify_execution_chain()["transition_count"], 65)
            self.assertEqual((ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash), semantic_before)

            trusted = runtime._trusted_transition_head_hash()
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET state_hash='CORRUPT_EXACT_SOURCE' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            recovered = runtime.recover_last_known_good(
                now="recover", control_id="recover-exact-source"
            )
            self.assertEqual(recovered, 65)
            self.assertEqual(str(runtime._verify_state()["state_hash"]), trusted)
            verified = runtime.verify_execution_chain()
            self.assertTrue(verified["pass"])
            self.assertEqual(verified["repaired_corrupt_observations"], 1)
            self.assertEqual((ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash), semantic_before)
        finally:
            ledger.close()

    def test_event_atomic_catchup_keeps_exact_source_hash_boundaries(self):
        ledger = seed()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=32, now="init"
            )
            bounds=[]
            for i in range(35):
                ledger.append_event(
                    event_id=f"e-{i}", idem=f"e-{i}", base_epoch=ledger.epoch,
                    event_type="V64_EXACT_SOURCE_EVENT", writer="exact-source-probe",
                    ops=[{"op":"SET","domain":"memory","key":f"e{i}",
                          "value":{"priority":0.0,"i":i},"epistemic":"KNOWN","status":"CURRENT"}],
                    committed_at=f"2026-08-10T05:41:{i%60:02d}Z",
                )
                e=ledger.conn.execute(
                    "SELECT seq,epoch,semantic_state_hash FROM events ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                bounds.append((int(e["seq"]),int(e["epoch"]),str(e["semantic_state_hash"])))
            basis=ledger.epoch
            c=runtime.catch_up(
                invocation_id="catch-32", basis_epoch=basis, max_source_events=32, now="catch"
            )
            self.assertEqual(c.source_event_count,32)
            self.assertEqual(c.backlog_events_after,3)
            self.assertEqual(
                (c.source_event_seq_after,c.source_epoch_after,c.source_semantic_state_hash_after),
                bounds[31],
            )
            final=runtime.run_pulse(PulseSpecV6(
                invocation_id="finish",basis_epoch=basis,source_domains=("memory",),
                max_candidates=8,max_focus=1,max_source_events=32,
            ),now="finish")
            self.assertEqual(final.source_event_count,3)
            self.assertEqual(
                (final.source_event_seq_after,final.source_epoch_after,final.source_semantic_state_hash_after),
                bounds[-1],
            )
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
