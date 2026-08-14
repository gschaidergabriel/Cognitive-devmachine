#!/usr/bin/env python3
"""Hosted-Linux application proxy suite using sealed ClayCode capabilities only."""
from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
from claycode_base_pure_toolchain import compile_source,differential
from claycode_base_runtime import ClayRuntime,RUNTIME_VERSION
from claycode_base_stdlib_extensions import install,STDLIB_EXT_VERSION
OUT=ROOT/'research_entity/claycode/autonomous/BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def compiler(source,entry,args):
 t=compile_source(source);d=differential(t,entry,args);return {'source_sha256':sha(source.encode()),'semantic_hash':t['semantic_hash'],'target_sha256':d['generated_c_sha256'],'observed':d['native_stdout'],'expected':d['expected_stdout'],'pass':d['match']}
def frank_probe():
 path=ROOT/'research_entity/harness/reference/active_assembly.py';spec=importlib.util.spec_from_file_location('frank_active_assembly',path);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
 packets=[mod.AssemblyPacket('a','memory','memory',.9,.8,.4,.1,3,claim_key='mode',claim_value='A',reexpand_ref='mem:a'),mod.AssemblyPacket('b','tool','tool_result',.8,.9,.5,.2,3,claim_key='mode',claim_value='B',reexpand_ref='tool:b'),mod.AssemblyPacket('stale','old','memory',1,1,1,0,2,reexpand_ref='old:stale')]
 a=mod.compile_active_assembly(packets,current_epoch=3,max_items=4,max_per_ancestry=2);vals={x.get('claim_value') for x in a['items']};ok=all(x.get('execution_authority') is False for x in a['items']) and all(x['packet_id']!='stale' for x in a['items']) and {'A','B'}.issubset(vals)
 return {'path':str(path.relative_to(ROOT)),'reference_sha256':sha(path.read_bytes()),'assembly_sha256':a['assembly_sha256'],'item_count':len(a['items']),'pass':ok}
def main():
 rows=[]
 def add(k,e,n=''):rows.append({'app_id':k,'pass':bool(e.get('pass')),'note':n,'evidence':e})
 with tempfile.TemporaryDirectory(prefix='claycode_apps_v2_') as td:
  rt=install(ClayRuntime(td))
  add('CLI',compiler('module app.cli\nfn main(x:Int)->Int=x+1\n','main',[41]),'Clay source -> typed IR -> C11 -> native process exit/output harness')
  net=rt.mint_capability('net.loopback',{'host':'127.0.0.1','routes':['/'],'max_body_bytes':4096});e=rt.invoke('http.loopback_roundtrip',net,'/','<html><body>ClayCode BASE</body></html>');e['pass']=e['status']==200 and e['matched'];add('HTTP_WEBSITE',e,'real loopback TCP/HTTP through named capability adapter')
  db=rt.mint_capability('db.sqlite',{'prefix':'db'});e=rt.invoke('db.sqlite_transaction',db,'app.db',[('CREATE TABLE kv(k TEXT PRIMARY KEY,v INTEGER)',()),('INSERT INTO kv(k,v) VALUES(?,?)',('answer',42)),('SELECT v FROM kv WHERE k=?',('answer',))]);e['pass']=e['rows'][-1]==[(42,)];add('DB_SERVICE',e)
  ac=rt.mint_capability('async.compute',{'operations':['square']});e=rt.invoke('async.map',ac,'square',list(range(32)),8);e2={'count':len(e),'result_sha256':sha(json.dumps(e,sort_keys=True).encode()),'pass':[x['value'] for x in e]==[x*x for x in range(32)]};add('CONCURRENT_SERVICE',e2)
  ui=rt.mint_capability('ui.interactive',{'events':['click','reset'],'max_events':16});e=rt.invoke('ui.interactive_event_loop',ui,{'counter':0,'label':'idle'},[{'kind':'click','value':1},{'kind':'click','value':2},{'kind':'reset'},{'kind':'click','value':4}]);e['pass']=e['state']=={'counter':4,'label':'count:4'} and e['rendered']=='[4] count:4';add('GUI_INTERACTIVE',e,'interactive input/state/render event loop adapter')
  add('COMPILER_TOOL',compiler('module app.compiler\nfn add(a:Int,b:Int)->Int=a+b\nfn score(a:Int,b:Int)->Int=add(a,b)*2\n','score',[7,5]))
  num=rt.mint_capability('numerical.cpu',{'max_vector':1024});v=rt.invoke('numerical.dot',num,[.5,1.5,-2],[2,4,3]);add('GPU_ML_NUMERICAL',{'backend':'numerical.cpu','observed':v,'pass':v==1.0},'numerical backend branch; no GPU claim')
  fw=rt.mint_capability('fs.write',{'prefix':'data'});fr=rt.mint_capability('fs.read',{'prefix':'data'});w=rt.invoke('fs.write_text',fw,'effect.txt','authorized');r=rt.invoke('fs.read_text',fr,'effect.txt');denied=False
  try:rt.invoke('fs.write_text',fw,'../escape.txt','forbidden')
  except Exception:denied=True
  add('SYSTEM_EFFECT_SANDBOX',{'resource':w['resource'],'escape_rejected':denied,'pass':denied and r['text']=='authorized' and r['sha256']==w['sha256']})
  f=frank_probe();add('FRANK_COMPONENT',f,'current H1 reference executed; Clay rewrite remains target handoff work')
  h=compiler('module frank.handoff\nfn amplify(x:Int)->Int=x*2+1\n','amplify',[int(f['item_count'])]);h['frank_assembly_sha256']=f['assembly_sha256'];add('FULL_FRANK_HANDOFF',h,'concrete FRANK-reference value crosses Clay native compiler boundary; not full H2/H3')
  trace=rt.trace_receipt()
 fails=[r['app_id'] for r in rows if not r['pass']];report={'schema_version':'2.0','experiment':'ClayCode BASE sealed-capability ten-class hosted application proxy','runtime_version':RUNTIME_VERSION,'stdlib_extension_version':STDLIB_EXT_VERSION,'evidence_class':'HOSTED_LINUX_PROXY_NOT_ANDREAS_TARGET_ACCEPTANCE','counts_as_target_acceptance':False,'counts_as_application_acceptance_pass':False,'rows':rows,'passed':len(rows)-len(fails),'total':len(rows),'failures':fails,'pass':not fails,'trace_sha256':sha(json.dumps(trace,sort_keys=True).encode()),'authority_invariant':'model_output != execution_authority','next_required':'same production chain must run on ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM before app PASS'};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'pass':report['pass'],'passed':report['passed'],'total':report['total'],'failures':fails}));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
