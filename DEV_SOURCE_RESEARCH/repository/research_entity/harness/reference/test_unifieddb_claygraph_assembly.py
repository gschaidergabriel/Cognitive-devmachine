import unittest

from .state_ledger import StateLedger, StaleEpoch
from .unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from .unifieddb_claygraph_assembly import (
    UnifiedClayContextAssembler, GraphProjectionReceipt, graph_rows_hash,
    StaleGraphProjection, AmbiguousGraphProjection, UnverifiedGraphProjection,
    GraphProjectionIntegrityError,
)

class UnifiedClayAssemblyTests(unittest.TestCase):
    def make(self):
        l=StateLedger(); p=UnifiedDBQueryPlane(l)
        p.transact(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='t',ops=[
            {'op':'SET','domain':'memory','key':'known','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'},
            {'op':'SET','domain':'memory','key':'unknown','value':{'v':2},'epistemic':'UNKNOWN','status':'CURRENT'},
            {'op':'SET','domain':'memory','key':'conflict','value':{'v':3},'epistemic':'CONFLICT','status':'CURRENT'},
        ])
        q=p.query(QuerySpec('q',domains=('memory',),basis_epoch=l.epoch,limit=32))
        rows=({'source':'memory:known','target':'gwt_workspace','relation':'candidate'},)
        g=GraphProjectionReceipt('g',7,l.epoch,graph_rows_hash(rows),len(rows),verified_equal=True)
        return l,p,q,rows,g

    def test_exact_epoch_verified_projection_assembles_known_state_only(self):
        l,p,q,rows,g=self.make(); a=UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=g,graph_rows=rows)
        self.assertEqual([x['key'] for x in a.state_items],['known']); self.assertEqual(a.conflicts_present,1); self.assertEqual(a.graph_source_epoch,a.basis_epoch); self.assertEqual(a.authority,'CONTEXT_ONLY_NO_EFFECT_AUTHORITY'); l.close()

    def test_state_write_stales_entire_assembly(self):
        l,p,q,rows,g=self.make(); p.transact(event_id='next',idem='next',base_epoch=l.epoch,event_type='X',writer='t',ops=[{'op':'SET','domain':'memory','key':'new','value':1,'epistemic':'KNOWN','status':'CURRENT'}])
        with self.assertRaises(StaleEpoch): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=g,graph_rows=rows)
        l.close()

    def test_graph_lag_is_rejected_in_exact_mode(self):
        l,p,q,rows,g=self.make(); lag=GraphProjectionReceipt('lag',6,l.epoch-1,graph_rows_hash(rows),len(rows),verified_equal=True)
        with self.assertRaises(StaleGraphProjection): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=lag,graph_rows=rows)
        l.close()

    def test_future_graph_source_epoch_is_always_rejected(self):
        l,p,q,rows,g=self.make(); future=GraphProjectionReceipt('future',8,l.epoch+1,graph_rows_hash(rows),len(rows),verified_equal=True)
        with self.assertRaises(StaleGraphProjection): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=future,graph_rows=rows,require_exact_graph_epoch=False)
        l.close()

    def test_ambiguous_projection_is_rejected(self):
        l,p,q,rows,g=self.make(); bad=GraphProjectionReceipt('amb',7,l.epoch,graph_rows_hash(rows),len(rows),ambiguous_heads=2,verified_equal=True)
        with self.assertRaises(AmbiguousGraphProjection): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=bad,graph_rows=rows)
        l.close()

    def test_unverified_projection_is_rejected(self):
        l,p,q,rows,g=self.make(); bad=GraphProjectionReceipt('unverified',7,l.epoch,graph_rows_hash(rows),len(rows),verified_equal=False)
        with self.assertRaises(UnverifiedGraphProjection): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=bad,graph_rows=rows)
        l.close()

    def test_graph_row_tampering_or_count_change_is_rejected(self):
        l,p,q,rows,g=self.make()
        with self.assertRaises(GraphProjectionIntegrityError): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=g,graph_rows=({'source':'tampered','target':'gwt_workspace','relation':'candidate'},))
        with self.assertRaises(GraphProjectionIntegrityError): UnifiedClayContextAssembler(p).assemble(assembly_id='a',query_receipt=q,graph_receipt=g,graph_rows=())
        l.close()

if __name__=='__main__': unittest.main()
