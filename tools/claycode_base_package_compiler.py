#!/usr/bin/env python3
"""Deterministic multi-file ClayCode BASE package linker.

Package manifests bind exact source files. Each module is parsed with V7, imports are
resolved inside the manifest, function symbols are linked once, then the existing BASE
compiler performs one global typecheck so imported functions can be called by their
unique bare symbol. No package/import text grants host authority.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any
from lark import Lark,Tree
import claycode_base_compiler as base
ROOT=Path(__file__).resolve().parents[1]
GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
VERSION='claycode-base-package-linker/0.1'
class PackageError(base.CompileError):pass
def sha(b):return hashlib.sha256(b).hexdigest()
def _decl_qid(node:Tree)->str:
 qs=[x for x in node.children if isinstance(x,Tree) and str(x.data)=='qid']
 if not qs:raise PackageError(f'MISSING_QID:{node.data}')
 return base.qid_name(qs[-1])
def inspect_module(source:str,grammar:str)->dict[str,Any]:
 p=Lark(grammar,parser='lalr',lexer='contextual',start='start');t=p.parse(source);mods=list(t.find_data('module_decl'));imports=list(t.find_data('import_decl'))
 if len(mods)!=1:raise PackageError(f'EXACTLY_ONE_MODULE_REQUIRED:{len(mods)}')
 return {'module':_decl_qid(mods[0]),'imports':sorted({_decl_qid(x) for x in imports})}
def build_package(manifest_path:Path)->dict[str,Any]:
 manifest=json.loads(manifest_path.read_text(encoding='utf-8'));package=manifest.get('package');version=manifest.get('version');source_names=manifest.get('sources')
 if not isinstance(package,str) or not package or not isinstance(version,str) or not isinstance(source_names,list) or not source_names:raise PackageError('BAD_PACKAGE_MANIFEST')
 grammar=GRAMMAR.read_text(encoding='utf-8');modules=[];functions=[];seen_modules=set();base_dir=manifest_path.parent
 for rel in source_names:
  if not isinstance(rel,str):raise PackageError('SOURCE_PATH_NOT_STRING')
  path=(base_dir/rel).resolve()
  try:path.relative_to(base_dir.resolve())
  except ValueError as exc:raise PackageError('PACKAGE_SOURCE_ESCAPE') from exc
  source=path.read_text(encoding='utf-8');meta=inspect_module(source,grammar)
  if meta['module'] in seen_modules:raise PackageError(f'DUPLICATE_MODULE:{meta["module"]}')
  seen_modules.add(meta['module']);program=base.parse_program(source,grammar);functions.extend(program['functions']);modules.append({'module':meta['module'],'imports':meta['imports'],'path':rel,'source_sha256':sha(source.encode())})
 for row in modules:
  for imp in row['imports']:
   if imp not in seen_modules:raise PackageError(f'UNRESOLVED_IMPORT:{row["module"]}:{imp}')
 ir=base.compile_ir({'functions':functions});entry=manifest.get('entry',{});entry_fn=entry.get('function') if isinstance(entry,dict) else None;entry_module=entry.get('module') if isinstance(entry,dict) else None
 if entry_module not in seen_modules:raise PackageError(f'ENTRY_MODULE_MISSING:{entry_module}')
 if entry_fn not in {f['name'] for f in ir['functions']}:raise PackageError(f'ENTRY_FUNCTION_MISSING:{entry_fn}')
 core={'schema':'claycode.package.v0','package':package,'version':version,'modules':sorted(modules,key=lambda x:x['module']),'entry':{'module':entry_module,'function':entry_fn},'linked_ir':ir,'authority':'NONE'};raw=json.dumps(core,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();return {'schema_version':'1.0','linker_version':VERSION,'grammar_sha256':sha(grammar.encode()),'manifest_sha256':sha(manifest_path.read_bytes()),'package_semantic_hash':sha(b'ClayCodePackage/v0\0'+raw),**core}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('--emit-json',type=Path);ap.add_argument('--emit-c',type=Path);a=ap.parse_args();pkg=build_package(a.manifest);render=json.dumps(pkg,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
 if a.emit_json:a.emit_json.parent.mkdir(parents=True,exist_ok=True);a.emit_json.write_text(render,encoding='utf-8')
 if a.emit_c:a.emit_c.parent.mkdir(parents=True,exist_ok=True);a.emit_c.write_text(base.lower_c(pkg['linked_ir'],pkg['entry']['function']),encoding='utf-8')
 if not a.emit_json:print(render,end='');return 0
if __name__=='__main__':raise SystemExit(main())
