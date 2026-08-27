#!/usr/bin/env python3
"""Merge sanitized Groq health into the consolidated RAE provider health state."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import groq_inference

HEALTH=ROOT/'research_entity'/'runtime'/'PROVIDER_HEALTH.json'
RECEIPT=ROOT/'research_entity'/'runtime'/'groq_verification.json'

def main():
    receipt=groq_inference.smoke_test()
    RECEIPT.parent.mkdir(parents=True,exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try: d=json.loads(HEALTH.read_text(encoding='utf-8'))
    except Exception: d={'schema_version':'1.0','results':[],'counts':{}}
    item={'tool':'groq_inference','provider':'Groq Llama 3.1 8B Instant','status':'RUNTIME_VERIFIED','receipt':receipt,'receipt_path':'research_entity/runtime/groq_verification.json'}
    rows=[x for x in d.get('results',[]) if x.get('tool')!='groq_inference']
    rows.append(item)
    d['results']=rows
    counts={}
    for x in rows: counts[x.get('status','UNKNOWN')]=counts.get(x.get('status','UNKNOWN'),0)+1
    d['counts']=counts
    d['checked_at']=datetime.now(timezone.utc).isoformat()
    d['groq_small_model_proxy']='llama-3.1-8b-instant / 8b_proxy_for_4b'
    HEALTH.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'status':'RUNTIME_VERIFIED','model':receipt.get('model')}))

if __name__=='__main__': main()
