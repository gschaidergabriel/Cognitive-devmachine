#!/usr/bin/env python3
"""Semantic Scholar Academic Graph adapter for FRANK/RAE.

Most Graph API endpoints work without authentication. If SEMANTIC_SCHOLAR_API_KEY is
configured, it is sent via x-api-key. Search/index output is scholarly metadata and
must not be treated as independent confirmation of the underlying paper.
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from rae_secret_loader import get_secret, secret_source  # noqa: E402

BASE='https://api.semanticscholar.org/graph/v1'
FIELDS='paperId,title,abstract,year,authors,citationCount,referenceCount,url,openAccessPdf,externalIds,publicationTypes,publicationDate,venue'


def _get(path:str, params:dict|None=None)->dict:
    url=BASE+path
    if params: url += '?' + urllib.parse.urlencode(params)
    headers={'Accept':'application/json','User-Agent':'FRANK-RAE/8.8 Semantic Scholar adapter'}
    key=get_secret('SEMANTIC_SCHOLAR_API_KEY', required=False)
    if key: headers['x-api-key']=key
    last=None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last=e
            if e.code not in {429,500,502,503,504} or attempt==3: raise
            time.sleep(min(2**attempt,8))
    raise RuntimeError(last)


def _paper(p:dict)->dict:
    return {k:p.get(k) for k in ['paperId','title','abstract','year','citationCount','referenceCount','url','openAccessPdf','externalIds','publicationTypes','publicationDate','venue']} | {
        'authors':[{'authorId':a.get('authorId'),'name':a.get('name')} for a in p.get('authors') or []]
    }


def search(query:str, limit:int=10)->dict:
    d=_get('/paper/search',{'query':query,'limit':max(1,min(limit,100)),'fields':FIELDS})
    return {'provider':'Semantic Scholar','tool':'semantic_scholar_search','evidence_class':'external_scholarly_metadata','query':query,'total':d.get('total'),'items':[_paper(x) for x in d.get('data') or []]}


def lookup(paper_id:str)->dict:
    d=_get('/paper/'+urllib.parse.quote(paper_id,safe=':'),{'fields':FIELDS})
    return {'provider':'Semantic Scholar','tool':'semantic_scholar_search','evidence_class':'external_scholarly_metadata','paper':_paper(d)}


def smoke_test()->dict:
    d=search('global workspace theory',1)
    if not d.get('items'): raise RuntimeError('Semantic Scholar smoke test returned no papers')
    return {'schema_version':'1.0','provider':'Semantic Scholar','tool':'semantic_scholar_search','status':'RUNTIME_VERIFIED','checked_at':datetime.now(timezone.utc).isoformat(),'credential_required':False,'credential_source':secret_source('SEMANTIC_SCHOLAR_API_KEY'),'verification_endpoint_class':'graph/paper/search'}


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--query'); g.add_argument('--paper-id'); g.add_argument('--smoke-test',action='store_true')
    ap.add_argument('--limit',type=int,default=10)
    a=ap.parse_args()
    out=smoke_test() if a.smoke_test else (lookup(a.paper_id) if a.paper_id else search(a.query,a.limit))
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
