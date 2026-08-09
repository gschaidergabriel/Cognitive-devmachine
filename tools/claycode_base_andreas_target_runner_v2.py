#!/usr/bin/env python3
"""Fail-closed ClayCode BASE acceptance runner for Andreas' Ubuntu developer host."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MARKER_TEXT='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM';DEFAULT_MARKER=Path.home()/'.claycode/ANDREAS_TARGET_HOST';OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_V2.json';V7='research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
PHASES=[
 ('frontend',['tools/claycode_base_frontend_validation.py','--grammar',V7,'--output','research_entity/claycode/autonomous/BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json']),
 ('canonicalizer',['tools/claycode_base_canonicalizer_validation.py']),
 ('typed_ir',['tools/claycode_wp03_typed_ir_validation.py']),
 ('effect_pipeline',['tools/claycode_base_effect_pipeline.py','--self-test','--output','research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json']),
 ('pure_native',['tools/claycode_base_pure_toolchain_validation.py']),
 ('package_link',['tools/claycode_base_package_validation.py']),
 ('runtime',['tools/claycode_base_runtime_validation.py']),
 ('applications',['tools/claycode_base_application_proxy_suite_v2.py']),
 ('fuzz',['tools/claycode_base_fuzz_conformance.py']),
 ('corpus',['tools/claycode_base_corpus_generator.py']),
 ('frank',['tools/claycode_frank_score_handoff_validation.py'])]
ARTIFACTS=['BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json','BASE_CANONICALIZER_RECEIPT.json','WP03_TYPED_IR_RECEIPT.json','BASE_EFFECT_PIPELINE_RECEIPT.json','BASE_PURE_TOOLCHAIN_RECEIPT.json','BASE_PACKAGE_LINK_RECEIPT.json','BASE_RUNTIME_CAPABILITY_RECEIPT.json','BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json','BASE_FUZZ_CONFORMANCE_RECEIPT.json','FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json']
def sha(b):return hashlib.sha256(b).hexdigest()
def release():
 d={};p=Path('/etc/os-release')
 if p.exists():
  for line in p.read_text(errors='replace').splitlines():
   if '=' in line:k,v=line.split('=',1);d[k]=v.strip().strip('"')
 return d
def gate(marker):
 r=release();cg=Path('/proc/1/cgroup').read_text(errors='replace').lower() if Path('/proc/1/cgroup').exists() else '';return {'linux':platform.system()=='Linux','ubuntu':r.get('ID')=='ubuntu','not_github_actions':os.getenv('GITHUB_ACTIONS','').lower()!='true','not_ci':os.getenv('CI','').lower() not in {'1','true','yes'},'not_docker_file':not Path('/.dockerenv').exists(),'not_known_container_cgroup':not any(x in cg for x in ('docker','containerd','kubepods','lxc')),'andreas_local_marker':marker.exists() and marker.read_text(errors='replace').strip()==MARKER_TEXT},r
def command(argv,timeout=300):
 t=time.monotonic();cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,timeout=timeout,check=False);return {'argv':argv,'returncode':cp.returncode,'duration_s':round(time.monotonic()-t,6),'stdout_sha256':sha(cp.stdout.encode()),'stderr_sha256':sha(cp.stderr.encode()),'stdout_tail':cp.stdout[-1200:],'stderr_tail':cp.stderr[-1200:],'pass':cp.returncode==0}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--marker',type=Path,default=DEFAULT_MARKER);ap.add_argument('--output',type=Path,default=OUT);a=ap.parse_args();checks,rel=gate(a.marker)
 if not all(checks.values()):print(json.dumps({'error':'TARGET_HOST_GATE_FAILED','checks':checks,'marker':str(a.marker)},indent=2));return 3
 phases=[]
 for name,args in PHASES:
  if not (ROOT/args[0]).exists():phases.append({'phase':name,'pass':False,'error':'MISSING_SCRIPT','path':args[0]});break
  row=command([sys.executable,*args]);row['phase']=name;phases.append(row)
  if not row['pass']:break
 auto=ROOT/'research_entity/claycode/autonomous';arts=[]
 for name in ARTIFACTS:
  p=auto/name
  if p.exists():
   try:d=json.loads(p.read_text());embedded=d.get('pass')
   except Exception:embedded=None
   arts.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,'embedded_pass':embedded})
  else:arts.append({'path':str(p.relative_to(ROOT)),'missing':True})
 corpus=ROOT/'research_entity/claycode/corpus/base_v1/CORPUS_MANIFEST.json'
 if corpus.exists():
  d=json.loads(corpus.read_text());arts.append({'path':str(corpus.relative_to(ROOT)),'sha256':sha(corpus.read_bytes()),'bytes':corpus.stat().st_size,'embedded_pass':d.get('pass')})
 else:arts.append({'path':str(corpus.relative_to(ROOT)),'missing':True})
 all_phases=len(phases)==len(PHASES) and all(x['pass'] for x in phases);all_artifacts=all(not x.get('missing') and x.get('embedded_pass') is not False for x in arts);git=command(['git','rev-parse','HEAD'],15);native=command(['cc','--version'],15)
 r={'schema_version':'2.0','created_at':datetime.now(timezone.utc).isoformat(),'target_host':'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM','target_host_checks':checks,'host':{'node':platform.node(),'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'os_release':rel},'repo_head':git,'native_compiler':native,'phases':phases,'artifacts':arts,'all_phases_pass':all_phases,'all_artifacts_present_and_nonfailed':all_artifacts,'target_acceptance_ready_for_wp14_audit':all_phases and all_artifacts,'automatic_promotion':False,'authority_invariant':'model_output != execution_authority','scope':'Target execution evidence; WP14 still decides package/app coverage and P0/P1 closure.'};raw=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(raw,encoding='utf-8');print(json.dumps({'pass':r['target_acceptance_ready_for_wp14_audit'],'receipt':str(a.output.relative_to(ROOT)),'sha256':sha(raw.encode())}));return 0 if r['target_acceptance_ready_for_wp14_audit'] else 2
if __name__=='__main__':raise SystemExit(main())
