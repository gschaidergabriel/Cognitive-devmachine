"""Clay/FRANK Database Pulse v0.1 candidate.

UnifiedDB is the semantic/provenance authority. Pulse only maintains rebuildable
possibility projections. It is normally model-free; rank/activation never grants truth
or effect authority. Cross-epoch scoped repair requires a verified complete change
manifest; otherwise the runtime rebuilds or fails closed.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, sqlite3, time
from typing import Any, Callable, Iterable

ORDER={"NOOP":0,"FACET_ONLY":1,"WITNESS_REPAIR":2,"ANCHOR_RECOMPILE":3,"FIELD_REBUILD":4,"FAIL_CLOSED":99}
class PulseError(RuntimeError): pass
class PulseStaleRace(PulseError): pass
class PulseVerificationError(PulseError): pass

def sj(v:Any)->str: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def digest(v:Any)->str: return hashlib.sha256(sj(v).encode()).hexdigest()
def refs(raw:str|None)->tuple[str,...]:
    try: v=json.loads(raw or "[]")
    except json.JSONDecodeError: return ()
    return tuple(sorted({str(x) for x in v if str(x)})) if isinstance(v,list) else ()

@dataclass(frozen=True)
class PulsePlan:
    pulse_id:str; source_epoch:int; graph_epoch:int; previous_field_epoch:int|None
    change_manifest_id:str|None; plan_class:str; invalidation_ids:tuple[str,...]
    invalidation_count_total:int; close_all_invalidations:bool; changed_refs:tuple[str,...]
    affected_anchors:tuple[str,...]; reason:str; semantic_plan_hash:str

@dataclass(frozen=True)
class StageResult:
    shadow_field_epoch:int; model_call_count:int=0; tool_call_count:int=0
    state_transition_count:int=0; graph_change_count:int=0; hypothesis_count:int=0
    memory_update_count:int=0; reentry_count:int=0; effect_count:int=0
    evidence:dict[str,Any]|None=None

StageFn=Callable[[sqlite3.Connection,PulsePlan],StageResult]

class DatabasePulseEngine:
    def __init__(self,con:sqlite3.Connection,*,max_invalidations:int=256):
        self.con=con; self.max_invalidations=max(1,int(max_invalidations))

    def _current(self)->tuple[int,int,int]|None:
        rows=self.con.execute("SELECT field_epoch,source_epoch,graph_epoch FROM clay_possibility_field_epochs WHERE status='CURRENT' ORDER BY field_epoch DESC LIMIT 2").fetchall()
        if len(rows)>1: raise PulseVerificationError("multiple CURRENT possibility fields")
        return tuple(map(int,rows[0])) if rows else None

    def _dirty(self,src:int):
        return self.con.execute("SELECT invalidation_id,source_epoch,graph_epoch,changed_ref,reason_class,affected_anchor_refs_clay,repair_mode FROM clay_possibility_invalidation_queue WHERE status='OPEN' AND source_epoch<=? ORDER BY source_epoch,invalidation_id LIMIT ?",(src,self.max_invalidations+1)).fetchall()

    def _truncated(self,field:int,anchors:Iterable[str])->bool:
        a=tuple(sorted(set(anchors)))
        if not a:return False
        q=",".join("?"*len(a))
        return self.con.execute(f"SELECT 1 FROM clay_possibility_anchor_fields f JOIN clay_possibility_field_members m USING(field_id) WHERE f.field_epoch=? AND f.status='CURRENT' AND f.anchor_ref IN ({q}) AND m.witness_truncated=1 LIMIT 1",(field,*a)).fetchone() is not None

    def _manifest(self,current:tuple[int,int,int],src:int,graph:int):
        _,ps,pg=current
        row=self.con.execute("SELECT manifest_id,changed_refs_clay,affected_anchor_refs_clay FROM database_pulse_change_manifests WHERE parent_source_epoch=? AND source_epoch=? AND parent_graph_epoch=? AND graph_epoch=? AND complete=1 AND status='VERIFIED' ORDER BY created_at DESC,manifest_id DESC LIMIT 1",(ps,src,pg,graph)).fetchone()
        return (str(row[0]),refs(row[1]),refs(row[2])) if row else None

    def _plan(self,pulse_id,src,graph,current,kind,ids,changed,anchors,reason,manifest=None,total=None,close_all=False):
        prev=current[0] if current else None; ids=tuple(sorted(set(ids))); changed=tuple(sorted(set(changed))); anchors=tuple(sorted(set(anchors)))
        body={"source_epoch":src,"graph_epoch":graph,"previous_field_epoch":prev,"change_manifest_id":manifest,"plan_class":kind,"invalidation_ids":ids,"invalidation_count_total":len(ids) if total is None else total,"close_all_invalidations":bool(close_all),"changed_refs":changed,"affected_anchors":anchors,"reason":reason}
        return PulsePlan(pulse_id,src,graph,prev,manifest,kind,ids,int(body["invalidation_count_total"]),bool(close_all),changed,anchors,reason,digest(body))

    def plan(self,*,pulse_id:str,source_epoch:int,graph_epoch:int)->PulsePlan:
        if not pulse_id.strip(): raise ValueError("pulse_id required")
        if source_epoch<0 or graph_epoch<0: raise ValueError("epochs must be non-negative")
        cur=self._current(); dirty=self._dirty(source_epoch); overflow=len(dirty)>self.max_invalidations
        total=len(dirty) if not overflow else int(self.con.execute("SELECT count(*) FROM clay_possibility_invalidation_queue WHERE status='OPEN' AND source_epoch<=?",(source_epoch,)).fetchone()[0])
        if overflow:dirty=dirty[:self.max_invalidations]
        ids=[]; changed=set(); anchors=set(); modes=[]; graph_bad=False
        for r in dirty:
            ids.append(str(r[0])); changed.add(str(r[3])); anchors.update(refs(r[5])); mode=str(r[6])
            if mode not in ORDER or mode in {"NOOP","FAIL_CLOSED"}: return self._plan(pulse_id,source_epoch,graph_epoch,cur,"FAIL_CLOSED",ids,changed,anchors,f"UNKNOWN_REPAIR_MODE:{mode}",total=total)
            modes.append(mode); graph_bad|=r[2] is not None and int(r[2])!=graph_epoch
        if graph_bad:return self._plan(pulse_id,source_epoch,graph_epoch,cur,"FAIL_CLOSED",ids,changed,anchors,"INVALIDATION_GRAPH_EPOCH_MISMATCH",total=total)
        if overflow:return self._plan(pulse_id,source_epoch,graph_epoch,cur,"FIELD_REBUILD",ids,changed,anchors,"DIRTY_FRONTIER_OVERFLOW_FORCE_FULL_REBUILD",total=total,close_all=True)
        if cur is None:return self._plan(pulse_id,source_epoch,graph_epoch,cur,"FIELD_REBUILD",ids,changed,anchors,"BOOTSTRAP_NO_CURRENT_FIELD",total=total)
        _,cs,cg=cur
        if cs>source_epoch or cg>graph_epoch:return self._plan(pulse_id,source_epoch,graph_epoch,cur,"FAIL_CLOSED",ids,changed,anchors,"REQUESTED_EPOCH_BEHIND_CURRENT",total=total)
        exact=(cs,cg)==(source_epoch,graph_epoch); mid=None
        if not exact:
            m=self._manifest(cur,source_epoch,graph_epoch)
            if not m:
                kind="FIELD_REBUILD" if dirty else "FAIL_CLOSED"; why="NO_VERIFIED_COMPLETE_CHANGE_MANIFEST" if dirty else "UNEXPLAINED_EPOCH_DRIFT_WITHOUT_INVALIDATION_OR_MANIFEST"
                return self._plan(pulse_id,source_epoch,graph_epoch,cur,kind,ids,changed,anchors,why,total=total)
            mid,mc,ma=m; changed.update(mc); anchors.update(ma)
            if ma and (not modes or ORDER[max(modes,key=ORDER.get)]<ORDER["ANCHOR_RECOMPILE"]): modes.append("ANCHOR_RECOMPILE")
        if exact and not dirty:return self._plan(pulse_id,source_epoch,graph_epoch,cur,"NOOP",(),(),(),"CURRENT_FIELD_COHERENT_AND_NO_DIRTY_WORK",total=0)
        kind=max(modes,key=ORDER.get) if modes else "FIELD_REBUILD"
        if kind=="WITNESS_REPAIR" and self._truncated(cur[0],anchors): kind="ANCHOR_RECOMPILE"; why="TRUNCATED_WITNESS_FORCES_ANCHOR_RECOMPILE"
        else: why="VERIFIED_CHANGE_MANIFEST_DIRTY_FRONTIER" if mid else "BOUNDED_DIRTY_FRONTIER"
        return self._plan(pulse_id,source_epoch,graph_epoch,cur,kind,ids,changed,anchors,why,manifest=mid,total=total)

    def _insert_cycle(self,p:PulsePlan,state:str,ts:str):
        self.con.execute("INSERT INTO database_pulse_cycles(pulse_id,source_epoch,graph_epoch,previous_field_epoch,change_manifest_id,state,plan_class,invalidation_count,changed_refs_clay,affected_anchors_clay,semantic_plan_hash,model_call_count,started_at,evidence_clay) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(p.pulse_id,p.source_epoch,p.graph_epoch,p.previous_field_epoch,p.change_manifest_id,state,p.plan_class,p.invalidation_count_total,sj(p.changed_refs),sj(p.affected_anchors),p.semantic_plan_hash,0,ts,sj({"reason":p.reason,"invalidation_ids":p.invalidation_ids})))

    def _receipt(self,p:PulsePlan,r:StageResult|None,state:str)->str:
        return digest({"plan_hash":p.semantic_plan_hash,"state":state,"shadow_field_epoch":r.shadow_field_epoch if r else None,"model_call_count":r.model_call_count if r else 0,"tool_call_count":r.tool_call_count if r else 0,"state_transition_count":r.state_transition_count if r else 0,"graph_change_count":r.graph_change_count if r else 0,"hypothesis_count":r.hypothesis_count if r else 0,"memory_update_count":r.memory_update_count if r else 0,"reentry_count":r.reentry_count if r else 0,"effect_count":r.effect_count if r else 0,"evidence":r.evidence if r else None})

    def _terminal(self,p,state,start,ts,reason):
        rh=self._receipt(p,None,state); latency=time.perf_counter_ns()-start
        with self.con:
            self._insert_cycle(p,state,ts); self.con.execute("UPDATE database_pulse_cycles SET completed_at=?,latency_ns=?,receipt_hash=?,evidence_clay=? WHERE pulse_id=?",(ts,latency,rh,sj({"reason":reason}),p.pulse_id))
        return {"pulse_id":p.pulse_id,"state":state,"plan_class":p.plan_class,"source_epoch":p.source_epoch,"graph_epoch":p.graph_epoch,"previous_field_epoch":p.previous_field_epoch,"shadow_field_epoch":None,"model_call_count":0,"receipt_hash":rh,"latency_ns":latency,"reason":reason}

    def _verify(self,p:PulsePlan,r:StageResult):
        row=self.con.execute("SELECT source_epoch,graph_epoch,status FROM clay_possibility_field_epochs WHERE field_epoch=?",(r.shadow_field_epoch,)).fetchone()
        if not row:raise PulseVerificationError("stage did not materialize shadow field epoch")
        if (int(row[0]),int(row[1]))!=(p.source_epoch,p.graph_epoch):raise PulseVerificationError("shadow field epoch does not match pulse basis")
        if row[2]!="BUILDING":raise PulseVerificationError("shadow field must remain BUILDING until publication")
        ac=int(self.con.execute("SELECT count(*) FROM clay_possibility_anchor_fields WHERE field_epoch=? AND status='CURRENT'",(r.shadow_field_epoch,)).fetchone()[0])
        mc=int(self.con.execute("SELECT count(*) FROM clay_possibility_field_members m JOIN clay_possibility_anchor_fields f USING(field_id) WHERE f.field_epoch=? AND f.status='CURRENT'",(r.shadow_field_epoch,)).fetchone()[0])
        if ac<1 or mc<1:raise PulseVerificationError("empty shadow field cannot replace last-known-good")
        broken=int(self.con.execute("SELECT count(*) FROM clay_possibility_field_members m JOIN clay_possibility_anchor_fields f USING(field_id) LEFT JOIN clay_possibility_ordinals o ON o.candidate_ref=m.candidate_ref AND o.ordinal=m.candidate_ordinal WHERE f.field_epoch=? AND o.candidate_ref IS NULL",(r.shadow_field_epoch,)).fetchone()[0])
        mismatch=int(self.con.execute("SELECT count(*) FROM clay_possibility_anchor_fields f WHERE f.field_epoch=? AND f.status='CURRENT' AND f.candidate_count!=(SELECT count(*) FROM clay_possibility_field_members m WHERE m.field_id=f.field_id)",(r.shadow_field_epoch,)).fetchone()[0])
        badw=int(self.con.execute("SELECT count(*) FROM clay_possibility_witnesses w JOIN clay_possibility_anchor_fields f USING(field_id) WHERE f.field_epoch=? AND w.status='CURRENT' AND w.path_score<0",(r.shadow_field_epoch,)).fetchone()[0])
        if broken:raise PulseVerificationError("broken candidate ordinals")
        if mismatch:raise PulseVerificationError("candidate_count does not match members")
        if badw:raise PulseVerificationError("invalid witness score")
        return {"anchor_count":ac,"member_count":mc}

    def _publish(self,p:PulsePlan,r:StageResult,v:dict[str,int],ts:str):
        self.con.execute("BEGIN IMMEDIATE")
        try:
            rows=self.con.execute("SELECT field_epoch FROM clay_possibility_field_epochs WHERE status='CURRENT' ORDER BY field_epoch DESC LIMIT 2").fetchall()
            if len(rows)>1:raise PulseStaleRace("multiple CURRENT fields appeared before publish")
            actual=int(rows[0][0]) if rows else None
            if actual!=p.previous_field_epoch:raise PulseStaleRace(f"possibility head moved: expected {p.previous_field_epoch}, got {actual}")
            if actual is not None:self.con.execute("UPDATE clay_possibility_field_epochs SET status='SUPERSEDED' WHERE field_epoch=? AND status='CURRENT'",(actual,))
            cur=self.con.execute("UPDATE clay_possibility_field_epochs SET status='CURRENT',completed_at=COALESCE(completed_at,built_at),build_metadata_clay=? WHERE field_epoch=? AND status='BUILDING'",(sj({"database_pulse":p.pulse_id,"verification":v}),r.shadow_field_epoch))
            if cur.rowcount!=1:raise PulseStaleRace("shadow field could not be promoted")
            if p.close_all_invalidations:self.con.execute("UPDATE clay_possibility_invalidation_queue SET status='DONE',processed_at=? WHERE status='OPEN' AND source_epoch<=?",(ts,p.source_epoch))
            elif p.invalidation_ids:
                q=",".join("?"*len(p.invalidation_ids)); self.con.execute(f"UPDATE clay_possibility_invalidation_queue SET status='DONE',processed_at=? WHERE invalidation_id IN ({q}) AND status='OPEN'",(ts,*p.invalidation_ids))
            self.con.commit()
        except Exception:self.con.rollback();raise

    def pulse_once(self,*,pulse_id:str,source_epoch:int,graph_epoch:int,stage_fn:StageFn|None=None,timestamp:str="UNKNOWN"):
        start=time.perf_counter_ns()
        try:p=self.plan(pulse_id=pulse_id,source_epoch=source_epoch,graph_epoch=graph_epoch)
        except Exception as e:
            p=self._plan(pulse_id,source_epoch,graph_epoch,None,"FAIL_CLOSED",(),(),(),f"PLAN_ERROR:{type(e).__name__}:{e}")
            return self._terminal(p,"FAILED",start,timestamp,p.reason)
        if p.plan_class=="NOOP":return self._terminal(p,"NOOP",start,timestamp,p.reason)
        if p.plan_class=="FAIL_CLOSED":return self._terminal(p,"FAILED",start,timestamp,p.reason)
        if stage_fn is None:return self._terminal(p,"FAILED",start,timestamp,"NO_STAGE_COMPILER_AVAILABLE")
        with self.con:self._insert_cycle(p,"RUNNING",timestamp)
        result=None
        try:
            result=stage_fn(self.con,p); verification=self._verify(p,result); self._publish(p,result,verification,timestamp)
            state="PUBLISHED"; ev={"verification":verification,**(result.evidence or {})}
        except Exception as e:
            if result is not None:
                with self.con:self.con.execute("UPDATE clay_possibility_field_epochs SET status='FAILED' WHERE field_epoch=? AND status='BUILDING'",(result.shadow_field_epoch,))
            state="QUARANTINED"; ev={"error_class":type(e).__name__,"error":str(e)}
        latency=time.perf_counter_ns()-start; rh=self._receipt(p,result,state)
        with self.con:
            self.con.execute("UPDATE database_pulse_cycles SET state=?,shadow_field_epoch=?,model_call_count=?,tool_call_count=?,state_transition_count=?,graph_change_count=?,hypothesis_count=?,memory_update_count=?,reentry_count=?,effect_count=?,completed_at=?,latency_ns=?,receipt_hash=?,evidence_clay=? WHERE pulse_id=?",(state,result.shadow_field_epoch if result else None,result.model_call_count if result else 0,result.tool_call_count if result else 0,result.state_transition_count if result else 0,result.graph_change_count if result else 0,result.hypothesis_count if result else 0,result.memory_update_count if result else 0,result.reentry_count if result else 0,result.effect_count if result else 0,timestamp,latency,rh,sj(ev),p.pulse_id))
        return {"pulse_id":p.pulse_id,"state":state,"plan_class":p.plan_class,"source_epoch":p.source_epoch,"graph_epoch":p.graph_epoch,"previous_field_epoch":p.previous_field_epoch,"shadow_field_epoch":result.shadow_field_epoch if result else None,"model_call_count":result.model_call_count if result else 0,"receipt_hash":rh,"latency_ns":latency,"evidence":ev}
