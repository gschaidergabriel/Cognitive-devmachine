#!/usr/bin/env python3
"""Run ClayCode BASE closure gates on the actual Andreas Ubuntu developer system.

This runner is intentionally unusable as target acceptance in GitHub Actions/containers.
It requires a local host marker that is never committed to the repository:
  ~/.claycode/ANDREAS_TARGET_HOST
with exact text:
  ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM

It executes current gates, records host/tool/repo identity and writes one hash-linked
umbrella receipt. It does NOT auto-promote the release workspace; WP14 audit remains the
only promotion step.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MARKER_TEXT='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_RECEIPT.json'
PHASES=[
 ('frontend',['tools/claycode_base_frontend_validation.py']),
 ('canonicalizer',['tools/claycode_base_canonicalizer_validation.py']),
 ('typed_ir',['tools/claycode_wp03_typed_ir_validation.py']),
 ('effect_pipeline',['tools/claycode_base_effect_pipeline.py','--self-test','--output','research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json']),
 ('pure_toolchain',['tools/claycode_base_pure_toolchain_validation.py']),
 ('runtime_abi_ffi',['tools/claycode_base_runtime_validation.py']),
 ('applications',['tools/claycode_base_application_proxy_suite_v2.py']),
 ('fuzz_conformance',['tools/claycode_base_fuzz_conformance.py']),
 ('heldout_corpus',['tools/claycode_base_corpus_generator.py']),
 ('frank_subsystem_handoff',['tools/claycode_frank_score_handoff_validation.py']),
]
ARTIFACTS=[
 'research_entity/claycode/autonomous/BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json',
 'research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json',
 'research_entity/claycode/autonomous/WP03_TYPED_IR_RECEIPT.json',
 'research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json',
 'research_entity/claycode/autonomous/BASE_PURE_TOOLCHAIN_RECEIPT.json',
 'research_entity/claycode/autonomous/BASE_RUNTIME_CAPABILITY_RECEIPT.json',
 'research_entity/claycode/autonomous/BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json',
 'research_entity/claycode/autonomous/BASE_FUZZ_CONFORMANCE_RECEIPT.json',
 'research_entity/claycode/corpus/base_v1/CORPUS_MANIFEST.json',
 'research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json',
]
def sha(b):return hashlib.sha256(b).hexdigest()
def os_release():
 d={};p=Path('/etc/os-release')
 if p.exists():
  for line in p.read_text(errors='replace').splitlines():
   if '=' in line:
    k,v=line.split('=',1);d[k]=v.strip().strip('"')
 return d
def host_gate(marker):
 rel=os_release();cgroup=Path('/proc/1/cgroup').read_text(errors='replace').lower() if Path('/proc/1/cgroup').exists() else ''
 checks={
  'linux':platform.system()=='Linux','ubuntu':rel.get('ID')=='ubuntu','not_github_actions':os.environ.get('GITHUB_ACTIONS','').lower()!='true','not_ci_env':os.environ.get('CI','').lower() not in {'1','true','yes'},'no_dockerenv':not Path('/.dockerenv').exists(),'no_known_container_cgroup':not any(x in cgroup for x in ('docker','containerd','kubepods','lxc')),'local_marker':marker.exists() and marker.read_text(errors='replace').strip()==MARKER_TEXT,
 }
 return checks,rel
def run_phase(name,args):
 start=time.monotonic();cp=subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True,timeout=300,check=False);return {'phase':name,'argv':[sys.executable,*args],'returncode':cp.returncode,'duration_s':round(time.monotonic()-start,6),'stdout_sha256':sha(cp.stdout.encode()),'stderr_sha256':sha(cp.stderr.encode()),'stdout_tail':cp.stdout[-2000:],'stderr_tail':cp.stderr[-2000:],'pass':cp.returncode==0}
def command_info(argv):
 try:
  cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,timeout=15,check=False);return {'argv':argv,'returncode':cp.returncode,'stdout_first_line':(cp.stdout or cp.stderr).splitlines()[0] if (cp.stdout or cp.stderr).splitlines() else ''}
 except Exception as exc:return {'argv':argv,'error':repr(exc)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--marker',type=Path,default=Path.home()/'.claycode/ANDREAS_TARGET_HOST');ap.add_argument('--output',type=Path,default=OUT);a=ap.parse_args();checks,release=host_gate(a.marker)
 if not all(checks.values()):
  print(json.dumps({'error':'TARGET_HOST_GATE_FAILED','checks':checks,'marker':str(a.marker)},indent=2));return 3
 git=command_info(['git','rev-parse','HEAD']);cc=command_info(['cc','--version']);phases=[]
 for name,args in PHASES:
  if not (ROOT/args[0]).exists():phases.append({'phase':name,'pass':False,'error':'MISSING_GATE_SCRIPT','path':args[0]});continue
  row=run_phase(name,args);phases.append(row)
  if not row['pass']:break
 artifacts=[]
 for rel in ARTIFACTS:
  p=ROOT/rel
  if p.exists():
   try:data=json.loads(p.read_text());semantic_pass=data.get('pass',data.get('leak_audit',{}).get('pass'))
   except Exception:semantic_pass=None
   artifacts.append({'path':rel,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,'embedded_pass':semantic_pass})
  else:artifacts.append({'path':rel,'missing':True})
 all_phases=all(x.get('pass') for x in phases) and len(phases)==len(PHASES);all_artifacts=all(not x.get('missing') and x.get('embedded_pass') is not False for x in artifacts)
 receipt={'schema_version':'1.0','created_at':datetime.now(timezone.utc).isoformat(),'target_host':'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM','target_host_checks':checks,'host':{'node':platform.node(),'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'os_release':release},'repo':git,'native_compiler':cc,'phases':phases,'artifacts':artifacts,'all_phases_pass':all_phases,'all_required_artifacts_present':all_artifacts,'target_acceptance_ready_for_wp14_audit':all_phases and all_artifacts,'automatic_workspace_promotion':False,'authority_invariant':'model_output != execution_authority','note':'This receipt may count as target-host evidence only because the runner refuses GitHub Actions/known containers and requires the uncommitted Andreas target marker. WP14 must still inspect receipt scope and unresolved defects.'}
 raw=json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(raw,encoding='utf-8');print(json.dumps({'pass':receipt['target_acceptance_ready_for_wp14_audit'],'output':str(a.output),'receipt_sha256':sha(raw.encode())}));return 0 if receipt['target_acceptance_ready_for_wp14_audit'] else 2
if __name__=='__main__':raise SystemExit(main())
