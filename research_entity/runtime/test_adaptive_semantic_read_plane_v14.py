#!/usr/bin/env python3
import unittest
from adaptive_semantic_read_plane_v14 import AdaptiveReadRequest,AdaptiveSemanticReadPlaneV14
class V14Tests(unittest.TestCase):
 def make(self):
  calls=[]
  def exact(k,n): calls.append('exact'); return ['E'] if k=='known' else []
  def sem(q,n): calls.append('semantic'); return ['S1','S2'] if 'compiled' in q else []
  def resolve(q,e): calls.append('resolve'); return 'entity_a' if 'amber' in q else None
  def graph(l,q,se,ge,n): calls.append('graph'); return ['G'] if l=='entity_a' else []
  def comp(q,se,ge,n): calls.append('compositional'); return ['P'] if 'route' in q else []
  def fallback(q,n): calls.append('fallback'); return ['F']
  return AdaptiveSemanticReadPlaneV14(exact_lookup=exact,compiled_semantic_lookup=sem,resolve_entity=resolve,graph_lookup=graph,compositional_lookup=comp,fallback_lookup=fallback),calls
 def test_exact_is_cheapest_and_stops(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','anything',1,1,exact_normalized_key='known'));self.assertEqual((r.mode,r.refs,c),('EXACT_INDEX_LOOKUP',('E',),['exact']))
 def test_verified_semantic_sufficiency_stop_never_pads(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','compiled family',1,1));self.assertEqual(r.mode,'VERIFIED_SEMANTIC_SUFFICIENCY_STOP');self.assertFalse(r.lexical_padding_used);self.assertNotIn('fallback',c)
 def test_alias_then_graph(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','what does amber require',1,1));self.assertEqual((r.mode,r.refs,r.resolved_logical_id),('ENTITY_RESOLVED_CLAYGRAPH',('G',),'entity_a'))
 def test_compositional_frontier_precedes_graph_after_resolution(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','best route for amber',1,1,compositional=True));self.assertEqual((r.mode,r.refs),('COMPOSITIONAL_PARETO_FRONTIER',('P',)));self.assertNotIn('graph',c)
 def test_unknown_falls_back(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','totally unknown',1,1));self.assertEqual((r.mode,r.refs),('CONVENTIONAL_FALLBACK',('F',)))
if __name__=='__main__':unittest.main(verbosity=2)
