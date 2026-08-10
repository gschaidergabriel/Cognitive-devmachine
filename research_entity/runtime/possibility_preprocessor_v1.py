"""Clay UnifiedDB possibility preprocessor research candidate.

This module turns already justified candidate possibilities from ClayCode semantics,
UnifiedDB state, ClayGraph topology, Hyperposition facets and runtime receipts into
standing, provenance-bound, family-factorized packets. The hot path reads one packet by
canonical context signature; packet relevance never creates truth or effect authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Mapping, Any
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone

DEFAULT_SELECTOR = {"utility":0.40,"coherence":0.16,"urgency":0.10,"evidence":0.22,"risk":-0.08,"cost":-0.04}

def utcnow() -> str: return datetime.now(timezone.utc).isoformat()
def stable_json(value: Any) -> str: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def sha256_text(value: str) -> str: return hashlib.sha256(value.encode("utf-8")).hexdigest()
def canonical_context_signature(cue_refs: Iterable[str], facets: Mapping[str, Any] | None = None) -> str:
    return sha256_text(stable_json({"cue_refs": sorted(set(cue_refs)), "facets": facets or {}}))

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
    family_id: str | None = None
    valid_until: str | None = None

def choose_materialization_mode(*, read_rate: float, update_rate: float, lazy_query_ms: float,
                                packet_query_ms: float, maintenance_ms: float,
                                storage_penalty_ms: float = 0.0,
                                uncertainty_fraction: float = 0.10) -> tuple[str, float]:
    """Choose where preprocessing happens; this is cost policy, never epistemic authority."""
    read_saving=max(0.0,lazy_query_ms-packet_query_ms)*max(0.0,read_rate)
    upkeep=max(0.0,maintenance_ms)*max(0.0,update_rate)+max(0.0,storage_penalty_ms)
    net=read_saving-upkeep; scale=max(read_saving+upkeep,1e-12)
    if abs(net)<=scale*max(0.0,uncertainty_fraction): return "HYBRID",net
    return ("STANDING" if net>0 else "LAZY"),net

def selector_hash(weights: Mapping[str,float]) -> str: return sha256_text(stable_json(dict(weights)))
def score(c: Candidate, w: Mapping[str,float]=DEFAULT_SELECTOR) -> float:
    return c.utility*w["utility"]+c.coherence*w["coherence"]+c.urgency*w["urgency"]+c.evidence_score*w["evidence"]+c.risk*w["risk"]+c.cost*w["cost"]

def upsert_candidates(con: sqlite3.Connection, candidates: Iterable[Candidate]) -> int:
    now=utcnow(); rows=[]; members=[]
    for c in candidates:
        family_id=c.family_id or str(c.provenance.get("possibility_family_id") or c.provenance.get("rule") or c.candidate_id)
        version_id=sha256_text(f"{c.candidate_id}|{family_id}|{c.source_epoch}|{c.graph_epoch}|{c.derivation_hash}|{c.valid_until}")[:32]
        con.execute("UPDATE possibility_candidates SET status='STALE' WHERE candidate_id=? AND status='CURRENT' AND candidate_version_id<>?",(c.candidate_id,version_id))
        rows.append((version_id,c.candidate_id,family_id,c.context_signature,c.source_epoch,c.graph_epoch,c.candidate_kind,
          stable_json(c.semantic_refs),stable_json(c.graph_refs),stable_json(c.hyperposition_refs),stable_json(c.evidence_refs),
          stable_json(c.conflict_refs),stable_json(c.uncertainty_refs),stable_json(c.authority_refs),stable_json(c.dependency_refs),
          c.utility,c.coherence,c.urgency,c.evidence_score,c.risk,c.cost,stable_json(c.provenance),c.derivation_hash,c.valid_until,"CURRENT",now))
        for ref in sorted(set(c.dependency_refs)): members.append((version_id,ref,"DEPENDENCY","SEMANTIC_CLOSURE"))
        for ref in sorted(set(c.graph_refs)): members.append((version_id,ref,"GRAPH","DERIVED_TOPOLOGY"))
        for ref in sorted(set(c.evidence_refs)): members.append((version_id,ref,"EVIDENCE","PROVENANCE"))
    con.executemany("""INSERT OR REPLACE INTO possibility_candidates(
      candidate_version_id,candidate_id,family_id,context_signature,source_epoch,graph_epoch,candidate_kind,
      semantic_refs_clay,graph_refs_clay,hyperposition_refs_clay,evidence_refs_clay,conflict_refs_clay,uncertainty_refs_clay,
      authority_refs_clay,dependency_refs_clay,utility,coherence,urgency,evidence_score,risk,cost,provenance_clay,
      derivation_hash,valid_until,status,materialized_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",rows)
    con.executemany("INSERT OR REPLACE INTO possibility_candidate_members(candidate_version_id,member_ref,member_role,dependency_class) VALUES(?,?,?,?)",members)
    return len(rows)

def compile_packet(con: sqlite3.Connection, context_signature: str, source_epoch: int,
                   graph_epoch: int | None, top_k: int=3,
                   weights: Mapping[str,float]=DEFAULT_SELECTOR,
                   selector_id: str="clay.possibility.selector.v1") -> dict[str,Any]:
    started=time.perf_counter_ns()
    rows=con.execute("""SELECT candidate_version_id,candidate_id,family_id,candidate_kind,semantic_refs_clay,graph_refs_clay,
      hyperposition_refs_clay,evidence_refs_clay,conflict_refs_clay,uncertainty_refs_clay,authority_refs_clay,dependency_refs_clay,
      utility,coherence,urgency,evidence_score,risk,cost,provenance_clay,derivation_hash,valid_until
      FROM possibility_candidates WHERE context_signature=? AND status='CURRENT' AND source_epoch<=?
      AND (valid_until IS NULL OR julianday(valid_until)>julianday('now'))
      AND (graph_epoch IS NULL OR ? IS NULL OR graph_epoch<=?)""",(context_signature,source_epoch,graph_epoch,graph_epoch)).fetchall()
    candidates=[]; deps=set()
    for r in rows:
        c=Candidate(candidate_id=r[1],context_signature=context_signature,source_epoch=source_epoch,graph_epoch=graph_epoch,
          candidate_kind=r[3],semantic_refs=json.loads(r[4]),graph_refs=json.loads(r[5]),hyperposition_refs=json.loads(r[6]),
          evidence_refs=json.loads(r[7]),conflict_refs=json.loads(r[8]),uncertainty_refs=json.loads(r[9]),authority_refs=json.loads(r[10]),
          dependency_refs=json.loads(r[11]),utility=r[12],coherence=r[13],urgency=r[14],evidence_score=r[15],risk=r[16],cost=r[17],
          provenance=json.loads(r[18]),derivation_hash=r[19],family_id=r[2],valid_until=r[20])
        candidates.append((score(c,weights),r[0],c)); deps.update(c.dependency_refs); deps.update(c.graph_refs); deps.update(c.evidence_refs)
    candidates.sort(key=lambda x:(-x[0],-x[2].evidence_score,x[2].risk,x[2].candidate_id,x[1]))
    selected=[]; suppressed=[]; selected_families=set()
    for item in candidates:
        _,vid,c=item; family=c.family_id or c.candidate_id
        if family in selected_families:
            suppressed.append({"candidate_version_id":vid,"candidate_id":c.candidate_id,"family_id":family,"reason":"DUPLICATE_FAMILY"}); continue
        if len(selected)<top_k:
            selected.append(item); selected_families.add(family)
        else:
            suppressed.append({"candidate_version_id":vid,"candidate_id":c.candidate_id,"family_id":family,"reason":"TOP_K"})
    packet={"context_signature":context_signature,"source_epoch":source_epoch,"graph_epoch":graph_epoch,
      "selector_id":selector_id,"selector_hash":selector_hash(weights),
      "selected":[{"candidate_version_id":vid,"candidate_id":c.candidate_id,"family_id":c.family_id or c.candidate_id,
        "candidate_kind":c.candidate_kind,"score":round(s,12),"semantic_refs":list(c.semantic_refs),"graph_refs":list(c.graph_refs),
        "hyperposition_refs":list(c.hyperposition_refs),"evidence_refs":list(c.evidence_refs),"conflict_refs":list(c.conflict_refs),
        "uncertainty_refs":list(c.uncertainty_refs),"authority_refs":list(c.authority_refs),"provenance":c.provenance,
        "derivation_hash":c.derivation_hash} for s,vid,c in selected],
      "suppressed":suppressed,"family_count":len({(c.family_id or c.candidate_id) for _,_,c in candidates})}
    packet_clay=stable_json(packet); packet_hash=sha256_text(packet_clay)
    packet_id=sha256_text(f"{context_signature}|{source_epoch}|{graph_epoch}|{packet['selector_hash']}|{packet_hash}|{utcnow()}|{time.perf_counter_ns()}")[:32]
    con.execute("UPDATE possibility_packets SET status='SUPERSEDED' WHERE context_signature=? AND status='CURRENT'",(context_signature,))
    con.execute("""INSERT INTO possibility_packets(packet_id,context_signature,source_epoch,graph_epoch,selector_id,selector_hash,top_k,
      candidate_refs_clay,suppressed_refs_clay,conflict_refs_clay,uncertainty_refs_clay,authority_refs_clay,next_intents_clay,
      packet_clay,packet_hash,candidate_count,family_count,valid_until,status,materialized_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (packet_id,context_signature,source_epoch,graph_epoch,selector_id,packet["selector_hash"],top_k,
       stable_json([{"candidate_version_id":x[1],"candidate_id":x[2].candidate_id,"family_id":x[2].family_id or x[2].candidate_id} for x in selected]),
       stable_json(suppressed),stable_json(sorted({x for _,_,c in selected for x in c.conflict_refs})),
       stable_json(sorted({x for _,_,c in selected for x in c.uncertainty_refs})),stable_json(sorted({x for _,_,c in selected for x in c.authority_refs})),
       "[]",packet_clay,packet_hash,len(candidates),packet["family_count"],None,"CURRENT",utcnow()))
    con.executemany("INSERT OR IGNORE INTO possibility_packet_dependencies(packet_id,member_ref,dependency_class) VALUES(?,?,?)",[(packet_id,r,"TRANSITIVE_MEMBER") for r in sorted(deps)])
    elapsed=(time.perf_counter_ns()-started)/1_000_000.0
    receipt_id=sha256_text(f"receipt|{packet_id}|{elapsed}|{time.perf_counter_ns()}")[:32]
    con.execute("""INSERT INTO possibility_compile_receipts(receipt_id,context_signature,source_epoch,graph_epoch,selector_hash,
      candidate_count,selected_count,compile_latency_ms,update_scope_count,packet_hash,verification_class,evidence_refs_clay,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(receipt_id,context_signature,source_epoch,graph_epoch,packet["selector_hash"],len(candidates),len(selected),elapsed,len(deps),packet_hash,"LOCAL_EXECUTION_PRIMARY","[]",utcnow()))
    return packet

def read_current_packet(con: sqlite3.Connection, context_signature: str, *, expected_source_epoch: int|None=None,
                        expected_graph_epoch: int|None=None) -> dict[str,Any] | None:
    row=con.execute("SELECT packet_clay,source_epoch,graph_epoch FROM v_current_possibility_packets WHERE context_signature=?",(context_signature,)).fetchone()
    if row is None: return None
    if expected_source_epoch is not None and row[1]!=expected_source_epoch: return None
    if expected_graph_epoch is not None and row[2]!=expected_graph_epoch: return None
    return json.loads(row[0])

def retire_candidates_by_ref(con: sqlite3.Connection, changed_ref: str) -> list[str]:
    rows=con.execute("""SELECT DISTINCT c.candidate_version_id,c.context_signature FROM possibility_candidate_members m
      JOIN possibility_candidates c ON c.candidate_version_id=m.candidate_version_id WHERE m.member_ref=? AND c.status='CURRENT'""",(changed_ref,)).fetchall()
    if rows: con.executemany("UPDATE possibility_candidates SET status='STALE' WHERE candidate_version_id=?",[(r[0],) for r in rows])
    return sorted(set(r[1] for r in rows))

def affected_signatures(con: sqlite3.Connection, changed_ref: str) -> list[str]:
    rows=con.execute("""SELECT DISTINCT p.context_signature FROM possibility_packet_dependencies d JOIN possibility_packets p ON p.packet_id=d.packet_id
      WHERE d.member_ref=? AND p.status='CURRENT'""",(changed_ref,)).fetchall()
    return sorted(r[0] for r in rows)

def invalidate_ref(con: sqlite3.Connection, changed_ref: str, source_epoch: int, reason_class: str) -> list[str]:
    sigs=affected_signatures(con,changed_ref)
    if sigs: con.executemany("UPDATE possibility_packets SET status='STALE' WHERE context_signature=? AND status='CURRENT'",[(s,) for s in sigs])
    inv_id=sha256_text(f"{changed_ref}|{source_epoch}|{reason_class}|{utcnow()}")[:32]
    con.execute("INSERT INTO possibility_packet_invalidations VALUES(?,?,?,?,?,?,?,?)",(inv_id,changed_ref,source_epoch,stable_json(sigs),reason_class,utcnow(),None,"OPEN"))
    return sigs
