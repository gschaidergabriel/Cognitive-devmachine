from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Any

from .store import StaleGeneration, UnifiedDB

METHOD_SCHEMA_VERSION = 2
SIGNATURE_SCHEMA_VERSION = 1
METHOD_KINDS = frozenset({
    "framework_candidate", "framework", "heuristic_candidate", "heuristic",
    "failure_pattern", "counterexample", "method_signature", "method_receipt",
})
METHOD_RECORD_KINDS = frozenset({
    "framework_candidate", "framework", "heuristic_candidate", "heuristic",
    "failure_pattern", "counterexample",
})
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
PROMOTED_METHOD_KINDS = frozenset({"framework", "heuristic"})
NEGATIVE_KINDS = frozenset({"failure_pattern", "counterexample"})
MAX_JSON_CHARS = 64 * 1024
MAX_LIST_ITEMS = 256
MAX_ITEM_CHARS = 4096
_LIST_FIELDS = (
    "preconditions", "method_steps", "invariants", "expected_observations",
    "falsifiers", "failure_modes", "scope_limits", "source_episode_ids",
    "supporting_memory_ids", "counterexample_memory_ids",
)


class MethodRecordError(ValueError):
    pass


@dataclass(frozen=True)
class MethodMatch:
    memory_id: str
    kind: str
    subject: str
    score: float
    record: dict[str, Any]
    provenance: dict[str, Any]


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodRecordError("non-canonical method JSON") from exc


def _atom(value: Any, *, max_len: int = 160) -> str:
    if not isinstance(value, str):
        raise MethodRecordError("signature atoms must be strings")
    value = " ".join(value.strip().lower().split())
    if not value or len(value) > max_len:
        raise MethodRecordError("invalid signature atom")
    return value


def _string_list(value: Any, field: str, *, required: bool = False) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_LIST_ITEMS:
        raise MethodRecordError(f"{field} must be a bounded list")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > MAX_ITEM_CHARS:
            raise MethodRecordError(f"invalid {field} item")
        out.append(item.strip())
    if required and not out:
        raise MethodRecordError(f"{field} must not be empty")
    return out


def canonical_problem_signature(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict) or not raw or len(raw) > 24:
        raise MethodRecordError("problem_signature must be a non-empty bounded object")
    result: dict[str, list[str]] = {}
    facets = 0
    for raw_key, raw_value in raw.items():
        key = _atom(raw_key, max_len=80)
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        if not values or len(values) > 32:
            raise MethodRecordError("invalid problem_signature facet")
        normalized = sorted({_atom(str(value)) for value in values})
        facets += len(normalized)
        if facets > 96:
            raise MethodRecordError("problem_signature has too many facets")
        result[key] = normalized
    return dict(sorted(result.items()))


def infer_problem_signature(text: str, resource_refs: list[str] | None = None) -> dict[str, list[str]]:
    raise MethodRecordError("raw-query signature inference is not serving authority")


def structural_score(query: dict[str, list[str]], candidate: dict[str, list[str]]) -> float:
    query = canonical_problem_signature(query)
    candidate = canonical_problem_signature(candidate)
    facets = sorted(set(query) | set(candidate))
    if not facets:
        return 0.0
    weighted = total = 0.0
    for facet in facets:
        q, c = set(query.get(facet, [])), set(candidate.get(facet, []))
        weight = 2.0 if facet in {"goal", "goal_shape", "mechanism"} else 1.0
        total += weight
        if q and c:
            weighted += weight * (len(q & c) / len(q | c))
    return weighted / total if total else 0.0


def validate_method_record(kind: str, record: Any) -> dict[str, Any]:
    if kind not in METHOD_RECORD_KINDS or not isinstance(record, dict):
        raise MethodRecordError("unrecognized method memory record")
    required = {"problem_signature", "goal_shape", "abstraction_version", "support_count", "success_count",
                "failure_count", "calibration", "last_validated_at", "status", *_LIST_FIELDS}
    missing = sorted(required - set(record))
    if missing:
        raise MethodRecordError("missing method fields: " + ",".join(missing))
    normalized = dict(record)
    normalized["problem_signature"] = canonical_problem_signature(record["problem_signature"])
    goal = record["goal_shape"] if isinstance(record["goal_shape"], list) else [record["goal_shape"]]
    normalized["goal_shape"] = sorted({_atom(x) for x in goal})
    for field in _LIST_FIELDS:
        normalized[field] = _string_list(record[field], field, required=field in {"method_steps", "falsifiers", "scope_limits", "source_episode_ids"})
    version = record["abstraction_version"]
    if not isinstance(version, str) or not version.strip() or len(version) > 128:
        raise MethodRecordError("invalid abstraction_version")
    normalized["abstraction_version"] = version.strip()
    for field in ("support_count", "success_count", "failure_count"):
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise MethodRecordError(f"{field} must be a non-negative integer")
        normalized[field] = value
    if normalized["success_count"] + normalized["failure_count"] > normalized["support_count"]:
        raise MethodRecordError("success/failure counts exceed support_count")
    calibration = record["calibration"]
    if isinstance(calibration, bool) or not isinstance(calibration, (int, float)) or not math.isfinite(float(calibration)) or not 0 <= float(calibration) <= 1:
        raise MethodRecordError("calibration must be finite in [0,1]")
    normalized["calibration"] = float(calibration)
    validated = record["last_validated_at"]
    if isinstance(validated, bool) or not isinstance(validated, (int, float)) or not math.isfinite(float(validated)) or float(validated) < 0:
        raise MethodRecordError("invalid last_validated_at")
    normalized["last_validated_at"] = float(validated)
    status = str(record["status"]).upper()
    if kind in CANDIDATE_KINDS and status != "CANDIDATE":
        raise MethodRecordError("candidate kind requires CANDIDATE status")
    if kind in PROMOTED_METHOD_KINDS and status not in {"PROMOTED", "DEMOTED", "RETIRED"}:
        raise MethodRecordError("method lifecycle status invalid")
    if kind in NEGATIVE_KINDS and status not in {"PROMOTED", "RETIRED"}:
        raise MethodRecordError("negative method lifecycle status invalid")
    normalized["status"] = status
    normalized["limits_method_ids"] = _string_list(record.get("limits_method_ids", []), "limits_method_ids")
    if kind in PROMOTED_METHOD_KINDS and status == "PROMOTED":
        if len(set(normalized["source_episode_ids"])) < 2 or normalized["support_count"] < 2 or normalized["success_count"] < 1:
            raise MethodRecordError("promotion requires cross-instance support")
        receipt = record.get("promotion_receipt_id")
        if not isinstance(receipt, str) or not receipt.strip():
            raise MethodRecordError("promoted method requires promotion_receipt_id")
        normalized["promotion_receipt_id"] = receipt.strip()
    normalized["method_schema_version"] = METHOD_SCHEMA_VERSION
    if len(_canonical_json(normalized)) > MAX_JSON_CHARS:
        raise MethodRecordError("method record exceeds bounded serialized size")
    return normalized


class MethodMemory:
    MIN_SCORE = 0.20

    def __init__(self, db: UnifiedDB): self.db = db

    @staticmethod
    def strategy_intent(query: str) -> bool:
        q = str(query or "").lower()
        return any(token in q for token in ("strategy", "plan", "approach", "diagnos", "debug", "investigat", "falsif", "method"))

    @staticmethod
    def _assert_user(user_id: str | None) -> str:
        if user_id not in {"gabriel", "andreas"}:
            raise MethodRecordError("explicit canonical user scope required")
        return str(user_id)

    def _assert_source_evidence(self, record: dict[str, Any], user_id: str, *, require_causal: bool) -> None:
        seen_turns: set[str] = set()
        for episode_id in set(record["source_episode_ids"]):
            row = self.db.db.execute(
                "SELECT w.state,w.observation_turn_id,s.user_id FROM workspace_episodes w JOIN sessions s ON s.session_id=w.session_id WHERE w.episode_id=?",
                (episode_id,),
            ).fetchone()
            if row is None: raise MethodRecordError("unknown source_episode_id")
            if str(row["user_id"]) != user_id: raise MethodRecordError("cross-user source episode denied")
            if require_causal:
                if str(row["state"]) not in {"COMPLETED", "ABORTED"} or not row["observation_turn_id"]:
                    raise MethodRecordError("promotion source episode is not terminal evidence")
                causal = self.db.db.execute("SELECT causal_id FROM causal_episodes WHERE episode_id=? AND reentered=1 ORDER BY ts DESC LIMIT 1", (episode_id,)).fetchone()
                if causal is None: raise MethodRecordError("promotion source episode lacks causal re-entry")
                seen_turns.add(str(row["observation_turn_id"]))
        if require_causal and len(seen_turns) < 2:
            raise MethodRecordError("promotion requires distinct causal problem instances")
        for memory_id in set(record["supporting_memory_ids"] + record["counterexample_memory_ids"] + record["limits_method_ids"]):
            row = self.db.db.execute("SELECT kind,user_id FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
            if row is None: raise MethodRecordError("unknown referenced memory_id")
            if row["user_id"] not in (None, user_id): raise MethodRecordError("cross-user referenced memory denied")
        for memory_id in set(record["counterexample_memory_ids"]):
            row = self.db.db.execute("SELECT kind FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
            if row is None or str(row["kind"]) not in NEGATIVE_KINDS:
                raise MethodRecordError("counterexample reference must target negative method memory")

    def _stored_provenance(self, provenance: dict[str, Any], user_id: str, admission: str) -> dict[str, Any]:
        if not isinstance(provenance, dict) or not provenance: raise MethodRecordError("method admission requires provenance")
        out = dict(provenance); out.update({"method_schema_version": METHOD_SCHEMA_VERSION, "admission": admission,
            "user_scope": user_id, "truth_authority": False, "effect_authority": False})
        _canonical_json(out); return out

    def admit(self, *, kind: str, subject: str, record: dict[str, Any], source_turn_id: str | None,
              user_id: str | None, provenance: dict[str, Any]) -> str:
        user_id = self._assert_user(user_id)
        if kind in PROMOTED_METHOD_KINDS: raise MethodRecordError("framework/heuristic requires dedicated promotion lifecycle")
        if kind not in CANDIDATE_KINDS | NEGATIVE_KINDS: raise MethodRecordError("reserved method kind requires dedicated authority")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 300: raise MethodRecordError("invalid method subject")
        normalized = validate_method_record(kind, record)
        self._assert_source_evidence(normalized, user_id, require_causal=(kind in NEGATIVE_KINDS))
        if source_turn_id is not None:
            row = self.db.db.execute("SELECT user_id FROM turns WHERE turn_id=?", (source_turn_id,)).fetchone()
            if row is None or str(row["user_id"]) != user_id: raise MethodRecordError("source turn is absent or cross-user")
        return self.db.add_memory(kind, subject.strip(), _canonical_json(normalized), source_turn_id, user_id,
            self._stored_provenance(provenance, user_id, "method_memory:v2"))

    def promote(self, candidate_memory_id: str, *, evaluation: str, provenance: dict[str, Any], source_turn_id: str | None = None) -> dict[str, str]:
        if not isinstance(candidate_memory_id, str) or not candidate_memory_id: raise MethodRecordError("candidate_memory_id required")
        if not isinstance(evaluation, str) or not evaluation.strip() or len(evaluation) > 8192: raise MethodRecordError("bounded promotion evaluation required")
        with self.db.tx() as db:
            row = db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (candidate_memory_id,)).fetchone()
            if row is None: raise MethodRecordError("promotion candidate does not exist")
            candidate = self.decode_row(row)
            if candidate["kind"] not in CANDIDATE_KINDS or candidate["value"]["status"] != "CANDIDATE": raise MethodRecordError("promotion source must be a candidate")
            user_id = self._assert_user(candidate["user_id"]); record = dict(candidate["value"])
            self._assert_source_evidence(record, user_id, require_causal=True)
            if record["support_count"] < 2 or record["success_count"] < 1 or record["calibration"] <= 0: raise MethodRecordError("promotion evidence is underpowered")
            prior = db.execute("SELECT memory_id FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts", (f"PROMOTE:{candidate_memory_id}",)).fetchone()
            if prior is not None: raise MethodRecordError("candidate already has promotion receipt")
            now = time.time(); receipt_payload = {"action": "PROMOTE", "candidate_memory_id": candidate_memory_id,
                "source_episode_ids": list(record["source_episode_ids"]), "supporting_memory_ids": list(record["supporting_memory_ids"]),
                "counterexample_memory_ids": list(record["counterexample_memory_ids"]), "evaluation": evaluation.strip(), "ts": now,
                "truth_authority": False, "effect_authority": False}
            receipt_id = self.db.add_memory("method_receipt", f"PROMOTE:{candidate_memory_id}", _canonical_json(receipt_payload),
                source_turn_id if source_turn_id is not None else candidate["source_turn_id"], user_id,
                self._stored_provenance(provenance, user_id, "method_promotion:v2"))
            promoted_kind = "framework" if candidate["kind"] == "framework_candidate" else "heuristic"
            promoted = dict(record); promoted.update({"status": "PROMOTED", "last_validated_at": now, "promotion_receipt_id": receipt_id})
            promoted = validate_method_record(promoted_kind, promoted)
            promoted_provenance = self._stored_provenance(provenance, user_id, "method_promotion:v2")
            promoted_provenance.update({"promotion_source_memory_id": candidate_memory_id, "promotion_receipt_id": receipt_id})
            promoted_id = self.db.add_memory(promoted_kind, candidate["subject"], _canonical_json(promoted),
                source_turn_id if source_turn_id is not None else candidate["source_turn_id"], user_id, promoted_provenance)
            return {"candidate_memory_id": candidate_memory_id, "receipt_memory_id": receipt_id, "promoted_memory_id": promoted_id}

    def admit_signature(self, *, user_id: str, session_id: str, turn_id: str, episode_id: str, causal_id: str,
                        generation: int, problem_signature: dict[str, Any], producer: str, provenance: dict[str, Any]) -> str:
        user_id = self._assert_user(user_id); self.db.assert_live_generation(session_id, generation)
        active = self.db.db.execute("SELECT * FROM active_turns WHERE session_id=?", (session_id,)).fetchone()
        if active is None or str(active["user_id"]) != user_id or str(active["turn_id"]) != turn_id or str(active["episode_id"]) != episode_id or str(active["causal_id"]) != causal_id or int(active["generation"]) != int(generation):
            raise StaleGeneration("method_signature_identity")
        signature = canonical_problem_signature(problem_signature)
        if not isinstance(producer, str) or not producer.strip() or len(producer) > 256: raise MethodRecordError("explicit signature producer required")
        signature_json = _canonical_json(signature)
        payload = {"signature_schema_version": SIGNATURE_SCHEMA_VERSION, "problem_signature": signature,
            "signature_sha256": hashlib.sha256(signature_json.encode()).hexdigest(), "producer": producer.strip(),
            "session_id": session_id, "turn_id": turn_id, "episode_id": episode_id, "causal_id": causal_id,
            "generation": int(generation), "truth_authority": False, "effect_authority": False}
        subject = f"SIGNATURE:{causal_id}"
        existing = self.db.db.execute("SELECT * FROM durable_memory WHERE kind='method_signature' AND subject=? ORDER BY ts LIMIT 1", (subject,)).fetchone()
        if existing is not None:
            decoded = self.decode_signature(existing)
            if decoded["value"] != payload: raise StaleGeneration("method_signature_identity")
            return decoded["memory_id"]
        return self.db.add_memory("method_signature", subject, _canonical_json(payload), turn_id, user_id,
            self._stored_provenance(provenance, user_id, "method_signature:v1"))

    def decode_signature(self, row) -> dict[str, Any]:
        if str(row["kind"]) != "method_signature": raise MethodRecordError("row is not method signature")
        try: value, provenance = json.loads(row["value"]), json.loads(row["provenance"])
        except Exception as exc: raise MethodRecordError("malformed method signature") from exc
        if not isinstance(value, dict) or value.get("signature_schema_version") != SIGNATURE_SCHEMA_VERSION: raise MethodRecordError("unknown method signature schema")
        signature = canonical_problem_signature(value.get("problem_signature")); expected = hashlib.sha256(_canonical_json(signature).encode()).hexdigest()
        if value.get("signature_sha256") != expected: raise MethodRecordError("method signature digest mismatch")
        if not isinstance(provenance, dict) or provenance.get("admission") != "method_signature:v1": raise MethodRecordError("unadmitted method signature")
        value = dict(value); value["problem_signature"] = signature
        return {"memory_id": str(row["memory_id"]), "kind": "method_signature", "subject": str(row["subject"]), "value": value,
            "source_turn_id": row["source_turn_id"], "user_id": row["user_id"], "ts": float(row["ts"]), "provenance": provenance}

    def load_signature(self, memory_id: str, *, user_id: str, session_id: str, turn_id: str, episode_id: str,
                       causal_id: str, generation: int) -> dict[str, Any]:
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        if row is None: raise StaleGeneration("method_signature_missing")
        decoded = self.decode_signature(row); value = decoded["value"]
        if decoded["user_id"] != user_id or value["session_id"] != session_id or value["turn_id"] != turn_id or value["episode_id"] != episode_id or value["causal_id"] != causal_id or int(value["generation"]) != int(generation):
            raise StaleGeneration("method_signature_identity")
        self.db.assert_live_generation(session_id, generation); return decoded

    def decode_row(self, row) -> dict[str, Any]:
        kind = str(row["kind"])
        if kind not in METHOD_RECORD_KINDS: raise MethodRecordError("row is not method record")
        try: provenance, record = json.loads(row["provenance"]), json.loads(row["value"])
        except Exception as exc: raise MethodRecordError("malformed stored method memory") from exc
        if not isinstance(provenance, dict) or provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION: raise MethodRecordError("unknown method provenance schema")
        normalized = validate_method_record(kind, record)
        if kind in PROMOTED_METHOD_KINDS and normalized["status"] == "PROMOTED":
            receipt_id = normalized.get("promotion_receipt_id")
            receipt = self.db.db.execute("SELECT kind,subject,user_id FROM durable_memory WHERE memory_id=?", (receipt_id,)).fetchone()
            if receipt is None or receipt["kind"] != "method_receipt" or receipt["subject"] != f"PROMOTE:{provenance.get('promotion_source_memory_id')}" or receipt["user_id"] != row["user_id"]: raise MethodRecordError("invalid promotion lineage")
            if provenance.get("admission") != "method_promotion:v2" or provenance.get("promotion_receipt_id") != receipt_id: raise MethodRecordError("unadmitted promoted method")
        return {"memory_id": str(row["memory_id"]), "kind": kind, "subject": str(row["subject"]), "value": normalized,
            "source_turn_id": row["source_turn_id"], "user_id": row["user_id"], "ts": float(row["ts"]), "provenance": provenance}

    def retrieve(self, *, query: str, user_id: str, evidence_status: str, resource_refs: list[str] | None = None,
                 problem_signature: dict[str, list[str]] | None = None, limit: int = 6, min_score: float = MIN_SCORE) -> dict[str, Any]:
        user_id = self._assert_user(user_id)
        if problem_signature is None: raise MethodRecordError("explicit admitted structural signature required")
        if not 1 <= int(limit) <= 24 or not 0 <= float(min_score) <= 1: raise MethodRecordError("invalid method retrieval bounds")
        status = str(evidence_status).upper()
        if status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}: raise MethodRecordError("invalid evidence status")
        signature = canonical_problem_signature(problem_signature); trigger = status in {"UNDERCOVERED", "UNKNOWN"} or self.strategy_intent(query)
        if not trigger: return {"triggered": False, "evidence_status": status, "problem_signature": signature, "methods": [], "counterevidence": [], "factual_status_unchanged": status}
        rows = self.db.db.execute("SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic','failure_pattern','counterexample') AND user_id=? ORDER BY ts DESC LIMIT 2000", (user_id,)).fetchall()
        matches: list[MethodMatch] = []
        for row in rows:
            decoded = self.decode_row(row); record = decoded["value"]
            if record["status"] != "PROMOTED": continue
            score = structural_score(signature, record["problem_signature"])
            if score >= float(min_score): matches.append(MethodMatch(decoded["memory_id"], decoded["kind"], decoded["subject"], score, record, decoded["provenance"]))
        negatives = [m for m in matches if m.kind in NEGATIVE_KINDS]; methods = [m for m in matches if m.kind in PROMOTED_METHOD_KINDS]
        blocked: set[str] = set()
        for negative in negatives:
            if negative.score >= 0.60: blocked.update(negative.record.get("limits_method_ids", []))
        methods = [m for m in methods if m.memory_id not in blocked]
        methods.sort(key=lambda m: (m.score, m.record["calibration"], m.memory_id), reverse=True); negatives.sort(key=lambda m: (m.score, m.memory_id), reverse=True)
        def public(m: MethodMatch) -> dict[str, Any]: return {"memory_id": m.memory_id, "kind": m.kind, "subject": m.subject,
            "structural_score": round(m.score, 6), "record": m.record, "truth_authority": False, "effect_authority": False}
        return {"triggered": True, "evidence_status": status, "problem_signature": signature, "methods": [public(m) for m in methods[:int(limit)]],
            "counterevidence": [public(m) for m in negatives[:int(limit)]], "factual_status_unchanged": status}
