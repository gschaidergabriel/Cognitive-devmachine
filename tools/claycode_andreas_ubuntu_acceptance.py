#!/usr/bin/env python3
"""One-command ClayCode BASE target preflight for Andreas' Ubuntu developer system.

Fail-closed rules:
- a generic Ubuntu box / GitHub runner cannot self-declare itself the v0.1 target;
- the target must match a project-owner-approved /etc/machine-id binding;
- current proxy gates may be rerun on that host, but proxy success is NOT automatically
  converted into GENERAL_PURPOSE_GATE or work-package PASS.
"""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_PREFLIGHT.json'
ROLE='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
MANDATORY_COMMANDS=[
    ['python','tools/claycode_base_application_proxy_suite.py'],
    ['python','tools/claycode_base_authority_runtime.py'],
    ['python','tools/claycode_base_authority_integration_validation.py'],
    ['python','tools/claycode_base_fuzz_conformance.py'],
    ['python','tools/claycode_base_corpus_generator.py'],
]
class Refusal(RuntimeError): pass

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def machine_id_hash()->str:
    p=Path('/etc/machine-id')
    if not p.exists(): raise Refusal('MACHINE_ID_MISSING')
    raw=p.read_text(encoding='utf-8').strip().encode()
    if not raw: raise Refusal('MACHINE_ID_EMPTY')
    return sha(raw)
def os_release()->dict[str,str]:
    p=Path('/etc/os-release')
    if not p.exists(): raise Refusal('OS_RELEASE_MISSING')
    out={}
    for line in p.read_text(encoding='utf-8').splitlines():
        if '=' in line:
            k,v=line.split('=',1);out[k]=v.strip().strip('"')
    return out
def host_fingerprint()->dict:
    osr=os_release()
    return {'role':ROLE,'machine_id_sha256':machine_id_hash(),'os_id':osr.get('ID',''),'os_version_id':osr.get('VERSION_ID',''),'kernel':platform.release(),'machine':platform.machine(),'python':platform.python_version()}
def verify_binding(binding_path:Path)->dict:
    actual=host_fingerprint()
    if actual['os_id'].lower()!='ubuntu': raise Refusal('TARGET_OS_NOT_UBUNTU')
    binding=json.loads(binding_path.read_text(encoding='utf-8'))
    if binding.get('host_role')!=ROLE: raise Refusal('TARGET_ROLE_BINDING_MISMATCH')
    expected=binding.get('machine_id_sha256','')
    if len(expected)!=64 or expected!=actual['machine_id_sha256']: raise Refusal('TARGET_MACHINE_BINDING_MISMATCH')
    if not binding.get('approved_by'): raise Refusal('TARGET_BINDING_APPROVER_MISSING')
    return {'binding':binding,'actual':actual,'pass':True}
def git_state()->dict:
    def run(*args):return subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()
    return {'commit':run('rev-parse','HEAD'),'branch':run('rev-parse','--abbrev-ref','HEAD'),'dirty':bool(run('status','--porcelain'))}
def execute(command:list[str])->dict:
    t0=time.time();cp=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    return {'command':command,'returncode':cp.returncode,'elapsed_s':round(time.time()-t0,3),'stdout_sha256':sha(cp.stdout.encode()),'stderr_sha256':sha(cp.stderr.encode()),'stdout_tail':cp.stdout[-2000:],'stderr_tail':cp.stderr[-2000:]}
def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--binding',type=Path,help='owner-approved target host binding JSON')
    ap.add_argument('--print-fingerprint',action='store_true',help='print host fingerprint and exit without acceptance')
    args=ap.parse_args()
    if args.print_fingerprint:
        print(json.dumps(host_fingerprint(),indent=2,sort_keys=True));return 0
    if not args.binding: raise Refusal('TARGET_BINDING_REQUIRED')
    host=verify_binding(args.binding);git=git_state()
    if git['dirty']: raise Refusal('WORKTREE_DIRTY')
    missing=[c[1] for c in MANDATORY_COMMANDS if not (ROOT/c[1]).exists()]
    if missing: raise Refusal('MANDATORY_GATE_SCRIPT_MISSING:'+','.join(missing))
    runs=[execute(c) for c in MANDATORY_COMMANDS];failed=[r['command'][1] for r in runs if r['returncode']!=0]
    preflight=not failed
    receipt={'schema_version':'1.1','receipt_class':'ANDREAS_UBUNTU_TARGET_PREFLIGHT','host':host,'git':git,'commands':runs,'target_preflight_passed':preflight,'failures':failed,'counts_as_target_acceptance':False,'counts_as_work_package_pass':False,'next_required':'Run package-specific production acceptance receipts, including real full FRANK handoff, then canonical BASE audit.','promotion_note':'Bound-host execution of proxy gates is useful evidence but is deliberately insufficient for GENERAL_PURPOSE_GATE PASS.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'preflight_pass':preflight,'counts_as_target_acceptance':False,'receipt':str(OUT.relative_to(ROOT)),'target_machine':host['actual']['machine_id_sha256'][:16]},sort_keys=True))
    return 0 if preflight else 1
if __name__=='__main__':
    try: raise SystemExit(main())
    except Refusal as e:
        print(json.dumps({'preflight_pass':False,'refused':str(e),'counts_as_target_acceptance':False},sort_keys=True),file=sys.stderr);raise SystemExit(64)
