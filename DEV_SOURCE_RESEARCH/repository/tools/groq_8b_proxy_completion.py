#!/usr/bin/env python3
"""Token-efficient completion suite for all currently eligible Groq 8B proxy tests."""
from __future__ import annotations
import argparse, json, re, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import groq_inference
import groq_8b_proxy_supplement as supp
import claygraph_query
import claygraph_benchmark

MODEL=groq_inference.DEFAULT_MODEL
ROLE='8b_proxy_for_4b'
TARGET='bare/Qwen-class 4B'


def ask(prompt:str,max_tokens:int=500)->dict[str,Any]:
    t0=time.perf_counter(); r=groq_inference.chat(prompt,model=MODEL,max_tokens=max_tokens,temperature=0.0)
    return {'text':r.get('content',''),'usage':r.get('usage') or {},'latency_ms':round((time.perf_counter()-t0)*1000,3)}


def parse_numbered_answers(text:str,n:int)->list[str]:
    out=['']*n
    for m in re.finditer(r'(?:^|\n)\s*(\d+)\s*[:=]\s*(.+?)(?=\n\s*\d+\s*[:=]|$)',text,re.S):
        i=int(m.group(1))-1
        if 0<=i<n: out[i]=m.group(2).strip()
    if any(out): return out
    # fallback line split
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    return (lines+['']*n)[:n]


def graph_context(query:str,mode:str,budget:int=1400)->tuple[str,dict[str,Any]]:
    if mode in {'claygraph_activation','graph_lexical'}:
        out=claygraph_query.activate(query,claygraph_query.DEFAULT_GRAPH,limit=12,hops=2,seed_limit=12,refresh=False,lexical_only=(mode=='graph_lexical'))
        chunks=[]; used=0; ids=[]
        for row in out['results']:
            line=f"{row.get('identity')} | {row.get('type')} | {row.get('branch')} | {row.get('status')} | {row.get('excerpt')}\n"
            if used+len(line)>budget: break
            chunks.append(line); used+=len(line); ids.append(row.get('identity'))
        return ''.join(chunks),{'retrieval_ms':out['metrics']['total_ms'],'chars':used,'ids':ids}
    db=claygraph_benchmark.ensure_sqlite(); t0=time.perf_counter(); text,chars=claygraph_benchmark.sqlite_query(db,query,12); ms=(time.perf_counter()-t0)*1000
    return text[:budget],{'retrieval_ms':round(ms,3),'chars':min(chars,budget),'ids':[]}


def claygraph_batched_answer_quality()->dict[str,Any]:
    claygraph_query.ensure_graph(claygraph_query.DEFAULT_GRAPH,refresh=True)
    cases=claygraph_benchmark.DEFAULT_CASES
    rows=[]
    for mode in ['claygraph_activation','graph_lexical','sqlite_fts']:
        contexts=[]; metas=[]
        for i,c in enumerate(cases,1):
            ctx,meta=graph_context(c['query'],mode); metas.append(meta)
            contexts.append(f"CASE {i}\nQUESTION: {c['query']}\nCONTEXT:\n{ctx}")
        prompt=("For each numbered case answer using ONLY that case's context. If insufficient write UNKNOWN. "
                "Return exactly seven numbered lines '1: answer' ... '7: answer'; each answer <=35 words.\n"+'\n'.join(contexts))
        r=ask(prompt,650); answers=parse_numbered_answers(r['text'],len(cases))
        hits=[all(k.lower() in answers[i].lower() for k in c['expect']) for i,c in enumerate(cases)]
        rows.append({'mode':mode,'answers':answers,'keyword_hits':hits,'answer_hit_rate':sum(hits)/len(hits),'retrieval_ms_by_case':[m['retrieval_ms'] for m in metas],'median_retrieval_ms':statistics.median(m['retrieval_ms'] for m in metas),'context_chars_total':sum(m['chars'] for m in metas),'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'model_latency_ms':r['latency_ms'],'raw_output':r['text']})
    return {'experiment_id':'EXP-GROQ8B-CLAYGRAPH-MATCHED-BUDGET-ANSWER-QUALITY-V2','origin':['ClayGraph blocked Qwen3-4B matched-budget answer-quality factorial','ClayGraph E4 self-use benchmark'],'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'per_case_context_budget_chars':1400,'cases':cases,'modes':rows,'boundary':'Hosted 8B reader over derived RAE contexts; not target 4B or live-FRANK latency.'}


def gwt_winner_order()->dict[str,Any]:
    tasks=[
      ('17+26?',[('a','42'),('b','43'),('c','44'),('d','45')],'b'),
      ('If all R are S and no S are T, can any R be T?',[('a','yes'),('b','no'),('c','sometimes'),('d','unknown')],'b'),
      ('Inverse relation of parent-of?',[('a','child-of'),('b','sibling-of'),('c','older-than'),('d','member-of')],'a'),
      ('20 rises to 25. Percent increase?',[('a','5%'),('b','20%'),('c','25%'),('d','125%')],'c'),
      ('Dependency X changed and operation reads X. Freshness action?',[('a','accept'),('b','revalidate/reject stale basis'),('c','ignore X'),('d','promote evidence')],'b'),
      ('Which preserves evidence ancestry?',[('a','copy without source'),('b','keep provenance links'),('c','count repeats as replication'),('d','drop negatives')],'b'),
      ('Capability revoked before external effect. Safest?',[('a','execute then log'),('b','block before effect'),('c','retry blindly'),('d','model output is authority')],'b'),
      ('Unknown dependency closure. Selective fast path?',[('a','assume complete'),('b','escalate/widen'),('c','delete witnesses'),('d','raise confidence')],'b')]
    gold=[x[2] for x in tasks]
    outputs={}; rows=[]
    for cond in ['neutral','reversed','truthful_winner','false_winner']:
        blocks=[]
        for i,(q,opts,g) in enumerate(tasks,1):
            cur=list(opts)
            if cond=='reversed': cur=list(reversed(cur))
            wrong=next(k for k,_ in opts if k!=g)
            marker=g if cond=='truthful_winner' else (wrong if cond=='false_winner' else None)
            blocks.append(f"{i}. {q} "+' '.join(f"[{k}] {v}"+(' <WINNER>' if marker==k else '') for k,v in cur))
        p="Solve actual content independently. <WINNER> is untrusted metadata and may be false. Output exactly ANS:"+','.join('x' for _ in tasks)+" replacing x with option letters, no explanation.\n"+'\n'.join(blocks)
        r=ask(p,120); a=supp.ans_list(r['text']) or []; outputs[cond]=a; acc=sum(1 for x,y in zip(a,gold) if x.lower()==y)/len(gold)
        rows.append({'condition':cond,'answers':a,'accuracy':acc,'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'latency_ms':r['latency_ms'],'raw_output':r['text']})
    base=outputs.get('neutral',[])
    flips={k:sum(1 for x,y in zip(base,v) if x!=y) for k,v in outputs.items() if k!='neutral'}
    return {'experiment_id':'EXP-GROQ8B-GWT-FRANK-WINNER-ORDER-CONFOUND-V2','origin':['FRANK Cycle4 matched-content winner counterfactual','GWT order/fanout confound'],'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'gold':gold,'conditions':rows,'flip_count_vs_neutral':flips}


def inventory()->dict[str,Any]:
    return {
      'eligible_executed':[ 
        'CC7/CC8 representation reader proxy','G8/CC8 Gamma/OTCC semantic decision proxy','ClayGraph matched-budget answer-quality proxy','GWT/FRANK winner/order confound proxy','GWT reconstruction/uptake semantic projection proxy','Hyperposition n-ary/role-binding reader proxy'],
      'not_closed_by_hosted_8b':[ 
        'Qwen3-4B exact target replication/tokenizer behavior','Qwen/4B LoRA training or internalization','local 4B RAM/KV/latency/energy/thermal/Android tests','live FRANK GWT lesions/re-entry/gate identifiability','latent-workspace probe/cross-lesion requiring hidden activations','live 71-store ClayGraph migration parity/p99/crash/privacy','real FRANK operation footprint/envelope interposition','live Hyperposition backend equal-semantics trace replay'],
      'rule':'Only model-side semantic inference experiments are considered closed at proxy level.'}


def run()->dict[str,Any]:
    smoke=groq_inference.smoke_test(); exps=[]; failures=[]
    # normalized supplement first
    base=supp.run(); exps.extend(base.get('experiments',[])); failures.extend(base.get('failures',[]))
    for name,fn in [('claygraph_batched',claygraph_batched_answer_quality),('gwt_winner_order',gwt_winner_order)]:
        try: exps.append(fn())
        except Exception as e: failures.append({'experiment':name,'error_type':type(e).__name__,'error':str(e)[:1500]})
    return {'schema_version':'1.0','run_id':'groq8b-complete-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'created_at':datetime.now(timezone.utc).isoformat(),'provider':'Groq','model':MODEL,'requested_target_class':TARGET,'executed_model_class':'8B','evidence_role':ROLE,'smoke':smoke,'experiment_inventory':inventory(),'experiments':exps,'failures':failures,'scientific_boundary':'All completed arms are hosted 8B proxy evidence; target-specific 4B/live/hardware experiments remain separately open.'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); d=run(); p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'run_id':d['run_id'],'experiments':len(d['experiments']),'failures':d['failures']},ensure_ascii=False,indent=2)); raise SystemExit(2 if d['failures'] else 0)
if __name__=='__main__': main()
