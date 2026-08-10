from __future__ import annotations

"""Real Clay ledger benchmark: flat retrieval vs compiled semantic-topology preprocessing.

This benchmark uses the repository's actual CLAIMS/CLAIM_STATUS ledgers, not a generated
claim corpus. Eight frozen natural-language queries are model-authored from the ledger and
therefore correlated research evidence, not independent held-out validation.

It deliberately separates three questions:
1. Does explicit Clay topic/domain/status topology improve evidence-set completeness over a
   native flat SQLite FTS5 path?
2. If SQLite is given the SAME topology and the SAME deterministic lexical seed scores, can
   it reproduce the exact compiled-topology output? (It should; semantics are not a storage
   engine monopoly.)
3. Under identical semantics and warm process state, is precompiled topology lookup cheaper
   than executing equivalent indexed SQLite joins?

UnifiedDB/ledger remains authoritative. The compiled maps are derived, disposable model-input
preprocessing state. This benchmark cannot support universal database superiority.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import random
import re
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
CLAIMS_PATH = ROOT / "research_entity" / "ledgers" / "CLAIMS.jsonl"
STATUS_PATH = ROOT / "research_entity" / "ledgers" / "CLAIM_STATUS_EVENTS.jsonl"
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)
K = 3

FROZEN_QUERIES = [
    {
        "id": "adaptive-coupling-current-refuted",
        "query": "What is the current conclusion about coupling strength and which fixed-kappa claim was refuted?",
        "expected": ["C-CURRENT-002", "C-REFUTED-002"],
    },
    {
        "id": "hyperposition-current-refuted",
        "query": "What is currently known about hyperposition representation and which one-shape storage claim was refuted?",
        "expected": ["C-CURRENT-001", "C-REFUTED-003"],
    },
    {
        "id": "gwt-validator-current-refuted",
        "query": "What is the current GWT validator result and which presence-only validation claim was refuted?",
        "expected": ["C-CURRENT-003", "C-REFUTED-004"],
    },
    {
        "id": "effect-authority-current",
        "query": "What is the current rule about model emitted commit syntax and effect authority?",
        "expected": ["C-CURRENT-004"],
    },
    {
        "id": "live-gwt-open",
        "query": "Which open claim asks whether causal GWT reentry improves future live Frank behavior?",
        "expected": ["C-OPEN-001"],
    },
    {
        "id": "hyperposition-backend-open",
        "query": "Which open claim asks which physical backend is best for hyperposition under real Frank concurrency and recovery?",
        "expected": ["C-OPEN-003"],
    },
    {
        "id": "scope-current-portability-open",
        "query": "What is the current project scope and which cross-platform runtime claim remains open?",
        "expected": ["C-CURRENT-005", "C-OPEN-005"],
    },
    {
        "id": "xeno-superseded-open",
        "query": "Which XENO lexical-compression objective was superseded and which communication-cost claim remains open?",
        "expected": ["C-SUPERSEDED-003", "C-OPEN-002"],
    },
]

STATUS_WORDS = {"CURRENT", "OPEN", "REFUTED", "SUPERSEDED", "SUPPORTED", "UNKNOWN"}


def jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def tokens(value: str) -> tuple[str, ...]:
    return tuple(t.lower() for t in TOKEN_RE.findall(value) if len(t) > 1)


def current_rows() -> list[dict[str, Any]]:
    claims = jsonl(CLAIMS_PATH)
    status_events = jsonl(STATUS_PATH)
    latest: dict[str, tuple[str, str]] = {
        c["claim_id"]: (str(c.get("first_status", "OPEN")).upper(), "") for c in claims
    }
    for event in status_events:
        cid = event.get("claim_id")
        ts = str(event.get("timestamp", ""))
        if cid and (cid not in latest or ts >= latest[cid][1]):
            latest[cid] = (str(event.get("to") or "UNKNOWN").upper(), ts)
    rows = []
    for claim in claims:
        row = dict(claim)
        row["current_status"] = latest.get(claim["claim_id"], (str(claim.get("first_status", "OPEN")).upper(), ""))[0]
        rows.append(row)
    return rows


def query_statuses(query: str) -> set[str]:
    q = set(tokens(query))
    return {status for status in STATUS_WORDS if status.lower() in q}


def compiled_lexical_index(rows: list[dict[str, Any]]):
    doc_tokens: dict[str, Counter[str]] = {}
    postings: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cid = row["claim_id"]
        text = " ".join([
            str(row.get("current_status", "")),
            str(row.get("scope", "")),
            str(row.get("proposition", "")),
        ])
        counts = Counter(tokens(text))
        doc_tokens[cid] = counts
        for token in counts:
            postings[token].add(cid)
    n = max(1, len(rows))
    idf = {token: math.log((n + 1.0) / (len(ids) + 1.0)) + 1.0 for token, ids in postings.items()}
    return doc_tokens, postings, idf


def lexical_scores(query: str, rows_by_id: dict[str, dict[str, Any]], postings, doc_tokens, idf) -> dict[str, float]:
    qtokens = tokens(query)
    candidates: set[str] = set()
    for token in qtokens:
        candidates.update(postings.get(token, ()))
    statuses = query_statuses(query)
    scores: dict[str, float] = {}
    for cid in candidates:
        counts = doc_tokens[cid]
        score = 0.0
        for token in qtokens:
            tf = counts.get(token, 0)
            if tf:
                score += idf.get(token, 1.0) * (1.0 + math.log1p(tf))
        status = str(rows_by_id[cid].get("current_status", "")).upper()
        if statuses and status in statuses:
            score += 3.0
        scores[cid] = score
    return scores


def ranked(scores: dict[str, float], limit: int) -> list[str]:
    return [cid for cid, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def compile_topology(rows: list[dict[str, Any]]):
    topics_by_claim: dict[str, frozenset[str]] = {}
    domains_by_claim: dict[str, frozenset[str]] = {}
    claims_by_topic: dict[str, set[str]] = defaultdict(set)
    claims_by_domain: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cid = row["claim_id"]
        topics = frozenset(str(x) for x in row.get("topic_packets", ()))
        domains = frozenset(str(x) for x in row.get("domains", ()))
        topics_by_claim[cid] = topics
        domains_by_claim[cid] = domains
        for topic in topics:
            claims_by_topic[topic].add(cid)
        for domain in domains:
            claims_by_domain[domain].add(cid)
    return topics_by_claim, domains_by_claim, claims_by_topic, claims_by_domain


def topology_scores_compiled(query: str, lexical: dict[str, float], rows_by_id, topology) -> dict[str, float]:
    topics_by_claim, domains_by_claim, claims_by_topic, claims_by_domain = topology
    seeds = ranked(lexical, 2)
    candidates = set(lexical)
    for seed in seeds:
        for topic in topics_by_claim.get(seed, ()):
            candidates.update(claims_by_topic.get(topic, ()))
        for domain in domains_by_claim.get(seed, ()):
            candidates.update(claims_by_domain.get(domain, ()))
    statuses = query_statuses(query)
    scores = {cid: lexical.get(cid, 0.0) for cid in candidates}
    for cid in candidates:
        for seed in seeds:
            if topics_by_claim.get(cid, frozenset()) & topics_by_claim.get(seed, frozenset()):
                scores[cid] += 4.0
            if domains_by_claim.get(cid, frozenset()) & domains_by_claim.get(seed, frozenset()):
                scores[cid] += 0.75
        if statuses and str(rows_by_id[cid].get("current_status", "")).upper() in statuses:
            scores[cid] += 3.0
    return scores


def make_sqlite(rows: list[dict[str, Any]]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE claims(
          claim_id TEXT PRIMARY KEY,
          status TEXT NOT NULL,
          scope TEXT,
          proposition TEXT
        ) WITHOUT ROWID;
        CREATE VIRTUAL TABLE claim_fts USING fts5(claim_id UNINDEXED,status,scope,proposition);
        CREATE TABLE claim_topic(claim_id TEXT NOT NULL, topic TEXT NOT NULL, PRIMARY KEY(claim_id,topic)) WITHOUT ROWID;
        CREATE INDEX idx_claim_topic_topic ON claim_topic(topic,claim_id);
        CREATE TABLE claim_domain(claim_id TEXT NOT NULL, domain TEXT NOT NULL, PRIMARY KEY(claim_id,domain)) WITHOUT ROWID;
        CREATE INDEX idx_claim_domain_domain ON claim_domain(domain,claim_id);
        """
    )
    for row in rows:
        values = (row["claim_id"], row["current_status"], row.get("scope", ""), row.get("proposition", ""))
        con.execute("INSERT INTO claims VALUES(?,?,?,?)", values)
        con.execute("INSERT INTO claim_fts VALUES(?,?,?,?)", values)
        for topic in row.get("topic_packets", ()):
            con.execute("INSERT INTO claim_topic VALUES(?,?)", (row["claim_id"], str(topic)))
        for domain in row.get("domains", ()):
            con.execute("INSERT INTO claim_domain VALUES(?,?)", (row["claim_id"], str(domain)))
    con.commit()
    return con


def fts_expression(query: str) -> str:
    terms = list(dict.fromkeys(tokens(query)))
    return " OR ".join('"' + token.replace('"', '""') + '"' for token in terms)


def sqlite_fts_flat(con: sqlite3.Connection, query: str, k: int) -> list[str]:
    expr = fts_expression(query)
    if not expr:
        return []
    rows = con.execute(
        "SELECT claim_id FROM claim_fts WHERE claim_fts MATCH ? ORDER BY bm25(claim_fts), claim_id LIMIT ?",
        (expr, k),
    ).fetchall()
    return [row[0] for row in rows]


def sql_topology_candidates(con: sqlite3.Connection, seeds: Iterable[str]) -> set[str]:
    seeds = tuple(dict.fromkeys(seeds))
    if not seeds:
        return set()
    placeholders = ",".join("?" for _ in seeds)
    candidates = set(seeds)
    topics = [r[0] for r in con.execute(f"SELECT DISTINCT topic FROM claim_topic WHERE claim_id IN ({placeholders})", seeds)]
    domains = [r[0] for r in con.execute(f"SELECT DISTINCT domain FROM claim_domain WHERE claim_id IN ({placeholders})", seeds)]
    if topics:
        ph = ",".join("?" for _ in topics)
        candidates.update(r[0] for r in con.execute(f"SELECT DISTINCT claim_id FROM claim_topic WHERE topic IN ({ph})", topics))
    if domains:
        ph = ",".join("?" for _ in domains)
        candidates.update(r[0] for r in con.execute(f"SELECT DISTINCT claim_id FROM claim_domain WHERE domain IN ({ph})", domains))
    return candidates


def sql_shared_count(con: sqlite3.Connection, cid: str, seed: str, table: str, column: str) -> int:
    return int(con.execute(
        f"SELECT COUNT(*) FROM {table} a JOIN {table} b ON a.{column}=b.{column} WHERE a.claim_id=? AND b.claim_id=?",
        (cid, seed),
    ).fetchone()[0])


def topology_scores_sqlite_matched(con: sqlite3.Connection, query: str, lexical: dict[str, float], rows_by_id) -> dict[str, float]:
    seeds = ranked(lexical, 2)
    candidates = set(lexical) | sql_topology_candidates(con, seeds)
    statuses = query_statuses(query)
    scores = {cid: lexical.get(cid, 0.0) for cid in candidates}
    for cid in candidates:
        for seed in seeds:
            if sql_shared_count(con, cid, seed, "claim_topic", "topic"):
                scores[cid] += 4.0
            if sql_shared_count(con, cid, seed, "claim_domain", "domain"):
                scores[cid] += 0.75
        if statuses and str(rows_by_id[cid].get("current_status", "")).upper() in statuses:
            scores[cid] += 3.0
    return scores


def retrieval_metrics(got: list[str], expected: list[str], k: int) -> dict[str, float]:
    got = list(dict.fromkeys(got))[:k]
    truth = set(expected)
    hits = [1 if cid in truth else 0 for cid in got]
    tp = sum(hits)
    precision = tp / k
    recall = tp / len(truth) if truth else 1.0
    rr = 0.0
    for i, hit in enumerate(hits, 1):
        if hit:
            rr = 1.0 / i
            break
    dcg = sum(hit / math.log2(i + 1) for i, hit in enumerate(hits, 1))
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(k, len(truth)) + 1))
    return {"precision_at_k": precision, "recall_at_k": recall, "mrr": rr, "ndcg_at_k": dcg / ideal if ideal else 1.0}


def aggregate(rows: list[dict[str, float]]) -> dict[str, float]:
    keys = ("precision_at_k", "recall_at_k", "mrr", "ndcg_at_k")
    return {key: statistics.mean(row[key] for row in rows) for key in keys}


def percentile(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    pos = (len(ys) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - pos) + ys[hi] * (pos - lo)


def latency_summary(samples_us: list[float]) -> dict[str, Any]:
    return {
        "n": len(samples_us),
        "min_us": min(samples_us),
        "p50_us": percentile(samples_us, 0.50),
        "p95_us": percentile(samples_us, 0.95),
        "p99_us": percentile(samples_us, 0.99),
        "max_us": max(samples_us),
        "mean_us": statistics.mean(samples_us),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=2000)
    ap.add_argument("--output")
    ap.add_argument("--raw-latency", action="store_true")
    args = ap.parse_args()

    rows = current_rows()
    rows_by_id = {row["claim_id"]: row for row in rows}
    doc_tokens, postings, idf = compiled_lexical_index(rows)
    topology = compile_topology(rows)
    con = make_sqlite(rows)

    def lexical(query: str) -> dict[str, float]:
        return lexical_scores(query, rows_by_id, postings, doc_tokens, idf)

    methods = {
        "sqlite_fts_flat": lambda q: sqlite_fts_flat(con, q, K),
        "compiled_lexical_flat": lambda q: ranked(lexical(q), K),
        "sqlite_topology_matched": lambda q: ranked(topology_scores_sqlite_matched(con, q, lexical(q), rows_by_id), K),
        "compiled_topology": lambda q: ranked(topology_scores_compiled(q, lexical(q), rows_by_id, topology), K),
    }

    per_query: list[dict[str, Any]] = []
    metric_rows: dict[str, list[dict[str, float]]] = {name: [] for name in methods}
    topology_equivalent = True
    for case in FROZEN_QUERIES:
        result = {"id": case["id"], "query": case["query"], "expected": case["expected"], "methods": {}}
        for name, fn in methods.items():
            got = fn(case["query"])
            metrics = retrieval_metrics(got, case["expected"], K)
            metric_rows[name].append(metrics)
            result["methods"][name] = {"got": got, "metrics": metrics}
        if result["methods"]["sqlite_topology_matched"]["got"] != result["methods"]["compiled_topology"]["got"]:
            topology_equivalent = False
        per_query.append(result)

    iterations = max(100, min(args.iterations, 100_000))
    schedule = [FROZEN_QUERIES[random.Random(42).randrange(len(FROZEN_QUERIES))]["query"] for _ in range(iterations)]
    # Warm all routes before measurement.
    for _ in range(5):
        for case in FROZEN_QUERIES:
            for fn in methods.values():
                fn(case["query"])

    latency: dict[str, list[float]] = {name: [] for name in methods}
    for query in schedule:
        for name, fn in methods.items():
            t0 = time.perf_counter_ns()
            fn(query)
            latency[name].append((time.perf_counter_ns() - t0) / 1000.0)

    summary = {
        name: {"quality": aggregate(metric_rows[name]), "latency": latency_summary(latency[name])}
        for name in methods
    }
    corpus_hash = hashlib.sha256(CLAIMS_PATH.read_bytes() + b"\0" + STATUS_PATH.read_bytes()).hexdigest()
    status_counts = Counter(row["current_status"] for row in rows)
    gate = {
        "topology_output_equivalent_all_queries": topology_equivalent,
        "compiled_topology_recall_delta_vs_flat_fts": summary["compiled_topology"]["quality"]["recall_at_k"] - summary["sqlite_fts_flat"]["quality"]["recall_at_k"],
        "compiled_topology_ndcg_delta_vs_flat_fts": summary["compiled_topology"]["quality"]["ndcg_at_k"] - summary["sqlite_fts_flat"]["quality"]["ndcg_at_k"],
        "compiled_topology_p50_ratio_vs_sqlite_matched": summary["compiled_topology"]["latency"]["p50_us"] / summary["sqlite_topology_matched"]["latency"]["p50_us"],
        "compiled_topology_strictly_faster_p50_than_sqlite_matched": summary["compiled_topology"]["latency"]["p50_us"] < summary["sqlite_topology_matched"]["latency"]["p50_us"],
    }
    gate["advance_to_independent_real_query_falsifier"] = bool(
        gate["topology_output_equivalent_all_queries"]
        and gate["compiled_topology_recall_delta_vs_flat_fts"] > 0.0
        and gate["compiled_topology_ndcg_delta_vs_flat_fts"] > 0.0
        and gate["compiled_topology_strictly_faster_p50_than_sqlite_matched"]
    )

    output: dict[str, Any] = {
        "schema_version": "1.0",
        "benchmark": "REAL_CLAY_CLAIM_TOPOLOGY_PREPROCESSOR_V1",
        "evidence_class": "REAL_REPOSITORY_LEDGER_CORRELATED_QUERY_DIFFERENTIAL",
        "corpus": {
            "claims": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "claims_path": str(CLAIMS_PATH.relative_to(ROOT)),
            "status_path": str(STATUS_PATH.relative_to(ROOT)),
            "corpus_hash": corpus_hash,
        },
        "query_set": {
            "count": len(FROZEN_QUERIES),
            "k": K,
            "class": "MODEL_AUTHORED_FROM_VISIBLE_LEDGER_NOT_INDEPENDENT_HELDOUT",
            "queries": FROZEN_QUERIES,
        },
        "semantic_equivalence_contract": {
            "sqlite_topology_matched": "same compiled lexical seed scores + indexed SQL topic/domain neighbor joins + same topology/status scoring",
            "compiled_topology": "same compiled lexical seed scores + precompiled in-memory topic/domain maps + same topology/status scoring",
            "required": "identical ordered top-k output on every frozen query",
        },
        "summary": summary,
        "per_query": per_query,
        "candidate_gate": gate,
        "execution_metadata": {
            "git_sha": os.environ.get("GITHUB_SHA", "UNKNOWN_LOCAL"),
            "python": sys.version,
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "iterations": iterations,
            "schedule_seed": 42,
            "warmup_rounds": 5,
        },
        "scope_guard": "Real Clay ledger, but only 17 claims and 8 model-authored correlated queries. This tests model-input preprocessing semantics/hot-path cost, not universal database superiority, independent generalization, or downstream Frank outcomes.",
        "interpretation_rules": [
            "If SQLite with matched topology equals compiled-topology accuracy, the accuracy gain belongs to semantic preprocessing/topology, not to a storage-engine superiority claim.",
            "A compiled hot-path speed win is valid only for this corpus/runtime/workload and does not imply SQLite/PostgreSQL/graph-engine inferiority in general.",
            "UnifiedDB/ledger remains authoritative; compiled topology is derived/disposable and must be invalidated on epoch/semantic change in production.",
        ],
        "next_falsifiers": [
            "Freeze an independently authored/paraphrased real Clay query set without tuning scoring constants on it.",
            "Expand to a much larger real claim/evidence/topic corpus and preserve complete evidence-set ground truth.",
            "Run fair PostgreSQL FTS/pgvector and graph-native competitors under the repository cross-engine contract.",
            "Measure downstream model answer/candidate quality at equal token/context budget.",
            "Replicate on Hostinger Ubuntu and finally on Andreas Ubuntu target hardware.",
        ],
    }
    if args.raw_latency:
        output["raw_latency_us"] = latency
    text = json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    con.close()


if __name__ == "__main__":
    main()
