from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_runtime_v4 import PulseRankPolicyV4
from research_entity.runtime.database_pulse_runtime_v5 import DatabasePulseRuntimeV5
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def policy(reads=200,n=8):
    return PulseRankPolicyV4(
        economics_without_horizon=CompileEconomics(
            build_cost_us=1000.0,online_query_us=100.0,compiled_query_us=10.0,
            online_quality=1.0,compiled_quality=1.0,expected_reads_before_invalidation=0.0,safety_factor=1.0),
        pulse_history=tuple(EpochReadLifetime(i+1,reads) for i in range(n)),
        provenance_ref=f"test:reads-{reads}:n-{n}")


def seed(path=":memory:",provider=None):
    l=StateLedger(path)
    ops=[]
    for i in range(80):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:03d}","value":{"priority":i/100.0},
                    "epistemic":"KNOWN","status":"CURRENT"})
    ops.append({"op":"SET","domain":"memory","key":"critical","value":{"priority":1.0,"urgency":1.0},
                "epistemic":"KNOWN","status":"CURRENT"})
    l.append_event(event_id="seed",idem="seed",base_epoch=0,event_type="SEED",writer="test",ops=ops,
                   committed_at="2026-08-10T02:20:00Z")
    r=DatabasePulseRuntimeV5(l,rank_policy_provider=provider)
    r.set_scheduler(enabled=True,event_id="on",base_epoch=l.epoch,actor="test",reason="test",
                    committed_at="2026-08-10T02:20:01Z")
    return l,r


class DatabasePulseRuntimeV5Tests(unittest.TestCase):
    def test_stable_policy_pulse_recommends_build_but_does_not_build(self):
        l,r=seed(provider=lambda spec:policy())
        self.assertFalse(r.rank_path.index_exists())
        out=r.run_pulse(PulseSpec("p1",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=32,max_focus=1),
                        committed_at="2026-08-10T02:20:02Z")
        self.assertEqual(out.focus_refs,("memory:critical",))
        latest=l.get("pulse","latest")["value"]
        self.assertEqual(latest["physical_rank_mode"],"ONLINE_PENDING_COMPILE")
        self.assertEqual(latest["rank_maintenance_recommendation"],"BUILD_INDEX")
        self.assertEqual(latest["rank_lifecycle_plan_reapply_after_commit"],"REPLAN_REQUIRED_AT_NEW_EPOCH")
        self.assertFalse(r.rank_path.index_exists())
        self.assertEqual(out.state_transition_count,0)
        l.close()

    def test_between_pulse_maintenance_replans_current_epoch_then_next_pulse_uses_index(self):
        p=policy();l,r=seed(provider=lambda spec:p)
        first=r.run_pulse(PulseSpec("p1",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=32,max_focus=1),
                          committed_at="2026-08-10T02:20:02Z")
        m=r.maintain_rank_index(basis_epoch=l.epoch,policy=p,actor="clay-maintenance-test")
        self.assertEqual(m.receipt.status,"BUILT");self.assertTrue(r.rank_path.index_exists())
        second=r.run_pulse(PulseSpec("p2",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=32,max_focus=1),
                           committed_at="2026-08-10T02:20:03Z")
        self.assertEqual(first.focus_refs,second.focus_refs)
        self.assertEqual(l.get("pulse","latest")["value"]["physical_rank_mode"],"COMPILED_INDEX")
        l.close()

    def test_pre_pulse_maintenance_plan_cannot_be_applied_after_pulse_epoch_change(self):
        p=policy();l,r=seed(provider=lambda spec:p)
        stale_plan=r.rank_path.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=p.economics_without_horizon,
                                              pulse_history=p.pulse_history)
        r.run_pulse(PulseSpec("p1",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=32,max_focus=1),
                    committed_at="2026-08-10T02:20:02Z")
        with self.assertRaises(StaleEpoch):r.rank_path.apply_maintenance(stale_plan)
        self.assertFalse(r.rank_path.index_exists())
        l.close()

    def test_churn_policy_returns_online_immediately_then_drop_between_pulses(self):
        longp=policy();shortp=policy(reads=2,n=2);current=[longp]
        l,r=seed(provider=lambda spec:current[0])
        r.maintain_rank_index(basis_epoch=l.epoch,policy=longp,actor="test")
        self.assertTrue(r.rank_path.index_exists())
        current[0]=shortp
        out=r.run_pulse(PulseSpec("churn",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=32,max_focus=1),
                        committed_at="2026-08-10T02:20:02Z")
        latest=l.get("pulse","latest")["value"]
        self.assertEqual(latest["physical_rank_mode"],"ONLINE_PENDING_DECOMPILE")
        self.assertEqual(latest["rank_maintenance_recommendation"],"DROP_INDEX")
        self.assertTrue(r.rank_path.index_exists())
        m=r.maintain_rank_index(basis_epoch=l.epoch,policy=shortp,actor="test")
        self.assertEqual(m.receipt.status,"DROPPED");self.assertFalse(r.rank_path.index_exists())
        self.assertEqual(out.effect_count,0)
        l.close()

    def test_pause_never_runs_policy_or_maintenance(self):
        calls=[]
        def provider(spec):calls.append(spec.pulse_id);return policy()
        l,r=seed(provider=provider)
        r.set_scheduler(enabled=False,event_id="off",base_epoch=l.epoch,actor="test",reason="pause",
                        committed_at="2026-08-10T02:20:02Z")
        e=l.epoch;out=r.run_pulse(PulseSpec("paused",basis_epoch=e,source_domains=("memory",)))
        self.assertEqual(out.status,"PAUSED");self.assertEqual(calls,[]);self.assertEqual(l.epoch,e)
        self.assertFalse(r.rank_path.index_exists());l.close()

    def test_model_output_remains_unknown_without_effect_or_transition(self):
        l,r=seed()
        out=r.run_pulse(PulseSpec("model",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=16,max_focus=2),
                        model_assistant=lambda ctx:{"proposal":"candidate"},committed_at="2026-08-10T02:20:02Z")
        self.assertEqual((out.model_call_count,out.hypothesis_count,out.state_transition_count,out.effect_count),(1,1,0,0))
        self.assertEqual(l.get("pulse","model_candidate")["epistemic"],"UNKNOWN")
        l.close()

    def test_pause_resume_process_reopen_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"pulse.sqlite";l,r=seed(path)
            r.set_scheduler(enabled=False,event_id="off",base_epoch=l.epoch,actor="test",reason="pause",
                            committed_at="2026-08-10T02:20:02Z");e=l.epoch;l.close()
            l2=StateLedger(path);r2=DatabasePulseRuntimeV5(l2)
            self.assertEqual(r2.run_pulse(PulseSpec("paused",basis_epoch=l2.epoch,source_domains=("memory",))).status,"PAUSED")
            self.assertEqual(l2.epoch,e)
            r2.set_scheduler(enabled=True,event_id="on2",base_epoch=l2.epoch,actor="test",reason="resume",
                             committed_at="2026-08-10T02:20:03Z")
            self.assertEqual(r2.run_pulse(PulseSpec("resume",basis_epoch=l2.epoch,source_domains=("memory",),max_candidates=16,max_focus=1),
                                         committed_at="2026-08-10T02:20:04Z").status,"COMMITTED")
            l2.close()

    def test_output_domains_rejected(self):
        l,r=seed()
        with self.assertRaises(ValueError):r.run_pulse(PulseSpec("bad",basis_epoch=l.epoch,source_domains=("pulse",)))
        l.close()

if __name__=="__main__":unittest.main(verbosity=2)
