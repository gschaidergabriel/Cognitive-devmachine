from __future__ import annotations

"""Possibility-conditioned context assembly for Clay/UnifiedDB.

This module is a research candidate, not a truth authority.  It keeps SQLite/FTS as a
physical candidate generator, fuses it with explicit semantic relations and a bounded
ClayGraph neighborhood, and emits an explainable active assembly.  The model does not
need to decide whether to retrieve first: callers can run this preprocessor on every
material prompt and expose only the bounded assembly.

Scientific/authority boundaries:
- candidate activation/rank never changes claim status or evidence strength;
- exact canonical/ledger state remains authoritative;
- graph expansion is bounded and qualified (one hop by default);
- counterevidence is preserved rather than silently optimized away.
"""

import json
import math
import re
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "research_sources" / "sources.db"
GRAPH_DIR = ROOT / "research_entity" / "claygraph" / "runtime" / "current"

STOP = {
    "the", "and", "for", "with", "from", "that", "this", "into", "under", "over",
    "oder", "und", "der", "die", "das", "den", "dem", "des", "eine", "einer", "einem",
    "einen", "für", "mit", "von", "zur", "zum", "wie", "was", "welche", "welcher",
    "welches", "ist", "sind", "auf", "bei",
}
COUNTER_STATUSES = {"REFUTED", "NEGATIVE_RESULT", "SUPERSEDED"}
RRF_K = 36.0


def tokens(text: str) -> list[str]:
    out: list[str] = []
    for raw in re.findall(r"[A-Za-zÄÖÜäöüß0-9][A-Za-zÄÖÜäöüß0-9_.:/+-]*", text.lower()):
        tok = raw.strip("._:/+-")
        if len(tok) >= 3 and tok not in STOP and tok not in out:
            out.append(tok)
    return out[:20]


def fts_expr(text: str) -> str:
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in tokens(text))


def _open_db(db: Path = SOURCE_DB) -> sqlite3.Connection:
    if not db.exists():
        raise RuntimeError(f"derived source DB missing: {db}")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


def _claim_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "claim_id": r["claim_id"],
        "status": r["status"],
        "scope": r["scope"],
        "proposition": r["proposition"],
    }


def bm25_claims(query: str, *, db: Path = SOURCE_DB, limit: int = 24) -> list[dict[str, Any]]:
    """Strong conventional baseline: SQLite FTS5 ordered by native BM25 rank."""
    expr = fts_expr(query)
    if not expr:
        return []
    con = _open_db(db)
    try:
        rows = con.execute(
            """SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,
                      bm25(claim_fts) AS bm25_score
               FROM claim_fts JOIN claims c USING(claim_id)
               LEFT JOIN claim_current_status cs USING(claim_id)
               WHERE claim_fts MATCH ?
               ORDER BY bm25_score ASC, c.claim_id ASC LIMIT ?""",
            (expr, limit),
        ).fetchall()
        return [{**_claim_row(r), "bm25_score": float(r["bm25_score"])} for r in rows]
    finally:
        con.close()


def _explicit_relation_claims(
    query: str,
    *,
    db: Path = SOURCE_DB,
    bm25_seed_ids: list[str] | None = None,
    experiment: str | None = None,
    packet: str | None = None,
    limit: int = 32,
) -> list[dict[str, Any]]:
    """Qualified relational expansion: explicit experiment/packet or one shared topic hop."""
    con = _open_db(db)
    seen: dict[str, dict[str, Any]] = {}

    def add(rows: list[sqlite3.Row], reason: str) -> None:
        for r in rows:
            cid = r["claim_id"]
            if cid not in seen:
                seen[cid] = {**_claim_row(r), "relation_reason": reason}

    try:
        if experiment:
            add(con.execute(
                """SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
                   FROM claim_evidence ce JOIN claims c USING(claim_id)
                   LEFT JOIN claim_current_status cs USING(claim_id)
                   WHERE ce.evidence_ref LIKE ? ORDER BY c.claim_id LIMIT ?""",
                (f"%{experiment}%", limit),
            ).fetchall(), "experiment")
        if packet:
            add(con.execute(
                """SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
                   FROM claim_topic ct JOIN claims c USING(claim_id)
                   LEFT JOIN claim_current_status cs USING(claim_id)
                   WHERE ct.packet_id=? ORDER BY c.claim_id LIMIT ?""",
                (packet, limit),
            ).fetchall(), "packet")

        seeds = list(dict.fromkeys(bm25_seed_ids or []))[:4]
        if seeds:
            marks = ",".join("?" for _ in seeds)
            packet_ids = [r["packet_id"] for r in con.execute(
                f"SELECT DISTINCT packet_id FROM claim_topic WHERE claim_id IN ({marks}) ORDER BY packet_id",
                seeds,
            ).fetchall()]
            if packet_ids:
                marks2 = ",".join("?" for _ in packet_ids)
                add(con.execute(
                    f"""SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
                        FROM claim_topic ct JOIN claims c USING(claim_id)
                        LEFT JOIN claim_current_status cs USING(claim_id)
                        WHERE ct.packet_id IN ({marks2}) ORDER BY c.claim_id LIMIT ?""",
                    (*packet_ids, limit),
                ).fetchall(), "shared_topic_1hop")
        return list(seen.values())[:limit]
    finally:
        con.close()


def _graph_claims(query: str, *, graph_dir: Path = GRAPH_DIR, limit: int = 32) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Use the existing explainable ClayGraph candidate, but constrain propagation to one hop."""
    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import claygraph_query  # type: ignore

    out = claygraph_query.activate(
        query,
        graph_dir,
        limit=max(limit * 3, 36),
        hops=1,
        seed_limit=14,
        refresh=False,
        lexical_only=False,
    )
    claims: list[dict[str, Any]] = []
    for r in out.get("results", []):
        if r.get("type") != "claim":
            continue
        cid = str(r.get("identity") or "")
        if not cid:
            continue
        claims.append({
            "claim_id": cid,
            "status": r.get("status"),
            "scope": r.get("evidence_class"),
            "proposition": r.get("excerpt") or r.get("label") or "",
            "graph_score": float(r.get("score") or 0.0),
            "activation_reason": r.get("activation_reason") or {},
        })
        if len(claims) >= limit:
            break
    return claims, out.get("metrics", {})


def _topic_neighbors(claim_ids: list[str], *, db: Path = SOURCE_DB) -> dict[str, list[dict[str, Any]]]:
    if not claim_ids:
        return {}
    con = _open_db(db)
    try:
        marks = ",".join("?" for _ in claim_ids)
        topic_by_claim: dict[str, list[str]] = defaultdict(list)
        for r in con.execute(f"SELECT claim_id,packet_id FROM claim_topic WHERE claim_id IN ({marks})", claim_ids):
            topic_by_claim[r["claim_id"]].append(r["packet_id"])
        packets = sorted({p for xs in topic_by_claim.values() for p in xs})
        if not packets:
            return {}
        marks2 = ",".join("?" for _ in packets)
        rows = con.execute(
            f"""SELECT ct.packet_id,c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
                FROM claim_topic ct JOIN claims c USING(claim_id)
                LEFT JOIN claim_current_status cs USING(claim_id)
                WHERE ct.packet_id IN ({marks2}) ORDER BY ct.packet_id,c.claim_id""",
            packets,
        ).fetchall()
        by_packet: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            by_packet[r["packet_id"]].append(_claim_row(r))
        out: dict[str, list[dict[str, Any]]] = {}
        for cid, ps in topic_by_claim.items():
            merged: dict[str, dict[str, Any]] = {}
            for p in ps:
                for row in by_packet.get(p, []):
                    if row["claim_id"] != cid:
                        merged[row["claim_id"]] = row
            out[cid] = list(merged.values())
        return out
    finally:
        con.close()


def _rrf_add(scores: dict[str, float], reasons: dict[str, list[dict[str, Any]]], channel: str,
             rows: list[dict[str, Any]], weight: float) -> None:
    for rank, row in enumerate(rows, 1):
        cid = row["claim_id"]
        contribution = weight / (RRF_K + rank)
        scores[cid] = scores.get(cid, 0.0) + contribution
        reasons.setdefault(cid, []).append({"channel": channel, "rank": rank, "rrf": contribution})


def assemble_claims(
    query: str,
    *,
    db: Path = SOURCE_DB,
    graph_dir: Path = GRAPH_DIR,
    limit: int = 8,
    candidate_limit: int = 32,
    experiment: str | None = None,
    packet: str | None = None,
    counterevidence_reserve: bool = True,
) -> dict[str, Any]:
    """Compile a bounded active claim assembly from independent candidate channels.

    RRF is intentionally rank-based so BM25 magnitude, graph activation and relation scores
    are not pretended to be calibrated probabilities.  A single optional counterevidence
    reserve is the GO-cycle lesionable out-of-box experiment.
    """
    started = time.perf_counter()
    qtokens = set(tokens(query))

    t0 = time.perf_counter()
    bm25 = bm25_claims(query, db=db, limit=candidate_limit)
    t1 = time.perf_counter()
    strong_seed_ids: list[str] = []
    for row in bm25[:8]:
        txt = f"{row.get('scope','')} {row.get('proposition','')}".lower()
        overlap = sum(1 for t in qtokens if t in txt)
        if overlap >= (2 if len(qtokens) >= 2 else 1):
            strong_seed_ids.append(row["claim_id"])
        if len(strong_seed_ids) >= 4:
            break
    relations = _explicit_relation_claims(
        query,
        db=db,
        bm25_seed_ids=strong_seed_ids,
        experiment=experiment,
        packet=packet,
        limit=candidate_limit,
    )
    t2 = time.perf_counter()
    graph, graph_metrics = _graph_claims(query, graph_dir=graph_dir, limit=candidate_limit)
    t3 = time.perf_counter()

    scores: dict[str, float] = {}
    reasons: dict[str, list[dict[str, Any]]] = {}
    rows_by_id: dict[str, dict[str, Any]] = {}
    for rows in (bm25, relations, graph):
        for row in rows:
            rows_by_id.setdefault(row["claim_id"], row)
    _rrf_add(scores, reasons, "sqlite_bm25", bm25, 1.00)
    _rrf_add(scores, reasons, "semantic_relation_1hop", relations, 1.10)
    _rrf_add(scores, reasons, "claygraph_qualified_1hop", graph, 0.92)

    for cid, row in rows_by_id.items():
        txt = f"{row.get('scope','')} {row.get('proposition','')}".lower()
        overlap = sum(1 for t in qtokens if t in txt)
        # Lexical overlap is a small tie-breaker only; it cannot mint status/truth.
        scores[cid] = scores.get(cid, 0.0) + min(0.004, overlap * 0.0005)
        reasons.setdefault(cid, []).append({"channel": "query_overlap_tiebreak", "count": overlap})

    ranked_ids = sorted(scores, key=lambda cid: (-scores[cid], cid))
    selected_ids = ranked_ids[:limit]
    counter_inserted: list[str] = []

    if counterevidence_reserve and limit >= 3 and selected_ids:
        neighbors = _topic_neighbors(selected_ids[: max(1, limit // 2)], db=db)
        counter_candidates: list[tuple[float, str, dict[str, Any], str]] = []
        for seed in selected_ids[: max(1, limit // 2)]:
            for row in neighbors.get(seed, []):
                cid = row["claim_id"]
                if cid in selected_ids or row.get("status") not in COUNTER_STATUSES:
                    continue
                txt = f"{row.get('scope','')} {row.get('proposition','')}".lower()
                overlap = sum(1 for t in qtokens if t in txt)
                relevance = scores.get(cid, 0.0) + overlap * 0.003
                counter_candidates.append((relevance, cid, row, seed))
        if counter_candidates:
            counter_candidates.sort(key=lambda x: (-x[0], x[1]))
            _, cid, row, seed = counter_candidates[0]
            rows_by_id[cid] = row
            reasons.setdefault(cid, []).append({"channel": "counterevidence_reserve", "paired_with": seed})
            scores[cid] = max(scores.get(cid, 0.0), scores.get(seed, 0.0) * 0.82)
            # Reserve exactly one slot, replacing only the weakest non-counter item.
            replace_at = None
            for idx in range(len(selected_ids) - 1, -1, -1):
                r = rows_by_id[selected_ids[idx]]
                if r.get("status") not in COUNTER_STATUSES:
                    replace_at = idx
                    break
            if replace_at is not None:
                selected_ids[replace_at] = cid
                counter_inserted.append(cid)

    # Deduplicate after possible reserve replacement while preserving order.
    dedup: list[str] = []
    for cid in selected_ids + ranked_ids:
        if cid not in dedup:
            dedup.append(cid)
        if len(dedup) >= limit:
            break
    selected_ids = dedup

    selected: list[dict[str, Any]] = []
    total_chars = 0
    for cid in selected_ids:
        row = rows_by_id[cid]
        prop = str(row.get("proposition") or "")
        total_chars += len(prop)
        selected.append({
            "claim_id": cid,
            "status": row.get("status"),
            "scope": row.get("scope"),
            "proposition": prop,
            "assembly_score": round(scores.get(cid, 0.0), 8),
            "selection_reasons": reasons.get(cid, []),
        })

    ended = time.perf_counter()
    return {
        "schema_version": "0.1",
        "assembly_kind": "POSSIBILITY_CONDITIONED_ACTIVE_ASSEMBLY",
        "query": query,
        "query_terms": list(qtokens),
        "selected": selected,
        "channels": {
            "sqlite_bm25": [r["claim_id"] for r in bm25],
            "semantic_relation_1hop": [r["claim_id"] for r in relations],
            "claygraph_qualified_1hop": [r["claim_id"] for r in graph],
        },
        "counterevidence_reserve": counterevidence_reserve,
        "counterevidence_inserted": counter_inserted,
        "metrics": {
            "sqlite_bm25_ms": round((t1 - t0) * 1000, 3),
            "relation_ms": round((t2 - t1) * 1000, 3),
            "graph_ms": round((t3 - t2) * 1000, 3),
            "total_ms": round((ended - started) * 1000, 3),
            "returned_chars": total_chars,
            "estimated_tokens_chars_div_4": int(math.ceil(total_chars / 4)),
            "graph_internal": graph_metrics,
        },
        "authority_boundary": "assembly rank/activation never changes evidence status or effect authority",
    }
