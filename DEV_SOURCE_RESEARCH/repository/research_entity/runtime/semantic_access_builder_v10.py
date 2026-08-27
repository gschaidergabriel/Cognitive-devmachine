"""Projection builder for ClayGraph V3 -> UnifiedDB U10.

This is a deterministic projection compiler, not a truth source.
It refuses mixed epochs and publishes by superseding prior CURRENT rows inside one
UnifiedDB transaction. Clay/ClayCode semantics remain authoritative.
"""
from __future__ import annotations
import hashlib
import sqlite3
import time
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class AccessPath:
    target_record_id: str
    target_logical_id: str
    path_rank: int
    hop_count: int
    path_weight: float
    authority_rank: float
    path_clay: str

def _version_id(seed_id: str, target_record_id: str, source_epoch: int, graph_epoch: int, derivation_hash: str) -> str:
    raw=f"{seed_id}|{target_record_id}|{source_epoch}|{graph_epoch}|{derivation_hash}".encode()
    return "sap:"+hashlib.sha256(raw).hexdigest()[:32]

def publish_projection(
    con: sqlite3.Connection,
    *,
    seed_id: str,
    source_epoch: int,
    graph_epoch: int,
    derivation_hash: str,
    paths: Iterable[AccessPath],
    created_at: str,
) -> dict:
    seed=con.execute(
        """SELECT seed_version_id,source_epoch,graph_epoch,status
           FROM semantic_query_seeds WHERE seed_id=? AND status='CURRENT'""",
        (seed_id,),
    ).fetchone()
    if not seed:
        raise ValueError(f"no CURRENT seed: {seed_id}")
    if seed[1] != source_epoch or (seed[2] is not None and seed[2] != graph_epoch):
        raise ValueError("epoch mismatch; refusing mixed semantic/graph publication")

    rows=sorted(list(paths), key=lambda p:(p.path_rank,-p.path_weight,-p.authority_rank,p.target_record_id))
    if not rows:
        raise ValueError("empty projection; refusing to retire last-known-good")

    started=time.perf_counter_ns()
    with con:
        con.execute(
            "UPDATE semantic_access_projection SET status='SUPERSEDED' WHERE seed_id=? AND status='CURRENT'",
            (seed_id,),
        )
        for p in rows:
            con.execute(
                """INSERT INTO semantic_access_projection(
                   projection_version_id,seed_id,target_record_id,target_logical_id,path_rank,hop_count,
                   path_weight,authority_rank,source_epoch,graph_epoch,derivation_hash,path_clay,status,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (_version_id(seed_id,p.target_record_id,source_epoch,graph_epoch,derivation_hash),
                 seed_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,p.path_weight,
                 p.authority_rank,source_epoch,graph_epoch,derivation_hash,p.path_clay,"CURRENT",created_at),
            )
    latency=time.perf_counter_ns()-started
    return {"seed_id":seed_id,"source_epoch":source_epoch,"graph_epoch":graph_epoch,
            "path_count":len(rows),"publish_latency_ns":latency,"derivation_hash":derivation_hash}
