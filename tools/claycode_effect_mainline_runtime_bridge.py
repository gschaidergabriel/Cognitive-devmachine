#!/usr/bin/env python3
"""Bridge ClayCode compiler-generated effect IR into the selected mainline runtime.

This is the discriminating integration test demanded by BASE_RUNTIME_INTEGRATION_DECISION_V2:
compiler-generated host.* calls must reach tools/claycode_base_runtime.py rather than stop
at the textual proxy Gateway. Descriptive capability names in IR are routing labels only;
opaque host-minted handles remain the sole authority.
"""
from __future__ import annotations
import hashlib, http.server, json, random, sys, tempfile, threading, urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from claycode_base_effect_pipeline import build, eval_function, exec_lowered
from claycode_base_runtime import CapabilityFault, ClayRuntime, RUNTIME_VERSION

OUT=ROOT/'research_entity/claycode/autonomous/BASE_COMPILER_MAINLINE_RUNTIME_BRIDGE_RECEIPT.json'
GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
H=lambda s:hashlib.sha256(s.encode()).hexdigest()
CONTEXT={'origin_hash':H('compiler-effect-ir'),'basis_hash':H('typed-effect-closure'),'selection_hash':H('entry-main'),'closure_hash':H('capability-lfp')}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query);v=int(q.get('v',['0'])[0]);body=str(v+7).encode()
        self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args):return

class MainlineRuntimeGateway:
    """IR routing labels -> host-owned opaque runtime handles."""
    def __init__(self,root:Path,origin:str,read_values:list[int],caps:set[str]):
        self.runtime=ClayRuntime(root);self.trace=[];self._handles={};self.origin=origin
        data=root/'read';data.mkdir(parents=True,exist_ok=True)
        for v in read_values:(data/f'{v}.txt').write_text(str(v+1000),encoding='utf-8')
        if 'cap.fs.read' in caps:self._handles['cap.fs.read']=self.runtime.mint_capability('fs.read',{'prefix':'read','require_context':True,'max_calls':10000,'max_units':10_000_000},CONTEXT)
        if 'cap.fs.write' in caps:self._handles['cap.fs.write']=self.runtime.mint_capability('fs.write',{'prefix':'write','require_context':True,'max_calls':10000,'max_units':10_000_000},CONTEXT)
        if 'cap.db.write' in caps:self._handles['cap.db.write']=self.runtime.mint_capability('db.sqlite',{'prefix':'db','require_context':True,'max_calls':10000,'max_units':100000},CONTEXT)
        if 'cap.http' in caps:self._handles['cap.http']=self.runtime.mint_capability('net.http_get',{'origins':[origin],'max_response_bytes':128,'require_context':True,'max_calls':10000,'max_units':10000},CONTEXT)
    def effect(self,effect:str,capability:str,value:int)->int:
        handle=self._handles.get(capability)
        if handle is None:raise CapabilityFault(f'MISSING_BEARER_HANDLE:{capability}')
        if effect=='FS_READ':
            r=self.runtime.invoke_bound('fs.read_text',handle,CONTEXT,f'{value}.txt');out=int(r['text'])
        elif effect=='FS_WRITE':
            self.runtime.invoke_bound('fs.write_text',handle,CONTEXT,f'{value}.txt',str(value));out=value
        elif effect=='DB_WRITE':
            r=self.runtime.invoke_bound('db.sqlite_transaction',handle,CONTEXT,'effects.sqlite',[
              ('CREATE TABLE IF NOT EXISTS effects(v INTEGER PRIMARY KEY, doubled INTEGER)',()),
              ('INSERT OR REPLACE INTO effects(v,doubled) VALUES(?,?)',(value,value*2)),
              ('SELECT doubled FROM effects WHERE v=?',(value,))]);out=int(r['rows'][-1][0][0])
        elif effect=='HTTP':
            r=self.runtime.invoke_bound('net.http_get',handle,CONTEXT,f'{self.origin}/?v={value}');out=int(r['body'].decode())
        else:raise RuntimeError('UNKNOWN_EFFECT:'+effect)
        self.trace.append([effect,capability,value,out]);return out

def main()->int:
    grammar=GRAMMAR.read_text(encoding='utf-8')
    source='''module app.mainline_bridge
fn read(x:Int)->Int=host.fs_read(x)
fn store(x:Int)->Int=host.db_put(read(x))
fn mix(x:Int)->Int=store(x)+host.http_send(x)
fn main(x:Int)->Int=mix(x)+read(x)
'''
    built=build(source,grammar);main_ir=next(f for f in built['ir']['functions'] if f['name']=='main')
    required=set(main_ir['required_capabilities']);expected_caps={'cap.fs.read','cap.db.write','cap.http'}
    checks=[]
    def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
    ck('compiler_effect_closure_exact',required==expected_caps,sorted(required))
    rng=random.Random(70407);vectors=[rng.randint(-500,500) for _ in range(64)]
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start();origin=f'http://127.0.0.1:{srv.server_port}'
    rows=[];mismatches=0;trace_failures=0
    try:
        with tempfile.TemporaryDirectory(prefix='clay_mainline_bridge_') as td:
            base=Path(td)
            for i,v in enumerate(vectors):
                g1=MainlineRuntimeGateway(base/f'r{i}',origin,vectors,required);g2=MainlineRuntimeGateway(base/f'l{i}',origin,vectors,required)
                expected=eval_function(built['ir'],'main',[v],g1);observed=exec_lowered(built['artifact'],'main',[v],g2)
                same=expected==observed;rt1=g1.runtime.trace_receipt();rt2=g2.runtime.trace_receipt()
                adapters1=[x['adapter'] for x in rt1];adapters2=[x['adapter'] for x in rt2]
                needed={'fs.read_text','db.sqlite_transaction','net.http_get'}
                trace_ok=needed.issubset(adapters1) and adapters1==adapters2 and all(x['status']=='PASS' for x in rt1+rt2)
                mismatches+=int(not same);trace_failures+=int(not trace_ok)
                rows.append({'v':v,'expected':expected,'observed':observed,'same':same,'runtime_adapters':adapters1,'runtime_trace_match':trace_ok})
            # Textual capability labels/descriptors cannot substitute for missing bearer possession.
            missing=MainlineRuntimeGateway(base/'missing',origin,vectors,{'cap.fs.read','cap.db.write'})
            denied=False
            try:eval_function(built['ir'],'main',[3],missing)
            except CapabilityFault:denied=True
            ck('textual_ir_capability_without_bearer_denied',denied)
            descgw=MainlineRuntimeGateway(base/'desc',origin,vectors,required)
            descriptor=descgw.runtime.capability_descriptor(descgw._handles['cap.http'])
            descgw._handles['cap.http']=descriptor
            denied_desc=False
            try:eval_function(built['ir'],'main',[3],descgw)
            except CapabilityFault:denied_desc=True
            ck('non_authorizing_descriptor_cannot_replace_handle',denied_desc)
    finally:srv.shutdown();srv.server_close();thread.join(timeout=3)
    ck('reference_vs_lowered_output_differential',mismatches==0,{'vectors':len(vectors),'mismatches':mismatches})
    ck('both_paths_enter_same_mainline_runtime_adapters',trace_failures==0,{'vectors':len(vectors),'trace_failures':trace_failures})
    failures=[x['name'] for x in checks if not x['pass']]
    report={'schema_version':'1.0','experiment':'compiler generated V7 typed-effect IR -> selected ClayRuntime mainline bridge','runtime_version':RUNTIME_VERSION,
      'compiler_candidate':built['candidate_version'],'source_hash':built['source_hash'],'semantic_hash':built['semantic_hash'],'artifact_hash':built['artifact_hash'],
      'required_capabilities':sorted(required),'authority_context':CONTEXT,'vectors':len(vectors),'output_mismatches':mismatches,'trace_failures':trace_failures,
      'checks':checks,'rows':rows,'failures':failures,'pass':not failures,'counts_as_target_acceptance':False,'counts_as_full_wp07_pass':False,
      'closes_discriminator':'compiler-generated effect calls enter selected tools/claycode_base_runtime.py through host-owned opaque handles rather than textual proxy authority',
      'authority_invariant':'model output != execution authority','next_required':'rerun this bridge on Andreas Ubuntu and adjudicate remaining child ambient-OS sandbox threat model'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps({'pass':report['pass'],'vectors':len(vectors),'mismatches':mismatches,'trace_failures':trace_failures,'failures':failures}))
    return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
