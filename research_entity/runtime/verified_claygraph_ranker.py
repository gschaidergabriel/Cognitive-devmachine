from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import re
import sqlite3
import unicodedata


class StaleGraphProjection(RuntimeError):
    pass


class AmbiguousGraphProjection(RuntimeError):
    pass


@dataclass(frozen=True)
class GraphRankedRef:
    ref: str
    score: float
    anchor_ref: str
    relation_type: str
    direction: str
    edge_ref: str
    source_epoch: int
    graph_epoch: int
    authority: str = 'ASSEMBLY_CONTEXT_ONLY'


_STOP = set(
    ('the a an is are was were be been being of to and or in on at for from by with as it '
     'this that what which who how does do where when after before into same actually der die '
     'das ein eine einer einem einen ist sind war waren sein wird werden von zu und oder im in '
     'am für aus mit als es dies diese dieser was welcher welche welches wer wie wo wann tatsächlich').split()
)


def _terms(value) -> set[str]:
    text = unicodedata.normalize('NFKC', str(value)).casefold().replace('v0.1', 'v0_1')
    text = re.sub(r'[_/:\-]+', ' ', text)
    text = re.sub(r'[^\w]+', ' ', text, flags=re.UNICODE)
    return {x for x in text.split() if len(x) > 1 and x not in _STOP and not x.isdigit()}


class VerifiedClayGraphRanker:
    """Verified one-hop ClayGraph ranker for U14/U15/U16 read/deepening callbacks.

    This is a rebuildable context/ranking projection, not a database or truth/effect-authority
    surface. It requires a verified V3 current-head projection plus a UnifiedDB-owned
    admissibility callback before any graph neighbor may enter assembly context.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        text_for_ref: Callable[[str, int], str],
        admissible_ref: Callable[[str, int], bool],
    ):
        self.conn = conn
        self.text_for_ref = text_for_ref
        self.admissible_ref = admissible_ref

    def _verify_projection(self, source_epoch: int, graph_epoch: int) -> None:
        row = self.conn.execute(
            "SELECT MAX(graph_epoch) FROM graph_epochs WHERE status='CURRENT'"
        ).fetchone()
        current = None if row is None else row[0]
        if current is None or int(current) != int(graph_epoch):
            raise StaleGraphProjection(f'graph epoch {graph_epoch}!={current}')

        ambiguous = int(
            self.conn.execute(
                'SELECT COUNT(*) FROM v_graph_projection_ambiguous_edge_epochs'
            ).fetchone()[0]
        )
        if ambiguous:
            raise AmbiguousGraphProjection(f'ambiguous edge epochs: {ambiguous}')

        verified = self.conn.execute(
            'SELECT 1 FROM graph_current_projection_receipts '
            'WHERE graph_epoch=? AND source_epoch=? AND verified_equal=1 '
            'ORDER BY created_at DESC LIMIT 1',
            (graph_epoch, source_epoch),
        ).fetchone()
        if verified is None:
            raise StaleGraphProjection('missing verified graph projection receipt')

        future_heads = int(
            self.conn.execute(
                'SELECT COUNT(*) FROM graph_head_edges WHERE graph_epoch>?',
                (graph_epoch,),
            ).fetchone()[0]
        )
        if future_heads:
            raise StaleGraphProjection('future graph head beyond verified receipt')

    def rank(
        self,
        anchor_ref: str,
        query_text: str,
        source_epoch: int,
        graph_epoch: int,
        limit: int = 8,
    ) -> tuple[GraphRankedRef, ...]:
        if not anchor_ref or not query_text.strip():
            raise ValueError('anchor_ref/query_text required')
        if limit <= 0 or limit > 128:
            raise ValueError('invalid limit')

        self._verify_projection(source_epoch, graph_epoch)
        if not self.admissible_ref(anchor_ref, source_epoch):
            return ()

        query_terms = _terms(query_text)
        anchor_terms = _terms(self.text_for_ref(anchor_ref, source_epoch) or '')
        residual_terms = query_terms - anchor_terms
        best: dict[str, GraphRankedRef] = {}

        rows = self.conn.execute(
            'SELECT logical_edge_id,source_logical_id,target_logical_id,relation_type,'
            'weight,confidence,graph_epoch FROM v_graph_current_edges_fast '
            'WHERE source_logical_id=? OR target_logical_id=? ORDER BY logical_edge_id',
            (anchor_ref, anchor_ref),
        )
        for row in rows:
            if str(row['source_logical_id']) == anchor_ref:
                target = str(row['target_logical_id'])
                direction = 'FORWARD'
                direction_factor = 1.0
            else:
                target = str(row['source_logical_id'])
                direction = 'REVERSE'
                direction_factor = 0.9

            if target == anchor_ref or not self.admissible_ref(target, source_epoch):
                continue

            weight = max(0.0, min(1.0, float(row['weight'])))
            confidence = (
                1.0 if row['confidence'] is None
                else max(0.0, min(1.0, float(row['confidence'])))
            )
            target_terms = _terms(self.text_for_ref(target, source_epoch) or '')
            relation_terms = _terms(row['relation_type'])
            residual_hits = len(residual_terms & target_terms)
            relation_hits = len(query_terms & relation_terms)
            score = (
                0.52 * weight * confidence * direction_factor
                + 0.07 * min(residual_hits, 5)
                + 0.06 * min(relation_hits, 3)
            )

            item = GraphRankedRef(
                ref=target,
                score=score,
                anchor_ref=anchor_ref,
                relation_type=str(row['relation_type']),
                direction=direction,
                edge_ref=f"claygraph:{row['logical_edge_id']}@{row['graph_epoch']}",
                source_epoch=int(source_epoch),
                graph_epoch=int(graph_epoch),
            )
            prior = best.get(target)
            if prior is None or (item.score, item.edge_ref) > (prior.score, prior.edge_ref):
                best[target] = item

        return tuple(
            sorted(best.values(), key=lambda x: (-x.score, x.ref, x.edge_ref))[:limit]
        )

    def refs(
        self,
        anchor_ref: str,
        query_text: str,
        source_epoch: int,
        graph_epoch: int,
        limit: int = 8,
    ) -> tuple[str, ...]:
        """Compatibility callback for AdaptiveSemanticReadPlaneV14.graph_lookup."""
        return tuple(
            item.ref
            for item in self.rank(anchor_ref, query_text, source_epoch, graph_epoch, limit)
        )
