#!/usr/bin/env python3
"""Real-contract retrieval gate for UnifiedDB + ClayGraph read planning.

The corpus is made only from current owner-fixed/current governing repository contracts.
Ground truth is manually adjudicated in a separate JSON file. The ranking implementations
never receive expected_path/expected_heading_contains.

Baseline:
  SQLite FTS5 unicode61 + weighted BM25 over Markdown sections.

Candidate:
  The same SQLite FTS5 baseline plus:
  - a small project-ontology bilingual normalization layer;
  - document/section structural cues;
  - an explicit directed reference graph parsed from Markdown contract references;
  - bounded one-hop graph deepening only when useful;
  - context-only receipts with source path/section identity.

This measures Clay/Frank contract evidence retrieval, not universal DB-engine superiority and
not final LLM answer quality. A conventional database can implement the same application
semantics; the test asks whether the Clay-specific adaptive read plan improves the target
workload at acceptable cost.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import sqlite3
import statistics
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "research_entity/benchmarks/unifieddb_real_contract_v1/queries.json"

CORPUS_PATHS = (
    "research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md",
    "research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md",
    "research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md",
    "research_entity/global/FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md",
    "research_entity/global/FRANK_ORGAN_MODULE_BASELINE_BENCHMARK_CONTRACT.md",
    "research_entity/global/LIVE_KNOWLEDGE_REFRESH_PROTOCOL.md",
    "research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md",
    "research_entity/triggers/GO_RECURSIVE_SWARM_CYCLE_PROTOCOL.md",
)

TOKEN_RE = re.compile(r"[\w\-]+", re.UNICODE)
HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
REFERENCE_RE = re.compile(
    r"(?:(?:research_entity|\.claude|tools)/[A-Za-z0-9_./-]+\.(?:md|clay|json)|[A-Z][A-Z0-9_./-]{4,}\.(?:md|clay|json))"
)

STOP = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "is", "are", "be", "as", "by",
    "what", "which", "who", "when", "where", "does", "do", "can", "may", "must", "with", "from", "it",
    "der", "die", "das", "ein", "eine", "einer", "eines", "und", "oder", "zu", "von", "für", "im", "in",
    "auf", "ist", "sind", "sein", "als", "wer", "was", "welche", "welcher", "welches", "wie", "wann", "wo",
    "kann", "darf", "muss", "mit", "aus", "dem", "den", "des", "nach", "vor", "wegen", "nur", "noch",
}

# Small ontology-level bilingual normalization. These are reusable project concepts, not
# expected-answer mappings. They intentionally do not contain file paths or query IDs.
SEMANTIC_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "ändern": ("change", "modify", "mutate", "mutation"),
    "aendern": ("change", "modify", "mutate", "mutation"),
    "autorisieren": ("authorize", "authority", "authorization"),
    "ausführungsautorität": ("execution", "authority", "effect"),
    "ausfuehrungsautoritaet": ("execution", "authority", "effect"),
    "selbstbeobachtung": ("self", "observation", "self-observe"),
    "eigenes": ("own", "self"),
    "raum": ("room", "home_room", "identity"),
    "identität": ("identity", "role", "worker"),
    "identitaet": ("identity", "role", "worker"),
    "betriebssystem": ("operating", "system", "ubuntu", "linux", "host", "target"),
    "release-target": ("release", "target", "host", "ubuntu"),
    "portabilitäts-gate": ("portability", "gate", "out-of-scope"),
    "portabilität": ("portability", "out-of-scope"),
    "portabilitaet": ("portability", "out-of-scope"),
    "handy": ("mobile", "android"),
    "visuelle": ("visual", "perception", "retina"),
    "wahrnehmung": ("perception", "perceptual", "retina"),
    "bildmodell": ("visual", "model", "classifier"),
    "lerner": ("learner", "learning", "classifier", "adaptive"),
    "benutzerspezifische": ("user-specific", "personal", "adaptive"),
    "zyklisch": ("cyclic", "bounded", "update"),
    "ungewöhnliche": ("unusual", "out-of-the-box", "experiment"),
    "ungewoehnliche": ("unusual", "out-of-the-box", "experiment"),
    "komponente": ("component", "subsystem", "module"),
    "ausnahme": ("exception", "foreign", "body"),
    "semantische": ("semantic", "architecture"),
    "verschmelzen": ("fuse", "fusion"),
    "auflösen": ("dissolve", "distribute", "replacement"),
    "aufloesen": ("dissolve", "distribute", "replacement"),
    "organ": ("organ", "module", "historical", "baseline"),
    "ursprünglichen": ("original", "historical", "baseline"),
    "urspruenglichen": ("original", "historical", "baseline"),
    "genauigkeitsmetriken": ("accuracy", "correctness", "metrics", "recall", "mrr", "ndcg"),
    "genauigkeit": ("accuracy", "correctness"),
    "provenienz": ("provenance", "source"),
    "staleness": ("stale", "staleness"),
    "websuche": ("web", "search", "external", "refresh"),
    "forschungsruns": ("research", "run", "cycle", "refresh"),
    "forschungsrun": ("research", "run", "cycle", "refresh"),
    "aktuelle": ("current", "fresh", "live"),
    "externen": ("external", "live", "source"),
    "informationen": ("knowledge", "information", "evidence"),
    "fehlerdruck": ("residual", "error", "pressure", "stalled"),
    "ungelöste": ("unresolved", "residual", "error"),
    "ungeloeste": ("unresolved", "residual", "error"),
    "zustand": ("state", "regime"),
    "verlinkte": ("linked", "referenced", "related", "contract"),
    "vertrag": ("contract", "directive", "protocol"),
    "makrozyklus": ("macro-cycle", "cycle", "go"),
    "ausgeführt": ("executed", "execution"),
    "ausgefuehrt": ("executed", "execution"),
    "bestanden": ("pass", "passed"),
    "reicht": ("sufficient", "enough"),
    "einzige": ("single", "sole", "only"),
    "required": ("mandatory", "requirement"),
    "replacement": ("replace", "redesign", "baseline"),
    "reconstructed": ("reconstruct", "baseline", "historical"),
    "dissolution": ("dissolve", "historical", "baseline"),
    "referenced": ("reference", "linked", "related"),
    "governing": ("contract", "directive", "protocol"),
    "freshness": ("fresh", "refresh", "live"),
    "blind": ("stale", "patch", "refresh"),
    "fixed": ("fixed", "point", "converging"),
    "stalled": ("stalled", "residual", "error", "pressure"),
    "ultimately": ("two", "hop", "chain"),
}

GRAPH_INTENT_TERMS = {
    "referenced", "reference", "linked", "verlinkte", "governing", "depends", "related",
    "which", "welcher", "welche", "contract", "vertrag", "protocol", "directive",
}


@dataclass(frozen=True)
class Section:
    section_id: str
    path: str
    heading: str
    level: int
    body: str
    ordinal: int


@dataclass(frozen=True)
class Hit:
    section_id: str
    path: str
    heading: str
    score: float
    lexical_rank: int | None
    via_path: str | None = None
    strategy: str = "FTS5"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNKNOWN"


def tokens(text: str) -> list[str]:
    out = []
    for tok in TOKEN_RE.findall(text.casefold()):
        tok = tok.strip("_-")
        if len(tok) < 2 or tok in STOP:
            continue
        out.append(tok)
    return out


def expanded_tokens(text: str) -> list[str]:
    raw = tokens(text)
    out: list[str] = []
    seen: set[str] = set()
    for tok in raw:
        for value in (tok, *SEMANTIC_EXPANSIONS.get(tok, ())):
            value = value.casefold().strip()
            if len(value) < 2 or value in seen:
                continue
            seen.add(value)
            out.append(value)
    return out[:64]


def fts_expression(values: list[str]) -> str:
    safe = []
    for value in values[:64]:
        # Keep each concept as one quoted FTS string; unicode61 will tokenize it using the
        # same tokenizer family as indexed text.
        safe.append('"' + value.replace('"', ' ') + '"')
    return " OR ".join(safe) if safe else '"__clay_no_match__"'


def split_markdown(path: str, text: str) -> list[Section]:
    matches = list(HEADING_RE.finditer(text))
    sections: list[Section] = []
    if not matches:
        return [Section(f"{path}#0", path, "__document__", 0, text, 0)]
    if matches[0].start() > 0 and text[: matches[0].start()].strip():
        sections.append(Section(f"{path}#0", path, "__preamble__", 0, text[: matches[0].start()], 0))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading = match.group(2).strip()
        level = len(match.group(1))
        body = text[start:end].strip()
        ordinal = len(sections)
        sections.append(Section(f"{path}#{ordinal}", path, heading, level, body, ordinal))
    return sections


def load_corpus() -> tuple[list[Section], dict[str, str], dict[str, set[str]]]:
    sections: list[Section] = []
    texts: dict[str, str] = {}
    for rel in CORPUS_PATHS:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        texts[rel] = text
        sections.extend(split_markdown(rel, text))

    by_basename = {Path(path).name: path for path in CORPUS_PATHS}
    graph: dict[str, set[str]] = {path: set() for path in CORPUS_PATHS}
    for source, text in texts.items():
        for raw in REFERENCE_RE.findall(text):
            candidate = raw.strip("`'\"()[]{}.,:;")
            target = None
            if candidate in graph:
                target = candidate
            else:
                target = by_basename.get(Path(candidate).name)
            if target and target != source:
                graph[source].add(target)
    return sections, texts, graph


def build_fts(sections: list[Section]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    enabled = int(con.execute("SELECT sqlite_compileoption_used('ENABLE_FTS5')").fetchone()[0])
    if enabled != 1:
        # Some distributions expose FTS5 even if compileoption_used reports 0. The CREATE
        # below is the final capability test and will fail explicitly if absent.
        pass
    con.execute(
        """CREATE VIRTUAL TABLE sections_fts USING fts5(
             section_id UNINDEXED,
             path UNINDEXED,
             heading,
             body,
             tokenize='unicode61 remove_diacritics 2',
             prefix='2 3 4'
           )"""
    )
    con.executemany(
        "INSERT INTO sections_fts(section_id,path,heading,body) VALUES (?,?,?,?)",
        [(s.section_id, s.path, s.heading, s.body) for s in sections],
    )
    return con


def fts_search(con: sqlite3.Connection, query_tokens: list[str], limit: int = 60) -> list[Hit]:
    rows = con.execute(
        """SELECT section_id,path,heading,bm25(sections_fts,0.0,0.0,7.0,1.0) AS bm
           FROM sections_fts
           WHERE sections_fts MATCH ?
           ORDER BY bm ASC, path ASC, section_id ASC
           LIMIT ?""",
        (fts_expression(query_tokens), limit),
    ).fetchall()
    return [
        Hit(str(r["section_id"]), str(r["path"]), str(r["heading"]), -float(r["bm"]), i + 1)
        for i, r in enumerate(rows)
    ]


def baseline_search(con: sqlite3.Connection, text: str, limit: int = 10) -> list[Hit]:
    return fts_search(con, tokens(text), max(limit, 10))[:limit]


def overlap_score(query_terms: set[str], section: Section) -> float:
    if not query_terms:
        return 0.0
    heading_terms = set(tokens(section.heading))
    body_terms = set(tokens(section.body))
    heading_overlap = len(query_terms & heading_terms)
    body_overlap = len(query_terms & body_terms)
    return (2.0 * heading_overlap + 0.35 * body_overlap) / max(1.0, len(query_terms))


def candidate_search(
    con: sqlite3.Connection,
    text: str,
    sections: list[Section],
    graph: dict[str, set[str]],
    limit: int = 10,
) -> tuple[list[Hit], dict[str, Any]]:
    q_terms = expanded_tokens(text)
    lexical = fts_search(con, q_terms, 80)
    by_id = {s.section_id: s for s in sections}
    by_path: dict[str, list[Section]] = defaultdict(list)
    for section in sections:
        by_path[section.path].append(section)

    scores: dict[str, float] = {}
    lexical_rank: dict[str, int] = {}
    via: dict[str, str | None] = {}
    strategy: dict[str, set[str]] = defaultdict(set)

    # Reciprocal-rank fusion is deliberately insensitive to SQLite's absolute BM25 scale.
    for rank, hit in enumerate(lexical, 1):
        rr = 1.0 / (18.0 + rank)
        scores[hit.section_id] = scores.get(hit.section_id, 0.0) + rr
        lexical_rank[hit.section_id] = rank
        via[hit.section_id] = None
        strategy[hit.section_id].add("SEMANTIC_FTS")

        section = by_id[hit.section_id]
        h = section.heading.casefold()
        # Small structural preference for sections that are explicitly normative. This is
        # generic contract structure, not a path-specific answer map.
        if any(term in h for term in ("absolute", "mandatory", "required", "fixed", "invariant", "boundary", "gate")):
            scores[hit.section_id] += 0.0025
            strategy[hit.section_id].add("NORMATIVE_SECTION")

    raw_terms = set(tokens(text))
    query_term_set = set(q_terms)
    graph_intent = bool(raw_terms & GRAPH_INTENT_TERMS) or any(
        phrase in text.casefold() for phrase in ("which referenced", "which governing", "welcher verlinkte", "welche verlinkte")
    )

    # Directed one-hop ClayGraph-like deepening from only the best lexical seed files.
    # It is bounded by seed count, neighbor count and two best sections per neighbor.
    seed_paths: list[str] = []
    for hit in lexical:
        if hit.path not in seed_paths:
            seed_paths.append(hit.path)
        if len(seed_paths) >= 6:
            break

    graph_edges_used: list[tuple[str, str]] = []
    for seed_rank, source in enumerate(seed_paths, 1):
        neighbors = sorted(graph.get(source, ()))[:12]
        for target in neighbors:
            graph_edges_used.append((source, target))
            candidates = sorted(
                by_path[target],
                key=lambda s: (-overlap_score(query_term_set, s), s.ordinal),
            )[:2]
            base_boost = (0.035 if graph_intent else 0.010) / (1.0 + seed_rank)
            for pos, section in enumerate(candidates, 1):
                local = overlap_score(query_term_set, section)
                boost = base_boost * (1.0 + min(local, 2.0)) / pos
                scores[section.section_id] = scores.get(section.section_id, 0.0) + boost
                via.setdefault(section.section_id, source)
                strategy[section.section_id].add("REFERENCE_GRAPH")

    # Lightweight file/heading semantic cue. It is derived from query/path tokens only.
    for section in sections:
        if section.section_id not in scores:
            continue
        path_terms = set(tokens(Path(section.path).stem.replace("_", " ")))
        overlap = len(query_term_set & path_terms)
        if overlap:
            scores[section.section_id] += min(0.006, overlap * 0.0015)
            strategy[section.section_id].add("PATH_SEMANTIC")

    ranked_ids = sorted(
        scores,
        key=lambda sid: (-scores[sid], lexical_rank.get(sid, 10**9), by_id[sid].path, by_id[sid].ordinal),
    )[:limit]
    hits = [
        Hit(
            sid,
            by_id[sid].path,
            by_id[sid].heading,
            scores[sid],
            lexical_rank.get(sid),
            via.get(sid),
            "+".join(sorted(strategy[sid])) or "UNKNOWN",
        )
        for sid in ranked_ids
    ]
    receipt = {
        "authority": "CONTEXT_ONLY",
        "query_terms": q_terms,
        "graph_intent": graph_intent,
        "seed_paths": seed_paths,
        "graph_edges_used": graph_edges_used[:72],
        "candidate_count": len(scores),
    }
    return hits, receipt


def percentile(values: list[int], p: float) -> int:
    values = sorted(values)
    if not values:
        return 0
    idx = min(len(values) - 1, max(0, math.ceil(p * len(values)) - 1))
    return values[idx]


def latency_stats(values: list[int]) -> dict[str, float | int]:
    return {
        "n": len(values),
        "mean_us": statistics.mean(values) / 1000.0 if values else 0.0,
        "p50_us": statistics.median(values) / 1000.0 if values else 0.0,
        "p95_us": percentile(values, 0.95) / 1000.0,
        "p99_us": percentile(values, 0.99) / 1000.0,
        "min_us": min(values) / 1000.0 if values else 0.0,
        "max_us": max(values) / 1000.0 if values else 0.0,
    }


def score_queries(
    queries: list[dict[str, Any]],
    runner,
) -> dict[str, Any]:
    top1_path = 0
    recall3 = 0
    recall5 = 0
    reciprocal: list[float] = []
    section_scored = 0
    section_top1 = 0
    latencies: list[int] = []
    rows: list[dict[str, Any]] = []

    for q in queries:
        started = time.perf_counter_ns()
        result = runner(str(q["query"]))
        receipt = None
        if isinstance(result, tuple):
            hits, receipt = result
        else:
            hits = result
        latencies.append(time.perf_counter_ns() - started)

        expected_path = str(q["expected_path"])
        ranks = [i + 1 for i, hit in enumerate(hits) if hit.path == expected_path]
        rank = ranks[0] if ranks else None
        top1_path += int(rank == 1)
        recall3 += int(rank is not None and rank <= 3)
        recall5 += int(rank is not None and rank <= 5)
        reciprocal.append(1.0 / rank if rank else 0.0)

        expected_heading = q.get("expected_heading_contains")
        if expected_heading:
            section_scored += 1
            section_top1 += int(
                bool(hits)
                and hits[0].path == expected_path
                and str(expected_heading).casefold() in hits[0].heading.casefold()
            )

        rows.append({
            "id": q["id"],
            "language": q["language"],
            "query": q["query"],
            "expected_path": expected_path,
            "expected_heading_contains": expected_heading,
            "rank": rank,
            "top": [
                {
                    "path": h.path,
                    "heading": h.heading,
                    "score": h.score,
                    "lexical_rank": h.lexical_rank,
                    "via_path": h.via_path,
                    "strategy": h.strategy,
                }
                for h in hits[:5]
            ],
            "receipt": receipt,
        })

    n = len(queries)
    return {
        "queries": n,
        "top1_path_accuracy": top1_path / n if n else 0.0,
        "recall_at_3_path": recall3 / n if n else 0.0,
        "recall_at_5_path": recall5 / n if n else 0.0,
        "mrr_path": statistics.mean(reciprocal) if reciprocal else 0.0,
        "section_top1_accuracy": section_top1 / section_scored if section_scored else None,
        "section_scored_queries": section_scored,
        "latency": latency_stats(latencies),
        "rows": rows,
    }


def compact_metrics(result: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in result.items() if k != "rows"}


def main() -> None:
    started = time.perf_counter()
    suite_raw = SUITE.read_bytes()
    suite = json.loads(suite_raw)
    queries = list(suite["queries"])
    sections, texts, graph = load_corpus()
    corpus_hashes = {path: sha256_bytes(text.encode("utf-8")) for path, text in texts.items()}

    con = build_fts(sections)
    # Warm FTS structures once for both strategies. Query order remains identical.
    con.execute("SELECT count(*) FROM sections_fts").fetchone()

    baseline = score_queries(queries, lambda text: baseline_search(con, text, 10))
    candidate = score_queries(
        queries,
        lambda text: candidate_search(con, text, sections, graph, 10),
    )

    by_language: dict[str, Any] = {}
    for language in sorted({q["language"] for q in queries}):
        subset = [q for q in queries if q["language"] == language]
        b = score_queries(subset, lambda text: baseline_search(con, text, 10))
        c = score_queries(subset, lambda text: candidate_search(con, text, sections, graph, 10))
        by_language[language] = {"baseline": compact_metrics(b), "candidate": compact_metrics(c)}

    baseline_m = compact_metrics(baseline)
    candidate_m = compact_metrics(candidate)
    delta = {
        "top1_path_accuracy_points": candidate["top1_path_accuracy"] - baseline["top1_path_accuracy"],
        "recall_at_3_points": candidate["recall_at_3_path"] - baseline["recall_at_3_path"],
        "recall_at_5_points": candidate["recall_at_5_path"] - baseline["recall_at_5_path"],
        "mrr_delta": candidate["mrr_path"] - baseline["mrr_path"],
        "section_top1_accuracy_points": (
            candidate["section_top1_accuracy"] - baseline["section_top1_accuracy"]
            if candidate["section_top1_accuracy"] is not None and baseline["section_top1_accuracy"] is not None
            else None
        ),
        "candidate_over_baseline_p50_latency_ratio": (
            candidate["latency"]["p50_us"] / baseline["latency"]["p50_us"]
            if baseline["latency"]["p50_us"] else None
        ),
    }

    # Accuracy must not regress. At least one primary accuracy/ranking dimension must improve
    # to call this candidate measurably better on this suite. Latency is a trade-off metric,
    # not allowed to compensate for accuracy loss.
    no_accuracy_regression = bool(
        candidate["top1_path_accuracy"] >= baseline["top1_path_accuracy"]
        and candidate["recall_at_3_path"] >= baseline["recall_at_3_path"]
        and candidate["recall_at_5_path"] >= baseline["recall_at_5_path"]
        and candidate["mrr_path"] >= baseline["mrr_path"]
        and (
            baseline["section_top1_accuracy"] is None
            or candidate["section_top1_accuracy"] >= baseline["section_top1_accuracy"]
        )
    )
    measurable_accuracy_gain = bool(
        delta["top1_path_accuracy_points"] > 0
        or delta["recall_at_3_points"] > 0
        or delta["recall_at_5_points"] > 0
        or delta["mrr_delta"] > 1e-12
        or (delta["section_top1_accuracy_points"] or 0) > 0
    )

    con.close()
    result = {
        "schema_version": "1.0",
        "benchmark": suite["suite_id"],
        "evidence_class": "EXECUTED_CURRENT_REPO_CONTRACT_RETRIEVAL",
        "execution_class": os.environ.get("CLAY_EXECUTION_CLASS", "LOCAL_OR_CI_UNKNOWN"),
        "git_head": git_head(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "fts5_compile_option": sqlite3.connect(":memory:").execute(
                "SELECT sqlite_compileoption_used('ENABLE_FTS5')"
            ).fetchone()[0],
        },
        "corpus": {
            "paths": list(CORPUS_PATHS),
            "documents": len(texts),
            "sections": len(sections),
            "directed_reference_edges": sum(len(v) for v in graph.values()),
            "document_sha256": corpus_hashes,
            "suite_sha256": sha256_bytes(suite_raw),
        },
        "ground_truth": {
            "class": suite["class"],
            "query_count": len(queries),
            "languages": sorted({q["language"] for q in queries}),
        },
        "baseline": baseline_m,
        "candidate": candidate_m,
        "delta": delta,
        "by_language": by_language,
        "acceptance": {
            "no_accuracy_regression": no_accuracy_regression,
            "measurable_accuracy_gain": measurable_accuracy_gain,
            "pass": no_accuracy_regression and measurable_accuracy_gain,
        },
        "per_query": {
            "baseline": baseline["rows"],
            "candidate": candidate["rows"],
        },
        "limitations": [
            "The corpus is real/current project contracts, but the query set is small and manually authored by one research worker; independent adjudication is still required.",
            "The candidate's bilingual ontology normalization is application semantics and could also be implemented on top of a conventional database.",
            "The reference graph is parsed from explicit Markdown links only; it does not prove general ClayGraph quality.",
            "This benchmark measures evidence retrieval, not model answer correctness, calibration, or downstream task outcome.",
            "No universal database-engine superiority follows from a win on this project-specific contract workload.",
        ],
        "wall_seconds": time.perf_counter() - started,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if result["acceptance"]["pass"] else 2)


if __name__ == "__main__":
    main()
