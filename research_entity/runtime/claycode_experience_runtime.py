#!/usr/bin/env python3
"""Convert observable RAE usage experience into staged ClayCode research material.

No hidden chain-of-thought. No single UX observation directly mutates architecture.
Positive, negative and friction signals all matter.
"""
from __future__ import annotations

import json
from typing import Any

from rae_state_runtime import RAEStateRuntime, RUNTIME_DIR, now, uid

MIGRATION=RUNTIME_DIR/"RAE_UNIFIEDDB_V5_CLAYCODE_EXPERIENCE_RESEARCH.sql"

LAYER_MAP={
 "misunderstanding":"semantic_projection",
 "good_outcome":"primitive_or_projection",
 "friction":"orchestration_or_ir",
 "awkwardness":"surface_or_ir",
 "retrieval_miss":"unifieddb_query",
 "stale_state":"temporal_world_model",
 "wrong_route":"gwt_or_capability_routing",
 "repair":"recovery_reentry",
 "token_waste":"compression_projection",
}


def _j(x:Any)->str:
    return json.dumps(x if x is not None else {},ensure_ascii=False,sort_keys=True,separators=(",",":"))

def init_tables(rt:RAEStateRuntime)->None:
    rt.u.executescript(MIGRATION.read_text(encoding="utf-8"));rt.u.commit()

def record(
    rt:RAEStateRuntime,*,node_id:str,signal_class:str,direction:str,magnitude:float,confidence:float,
    symptom:Any,evidence:Any,episode_id:str|None=None,cycle_id:str|None=None,task_shape:str|None=None,
    suspected_layer:str|None=None,preferred_property:Any=None,evidence_refs:Any=None,
    token_cost_estimate:float|None=None,latency_cost_ms:float|None=None,repair_cost_estimate:float|None=None,
)->str:
    init_tables(rt);oid=uid("ux")
    layer=suspected_layer or LAYER_MAP.get(signal_class,"unknown")
    ts=now()
    rt.u.execute(
      "INSERT INTO rae_experience_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
      (oid,episode_id,cycle_id,node_id,ts,signal_class,task_shape,direction,max(0,min(1,float(magnitude))),
       max(0,min(1,float(confidence))),_j(evidence),layer,_j(symptom),_j(preferred_property),
       _j(evidence_refs or []),token_cost_estimate,latency_cost_ms,repair_cost_estimate,"OPEN",ts)
    );rt.u.commit();return oid

def _candidate_template(signal:str,layer:str)->tuple[dict,dict,dict,dict,dict]:
    h={"claim":f"changing ClayCode/{layer} can improve repeated {signal} outcomes"}
    ch={"claim":"observed pattern is task/provider noise or upstream architecture issue, not ClayCode"}
    gain={"metrics":["verified_outcome_per_token","repair_latency","state_error_rate","regression_rate"]}
    fals={"rule":"matched-budget replay shows no improvement or introduces hard-loss regression"}
    bench={"arms":["current","candidate"],"controls":["same task","same evidence","same model/provider when feasible"],"require":["counterevidence","negative_results","rollback"]}
    return h,ch,gain,fals,bench

def derive(rt:RAEStateRuntime,observation_id:str,pattern_key:str|None=None)->str:
    init_tables(rt)
    o=rt.u.execute("SELECT * FROM rae_experience_observations WHERE observation_id=?",(observation_id,)).fetchone()
    if not o:raise KeyError(observation_id)
    layer=o["suspected_layer"] or "unknown";signal=o["signal_class"]
    key=pattern_key or f"{layer}:{signal}:{o['task_shape'] or '*'}"
    row=rt.u.execute("SELECT * FROM claycode_research_candidates WHERE pattern_key=? AND status IN ('OPEN','ACCUMULATING','READY_FOR_EXPERIMENT','EXPERIMENTING') ORDER BY updated_at DESC LIMIT 1",(key,)).fetchone()
    positive=1 if o["direction"] in ("POSITIVE","GOOD","IMPROVED") else 0
    negative=0 if positive else 1
    impact=float(o["magnitude"])*float(o["confidence"])
    ts=now()
    if row:
        ids=json.loads(row["supporting_observation_ids_clay"]);ids.append(observation_id)
        count=int(row["supporting_count"])+1
        conf=((float(row["mean_confidence"])*int(row["supporting_count"]))+float(o["confidence"]))/count
        status="READY_FOR_EXPERIMENT" if count>=3 or float(row["accumulated_impact"])+impact>=2.0 else "ACCUMULATING"
        rt.u.execute("""UPDATE claycode_research_candidates SET updated_at=?,supporting_observation_ids_clay=?,supporting_count=?,positive_count=positive_count+?,negative_count=negative_count+?,mean_confidence=?,accumulated_impact=accumulated_impact+?,status=? WHERE candidate_id=?""",
          (ts,_j(ids),count,positive,negative,conf,impact,status,row["candidate_id"]))
        cid=row["candidate_id"]
    else:
        cid=uid("cc-research");h,ch,gain,fals,bench=_candidate_template(signal,layer)
        status="READY_FOR_EXPERIMENT" if impact>=.85 else "ACCUMULATING"
        rt.u.execute("INSERT INTO claycode_research_candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (cid,ts,ts,signal,layer,key,_j([observation_id]),1,positive,negative,float(o["confidence"]),impact,_j(h),_j(ch),_j(gain),_j(fals),_j(bench),None,status,"MATCHED_BUDGET_REPLAY_AND_NO_HARD_LOSS"))
    rt.u.execute("UPDATE rae_experience_observations SET status='ROUTED' WHERE observation_id=?",(observation_id,));rt.u.commit();return cid

def queue(rt:RAEStateRuntime,limit:int=20)->list[dict[str,Any]]:
    init_tables(rt)
    return [dict(r) for r in rt.u.execute("SELECT * FROM v_claycode_experience_research_queue LIMIT ?",(int(limit),))]
