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
        ])
        return l,p
    def test_query_is_deterministic_at_epoch(self):
        l,p=self.make(); a=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); b=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); self.assertEqual(a.query_hash,b.query_hash); self.assertEqual(a.row_hashes,b.row_hashes); l.close()
    def test_stale_query_basis_rejected(self):
        l,p=self.make(); old=l.epoch; p.transact(event_id='n',idem='n',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'semantic','key':'n','value':1,'epistemic':'KNOWN','status':'CURRENT'}]);
        with self.assertRaises(StaleEpoch): p.query(QuerySpec('q',basis_epoch=old))
        l.close()
    def test_default_assembly_selects_known_not_unknown_or_conflict(self):
        l,p=self.make(); r=p.query(QuerySpec('q',domains=('semantic',),basis_epoch=l.epoch)); s=p.select_for_assembly(r); self.assertEqual([x['key'] for x in s['selected']],['known']); self.assertEqual(s['conflicts_present'],1); l.close()
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
    def test_query_filters_order_and_truncation(self):
        l,p=self.make(); p.transact(event_id='more',idem='more',base_epoch=l.epoch,event_type='X',writer='t',ops=[
            {'op':'SET','domain':'alpha','key':'b','value':2,'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'alpha','key':'a','value':1,'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'beta','key':'a','value':3,'epistemic':'KNOWN','status':'CURRENT'},
        ])
        r=p.query(QuerySpec('filtered',domains=('alpha',),keys=('a','b'),statuses=('current','CURRENT'),epistemic=('known','KNOWN'),limit=1,basis_epoch=l.epoch))
        self.assertEqual([(x['domain'],x['key']) for x in r.rows],[('alpha','a')]); self.assertTrue(r.truncated); l.close()
    def test_empty_status_or_epistemic_filter_admits_nothing(self):
        l,p=self.make(); a=p.query(QuerySpec('empty-status',statuses=(),basis_epoch=l.epoch)); b=p.query(QuerySpec('empty-epi',epistemic=(),basis_epoch=l.epoch)); self.assertEqual(a.rows,()); self.assertEqual(b.rows,()); self.assertFalse(a.truncated); self.assertFalse(b.truncated); l.close()
    def test_query_value_shape_matches_materialized_contract(self):
        l,p=self.make(); r=p.query(QuerySpec('shape',domains=('semantic',),keys=('known',),basis_epoch=l.epoch)); self.assertEqual(len(r.rows),1); row=r.rows[0]; self.assertEqual(row['value'],{'v':1}); self.assertEqual(row['epistemic'],'KNOWN'); self.assertEqual(row['status'],'CURRENT'); self.assertIsInstance(row['domain_epoch'],int); self.assertTrue(row['semantic_hash']); l.close()
if __name__=='__main__': unittest.main()
