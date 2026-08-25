#!/usr/bin/env python3
from __future__ import annotations
import re
from typing import Any
SCHEMA='CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_CANDIDATES/v1'
SHA40=re.compile(r'^[0-9a-f]{40}$'); SHA256=re.compile(r'^[0-9a-f]{64}$')
EXPECTED={
 'QWEN35_08B_BASE':('Qwen/Qwen3.5-0.8B-Base','dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68','c2b1e5a17d9c1e27685d92ed9b382911ebb99955ecd89052d1721241adfbab6c','fe000e3ed39ed12b8d2481d527d44f93c65d37e87645d2dcc80d1bf9d50d2927'),
 'QWEN35_08B_POSTTRAINED':('Qwen/Qwen3.5-0.8B','2fc06364715b967f1860aea9cf38778875588b17','04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696','5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42')}
def adjudicate(x:Any)->dict[str,Any]:
 f=[]
 if not isinstance(x,dict): x={}; f.append('OBJECT_REQUIRED')
 if x.get('schema')!=SCHEMA:f.append('SCHEMA_MISMATCH')
 if x.get('selection_status')!='UNRESOLVED_MATCHED_PILOT_REQUIRED':f.append('SELECTION_STATUS_MUST_REMAIN_UNRESOLVED')
 if x.get('selected_candidate') is not None:f.append('SOURCE_PIN_CANNOT_SELECT_WINNER')
 cs=x.get('candidates'); seen={}
 if not isinstance(cs,list):f.append('CANDIDATES_REQUIRED')
 else:
  for c in cs:
   if not isinstance(c,dict):f.append('CANDIDATE_OBJECT_REQUIRED');continue
   cid=c.get('candidate_id');seen[cid]=c
   if cid not in EXPECTED:f.append('UNKNOWN_CANDIDATE:'+str(cid));continue
   repo,rev,w,t=EXPECTED[cid]
   if c.get('repo')!=repo:f.append('REPO_MISMATCH:'+cid)
   if c.get('revision')!=rev or not SHA40.fullmatch(str(c.get('revision',''))):f.append('REVISION_MISMATCH:'+cid)
   if c.get('weights_sha256')!=w or not SHA256.fullmatch(str(c.get('weights_sha256',''))):f.append('WEIGHTS_SHA_MISMATCH:'+cid)
   if c.get('tokenizer_sha256')!=t or not SHA256.fullmatch(str(c.get('tokenizer_sha256',''))):f.append('TOKENIZER_SHA_MISMATCH:'+cid)
   if c.get('source_observed') is not True:f.append('SOURCE_OBSERVATION_REQUIRED:'+cid)
   if c.get('loader_consumption_observed') is not False:f.append('LOADER_CONSUMPTION_MUST_REMAIN_UNOBSERVED:'+cid)
   for k in ('runtime_credit','jspace_credit','training_credit'):
    if c.get(k)!=0:f.append('CREDIT_MUST_BE_ZERO:'+cid+':'+k)
 for cid in EXPECTED:
  if cid not in seen:f.append('MISSING_CANDIDATE:'+cid)
 p=x.get('matched_pilot_contract')
 if not isinstance(p,dict):f.append('MATCHED_PILOT_CONTRACT_REQUIRED')
 else:
  for k in ('same_training_token_budget','same_example_budget','same_optimizer_family','same_hyperparameter_search_budget','same_corpus_revision','same_calibration_validation_split'):
   if p.get(k) is not True:f.append('MATCHING_REQUIRED:'+k)
  if p.get('holdout_seen_during_selection') is not False:f.append('HOLDOUT_LEAK_FORBIDDEN')
 e=x.get('execution_boundary')
 if not isinstance(e,dict):f.append('EXECUTION_BOUNDARY_REQUIRED')
 else:
  for k in ('provider_preflight_performed','provider_credentials_consumed','training_performed','paid_job_authorized','together_job_authorized'):
   if e.get(k) is not False:f.append('EXECUTION_MUST_REMAIN_FALSE:'+k)
 return {'schema':'CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v1','pass':not f,'failures':sorted(set(f)),'runtime_credit_minted':False,'training_credit_minted':False,'selection_performed':False,'evidence_boundary':'Static source-identity and matched-pilot-contract gate only.'}
