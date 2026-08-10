#!/usr/bin/env python3
"""Typed, bounded context retrieval for UnifiedDB + ClayGraph candidate projections.

No LLM is used inside the authority path. Callers pass a typed QueryIntent.
The projections are rebuildable; semantic truth remains in UnifiedDB.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass(frozen=True)
class QueryIntent:
    seed_logical_id: str
    mode: str = "DIRECT"
    relation_type: Optional[str] = None
    hops: int = 0
    limit: int = 8


class ContextAssembler:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def resolve(self, intent: QueryIntent) -> list[sqlite3.Row]:
        if intent.limit < 1 or intent.limit > 128:
            raise ValueError("limit outside 1..128")
        if intent.mode == "DIRECT":
            return list(self.conn.execute(
                "SELECT * FROM clay_current_semantic_projection WHERE logical_id=? LIMIT ?",
                (intent.seed_logical_id, intent.limit),
            ))
        if intent.mode != "LOCAL_GRAPH":
            raise ValueError(f"unsupported mode: {intent.mode}")
        if not intent.relation_type:
            raise ValueError("LOCAL_GRAPH requires relation_type")
        if intent.hops < 1 or intent.hops > 32:
            raise ValueError("hops outside 1..32")
        sql = """
        WITH RECURSIVE walk(node,depth) AS (
          SELECT ?,0
          UNION ALL
          SELECT a.target_logical_id,w.depth+1
          FROM walk w
          JOIN graph_current_adjacency a
            ON a.source_logical_id=w.node AND a.relation_type=?
          WHERE w.depth < ?
        )
        SELECT p.*
        FROM walk w
        JOIN clay_current_semantic_projection p ON p.logical_id=w.node
        WHERE w.depth=?
        LIMIT ?
        """
        return list(self.conn.execute(
            sql,
            (intent.seed_logical_id, intent.relation_type, intent.hops, intent.hops, intent.limit),
        ))
