#!/usr/bin/env python3
"""Executable adversarial validation for tools/claycode_base_runtime.py.

Hosted Ubuntu execution is proxy evidence only; target-host receipts remain required.
The suite explicitly probes caller-controlled policy/callable/path laundering.
"""
from __future__ import annotations
import json, os, pickle, tempfile
from pathlib import Path
from claycode_base_runtime import CapabilityFault, ClayRuntime, ResourceFault, VersionedCell, RUNTIME_VERSION

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research_entity/claycode/autonomous/BASE_RUNTIME_CAPABILITY_RECEIPT.json'

def main()->int:
    checks=[]
    def check(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})
    def rejects(name,fn,expected):
        try: fn(); check(name,False,'unexpected_accept')
        except expected as exc: check(name,True,str(exc))

    with tempfile.TemporaryDirectory(prefix='claycode_runtime_') as td:
        rt=ClayRuntime(td)
        fsw=rt.mint_capability('fs.write',{'prefix':'data'})
        fsr=rt.mint_capability('fs.read',{'prefix':'data'})
        write=rt.invoke('fs.write_text',fsw,'nested/x.txt','clay')
        read=rt.invoke('fs.read_text',fsr,'nested/x.txt')
        check('fs_roundtrip',read['text']=='clay' and read['sha256']==write['sha256'])
        check('resource_identity_runtime_bound',write['resource']['runtime_id']==rt.runtime_id and bool(write['resource']['resource_id']))
        rejects('wrong_capability_kind',lambda:rt.invoke('fs.read_text',fsw,'nested/x.txt'),CapabilityFault)
        rejects('textual_capability_name_not_authority',lambda:rt.invoke('fs.read_text','fs.read','nested/x.txt'),CapabilityFault)
        rejects('sandbox_parent_escape',lambda:rt.invoke('fs.write_text',fsw,'../escape.txt','bad'),ResourceFault)
        rejects('capability_not_serializable',lambda:pickle.dumps(fsw),CapabilityFault)
        desc=rt.capability_descriptor(fsr)
        check('descriptor_explicitly_non_authorizing',desc['authorizing'] is False and desc['policy']=={'prefix':'data'})
        rejects('descriptor_not_authority',lambda:rt.invoke('fs.read_text',desc,'nested/x.txt'),CapabilityFault)

        rt.revoke(fsw)
        rejects('revoked_capability_rejected',lambda:rt.invoke('fs.write_text',fsw,'y.txt','bad'),CapabilityFault)
        old=fsr; rt.rotate_epoch()
        rejects('stale_epoch_rejected',lambda:rt.invoke('fs.read_text',old,'nested/x.txt'),CapabilityFault)
        other=ClayRuntime(Path(td)/'other'); other_read=other.mint_capability('fs.read')
        rejects('cross_runtime_capability_rejected',lambda:rt.invoke('fs.read_text',other_read,'nested/x.txt'),CapabilityFault)

        db=rt.mint_capability('db.sqlite',{'prefix':'db'})
        first=rt.invoke('db.sqlite_transaction',db,'state.db',[
            ('CREATE TABLE IF NOT EXISTS t(k TEXT PRIMARY KEY,v INTEGER)',()),
            ('INSERT INTO t(k,v) VALUES(?,?)',('a',1)),('SELECT k,v FROM t ORDER BY k',())])
        check('sqlite_commit',first['rows'][-1]==[('a',1)])
        try:
            rt.invoke('db.sqlite_transaction',db,'state.db',[
                ('INSERT INTO t(k,v) VALUES(?,?)',('b',2)),('INSERT INTO missing_table(x) VALUES(1)',())])
            check('sqlite_failure_triggered',False,'unexpected_accept')
        except Exception as exc: check('sqlite_failure_triggered',True,type(exc).__name__)
        after=rt.invoke('db.sqlite_transaction',db,'state.db',[('SELECT k,v FROM t ORDER BY k',())])
        check('sqlite_rollback_atomic',after['rows'][-1]==[('a',1)])

        # Process authority is bound to a canonical absolute executable at mint time.
        echo_real=str(Path('/bin/echo').resolve(strict=True))
        proc=rt.mint_capability('process.exec',{'programs':[echo_real]})
        echo=rt.invoke('process.exec',proc,[echo_real,'clay'])
        check('process_allowlist_positive',echo['returncode']==0 and echo['stdout'].strip()=='clay')
        rejects('process_policy_scope_negative',lambda:rt.invoke('process.exec',proc,[str(Path('/bin/true').resolve(strict=True))]),CapabilityFault)
        rejects('process_policy_missing_rejected',lambda:rt.mint_capability('process.exec'),CapabilityFault)
        rejects('process_policy_basename_entry_rejected',lambda:rt.mint_capability('process.exec',{'programs':['echo']}),CapabilityFault)
        rejects('process_relative_argv_rejected',lambda:rt.invoke('process.exec',proc,['echo','clay']),CapabilityFault)
        # P0 regression: a hostile binary with the same basename must not inherit authority.
        fake_dir=Path(td)/'evil'; fake_dir.mkdir(); fake_echo=fake_dir/'echo'
        fake_echo.write_text('#!/bin/sh\nprintf "PWNED\\n"\n',encoding='utf-8'); os.chmod(fake_echo,0o755)
        rejects('process_same_basename_spoof_rejected',lambda:rt.invoke('process.exec',proc,[str(fake_echo)]),CapabilityFault)
        # Caller still cannot widen a sealed policy during invocation.
        rejects('caller_cannot_widen_process_allowlist',lambda:rt.invoke('process.exec',proc,[str(Path('/bin/true').resolve(strict=True))],['/bin/true']),TypeError)

        num=rt.mint_capability('numerical.cpu',{'max_vector':3})
        check('numerical_dot',rt.invoke('numerical.dot',num,[1,2,3],[4,5,6])==32.0)
        rejects('numerical_shape_error',lambda:rt.invoke('numerical.dot',num,[1],[1,2]),ResourceFault)
        rejects('numerical_resource_limit',lambda:rt.invoke('numerical.dot',num,[1,2,3,4],[1,2,3,4]),ResourceFault)

        # Arbitrary host callables are forbidden at the async boundary.
        ac=rt.mint_capability('async.compute',{'operations':['square']})
        mapped=rt.invoke('async.map',ac,'square',[5,1,3,2],4)
        check('async_publication_order_deterministic',mapped==[
            {'index':0,'value':25},{'index':1,'value':1},{'index':2,'value':9},{'index':3,'value':4}])
        rejects('async_operation_scope_negative',lambda:rt.invoke('async.map',ac,'negate',[1],1),CapabilityFault)
        rejects('async_callable_laundering_rejected',lambda:rt.invoke('async.map',ac,lambda x:x,[1],1),CapabilityFault)

        cell=VersionedCell('A');v0,_=cell.snapshot();ok1,v1,_=cell.compare_and_swap(v0,'B');ok2,v2,_=cell.compare_and_swap(v1,'A');stale,ov,oval=cell.compare_and_swap(v0,'C')
        check('cas_positive',ok1 and ok2 and v2==v0+2)
        check('cas_aba_stale_rejected',not stale and ov==v2 and oval=='A')
        trace=rt.trace_receipt()
        check('trace_monotonic_sequence',[x['seq'] for x in trace]==list(range(1,len(trace)+1)))
        rendered=json.dumps(trace,sort_keys=True)
        check('trace_no_raw_capability_secret','nonce' not in rendered and 'issuer_secret' not in rendered)

    failures=[c['name'] for c in checks if not c['pass']]
    report={'schema_version':'1.2','runtime_version':RUNTIME_VERSION,'experiment':'ClayCode BASE sealed runtime/ABI/FFI authority boundary adversarial validation','evidence_class':'HOSTED_OR_LOCAL_LINUX_EXECUTION_NOT_ANDREAS_TARGET_ACCEPTANCE','counts_as_target_acceptance':False,'counts_as_full_work_package_pass':False,'supports':['CC-WP-07-RUNTIME-ABI-FFI','CC-WP-08-STDLIB-SDK','CC-WP-09-CONCURRENCY-MEMORY','CC-WP-11-FUZZ-CONFORMANCE'],'checks':checks,'checks_passed':len(checks)-len(failures),'checks_total':len(checks),'failures':failures,'pass':not failures,'authority_invariant':'model_output != execution_authority','closed_regressions':['CALLER_SUPPLIED_PROCESS_ALLOWLIST','PROCESS_BASENAME_COLLISION','RELATIVE_PROCESS_PATH','ARBITRARY_CALLABLE_ASYNC_MAP'],'target_host_required_next':'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'pass':report['pass'],'passed':report['checks_passed'],'total':report['checks_total'],'failures':failures}))
    return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
