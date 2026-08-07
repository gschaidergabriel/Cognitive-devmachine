#!/usr/bin/env python3
"""Piston public/self-hosted code execution adapter for FRANK/RAE.

Defaults to EMKC's public v2 endpoint. Set PISTON_API_URL to override for a self-hosted
instance. Public Piston is a reproducibility aid, not a trusted target-runtime replica.
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from rae_secret_loader import get_secret  # noqa: E402

DEFAULT_BASE='https://emkc.org/api/v2/piston'


def _base()->str:
    return (os.environ.get('PISTON_API_URL') or get_secret('PISTON_API_URL',required=False) or DEFAULT_BASE).rstrip('/')


def _request(path:str, method:str='GET', body:dict|None=None):
    data=json.dumps(body).encode() if body is not None else None
    headers={'Accept':'application/json','Content-Type':'application/json','User-Agent':'FRANK-RAE/8.8 Piston adapter'}
    req=urllib.request.Request(_base()+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())


def runtimes()->list:
    return _request('/runtimes')


def _runtime(language:str)->dict:
    needle=language.lower()
    items=runtimes()
    candidates=[x for x in items if needle==str(x.get('language','')).lower() or needle in [str(a).lower() for a in x.get('aliases') or []]]
    if not candidates: raise RuntimeError(f'Piston runtime not found: {language}')
    return candidates[-1]


def execute(code:str, language:str='python', stdin:str='')->dict:
    rt=_runtime(language)
    payload={'language':rt['language'],'version':rt['version'],'files':[{'name':'main','content':code}],'stdin':stdin}
    d=_request('/execute','POST',payload)
    return {'provider':'Piston','tool':'piston_execute','evidence_class':'runtime_experiment','endpoint':_base(),'runtime':rt,'result':d}


def smoke_test()->dict:
    d=execute("print('RAE_PISTON_OK')",'python')
    out=((d.get('result') or {}).get('run') or {}).get('stdout') or ''
    if 'RAE_PISTON_OK' not in out: raise RuntimeError('Piston smoke test failed')
    return {'schema_version':'1.0','provider':'Piston','tool':'piston_execute','status':'RUNTIME_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),'credential_required':False,'endpoint':_base(),'verification_class':'remote_python_execution'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--code'); ap.add_argument('--language',default='python'); ap.add_argument('--stdin',default=''); ap.add_argument('--list-runtimes',action='store_true'); ap.add_argument('--smoke-test',action='store_true')
    a=ap.parse_args()
    if a.smoke_test: out=smoke_test()
    elif a.list_runtimes: out=runtimes()
    else:
        if a.code is None: ap.error('--code required')
        out=execute(a.code,a.language,a.stdin)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
