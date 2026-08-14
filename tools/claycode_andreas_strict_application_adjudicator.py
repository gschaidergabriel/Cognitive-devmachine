#!/usr/bin/env python3
"""Strict target app adjudicator: host behavior AND Clay compiler/effect path must pass.

By default exit 0 means all ten target application classes pass.  With
--allow-pending-full-frank, exit 0 is allowed only for the explicit 9/10 intermediate
state where every class except FULL_FRANK_HANDOFF passes; the report itself remains
pass=false and therefore cannot be mistaken for release acceptance.
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import claycode_base_target_application_suite_v2 as host_suite
import claycode_andreas_effect_app_chain as effect_suite
from claycode_target_host_identity import verify,DEFAULT_REGISTRATION,TARGET_HOST
HOST_RECEIPT=ROOT/'research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json'
EFFECT_RECEIPT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_EFFECT_APP_CHAIN.json'
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_APPLICATIONS_STRICT.json'
EFFECTFUL={'HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX'}
ORDER=['CLI','HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','COMPILER_TOOL','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX','FRANK_COMPONENT','FULL_FRANK_HANDOFF']
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--allow-pending-full-frank',action='store_true');a=ap.parse_args()
 ok,host=verify(DEFAULT_REGISTRATION)
 if not ok:print(json.dumps({'error':'TARGET_HOST_IDENTITY_NOT_VERIFIED','details':host}));return 3
 head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=False).stdout.strip()
 host_rc=host_suite.main();effect_rc=effect_suite.main()
 if not HOST_RECEIPT.exists() or not EFFECT_RECEIPT.exists():print(json.dumps({'error':'REQUIRED_FRESH_RECEIPT_MISSING','host_rc':host_rc,'effect_rc':effect_rc}));return 2
 hd=json.loads(HOST_RECEIPT.read_text());ed=json.loads(EFFECT_RECEIPT.read_text());hrows=hd.get('applications',{});erows=ed.get('applications',{})
 rows={};fail=[]
 for app in ORDER:
  hr=dict(hrows.get(app) or {})
  if app in EFFECTFUL:
   er=erows.get(app) or {};passed=hr.get('pass') is True and er.get('pass') is True and er.get('authority_boundary_preserved') is True
   row={'pass':passed,'source_or_program_hash':er.get('source_or_program_hash'),'semantic_or_ir_hash':er.get('semantic_or_ir_hash'),'compiler_runtime_version':er.get('compiler_runtime_version'),'target_artifact_hash':er.get('target_artifact_hash'),'execution_command_or_test_id':f"{hr.get('execution_command_or_test_id')} + {er.get('execution_command_or_test_id')}",'expected':{'host_behavior':hr.get('expected'),'clay_effect_chain':er.get('expected')},'observed':{'host_behavior':hr.get('observed'),'clay_effect_chain':er.get('observed'),'runtime_adapters':er.get('runtime_adapters')},'negative_or_failure_path':{'host':hr.get('negative_or_failure_path'),'clay_effect_chain':er.get('negative_or_failure_path')},'authority_boundary_preserved':hr.get('authority_boundary_preserved') is True and er.get('authority_boundary_preserved') is True,'dual_proof':{'hardened_host_behavior_pass':hr.get('pass') is True,'clay_source_effect_chain_pass':er.get('pass') is True}}
  else:row=hr
  if not row.get('pass'):fail.append(app)
  rows[app]=row
 nine=all(rows[x].get('pass') is True for x in ORDER if x!='FULL_FRANK_HANDOFF')
 full=rows['FULL_FRANK_HANDOFF'].get('pass') is True
 report={'schema_version':'1.1','target_host':TARGET_HOST,'target_host_verified':True,'host_fingerprint':host.get('host_fingerprint',{}),'repository_commit':head,'host_suite_returncode':host_rc,'effect_suite_returncode':effect_rc,'applications':rows,'passed':[x for x in ORDER if rows[x].get('pass') is True],'failures':fail,'pass':not fail,'nine_of_ten_ready':nine,'full_frank_handoff_ready':full,'intermediate_exit_allowed':bool(a.allow_pending_full_frank and nine and not full and fail==['FULL_FRANK_HANDOFF']),'authority_invariant':'model output != execution authority','promotion_performed':False,'rule':'Effectful applications require both real hardened target behavior and a Clay source -> typed effect IR -> opaque mainline runtime path. FULL_FRANK_HANDOFF remains independent and fail-closed.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'pass':report['pass'],'passed':len(report['passed']),'failures':fail,'nine_of_ten_ready':nine,'intermediate_exit_allowed':report['intermediate_exit_allowed'],'output':str(OUT.relative_to(ROOT))}));return 0 if report['pass'] or report['intermediate_exit_allowed'] else 2
if __name__=='__main__':raise SystemExit(main())
