#!/usr/bin/env python3
"""EntityOS/HCU 24h swarm driver with pre-secret/pre-network typed admission."""
from __future__ import annotations
import argparse, asyncio, json, os, re, urllib.error, urllib.request
from pathlib import Path
import run_free_go_swarm as base
from free_swarm_provider_admission import AdmissionError, admitted_free_providers, load_admission

ROOT=Path(__file__).resolve().parents[1]
base.OWNER_DIRECTIVE_PATH=ROOT/"governance/CLAY_24H_EXTERNAL_WORKER_SWARM_POLICY.md"
CATALOGS={"groq":"https://api.groq.com/openai/v1/models","mistral":"https://api.mistral.ai/v1/models","nvidia":"https://integrate.api.nvidia.com/v1/models"}
EXCLUDE=("embedding","embed-","rerank","whisper","speech","audio","tts","guard","safety","moderation","classifier","reward","diffusion")
UNKNOWN_HIGH_VALUE=("mistral-large","mistral-medium","mistral-small","magistral","codestral","devstral","nemotron","deepseek","reasoning","instruct","coder")
_ORIGINAL_REQUEST_CHAT=base.request_chat

def provider_bounded_request_chat(spec,key,model,prompt,max_tokens,timeout):
    caps={"groq":1000,"mistral":1600,"nvidia":1800}; cap=int(os.getenv(f"CLAY_{spec.name.upper()}_MAX_TOKENS",str(caps.get(spec.name,max_tokens)))); return _ORIGINAL_REQUEST_CHAT(spec,key,model,prompt,min(int(max_tokens),cap),timeout)
base.request_chat=provider_bounded_request_chat

def fetch_catalog(url,key,timeout):
    req=urllib.request.Request(url,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp: payload=json.loads(resp.read().decode("utf-8",errors="replace"))
    except (urllib.error.URLError,json.JSONDecodeError,TimeoutError): return []
    rows=payload.get("data",[]) if isinstance(payload,dict) else []; return [x if isinstance(x,dict) else {"id":str(x)} for x in rows]

def explicit_billions(model_id):
    vals=[]
    for raw in re.findall(r"(?i)(\d+(?:\.\d+)?)\s*b(?:\b|[-_])",model_id):
        try: vals.append(float(raw))
        except ValueError: pass
    return max(vals) if vals else None

def choose_models(provider,rows):
    ranked=[]
    for card in rows:
        mid=str(card.get("id") or card.get("model") or "").strip(); low=mid.lower()
        if not mid or any(x in low for x in EXCLUDE): continue
        caps=card.get("capabilities")
        if isinstance(caps,dict) and caps.get("completion_chat") is False: continue
        b=explicit_billions(mid)
        if b is not None and b<12: continue
        if b is None and not any(x in low for x in UNKNOWN_HIGH_VALUE): continue
        score=b or 0
        if any(x in low for x in ("ultra","large","reasoning","deepseek","120b","405b","550b")): score+=120
        if any(x in low for x in ("nemotron","magistral","devstral","codestral","coder","instruct")): score+=60
        ranked.append((score,mid))
    ranked.sort(key=lambda x:(-x[0],x[1])); return base.unique([m for _,m in ranked])

def discover_and_export(timeout,admission_file):
    # Admission resolution MUST precede collect_keys and fetch_catalog.
    doc=load_admission(admission_file); free=set(admitted_free_providers(doc)); report={}
    for spec in base.PROVIDERS:
        if spec.name not in free:
            report[spec.name]={"source":"admission_blocked","cost_class":"NOT_EFFECTIVE_FREE","keys":0,"models":[]}; continue
        keys=base.collect_keys(spec)
        override=base.split_values(os.getenv(spec.models_env))
        if override: report[spec.name]={"source":"environment_override","keys":len(keys),"models":override}; continue
        if not keys: report[spec.name]={"source":"no_keys","keys":0,"models":[]}; continue
        rows=fetch_catalog(CATALOGS[spec.name],keys[0],timeout); selected=choose_models(spec.name,rows)
        if selected: os.environ[spec.models_env]=",".join(selected); report[spec.name]={"source":"live_catalog","keys":len(keys),"catalog":len(rows),"models":selected}
        else: report[spec.name]={"source":"controller_fallback","keys":len(keys),"catalog":len(rows),"models":list(spec.default_models)}
    return doc,report

async def main(args):
    try: doc,report=discover_and_export(args.timeout,args.provider_admission_file)
    except AdmissionError as exc: print(json.dumps({"schema":"CLAY_ENTITYOS_SWARM_DISCOVERY/v3","state":"ADMISSION_BLOCKED","reason":str(exc)})); return 3
    print(json.dumps({"schema":"CLAY_ENTITYOS_SWARM_DISCOVERY/v3","admission_id":doc.admission_id,"providers":report},ensure_ascii=False),flush=True)
    if args.inventory_only: return 0
    out=args.output_dir or f"/artifacts/clay-entityos-swarm/{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    base_args=argparse.Namespace(hours=args.hours,max_tokens=args.max_tokens,context_chars=args.context_chars,timeout=args.timeout,drain_seconds=args.drain_seconds,output_dir=out,provider_admission_file=args.provider_admission_file)
    return await base.run(base_args)

def parse_args():
    p=argparse.ArgumentParser(); p.add_argument("--hours",type=float,default=24); p.add_argument("--max-tokens",type=int,default=1800); p.add_argument("--context-chars",type=int,default=22000); p.add_argument("--timeout",type=float,default=180); p.add_argument("--drain-seconds",type=float,default=240); p.add_argument("--output-dir",default=""); p.add_argument("--inventory-only",action="store_true"); p.add_argument("--provider-admission-file",default=os.getenv("CLAY_PROVIDER_ADMISSION_FILE","")); return p.parse_args()
if __name__=="__main__": raise SystemExit(asyncio.run(main(parse_args())))
