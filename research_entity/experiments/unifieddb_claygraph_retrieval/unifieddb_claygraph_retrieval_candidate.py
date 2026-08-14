from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+")
_GRAPH_TERMS = {"depends","dependency","requires","required","requirement","upstream","downstream","route","routes","successor","lineage","receiver","effect","why","because","related","relation","relies","rely","ultimately","through","chain","supports"}
_FRESH_TERMS = {"current","latest","active","now","today","valid"}
_TRUTH_TERMS = {"verified","evidence","supported","truth","authoritative","confirmed"}
_HYP_TERMS = {"hypothesis","hypothetical","speculative","speculation","allegedly","unverified","possible"}
_EVIDENCE_WEIGHT = {
    "KNOWN":1.00,"VERIFIED":1.00,"VALIDATED":0.92,"SUPPORTED":0.90,"DERIVED":0.78,
    "HYPOTHESIS":0.58,"CONFLICT":0.50,"UNKNOWN":0.40,"REVOKED":0.0,
}


class StaleRetrievalProjection(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectionBasis:
    source_epoch: int
    semantic_state_hash: str
    graph_epoch: int
    semantic_projection_verified: bool
    graph_projection_verified: bool


@dataclass(frozen=True)
class RetrievalResult:
    record_id: str
    logical_id: str
    record_kind: str
    epistemic_class: str
    score: float


@dataclass(frozen=True)
class RetrievalReceipt:
    query_id: str
    query_text_hash: str
    basis: ProjectionBasis
    strategy: str
    lexical_candidate_count: int
    graph_candidate_count: int
    latency_us: int
    results: tuple[RetrievalResult, ...]
    authority: str = "CONTEXT_ONLY"


class UnifiedDBClayGraphRetrievalCandidate:
    """Disposable, rebuildable retrieval projection over a coherent UnifiedDB/ClayGraph epoch.

    It is deliberately not canonical state. UnifiedDB/StateLedger remains truth authority;
    ClayGraph remains a derived topology. A projection is rejected once the caller's basis
    epoch/hash no longer matches the basis used to build it.
    """

    def __init__(self, path: str | Path = ":memory:"):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(Path(__file__).with_name("UNIFIEDDB_CLAYGRAPH_RETRIEVAL_PROJECTION_CANDIDATE.sql").read_text())
        self.basis: ProjectionBasis | None = None

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def _stable_json(v: Any) -> str:
        return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _record_from_state(row: dict[str, Any]) -> tuple[Any, ...]:
        value = row.get("value")
        meta = value if isinstance(value, dict) else {}
        domain = str(row.get("domain", "semantic"))
        key = str(row.get("key", ""))
        logical_id = str(meta.get("logical_id") or meta.get("entity_id") or meta.get("component_id") or key)
        record_kind = str(meta.get("record_kind") or meta.get("kind") or domain)
        evidence = str(meta.get("evidence_class") or meta.get("epistemic_class") or row.get("epistemic", "UNKNOWN")).upper()
        status = str(row.get("status", "CURRENT")).upper()
        title = str(meta.get("title") or key)
        if isinstance(meta.get("search_text"), str):
            body = meta["search_text"]
        else:
            body = UnifiedDBClayGraphRetrievalCandidate._stable_json(value)
        raw_tags = meta.get("tags") or meta.get("topics") or []
        if isinstance(raw_tags, (list, tuple, set)):
            tags = " ".join(str(x) for x in raw_tags)
        else:
            tags = str(raw_tags)
        record_id = str(meta.get("record_id") or row.get("semantic_hash") or hashlib.sha256(f"{domain}:{key}".encode()).hexdigest())
        return (
            record_id, logical_id, record_kind, key, domain, evidence, status,
            int(row.get("domain_epoch") or 0), title, body, tags, str(row.get("semantic_hash") or ""),
        )

    def rebuild(self, *, state_rows: Iterable[dict[str, Any]], graph_edges: Iterable[dict[str, Any]], basis: ProjectionBasis) -> dict[str, int]:
        if not basis.semantic_projection_verified:
            raise ValueError("semantic projection is not verified equivalent to canonical UnifiedDB semantics")
        if not basis.graph_projection_verified:
            raise ValueError("ClayGraph projection is ambiguous or not verified equivalent to version-log truth")
        docs = [self._record_from_state(r) for r in state_rows]
        edges = []
        for e in graph_edges:
            edges.append((
                str(e["source_logical_id"]), str(e["target_logical_id"]), str(e.get("relation_type", "RELATED")),
                float(e.get("weight", 0.0)), float(e.get("confidence", 0.5)), int(basis.graph_epoch),
                int(basis.source_epoch), str(e.get("causal_class") or ""),
                self._stable_json(e.get("provenance") or e.get("provenance_clay") or {}),
                self._stable_json(e.get("admissibility") or e.get("admissibility_clay") or {}),
            ))
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute("DELETE FROM udb_retrieval_fts")
            self.conn.execute("DELETE FROM udb_retrieval_documents")
            self.conn.execute("DELETE FROM claygraph_neighbor_cache")
            self.conn.executemany("INSERT INTO udb_retrieval_documents(record_id,logical_id,record_kind,record_key,scope,epistemic_class,status,source_epoch,title,body,tags,source_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", docs)
            self.conn.executemany("INSERT INTO udb_retrieval_fts(record_id,logical_id,title,body,tags) VALUES (?,?,?,?,?)", [(d[0],d[1],d[8],d[9],d[10]) for d in docs])
            self.conn.executemany("INSERT INTO claygraph_neighbor_cache VALUES (?,?,?,?,?,?,?,?,?,?)", edges)
            meta = {"source_epoch":str(basis.source_epoch),"semantic_state_hash":basis.semantic_state_hash,"graph_epoch":str(basis.graph_epoch)}
            self.conn.execute("DELETE FROM retrieval_projection_meta")
            self.conn.executemany("INSERT INTO retrieval_projection_meta(key,value) VALUES (?,?)", meta.items())
            self.conn.commit()
        except Exception:
            self.conn.rollback(); raise
        self.basis = basis
        return {"documents":len(docs),"edges":len(edges)}

    def _assert_basis(self, basis: ProjectionBasis) -> None:
        if self.basis != basis:
            raise StaleRetrievalProjection(f"projection basis {self.basis!r} != requested {basis!r}")

    @staticmethod
    def _fts_query(text: str) -> str:
        toks = [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1]
        return " OR ".join('"' + t.replace('"', '') + '"' for t in toks[:20]) or '"__none__"'

    def _lexical(self, text: str, limit: int = 48):
        return self.conn.execute("""
          SELECT d.record_id,d.logical_id,d.record_kind,d.epistemic_class,udb_retrieval_fts.rank AS rank
          FROM udb_retrieval_fts JOIN udb_retrieval_documents d USING(record_id)
          WHERE udb_retrieval_fts MATCH ? AND d.status='CURRENT'
          ORDER BY udb_retrieval_fts.rank LIMIT ?
        """, (self._fts_query(text), limit)).fetchall()

    def _anchors(self, tokens: set[str]) -> list[str]:
        if not tokens:
            return []
        vals = list(tokens)[:20]
        sql = f"SELECT DISTINCT logical_id FROM udb_retrieval_documents WHERE logical_id IN ({','.join('?' for _ in vals)}) AND status='CURRENT'"
        return [str(r[0]) for r in self.conn.execute(sql, vals)]

    def _walk(self, anchor: str, max_depth: int = 2, limit: int = 48):
        return self.conn.execute("""
          WITH RECURSIVE walk(node,depth,path_score,path) AS (
            SELECT ?1,0,1.0,'|'||?1||'|'
            UNION ALL
            SELECT e.target_logical_id,w.depth+1,
                   w.path_score*e.weight*COALESCE(e.confidence,0.5)*0.82,
                   w.path||e.target_logical_id||'|'
            FROM walk w JOIN claygraph_neighbor_cache e ON e.source_logical_id=w.node
            WHERE w.depth < ?2 AND e.graph_epoch=?3
              AND instr(w.path,'|'||e.target_logical_id||'|')=0
          )
          SELECT d.record_id,d.logical_id,d.record_kind,d.epistemic_class,
                 MIN(w.depth) AS depth,MAX(w.path_score) AS path_score
          FROM walk w JOIN udb_retrieval_documents d ON d.logical_id=w.node
          WHERE w.depth>0 AND d.status='CURRENT'
          GROUP BY d.record_id,d.logical_id,d.record_kind,d.epistemic_class
          ORDER BY depth ASC,path_score DESC LIMIT ?4
        """, (anchor, max_depth, self.basis.graph_epoch, limit)).fetchall()

    def query(self, *, query_id: str, text: str, basis: ProjectionBasis, limit: int = 8, graph_enabled: bool = True) -> RetrievalReceipt:
        if not query_id.strip() or not text.strip():
            raise ValueError("query_id and text are required")
        if limit <= 0 or limit > 128:
            raise ValueError("invalid retrieval limit")
        self._assert_basis(basis)
        started = time.perf_counter_ns()
        rows = self._lexical(text, 48)
        tokens = {t.lower() for t in _TOKEN_RE.findall(text)}
        graph_intent = bool(tokens & _GRAPH_TERMS)
        truth_intent = bool(tokens & _TRUTH_TERMS)
        fresh_intent = bool(tokens & _FRESH_TERMS)
        hyp_intent = bool(tokens & _HYP_TERMS)
        two_hop_intent = bool(tokens & {"ultimately","two","steps","itself"}) or "service chain" in text.lower()
        target_resource = "resource" in tokens or "resources" in tokens
        target_service = "service" in tokens or "capability" in tokens
        scores: dict[str,float] = {}
        meta: dict[str,tuple[str,str,str]] = {}
        for rank, r in enumerate(rows, 1):
            rid=str(r["record_id"]); lid=str(r["logical_id"]); kind=str(r["record_kind"]); ep=str(r["epistemic_class"]).upper()
            scores[rid]=1.0/math.log2(rank+1); meta[rid]=(lid,kind,ep)
        anchors=self._anchors(tokens)
        anchor_set=set(anchors)
        for rid,(lid,kind,ep) in list(meta.items()):
            if lid in anchor_set or (hyp_intent and lid.removesuffix("_hyp") in anchor_set):
                scores[rid]=scores.get(rid,0.0)+0.92
        graph_candidate_count=0
        if graph_enabled and graph_intent:
            for anchor in anchors[:2]:
                for r in self._walk(anchor, 2, 48):
                    rid=str(r["record_id"]); lid=str(r["logical_id"]); kind=str(r["record_kind"]); ep=str(r["epistemic_class"]).upper(); depth=int(r["depth"]); path=float(r["path_score"])
                    if two_hop_intent:
                        depth_bonus=1.28 if depth==2 else 0.42
                    else:
                        depth_bonus=1.0 if depth==1 else 0.42
                    type_bonus=0.0
                    if target_resource and (lid.startswith("resource_") or "resource" in kind.lower()): type_bonus=0.72
                    if target_service and (lid.startswith("service_") or "service" in kind.lower()): type_bonus=0.52
                    scores[rid]=scores.get(rid,0.0)+2.15*path*depth_bonus+type_bonus
                    meta[rid]=(lid,kind,ep); graph_candidate_count += 1
        for rid in list(scores):
            lid,kind,ep=meta.get(rid,("","","UNKNOWN"))
            if hyp_intent:
                evidence_bonus=0.56 if ep=="HYPOTHESIS" else 0.08*_EVIDENCE_WEIGHT.get(ep,0.4)
            else:
                evidence_bonus=(0.44 if truth_intent else 0.13)*_EVIDENCE_WEIGHT.get(ep,0.4)
            scores[rid]+=evidence_bonus
            if fresh_intent: scores[rid]+=0.22
        ranked=sorted(scores.items(), key=lambda kv:(-kv[1],kv[0]))[:limit]
        results=tuple(RetrievalResult(rid,*meta[rid],float(score)) for rid,score in ranked)
        elapsed=(time.perf_counter_ns()-started)//1000
        return RetrievalReceipt(
            query_id=query_id,
            query_text_hash=hashlib.sha256(text.encode()).hexdigest(),
            basis=basis,
            strategy="FTS5_RANK+ENTITY_ANCHOR+BOUNDED_RECURSIVE_CLAYGRAPH+EVIDENCE_INTENT",
            lexical_candidate_count=len(rows),
            graph_candidate_count=graph_candidate_count,
            latency_us=int(elapsed),
            results=results,
        )
