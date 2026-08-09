#!/usr/bin/env python3
"""Fail-closed ClayCode BASE target runner for Andreas' Ubuntu developer host.

Exit 0 means the currently implemented target-component battery passed on a clean,
locally-attested Andreas Ubuntu host. It NEVER means ClayCode BASE release PASS: the
hosted/proxy ten-app suite is deliberately non-accepting, so WP10 real application
receipts and WP14 final audit remain separate mandatory gates.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MARKER_TEXT='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
DEFAULT_MARKER=Path.home()/'.claycode/ANDREAS_TARGET_HOST'
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_V2.json'
V7='research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
STRICT='research_entity/claycode/target_receipts/STRICT_LALR_D_V7_TARGET_RECEIPT.json'
PHASES=[
 ('strict_lalr',['tools/claycode_strict_lalr_probe.py','--grammar',V7,'--output',STRICT],True),
 ('frontend',['tools/claycode_base_frontend_validation.py','--grammar',V7,'--output','research_entity/claycode/autonomous/BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json'],True),
 ('canonicalizer',['tools/claycode_base_canonicalizer_validation.py'],True),
 ('typed_ir',['tools/claycode_wp03_typed_ir_validation.py'],True),
 ('effect_pipeline',['tools/claycode_base_effect_pipeline.py','--self-test','--output','research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json'],True),
 ('pure_native',['tools/claycode_base_pure_toolchain_validation.py'],True),
 ('package_link',['tools/claycode_base_package_validation.py'],True),
 ('runtime',['tools/claycode_base_runtime_validation.py'],True),
 ('applications_proxy',['tools/claycode_base_application_proxy_suite_v2.py'],False),
 ('fuzz',['tools/claycode_base_fuzz_conformance.py'],True),
 ('corpus',['tools/claycode_base_corpus_generator.py'],True),
 ('frank',['tools/claycode_frank_score_handoff_validation.py'],True)]
ARTIFACTS=['BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json','BASE_CANONICALIZER_RECEIPT.json','WP03_TYPED_IR_RECEIPT.json','BASE_EFFECT_PIPELINE_RECEIPT.json','BASE_PURE_TOOLCHAIN_RECEIPT.json','BASE_PACKAGE_LINK_RECEIPT.json','BASE_RUNTIME_CAPABILITY_RECEIPT.json','BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json','BASE_FUZZ_CONFORMANCE_RECEIPT.json','FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json']
def sha(b):return hashlib.sha256(b).hexdigest()
def release():
 d={};p=Path('/etc/os-release')
 if p.exists():
  for line in p.read_text(errors='replace').splitlines():
   if '=' in line:k,v=line.split('=',1);d[k]=v.strip().strip('"')
 return d
def command(argv,timeout=900):
 t=time.monotonic()
 try:cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,timeout=timeout,check=False);return {'argv':argv,'returncode':cp.returncode,'duration_s':round(time.monotonic()-t,6),'stdout_sha256':sha(cp.stdout.encode()),'stderr_sha256':sha(cp.stderr.encode()),'stdout_tail':cp.stdout[-1600:],'stderr_tail':cp.stderr[-1600:],'process_pass':cp.returncode==0}
 except Exception as exc:return {'argv':argv,'returncode':None,'duration_s':round(time.monotonic()-t,6),'process_pass':False,'exception':f'{type(exc).__name__}: {exc}'}
def git_clean():
 cp=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True,check=False);return cp.returncode==0 and not cp.stdout.strip(),cp.stdout.splitlines()[:100]
def gate(marker):
 r=release();cg=Path('/proc/1/cgroup').read_text(errors='replace').lower() if Path('/proc/1/cgroup').exists() else '';clean,dirty=git_clean();checks={'linux':platform.system()=='Linux','ubuntu':r.get('ID')=='ubuntu','not_github_actions':os.getenv('GITHUB_ACTIONS','').lower()!='true','not_ci':os.getenv('CI','').lower() not in {'1','true','yes'},'not_docker_file':not Path('/.dockerenv').exists(),'not_known_container_cgroup':not any(x in cg for x in ('docker','containerd','kubepods','lxc')),'andreas_local_marker':marker.exists() and marker.read_text(errors='replace').strip()==MARKER_TEXT,'clean_git_checkout':clean};return checks,r,dirty
def embedded(path):
 try:return json.loads(path.read_text())
 except Exception:return {}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--marker',type=Path,default=DEFAULT_MARKER);ap.add_argument('--output',type=Path,default=OUT);a=ap.parse_args();checks,rel,dirty=gate(a.marker)
 if not all(checks.values()):print(json.dumps({'error':'TARGET_HOST_GATE_FAILED','checks':checks,'dirty':dirty,'marker':str(a.marker)},indent=2));return 3
 phases=[]
 for name,args,target_component in PHASES:
  if not (ROOT/args[0]).exists():phases.append({'phase':name,'semantic_pass':False,'error':'MISSING_SCRIPT','path':args[0],'target_component':target_component});break
  row=command([sys.executable,*args]);row['phase']=name;row['target_component']=target_component;semantic=bool(row['process_pass'])
  if name=='strict_lalr':
   d=embedded(ROOT/STRICT);semantic=semantic and d.get('strict_build_ok') is True and not d.get('conflict_diagnostics');row['strict_receipt']={'strict_build_ok':d.get('strict_build_ok'),'conflict_diagnostics':d.get('conflict_diagnostics'),'strict_error':d.get('strict_error')}
  if name=='applications_proxy':
   d=embedded(ROOT/'research_entity/claycode/autonomous/BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json');row['proxy_contract']={'pass':d.get('pass'),'counts_as_target_acceptance':d.get('counts_as_target_acceptance'),'counts_as_application_acceptance_pass':d.get('counts_as_application_acceptance_pass')};semantic=semantic and d.get('pass') is True and d.get('counts_as_target_acceptance') is False and d.get('counts_as_application_acceptance_pass') is False
  row['semantic_pass']=semantic;phases.append(row)
  if not semantic:break
 auto=ROOT/'research_entity/claycode/autonomous';arts=[]
 for name in ARTIFACTS:
  p=auto/name;d=embedded(p) if p.exists() else {};arts.append({'path':str(p.relative_to(ROOT)),'missing':not p.exists(),'sha256':sha(p.read_bytes()) if p.exists() else None,'embedded_pass':d.get('pass')})
 corpus=ROOT/'research_entity/claycode/corpus/base_v1/CORPUS_MANIFEST.json';cd=embedded(corpus) if corpus.exists() else {};arts.append({'path':str(corpus.relative_to(ROOT)),'missing':not corpus.exists(),'sha256':sha(corpus.read_bytes()) if corpus.exists() else None,'embedded_pass':cd.get('pass')})
 strictp=ROOT/STRICT;sd=embedded(strictp) if strictp.exists() else {};arts.append({'path':STRICT,'missing':not strictp.exists(),'sha256':sha(strictp.read_bytes()) if strictp.exists() else None,'strict_build_ok':sd.get('strict_build_ok'),'conflict_diagnostics':sd.get('conflict_diagnostics')})
 target_rows=[x for x in phases if x.get('target_component')];target_components_pass=len(target_rows)==sum(1 for _,_,t in PHASES if t) and all(x['semantic_pass'] for x in target_rows)
 proxy_rows=[x for x in phases if not x.get('target_component')];proxy_preflight_pass=bool(proxy_rows) and all(x['semantic_pass'] for x in proxy_rows)
 git=command(['git','rev-parse','HEAD'],15);native=command(['cc','--version'],15)
 unresolved=[]
 if not target_components_pass:unresolved.append('TARGET_COMPONENT_BATTERY_NOT_GREEN')
 unresolved+=['CC-WP-10_REQUIRES_REAL_NON_PROXY_PER_APPLICATION_TARGET_RECEIPTS','CC-WP-14_REQUIRES_FINAL_GENERAL_PURPOSE_MANIFEST_AND_ZERO_P0_P1_AUDIT']
 r={'schema_version':'2.1','created_at':datetime.now(timezone.utc).isoformat(),'target_host':'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM','target_host_checks':checks,'host':{'node':platform.node(),'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'os_release':rel},'repo_head':git,'native_compiler':native,'phases':phases,'artifacts':arts,'target_component_battery_pass':target_components_pass,'wp10_proxy_preflight_pass':proxy_preflight_pass,'base_release_pass':False,'general_purpose_gate_pass':False,'target_acceptance_ready_for_wp14_audit':False,'unresolved':unresolved,'automatic_promotion':False,'authority_invariant':'model_output != execution_authority','scope':'Real target component evidence collector. Proxy application execution is explicitly non-accepting; WP10 real app receipts and WP14 remain mandatory.'}
 raw=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(raw,encoding='utf-8');print(json.dumps({'target_component_battery_pass':target_components_pass,'base_release_pass':False,'receipt':str(a.output.relative_to(ROOT)),'sha256':sha(raw.encode()),'unresolved':unresolved}));return 0 if target_components_pass else 2
if __name__=='__main__':raise SystemExit(main())
