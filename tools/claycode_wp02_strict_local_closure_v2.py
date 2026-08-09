#!/usr/bin/env python3
"""Contract-driven local Ubuntu strict closure for selected CC-WP-02 grammar.

V2 intentionally limits itself to evidence that can be self-contained and grammar-bound:
selection discriminator (when required), strict LALR construction, full G9/Dialect
frontend validation, canonical syntax identity, both admitted declarative IR corpora, and
the active production canonicalizer default. It does not consume the legacy declaration
IR self-test because that receipt does not embed its grammar hash.
"""
from __future__ import annotations
import argparse,hashlib,importlib.metadata,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json'
RDIR=ROOT/'research_entity/claycode/base/receipts'
DEFAULT_OUT=RDIR/'LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->dict[str,Any]:
 x=json.loads(p.read_text(encoding='utf-8'))
 if not isinstance(x,dict):raise ValueError(f'JSON_NOT_OBJECT:{p}')
 return x
def ver(n:str)->str|None:
 try:return importlib.metadata.version(n)
 except importlib.metadata.PackageNotFoundError:return None
def osid()->str|None:
 p=Path('/etc/os-release')
 if not p.exists():return None
 for line in p.read_text(errors='replace').splitlines():
  if line.startswith('ID='):return line.split('=',1)[1].strip().strip('"').lower()
 return None
def run(argv:list[str],timeout:int=300)->dict[str,Any]:
 cp=subprocess.run([sys.executable,*argv],cwd=ROOT,text=True,capture_output=True,timeout=timeout,check=False)
 return {'argv':[sys.executable,*argv],'returncode':cp.returncode,'process_pass':cp.returncode==0,'stdout_sha256':hashlib.sha256(cp.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(cp.stderr.encode()).hexdigest(),'stdout_tail':cp.stdout[-3000:],'stderr_tail':cp.stderr[-3000:]}
def embedded_grammar(doc:dict[str,Any],fallback_path:str|None=None)->tuple[str|None,str|None]:
 p=doc.get('grammar_path') or doc.get('grammar') or fallback_path
 h=doc.get('grammar_sha256')
 ident=doc.get('identity') if isinstance(doc.get('identity'),dict) else {}
 h=h or ident.get('grammar_sha256')
 return (str(p) if p else None,str(h) if h else None)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=DEFAULT_OUT);ap.add_argument('--allow-ci',action='store_true');a=ap.parse_args()
 contract=load(CONTRACT);wp02=contract.get('wp02_parser_contract') if isinstance(contract.get('wp02_parser_contract'),dict) else {};grel=str(wp02.get('selected_grammar_path') or '');g=ROOT/grel if grel else ROOT/'__MISSING__';gsha=sha(g) if g.exists() else None
 pre={'linux':platform.system()=='Linux','ubuntu':osid()=='ubuntu','not_github_actions':a.allow_ci or os.getenv('GITHUB_ACTIONS','').lower()!='true','not_ci':a.allow_ci or os.getenv('CI','').lower() not in {'1','true','yes'},'selected_grammar_exists':bool(grel) and g.exists(),'lark_installed':ver('lark') is not None,'interegular_installed':ver('interegular') is not None}
 try:import interegular # noqa:F401
 except Exception as exc:pre['interegular_importable']=False;pre['interegular_import_error']=f'{type(exc).__name__}:{exc}'
 else:pre['interegular_importable']=True
 gh=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=False);gs=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True,check=False)
 base={'schema_version':'2.0','receipt_id':'LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE','created_at':datetime.now(timezone.utc).isoformat(),'contract':{'path':str(CONTRACT.relative_to(ROOT)),'sha256':sha(CONTRACT)},'selected_grammar':{'path':grel or None,'sha256':gsha},'host':{'node':platform.node(),'platform':platform.platform(),'python':platform.python_version(),'os_id':osid()},'packages':{'lark':ver('lark'),'interegular':ver('interegular')},'repository':{'head':gh.stdout.strip() if gh.returncode==0 else None,'dirty':bool(gs.stdout.strip()) if gs.returncode==0 else None},'preconditions':pre,'authority_invariant':'model output != execution authority','scope_guard':'Local strict selected-WP02 evidence only; physical target/apps/FULL_FRANK/WP14 remain mandatory.'}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 if not all(v is True for k,v in pre.items() if k!='interegular_import_error'):
  base.update({'components':[],'pass':False,'failure':'PRECONDITION_FAILED'});a.output.write_text(json.dumps(base,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':False,'failure':'PRECONDITION_FAILED','preconditions':pre}));return 3
 specs=[]
 if g.name=='D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark':
  specs.append(('selection_discriminator',['tools/claycode_v17_declarative_trivia_discriminator.py','--require-strict','--output','research_entity/claycode/base/receipts/LOCAL_WP02_SELECTION_DISCRIMINATOR.json'],RDIR/'LOCAL_WP02_SELECTION_DISCRIMINATOR.json','disc'))
 specs += [
  ('strict_lalr',['tools/claycode_strict_lalr_probe.py','--grammar',grel,'--output','research_entity/claycode/base/receipts/LOCAL_WP02_STRICT_LALR.json'],RDIR/'LOCAL_WP02_STRICT_LALR.json','strict'),
  ('frontend',['tools/claycode_base_frontend_validation.py','--grammar',grel,'--output','research_entity/claycode/base/receipts/LOCAL_WP02_FRONTEND.json'],RDIR/'LOCAL_WP02_FRONTEND.json','pass'),
  ('canonical',['tools/claycode_base_canonicalizer.py','--grammar',grel,'--output','research_entity/claycode/base/receipts/LOCAL_WP02_CANONICAL.json'],RDIR/'LOCAL_WP02_CANONICAL.json','pass'),
  ('decl_ir_g9',['tools/claycode_base_ir.py','research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay','--grammar',grel,'--output','research_entity/claycode/base/receipts/LOCAL_WP02_IR_G9.json'],RDIR/'LOCAL_WP02_IR_G9.json','decl'),
  ('decl_ir_dialect',['tools/claycode_base_ir.py','research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay','--grammar',grel,'--output','research_entity/claycode/base/receipts/LOCAL_WP02_IR_DIALECT.json'],RDIR/'LOCAL_WP02_IR_DIALECT.json','decl')]
 rows=[]
 for name,argv,rp,kind in specs:
  if rp.exists():rp.unlink()
  proc=run(argv);doc=load(rp) if rp.exists() else {};p,h=embedded_grammar(doc,grel if kind=='decl' else None)
  if kind=='disc':
   cand=doc.get('candidate') if isinstance(doc.get('candidate'),dict) else {};p=str(cand.get('path') or '');h=str(cand.get('sha256') or '');sem=doc.get('pass') is True and doc.get('promotion_allowed') is True and doc.get('counts_as_wp02_pass') is True
  elif kind=='strict':sem=doc.get('strict_build_ok') is True and not doc.get('conflict_diagnostics')
  elif kind=='decl':sem=bool(doc.get('declarations'))
  else:sem=doc.get('pass') is True
  bound=p==grel and h==gsha;row={'name':name,**proc,'receipt_path':str(rp.relative_to(ROOT)),'receipt_exists':rp.exists(),'receipt_sha256':sha(rp) if rp.exists() else None,'embedded_grammar_path':p,'embedded_grammar_sha256':h,'grammar_bound':bound,'semantic_pass':bool(proc['process_pass'] and rp.exists() and sem and bound)};rows.append(row)
  if not row['semantic_pass']:break
 prod=run(['tools/claycode_base_canonicalizer_validation.py'],180);pr=ROOT/str(wp02.get('canonicalizer_receipt_path') or 'research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json');pd=load(pr) if pr.exists() else {};pbound=pd.get('grammar')==grel;prow={**prod,'receipt_path':str(pr.relative_to(ROOT)),'receipt_exists':pr.exists(),'receipt_sha256':sha(pr) if pr.exists() else None,'embedded_grammar_path':pd.get('grammar'),'grammar_bound':pbound,'semantic_pass':bool(prod['process_pass'] and pd.get('pass') is True and pbound)}
 passed=len(rows)==len(specs) and all(x['semantic_pass'] for x in rows) and prow['semantic_pass'];base.update({'components':rows,'production_canonicalizer':prow,'pass':passed});
 if not passed:base['failure']='SELECTED_WP02_COMPONENT_FAILED'
 a.output.write_text(json.dumps(base,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'pass':passed,'selected_grammar':grel,'grammar_sha256':gsha,'output':str(a.output.relative_to(ROOT)),'failed':[x['name'] for x in rows if not x['semantic_pass']]+([] if prow['semantic_pass'] else ['production_canonicalizer'])}));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())