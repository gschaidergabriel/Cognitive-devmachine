import os, tempfile, unittest
from pathlib import Path
from .state_ledger import StateLedger
from .effect_gateway_runtime import SandboxEffectGateway, SandboxWriteProposal, EffectDenied, InjectedCrash

class EffectRuntimeTests(unittest.TestCase):
    def make(self):
        td=tempfile.TemporaryDirectory(); l=StateLedger(); g=SandboxEffectGateway(l,td.name); return td,l,g
    def test_successful_atomic_write_has_verified_outcome(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','hello'); q=g.issue_permit(p); o=g.execute(p,q); self.assertEqual(o['status'],'COMMITTED_VERIFIED'); self.assertEqual(Path(td.name,'a.txt').read_text(),'hello'); self.assertEqual(l.get('effect','e1')['value']['status'],'COMMITTED_VERIFIED'); l.close(); td.cleanup()
    def test_missing_permit_denied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','x');
        with self.assertRaises(EffectDenied): g.execute(p,None)
        self.assertFalse(Path(td.name,'a.txt').exists()); l.close(); td.cleanup()
    def test_model_authority_claim_denied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','x',authority='EXECUTE'); q=g.issue_permit(p)
        with self.assertRaises(EffectDenied): g.execute(p,q)
        l.close(); td.cleanup()
    def test_tampered_proposal_after_permit_denied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','x'); q=g.issue_permit(p); t=SandboxWriteProposal('e1','a.txt','changed')
        with self.assertRaises(EffectDenied): g.execute(t,q)
        l.close(); td.cleanup()
    def test_stale_epoch_permit_denied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','x'); q=g.issue_permit(p); l.append_event(event_id='advance',idem='advance',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'x','value':1,'epistemic':'KNOWN','status':'CURRENT'}])
        with self.assertRaises(EffectDenied): g.execute(p,q)
        l.close(); td.cleanup()
    def test_scope_escape_denied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','../escape.txt','x'); q=g.issue_permit(p)
        with self.assertRaises(EffectDenied): g.execute(p,q)
        l.close(); td.cleanup()
    def test_size_budget_enforced(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','x'*20); q=g.issue_permit(p,max_bytes=5)
        with self.assertRaises(EffectDenied): g.execute(p,q)
        l.close(); td.cleanup()
    def test_crash_after_intent_recovers_not_applied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','x'); q=g.issue_permit(p)
        with self.assertRaises(InjectedCrash): g.execute(p,q,crash_at='after_intent')
        r=g.recover_pending('e1'); self.assertEqual(r['status'],'RECOVERED_NOT_APPLIED'); self.assertFalse(Path(td.name,'a.txt').exists()); l.close(); td.cleanup()
    def test_crash_after_temp_fsync_leaves_target_unchanged_and_recovers(self):
        td,l,g=self.make(); Path(td.name,'a.txt').write_text('old'); p=SandboxWriteProposal('e1','a.txt','new'); q=g.issue_permit(p)
        with self.assertRaises(InjectedCrash): g.execute(p,q,crash_at='after_temp_fsync')
        self.assertEqual(Path(td.name,'a.txt').read_text(),'old'); r=g.recover_pending('e1'); self.assertEqual(r['status'],'RECOVERED_NOT_APPLIED'); l.close(); td.cleanup()
    def test_crash_after_replace_is_recovered_as_committed(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','new'); q=g.issue_permit(p)
        with self.assertRaises(InjectedCrash): g.execute(p,q,crash_at='after_replace')
        self.assertEqual(Path(td.name,'a.txt').read_text(),'new'); r=g.recover_pending('e1'); self.assertEqual(r['status'],'RECOVERED_COMMITTED_VERIFIED'); self.assertEqual(l.get('effect','e1')['value']['status'],'RECOVERED_COMMITTED_VERIFIED'); l.close(); td.cleanup()
    def test_recovery_detects_external_conflict(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','new'); q=g.issue_permit(p)
        with self.assertRaises(InjectedCrash): g.execute(p,q,crash_at='after_intent')
        Path(td.name,'a.txt').write_text('other'); r=g.recover_pending('e1'); self.assertEqual(r['status'],'RECOVERY_CONFLICT'); l.close(); td.cleanup()
    def test_recover_verified_is_idempotent(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','new'); q=g.issue_permit(p); g.execute(p,q); r=g.recover_pending('e1'); self.assertEqual(r['status'],'ALREADY_VERIFIED'); l.close(); td.cleanup()
    def test_execute_retry_is_exactly_once(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','new'); q=g.issue_permit(p); g.execute(p,q); epoch=l.epoch; q2=g.issue_permit(p); r=g.execute(p,q2); self.assertEqual(r['status'],'ALREADY_COMMITTED'); self.assertTrue(r['idempotent_replay']); self.assertEqual(l.epoch,epoch); self.assertEqual(Path(td.name,'a.txt').read_text(),'new'); l.close(); td.cleanup()
    def test_effect_id_reuse_with_different_proposal_denied(self):
        td,l,g=self.make(); p=SandboxWriteProposal('e1','a.txt','one'); q=g.issue_permit(p); g.execute(p,q); p2=SandboxWriteProposal('e1','a.txt','two'); q2=g.issue_permit(p2)
        with self.assertRaises(EffectDenied): g.execute(p2,q2)
        self.assertEqual(Path(td.name,'a.txt').read_text(),'one'); l.close(); td.cleanup()
    def test_semantic_effect_state_is_independent_of_absolute_sandbox_root(self):
        states=[]; traces=[]
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                l=StateLedger(); g=SandboxEffectGateway(l,td); p=SandboxWriteProposal('e1','nested/a.txt','same'); g.execute(p,g.issue_permit(p)); states.append(l.semantic_state_hash); traces.append(l.trace_root_hash); self.assertNotIn(str(Path(td).resolve()),str(l.get('effect','e1')['value'])); l.close()
        self.assertEqual(states[0],states[1]); self.assertEqual(traces[0],traces[1])
if __name__=='__main__': unittest.main()
