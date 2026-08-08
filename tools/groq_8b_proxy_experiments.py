#!/usr/bin/env python3
"""Run outstanding small-model research experiments on Groq Llama 3.1 8B Instant.

All results are explicitly `8b_proxy_for_4b`. This batch is designed to close model-side
blocked tests without pretending that an 8B hosted model is Qwen3-4B or live FRANK.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import groq_inference  # noqa: E402
import claygraph_query  # noqa: E402
import claygraph_benchmark  # noqa: E402

MODEL = groq_inference.DEFAULT_MODEL
EVIDENCE_ROLE = "8b_proxy_for_4b"
TARGET = "bare/Qwen-class 4B"


def call(prompt: str, max_tokens: int = 512) -> dict[str, Any]:
    t0 = time.perf_counter()
    out = groq_inference.chat(prompt, model=MODEL, max_tokens=max_tokens, temperature=0.0)
    return {
        "content": out.get("content", ""),
        "usage": out.get("usage", {}),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
        "model": out.get("model", MODEL),
        "evidence_role": EVIDENCE_ROLE,
    }


def parse_json_array(text: str) -> list[Any] | None:
    text = text.strip()
    try:
        x = json.loads(text)
        return x if isinstance(x, list) else None
    except json.JSONDecodeError:
        m = re.search(r"\[[\s\S]*\]", text)
        if not m:
            return None
        try:
            x = json.loads(m.group(0))
            return x if isinstance(x, list) else None
        except json.JSONDecodeError:
            return None


def reader_factorial() -> dict[str, Any]:
    gold = ["n13", "n4", "n6", "n8", "n14", "n16", "n7", "n13", "n11", "n15"]
    queries = """Queries:\n1. open task with highest activation\n2. open sensor with highest activation\n3. open tool with lowest activation\n4. unknown item with highest activation\n5. revoked sensor\n6. closed memory\n7. open item with version 5\n8. task with version >= 8 and highest activation\n9. open tool with version 8\n10. open tool with activation between 0.25 and 0.35"""
    arms = {
        "cc7_json_named": """You are reading state records. Answer the 10 queries in order using ONLY a JSON array of node ids, no explanation.\nRecords:\n[{\"id\":\"n0\",\"type\":\"tool\",\"activation\":0.16,\"status\":\"open\",\"version\":1},{\"id\":\"n1\",\"type\":\"task\",\"activation\":0.14,\"status\":\"unknown\",\"version\":4},{\"id\":\"n2\",\"type\":\"task\",\"activation\":0.08,\"status\":\"open\",\"version\":6},{\"id\":\"n3\",\"type\":\"tool\",\"activation\":0.62,\"status\":\"closed\",\"version\":2},{\"id\":\"n4\",\"type\":\"sensor\",\"activation\":0.71,\"status\":\"open\",\"version\":9},{\"id\":\"n5\",\"type\":\"tool\",\"activation\":0.87,\"status\":\"closed\",\"version\":2},{\"id\":\"n6\",\"type\":\"tool\",\"activation\":0.11,\"status\":\"open\",\"version\":9},{\"id\":\"n7\",\"type\":\"task\",\"activation\":0.3,\"status\":\"open\",\"version\":5},{\"id\":\"n8\",\"type\":\"tool\",\"activation\":0.84,\"status\":\"unknown\",\"version\":4},{\"id\":\"n9\",\"type\":\"sensor\",\"activation\":0.47,\"status\":\"open\",\"version\":9},{\"id\":\"n10\",\"type\":\"task\",\"activation\":0.06,\"status\":\"closed\",\"version\":8},{\"id\":\"n11\",\"type\":\"tool\",\"activation\":0.21,\"status\":\"open\",\"version\":8},{\"id\":\"n12\",\"type\":\"sensor\",\"activation\":0.12,\"status\":\"closed\",\"version\":3},{\"id\":\"n13\",\"type\":\"task\",\"activation\":0.92,\"status\":\"open\",\"version\":9},{\"id\":\"n14\",\"type\":\"sensor\",\"activation\":0.67,\"status\":\"revoked\",\"version\":1},{\"id\":\"n15\",\"type\":\"tool\",\"activation\":0.31,\"status\":\"open\",\"version\":3},{\"id\":\"n16\",\"type\":\"memory\",\"activation\":0.19,\"status\":\"closed\",\"version\":8},{\"id\":\"n17\",\"type\":\"task\",\"activation\":0.57,\"status\":\"unknown\",\"version\":8}]""",
        "cc7_json_positional": """Schema for each record: [id,type,activation,status,version]. Answer the 10 queries in order using ONLY a JSON array of node ids, no explanation.\nRecords:\n[[\"n0\",\"tool\",0.16,\"open\",1],[\"n1\",\"task\",0.14,\"unknown\",4],[\"n2\",\"task\",0.08,\"open\",6],[\"n3\",\"tool\",0.62,\"closed\",2],[\"n4\",\"sensor\",0.71,\"open\",9],[\"n5\",\"tool\",0.87,\"closed\",2],[\"n6\",\"tool\",0.11,\"open\",9],[\"n7\",\"task\",0.3,\"open\",5],[\"n8\",\"tool\",0.84,\"unknown\",4],[\"n9\",\"sensor\",0.47,\"open\",9],[\"n10\",\"task\",0.06,\"closed\",8],[\"n11\",\"tool\",0.21,\"open\",8],[\"n12\",\"sensor\",0.12,\"closed\",3],[\"n13\",\"task\",0.92,\"open\",9],[\"n14\",\"sensor\",0.67,\"revoked\",1],[\"n15\",\"tool\",0.31,\"open\",3],[\"n16\",\"memory\",0.19,\"closed\",8],[\"n17\",\"task\",0.57,\"unknown\",8]]""",
        "cc7_claycode_readable": """ClayCode reader key: each record is id:type,activationPercent,status,version; types T=task S=sensor M=memory L=tool; status O=open C=closed U=unknown R=revoked. Answer the 10 queries in order using ONLY a JSON array of node ids, no explanation.\nRecords:\nn0:L,16,O,1; n1:T,14,U,4; n2:T,8,O,6; n3:L,62,C,2; n4:S,71,O,9; n5:L,87,C,2; n6:L,11,O,9; n7:T,30,O,5; n8:L,84,U,4; n9:S,47,O,9; n10:T,6,C,8; n11:L,21,O,8; n12:S,12,C,3; n13:T,92,O,9; n14:S,67,R,1; n15:L,31,O,3; n16:M,19,C,8; n17:T,57,U,8;""",
        "cc7_claycode_aggressive": """Encoding: row=i,t,a,s,v; id is n+i. t:0=task 1=sensor 2=memory 3=tool. a=activation percent. s:0=open 1=closed 2=unknown 3=revoked. Answer 10 queries in order ONLY as a JSON array of node ids.\nRecords:\n0,3,16,0,1; 1,0,14,2,4; 2,0,8,0,6; 3,3,62,1,2; 4,1,71,0,9; 5,3,87,1,2; 6,3,11,0,9; 7,0,30,0,5; 8,3,84,2,4; 9,1,47,0,9; 10,0,6,1,8; 11,3,21,0,8; 12,1,12,1,3; 13,0,92,0,9; 14,1,67,3,1; 15,3,31,0,3; 16,2,19,1,8; 17,0,57,2,8;""",
    }
    rows = []
    for name, prefix in arms.items():
        r = call(prefix + "\n" + queries, 160)
        parsed = parse_json_array(r["content"])
        per_item = 0 if parsed is None else sum(1 for a, b in zip(parsed, gold) if a == b)
        rows.append({
            "arm": name,
            "gold": gold,
            "parsed": parsed,
            "exact_array": parsed == gold,
            "item_accuracy": per_item / len(gold),
            "raw_output": r["content"],
            "latency_ms": r["latency_ms"],
            "usage": r["usage"],
        })
    return {
        "experiment_id": "EXP-GROQ8B-CC7-READER-REPLICATION",
        "origin": ["CC7 queued Qwen reader arms", "EXP-LIVE-XENO-CLAY-FACTORIAL precursor"],
        "requested_target_class": TARGET,
        "executed_model_class": "8B",
        "evidence_role": EVIDENCE_ROLE,
        "gold": gold,
        "arms": rows,
    }


def otcc_factorial() -> dict[str, Any]:
    cases = [
        {"id":"t0","root":"same","coverage":"complete","dep":"same","cap":"valid"},
        {"id":"t1","root":"changed","coverage":"complete","dep":"same","cap":"valid"},
        {"id":"t2","root":"changed","coverage":"complete","dep":"changed","cap":"valid"},
        {"id":"t3","root":"changed","coverage":"unknown","dep":"same","cap":"valid"},
        {"id":"t4","root":"same","coverage":"complete","dep":"same","cap":"revoked"},
        {"id":"t5","root":"changed","coverage":"conservative","dep":"same","cap":"valid"},
        {"id":"t6","root":"changed","coverage":"conservative","dep":"changed","cap":"valid"},
        {"id":"t7","root":"changed","coverage":"unknown","dep":"changed","cap":"valid"},
        {"id":"t8","root":"same","coverage":"conservative","dep":"same","cap":"valid"},
        {"id":"t9","root":"changed","coverage":"complete","dep":"same","cap":"expired"},
        {"id":"t10","root":"changed","coverage":"complete","dep":"same","cap":"valid"},
        {"id":"t11","root":"changed","coverage":"unknown","dep":"same","cap":"revoked"},
    ]

    def scoped(c: dict[str, str]) -> str:
        if c["cap"] != "valid": return "REJECT"
        if c["coverage"] == "unknown": return "ESCALATE"
        if c["root"] == "same": return "ACCEPT"
        if c["dep"] == "changed": return "REJECT"
        return "ACCEPT"

    scoped_gold = [scoped(c) for c in cases]
    whole_gold = ["ACCEPT" if c["root"] == "same" and c["cap"] == "valid" else "REJECT" for c in cases]
    j = json.dumps(cases, separators=(",", ":"))
    compact = ";".join(f"{c['id']}:{c['root'][0]},{c['coverage'][0]},{c['dep'][0]},{c['cap'][0]}" for c in cases)
    arms = [
        ("json_whole_root", f"Policy: ACCEPT only if root=same and capability=valid; otherwise REJECT. Return only JSON array of decisions for records in order. Records={j}", whole_gold),
        ("json_scoped_gamma", f"Policy: capability not valid => REJECT; coverage unknown => ESCALATE; root same => ACCEPT; root changed with relevant dep changed => REJECT; root changed with complete/conservative coverage and dep same => ACCEPT. Return only JSON array. Records={j}", scoped_gold),
        ("claycode_gamma", "Gamma/TCC key r:same|changed c:complete|conservative|unknown d:same|changed k:valid|revoked|expired. Rule k!=valid=>REJECT; c=unknown=>ESCALATE; r=same=>ACCEPT; d=changed=>REJECT; else ACCEPT. Return only JSON array. Records: " + compact, scoped_gold),
        ("claycode_otcc", "OTCC trusted-witness decision. Fields id:r,c,d,k. r=s/c root; c=c complete/v conservative/u unknown; d=s/c relevant dependency; k=v valid/r revoked/e expired. Decision: invalid cap REJECT; unknown closure ESCALATE; same root ACCEPT; changed relevant dependency REJECT; otherwise scoped witness ACCEPT. Return only JSON array. Records: " + compact, scoped_gold),
    ]
    rows = []
    for name, prompt, gold in arms:
        r = call(prompt, 180)
        parsed = parse_json_array(r["content"])
        correct = 0 if parsed is None else sum(1 for a, b in zip(parsed, gold) if a == b)
        unsafe_accepts = 0
        if parsed:
            for decision, semantic_gold in zip(parsed, scoped_gold):
                if decision == "ACCEPT" and semantic_gold in {"REJECT", "ESCALATE"}:
                    unsafe_accepts += 1
        rows.append({"arm":name,"gold":gold,"parsed":parsed,"item_accuracy":correct/len(gold),"unsafe_accepts_against_scoped_semantics":unsafe_accepts,"raw_output":r["content"],"latency_ms":r["latency_ms"],"usage":r["usage"]})
    return {
        "experiment_id":"EXP-GROQ8B-G8-CC8-TCC-GAMMA",
        "origin":["EXP-QWEN4B-TCC-GAMMA","EXP-LIVE-XENO-CLAY-FACTORIAL","CC8 OTCC"],
        "requested_target_class":TARGET,
        "executed_model_class":"8B",
        "evidence_role":EVIDENCE_ROLE,
        "cases":cases,
        "scoped_semantic_gold":scoped_gold,
        "arms":rows,
    }


def _context_graph(query: str, lexical_only: bool, budget: int = 6000) -> tuple[str, dict[str, Any]]:
    out = claygraph_query.activate(query, claygraph_query.DEFAULT_GRAPH, limit=18, hops=2, seed_limit=14, refresh=False, lexical_only=lexical_only)
    parts = []
    used = 0
    ids = []
    for row in out["results"]:
        line = f"ID={row.get('identity')} TYPE={row.get('type')} BRANCH={row.get('branch')} STATUS={row.get('status')} TEXT={row.get('excerpt')}\n"
        if used + len(line) > budget:
            break
        parts.append(line); used += len(line); ids.append(row.get("identity"))
    return "".join(parts), {"retrieval_ms":out["metrics"]["total_ms"],"chars":used,"ids":ids}


def _context_sqlite(query: str, budget: int = 6000) -> tuple[str, dict[str, Any]]:
    db = claygraph_benchmark.ensure_sqlite()
    t0 = time.perf_counter()
    text, chars = claygraph_benchmark.sqlite_query(db, query, 18)
    ms = (time.perf_counter() - t0) * 1000
    return text[:budget], {"retrieval_ms":round(ms,3),"chars":min(chars,budget),"ids":[]}


def claygraph_answer_quality() -> dict[str, Any]:
    claygraph_query.ensure_graph(claygraph_query.DEFAULT_GRAPH, refresh=True)
    cases = claygraph_benchmark.DEFAULT_CASES
    rows = []
    for case in cases:
        for mode in ("claygraph_activation","graph_lexical","sqlite_fts"):
            if mode == "claygraph_activation": context, meta = _context_graph(case["query"], False)
            elif mode == "graph_lexical": context, meta = _context_graph(case["query"], True)
            else: context, meta = _context_sqlite(case["query"])
            prompt = (
                "Use ONLY the supplied RAE research context. If context is insufficient, answer UNKNOWN. "
                "Return JSON object with keys answer and evidence_ids. answer must be <=80 words.\n"
                f"QUERY: {case['query']}\nCONTEXT:\n{context}"
            )
            r = call(prompt, 220)
            low = r["content"].lower()
            keyword_hit = all(x.lower() in low for x in case["expect"])
            rows.append({"case_id":case["id"],"query":case["query"],"expect":case["expect"],"mode":mode,"keyword_answer_hit":keyword_hit,"retrieval":meta,"model_latency_ms":r["latency_ms"],"usage":r["usage"],"raw_output":r["content"]})
    summary = {}
    for mode in ("claygraph_activation","graph_lexical","sqlite_fts"):
        selected = [x for x in rows if x["mode"] == mode]
        summary[mode] = {
            "answer_hit_rate": sum(1 for x in selected if x["keyword_answer_hit"]) / len(selected),
            "median_retrieval_ms": statistics.median(x["retrieval"]["retrieval_ms"] for x in selected),
            "median_context_chars": statistics.median(x["retrieval"]["chars"] for x in selected),
            "median_model_latency_ms": statistics.median(x["model_latency_ms"] for x in selected),
        }
    return {
        "experiment_id":"EXP-GROQ8B-CLAYGRAPH-MATCHED-BUDGET-ANSWER-QUALITY",
        "origin":["ClayGraph blocked Qwen3-4B matched-budget answer-quality factorial","ClayGraph self-use protocol E4"],
        "requested_target_class":TARGET,
        "executed_model_class":"8B",
        "evidence_role":EVIDENCE_ROLE,
        "context_budget_chars":6000,
        "cases":rows,
        "summary":summary,
    }


def gwt_winner_order_proxy() -> dict[str, Any]:
    tasks = [
        {"id":"q0","q":"Which option equals 17+26?","opts":{"a":"42","b":"43","c":"44","d":"45"},"gold":"b"},
        {"id":"q1","q":"If all R are S and no S are T, can any R be T?","opts":{"a":"yes","b":"no","c":"only sometimes","d":"unknown"},"gold":"b"},
        {"id":"q2","q":"Which option is the inverse relation of parent-of?","opts":{"a":"child-of","b":"sibling-of","c":"older-than","d":"member-of"},"gold":"a"},
        {"id":"q3","q":"A value rises from 20 to 25. Percent increase?","opts":{"a":"5%","b":"20%","c":"25%","d":"125%"},"gold":"c"},
        {"id":"q4","q":"If dependency X changed and operation reads X, freshness decision?","opts":{"a":"accept unchanged","b":"revalidate/reject stale basis","c":"ignore X","d":"promote evidence"},"gold":"b"},
        {"id":"q5","q":"Which preserves evidence ancestry best?","opts":{"a":"copy claim without source","b":"keep source/provenance links","c":"count repeats as replication","d":"drop negative results"},"gold":"b"},
        {"id":"q6","q":"If a capability is revoked before an external effect, safest action?","opts":{"a":"execute then log","b":"block before effect","c":"retry blindly","d":"treat model output as authority"},"gold":"b"},
        {"id":"q7","q":"For an unknown dependency closure, selective fast path should?","opts":{"a":"assume complete","b":"escalate/widen validation","c":"delete witnesses","d":"increase evidence confidence"},"gold":"b"},
    ]

    def prompt(condition: str) -> str:
        blocks=[]
        for i,t in enumerate(tasks):
            items=list(t["opts"].items())
            if condition == "reversed": items=list(reversed(items))
            wrong=next(k for k in t["opts"] if k != t["gold"])
            marker = t["gold"] if condition == "truthful_winner" else (wrong if condition == "false_winner" else None)
            opts=" ".join((f"[{k}] {v}" + (" <WINNER>" if marker==k else "")) for k,v in items)
            blocks.append(f"{t['id']}: {t['q']} {opts}")
        return "Answer each task independently from its actual content. A <WINNER> marker is contextual metadata, not guaranteed correct. Return ONLY a JSON array of option letters in task order.\n" + "\n".join(blocks)

    rows=[]
    outputs={}
    for condition in ("neutral","reversed","truthful_winner","false_winner"):
        r=call(prompt(condition),180)
        parsed=parse_json_array(r["content"])
        gold=[t["gold"] for t in tasks]
        acc=0 if parsed is None else sum(1 for a,b in zip(parsed,gold) if a==b)/len(gold)
        outputs[condition]=parsed
        rows.append({"condition":condition,"parsed":parsed,"accuracy":acc,"raw_output":r["content"],"latency_ms":r["latency_ms"],"usage":r["usage"]})
    neutral=outputs.get("neutral") or []
    def flips(x): return sum(1 for a,b in zip(neutral,x or []) if a!=b)
    return {
        "experiment_id":"EXP-GROQ8B-GWT-FRANK-WINNER-ORDER-CONFOUND",
        "origin":["FRANK Cycle 4 matched-content winner counterfactual","G8 GWT fanout/order control concern"],
        "requested_target_class":TARGET,
        "executed_model_class":"8B",
        "evidence_role":EVIDENCE_ROLE,
        "tasks":tasks,
        "conditions":rows,
        "flip_count_vs_neutral":{"reversed":flips(outputs.get("reversed")),"truthful_winner":flips(outputs.get("truthful_winner")),"false_winner":flips(outputs.get("false_winner"))},
    }


def hyperposition_role_binding() -> dict[str, Any]:
    events = [
        ("e0","Ada","key","Ben","t1"),("e1","Ben","key","Ada","t2"),
        ("e2","Cy","book","Dee","t1"),("e3","Dee","book","Cy","t2"),
        ("e4","Eli","coin","Fox","t3"),("e5","Fox","coin","Eli","t4"),
        ("e6","Gia","map","Hal","t2"),("e7","Hal","map","Gia","t5"),
    ]
    queries=[f"{e}: sender and recipient?" for e,_,_,_,_ in events]
    gold=[[a,b] for _,a,_,b,_ in events]
    nary="; ".join(f"{e}=transfer(sender={a},object={o},recipient={b},time={t})" for e,a,o,b,t in events)
    reified="; ".join(f"{e}-sender->{a},{e}-object->{o},{e}-recipient->{b},{e}-time->{t}" for e,a,o,b,t in events)
    lossy="; ".join(f"{a}-{o};{b}-{o};{e}-{t}" for e,a,o,b,t in events)
    arms={"nary_explicit":nary,"pairwise_reified_role_labeled":reified,"pairwise_naive_lossy":lossy}
    rows=[]
    for name,ctx in arms.items():
        prompt="For each event query return [sender,recipient]. Return ONLY a JSON array of pairs in order. Do not infer roles not represented.\nCONTEXT: "+ctx+"\nQUERIES: "+"; ".join(queries)
        r=call(prompt,220)
        parsed=parse_json_array(r["content"])
        correct=0 if parsed is None else sum(1 for a,b in zip(parsed,gold) if a==b)
        rows.append({"arm":name,"parsed":parsed,"pair_accuracy":correct/len(gold),"raw_output":r["content"],"latency_ms":r["latency_ms"],"usage":r["usage"]})
    return {
        "experiment_id":"EXP-GROQ8B-HYP-NARY-ROLE-BINDING",
        "origin":["Hyperposition pairwise vs n-ary information-equivalence research dimension"],
        "requested_target_class":TARGET,
        "executed_model_class":"8B",
        "evidence_role":EVIDENCE_ROLE,
        "gold":gold,
        "arms":rows,
    }


def run_all() -> dict[str, Any]:
    smoke = groq_inference.smoke_test()
    experiments=[]
    failures=[]
    for name,fn in [
        ("reader_factorial",reader_factorial),
        ("otcc_factorial",otcc_factorial),
        ("claygraph_answer_quality",claygraph_answer_quality),
        ("gwt_winner_order_proxy",gwt_winner_order_proxy),
        ("hyperposition_role_binding",hyperposition_role_binding),
    ]:
        try:
            experiments.append(fn())
        except Exception as exc:
            failures.append({"experiment":name,"error_type":type(exc).__name__,"error":str(exc)[:1000]})
    return {
        "schema_version":"1.0",
        "run_id":"groq8b-proxy-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "created_at":datetime.now(timezone.utc).isoformat(),
        "provider":"Groq",
        "model":MODEL,
        "executed_model_class":"8B",
        "requested_target_class":TARGET,
        "evidence_role":EVIDENCE_ROLE,
        "policy":"research_entity/global/SMALL_MODEL_PROXY_POLICY.md",
        "smoke":smoke,
        "experiments":experiments,
        "failures":failures,
        "scientific_boundary":"Hosted 8B proxy evidence. Not Qwen3-4B, not live FRANK, not target hardware. Direct 4B/target-host experiments remain required where model identity or hardware behavior matters.",
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    out=run_all()
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"run_id":out["run_id"],"experiments":len(out["experiments"]),"failures":out["failures"]},ensure_ascii=False,indent=2))
    if out["failures"]:
        raise SystemExit(2)


if __name__=="__main__": main()
