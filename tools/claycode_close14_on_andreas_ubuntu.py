#!/usr/bin/env python3
"""One-command fail-closed ClayCode BASE14 closure on Andreas' Ubuntu target.

Prerequisite once per machine:
  python tools/claycode_target_host_identity.py register \
    --acknowledge ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM

The command never fabricates missing evidence. It runs the V2 component collector, real
10-app suite, strict target adjudication, evidence-gated preaudit promotion, WP14 release
audit and final promotion. It stops at the first real blocker and reports that stage.
"""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM';MARKER=Path.home()/'.claycode/ANDREAS_TARGET_HOST'
STAGES=[
 ('target_components',['tools/claycode_base_andreas_target_runner_v2.py']),
 ('real_ten_apps',['tools/claycode_base_target_application_suite.py']),
 ('strict_target_adjudication',['tools/claycode_andreas_ubuntu_acceptance_assembler.py']),
 ('promote_wp02_wp13',['tools/claycode_base_release_promote.py','preaudit']),
 ('wp14_release_audit',['tools/claycode_base_release_audit.py']),
 ('promote_wp14',['tools/claycode_base_release_promote.py','finalize'])]
def run(argv,timeout=3600):
 cp=subprocess.run([sys.executable,*argv],cwd=ROOT,text=True,capture_output=True,timeout=timeout,check=False)
 return {'argv':argv,'returncode':cp.returncode,'stdout_tail':cp.stdout[-5000:],'stderr_tail':cp.stderr[-5000:],'pass':cp.returncode==0}
def git_clean():
 cp=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True,check=False);return cp.returncode==0 and not cp.stdout.strip(),cp.stdout.splitlines()[:100]
def main()->int:
 verify=run(['tools/claycode_target_host_identity.py','verify','--json'],30)
 if not verify['pass']:
  print(json.dumps({'closed':False,'stage':'target_identity','detail':verify,'next_command':f'python tools/claycode_target_host_identity.py register --acknowledge {TARGET}'},ensure_ascii=False,indent=2));return 3
 clean,dirty=git_clean()
 if not clean:
  print(json.dumps({'closed':False,'stage':'clean_checkout','dirty':dirty,'rule':'Start closure from a clean checkout so target evidence is bound to one repository revision.'},ensure_ascii=False,indent=2));return 3
 MARKER.parent.mkdir(parents=True,exist_ok=True);MARKER.write_text(TARGET+'\n',encoding='utf-8')
 rows=[]
 for name,argv in STAGES:
  row=run(argv);row['stage']=name;rows.append(row)
  if not row['pass']:
   print(json.dumps({'closed':False,'failed_stage':name,'completed_stages':[x['stage'] for x in rows if x['pass']],'detail':row,'rule':'Fail closed; no later promotion stage was executed.'},ensure_ascii=False,indent=2));return row['returncode'] or 2
 ws=ROOT/'research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json';d=json.loads(ws.read_text());wps=d.get('work_packages') or {};not_pass=[k for k,v in wps.items() if (v or {}).get('status')!='PASS'];apps=d.get('application_acceptance',{}).get('passed') or []
 closed=not not_pass and d.get('gate_status')=='PASS' and d.get('general_purpose_gate_status')=='PASS' and len(apps)==10
 report={'closed':closed,'work_packages_pass':len(wps)-len(not_pass),'work_packages_total':len(wps),'not_pass':not_pass,'applications_pass':len(apps),'gate_status':d.get('gate_status'),'general_purpose_gate_status':d.get('general_purpose_gate_status'),'stages':[x['stage'] for x in rows]}
 print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if closed else 2
if __name__=='__main__':raise SystemExit(main())