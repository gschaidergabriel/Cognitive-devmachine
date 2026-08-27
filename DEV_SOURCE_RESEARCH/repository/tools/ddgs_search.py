#!/usr/bin/env python3
"""Credential-free DuckDuckGo/DDGS fallback search adapter for FRANK/RAE.

Requires: pip install ddgs
This is a discovery layer, not a primary verification source.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone


def _client():
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise RuntimeError('DDGS package missing; install with: pip install ddgs') from exc
    return DDGS


def search(query:str, max_results:int=10, region:str='wt-wt')->dict:
    DDGS=_client()
    items=list(DDGS().text(query,region=region,max_results=max(1,min(max_results,50))))
    return {'provider':'DuckDuckGo/DDGS','tool':'duckduckgo_search','evidence_class':'external_web_discovery','query':query,'items':[{'title':x.get('title'),'url':x.get('href') or x.get('url'),'snippet':x.get('body')} for x in items]}


def smoke_test()->dict:
    d=search('OpenAlex API official documentation',2)
    if not d.get('items'): raise RuntimeError('DDGS smoke test returned no results')
    return {'schema_version':'1.0','provider':'DuckDuckGo/DDGS','tool':'duckduckgo_search','status':'RUNTIME_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),'credential_required':False,'verification_class':'text_search'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('query',nargs='?')
    ap.add_argument('--max-results',type=int,default=10)
    ap.add_argument('--region',default='wt-wt')
    ap.add_argument('--smoke-test',action='store_true')
    a=ap.parse_args()
    if a.smoke_test: out=smoke_test()
    else:
        if not a.query: ap.error('query required unless --smoke-test')
        out=search(a.query,a.max_results,a.region)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
