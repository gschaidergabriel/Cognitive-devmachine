#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any, Callable
REGISTRY_SCHEMA='CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_CANDIDATES/v4'
GATE_SCHEMA='CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v3'
IDENTITY_SCHEMA='CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_IDENTITY/v1'
LOADER_SCHEMA='CLAY_TRIGGER2_QWEN35_08B_LOADER_CONSUMPTION_AND_RESOURCE_PROBE/v1'
SHA40=re.compile(r'^[0-9a-f]{40}$'); SHA256=re.compile(r'^[0-9a-f]{64}$')
PINNED={
 'QWEN35_08B_BASE':{'role':'CONTROL','repo':'Qwen/Qwen3.5-0.8B-Base','revision':'dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68'},
 'QWEN35_08B_POSTTRAINED':{'role':'CONTROL','repo':'Qwen/Qwen3.5-0.8B','revision':'2fc06364715b967f1860aea9cf38778875588b17'},
 'QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED':{'role':'TARGET_MEASURED','repo':'Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1','revision':'591852bda6e1979f59e4b0f5ee2919697b12e936'},
}
REQUIRED_TEXT_ARCH={'model_type':'qwen3_5_text','num_hidden_layers':24,'hidden_size':1024,'num_attention_heads':8,'num_key_value_heads':2,'vocab_size':248320,'max_position_embeddings':262144}
def _sha256(x): return isinstance(x,str) and bool(SHA256.fullmatch(x))
def _manifest_map(receipt):
 f=[]; rows=receipt.get('file_manifest')
 if not isinstance(rows,list) or not rows:return {},['IDENTITY_FILE_MANIFEST_REQUIRED']
 out={}
 for row in rows:
  if not isinstance(row,dict):f.append('IDENTITY_MANIFEST_ROW_OBJECT_REQUIRED');continue
  p=row.get('path')
  if not isinstance(p,str) or not p:f.append('IDENTITY_MANIFEST_PATH_REQUIRED');continue
  if p in out:f.append('IDENTITY_MANIFEST_DUPLICATE_PATH:'+p);continue
  if not isinstance(row.get('size'),int) or row['size']<0:f.append('IDENTITY_MANIFEST_SIZE_INVALID:'+p)
  if not _sha256(row.get('sha256')):f.append('IDENTITY_MANIFEST_SHA_INVALID:'+p)
  out[p]=row
 return out,f
def _bind(receipt,manifest,field,path,f):
 row=manifest.get(path); declared=receipt.get(field)
 if row is None:f.append('IDENTITY_REQUIRED_FILE_MISSING:'+path)
 elif declared!=row.get('sha256'):f.append('IDENTITY_DECLARED_DIGEST_MISMATCH:'+field)
def derive_identity(candidate,receipt):
 cid=candidate.get('candidate_id'); f=[]
 if not isinstance(receipt,dict): return {'pass':False,'failures':['IDENTITY_RECEIPT_REQUIRED'],'identity_complete':False,'architecture':None,'weight_artifacts':[],'chat_template':{'status':'UNKNOWN','sha256':None}}
 if receipt.get('schema')!=IDENTITY_SCHEMA:f.append('IDENTITY_RECEIPT_SCHEMA_MISMATCH')
 if receipt.get('candidate_id')!=cid:f.append('IDENTITY_RECEIPT_CANDIDATE_MISMATCH')
 if receipt.get('repo')!=candidate.get('repo'):f.append('IDENTITY_RECEIPT_REPO_MISMATCH')
 rev=candidate.get('immutable_revision')
 if not isinstance(rev,str) or not SHA40.fullmatch(rev):f.append('CANDIDATE_REVISION_INVALID')
 if receipt.get('requested_revision')!=rev:f.append('IDENTITY_RECEIPT_REVISION_MISMATCH')
 if receipt.get('revision_matches_pinned') is not True:f.append('IDENTITY_REVISION_NOT_PINNED')
 if receipt.get('identity_complete') is not True:f.append('IDENTITY_RECEIPT_NOT_COMPLETE')
 if not _sha256(receipt.get('file_manifest_sha256')):f.append('IDENTITY_MANIFEST_DIGEST_INVALID')
 manifest,mf=_manifest_map(receipt);f+=mf
 _bind(receipt,manifest,'config_json_sha256','config.json',f);_bind(receipt,manifest,'tokenizer_json_sha256','tokenizer.json',f)
 if 'tokenizer_config.json' in manifest:_bind(receipt,manifest,'tokenizer_config_json_sha256','tokenizer_config.json',f)
 chatrow=manifest.get('chat_template.jinja')
 if chatrow is None:
  if receipt.get('chat_template_jinja_sha256') not in (None,''):f.append('CHAT_TEMPLATE_DECLARED_BUT_ABSENT_FROM_MANIFEST')
  chat={'status':'ABSENT_FROM_MANIFEST','sha256':None}
 else:
  csha=chatrow.get('sha256')
  if not _sha256(csha):f.append('CHAT_TEMPLATE_SHA_INVALID')
  if receipt.get('chat_template_jinja_sha256')!=csha:f.append('CHAT_TEMPLATE_DECLARED_DIGEST_MISMATCH')
  chat={'status':'PRESENT_BOUND_SHA','sha256':csha}
 weights=[{'path':p,'sha256':r.get('sha256'),'size':r.get('size')} for p,r in sorted(manifest.items()) if p.endswith('.safetensors')]
 if not weights:f.append('WEIGHT_ARTIFACT_REQUIRED')
 if any(not _sha256(r.get('sha256')) for r in weights):f.append('WEIGHT_ARTIFACT_SHA_INVALID')
 config=receipt.get('config');tc=config.get('text_config') if isinstance(config,dict) else None
 if not isinstance(tc,dict):f.append('QWEN35_TEXT_CONFIG_REQUIRED');arch=None
 else:
  arch={k:tc.get(k) for k in REQUIRED_TEXT_ARCH}
  for k,e in REQUIRED_TEXT_ARCH.items():
   if tc.get(k)!=e:f.append('QWEN35_TEXT_ARCH_MISMATCH:'+k)
 return {'pass':not f,'failures':sorted(set(f)),'identity_complete':not f,'file_manifest_sha256':receipt.get('file_manifest_sha256'),'architecture_adapter':'QWEN3_5_TEXT_CONFIG/v1','architecture':arch,'weight_artifacts':weights,'chat_template':chat}
def derive_loader(candidate,receipt):
 cid=candidate.get('candidate_id');f=[]
 if not isinstance(receipt,dict):return {'pass':False,'failures':['LOADER_RECEIPT_REQUIRED'],'loader_consumption_observed':False,'consumed_identity_match':'UNKNOWN_NO_RECEIPT'}
 if receipt.get('schema')!=LOADER_SCHEMA:f.append('LOADER_RECEIPT_SCHEMA_MISMATCH')
 if receipt.get('candidate_id')!=cid:f.append('LOADER_RECEIPT_CANDIDATE_MISMATCH')
 if receipt.get('loader_consumption_observed') is not True:f.append('LOADER_CONSUMPTION_NOT_OBSERVED')
 ld=receipt.get('local_dir');rev=candidate.get('immutable_revision')
 if not isinstance(ld,str) or not isinstance(rev,str) or not ld.rstrip('/').endswith('/'+rev):f.append('LOADER_LOCAL_DIR_REVISION_MISMATCH')
 strong=receipt.get('consumed_identity')
 if isinstance(strong,dict) and strong.get('verified') is True:
  req=('file_manifest_sha256','weight_artifact_sha256s','tokenizer_json_sha256','config_json_sha256')
  if all(strong.get(k) for k in req):consumed='VERIFIED_BOUND_BYTES'
  else:f.append('CONSUMED_IDENTITY_VERIFIED_BUT_INCOMPLETE');consumed='UNKNOWN_INCOMPLETE_BOUND_BYTES'
 else:consumed='UNKNOWN_UNBOUND_BYTES'
 return {'pass':not f,'failures':sorted(set(f)),'loader_consumption_observed':not f,'consumed_identity_match':consumed}
def adjudicate(registry,receipt_loader:Callable[[str],Any]):
 f=[]
 if not isinstance(registry,dict):registry={};f.append('REGISTRY_OBJECT_REQUIRED')
 if registry.get('schema')!=REGISTRY_SCHEMA:f.append('REGISTRY_SCHEMA_MISMATCH')
 if registry.get('selected_candidate') is not None:f.append('SOURCE_REGISTRY_CANNOT_SELECT_WINNER')
 if registry.get('selection_status')!='UNRESOLVED_MATCHED_PILOT_AND_CONSUMED_IDENTITY_REQUIRED':f.append('SELECTION_STATUS_MUST_REMAIN_UNRESOLVED')
 cs=registry.get('candidates');seen={};derived={}
 if not isinstance(cs,list):f.append('CANDIDATES_REQUIRED');cs=[]
 for c in cs:
  if not isinstance(c,dict):f.append('CANDIDATE_OBJECT_REQUIRED');continue
  cid=c.get('candidate_id')
  if not isinstance(cid,str):f.append('CANDIDATE_ID_REQUIRED');continue
  if cid in seen:f.append('DUPLICATE_CANDIDATE:'+cid);continue
  seen[cid]=c;p=PINNED.get(cid)
  if p:
   if c.get('candidate_role')!=p['role']:f.append('PINNED_ROLE_MISMATCH:'+cid)
   if c.get('repo')!=p['repo']:f.append('PINNED_REPO_MISMATCH:'+cid)
   if c.get('immutable_revision')!=p['revision']:f.append('PINNED_REVISION_MISMATCH:'+cid)
  for key in ('runtime_credit','jspace_credit','training_credit','checkpoint_winner_credit'):
   if c.get(key)!=0:f.append('CREDIT_MUST_BE_ZERO:'+cid+':'+key)
  ip=c.get('checkpoint_identity_receipt');lp=c.get('loader_receipt')
  ir=receipt_loader(ip) if isinstance(ip,str) else None;lr=receipt_loader(lp) if isinstance(lp,str) else None
  identity=derive_identity(c,ir) if ip else {'pass':False,'failures':['IDENTITY_RECEIPT_NOT_DECLARED'],'identity_complete':False,'architecture':None,'weight_artifacts':[],'chat_template':{'status':'UNKNOWN','sha256':None}}
  loader=derive_loader(c,lr) if lp else {'pass':False,'failures':['LOADER_RECEIPT_NOT_DECLARED'],'loader_consumption_observed':False,'consumed_identity_match':'UNKNOWN_NO_RECEIPT'}
  expected_part=bool(identity['pass'] and loader['pass'])
  if c.get('matched_evaluation_participation_eligible') is not expected_part:f.append('MATCHED_PARTICIPATION_DECLARATION_MISMATCH:'+cid)
  role=c.get('candidate_role');expected_role=role in {'TARGET_MEASURED','TARGET_EXTERNAL_UNMEASURED'}
  if c.get('final_winner_role_eligible') is not expected_role:f.append('FINAL_WINNER_ROLE_DECLARATION_MISMATCH:'+cid)
  if role=='TARGET_MEASURED' and c.get('model_specific_measurements_observed') is not True:f.append('MEASURED_TARGET_MEASUREMENTS_REQUIRED:'+cid)
  if role=='CONTROL' and c.get('final_winner_role_eligible') is not False:f.append('CONTROL_CANNOT_BE_FINAL_WINNER:'+cid)
  claims=c.get('external_claims')
  if claims is not None:
   if not isinstance(claims,dict):f.append('EXTERNAL_CLAIMS_OBJECT_REQUIRED:'+cid)
   elif claims.get('clay_selection_credit')!=0:f.append('MODEL_CARD_CLAIM_CANNOT_MINT_SELECTION_CREDIT:'+cid)
  derived[cid]={'identity':identity,'loader':loader}
 for cid in PINNED:
  if cid not in seen:f.append('MISSING_PINNED_CANDIDATE:'+cid)
 contract=registry.get('matched_pilot_contract')
 if not isinstance(contract,dict):f.append('MATCHED_PILOT_CONTRACT_REQUIRED');contract={}
 for key in ('same_training_token_budget','same_example_budget','same_optimizer_family','same_hyperparameter_search_budget','same_corpus_revision','same_calibration_validation_split','separate_low_refusal_and_cognition_retention_axes','separate_jspace_causal_axis'):
  if contract.get(key) is not True:f.append('MATCHING_REQUIRED:'+key)
 if contract.get('holdout_seen_during_selection') is not False:f.append('HOLDOUT_LEAK_FORBIDDEN')
 if contract.get('matched_pilot_executed') is not False:f.append('MATCHED_PILOT_MUST_REMAIN_UNEXECUTED_IN_SOURCE_REGISTRY')
 b=registry.get('execution_boundary')
 if not isinstance(b,dict):f.append('EXECUTION_BOUNDARY_REQUIRED')
 else:
  for key in ('provider_preflight_performed','provider_credentials_consumed','training_performed','paid_job_authorized','together_job_authorized'):
   if b.get(key) is not False:f.append('EXECUTION_MUST_REMAIN_FALSE:'+key)
  if b.get('mode')!='FREE_ONLY':f.append('EXECUTION_MODE_MUST_BE_FREE_ONLY')
 f=sorted(set(f))
 return {'schema':GATE_SCHEMA,'pass':not f,'failures':f,'registry_valid':not f,'selection_ready':False,'checkpoint_winner':None,'derived_candidates':derived,'runtime_credit_minted':False,'jspace_credit_minted':False,'training_credit_minted':False,'checkpoint_winner_credit_minted':False,'evidence_boundary':'Source/receipt integrity only. Loader v1 proves load execution but not exact consumed bytes. A matched pilot and bound consumed identity remain required before any checkpoint winner can be selected.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--registry',default='research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v4.json');ap.add_argument('--repo-root',default='.');a=ap.parse_args();root=Path(a.repo_root).resolve();reg=json.loads((root/a.registry).read_text())
 def loader(rel):return json.loads((root/rel).read_text())
 r=adjudicate(reg,loader);print(json.dumps(r,sort_keys=True,indent=2));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
