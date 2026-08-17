from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass
from typing import Any

from .store import StaleGeneration

METHOD_KINDS = frozenset({
    "framework_candidate","framework","heuristic_candidate","heuristic",
    "failure_pattern","counterexample","method_receipt"
})
SERVABLE_KINDS = frozenset({"framework","heuristic"})
NEGATIVE_KINDS = frozenset({"failure_pattern","counterexample"})
_TOKEN = re.compile(r"[\w.-]{2,}", re.UNICODE)

class MethodRecordError(ValueError): pass

@dataclass(frozen=True)
class MethodCandidate:
    memory_id: str
    kind: str
    subject: str
    record: dict[str, Any]
    structural_score: float
    lexical_tiebreak: float
    penalty: float
    counterevidence: tuple[str, ...]

    @property
    def score(self) -> float:
        return self.structural_score + self.lexical_tiebreak - self.penalty

class MethodTransfer:
    POLICY_VERSION = 1
    MIN_STRUCTURAL_SCORE = 0.45
    MAX_ROWS = 2000
    MAX_METHODS = 4
    MAX_RECORD_CHARS = 24000

    STRATEGY_WORDS = frozenset({
        "strategy","plan","diagnose","diagnosis","debug","investigate","hypothesis",
        "strategie","planung","diagnostik","debuggen","untersuche","untersuchen",
        "hypothese","hypothesen","analysiere","analyse"
    })
    GOAL_MAP = {
        "debug":"diagnose_repair","diagnose":"diagnose_repair","diagnosis":"diagnose_repair",
        "repair":"diagnose_repair","fix":"diagnose_repair","fehler":"diagnose_repair",
        "debuggen":"diagnose_repair","reparieren":"diagnose_repair","diagnostik":"diagnose_repair",
        "plan":"plan","planung":"plan","strategy":"plan","strategie":"plan",
        "investigate":"investigate","untersuchen":"investigate","untersuche":"investigate",
        "hypothesis":"hypothesis_search","hypothese":"hypothesis_search","hypothesen":"hypothesis_search",
    }

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.lower() for x in _TOKEN.findall(text or "")[:256]}

    @staticmethod
    def _safe_json(raw: str) -> dict[str, Any]:
        try:
            value = json.loads(raw)
        except Exception as exc:
            raise MethodRecordError("method record is not JSON") from exc
        if not isinstance(value, dict):
            raise MethodRecordError("method record must be an object")
        if len(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)) > MethodTransfer.MAX_RECORD_CHARS:
            raise MethodRecordError("method record too large")
        return value

    @staticmethod
    def _string_list(value: Any, field: str, *, min_items: int = 0, max_items: int = 64) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or len(value) < min_items or len(value) > max_items:
            raise MethodRecordError(f"{field} must be a bounded list")
        result = []
        for item in value:
            if not isinstance(item, str) or not item.strip() or len(item) > 512:
                raise MethodRecordError(f"{field} contains invalid item")
            result.append(item.strip().lower())
        return tuple(result)

    @classmethod
    def normalize_signature(cls, signature: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(signature, dict):
            raise MethodRecordError("problem_signature must be an object")
        goal = signature.get("goal_shape")
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 128:
            raise MethodRecordError("problem_signature.goal_shape missing")
        facets = cls._string_list(signature.get("facets"), "problem_signature.facets", min_items=1, max_items=32)
        resources = cls._string_list(signature.get("resource_shapes", []), "problem_signature.resource_shapes", max_items=16)
        return {"goal_shape": goal.strip().lower(), "facets": facets, "resource_shapes": resources}

    @classmethod
    def derive_signature(cls, query: str, resource_refs: list[str] | tuple[str, ...], evidence_status: str) -> dict[str, Any]:
        tokens = cls._tokens(query)
        goal = "general"
        for token in sorted(tokens):
            if token in cls.GOAL_MAP:
                goal = cls.GOAL_MAP[token]
                break
        facets = set()
        if str(evidence_status).upper() in {"UNKNOWN","UNDERCOVERED"}:
            facets.add("evidence_gap")
        if "?" in query:
            facets.add("question")
        if len(resource_refs) > 1:
            facets.add("multi_resource")
        lower = query.lower()
        if any(x in lower for x in ("fail","error","bug","broken","fehler","kaputt","scheit")):
            facets.add("failure_observed")
        if any(x in lower for x in ("compare","versus","alternative","vergleich","gegenhypoth")):
            facets.add("alternatives")
        if not facets:
            facets.add("open_problem")
        resource_shapes = sorted({str(ref).split(":",1)[0].lower() for ref in resource_refs if ":" in str(ref)})
        return {"goal_shape": goal, "facets": sorted(facets), "resource_shapes": resource_shapes}

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> float:
        union = a | b
        return (len(a & b) / len(union)) if union else 1.0

    @classmethod
    def structural_score(cls, query_sig: dict[str, Any], method_sig: dict[str, Any]) -> float:
        q = cls.normalize_signature(query_sig)
        m = cls.normalize_signature(method_sig)
        goal = 1.0 if q["goal_shape"] == m["goal_shape"] else 0.0
        facets = cls._jaccard(set(q["facets"]), set(m["facets"]))
        resources = cls._jaccard(set(q["resource_shapes"]), set(m["resource_shapes"]))
        return round(0.40 * goal + 0.50 * facets + 0.10 * resources, 6)

    @classmethod
    def validate_record(cls, kind: str, raw: str) -> dict[str, Any]:
        if kind not in METHOD_KINDS:
            raise MethodRecordError("not a method-memory kind")
        record = cls._safe_json(raw)
        if kind in SERVABLE_KINDS:
            if record.get("status") != "PROMOTED":
                raise MethodRecordError("servable method must be PROMOTED")
            cls.normalize_signature(record.get("problem_signature"))
            required_lists = (
                "preconditions","method_steps","invariants","expected_observations","falsifiers",
                "failure_modes","scope_limits","source_episode_ids","supporting_memory_ids",
                "counterexample_memory_ids"
            )
            for field in required_lists:
                cls._string_list(
                    record.get(field), field,
                    min_items=1 if field in {"method_steps","falsifiers","source_episode_ids"} else 0
                )
            goal_shape = record.get("goal_shape")
            if not isinstance(goal_shape, str) or goal_shape.strip().lower() != cls.normalize_signature(record["problem_signature"])["goal_shape"]:
                raise MethodRecordError("goal_shape must match problem_signature.goal_shape")
            provenance = record.get("provenance")
            if not isinstance(provenance, dict) or not provenance:
                raise MethodRecordError("missing method provenance")
            calibration = record.get("calibration")
            if not isinstance(calibration, (int,float)) or isinstance(calibration, bool) or not 0.0 <= float(calibration) <= 1.0:
                raise MethodRecordError("invalid calibration")
            for field in ("support_count","success_count","failure_count"):
                if not isinstance(record.get(field), int) or isinstance(record.get(field), bool) or record[field] < 0:
                    raise MethodRecordError(f"invalid {field}")
            if not isinstance(record.get("abstraction_version"), str) or not record["abstraction_version"]:
                raise MethodRecordError("missing abstraction_version")
            validated = record.get("last_validated_at")
            if not isinstance(validated, (int,float)) or isinstance(validated, bool) or float(validated) <= 0:
                raise MethodRecordError("invalid last_validated_at")
        elif kind in {"framework_candidate","heuristic_candidate"}:
            if record.get("status") != "CANDIDATE":
                raise MethodRecordError("candidate method must be CANDIDATE")
            cls.normalize_signature(record.get("problem_signature"))
        elif kind in NEGATIVE_KINDS:
            cls.normalize_signature(record.get("problem_signature"))
            cls._string_list(record.get("targets", []), "targets", min_items=1, max_items=32)
        return record

    @staticmethod
    def _strategy_requested(query: str) -> bool:
        tokens = MethodTransfer._tokens(query)
        return bool(tokens & MethodTransfer.STRATEGY_WORDS)

    def retrieve(self, *, query: str, signature: dict[str, Any], evidence_status: str,
                 user_id: str, session_id: str, turn_id: str, episode_id: str,
                 causal_id: str, generation: int, limit: int = 4) -> dict[str, Any]:
        if not all(isinstance(x, str) and x for x in (user_id, session_id, turn_id, episode_id, causal_id)):
            raise ValueError("method retrieval requires complete causal identity")
        self.db.assert_live_generation(session_id, generation)
        status = str(evidence_status).upper()
        triggered = status in {"UNKNOWN","UNDERCOVERED"} or self._strategy_requested(query)
        normalized_sig = self.normalize_signature(signature)
        signature_hash = hashlib.sha256(json.dumps(normalized_sig, sort_keys=True, separators=(",",":")).encode()).hexdigest()
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        receipt_base = {
            "policy_version": self.POLICY_VERSION,
            "routing_mode": "BASELINE_STRUCTURAL",
            "learned_routing_active": False,
            "query_sha256": query_hash,
            "signature_sha256": signature_hash,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        }
        if not triggered:
            receipt = dict(receipt_base)
            receipt.update({"triggered": False, "selected_method_ids": [], "fact_status_unchanged": True})
            return {"items":[],"counterevidence":[],"fact_status":status,"method_status":"NOT_TRIGGERED","receipt":receipt}
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic','failure_pattern','counterexample') "
            "AND (user_id IS NULL OR user_id=?) AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?", (user_id, turn_id, self.MAX_ROWS)
        ).fetchall()
        positive, negatives = [], []
        malformed = 0
        qtokens = self._tokens(query)
        for row in rows:
            try:
                rec = self.validate_record(str(row["kind"]), str(row["value"]))
            except MethodRecordError:
                malformed += 1
                continue
            struct = self.structural_score(normalized_sig, rec["problem_signature"])
            if row["kind"] in NEGATIVE_KINDS:
                negatives.append((row, rec, struct))
                continue
            if struct < self.MIN_STRUCTURAL_SCORE:
                continue
            method_text = " ".join([str(row["subject"]), *rec.get("method_steps",[])])
            lex = self._jaccard(qtokens, self._tokens(method_text)) * 0.02
            positive.append(MethodCandidate(str(row["memory_id"]),str(row["kind"]),str(row["subject"]),rec,struct,lex,0.0,tuple()))
        rescored = []
        for item in positive:
            penalty, counter_ids = 0.0, []
            for neg_row, neg_rec, neg_struct in negatives:
                if neg_struct < self.MIN_STRUCTURAL_SCORE:
                    continue
                target_set = set(neg_rec.get("targets", []))
                if item.memory_id in target_set or item.subject.lower() in target_set:
                    penalty = max(penalty, 0.50 * neg_struct)
                    counter_ids.append(str(neg_row["memory_id"]))
            rescored.append(MethodCandidate(item.memory_id,item.kind,item.subject,item.record,item.structural_score,item.lexical_tiebreak,penalty,tuple(counter_ids)))
        rescored.sort(key=lambda x:(x.score,x.structural_score,x.memory_id), reverse=True)
        selected = [x for x in rescored if x.score >= self.MIN_STRUCTURAL_SCORE][:min(limit,self.MAX_METHODS)]
        items = [{
            "memory_id": x.memory_id, "kind": x.kind, "subject": x.subject,
            "problem_signature": x.record["problem_signature"],
            "preconditions": x.record.get("preconditions",[]),
            "method_steps": x.record.get("method_steps",[]),
            "falsifiers": x.record.get("falsifiers",[]),
            "failure_modes": x.record.get("failure_modes",[]),
            "scope_limits": x.record.get("scope_limits",[]),
            "calibration": x.record.get("calibration"),
            "structural_score": x.structural_score,
            "counterexample_memory_ids": list(x.counterevidence),
            "truth_authority": False, "effect_authority": False,
        } for x in selected]
        counters = sorted({cid for x in selected for cid in x.counterevidence})
        method_status = "PRESENT" if items else "UNKNOWN"
        receipt = dict(receipt_base)
        receipt.update({
            "selected_method_ids": [x["memory_id"] for x in items],
            "malformed_rejected": malformed,
            "fact_status": status,
            "method_status": method_status,
            "fact_status_unchanged": True,
            "triggered": True,
        })
        receipt_subject = f"method-use:{causal_id}"
        receipt_json = json.dumps(receipt, sort_keys=True, separators=(",",":"))
        existing = self.db.db.execute(
            "SELECT memory_id,value FROM durable_memory WHERE kind='method_receipt' "
            "AND subject=? AND source_turn_id=? AND user_id=? ORDER BY ts DESC LIMIT 1",
            (receipt_subject, turn_id, user_id),
        ).fetchone()
        if existing:
            if str(existing["value"]) != receipt_json:
                raise StaleGeneration("method_receipt_identity")
            receipt_id = str(existing["memory_id"])
        else:
            receipt_id = self.db.add_memory(
                "method_receipt", receipt_subject, receipt_json, turn_id, user_id,
                {"source":"method_transfer:use","causal_id":causal_id,"episode_id":episode_id,
                 "generation":int(generation),"truth_authority":False,"effect_authority":False},
            )
        receipt["use_receipt_memory_id"] = receipt_id
        return {
            "items": items,
            "counterevidence": counters,
            "fact_status": status,
            "method_status": method_status,
            "receipt": receipt,
        }
