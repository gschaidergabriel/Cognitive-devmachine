#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,tempfile
from pathlib import Path
import claycode_base_package_compiler as pkg
ROOT=Path(__file__).resolve().parents[1];MAN=ROOT/'research_entity/claycode/base/examples/package_demo/manifest.json';OUT=ROOT/'research_entity/claycode/autonomous/BASE_PACKAGE_LINK_RECEIPT.json'
def main():
 checks=[]
 def c(n,ok,d=None):checks.append({'name':n,'pass':bool(ok),'detail':d})
 try:
  a=pkg.build_package(MAN);b=pkg.build_package(MAN);c('deterministic_package_hash',a['package_semantic_hash']==b['package_semantic_hash'],a['package_semantic_hash']);c('imports_resolved',all(x['imports']==[] or x['imports']==['clay.demo.math'] for x in a['modules']));c('linked_functions',{x['name'] for x in a['linked_ir']['functions']}=={'add','twice','main'});c('no_package_authority',a['authority']=='NONE')
  code=pkg.base.lower_c(a['linked_ir'],'main')
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);src=td/'x.c';exe=td/'x';src.write_text(code);cp=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],text=True,capture_output=True);rp=subprocess.run([str(exe),'20'],text=True,capture_output=True) if cp.returncode==0 else None
  c('native_package_compile',cp.returncode==0,cp.stderr[-1000:]);c('native_cross_module_call',rp is not None and rp.returncode==0 and rp.stdout.strip()=='41',rp.stdout if rp else None)
 except Exception as exc:a=None;c('package_pipeline_exception',False,repr(exc))
 # fail-closed unresolved import
 try:
  data=json.loads(MAN.read_text());data['sources']=['app.clay']
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);(td/'app.clay').write_text((MAN.parent/'app.clay').read_text());(td/'manifest.json').write_text(json.dumps(data));pkg.build_package(td/'manifest.json')
  c('unresolved_import_rejected',False,'unexpected_accept')
 except pkg.PackageError as exc:c('unresolved_import_rejected',True,str(exc))
 fails=[x['name'] for x in checks if not x['pass']];r={'schema_version':'1.0','experiment':'ClayCode BASE multi-file package/import/link validation','checks':checks,'failures':fails,'pass':not fails,'supports':['CC-WP-07-RUNTIME-ABI-FFI','CC-WP-08-STDLIB-SDK'],'scope_guard':'Unique bare symbols are linked package-wide; explicit namespace-qualified function definitions are not yet implemented. Hosted Linux is not target-host acceptance.'};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':r['pass'],'failures':fails}));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
