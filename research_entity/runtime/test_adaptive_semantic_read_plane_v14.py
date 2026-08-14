#!/usr/bin/env python3
import unittest
from adaptive_semantic_read_plane_v14 import (
    AdaptiveReadRequest,AdaptiveSemanticReadPlaneV14,VerifiedReadBasis,
    StaleReadBasis,UnverifiedReadBasis,
)

class V14Tests(unittest.TestCase):
 def make(self,*,basis=None):
  calls=[]
  chosen=basis or VerifiedReadBasis('cycle:g1',1,1,'h1')
  def verify(r): calls.append('basis'); return chosen
  def exact(k,b,n): calls.append(('exact',b.basis_id)); return ['E'] if k=='known' else []
  def sem(q,b,n): calls.append(('semantic',b.basis_id)); return ['S1','S2'] if 'compiled' in q else []
  def resolve(q,b): calls.append(('resolve',b.basis_id)); return 'entity_a' if 'amber' in q else None
  def graph(l,q,b,n): calls.append(('graph',b.basis_id)); return ['G'] if l=='entity_a' else []
  def comp(q,b,n): calls.append(('compositional',b.basis_id)); return ['P'] if 'route' in q else []
  def fallback(q,b,n): calls.append(('fallback',b.basis_id)); return ['F']
  return AdaptiveSemanticReadPlaneV14(
      verify_read_basis=verify,exact_lookup=exact,compiled_semantic_lookup=sem,
      resolve_entity=resolve,graph_lookup=graph,compositional_lookup=comp,
      fallback_lookup=fallback),calls

 def test_exact_is_cheapest_and_stops(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','anything',1,1,exact_normalized_key='known'))
  self.assertEqual((r.mode,r.refs,r.read_basis_id),('EXACT_INDEX_LOOKUP',('E',),'cycle:g1'))
  self.assertEqual(c,['basis',('exact','cycle:g1')])

 def test_verified_semantic_sufficiency_stop_never_pads(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','compiled family',1,1))
  self.assertEqual(r.mode,'VERIFIED_SEMANTIC_SUFFICIENCY_STOP');self.assertFalse(r.lexical_padding_used)
  self.assertNotIn(('fallback','cycle:g1'),c)

 def test_alias_then_graph(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','what does amber require',1,1))
  self.assertEqual((r.mode,r.refs,r.resolved_logical_id),('ENTITY_RESOLVED_CLAYGRAPH',('G',),'entity_a'))

 def test_compositional_frontier_precedes_graph_after_resolution(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','best route for amber',1,1,compositional=True))
  self.assertEqual((r.mode,r.refs),('COMPOSITIONAL_PARETO_FRONTIER',('P',)))
  self.assertNotIn(('graph','cycle:g1'),c)

 def test_unknown_falls_back(self):
  p,c=self.make();r=p.query(AdaptiveReadRequest('q','totally unknown',1,1))
  self.assertEqual((r.mode,r.refs),('CONVENTIONAL_FALLBACK',('F',)))

 def test_stale_basis_fails_closed_before_exact_fastpath(self):
  p,c=self.make(basis=VerifiedReadBasis('cycle:old',1,1,'h-old'))
  with self.assertRaises(StaleReadBasis):
   p.query(AdaptiveReadRequest('q','anything',2,2,exact_normalized_key='known'))
  self.assertEqual(c,['basis'])

 def test_stale_basis_fails_closed_before_compiled_fastpath(self):
  p,c=self.make(basis=VerifiedReadBasis('cycle:old',1,1,'h-old'))
  with self.assertRaises(StaleReadBasis):
   p.query(AdaptiveReadRequest('q','compiled family',2,2))
  self.assertEqual(c,['basis'])

 def test_unverified_basis_fails_closed(self):
  p,c=self.make(basis=VerifiedReadBasis('cycle:g1',1,1,'h1',verified=False))
  with self.assertRaises(UnverifiedReadBasis):
   p.query(AdaptiveReadRequest('q','anything',1,1,exact_normalized_key='known'))
  self.assertEqual(c,['basis'])

if __name__=='__main__':unittest.main(verbosity=2)
