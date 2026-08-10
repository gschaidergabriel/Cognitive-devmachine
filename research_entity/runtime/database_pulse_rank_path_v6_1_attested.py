from __future__ import annotations

"""Stacked Pulse rank V6.1: runtime-attested expression-index admission.

Parent V6 owns provenance-complete BUILD/DROP audit. V6.1 adds a distinct, rebuildable
attestation plane for the physical accelerator: canonical sqlite_schema definition, rootpage,
SQLite source/runtime fingerprint, and the latest parent V6 material receipt identity.

An index that merely has the expected name is never enough for compiled cognition. Missing or
drifted attestation routes immediately through the correct NOT INDEXED query and produces a
bounded maintenance obligation. REFRESH_ATTESTATION uses SQLite REINDEX and the attestation
receipt in one transaction. Definition/parent drift is repaired as parent-V6 DROP -> BUILD
followed by attestation; interruption at any boundary remains safe because un/attested
acceleration is never semantic truth or effect authority.
"""

from dataclasses import dataclass
import hashlib
import json
import platform
import sqlite3
import sys
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import StaleEpoch, h
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME, REENTRY_BOOST, SCORE_EXPR
from research_entity.runtime.database_pulse_rank_path_v5 import RankLifecyclePlan, RankPhysicalStateStale
from research_entity.runtime.database_pulse_rank_path_v6 import AdaptiveAuthoritativeRankPathV6, NATIVE_PROVENANCE_STATUS
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime, decide_compile_from_pulse_history

IMPLEMENTATION_ID="PULSE_PROVENANCE_PLUS_ATTESTED_RANK_PATH_V6_1"
ATTESTATION_TABLE="pulse_rank_index_attestations_v6_1"
AUTHORITY="PHYSICAL_ACCELERATOR_ATTESTATION_ONLY_NO_SEMANTIC_OR_EFFECT_AUTHORITY"

def _stable(v:Any)->str:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def _sha(s:str)->str:return hashlib.sha256(s.encode()).hexdigest()
def _norm(sql:str|None)->str|None:return None if sql is None else " ".join(sql.strip().rstrip(";").split())
CANONICAL_INDEX_SQL=_norm(f"""CREATE INDEX {INDEX_NAME}
 ON state({SCORE_EXPR} DESC,domain COLLATE BINARY,k COLLATE BINARY,semantic_hash COLLATE BINARY)
 WHERE status='CURRENT' AND epistemic='KNOWN'""") or ""
CANONICAL_INDEX_SQL_HASH=_sha(CANONICAL_INDEX_SQL)

@dataclass(frozen=True)
class RankIndexAttestationIdentity:
    present:bool; state:str; sql_hash:str|None; rootpage:int|None; runtime_env_hash:str
    latest_v6_receipt_id:str|None; attestation_receipt_id:str|None
    authority:str="PHYSICAL_ACCELERATOR_IDENTITY_ONLY"

@dataclass(frozen=True)
class RankLifecyclePlanV61:
    basis_epoch:int; semantic_state_hash:str; desired_mode:str; maintenance_action:str; physical_state:str
    actual_index_present:bool; index_sql_hash:str|None; index_rootpage:int|None; runtime_env_hash:str
    actor:str; policy_provenance_ref:str; policy_decision_hash:str; horizon_status:str
    horizon_reads_lower_bound:float; compile_reason:str; guarded_break_even_reads:float|None; plan_hash:str
    authority:str="PERFORMANCE_MAINTENANCE_PLAN_ONLY"

@dataclass(frozen=True)
class RankMaintenanceReceiptV61:
    basis_epoch:int; action:str; status:str; physical_state_before:str; physical_state_after:str
    parent_v6_receipt_ids:tuple[str,...]; attestation_receipt_id:str|None; actor:str
    policy_provenance_ref:str; policy_decision_hash:str; plan_hash:str; persisted:bool
    authority:str=AUTHORITY

@dataclass(frozen=True)
class RankSelectionV61:
    basis_epoch:int; semantic_state_hash:str; candidate_refs:tuple[str,...]; focus_refs:tuple[str,...]
    candidate_scores:tuple[float,...]; candidate_universe_count:int; query_truncated:bool
    conflicts_present:int; unknown_present:int; selection_hash:str; query_plan:tuple[str,...]
    reentry_mode:str; physical_read_mode:str; desired_mode:str; maintenance_action:str
    physical_state:str; lifecycle_plan_hash:str
    authority:str="CONTEXT_ONLY_PERFORMANCE_ROUTING_NO_EFFECT_AUTHORITY"

class AdaptiveAuthoritativeRankPathV61Attested(AdaptiveAuthoritativeRankPathV6):
    def _runtime_payload(self)->dict[str,str]:
        return {"sqlite_version":sqlite3.sqlite_version,
                "sqlite_source_id":str(self.con.execute("select sqlite_source_id()").fetchone()[0]),
                "platform_system":platform.system(),"platform_release":platform.release(),
                "platform_machine":platform.machine(),"byteorder":sys.byteorder}

    def _runtime(self)->tuple[str,str]:
        raw=_stable(self._runtime_payload()); return _sha(raw),raw

    def _raw_index(self)->tuple[bool,str|None,int|None]:
        row=self.con.execute("select sql,rootpage from sqlite_schema where type='index' and name=?",(INDEX_NAME,)).fetchone()
        return (False,None,None) if row is None else (True,_sha(_norm(str(row[0])) or ""),int(row[1]))

    def _attestation_table_exists(self)->bool:
        return self.con.execute("select 1 from sqlite_schema where type='table' and name=?",(ATTESTATION_TABLE,)).fetchone() is not None

    def _create_attestation_table_no_commit(self)->None:
        self.con.execute(f"""create table if not exists {ATTESTATION_TABLE}(
            receipt_id text primary key,basis_epoch integer not null,semantic_state_hash text not null,
            index_sql_hash text not null,index_rootpage integer not null,runtime_env_hash text not null,
            runtime_env_json text not null,v6_source_receipt_id text,actor text not null,
            policy_provenance_ref text not null,policy_decision_hash text not null,created_at text not null,
            authority text not null)""")

    def _latest_attestation(self)->dict[str,Any]|None:
        if not self._attestation_table_exists():return None
        row=self.con.execute(f"select * from {ATTESTATION_TABLE} order by rowid desc limit 1").fetchone()
        return dict(row) if row is not None else None

    def _latest_v6_marker(self)->tuple[str|None,str|None,str|None]:
        if not self._v6_log_exists():return None,None,None
        row=self.con.execute("select receipt_id,status,provenance_status from pulse_rank_maintenance_receipts_v6 order by rowid desc limit 1").fetchone()
        return (None,None,None) if row is None else (str(row["receipt_id"]),str(row["status"]),str(row["provenance_status"]))

    def _latest_native_v6_material_receipt_id(self)->str|None:
        rid,status,prov=self._latest_v6_marker()
        return rid if prov==NATIVE_PROVENANCE_STATUS and status in {"BUILT","REBUILT"} else None

    def physical_identity(self)->RankIndexAttestationIdentity:
        present,sql_hash,rootpage=self._raw_index(); env_hash,_=self._runtime()
        marker_id,marker_status,marker_prov=self._latest_v6_marker()
        latest_v6=marker_id if marker_prov==NATIVE_PROVENANCE_STATUS and marker_status in {"BUILT","REBUILT"} else None
        att=self._latest_attestation(); att_id=str(att["receipt_id"]) if att else None
        if not present:return RankIndexAttestationIdentity(False,"ABSENT",None,None,env_hash,latest_v6,att_id)
        if sql_hash!=CANONICAL_INDEX_SQL_HASH:return RankIndexAttestationIdentity(True,"DEFINITION_DRIFT",sql_hash,rootpage,env_hash,latest_v6,att_id)
        if not att:return RankIndexAttestationIdentity(True,"UNATTESTED",sql_hash,rootpage,env_hash,latest_v6,None)
        if str(att["runtime_env_hash"])!=env_hash:return RankIndexAttestationIdentity(True,"RUNTIME_DRIFT",sql_hash,rootpage,env_hash,latest_v6,att_id)
        if str(att["index_sql_hash"])!=sql_hash or int(att["index_rootpage"])!=int(rootpage):
            return RankIndexAttestationIdentity(True,"PHYSICAL_DRIFT",sql_hash,rootpage,env_hash,latest_v6,att_id)
        att_v6=att["v6_source_receipt_id"]
        if marker_prov==NATIVE_PROVENANCE_STATUS and marker_status=="DROPPED":
            return RankIndexAttestationIdentity(True,"PARENT_V6_DRIFT",sql_hash,rootpage,env_hash,None,att_id)
        if latest_v6 is not None and str(att_v6 or "")!=latest_v6:
            return RankIndexAttestationIdentity(True,"PARENT_V6_DRIFT",sql_hash,rootpage,env_hash,latest_v6,att_id)
        return RankIndexAttestationIdentity(True,"ATTESTED",sql_hash,rootpage,env_hash,latest_v6,att_id)

    def plan_lifecycle(self,*,basis_epoch:int,economics_without_horizon:CompileEconomics,pulse_history:Iterable[EpochReadLifetime],
                       actor:str,policy_provenance_ref:str,policy_decision_hash:str,**horizon_kwargs)->RankLifecyclePlanV61:
        actor,policy_provenance_ref,policy_decision_hash=self._native_provenance(
            actor=actor,policy_provenance_ref=policy_provenance_ref,policy_decision_hash=policy_decision_hash)
        if basis_epoch!=self.ledger.epoch:raise StaleEpoch(f"rank lifecycle basis {basis_epoch}!={self.ledger.epoch}")
        horizon,decision=decide_compile_from_pulse_history(economics_without_horizon,list(pulse_history),**horizon_kwargs)
        physical=self.physical_identity(); desired="COMPILED_INDEX" if decision.mode=="COMPILE" else "ONLINE"
        if desired=="ONLINE":action="DROP_INDEX" if physical.present else "NONE"
        elif not physical.present:action="BUILD_INDEX"
        elif physical.state=="ATTESTED":action="NONE"
        elif physical.state in {"DEFINITION_DRIFT","PARENT_V6_DRIFT"}:action="REBUILD_INDEX"
        else:action="REFRESH_ATTESTATION"
        body={"implementation":IMPLEMENTATION_ID,"basis_epoch":basis_epoch,"semantic_state_hash":self.ledger.semantic_state_hash,
              "desired_mode":desired,"maintenance_action":action,"physical_state":physical.state,"actual_index_present":physical.present,
              "index_sql_hash":physical.sql_hash,"index_rootpage":physical.rootpage,"runtime_env_hash":physical.runtime_env_hash,
              "actor":actor,"policy_provenance_ref":policy_provenance_ref,"policy_decision_hash":policy_decision_hash,
              "horizon_status":horizon.status,"horizon_reads_lower_bound":horizon.expected_reads_lower_bound,
              "compile_reason":decision.reason,"guarded_break_even_reads":decision.guarded_break_even_reads}
        return RankLifecyclePlanV61(basis_epoch,self.ledger.semantic_state_hash,desired,action,physical.state,physical.present,
            physical.sql_hash,physical.rootpage,physical.runtime_env_hash,actor,policy_provenance_ref,policy_decision_hash,
            horizon.status,horizon.expected_reads_lower_bound,decision.reason,decision.guarded_break_even_reads,h(body))

    def _parent_plan(self,plan:RankLifecyclePlanV61,action:str,present:bool)->RankLifecyclePlan:
        return RankLifecyclePlan(plan.basis_epoch,plan.semantic_state_hash,"COMPILED_INDEX" if action=="BUILD_INDEX" else "ONLINE",
            present,action,plan.horizon_status,plan.horizon_reads_lower_bound,f"V6_1:{plan.compile_reason}:{action}",
            plan.guarded_break_even_reads,h({"v6_1_parent":plan.plan_hash,"action":action,"present":present}))

    def _insert_attestation_no_commit(self,values:dict[str,Any])->None:
        cols=list(values); marks=','.join('?' for _ in cols)
        self.con.execute(f"insert into {ATTESTATION_TABLE}({','.join(cols)}) values({marks})",[values[c] for c in cols])

    def refresh_attestation(self,plan:RankLifecyclePlanV61,*,v6_source_receipt_id:str|None=None)->str:
        if plan.basis_epoch!=self.ledger.epoch or plan.semantic_state_hash!=self.ledger.semantic_state_hash:raise StaleEpoch("attestation basis stale")
        before=self.physical_identity()
        if not before.present or before.sql_hash!=CANONICAL_INDEX_SQL_HASH:raise RankPhysicalStateStale("refresh requires canonical index")
        roots=(self.ledger.semantic_state_hash,self.ledger.trace_root_hash)
        try:
            self.con.execute("begin immediate")
            present,sql_hash,rootpage=self._raw_index()
            if not present or sql_hash!=CANONICAL_INDEX_SQL_HASH:raise RankPhysicalStateStale("index changed before REINDEX")
            if plan.basis_epoch!=self.ledger.epoch or plan.semantic_state_hash!=self.ledger.semantic_state_hash:raise StaleEpoch("basis changed before REINDEX")
            self.con.execute(f"REINDEX {INDEX_NAME}")
            present,sql_hash,rootpage=self._raw_index()
            if not present or sql_hash!=CANONICAL_INDEX_SQL_HASH:raise AssertionError("REINDEX lost canonical index")
            self._create_attestation_table_no_commit(); env_hash,env_json=self._runtime()
            source=v6_source_receipt_id if v6_source_receipt_id is not None else self._latest_native_v6_material_receipt_id()
            body={"basis_epoch":plan.basis_epoch,"semantic_state_hash":plan.semantic_state_hash,"index_sql_hash":sql_hash,
                  "index_rootpage":rootpage,"runtime_env_hash":env_hash,"v6_source_receipt_id":source,"actor":plan.actor,
                  "policy_provenance_ref":plan.policy_provenance_ref,"policy_decision_hash":plan.policy_decision_hash,"authority":AUTHORITY}
            rid=h(body)
            self._insert_attestation_no_commit({"receipt_id":rid,"basis_epoch":plan.basis_epoch,"semantic_state_hash":plan.semantic_state_hash,
                "index_sql_hash":sql_hash,"index_rootpage":rootpage,"runtime_env_hash":env_hash,"runtime_env_json":env_json,
                "v6_source_receipt_id":source,"actor":plan.actor,"policy_provenance_ref":plan.policy_provenance_ref,
                "policy_decision_hash":plan.policy_decision_hash,"created_at":self.con.execute("select strftime('%Y-%m-%dT%H:%M:%fZ','now')").fetchone()[0],
                "authority":AUTHORITY})
            if roots!=(self.ledger.semantic_state_hash,self.ledger.trace_root_hash):raise AssertionError("attestation mutated semantic roots")
            self.con.commit(); return rid
        except Exception:self.con.rollback();raise

    def apply_maintenance(self,plan:RankLifecyclePlanV61)->RankMaintenanceReceiptV61:
        if plan.basis_epoch!=self.ledger.epoch or plan.semantic_state_hash!=self.ledger.semantic_state_hash:raise StaleEpoch("V6.1 plan stale")
        before=self.physical_identity(); action=plan.maintenance_action; parent_ids=[]; att_id=None
        if (before.present,before.state,before.sql_hash,before.rootpage,before.runtime_env_hash)!=(plan.actual_index_present,plan.physical_state,plan.index_sql_hash,plan.index_rootpage,plan.runtime_env_hash):
            raise RankPhysicalStateStale("V6.1 physical precondition changed")
        if action=="NONE":return RankMaintenanceReceiptV61(plan.basis_epoch,action,"NO_CHANGE",before.state,before.state,(),before.attestation_receipt_id,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,False)
        if action=="DROP_INDEX":
            r=super().apply_maintenance(self._parent_plan(plan,"DROP_INDEX",True),actor=plan.actor,policy_provenance_ref=plan.policy_provenance_ref,policy_decision_hash=plan.policy_decision_hash)
            if r.receipt_id:parent_ids.append(r.receipt_id)
            after=self.physical_identity(); return RankMaintenanceReceiptV61(plan.basis_epoch,action,"DROPPED" if r.status=="DROPPED" else r.status,before.state,after.state,tuple(parent_ids),None,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,r.persisted)
        if action=="REBUILD_INDEX":
            drop=super().apply_maintenance(self._parent_plan(plan,"DROP_INDEX",True),actor=plan.actor,policy_provenance_ref=plan.policy_provenance_ref,policy_decision_hash=plan.policy_decision_hash)
            if drop.status!="DROPPED":
                after=self.physical_identity(); return RankMaintenanceReceiptV61(plan.basis_epoch,action,"REBUILD_DROP_FAILED_SAFE",before.state,after.state,tuple(x for x in (drop.receipt_id,) if x),None,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,drop.persisted)
            if drop.receipt_id:parent_ids.append(drop.receipt_id)
            build=super().apply_maintenance(self._parent_plan(plan,"BUILD_INDEX",False),actor=plan.actor,policy_provenance_ref=plan.policy_provenance_ref,policy_decision_hash=plan.policy_decision_hash)
            if build.receipt_id:parent_ids.append(build.receipt_id)
            if build.status!="BUILT":
                after=self.physical_identity(); return RankMaintenanceReceiptV61(plan.basis_epoch,action,"REBUILD_BUILD_FAILED_SAFE",before.state,after.state,tuple(parent_ids),None,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,build.persisted)
            att_id=self.refresh_attestation(plan,v6_source_receipt_id=build.receipt_id); after=self.physical_identity()
            return RankMaintenanceReceiptV61(plan.basis_epoch,action,"REBUILT_ATTESTED" if after.state=="ATTESTED" else "REBUILT_UNATTESTED_SAFE",before.state,after.state,tuple(parent_ids),att_id,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,after.state=="ATTESTED")
        if action=="BUILD_INDEX":
            build=super().apply_maintenance(self._parent_plan(plan,"BUILD_INDEX",False),actor=plan.actor,policy_provenance_ref=plan.policy_provenance_ref,policy_decision_hash=plan.policy_decision_hash)
            if build.receipt_id:parent_ids.append(build.receipt_id)
            if build.status!="BUILT":
                after=self.physical_identity(); return RankMaintenanceReceiptV61(plan.basis_epoch,action,build.status,before.state,after.state,tuple(parent_ids),None,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,False)
            att_id=self.refresh_attestation(plan,v6_source_receipt_id=build.receipt_id)
        elif action=="REFRESH_ATTESTATION":att_id=self.refresh_attestation(plan)
        else:raise ValueError(action)
        after=self.physical_identity(); return RankMaintenanceReceiptV61(plan.basis_epoch,action,"ATTESTED" if after.state=="ATTESTED" else "UNATTESTED_SAFE_FALLBACK",before.state,after.state,tuple(parent_ids),att_id,plan.actor,plan.policy_provenance_ref,plan.policy_decision_hash,plan.plan_hash,after.state=="ATTESTED")

    def select(self,*,source_domains:tuple[str,...],basis_epoch:int,max_candidates:int,max_focus:int,economics_without_horizon:CompileEconomics,
               pulse_history:Iterable[EpochReadLifetime],actor:str,policy_provenance_ref:str,policy_decision_hash:str,reentry_mode:str="NO_REENTRY",
               previous_focus_refs:tuple[str,...]=(),shuffle_salt:str|None=None,**horizon_kwargs)->RankSelectionV61:
        if basis_epoch!=self.ledger.epoch:raise StaleEpoch(f"rank basis {basis_epoch}!={self.ledger.epoch}")
        if not 1<=max_candidates<=512 or not 1<=max_focus<=min(64,max_candidates):raise ValueError("candidate/focus bounds")
        mode=reentry_mode.upper()
        if mode not in {"TRUTHFUL","NO_REENTRY","SHUFFLED_CONTROL","PROVENANCE_BROKEN_CONTROL"}:raise ValueError(mode)
        domains=self._domains(source_domains)
        plan=self.plan_lifecycle(basis_epoch=basis_epoch,economics_without_horizon=economics_without_horizon,pulse_history=pulse_history,
            actor=actor,policy_provenance_ref=policy_provenance_ref,policy_decision_hash=policy_decision_hash,**horizon_kwargs)
        physical=self.physical_identity(); use_index=plan.desired_mode=="COMPILED_INDEX" and physical.state=="ATTESTED"
        read_mode=("COMPILED_ATTESTED_INDEX" if use_index else "ONLINE_PENDING_COMPILE" if plan.desired_mode=="COMPILED_INDEX" and not physical.present
                   else "ONLINE_PENDING_REBUILD" if plan.maintenance_action=="REBUILD_INDEX" else "ONLINE_PENDING_ATTESTATION" if plan.desired_mode=="COMPILED_INDEX"
                   else "ONLINE_PENDING_DECOMPILE" if physical.present else "ONLINE")
        roots=(self.ledger.epoch,self.ledger.semantic_state_hash,self.ledger.trace_root_hash)
        rows,qplan=self._rows(domains,max_candidates,use_index=use_index); by_ref={f"{r['domain']}:{r['k']}":r for r in rows}; targets=set()
        if mode=="TRUTHFUL":
            allowed=set(domains)
            for ref in previous_focus_refs:
                if ":" not in ref or ref.split(":",1)[0] not in allowed:continue
                row=self._row_by_ref(ref)
                if row is not None:by_ref[ref]=row;targets.add(ref)
        elif mode=="SHUFFLED_CONTROL" and previous_focus_refs:
            salt=shuffle_salt or h({"control":"SHUFFLED","basis":basis_epoch}); ordered=sorted(by_ref,key=lambda ref:h({"salt":salt,"ref":ref})); targets=set(ordered[:min(len(previous_focus_refs),len(ordered))])
        ranked=[]
        for ref,row in by_ref.items():ranked.append((float(row["score"])+(REENTRY_BOOST if ref in targets else 0.0),ref,str(row["semantic_hash"])))
        ranked.sort(key=lambda x:(-x[0],x[1],x[2])); ranked=ranked[:max_candidates]
        candidates=tuple(x[1] for x in ranked); focus=candidates[:max_focus]; scores=tuple(round(x[0],8) for x in ranked)
        universe=self._count(domains,"KNOWN"); conflicts=self._count(domains,"CONFLICT"); unknown=self._count(domains,"UNKNOWN")
        if roots!=(self.ledger.epoch,self.ledger.semantic_state_hash,self.ledger.trace_root_hash):raise AssertionError("read mutated ledger roots")
        body={"implementation":IMPLEMENTATION_ID,"basis_epoch":basis_epoch,"candidate_refs":list(candidates),"focus_refs":list(focus),"scores":list(scores),"reentry_mode":mode,"physical_read_mode":read_mode,"physical_state":physical.state,"plan":plan.plan_hash}
        return RankSelectionV61(basis_epoch,self.ledger.semantic_state_hash,candidates,focus,scores,universe,universe>len(candidates),conflicts,unknown,h(body),qplan,mode,read_mode,plan.desired_mode,plan.maintenance_action,physical.state,plan.plan_hash)
