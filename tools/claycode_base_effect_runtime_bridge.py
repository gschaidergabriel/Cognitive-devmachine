#!/usr/bin/env python3
"""Bridge compiler-generated ClayCode effects into the selected BASE ClayRuntime.

Compiler labels remain descriptive only; actual authority is a runtime-minted opaque
handle held by this host-side bridge. Hosted Linux evidence is not target acceptance.
"""
from __future__ import annotations
import hashlib,json,sys,tempfile
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claycode_base_effect_pipeline import DEFAULT_GRAMMAR,Gateway,build,eval_function,exec_lowered
from claycode_base_runtime import CapabilityFault,ClayRuntime,RUNTIME_VERSION
from claycode_base_stdlib_extensions import install,STDLIB_EXT_VERSION
OUT=ROOT/'research_entity/claycode/autonomous/BASE_EFFECT_MAINLINE_RUNTIME_BRIDGE_RECEIPT.json'
VERSION='claycode-base-effect-runtime-bridge/0.1'
SOURCE='''module app.mainline_effect_bridge
fn write(x:Int)->Int=host.fs_write(x)
fn read(x:Int)->Int=host.fs_read(x)
fn db(x:Int)->Int=host.db_put(x)
fn net(x:Int)->Int=host.http_send(x)
fn main(x:Int)->Int=write(x)+read(x)+db(x)+net(x)
'''
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
class RuntimeGateway:
 def __init__(self,rt:ClayRuntime,handles:dict[str,Any]):self.rt=rt;self._handles=dict(handles);self.trace=[]
 def effect(self,effect:str,capability:str,value:int)->int:
  if capability not in self._handles:raise CapabilityFault('MISSING_RUNTIME_CAPABILITY:'+capability)
  h=self._handles[capability];value=int(value)
  if effect=='FS_WRITE':self.rt.invoke('fs.write_text',h,'effect/value.txt',str(value));observed=value
  elif effect=='FS_READ':observed=int(self.rt.invoke('fs.read_text',h,'effect/value.txt')['text'])+1000
  elif effect=='DB_WRITE':
   self.rt.invoke('db.sqlite_transaction',h,'effect/effects.db',[('CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY,v INTEGER)',()),('INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v',('value',value)),('SELECT v FROM kv WHERE k=?',('value',))]);observed=value*2
  elif effect=='HTTP':
   row=self.rt.invoke('http.loopback_roundtrip',h,'/effect',str(value))
   if row['status']!=200 or not row['matched']:raise RuntimeError('HTTP_EFFECT_ROUNDTRIP_MISMATCH')
   observed=value+7
  else:raise RuntimeError('UNKNOWN_EFFECT:'+effect)
  self.trace.append([effect,capability,value]);return observed
def make_runtime(td:str):
 rt=install(ClayRuntime(td));handles={'cap.fs.write':rt.mint_capability('fs.write',{'prefix':'bridge'}),'cap.fs.read':rt.mint_capability('fs.read',{'prefix':'bridge'}),'cap.db.write':rt.mint_capability('db.sqlite',{'prefix':'bridge'}),'cap.http':rt.mint_capability('net.loopback',{'host':'127.0.0.1','routes':['/effect'],'max_body_bytes':4096})};return rt,handles
def run_vector(built,value:int,root:Path):
 ref=Gateway({'cap.fs.write','cap.fs.read','cap.db.write','cap.http'});expected=eval_function(built['ir'],'main',[value],ref)
 rt1,h1=make_runtime(str(root/'interp'));gw1=RuntimeGateway(rt1,h1);oi=eval_function(built['ir'],'main',[value],gw1)
 rt2,h2=make_runtime(str(root/'lowered'));gw2=RuntimeGateway(rt2,h2);ol=exec_lowered(built['artifact'],'main',[value],gw2)
 ok=expected==oi==ol and ref.trace==gw1.trace==gw2.trace and len(rt1.trace_receipt())==4 and len(rt2.trace_receipt())==4
 return {'input':value,'expected_reference':expected,'observed_runtime_interpreter':oi,'observed_runtime_lowered':ol,'compiler_effect_trace':gw1.trace,'runtime_interpreter_trace_sha256':sha(json.dumps(rt1.trace_receipt(),sort_keys=True).encode()),'runtime_lowered_trace_sha256':sha(json.dumps(rt2.trace_receipt(),sort_keys=True).encode()),'pass':ok}
def main()->int:
 grammar=DEFAULT_GRAMMAR.read_text(encoding='utf-8');built=build(SOURCE,grammar);rows=[]
 with tempfile.TemporaryDirectory(prefix='clay_effect_runtime_bridge_') as td:
  base=Path(td)
  for i,v in enumerate([-11,0,1,7,42,1001]):rows.append(run_vector(built,v,base/str(i)))
  rt,h=make_runtime(str(base/'missing'));del h['cap.http'];missing=False
  try:eval_function(built['ir'],'main',[3],RuntimeGateway(rt,h))
  except CapabilityFault:missing=True
  rt2,h2=make_runtime(str(base/'textual'));h2['cap.http']='net.loopback';textual=False
  try:eval_function(built['ir'],'main',[3],RuntimeGateway(rt2,h2))
  except CapabilityFault:textual=True
 fails=[r['input'] for r in rows if not r['pass']];mainfn=next(f for f in built['ir']['functions'] if f['name']=='main')
 report={'schema_version':'1.0','experiment':'compiler-generated ClayCode effects -> selected mainline ClayRuntime','bridge_version':VERSION,'runtime_version':RUNTIME_VERSION,'stdlib_extension_version':STDLIB_EXT_VERSION,'effect_pipeline_version':built['candidate_version'],'source_sha256':built['source_hash'],'semantic_hash':built['semantic_hash'],'lowered_artifact_hash':built['artifact_hash'],'required_capabilities':mainfn['required_capabilities'],'effect_summary':mainfn['effect_summary'],'rows':rows,'negative_controls':{'missing_runtime_handle_rejected':missing,'textual_capability_not_authority':textual},'failures':fails,'pass':not fails and missing and textual,'supports':['CC-WP-04-TYPE-EFFECT','CC-WP-05-EVALUATOR','CC-WP-07-RUNTIME-ABI-FFI','CC-WP-08-STDLIB-SDK'],'closes_discriminator':'compiler-generated effect calls enter selected mainline ClayRuntime rather than proxy Gateway','counts_as_target_acceptance':False,'counts_as_full_work_package_pass':False,'authority_invariant':'compiler labels/descriptors never authorize; only runtime-minted opaque handle possession authorizes','next_required':'rerun on Andreas Ubuntu target and close child-process/context-budget/TOCTOU discriminators'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'pass':report['pass'],'rows':len(rows),'failures':fails,'negative_controls':report['negative_controls']}));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
