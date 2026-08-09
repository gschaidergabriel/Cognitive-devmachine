#!/usr/bin/env python3
"""Autonomous FREE_ONLY ClayCode research cycle.

This controller is a research engine, not a release gate. It may create research receipts,
external-research requests and bounded sandbox requests. It never marks work packages PASS,
changes canonical semantics, grants authority, or edits FRANK's Harness.
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
OUT=ROOT/"research_entity/claycode/autonomous/cycles"
INBOX=ROOT/"research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
REQ=ROOT/"research_entity/runtime/tool_requests"

CRITICAL_FILES=[
 "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json",
 "research_entity/claycode/g9/grammar.ebnf",
 "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
 "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
 "research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay",
 "research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md",
 "research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md",
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
            except json.JSONDecodeError: pass
        return {"raw":text[:12000],"parse_error":True}


def passages()->list[dict[str,str]]:
    out=[]
    for rel in CRITICAL_FILES:
        p=ROOT/rel
        if not p.exists():continue
        text=p.read_text(encoding="utf-8",errors="replace")
        for i in range(0,min(len(text),30000),5000):
            chunk=text[i:i+5000]
            if chunk.strip():out.append({"ref":f"{rel}#chars={i}-{i+len(chunk)}","text":chunk})
    return out


def simple_rank(query:str, ps:list[dict[str,str]], n:int=8)->list[dict[str,str]]:
    terms=set(re.findall(r"[a-z0-9_-]{4,}",query.lower()))
    scored=[]
    for p in ps:
        s=sum(p["text"].lower().count(t) for t in terms)
        scored.append((s,p))
    return [p for _,p in sorted(scored,key=lambda x:x[0],reverse=True)[:n]]


def nvidia_rank(query:str, ps:list[dict[str,str]], n:int=8)->tuple[list[dict[str,str]],str|None]:
    try:
        raw=nv.rerank(query,[p["text"] for p in ps])
        ranks=raw.get("rankings")
        if not isinstance(ranks,list):return simple_rank(query,ps,n),"rerank_shape_unrecognized"
        chosen=[]
        for r in ranks[:n]:
            idx=r.get("index") if isinstance(r,dict) else None
            if isinstance(idx,int) and 0<=idx<len(ps): chosen.append(ps[idx])
        return (chosen or simple_rank(query,ps,n)),None
    except Exception as exc:return simple_rank(query,ps,n),f"{type(exc).__name__}:{str(exc)[:300]}"


def model_ids(cards:list[dict[str,Any]])->list[str]:return [str(x.get("id")) for x in cards if x.get("id")]


def choose(ids:list[str], wants:list[str], used_families:set[str])->str|None:
    for w in wants:
        for mid in ids:
            if w in mid.lower() and nv.family(mid) not in used_families:return mid
    for mid in ids:
        if nv.family(mid) not in used_families:return mid
    return ids[0] if ids else None


def call_mistral(prompt:str, model:str)->tuple[dict[str,Any],dict[str,Any]]:
    out=mi.chat(prompt,model=model,system=SYSTEM,max_tokens=2048,temperature=0.05,reasoning_effort="high",json_mode=True,prompt_cache_key="claycode-base-cycle-v1")
    answer=(out.get("answers") or [{}])[0].get("content") or ""
    return parse_jsonish(answer),{"provider":"Mistral","model":model,"usage":out.get("usage") or {},"reasoning_trace_persisted":False}


def call_nv(prompt:str, model:str)->tuple[dict[str,Any],dict[str,Any]]:
    out=nv.chat(prompt,model=model,system=SYSTEM,max_tokens=2048,temperature=0.05)
    return parse_jsonish(out.get("content") or ""),{"provider":"NVIDIA","model":model,"family":nv.family(model),"usage":out.get("usage") or {}}


def compact_context(chosen:list[dict[str,str]])->str:
    blocks=[]
    for p in chosen:
        text=re.sub(r"\s+"," ",p["text"]).strip()
        blocks.append(f"SOURCE {p['ref']}\n{text[:2500]}")
    return "\n\n".join(blocks)


def cosine(a:list[float],b:list[float])->float:
    if not a or not b or len(a)!=len(b):return 0.0
    d=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return d/(na*nb) if na and nb else 0.0


def diversity(texts:list[str])->dict[str,Any]:
    if len(texts)<2:return {"status":"INSUFFICIENT"}
    try:
        e=nv.embed(texts,input_type="passage"); vec=[x.get("embedding") for x in e.get("data",[]) if isinstance(x,dict) and isinstance(x.get("embedding"),list)]
        pairs=[]
        for i in range(len(vec)):
            for j in range(i+1,len(vec)):pairs.append(round(cosine(vec[i],vec[j]),4))
        return {"status":"OK","pairwise_cosine":pairs,"mean_cosine":round(sum(pairs)/len(pairs),4) if pairs else None,"model":e.get("model")}
    except Exception as exc:return {"status":"UNAVAILABLE","error":f"{type(exc).__name__}:{str(exc)[:300]}"}


def safe_test(code:str)->bool:
    if not code or len(code)>12000:return False
    bad=("subprocess","socket","requests","urllib","shutil.rmtree","os.system","eval(","exec(","open(","pathlib","ctypes")
    return not any(x in code for x in bad)


def queue_request(tool:str,query:str="",code:str="",options:dict[str,Any]|None=None)->str:
    seed=f"{tool}|{query}|{code}|{json.dumps(options or {},sort_keys=True)}".encode()
    rid="ccauto-"+hashlib.sha256(seed).hexdigest()[:20]
    REQ.mkdir(parents=True,exist_ok=True); p=REQ/f"{rid}.json"
    if not p.exists():p.write_text(json.dumps({"schema_version":"1.0","request_id":rid,"tool":tool,"query":query,"code":code,"options":options or {}},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return str(p.relative_to(ROOT))


def main()->None:
    control=load(CONTROL); workspace=load(WORKSPACE)
    if control.get("status")!="ACTIVE":
        print(json.dumps({"status":"SKIPPED","reason":"control not ACTIVE"}));return
    focus=str(control.get("current_focus") or "ClayCode BASE highest-information open blocker")
    now=datetime.now(timezone.utc); cycle_id="ccauto-"+now.strftime("%Y%m%dT%H%M%SZ")
    provider={}; errors=[]; mistral_cards=[]; nv_cards=[]
    try:
        if secret_source("MISTRAL_API_KEY"):mistral_cards=mi.list_models(); provider["mistral"]={"status":"AVAILABLE","models":len(mistral_cards)}
        else:provider["mistral"]={"status":"CREDENTIAL_NOT_CONFIGURED"}
    except Exception as exc:provider["mistral"]={"status":"UNAVAILABLE","error":f"{type(exc).__name__}:{str(exc)[:300]}"};errors.append("mistral")
    try:
        if secret_source("NVIDIA_API_KEY"):nv_cards=nv.list_models(); provider["nvidia"]={"status":"AVAILABLE","models":len(nv_cards)}
        else:provider["nvidia"]={"status":"CREDENTIAL_NOT_CONFIGURED"}
    except Exception as exc:provider["nvidia"]={"status":"UNAVAILABLE","error":f"{type(exc).__name__}:{str(exc)[:300]}"};errors.append("nvidia")

    ps=passages(); chosen,rerank_error=nvidia_rank(focus,ps,8) if nv_cards else (simple_rank(focus,ps,8),"nvidia_unavailable")
    ctx=compact_context(chosen)
    base=f"CURRENT FOCUS: {focus}\n\nCURRENT EVIDENCE:\n{ctx}\n\nReturn JSON matching this shape: {json.dumps(SCHEMA_HINT)}"
    results={}; meta=[]; used=set()
    mids=model_ids(mistral_cards); nids=model_ids(nv_cards)

    # Architect: prefer Mistral adjustable reasoning; otherwise a distinct NVIDIA family.
    architect_model=next((x for x in ["mistral-medium-3-5","mistral-small-latest"] if x in mids),mids[0] if mids else None)
    try:
        if architect_model:
            results["architect"],m=call_mistral("Act as compiler architect. Find the smallest evidence-backed implementation step.\n"+base,architect_model);meta.append(m);used.add("mistral")
        else:
            nm=choose(nids,["nemotron","deepseek","qwen","glm"],used)
            if nm:results["architect"],m=call_nv("Act as compiler architect. Find the smallest evidence-backed implementation step.\n"+base,nm);meta.append(m);used.add(nv.family(nm))
    except Exception as exc:errors.append(f"architect:{type(exc).__name__}:{str(exc)[:300]}")

    arch=json.dumps(results.get("architect",{}),ensure_ascii=False)
    # Falsifier and alternative must prefer different base families.
    for role,wants,instruction in [
        ("falsifier",["deepseek","qwen","glm","nemotron","llama"],"Attack the architect claim. Seek a concrete counterexample, hidden semantic assumption, or simpler existing mechanism."),
        ("alternative",["qwen","glm","deepseek","nemotron","llama"],"Independently solve the focus without assuming the architect is right. Prefer a genuinely different implementation path.")]:
        nm=choose(nids,wants,used)
        if not nm:continue
        try:
            results[role],m=call_nv(f"{instruction}\nARCHITECT={arch}\n"+base,nm);meta.append(m);used.add(nv.family(nm))
        except Exception as exc:errors.append(f"{role}:{type(exc).__name__}:{str(exc)[:300]}")

    candidate_texts=[json.dumps(v,ensure_ascii=False,sort_keys=True) for v in results.values()]
    div=diversity(candidate_texts) if nv_cards else {"status":"NVIDIA_UNAVAILABLE"}

    nm=choose(nids,["nemotron","glm","qwen","deepseek","llama"],used) or (nids[0] if nids else None)
    judge_prompt="Synthesize without majority voting. Shared model ancestry is correlated evidence. Executable counterexamples outrank agreement. Return one discriminating next step, preserve unresolved conflicts, and set semantic_change_required true only if current semantics are executable-inadequate.\nCANDIDATES="+json.dumps(results,ensure_ascii=False)+"\nDIVERSITY="+json.dumps(div)+"\n"+base
    try:
        if nm:
            results["judge"],m=call_nv(judge_prompt,nm);meta.append(m)
        elif architect_model:
            results["judge"],m=call_mistral(judge_prompt,architect_model);meta.append(m)
    except Exception as exc:errors.append(f"judge:{type(exc).__name__}:{str(exc)[:300]}")

    judge=results.get("judge") or results.get("architect") or {}
    queued=[]
    code=str(judge.get("bounded_python_test") or "")
    if safe_test(code):queued.append(queue_request("judge0_execute",code=code,options={"timeout":20,"language":"Python"}))
    for q in (judge.get("external_queries") or [])[:1]:
        if isinstance(q,str) and q.strip():
            queued.append(queue_request("arxiv_search",query=q.strip(),options={"max_results":8}))
            queued.append(queue_request("openalex_search",query=q.strip(),options={"per_page":8}))

    receipt={
      "schema_version":"1.0","cycle_id":cycle_id,"created_at":now.isoformat(),"mode":"FREE_ONLY","target_stage":"BASE_CLAYCODE_RELEASE","focus":focus,
      "gate_snapshot":{"gate_status":workspace.get("gate_status"),"general_purpose_gate_status":workspace.get("general_purpose_gate_status"),"passed_apps":((workspace.get("application_acceptance") or {}).get("passed") or [])},
      "provider_discovery":provider,"selected_context_refs":[p["ref"] for p in chosen],"rerank_error":rerank_error,"model_calls":meta,"candidate_roles":results,
      "cross_model_diversity":div,"queued_safe_requests":queued,"errors":errors,
      "authority":{"research_only":True,"may_mark_work_package_pass":False,"may_promote_semantics":False,"may_modify_frank_harness":False},
      "next_focus":judge.get("next_focus") or judge.get("executable_discriminator") or focus,
      "supervisor_attention":bool(errors or judge.get("semantic_change_required") or div.get("mean_cosine",0)>0.94)
    }
    OUT.mkdir(parents=True,exist_ok=True); path=OUT/f"{cycle_id}.json"; path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    INBOX.parent.mkdir(parents=True,exist_ok=True); INBOX.write_text(json.dumps({"schema_version":"1.0","latest_cycle":cycle_id,"cycle_path":str(path.relative_to(ROOT)),"needs_review":receipt["supervisor_attention"],"next_focus":receipt["next_focus"],"errors":errors,"provider_discovery":provider,"instruction":"ChatGPT supervisor: inspect this cycle plus any completed tool_results, cross-check current official provider capabilities when material, then update supervisor state/control only when evidence justifies steering."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"COMPLETE","cycle_id":cycle_id,"receipt":str(path.relative_to(ROOT)),"queued":queued,"errors":errors},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
