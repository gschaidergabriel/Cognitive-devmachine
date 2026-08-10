"""Clay UnifiedDB possibility preprocessor research candidate.

This module is intentionally small: it turns already justified candidate possibilities
(from ClayCode semantics, UnifiedDB state, ClayGraph topology, Hyperposition facets, runtime
receipts or deterministic affordance rules) into standing, provenance-bound packets.
The hot path reads one packet by canonical context signature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Mapping, Any
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone

DEFAULT_SELECTOR = {
    "utility": 0.40,
    "coherence": 0.16,
    "urgency": 0.10,
    "evidence": 0.22,
    "risk": -0.08,
    "cost": -0.04,
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_context_signature(cue_refs: Iterable[str], facets: Mapping[str, Any] | None = None) -> str:
    payload = {"cue_refs": sorted(set(cue_refs)), "facets": facets or {}}
    return sha256_text(stable_json(payload))


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    context_signature: str
    source_epoch: int
    graph_epoch: int | None
    candidate_kind: str
    semantic_refs: Sequence[str]
    graph_refs: Sequence[str]
    hyperposition_refs: Sequence[str]
    evidence_refs: Sequence[str]
    conflict_refs: Sequence[str]
    uncertainty_refs: Sequence[str]
    authority_refs: Sequence[str]
    dependency_refs: Sequence[str]
    utility: float
    coherence: float
    urgency: float
    evidence_score: float
    risk: float
    cost: float
    provenance: Mapping[str, Any]
    derivation_hash: str


def choose_materialization_mode(*, read_rate: float, update_rate: float, lazy_query_ms: float,
                                packet_query_ms: float, maintenance_ms: float,
                                storage_penalty_ms: float = 0.0,
                                uncertainty_fraction: float = 0.10) -> tuple[str, float]:
    """Place preprocessing work only where measured read savings beat upkeep."""
    read_saving = max(0.0, lazy_query_ms - packet_query_ms) * max(0.0, read_rate)
    upkeep = max(0.0, maintenance_ms) * max(0.0, update_rate) + max(0.0, storage_penalty_ms)
    net = read_saving - upkeep
    scale = max(read_saving + upkeep, 1e-12)
    if abs(net) <= scale * max(0.0, uncertainty_fraction):
        return "HYBRID", net
    return ("STANDING" if net > 0 else "LAZY"), net


def selector_hash(weights: Mapping[str, float]) -> str:
    return sha256_text(stable_json(dict(weights)))


def score(candidate: Candidate, weights: Mapping[str, float] = DEFAULT_SELECTOR) -> float:
    return (candidate.utility * weights["utility"] + candidate.coherence * weights["coherence"]
            + candidate.urgency * weights["urgency"] + candidate.evidence_score * weights["evidence"]
            + candidate.risk * weights["risk"] + candidate.cost * weights["cost"])


def upsert_candidates(con: sqlite3.Connection, candidates: Iterable[Candidate]) -> int:
    now = utcnow()
    rows, members = [], []
    for c in candidates:
        candidate_version_id = sha256_text(
            f"{c.candidate_id}|{c.source_epoch}|{c.graph_epoch}|{c.derivation_hash}"
        )[:32]
        # Preserve history but enforce one CURRENT version per logical candidate.
        con.execute(
            "UPDATE possibility_candidates SET status='STALE' WHERE candidate_id=? AND status='CURRENT' AND candidate_version_id<>?",
            (c.candidate_id, candidate_version_id),
        )
        rows.append((candidate_version_id, c.candidate_id, c.context_signature, c.source_epoch,
                     c.graph_epoch, c.candidate_kind, stable_json(c.semantic_refs),
                     stable_json(c.graph_refs), stable_json(c.hyperposition_refs),
                     stable_json(c.evidence_refs), stable_json(c.conflict_refs),
                     stable_json(c.uncertainty_refs), stable_json(c.authority_refs),
                     stable_json(c.dependency_refs), c.utility, c.coherence, c.urgency,
                     c.evidence_score, c.risk, c.cost, stable_json(c.provenance),
                     c.derivation_hash, "CURRENT", now))
        for ref in sorted(set(c.dependency_refs)):
            members.append((candidate_version_id, ref, "DEPENDENCY", "SEMANTIC_CLOSURE"))
        for ref in sorted(set(c.graph_refs)):
            members.append((candidate_version_id, ref, "GRAPH", "DERIVED_TOPOLOGY"))
        for ref in sorted(set(c.evidence_refs)):
            members.append((candidate_version_id, ref, "EVIDENCE", "PROVENANCE"))
    con.executemany("""INSERT OR REPLACE INTO possibility_candidates(
        candidate_version_id,candidate_id,context_signature,source_epoch,graph_epoch,candidate_kind,
        semantic_refs_clay,graph_refs_clay,hyperposition_refs_clay,evidence_refs_clay,
        conflict_refs_clay,uncertainty_refs_clay,authority_refs_clay,dependency_refs_clay,
        utility,coherence,urgency,evidence_score,risk,cost,provenance_clay,derivation_hash,status,materialized_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    con.executemany("""INSERT OR REPLACE INTO possibility_candidate_members(
        candidate_version_id,member_ref,member_role,dependency_class) VALUES(?,?,?,?)""", members)
    return len(rows)


def compile_packet(con: sqlite3.Connection, context_signature: str, source_epoch: int,
                   graph_epoch: int | None, top_k: int = 3,
                   weights: Mapping[str, float] = DEFAULT_SELECTOR,
                   selector_id: str = "clay.possibility.selector.v1") -> dict[str, Any]:
    started = time.perf_counter_ns()
    rows = con.execute("""SELECT candidate_version_id,candidate_id,candidate_kind,
                  semantic_refs_clay,graph_refs_clay,hyperposition_refs_clay,evidence_refs_clay,
                  conflict_refs_clay,uncertainty_refs_clay,authority_refs_clay,dependency_refs_clay,
                  utility,coherence,urgency,evidence_score,risk,cost,provenance_clay,derivation_hash
           FROM possibility_candidates
           WHERE context_signature=? AND status='CURRENT' AND source_epoch<=?
             AND (graph_epoch IS NULL OR ? IS NULL OR graph_epoch<=?)""",
        (context_signature, source_epoch, graph_epoch, graph_epoch)).fetchall()
    candidates = []
    dependency_refs: set[str] = set()
    for r in rows:
        candidate_version_id = r[0]
        c = Candidate(candidate_id=r[1], context_signature=context_signature,
            source_epoch=source_epoch, graph_epoch=graph_epoch, candidate_kind=r[2],
            semantic_refs=json.loads(r[3]), graph_refs=json.loads(r[4]),
            hyperposition_refs=json.loads(r[5]), evidence_refs=json.loads(r[6]),
            conflict_refs=json.loads(r[7]), uncertainty_refs=json.loads(r[8]),
            authority_refs=json.loads(r[9]), dependency_refs=json.loads(r[10]),
            utility=r[11], coherence=r[12], urgency=r[13], evidence_score=r[14],
            risk=r[15], cost=r[16], provenance=json.loads(r[17]), derivation_hash=r[18])
        candidates.append((score(c, weights), candidate_version_id, c))
        dependency_refs.update(c.dependency_refs)
        dependency_refs.update(c.graph_refs)
        dependency_refs.update(c.evidence_refs)
    candidates.sort(key=lambda sc: (-sc[0], -sc[2].evidence_score, sc[2].risk,
                                    sc[2].candidate_id, sc[1]))
    selected = candidates[:top_k]
    suppressed = [{"candidate_version_id": v, "candidate_id": c.candidate_id}
                  for _, v, c in candidates[top_k:]]
    packet = {
        "context_signature": context_signature,
        "source_epoch": source_epoch,
        "graph_epoch": graph_epoch,
        "selector_id": selector_id,
        "selector_hash": selector_hash(weights),
        "selected": [{"candidate_version_id": v, "candidate_id": c.candidate_id,
            "candidate_kind": c.candidate_kind, "score": round(s, 12),
            "semantic_refs": list(c.semantic_refs), "graph_refs": list(c.graph_refs),
            "hyperposition_refs": list(c.hyperposition_refs),
            "evidence_refs": list(c.evidence_refs), "conflict_refs": list(c.conflict_refs),
            "uncertainty_refs": list(c.uncertainty_refs),
            "authority_refs": list(c.authority_refs), "provenance": c.provenance,
            "derivation_hash": c.derivation_hash} for s, v, c in selected],
        "suppressed": suppressed,
    }
    packet_clay = stable_json(packet)
    packet_hash = sha256_text(packet_clay)
    packet_id = sha256_text(
        f"{context_signature}|{source_epoch}|{graph_epoch}|{packet['selector_hash']}|"
        f"{packet_hash}|{utcnow()}|{time.perf_counter_ns()}"
    )[:32]
    con.execute("UPDATE possibility_packets SET status='SUPERSEDED' WHERE context_signature=? AND status='CURRENT'",
                (context_signature,))
    con.execute("""INSERT INTO possibility_packets(
        packet_id,context_signature,source_epoch,graph_epoch,selector_id,selector_hash,top_k,
        candidate_refs_clay,suppressed_refs_clay,conflict_refs_clay,uncertainty_refs_clay,
        authority_refs_clay,next_intents_clay,packet_clay,packet_hash,candidate_count,valid_until,status,materialized_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (packet_id, context_signature, source_epoch, graph_epoch, selector_id,
         packet["selector_hash"], top_k,
         stable_json([{"candidate_version_id": x[1], "candidate_id": x[2].candidate_id}
                      for x in selected]), stable_json(suppressed),
         stable_json(sorted({x for _, _, c in selected for x in c.conflict_refs})),
         stable_json(sorted({x for _, _, c in selected for x in c.uncertainty_refs})),
         stable_json(sorted({x for _, _, c in selected for x in c.authority_refs})),
         "[]", packet_clay, packet_hash, len(candidates), None, "CURRENT", utcnow()))
    con.executemany("""INSERT OR IGNORE INTO possibility_packet_dependencies(
        packet_id,member_ref,dependency_class) VALUES(?,?,?)""",
        [(packet_id, ref, "TRANSITIVE_MEMBER") for ref in sorted(dependency_refs)])
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    receipt_id = sha256_text(f"receipt|{packet_id}|{elapsed_ms}|{time.perf_counter_ns()}")[:32]
    con.execute("""INSERT INTO possibility_compile_receipts(
        receipt_id,context_signature,source_epoch,graph_epoch,selector_hash,candidate_count,
        selected_count,compile_latency_ms,update_scope_count,packet_hash,verification_class,
        evidence_refs_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (receipt_id, context_signature, source_epoch, graph_epoch, packet["selector_hash"],
         len(candidates), len(selected), elapsed_ms, len(dependency_refs), packet_hash,
         "LOCAL_EXECUTION_PRIMARY", "[]", utcnow()))
    return packet


def read_current_packet(con: sqlite3.Connection, context_signature: str, *,
                        expected_source_epoch: int | None = None,
                        expected_graph_epoch: int | None = None) -> dict[str, Any] | None:
    row = con.execute(
        "SELECT packet_clay,source_epoch,graph_epoch FROM v_current_possibility_packets WHERE context_signature=?",
        (context_signature,),
    ).fetchone()
    if row is None:
        return None
    if expected_source_epoch is not None and row[1] != expected_source_epoch:
        return None
    if expected_graph_epoch is not None and row[2] != expected_graph_epoch:
        return None
    return json.loads(row[0])


def retire_candidates_by_ref(con: sqlite3.Connection, changed_ref: str) -> list[str]:
    rows = con.execute("""SELECT DISTINCT c.candidate_version_id,c.context_signature
           FROM possibility_candidate_members m
           JOIN possibility_candidates c ON c.candidate_version_id=m.candidate_version_id
           WHERE m.member_ref=? AND c.status='CURRENT'""", (changed_ref,)).fetchall()
    ids = [r[0] for r in rows]
    if ids:
        con.executemany("UPDATE possibility_candidates SET status='STALE' WHERE candidate_version_id=?",
                        [(x,) for x in ids])
    return sorted(set(r[1] for r in rows))


def affected_signatures(con: sqlite3.Connection, changed_ref: str) -> list[str]:
    rows = con.execute("""SELECT DISTINCT p.context_signature
           FROM possibility_packet_dependencies d
           JOIN possibility_packets p ON p.packet_id=d.packet_id
           WHERE d.member_ref=? AND p.status='CURRENT'""", (changed_ref,)).fetchall()
    return sorted(r[0] for r in rows)


def invalidate_ref(con: sqlite3.Connection, changed_ref: str, source_epoch: int,
                   reason_class: str) -> list[str]:
    sigs = affected_signatures(con, changed_ref)
    if sigs:
        con.executemany("UPDATE possibility_packets SET status='STALE' WHERE context_signature=? AND status='CURRENT'",
                        [(s,) for s in sigs])
    inv_id = sha256_text(f"{changed_ref}|{source_epoch}|{reason_class}|{utcnow()}")[:32]
    con.execute("INSERT INTO possibility_packet_invalidations VALUES(?,?,?,?,?,?,?,?)",
                (inv_id, changed_ref, source_epoch, stable_json(sigs), reason_class,
                 utcnow(), None, "OPEN"))
    return sigs
