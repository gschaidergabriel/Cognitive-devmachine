from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

METHOD_KINDS = (
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
)
SERVING_METHOD_KINDS = ("framework", "heuristic")
NEGATIVE_METHOD_KINDS = ("failure_pattern", "counterexample")
METHOD_STATUSES = ("CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED")

_METHOD_INTENT = re.compile(
    r"(?i)\b(strategy|strateg(?:y|ie)|plan(?:ning|en)?|diagnos(?:e|is|tik)|"
    r"hypothes(?:is|e|es|en)|investigat(?:e|ion)|untersuch(?:en|ung)|"
    r"debug|troubleshoot|how should|wie soll|vorgehen|methode|method)\b"
)
_GOAL_PATTERNS = (
    ("diagnose", re.compile(r"(?i)\b(debug|diagnos|troubleshoot|error|fail|broken|crash|why|warum)\b")),
    ("design", re.compile(r"(?i)\b(design|architect|architecture|build|implement|entwerf|baue|implementier)\b")),
    ("compare", re.compile(r"(?i)\b(compare|evaluate|choose|tradeoff|versus|vs\.?|vergleich|bewert|auswahl)\b")),
    ("optimize", re.compile(r"(?i)\b(optimi[sz]|improve|reduce|faster|latency|efficien|verbesser|schneller)\b")),
    ("recover", re.compile(r"(?i)\b(recover|rollback|restore|restart|recovery|wiederherstell|zurückroll)\b")),
    ("investigate", re.compile(r"(?i)\b(test|verify|measure|falsif|experiment|inspect|research|prüf|mess|forsch|untersuch)\b")),
)
_FACET_PATTERNS = (
    ("concurrency", re.compile(r"(?i)\b(concurr|race|parallel|simultan|lock|lease|epoch|generation)\b")),
    ("state-continuity", re.compile(r"(?i)\b(state|memory|persist|restart|recovery|checkpoint|snapshot|zustand|speicher)\b")),
    ("security-boundary", re.compile(r"(?i)\b(auth|security|permission|capabilit|clerk|jwt|privacy|recht|sicher)\b")),
    ("retrieval", re.compile(r"(?i)\b(retriev|memory|microclay|entry.?point|context|abruf|erinner)\b")),
    ("causal-evidence", re.compile(r"(?i)\b(causal|outcome|evidence|falsif|receipt|provenance|kausal|evidenz|beleg)\b")),
    ("runtime-container", re.compile(r"(?i)\b(runtime|container|docker|oci|process|terminal|sandbox)\b")),
    ("network-io", re.compile(r"(?i)\b(network|socket|tls|http|websocket|dns|stream|netz)\b")),
    ("data-integrity", re.compile(r"(?i)\b(data|schema|sqlite|database|db|integrity|migration|daten)\b")),
    ("performance", re.compile(r"(?i)\b(latency|throughput|budget|token|alloc|copy|performance|leistung)\b")),
    ("conflict", re.compile(r"(?i)\b(conflict|contradict|counterexample|gegenhypoth|widerspruch)\b")),
)

_METHOD_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS method_records(
  method_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN ('framework_candidate','framework','heuristic_candidate','heuristic','failure_pattern','counterexample')),
  name TEXT NOT NULL,
  problem_signature TEXT NOT NULL,
  preconditions TEXT NOT NULL,
  goal_shape TEXT NOT NULL,
  method_steps TEXT NOT NULL,
  invariants TEXT NOT NULL,
  expected_observations TEXT NOT NULL,
  falsifiers TEXT NOT NULL,
  failure_modes TEXT NOT NULL,
  scope_limits TEXT NOT NULL,
  source_episode_ids TEXT NOT NULL,
  supporting_memory_ids TEXT NOT NULL,
  counterexample_memory_ids TEXT NOT NULL,
  target_method_ids TEXT NOT NULL DEFAULT '[]',
  provenance TEXT NOT NULL,
  abstraction_version INTEGER NOT NULL,
  support_count INTEGER NOT NULL,
  success_count INTEGER NOT NULL,
  failure_count INTEGER NOT NULL,
  calibration REAL NOT NULL,
  last_validated_at REAL NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','PROMOTED','DEMOTED','RETIRED')),
  user_id TEXT REFERENCES users(user_id),
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_method_records_status_kind ON method_records(status,kind,updated_at DESC);
CREATE TABLE IF NOT EXISTS method_use_receipts(
  receipt_id TEXT PRIMARY KEY,
  causal_id TEXT NOT NULL UNIQUE,
  turn_id TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  generation INTEGER NOT NULL,
  query_hash TEXT NOT NULL,
  signature_hash TEXT NOT NULL,
  evidence_status TEXT NOT NULL,
  trigger TEXT NOT NULL,
  selected_method_ids TEXT NOT NULL,
  blocked_method_ids TEXT NOT NULL,
  snapshot TEXT NOT NULL,
  ts REAL NOT NULL
);
'''


class MethodMemoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class QuerySignature:
    goal_shape: str
    facets: tuple[str, ...]
    resource_types: tuple[str, ...]

    def public(self) -> dict[str, Any]:
        return {
            "goal_shape": self.goal_shape,
            "facets": list(self.facets),
            "resource_types": list(self.resource_types),
        }


_REQUIRED_LIST_FIELDS = (
    "preconditions",
    "method_steps",
    "invariants",
    "expected_observations",
    "falsifiers",
    "failure_modes",
    "scope_limits",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
)


def _as_string_list(value: Any, *, field: str, max_items: int = 64, max_chars: int = 2_000) -> list[str]:
    if not isinstance(value, list) or len(value) > max_items:
        raise MethodMemoryError(f"{field} must be a bounded list")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > max_chars:
            raise MethodMemoryError(f"{field} contains invalid item")
        out.append(item.strip())
    return out


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodMemoryError("method record is not canonical JSON") from exc


def infer_query_signature(query: str, resource_refs: list[str] | tuple[str, ...]) -> QuerySignature:
    text = str(query or "")
    goal = "investigate"
    for candidate, pattern in _GOAL_PATTERNS:
        if pattern.search(text):
            goal = candidate
            break
    facets = {name for name, pattern in _FACET_PATTERNS if pattern.search(text)}
    resource_types = set()
    for ref in resource_refs or ():
        if not isinstance(ref, str) or ":" not in ref:
            continue
        kind = ref.split(":", 1)[0].strip().lower()
        if kind:
            resource_types.add(kind[:32])
    if resource_types:
        facets.add("explicit-resource")
    return QuerySignature(goal, tuple(sorted(facets)), tuple(sorted(resource_types)))


def should_activate_method_stage(evidence_status: str, query: str) -> str | None:
    status = str(evidence_status or "UNKNOWN").upper()
    if status in {"UNKNOWN", "UNDERCOVERED"}:
        return f"EVIDENCE_{status}"
    if _METHOD_INTENT.search(str(query or "")):
        return "EXPLICIT_METHOD_INTENT"
    return None


class MethodMemory:
    """Validated UnifiedDB method memory and deterministic Stage-B retrieval.

    It changes method accessibility only. It never changes factual evidence status,
    truth authority, effect authority, user rights, or MicroClay evidence ranking.
    """

    MAX_RECORD_CHARS = 32_000
    MAX_CONTEXT_CHARS = 24_000
    MAX_METHODS = 3
    MAX_NEGATIVES = 6
    MIN_STRUCTURAL_SCORE = 0.35
    BLOCKING_NEGATIVE_SCORE = 0.72

    def __init__(self, db):
        self.db = db
        self.db.db.executescript(_METHOD_SCHEMA)
        self.db.db.execute(
            "INSERT INTO meta(key,value) VALUES('method_schema_version','1') "
            "ON CONFLICT(key) DO UPDATE SET value='1'"
        )

    @staticmethod
    def _normalize_problem_signature(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise MethodMemoryError("problem_signature must be an object")
        goal = value.get("goal_shape")
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 80:
            raise MethodMemoryError("problem_signature.goal_shape invalid")
        facets = _as_string_list(value.get("facets", []), field="problem_signature.facets", max_items=32, max_chars=120)
        resource_types = _as_string_list(value.get("resource_types", []), field="problem_signature.resource_types", max_items=16, max_chars=64)
        return {
            "goal_shape": goal.strip().lower(),
            "facets": sorted(set(x.lower() for x in facets)),
            "resource_types": sorted(set(x.lower() for x in resource_types)),
        }

    @classmethod
    def validate_record(cls, record: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise MethodMemoryError("method record must be an object")
        kind = record.get("kind")
        if kind not in METHOD_KINDS:
            raise MethodMemoryError("invalid method kind")
        name = record.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 240:
            raise MethodMemoryError("invalid method name")
        signature = cls._normalize_problem_signature(record.get("problem_signature"))
        goal_shape = record.get("goal_shape")
        if not isinstance(goal_shape, str) or goal_shape.strip().lower() != signature["goal_shape"]:
            raise MethodMemoryError("goal_shape must match problem_signature.goal_shape")
        normalized: dict[str, Any] = {
            "kind": kind,
            "name": name.strip(),
            "problem_signature": signature,
            "goal_shape": signature["goal_shape"],
        }
        for field in _REQUIRED_LIST_FIELDS:
            normalized[field] = _as_string_list(record.get(field), field=field)
        normalized["target_method_ids"] = _as_string_list(record.get("target_method_ids", []), field="target_method_ids", max_items=64, max_chars=128)
        provenance = record.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodMemoryError("provenance must be a non-empty object")
        normalized["provenance"] = provenance
        for field in ("abstraction_version", "support_count", "success_count", "failure_count"):
            value = record.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise MethodMemoryError(f"{field} must be a non-negative integer")
            normalized[field] = int(value)
        calibration = record.get("calibration")
        if not isinstance(calibration, (int, float)) or isinstance(calibration, bool) or not math.isfinite(float(calibration)):
            raise MethodMemoryError("calibration must be finite")
        if not 0.0 <= float(calibration) <= 1.0:
            raise MethodMemoryError("calibration outside [0,1]")
        normalized["calibration"] = float(calibration)
        last_validated_at = record.get("last_validated_at")
        if not isinstance(last_validated_at, (int, float)) or isinstance(last_validated_at, bool) or not math.isfinite(float(last_validated_at)) or float(last_validated_at) < 0:
            raise MethodMemoryError("last_validated_at invalid")
        normalized["last_validated_at"] = float(last_validated_at)
        status = record.get("status")
        if status not in METHOD_STATUSES:
            raise MethodMemoryError("invalid method status")
        if kind in {"framework_candidate", "heuristic_candidate"} and status != "CANDIDATE":
            raise MethodMemoryError("candidate method kind must remain CANDIDATE")
        if kind in SERVING_METHOD_KINDS and status == "CANDIDATE":
            raise MethodMemoryError("candidate framework/heuristic must use candidate kind")
        normalized["status"] = status
        if len(_canonical_json(normalized)) > cls.MAX_RECORD_CHARS:
            raise MethodMemoryError("method record exceeds size bound")
        return normalized

    def admit(self, record: dict[str, Any], *, user_id: str | None = None, method_id: str | None = None) -> str:
        normalized = self.validate_record(record)
        method_id = str(method_id or uuid.uuid4())
        now = time.time()
        self.db.db.execute(
            "INSERT INTO method_records(method_id,kind,name,problem_signature,preconditions,goal_shape,method_steps,"
            "invariants,expected_observations,falsifiers,failure_modes,scope_limits,source_episode_ids,"
            "supporting_memory_ids,counterexample_memory_ids,target_method_ids,provenance,abstraction_version,"
            "support_count,success_count,failure_count,calibration,last_validated_at,status,user_id,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                method_id, normalized["kind"], normalized["name"], _canonical_json(normalized["problem_signature"]),
                _canonical_json(normalized["preconditions"]), normalized["goal_shape"], _canonical_json(normalized["method_steps"]),
                _canonical_json(normalized["invariants"]), _canonical_json(normalized["expected_observations"]),
                _canonical_json(normalized["falsifiers"]), _canonical_json(normalized["failure_modes"]),
                _canonical_json(normalized["scope_limits"]), _canonical_json(normalized["source_episode_ids"]),
                _canonical_json(normalized["supporting_memory_ids"]), _canonical_json(normalized["counterexample_memory_ids"]),
                _canonical_json(normalized["target_method_ids"]), _canonical_json(normalized["provenance"]),
                normalized["abstraction_version"], normalized["support_count"], normalized["success_count"],
                normalized["failure_count"], normalized["calibration"], normalized["last_validated_at"], normalized["status"],
                user_id, now, now,
            ),
        )
        return method_id

    @staticmethod
    def _row_public(row) -> dict[str, Any]:
        return {
            "method_id": str(row["method_id"]), "kind": str(row["kind"]), "name": str(row["name"]),
            "problem_signature": json.loads(row["problem_signature"]), "preconditions": json.loads(row["preconditions"]),
            "goal_shape": str(row["goal_shape"]), "method_steps": json.loads(row["method_steps"]),
            "invariants": json.loads(row["invariants"]), "expected_observations": json.loads(row["expected_observations"]),
            "falsifiers": json.loads(row["falsifiers"]), "failure_modes": json.loads(row["failure_modes"]),
            "scope_limits": json.loads(row["scope_limits"]), "source_episode_ids": json.loads(row["source_episode_ids"]),
            "supporting_memory_ids": json.loads(row["supporting_memory_ids"]),
            "counterexample_memory_ids": json.loads(row["counterexample_memory_ids"]),
            "target_method_ids": json.loads(row["target_method_ids"]), "provenance": json.loads(row["provenance"]),
            "abstraction_version": int(row["abstraction_version"]), "support_count": int(row["support_count"]),
            "success_count": int(row["success_count"]), "failure_count": int(row["failure_count"]),
            "calibration": float(row["calibration"]), "last_validated_at": float(row["last_validated_at"]),
            "status": str(row["status"]),
        }

    @staticmethod
    def _structural_score(query_sig: QuerySignature, record: dict[str, Any]) -> float:
        rec_sig = record["problem_signature"]
        goal_match = 1.0 if query_sig.goal_shape == rec_sig.get("goal_shape") else 0.0
        q_facets, r_facets = set(query_sig.facets), set(rec_sig.get("facets", []))
        facet_union = q_facets | r_facets
        facet_jaccard = len(q_facets & r_facets) / len(facet_union) if facet_union else 0.0
        q_resources, r_resources = set(query_sig.resource_types), set(rec_sig.get("resource_types", []))
        resource_union = q_resources | r_resources
        resource_jaccard = len(q_resources & r_resources) / len(resource_union) if resource_union else 0.0
        return max(0.0, min(1.0, 0.50 * goal_match + 0.40 * facet_jaccard + 0.10 * resource_jaccard))

    def _rows(self, user_id: str):
        return self.db.db.execute(
            "SELECT * FROM method_records WHERE status='PROMOTED' AND (user_id IS NULL OR user_id=?) "
            "ORDER BY updated_at DESC, method_id LIMIT 1000", (user_id,)
        ).fetchall()

    def retrieve(self, *, query: str, resource_refs: list[str], evidence_status: str, user_id: str,
                 session_id: str, turn_id: str, episode_id: str, causal_id: str, generation: int) -> dict[str, Any]:
        self.db.assert_live_generation(session_id, generation)
        evidence_status = str(evidence_status or "UNKNOWN").upper()
        trigger = should_activate_method_stage(evidence_status, query)
        query_hash = hashlib.sha256(str(query).encode("utf-8")).hexdigest()
        signature = infer_query_signature(query, resource_refs)
        signature_payload = signature.public()
        signature_hash = hashlib.sha256(_canonical_json(signature_payload).encode("utf-8")).hexdigest()
        existing = self.db.db.execute("SELECT * FROM method_use_receipts WHERE causal_id=?", (causal_id,)).fetchone()
        if existing:
            if (
                existing["turn_id"] != turn_id or existing["episode_id"] != episode_id or
                existing["session_id"] != session_id or existing["user_id"] != user_id or
                int(existing["generation"]) != int(generation) or existing["query_hash"] != query_hash or
                existing["signature_hash"] != signature_hash or existing["evidence_status"] != evidence_status or
                existing["trigger"] != trigger
            ):
                raise MethodMemoryError("method_retrieval_identity")
            snapshot = json.loads(existing["snapshot"])
            snapshot["receipt"]["replayed"] = True
            return snapshot
        if trigger is None:
            return {
                "status": "NOT_TRIGGERED", "query_signature": signature_payload, "methods": [], "counterevidence": [],
                "receipt": {"mode": "DETERMINISTIC_BASELINE", "status": "NOT_TRIGGERED", "truth_authority": False,
                            "effect_authority": False, "fact_status_unchanged": evidence_status},
            }

        ranked: list[tuple[float, dict[str, Any]]] = []
        negatives: list[tuple[float, dict[str, Any]]] = []
        for row in self._rows(user_id):
            try:
                record = self._row_public(row)
                self.validate_record(record)
            except (MethodMemoryError, ValueError, TypeError, json.JSONDecodeError):
                continue
            score = self._structural_score(signature, record)
            if score < self.MIN_STRUCTURAL_SCORE:
                continue
            calibrated = score * (0.70 + 0.30 * float(record["calibration"]))
            item = {**record, "structural_score": round(score, 6), "retrieval_score": round(calibrated, 6)}
            if record["kind"] in SERVING_METHOD_KINDS:
                ranked.append((calibrated, item))
            elif record["kind"] in NEGATIVE_METHOD_KINDS:
                negatives.append((calibrated, item))
        ranked.sort(key=lambda x: (x[0], x[1]["last_validated_at"], x[1]["method_id"]), reverse=True)
        negatives.sort(key=lambda x: (x[0], x[1]["last_validated_at"], x[1]["method_id"]), reverse=True)

        blocking_targets: set[str] = set()
        counterevidence: list[dict[str, Any]] = []
        for score, item in negatives[: self.MAX_NEGATIVES]:
            counterevidence.append(item)
            if score >= self.BLOCKING_NEGATIVE_SCORE:
                blocking_targets.update(str(x) for x in item.get("target_method_ids", []))
        methods: list[dict[str, Any]] = []
        for _, item in ranked:
            if item["method_id"] in blocking_targets:
                continue
            methods.append(item)
            if len(methods) >= self.MAX_METHODS:
                break

        status = "PRESENT" if methods else "UNKNOWN"
        receipt_id = str(uuid.uuid4())
        receipt = {
            "receipt_id": receipt_id, "mode": "DETERMINISTIC_BASELINE", "status": status, "trigger": trigger,
            "query_sha256": query_hash, "signature_sha256": signature_hash, "turn_id": turn_id, "episode_id": episode_id,
            "causal_id": causal_id, "session_id": session_id, "user_id": user_id, "generation": int(generation),
            "selected_method_ids": [x["method_id"] for x in methods], "blocked_method_ids": sorted(blocking_targets),
            "truth_authority": False, "effect_authority": False, "fact_status_unchanged": evidence_status,
        }
        snapshot = {"status": status, "query_signature": signature_payload, "methods": methods,
                    "counterevidence": counterevidence, "receipt": receipt}
        encoded_snapshot = _canonical_json(snapshot)
        if len(encoded_snapshot) > self.MAX_CONTEXT_CHARS:
            while len(encoded_snapshot) > self.MAX_CONTEXT_CHARS and counterevidence:
                counterevidence.pop(); snapshot["counterevidence"] = counterevidence; encoded_snapshot = _canonical_json(snapshot)
            while len(encoded_snapshot) > self.MAX_CONTEXT_CHARS and methods:
                methods.pop(); snapshot["methods"] = methods; snapshot["status"] = "PRESENT" if methods else "UNKNOWN"
                receipt["selected_method_ids"] = [x["method_id"] for x in methods]; receipt["status"] = snapshot["status"]
                encoded_snapshot = _canonical_json(snapshot)
            if len(encoded_snapshot) > self.MAX_CONTEXT_CHARS:
                raise MethodMemoryError("method context cannot satisfy size bound")
        self.db.db.execute(
            "INSERT INTO method_use_receipts(receipt_id,causal_id,turn_id,episode_id,session_id,user_id,generation,"
            "query_hash,signature_hash,evidence_status,trigger,selected_method_ids,blocked_method_ids,snapshot,ts) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (receipt_id, causal_id, turn_id, episode_id, session_id, user_id, int(generation), query_hash, signature_hash,
             evidence_status, trigger, _canonical_json(receipt["selected_method_ids"]), _canonical_json(receipt["blocked_method_ids"]),
             encoded_snapshot, time.time()),
        )
        return snapshot
