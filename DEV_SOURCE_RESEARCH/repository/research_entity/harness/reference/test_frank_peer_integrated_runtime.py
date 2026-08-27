import unittest
from .frank_peer_integrated_runtime import FrankPeerIntegratedRuntime
from .claude_peer_fabric import ClaudeCapability

VIS={'source_id':'cam0','capture_epoch':1,'features':{'shape':'box'},'sensor_confidence':.9,'candidate_label':'cup','prototype_similarity':.9}
BASE=[{'name':'local_answer','salience':.7}]
CAP=ClaudeCapability('CLAUDE_CODE_A','CAN_NOW',('repo_read','test_run'),ttl_epochs=4)
class IntegratedPeerTests(unittest.TestCase):
    def test_peer_delta_enters_same_ledger_and_gwt(self):
        r=FrankPeerIntegratedRuntime(); out=r.cycle_with_peer(text='prüfe',visual=VIS,base_options=BASE,capability=CAP,result_semantics={'claim_key':'peer_hint','value':{'fix':'use replay'}}); self.assertEqual(out['peer_accept']['status'],'ACCEPTED'); self.assertTrue(out['same_unified_ledger']); self.assertTrue(out['peer_selected_by_workspace']); self.assertTrue(out['cycle']['workspace']['uptake']); self.assertTrue(out['cycle']['workspace']['causal_use']); r.close()
    def test_peer_backflow_is_bounded_not_whole_state(self):
        r=FrankPeerIntegratedRuntime(); out=r.cycle_with_peer(text='prüfe',visual=VIS,base_options=BASE,capability=CAP,result_semantics={'claim_key':'peer_hint','value':{'fix':'x'}},raw_prose='z'*5000); m=out['peer_context_metric']; self.assertLess(m['compact_chars'],m['full_chars']); self.assertGreater(m['saved_chars'],3000); self.assertNotIn('zzzzzzzzzz',str(out['peer_backflow'])); r.close()
    def test_peer_does_not_bypass_effect_gateway(self):
        r=FrankPeerIntegratedRuntime(); out=r.cycle_with_peer(text='prüfe',visual=VIS,base_options=BASE,capability=CAP,result_semantics={'claim_key':'peer_hint','value':{'execute':'delete'}}); self.assertEqual(out['cycle']['proposal']['authority'],'NONE'); self.assertEqual(out['cycle']['effect']['status'],'COMMITTED'); r.close()
if __name__=='__main__': unittest.main()
