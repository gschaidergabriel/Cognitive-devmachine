#!/usr/bin/env python3
"""Regression for exact checked ClayCode Int division across evaluator and C11."""
from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import claycode_base_pure_toolchain as cc

SOURCE='''module regression.int_div
fn div(a:Int,b:Int)->Int=a/b
'''
CASES=[
 (9223372036854775807,3),
 (9223372036854775807,-3),
 (-9223372036854775807,3),
 (-9223372036854775807,-3),
 (9007199254740993,7),
 (-9007199254740993,7),
]
def trunc(a,b):
 q=abs(a)//abs(b);return -q if (a<0)!=(b<0) else q

def native_error(typed,args,expected_rc,marker):
 code=cc.lower_c(typed,'div')
 with tempfile.TemporaryDirectory(prefix='claycode_intdiv_') as td:
  td=Path(td);src=td/'prog.c';exe=td/'prog';src.write_text(code,encoding='utf-8')
  build=subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],text=True,capture_output=True,check=False)
  if build.returncode!=0:return {'pass':False,'phase':'compile','returncode':build.returncode,'stderr':build.stderr[-2000:]}
  run=subprocess.run([str(exe),*[str(x) for x in args]],text=True,capture_output=True,check=False)
  return {'pass':run.returncode==expected_rc and marker in run.stderr,'returncode':run.returncode,'stderr':run.stderr,'stdout':run.stdout}

def main()->int:
 typed=cc.compile_source(SOURCE);rows=[]
 for a,b in CASES:
  want=trunc(a,b);got=cc.evaluate(typed,'div',[a,b]);native=cc.differential(typed,'div',[a,b])
  rows.append({'a':a,'b':b,'expected':want,'evaluator':got,'native':native['native_stdout'],'pass':got==want and native['match'] and int(native['native_stdout'])==want})
 reference_zero=False
 try:cc.evaluate(typed,'div',[1,0])
 except Exception as exc:reference_zero='DIVISION_BY_ZERO' in str(exc)
 reference_overflow=False
 try:cc.evaluate(typed,'div',[-9223372036854775808,-1])
 except Exception as exc:reference_overflow='INT_DIV_OVERFLOW' in str(exc)
 native_zero=native_error(typed,[1,0],65,'CC_INT_DIV_ZERO')
 native_overflow=native_error(typed,[-9223372036854775808,-1],66,'CC_INT_DIV_OVERFLOW')
 failures=[r for r in rows if not r['pass']]
 report={
  'schema_version':'1.1','experiment':'ClayCode exact checked int64 division regression','rows':rows,
  'division_by_zero_reference_rejected':reference_zero,'int64_overflow_reference_rejected':reference_overflow,
  'division_by_zero_native':native_zero,'int64_overflow_native':native_overflow,
  'known_remaining_boundary':None,
  'pass':not failures and reference_zero and reference_overflow and native_zero['pass'] and native_overflow['pass']
 }
 out=ROOT/'research_entity/claycode/autonomous/BASE_INT_DIVISION_REGRESSION_RECEIPT.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'pass':report['pass'],'cases':len(rows),'failures':len(failures),'zero_reference':reference_zero,'overflow_reference':reference_overflow,'zero_native':native_zero['pass'],'overflow_native':native_overflow['pass']}))
 return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
