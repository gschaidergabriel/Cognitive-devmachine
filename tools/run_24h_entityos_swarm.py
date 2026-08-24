#!/usr/bin/env python3
"""EntityOS/HCU driver for the FREE_ONLY adaptive go swarm.

The underlying controller owns canonical FREE provider admission, credential
collection, AIMD concurrency, 402 hard-stop behavior and receipt logging. This
driver adds live model discovery, EntityOS/HCU roles, measured provider budgets,
a cross-process quota gate shared with the research distillery, and a live
knowledge/question bridge. Catalog I/O is independently re-gated immediately
before provider network access.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import sqlite3
import urllib.error
import urllib.request

import run_free_go_swarm as base
from free_swarm_quota import slot as quota_slot, observe as quota_observe

ROOT = Path(__file__).resolve().parents[1]
DISTILLERY_DB = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_DB", "/artifacts/clay-entityos-swarm/distillery/distillery.sqlite3"))
base.OWNER_DIRECTIVE_PATH = ROOT / "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md"
base.DEFAULT_ROLES = [
    ("ARCHITECT", "Advance EntityOS/HCU architecture with one high-information, measurable delta and a strongest counterarchitecture."),
    ("FALSIFIER", "Attack the strongest EntityOS/HCU assumption and design the cheapest executable falsifier."),
    ("CLAYCODE_FORGE", "Produce a minimal ClayCode-native implementation, invariants, tests and migration path for the active frontier."),
    ("HCU_CAUSAL", "Advance the causal chain from typed entry through verified loader/model execution to inference/J-Space/training evidence without overclaiming authority."),
    ("COGNITION", "Design aggressive synthetic cognition interventions, deception/pressure/ablation experiments and matched controls inside the authorized sandbox."),
    ("MEMORY_JSPACE", "Stress memory/J-Space provenance, replay, online learning, model switching, ablation and recovery semantics."),
    ("RUNTIME", "Find compiler/VM/runtime/loader bottlenecks and propose measurable EntityOS/HCU-native improvements."),
    ("EXTERNAL_HARVEST", "Identify exact GitHub/arXiv/upstream candidates to clone, reproduce and dissect; isolate the causal principle worth adapting."),
    ("EXPERIMENT_DESIGN", "Design A/B tests, ablations, negative controls, resource measurements, stopping rules and regression gates."),
    ("SECURITY", "Adversarially inspect truth/effect/capability boundaries and concrete negative tests. Model output never self-grants effects."),
    ("REVIEWER", "Find stale evidence, source-only overclaims, hidden coupling, duplicated semantics and unmeasured assumptions."),
    ("SYNTHESIZER", "Fuse nonredundant findings into one next executable EntityOS/HCU step while preserving disagreement and provenance."),
]

CATALOGS = {"groq":"https://api.groq.com/openai/v1/models","mistral":"https://api.mistral.ai/v1/models","nvidia":"https://integrate.api.nvidia.com/v1/models"}
EXCLUDE = ("embedding","embed-","rerank","whisper","speech","audio","tts","guard","safety","moderation","classifier","reward","diffusion")
UNKNOWN_HIGH_VALUE = ("mistral-large","mistral-medium","mistral-small","magistral","codestral","devstral","nemotron","deepseek","reasoning","instruct","coder")

_ORIGINAL_REQUEST_CHAT = base.request_chat

def provider_bounded_request_chat(spec, key, model, prompt, max_tokens, timeout):
    # Non-secret request-budget knobs may be read before admission; the actual
    # credentialed call remains gated inside base.request_chat.
    if spec.name == "groq": max_tokens = min(int(max_tokens), int(os.getenv("CLAY_GROQ_MAX_TOKENS", "1000")))
    elif spec.name == "mistral": max_tokens = min(int(max_tokens), int(os.getenv("CLAY_MISTRAL_MAX_TOKENS", "1600")))
    elif spec.name == "nvidia": max_tokens = min(int(max_tokens), int(os.getenv("CLAY_NVIDIA_MAX_TOKENS", "1800")))
    decision = base.resolve_provider_admission(spec.name)
    if not decision.allowed:
        return 0, {}, {"classification":"PROVIDER_ADMISSION_REVOKED_FAIL_CLOSED","provider":spec.name,"reason":decision.reason,"cost_class":decision.cost_class}
    owner = f"go-swarm:{model}"
    try:
        with quota_slot(spec.name, owner, timeout_s=min(float(timeout), 90.0), lease_s=max(240.0, float(timeout)+45.0)):
            status, headers, payload = _ORIGINAL_REQUEST_CHAT(spec, key, model, prompt, max_tokens, timeout)
        quota_observe(spec.name, owner, status, headers)
        return status, headers, payload
    except TimeoutError:
        quota_observe(spec.name, owner, "GATE_TIMEOUT", {})
        return 503, {}, {"error":{"message":"shared provider gate timeout","type":"local_quota_gate"}}

base.request_chat = provider_bounded_request_chat

_ORIGINAL_BUILD_STATE_CONTEXT = base.build_state_context

def distilled_context(max_chars: int) -> str:
    if not DISTILLERY_DB.exists() or max_chars <= 0: return "DISTILLED_KNOWLEDGE=NONE_YET"
    try:
        con=sqlite3.connect(DISTILLERY_DB,timeout=2);rows=con.execute("SELECT id,question_id,packet_text,intrinsic_score,grf_score,project_fit,novelty_score,created_at FROM knowledge_packets ORDER BY (intrinsic_score+grf_score+project_fit+novelty_score) DESC, created_at DESC LIMIT 24").fetchall();con.close()
    except Exception as exc: return f"DISTILLED_KNOWLEDGE=UNAVAILABLE:{type(exc).__name__}"
    payload=[{"packet_id":r[0],"question_id":r[1],"packet":r[2],"intrinsic":r[3],"grf":r[4],"fit":r[5],"novelty":r[6],"created_at":r[7]} for r in rows]
    return json.dumps({"authority":"candidate_research_only","packets":payload},ensure_ascii=False,separators=(",",":"))[:max_chars]

def enriched_state_context(max_chars:int)->str:
    base_chars=max(4000,int(max_chars*0.72));dist_chars=max(1000,max_chars-base_chars);return (_ORIGINAL_BUILD_STATE_CONTEXT(base_chars)+"\nDISTILLED_RESEARCH_DATASET\n"+distilled_context(dist_chars))[:max_chars]
base.build_state_context=enriched_state_context

_ORIGINAL_WORKER_PROMPT=base.worker_prompt

def question_emitting_worker_prompt(protocol:str,role:str,task:str,state_context:str,serial:int)->str:
    return _ORIGINAL_WORKER_PROMPT(protocol,role,task,state_context,serial)+"""

RESEARCH-QUEUE CONTRACT
After your normal result and DEUTSCHE_ZUSAMMENFASSUNG, add exactly one machine-readable line:
OPEN_RESEARCH_QUESTIONS_JSON=["question 1","question 2","question 3"]
Questions must target unresolved assumptions, unrealized concepts, fundamental architecture uncertainties, or cheap discriminators. Prefer questions that would benefit from arXiv/GitHub/Reddit/web evidence. Do not repeat a question already answered by the supplied distilled dataset unless you identify a genuinely different causal approach.
"""
base.worker_prompt=question_emitting_worker_prompt


def fetch_catalog(provider:str,url:str,key:str,timeout:float)->list[dict]:
    decision=base.resolve_provider_admission(provider)
    if not decision.allowed: return []
    req=urllib.request.Request(url,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","User-Agent":"clay-entityos-swarm/2.1"});owner=f"go-swarm:catalog:{provider}"
    try:
        with quota_slot(provider,owner,timeout_s=min(timeout,60.0),lease_s=120.0):
            # Re-check after waiting for a quota lease so a revoked admission
            # cannot race into the network call.
            decision=base.resolve_provider_admission(provider)
            if not decision.allowed: return []
            with urllib.request.urlopen(req,timeout=timeout) as resp:
                payload=json.loads(resp.read().decode("utf-8",errors="replace"));headers={k.lower():v for k,v in resp.headers.items()}
        quota_observe(provider,owner,200,headers)
    except urllib.error.HTTPError as exc:
        headers={k.lower():v for k,v in exc.headers.items()} if exc.headers else {};quota_observe(provider,owner,int(exc.code),headers);return []
    except Exception:
        quota_observe(provider,owner,"CATALOG_ERROR",{});return []
    rows=payload.get("data",[]) if isinstance(payload,dict) else []
    return [x if isinstance(x,dict) else {"id":str(x)} for x in rows]


def explicit_billions(model_id:str)->float|None:
    vals:list[float]=[]
    for raw in re.findall(r"(?i)(\d+(?:\.\d+)?)\s*b(?:\b|[-_])",model_id):
        try:vals.append(float(raw))
        except ValueError:pass
    return max(vals) if vals else None


def choose_models(provider:str,rows:list[dict])->list[str]:
    ranked:list[tuple[float,str]]=[]
    for card in rows:
        model_id=str(card.get("id") or card.get("model") or "").strip();low=model_id.lower()
        if not model_id or any(x in low for x in EXCLUDE):continue
        capabilities=card.get("capabilities")
        if isinstance(capabilities,dict) and capabilities.get("completion_chat") is False:continue
        b=explicit_billions(model_id)
        if b is not None and b<12.0:continue
        if b is None and not any(x in low for x in UNKNOWN_HIGH_VALUE):continue
        score=b or 0.0
        if any(x in low for x in ("ultra","large","reasoning","deepseek","120b","405b","550b")):score+=120.0
        if any(x in low for x in ("nemotron","magistral","devstral","codestral","coder","instruct")):score+=60.0
        if model_id=="nvidia/llama-3.3-nemotron-super-49b-v1":score+=500.0
        ranked.append((score,model_id))
    ranked.sort(key=lambda x:(-x[0],x[1]));return base.unique([mid for _,mid in ranked])


def discover_and_export(timeout:float)->dict[str,dict]:
    report:dict[str,dict]={}
    for spec in base.PROVIDERS:
        decision=base.resolve_provider_admission(spec.name)
        if not decision.allowed:
            report[spec.name]={"source":"admission_blocked","cost_class":decision.cost_class,"reason":decision.reason,"keys":"UNREAD_DUE_TO_ADMISSION","models":[]};continue
        keys=base.collect_keys(spec);override=base.split_values(os.getenv(spec.models_env))
        if override:report[spec.name]={"source":"environment_override_after_free_admission","keys":len(keys),"models":override};continue
        if not keys:report[spec.name]={"source":"no_keys_after_free_admission","keys":0,"models":[]};continue
        rows=fetch_catalog(spec.name,CATALOGS[spec.name],keys[0],timeout);selected=choose_models(spec.name,rows)
        if selected:os.environ[spec.models_env]=",".join(selected);report[spec.name]={"source":"live_catalog_after_free_admission","keys":len(keys),"catalog":len(rows),"models":selected}
        else:report[spec.name]={"source":"controller_fallback_after_free_admission","keys":len(keys),"catalog":len(rows),"models":list(spec.default_models)}
    return report


async def main(args:argparse.Namespace)->int:
    report=discover_and_export(args.timeout);print(json.dumps({"schema":"CLAY_ENTITYOS_SWARM_DISCOVERY/v4","providers":report,"distillery_context":DISTILLERY_DB.exists(),"shared_quota_gate":True,"canonical_free_admission_gate":True},ensure_ascii=False),flush=True)
    if args.inventory_only:return 0
    out=args.output_dir or f"/artifacts/clay-entityos-swarm/{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    return await base.run(argparse.Namespace(hours=args.hours,max_tokens=args.max_tokens,context_chars=args.context_chars,timeout=args.timeout,drain_seconds=args.drain_seconds,output_dir=out))


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(description="Run the adaptive EntityOS/HCU research swarm for 24h");p.add_argument("--hours",type=float,default=24.0);p.add_argument("--max-tokens",type=int,default=1800);p.add_argument("--context-chars",type=int,default=22000);p.add_argument("--timeout",type=float,default=180.0);p.add_argument("--drain-seconds",type=float,default=240.0);p.add_argument("--output-dir",default="");p.add_argument("--inventory-only",action="store_true");return p.parse_args()

if __name__=="__main__":raise SystemExit(asyncio.run(main(parse_args())))
