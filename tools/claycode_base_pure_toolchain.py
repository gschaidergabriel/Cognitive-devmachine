#!/usr/bin/env python3
"""Compatibility facade over the integrated ClayCode BASE pure compiler.

There must be one executable arithmetic/type semantics, not two. This module keeps the
API used by existing validation/application gates while delegating parse, typecheck,
reference evaluation and C lowering to tools/claycode_base_compiler.py.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from typing import Any
import claycode_base_compiler as base

ROOT=Path(__file__).resolve().parents[1]
GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
VERSION='claycode-base-pure-toolchain/0.2-integrated'
ClayError=base.CompileError
TypeFailure=base.CompileError
Unsupported=base.CompileError

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def _compat_ir(ir:dict[str,Any])->dict[str,Any]:
 return {'kind':'TypedProgram','module':None,'functions':[{'kind':'Function','name':f['name'],'params':f['params'],'return_type':f['return'],'body':f['body'],'effects':[]} for f in ir['functions']],'effect_summary':[]}

def compile_source(source:str)->dict[str,Any]:
 grammar=GRAMMAR.read_text(encoding='utf-8');built=base.build(source,grammar)
 return {'schema_version':'1.1','ir_schema':'claycode.typed-ir.v0','compiler_version':VERSION,'semantic_hash':built['semantic_hash'],'source_sha256':built['source_hash'],'grammar_sha256':built['grammar_hash'],'base_ir':built['ir'],'typed_ir':_compat_ir(built['ir'])}

def evaluate(typed:dict[str,Any],entry:str,args:list[Any])->Any:return base.eval_function(typed['base_ir'],entry,args)
def lower_c(typed:dict[str,Any],entry:str|None=None)->str:return base.lower_c(typed['base_ir'],entry)

def _arg_text(value:Any,type_name:str)->str:
 if type_name=='Bool':return '1' if bool(value) else '0'
 if type_name=='Int':return str(int(value))
 if type_name=='Real':return format(float(value),'.17g')
 raise ClayError('ENTRY_ARG_TYPE_UNSUPPORTED')
def _expected_text(value:Any,type_name:str)->str:
 if type_name=='Bool':return '1' if bool(value) else '0'
 if type_name=='Int':return str(int(value))
 if type_name=='Real':return format(float(value),'.17g')
 if type_name=='String':return str(value)
 raise ClayError('ENTRY_RETURN_TYPE_UNSUPPORTED')

def differential(typed:dict[str,Any],entry:str,args:list[Any],cc:str='cc')->dict[str,Any]:
 funcs={f['name']:f for f in typed['base_ir']['functions']}
 if entry not in funcs:raise ClayError(f'UNDEFINED_ENTRY:{entry}')
 fn=funcs[entry]
 if len(args)!=len(fn['params']):raise ClayError(f'ARITY_MISMATCH:{entry}')
 expected=evaluate(typed,entry,args);code=lower_c(typed,entry)
 with tempfile.TemporaryDirectory(prefix='claycode-base-') as td:
  td=Path(td);c=td/'program.c';exe=td/'program';c.write_text(code,encoding='utf-8')
  cp=subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],text=True,capture_output=True,check=False)
  if cp.returncode:raise ClayError('C_COMPILE_FAILED:'+cp.stderr[-2000:])
  argv=[str(exe)]+[_arg_text(v,p['type']) for v,p in zip(args,fn['params'])]
  rp=subprocess.run(argv,text=True,capture_output=True,check=False)
  if rp.returncode:raise ClayError(f'NATIVE_EXEC_FAILED:{rp.returncode}:{rp.stderr[-1000:]}')
 observed=rp.stdout.strip();expected_text=_expected_text(expected,fn['return'])
 return {'entry':entry,'args':args,'interpreter_result':expected,'native_stdout':observed,'expected_stdout':expected_text,'match':observed==expected_text,'generated_c_sha256':sha(code.encode()),'semantic_hash':typed['semantic_hash']}

def parse_arg(raw:str,type_name:str)->Any:
 if type_name=='Int':return int(raw)
 if type_name=='Real':return float(raw)
 if type_name=='Bool':
  if raw.lower() in {'1','true'}:return True
  if raw.lower() in {'0','false'}:return False
 raise ClayError(f'BAD_CLI_ARG:{type_name}:{raw}')
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--emit',choices=['typed-ir','c'],default='typed-ir');ap.add_argument('--entry');ap.add_argument('--arg',action='append',default=[]);ap.add_argument('--native-differential',action='store_true');ap.add_argument('--output',type=Path);a=ap.parse_args();typed=compile_source(a.source.read_text(encoding='utf-8'))
 if a.native_differential:
  if not a.entry:raise ClayError('ENTRY_REQUIRED')
  fn=next(f for f in typed['base_ir']['functions'] if f['name']==a.entry);vals=[parse_arg(v,p['type']) for v,p in zip(a.arg,fn['params'])];text=json.dumps(differential(typed,a.entry,vals),indent=2,sort_keys=True)+'\n'
 elif a.emit=='c':text=lower_c(typed,a.entry)
 else:text=json.dumps(typed,indent=2,sort_keys=True)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
 else:print(text,end='')
 return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except ClayError as exc:print(json.dumps({'error':'CompileError','message':str(exc)}));raise SystemExit(2)
