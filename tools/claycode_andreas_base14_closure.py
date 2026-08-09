#!/usr/bin/env python3
"""One-command convergence runner for the ClayCode BASE14 closeout on Andreas Ubuntu.

Runs target component gate first from a clean source tree, then resource-lifetime and
nine real app acceptances, then the fail-closed WP14 auditor. The command is expected to
remain nonzero until a genuine FULL_FRANK_HANDOFF receipt exists and every gate passes.
"""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE14_CLOSURE.json';TARGET='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
STEPS=[
 ('target_components',[sys.executable,'tools/claycode_andreas_ubuntu_target_gate.py']),
 ('resource_lifetime',[sys.executable,'tools/claycode_base_resource_lifetime_validation.py']),
 ('real_apps_9_of_10',[sys.executable,'tools/claycode_andreas_application_acceptance.py']),
 ('wp14_audit',[sys.executable,'tools/claycode_base_wp14_audit.py']),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def clean_source_tree():
 cp=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True,check=False);return cp.returncode==0 and not cp.stdout.strip(),cp.stdout.splitlines()[:30]
def main()->int:
 if os.getenv('CLAYCODE_TARGET_HOST_ID')!=TARGET or platform.system()!='Linux' or os.getenv('GITHUB_ACTIONS','').lower()=='true' or os.getenv('CI','').lower() in {'1','true','yes'}:print(json.dumps({'error':'TARGET_ATTESTATION_FAILED'}));return 3
 clean,dirty=clean_source_tree()
 if not clean:print(json.dumps({'error':'INITIAL_CHECKOUT_NOT_CLEAN','entries':dirty}));return 3
 head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=False).stdout.strip();rows=[]
 for name,argv in STEPS:
  cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,check=False);rows.append({'step':name,'argv':argv,'returncode':cp.returncode,'pass':cp.returncode==0,'stdout_tail':cp.stdout[-3000:],'stderr_tail':cp.stderr[-3000:]})
  if name!='wp14_audit' and cp.returncode!=0:break
 manifest=ROOT/'CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json';m={}
 if manifest.exists():
  try:m=json.loads(manifest.read_text())
  except Exception:pass
 report={'schema_version':'1.0','created_at':datetime.now(timezone.utc).isoformat(),'target_host':TARGET,'input_git_head':head,'steps':rows,'general_purpose_gate_pass':m.get('general_purpose_gate_pass') is True,'claycode_release_gate_pass':m.get('claycode_release_gate_pass') is True,'failed_work_packages':m.get('failed_work_packages',[]),'manifest_sha256':sha(manifest.read_bytes()) if manifest.exists() else None,'note':'A nonzero result is an evidence-preserving blocker verdict, not a partial-success promotion.'};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'pass':report['claycode_release_gate_pass'],'failed_work_packages':report['failed_work_packages'],'output':str(OUT.relative_to(ROOT))}));return 0 if report['claycode_release_gate_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
