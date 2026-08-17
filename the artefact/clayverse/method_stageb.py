from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .method_memory import (
    METHOD_SCHEMA_VERSION,
    MethodMemoryManager,
    MethodMemoryValidationError,
    canonical_problem_signature,
    structural_similarity,
)

QUERY_SCHEMA = "clayverse.problem_signature/v1"
QUERY_ADMISSION_VERSION = 1
METHOD_POLICY_VERSION = 1
METHOD_POLICY_MODE = "SHADOW_METHOD_V1"
_MAX_METHODS = 4
_MAX_COUNTEREVIDENCE = 4
_MIN_STRUCTURAL_SCORE = 0.35
_BLOCKING_COUNTER_SCORE = 0.60
_QUERY_FIELDS = {"schema", "problem_signature", "goal_shape", "provenance"}
_PROVENANCE_FIELDS = {"source", "turn_id", "episode_id", "causal_id", "generation", "admission_version"}
_FORBIDDEN_QUERY_SOURCES = {"raw_prompt", "raw_query", "lexical_prompt", "lexical_query"}
_ALLOWED_TRIGGERS = {"EVIDENCE_UNKNOWN", "EVIDENCE_UNDERCOVERED", "OOD", "CONFLICT", "STRATEGY", "NOT_TRIGGERED"}


class ProblemSignatureAdmissionError(ValueError): pass
class MethodRetrievalIdentityError(RuntimeError): pass


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProblemSignatureAdmissionError("Stage-B request must be canonical JSON") from exc


def _bounded_token(value: Any, field: str, *, max_len: int = 160) -> str:
    if not isinstance(value, str): raise ProblemSignatureAdmissionError(f"{field} must be a structural token")
    token = " ".join(value.strip().lower().split())
    if not token or len(token) > max_len or any(ord(ch) < 32 for ch in token):
        raise ProblemSignatureAdmissionError(f"{field} is invalid")
    return token


@dataclass(frozen=True)
class AdmittedProblemQuery:
    problem_signature: dict[str, tuple[str, ...]]
    goal_shape: str
    provenance: dict[str, Any]
    def identity_payload(self) -> dict[str, Any]:
        return {"schema": QUERY_SCHEMA, "admission_version": QUERY_ADMISSION_VERSION,
                "problem_signature": {key: list(values) for key, values in self.problem_signature.items()},
                "goal_shape": self.goal_shape, "source": self.provenance["source"]}
    def identity_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.identity_payload()).encode()).hexdigest()
    def receipt(self) -> dict[str, Any]:
        return {"schema": QUERY_SCHEMA, "admission_version": QUERY_ADMISSION_VERSION,
                "signature_sha256": self.identity_hash(), "goal_shape": self.goal_shape,
                "source": self.provenance["source"], "truth_authority": False, "effect_authority": False}


def admit_problem_query(value: Any) -> AdmittedProblemQuery:
    """Admit an explicit structural query object; raw prompts are never accepted here."""
    if not isinstance(value, dict): raise ProblemSignatureAdmissionError("problem query must be an object")
    unknown=set(value)-_QUERY_FIELDS; missing=_QUERY_FIELDS-set(value)
    if unknown: raise ProblemSignatureAdmissionError("unknown problem-query fields: "+",".join(sorted(unknown)))
    if missing: raise ProblemSignatureAdmissionError("missing problem-query fields: "+",".join(sorted(missing)))
    if value["schema"] != QUERY_SCHEMA: raise ProblemSignatureAdmissionError("problem-query schema mismatch")
    try: signature=canonical_problem_signature(value["problem_signature"])
    except MethodMemoryValidationError as exc: raise ProblemSignatureAdmissionError(str(exc)) from exc
    goal_shape=_bounded_token(value["goal_shape"],"goal_shape",max_len=1024)
    provenance=value["provenance"]
    if not isinstance(provenance,dict): raise ProblemSignatureAdmissionError("problem-query provenance must be an object")
    unknown=set(provenance)-_PROVENANCE_FIELDS; missing=_PROVENANCE_FIELDS-set(provenance)
    if unknown: raise ProblemSignatureAdmissionError("unknown problem-query provenance fields: "+",".join(sorted(unknown)))
    if missing: raise ProblemSignatureAdmissionError("missing problem-query provenance fields: "+",".join(sorted(missing)))
    source=_bounded_token(provenance["source"],"provenance.source",max_len=80)
    if source in _FORBIDDEN_QUERY_SOURCES: raise ProblemSignatureAdmissionError("raw-prompt lexical derivation is not an admitted Stage-B source")
    if provenance["admission_version"] != QUERY_ADMISSION_VERSION: raise ProblemSignatureAdmissionError("problem-query admission version mismatch")
    for field in ("turn_id","episode_id","causal_id"):
        item=provenance[field]
        if not isinstance(item,str) or not item.strip() or len(item)>256: raise ProblemSignatureAdmissionError(f"provenance.{field} is invalid")
    generation=provenance["generation"]
    if isinstance(generation,bool) or not isinstance(generation,int) or generation<1: raise ProblemSignatureAdmissionError("provenance.generation is invalid")
    return AdmittedProblemQuery(signature,goal_shape,{"source":source,"turn_id":provenance["turn_id"],"episode_id":provenance["episode_id"],
        "causal_id":provenance["causal_id"],"generation":generation,"admission_version":QUERY_ADMISSION_VERSION})


def _normalize_resource_refs(resource_refs: Any) -> list[str]:
    if resource_refs is None: return []
    if not isinstance(resource_refs,(list,tuple)): raise ProblemSignatureAdmissionError("resource_refs must be a list/tuple")
    refs=[]
    for ref in resource_refs:
        if not isinstance(ref,str) or not ref.strip() or len(ref)>2048: raise ProblemSignatureAdmissionError("resource_refs contains invalid item")
        refs.append(ref.strip())
    return sorted(set(refs))[:50]


def _resource_refs_hash(resource_refs: Any) -> tuple[list[str],str]:
    refs=_normalize_resource_refs(resource_refs); return refs,hashlib.sha256(_canonical_json(refs).encode()).hexdigest()


def _trigger(fact_status: str, requested: str|None) -> str:
    status=str(fact_status or "UNKNOWN").upper()
    if requested is None:
        if status=="UNKNOWN": return "EVIDENCE_UNKNOWN"
        if status=="UNDERCOVERED": return "EVIDENCE_UNDERCOVERED"
        return "NOT_TRIGGERED"
    trigger=str(requested).upper()
    if trigger not in _ALLOWED_TRIGGERS: raise ProblemSignatureAdmissionError("invalid Stage-B trigger")
    return trigger


def _method_score(admitted: AdmittedProblemQuery, record: dict[str,Any]) -> float:
    try: candidate=canonical_problem_signature(record["problem_signature"])
    except MethodMemoryValidationError: return 0.0
    structural=structural_similarity(admitted.problem_signature,candidate)
    if structural<=0.0: return 0.0
    goal_match=1.0 if str(record.get("goal_shape","")).strip().lower()==admitted.goal_shape else 0.0
    calibration=float(record.get("calibration",0.0))
    if not math.isfinite(calibration): return 0.0
    return (0.85*structural)+(0.10*goal_match)+(0.05*calibration)


class AdmittedMethodRetriever:
    """One SHADOW Stage-B route over canonical durable method memory.

    Schema 8 adds only durable method-use request identity/replay. Method records remain
    in UnifiedDB durable_memory and therefore do not create a second truth authority.
    """
    def __init__(self,db): self.db=db; self.manager=MethodMemoryManager(db)
    def _rows(self,user_id:str):
        return self.db.db.execute("SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic','failure_pattern','counterexample') AND user_id=? ORDER BY ts DESC,memory_id LIMIT 2000",(user_id,)).fetchall()
    def _assert_active_identity(self,*,user_id,session_id,turn_id,episode_id,causal_id,generation):
        row=self.db.db.execute("SELECT user_id,turn_id,episode_id,causal_id,generation FROM active_turns WHERE session_id=?",(session_id,)).fetchone()
        if row is None: raise MethodRetrievalIdentityError("Stage-B retrieval requires active canonical turn")
        if not (str(row["user_id"])==str(user_id) and str(row["turn_id"])==str(turn_id) and str(row["episode_id"])==str(episode_id)
                and str(row["causal_id"])==str(causal_id) and int(row["generation"])==int(generation)):
            raise MethodRetrievalIdentityError("method_retrieval_active_identity")
    def _promotion_routable(self,decoded:dict[str,Any])->bool:
        if decoded["kind"] not in {"framework","heuristic"}: return True
        provenance=decoded["provenance"]; receipt_id=provenance.get("promotion_receipt_id"); source_id=provenance.get("promotion_source_memory_id")
        if not isinstance(receipt_id,str) or not isinstance(source_id,str): raise MethodMemoryValidationError("promoted method lacks promotion lineage")
        row=self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt'",(receipt_id,)).fetchone()
        if row is None: raise MethodMemoryValidationError("promotion receipt is missing")
        receipt=self.manager.decode_row(row)
        if receipt["value"]["action"]!="PROMOTE" or receipt["value"]["method_memory_id"]!=source_id:
            raise MethodMemoryValidationError("promotion receipt lineage mismatch")
        return self.manager.lifecycle_action(decoded["memory_id"]) not in {"DEMOTE","RETIRE","REJECT"}
    @staticmethod
    def _pack(methods,counters,*,limit,budget_chars):
        selected=[]; selected_counters=[]; used=0
        for item in methods:
            if len(selected)>=limit: break
            chars=len(_canonical_json(item))
            if chars>budget_chars-used: continue
            selected.append(item); used+=chars
        for item in counters:
            if len(selected_counters)>=_MAX_COUNTEREVIDENCE: break
            chars=len(_canonical_json(item))
            if chars>budget_chars-used: continue
            selected_counters.append(item); used+=chars
        return selected,selected_counters
    @staticmethod
    def _identity(row,request):
        return all((str(row["turn_id"])==request["turn_id"],str(row["episode_id"])==request["episode_id"],str(row["session_id"])==request["session_id"],
            str(row["user_id"])==request["user_id"],int(row["generation"])==request["generation"],str(row["fact_status"])==request["fact_status"],
            str(row["trigger"])==request["trigger"],str(row["resource_refs_hash"])==request["resource_refs_hash"],str(row["problem_signature_hash"])==request["problem_signature_hash"],
            str(row["query_schema"])==QUERY_SCHEMA,int(row["admission_version"])==QUERY_ADMISSION_VERSION,int(row["policy_version"])==METHOD_POLICY_VERSION,
            int(row["limit_items"])==request["limit_items"],int(row["budget_chars"])==request["budget_chars"]))
    def _replay_or_none(self,request):
        row=self.db.db.execute("SELECT * FROM method_use_receipts WHERE causal_id=?",(request["causal_id"],)).fetchone()
        if row is None: return None
        if not self._identity(row,request): raise MethodRetrievalIdentityError("method_retrieval_identity")
        try:
            snapshot=json.loads(str(row["snapshot"])); selected_ids=json.loads(str(row["selected_method_ids"])); counter_ids=json.loads(str(row["counterevidence_ids"]))
        except json.JSONDecodeError as exc: raise MethodRetrievalIdentityError("method_retrieval_receipt_corrupt") from exc
        if not isinstance(snapshot,dict) or not isinstance(selected_ids,list) or not isinstance(counter_ids,list): raise MethodRetrievalIdentityError("method_retrieval_receipt_corrupt")
        if [item.get("memory_id") for item in snapshot.get("items",[])]!=selected_ids: raise MethodRetrievalIdentityError("method_retrieval_receipt_selection_mismatch")
        if [item.get("memory_id") for item in snapshot.get("counterevidence",[])]!=counter_ids: raise MethodRetrievalIdentityError("method_retrieval_receipt_counter_mismatch")
        receipt=dict(snapshot.get("receipt",{})); receipt["replayed"]=True; snapshot["receipt"]=receipt; return snapshot
    def _persist(self,request,snapshot):
        selected=[item["memory_id"] for item in snapshot["items"]]; counters=[item["memory_id"] for item in snapshot["counterevidence"]]
        self.db.db.execute("INSERT INTO method_use_receipts(receipt_id,causal_id,turn_id,episode_id,session_id,user_id,generation,fact_status,trigger,resource_refs_hash,problem_signature_hash,query_schema,admission_version,policy_version,limit_items,budget_chars,selected_method_ids,counterevidence_ids,snapshot,ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()),request["causal_id"],request["turn_id"],request["episode_id"],request["session_id"],request["user_id"],request["generation"],request["fact_status"],request["trigger"],
             request["resource_refs_hash"],request["problem_signature_hash"],QUERY_SCHEMA,QUERY_ADMISSION_VERSION,METHOD_POLICY_VERSION,request["limit_items"],request["budget_chars"],
             _canonical_json(selected),_canonical_json(counters),_canonical_json(snapshot),time.time()))
    def retrieve(self,*,problem_query,user_id,session_id,turn_id,episode_id,causal_id,generation,fact_status,resource_refs=(),trigger=None,limit=_MAX_METHODS,budget_chars=24_000):
        if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=16: raise ProblemSignatureAdmissionError("invalid Stage-B limit")
        if not isinstance(budget_chars,int) or isinstance(budget_chars,bool) or not 512<=budget_chars<=64_000: raise ProblemSignatureAdmissionError("invalid Stage-B budget")
        admitted=admit_problem_query(problem_query); self.db.assert_session_owner(session_id,user_id); self.db.assert_live_generation(session_id,generation)
        self._assert_active_identity(user_id=user_id,session_id=session_id,turn_id=turn_id,episode_id=episode_id,causal_id=causal_id,generation=generation)
        if admitted.provenance["turn_id"]!=turn_id: raise ProblemSignatureAdmissionError("problem-query turn identity mismatch")
        if admitted.provenance["episode_id"]!=episode_id: raise ProblemSignatureAdmissionError("problem-query episode identity mismatch")
        if admitted.provenance["causal_id"]!=causal_id: raise ProblemSignatureAdmissionError("problem-query causal identity mismatch")
        if int(admitted.provenance["generation"])!=int(generation): raise ProblemSignatureAdmissionError("problem-query generation mismatch")
        _,refs_hash=_resource_refs_hash(resource_refs); fact_status=str(fact_status or "UNKNOWN").upper(); resolved_trigger=_trigger(fact_status,trigger)
        request={"turn_id":str(turn_id),"episode_id":str(episode_id),"session_id":str(session_id),"user_id":str(user_id),"causal_id":str(causal_id),"generation":int(generation),
                 "fact_status":fact_status,"trigger":resolved_trigger,"resource_refs_hash":refs_hash,"problem_signature_hash":admitted.identity_hash(),"limit_items":int(limit),"budget_chars":int(budget_chars)}
        replay=self._replay_or_none(request)
        if replay is not None: return replay
        if resolved_trigger=="NOT_TRIGGERED":
            receipt={"route":"method_structural_admitted","mode":METHOD_POLICY_MODE,"status":"METHOD_NOT_TRIGGERED","causal_id":str(causal_id),"generation":int(generation),
                     "policy_version":METHOD_POLICY_VERSION,"query_schema":QUERY_SCHEMA,"admission_version":QUERY_ADMISSION_VERSION,"fact_status":fact_status,"selected_count":0,
                     "counterevidence_count":0,"signature_sha256":admitted.identity_hash(),"resource_refs_sha256":refs_hash,"limit_items":int(limit),"budget_chars":int(budget_chars),
                     "truth_authority":False,"effect_authority":False,"served":False,"replayed":False}
            snapshot={"items":[],"counterevidence":[],"receipt":receipt}; self._persist(request,snapshot); return snapshot
        methods=[]; negatives=[]
        for row in self._rows(user_id):
            decoded=self.manager.decode_row(row); record=decoded["value"]
            if record.get("status")!="PROMOTED": continue
            if decoded["kind"] in {"framework","heuristic"} and not self._promotion_routable(decoded): continue
            score=_method_score(admitted,record)
            if score<_MIN_STRUCTURAL_SCORE: continue
            public={"memory_id":decoded["memory_id"],"kind":decoded["kind"],"subject":decoded["subject"],"method":record,"method_score":round(score,6),
                    "context_class":"method_context","truth_authority":False,"effect_authority":False,"provenance":decoded["provenance"]}
            if decoded["kind"] in {"framework","heuristic"}: methods.append(public)
            else: public["context_class"]="counterevidence"; negatives.append(public)
        methods.sort(key=lambda item:(float(item["method_score"]),float(item["method"].get("calibration",0.0)),item["memory_id"]),reverse=True)
        negatives.sort(key=lambda item:(float(item["method_score"]),item["memory_id"]),reverse=True)
        matching_negative_ids={item["memory_id"] for item in negatives if float(item["method_score"])>=_BLOCKING_COUNTER_SCORE}
        methods=[item for item in methods if not (set(item["method"].get("counterexample_memory_ids",[])) & matching_negative_ids)]
        selected,selected_negatives=self._pack(methods,negatives,limit=limit,budget_chars=budget_chars); status="METHOD_PRESENT" if selected else "METHOD_UNKNOWN"
        receipt={"route":"method_structural_admitted","mode":METHOD_POLICY_MODE,"status":status,"causal_id":str(causal_id),"generation":int(generation),"policy_version":METHOD_POLICY_VERSION,
                 "query_schema":QUERY_SCHEMA,"admission_version":QUERY_ADMISSION_VERSION,"fact_status":fact_status,"selected_count":len(selected),"counterevidence_count":len(selected_negatives),
                 "signature_sha256":admitted.identity_hash(),"resource_refs_sha256":refs_hash,"limit_items":int(limit),"budget_chars":int(budget_chars),"truth_authority":False,"effect_authority":False,
                 "served":False,"replayed":False}
        snapshot={"items":selected,"counterevidence":selected_negatives,"receipt":receipt}; self._persist(request,snapshot); return snapshot
