import os, sqlite3, tempfile, unittest
from dataclasses import replace
from .frank_integrated_spine import FrankIntegratedSpine, MODULES, LINEAGE
from .state_ledger import StaleEpoch

VIS={'source_id':'cam0','capture_epoch':1,'features':{'shape':'box'},'sensor_confidence':.92,'candidate_label':'cup','prototype_similarity':.9}
OPTS=[{'name':'answer','salience':.8},{'name':'inspect','salience':.5}]

class SpineTests(unittest.TestCase):
    def test_full_cycle_exercises_all_modules_and_lineage(self):
        r=FrankIntegratedSpine(); out=r.cycle('Hallo Frank',VIS,OPTS); self.assertTrue(out['all_modules_exercised']); self.assertEqual(set(out['modules_seen']),set(MODULES)); self.assertTrue(out['lineage_coverage']['pass']); self.assertEqual(out['lineage_coverage']['families'],len(LINEAGE)); r.close()
    def test_effect_needs_external_fresh_permit(self):
        r=FrankIntegratedSpine(); p={'kind':'COGNITIVE_PROPOSAL','authority':'NONE'}; self.assertEqual(r.effect(p,None,'x')['status'],'DENIED_NO_PERMIT'); q=r.permit(p,'x'); r.commit({'x':1},'advance'); self.assertEqual(r.effect(p,q,'x')['status'],'DENIED_STALE_EPOCH'); r.close()
    def test_model_never_mints_authority(self):
        r=FrankIntegratedSpine(); p={'kind':'COGNITIVE_PROPOSAL','authority':'EXECUTE'}; q=r.permit(p,'x'); self.assertEqual(r.effect(p,q,'x')['status'],'DENIED_MODEL_AUTHORITY_CLAIM'); r.close()
    def test_recurrence_not_false_convergence_or_emergence(self):
        r=FrankIntegratedSpine(); x=r.recurrence(delta=.01,pressure=.8,count=1,budget=4,utility=.01); self.assertEqual(x['decision'],'ESCALATE_STALLED'); self.assertFalse(x['emergence_claim']); r.close()
    def test_visual_conflict_beats_familiarity(self):
        r=FrankIntegratedSpine(); f=dict(VIS,sensor_conflict=True); self.assertEqual(r.perceive(f)['mvc']['outcome'],'CONFLICT'); r.close()
    def test_bronze_cannot_promote_truth(self):
        r=FrankIntegratedSpine(); x=r.promote(tier='BRONZE',before=.1,after=.99); self.assertEqual(x['status'],'SHADOW_ONLY_BRONZE'); self.assertIsNone(r.ledger.get('visual','promoted_classifier')); r.close()
    def test_poison_and_no_improvement_rejected(self):
        r=FrankIntegratedSpine(); self.assertEqual(r.promote(poison=True)['status'],'REJECTED_POISON_RISK'); self.assertEqual(r.promote(before=.8,after=.7)['status'],'REJECTED_NO_IMPROVEMENT'); r.close()
    def test_recovery_exact(self):
        r=FrankIntegratedSpine(); r.cycle('A',VIS,OPTS); r.cycle('B',dict(VIS,capture_epoch=2),OPTS,mode='thinking'); x=r.recovery(); self.assertTrue(x['semantic_state_hash_equal']); self.assertTrue(x['trace_root_hash_equal']); self.assertTrue(x['epoch_equal']); r.close()
    def test_derived_graph_not_authority(self):
        r=FrankIntegratedSpine(); r.commit({'a':1,'b':2},'s'); g=r.topology(); self.assertEqual(g['authority'],'DERIVED_NON_AUTHORITATIVE'); r.close()
    def test_workspace_stages_are_distinct(self):
        r=FrankIntegratedSpine(); w=r.workspace({'relay':True},{'alternatives':[{'salience':.3}]}); self.assertFalse(w['ignition']); self.assertFalse(w['delivered']); self.assertFalse(w['uptake']); self.assertFalse(w['causal_use']); self.assertFalse(w['reentry']); r.close()
    def test_model_modes_are_abi_not_identity(self):
        r=FrankIntegratedSpine(); w={'ignition':True,'selected':'0'}; a=r.model(dict(w),mode='instruct'); b=r.model(dict(w),mode='thinking'); self.assertEqual(a['authority'],'NONE'); self.assertEqual(b['authority'],'NONE'); self.assertNotEqual(a['mode'],b['mode']); r.close()
    def test_sqlite_wal_full_and_stale_writer(self):
        fd,path=tempfile.mkstemp(); os.close(fd)
        try:
            a=FrankIntegratedSpine(path); b=FrankIntegratedSpine(path); jm=a.ledger.conn.execute('PRAGMA journal_mode').fetchone()[0].lower(); sy=a.ledger.conn.execute('PRAGMA synchronous').fetchone()[0]; self.assertEqual(jm,'wal'); self.assertEqual(int(sy),2); base=b.ledger.epoch; a.commit({'a':1},'a1');
            with self.assertRaises(StaleEpoch): b.ledger.append_event(event_id='stale',idem='stale',base_epoch=base,event_type='X',writer='b',ops=[{'op':'SET','domain':'semantic','key':'b','value':2,'epistemic':'KNOWN','status':'CURRENT'}])
            a.close(); b.close()
        finally:
            for p in (path,path+'-wal',path+'-shm'):
                if os.path.exists(p): os.unlink(p)
    def test_many_cycles_preserve_invariants(self):
        r=FrankIntegratedSpine()
        for i in range(50):
            out=r.cycle(str(i),dict(VIS,capture_epoch=i+1,prototype_similarity=.9 if i%2 else .4),OPTS,mode='thinking' if i%2 else 'instruct'); self.assertTrue(out['all_modules_exercised']); self.assertTrue(out['lineage_coverage']['pass']); self.assertNotEqual(out['proposal']['authority'],'EXECUTE')
        rec=r.recovery(); self.assertEqual(rec['events'],150); self.assertTrue(rec['semantic_state_hash_equal']); self.assertTrue(rec['trace_root_hash_equal']); r.close()
    def test_snapshot_remains_verifiable_after_later_commit(self):
        r=FrankIntegratedSpine(); r.commit({'a':1},'a'); s=r.ledger.snapshot('s'); r.commit({'b':2},'b'); self.assertTrue(r.ledger.verify_snapshot('s')); r.close()

if __name__=='__main__': unittest.main()
