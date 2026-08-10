from __future__ import annotations

import random
import tempfile
import unittest

from .state_ledger import StateLedger


class StreamingRootEquivalenceTests(unittest.TestCase):
    def assert_roots_equal(self, ledger: StateLedger):
        self.assertEqual(ledger._roots(), ledger._roots_legacy())
        self.assertEqual(ledger.semantic_state_hash, ledger._roots_legacy()[0])

    def test_empty_ledger_root_is_byte_equivalent(self):
        l=StateLedger(); self.assert_roots_equal(l); l.close()

    def test_nested_unicode_typed_values_are_equivalent(self):
        l=StateLedger()
        values=[
            None, True, False, 0, -7, 1.25, -0.0,
            'Grüße 世界 🧠',
            {'z':3,'a':[1,2,{'nested':'✓'}]},
            {'$kind':'set','items':['β','a','β',3,1]},
            {'$kind':'ordered','items':[{'z':2,'a':1},'x',False]},
        ]
        for i,value in enumerate(values):
            l.append_event(
                event_id=f'e{i}',idem=f'e{i}',base_epoch=l.epoch,event_type='ROOT_EQ',writer='test',
                ops=[{'op':'SET','domain':'δοκιμή' if i%2 else 'semantic','key':f'κ-{i:03d}','value':value,'epistemic':'KNOWN','status':'CURRENT'}],
                provenance={'i':i,'unicode':'源'},source={'fixture':'stream-root'},execution={'mode':'test'},
            )
            self.assert_roots_equal(l)
        l.close()

    def test_status_transitions_and_multidomain_updates_are_equivalent(self):
        l=StateLedger()
        l.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='test',ops=[
            {'op':'SET','domain':'memory','key':'a','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'world','key':'b','value':{'v':2},'epistemic':'UNKNOWN','status':'CURRENT'},
            {'op':'SET','domain':'goal','key':'c','value':{'v':3},'epistemic':'CONFLICT','status':'CURRENT'},
        ])
        self.assert_roots_equal(l)
        transitions=[
            {'op':'SUPERSEDE','domain':'memory','key':'a','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'RETRACT','domain':'world','key':'b','value':None,'epistemic':'REVOKED','status':'CURRENT'},
            {'op':'SET','domain':'goal','key':'c','value':{'v':4},'epistemic':'KNOWN','status':'QUARANTINED'},
        ]
        l.append_event(event_id='transition',idem='transition',base_epoch=l.epoch,event_type='TRANSITION',writer='test',ops=transitions)
        self.assert_roots_equal(l); l.close()

    def test_randomized_event_sequence_preserves_root_after_every_commit(self):
        rnd=random.Random(73419); l=StateLedger()
        domains=('semantic','memory','world','goal','capability')
        for i in range(160):
            d=rnd.choice(domains); k=f'k{rnd.randrange(45):03d}'
            v={'i':i,'n':rnd.randrange(100000),'flag':bool(i%2),'tags':{'$kind':'set','items':[rnd.randrange(7),rnd.randrange(7),rnd.randrange(7)]}}
            l.append_event(event_id=f'r{i}',idem=f'r{i}',base_epoch=l.epoch,event_type='RANDOM',writer='test',ops=[{'op':'SET','domain':d,'key':k,'value':v,'epistemic':rnd.choice(('KNOWN','UNKNOWN','CONFLICT')),'status':'CURRENT'}])
            self.assert_roots_equal(l)
        l.close()

    def test_replay_and_snapshot_keep_historical_contract(self):
        with tempfile.TemporaryDirectory() as td:
            l=StateLedger(f'{td}/a.sqlite')
            for i in range(24):
                l.append_event(event_id=f'e{i}',idem=f'e{i}',base_epoch=l.epoch,event_type='REPLAY',writer='test',ops=[{'op':'SET','domain':f'd{i%4}','key':f'k{i:03d}','value':{'i':i,'s':'µ'},'epistemic':'KNOWN','status':'CURRENT'}])
            self.assert_roots_equal(l)
            events=l.export_events(); snap=l.snapshot('s1'); self.assertTrue(l.verify_snapshot('s1'))
            replayed=StateLedger.replay(events,f'{td}/b.sqlite')
            self.assertEqual(replayed.semantic_state_hash,l.semantic_state_hash)
            self.assertEqual(replayed.trace_root_hash,l.trace_root_hash)
            self.assert_roots_equal(replayed)
            self.assertEqual(snap['semantic_state_hash'],l.semantic_state_hash)
            replayed.close(); l.close()


if __name__=='__main__':
    unittest.main()
