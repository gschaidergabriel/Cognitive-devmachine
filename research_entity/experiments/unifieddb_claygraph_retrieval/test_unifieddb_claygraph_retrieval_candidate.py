import unittest
from unifieddb_claygraph_retrieval_candidate import ProjectionBasis, StaleRetrievalProjection, UnifiedDBClayGraphRetrievalCandidate

class RetrievalCandidateTests(unittest.TestCase):
    def make(self):
        rows=[]
        def row(key,lid,kind,ep,text):
            return {'domain':'semantic','key':key,'value':{'logical_id':lid,'record_kind':kind,'evidence_class':ep,'search_text':text},'epistemic':'KNOWN','status':'CURRENT','domain_epoch':7,'semantic_hash':'h-'+key}
        rows += [
          row('cur','component_a','component_state','VERIFIED','component_a zxalpha active current owner team_a stable mode mode_7'),
          row('svc','service_b','service_fact','VALIDATED','service_b provides capability cap_beta through interface iface_beta'),
          row('res','resource_c','resource_fact','VALIDATED','resource_c supplies resource quota_gamma for downstream chain'),
          row('hyp','component_a_hyp','claim','HYPOTHESIS','component_a zxalpha allegedly owned by speculative_team; unverified hypothesis'),
        ]
        edges=[
          {'source_logical_id':'component_a','target_logical_id':'service_b','relation_type':'REQUIRES','weight':.97,'confidence':.98,'causal_class':'CAUSAL'},
          {'source_logical_id':'service_b','target_logical_id':'resource_c','relation_type':'DEPENDS_ON','weight':.95,'confidence':.97,'causal_class':'CAUSAL'},
        ]
        basis=ProjectionBasis(7,'statehash',4,True,True)
        x=UnifiedDBClayGraphRetrievalCandidate(); x.rebuild(state_rows=rows,graph_edges=edges,basis=basis)
        return x,basis
    def top(self,x,b,text,graph=True): return x.query(query_id='q',text=text,basis=b,graph_enabled=graph).results[0].record_id
    def test_direct_current(self):
        x,b=self.make(); self.assertEqual(self.top(x,b,'What is the current stable mode of component_a zxalpha?'),'h-cur'); x.close()
    def test_provenance_beats_hypothesis(self):
        x,b=self.make(); self.assertEqual(self.top(x,b,'Which verified owner is confirmed for component_a zxalpha?'),'h-cur'); x.close()
    def test_one_hop(self):
        x,b=self.make(); self.assertEqual(self.top(x,b,'Which capability is provided by the service that component_a requires?'),'h-svc'); x.close()
    def test_two_hop(self):
        x,b=self.make(); self.assertEqual(self.top(x,b,'Which resource ultimately supports component_a through its required service chain?'),'h-res'); x.close()
    def test_hypothesis_request_preserves_uncertainty(self):
        x,b=self.make(); self.assertEqual(self.top(x,b,'What speculative ownership hypothesis exists for component_a zxalpha?'),'h-hyp'); x.close()
    def test_graph_lesion_breaks_graph_retrieval(self):
        x,b=self.make(); self.assertNotEqual(self.top(x,b,'Which capability is provided by the service that component_a requires?',False),'h-svc'); x.close()
    def test_unverified_graph_projection_refused(self):
        rows=[{'domain':'semantic','key':'x','value':{'logical_id':'x','search_text':'x'},'epistemic':'KNOWN','status':'CURRENT','domain_epoch':1,'semantic_hash':'hx'}]
        x=UnifiedDBClayGraphRetrievalCandidate()
        with self.assertRaises(ValueError): x.rebuild(state_rows=rows,graph_edges=[],basis=ProjectionBasis(1,'h',1,True,False))
        x.close()
    def test_stale_basis_rejected(self):
        x,b=self.make()
        with self.assertRaises(StaleRetrievalProjection): x.query(query_id='q',text='component_a',basis=ProjectionBasis(8,'other',4,True,True))
        x.close()

if __name__=='__main__': unittest.main()
