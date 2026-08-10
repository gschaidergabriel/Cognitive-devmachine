from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger, h
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_rank_path_v5 import RankLifecyclePlan
from research_entity.runtime.database_pulse_rank_path_v6 import AdaptiveAuthoritativeRankPathV6
from research_entity.runtime.database_pulse_rank_path_v6_3_attested import (
    AdaptiveAuthoritativeRankPathV63Attested,
    CANONICAL_INDEX_DEFINITION_HASH,
    CANONICAL_INDEX_SQL,
    sql_definition_hash,
    sql_lexical_tokens,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics() -> CompileEconomics:
    return CompileEconomics(
        build_cost_us=1000.0,
        online_query_us=100.0,
        compiled_query_us=10.0,
        online_quality=1.0,
        compiled_quality=1.0,
        expected_reads_before_invalidation=0.0,
        safety_factor=1.0,
    )


def stable_history() -> list[EpochReadLifetime]:
    return [EpochReadLifetime(i + 1, 200) for i in range(8)]


def sparse_history() -> list[EpochReadLifetime]:
    return [EpochReadLifetime(1, 200), EpochReadLifetime(2, 200)]


def provenance() -> dict[str, str]:
    return {
        "actor": "research-entity:test-worker",
        "policy_provenance_ref": "test://rank-policy/v63",
        "policy_decision_hash": h({"policy": "rank-v63", "decision": "compile"}),
    }


def seeded() -> tuple[StateLedger, AdaptiveAuthoritativeRankPathV63Attested]:
    ledger = StateLedger()
    ops = []
    for i in range(100):
        ops.append(
            {
                "op": "SET",
                "domain": "memory",
                "key": f"k{i:03d}",
                "value": {
                    "priority": i / 100.0,
                    "urgency": ((100 - i) % 79) / 78.0,
                    "salience": (i % 13) / 13.0,
                    "novelty": (i % 7) / 7.0,
                },
                "epistemic": "KNOWN",
                "status": "CURRENT",
            }
        )
    ledger.append_event(
        event_id="seed",
        idem="seed",
        base_epoch=0,
        event_type="SEED",
        writer="test",
        ops=ops,
        committed_at="2026-08-10T05:45:00Z",
    )
    return ledger, AdaptiveAuthoritativeRankPathV63Attested(ledger)


def plan(path: AdaptiveAuthoritativeRankPathV63Attested, history=None):
    return path.plan_lifecycle(
        basis_epoch=path.ledger.epoch,
        economics_without_horizon=economics(),
        pulse_history=history or stable_history(),
        **provenance(),
    )


def select(path: AdaptiveAuthoritativeRankPathV63Attested, history=None):
    return path.select(
        source_domains=("memory",),
        basis_epoch=path.ledger.epoch,
        max_candidates=50,
        max_focus=8,
        economics_without_horizon=economics(),
        pulse_history=history or stable_history(),
        **provenance(),
    )


def parent_plan(path: AdaptiveAuthoritativeRankPathV63Attested, action: str, present: bool):
    return RankLifecyclePlan(
        basis_epoch=path.ledger.epoch,
        semantic_state_hash=path.ledger.semantic_state_hash,
        desired_mode="COMPILED_INDEX" if action == "BUILD_INDEX" else "ONLINE",
        actual_index_present=present,
        maintenance_action=action,
        horizon_status="TEST_FIXED",
        horizon_reads_lower_bound=1000.0,
        compile_reason="TEST_FIXED",
        guarded_break_even_reads=1.0,
        plan_hash=h({"parent-test": action, "present": present, "epoch": path.ledger.epoch}),
    )


class SqlIdentityTests(unittest.TestCase):
    def test_formatting_and_case_do_not_false_drift_but_token_boundaries_do_not_collide(self):
        formatted = " CREATE   INDEX Ix ON T ( A COLLATE BINARY ) WHERE S = 'A B' ; "
        compact = "create index ix on t(a collate binary) where s='A B'"
        collision = "create index ix on t(acollatebinary) where s='A B'"
        literal_change = "create index ix on t(a collate binary) where s='AB'"
        self.assertEqual(sql_lexical_tokens(formatted), sql_lexical_tokens(compact))
        self.assertNotEqual(sql_lexical_tokens(compact), sql_lexical_tokens(collision))
        self.assertNotEqual(sql_definition_hash(compact), sql_definition_hash(literal_change))

    def test_parent_sql_storage_shape_matches_canonical_definition(self):
        ledger, path = seeded()
        AdaptiveAuthoritativeRankPathV6.apply_maintenance(
            path,
            parent_plan(path, "BUILD_INDEX", False),
            **provenance(),
        )
        present, definition_hash, _ = path._raw_index()
        self.assertTrue(present)
        self.assertEqual(definition_hash, CANONICAL_INDEX_DEFINITION_HASH)
        self.assertEqual(sql_definition_hash(CANONICAL_INDEX_SQL), CANONICAL_INDEX_DEFINITION_HASH)
        # It is correct but still unavailable to compiled cognition until explicitly attested.
        self.assertEqual(path.physical_identity().state, "UNATTESTED")
        ledger.close()


class V63AttestationTests(unittest.TestCase):
    def test_absent_build_uses_parent_v6_then_attests(self):
        ledger, path = seeded()
        p = plan(path)
        self.assertEqual(p.maintenance_action, "BUILD_INDEX")
        roots = (ledger.semantic_state_hash, ledger.trace_root_hash)
        receipt = path.apply_maintenance(p)
        self.assertEqual(receipt.status, "ATTESTED")
        self.assertTrue(receipt.persisted)
        self.assertEqual(len(receipt.parent_v6_receipt_ids), 1)
        self.assertIsNotNone(receipt.attestation_receipt_id)
        self.assertEqual(path.physical_identity().state, "ATTESTED")
        self.assertEqual(roots, (ledger.semantic_state_hash, ledger.trace_root_hash))
        result = select(path)
        self.assertEqual(result.physical_read_mode, "COMPILED_ATTESTED_INDEX")
        self.assertTrue(any(INDEX_NAME in line for line in result.query_plan))
        ledger.close()

    def test_parent_built_index_is_online_until_attested_not_definition_drift(self):
        ledger, path = seeded()
        parent = AdaptiveAuthoritativeRankPathV6.apply_maintenance(
            path,
            parent_plan(path, "BUILD_INDEX", False),
            **provenance(),
        )
        self.assertEqual(parent.status, "BUILT")
        self.assertEqual(path.physical_identity().state, "UNATTESTED")
        result = select(path)
        self.assertEqual(result.physical_read_mode, "ONLINE_PENDING_ATTESTATION")
        self.assertFalse(any(INDEX_NAME in line for line in result.query_plan))
        receipt = path.apply_maintenance(plan(path))
        self.assertEqual(receipt.status, "ATTESTED")
        self.assertEqual(path.physical_identity().state, "ATTESTED")
        ledger.close()

    def test_wrong_same_name_definition_never_admitted_and_is_rebuilt(self):
        ledger, path = seeded()
        path.con.execute(f"CREATE INDEX {INDEX_NAME} ON state(domain)")
        path.con.commit()
        self.assertEqual(path.physical_identity().state, "DEFINITION_DRIFT")
        p = plan(path)
        self.assertEqual(p.maintenance_action, "REBUILD_INDEX")
        result = select(path)
        self.assertEqual(result.physical_read_mode, "ONLINE_PENDING_REBUILD")
        self.assertFalse(any(INDEX_NAME in line for line in result.query_plan))
        receipt = path.apply_maintenance(p)
        self.assertEqual(receipt.status, "REBUILT_ATTESTED")
        self.assertEqual(len(receipt.parent_v6_receipt_ids), 2)
        self.assertEqual(path.physical_identity().state, "ATTESTED")
        ledger.close()

    def test_schema_aba_same_definition_is_not_silently_reused(self):
        ledger, path = seeded()
        path.apply_maintenance(plan(path))
        attested = path.physical_identity()
        self.assertEqual(attested.state, "ATTESTED")
        # External physical ABA: same definition, no parent-V6 receipt. SQLite may reuse the same
        # rootpage; schema_version must still revoke the old attestation.
        path.con.execute(f"DROP INDEX {INDEX_NAME}")
        path.con.execute(CANONICAL_INDEX_SQL)
        path.con.commit()
        after = path.physical_identity()
        self.assertEqual(after.definition_hash, CANONICAL_INDEX_DEFINITION_HASH)
        self.assertNotEqual(after.schema_version, attested.schema_version)
        self.assertEqual(after.state, "SCHEMA_DRIFT")
        self.assertEqual(plan(path).maintenance_action, "REBUILD_INDEX")
        self.assertEqual(select(path).physical_read_mode, "ONLINE_PENDING_REBUILD")
        ledger.close()

    def test_parent_drop_then_external_recreate_is_parent_drift_even_if_definition_matches(self):
        ledger, path = seeded()
        path.apply_maintenance(plan(path))
        dropped = AdaptiveAuthoritativeRankPathV6.apply_maintenance(
            path,
            parent_plan(path, "DROP_INDEX", True),
            **provenance(),
        )
        self.assertEqual(dropped.status, "DROPPED")
        path._create_index_no_commit()
        path.con.commit()
        self.assertEqual(path.physical_identity().state, "PARENT_V6_DRIFT")
        self.assertEqual(plan(path).maintenance_action, "REBUILD_INDEX")
        ledger.close()

    def test_runtime_drift_revokes_compiled_use_then_reindexes_and_reattests(self):
        ledger, path = seeded()
        path.apply_maintenance(plan(path))
        original = path._runtime_payload
        fake = dict(original())
        fake["platform_release"] = fake["platform_release"] + "-SIMULATED-DRIFT"
        path._runtime_payload = lambda: fake
        self.assertEqual(path.physical_identity().state, "RUNTIME_DRIFT")
        p = plan(path)
        self.assertEqual(p.maintenance_action, "REFRESH_ATTESTATION")
        self.assertEqual(select(path).physical_read_mode, "ONLINE_PENDING_ATTESTATION")
        receipt = path.apply_maintenance(p)
        self.assertEqual(receipt.status, "ATTESTED")
        self.assertEqual(path.physical_identity().state, "ATTESTED")
        ledger.close()

    def test_attestation_receipt_failure_rolls_back_reindex_and_audit_table(self):
        class Broken(AdaptiveAuthoritativeRankPathV63Attested):
            def _insert_attestation_no_commit(self, values):
                raise RuntimeError("injected-attestation-receipt-failure")

        ledger, _ = seeded()
        path = Broken(ledger)
        parent = AdaptiveAuthoritativeRankPathV6.apply_maintenance(
            path,
            parent_plan(path, "BUILD_INDEX", False),
            **provenance(),
        )
        self.assertEqual(parent.status, "BUILT")
        roots = (ledger.semantic_state_hash, ledger.trace_root_hash)
        receipt = path.apply_maintenance(plan(path))
        self.assertEqual(receipt.status, "UNATTESTED_SAFE_FALLBACK")
        self.assertEqual(receipt.error_class, "RuntimeError")
        self.assertTrue(path.index_exists())
        self.assertEqual(path.physical_identity().state, "UNATTESTED")
        self.assertFalse(path._attestation_table_exists())
        self.assertEqual(roots, (ledger.semantic_state_hash, ledger.trace_root_hash))
        ledger.close()

    def test_online_and_attested_compiled_semantics_are_identical(self):
        ledger, path = seeded()
        online = select(path, sparse_history())
        self.assertEqual(online.physical_read_mode, "ONLINE")
        path.apply_maintenance(plan(path))
        compiled = select(path, stable_history())
        self.assertEqual(online.candidate_refs, compiled.candidate_refs)
        self.assertEqual(online.focus_refs, compiled.focus_refs)
        self.assertEqual(online.candidate_scores, compiled.candidate_scores)
        ledger.close()

    def test_parent_provenance_unknown_remains_rejected_before_effect(self):
        ledger, path = seeded()
        with self.assertRaises(ValueError):
            path.plan_lifecycle(
                basis_epoch=ledger.epoch,
                economics_without_horizon=economics(),
                pulse_history=stable_history(),
                actor="UNKNOWN",
                policy_provenance_ref="test://policy",
                policy_decision_hash="hash",
            )
        self.assertFalse(path.index_exists())
        ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
