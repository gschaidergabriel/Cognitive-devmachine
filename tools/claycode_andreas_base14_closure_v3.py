#!/usr/bin/env python3
"""Atomic evidence-gated closure of ClayCode BASE14 on the registered Andreas Ubuntu host.

This is the convergence command.  It starts only from a clean checkout, binds every
receipt to one git HEAD and one locally registered host fingerprint, runs all production
component/application/H2 discriminators fresh, emits the strict target receipt, and only
then promotes workspace package states.  No failed or missing phase can be promoted.

The script intentionally does not git-commit its generated receipts/promotion.  The local
single-writer/Claude Code organ may review and commit the resulting diff after the run.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from claycode_target_host_identity import verify,DEFAULT_REGISTRATION,TARGET_HOST

WORKSPACE=ROOT/'research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json'
STRICT_TARGET=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json'
PROMOTION=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE14_PROMOTION.json'
STRICT_APPS=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_APPLICATIONS_STRICT.json'
H2_TARGET=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_FULL_FRANK_H2_HANDOFF.json'
RUNTIME_V04=ROOT/'research_entity/claycode/autonomous/BASE_RUNTIME_V04_HARDENING_RECEIPT.json'
BRIDGE=ROOT/'research_entity/claycode/autonomous/BASE_COMPILER_MAINLINE_RUNTIME_BRIDGE_RECEIPT.json'
AUDIT=ROOT/'research_entity/claycode/autonomous/BASE_RELEASE_AUDIT_RECEIPT.json'
MANIFEST=ROOT/'research_entity/claycode/CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json'
V7='research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
STRICT_LALR='research_entity/claycode/target_receipts/STRICT_LALR_D_V7_TARGET_RECEIPT.json'
APP_ORDER=['CLI','HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','COMPILER_TOOL','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX','FRANK_COMPONENT','FULL_FRANK_HANDOFF']
WP_NAMES=[
 'CC-WP-01-SPEC-FREEZE','CC-WP-02-PARSER-CANON','CC-WP-03-IR-TYPES','CC-WP-04-TYPE-EFFECT','CC-WP-05-EVALUATOR','CC-WP-06-COMPILER-LOWERING','CC-WP-07-RUNTIME-ABI-FFI','CC-WP-08-STDLIB-SDK','CC-WP-09-CONCURRENCY-MEMORY','CC-WP-10-GENERAL-APP-SUITE','CC-WP-11-FUZZ-CONFORMANCE','CC-WP-12-CORPUS-HELDOUT','CC-WP-13-HARNESS-HANDOFF','CC-WP-14-BASE-AUDIT']
PHASES=[
 ('strict_lalr',[sys.executable,'tools/claycode_strict_lalr_probe.py','--grammar',V7,'--output',STRICT_LALR]),
 ('frontend',[sys.executable,'tools/claycode_base_frontend_validation.py','--grammar',V7,'--output','research_entity/claycode/autonomous/BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json']),
 ('canonicalizer',[sys.executable,'tools/claycode_base_canonicalizer_validation.py']),
 ('typed_ir',[sys.executable,'tools/claycode_wp03_typed_ir_validation.py']),
 ('type_effect',[sys.executable,'tools/claycode_base_effect_pipeline.py','--self-test','--output','research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json']),
 ('evaluator_lowering',[sys.executable,'tools/claycode_base_pure_toolchain_validation.py']),
 ('package_link',[sys.executable,'tools/claycode_base_package_validation.py']),
 ('runtime',[sys.executable,'tools/claycode_base_runtime_validation.py']),
 ('runtime_v04',[sys.executable,'tools/claycode_runtime_v04_hardening_validation.py']),
 ('resource_lifetime',[sys.executable,'tools/claycode_base_resource_lifetime_validation.py']),
 ('compiler_runtime_bridge',[sys.executable,'tools/claycode_effect_mainline_runtime_bridge.py']),
 ('fuzz_conformance',[sys.executable,'tools/claycode_base_fuzz_conformance.py']),
 ('corpus_heldout',[sys.executable,'tools/claycode_base_corpus_generator.py']),
 ('strict_apps',[sys.executable,'tools/claycode_andreas_strict_application_adjudicator.py']),
 ('full_frank_h2',[sys.executable,'tools/claycode_andreas_h2_full_handoff.py']),
]

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path:Path)->dict[str,Any]:return json.loads(path.read_text(encoding='utf-8'))
def write(path:Path,obj:dict[str,Any]):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True,check=False)
def clean_checkout()->tuple[bool,list[str]]:
 cp=git('status','--porcelain');lines=cp.stdout.splitlines();return cp.returncode==0 and not lines,lines[:100]
def run(name:str,argv:list[str],timeout:int=1200)->dict[str,Any]:
 t=time.monotonic()
 try:
  cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,check=False,timeout=timeout)
  return {'phase':name,'argv':argv,'returncode':cp.returncode,'pass':cp.returncode==0,'duration_s':round(time.monotonic()-t,6),'stdout_tail':cp.stdout[-4000:],'stderr_tail':cp.stderr[-4000:]}
 except Exception as exc:return {'phase':name,'argv':argv,'returncode':None,'pass':False,'duration_s':round(time.monotonic()-t,6),'exception':f'{type(exc).__name__}:{exc}'}
def evidence(phase_rows:dict[str,dict],*names:str)->list[dict[str,Any]]:
 return [{'phase':n,'argv':phase_rows[n]['argv'],'returncode':phase_rows[n]['returncode']} for n in names]
def component_wp_rows(phases:dict[str,dict],apps_pass:bool,h2_pass:bool)->dict[str,dict]:
 spec={
  WP_NAMES[1]:('strict_lalr','frontend','canonicalizer'),
  WP_NAMES[2]:('typed_ir',),
  WP_NAMES[3]:('type_effect',),
  WP_NAMES[4]:('evaluator_lowering',),
  WP_NAMES[5]:('evaluator_lowering','package_link'),
  WP_NAMES[6]:('runtime','runtime_v04','compiler_runtime_bridge'),
  WP_NAMES[7]:('runtime','runtime_v04','resource_lifetime','compiler_runtime_bridge'),
  WP_NAMES[8]:('runtime','runtime_v04','resource_lifetime','fuzz_conformance'),
  WP_NAMES[9]:('strict_apps',),
  WP_NAMES[10]:('fuzz_conformance',),
  WP_NAMES[11]:('corpus_heldout',),
  WP_NAMES[12]:('full_frank_h2','compiler_runtime_bridge'),
 }
 out={}
 for wp,names in spec.items():
  ok=all(phases[n]['pass'] for n in names)
  if wp==WP_NAMES[9]:ok=ok and apps_pass
  if wp==WP_NAMES[12]:ok=ok and h2_pass
  out[wp]={'pass':ok,'evidence':evidence(phases,*names),'target_host':TARGET_HOST}
 return out

def promote_workspace(strict:dict[str,Any])->dict[str,Any]:
 original=read(WORKSPACE);before=sha(WORKSPACE);w=copy.deepcopy(original)
 if (w.get('work_packages') or {}).get(WP_NAMES[0],{}).get('status')!='PASS':raise RuntimeError('WP01_NOT_PASS')
 for wp in WP_NAMES[1:13]:
  row=strict['work_packages'][wp]
  if row.get('pass') is not True:raise RuntimeError('TARGET_WP_NOT_PASS:'+wp)
  dst=w['work_packages'][wp];dst['status']='PASS';dst['receipts']=[str(STRICT_TARGET.relative_to(ROOT))];dst['target_host']=TARGET_HOST
 w['application_acceptance']['passed']=APP_ORDER
 w['gate_status']='NOT_PASS';w['general_purpose_gate_status']='NOT_PASS';w['last_updated']='2026-08-09'
 write(WORKSPACE,w)
 audit1=run('wp14_audit_prepass',[sys.executable,'tools/claycode_base_release_audit.py'])
 if not AUDIT.exists():raise RuntimeError('WP14_AUDIT_RECEIPT_MISSING')
 ad=read(AUDIT)
 if ad.get('wp14_pass_eligible') is not True or ad.get('release_manifest_created') is not True:raise RuntimeError('WP14_NOT_ELIGIBLE:'+repr(ad.get('missing_or_blocking')))
 w=read(WORKSPACE);w['work_packages'][WP_NAMES[13]]['status']='PASS';w['work_packages'][WP_NAMES[13]]['receipts']=[str(AUDIT.relative_to(ROOT)),str(MANIFEST.relative_to(ROOT))];w['work_packages'][WP_NAMES[13]]['target_host']=TARGET_HOST;w['gate_status']='PASS';w['general_purpose_gate_status']='PASS';w['status']='BASE_PASS';write(WORKSPACE,w)
 audit2=run('wp14_audit_final',[sys.executable,'tools/claycode_base_release_audit.py'])
 final_audit=read(AUDIT);final_manifest=read(MANIFEST)
 if final_audit.get('overall_pass') is not True or final_audit.get('release_manifest_created') is not True:raise RuntimeError('FINAL_AUDIT_NOT_PASS')
 # Stamp the already evidence-generated manifest as promoted only after WP14 itself is PASS.
 final_manifest['status']='PASS';final_manifest['promoted_by']='tools/claycode_andreas_base14_closure_v3.py';final_manifest['target_host']=TARGET_HOST;final_manifest['promotion_receipt']=str(PROMOTION.relative_to(ROOT));write(MANIFEST,final_manifest)
 return {'workspace_sha256_before':before,'workspace_sha256_after':sha(WORKSPACE),'audit_prepass':audit1,'audit_final':audit2,'audit_sha256':sha(AUDIT),'manifest_sha256':sha(MANIFEST)}

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--registration',type=Path,default=DEFAULT_REGISTRATION);ap.add_argument('--no-promote',action='store_true');a=ap.parse_args()
 ok,host=verify(a.registration)
 if not ok:print(json.dumps({'error':'TARGET_HOST_IDENTITY_NOT_VERIFIED','details':host},indent=2));return 3
 clean,dirty=clean_checkout()
 if not clean:print(json.dumps({'error':'CLEAN_CHECKOUT_REQUIRED','dirty':dirty},indent=2));return 4
 head=git('rev-parse','HEAD').stdout.strip();started=datetime.now(timezone.utc).isoformat();rows=[];phase_map={}
 for name,argv in PHASES:
  row=run(name,argv);rows.append(row);phase_map[name]=row
  if not row['pass']:break
 if len(rows)!=len(PHASES) or not all(r['pass'] for r in rows):
  report={'schema_version':'3.0','target_host':TARGET_HOST,'repository_commit':head,'host_fingerprint':host.get('host_fingerprint',{}),'collector_clean_target_attestation_pass':True,'started_at':started,'phases':rows,'overall_pass':False,'unresolved_language_counterexamples':['PHASE_FAILURE'],'automatic_promotion':False,'authority_invariant':'model output != execution authority'};write(STRICT_TARGET,report);print(json.dumps({'overall_pass':False,'failed_phase':rows[-1]['phase'] if rows else None,'receipt':str(STRICT_TARGET.relative_to(ROOT))}));return 2
 # All fresh phase commands passed. Now validate their structured receipts.
 apps=read(STRICT_APPS);h2=read(H2_TARGET);rv4=read(RUNTIME_V04);bridge=read(BRIDGE)
 merged_apps=copy.deepcopy(apps.get('applications') or {});merged_apps['FULL_FRANK_HANDOFF']=copy.deepcopy(h2.get('application') or {})
 apps_pass=set(merged_apps)==set(APP_ORDER) and all((merged_apps.get(x) or {}).get('pass') is True and (merged_apps.get(x) or {}).get('authority_boundary_preserved') is True for x in APP_ORDER)
 h2_pass=h2.get('pass') is True and h2.get('repository_commit')==head and (h2.get('frank_handoff') or {}).get('pass') is True
 rv4_pass=rv4.get('pass') is True;bridge_pass=bridge.get('pass') is True
 wp=component_wp_rows(phase_map,apps_pass,h2_pass)
 all_wp=all(x.get('pass') is True for x in wp.values())
 overall=all_wp and apps_pass and h2_pass and rv4_pass and bridge_pass
 strict={'schema_version':'3.0','target_host':TARGET_HOST,'repository_commit':head,'host_fingerprint':host.get('host_fingerprint',{}),'collector_clean_target_attestation_pass':True,'started_at':started,'completed_at':datetime.now(timezone.utc).isoformat(),'compiler_runtime':{'runtime_v04_hardening_pass':rv4_pass,'compiler_mainline_runtime_bridge_pass':bridge_pass,'runtime_receipt_sha256':sha(RUNTIME_V04),'bridge_receipt_sha256':sha(BRIDGE)},'runtime_v04_hardening_pass':rv4_pass,'compiler_mainline_runtime_bridge_pass':bridge_pass,'work_packages':wp,'applications':merged_apps,'frank_handoff':h2.get('frank_handoff') or {},'unresolved_language_counterexamples':[] if h2_pass else ['FULL_ACTIVE_ASSEMBLY_H2'],'phases':rows,'overall_pass':overall,'automatic_promotion':False,'authority_invariant':'model output != execution authority'};write(STRICT_TARGET,strict)
 if not overall:print(json.dumps({'overall_pass':False,'apps_pass':apps_pass,'h2_pass':h2_pass,'all_wp':all_wp,'receipt':str(STRICT_TARGET.relative_to(ROOT))}));return 2
 promotion_details=None
 if not a.no_promote:
  promotion_details=promote_workspace(strict)
 promotion={'schema_version':'1.0','target_host':TARGET_HOST,'repository_parent':head,'strict_target_receipt':str(STRICT_TARGET.relative_to(ROOT)),'strict_target_receipt_sha256':sha(STRICT_TARGET),'overall_target_pass':True,'promotion_performed':not a.no_promote,'promotion':promotion_details,'final_workspace_gate_status':read(WORKSPACE).get('gate_status') if not a.no_promote else None,'final_general_purpose_gate_status':read(WORKSPACE).get('general_purpose_gate_status') if not a.no_promote else None,'authority_invariant':'model output != execution authority'};write(PROMOTION,promotion)
 print(json.dumps({'overall_pass':True,'promoted':not a.no_promote,'strict_receipt':str(STRICT_TARGET.relative_to(ROOT)),'promotion_receipt':str(PROMOTION.relative_to(ROOT)),'workspace_gate':promotion['final_workspace_gate_status']}));return 0
if __name__=='__main__':raise SystemExit(main())
