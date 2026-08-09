#!/usr/bin/env python3
"""Executable gate for ClayCode BASE typed pure-core vertical slice.

Produces evidence for the WP03->WP06 path without promoting whole work packages.
"""
from __future__ import annotations
import json, shutil
from pathlib import Path
import claycode_base_pure_toolchain as cc

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'research_entity/claycode/base/examples/PURE_CORE_V1.clay'
OUT=ROOT/'research_entity/claycode/autonomous/BASE_PURE_TOOLCHAIN_RECEIPT.json'

def main()->int:
    checks=[]
    def add(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
    src=FIXTURE.read_text(encoding='utf-8')
    try:
        typed=cc.compile_source(src)
        add('typed_ir_constructed',typed['ir_schema']=='ClayCodeTypedPureIR/v1',typed['semantic_hash'])
        add('pure_effect_summary_empty',typed['typed_ir']['effect_summary']==[])
        fns={f['name']:f for f in typed['typed_ir']['functions']}
        add('all_fixture_functions_typed',set(fns)=={'add','muladd','positive','same','both','ratio','twice'},sorted(fns))
        add('declared_return_types_preserved',{k:v['return_type'] for k,v in fns.items()}=={'add':'Int','muladd':'Int','positive':'Bool','same':'Bool','both':'Bool','ratio':'Real','twice':'Int'})
        add('interpreter_add',cc.evaluate(typed,'add',[2,3])==5)
        # Grammar is intentionally left-folded; the backend must not inherit C precedence.
        add('interpreter_left_fold_semantics',cc.evaluate(typed,'muladd',[2,3,4])==20)
        add('interpreter_call',cc.evaluate(typed,'twice',[9])==18)
        add('interpreter_bool',cc.evaluate(typed,'positive',[-1]) is False and cc.evaluate(typed,'positive',[1]) is True)
        add('interpreter_division',cc.evaluate(typed,'ratio',[5,2])==2.5)
    except Exception as exc:
        typed=None; add('typed_pipeline_exception',False,repr(exc))

    # Typed semantic identity must ignore formatting/comments yet discriminate operators.
    try:
        a=cc.compile_source('module x\nfn add(a:Int,b:Int)->Int=a+b\n')
        b=cc.compile_source('// layout\nmodule   x\n\nfn add ( a : Int , b : Int ) -> Int = a + b\n')
        m=cc.compile_source('module x\nfn add(a:Int,b:Int)->Int=a-b\n')
        add('typed_hash_layout_equivalence',a['semantic_hash']==b['semantic_hash'],{'a':a['semantic_hash'],'b':b['semantic_hash']})
        add('typed_hash_operator_discrimination',a['semantic_hash']!=m['semantic_hash'],{'base':a['semantic_hash'],'mutated':m['semantic_hash']})
    except Exception as exc:add('typed_identity_exception',False,repr(exc))

    # Fail closed on type errors and ambient/unknown effectful symbols.
    negatives={
        'return_type_mismatch':'module x\nfn bad(a:Int)->Bool=a+1\n',
        'unknown_name':'module x\nfn bad(a:Int)->Int=a+missing\n',
        'unknown_call_no_ambient_authority':'module x\nfn bad(a:Int)->Int=host.file_read(a)\n',
        'argument_type_mismatch':'module x\nfn id(a:Int)->Int=a\nfn bad(b:Bool)->Int=id(b)\n',
    }
    for name,source in negatives.items():
        try:
            cc.compile_source(source); add(name,False,'unexpected_accept')
        except cc.ClayError as exc:add(name,True,type(exc).__name__)
        except Exception as exc:add(name,False,'wrong_exception:'+repr(exc))

    # Native C differential is required; no compiler means this gate is not green.
    native=[]
    if typed is not None and shutil.which('cc'):
        cases=[('add',[2,3]),('muladd',[2,3,4]),('twice',[9]),('positive',[-7]),('same',[4,4]),('both',[True,False]),('ratio',[5,2])]
        for entry,args in cases:
            try:
                row=cc.differential(typed,entry,args); native.append(row); add('native_'+entry,row['match'],row)
            except Exception as exc:add('native_'+entry,False,repr(exc))
    else:add('native_c_compiler_available',False,shutil.which('cc'))

    failures=[x['name'] for x in checks if not x['pass']]
    out={
        'schema_version':'1.0',
        'experiment':'ClayCode BASE typed pure-core integrated native differential',
        'fixture':str(FIXTURE.relative_to(ROOT)),
        'compiler_version':cc.VERSION,
        'grammar':str(cc.GRAMMAR.relative_to(ROOT)),
        'checks':checks,
        'native_differentials':native,
        'passed':len(checks)-len(failures),'total':len(checks),'failures':failures,'pass':not failures,
        'work_package_evidence':{
            'CC-WP-03-IR-TYPES':'typed scalar/function IR + semantic hash + mutation/layout identity',
            'CC-WP-04-TYPE-EFFECT':'function/argument/return checking; unknown host/effect symbol fails closed; pure effect summary',
            'CC-WP-05-EVALUATOR':'reference evaluator for typed pure function core',
            'CC-WP-06-COMPILER-LOWERING':'C11 lowering + actual cc compile/execute + evaluator/native differential'
        },
        'scope_guard':'PASS proves the integrated typed pure-core vertical slice only. It does not close complete WP03-06, which still require collections/epistemic state/effects/runtime/FFI/general application coverage and target-host receipts.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'pass':out['pass'],'passed':out['passed'],'total':out['total'],'failures':failures,'out':str(OUT.relative_to(ROOT))}))
    return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
