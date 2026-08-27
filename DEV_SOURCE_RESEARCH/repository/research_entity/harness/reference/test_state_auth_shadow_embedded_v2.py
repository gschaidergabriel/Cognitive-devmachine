import unittest

from .state_auth_shadow_embedded_v2 import EmbeddedAuthenticatedStateShadowV2
from .state_ledger import StateLedger


class EmbeddedAuthShadowV2Tests(unittest.TestCase):
    def seed(self):
        ledger=StateLedger()
        ledger.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='t',ops=[
            {'op':'SET','domain':'memory','key':'alpha','value':{'v':1,'u':'ä✓'},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'memory','key':'beta','value':{'$kind':'set','items':[3,1,3,2]},'epistemic':'UNKNOWN','status':'CURRENT'},
            {'op':'SET','domain':'goal','key':'g1','value':{'priority':0.8},'epistemic':'KNOWN','status':'CURRENT'},
        ])
        return ledger

    def test_install_and_rebuild_do_not_change_canonical_semantic_hash(self):
        ledger=self.seed(); before=ledger.semantic_state_hash; shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0')
        self.assertEqual(ledger.semantic_state_hash,before)
        self.assertEqual(ledger._roots()[0],before)
        self.assertTrue(shadow.verify_full().passed)
        ledger.close()

    def test_normal_ledger_write_survives_added_physical_columns(self):
        ledger=self.seed(); shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0')
        receipt=ledger.append_event(event_id='u',idem='u',base_epoch=ledger.epoch,event_type='UPDATE',writer='t',ops=[{'op':'SET','domain':'memory','key':'alpha','value':{'v':2},'epistemic':'KNOWN','status':'CURRENT'}])
        self.assertEqual(receipt['status'],'COMMITTED')
        out=shadow.refresh(now='t1')
        self.assertEqual(out['mode'],'DELTA_REFRESH')
        self.assertEqual(out['touched_refs'],1)
        self.assertTrue(shadow.verify_full().passed)
        ledger.close()

    def test_shadow_physical_metadata_is_excluded_from_canonical_root(self):
        ledger=self.seed(); shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0'); canonical=ledger._roots()[0]
        ledger.conn.execute("UPDATE state SET auth_leaf_hash=? WHERE domain='memory' AND k='alpha'",(b'bad',)); ledger.conn.commit()
        self.assertEqual(ledger._roots()[0],canonical)
        self.assertFalse(shadow.verify_full().passed)
        ledger.close()

    def test_delta_then_rebuild_is_root_equivalent(self):
        ledger=self.seed(); shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0')
        for i in range(7):
            ledger.append_event(event_id=f'e{i}',idem=f'e{i}',base_epoch=ledger.epoch,event_type='UPDATE',writer='t',ops=[{'op':'SET','domain':'goal','key':'g1','value':{'priority':i/6},'epistemic':'KNOWN','status':'CURRENT'}])
            shadow.refresh(now=f't{i+1}')
        incremental=shadow.receipt().root_hash
        rebuilt=shadow.full_rebuild(now='rebuild')['root_hash']
        self.assertEqual(incremental,rebuilt)
        self.assertTrue(shadow.verify_full().passed)
        ledger.close()

    def test_raw_semantic_state_tamper_is_detected(self):
        ledger=self.seed(); shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0')
        ledger.conn.execute("UPDATE state SET value_json=? WHERE domain='memory' AND k='alpha'",('{"tampered":true}',)); ledger.conn.commit()
        verification=shadow.verify_full()
        self.assertFalse(verification.passed)
        self.assertGreaterEqual(verification.altered_leaf_count,1)
        ledger.close()

    def test_retract_remains_authenticated_row(self):
        ledger=self.seed(); shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0'); before=shadow.receipt().root_hash
        ledger.append_event(event_id='ret',idem='ret',base_epoch=ledger.epoch,event_type='RETRACT',writer='t',ops=[{'op':'RETRACT','domain':'memory','key':'beta','value':None,'epistemic':'REVOKED'}])
        shadow.refresh(now='t1'); after=shadow.receipt().root_hash
        self.assertNotEqual(before,after)
        self.assertEqual(shadow.receipt().authenticated_rows,3)
        self.assertTrue(shadow.verify_full().passed)
        ledger.close()

    def test_snapshot_and_replay_ignore_physical_shadow_columns(self):
        ledger=self.seed(); shadow=EmbeddedAuthenticatedStateShadowV2(ledger); shadow.full_rebuild(now='t0'); snap=ledger.snapshot('s1'); self.assertTrue(ledger.verify_snapshot('s1'))
        events=ledger.export_events(); replay=StateLedger.replay(events); self.assertEqual(replay.semantic_state_hash,ledger.semantic_state_hash); self.assertEqual(replay.epoch,snap['epoch'])
        replay.close(); ledger.close()


if __name__=='__main__': unittest.main()
