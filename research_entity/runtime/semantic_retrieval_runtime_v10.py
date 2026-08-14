"""Clay UnifiedDB/ClayGraph semantic retrieval runtime v10/v11 candidate.

Conventional Python runtime only. Clay/ClayCode remains semantic authority.
This module consumes provenance-bound semantic seeds and rebuildable graph projections.

V11 adds a deliberately important semantic distinction: a VERIFIED/CURRENT compiled access
field can be *sufficient*.  When that invariant holds the runtime returns the compiled
family as-is and DOES NOT pad a free top-k budget with unrelated lexical hits.  This is a
preprocessor/context-compiler contract, not a truth or effect-authority promotion.
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
    generation_id: str | None = None
    sufficient: bool = False


class SemanticRetrievalFabric:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def _table_exists(self, name: str) -> bool:
        return self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=? LIMIT 1",
            (name,),
        ).fetchone() is not None

    def _resolve_seed(self, key: str, typed_seed_id: str | None) -> tuple[str] | None:
        if typed_seed_id:
            return self.con.execute(
                """SELECT seed_id FROM semantic_query_seeds
                   WHERE seed_id=? AND status='CURRENT'
                   ORDER BY confidence DESC LIMIT 1""",
                (typed_seed_id,),
            ).fetchone()

        # Exact compiled key is the cheapest and most reproducible path.
        row = self.con.execute(
            """SELECT seed_id FROM semantic_query_seeds
               WHERE normalized_key=? AND status='CURRENT'
               ORDER BY confidence DESC,seed_id LIMIT 1""",
            (key,),
        ).fetchone()
        if row is not None or not key:
            return row

        # Bounded natural-language wrapper support: a compiled semantic key may be embedded
        # in a larger thought ("assemble evidence for gwt causal receipts").  Longest key
        # wins deterministically.  This never creates a new seed or authority.
        return self.con.execute(
            """SELECT seed_id FROM semantic_query_seeds
               WHERE status='CURRENT'
                 AND length(normalized_key)>=3
                 AND instr(?, normalized_key)>0
               ORDER BY length(normalized_key) DESC,confidence DESC,seed_id
               LIMIT 1""",
            (key,),
        ).fetchone()

    def _epochs_match(self, seed_id: str, source_epoch: int, graph_epoch: int) -> bool:
        return self.con.execute(
            """SELECT 1 FROM semantic_query_seeds
               WHERE seed_id=? AND status='CURRENT'
                 AND source_epoch=?
                 AND (graph_epoch IS NULL OR graph_epoch=?)""",
            (seed_id, source_epoch, graph_epoch),
        ).fetchone() is not None

    def _query_v11_sufficient_generation(
        self,
        *,
        seed_id: str,
        source_epoch: int,
        graph_epoch: int,
        limit: int,
    ) -> tuple[tuple[str, ...], str] | None:
        """Return one coherent CURRENT generation, or None.

        Publication through semantic_access_head is the sufficiency boundary.  Readers never
        mix STAGING/old/new generations.  Empty generations do not count as sufficient and
        therefore fall back to the measured conventional retrieval path.
        """
        required = (
            "semantic_access_head",
            "semantic_access_generations",
            "semantic_access_projection_v11",
        )
        if not all(self._table_exists(name) for name in required):
            return None

        head = self.con.execute(
            """SELECT h.generation_id
               FROM semantic_access_head h
               JOIN semantic_access_generations g ON g.generation_id=h.generation_id
               WHERE h.head_key='CURRENT'
                 AND h.source_epoch=? AND h.graph_epoch=?
                 AND g.status='CURRENT'
                 AND g.source_epoch=h.source_epoch
                 AND g.graph_epoch=h.graph_epoch
                 AND g.derivation_hash=h.derivation_hash
               LIMIT 1""",
            (source_epoch, graph_epoch),
        ).fetchone()
        if head is None:
            return None

        generation_id = str(head[0])
        refs = tuple(
            row[0]
            for row in self.con.execute(
                """SELECT target_record_id
                   FROM semantic_access_projection_v11
                   WHERE generation_id=? AND seed_id=?
                   ORDER BY path_rank ASC,path_weight DESC,authority_rank DESC,target_record_id
                   LIMIT ?""",
                (generation_id, seed_id, limit),
            )
        )
        if not refs:
            return None
        return refs, generation_id

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
        if limit <= 0:
            raise ValueError("limit must be positive")
        started = time.perf_counter_ns()
        key = normalize_key(natural_or_typed_key)
        seed = self._resolve_seed(key, typed_seed_id)

        if seed and self._epochs_match(seed[0], source_epoch, graph_epoch):
            v11 = self._query_v11_sufficient_generation(
                seed_id=seed[0],
                source_epoch=source_epoch,
                graph_epoch=graph_epoch,
                limit=limit,
            )
            if v11 is not None:
                refs, generation_id = v11
                return RetrievalResult(
                    refs,
                    "SEMANTIC_GENERATION_SUFFICIENT",
                    seed[0],
                    source_epoch,
                    graph_epoch,
                    time.perf_counter_ns() - started,
                    generation_id,
                    True,
                )

            # V10 compatibility path: still a semantic fast path, but it is not marked
            # sufficient because it lacks the V11 atomic verified-generation boundary.
            if self._table_exists("semantic_access_projection"):
                refs = tuple(
                    row[0]
                    for row in self.con.execute(
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
                        refs,
                        "SEMANTIC_SEED_FASTPATH",
                        seed[0],
                        source_epoch,
                        graph_epoch,
                        time.perf_counter_ns() - started,
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
        return RetrievalResult(
            refs,
            mode,
            seed[0] if seed else None,
            source_epoch,
            graph_epoch,
            time.perf_counter_ns() - started,
        )


def content_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
