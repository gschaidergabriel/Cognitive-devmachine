#!/usr/bin/env python3
"""Regression probe for ClayCode short-circuit evaluator parity. Run from current checkout."""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
import claycode_base_pure_toolchain as cc
CASES={
 'false_and':("""module regression.shortcircuit
fn diverge(a:Bool)->Bool=diverge(a)
fn test(a:Bool)->Bool=a&&diverge(a)
""",'test',[False],False),
 'true_or':("""module regression.shortcircuit
fn diverge(a:Bool)->Bool=diverge(a)
fn test(a:Bool)->Bool=a||diverge(a)
""",'test',[True],True)
}
def main():
 rows=[]; failures=[]
 for name,(src,entry,args,want) in CASES.items():
  typed=cc.compile_source(src)
  try:
   got=cc.evaluate(typed,entry,args); ok=(got is want); err=None
  except Exception as exc:
   got=None; ok=False; err=f'{type(exc).__name__}:{exc}'
  rows.append({'case':name,'expected':want,'observed':got,'error':err,'pass':ok})
  if not ok: failures.append(name)
 print(json.dumps({'pass':not failures,'failures':failures,'rows':rows},indent=2,sort_keys=True))
 return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
