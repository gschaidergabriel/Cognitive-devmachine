#!/usr/bin/env python3
"""Fail-closed ClayCode BASE target runner for Andreas' Ubuntu developer host.

Exit 0 means the currently implemented target-component battery passed on a clean,
locally-attested Andreas Ubuntu host. It NEVER means ClayCode BASE release PASS: real
ten-app acceptance, full FRANK handoff and WP14 strict audit remain separate gates.

Grammar contract:
- CC-WP-02 grammar identity is read from ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json.
- The runner never selects a grammar independently from the strict assembler.
- CC-WP-03 executable typed-function evidence remains separately versioned and must not
  be silently relabeled as WP02 declarative strict evidence.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MARKER_TEXT='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
DEFAULT_MARKER=Path.home()/'.claycode/ANDREAS_TARGET_HOST'
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_V2.json'
CONTRACT_PATH=ROOT/'research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json'

def load_contract():
 try:
  doc=json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
  wp02=doc.get('wp02_parser_contract') or {}
  grammar=str(wp02.get('selected_grammar_path') or '')
  strict=str(wp02.get('strict_receipt_path') or '')
  frontend=str(wp02.get('frontend_receipt_path') or '')
  canonical=str(wp02.get('canonicalizer_receipt_path') or '')
  if not grammar or not strict or not frontend or not canonical:raise ValueError('WP02_CONTRACT_FIELDS_MISSING')
  return doc,grammar,strict,frontend,canonical
 except Exception as exc:raise RuntimeError(f'TARGET_CONTRACT_INVALID:{type(exc).__name__}:{exc}') from exc
CONTRACT_DOC,WP02_GRAMMAR,STRICT,FRONTEND,CANONICAL=load_contract()
PHASES=[
 ('strict_lalr',['tools/claycode_strict_lalr_probe.py','--grammar',WP02_GRAMMAR,'--output',STRICT],True),
 ('frontend',['tools/claycode_base_frontend_validation.py','--grammar',WP02_GRAMMAR,'--output',FRONTEND],True),
 ('canonicalizer',['tools/claycode_base_canonicalizer_validation.py'],True),
 ('typed_ir',['tools/claycode_wp03_typed_ir_validation.py'],True),
 ('effect_pipeline',['tools/claycode_base_effect_pipeline.py','--self-test','--output','research_entity/claycode/autonomous/BASE_EFFECT_PIPELINE_RECEIPT.json'],True),
 ('pure_native',['tools/claycode_base_pure_toolchain_validation.py'],True),
 ('int_division',['tools/claycode_int_division_regression.py'],True),
 ('package_link',['tools/claycode_base_package_validation.py'],True),
 ('runtime',['tools/claycode_base_runtime_validation.py'],True),
 ('runtime_v04_hardening',['tools/claycode_runtime_v04_hardening_validation.py'],True),
 ('compiler_mainline_runtime_bridge',['tools/claycode_effect_mainline_runtime_bridge.py'],True),
 ('concurrency_cancellation_error',['tools/claycode_base_concurrency_validation.py'],True),
 ('applications_proxy',['tools/claycode_base_application_proxy_suite_v2.py'],False),
 ('fuzz',['tools/claycode_base_fuzz_conformance.py'],True),
 ('corpus',['tools/claycode_base_corpus_generator.py'],True),
 ('frank',['tools/claycode_frank_score_handoff_validation.py'],True)]
ARTIFACTS=[
 'BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json','BASE_CANONICALIZER_RECEIPT.json','WP03_TYPED_IR_RECEIPT.json',
 'BASE_EFFECT_PIPELINE_RECEIPT.json','BASE_PURE_TOOLCHAIN_RECEIPT.json','BASE_INT_DIVISION_REGRESSION_RECEIPT.json',
 'BASE_PACKAGE_LINK_RECEIPT.json','BASE_RUNTIME_CAPABILITY_RECEIPT.json','BASE_RUNTIME_V04_HARDENING_RECEIPT.json',
 'BASE_COMPILER_MAINLINE_RUNTIME_BRIDGE_RECEIPT.json','BASE_CONCURRENCY_CANCELLATION_RECEIPT.json',
 'BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json','BASE_FUZZ_CONFORMANCE_RECEIPT.json','FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json']
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
 wp02_path=ROOT/WP02_GRAMMAR
 if not wp02_path.exists():print(json.dumps({'error':'WP02_GRAMMAR_MISSING','path':WP02_GRAMMAR},indent=2));return 3
 wp02_grammar_sha256=sha(wp02_path.read_bytes())
 phases=[]
 for name,args,target_component in PHASES:
  if not (ROOT/args[0]).exists():phases.append({'phase':name,'semantic_pass':False,'error':'MISSING_SCRIPT','path':args[0],'target_component':target_component});break
  row=command([sys.executable,*args]);row['phase']=name;row['target_component']=target_component;semantic=bool(row['process_pass'])
  if name=='strict_lalr':
   d=embedded(ROOT/STRICT);grammar_bound=d.get('grammar_sha256')==wp02_grammar_sha256 and d.get('grammar_path')==WP02_GRAMMAR;semantic=semantic and d.get('strict_build_ok') is True and not d.get('conflict_diagnostics') and grammar_bound;row['strict_receipt']={'strict_build_ok':d.get('strict_build_ok'),'conflict_diagnostics':d.get('conflict_diagnostics'),'strict_error':d.get('strict_error'),'grammar_path':d.get('grammar_path'),'grammar_sha256':d.get('grammar_sha256'),'grammar_bound_to_selected_wp02':grammar_bound}
  if name=='frontend':
   d=embedded(ROOT/FRONTEND);grammar_bound=d.get('grammar_sha256')==wp02_grammar_sha256 and d.get('grammar_path')==WP02_GRAMMAR;semantic=semantic and d.get('pass') is True and grammar_bound;row['frontend_receipt']={'pass':d.get('pass'),'grammar_path':d.get('grammar_path'),'grammar_sha256':d.get('grammar_sha256'),'grammar_bound_to_selected_wp02':grammar_bound}
  if name=='canonicalizer':
   d=embedded(ROOT/CANONICAL);grammar_bound=d.get('grammar')==WP02_GRAMMAR;semantic=semantic and d.get('pass') is True and grammar_bound;row['canonicalizer_receipt']={'pass':d.get('pass'),'grammar_path':d.get('grammar'),'grammar_bound_to_selected_wp02':grammar_bound}
  if name=='applications_proxy':
   d=embedded(ROOT/'research_entity/claycode/autonomous/BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json');row['proxy_contract']={'pass':d.get('pass'),'counts_as_target_acceptance':d.get('counts_as_target_acceptance'),'counts_as_application_acceptance_pass':d.get('counts_as_application_acceptance_pass')};semantic=semantic and d.get('pass') is True and d.get('counts_as_target_acceptance') is False and d.get('counts_as_application_acceptance_pass') is False
  row['semantic_pass']=semantic;phases.append(row)
  if not semantic:break
 auto=ROOT/'research_entity/claycode/autonomous';arts=[]
 for name in ARTIFACTS:
  p=auto/name;d=embedded(p) if p.exists() else {};arts.append({'path':str(p.relative_to(ROOT)),'missing':not p.exists(),'sha256':sha(p.read_bytes()) if p.exists() else None,'embedded_pass':d.get('pass')})
 corpus=ROOT/'research_entity/claycode/corpus/base_v1/CORPUS_MANIFEST.json';cd=embedded(corpus) if corpus.exists() else {};arts.append({'path':str(corpus.relative_to(ROOT)),'missing':not corpus.exists(),'sha256':sha(corpus.read_bytes()) if corpus.exists() else None,'embedded_pass':cd.get('pass')})
 strictp=ROOT/STRICT;sd=embedded(strictp) if strictp.exists() else {};arts.append({'path':STRICT,'missing':not strictp.exists(),'sha256':sha(strictp.read_bytes()) if strictp.exists() else None,'strict_build_ok':sd.get('strict_build_ok'),'conflict_diagnostics':sd.get('conflict_diagnostics'),'grammar_path':sd.get('grammar_path'),'grammar_sha256':sd.get('grammar_sha256')})
 target_rows=[x for x in phases if x.get('target_component')];target_components_pass=len(target_rows)==sum(1 for _,_,t in PHASES if t) and all(x['semantic_pass'] for x in target_rows)
 proxy_rows=[x for x in phases if not x.get('target_component')];proxy_preflight_pass=bool(proxy_rows) and all(x['semantic_pass'] for x in proxy_rows)
 git=command(['git','rev-parse','HEAD'],15);native=command(['cc','--version'],15)
 unresolved=[]
 if not target_components_pass:unresolved.append('TARGET_COMPONENT_BATTERY_NOT_GREEN')
 unresolved+=['CC-WP-10_REQUIRES_REAL_NON_PROXY_PER_APPLICATION_TARGET_RECEIPTS','CC-WP-13_REQUIRES_FULL_STATEFUL_FRANK_HANDOFF','CC-WP-14_REQUIRES_STRICT_ADJUDICATION_AND_FINAL_GENERAL_PURPOSE_MANIFEST']
 r={'schema_version':'2.4','created_at':datetime.now(timezone.utc).isoformat(),'target_host':'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM','target_host_checks':checks,'host':{'node':platform.node(),'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'os_release':rel},'repo_head':git,'native_compiler':native,'wp02_parser_contract':{'contract_path':str(CONTRACT_PATH.relative_to(ROOT)),'grammar_path':WP02_GRAMMAR,'grammar_sha256':wp02_grammar_sha256,'strict_receipt_path':STRICT,'frontend_receipt_path':FRONTEND,'canonicalizer_receipt_path':CANONICAL,'scope':'CC-WP-02 declarative strict/full-corpus/canonical identity selected by acceptance contract; executable typed-fn evidence remains separately versioned'},'phases':phases,'artifacts':arts,'target_component_battery_pass':target_components_pass,'runtime_v04_hardening_pass':any(x.get('phase')=='runtime_v04_hardening' and x.get('semantic_pass') for x in phases),'compiler_mainline_runtime_bridge_pass':any(x.get('phase')=='compiler_mainline_runtime_bridge' and x.get('semantic_pass') for x in phases),'concurrency_cancellation_error_pass':any(x.get('phase')=='concurrency_cancellation_error' and x.get('semantic_pass') for x in phases),'int_division_pass':any(x.get('phase')=='int_division' and x.get('semantic_pass') for x in phases),'wp10_proxy_preflight_pass':proxy_preflight_pass,'base_release_pass':False,'general_purpose_gate_pass':False,'target_acceptance_ready_for_wp14_audit':False,'unresolved':unresolved,'automatic_promotion':False,'authority_invariant':'model_output != execution_authority','scope':'Real target component evidence collector. WP02 grammar identity comes only from the target acceptance contract. Proxy application execution is explicitly non-accepting; WP10 real app receipts, full FRANK and strict WP14 adjudication remain mandatory.'}
 raw=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(raw,encoding='utf-8');print(json.dumps({'target_component_battery_pass':target_components_pass,'wp02_grammar':WP02_GRAMMAR,'wp02_grammar_sha256':wp02_grammar_sha256,'runtime_v04_hardening_pass':r['runtime_v04_hardening_pass'],'compiler_mainline_runtime_bridge_pass':r['compiler_mainline_runtime_bridge_pass'],'concurrency_cancellation_error_pass':r['concurrency_cancellation_error_pass'],'int_division_pass':r['int_division_pass'],'base_release_pass':False,'receipt':str(a.output.relative_to(ROOT)),'sha256':sha(raw.encode()),'unresolved':unresolved}));return 0 if target_components_pass else 2
if __name__=='__main__':raise SystemExit(main())