import unittest
from .state_ledger import StateLedger, StaleEpoch
from .unifieddb_query_plane import UnifiedDBQueryPlane, QuerySpec, SelectionPolicy

class UDBTests(unittest.TestCase):
    def make(self):
        l=StateLedger(); p=UnifiedDBQueryPlane(l)
        p.transact(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='t',ops=[
            {'op':'SET','domain':'semantic','key':'known','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'semantic','key':'unknown','value':{'v':2},'epistemic':'UNKNOWN','status':'CURRENT'},
            {'op':'SET','domain':'semantic','key':'conflict','value':{'v':3},'epistemic':'CONFLICT','status':'CURRENT'},
            {'op':'SET','domain':'semantic','key':'ä-key','value':{'v':4},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'memory','key':'known','value':{'v':5},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'memory','key':'old','value':{'v':6},'epistemic':'KNOWN','status':'SUPERSEDED'},
        ])
        return l,p

    def assert_fast_equals_legacy(self,p,spec):
        self.assertEqual(p._query_rows_fast(spec),p._query_rows_legacy(spec))

    def test_query_is_deterministic_at_epoch(self):
        l,p=self.make(); a=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); b=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); self.assertEqual(a.query_hash,b.query_hash); self.assertEqual(a.row_hashes,b.row_hashes); l.close()
    def test_stale_query_basis_rejected(self):
        l,p=self.make(); old=l.epoch; p.transact(event_id='n',idem='n',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'n','value':1,'epistemic':'KNOWN','status':'CURRENT'}]);
        with self.assertRaises(StaleEpoch): p.query(QuerySpec('q',basis_epoch=old))
        l.close()
    def test_default_assembly_selects_known_not_unknown_or_conflict(self):
        l,p=self.make(); r=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); s=p.select_for_assembly(r); self.assertEqual([x['key'] for x in s['selected']],['known','ä-key']); self.assertEqual(s['conflicts_present'],1); l.close()
    def test_conflict_can_be_included_but_remains_labelled(self):
        l,p=self.make(); r=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); s=p.select_for_assembly(r,SelectionPolicy(allow_epistemic=('KNOWN','CONFLICT'),include_conflicts=True)); row=next(x for x in s['selected'] if x['key']=='conflict'); self.assertEqual(row['epistemic'],'CONFLICT'); self.assertEqual(row['authority'],'CONTEXT_ONLY'); l.close()
    def test_selection_receipt_stales_after_write(self):
        l,p=self.make(); r=p.query(QuerySpec('q',basis_epoch=l.epoch)); p.transact(event_id='x',idem='x',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'x','value':1,'epistemic':'KNOWN','status':'CURRENT'}]);
        with self.assertRaises(StaleEpoch): p.select_for_assembly(r)
        l.close()
    def test_capability_view_is_derived_not_second_store(self):
        l,p=self.make(); p.transact(event_id='cap',idem='cap',base_epoch=l.epoch,event_type='CAP',writer='t',ops=[{'op':'SET','domain':'capability','key':'claude','value':{'state':'CAN_NOW'},'epistemic':'KNOWN','status':'CURRENT'}]); v=p.capability_view(); self.assertTrue(v['derived']); self.assertFalse(v['persistent_second_store']); self.assertEqual(v['authority'],'NON_AUTHORITATIVE_PROJECTION'); self.assertEqual(len(v['items']),1); l.close()
    def test_transaction_idempotency_reuses_ledger_contract(self):
        l,p=self.make(); base=l.epoch; kw=dict(event_id='idem',idem='idem',base_epoch=base,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'i','value':1,'epistemic':'KNOWN','status':'CURRENT'}]); a=p.transact(**kw); b=p.transact(**kw); self.assertEqual(a['status'],'COMMITTED'); self.assertEqual(b['status'],'ALREADY_COMMITTED'); l.close()

    def test_fast_path_matches_legacy_filter_and_truncation_semantics(self):
        l,p=self.make()
        specs=(
            QuerySpec('all',basis_epoch=l.epoch,limit=2),
            QuerySpec('domain',domains=('semantic',),basis_epoch=l.epoch,limit=3),
            QuerySpec('key',keys=('known',),basis_epoch=l.epoch,limit=8),
            QuerySpec('mixed',domains=('semantic','memory'),keys=('known','ä-key'),epistemic=('KNOWN',),basis_epoch=l.epoch,limit=8),
            QuerySpec('superseded',statuses=('SUPERSEDED',),epistemic=('KNOWN',),basis_epoch=l.epoch,limit=8),
            QuerySpec('empty-status',statuses=(),basis_epoch=l.epoch,limit=8),
            QuerySpec('empty-epistemic',epistemic=(),basis_epoch=l.epoch,limit=8),
        )
        for spec in specs:
            with self.subTest(spec=spec.query_id): self.assert_fast_equals_legacy(p,spec)
        l.close()

    def test_large_bound_filter_falls_back_without_semantic_drift(self):
        l,p=self.make(); keys=tuple(f'k{i}' for i in range(801))+('known',); spec=QuerySpec('fallback',keys=keys,basis_epoch=l.epoch,limit=8); self.assert_fast_equals_legacy(p,spec); l.close()

if __name__=='__main__': unittest.main()
