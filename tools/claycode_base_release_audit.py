#!/usr/bin/env python3
"""Fail-closed ClayCode BASE release audit and manifest eligibility checker.

This script never upgrades the workspace by itself. It produces an audit receipt and,
only when the repository already contains all required PASS states plus a valid strict
Andreas Ubuntu target acceptance receipt, materializes the general-purpose manifest.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT/'research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json'
FREEZE=ROOT/'research_entity/claycode/base/BASE_SEMANTIC_FREEZE_V1.json'
TARGET_CONTRACT=ROOT/'research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json'
TARGET=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json'
OUT=ROOT/'research_entity/claycode/autonomous/BASE_RELEASE_AUDIT_RECEIPT.json'
MANIFEST=ROOT/'research_entity/claycode/CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json'
REQ_WP=[f'CC-WP-{i:02d}-'+suffix for i,suffix in [(1,'SPEC-FREEZE'),(2,'PARSER-CANON'),(3,'IR-TYPES'),(4,'TYPE-EFFECT'),(5,'EVALUATOR'),(6,'COMPILER-LOWERING'),(7,'RUNTIME-ABI-FFI'),(8,'STDLIB-SDK'),(9,'CONCURRENCY-MEMORY'),(10,'GENERAL-APP-SUITE'),(11,'FUZZ-CONFORMANCE'),(12,'CORPUS-HELDOUT'),(13,'HARNESS-HANDOFF'),(14,'BASE-AUDIT')]]
REQ_APPS=['CLI','HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','COMPILER_TOOL','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX','FRANK_COMPONENT','FULL_FRANK_HANDOFF']
def load(path:Path)->Any:return json.loads(path.read_text(encoding='utf-8'))
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_target(obj:dict)->list[str]:
 errors=[]
 if obj.get('target_host')!='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM':errors.append('TARGET_HOST_IDENTITY')
 if obj.get('overall_pass') is not True:errors.append('TARGET_OVERALL_NOT_PASS')
 host=obj.get('host_fingerprint') or {}
 for k in ['uname','architecture','python_version','c_compiler_version']:
  if not host.get(k):errors.append('HOST_FINGERPRINT:'+k)
 wp=obj.get('work_packages') or {}
 for name in REQ_WP[1:13]:
  row=wp.get(name) or {}
  if row.get('pass') is not True:errors.append('TARGET_WP_NOT_PASS:'+name)
  if not row.get('evidence'):errors.append('TARGET_WP_NO_EVIDENCE:'+name)
 apps=obj.get('applications') or {}
 for name in REQ_APPS:
  row=apps.get(name) or {}
  if row.get('pass') is not True:errors.append('APP_NOT_PASS:'+name)
  for key in ['source_or_program_hash','semantic_or_ir_hash','compiler_runtime_version','target_artifact_hash','execution_command_or_test_id','expected','observed','negative_or_failure_path','authority_boundary_preserved']:
   if key not in row:errors.append(f'APP_FIELD_MISSING:{name}:{key}')
  if row.get('authority_boundary_preserved') is not True:errors.append('APP_AUTHORITY_BOUNDARY:'+name)
 handoff=obj.get('frank_handoff') or {}
 for key in ['pass','frozen_frank_source_hashes','claycode_source_hashes','production_chain_receipts','semantic_escape_hatches','h2_h3_handoff_ready']:
  if key not in handoff:errors.append('FRANK_HANDOFF_FIELD:'+key)
 if handoff.get('pass') is not True:errors.append('FRANK_HANDOFF_NOT_PASS')
 if handoff.get('h2_h3_handoff_ready') is not True:errors.append('FRANK_HANDOFF_NOT_READY')
 if handoff.get('semantic_escape_hatches') not in ([],0,None):errors.append('FRANK_SEMANTIC_ESCAPE_HATCH')
 if obj.get('runtime_v04_hardening_pass') is not True:errors.append('RUNTIME_V04_HARDENING_NOT_PASS')
 if obj.get('compiler_mainline_runtime_bridge_pass') is not True:errors.append('COMPILER_MAINLINE_RUNTIME_BRIDGE_NOT_PASS')
 if obj.get('collector_clean_target_attestation_pass') is not True:errors.append('COLLECTOR_TARGET_ATTESTATION_NOT_PASS')
 if obj.get('unresolved_language_counterexamples') not in ([],None):errors.append('TARGET_LANGUAGE_COUNTEREXAMPLES')
 return errors
def receipt_inventory()->list[dict]:
 base=ROOT/'research_entity/claycode';rows=[]
 for p in sorted(base.rglob('*.json')):
  n=p.name.upper()
  if not any(k in n for k in ('RECEIPT','MANIFEST','AUDIT')):continue
  rows.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
 return rows
def main()->int:
 workspace=load(WORKSPACE);freeze=load(FREEZE);contract=load(TARGET_CONTRACT)
 packages=workspace.get('work_packages') or {};package_status={name:(packages.get(name) or {}).get('status') for name in REQ_WP};missing=[]
 for name in REQ_WP[:13]:
  if package_status.get(name)!='PASS':missing.append('WORKSPACE_NOT_PASS:'+name)
 got=set(workspace.get('application_acceptance',{}).get('passed') or [])
 if got!=set(REQ_APPS):missing.extend('WORKSPACE_APP_NOT_PASS:'+x for x in sorted(set(REQ_APPS)-got))
 if freeze.get('unresolved_language_counterexamples') not in ([],None):missing.append('FREEZE_LANGUAGE_COUNTEREXAMPLES')
 target_errors=['TARGET_RECEIPT_MISSING'] if not TARGET.exists() else validate_target(load(TARGET));missing.extend(target_errors)
 eligible=not missing;inventory=receipt_inventory();audit={'schema_version':'1.1','audit':'ClayCode BASE general-purpose release eligibility','fail_closed':True,'workspace_sha256':sha(WORKSPACE),'semantic_freeze_sha256':sha(FREEZE),'target_contract_sha256':sha(TARGET_CONTRACT),'strict_target_receipt_path':str(TARGET.relative_to(ROOT)),'package_status':package_status,'target_receipt_exists':TARGET.exists(),'target_errors':target_errors,'missing_or_blocking':missing,'receipt_inventory_count':len(inventory),'receipt_inventory':inventory,'wp14_pass_eligible':eligible,'release_manifest_created':False,'overall_pass':eligible,'rule':'WP14 requires WP01..13 PASS, all ten target apps PASS, strict Andreas target receipt including runtime-v0.4+mainline bridge, zero unresolved language counterexamples and full stateful FRANK handoff'}
 if eligible:
  target=load(TARGET);manifest={'schema_version':'1.1','manifest_id':'CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST_V1','status':'PASS_ELIGIBLE_PENDING_CANONICAL_PROMOTION','workspace_sha256':audit['workspace_sha256'],'semantic_freeze_sha256':audit['semantic_freeze_sha256'],'target_receipt_sha256':sha(TARGET),'repository_commit':target.get('repository_commit'),'target_host':target.get('target_host'),'compiler_runtime':target.get('compiler_runtime'),'applications':target.get('applications'),'frank_handoff':target.get('frank_handoff'),'work_packages':{**package_status,'CC-WP-14-BASE-AUDIT':'PASS_ELIGIBLE'},'unresolved_language_counterexamples':[],'authority_invariant':'model_output != execution_authority','receipt_inventory':inventory}
  MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');audit['release_manifest_created']=True;audit['release_manifest_sha256']=sha(MANIFEST)
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'eligible':eligible,'blocking_count':len(missing),'manifest_created':audit['release_manifest_created'],'target_receipt_exists':TARGET.exists()}));return 0 if eligible else 2
if __name__=='__main__':raise SystemExit(main())
