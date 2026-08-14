#!/usr/bin/env python3
"""Materialize WP10 per-application receipts from hardened target executions.

Requires the registered non-CI Andreas Ubuntu host. Six effectful apps are additionally
re-executed through Clay source -> typed-effect IR -> selected ClayRuntime and combined
with the richer target behavior rows. GUI_INTERACTIVE additionally requires the real
Ubuntu mapped-window desktop receipt. FULL_FRANK_HANDOFF is never fabricated here; the
full FRANK target finalizer owns that receipt.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claycode_target_host_identity import DEFAULT_REGISTRATION,TARGET_HOST,verify
AGG=ROOT/'research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json'
DESKTOP=ROOT/'research_entity/claycode/target/APP05_UBUNTU_DESKTOP.json'
EFFECT_TOOL=ROOT/'tools/claycode_base_effect_apps_v2.py'
EFFECT_RECEIPT=ROOT/'research_entity/claycode/autonomous/BASE_EFFECT_APPLICATIONS_V2_RECEIPT.json'
OUTDIR=ROOT/'research_entity/claycode/target_receipts/apps'
TARGET='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
EFFECT_APPS={'HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX'}
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path):return json.loads(p.read_text(encoding='utf-8'))
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--registration',type=Path,default=DEFAULT_REGISTRATION);args=ap.parse_args()
 host_ok,host=verify(args.registration)
 if not host_ok or host.get('target_host')!=TARGET_HOST or TARGET_HOST!=TARGET or platform.system()!='Linux' or os.getenv('GITHUB_ACTIONS','').lower()=='true' or os.getenv('CI','').lower() in {'1','true','yes'}:
  print(json.dumps({'error':'REAL_APP_RECEIPT_TARGET_PRECONDITION_FAILED','host':host}));return 3
 if not AGG.exists():print(json.dumps({'error':'HARDENED_APPLICATION_AGGREGATE_MISSING'}));return 2
 if not DESKTOP.exists():print(json.dumps({'error':'REAL_UBUNTU_DESKTOP_RECEIPT_MISSING'}));return 2
 desktop=load(DESKTOP)
 desktop_ok=(desktop.get('target_host')==TARGET and desktop.get('application')=='GUI_INTERACTIVE' and desktop.get('pass') is True and desktop.get('counts_as_target_acceptance') is True and desktop.get('authority_boundary_preserved') is True and (desktop.get('observed') or {}).get('io_mode')=='TK_REAL_DESKTOP_EVENT_LOOP' and (desktop.get('observed') or {}).get('window_was_mapped') is True)
 if not desktop_ok:
  print(json.dumps({'error':'REAL_UBUNTU_DESKTOP_RECEIPT_NOT_PASS','desktop':desktop}));return 2
 agg=load(AGG);apps=agg.get('applications') or {}
 if agg.get('target_host')!=TARGET or agg.get('target_host_verified') is not True:
  print(json.dumps({'error':'HARDENED_APPLICATION_AGGREGATE_NOT_TARGET_VERIFIED'}));return 2
 cp=subprocess.run([sys.executable,str(EFFECT_TOOL)],cwd=ROOT,text=True,capture_output=True,check=False,timeout=600)
 if cp.returncode!=0 or not EFFECT_RECEIPT.exists():
  print(json.dumps({'error':'TYPED_EFFECT_APPLICATION_PROOF_FAILED','returncode':cp.returncode,'stdout':cp.stdout[-2000:],'stderr':cp.stderr[-2000:]}));return 2
 effect=load(EFFECT_RECEIPT);effect_rows={r.get('app_id'):r for r in effect.get('rows',[]) if isinstance(r,dict)}
 if effect.get('pass') is not True or effect.get('textual_capability_without_bearer_denied') is not True:
  print(json.dumps({'error':'TYPED_EFFECT_APPLICATION_RECEIPT_NOT_PASS'}));return 2
 head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=False).stdout.strip();OUTDIR.mkdir(parents=True,exist_ok=True)
 failures=[];written=[]
 for name,row in apps.items():
  if name=='FULL_FRANK_HANDOFF':continue
  if not isinstance(row,dict):failures.append(name+':ROW_INVALID');continue
  er=effect_rows.get(name) if name in EFFECT_APPS else None
  if name in EFFECT_APPS and (not er or er.get('pass') is not True):failures.append(name+':TYPED_EFFECT_ROW_MISSING_OR_FAIL');continue
  source_hash=(er or {}).get('source_or_program_hash') or row.get('source_or_program_hash')
  semantic_hash=(er or {}).get('semantic_or_ir_hash') or row.get('semantic_or_ir_hash')
  artifact_hash=(er or {}).get('target_artifact_hash') or row.get('target_artifact_hash')
  gui_ok=True if name!='GUI_INTERACTIVE' else desktop_ok
  ok=row.get('pass') is True and (er is None or er.get('pass') is True) and row.get('authority_boundary_preserved') is True and gui_ok
  negative_detail=row.get('negative_or_failure_path')
  receipt={'schema_version':'2.1','app':name,'pass':ok,'target_host':TARGET,'evidence_class':'ANDREAS_UBUNTU_REAL_APPLICATION','model_output_is_execution_authority':False,'git_head':head,'source_sha256':source_hash,'semantic_or_ir_sha256':semantic_hash,'artifact_sha256':artifact_hash,'expected':row.get('expected'),'observed':row.get('observed'),'positive_test':{'pass':ok,'hardened_target_test_id':row.get('execution_command_or_test_id'),'typed_effect_ir_test_id':(er or {}).get('execution_command_or_test_id'),'typed_effect_ir_pass':None if er is None else er.get('pass'),'real_ubuntu_desktop_pass':desktop_ok if name=='GUI_INTERACTIVE' else None,'desktop_receipt_sha256':sha(DESKTOP) if name=='GUI_INTERACTIVE' else None},'negative_test':{'pass':bool(negative_detail) and row.get('authority_boundary_preserved') is True,'detail':negative_detail,'textual_capability_without_bearer_denied':effect.get('textual_capability_without_bearer_denied') if er else None,'desktop_forbidden_event_rejected':(desktop.get('negative_or_failure_path') or {}).get('forbidden_event_rejected') if name=='GUI_INTERACTIVE' else None},'authority_boundary_preserved':True,'aggregate_receipt_sha256':sha(AGG),'typed_effect_receipt_sha256':sha(EFFECT_RECEIPT) if er else None,'desktop_receipt_sha256':sha(DESKTOP) if name=='GUI_INTERACTIVE' else None}
  (OUTDIR/f'{name}.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');written.append(name)
  if not ok:failures.append(name+':NOT_PASS')
 full=OUTDIR/'FULL_FRANK_HANDOFF.json'
 if not full.exists():failures.append('FULL_FRANK_HANDOFF:FINALIZER_RECEIPT_MISSING')
 else:
  fr=load(full)
  if fr.get('pass') is not True or fr.get('target_host')!=TARGET or fr.get('evidence_class')!='ANDREAS_UBUNTU_REAL_APPLICATION':failures.append('FULL_FRANK_HANDOFF:NOT_PASS')
 print(json.dumps({'pass':not failures,'written':sorted(written),'full_frank_preserved':full.exists(),'real_ubuntu_desktop_pass':desktop_ok,'failures':failures}))
 return 0 if not failures else 2
if __name__=='__main__':raise SystemExit(main())
