#!/usr/bin/env python3
"""Write a sanitized Groq runtime probe receipt even on failure."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import groq_inference
from rae_secret_loader import get_secret

OUT=ROOT/'research_entity'/'runtime'/'groq_probe.json'

def redact(text: str) -> str:
    try:
        secret=get_secret('GROQ_API_KEY',required=False)
    except Exception:
        secret=None
    if secret: text=text.replace(secret,'[REDACTED]')
    return text[:1500]

def main():
    out={'schema_version':'1.0','checked_at':datetime.now(timezone.utc).isoformat(),'provider':'Groq','model':groq_inference.DEFAULT_MODEL,'credential_value_exposed':False}
    try:
        models=groq_inference.list_models()
        ids=[x.get('id') for x in models if isinstance(x,dict) and x.get('id')]
        out['model_list_ok']=True
        out['model_count']=len(ids)
        out['default_model_available']=groq_inference.DEFAULT_MODEL in ids
        out['visible_model_ids']=ids
        if not out['default_model_available']:
            out['status']='MODEL_UNAVAILABLE'
        else:
            r=groq_inference.chat('Reply with exactly: GROQ_8B_OK',max_tokens=16,temperature=0.0)
            out['chat_ok']='GROQ_8B_OK' in (r.get('content') or '')
            out['usage']=r.get('usage') or {}
            out['status']='RUNTIME_VERIFIED' if out['chat_ok'] else 'SENTINEL_MISMATCH'
    except Exception as exc:
        out.update({'status':'FAILED','error_type':type(exc).__name__,'error':redact(str(exc))})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'model':out['model']},ensure_ascii=False))

if __name__=='__main__': main()
