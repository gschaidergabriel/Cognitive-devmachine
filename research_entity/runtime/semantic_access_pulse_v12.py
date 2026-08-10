from __future__ import annotations

"""Clay UnifiedDB U12 segmented semantic-access pulse candidate.

U12 is a disposable access-plane candidate layered conceptually above U10/U11.
It does not replace UnifiedDB/StateLedger truth. The core idea is immutable per-seed
access segments plus an atomic generation->segment map:

  current generation -> seed map -> immutable segment -> ranked access paths

A local pulse recomputes only seeds proven to be affected, reuses immutable segments for
unaffected seeds, creates a coherent generation map, verifies it, then atomically flips
the head. If impact closure is incomplete, topology expansion is not bounded, affected
fraction is too large, or any invariant fails, the candidate falls back to full rebuild
or preserves the last-known-good head.
"""

from dataclasses import dataclass
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Callable, Sequence

SAFE_INCREMENTAL_CHANGE_CLASSES = frozenset({
    "VALUE_UPDATE",
    "STATUS_UPDATE",
    "EDGE_WEIGHT_UPDATE",
    "EDGE_REMOVE",
    "LOCAL_REWRITE",
})

@dataclass(frozen=True)
class AccessPath:
    target_record_id: str
    target_logical_id: str
    path_rank: int
    hop_count: int
    path_weight: float
    authority_rank: float = 0.0
    path_clay: str = "{}"
    dependencies: tuple[str, ...] = ()

@dataclass(frozen=True)
class PulsePlan:
    event_id: str
    change_class: str
    changed_logical_ids: tuple[str, ...]
    impact_seed_ids: tuple[str, ...]
    impact_complete: bool
    to_source_epoch: int
    to_graph_epoch: int

@dataclass(frozen=True)
class PulseReceipt:
    event_id: str
    mode: str
    generation_id: str
    previous_generation_id: str | None
    from_source_epoch: int | None
    from_graph_epoch: int | None
    to_source_epoch: int
    to_graph_epoch: int
    affected_seed_count: int
    total_seed_count: int
    affected_fraction: float
    reused_segment_count: int
    new_segment_count: int
    new_path_count: int
    generation_map_rows: int
    publish_latency_ns: int
    head_hash: str
    authority: str = "NON_AUTHORITATIVE_REBUILDABLE_ACCESS_PROJECTION"

class PulseInvariantError(RuntimeError):
    pass

class StalePulse(RuntimeError):
    pass

def _stable(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _digest(value) -> str:
    return hashlib.sha256(_stable(value).encode()).hexdigest()

class SegmentedPulseProjection:
    """SQLite reference implementation for coherent copy-on-write access generations."""

    def __init__(self, path: str = ":memory:"):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys=ON")
        schema_path = Path(__file__).with_name("RAE_UNIFIEDDB_V12_SEGMENTED_PULSE_GENERATIONS.sql")
        self.con.executescript(schema_path.read_text(encoding="utf-8"))

    def close(self) -> None:
        self.con.close()

    def _head(self):
        return self.con.execute("""
          SELECT h.generation_id,h.source_epoch,h.graph_epoch,h.generation_hash
          FROM access_head h JOIN access_generation g ON g.generation_id=h.generation_id
          WHERE h.head_key='CURRENT' AND g.status='CURRENT'
            AND g.source_epoch=h.source_epoch AND g.graph_epoch=h.graph_epoch
            AND g.generation_hash=h.generation_hash
        """).fetchone()

    @staticmethod
    def _validate_seed_paths(seed_id: str, paths: Sequence[AccessPath]) -> list[AccessPath]:
        paths=list(paths)
        if not seed_id or not paths:
            raise PulseInvariantError("each mapped seed requires at least one path")
        seen=set()
        ranks=set()
        for p in paths:
            if not p.target_record_id or not p.target_logical_id:
                raise PulseInvariantError("path identity is required")
            if p.path_rank <= 0 or p.hop_count < 0:
                raise PulseInvariantError("invalid path rank/hop")
            if p.target_record_id in seen:
                raise PulseInvariantError("duplicate target record in seed segment")
            seen.add(p.target_record_id)
            ranks.add(p.path_rank)
            deps=set(p.dependencies)
            if seed_id not in deps or p.target_logical_id not in deps:
                raise PulseInvariantError("dependencies must include seed and target logical ids")
        if min(ranks) != 1:
            raise PulseInvariantError("seed segment lacks rank 1")
        return sorted(paths,key=lambda p:(p.path_rank,-p.path_weight,-p.authority_rank,p.target_record_id))

    def _ensure_segment(self, seed_id: str, paths: Sequence[AccessPath]) -> tuple[str,bool,int]:
        paths=self._validate_seed_paths(seed_id,paths)
        body=[
            [p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,
             round(p.path_weight,12),round(p.authority_rank,12),p.path_clay,sorted(set(p.dependencies))]
            for p in paths
        ]
        segment_hash=_digest({"seed_id":seed_id,"paths":body})
        segment_id="seg-"+segment_hash[:24]
        exists=self.con.execute("SELECT 1 FROM access_segment WHERE segment_id=?",(segment_id,)).fetchone()
        if exists:
            return segment_id,False,len(paths)
        self.con.execute("INSERT INTO access_segment VALUES(?,?,?,?,?)",
                         (segment_id,seed_id,segment_hash,len(paths),time.time_ns()))
        self.con.executemany("INSERT INTO access_segment_path VALUES(?,?,?,?,?,?,?,?)",[
            (segment_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,p.path_weight,p.authority_rank,p.path_clay)
            for p in paths
        ])
        deps=sorted({d for p in paths for d in p.dependencies})
        self.con.executemany("INSERT INTO access_segment_dependency VALUES(?,?)",
                             [(segment_id,d) for d in deps])
        actual=self.con.execute(
            "SELECT count(*) FROM access_segment_path WHERE segment_id=?",(segment_id,)
        ).fetchone()[0]
        if actual != len(paths):
            raise PulseInvariantError("segment path count mismatch")
        return segment_id,True,len(paths)

    @staticmethod
    def _generation_hash(source_epoch: int, graph_epoch: int, mapping: Sequence[tuple[str,str]]) -> str:
        return _digest({
            "source_epoch":source_epoch,
            "graph_epoch":graph_epoch,
            "mapping":sorted(mapping),
        })

    def _stage_publish_generation(
        self,
        *,
        event_id: str,
        source_epoch: int,
        graph_epoch: int,
        mapping: Sequence[tuple[str,str]],
        previous_generation_id: str | None,
        receipt_meta: dict,
    ) -> PulseReceipt:
        started=time.perf_counter_ns()
        mapping=sorted(mapping)
        if not mapping:
            raise PulseInvariantError("empty generation cannot replace last-known-good")
        seeds=[s for s,_ in mapping]
        if len(seeds) != len(set(seeds)):
            raise PulseInvariantError("duplicate seed in generation mapping")
        generation_hash=self._generation_hash(source_epoch,graph_epoch,mapping)
        generation_id="gen-"+_digest({"event":event_id,"hash":generation_hash})[:24]
        now=time.time_ns()
        self.con.execute("INSERT INTO access_generation VALUES(?,?,?,?,?,'STAGING',?,NULL)",
                         (generation_id,source_epoch,graph_epoch,generation_hash,len(mapping),now))
        self.con.executemany("INSERT INTO access_generation_seed VALUES(?,?,?)",
                             [(generation_id,s,seg) for s,seg in mapping])
        actual=self.con.execute("""
          SELECT count(*),count(DISTINCT gs.seed_id),
                 sum(CASE WHEN s.seed_id=gs.seed_id AND s.path_count>0 THEN 0 ELSE 1 END)
          FROM access_generation_seed gs
          JOIN access_segment s ON s.segment_id=gs.segment_id
          WHERE gs.generation_id=?
        """,(generation_id,)).fetchone()
        if actual[0] != len(mapping) or actual[1] != len(mapping) or int(actual[2] or 0) != 0:
            self.con.execute("UPDATE access_generation SET status='QUARANTINED' WHERE generation_id=?",(generation_id,))
            raise PulseInvariantError("generation verification failed")
        self.con.execute("UPDATE access_generation SET status='VERIFIED' WHERE generation_id=?",(generation_id,))
        if previous_generation_id:
            self.con.execute(
                "UPDATE access_generation SET status='SUPERSEDED' WHERE generation_id=? AND status='CURRENT'",
                (previous_generation_id,)
            )
        self.con.execute("UPDATE access_generation SET status='CURRENT',published_ns=? WHERE generation_id=?",
                         (now,generation_id))
        self.con.execute("""
          INSERT INTO access_head VALUES('CURRENT',?,?,?,?,?)
          ON CONFLICT(head_key) DO UPDATE SET
            generation_id=excluded.generation_id,
            source_epoch=excluded.source_epoch,
            graph_epoch=excluded.graph_epoch,
            generation_hash=excluded.generation_hash,
            published_ns=excluded.published_ns
        """,(generation_id,source_epoch,graph_epoch,generation_hash,now))
        head=self._head()
        if not head or head["generation_id"] != generation_id:
            raise PulseInvariantError("head publication did not resolve to new coherent generation")
        # Generation hash commits to the complete seed->immutable-segment map. A global
        # path rescan here would destroy locality; deep snapshot equivalence is a slower audit.
        head_hash=generation_hash
        receipt=PulseReceipt(
            event_id=event_id,
            mode=str(receipt_meta["mode"]),
            generation_id=generation_id,
            previous_generation_id=previous_generation_id,
            from_source_epoch=receipt_meta.get("from_source_epoch"),
            from_graph_epoch=receipt_meta.get("from_graph_epoch"),
            to_source_epoch=source_epoch,
            to_graph_epoch=graph_epoch,
            affected_seed_count=int(receipt_meta.get("affected_seed_count",len(mapping))),
            total_seed_count=len(mapping),
            affected_fraction=float(receipt_meta.get("affected_fraction",1.0)),
            reused_segment_count=int(receipt_meta.get("reused_segment_count",0)),
            new_segment_count=int(receipt_meta.get("new_segment_count",len(mapping))),
            new_path_count=int(receipt_meta.get("new_path_count",0)),
            generation_map_rows=len(mapping),
            publish_latency_ns=time.perf_counter_ns()-started,
            head_hash=head_hash,
        )
        self.con.execute("INSERT INTO access_pulse_receipt VALUES(?,?,?,?)",
                         (event_id,generation_id,_stable(receipt.__dict__),time.time_ns()))
        return receipt

    def bootstrap(
        self,
        *,
        event_id: str,
        source_epoch: int,
        graph_epoch: int,
        seeds: Sequence[str],
        recompute_seed: Callable[[str], Sequence[AccessPath]],
    ) -> PulseReceipt:
        if self._head():
            raise PulseInvariantError("bootstrap requires empty projection")
        started=time.perf_counter_ns()
        with self.con:
            mapping=[]
            new_segments=0
            new_paths=0
            for seed in sorted(set(seeds)):
                seg,created,count=self._ensure_segment(seed,recompute_seed(seed))
                mapping.append((seed,seg))
                new_segments += int(created)
                new_paths += count if created else 0
            receipt=self._stage_publish_generation(
                event_id=event_id,source_epoch=source_epoch,graph_epoch=graph_epoch,
                mapping=mapping,previous_generation_id=None,
                receipt_meta={
                    "mode":"FULL_BOOTSTRAP","affected_seed_count":len(mapping),"affected_fraction":1.0,
                    "new_segment_count":new_segments,"new_path_count":new_paths,
                }
            )
        return PulseReceipt(**{**receipt.__dict__,"publish_latency_ns":time.perf_counter_ns()-started})

    def _current_mapping(self, generation_id: str) -> dict[str,str]:
        return {r["seed_id"]:r["segment_id"] for r in self.con.execute(
            "SELECT seed_id,segment_id FROM access_generation_seed WHERE generation_id=?",(generation_id,)
        )}

    def _observed_affected(self, generation_id: str, changed: Sequence[str]) -> set[str]:
        changed=sorted(set(changed))
        if not changed:
            return set()
        marks=",".join("?" for _ in changed)
        return {r[0] for r in self.con.execute(f"""
          SELECT DISTINCT gs.seed_id
          FROM access_generation_seed gs
          JOIN access_segment_dependency d ON d.segment_id=gs.segment_id
          WHERE gs.generation_id=? AND d.dependency_logical_id IN ({marks})
        """,(generation_id,*changed))}

    def apply_pulse(
        self,
        plan: PulsePlan,
        *,
        recompute_seed: Callable[[str], Sequence[AccessPath]],
        recompute_all_seeds: Callable[[], Sequence[str]],
        incremental_fraction_limit: float = 0.25,
    ) -> PulseReceipt:
        head=self._head()
        if not head:
            raise PulseInvariantError("pulse requires current generation")
        if plan.to_source_epoch < head["source_epoch"] or plan.to_graph_epoch < head["graph_epoch"]:
            raise StalePulse("pulse epoch regressed")
        if plan.to_source_epoch == head["source_epoch"] and plan.to_graph_epoch == head["graph_epoch"]:
            raise StalePulse("pulse must advance source or graph epoch")
        changed=sorted(set(plan.changed_logical_ids))
        if not changed:
            raise PulseInvariantError("pulse requires changed logical ids")
        old_gen=head["generation_id"]
        old_map=self._current_mapping(old_gen)
        observed=self._observed_affected(old_gen,changed)
        declared=set(plan.impact_seed_ids)
        affected=observed | declared
        complete=(
            plan.impact_complete
            and plan.change_class in SAFE_INCREMENTAL_CHANGE_CLASSES
            and declared.issubset(old_map)
        )
        fraction=len(affected)/max(1,len(old_map))
        use_incremental=complete and fraction <= incremental_fraction_limit

        started=time.perf_counter_ns()
        try:
            self.con.execute("BEGIN IMMEDIATE")
            if use_incremental:
                mapping=dict(old_map)
                new_segments=0
                new_paths=0
                for seed in sorted(affected):
                    seg,created,count=self._ensure_segment(seed,recompute_seed(seed))
                    mapping[seed]=seg
                    new_segments += int(created)
                    new_paths += count if created else 0
                mode="SEGMENTED_INCREMENTAL_PULSE"
                reused=sum(1 for seed,seg in mapping.items() if old_map.get(seed)==seg)
            else:
                seeds=sorted(set(recompute_all_seeds()))
                if not seeds:
                    raise PulseInvariantError("full fallback returned no seeds")
                mapping={}
                new_segments=0
                new_paths=0
                for seed in seeds:
                    seg,created,count=self._ensure_segment(seed,recompute_seed(seed))
                    mapping[seed]=seg
                    new_segments += int(created)
                    new_paths += count if created else 0
                mode="FULL_FALLBACK"
                reused=sum(1 for seed,seg in mapping.items() if old_map.get(seed)==seg)
            receipt=self._stage_publish_generation(
                event_id=plan.event_id,source_epoch=plan.to_source_epoch,graph_epoch=plan.to_graph_epoch,
                mapping=list(mapping.items()),previous_generation_id=old_gen,
                receipt_meta={
                    "mode":mode,
                    "from_source_epoch":head["source_epoch"],"from_graph_epoch":head["graph_epoch"],
                    "affected_seed_count":len(affected),"affected_fraction":fraction,
                    "reused_segment_count":reused,"new_segment_count":new_segments,"new_path_count":new_paths,
                }
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise
        return PulseReceipt(**{**receipt.__dict__,"publish_latency_ns":time.perf_counter_ns()-started})

    def query(self, seed_id: str, limit: int = 20) -> tuple[str,...]:
        head=self._head()
        if not head:
            return ()
        return tuple(r[0] for r in self.con.execute("""
          SELECT p.target_record_id
          FROM access_generation_seed gs
          JOIN access_segment_path p ON p.segment_id=gs.segment_id
          WHERE gs.generation_id=? AND gs.seed_id=?
          ORDER BY p.path_rank,p.path_weight DESC,p.authority_rank DESC,p.target_record_id
          LIMIT ?
        """,(head["generation_id"],seed_id,limit)))

    def snapshot(self) -> list[tuple]:
        head=self._head()
        if not head:
            return []
        return [tuple(r) for r in self.con.execute("""
          SELECT gs.seed_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,
                 round(p.path_weight,12),round(p.authority_rank,12),p.path_clay
          FROM access_generation_seed gs
          JOIN access_segment_path p ON p.segment_id=gs.segment_id
          WHERE gs.generation_id=?
          ORDER BY gs.seed_id,p.path_rank,p.target_record_id
        """,(head["generation_id"],))]

    def head_basis(self) -> tuple[int,int,str] | None:
        h=self._head()
        return None if not h else (h["source_epoch"],h["graph_epoch"],h["generation_id"])

    def storage_counts(self) -> dict[str,int]:
        return {
            "segments":self.con.execute("SELECT count(*) FROM access_segment").fetchone()[0],
            "segment_paths":self.con.execute("SELECT count(*) FROM access_segment_path").fetchone()[0],
            "generation_maps":self.con.execute("SELECT count(*) FROM access_generation_seed").fetchone()[0],
            "generations":self.con.execute("SELECT count(*) FROM access_generation").fetchone()[0],
        }
