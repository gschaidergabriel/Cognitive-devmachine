from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_rank_path_v5 import RankPhysicalStateStale
from research_entity.runtime.database_pulse_rank_path_v5_1_attested import (
    AttestedAdaptiveAuthoritativeRankPathV5_1,
    EXPECTED_INDEX_SQL_HASH,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics():
    return CompileEconomics(
        build_cost_us=1000.0, online_query_us=100.0, compiled_query_us=10.0,
        online_quality=1.0, compiled_quality=1.0,
        expected_reads_before_invalidation=0.0, safety_factor=1.0,
    )


def stable_long():
    return [EpochReadLifetime(i + 1, 200) for i in range(8)]


def sparse():
    return [EpochReadLifetime(1, 200), EpochReadLifetime(2, 200)]


def seed():
    ledger = StateLedger()
    ops = [
        {
            "op": "SET", "domain": "memory", "key": f"k{i:03d}",
            "value": {
                "priority": i / 100.0, "urgency": (100 - i) / 200.0,
                "salience": (i % 13) / 13.0, "novelty": (i % 7) / 7.0,
            },
            "epistemic": "KNOWN", "status": "CURRENT",
        }
        for i in range(100)
    ]
    ledger.append_event(
        event_id="seed", idem="seed", base_epoch=0, event_type="SEED", writer="test", ops=ops,
        committed_at="2026-08-10T05:15:00Z",
    )
    return ledger, AttestedAdaptiveAuthoritativeRankPathV5_1(ledger)


def plan(v, history=None):
    return v.plan_lifecycle(
        basis_epoch=v.ledger.epoch, economics_without_horizon=economics(),
        pulse_history=history or stable_long(), actor="test-worker",
        policy_provenance_ref="fixture://compile-economics-v1",
    )


def select(v, history=None):
    return v.select(
        source_domains=("memory",), basis_epoch=v.ledger.epoch,
        max_candidates=50, max_focus=8, economics_without_horizon=economics(),
        pulse_history=history or stable_long(), actor="test-worker",
        policy_provenance_ref="fixture://compile-economics-v1",
    )


class AttestedRankPathV51Tests(unittest.TestCase):
    def test_build_persists_provenance_and_admits_compiled_read(self):
        ledger, v = seed()
        p = plan(v)
        self.assertEqual(p.maintenance_action, "BUILD_INDEX")
        m = v.apply_maintenance(p)
        self.assertEqual(m.status, "BUILT")
        self.assertTrue(m.persisted)
        identity = v.physical_identity()
        self.assertEqual(identity.state, "ATTESTED")
        rows = v.maintenance_receipts()
        self.assertEqual(rows[-1]["actor"], "test-worker")
        self.assertEqual(rows[-1]["policy_provenance_ref"], "fixture://compile-economics-v1")
        self.assertEqual(rows[-1]["index_sql_hash_after"], EXPECTED_INDEX_SQL_HASH)
        r = select(v)
        self.assertEqual(r.physical_read_mode, "COMPILED_ATTESTED_INDEX")
        self.assertTrue(any(INDEX_NAME in x for x in r.query_plan))
        ledger.close()

    def test_legacy_correct_but_unattested_index_falls_online_then_rebuilds(self):
        ledger, v = seed()
        v.v3.ensure_index()
        self.assertEqual(v.physical_identity().state, "UNATTESTED")
        r = select(v)
        self.assertEqual(r.physical_read_mode, "ONLINE_PENDING_REBUILD")
        self.assertEqual(r.maintenance_action, "REBUILD_INDEX")
        self.assertFalse(any(INDEX_NAME in x for x in r.query_plan))
        m = v.apply_maintenance(plan(v))
        self.assertEqual(m.status, "REBUILT")
        self.assertEqual(v.physical_identity().state, "ATTESTED")
        ledger.close()

    def test_same_name_wrong_definition_never_admitted(self):
        ledger, v = seed()
        v.con.execute(f"CREATE INDEX {INDEX_NAME} ON state(domain)")
        v.con.commit()
        self.assertEqual(v.physical_identity().state, "DEFINITION_DRIFT")
        r = select(v)
        self.assertEqual(r.physical_read_mode, "ONLINE_PENDING_REBUILD")
        self.assertFalse(any(INDEX_NAME in x for x in r.query_plan))
        m = v.apply_maintenance(plan(v))
        self.assertEqual(m.status, "REBUILT")
        self.assertEqual(v.physical_identity().state, "ATTESTED")
        ledger.close()

    def test_runtime_capability_drift_revokes_compiled_use(self):
        ledger, v = seed()
        v.apply_maintenance(plan(v))
        original = v._runtime_env_payload
        current = dict(original())
        current["platform_release"] = current["platform_release"] + "-SIMULATED-DRIFT"
        v._runtime_env_payload = lambda: current
        self.assertEqual(v.physical_identity().state, "RUNTIME_DRIFT")
        r = select(v)
        self.assertEqual(r.physical_read_mode, "ONLINE_PENDING_REBUILD")
        self.assertEqual(r.maintenance_action, "REBUILD_INDEX")
        self.assertFalse(any(INDEX_NAME in x for x in r.query_plan))
        ledger.close()

    def test_physical_definition_change_after_plan_fails_cas(self):
        ledger, v = seed()
        v.v3.ensure_index()
        p = plan(v)
        v.con.execute(f"DROP INDEX {INDEX_NAME}")
        v.con.execute(f"CREATE INDEX {INDEX_NAME} ON state(k)")
        v.con.commit()
        with self.assertRaises(RankPhysicalStateStale):
            v.apply_maintenance(p)
        ledger.close()

    def test_missing_actor_or_policy_provenance_fails_closed(self):
        ledger, v = seed()
        with self.assertRaises(ValueError):
            v.plan_lifecycle(
                basis_epoch=ledger.epoch, economics_without_horizon=economics(),
                pulse_history=stable_long(), actor="", policy_provenance_ref="fixture://policy",
            )
        with self.assertRaises(ValueError):
            v.plan_lifecycle(
                basis_epoch=ledger.epoch, economics_without_horizon=economics(),
                pulse_history=stable_long(), actor="worker", policy_provenance_ref="",
            )
        ledger.close()

    def test_receipt_failure_rolls_back_rebuild_and_log_migration(self):
        class BrokenReceipt(AttestedAdaptiveAuthoritativeRankPathV5_1):
            def _persist_receipt_no_commit(self, values):
                raise RuntimeError("injected receipt failure")

        ledger, _ = seed()
        v = BrokenReceipt(ledger)
        v.con.execute(f"CREATE INDEX {INDEX_NAME} ON state(domain)")
        v.con.commit()
        before = v._raw_index_info()
        roots = (ledger.semantic_state_hash, ledger.trace_root_hash)
        m = v.apply_maintenance(plan(v))
        self.assertEqual(m.status, "FAILED_RETRYABLE_PHYSICAL_MAINTENANCE")
        self.assertEqual(before, v._raw_index_info())
        self.assertEqual(v.physical_identity().state, "DEFINITION_DRIFT")
        self.assertEqual(roots, (ledger.semantic_state_hash, ledger.trace_root_hash))
        self.assertFalse(v._maintenance_log_exists())
        ledger.close()

    def test_online_and_attested_compiled_semantics_are_identical(self):
        ledger, v = seed()
        online = select(v, sparse())
        v.apply_maintenance(plan(v))
        compiled = select(v, stable_long())
        self.assertEqual(online.candidate_refs, compiled.candidate_refs)
        self.assertEqual(online.focus_refs, compiled.focus_refs)
        self.assertEqual(online.candidate_scores, compiled.candidate_scores)
        ledger.close()

    def test_online_policy_drops_attested_index_with_audited_provenance(self):
        ledger, v = seed()
        v.apply_maintenance(plan(v))
        p = plan(v, sparse())
        self.assertEqual(p.maintenance_action, "DROP_INDEX")
        m = v.apply_maintenance(p)
        self.assertEqual(m.status, "DROPPED")
        self.assertEqual(v.physical_identity().state, "ABSENT")
        self.assertEqual(m.semantic_state_hash_before, m.semantic_state_hash_after)
        self.assertEqual(m.trace_root_hash_before, m.trace_root_hash_after)
        ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
