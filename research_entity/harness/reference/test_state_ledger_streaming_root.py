import random
import unittest

from .state_ledger import StateLedger

class StreamingSemanticRootTests(unittest.TestCase):
    def assert_roots_equal(self,ledger):
        self.assertEqual(ledger._roots(),ledger._roots_legacy())
        self.assertEqual(ledger.semantic_state_hash,ledger._roots_legacy()[0])

    def test_genesis_root_is_byte_equivalent(self):
        l=StateLedger(); self.assert_roots_equal(l); l.close()

    def test_unicode_nested_typed_collections_and_statuses_remain_equivalent(self):
        l=StateLedger()
        values=[
            {'text':'ä✓\n"','n':1,'f':1.25,'nil':None,'b':True},
            {'set':{'$kind':'set','items':[3,1,3,2]},'ordered':{'$kind':'ordered','items':['β','α']}},
            {'nested':[{'z':2,'a':1},[False,None,3.5]]},
        ]
        for i,v in enumerate(values):
            l.append_event(event_id=f'e{i}',idem=f'e{i}',base_epoch=l.epoch,event_type='TEST',writer='t',ops=[{'op':'SET','domain':'semäntic','key':f'k{i}✓','value':v,'epistemic':('KNOWN','UNKNOWN','CONFLICT')[i],'status':'CURRENT'}])
            self.assert_roots_equal(l)
        l.append_event(event_id='retract',idem='retract',base_epoch=l.epoch,event_type='TEST',writer='t',ops=[{'op':'RETRACT','domain':'semäntic','key':'k1✓','value':None,'epistemic':'REVOKED'}])
        self.assert_roots_equal(l); l.close()

    def test_random_event_sequence_matches_legacy_after_every_commit(self):
        l=StateLedger(); rng=random.Random(731)
        for i in range(80):
            key=f'k{rng.randrange(17):02d}'
            op='SET' if i%9 else 'SUPERSEDE'
            l.append_event(event_id=f'r{i}',idem=f'r{i}',base_epoch=l.epoch,event_type='RANDOM',writer='t',ops=[{'op':op,'domain':f'd{rng.randrange(4)}','key':key,'value':{'i':i,'u':'λ','x':[rng.randrange(9),i/10]},'epistemic':('KNOWN','UNKNOWN','CONFLICT')[i%3],'status':'CURRENT'}])
            self.assert_roots_equal(l)
        l.close()

    def test_replay_and_snapshot_preserve_existing_root_contract(self):
        l=StateLedger()
        for i in range(12):
            l.append_event(event_id=f'p{i}',idem=f'p{i}',base_epoch=l.epoch,event_type='REPLAY',writer='t',ops=[{'op':'SET','domain':'memory','key':f'm{i}','value':{'i':i,'set':{'$kind':'set','items':[i%3,2,1]}},'epistemic':'KNOWN','status':'CURRENT'}])
        self.assert_roots_equal(l); events=l.export_events(); snap=l.snapshot('s1'); self.assertTrue(l.verify_snapshot('s1'))
        r=StateLedger.replay(events); self.assert_roots_equal(r); self.assertEqual(r.semantic_state_hash,l.semantic_state_hash); self.assertEqual(r.trace_root_hash,l.trace_root_hash); self.assertEqual(r.epoch,snap['epoch'])
        r.close(); l.close()

if __name__=='__main__': unittest.main()
