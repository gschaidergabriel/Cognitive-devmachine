from __future__ import annotations

"""Query-adaptive channel router for Clay's possibility-conditioned preprocessor.

This module is deliberately a thin experimental policy over the existing
``rae_core.possibility_preprocessor``. It does not persist state, mint truth, or create a
second possibility store. The preprocessor still runs on every material prompt; this policy
only decides whether the expensive derived ClayGraph/relation channels are likely to add
value for the current query.

Promotion rule: keep only if a same-corpus differential shows no retrieval-quality loss and
lower latency/resource cost. Otherwise lesion/delete this module.
"""

from typing import Any
import math
import time

from . import possibility_preprocessor as base

# Query terms that make relation/topology/counterevidence structure material. Keep this
# conservative: false FULL_ROUTE costs latency; false FAST_ROUTE can lose evidence.
RELATIONAL_ROUTE_TERMS = frozenset({
    "graph", "claygraph", "relation", "relations", "related", "dependency", "dependencies",
    "causal", "cause", "gwt", "workspace", "reentry", "re-entry", "broadcast", "receiver",
    "hyperposition", "alternative", "alternatives", "conflict", "conflicts", "counterevidence",
    "refuted", "superseded", "negative", "authority", "effect", "effects", "capability",
    "capabilities", "tool", "tools", "route", "routing", "coupling", "kappa", "transfer",
    "controller", "loop", "loops", "emergence", "provenance", "lineage", "evidence",
    "receipt", "receipts", "validator", "validation", "constraint", "constraints",
    "possibility", "possibilities", "affordance", "affordances", "stale", "epoch",
})


def route_decision(query: str, *, experiment: str | None = None, packet: str | None = None) -> dict[str, Any]:
    """Return a deterministic non-authoritative channel decision.

    Explicit experiment/packet context always requires the full route. Otherwise the rule is
    intentionally high-recall for relational intent: if a recognized relational token is
    present, use the existing full possibility preprocessor; only clearly lexical queries use
    the SQLite BM25 fast path.
    """
    qterms = tuple(base.tokens(query))
    matched = sorted(set(qterms) & RELATIONAL_ROUTE_TERMS)
    if experiment:
        return {"route": "FULL", "reason": "EXPLICIT_EXPERIMENT", "matched_terms": matched}
    if packet:
        return {"route": "FULL", "reason": "EXPLICIT_PACKET", "matched_terms": matched}
    if matched:
        return {"route": "FULL", "reason": "RELATIONAL_QUERY", "matched_terms": matched}
    return {"route": "FAST", "reason": "LEXICAL_FRONTIER_SUFFICIENT", "matched_terms": []}


def _fast_assembly(query: str, *, limit: int, db=base.SOURCE_DB) -> dict[str, Any]:
    started = time.perf_counter()
    rows = base.bm25_claims(query, db=db, limit=limit)
    selected = []
    chars = 0
    for rank, row in enumerate(rows, 1):
        proposition = str(row.get("proposition") or "")
        chars += len(proposition)
        selected.append({
            "claim_id": row["claim_id"],
            "status": row.get("status"),
            "scope": row.get("scope"),
            "proposition": proposition,
            "assembly_score": None,
            "selection_reasons": [{"channel": "sqlite_bm25_fast", "rank": rank}],
        })
    elapsed = (time.perf_counter() - started) * 1000
    return {
        "schema_version": "0.1-adaptive",
        "assembly_kind": "POSSIBILITY_CONDITIONED_ACTIVE_ASSEMBLY",
        "query": query,
        "query_terms": base.tokens(query),
        "selected": selected,
        "channels": {
            "sqlite_bm25": [r["claim_id"] for r in rows],
            "semantic_relation_1hop": [],
            "claygraph_qualified_1hop": [],
        },
        "counterevidence_reserve": False,
        "counterevidence_inserted": [],
        "metrics": {
            "sqlite_bm25_ms": round(elapsed, 3),
            "relation_ms": 0.0,
            "graph_ms": 0.0,
            "total_ms": round(elapsed, 3),
            "returned_chars": chars,
            "estimated_tokens_chars_div_4": int(math.ceil(chars / 4)),
            "graph_internal": {"skipped": True, "reason": "LEXICAL_FRONTIER_SUFFICIENT"},
        },
        "authority_boundary": "assembly rank/activation never changes evidence status or effect authority",
    }


def assemble_claims_adaptive(
    query: str,
    *,
    db=base.SOURCE_DB,
    graph_dir=base.GRAPH_DIR,
    limit: int = 8,
    candidate_limit: int = 32,
    experiment: str | None = None,
    packet: str | None = None,
    counterevidence_reserve: bool = True,
) -> dict[str, Any]:
    decision = route_decision(query, experiment=experiment, packet=packet)
    if decision["route"] == "FULL":
        out = base.assemble_claims(
            query,
            db=db,
            graph_dir=graph_dir,
            limit=limit,
            candidate_limit=candidate_limit,
            experiment=experiment,
            packet=packet,
            counterevidence_reserve=counterevidence_reserve,
        )
    else:
        out = _fast_assembly(query, limit=limit, db=db)
    out = dict(out)
    out["adaptive_route"] = decision
    out["persistent_second_store"] = False
    out["authority"] = "NON_AUTHORITATIVE_PREPROCESSOR_CONTEXT"
    return out
