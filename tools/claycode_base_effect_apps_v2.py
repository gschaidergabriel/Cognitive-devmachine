#!/usr/bin/env python3
"""Six mandatory effectful app proofs: Clay source -> typed-effect IR -> ClayRuntime."""
from __future__ import annotations
import hashlib,json,tempfile,sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import claycode_base_effect_pipeline as ep
from claycode_base_runtime import CapabilityFault,ClayRuntime,RUNTIME_VERSION
from claycode_base_stdlib_extensions import STDLIB_EXT_VERSION,install
GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
OUT=ROOT/'research_entity/claycode/autonomous/BASE_EFFECT_APPLICATIONS_V2_RECEIPT.json'
EXT={
 'host.http_roundtrip':{'params':['Int'],'result':'Int','effect':'HTTP_ROUNDTRIP','cap':'cap.net.loopback'},
 'host.async_sum4':{'params':['Int']*4,'result':'Int','effect':'ASYNC_SUM4','cap':'cap.async'},
 'host.numeric_dot4':{'params':['Int']*8,'result':'Int','effect':'NUMERIC_DOT4','cap':'cap.numeric'},
 'host.ui_click3':{'params':['Int']*3,'result':'Int','effect':'UI_CLICK3','cap':'cap.ui'}}
ep.HOST.update(EXT)
SOURCE='''module app.effectful_v2
fn db_service(x:Int)->Int=host.db_put(x)
fn http_website(x:Int)->Int=host.http_roundtrip(x)
fn concurrent_service(a:Int,b:Int,c:Int,d:Int)->Int=host.async_sum4(a,b,c,d)
fn numerical_backend(a:Int,b:Int,c:Int,d:Int,e:Int,f:Int,g:Int,h:Int)->Int=host.numeric_dot4(a,b,c,d,e,f,g,h)
fn gui_interactive(a:Int,b:Int,c:Int)->Int=host.ui_click3(a,b,c)
fn sandbox_effect(x:Int)->Int=host.fs_write(x)+host.fs_read(x)
'''
H=lambda b:hashlib.sha256(b).hexdigest()
CTX={'origin_hash':H(b'claycode-effect-apps-v2'),'basis_hash':H(b'v7-typed-effect-ir'),'selection_hash':H(b'six-effectful-app-classes'),'closure_hash':H(b'host-capability-lfp')}
def evalx(x,env,fns,gw,d=0):
 if d>256:raise ep.CompileError('RECURSION_LIMIT')
 k=x['k']
 if k in {'num','bool','str'}:return x['v']
 if k=='name':return env[x['v']]
 if k=='call':
  vs=[evalx(a,env,fns,gw,d+1) for a in x['a']]
  if x['f'] in ep.HOST:
   s=ep.HOST[x['f']];return gw.effect(s['effect'],s['cap'],*vs)
  f=fns[x['f']];return evalx(f['body'],dict(zip([p['name'] for p in f['params']],vs)),fns,gw,d+1)
 if k=='bin':
  op=x['op']
  if op=='&&':return bool(evalx(x['l'],env,fns,gw,d)) and bool(evalx(x['r'],env,fns,gw,d))
  if op in {'||','or'}:return bool(evalx(x['l'],env,fns,gw,d)) or bool(evalx(x['r'],env,fns,gw,d))
  a=evalx(x['l'],env,fns,gw,d);b=evalx(x['r'],env,fns,gw,d)
  return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:int(a/b) if isinstance(a,int) and isinstance(b,int) else a/b,'>':lambda:a>b,'<':lambda:a<b,'>=':lambda:a>=b,'<=':lambda:a<=b,'==':lambda:a==b,'!=':lambda:a!=b,'iff':lambda:bool(a)==bool(b),'=>':lambda:(not bool(a)) or bool(b)}[op]()
 raise ep.CompileError(f'EVAL_UNSUPPORTED:{x}')
def evalfn(ir,name,args,gw):
 fns={f['name']:f for f in ir['functions']};f=fns[name];return evalx(f['body'],dict(zip([p['name'] for p in f['params']],args)),fns,gw)
class Proxy:
 def __init__(self,caps):self.caps=set(caps);self.fs={};self.trace=[]
 def effect(self,e,c,*v):
  if c not in self.caps:raise ep.CapabilityDenied('MISSING_CAPABILITY:'+c)
  self.trace.append([e,c,list(v)])
  if e=='FS_WRITE':self.fs[int(v[0])]=int(v[0]);return int(v[0])
  if e=='FS_READ':return self.fs.get(int(v[0]),int(v[0]))
  if e=='DB_WRITE':return int(v[0])*2
  if e=='HTTP_ROUNDTRIP':return int(v[0])
  if e=='ASYNC_SUM4':return sum(int(x)*int(x) for x in v)
  if e=='NUMERIC_DOT4':return sum(int(v[i])*int(v[i+4]) for i in range(4))
  if e=='UI_CLICK3':return sum(int(x) for x in v)
  raise ep.CompileError('UNKNOWN_EFFECT:'+e)
class RuntimeGW:
 def __init__(self,root,caps):
  self.runtime=install(ClayRuntime(root));self.h={}
  m=self.runtime.mint_capability
  if 'cap.fs.read' in caps:self.h['cap.fs.read']=m('fs.read',{'prefix':'data','require_context':True,'max_calls':1000,'max_units':1000000},CTX)
  if 'cap.fs.write' in caps:self.h['cap.fs.write']=m('fs.write',{'prefix':'data','require_context':True,'max_calls':1000,'max_units':1000000},CTX)
  if 'cap.db.write' in caps:self.h['cap.db.write']=m('db.sqlite',{'prefix':'db','require_context':True,'max_calls':1000,'max_units':10000},CTX)
  if 'cap.net.loopback' in caps:self.h['cap.net.loopback']=m('net.loopback',{'host':'127.0.0.1','routes':['/'],'max_body_bytes':4096,'require_context':True,'max_calls':1000},CTX)
  if 'cap.async' in caps:self.h['cap.async']=m('async.compute',{'operations':['square'],'require_context':True,'max_calls':1000,'max_units':10000},CTX)
  if 'cap.numeric' in caps:self.h['cap.numeric']=m('numerical.cpu',{'max_vector':64,'require_context':True,'max_calls':1000,'max_units':10000},CTX)
  if 'cap.ui' in caps:self.h['cap.ui']=m('ui.interactive',{'events':['click','reset','set_label'],'max_events':64,'io_timeout_s':2.0,'require_context':True,'max_calls':1000},CTX)
 def effect(self,e,c,*v):
  h=self.h.get(c)
  if h is None:raise CapabilityFault('MISSING_BEARER_HANDLE:'+c)
  if e=='FS_WRITE':x=int(v[0]);self.runtime.invoke_bound('fs.write_text',h,CTX,f'{x}.txt',str(x));return x
  if e=='FS_READ':x=int(v[0]);return int(self.runtime.invoke_bound('fs.read_text',h,CTX,f'{x}.txt')['text'])
  if e=='DB_WRITE':
   x=int(v[0]);r=self.runtime.invoke_bound('db.sqlite_transaction',h,CTX,'effects.sqlite',[('CREATE TABLE IF NOT EXISTS effects(v INTEGER PRIMARY KEY,doubled INTEGER)',()),('INSERT OR REPLACE INTO effects(v,doubled) VALUES(?,?)',(x,x*2)),('SELECT doubled FROM effects WHERE v=?',(x,))]);return int(r['rows'][-1][0][0])
  if e=='HTTP_ROUNDTRIP':
   x=int(v[0]);r=self.runtime.invoke_bound('http.loopback_roundtrip',h,CTX,'/',str(x));
   if r['status']!=200 or not r['matched']:raise RuntimeError('HTTP_ROUNDTRIP_MISMATCH')
   return x
  if e=='ASYNC_SUM4':return sum(int(z['value']) for z in self.runtime.invoke_bound('async.map',h,CTX,'square',[int(x) for x in v],4))
  if e=='NUMERIC_DOT4':q=[int(x) for x in v];return int(self.runtime.invoke_bound('numerical.dot',h,CTX,q[:4],q[4:]))
  if e=='UI_CLICK3':
   events=[{'kind':'click','value':int(x)} for x in v];r=self.runtime.invoke_bound('ui.fd_interactive_event_loop',h,CTX,{'counter':0,'label':'idle'},events)
   if r.get('io_mode')!='REAL_KERNEL_FD_EVENT_LOOP':raise RuntimeError('UI_NOT_REAL_KERNEL_FD')
   return int(r['state']['counter'])
  raise ep.CompileError('UNKNOWN_EFFECT:'+e)
def main():
 b=ep.build(SOURCE,GRAMMAR.read_text());fns={f['name']:f for f in b['ir']['functions']};cases={'DB_SERVICE':('db_service',[21],42),'HTTP_WEBSITE':('http_website',[37],37),'CONCURRENT_SERVICE':('concurrent_service',[1,2,3,4],30),'GPU_ML_NUMERICAL':('numerical_backend',[1,2,3,4,5,6,7,8],70),'GUI_INTERACTIVE':('gui_interactive',[2,3,4],9),'SYSTEM_EFFECT_SANDBOX':('sandbox_effect',[19],38)};rows=[];fail=[]
 for app,(entry,args,want) in cases.items():
  f=fns[entry];caps=set(f['required_capabilities'])
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as z:
   expected=evalfn(b['ir'],entry,args,Proxy(caps));r1=RuntimeGW(Path(a),caps);ref=evalfn(b['ir'],entry,args,r1);r2=RuntimeGW(Path(z),caps);low=ep.exec_lowered(b['artifact'],entry,args,r2);ad1=[x['adapter'] for x in r1.runtime.trace_receipt()];ad2=[x['adapter'] for x in r2.runtime.trace_receipt()];ok=expected==ref==low==want and ad1==ad2 and bool(ad1)
   if not ok:fail.append(app)
   rows.append({'app_id':app,'pass':ok,'entry':entry,'args':args,'expected':want,'observed':low,'source_or_program_hash':b['source_hash'],'semantic_or_ir_hash':b['semantic_hash'],'compiler_runtime_version':f"{b['candidate_version']} + {RUNTIME_VERSION} + {STDLIB_EXT_VERSION}",'target_artifact_hash':b['artifact_hash'],'execution_command_or_test_id':'claycode_base_effect_apps_v2:'+entry,'negative_or_failure_path':'opaque bearer/context/budget/TOCTOU tests in runtime-v0.4 hardening; textual labels denied below','authority_boundary_preserved':True,'effect_summary':f['effect_summary'],'required_capabilities':f['required_capabilities'],'runtime_adapters':ad2,'runtime_trace_sha256':H(json.dumps(r2.runtime.trace_receipt(),sort_keys=True,separators=(',',':')).encode())})
 denied=False
 try:
  with tempfile.TemporaryDirectory() as td:evalfn(b['ir'],'http_website',[1],RuntimeGW(Path(td),set()))
 except CapabilityFault:denied=True
 if not denied:fail.append('TEXTUAL_CAPABILITY_FORGERY')
 rep={'schema_version':'2.0','experiment':'six effectful app classes through Clay source typed-effect IR and selected runtime','source':SOURCE,'source_sha256':b['source_hash'],'semantic_hash':b['semantic_hash'],'artifact_hash':b['artifact_hash'],'translation_contract_hash':b['translation_contract_hash'],'compiler_candidate':b['candidate_version'],'runtime_version':RUNTIME_VERSION,'stdlib_extension_version':STDLIB_EXT_VERSION,'authority_context':CTX,'rows':rows,'passed':sum(r['pass'] for r in rows),'total':len(rows),'textual_capability_without_bearer_denied':denied,'failures':fail,'pass':not fail and len(rows)==6,'counts_as_target_acceptance':False,'target_credit_rule':'Only strict Andreas-target finalizer at same repo commit may credit rows; this receipt never self-promotes.','authority_invariant':'model output != execution authority'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(rep,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'pass':rep['pass'],'passed':rep['passed'],'total':rep['total'],'failures':fail}));return 0 if rep['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
