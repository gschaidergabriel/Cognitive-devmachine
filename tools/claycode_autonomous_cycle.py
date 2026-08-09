#!/usr/bin/env python3
"""Autonomous FREE_ONLY ClayCode research cycle.

Research engine only: it may create research receipts, provider capability observations,
external-research requests and bounded sandbox requests. It never marks ClayCode work
packages PASS, changes canonical semantics, grants execution authority, or edits Frank's
Harness. Provider catalog visibility is never treated as execution entitlement.
"""
from __future__ import annotations
import hashlib, json, math, re, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/"tools"
sys.path.insert(0,str(TOOLS))
from rae_secret_loader import secret_source  # noqa:E402
import nvidia_inference as nv  # noqa:E402
import mistral_inference as mi  # noqa:E402

CONTROL=ROOT/"research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
WORKSPACE=ROOT/"research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json"
SUPERVISOR=ROOT/"research_entity/claycode/autonomous/SUPERVISOR_STATE.json"
POOL=ROOT/"research_entity/claycode/autonomous/PROVIDER_EXECUTABLE_POOL.json"
OUT=ROOT/"research_entity/claycode/autonomous/cycles"
INBOX=ROOT/"research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
REQ=ROOT/"research_entity/runtime/tool_requests"

CRITICAL_FILES=[
 "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json",
 "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json",
 "research_entity/claycode/autonomous/SUPERVISOR_STATE.json",
 "research_entity/claycode/g9/grammar.ebnf",
 "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
 "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
 "research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay",
 "research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md",
 "research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md",
 "research_entity/trigger_runs/claycode/claycode-20260809T1727p0700-chatgpt-secondary-fn-parser-integration/FINAL_REPORT.md",
 "research_entity/trigger_runs/claycode/claycode-20260809T1711p0700-chatgpt-secondary-fn-closure/FINAL_REPORT.md"
]

SYSTEM="""You are a temporary ClayCode research worker. Target: general-purpose ClayCode compiler/runtime on Ubuntu for Frank v0.1. Less redesign, more compile. Model agreement is not evidence. Preserve negative results. No model output grants authority. A semantic change requires an executable counterexample. Return only compact JSON; never expose hidden reasoning traces."""
SCHEMA_HINT={
 "claim":"one precise claim",
 "counterhypothesis":"strongest competing explanation",
 "minimal_delta":"smallest implementation change",
 "executable_discriminator":"test that separates claim from counterhypothesis",
 "affected_work_packages":["CC-WP-.."],
 "semantic_change_required":False,
 "next_focus":"next highest-information target",
 "external_queries":[],
 "bounded_python_test":""
}


def load(path:Path,default:Any=None)->Any:
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError,json.JSONDecodeError):return {} if default is None else default


def clean_error(exc:Exception)->str:
    text=f"{type(exc).__name__}:{str(exc)}"
    text=re.sub(r"account\s+['\"][^'\"]+['\"]","account [REDACTED]",text,flags=re.I)
    text=re.sub(r"nvapi-[A-Za-z0-9_-]+","[REDACTED]",text)
    return text[:500]


def parse_jsonish(text:str)->dict[str,Any]:
    text=(text or "").strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?\s*","",text); text=re.sub(r"\s*```$","",text)
    try:
        x=json.loads(text); return x if isinstance(x,dict) else {"raw":text}
    except json.JSONDecodeError:
        m=re.search(r"\{.*\}",text,re.S)
        if m:
            try:
                x=json.loads(m.group(0)); return x if isinstance(x,dict) else {"raw":text}
            except json.JSONDecodeError:pass
        return {"raw":text[:12000],"parse_error":True}


def passages()->list[dict[str,str]]:
    out=[]
    for rel in CRITICAL_FILES:
        p=ROOT/rel
        if not p.exists():continue
        text=p.read_text(encoding="utf-8",errors="replace")
        for i in range(0,min(len(text),40000),5000):
            chunk=text[i:i+5000]
            if chunk.strip():out.append({"ref":f"{rel}#chars={i}-{i+len(chunk)}","text":chunk})
    return out


def simple_rank(query:str,ps:list[dict[str,str]],n:int=8)->list[dict[str,str]]:
    terms=set(re.findall(r"[a-z0-9_-]{4,}",query.lower()))
    scored=[]
    for p in ps:
        low=p["text"].lower(); score=sum(low.count(t) for t in terms)
        scored.append((score,p))
    return [p for _,p in sorted(scored,key=lambda x:x[0],reverse=True)[:n]]


def nvidia_rank(query:str,ps:list[dict[str,str]],n:int=8)->tuple[list[dict[str,str]],dict[str,Any]]:
    try:
        raw=nv.rerank(query,[p["text"] for p in ps])
        ranks=raw.get("rankings")
        chosen=[]
        if isinstance(ranks,list):
            for row in ranks[:n]:
                idx=row.get("index") if isinstance(row,dict) else None
                if isinstance(idx,int) and 0<=idx<len(ps):chosen.append(ps[idx])
        return (chosen or simple_rank(query,ps,n)),{"status":"SUCCESS","model":raw.get("model"),"route":raw.get("route")}
    except Exception as exc:
        return simple_rank(query,ps,n),{"status":"FALLBACK_LEXICAL","error":clean_error(exc)}


def model_ids(cards:list[dict[str,Any]])->list[str]:
    return [str(x.get("id")) for x in cards if x.get("id")]


def unique_models(rows:list[dict[str,Any]])->list[str]:
    seen=set();out=[]
    for row in rows:
        mid=str(row.get("model") or "")
        if mid and mid not in seen:seen.add(mid);out.append(mid)
    return out


def choose(ids:list[str],wants:list[str],used_families:set[str])->str|None:
    for w in wants:
        for mid in ids:
            if w in mid.lower() and nv.family(mid) not in used_families:return mid
    for mid in ids:
        if nv.family(mid) not in used_families:return mid
    return ids[0] if ids else None


def append_pool(pool:dict[str,Any],model:str,status:str,evidence_ref:str)->None:
    root=pool.setdefault("nvidia",{})
    key="verified" if status.startswith("RUNTIME_VERIFIED") else "failed_or_blocked"
    rows=[r for r in root.setdefault(key,[]) if str(r.get("model"))!=model]
    rows.append({"model":model,"family":nv.family(model),"status":status,"evidence_ref":evidence_ref,"observed_at":datetime.now(timezone.utc).isoformat()})
    root[key]=rows[-40:]
    if key=="verified":root["failed_or_blocked"]=[r for r in root.get("failed_or_blocked",[]) if str(r.get("model"))!=model]


def probe_pool(catalog:list[str],pool:dict[str,Any],budget:dict[str,int],cycle_id:str)->tuple[list[str],list[dict[str,Any]]]:
    verified=[m for m in unique_models((pool.get("nvidia") or {}).get("verified",[])) if m in catalog]
    blocked={str(r.get("model")) for r in (pool.get("nvidia") or {}).get("failed_or_blocked",[])}
    families={nv.family(m) for m in verified}
    preferred=[
      "nvidia/nemotron-3-super-120b-a12b",
      "nvidia/nemotron-3-ultra-550b-a55b",
      "deepseek-ai/deepseek-v4-flash-0731",
      "openai/gpt-oss-120b",
      "moonshotai/kimi-k2.6",
      "poolside/laguna-xs-2.1",
      "ibm/granite-34b-code-instruct"
    ]
    probes=[]
    for mid in preferred:
        if len(families)>=4 or budget["used"]>=budget["max"]-4:break
        if mid not in catalog or mid in verified or mid in blocked:continue
        budget["used"]+=1
        try:
            out=nv.chat("Reply with exactly OK.",model=mid,max_tokens=16,temperature=0.0)
            append_pool(pool,mid,"RUNTIME_VERIFIED_PROBE",f"cycle:{cycle_id}")
            verified.append(mid);families.add(nv.family(mid));probes.append({"model":mid,"status":"SUCCESS","usage":out.get("usage") or {}})
        except nv.RateLimited as exc:
            probes.append({"model":mid,"status":"RATE_LIMITED","error":clean_error(exc)});break
        except nv.FreeOnlyViolation as exc:
            append_pool(pool,mid,"FREE_ONLY_BLOCKED_402",f"cycle:{cycle_id}");probes.append({"model":mid,"status":"FREE_ONLY_BLOCKED_402","error":clean_error(exc)})
        except Exception as exc:
            e=clean_error(exc);status="ACCOUNT_FUNCTION_NOT_FOUND_404" if "HTTP 404" in e or "not found for account" in e.lower() else "PROBE_FAILED_TRANSIENT_OR_MODEL_SPECIFIC"
            if status.startswith("ACCOUNT_"):append_pool(pool,mid,status,f"cycle:{cycle_id}")
            probes.append({"model":mid,"status":status,"error":e})
    return verified,probes


def call_mistral(prompt:str,model:str,budget:dict[str,int])->tuple[dict[str,Any],dict[str,Any]]:
    if budget["used"]>=budget["max"]:raise RuntimeError("cycle LLM call budget exhausted")
    budget["used"]+=1
    out=mi.chat(prompt,model=model,system=SYSTEM,max_tokens=2048,temperature=0.05,reasoning_effort="high",json_mode=True,prompt_cache_key="claycode-base-cycle-v1")
    answer=(out.get("answers") or [{}])[0].get("content") or ""
    return parse_jsonish(answer),{"provider":"Mistral","model":model,"family":"mistral-direct","usage":out.get("usage") or {},"reasoning_trace_persisted":False}


def call_nv(prompt:str,model:str,budget:dict[str,int])->tuple[dict[str,Any],dict[str,Any]]:
    if budget["used"]>=budget["max"]:raise RuntimeError("cycle LLM call budget exhausted")
    budget["used"]+=1
    out=nv.chat(prompt,model=model,system=SYSTEM,max_tokens=2048,temperature=0.05)
    return parse_jsonish(out.get("content") or ""),{"provider":"NVIDIA","model":model,"family":nv.family(model),"usage":out.get("usage") or {},"reasoning_trace_persisted":False}


def compact_context(chosen:list[dict[str,str]])->str:
    blocks=[]
    for p in chosen:
        text=re.sub(r"\s+"," ",p["text"]).strip();blocks.append(f"SOURCE {p['ref']}\n{text[:2500]}")
    return "\n\n".join(blocks)


def cosine(a:list[float],b:list[float])->float:
    if not a or not b or len(a)!=len(b):return 0.0
    dot=sum(x*y for x,y in zip(a,b));na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0


def diversity(texts:list[str])->dict[str,Any]:
    if len(texts)<2:return {"status":"INSUFFICIENT"}
    last="embedding unavailable"
    for model in [nv.DEFAULT_EMBED_MODEL,"nvidia/nv-embedqa-e5-v5"]:
        try:
            emb=nv.embed(texts,model=model,input_type="passage");vec=[x.get("embedding") for x in emb.get("data",[]) if isinstance(x,dict) and isinstance(x.get("embedding"),list)]
            pairs=[]
            for i in range(len(vec)):
                for j in range(i+1,len(vec)):pairs.append(round(cosine(vec[i],vec[j]),4))
            if pairs:return {"status":"OK","pairwise_cosine":pairs,"mean_cosine":round(sum(pairs)/len(pairs),4),"model":model}
        except Exception as exc:last=clean_error(exc)
    return {"status":"UNAVAILABLE","error":last}


def safe_test(code:str)->bool:
    if not code or len(code)>14000:return False
    bad=("subprocess","socket","requests","urllib","shutil.rmtree","os.system","eval(","exec(","open(","pathlib","ctypes","fork(")
    return not any(x in code for x in bad)


def queue_request(tool:str,query:str="",code:str="",options:dict[str,Any]|None=None)->str:
    seed=f"{tool}|{query}|{code}|{json.dumps(options or {},sort_keys=True)}".encode();rid="ccauto-"+hashlib.sha256(seed).hexdigest()[:20]
    REQ.mkdir(parents=True,exist_ok=True);p=REQ/f"{rid}.json"
    if not p.exists():p.write_text(json.dumps({"schema_version":"1.0","request_id":rid,"tool":tool,"query":query,"code":code,"options":options or {}},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return str(p.relative_to(ROOT))


def main()->None:
    control=load(CONTROL);workspace=load(WORKSPACE);supervisor=load(SUPERVISOR);pool=load(POOL,{"schema_version":"1.0","mode":"FREE_ONLY","nvidia":{"verified":[],"failed_or_blocked":[]},"mistral":{"verified":[]}})
    if control.get("status")!="ACTIVE":print(json.dumps({"status":"SKIPPED","reason":"control not ACTIVE"}));return
    policy=control.get("cycle_policy") or {};budget={"max":int(policy.get("max_llm_calls_per_cycle",8)),"used":0}
    focus=str(control.get("current_focus") or supervisor.get("current_focus") or "ClayCode BASE highest-information open blocker")
    now=datetime.now(timezone.utc);cycle_id="ccauto-"+now.strftime("%Y%m%dT%H%M%SZ")
    provider={};errors=[];mistral_cards=[];nv_cards=[]
    try:
        if secret_source("MISTRAL_API_KEY"):
            mistral_cards=mi.list_models();provider["mistral"]={"status":"AVAILABLE","models":len(mistral_cards)};pool.setdefault("mistral",{})["status"]="CATALOG_AVAILABLE"
        else:provider["mistral"]={"status":"CREDENTIAL_NOT_CONFIGURED"};pool.setdefault("mistral",{})["status"]="CREDENTIAL_NOT_CONFIGURED"
    except Exception as exc:provider["mistral"]={"status":"UNAVAILABLE","error":clean_error(exc)};errors.append("mistral discovery failed")
    try:
        if secret_source("NVIDIA_API_KEY"):nv_cards=nv.list_models();provider["nvidia"]={"status":"AVAILABLE","models":len(nv_cards)}
        else:provider["nvidia"]={"status":"CREDENTIAL_NOT_CONFIGURED"}
    except Exception as exc:provider["nvidia"]={"status":"UNAVAILABLE","error":clean_error(exc)};errors.append("nvidia discovery failed")

    mids=model_ids(mistral_cards);nids=model_ids(nv_cards)
    verified_nv,probes=probe_pool(nids,pool,budget,cycle_id) if nids else ([],[])
    pool["last_cycle"]=cycle_id;pool["last_probe_results"]=probes;POOL.parent.mkdir(parents=True,exist_ok=True);POOL.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    provider["nvidia_executable_pool"]={"verified_models":verified_nv,"families":sorted({nv.family(x) for x in verified_nv}),"probes":probes}

    ps=passages();chosen,rerank=nvidia_rank(focus,ps,8) if nids else (simple_rank(focus,ps,8),{"status":"NVIDIA_UNAVAILABLE"});ctx=compact_context(chosen)
    base=f"CURRENT FOCUS: {focus}\n\nCURRENT EVIDENCE:\n{ctx}\n\nReturn JSON matching this shape: {json.dumps(SCHEMA_HINT)}"
    results={};meta=[];used=set()
    architect_model=next((x for x in ["mistral-medium-3-5","mistral-small-latest"] if x in mids),mids[0] if mids else None)
    try:
        if architect_model:
            results["architect"],m=call_mistral("Act as compiler architect. Find the smallest evidence-backed implementation step.\n"+base,architect_model,budget);meta.append(m);used.add("mistral-direct")
        else:
            nm=choose(verified_nv,["nemotron-3-super","nemotron-3-ultra","nemotron","gpt-oss","glm"],used)
            if nm:results["architect"],m=call_nv("Act as compiler architect. Find the smallest evidence-backed implementation step.\n"+base,nm,budget);meta.append(m);used.add(nv.family(nm))
    except Exception as exc:errors.append("architect:"+clean_error(exc))

    arch=json.dumps(results.get("architect",{}),ensure_ascii=False)
    for role,wants,instruction in [
      ("falsifier",["deepseek","gpt-oss","glm","kimi","poolside","nemotron"],"Attack the architect claim. Seek the strongest concrete counterexample, hidden semantic assumption, or simpler existing mechanism."),
      ("alternative",["glm","deepseek","gpt-oss","kimi","poolside","granite","nemotron"],"Independently solve the focus without assuming the architect is right. Prefer a genuinely different implementation path.")]:
        nm=choose(verified_nv,wants,used)
        if not nm:continue
        try:results[role],m=call_nv(f"{instruction}\nARCHITECT={arch}\n"+base,nm,budget);meta.append(m);used.add(nv.family(nm))
        except Exception as exc:errors.append(role+":"+clean_error(exc))

    candidate_texts=[json.dumps(v,ensure_ascii=False,sort_keys=True) for v in results.values()];div=diversity(candidate_texts) if nids else {"status":"NVIDIA_UNAVAILABLE"}
    judge_model=choose(verified_nv,["nemotron-3-super","gpt-oss","glm","deepseek","kimi","nemotron"],used) or (verified_nv[0] if verified_nv else None)
    judge_prompt="Synthesize without majority voting. Shared model ancestry is correlated evidence. Executable counterexamples outrank agreement. Return one discriminating next step, preserve unresolved conflicts, and set semantic_change_required true only if current semantics are executable-inadequate.\nCANDIDATES="+json.dumps(results,ensure_ascii=False)+"\nDIVERSITY="+json.dumps(div)+"\n"+base
    try:
        if judge_model:results["judge"],m=call_nv(judge_prompt,judge_model,budget);meta.append(m)
        elif architect_model:results["judge"],m=call_mistral(judge_prompt,architect_model,budget);meta.append(m)
    except Exception as exc:errors.append("judge:"+clean_error(exc))

    synthesis=results.get("judge") or results.get("architect") or results.get("falsifier") or results.get("alternative") or {}
    queued=[];code=str(synthesis.get("bounded_python_test") or "")
    if safe_test(code):queued.append(queue_request("judge0_execute",code=code,options={"timeout":20,"language":"Python"}))
    queries=[q.strip() for q in (synthesis.get("external_queries") or []) if isinstance(q,str) and q.strip()][:1]
    for q in queries:
        queued.append(queue_request("arxiv_search",query=q,options={"max_results":8}));queued.append(queue_request("openalex_search",query=q,options={"per_page":8}));queued.append(queue_request("duckduckgo_search",query=q,options={"max_results":8}))

    receipt={"schema_version":"1.1","cycle_id":cycle_id,"created_at":now.isoformat(),"mode":"FREE_ONLY","target_stage":"BASE_CLAYCODE_RELEASE","focus":focus,
      "gate_snapshot":{"gate_status":workspace.get("gate_status"),"general_purpose_gate_status":workspace.get("general_purpose_gate_status"),"passed_apps":((workspace.get("application_acceptance") or {}).get("passed") or [])},
      "provider_discovery":provider,"retrieval":{"selected_context_refs":[p["ref"] for p in chosen],"rerank":rerank},"llm_call_budget":budget,"model_calls":meta,"candidate_roles":results,"cross_model_diversity":div,"queued_safe_requests":queued,"errors":errors,
      "authority":{"research_only":True,"may_mark_work_package_pass":False,"may_promote_semantics":False,"may_modify_frank_harness":False},"next_focus":synthesis.get("next_focus") or synthesis.get("executable_discriminator") or focus,
      "supervisor_attention":bool(errors or synthesis.get("semantic_change_required") or (isinstance(div.get("mean_cosine"),float) and div["mean_cosine"]>0.94) or len({m.get("family") for m in meta if m.get("family")})<2)}
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/f"{cycle_id}.json";path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    INBOX.parent.mkdir(parents=True,exist_ok=True);INBOX.write_text(json.dumps({"schema_version":"1.1","latest_cycle":cycle_id,"cycle_path":str(path.relative_to(ROOT)),"needs_review":receipt["supervisor_attention"],"next_focus":receipt["next_focus"],"errors":errors,"provider_discovery":provider,"instruction":"ChatGPT supervisor: inspect cycle/tool_results, prefer executable evidence, use all materially relevant connected capabilities, then steer control/state only if evidence warrants it. FREE_ONLY; no gate promotion or Frank-Harness modification."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"COMPLETE","cycle_id":cycle_id,"receipt":str(path.relative_to(ROOT)),"verified_nv":verified_nv,"queued":queued,"errors":errors,"llm_call_budget":budget},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
