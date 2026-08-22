#!/usr/bin/env python3
"""Convergence layer for the generic Clay mini-entity runtime.
Application/personality/study semantics stay DB/profile data; this module owns only invariants.
"""
from __future__ import annotations
import hashlib,json,os,re,sqlite3,subprocess,tempfile,time,secrets
from pathlib import Path
from typing import Any
import clay_profile_pipeline_runtime as v1
VERSION="clay-profile-pipeline-runtime/0.2"
IMMUTABLE_GUARD=v1.IMMUTABLE_GUARD
PipelineFault=v1.PipelineFault

def _hash(x:Any)->str:
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()

class ProfilePipelineRuntime(v1.ProfilePipelineRuntime):
 def __init__(self,**kw:Any):
  super().__init__(**kw); self.allowed_effects.update({"pipeline_profile_read","inference_generate","pipeline_post_render"})
 @staticmethod
 def _norm(p:dict[str,Any])->dict[str,Any]:
  p=json.loads(json.dumps(p)); s=p.get("schema")
  if s not in {"clay-pipeline-profile/v1","clay-pipeline-profile/v2"}: raise PipelineFault("BAD_PROFILE_SCHEMA")
  if s.endswith("/v1"): p["schema"]="clay-pipeline-profile/v2"; p["inference"]=p.pop("provider")
  for k in ("profile_id","inference","personality","sources","state_metrics","gate"):
   if k not in p: raise PipelineFault("PROFILE_MISSING:"+k)
  p.setdefault("canonical_probes",[]); p.setdefault("post_render",{"enabled":False}); return p
 @staticmethod
 def _schema(db:sqlite3.Connection)->None:
  db.executescript("""
  CREATE TABLE IF NOT EXISTS eos_pipeline_profiles(profile_id TEXT PRIMARY KEY,profile_json TEXT NOT NULL,profile_hash TEXT NOT NULL,updated_at REAL NOT NULL);
  CREATE TABLE IF NOT EXISTS eos_pipeline_profile_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),active_profile_id TEXT,updated_at REAL NOT NULL DEFAULT 0);
  INSERT OR IGNORE INTO eos_pipeline_profile_state(singleton) VALUES(1);
  CREATE TABLE IF NOT EXISTS eos_pipeline_studies(output_id TEXT PRIMARY KEY,generation INTEGER NOT NULL,profile_id TEXT NOT NULL,study_kind TEXT NOT NULL,study_json TEXT NOT NULL,rendered_text TEXT NOT NULL,ts REAL NOT NULL);
  """)
 def _pipeline_init(self,p):
  r=super()._pipeline_init(p)
  if not r.get("ok"): return r
  try:
   with self._db(str(p["entity_db"])) as db:self._schema(db)
   return {"ok":True}
  except Exception as e:return {"ok":False,"error_kind":type(e).__name__,"error":str(e)}
 def apply_profile(self,entity_db:str,profile:dict[str,Any])->dict[str,Any]:
  p=self._norm(profile); r=self._pipeline_init({"entity_db":entity_db})
  if not r.get("ok"): raise PipelineFault(r.get("error","INIT_FAILED"))
  raw=json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False); ph=hashlib.sha256(raw.encode()).hexdigest(); now=time.time()
  with self._db(entity_db) as db:
   self._schema(db); db.execute("BEGIN IMMEDIATE")
   db.execute("INSERT INTO eos_pipeline_profiles(profile_id,profile_json,profile_hash,updated_at) VALUES(?,?,?,?) ON CONFLICT(profile_id) DO UPDATE SET profile_json=excluded.profile_json,profile_hash=excluded.profile_hash,updated_at=excluded.updated_at",(p["profile_id"],raw,ph,now))
   db.execute("UPDATE eos_pipeline_profile_state SET active_profile_id=?,updated_at=? WHERE singleton=1",(p["profile_id"],now))
   g=int(db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0]); db.commit()
  return {"ok":True,"profile_id":p["profile_id"],"profile_hash":ph,"generation":g}
 def apply_post_render(self,entity_db:str,cfg:dict[str,Any])->dict[str,Any]:
  if cfg.get("schema")!="clay-pipeline-post-render/v1": raise PipelineFault("BAD_POST_RENDER_SCHEMA")
  r=self._profile_read({"entity_db":entity_db})
  if not r.get("ok"): raise PipelineFault(r.get("error","NO_ACTIVE_PROFILE"))
  p=r["profile"]
  if cfg.get("profile_id") and cfg["profile_id"]!=p["profile_id"]: raise PipelineFault("POST_RENDER_PROFILE_MISMATCH")
  p["post_render"]=cfg["post_render"]; return self.apply_profile(entity_db,p)
 def _profile_read(self,p):
  try:
   with self._db(str(p["entity_db"])) as db:
    self._schema(db); row=db.execute("SELECT p.profile_json,p.profile_hash FROM eos_pipeline_profile_state s JOIN eos_pipeline_profiles p ON p.profile_id=s.active_profile_id WHERE s.singleton=1").fetchone()
   if not row: raise PipelineFault("NO_ACTIVE_PROFILE")
   return {"ok":True,"profile":self._norm(json.loads(row[0])),"profile_hash":row[1]}
  except Exception as e:return {"ok":False,"error_kind":type(e).__name__,"error":str(e)}
 def effect(self,kind,payload=None):
  p=payload or {}
  if kind=="pipeline_profile_read": r=self._profile_read(p)
  elif kind=="inference_generate": r=self._infer(p)
  elif kind=="pipeline_post_render": r=self._post(p)
  else:return super().effect(kind,p)
  self.effect_trace.append({"kind":kind,"ok":bool(r.get("ok")),"ms":0.0,"payload_hash":_hash(p)}); return r
 def _local(self,i,system,user):
  model=self._resolve(str(i.get("local_model_path",""))); argv=i.get("local_argv_json")
  if isinstance(argv,str): argv=json.loads(argv)
  if not model.is_file(): raise PipelineFault("LOCAL_MODEL_NOT_READABLE")
  if not isinstance(argv,list) or not argv: raise PipelineFault("BAD_LOCAL_ARGV")
  prompt=str(i.get("local_prompt_template","{{SYSTEM}}\n\n{{USER}}")).replace("{{SYSTEM}}",system).replace("{{USER}}",user); fn=None
  try:
   with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False,dir=self.root) as f:f.write(prompt); fn=f.name
   m={"{{MODEL_PATH}}":str(model),"{{PROMPT_FILE}}":fn,"{{MAX_TOKENS}}":str(i.get("max_tokens",2000)),"{{TEMPERATURE}}":str(i.get("temperature",.7))}; out=[]
   for x in argv:
    for a,b in m.items():x=x.replace(a,b)
    out.append(x)
   cp=subprocess.run(out,shell=False,cwd=self.root,capture_output=True,text=True,timeout=float(i.get("timeout_seconds",120)))
   if cp.returncode: raise PipelineFault("LOCAL_EXEC_FAILED:"+str(cp.returncode))
   q=json.loads(cp.stdout.strip())
   if not isinstance(q,dict): raise PipelineFault("LOCAL_OUTPUT_NOT_OBJECT")
   return {"ok":True,"payload":q,"provider_kind":"local_exec","model":i.get("model") or model.name}
  finally:
   if fn:
    try:Path(fn).unlink()
    except OSError:pass
 def _infer(self,p):
  i=dict(p.get("inference") or {})
  try:
   if self.provider_override is not None:
    self._active_secrets=[]; return {"ok":True,"payload":self.provider_override(p),"provider_kind":i.get("kind","override"),"model":i.get("model")}
   if i.get("kind")=="local_exec": return self._local(i,str(p.get("system","")),str(p.get("user","")))
   if i.get("kind") in {"openai_style_chat_json","json_chat","mock"}:
    q=dict(p); j=dict(i); ptr=str(j.get("response_pointer",""))
    if ptr.startswith("/"): j["response_pointer"]=".".join(x.replace("~1","/").replace("~0","~") for x in ptr[1:].split("/"))
    q["provider"]=j; return super()._provider_chat_json(q)
   return {"ok":False,"error_kind":"UNKNOWN_INFERENCE_KIND","error":str(i.get("kind"))}
  except Exception as e:return {"ok":False,"error_kind":type(e).__name__,"error":str(e)}
 @staticmethod
 def _scale(v,name):
  if v is None or (isinstance(v,str) and v.upper()=="UNKNOWN"): return "UNKNOWN"
  n=float(v)
  if not 0<=n<=1: raise PipelineFault("SELF_REPORT_OUT_OF_RANGE:"+name)
  return n
 def _self(self,payload,profile,cfg):
  field=str(cfg.get("self_report_field") or profile["personality"]["output_contract"].get("longitudinal_self_report_field","")); r=payload.get(field) if field else None
  if r is None:
   if cfg.get("require_self_report"): raise PipelineFault("MISSING_MODEL_SELF_REPORT")
   r={}
  if not isinstance(r,dict): raise PipelineFault("MODEL_SELF_REPORT_NOT_OBJECT")
  out={}; schema=cfg.get("self_report_schema",{})
  for name in cfg.get("self_report_fields",list(schema)):
   s=schema.get(name,{"type":"scale01_or_unknown"}); v=r.get(name,"UNKNOWN")
   if s.get("required") and name not in r: raise PipelineFault("MISSING_SELF_REPORT_FIELD:"+name)
   if s.get("type")=="enum":
    if v not in s.get("values",[]): raise PipelineFault("BAD_SELF_REPORT_ENUM:"+name)
    out[name]=v
   else: out[name]=self._scale(v,name)
  return out
 def _prev(self,db,profile_id):
  with self._db(db) as c:self._schema(c); row=c.execute("SELECT study_json FROM eos_pipeline_studies WHERE profile_id=? ORDER BY generation DESC LIMIT 1",(profile_id,)).fetchone()
  return json.loads(row[0]) if row else None
 def _post(self,p):
  try:
   profile=p["profile"]; cfg=profile.get("post_render",{})
   if not cfg.get("enabled"): return {"ok":True,"enabled":False,"rendered_text":"","study_payload":None}
   if cfg.get("kind")!="study_state_box": raise PipelineFault("UNKNOWN_POST_RENDER_KIND")
   d=p["data"]; comp,col,gen=d["compiled"],d["collected"],d["generated"]
   raw_payload=json.dumps(d["gated"]["payload"],ensure_ascii=False,default=str); patterns=[re.compile(x,re.I) for x in profile.get("gate",{}).get("leak_patterns",[])]
   if any(x.search(raw_payload) for x in patterns): raise PipelineFault("LEAK_PATTERN")
   if any(secret and secret in raw_payload for secret in self._active_secrets): raise PipelineFault("SECRET_LEAK")
   report=self._self(d["gated"]["payload"],profile,cfg); prev=self._prev(str(p["entity_db"]),profile["profile_id"]); g=int(p["previous"]["generation"])+1
   sensors=col.get("sensors",{}); health="VERIFIED" if sensors and all(x.get("ok") for x in sensors.values()) else ("DEGRADED" if sensors else "UNKNOWN"); quiet="VERIFIED_QUIET" if col.get("source_count")==0 and col.get("quiet_sensors_ok") else ("NOT_QUIET" if col.get("source_count",0)>0 else "UNKNOWN")
   system={"generation":g,"timestamp":time.time(),"inference_backend":gen.get("provider_kind") or profile["inference"].get("kind"),"model_label":gen.get("model") or profile["inference"].get("model"),"source_count":comp.get("source_count",0),"sensor_health":health,"quiet_status":quiet}
   for n,m in comp.get("personality_state",{}).items():system[n]={"status":m.get("status","UNKNOWN"),"value":m.get("value") if m.get("status")=="VERIFIED" else None}
   deltas={}
   if cfg.get("show_previous_post_delta") and prev:
    for n,v in system.items():
     o=prev.get("system_state",{}).get(n)
     if isinstance(v,dict) and v.get("status")=="VERIFIED" and isinstance(o,dict) and o.get("status")=="VERIFIED" and isinstance(o.get("value"),(int,float)):deltas[n]=float(v["value"])-float(o["value"])
   ph=_hash(profile); sh=hashlib.sha256(str(profile["personality"].get("system_prompt","")).encode()).hexdigest(); conf=[]
   if prev:
    if prev.get("_profile_hash")!=ph:conf.append("PROFILE_CHANGED")
    if prev.get("_system_prompt_hash")!=sh:conf.append("SYSTEM_PROMPT_CHANGED")
    if prev.get("_inference_kind")!=system["inference_backend"]:conf.append("INFERENCE_BACKEND_CHANGED")
    if prev.get("_model")!=system["model_label"]:conf.append("MODEL_CHANGED")
   unknown=[n for n,v in system.items() if (isinstance(v,dict) and v.get("status")!="VERIFIED") or (isinstance(v,str) and v.upper() in {"UNKNOWN","ERROR","DEGRADED"})]
   comparisons=[]
   for x in cfg.get("comparisons",[]):
    sv=system.get(str(x.get("system_metric"))); rv=report.get(str(x.get("self_report")),"UNKNOWN")
    if isinstance(sv,dict) and sv.get("status")=="VERIFIED" and isinstance(sv.get("value"),(int,float)) and isinstance(rv,(int,float)):
     diff=abs(float(sv["value"])-float(rv)); comparisons.append({"id":x.get("id"),"status":"CONGRUENT" if diff<=float(x.get("tolerance",.2)) else "DIVERGENT","absolute_difference":diff})
    else: comparisons.append({"id":x.get("id"),"status":"UNKNOWN"})
   ev={"unknown_system_fields":unknown,"comparisons":comparisons,"confounds":conf,"trend_claim_allowed":False,"causal_claim_allowed":False,"epistemic_law":str(cfg.get("epistemic_law","SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"))}; study={"schema":str(cfg.get("study_schema","clay-study-state-box/v1")),"system_state":system,"model_self_report":report,"deltas":deltas,"evaluation":ev,"_profile_hash":ph,"_system_prompt_hash":sh,"_inference_kind":system["inference_backend"],"_model":system["model_label"]}
   labels=cfg.get("labels",{}); lines=[str(cfg.get("title","STATE"))+" — generation "+str(g),str(labels.get("system","SYSTEM STATE"))]
   for n in cfg.get("canonical_fields",list(system)):
    if n in system:lines.append(f"{n} = {json.dumps(system[n],ensure_ascii=False,sort_keys=True)}")
   lines += ["",str(labels.get("self_report","MODEL SELF-REPORT"))]
   for n in cfg.get("self_report_fields",list(report)):lines.append(f"{n} = {json.dumps(report.get(n,'UNKNOWN'),ensure_ascii=False)}")
   lines += ["",str(labels.get("evaluation","EVALUATION"))]
   if unknown:lines.append("- UNKNOWN/degraded canonical fields: "+", ".join(unknown))
   for x in comparisons: lines.append("- "+str(x.get("id"))+": "+str(x.get("status")))
   if conf:lines.append("- Longitudinal confounds: "+", ".join(conf))
   if not unknown and not comparisons and not conf:lines.append("- No configured uncertainty or longitudinal confound detected.")
   return {"ok":True,"enabled":True,"rendered_text":"```"+str(cfg.get("fence","text"))+"\n"+"\n".join(lines)+"\n```","study_payload":study,"evaluation":ev}
  except Exception as e:return {"ok":False,"error_kind":type(e).__name__,"error":str(e)}
 def _pipeline_commit(self,p):
  db=self._db(str(p["entity_db"])); profile=p["profile"]; prev=p["previous"]; d=p["data"]; col,comp,gen=d["collected"],d["compiled"],d["generated"]; payload=d["gated"]["payload"]; post=d.get("post_render",{"enabled":False}); contract=profile["personality"]["output_contract"]; oid=secrets.token_hex(16); now=time.time(); g=int(prev["generation"])+1; continuity={"narrative":payload.get(contract["continuity_field"]),"autobiographical_hypotheses":payload.get(contract["autobiographical_hypotheses_field"])}
  try:
   self._schema(db); db.execute("BEGIN IMMEDIATE")
   active=db.execute("SELECT s.active_profile_id,p.profile_hash FROM eos_pipeline_profile_state s LEFT JOIN eos_pipeline_profiles p ON p.profile_id=s.active_profile_id WHERE s.singleton=1").fetchone()
   if not active or active[0]!=profile["profile_id"] or active[1]!=_hash(profile): raise PipelineFault("STALE_PROFILE")
   if db.execute("UPDATE eos_pipeline_state SET updated_at=? WHERE singleton=1 AND generation=?",(now,prev["generation"])).rowcount!=1:raise PipelineFault("STALE_GENERATION")
   for x in col["consume"]:db.execute("INSERT INTO eos_pipeline_consumed VALUES(?,?,?,?)",(x["kind"],x["id"],oid,now))
   db.execute("INSERT INTO eos_pipeline_outputs VALUES(?,?,?,?,?,?,?,?,?)",(oid,now,g,profile["profile_id"],json.dumps(payload,ensure_ascii=False),gen.get("provider_kind",""),gen.get("model"),comp["packet_hash"],comp["canonical_state_hash"])); db.execute("INSERT INTO eos_pipeline_packets VALUES(?,?,?,?,?,?,?)",(comp["packet_hash"],oid,now,g,profile["profile_id"],comp["source_count"],comp["canonical_state_hash"]))
   if post.get("enabled"):
    study=dict(post["study_payload"]); db.execute("INSERT INTO eos_pipeline_studies(output_id,generation,profile_id,study_kind,study_json,rendered_text,ts) VALUES(?,?,?,?,?,?,?)",(oid,g,profile["profile_id"],str(profile.get("post_render",{}).get("kind","study_state_box")),json.dumps(study,sort_keys=True,ensure_ascii=False),str(post.get("rendered_text","")),now))
   if db.execute("UPDATE eos_pipeline_state SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,cursors_json=?,updated_at=? WHERE singleton=1 AND generation=?",(g,json.dumps(continuity,ensure_ascii=False),json.dumps(comp["canonical"],ensure_ascii=False),comp["canonical_state_hash"],json.dumps(col["next_cursors"]),now,prev["generation"])).rowcount!=1:raise PipelineFault("STALE_GENERATION_FINAL")
   db.commit(); return {"ok":True,"output_id":oid,"generation":g,"public_append_text":str(post.get("rendered_text","")),"study_enabled":bool(post.get("enabled"))}
  except Exception as e:db.rollback(); return {"ok":False,"error_kind":type(e).__name__,"error":str(e)}
  finally:db.close()

def execute_source(source:str,entry:str,args:list[Any],runtime:ProfilePipelineRuntime|None=None):return v1.execute_source(source,entry,args,runtime or ProfilePipelineRuntime())
__all__=["VERSION","IMMUTABLE_GUARD","PipelineFault","ProfilePipelineRuntime","execute_source"]
