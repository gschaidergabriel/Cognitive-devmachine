#!/usr/bin/env python3
"""Executable gate for the consolidated ClayCode BASE pure compiler path."""
from __future__ import annotations
import json,shutil
from pathlib import Path
import claycode_base_pure_toolchain as cc
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'research_entity/claycode/base/examples/PURE_CORE_V1.clay';OUT=ROOT/'research_entity/claycode/autonomous/BASE_PURE_TOOLCHAIN_RECEIPT.json'
def main()->int:
 checks=[]
 def add(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
 try:
  typed=cc.compile_source(FIXTURE.read_text());add('typed_ir_constructed',typed['ir_schema']=='claycode.typed-ir.v0',typed['semantic_hash']);add('pure_effect_summary_empty',typed['typed_ir']['effect_summary']==[]);fns={f['name']:f for f in typed['typed_ir']['functions']};add('all_fixture_functions_typed',set(fns)=={'add','muladd','positive','same','both','ratio','twice'},sorted(fns));add('declared_return_types_preserved',{k:v['return_type'] for k,v in fns.items()}=={'add':'Int','muladd':'Int','positive':'Bool','same':'Bool','both':'Bool','ratio':'Int','twice':'Int'});add('interpreter_add',cc.evaluate(typed,'add',[2,3])==5);add('interpreter_left_fold_semantics',cc.evaluate(typed,'muladd',[2,3,4])==20);add('interpreter_call',cc.evaluate(typed,'twice',[9])==18);add('interpreter_bool',cc.evaluate(typed,'positive',[-1]) is False and cc.evaluate(typed,'positive',[1]) is True);add('interpreter_int_division',cc.evaluate(typed,'ratio',[5,2])==2)
 except Exception as exc:typed=None;add('typed_pipeline_exception',False,repr(exc))
 try:
  a=cc.compile_source('module x\nfn add(a:Int,b:Int)->Int=a+b\n');b=cc.compile_source('// layout\nmodule   x\n\nfn add ( a : Int , b : Int ) -> Int = a + b\n');m=cc.compile_source('module x\nfn add(a:Int,b:Int)->Int=a-b\n');add('typed_hash_layout_equivalence',a['semantic_hash']==b['semantic_hash'],{'a':a['semantic_hash'],'b':b['semantic_hash']});add('typed_hash_operator_discrimination',a['semantic_hash']!=m['semantic_hash'],{'base':a['semantic_hash'],'mutated':m['semantic_hash']})
 except Exception as exc:add('typed_identity_exception',False,repr(exc))
 for name,source in {'return_type_mismatch':'module x\nfn bad(a:Int)->Bool=a+1\n','unknown_name':'module x\nfn bad(a:Int)->Int=a+missing\n','unknown_call_no_ambient_authority':'module x\nfn bad(a:Int)->Int=host.file_read(a)\n','argument_type_mismatch':'module x\nfn id(a:Int)->Int=a\nfn bad(b:Bool)->Int=id(b)\n'}.items():
  try:cc.compile_source(source);add(name,False,'unexpected_accept')
  except cc.ClayError as exc:add(name,True,type(exc).__name__)
  except Exception as exc:add(name,False,'wrong_exception:'+repr(exc))
 native=[]
 if typed is not None and shutil.which('cc'):
  for entry,args in [('add',[2,3]),('muladd',[2,3,4]),('twice',[9]),('positive',[-7]),('same',[4,4]),('both',[True,False]),('ratio',[5,2])]:
   try:row=cc.differential(typed,entry,args);native.append(row);add('native_'+entry,row['match'],row)
   except Exception as exc:add('native_'+entry,False,repr(exc))
 else:add('native_c_compiler_available',False,shutil.which('cc'))
 failures=[x['name'] for x in checks if not x['pass']];out={'schema_version':'1.1','experiment':'ClayCode BASE consolidated pure compiler native differential','fixture':str(FIXTURE.relative_to(ROOT)),'compiler_version':cc.VERSION,'grammar':str(cc.GRAMMAR.relative_to(ROOT)),'checks':checks,'native_differentials':native,'passed':len(checks)-len(failures),'total':len(checks),'failures':failures,'pass':not failures,'semantic_consolidation':'Uses tools/claycode_base_compiler.py as the single arithmetic/type/evaluator/lowering implementation; no divergent division semantics.','work_package_evidence':{'CC-WP-03-IR-TYPES':'typed scalar/function IR + semantic hash + mutation/layout identity','CC-WP-04-TYPE-EFFECT':'function/argument/return checking; unknown host symbol fails closed','CC-WP-05-EVALUATOR':'reference evaluator','CC-WP-06-COMPILER-LOWERING':'C11 lowering + actual cc differential'},'scope_guard':'PASS proves the integrated pure-core vertical slice only; effect/runtime/general apps and Andreas target receipts remain separate gates.'};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'pass':out['pass'],'passed':out['passed'],'total':out['total'],'failures':failures}));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
