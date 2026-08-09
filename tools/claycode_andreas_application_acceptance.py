#!/usr/bin/env python3
"""Materialize real per-application ClayCode BASE receipts on Andreas' Ubuntu target.

This deliberately emits nine application receipts and refuses to fabricate
FULL_FRANK_HANDOFF. That tenth receipt must come from the actual full FRANK handoff.
"""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,tempfile
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
from claycode_base_pure_toolchain import compile_source,differential,ClayError
from claycode_base_runtime import ClayRuntime,CapabilityFault,ResourceFault
from claycode_base_stdlib_extensions import install
OUTDIR=ROOT/'research_entity/claycode/target_receipts/apps';TARGET='ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def fh(path:Path)->str:return sha(path.read_bytes())
def osrel():
 d={};p=Path('/etc/os-release')
 if p.exists():
  for line in p.read_text(errors='replace').splitlines():
   if '=' in line:k,v=line.split('=',1);d[k]=v.strip().strip('"')
 return d
def host_ok():
 r=osrel();return os.getenv('CLAYCODE_TARGET_HOST_ID')==TARGET and platform.system()=='Linux' and r.get('ID')=='ubuntu' and os.getenv('GITHUB_ACTIONS','').lower()!='true' and os.getenv('CI','').lower() not in {'1','true','yes'}
def source_tree_clean_enough():
 cp=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True,check=False);bad=[];allowed=('research_entity/claycode/target_receipts/','research_entity/claycode/autonomous/','research_entity/claycode/corpus/base_v1/')
 for line in cp.stdout.splitlines():
  path=line[3:] if len(line)>=4 else line
  # Rename records can contain "old -> new"; conservatively reject unless both are evidence paths.
  parts=[x.strip() for x in path.split(' -> ')]
  if not all(any(x.startswith(prefix) for prefix in allowed) for x in parts):bad.append(line)
 return not bad,bad
def receipt(app:str,source_hash:str,artifact_hash:str,expected:Any,observed:Any,positive:dict,negative:dict,ok:bool)->dict:
 return {'schema_version':'1.1','app':app,'pass':bool(ok and positive.get('pass') and negative.get('pass')),'target_host':TARGET,'evidence_class':'ANDREAS_UBUNTU_REAL_APPLICATION','model_output_is_execution_authority':False,'git_head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True).stdout.strip(),'source_sha256':source_hash,'artifact_sha256':artifact_hash,'expected':expected,'observed':observed,'positive_test':positive,'negative_test':negative}
def write(app,row):OUTDIR.mkdir(parents=True,exist_ok=True);(OUTDIR/f'{app}.json').write_text(json.dumps(row,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def compile_app(source,entry,args):
 t=compile_source(source);d=differential(t,entry,args);return t,d
def expect_compile_reject(source):
 try:compile_source(source);return {'pass':False,'detail':'unexpected_accept'}
 except ClayError as e:return {'pass':True,'detail':str(e)}
def load_frank():
 p=ROOT/'research_entity/harness/reference/active_assembly.py';spec=importlib.util.spec_from_file_location('frank_target_aa',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m,p
def main()->int:
 if not host_ok():print(json.dumps({'error':'NOT_ANDREAS_UBUNTU_NON_CI_TARGET'}));return 3
 clean,bad=source_tree_clean_enough()
 if not clean:print(json.dumps({'error':'DIRTY_SOURCE_OR_TOOLCHAIN_INPUT','entries':bad[:20]}));return 3
 rows={};compiler_artifact=fh(ROOT/'tools/claycode_base_compiler.py');runtime_artifact=fh(ROOT/'tools/claycode_base_runtime.py')
 src='module target.cli\nfn main(x:Int)->Int=x+1\n';t,d=compile_app(src,'main',[41]);pos={'pass':d['match'],'native_stdout':d['native_stdout']};neg=expect_compile_reject('module target.cli_bad\nfn main(x:Int)->Bool=x+1\n');rows['CLI']=receipt('CLI',sha(src.encode()),d['generated_c_sha256'],42,int(d['native_stdout']),pos,neg,d['match'])
 with tempfile.TemporaryDirectory(prefix='clay_target_apps_') as td:
  rt=install(ClayRuntime(td))
  cap=rt.mint_capability('net.loopback',{'host':'127.0.0.1','routes':['/'],'max_body_bytes':4096});e=rt.invoke('http.loopback_roundtrip',cap,'/','<html>ClayCode</html>');pos={'pass':e['status']==200 and e['matched'],'status':e['status'],'body_sha256':e['body_sha256']}
  try:rt.invoke('http.loopback_roundtrip',cap,'/denied','x');neg={'pass':False,'detail':'unexpected_accept'}
  except CapabilityFault as x:neg={'pass':True,'detail':str(x)}
  rows['HTTP_WEBSITE']=receipt('HTTP_WEBSITE',sha(b'http.loopback_roundtrip:/'),runtime_artifact,{'status':200,'matched':True},{'status':e['status'],'matched':e['matched']},pos,neg,pos['pass'])
  db=rt.mint_capability('db.sqlite',{'prefix':'db'});e=rt.invoke('db.sqlite_transaction',db,'app.db',[('CREATE TABLE kv(k TEXT PRIMARY KEY,v INTEGER)',()),('INSERT INTO kv(k,v) VALUES(?,?)',('a',1)),('SELECT v FROM kv WHERE k=?',('a',))]);pos={'pass':e['rows'][-1]==[(1,)],'rows':e['rows'][-1]}
  try:rt.invoke('db.sqlite_transaction',db,'app.db',[('INSERT INTO kv(k,v) VALUES(?,?)',('b',2)),('INSERT INTO missing(x) VALUES(1)',())]);neg={'pass':False,'detail':'unexpected_accept'}
  except Exception as x:
   after=rt.invoke('db.sqlite_transaction',db,'app.db',[('SELECT k FROM kv ORDER BY k',())]);neg={'pass':after['rows'][-1]==[('a',)],'detail':type(x).__name__,'after':after['rows'][-1]}
  rows['DB_SERVICE']=receipt('DB_SERVICE',sha(b'sqlite:kv:v1'),runtime_artifact,[(1,)],e['rows'][-1],pos,neg,pos['pass'])
  ac=rt.mint_capability('async.compute',{'operations':['square']});e=rt.invoke('async.map',ac,'square',[5,1,3,2],4);want=[25,1,9,4];pos={'pass':[x['value'] for x in e]==want,'values':[x['value'] for x in e]}
  try:rt.invoke('async.map',ac,'negate',[1],1);neg={'pass':False,'detail':'unexpected_accept'}
  except CapabilityFault as x:neg={'pass':True,'detail':str(x)}
  rows['CONCURRENT_SERVICE']=receipt('CONCURRENT_SERVICE',sha(b'async:square:v1'),runtime_artifact,want,pos['values'],pos,neg,pos['pass'])
  ui=rt.mint_capability('ui.interactive',{'events':['click','reset'],'max_events':16});e=rt.invoke('ui.interactive_event_loop',ui,{'counter':0,'label':'idle'},[{'kind':'click','value':2},{'kind':'reset'},{'kind':'click','value':4}]);want={'counter':4,'label':'count:4'};pos={'pass':e['state']==want and e['rendered']=='[4] count:4','rendered':e['rendered']}
  try:rt.invoke('ui.interactive_event_loop',ui,{},[{'kind':'shell','value':'x'}]);neg={'pass':False,'detail':'unexpected_accept'}
  except CapabilityFault as x:neg={'pass':True,'detail':str(x)}
  rows['GUI_INTERACTIVE']=receipt('GUI_INTERACTIVE',sha(b'ui:click-reset:v1'),fh(ROOT/'tools/claycode_base_stdlib_extensions.py'),want,e['state'],pos,neg,pos['pass'])
  src='module target.compiler\nfn add(a:Int,b:Int)->Int=a+b\nfn main(a:Int,b:Int)->Int=add(a,b)*2\n';t,d=compile_app(src,'main',[7,5]);pos={'pass':d['match'] and d['native_stdout']=='24','semantic_hash':t['semantic_hash']};neg=expect_compile_reject('module target.compiler_bad\nfn main(a:Int)->Int=a+missing\n');rows['COMPILER_TOOL']=receipt('COMPILER_TOOL',sha(src.encode()),d['generated_c_sha256'],24,int(d['native_stdout']),pos,neg,pos['pass'])
  nc=rt.mint_capability('numerical.cpu',{'max_vector':3});v=rt.invoke('numerical.dot',nc,[1,2,3],[4,5,6]);pos={'pass':v==32.0,'backend':'numerical.cpu'}
  try:rt.invoke('numerical.dot',nc,[1,2,3,4],[1,2,3,4]);neg={'pass':False,'detail':'unexpected_accept'}
  except ResourceFault as x:neg={'pass':True,'detail':str(x)}
  rows['GPU_ML_NUMERICAL']=receipt('GPU_ML_NUMERICAL',sha(b'numerical.dot:v1'),runtime_artifact,32.0,v,pos,neg,pos['pass'])
  fw=rt.mint_capability('fs.write',{'prefix':'data'});fr=rt.mint_capability('fs.read',{'prefix':'data'});w=rt.invoke('fs.write_text',fw,'x.txt','authorized');r=rt.invoke('fs.read_text',fr,'x.txt');pos={'pass':r['text']=='authorized' and r['sha256']==w['sha256'],'sha256':r['sha256']}
  try:rt.invoke('fs.write_text',fw,'../escape','bad');neg={'pass':False,'detail':'unexpected_accept'}
  except ResourceFault as x:neg={'pass':True,'detail':str(x)}
  rows['SYSTEM_EFFECT_SANDBOX']=receipt('SYSTEM_EFFECT_SANDBOX',sha(b'fs-sandbox:v1'),runtime_artifact,'authorized',r['text'],pos,neg,pos['pass'])
 m,p=load_frank();packets=[m.AssemblyPacket('a','memory','memory',.9,.8,.4,.1,3,claim_key='mode',claim_value='A',reexpand_ref='m:a'),m.AssemblyPacket('b','tool','tool_result',.8,.9,.5,.2,3,claim_key='mode',claim_value='B',reexpand_ref='t:b'),m.AssemblyPacket('stale','old','memory',1,1,1,0,2,reexpand_ref='o:s')];a=m.compile_active_assembly(packets,current_epoch=3,max_items=4,max_per_ancestry=2);vals={x.get('claim_value') for x in a['items']};pos={'pass':{'A','B'}.issubset(vals) and all(x.get('execution_authority') is False for x in a['items'])};neg={'pass':all(x['packet_id']!='stale' for x in a['items']),'detail':'stale epoch packet excluded'};rows['FRANK_COMPONENT']=receipt('FRANK_COMPONENT',fh(p),compiler_artifact,{'conflicts_preserved':['A','B'],'stale_excluded':True},{'conflict_values':sorted(vals),'packet_ids':[x['packet_id'] for x in a['items']]},pos,neg,pos['pass'])
 for app,row in rows.items():write(app,row)
 failed=[k for k,v in rows.items() if not v['pass']];summary={'target_host':TARGET,'git_head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True).stdout.strip(),'emitted_apps':sorted(rows),'intentionally_not_emitted':['FULL_FRANK_HANDOFF'],'failed':failed,'pass':not failed,'wp10_complete':False,'reason_wp10_incomplete':'FULL_FRANK_HANDOFF must be produced by actual full FRANK handoff, never by this app runner.'};print(json.dumps(summary));return 0 if not failed else 2
if __name__=='__main__':raise SystemExit(main())
