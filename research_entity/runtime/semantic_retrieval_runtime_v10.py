"""Clay UnifiedDB/ClayGraph semantic retrieval runtime v10 candidate.

Conventional Python runtime only. Clay/ClayCode remains semantic authority.
This module consumes provenance-bound semantic seeds and rebuildable graph projections.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re
import sqlite3
import time
from typing import Sequence

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

def normalize_key(text: str) -> str:
    return " ".join(m.group(0).lower() for m in _TOKEN_RE.finditer(text))

def reciprocal_rank_fusion(rankings: Sequence[Sequence[str]], k: int = 60) -> list[str]:
    """Fuse independent rank lists; raw heterogeneous scores are never compared."""
    score: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            score[item] = score.get(item, 0.0) + 1.0 / (k + rank)
    return [item for item, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))]

@dataclass(frozen=True)
class RetrievalResult:
    refs: tuple[str, ...]
    mode: str
    seed_id: str | None
    source_epoch: int
    graph_epoch: int
    latency_ns: int

class SemanticRetrievalFabric:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def _resolve_seed(self, key: str, typed_seed_id: str | None) -> tuple[str] | None:
        if typed_seed_id:
            return self.con.execute(
                """SELECT seed_id FROM semantic_query_seeds
                   WHERE seed_id=? AND status='CURRENT'
                   ORDER BY confidence DESC LIMIT 1""", (typed_seed_id,)
            ).fetchone()
        return self.con.execute(
            """SELECT seed_id FROM semantic_query_seeds
               WHERE normalized_key=? AND status='CURRENT'
               ORDER BY confidence DESC LIMIT 1""", (key,)
        ).fetchone()

    def _epochs_match(self, seed_id: str, source_epoch: int, graph_epoch: int) -> bool:
        return self.con.execute(
            """SELECT 1 FROM semantic_query_seeds
               WHERE seed_id=? AND status='CURRENT'
                 AND source_epoch=?
                 AND (graph_epoch IS NULL OR graph_epoch=?)""",
            (seed_id, source_epoch, graph_epoch),
        ).fetchone() is not None

    def query_seed(
        self,
        natural_or_typed_key: str = "",
        *,
        typed_seed_id: str | None = None,
        source_epoch: int,
        graph_epoch: int,
        limit: int = 8,
        lexical_ranking: Sequence[str] | None = None,
        graph_fallback_ranking: Sequence[str] | None = None,
    ) -> RetrievalResult:
        started = time.perf_counter_ns()
        seed = self._resolve_seed(normalize_key(natural_or_typed_key), typed_seed_id)

        if seed and self._epochs_match(seed[0], source_epoch, graph_epoch):
            refs = tuple(
                row[0] for row in self.con.execute(
                    """SELECT target_record_id
                       FROM semantic_access_projection
                       WHERE seed_id=? AND status='CURRENT'
                         AND source_epoch=? AND graph_epoch=?
                       ORDER BY path_rank ASC,path_weight DESC,authority_rank DESC,target_record_id
                       LIMIT ?""",
                    (seed[0], source_epoch, graph_epoch, limit),
                )
            )
            if refs:
                return RetrievalResult(
                    refs, "SEMANTIC_SEED_FASTPATH", seed[0],
                    source_epoch, graph_epoch, time.perf_counter_ns() - started
                )

        rankings = [r for r in (lexical_ranking, graph_fallback_ranking) if r]
        if len(rankings) >= 2:
            refs = tuple(reciprocal_rank_fusion(rankings)[:limit])
            mode = "HYBRID_RRF_FALLBACK"
        elif rankings:
            refs = tuple(rankings[0][:limit])
            mode = "LEXICAL_FALLBACK"
        else:
            refs = ()
            mode = "MISS"
        return RetrievalResult(refs, mode, seed[0] if seed else None,
                               source_epoch, graph_epoch, time.perf_counter_ns() - started)

def content_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
