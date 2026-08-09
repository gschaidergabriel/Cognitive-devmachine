#!/usr/bin/env python3
"""Regression for exact truncating ClayCode Int division across evaluator and C11."""
from __future__ import annotations
import json,sys
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

def main()->int:
 typed=cc.compile_source(SOURCE);rows=[]
 for a,b in CASES:
  want=trunc(a,b);got=cc.evaluate(typed,'div',[a,b]);native=cc.differential(typed,'div',[a,b])
  rows.append({'a':a,'b':b,'expected':want,'evaluator':got,'native':native['native_stdout'],'pass':got==want and native['match'] and int(native['native_stdout'])==want})
 zero_rejected=False
 try:cc.evaluate(typed,'div',[1,0])
 except Exception:zero_rejected=True
 failures=[r for r in rows if not r['pass']]
 report={'schema_version':'1.0','experiment':'ClayCode exact int64 division regression','rows':rows,'division_by_zero_reference_rejected':zero_rejected,'known_remaining_boundary':'INT64_MIN/-1 requires structured overflow/error semantics before WP09 PASS','pass':not failures and zero_rejected}
 out=ROOT/'research_entity/claycode/autonomous/BASE_INT_DIVISION_REGRESSION_RECEIPT.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'pass':report['pass'],'cases':len(rows),'failures':len(failures),'zero_rejected':zero_rejected}))
 return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
