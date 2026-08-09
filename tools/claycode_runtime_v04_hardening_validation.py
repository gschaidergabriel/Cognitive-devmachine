#!/usr/bin/env python3
"""Adversarial discriminators for ClayCode mainline runtime v0.4 hardening."""
from __future__ import annotations
import hashlib, http.server, json, os, tempfile, threading
from pathlib import Path
from claycode_base_runtime import CapabilityFault, ClayRuntime, ResourceFault, RUNTIME_VERSION

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research_entity/claycode/autonomous/BASE_RUNTIME_V04_HARDENING_RECEIPT.json'
H=lambda s:hashlib.sha256(s.encode()).hexdigest()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/ok':
            b=b'clay-http-ok'; self.send_response(200); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        elif self.path=='/redir':
            self.send_response(302); self.send_header('Location','http://example.com/'); self.end_headers()
        elif self.path=='/big':
            b=b'x'*256; self.send_response(200); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        else:self.send_response(404);self.end_headers()
    def log_message(self,*args):return

def main()->int:
    checks=[]
    def ck(name,cond,detail=None):checks.append({'name':name,'pass':bool(cond),'detail':detail})
    def rej(name,fn,exc=(CapabilityFault,ResourceFault)):
        try:fn();ck(name,False,'unexpected_accept')
        except exc as e:ck(name,True,f'{type(e).__name__}:{e}')
    with tempfile.TemporaryDirectory(prefix='clay_rt04_') as td:
        rt=ClayRuntime(td)
        context={'origin_hash':H('origin'),'basis_hash':H('basis'),'selection_hash':H('selection'),'closure_hash':H('closure')}
        wrong={**context,'closure_hash':H('wrong')}
        bound=rt.mint_capability('fs.write',{'prefix':'ctx','require_context':True,'max_calls':2,'max_units':20},context)
        rej('bound_capability_rejects_unbound_invoke',lambda:rt.invoke('fs.write_text',bound,'x.txt','ok'))
        rej('bound_capability_rejects_wrong_context',lambda:rt.invoke_bound('fs.write_text',bound,wrong,'x.txt','ok'))
        wr=rt.invoke_bound('fs.write_text',bound,context,'x.txt','ok')
        ck('bound_capability_exact_context_pass',wr['bytes']==2)
        desc=rt.capability_descriptor(bound)
        ck('descriptor_exposes_non_authorizing_context_binding',desc['authorizing'] is False and desc['context_hash']==H(json.dumps(context,sort_keys=True,separators=(',',':'))))
        rej('descriptor_still_not_authority',lambda:rt.invoke_bound('fs.write_text',desc,context,'y.txt','x'),(CapabilityFault,))

        # Cumulative budgets are charged before the external effect.
        budget=rt.mint_capability('fs.write',{'prefix':'budget','max_calls':2,'max_units':4})
        rt.invoke('fs.write_text',budget,'a','aa'); rt.invoke('fs.write_text',budget,'b','bb')
        rej('cumulative_call_budget_fail_closed',lambda:rt.invoke('fs.write_text',budget,'c',''))
        usage=rt.usage_descriptor(budget)['usage']; ck('cumulative_usage_exact',usage=={'calls':2,'units':4},usage)
        units=rt.mint_capability('fs.write',{'prefix':'units','max_calls':5,'max_units':3})
        rej('cumulative_unit_budget_prevents_effect',lambda:rt.invoke('fs.write_text',units,'too-big','four'))
        ck('overbudget_file_not_created',not (Path(td)/'units'/'too-big').exists())

        # Process executable is fingerprinted at mint and executed from an opened fd.
        prog=Path(td)/'pinned.sh';prog.write_text('#!/bin/sh\nprintf "ORIGINAL\\n"\n');os.chmod(prog,0o755)
        pcap=rt.mint_capability('process.exec',{'programs':[str(prog)],'max_calls':2})
        first=rt.invoke('process.exec',pcap,[str(prog)]);ck('pinned_exec_positive',first['stdout'].strip()=='ORIGINAL' and first['child_capability_propagation']=='NONE')
        prog.write_text('#!/bin/sh\nprintf "REPLACED\\n"\n');os.chmod(prog,0o755)
        rej('same_path_executable_replacement_detected',lambda:rt.invoke('process.exec',pcap,[str(prog)]),(CapabilityFault,))

        # Child receives no Clay capability material via environment.
        envbin=str(Path('/usr/bin/env').resolve(strict=True))
        envcap=rt.mint_capability('process.exec',{'programs':[envbin]})
        old=os.environ.get('CLAYCODE_CAPABILITY_FAKE');os.environ['CLAYCODE_CAPABILITY_FAKE']='must-not-cross'
        try: envout=rt.invoke('process.exec',envcap,[envbin])['stdout']
        finally:
            if old is None:os.environ.pop('CLAYCODE_CAPABILITY_FAKE',None)
            else:os.environ['CLAYCODE_CAPABILITY_FAKE']=old
        ck('child_capability_environment_scrubbed','CLAYCODE_CAPABILITY_FAKE=' not in envout)

        # HTTP adapter is origin-bound, redirect-fail-closed and response-limited.
        srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
        try:
            origin=f'http://127.0.0.1:{srv.server_port}'
            httpcap=rt.mint_capability('net.http_get',{'origins':[origin],'max_response_bytes':64,'max_calls':4})
            ok=rt.invoke('net.http_get',httpcap,origin+'/ok');ck('http_origin_positive',ok['status']==200 and ok['body']==b'clay-http-ok')
            rej('http_disallowed_origin',lambda:rt.invoke('net.http_get',httpcap,'http://example.com/'),(CapabilityFault,))
            rej('http_redirect_fail_closed',lambda:rt.invoke('net.http_get',httpcap,origin+'/redir'),(CapabilityFault,))
            rej('http_response_limit',lambda:rt.invoke('net.http_get',httpcap,origin+'/big'),(ResourceFault,))
        finally:srv.shutdown();srv.server_close();thread.join(timeout=3)

        trace=rt.trace_receipt();ck('trace_carries_context_and_usage',all('context_hash' in x and 'cumulative_usage' in x for x in trace))
    fails=[x['name'] for x in checks if not x['pass']]
    report={'schema_version':'1.0','runtime_version':RUNTIME_VERSION,'experiment':'mainline runtime v0.4 closure discriminators','checks':checks,'failures':fails,'pass':not fails,
            'closes_or_binds':['FRANK_ORIGIN_BASIS_SELECTION_CLOSURE_BINDING','CUMULATIVE_CAPABILITY_RESOURCE_BUDGETS','PROCESS_SAME_PATH_TOCTOU_IDENTITY','CHILD_CLAY_CAPABILITY_NONPROPAGATION','HTTP_ORIGIN_REDIRECT_RESPONSE_BOUNDARY'],
            'still_target_dependent':['ambient OS authority of launched child is bounded only by executable selection unless target sandbox backend is added/tested','all host claims require Andreas Ubuntu rerun'],
            'counts_as_work_package_pass':False,'counts_as_target_acceptance':False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps({'pass':report['pass'],'runtime_version':RUNTIME_VERSION,'checks':len(checks),'failures':fails}))
    return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
