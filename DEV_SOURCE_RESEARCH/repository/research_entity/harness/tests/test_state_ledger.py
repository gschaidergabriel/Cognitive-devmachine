import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference'))
from state_ledger import StateLedger, StaleEpoch, IdempotencyConflict, InvalidOperation, h

class T(unittest.TestCase):
    def event(self,**kw):
        x=dict(event_id='e1',idem='k1',base_epoch=0,event_type='STATE',writer='test',ops=[{'op':'SET','domain':'world','key':'door','value':{'open':False}}],provenance={'p':'fixture'},source={'baseline':'A'},execution={'runtime':'A'},committed_at='2026-08-09T10:00:00Z'); x.update(kw); return x
    def test_dict_order(self): self.assertEqual(h({'b':2,'a':1}),h({'a':1,'b':2}))
    def test_list_order(self): self.assertNotEqual(h([1,2]),h([2,1]))
    def test_typed_set(self): self.assertEqual(h({'$kind':'set','items':[3,1,1,2]}),h({'$kind':'set','items':[2,3,1]}))
    def test_typed_ordered(self): self.assertNotEqual(h({'$kind':'ordered','items':[1,2]}),h({'$kind':'ordered','items':[2,1]}))
    def test_commit_epochs(self):
        l=StateLedger(); r=l.append_event(**self.event()); self.assertEqual(r['epoch'],1); self.assertEqual(l.domain_epochs(),{'world':1}); self.assertEqual(l.get('world','door')['value'],{'open':False}); l.close()
    def test_stale_fail_closed(self):
        l=StateLedger(); l.append_event(**self.event()); root=l.semantic_state_hash
        with self.assertRaises(StaleEpoch): l.append_event(event_id='e2',idem='k2',base_epoch=0,event_type='X',writer='x',ops=[{'op':'SET','domain':'world','key':'door','value':{'open':True}}])
        self.assertEqual(root,l.semantic_state_hash); l.close()
    def test_idempotency(self):
        l=StateLedger(); a=l.append_event(**self.event()); b=l.append_event(**self.event()); self.assertEqual(b['status'],'ALREADY_COMMITTED'); self.assertEqual(a['semantic_state_hash'],b['semantic_state_hash'])
        bad=self.event(ops=[{'op':'SET','domain':'world','key':'door','value':{'open':True}}])
        with self.assertRaises(IdempotencyConflict): l.append_event(**bad)
        l.close()
    def test_epistemic(self):
        l=StateLedger(); l.append_event(event_id='e',idem='e',base_epoch=0,event_type='E',writer='t',ops=[{'op':'SET','domain':'m','key':'u','value':None,'epistemic':'UNKNOWN'},{'op':'SET','domain':'m','key':'c','value':[1,2],'epistemic':'CONFLICT'},{'op':'SET','domain':'a','key':'x','value':None,'epistemic':'REVOKED'}]); self.assertEqual(l.get('m','u')['epistemic'],'UNKNOWN'); self.assertEqual(l.get('m','c')['epistemic'],'CONFLICT'); self.assertEqual(l.get('a','x')['epistemic'],'REVOKED'); l.close()
    def test_atomic_invalid(self):
        l=StateLedger(); root=l.semantic_state_hash
        with self.assertRaises(InvalidOperation): l.append_event(event_id='bad',idem='bad',base_epoch=0,event_type='BAD',writer='t',ops=[{'op':'SET','domain':'w','key':'a','value':1},{'op':'EXECUTE','domain':'effect','key':'b','value':2}])
        self.assertEqual(l.epoch,0); self.assertEqual(root,l.semantic_state_hash); self.assertIsNone(l.get('w','a')); l.close()
    def test_execution_separation(self):
        a=StateLedger(); b=StateLedger(); ra=a.append_event(**self.event(execution={'token':'A'})); rb=b.append_event(**self.event(execution={'token':'B'})); self.assertEqual(ra['semantic_state_hash'],rb['semantic_state_hash']); self.assertNotEqual(ra['trace_root_hash'],rb['trace_root_hash']); a.close(); b.close()
    def test_source_separation(self):
        a=StateLedger(); b=StateLedger(); ra=a.append_event(**self.event(source={'baseline':'A'})); rb=b.append_event(**self.event(source={'baseline':'B'})); self.assertEqual(ra['semantic_state_hash'],rb['semantic_state_hash']); self.assertNotEqual(ra['trace_root_hash'],rb['trace_root_hash']); a.close(); b.close()
    def test_loop_order(self):
        a=StateLedger(); b=StateLedger(); vals=[{'delta':.9,'pressure':.8},{'delta':.2,'pressure':.1}]
        common=dict(event_id='l',idem='l',base_epoch=0,event_type='LOOP',writer='t')
        ra=a.append_event(**common,ops=[{'op':'SET','domain':'loop','key':'L','value':{'samples':{'$kind':'ordered','items':vals}}}]); rb=b.append_event(**common,ops=[{'op':'SET','domain':'loop','key':'L','value':{'samples':{'$kind':'ordered','items':list(reversed(vals))}}}]); self.assertNotEqual(ra['semantic_state_hash'],rb['semantic_state_hash']); a.close(); b.close()
    def test_replay_roots(self):
        l=StateLedger(); l.append_event(**self.event()); l.append_event(event_id='e2',idem='k2',base_epoch=1,event_type='GWT',writer='t',ops=[{'op':'SET','domain':'gwt','key':'r','value':{'delivered':True,'used':False}}],source={'baseline':'A'},execution={'runtime':'A'}); r=StateLedger.replay(l.export_events()); self.assertEqual(l.semantic_state_hash,r.semantic_state_hash); self.assertEqual(l.trace_root_hash,r.trace_root_hash); self.assertEqual(l.domain_epochs(),r.domain_epochs()); l.close(); r.close()
    def test_snapshot_tamper(self):
        l=StateLedger(); l.append_event(**self.event()); l.snapshot('s'); self.assertTrue(l.verify_snapshot('s')); l.conn.execute("UPDATE snapshots SET state_json='[]' WHERE id='s'"); l.conn.commit(); self.assertFalse(l.verify_snapshot('s')); l.close()
    def test_persistent_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p=os.path.join(td,'l.db'); a=StateLedger(p); a.append_event(**self.event()); root=a.semantic_state_hash; a.close(); b=StateLedger(p); self.assertEqual(b.epoch,1); self.assertEqual(b.semantic_state_hash,root); b.close()
if __name__=='__main__': unittest.main(verbosity=2)
