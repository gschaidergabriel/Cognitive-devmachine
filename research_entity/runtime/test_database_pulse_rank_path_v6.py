from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger, h
from research_entity.runtime.database_pulse_rank_path_v5 import (
    RankLifecyclePlan,
    RankPhysicalStateStale,
)
from research_entity.runtime.database_pulse_rank_path_v6 import (
    AdaptiveAuthoritativeRankPathV6,
    LEGACY_PROVENANCE_STATUS,
    MAINTENANCE_LOG_TABLE_V6,
    NATIVE_PROVENANCE_STATUS,
)


def _plan(
    path: AdaptiveAuthoritativeRankPathV6,
    action: str,
    *,
    actual_index_present: bool | None = None,
) -> RankLifecyclePlan:
    if actual_index_present is None:
        actual_index_present = path.index_exists()
    desired_mode = "COMPILED_INDEX" if action == "BUILD_INDEX" else "ONLINE"
    body = {
        "basis_epoch": path.ledger.epoch,
        "semantic_state_hash": path.ledger.semantic_state_hash,
        "desired_mode": desired_mode,
        "actual_index_present": bool(actual_index_present),
        "maintenance_action": action,
        "test": True,
    }
    return RankLifecyclePlan(
        basis_epoch=path.ledger.epoch,
        semantic_state_hash=path.ledger.semantic_state_hash,
        desired_mode=desired_mode,
        actual_index_present=bool(actual_index_present),
        maintenance_action=action,
        horizon_status="TEST_FIXED",
        horizon_reads_lower_bound=1000.0,
        compile_reason="TEST_FIXED",
        guarded_break_even_reads=10.0,
        plan_hash=h(body),
    )


def _apply(path: AdaptiveAuthoritativeRankPathV6, plan: RankLifecyclePlan):
    return path.apply_maintenance(
        plan,
        actor="research-entity:test-worker",
        policy_provenance_ref="test://compile-policy/decision-1",
        policy_decision_hash=h({"policy": "test", "decision": plan.maintenance_action}),
    )


class DatabasePulseRankPathV6Tests(unittest.TestCase):
    def test_native_build_is_atomic_and_provenance_complete(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        state_before = ledger.semantic_state_hash
        trace_before = ledger.trace_root_hash

        receipt = _apply(path, _plan(path, "BUILD_INDEX"))

        self.assertEqual(receipt.status, "BUILT")
        self.assertTrue(receipt.persisted)
        self.assertEqual(receipt.audit_sequence, 1)
        self.assertTrue(path.index_exists())
        self.assertEqual(ledger.semantic_state_hash, state_before)
        self.assertEqual(ledger.trace_root_hash, trace_before)
        rows = path.maintenance_receipts_v6()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["audit_sequence"], 1)
        self.assertEqual(row["actor"], "research-entity:test-worker")
        self.assertEqual(row["policy_provenance_ref"], "test://compile-policy/decision-1")
        self.assertNotEqual(row["policy_decision_hash"], "UNKNOWN")
        self.assertEqual(row["provenance_status"], NATIVE_PROVENANCE_STATUS)
        self.assertIsNone(row["legacy_source_receipt_id"])

    def test_native_unknown_or_blank_provenance_is_rejected_before_effect(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        plan = _plan(path, "BUILD_INDEX")
        cases = [
            {"actor": "", "policy_provenance_ref": "p", "policy_decision_hash": "h"},
            {"actor": "UNKNOWN", "policy_provenance_ref": "p", "policy_decision_hash": "h"},
            {"actor": "a", "policy_provenance_ref": "UNKNOWN", "policy_decision_hash": "h"},
            {"actor": "a", "policy_provenance_ref": "p", "policy_decision_hash": "UNKNOWN"},
        ]
        for kwargs in cases:
            with self.assertRaises(ValueError):
                path.apply_maintenance(plan, **kwargs)
            self.assertFalse(path.index_exists())
            self.assertEqual(path.maintenance_receipts_v6(), [])

    def test_receipt_insert_failure_rolls_back_build(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        state_before = ledger.semantic_state_hash
        trace_before = ledger.trace_root_hash

        # Deliberately create a table that supports V6 sequencing/indexes but lacks actor.
        # Native receipt insertion therefore fails after CREATE INDEX in the same transaction.
        path.con.execute(
            f"""CREATE TABLE {MAINTENANCE_LOG_TABLE_V6}(
                receipt_id TEXT PRIMARY KEY,
                audit_sequence INTEGER NOT NULL UNIQUE,
                plan_hash TEXT NOT NULL,
                basis_epoch INTEGER NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                index_present_before INTEGER NOT NULL,
                index_present_after INTEGER NOT NULL,
                semantic_state_hash_before TEXT NOT NULL,
                semantic_state_hash_after TEXT NOT NULL,
                trace_root_hash_before TEXT NOT NULL,
                trace_root_hash_after TEXT NOT NULL,
                policy_provenance_ref TEXT NOT NULL,
                policy_decision_hash TEXT NOT NULL,
                provenance_status TEXT NOT NULL,
                legacy_source_receipt_id TEXT,
                executed_at TEXT NOT NULL,
                authority TEXT NOT NULL
            )"""
        )
        path.con.commit()

        receipt = _apply(path, _plan(path, "BUILD_INDEX"))

        self.assertEqual(receipt.status, "FAILED_RETRYABLE_PHYSICAL_MAINTENANCE")
        self.assertFalse(receipt.persisted)
        self.assertFalse(path.index_exists())
        self.assertEqual(ledger.semantic_state_hash, state_before)
        self.assertEqual(ledger.trace_root_hash, trace_before)

    def test_physical_compare_and_swap_rejects_external_index_change(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        plan = _plan(path, "BUILD_INDEX", actual_index_present=False)
        path._create_index_no_commit()
        path.con.commit()
        self.assertTrue(path.index_exists())
        with self.assertRaises(RankPhysicalStateStale):
            _apply(path, plan)
        self.assertTrue(path.index_exists())
        self.assertEqual(path.maintenance_receipts_v6(), [])

    def test_legacy_v5_receipts_backfill_unknown_without_rewriting_v5(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        path._create_maintenance_log_no_commit()
        legacy_receipt_id = h({"legacy": 1})
        legacy_plan_hash = h({"legacy-plan": 1})
        path.con.execute(
            """INSERT INTO pulse_rank_maintenance_receipts_v5(
                receipt_id,plan_hash,basis_epoch,action,status,
                index_present_before,index_present_after,
                semantic_state_hash_before,semantic_state_hash_after,
                trace_root_hash_before,trace_root_hash_after,executed_at,authority
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                legacy_receipt_id,
                legacy_plan_hash,
                ledger.epoch,
                "DROP_INDEX",
                "DROPPED",
                1,
                0,
                ledger.semantic_state_hash,
                ledger.semantic_state_hash,
                ledger.trace_root_hash,
                ledger.trace_root_hash,
                "2026-08-10T00:00:00Z",
                "PHYSICAL_INDEX_MAINTENANCE_ONLY_NO_SEMANTIC_AUTHORITY",
            ),
        )
        path.con.commit()
        v5_before = path.maintenance_receipts()

        native = _apply(path, _plan(path, "BUILD_INDEX"))

        self.assertEqual(native.status, "BUILT")
        self.assertEqual(path.maintenance_receipts(), v5_before)
        rows = path.maintenance_receipts_v6()
        self.assertEqual(len(rows), 2)
        self.assertEqual([row["audit_sequence"] for row in rows], [1, 2])
        legacy = next(row for row in rows if row["legacy_source_receipt_id"] is not None)
        current = next(row for row in rows if row["legacy_source_receipt_id"] is None)
        self.assertEqual(legacy["legacy_source_receipt_id"], legacy_receipt_id)
        self.assertEqual(legacy["actor"], "UNKNOWN")
        self.assertEqual(legacy["policy_provenance_ref"], "UNKNOWN")
        self.assertEqual(legacy["policy_decision_hash"], "UNKNOWN")
        self.assertEqual(legacy["provenance_status"], LEGACY_PROVENANCE_STATUS)
        self.assertEqual(current["provenance_status"], NATIVE_PROVENANCE_STATUS)
        self.assertNotEqual(current["actor"], "UNKNOWN")

    def test_drop_is_provenance_bound_and_preserves_roots(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        built = _apply(path, _plan(path, "BUILD_INDEX"))
        self.assertEqual(built.status, "BUILT")
        state_before = ledger.semantic_state_hash
        trace_before = ledger.trace_root_hash
        dropped = _apply(path, _plan(path, "DROP_INDEX"))
        self.assertEqual(dropped.status, "DROPPED")
        self.assertFalse(path.index_exists())
        self.assertEqual(ledger.semantic_state_hash, state_before)
        self.assertEqual(ledger.trace_root_hash, trace_before)
        self.assertEqual([r["audit_sequence"] for r in path.maintenance_receipts_v6()], [1, 2])

    def test_identical_build_plan_can_be_audited_after_build_drop_build_cycle(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        build_plan = _plan(path, "BUILD_INDEX")
        first = _apply(path, build_plan)
        self.assertEqual(first.status, "BUILT")
        drop = _apply(path, _plan(path, "DROP_INDEX"))
        self.assertEqual(drop.status, "DROPPED")
        self.assertFalse(path.index_exists())

        second = _apply(path, build_plan)

        self.assertEqual(second.status, "BUILT")
        self.assertTrue(second.persisted)
        self.assertNotEqual(first.receipt_id, second.receipt_id)
        self.assertEqual([first.audit_sequence, drop.audit_sequence, second.audit_sequence], [1, 2, 3])
        rows = path.maintenance_receipts_v6()
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["audit_sequence"] for r in rows], [1, 2, 3])

    def test_none_action_never_creates_audit_schema(self):
        ledger = StateLedger()
        path = AdaptiveAuthoritativeRankPathV6(ledger)
        receipt = _apply(path, _plan(path, "NONE"))
        self.assertEqual(receipt.status, "NO_CHANGE")
        self.assertFalse(receipt.persisted)
        self.assertIsNone(receipt.audit_sequence)
        self.assertFalse(path._v6_log_exists())
        self.assertFalse(path.index_exists())


if __name__ == "__main__":
    unittest.main()
