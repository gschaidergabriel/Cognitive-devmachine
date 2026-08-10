from __future__ import annotations

"""Two-phase adaptive authoritative rank path V5.

V4 correctly separated semantic ordering from optional index acceleration, but still created an
index inside select() and left an already-built index alive when later economics returned to
ONLINE. V5 makes the lifecycle explicit:

  cognition/read phase: choose desired mode, NEVER mutate schema, execute correct score-before-
  LIMIT semantics immediately; force NOT INDEXED whenever online is desired.

  maintenance phase: against the same authoritative ledger epoch, build/drop the disposable
  expression index outside the cognition read. A stale maintenance plan is rejected and must be
  recomputed. Build/drop failure cannot change semantic correctness of the online path.

This controller has performance-routing authority only. StateLedger remains semantic authority.
"""

from dataclasses import dataclass
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import StaleEpoch, h
from research_entity.runtime.database_pulse_rank_index_v3 import (
    AuthoritativeRankIndexV3, INDEX_NAME, REENTRY_BOOST, SCORE_EXPR,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime, decide_compile_from_pulse_history,
)

IMPLEMENTATION_ID="PULSE_TWO_PHASE_AUTHORITATIVE_RANK_PATH_V5"
FORBIDDEN_SOURCE_DOMAINS={"pulse","pulse_control"}


@dataclass(frozen=True)
class RankLifecyclePlan:
    basis_epoch:int
    semantic_state_hash:str
    desired_mode:str
    actual_index_present:bool
    maintenance_action:str
    horizon_status:str
    horizon_reads_lower_bound:float
    compile_reason:str
    guarded_break_even_reads:float|None
    plan_hash:str
    authority:str="PERFORMANCE_MAINTENANCE_PLAN_ONLY"


@dataclass(frozen=True)
class RankMaintenanceReceipt:
    basis_epoch:int
    action:str
    status:str
    index_present_before:bool
    index_present_after:bool
    semantic_state_hash_before:str
    semantic_state_hash_after:str
    trace_root_hash_before:str
    trace_root_hash_after:str
    plan_hash:str
    authority:str="PHYSICAL_INDEX_MAINTENANCE_ONLY_NO_SEMANTIC_AUTHORITY"


@dataclass(frozen=True)
class RankSelectionV5:
    basis_epoch:int
    semantic_state_hash:str
    candidate_refs:tuple[str,...]
    focus_refs:tuple[str,...]
    candidate_scores:tuple[float,...]
    candidate_universe_count:int
    query_truncated:bool
    conflicts_present:int
    unknown_present:int
    selection_hash:str
    query_plan:tuple[str,...]
    reentry_mode:str
    physical_read_mode:str
    desired_mode:str
    maintenance_action:str
    index_present:bool
    lifecycle_plan_hash:str
    authority:str="CONTEXT_ONLY_PERFORMANCE_ROUTING_NO_EFFECT_AUTHORITY"


class AdaptiveAuthoritativeRankPathV5:
    def __init__(self,ledger):
        self.ledger=ledger; self.con=ledger.conn; self.v3=AuthoritativeRankIndexV3(ledger)

    def index_exists(self)->bool:
        return self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",(INDEX_NAME,)
        ).fetchone() is not None

    @staticmethod
    def _domains(source_domains:tuple[str,...])->tuple[str,...]:
        ds=tuple(dict.fromkeys(source_domains))
        if not ds: raise ValueError("source_domains required")
        if any(d in FORBIDDEN_SOURCE_DOMAINS for d in ds):
            raise ValueError("Pulse output/control domains cannot feed Pulse candidate selection")
        return ds

    @staticmethod
    def _domain_clause(domains:tuple[str,...])->tuple[str,list[Any]]:
        return f"domain IN ({','.join('?' for _ in domains)})",list(domains)

    def plan_lifecycle(self,*,basis_epoch:int,economics_without_horizon:CompileEconomics,
                       pulse_history:Iterable[EpochReadLifetime],**horizon_kwargs)->RankLifecyclePlan:
        if basis_epoch!=self.ledger.epoch:
            raise StaleEpoch(f"rank lifecycle basis {basis_epoch}!={self.ledger.epoch}")
        horizon,decision=decide_compile_from_pulse_history(
            economics_without_horizon,list(pulse_history),**horizon_kwargs)
        present=self.index_exists()
        desired="COMPILED_INDEX" if decision.mode=="COMPILE" else "ONLINE"
        action=("BUILD_INDEX" if desired=="COMPILED_INDEX" and not present else
                "DROP_INDEX" if desired=="ONLINE" and present else "NONE")
        body={"basis_epoch":basis_epoch,"semantic_state_hash":self.ledger.semantic_state_hash,
              "desired_mode":desired,"actual_index_present":present,"maintenance_action":action,
              "horizon_status":horizon.status,"horizon_reads_lower_bound":horizon.expected_reads_lower_bound,
              "compile_reason":decision.reason,"guarded_break_even_reads":decision.guarded_break_even_reads}
        return RankLifecyclePlan(
            basis_epoch=basis_epoch,semantic_state_hash=self.ledger.semantic_state_hash,
            desired_mode=desired,actual_index_present=present,maintenance_action=action,
            horizon_status=horizon.status,horizon_reads_lower_bound=horizon.expected_reads_lower_bound,
            compile_reason=decision.reason,guarded_break_even_reads=decision.guarded_break_even_reads,
            plan_hash=h(body))

    def apply_maintenance(self,plan:RankLifecyclePlan)->RankMaintenanceReceipt:
        if plan.basis_epoch!=self.ledger.epoch or plan.semantic_state_hash!=self.ledger.semantic_state_hash:
            raise StaleEpoch("rank maintenance plan no longer matches authoritative ledger")
        before=self.index_exists()
        state_before=self.ledger.semantic_state_hash; trace_before=self.ledger.trace_root_hash
        action=plan.maintenance_action
        status="NO_CHANGE"
        try:
            if action=="BUILD_INDEX":
                self.v3.ensure_index(); status="BUILT"
            elif action=="DROP_INDEX":
                self.v3.drop_index(); status="DROPPED"
            elif action!="NONE":
                raise ValueError(f"unsupported maintenance action: {action}")
        except Exception:
            # Semantic state is still authoritative/correct; caller may retry maintenance later.
            status="FAILED_RETRYABLE_PHYSICAL_MAINTENANCE"
        after=self.index_exists()
        state_after=self.ledger.semantic_state_hash; trace_after=self.ledger.trace_root_hash
        if (state_before,trace_before)!=(state_after,trace_after):
            raise AssertionError("physical rank-index maintenance mutated semantic/trace roots")
        return RankMaintenanceReceipt(
            basis_epoch=plan.basis_epoch,action=action,status=status,
            index_present_before=before,index_present_after=after,
            semantic_state_hash_before=state_before,semantic_state_hash_after=state_after,
            trace_root_hash_before=trace_before,trace_root_hash_after=trace_after,
            plan_hash=plan.plan_hash)

    def _rows(self,domains:tuple[str,...],limit:int,*,use_index:bool):
        clause,args=self._domain_clause(domains)
        table_hint=f"INDEXED BY {INDEX_NAME}" if use_index else "NOT INDEXED"
        sql=f"""SELECT domain,k,value_json,domain_epoch,semantic_hash,{SCORE_EXPR} AS score
                FROM state {table_hint}
                WHERE status='CURRENT' AND epistemic='KNOWN' AND {clause}
                ORDER BY {SCORE_EXPR} DESC,
                         domain COLLATE BINARY,k COLLATE BINARY,semantic_hash COLLATE BINARY
                LIMIT ?"""
        final=[*args,limit]
        plan=tuple(str(r[3]) for r in self.con.execute("EXPLAIN QUERY PLAN "+sql,final))
        return list(self.con.execute(sql,final)),plan

    def _row_by_ref(self,ref:str):
        if ":" not in ref:return None
        domain,key=ref.split(":",1)
        return self.con.execute(
            f"""SELECT domain,k,value_json,domain_epoch,semantic_hash,{SCORE_EXPR} AS score
                FROM state NOT INDEXED WHERE status='CURRENT' AND epistemic='KNOWN'
                AND domain=? AND k=?""",(domain,key)).fetchone()

    def _count(self,domains:tuple[str,...],epistemic:str)->int:
        clause,args=self._domain_clause(domains)
        return int(self.con.execute(
            f"SELECT COUNT(*) FROM state WHERE status='CURRENT' AND epistemic=? AND {clause}",
            [epistemic,*args]).fetchone()[0])

    def select(self,*,source_domains:tuple[str,...],basis_epoch:int,max_candidates:int,max_focus:int,
               economics_without_horizon:CompileEconomics,pulse_history:Iterable[EpochReadLifetime],
               reentry_mode:str="NO_REENTRY",previous_focus_refs:tuple[str,...]=(),
               shuffle_salt:str|None=None,**horizon_kwargs)->RankSelectionV5:
        if basis_epoch!=self.ledger.epoch:
            raise StaleEpoch(f"rank selection basis {basis_epoch}!={self.ledger.epoch}")
        if not 1<=max_candidates<=512:raise ValueError("max_candidates out of bounds")
        if not 1<=max_focus<=min(64,max_candidates):raise ValueError("max_focus out of bounds")
        mode=reentry_mode.upper()
        if mode not in {"TRUTHFUL","NO_REENTRY","SHUFFLED_CONTROL","PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(mode)
        domains=self._domains(source_domains)
        lifecycle=self.plan_lifecycle(basis_epoch=basis_epoch,
            economics_without_horizon=economics_without_horizon,pulse_history=pulse_history,**horizon_kwargs)
        # CRITICAL: read phase never creates/drops schema. Compiled mode is usable only if a
        # previous maintenance phase already prepared it. ONLINE always forces NOT INDEXED.
        present=self.index_exists()
        use_index=lifecycle.desired_mode=="COMPILED_INDEX" and present
        physical=("COMPILED_INDEX" if use_index else
                  "ONLINE_PENDING_COMPILE" if lifecycle.desired_mode=="COMPILED_INDEX" else
                  "ONLINE_PENDING_DECOMPILE" if present else "ONLINE")
        root_before=(self.ledger.epoch,self.ledger.semantic_state_hash,self.ledger.trace_root_hash)
        rows,query_plan=self._rows(domains,max_candidates,use_index=use_index)
        by_ref={f"{r['domain']}:{r['k']}":r for r in rows}
        targets:set[str]=set()
        if mode=="TRUTHFUL":
            allowed=set(domains)
            for ref in previous_focus_refs:
                if ":" not in ref or ref.split(":",1)[0] not in allowed:continue
                row=self._row_by_ref(ref)
                if row is not None:by_ref[ref]=row;targets.add(ref)
        elif mode=="SHUFFLED_CONTROL" and previous_focus_refs:
            salt=shuffle_salt or h({"control":"SHUFFLED","basis":basis_epoch})
            ordered=sorted(by_ref,key=lambda ref:h({"salt":salt,"ref":ref}))
            targets=set(ordered[:min(len(previous_focus_refs),len(ordered))])
        ranked=[]
        for ref,row in by_ref.items():
            score=float(row["score"])+(REENTRY_BOOST if ref in targets else 0.0)
            ranked.append((score,ref,str(row["semantic_hash"])))
        ranked.sort(key=lambda x:(-x[0],x[1],x[2])); ranked=ranked[:max_candidates]
        candidates=tuple(x[1] for x in ranked); focus=candidates[:max_focus]
        scores=tuple(round(float(x[0]),8) for x in ranked)
        universe=self._count(domains,"KNOWN"); conflicts=self._count(domains,"CONFLICT"); unknown=self._count(domains,"UNKNOWN")
        if root_before!=(self.ledger.epoch,self.ledger.semantic_state_hash,self.ledger.trace_root_hash):
            raise AssertionError("rank read phase mutated ledger roots")
        body={"implementation":IMPLEMENTATION_ID,"basis_epoch":basis_epoch,
              "semantic_state_hash":self.ledger.semantic_state_hash,"domains":list(domains),
              "candidate_refs":list(candidates),"candidate_scores":list(scores),"focus_refs":list(focus),
              "reentry_mode":mode,"physical_read_mode":physical,"desired_mode":lifecycle.desired_mode,
              "maintenance_action":lifecycle.maintenance_action,"index_present":present,
              "lifecycle_plan_hash":lifecycle.plan_hash}
        return RankSelectionV5(
            basis_epoch=basis_epoch,semantic_state_hash=self.ledger.semantic_state_hash,
            candidate_refs=candidates,focus_refs=focus,candidate_scores=scores,
            candidate_universe_count=universe,query_truncated=universe>len(candidates),
            conflicts_present=conflicts,unknown_present=unknown,selection_hash=h(body),
            query_plan=query_plan,reentry_mode=mode,physical_read_mode=physical,
            desired_mode=lifecycle.desired_mode,maintenance_action=lifecycle.maintenance_action,
            index_present=present,lifecycle_plan_hash=lifecycle.plan_hash)
