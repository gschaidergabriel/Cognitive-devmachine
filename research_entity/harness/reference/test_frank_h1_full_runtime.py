import unittest
from .frank_h1_full_runtime import FrankH1FullRuntime
from .claude_peer_fabric import ClaudeCapability

VIS={'source_id':'cam0','capture_epoch':1,'features':{'shape':'box'},'sensor_confidence':.93,'candidate_label':'cup','prototype_similarity':.9}
OPTS=[{'name':'local','salience':.7}]
CAP=ClaudeCapability('CLAUDE_CODE_A','CAN_NOW',('repo_read','test_run'),ttl_epochs=4)

class FullRuntimeTests(unittest.TestCase):
    def test_full_runtime_without_peer_still_passes(self):
        r=FrankH1FullRuntime(); out=r.run(text='hello',visual=VIS,options=OPTS); self.assertTrue(out['integration_audit']['pass'],out['integration_audit']); self.assertIsNone(out['peer']); self.assertTrue(out['static_claygraph_validation']['pass']); self.assertTrue(out['dynamic_claygraph_validation']['pass']); r.close()
    def test_full_runtime_with_peer_passes_same_organism_audit(self):
        r=FrankH1FullRuntime(); out=r.run(text='hello',visual=VIS,options=OPTS,peer_capability=CAP,peer_semantics={'claim_key':'peer_hint','value':{'fix':'replay'}}); self.assertTrue(out['integration_audit']['pass'],out['integration_audit']); self.assertTrue(out['peer']['peer_selected_by_workspace']); self.assertEqual(out['integration_audit']['peer_authority'],'NONE'); self.assertIn('peer_causal_path',out['dynamic_run_claygraph']); r.close()
    def test_unifieddb_query_and_assembly_are_epoch_bound(self):
        r=FrankH1FullRuntime(); out=r.run(text='hello',visual=VIS,options=OPTS); q=out['unifieddb_query_receipt']; self.assertEqual(q.basis_epoch,r.spine.ledger.epoch); self.assertEqual(q.semantic_state_hash,r.spine.ledger.semantic_state_hash); self.assertEqual(out['active_assembly']['basis_epoch'],q.basis_epoch); r.close()
    def test_capability_view_is_derived(self):
        r=FrankH1FullRuntime(); out=r.run(text='hello',visual=VIS,options=OPTS,peer_capability=CAP,peer_semantics={'claim_key':'peer_hint','value':1}); v=out['capability_view']; self.assertTrue(v['derived']); self.assertFalse(v['persistent_second_store']); self.assertEqual(v['authority'],'NON_AUTHORITATIVE_PROJECTION'); r.close()
    def test_many_full_cycles_replay_exact(self):
        r=FrankH1FullRuntime()
        for i in range(25):
            out=r.run(text=str(i),visual=dict(VIS,capture_epoch=i+1),options=OPTS,mode='thinking' if i%2 else 'instruct',peer_capability=CAP,peer_semantics={'claim_key':f'p{i}','value':{'i':i}})
            self.assertTrue(out['integration_audit']['pass'])
        rec=r.recovery(); self.assertTrue(rec['semantic_state_hash_equal']); self.assertTrue(rec['trace_root_hash_equal']); self.assertTrue(rec['epoch_equal']); self.assertEqual(rec['events'],125); r.close()
if __name__=='__main__': unittest.main()
