import unittest

from .state_auth_shadow import AuthenticatedStateShadowV1, AuthShadowIntegrityError
from .state_ledger import StateLedger


class AuthenticatedStateShadowTests(unittest.TestCase):
    def seed(self):
        l=StateLedger()
        l.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='t',ops=[
            {'op':'SET','domain':'memory','key':'alpha','value':{'v':1,'u':'ä✓'},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'memory','key':'beta','value':{'$kind':'set','items':[3,1,3,2]},'epistemic':'UNKNOWN','status':'CURRENT'},
            {'op':'SET','domain':'goal','key':'g1','value':{'priority':0.8},'epistemic':'KNOWN','status':'CURRENT'},
        ])
        return l

    def test_full_rebuild_verifies_and_is_non_authoritative(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); out=s.full_rebuild(now='t0'); v=s.verify_full(); r=s.receipt(verified_full=v.passed)
        self.assertEqual(out['leaf_count'],3); self.assertTrue(v.passed); self.assertTrue(r.verified_full); self.assertEqual(r.authority,'NON_AUTHORITATIVE_REBUILDABLE_INTEGRITY_SHADOW'); l.close()

    def test_delta_refresh_changes_root_and_full_verify_matches(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); first=s.full_rebuild(now='t0')['root_hash']
        l.append_event(event_id='u',idem='u',base_epoch=l.epoch,event_type='UPDATE',writer='t',ops=[{'op':'SET','domain':'memory','key':'alpha','value':{'v':2,'u':'λ'},'epistemic':'KNOWN','status':'CURRENT'}])
        out=s.refresh(now='t1'); self.assertEqual(out['mode'],'DELTA_REFRESH'); self.assertEqual(out['touched_refs'],1); self.assertNotEqual(first,out['root_hash']); self.assertTrue(s.verify_full().passed); l.close()

    def test_rebuild_after_delta_is_root_equivalent(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); s.full_rebuild(now='t0')
        for i in range(5):
            l.append_event(event_id=f'e{i}',idem=f'e{i}',base_epoch=l.epoch,event_type='UPDATE',writer='t',ops=[{'op':'SET','domain':'goal','key':'g1','value':{'priority':i/4},'epistemic':'KNOWN','status':'CURRENT'}]); s.refresh(now=f't{i+1}')
        incremental=s.receipt().root_hash; rebuilt=s.full_rebuild(now='rebuild')['root_hash']; self.assertEqual(incremental,rebuilt); self.assertTrue(s.verify_full().passed); l.close()

    def test_raw_state_tamper_is_detected_by_full_verify(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); s.full_rebuild(now='t0')
        l.conn.execute("UPDATE state SET value_json=? WHERE domain='memory' AND k='alpha'", ('{"tampered":true}',)); l.conn.commit()
        v=s.verify_full(); self.assertFalse(v.passed); self.assertGreaterEqual(v.altered_leaf_count,1); l.close()

    def test_same_event_history_replay_rebuilds_same_shadow_root(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); a=s.full_rebuild(now='a')['root_hash']; events=l.export_events(); r=StateLedger.replay(events); sr=AuthenticatedStateShadowV1(r); b=sr.full_rebuild(now='b')['root_hash']
        self.assertEqual(l.semantic_state_hash,r.semantic_state_hash); self.assertEqual(a,b); self.assertTrue(sr.verify_full().passed); r.close(); l.close()

    def test_no_change_refresh_rejects_unexplained_canonical_root_drift(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); s.full_rebuild(now='t0'); l._set('semantic_state_hash','00'*32); l.conn.commit()
        with self.assertRaises(AuthShadowIntegrityError): s.refresh(now='t1')
        l.close()

    def test_retract_is_an_authenticated_state_change_not_a_disappearing_leaf(self):
        l=self.seed(); s=AuthenticatedStateShadowV1(l); s.full_rebuild(now='t0'); before=s.receipt().root_hash
        l.append_event(event_id='ret',idem='ret',base_epoch=l.epoch,event_type='RETRACT',writer='t',ops=[{'op':'RETRACT','domain':'memory','key':'beta','value':None,'epistemic':'REVOKED'}]); s.refresh(now='t1'); after=s.receipt().root_hash
        self.assertNotEqual(before,after); self.assertEqual(s.receipt().leaf_count,3); self.assertTrue(s.verify_full().passed); l.close()


if __name__=='__main__': unittest.main()
