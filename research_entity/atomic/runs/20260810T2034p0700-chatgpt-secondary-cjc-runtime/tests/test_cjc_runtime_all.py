#!/usr/bin/env python3
"""Consolidated executable discriminator suite for ATOMIC-CANDIDATE-CJC-001."""
from __future__ import annotations
import random, unittest
from causal_jet_commutator import *
from typed_ir_cjc_adapter import *
from frank_v01_cjc_gate import *

def contract(use,tid,*,epoch='7',effect=EffectClass.INTERNAL_STATE,reads=('x',),writes=('x',)):
    return TransitionContract(tid,use,'1',epoch,effect,frozenset(reads),frozenset(writes),(f'evidence:{tid}',),True,True)
def execid(epoch='7'): return FrankExecutionIdentity('clayir:test',epoch,'3','a'*64,'lineage-1','work-1')

class AlgebraTests(unittest.TestCase):
    def test_boolean_idempotence(self):
        z=BoolJet.var('u'); self.assertEqual(z.mul(z,JetPolicy()).canonical(),z.canonical())
    def test_masked_hidden_order(self):
        ident=StateIdentity.derive(program_semantic_id='clayir:t',state_epoch='7',state_version='1'); a=Scale(contract('A','scale'),'x',2); b=Add(contract('B','add'),'x',1); c=SetValue(contract('C','mask'),'x',0)
        rec=classify_cjc_context(JetState.from_concrete(ident,{'x':1}),[],a,b,[c],JetPolicy()); self.assertEqual(rec.classification,PairClass.HIDDEN_CAUSAL_NONCOMMUTE); self.assertFalse(rec.authority_minted)
        self.assertEqual(classify_state_only_context({'x':1},[],a,b,[c]),PairClass.FULL_COMMUTE); self.assertEqual(classify_reference_context({'x':1},[],a,b,[c]),PairClass.HIDDEN_CAUSAL_NONCOMMUTE)
    def test_visible_noncommute(self):
        ident=StateIdentity.derive(program_semantic_id='clayir:t',state_epoch='7',state_version='1'); rec=classify_cjc(JetState.from_concrete(ident,{'x':1}),Scale(contract('A','s'),'x',2),Add(contract('B','a'),'x',1),JetPolicy()); self.assertEqual(rec.classification,PairClass.STATE_NONCOMMUTE)
    def test_disjoint_commute(self):
        ident=StateIdentity.derive(program_semantic_id='clayir:t',state_epoch='7',state_version='1'); a=Add(contract('A','x',reads=('x',),writes=('x',)),'x',1); b=Add(contract('B','y',reads=('y',),writes=('y',)),'y',1); self.assertEqual(classify_cjc(JetState.from_concrete(ident,{'x':0,'y':0}),a,b,JetPolicy()).classification,PairClass.FULL_COMMUTE)
    def test_stale_fails_closed(self):
        ident=StateIdentity.derive(program_semantic_id='clayir:t',state_epoch='7',state_version='1'); a=Add(contract('A','stale',epoch='6'),'x',1); b=Add(contract('B','b'),'x',1); self.assertEqual(classify_cjc(JetState.from_concrete(ident,{'x':0}),a,b,JetPolicy()).classification,PairClass.UNKNOWN)
    def test_opaque_fails_closed(self):
        ident=StateIdentity.derive(program_semantic_id='clayir:t',state_epoch='7',state_version='1'); a=OpaqueTransition(contract('A','opaque',effect=EffectClass.OPAQUE),'x'); b=Add(contract('B','b'),'x',1); self.assertEqual(classify_cjc(JetState.from_concrete(ident,{'x':0}),a,b,JetPolicy()).classification,PairClass.UNKNOWN)
    def test_credit_matches_replay(self):
        ident=StateIdentity.derive(program_semantic_id='clayir:t',state_epoch='7',state_version='1'); ops=[Add(contract('A','a'),'x',2),Scale(contract('B','b'),'x',3)]; sym=run_symbolic(JetState.from_concrete(ident,{'x':1}),ops,JetPolicy()); self.assertEqual(credit_signature_from_symbolic(sym,exact_use_set(ops)),credit_signature_replay({'x':1},ops))
    def test_random_differential_2500(self):
        rng=random.Random(20260810); ident=StateIdentity.derive(program_semantic_id='clayir:r',state_epoch='7',state_version='1')
        for i in range(2500):
            x=rng.randint(-3,3); a=Scale(contract(f'A{i}',f's{i}'),'x',rng.choice([-2,-1,0,2,3])); b=Add(contract(f'B{i}',f'a{i}'),'x',rng.randint(-3,3)); suffix=[]
            if rng.random()<0.4:suffix=[SetValue(contract(f'C{i}',f'm{i}'),'x',rng.randint(-2,2))]
            got=classify_cjc_context(JetState.from_concrete(ident,{'x':x}),[],a,b,suffix,JetPolicy(max_degree=8,max_terms=4096)).classification; truth=classify_reference_context({'x':x},[],a,b,suffix); self.assertEqual(got,truth)

class AdapterTests(unittest.TestCase):
    def bridge(self): return {'bridge_schema':EXPECTED_BRIDGE_SCHEMA,'semantic_identity':'clayir:'+'1'*64,'state_identity':{'semantic_id':'clayir:'+'1'*64,'state_epoch':'7','state_version':'3','state_instance_id':'claystate:'+'2'*64},'authority':{'typed_ir_description_mints_effect_authority':False,'frontend_artifact_mints_effect_authority':False},'typed_ir':{'declarations':[{'kind':'record','fields':[{'name':'x'}]}]}}
    def spec(self,op='ADD'):
        params={'field':'x','amount':1} if op=='ADD' else {'field':'x','value':0}; return TransitionSpec('t','U','1',op,params,frozenset({'x'}),frozenset({'x'}),('evidence:t',),'INTERNAL_STATE')
    def test_explicit_operator_compiles(self): self.assertIsInstance(compile_transition(identity_from_wp03_bridge(self.bridge()),self.spec()),Add)
    def test_unknown_operator_never_infers(self):
        with self.assertRaises(AdapterError): compile_transition(identity_from_wp03_bridge(self.bridge()),self.spec('MAGIC_ADD'))
    def test_external_effect_rejected(self):
        rt=identity_from_wp03_bridge(self.bridge()); s=self.spec(); s=TransitionSpec(s.transition_id,s.use_ref,s.version,s.operator,s.params,s.reads,s.writes,s.evidence_refs,'EXTERNAL_EFFECT')
        with self.assertRaises(AdapterError): compile_transition(rt,s)
    def test_wp03_state_identity_preserved(self):
        rt=identity_from_wp03_bridge(self.bridge()); self.assertEqual(state_identity_for_cjc(rt).state_instance_id,rt.state_instance_id)

class FrankGateTests(unittest.TestCase):
    def test_hidden_routes_coordinate(self):
        a=Scale(contract('A','scale'),'x',2); b=Add(contract('B','add'),'x',1); c=SetValue(contract('C','mask'),'x',0); d=classify_pair_for_frank(execution=execid(),initial_values={'x':1},prefix=[],a=a,b=b,suffix=[c],policy=JetPolicy()); self.assertEqual(d.route,GateRoute.COORDINATE_HIDDEN_CAUSAL); self.assertFalse(d.effect_authority_minted)
    def test_effect_routes_effect_gate(self):
        a=Add(contract('A','e',effect=EffectClass.EXTERNAL_EFFECT),'x',1); b=Add(contract('B','b'),'x',1); d=classify_pair_for_frank(execution=execid(),initial_values={'x':0},prefix=[],a=a,b=b,suffix=[],policy=JetPolicy()); self.assertEqual(d.route,GateRoute.FALLBACK_EFFECT_GATE)
    def test_fabric_extracts_component_and_isolate(self):
        seq=[Scale(contract('A','s'),'x',2),Add(contract('B','a'),'x',1),SetValue(contract('C','m'),'x',0),Add(contract('D','y',reads=('y',),writes=('y',)),'y',1)]; f=build_coordination_fabric(execution=execid(),initial_values={'x':1,'y':0},sequence=seq,policy=JetPolicy(max_degree=10,max_terms=8192)); assert_no_authority_mint(f); self.assertEqual(f.independent_use_refs,('D',)); self.assertTrue(any('A' in c.use_refs and 'B' in c.use_refs for c in f.coordination_components))
    def test_duplicate_use_refs_fail(self):
        with self.assertRaises(ValueError):build_coordination_fabric(execution=execid(),initial_values={'x':0},sequence=[Add(contract('A','1'),'x',1),Add(contract('A','2'),'x',2)])
    def test_hashes_deterministic(self):
        seq=[Add(contract('A','1'),'x',1),Add(contract('B','2'),'x',2)]; kw=dict(execution=execid(),initial_values={'x':0},sequence=seq); self.assertEqual(build_coordination_fabric(**kw).semantic_hash,build_coordination_fabric(**kw).semantic_hash)

if __name__=='__main__':unittest.main(verbosity=2)
