import unittest
from .state_ledger import StateLedger
from .claude_peer_fabric import ClaudeCapability, ClaudeCodePeerResult, ClaudePeerFabric, PeerFabricError

CAP=ClaudeCapability('CLAUDE_CODE_A','CAN_NOW',('repo_read','code_edit','test_run'),ttl_epochs=3)
def result(req,**kw):
    d=dict(request_id=req.request_id,responder_instance='CLAUDE_CODE_A',status='COMPLETE',result_semantics={'claim_key':'peer_claim','value':{'answer':42}},evidence_refs=('ev:1',),artifact_refs=('file:a',),execution_receipts=(),unresolved=(),capability_observations=('repo_read',),local_effects_claimed=(),basis_epoch=req.basis_epoch,provenance='claude-code-fixture',raw_prose='long '+('x'*1500)); d.update(kw); return ClaudeCodePeerResult(**d)
class PeerTests(unittest.TestCase):
    def make(self): l=StateLedger(); f=ClaudePeerFabric(l); f.observe(CAP); return l,f
    def test_01_visible_when_fresh(self):
        l,f=self.make(); self.assertTrue(f.tool_view()['visible']); self.assertIn('repo_read',f.tool_view()['capabilities']); l.close()
    def test_02_absent_when_unavailable_or_stale(self):
        l=StateLedger(); f=ClaudePeerFabric(l); f.observe(ClaudeCapability('C','UNAVAILABLE',(),ttl_epochs=1)); self.assertFalse(f.tool_view()['visible']); f.observe(CAP); l.append_event(event_id='a',idem='a',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'a','value':1,'epistemic':'KNOWN','status':'CURRENT'}]); l.append_event(event_id='b',idem='b',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'b','value':1,'epistemic':'KNOWN','status':'CURRENT'}]); l.append_event(event_id='c',idem='c',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'c','value':1,'epistemic':'KNOWN','status':'CURRENT'}]); l.append_event(event_id='d',idem='d',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'d','value':1,'epistemic':'KNOWN','status':'CURRENT'}]); self.assertEqual(f.tool_view()['state'],'STALE'); self.assertFalse(f.tool_view()['visible']); l.close()
    def test_03_request_result_correlation(self):
        l,f=self.make(); q=f.request(request_id='q1',goal='fix',task='inspect',required_capabilities=('repo_read',)); x=f.accept(result(q)); self.assertEqual(x['status'],'ACCEPTED'); self.assertEqual(l.get('peer','claude_code_peer:q1')['value']['request_id'],'q1'); l.close()
    def test_04_provenance_preserved(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); f.accept(result(q)); self.assertEqual(l.get('peer','claude_code_peer:q')['value']['provenance'],'claude-code-fixture'); l.close()
    def test_05_opinion_cannot_masquerade_as_execution(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); r=result(q,local_effects_claimed=('effect:delete',)); x=f.accept(r); self.assertIn('effect:delete',x['unsupported_local_effect_claims']); self.assertEqual(x['verified_execution_receipts'],[]); l.close()
    def test_06_verified_execution_receipt_is_scoped(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); rec={'status':'VERIFIED','effect_id':'effect:test','scope':'sandbox:file:a'}; x=f.accept(result(q,execution_receipts=(rec,),local_effects_claimed=('effect:test',))); self.assertEqual(x['verified_execution_receipts'][0]['scope'],'sandbox:file:a'); self.assertEqual(x['unsupported_local_effect_claims'],[]); l.close()
    def test_07_stale_basis_rejected_before_writeback(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); l.append_event(event_id='advance',idem='advance',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'x','value':1,'epistemic':'KNOWN','status':'CURRENT'}]); self.assertEqual(f.accept(result(q))['status'],'STALE_BASIS_REPLAN'); self.assertIsNone(l.get('peer','claude_code_peer:q')); l.close()
    def test_08_disconnect_reconnect(self):
        l,f=self.make(); f.observe(ClaudeCapability('C','UNAVAILABLE',(),ttl_epochs=2)); self.assertFalse(f.tool_view()['visible']); f.observe(CAP); self.assertTrue(f.tool_view()['visible']); l.close()
    def test_09_duplicate_and_out_of_order(self):
        l,f=self.make(); ghost=ClaudeCodePeerResult('ghost','C','COMPLETE',{},(),(),(),(),(),(),l.epoch,'x'); self.assertEqual(f.accept(ghost)['status'],'REJECTED_UNKNOWN_OR_OUT_OF_ORDER_REQUEST'); q=f.request(request_id='q',goal='g',task='t'); r=result(q); self.assertEqual(f.accept(r)['status'],'ACCEPTED'); self.assertEqual(f.accept(r)['status'],'DUPLICATE_IGNORED'); l.close()
    def test_10_conflict_is_preserved_not_overwritten(self):
        l,f=self.make(); l.append_event(event_id='local',idem='local',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'truth','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'}]); f.observe(CAP); q=f.request(request_id='q',goal='g',task='t'); r=result(q,result_semantics={'claim_key':'truth','value':{'v':2}}); self.assertEqual(f.accept(r)['status'],'ACCEPTED_CONFLICT'); self.assertEqual(l.get('semantic','truth')['value'],{'v':1}); self.assertEqual(l.get('peer','claude_code_peer:q')['epistemic'],'CONFLICT'); l.close()
    def test_11_typed_writeback_can_feed_later_assembly(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); f.accept(result(q)); b=f.compact_backflow('q'); self.assertEqual(b['semantics']['value']['answer'],42); self.assertEqual(b['authority'],'NONE'); l.close()
    def test_12_full_prose_not_mirrored(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); r=result(q); f.accept(r); v=l.get('peer','claude_code_peer:q')['value']; self.assertFalse(v['raw_prose_mirrored']); self.assertNotIn(r.raw_prose,str(v)); self.assertLess(len(str(f.compact_backflow('q'))),len(r.raw_prose)); l.close()
    def test_13_lesion_and_rescue(self):
        l,f=self.make(); f.lesion(); self.assertFalse(f.tool_view()['visible']); f.rescue(); self.assertTrue(f.tool_view()['visible']); l.close()
    def test_14_context_cost_with_and_without_compaction(self):
        l,f=self.make(); q=f.request(request_id='q',goal='g',task='t'); r=result(q); f.accept(r); m=f.context_cost(r,'q'); self.assertGreater(m['saved_chars'],0); self.assertLess(m['compression_ratio'],1); l.close()
    def test_required_capability_enforced(self):
        l,f=self.make();
        with self.assertRaises(PeerFabricError): f.request(request_id='q',goal='g',task='t',required_capabilities=('root_shell',))
        l.close()
if __name__=='__main__': unittest.main()
