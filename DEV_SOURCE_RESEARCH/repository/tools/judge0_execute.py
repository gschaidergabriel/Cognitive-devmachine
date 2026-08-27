#!/usr/bin/env python3
"""Judge0 remote code execution adapter for FRANK/RAE.

Defaults to the official CE host. JUDGE0_API_URL and JUDGE0_API_KEY are optional;
self-hosted deployments can override both. The adapter polls asynchronously and returns
only execution metadata/output required for reproducibility.
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from rae_secret_loader import get_secret, secret_source  # noqa: E402

DEFAULT_BASE='https://ce.judge0.com'


def _base()->str:
    return (os.environ.get('JUDGE0_API_URL') or get_secret('JUDGE0_API_URL',required=False) or DEFAULT_BASE).rstrip('/')


def _headers()->dict:
    h={'Accept':'application/json','Content-Type':'application/json','User-Agent':'FRANK-RAE/8.8 Judge0 adapter'}
    key=get_secret('JUDGE0_API_KEY',required=False)
    if key: h['X-Auth-Token']=key
    return h


def _request(path:str, method:str='GET', body:dict|None=None)->dict|list:
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(_base()+path,data=data,headers=_headers(),method=method)
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())


def languages()->list:
    return _request('/languages')


def _language_id(name:str)->int:
    needle=name.lower()
    langs=languages()
    exact=[x for x in langs if needle==str(x.get('name','')).lower()]
    if exact: return int(exact[0]['id'])
    partial=[x for x in langs if needle in str(x.get('name','')).lower()]
    if not partial: raise RuntimeError(f'Judge0 language not found: {name}')
    return int(partial[-1]['id'])


def execute(source:str, language:str='Python', stdin:str='')->dict:
    lid=_language_id(language)
    created=_request('/submissions?base64_encoded=false&wait=false','POST',{'source_code':source,'language_id':lid,'stdin':stdin})
    token=created.get('token') if isinstance(created,dict) else None
    if not token: raise RuntimeError(f'Judge0 submission failed: {created}')
    result=None
    for _ in range(30):
        result=_request('/submissions/'+urllib.parse.quote(token)+'?base64_encoded=false&fields=stdout,stderr,compile_output,message,status,time,memory,language')
        sid=((result.get('status') or {}).get('id')) if isinstance(result,dict) else None
        if sid and sid>2: break
        time.sleep(1)
    return {'provider':'Judge0','tool':'judge0_execute','evidence_class':'runtime_experiment','endpoint':_base(),'language_id':lid,'result':result}


def smoke_test()->dict:
    d=execute("print('RAE_JUDGE0_OK')",'Python')
    r=d.get('result') or {}
    if 'RAE_JUDGE0_OK' not in (r.get('stdout') or ''): raise RuntimeError('Judge0 smoke test failed')
    return {'schema_version':'1.0','provider':'Judge0','tool':'judge0_execute','status':'RUNTIME_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),'endpoint':_base(),'credential_source':secret_source('JUDGE0_API_KEY'),'verification_class':'remote_python_execution'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--code'); ap.add_argument('--language',default='Python'); ap.add_argument('--stdin',default=''); ap.add_argument('--list-languages',action='store_true'); ap.add_argument('--smoke-test',action='store_true')
    a=ap.parse_args()
    if a.smoke_test: out=smoke_test()
    elif a.list_languages: out=languages()
    else:
        if a.code is None: ap.error('--code required')
        out=execute(a.code,a.language,a.stdin)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
