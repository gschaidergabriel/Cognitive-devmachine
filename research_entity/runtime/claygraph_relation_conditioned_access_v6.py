from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Optional


GLOBAL_INDEX = "idx_graph_head_edges_current_source_weight_v6"
RELATION_INDEX = "idx_graph_head_edges_current_source_relation_weight_v6"


@dataclass(frozen=True)
class RelationConditionedEdge:
    logical_edge_id: str
    edge_version_id: str
    graph_epoch: int
    source_epoch: int
    source_logical_id: str
    target_logical_id: str
    relation_type: str
    weight: float
    confidence: float | None
    provenance_clay: str
    admissibility_clay: str
    causal_class: str | None


@dataclass(frozen=True)
class RelationConditionedReceipt:
    source_logical_id: str
    typed_relation: str | None
    total_budget: int
    relation_reserve: int
    requested_relation_count: int
    fallback_count: int
    selected_edge_ids: tuple[str, ...]
    authority: str = "CONTEXT_ONLY_DERIVED_CLAYGRAPH_ACCESS"


class ClayGraphRelationConditionedAccessV6:
    """Bounded reader over verified/rebuildable ClayGraph head edges.

    This helper does not infer relation intent. A caller may pass a relation only when a typed
    planner stage has already admitted that relation intent. Without one, V6 is ordinary
    global bounded head access.

    V6 never mutates canonical graph/version state and never converts retrieval activation
    into truth or effect authority.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    @staticmethod
    def _edge(row: sqlite3.Row) -> RelationConditionedEdge:
        return RelationConditionedEdge(
            logical_edge_id=str(row["logical_edge_id"]),
            edge_version_id=str(row["edge_version_id"]),
            graph_epoch=int(row["graph_epoch"]),
            source_epoch=int(row["source_epoch"]),
            source_logical_id=str(row["source_logical_id"]),
            target_logical_id=str(row["target_logical_id"]),
            relation_type=str(row["relation_type"]),
            weight=float(row["weight"]),
            confidence=None if row["confidence"] is None else float(row["confidence"]),
            provenance_clay=str(row["provenance_clay"]),
            admissibility_clay=str(row["admissibility_clay"]),
            causal_class=None if row["causal_class"] is None else str(row["causal_class"]),
        )

    def query(
        self,
        *,
        source_logical_id: str,
        total_budget: int = 32,
        typed_relation: Optional[str] = None,
        relation_reserve: int = 8,
    ) -> tuple[tuple[RelationConditionedEdge, ...], RelationConditionedReceipt]:
        if not source_logical_id:
            raise ValueError("source_logical_id is required")
        if total_budget <= 0 or total_budget > 512:
            raise ValueError("total_budget must be in 1..512")
        if relation_reserve < 0 or relation_reserve > total_budget:
            raise ValueError("relation_reserve must be in 0..total_budget")

        relation = typed_relation.strip().upper() if typed_relation else None
        requested_rows: list[sqlite3.Row] = []
        if relation and relation_reserve:
            requested_rows = self.conn.execute(
                f"""
                SELECT logical_edge_id,edge_version_id,graph_epoch,source_epoch,
                       source_logical_id,target_logical_id,relation_type,weight,confidence,
                       provenance_clay,admissibility_clay,causal_class
                FROM graph_head_edges INDEXED BY {RELATION_INDEX}
                WHERE source_status='CURRENT'
                  AND source_logical_id=?
                  AND relation_type=?
                ORDER BY weight DESC,target_logical_id ASC,logical_edge_id ASC
                LIMIT ?
                """,
                (source_logical_id, relation, relation_reserve),
            ).fetchall()

        remaining = total_budget - len(requested_rows)
        fallback_rows: list[sqlite3.Row] = []
        if remaining > 0:
            selected_ids = [str(row["logical_edge_id"]) for row in requested_rows]
            params: list[object] = [source_logical_id]
            exclusion = ""
            if selected_ids:
                exclusion = " AND logical_edge_id NOT IN (" + ",".join("?" for _ in selected_ids) + ")"
                params.extend(selected_ids)
            params.append(remaining)
            fallback_rows = self.conn.execute(
                f"""
                SELECT logical_edge_id,edge_version_id,graph_epoch,source_epoch,
                       source_logical_id,target_logical_id,relation_type,weight,confidence,
                       provenance_clay,admissibility_clay,causal_class
                FROM graph_head_edges INDEXED BY {GLOBAL_INDEX}
                WHERE source_status='CURRENT'
                  AND source_logical_id=?
                  {exclusion}
                ORDER BY weight DESC,target_logical_id ASC,logical_edge_id ASC
                LIMIT ?
                """,
                params,
            ).fetchall()

        rows = requested_rows + fallback_rows
        edges = tuple(self._edge(row) for row in rows)
        receipt = RelationConditionedReceipt(
            source_logical_id=source_logical_id,
            typed_relation=relation,
            total_budget=total_budget,
            relation_reserve=relation_reserve if relation else 0,
            requested_relation_count=len(requested_rows),
            fallback_count=len(fallback_rows),
            selected_edge_ids=tuple(edge.logical_edge_id for edge in edges),
        )
        return edges, receipt
