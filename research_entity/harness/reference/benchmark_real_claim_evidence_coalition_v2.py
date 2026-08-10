from __future__ import annotations

"""V2 real-ledger experiment: compile an Evidence Coalition, not a global row ranking.

V1.1 showed that topic/domain topology can recover complete relevant claim sets, but a frozen
paraphrase stress exposed the deeper abstraction error: multi-facet questions such as
"CURRENT + REFUTED" or "SUPERSEDED + OPEN" should not force all evidence claims to compete
for one undifferentiated rank. V2 therefore detects EXPLICIT epistemic/status facets in the
query and reserves one coalition slot per requested facet. Topic/domain topology still ranks
claims WITHIN each slot; the residual item budget is filled from the ordinary topology rank.

The same deterministic coalition policy is applied to:
- indexed SQLite topic/domain joins, and
- disposable precompiled topic/domain maps.
Exact output equality remains mandatory, so model-facing semantics are not attributed to a
particular storage engine.

The new-topic holdout below was frozen before first V2 execution and uses claims not present in
the original eight-query development set. It is still model-authored and therefore not an
independent external evaluation.
"""

import argparse
import io
import json
import os
import platform
import random
import sqlite3
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

from . import benchmark_real_claim_topology_preprocessor_v1 as base
from .benchmark_real_claim_topology_preprocessor_v1_1 import (
    topology_scores_compiled,
    topology_scores_sqlite_matched,
)

K = 3

PARAPHRASE_STRESS = [
    {"id":"p1a","query":"Which evidence replaced the idea of one transferable coupling constant, and what remains current?","expected":["C-CURRENT-002","C-REFUTED-002"]},
    {"id":"p1b","query":"Which current coupling conclusion rejects a universal constant, and which old fixed value hypothesis failed?","expected":["C-CURRENT-002","C-REFUTED-002"]},
    {"id":"p2a","query":"Find the surviving hyperposition representation conclusion and the rejected claim that a single storage shape is required.","expected":["C-CURRENT-001","C-REFUTED-003"]},
    {"id":"p2b","query":"Which claim says multiple physical realizations can reconstruct hyperposition, and which necessity claim for one graph shape failed?","expected":["C-CURRENT-001","C-REFUTED-003"]},
    {"id":"p3a","query":"Which validated GWT result requires causal receipts, and what stage-label shortcut failed?","expected":["C-CURRENT-003","C-REFUTED-004"]},
    {"id":"p3b","query":"Which current GWT claim requires identity order receipts, and which stage-presence claim is false?","expected":["C-CURRENT-003","C-REFUTED-004"]},
    {"id":"p4a","query":"Can model output authorize commits by itself?","expected":["C-CURRENT-004"]},
    {"id":"p4b","query":"Does generated commit syntax itself confer execution authority?","expected":["C-CURRENT-004"]},
    {"id":"p5a","query":"What unresolved live Frank question concerns causal reentry changing later behavior?","expected":["C-OPEN-001"]},
    {"id":"p5b","query":"Is there still an open causal question whether GWT re-entry changes subsequent Frank state?","expected":["C-OPEN-001"]},
    {"id":"p6a","query":"What unresolved backend question remains for hyperposition concurrency recovery cost?","expected":["C-OPEN-003"]},
    {"id":"p6b","query":"Which hyperposition implementation backend remains an open choice under concurrency and recovery?","expected":["C-OPEN-003"]},
    {"id":"p7a","query":"What is the project-wide scope and what portability runtime question is still unresolved?","expected":["C-CURRENT-005","C-OPEN-005"]},
    {"id":"p7b","query":"Which claim says the research entity spans complete architecture, and which portability claim across operating systems is open?","expected":["C-CURRENT-005","C-OPEN-005"]},
    {"id":"p8a","query":"What earlier XENO goal was retired, and what fair end-to-end cost question remains unresolved?","expected":["C-SUPERSEDED-003","C-OPEN-002"]},
    {"id":"p8b","query":"Which XENO compression-centric objective is superseded, and which economic communication-cost claim remains open?","expected":["C-SUPERSEDED-003","C-OPEN-002"]},
]

NEW_TOPIC_HOLDOUT = [
    {"id":"h1","query":"Which formal assurance claim about CC-RC1.1 invariants remains open?","expected":["C-OPEN-004"]},
    {"id":"h2","query":"Which claim blaming the trimmer for zero reentry closure was refuted?","expected":["C-REFUTED-001"]},
    {"id":"h3","query":"Which Synthetic Clay claim that it should be one monolithic graph database was superseded?","expected":["C-SUPERSEDED-002"]},
    {"id":"h4","query":"Which earlier XENO lineage promotion result is superseded?","expected":["C-SUPERSEDED-001"]},
    {"id":"h5","query":"Which monolithic Synthetic Clay graph-database claim was superseded and which formal verification claim remains open?","expected":["C-SUPERSEDED-002","C-OPEN-004"]},
    {"id":"h6","query":"Which Frank trimmer reentry explanation was refuted and which live GWT reentry claim remains open?","expected":["C-REFUTED-001","C-OPEN-001"]},
    {"id":"h7","query":"Which old XENO lineage promotion result is superseded and which success-adjusted communication-cost claim is still open?","expected":["C-SUPERSEDED-001","C-OPEN-002"]},
]

# Only explicit lexical markers are allowed to create a facet slot. These markers change
# assembly/rank only; repository status remains the authoritative status.
FACET_MARKERS = {
    "CURRENT": ("current", "currently", "surviving"),
    "OPEN": ("open", "unresolved"),
    "REFUTED": ("refuted", "rejected", "failed", "false"),
    "SUPERSEDED": ("superseded", "retired"),
}


def requested_facets(query: str) -> tuple[str, ...]:
    q = set(base.tokens(query))
    found = []
    for status, markers in FACET_MARKERS.items():
        if any(marker in q for marker in markers):
            found.append(status)
    return tuple(found)


def coalition_rank(scores: dict[str, float], rows_by_id: dict[str, dict[str, Any]], query: str, k: int = K) -> list[str]:
    global_rank = base.ranked(scores, max(k, len(scores)))
    selected: list[str] = []
    for facet in requested_facets(query):
        for cid in global_rank:
            if cid in selected:
                continue
            if str(rows_by_id[cid].get("current_status", "")).upper() == facet:
                selected.append(cid)
                break
    for cid in global_rank:
        if len(selected) >= k:
            break
        if cid not in selected:
            selected.append(cid)
    return selected[:k]


def metrics_for_set(cases: list[dict[str, Any]], methods: dict[str, Callable[[str], list[str]]]):
    per_query = []
    agg: dict[str, list[dict[str, float]]] = {name: [] for name in methods}
    for case in cases:
        row = {"id":case["id"],"query":case["query"],"expected":case["expected"],"methods":{}}
        for name, fn in methods.items():
            got = fn(case["query"])
            metric = base.retrieval_metrics(got, case["expected"], K)
            agg[name].append(metric)
            row["methods"][name] = {"got":got,"metrics":metric}
        per_query.append(row)
    return {
        "summary": {name: base.aggregate(values) for name, values in agg.items()},
        "per_query": per_query,
    }


def percentile(xs, p):
    ys=sorted(xs); pos=(len(ys)-1)*p; lo=int(pos); hi=min(len(ys)-1,lo+1)
    return ys[lo] if lo==hi else ys[lo]*(hi-pos)+ys[hi]*(pos-lo)


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--iterations",type=int,default=2000)
    ap.add_argument("--output")
    args=ap.parse_args()

    rows=base.current_rows(); rows_by_id={r["claim_id"]:r for r in rows}
    doc_tokens,postings,idf=base.compiled_lexical_index(rows)
    topology=base.compile_topology(rows); con=base.make_sqlite(rows)
    def lexical(q): return base.lexical_scores(q,rows_by_id,postings,doc_tokens,idf)
    def compiled_topology(q): return base.ranked(topology_scores_compiled(q,lexical(q),rows_by_id,topology),K)
    def sqlite_topology(q): return base.ranked(topology_scores_sqlite_matched(con,q,lexical(q),rows_by_id),K)
    def compiled_coalition(q): return coalition_rank(topology_scores_compiled(q,lexical(q),rows_by_id,topology),rows_by_id,q,K)
    def sqlite_coalition(q): return coalition_rank(topology_scores_sqlite_matched(con,q,lexical(q),rows_by_id),rows_by_id,q,K)
    methods={
        "sqlite_fts_flat":lambda q:base.sqlite_fts_flat(con,q,K),
        "compiled_topology_v1_1":compiled_topology,
        "sqlite_coalition_matched_v2":sqlite_coalition,
        "compiled_coalition_v2":compiled_coalition,
    }
    sets={
        "development_8":base.FROZEN_QUERIES,
        "paraphrase_stress_16_seen_after_v1_1":PARAPHRASE_STRESS,
        "new_topic_holdout_7_frozen_before_v2_execution":NEW_TOPIC_HOLDOUT,
    }
    result_sets={name:metrics_for_set(cases,methods) for name,cases in sets.items()}

    semantic_equivalent=True
    for set_result in result_sets.values():
        for row in set_result["per_query"]:
            if row["methods"]["sqlite_coalition_matched_v2"]["got"] != row["methods"]["compiled_coalition_v2"]["got"]:
                semantic_equivalent=False

    iterations=max(100,min(args.iterations,100000))
    timing_cases=base.FROZEN_QUERIES+PARAPHRASE_STRESS+NEW_TOPIC_HOLDOUT
    rng=random.Random(211)
    schedule=[timing_cases[rng.randrange(len(timing_cases))]["query"] for _ in range(iterations)]
    for _ in range(5):
        for case in timing_cases:
            for fn in methods.values(): fn(case["query"])
    latency={name:[] for name in methods}
    for q in schedule:
        for name,fn in methods.items():
            t0=time.perf_counter_ns(); fn(q); latency[name].append((time.perf_counter_ns()-t0)/1000.0)
    lat_summary={name:{"n":len(xs),"p50_us":percentile(xs,.5),"p95_us":percentile(xs,.95),"p99_us":percentile(xs,.99),"mean_us":statistics.mean(xs),"min_us":min(xs),"max_us":max(xs)} for name,xs in latency.items()}

    hold=result_sets["new_topic_holdout_7_frozen_before_v2_execution"]["summary"]
    stress=result_sets["paraphrase_stress_16_seen_after_v1_1"]["summary"]
    gate={
        "sqlite_compiled_coalition_ordered_top3_equivalent_all_queries":semantic_equivalent,
        "holdout_recall_delta_v2_vs_flat_fts":hold["compiled_coalition_v2"]["recall_at_k"]-hold["sqlite_fts_flat"]["recall_at_k"],
        "holdout_ndcg_delta_v2_vs_flat_fts":hold["compiled_coalition_v2"]["ndcg_at_k"]-hold["sqlite_fts_flat"]["ndcg_at_k"],
        "holdout_ndcg_delta_v2_vs_v1_1_topology":hold["compiled_coalition_v2"]["ndcg_at_k"]-hold["compiled_topology_v1_1"]["ndcg_at_k"],
        "stress_ndcg_delta_v2_vs_v1_1_topology":stress["compiled_coalition_v2"]["ndcg_at_k"]-stress["compiled_topology_v1_1"]["ndcg_at_k"],
        "compiled_coalition_p50_ratio_vs_sqlite_matched":lat_summary["compiled_coalition_v2"]["p50_us"]/lat_summary["sqlite_coalition_matched_v2"]["p50_us"],
    }
    gate["advance_to_larger_real_corpus"]=(
        semantic_equivalent
        and gate["holdout_recall_delta_v2_vs_flat_fts"]>=0
        and gate["holdout_ndcg_delta_v2_vs_flat_fts"]>=0
        and gate["stress_ndcg_delta_v2_vs_v1_1_topology"]>0
        and gate["compiled_coalition_p50_ratio_vs_sqlite_matched"]<1.0
    )
    output={
        "schema_version":"2.0",
        "benchmark":"REAL_CLAY_CLAIM_EVIDENCE_COALITION_V2",
        "evidence_class":"REAL_REPOSITORY_LEDGER_CORRELATED_PLUS_NEW_TOPIC_HOLDOUT",
        "corpus_claims":len(rows),
        "k":K,
        "facet_markers":FACET_MARKERS,
        "sets":result_sets,
        "latency":lat_summary,
        "semantic_equivalence":{
            "all_queries":semantic_equivalent,
            "rule":"SQLite and compiled routes use the same lexical scores, V1.1 topology semantics, and V2 coalition-slot policy; only neighbor execution differs (indexed joins vs precompiled maps).",
        },
        "candidate_gate":gate,
        "execution_metadata":{
            "git_sha":os.environ.get("GITHUB_SHA","UNKNOWN_LOCAL"),
            "python":sys.version,
            "sqlite":sqlite3.sqlite_version,
            "platform":platform.platform(),
            "iterations":iterations,
            "timing_seed":211,
        },
        "scope_guard":"17 real Clay claims. Development/paraphrase sets are correlated; only the seven new-topic questions were frozen before first V2 execution, and they remain model-authored rather than independent.",
        "next_falsifiers":[
            "Independent worker authors a query set without seeing V2 outputs/scoring.",
            "Larger real claims/evidence corpus with explicit required evidence facets.",
            "Native PostgreSQL/pgvector and graph-engine competitors under matched semantics.",
            "Downstream model answer/candidate selection under equal context-token budget.",
        ],
    }
    text=json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if args.output:
        p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")
    print(text,end=""); con.close()

if __name__=="__main__": main()
