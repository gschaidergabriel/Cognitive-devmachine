from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger, h
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_rank_path_v5 import RankLifecyclePlan
from research_entity.runtime.database_pulse_rank_path_v6 import AdaptiveAuthoritativeRankPathV6
from research_entity.runtime.database_pulse_rank_path_v6_1_attested import AdaptiveAuthoritativeRankPathV61Attested
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics():
    return CompileEconomics(build_cost_us=1000.0,online_query_us=100.0,compiled_query_us=10.0,
        online_quality=1.0,compiled_quality=1.0,expected_reads_before_invalidation=0.0,safety_factor=1.0)
def stable():return [EpochReadLifetime(i+1,200) for i in range(8)]
def sparse():return [EpochReadLifetime(1,200),EpochReadLifetime(2,200)]

def seeded():
    l=StateLedger(); ops=[]
    for i in range(100):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:03d}","value":{"priority":i/100.0,
            "urgency":((100-i)%79)/78.0,"salience":(i%13)/13.0,"novelty":(i%7)/7.0},
            "epistemic":"KNOWN","status":"CURRENT"})
    l.append_event(event_id="seed",idem="seed",base_epoch=0,event_type="SEED",writer="test",ops=ops,
        committed_at="2026-08-10T05:30:00Z")
    return l,AdaptiveAuthoritativeRankPathV61Attested(l)

def kwargs():
    return {"actor":"research-entity:test-worker","policy_provenance_ref":"test://rank-policy/v61",
            "policy_decision_hash":h({"policy":"rank-v61","decision":"compile"})}
def plan(v,hist=None):
    return v.plan_lifecycle(basis_epoch=v.ledger.epoch,economics_without_horizon=economics(),pulse_history=hist or stable(),**kwargs())
def select(v,hist=None):
    return v.select(source_domains=("memory",),basis_epoch=v.ledger.epoch,max_candidates=50,max_focus=8,
        economics_without_horizon=economics(),pulse_history=hist or stable(),**kwargs())
def parent_plan(v,action,present):
    return RankLifecyclePlan(basis_epoch=v.ledger.epoch,semantic_state_hash=v.ledger.semantic_state_hash,
        desired_mode="COMPILED_INDEX" if action=="BUILD_INDEX" else "ONLINE",actual_index_present=present,
        maintenance_action=action,horizon_status="TEST",horizon_reads_lower_bound=1000.0,compile_reason="TEST",
        guarded_break_even_reads=1.0,plan_hash=h({"action":action,"present":present,"epoch":v.ledger.epoch}))

class V61AttestedTests(unittest.TestCase):
    def test_build_uses_parent_v6_provenance_then_attests(self):
        l,v=seeded(); p=plan(v); self.assertEqual(p.maintenance_action,"BUILD_INDEX")
        r=v.apply_maintenance(p); self.assertEqual(r.status,"ATTESTED"); self.assertTrue(r.persisted)
        self.assertEqual(len(r.parent_v6_receipt_ids),1); self.assertIsNotNone(r.attestation_receipt_id)
        self.assertEqual(v.physical_identity().state,"ATTESTED")
        rows=v.maintenance_receipts_v6(); self.assertEqual(rows[-1]["actor"],kwargs()["actor"])
        q=select(v); self.assertEqual(q.physical_read_mode,"COMPILED_ATTESTED_INDEX")
        self.assertTrue(any(INDEX_NAME in x for x in q.query_plan)); l.close()

    def test_correct_external_index_is_online_until_reindex_attestation(self):
        l,v=seeded(); v._create_index_no_commit(); v.con.commit()
        self.assertEqual(v.physical_identity().state,"UNATTESTED")
        q=select(v); self.assertEqual(q.physical_read_mode,"ONLINE_PENDING_ATTESTATION")
        self.assertFalse(any(INDEX_NAME in x for x in q.query_plan))
        r=v.apply_maintenance(plan(v)); self.assertEqual(r.status,"ATTESTED")
        self.assertEqual(v.physical_identity().state,"ATTESTED"); l.close()

    def test_wrong_same_name_definition_repairs_via_parent_drop_build(self):
        l,v=seeded(); v.con.execute(f"create index {INDEX_NAME} on state(domain)"); v.con.commit()
        self.assertEqual(v.physical_identity().state,"DEFINITION_DRIFT")
        p=plan(v); self.assertEqual(p.maintenance_action,"REBUILD_INDEX")
        self.assertEqual(select(v).physical_read_mode,"ONLINE_PENDING_REBUILD")
        r=v.apply_maintenance(p); self.assertEqual(r.status,"REBUILT_ATTESTED")
        self.assertEqual(len(r.parent_v6_receipt_ids),2); self.assertEqual(v.physical_identity().state,"ATTESTED"); l.close()

    def test_runtime_drift_revokes_compiled_use_and_refreshes(self):
        l,v=seeded(); v.apply_maintenance(plan(v)); original=v._runtime_payload; fake=dict(original()); fake["platform_release"]+="-DRIFT"
        v._runtime_payload=lambda:fake
        self.assertEqual(v.physical_identity().state,"RUNTIME_DRIFT")
        self.assertEqual(select(v).physical_read_mode,"ONLINE_PENDING_ATTESTATION")
        r=v.apply_maintenance(plan(v)); self.assertEqual(r.status,"ATTESTED"); l.close()

    def test_attestation_insert_failure_rolls_back_refresh_not_semantic_state(self):
        class Broken(AdaptiveAuthoritativeRankPathV61Attested):
            def _insert_attestation_no_commit(self,values):raise RuntimeError("injected")
        l,_=seeded(); v=Broken(l); v._create_index_no_commit(); v.con.commit(); roots=(l.semantic_state_hash,l.trace_root_hash)
        with self.assertRaises(RuntimeError):v.apply_maintenance(plan(v))
        self.assertTrue(v.index_exists()); self.assertEqual(v.physical_identity().state,"UNATTESTED")
        self.assertFalse(v._attestation_table_exists()); self.assertEqual(roots,(l.semantic_state_hash,l.trace_root_hash)); l.close()

    def test_parent_v6_drop_then_external_recreate_forces_rebuild(self):
        l,v=seeded(); v.apply_maintenance(plan(v)); self.assertEqual(v.physical_identity().state,"ATTESTED")
        parent=AdaptiveAuthoritativeRankPathV6.apply_maintenance(v,parent_plan(v,"DROP_INDEX",True),**kwargs())
        self.assertEqual(parent.status,"DROPPED")
        v._create_index_no_commit(); v.con.commit()
        self.assertEqual(v.physical_identity().state,"PARENT_V6_DRIFT")
        self.assertEqual(plan(v).maintenance_action,"REBUILD_INDEX")
        self.assertEqual(select(v).physical_read_mode,"ONLINE_PENDING_REBUILD"); l.close()

    def test_online_and_attested_compiled_semantics_equal(self):
        l,v=seeded(); online=select(v,sparse()); v.apply_maintenance(plan(v)); compiled=select(v,stable())
        self.assertEqual(online.candidate_refs,compiled.candidate_refs)
        self.assertEqual(online.focus_refs,compiled.focus_refs)
        self.assertEqual(online.candidate_scores,compiled.candidate_scores); l.close()

    def test_parent_provenance_gate_is_reused_not_weakened(self):
        l,v=seeded()
        with self.assertRaises(ValueError):
            v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable(),
                actor="UNKNOWN",policy_provenance_ref="test://p",policy_decision_hash="h")
        self.assertFalse(v.index_exists()); l.close()

if __name__=="__main__":unittest.main(verbosity=2)
