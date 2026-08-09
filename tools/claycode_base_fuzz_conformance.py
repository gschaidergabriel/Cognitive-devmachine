#!/usr/bin/env python3
"""Deterministic ClayCode BASE compiler/runtime fuzz and conformance gate."""
from __future__ import annotations
import json, random, tempfile
from pathlib import Path
import claycode_base_pure_toolchain as cc
from claycode_base_runtime import ClayRuntime, CapabilityFault
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research_entity/claycode/autonomous/BASE_FUZZ_CONFORMANCE_RECEIPT.json'
SEED=0xC1A7C0DE

def oracle(op,a,b):
 if op=='+':return a+b
 if op=='-':return a-b
 if op=='*':return a*b
 raise AssertionError(op)

def main():
 rng=random.Random(SEED);fail=[];cases=0
 # 1200 independently generated source/type/evaluator cases.
 for i in range(1200):
  op=rng.choice(['+','-','*']);a=rng.randint(-10000,10000);b=rng.randint(-10000,10000)
  src=f'module fuzz.m{i}\nfn main(a:Int,b:Int)->Int=a{op}b\n'
  try:
   typed=cc.compile_source(src);got=cc.evaluate(typed,'main',[a,b]);want=oracle(op,a,b);cases+=1
   if got!=want:fail.append({'case':i,'kind':'evaluator','got':got,'want':want,'source':src})
  except Exception as exc:fail.append({'case':i,'kind':'unexpected_exception','error':repr(exc),'source':src})
 # Native translation validation on bounded sample.
 native=[]
 for i in range(24):
  op=rng.choice(['+','-','*']);a=rng.randint(-1000,1000);b=rng.randint(-1000,1000);src=f'module fuzz.native{i}\nfn main(a:Int,b:Int)->Int=a{op}b\n'
  try:
   row=cc.differential(cc.compile_source(src),'main',[a,b]);native.append(row)
   if not row['match']:fail.append({'case':i,'kind':'native_translation','row':row})
  except Exception as exc:fail.append({'case':i,'kind':'native_exception','error':repr(exc)})
 # Negative type corpus must fail closed.
 negatives=['module n\nfn bad(a:Int)->Bool=a+1\n','module n\nfn bad(a:Int)->Int=a+missing\n','module n\nfn id(a:Int)->Int=a\nfn bad(b:Bool)->Int=id(b)\n']
 for i,s in enumerate(negatives):
  try:cc.compile_source(s);fail.append({'case':i,'kind':'negative_unexpected_accept'})
  except cc.ClayError:pass
  except Exception as exc:fail.append({'case':i,'kind':'negative_wrong_exception','error':repr(exc)})
 # Runtime forgery/revocation/path/policy fuzz.
 auth_cases=0
 with tempfile.TemporaryDirectory(prefix='clay_fuzz_') as td:
  rt=ClayRuntime(td);cap=rt.mint_capability('fs.write',{'prefix':'data'})
  for i in range(1000):
   auth_cases+=1
   fake=rng.choice(['fs.write',{'kind':'fs.write'},None,rng.randint(-100,100)])
   try:rt.invoke('fs.write_text',fake,f'x{i}.txt','bad');fail.append({'case':i,'kind':'forged_capability_accepted'})
   except CapabilityFault:pass
   except Exception as exc:fail.append({'case':i,'kind':'forgery_wrong_exception','error':repr(exc)})
  # All path traversal variants must fail.
  for i,p in enumerate(['../x','../../x','a/../../../x','/tmp/x']):
   try:rt.invoke('fs.write_text',cap,p,'bad');fail.append({'case':i,'kind':'path_escape_accepted','path':p})
   except Exception:pass
  rt.revoke(cap)
  try:rt.invoke('fs.write_text',cap,'x','bad');fail.append({'kind':'revoked_accepted'})
  except CapabilityFault:pass
 report={'schema_version':'1.0','experiment':'ClayCode BASE deterministic compiler/runtime fuzz conformance','seed':SEED,'evaluator_cases':cases,'native_translation_cases':len(native),'authority_forgery_cases':auth_cases,'negative_type_cases':len(negatives),'failures':fail[:100],'failure_count':len(fail),'pass':not fail,'scope_guard':'Hosted Linux fuzz evidence; target-host rerun remains required for BASE promotion.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':report['pass'],'failure_count':len(fail),'evaluator_cases':cases,'authority_cases':auth_cases}));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
