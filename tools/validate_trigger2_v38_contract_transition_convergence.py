#!/usr/bin/env python3
"""Validate Trigger-2 v38 checkpoint-contract and executable-transition successors."""
from __future__ import annotations
import copy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
import trigger2_qwen35_checkpoint_candidates_gate_v3 as cg
import trigger2_executable_transition_pilot_v1 as et
REGISTRY=ROOT/'research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v4.json'
def rehash(r):
 semantic={'process_id':r.get('process_id_evaluator_only'),'state_before':r.get('state_before'),'semantic_delta':r.get('semantic_delta'),'candidate_payload':r.get('candidate_payload_target'),'expected_state_after':r.get('expected_state_after')}
 r['semantic_transition_sha256']=et.dg(semantic)

def run()->dict:
 tests={}
 reg=json.loads(REGISTRY.read_text(encoding='utf-8'))
 paths=[]
 for c in reg['candidates']:
  for k in ('checkpoint_identity_receipt','loader_receipt'):
   if c.get(k):paths.append(c[k])
 cache={p:json.loads((ROOT/p).read_text(encoding='utf-8')) for p in paths}
 def loader(p):return copy.deepcopy(cache[p])
 base=cg.adjudicate(copy.deepcopy(reg),loader)
 tests['C1_CURRENT_EXACT_RECEIPTS_SOURCE_INTEGRITY_PASS']=base['pass'] is True
 tests['C2_SELECTION_REMAINS_UNREADY']=base['selection_ready'] is False and base['checkpoint_winner'] is None
 d=base['derived_candidates']
 tests['C3_BASE_ABSENT_CHAT_TEMPLATE_EXPLICIT']=d['QWEN35_08B_BASE']['identity']['chat_template']['status']=='ABSENT_FROM_MANIFEST'
 tests['C4_TARGET_NESTED_ARCH_EXTRACTED']=d['QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED']['identity']['architecture']==cg.REQUIRED_TEXT_ARCH
 tests['C5_LOADER_V1_DOES_NOT_BIND_BYTES']=all(x['loader']['consumed_identity_match']=='UNKNOWN_UNBOUND_BYTES' for x in d.values() if x['loader']['loader_consumption_observed'])
 mutations=[]
 r=copy.deepcopy(reg);r['schema']='STALE';mutations.append(('M_SCHEMA',r,cache))
 r=copy.deepcopy(reg);r['candidates'][0]['immutable_revision']='0'*40;mutations.append(('M_REVISION',r,cache))
 r=copy.deepcopy(reg);r['candidates'][0]['candidate_role']='TARGET_MEASURED';mutations.append(('M_ROLE',r,cache))
 r=copy.deepcopy(reg);r['candidates'][0]['final_winner_role_eligible']=True;mutations.append(('M_ELIGIBILITY',r,cache))
 for name,r,c in mutations:
  out=cg.adjudicate(r,lambda p,cc=c:copy.deepcopy(cc[p]));tests[name]=out['pass'] is False
 r=copy.deepcopy(reg);c=copy.deepcopy(cache);p=r['candidates'][2]['checkpoint_identity_receipt'];c[p]['config']['text_config']['hidden_size']=None
 tests['M_NESTED_ARCH']=cg.adjudicate(r,lambda x:copy.deepcopy(c[x]))['pass'] is False
 r=copy.deepcopy(reg);c=copy.deepcopy(cache);p=r['candidates'][0]['loader_receipt'];c[p]['loader_consumption_observed']=False
 tests['M_LOADER_OBSERVATION']=cg.adjudicate(r,lambda x:copy.deepcopy(c[x]))['pass'] is False
 r=copy.deepcopy(reg);c=copy.deepcopy(cache);p=r['candidates'][0]['checkpoint_identity_receipt'];c[p]['config_json_sha256']='9'*64
 tests['M_DECLARED_DIGEST']=cg.adjudicate(r,lambda x:copy.deepcopy(c[x]))['pass'] is False
 ers=et.rows();e0=et.adjudicate(copy.deepcopy(ers))
 tests['E1_EXECUTABLE_TRANSITION_PILOT_PASS']=e0['pass'] is True and e0['row_count']==6 and e0['training_rows_admitted']==0
 r=copy.deepcopy(ers);r[0]['candidate_payload_target']['rule']='narrate';rehash(r[0]);tests['E_META_RULE_REJECTED']=et.adjudicate(r)['pass'] is False
 r=copy.deepcopy(ers);r[0]['candidate_payload_target']['effect_receipt']={'ok':True};rehash(r[0]);tests['E_SELF_MINTED_EFFECT_RECEIPT_REJECTED']=et.adjudicate(r)['pass'] is False
 r=copy.deepcopy(ers);r[0]['candidate_payload_target']['unknowns']=[];r[0]['expected_state_after']['deadline']='FALSE';rehash(r[0]);tests['E_UNKNOWN_COLLAPSE_REJECTED']=et.adjudicate(r)['pass'] is False
 r=copy.deepcopy(ers);r[1]['candidate_payload_target']['result_payload']['resolved_winner']='A';r[1]['candidate_payload_target']['result_payload']['alternative_set']=['A'];rehash(r[1]);tests['E_MAJORITY_COLLAPSE_REJECTED']=et.adjudicate(r)['pass'] is False
 r=copy.deepcopy(ers);r[3]['candidate_payload_target']['result_payload']['claude_handoff_packet']['activation_access']='DIRECT_HIDDEN_STATE';rehash(r[3]);tests['E_HIDDEN_ACTIVATION_CLAIM_REJECTED']=et.adjudicate(r)['pass'] is False
 r=copy.deepcopy(ers);r[5]['candidate_payload_target']['result_payload']['jspace_measurement']['behavioral_causal_effect']='TRUE';r[5]['expected_state_after']['jspace_causal_credit']=1;rehash(r[5]);tests['E_JSPACE_CAUSAL_OVERCLAIM_REJECTED']=et.adjudicate(r)['pass'] is False
 passed=all(tests.values())
 return {'schema':'CLAY_TRIGGER2_V38_CONTRACT_TRANSITION_VALIDATION/v1','pass':passed,'tests':tests,'checkpoint_winner':None,'accepted_dataset_tokens':0,'training_rows_admitted':0,'training_credit':0,'jspace_model_credit':0,'whole_hcu_runtime_credit':0,'whole_entityos_runtime_credit':0,'evidence_boundary':'Repository source/receipt integrity plus deterministic transition fixtures only; no runtime/model/training promotion.'}
if __name__=='__main__':
 out=run();print(json.dumps(out,sort_keys=True,indent=2));raise SystemExit(0 if out['pass'] else 1)
