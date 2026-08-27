#!/usr/bin/env python3
"""Unified one-command ClayCode BASE14 closure for the registered Andreas Ubuntu host.

Evidence graph, all at one git parent and one verified physical host:
  registered host fingerprint
    -> V2 component collector (temporary legacy marker derived from verified identity)
    -> evidence-aware target gate
    -> full FRANK H1/H2/H3 + packet-score + GRT target finalizer
    -> ten real target application receipts
    -> strict dual-proof application adjudication (host behavior + Clay effect chain)
    -> strict Andreas acceptance assembler
    -> independent WP14 receipt auditor
    -> workspace 14/14 promotion only if BOTH final auditors say PASS.

No target execution can be substituted by hosted CI. No failed phase is promoted. This
script writes but does not git-commit the resulting receipts/workspace; the local
single-writer organ should review and commit the diff atomically.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from claycode_target_host_identity import DEFAULT_REGISTRATION, TARGET_HOST, verify

TARGET='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
WORKSPACE=ROOT/'research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json'
COLLECTOR=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_V2.json'
TARGET_GATE=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_TARGET_GATE.json'
FULL_FRANK=ROOT/'research_entity/claycode/target_receipts/FULL_FRANK_HANDOFF_RECEIPT.json'
STRICT_APPS=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_APPLICATIONS_STRICT.json'
STRICT_ACCEPT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json'
MANIFEST=ROOT/'CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json'
PROMOTION=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE14_PROMOTION_V5.json'
APP_DIR=ROOT/'research_entity/claycode/target_receipts/apps'
APP_ORDER=['CLI','HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','COMPILER_TOOL','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX','FRANK_COMPONENT','FULL_FRANK_HANDOFF']
WP_ORDER=['CC-WP-01-SPEC-FREEZE','CC-WP-02-PARSER-CANON','CC-WP-03-IR-TYPES','CC-WP-04-TYPE-EFFECT','CC-WP-05-EVALUATOR','CC-WP-06-COMPILER-LOWERING','CC-WP-07-RUNTIME-ABI-FFI','CC-WP-08-STDLIB-SDK','CC-WP-09-CONCURRENCY-MEMORY','CC-WP-10-GENERAL-APP-SUITE','CC-WP-11-FUZZ-CONFORMANCE','CC-WP-12-CORPUS-HELDOUT','CC-WP-13-HARNESS-HANDOFF','CC-WP-14-BASE-AUDIT']

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path:Path)->dict[str,Any]:
 v=json.loads(path.read_text(encoding='utf-8'))
 if not isinstance(v,dict):raise RuntimeError('NOT_OBJECT:'+str(path))
 return v
def write(path:Path,obj:dict[str,Any]):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def git(*args:str):return subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True,check=False)
def initial_clean()->tuple[bool,list[str]]:
 cp=git('status','--porcelain');return cp.returncode==0 and not cp.stdout.strip(),cp.stdout.splitlines()[:100]
def run(name:str,argv:list[str],env:dict[str,str],timeout:int=1800)->dict[str,Any]:
 t=time.monotonic()
 try:
  cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,check=False,timeout=timeout,env=env)
  return {'name':name,'argv':argv,'returncode':cp.returncode,'pass':cp.returncode==0,'duration_s':round(time.monotonic()-t,6),'stdout_tail':cp.stdout[-8000:],'stderr_tail':cp.stderr[-8000:]}
 except Exception as exc:return {'name':name,'argv':argv,'returncode':None,'pass':False,'duration_s':round(time.monotonic()-t,6),'exception':f'{type(exc).__name__}:{exc}'}
def file_pass(path:Path,key:str='pass')->bool:
 try:return read(path).get(key) is True
 except Exception:return False

def promote_workspace(head:str,host:dict[str,Any],strict:dict[str,Any],manifest:dict[str,Any])->dict[str,Any]:
 if strict.get('overall_pass') is not True:raise RuntimeError('STRICT_ACCEPTANCE_NOT_PASS')
 if manifest.get('general_purpose_gate_pass') is not True or manifest.get('claycode_release_gate_pass') is not True or manifest.get('failed_work_packages') not in ([],None):raise RuntimeError('WP14_MANIFEST_NOT_PASS')
 wp_manifest=manifest.get('work_packages') or {}
 for wp in WP_ORDER:
  if (wp_manifest.get(wp) or {}).get('pass') is not True:raise RuntimeError('MANIFEST_WP_NOT_PASS:'+wp)
 workspace=read(WORKSPACE);before=sha(WORKSPACE)
 if (workspace.get('work_packages') or {}).get(WP_ORDER[0],{}).get('status')!='PASS':raise RuntimeError('WORKSPACE_WP01_NOT_PASS')
 for wp in WP_ORDER:
  dst=workspace['work_packages'][wp];dst['status']='PASS';dst['target_host']=TARGET;dst['promotion_receipts']=[str(STRICT_ACCEPT.relative_to(ROOT)),str(MANIFEST.relative_to(ROOT))]
 workspace['application_acceptance']['passed']=APP_ORDER
 workspace['gate_status']='PASS';workspace['general_purpose_gate_status']='PASS';workspace['status']='BASE_PASS';workspace['last_updated']='2026-08-09'
 workspace.setdefault('live_claims',[]).append({'id':'BASE14-TARGET-PASS-V5','class':'TARGET_EXECUTION_RELEASE_STATE','status':'CURRENT','claim':'All fourteen BASE work packages and all ten mandatory applications passed the dual final audit on the registered Andreas Ubuntu target.','evidence':[str(STRICT_ACCEPT.relative_to(ROOT)),str(MANIFEST.relative_to(ROOT)),str(FULL_FRANK.relative_to(ROOT))],'repository_parent':head,'host_fingerprint':host.get('host_fingerprint',{})})
 workspace.setdefault('completed_receipts',[]).extend([str(STRICT_ACCEPT.relative_to(ROOT)),str(MANIFEST.relative_to(ROOT)),str(FULL_FRANK.relative_to(ROOT))])
 # de-duplicate without reordering historical receipts
 workspace['completed_receipts']=list(dict.fromkeys(workspace['completed_receipts']))
 write(WORKSPACE,workspace)
 return {'workspace_sha256_before':before,'workspace_sha256_after':sha(WORKSPACE),'gate_status':workspace['gate_status'],'general_purpose_gate_status':workspace['general_purpose_gate_status'],'formal_pass_count':sum(1 for x in workspace['work_packages'].values() if x.get('status')=='PASS')}

def main()->int:
 host_ok,host=verify(DEFAULT_REGISTRATION)
 if not host_ok or host.get('target_host')!=TARGET_HOST or TARGET_HOST!=TARGET:
  print(json.dumps({'error':'REGISTERED_ANDREAS_TARGET_NOT_VERIFIED','host':host},ensure_ascii=False,indent=2));return 3
 clean,dirty=initial_clean()
 if not clean:
  print(json.dumps({'error':'INITIAL_TOOLCHAIN_CHECKOUT_NOT_CLEAN','dirty':dirty},ensure_ascii=False,indent=2));return 4
 head=git('rev-parse','HEAD').stdout.strip();env=dict(os.environ);env['CLAYCODE_TARGET_HOST_ID']=TARGET
 rows=[]
 with tempfile.TemporaryDirectory(prefix='claycode-target-trust-') as td:
  marker=Path(td)/'ANDREAS_TARGET_HOST';marker.write_text(TARGET+'\n',encoding='utf-8')
  steps=[
   ('v2_component_collector',[sys.executable,'tools/claycode_base_andreas_target_runner_v2.py','--marker',str(marker)]),
   ('target_gate_independent',[sys.executable,'tools/claycode_andreas_ubuntu_target_gate_v2.py']),
   ('full_frank_h2_h3_finalizer',[sys.executable,'tools/claycode_full_frank_target_finalizer.py']),
   ('real_application_receipts',[sys.executable,'tools/claycode_andreas_application_acceptance.py']),
   ('strict_dual_application_adjudicator',[sys.executable,'tools/claycode_andreas_strict_application_adjudicator.py']),
   ('strict_acceptance_assembler',[sys.executable,'tools/claycode_andreas_ubuntu_acceptance_assembler.py']),
   ('independent_wp14_audit',[sys.executable,'tools/claycode_base_wp14_audit.py']),
  ]
  for name,argv in steps:
   row=run(name,argv,env);rows.append(row)
   if not row['pass']:
    break
 # Validate outputs independently; a process exit alone is not evidence.
 validations={
  'collector_components_pass':file_pass(COLLECTOR,'component_gates_pass'),
  'collector_runtime_v04_pass':file_pass(COLLECTOR,'runtime_v04_hardening_pass'),
  'collector_compiler_mainline_bridge_pass':file_pass(COLLECTOR,'compiler_mainline_runtime_bridge_pass'),
  'target_gate_components_pass':file_pass(TARGET_GATE,'target_component_steps_pass'),
  'full_frank_pass':file_pass(FULL_FRANK),
  'strict_apps_ten_pass':False,
  'strict_acceptance_pass':file_pass(STRICT_ACCEPT,'overall_pass'),
  'wp14_general_purpose_pass':file_pass(MANIFEST,'general_purpose_gate_pass'),
  'wp14_claycode_release_pass':file_pass(MANIFEST,'claycode_release_gate_pass'),
  'wp14_zero_failed_packages':False,
  'all_ten_per_app_receipts_pass':False,
 }
 try:
  sa=read(STRICT_APPS);apps=sa.get('applications') or {};validations['strict_apps_ten_pass']=set(apps)==set(APP_ORDER) and all((apps.get(x) or {}).get('pass') is True for x in APP_ORDER)
 except Exception:pass
 try:
  m=read(MANIFEST);validations['wp14_zero_failed_packages']=m.get('failed_work_packages') in ([],None)
 except Exception:pass
 per_app=[]
 for app in APP_ORDER:
  p=APP_DIR/f'{app}.json';ok=False
  try:
   d=read(p);ok=d.get('pass') is True and d.get('target_host')==TARGET and d.get('evidence_class')=='ANDREAS_UBUNTU_REAL_APPLICATION' and d.get('model_output_is_execution_authority') is False
  except Exception:pass
  per_app.append({'app':app,'path':str(p.relative_to(ROOT)),'pass':ok,'sha256':sha(p) if p.exists() else None})
 validations['all_ten_per_app_receipts_pass']=all(x['pass'] for x in per_app)
 all_processes=len(rows)==7 and all(x['pass'] for x in rows)
 overall=all_processes and all(validations.values())
 promotion_detail=None
 if overall:
  promotion_detail=promote_workspace(head,host,read(STRICT_ACCEPT),read(MANIFEST))
 report={'schema_version':'5.0','created_at':datetime.now(timezone.utc).isoformat(),'target_host':TARGET,'registered_host_fingerprint':host.get('host_fingerprint',{}),'repository_parent':head,'steps':rows,'validations':validations,'per_application_receipts':per_app,'overall_pass':overall,'promotion_performed':overall,'promotion':promotion_detail,'authority_invariant':'model output != execution authority','rule':'Workspace 14/14 promotion requires process PASS plus independent structured PASS from V2 collector, target-gate, full H2/H3 FRANK finalizer, ten strict apps, strict acceptance assembler and WP14 auditor.'}
 write(PROMOTION,report)
 print(json.dumps({'overall_pass':overall,'formal_pass_count':promotion_detail.get('formal_pass_count') if promotion_detail else None,'failed_validations':[k for k,v in validations.items() if not v],'last_step':rows[-1]['name'] if rows else None,'promotion_receipt':str(PROMOTION.relative_to(ROOT))},ensure_ascii=False))
 return 0 if overall else 2
if __name__=='__main__':raise SystemExit(main())
