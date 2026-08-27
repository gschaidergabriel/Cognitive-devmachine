"""Clay U10 possibility compiler candidate.

This module compiles bounded ClayGraph neighborhoods into ranked possibility fields and
keeps dynamic admissibility constraints as bitset facets. It is a derived read product:
UnifiedDB/ClayGraph source epochs and provenance remain authoritative.

The compiler deliberately keeps multiple simple path states until final projection so that
strong-but-blocking paths do not erase weaker alternatives that can reach a better later
candidate. Stored witnesses are bounded; exploration is separately bounded by
``max_path_states``. Hitting that bound marks the field truncated, and exact callers must
fall back to an authoritative recursive evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import sqlite3
import time
from typing import Dict, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    weight: float = 1.0
    relation_ref: str = ""


@dataclass(frozen=True)
class CandidateMeta:
    utility: float = 1.0
    admissible: bool = True
    facets: Mapping[str, str] = field(default_factory=dict)
    evidence_refs: Sequence[str] = field(default_factory=tuple)
    provenance: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CompilerConfig:
    compiler_id: str = "clay-possibility-compiler-v10"
    compiler_version: str = "10.0.0-candidate"
    max_depth: int = 3
    max_witnesses_per_candidate: int = 4
    max_path_states: int = 250_000

    @property
    def policy_hash(self) -> str:
        payload = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()


class TruncatedField(RuntimeError):
    pass


def _json(v: object) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(v: object) -> str:
    return sha256(_json(v).encode()).hexdigest()


def encode_dense_bitset(ordinals: Iterable[int], highwater: int) -> bytes:
    bits = 0
    for ordinal in ordinals:
        if ordinal < 0:
            raise ValueError("negative ordinal")
        bits |= 1 << ordinal
    width = max(1, (highwater + 8) // 8)
    return bits.to_bytes(width, "little", signed=False)


def decode_dense_bitset(blob: bytes | None) -> int:
    return int.from_bytes(blob or b"\x00", "little", signed=False)


class PossibilityCompiler:
    def __init__(self, conn: sqlite3.Connection, config: CompilerConfig = CompilerConfig()):
        self.conn = conn
        self.config = config
        self._ordinal_cache: Dict[str, int] | None = None
        self._adj_cache_key: tuple[int, int, int] | None = None
        self._adj_cache: Dict[str, list[GraphEdge]] | None = None

    def install_spec(self, created_at: str) -> None:
        c = self.config
        self.conn.execute(
            """
            INSERT OR REPLACE INTO clay_possibility_compiler_specs(
              compiler_id,compiler_version,max_depth,max_witnesses_per_candidate,max_path_states,
              selector_clay,score_policy_clay,facet_schema_clay,invalidation_policy_clay,
              policy_hash,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                c.compiler_id,c.compiler_version,c.max_depth,c.max_witnesses_per_candidate,
                c.max_path_states,
                "bounded simple-path field; preserve alternatives until projection",
                "score = path_product * candidate.utility",
                "dynamic exact-match facet bitsets over stable candidate ordinals",
                "facet delta -> facet-only; witness invalidation -> witness repair or anchor recompile; truncation -> exact fallback",
                c.policy_hash,"CANDIDATE",created_at,
            ),
        )

    def ensure_ordinals(self, candidate_refs: Iterable[str], source_epoch: int) -> Dict[str, int]:
        if self._ordinal_cache is None:
            self._ordinal_cache = dict(self.conn.execute("SELECT candidate_ref,ordinal FROM clay_possibility_ordinals"))
        existing = self._ordinal_cache
        high = max(existing.values(), default=-1)
        for ref in sorted(set(candidate_refs)):
            if ref not in existing:
                high += 1
                self.conn.execute(
                    "INSERT INTO clay_possibility_ordinals(candidate_ref,ordinal,first_source_epoch,status) VALUES(?,?,?,'CURRENT')",
                    (ref, high, source_epoch),
                )
                existing[ref] = high
        return existing

    def start_field_epoch(self, *, field_epoch: int, source_epoch: int, graph_epoch: int,
                          input_hash: str, built_at: str,
                          metadata: Mapping[str, object] | None = None) -> None:
        self.conn.execute(
            """INSERT INTO clay_possibility_field_epochs(
              field_epoch,source_epoch,graph_epoch,compiler_id,input_hash,status,built_at,build_metadata_clay
            ) VALUES(?,?,?,?,?,'BUILDING',?,?)""",
            (field_epoch,source_epoch,graph_epoch,self.config.compiler_id,input_hash,built_at,_json(metadata or {})),
        )

    def complete_field_epoch(self, field_epoch: int, completed_at: str) -> None:
        row = self.conn.execute(
            "SELECT field_id,output_hash,truncated FROM clay_possibility_anchor_fields WHERE field_epoch=? ORDER BY anchor_ref",
            (field_epoch,),
        ).fetchall()
        field_hash = _hash(row)
        with self.conn:
            self.conn.execute(
                "UPDATE clay_possibility_field_epochs SET status='SUPERSEDED' WHERE status='CURRENT' AND field_epoch<>?",
                (field_epoch,),
            )
            self.conn.execute(
                "UPDATE clay_possibility_field_epochs SET field_hash=?,status='CURRENT',completed_at=? WHERE field_epoch=? AND status='BUILDING'",
                (field_hash, completed_at, field_epoch),
            )
            if self.conn.execute("SELECT changes()").fetchone()[0] != 1:
                raise RuntimeError("field epoch was not BUILDING at promotion")

    def build_facets(self, *, field_epoch: int, candidate_meta: Mapping[str, CandidateMeta],
                     source_epoch: int, created_at: str) -> None:
        ordinals = self.ensure_ordinals(candidate_meta.keys(), source_epoch)
        high = max(ordinals.values(), default=0)
        buckets: Dict[tuple[str, str], list[int]] = {}
        for ref, meta in candidate_meta.items():
            if not meta.admissible:
                continue
            buckets.setdefault(("admissible", "true"), []).append(ordinals[ref])
            for k, v in meta.facets.items():
                buckets.setdefault((str(k), str(v)), []).append(ordinals[ref])
        for (key, value), members in buckets.items():
            blob = encode_dense_bitset(members, high)
            fid = f"facet:{field_epoch}:{_hash([key,value])[:20]}"
            self.conn.execute(
                """INSERT OR REPLACE INTO clay_possibility_facets(
                  facet_id,field_epoch,facet_key,facet_value,encoding,membership_blob,member_count,
                  ordinal_highwater,source_hash,status,created_at
                ) VALUES(?,?,?,?, 'DENSE_BITSET_LE',?,?,?,?, 'CURRENT',?)""",
                (fid,field_epoch,key,value,blob,len(members),high,
                 _hash([source_epoch,key,value,sorted(members)]),created_at),
            )

    def compile_anchor(self, *, field_epoch: int, source_epoch: int, graph_epoch: int,
                       anchor_ref: str, edges: Sequence[GraphEdge],
                       candidate_meta: Mapping[str, CandidateMeta], created_at: str) -> dict:
        t0 = time.perf_counter_ns()
        ordinals = self.ensure_ordinals(candidate_meta.keys(), source_epoch)
        cache_key = (graph_epoch, id(edges), len(edges))
        if self._adj_cache_key != cache_key or self._adj_cache is None:
            adj: Dict[str, list[GraphEdge]] = {}
            for e in edges:
                if e.weight < 0:
                    raise ValueError("negative edge weight unsupported in v10 candidate")
                adj.setdefault(e.source, []).append(e)
            self._adj_cache_key = cache_key
            self._adj_cache = adj
        else:
            adj = self._adj_cache

        witnesses: Dict[str, list[tuple[float, tuple[str, ...], tuple[str, ...]]]] = {
            anchor_ref: [(1.0, (anchor_ref,), ())]
        }
        frontier = [(anchor_ref, 1.0, (anchor_ref,), ())]
        explored = 1
        truncated = False
        for _depth in range(self.config.max_depth):
            nxt = []
            for node, pscore, path, rels in frontier:
                for edge in adj.get(node, ()):
                    if edge.target in path:
                        continue
                    explored += 1
                    if explored > self.config.max_path_states:
                        truncated = True
                        break
                    score = pscore * edge.weight
                    npath = path + (edge.target,)
                    nrels = rels + ((edge.relation_ref or f"{edge.source}->{edge.target}"),)
                    nxt.append((edge.target, score, npath, nrels))
                    witnesses.setdefault(edge.target, []).append((score, npath, nrels))
                if truncated:
                    break
            frontier = nxt
            if truncated or not frontier:
                break

        ranked = []
        for ref, ws in witnesses.items():
            meta = candidate_meta.get(ref)
            if meta is None or not meta.admissible:
                continue
            best_path = max(w[0] for w in ws)
            ranked.append((ref, best_path * meta.utility, best_path, ws, meta))
        ranked.sort(key=lambda x: (-x[1], x[0]))

        input_hash = _hash({
            "source_epoch": source_epoch,"graph_epoch": graph_epoch,"anchor": anchor_ref,
            "edges": [(e.source,e.target,e.weight,e.relation_ref) for e in edges],
            "meta": {k:{"utility":v.utility,"admissible":v.admissible,"facets":dict(v.facets)}
                     for k,v in candidate_meta.items()},
            "policy": self.config.policy_hash,
        })
        output_hash = _hash([(r[0],r[1],r[2],len(r[3])) for r in ranked])
        field_id = f"pf:{field_epoch}:{_hash(anchor_ref)[:20]}"
        compile_ms = (time.perf_counter_ns() - t0) / 1e6
        self.conn.execute(
            """INSERT OR REPLACE INTO clay_possibility_anchor_fields(
              field_id,field_epoch,anchor_ref,candidate_count,truncated,compile_ms,input_hash,output_hash,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?, 'CURRENT',?)""",
            (field_id,field_epoch,anchor_ref,len(ranked),1 if truncated else 0,
             compile_ms,input_hash,output_hash,created_at),
        )
        self.conn.execute("DELETE FROM clay_possibility_field_members WHERE field_id=?", (field_id,))

        member_rows = []
        witness_rows = []
        for rank, (ref, score, best_path, ws, meta) in enumerate(ranked):
            ordinal = ordinals[ref]
            sorted_ws = sorted(ws, key=lambda w: (-w[0], w[1]))
            kept = sorted_ws[: self.config.max_witnesses_per_candidate]
            witness_truncated = len(sorted_ws) > len(kept)
            member_rows.append(
                (field_id,ref,ordinal,rank,score,best_path,len(ws),1 if witness_truncated else 0,
                 _json(list(meta.evidence_refs)),_json(dict(meta.provenance)))
            )
            for wrank, (pscore, path, rels) in enumerate(kept):
                ph = _hash([path,rels])
                witness_rows.append(
                    (f"pw:{field_id}:{ordinal}:{wrank}:{ph[:10]}",field_id,ref,wrank,
                     pscore,_json(path),_json(rels),ph,created_at)
                )
        self.conn.executemany(
            """INSERT INTO clay_possibility_field_members(
              field_id,candidate_ref,candidate_ordinal,rank,score,best_path_score,derivation_count,
              witness_truncated,evidence_refs_clay,provenance_clay
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            member_rows,
        )
        self.conn.executemany(
            """INSERT INTO clay_possibility_witnesses(
              witness_id,field_id,candidate_ref,witness_rank,path_score,path_refs_clay,
              relation_refs_clay,path_hash,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?, 'CURRENT',?)""",
            witness_rows,
        )
        return {"field_id":field_id,"candidates":len(ranked),"explored_path_states":explored,
                "truncated":truncated,"compile_ms":compile_ms,"output_hash":output_hash}

    def query(self, *, anchor_ref: str, required_facets: Mapping[str, str] | None = None,
              limit: int = 20, require_exact: bool = True,
              expected_source_epoch: int | None = None,
              expected_graph_epoch: int | None = None) -> list[tuple[str, float]]:
        epoch = self.conn.execute(
            "SELECT field_epoch,source_epoch,graph_epoch FROM v_clay_current_possibility_field_epoch"
        ).fetchone()
        if not epoch:
            raise TruncatedField("no current compiled field epoch")
        field_epoch, source_epoch, graph_epoch = map(int, epoch)
        if expected_source_epoch is not None and source_epoch != expected_source_epoch:
            raise TruncatedField(f"source epoch mismatch current={source_epoch} expected={expected_source_epoch}")
        if expected_graph_epoch is not None and graph_epoch != expected_graph_epoch:
            raise TruncatedField(f"graph epoch mismatch current={graph_epoch} expected={expected_graph_epoch}")
        row = self.conn.execute(
            "SELECT field_id,truncated FROM clay_possibility_anchor_fields WHERE field_epoch=? AND anchor_ref=? AND status='CURRENT'",
            (field_epoch,anchor_ref),
        ).fetchone()
        if not row:
            raise TruncatedField("anchor field missing")
        field_id, truncated = row
        if require_exact and truncated:
            raise TruncatedField("field path-state budget truncated; exact fallback required")

        allowed: int | None = None
        for key, value in (required_facets or {}).items():
            f = self.conn.execute(
                """SELECT encoding,membership_blob FROM clay_possibility_facets
                   WHERE field_epoch=? AND facet_key=? AND facet_value=? AND status='CURRENT'""",
                (field_epoch,str(key),str(value)),
            ).fetchone()
            if not f:
                return []
            if f[0] != "DENSE_BITSET_LE":
                raise NotImplementedError(f"encoding {f[0]}")
            bits = decode_dense_bitset(f[1])
            allowed = bits if allowed is None else allowed & bits

        out = []
        for ref, ordinal, score in self.conn.execute(
            "SELECT candidate_ref,candidate_ordinal,score FROM clay_possibility_field_members WHERE field_id=? ORDER BY rank",
            (field_id,),
        ):
            if allowed is not None and ((allowed >> ordinal) & 1) == 0:
                continue
            out.append((ref,float(score)))
            if len(out) >= limit:
                break
        return out
