from __future__ import annotations

import json
import math
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .store import UnifiedDB

METHOD_SCHEMA_VERSION = 1
PROMOTION_RECEIPT_SCHEMA = "clayverse.method-promotion/v1"
METHOD_KINDS = frozenset({
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
    "method_receipt",
})
METHOD_RECORD_KINDS = frozenset(METHOD_KINDS - {"method_receipt"})
ROUTABLE_METHOD_KINDS = frozenset({"framework", "heuristic", "failure_pattern", "counterexample"})
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
PROMOTABLE_KINDS = frozenset({"framework", "heuristic"})
VALID_STATUS = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})
MAX_METHOD_JSON_BYTES = 64 * 1024
MAX_LIST_ITEM_CHARS = 2048
MAX_LIST_ITEMS = 256

_LIST_FIELDS = (
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

_GOAL_PATTERNS = {
    "diagnose": ("diagnose", "debug", "root cause", "investigate", "why fail", "failure"),
    "plan": ("plan", "strategy", "architect", "design", "roadmap"),
    "verify": ("verify", "validate", "test", "falsify", "check", "evidence"),
    "compare": ("compare", "versus", "tradeoff", "choose", "select"),
    "recover": ("recover", "restore", "restart", "rollback", "crash", "replay"),
    "optimize": ("optimize", "improve", "latency", "efficient", "budget", "faster"),
}
_MECHANISM_PATTERNS = {
    "concurrency": ("concurrent", "race", "collision", "simultaneous", "parallel"),
    "provenance": ("provenance", "identity", "digest", "sha", "attest", "source binding"),
    "unknown": ("unknown", "insufficient", "uncertain", "missing evidence", "not known"),
    "conflict": ("conflict", "contradict", "disagree", "counterevidence"),
    "privacy": ("privacy", "permission", "cross-session", "cross user", "access boundary"),
    "causal": ("causal", "outcome", "credit", "intervention", "effect"),
    "stateful": ("state", "persistent", "restart", "generation", "recovery", "database"),
    "retrieval": ("retrieval", "memory", "context", "entry point", "recall"),
}
_STRATEGY_PATTERN = re.compile(
    r"(?i)\b(strategy|plan|approach|diagnos|debug|investigat|hypothes|falsif|how should|how do|method)\w*\b"
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


def _norm_atom(value: Any) -> str:
    if not isinstance(value, str):
        raise MethodRecordError("signature atoms must be strings")
    atom = " ".join(value.strip().lower().split())
    if not atom or len(atom) > 160:
        raise MethodRecordError("invalid signature atom")
    return atom


def _bounded_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise MethodRecordError(f"{field} items must be strings")
    item = value.strip()
    if not item or len(item) > MAX_LIST_ITEM_CHARS:
        raise MethodRecordError(f"invalid {field} item")
    return item


def canonical_problem_signature(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict) or not raw or len(raw) > 24:
        raise MethodRecordError("problem_signature must be a non-empty bounded object")
    result: dict[str, list[str]] = {}
    for key, value in raw.items():
        key = _norm_atom(key)
        values = value if isinstance(value, list) else [value]
        if not values or len(values) > 32:
            raise MethodRecordError("invalid problem_signature facet")
        result[key] = sorted({_norm_atom(v) for v in values})
    return dict(sorted(result.items()))


def infer_problem_signature(text: str, resource_refs: list[str] | None = None) -> dict[str, list[str]]:
    """Diagnostic/SHADOW helper only; never an ACTIVE Stage-B serving authority."""
    if not isinstance(text, str) or not text.strip():
        raise MethodRecordError("cannot infer signature from empty text")
    lowered = " ".join(text.lower().split())
    goals = sorted({name for name, needles in _GOAL_PATTERNS.items() if any(n in lowered for n in needles)})
    mechanisms = sorted({name for name, needles in _MECHANISM_PATTERNS.items() if any(n in lowered for n in needles)})
    resources = sorted({str(ref).split(":", 1)[0].lower() for ref in (resource_refs or []) if ":" in str(ref)})
    result: dict[str, list[str]] = {}
    if goals:
        result["goal"] = goals
    if mechanisms:
        result["mechanism"] = mechanisms
    if resources:
        result["resource_shape"] = resources[:12]
    if not result:
        result["goal"] = ["general_problem_solving"]
    return result


def _parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw,
            parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)),
        )
    except Exception as exc:
        raise MethodRecordError(f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise MethodRecordError(f"{label} must be an object")
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodRecordError(f"{label} must be finite canonical JSON") from exc
    return value


def validate_method_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise MethodRecordError("method receipt must be an object")
    required = {
        "schema",
        "candidate_memory_id",
        "promoted_memory_id",
        "action",
        "source_episode_ids",
        "supporting_memory_ids",
        "counterexample_memory_ids",
        "evaluation",
        "ts",
    }
    unknown = sorted(set(receipt) - required)
    missing = sorted(required - set(receipt))
    if unknown:
        raise MethodRecordError("unknown method receipt fields: " + ",".join(unknown))
    if missing:
        raise MethodRecordError("missing method receipt fields: " + ",".join(missing))
    normalized = dict(receipt)
    if receipt["schema"] != PROMOTION_RECEIPT_SCHEMA:
        raise MethodRecordError("unsupported method receipt schema")
    normalized["schema"] = PROMOTION_RECEIPT_SCHEMA
    normalized["candidate_memory_id"] = _bounded_string(
        receipt["candidate_memory_id"], "candidate_memory_id"
    )
    normalized["promoted_memory_id"] = _bounded_string(
        receipt["promoted_memory_id"], "promoted_memory_id"
    )
    if receipt["action"] != "PROMOTE":
        raise MethodRecordError("unsupported method receipt action")
    normalized["action"] = "PROMOTE"
    for field in ("source_episode_ids", "supporting_memory_ids", "counterexample_memory_ids"):
        value = receipt[field]
        if not isinstance(value, list) or len(value) > MAX_LIST_ITEMS:
            raise MethodRecordError(f"{field} must be a bounded list")
        if field == "source_episode_ids" and len(value) < 2:
            raise MethodRecordError("promotion receipt requires at least two source episodes")
        normalized[field] = [_bounded_string(x, field) for x in value]
        if len(set(normalized[field])) != len(normalized[field]):
            raise MethodRecordError(f"duplicate {field} values are forbidden")
    normalized["evaluation"] = _bounded_string(receipt["evaluation"], "evaluation")
    ts = receipt["ts"]
    if isinstance(ts, bool) or not isinstance(ts, (int, float)):
        raise MethodRecordError("invalid method receipt ts")
    ts = float(ts)
    if not math.isfinite(ts) or ts <= 0:
        raise MethodRecordError("invalid method receipt ts")
    normalized["ts"] = ts
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_METHOD_JSON_BYTES:
        raise MethodRecordError("method receipt exceeds bounded serialized size")
    return normalized


def validate_method_record(kind: str, record: Any) -> dict[str, Any]:
    if kind == "method_receipt":
        raise MethodRecordError("method_receipt uses a separate receipt contract")
    if kind not in METHOD_RECORD_KINDS:
        raise MethodRecordError("unrecognized method memory kind")
    if not isinstance(record, dict):
        raise MethodRecordError("method record must be an object")

    required = {
        "problem_signature",
        "goal_shape",
        "abstraction_version",
        "support_count",
        "success_count",
        "failure_count",
        "calibration",
        "last_validated_at",
        "status",
        *_LIST_FIELDS,
    }
    allowed = required | {"limits_method_ids", "method_schema_version"}
    missing = sorted(required.difference(record))
    unknown = sorted(set(record).difference(allowed))
    if missing:
        raise MethodRecordError("missing method fields: " + ",".join(missing))
    if unknown:
        raise MethodRecordError("unknown method fields: " + ",".join(unknown))
    if "method_schema_version" in record and record["method_schema_version"] != METHOD_SCHEMA_VERSION:
        raise MethodRecordError("unsupported method_schema_version")

    normalized = dict(record)
    normalized["problem_signature"] = canonical_problem_signature(record["problem_signature"])
    goal_shape = record["goal_shape"]
    if isinstance(goal_shape, str):
        goal_shape = [goal_shape]
    if not isinstance(goal_shape, list) or not goal_shape or len(goal_shape) > 24:
        raise MethodRecordError("goal_shape must be a non-empty bounded list")
    normalized["goal_shape"] = sorted({_norm_atom(x) for x in goal_shape})

    for field in _LIST_FIELDS:
        value = record[field]
        if not isinstance(value, list) or len(value) > MAX_LIST_ITEMS:
            raise MethodRecordError(f"{field} must be a bounded list")
        normalized[field] = [_bounded_string(x, field) for x in value]
        if len(set(normalized[field])) != len(normalized[field]):
            raise MethodRecordError(f"duplicate {field} values are forbidden")

    if not isinstance(record["abstraction_version"], str) or not record["abstraction_version"].strip():
        raise MethodRecordError("invalid abstraction_version")
    normalized["abstraction_version"] = _bounded_string(record["abstraction_version"], "abstraction_version")

    for field in ("support_count", "success_count", "failure_count"):
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise MethodRecordError(f"{field} must be a non-negative integer")
        normalized[field] = value
    if normalized["success_count"] + normalized["failure_count"] > normalized["support_count"]:
        raise MethodRecordError("success/failure counts exceed support_count")

    calibration = record["calibration"]
    if isinstance(calibration, bool) or not isinstance(calibration, (int, float)):
        raise MethodRecordError("calibration must be in [0,1]")
    calibration = float(calibration)
    if not math.isfinite(calibration) or not 0.0 <= calibration <= 1.0:
        raise MethodRecordError("calibration must be finite and in [0,1]")
    normalized["calibration"] = calibration

    last_validated_at = record["last_validated_at"]
    if isinstance(last_validated_at, bool) or not isinstance(last_validated_at, (int, float)):
        raise MethodRecordError("invalid last_validated_at")
    last_validated_at = float(last_validated_at)
    if not math.isfinite(last_validated_at) or last_validated_at < 0:
        raise MethodRecordError("invalid last_validated_at")
    normalized["last_validated_at"] = last_validated_at

    status = str(record["status"]).upper()
    if status not in VALID_STATUS:
        raise MethodRecordError("invalid method status")
    if kind in CANDIDATE_KINDS and status != "CANDIDATE":
        raise MethodRecordError("candidate kind requires CANDIDATE status")
    if kind in PROMOTABLE_KINDS and status == "CANDIDATE":
        raise MethodRecordError("promoted method kind cannot retain CANDIDATE status")
    if kind in PROMOTABLE_KINDS and status == "PROMOTED":
        if normalized["support_count"] < 2 or len(set(normalized["source_episode_ids"])) < 2:
            raise MethodRecordError("single-episode promotion is forbidden")
        if not normalized["falsifiers"]:
            raise MethodRecordError("promoted method requires explicit falsifier")
        if normalized["calibration"] <= 0.0:
            raise MethodRecordError("promoted method requires non-zero calibration")
    normalized["status"] = status

    limits = record.get("limits_method_ids", [])
    if not isinstance(limits, list) or len(limits) > 128:
        raise MethodRecordError("limits_method_ids must be a bounded list")
    normalized["limits_method_ids"] = [_bounded_string(x, "limits_method_ids") for x in limits]
    if len(set(normalized["limits_method_ids"])) != len(normalized["limits_method_ids"]):
        raise MethodRecordError("duplicate limits_method_ids values are forbidden")
    normalized["method_schema_version"] = METHOD_SCHEMA_VERSION

    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_METHOD_JSON_BYTES:
        raise MethodRecordError("method record exceeds bounded serialized size")
    return normalized


def structural_score(query: dict[str, list[str]], candidate: dict[str, list[str]]) -> float:
    facets = set(query).intersection(candidate)
    if not facets:
        return 0.0
    weighted = 0.0
    total = 0.0
    for facet in sorted(set(query).union(candidate)):
        q = set(query.get(facet, []))
        c = set(candidate.get(facet, []))
        weight = 2.0 if facet in {"goal", "mechanism"} else 1.0
        total += weight
        if q and c:
            weighted += weight * (len(q.intersection(c)) / len(q.union(c)))
    return weighted / max(total, 1.0)


class MethodMemory:
    """Validated method-memory admission and deterministic Stage-B retrieval.

    V1 is deliberately user-scoped. Cross-user/global method promotion requires a later
    explicit declassification/share contract; this baseline cannot broaden session/user
    accessibility merely because an abstraction looks generic.

    Ordinary admission can persist candidates and bounded negative method memory. It
    cannot mint reusable promoted frameworks/heuristics. Positive promotion requires an
    atomic causal lifecycle bound to terminal, causally re-entered source episodes and
    durable candidate-validation receipts whose utility is derived from external effects.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    def _assert_refs(self, record: dict[str, Any], user_id: str, *, require_terminal: bool = False) -> None:
        expected_session = f"session:{user_id}"
        for episode_id in set(record["source_episode_ids"]):
            row = self.db.db.execute(
                "SELECT s.user_id,w.session_id,w.state,"
                "EXISTS(SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id AND c.reentered=1) AS reentered "
                "FROM workspace_episodes w JOIN sessions s ON s.session_id=w.session_id WHERE w.episode_id=?",
                (episode_id,),
            ).fetchone()
            if row is None:
                raise MethodRecordError("unknown source_episode_id")
            if str(row["user_id"]) != user_id or str(row["session_id"]) != expected_session:
                raise MethodRecordError("source episode crosses canonical user/session scope")
            if require_terminal and (
                str(row["state"]) not in {"COMPLETED", "ABORTED"} or not int(row["reentered"])
            ):
                raise MethodRecordError("source episode is not terminal and causally re-entered")

        referenced = set(
            record["supporting_memory_ids"]
            + record["counterexample_memory_ids"]
            + record["limits_method_ids"]
        )
        counter_ids = set(record["counterexample_memory_ids"])
        for memory_id in referenced:
            row = self.db.db.execute(
                "SELECT user_id,kind FROM durable_memory WHERE memory_id=?",
                (memory_id,),
            ).fetchone()
            if row is None:
                raise MethodRecordError("unknown referenced memory_id")
            if str(row["user_id"] or "") != user_id:
                raise MethodRecordError("referenced memory lacks exact user scope")
            if memory_id in counter_ids and str(row["kind"]) not in {"counterexample", "failure_pattern"}:
                raise MethodRecordError("counterexample link must reference counterexample/failure_pattern memory")

    def _assert_source_turn(self, source_turn_id: str | None, user_id: str) -> None:
        if source_turn_id is None:
            return
        source = self.db.db.execute("SELECT user_id FROM turns WHERE turn_id=?", (source_turn_id,)).fetchone()
        if source is None or str(source["user_id"]) != user_id:
            raise MethodRecordError("source turn is absent or cross-user")

    def _decode_method_row(self, row) -> tuple[dict[str, Any], dict[str, Any]]:
        record = validate_method_record(
            str(row["kind"]),
            _parse_json_object(str(row["value"]), "method record"),
        )
        provenance = _parse_json_object(str(row["provenance"]), "method provenance")
        return record, provenance

    def _assert_promotion_lineage(
        self,
        row,
        record: dict[str, Any],
        provenance: dict[str, Any],
        user_id: str,
    ) -> None:
        source_id = provenance.get("promotion_source_memory_id")
        receipt_id = provenance.get("promotion_receipt_id")
        if (
            provenance.get("promotion_transaction_version") != 1
            or not isinstance(source_id, str)
            or not source_id
            or not isinstance(receipt_id, str)
            or not receipt_id
        ):
            raise MethodRecordError("promoted method lacks verified promotion lineage")
        candidate_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1",
            (source_id,),
        ).fetchone()
        receipt_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1",
            (receipt_id,),
        ).fetchone()
        if candidate_row is None or receipt_row is None:
            raise MethodRecordError("promoted method source/receipt is missing")
        candidate, candidate_provenance = self._decode_method_row(candidate_row)
        expected_candidate_kind = "framework_candidate" if str(row["kind"]) == "framework" else "heuristic_candidate"
        if str(candidate_row["kind"]) != expected_candidate_kind or candidate["status"] != "CANDIDATE":
            raise MethodRecordError("promotion source is not the matching candidate kind")
        if str(candidate_row["subject"]) != str(row["subject"]) or str(candidate_row["user_id"]) != user_id:
            raise MethodRecordError("promotion source identity/scope mismatch")
        if (
            candidate_provenance.get("admission") != "method_memory:v1"
            or candidate_provenance.get("user_scope") != user_id
        ):
            raise MethodRecordError("promotion source is not canonically admitted")
        if str(receipt_row["kind"]) != "method_receipt" or str(receipt_row["subject"]) != f"promotion:{source_id}":
            raise MethodRecordError("promotion receipt identity mismatch")
        if str(receipt_row["user_id"] or "") != user_id:
            raise MethodRecordError("promotion receipt crosses user scope")
        receipt = validate_method_receipt(_parse_json_object(str(receipt_row["value"]), "method receipt"))
        receipt_provenance = _parse_json_object(str(receipt_row["provenance"]), "method receipt provenance")
        if (
            receipt["candidate_memory_id"] != source_id
            or receipt["promoted_memory_id"] != str(row["memory_id"])
            or receipt_provenance.get("admission") != "method_memory_receipt:v1"
            or receipt_provenance.get("promotion_source_memory_id") != source_id
            or receipt_provenance.get("promoted_memory_id") != str(row["memory_id"])
            or receipt_provenance.get("promotion_transaction_version") != 1
            or receipt_provenance.get("user_scope") != user_id
        ):
            raise MethodRecordError("promotion receipt provenance mismatch")

        immutable_fields = (
            "problem_signature",
            "preconditions",
            "goal_shape",
            "method_steps",
            "invariants",
            "expected_observations",
            "falsifiers",
            "failure_modes",
            "scope_limits",
            "source_episode_ids",
            "supporting_memory_ids",
            "counterexample_memory_ids",
            "abstraction_version",
            "limits_method_ids",
        )
        if any(record[field] != candidate[field] for field in immutable_fields):
            raise MethodRecordError("promoted method payload drifted from candidate")

        from .method_validation import MethodValidationError, derive_promotion_stats
        try:
            validation = derive_promotion_stats(self.db.db, source_id, candidate, user_id)
        except MethodValidationError as exc:
            raise MethodRecordError("promoted method validation evidence is invalid") from exc
        for field in ("support_count", "success_count", "failure_count", "calibration", "last_validated_at"):
            if record[field] != validation[field]:
                raise MethodRecordError("promoted method statistics drifted from validation receipts")
        expected_validation_ids = validation["validation_receipt_ids"]
        expected_validation_digest = validation["validation_evidence_sha256"]
        if (
            provenance.get("validation_receipt_ids") != expected_validation_ids
            or provenance.get("validation_evidence_sha256") != expected_validation_digest
            or receipt_provenance.get("validation_receipt_ids") != expected_validation_ids
            or receipt_provenance.get("validation_evidence_sha256") != expected_validation_digest
        ):
            raise MethodRecordError("promotion validation provenance mismatch")
        if (
            receipt["source_episode_ids"] != record["source_episode_ids"]
            or receipt["supporting_memory_ids"] != record["supporting_memory_ids"]
            or receipt["counterexample_memory_ids"] != record["counterexample_memory_ids"]
        ):
            raise MethodRecordError("promotion receipt evidence mismatch")
        self._assert_refs(record, user_id, require_terminal=True)

    def admit(
        self,
        *,
        kind: str,
        subject: str,
        record: dict[str, Any],
        source_turn_id: str | None,
        user_id: str | None,
        provenance: dict[str, Any],
    ) -> str:
        if user_id not in {"gabriel", "andreas"}:
            raise MethodRecordError("v1 method admission requires an explicit canonical user scope")
        if kind in PROMOTABLE_KINDS:
            raise MethodRecordError("framework/heuristic admission requires dedicated promotion lifecycle")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 300:
            raise MethodRecordError("invalid method subject")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodRecordError("method admission requires provenance")
        normalized = validate_method_record(kind, record)
        self._assert_refs(
            normalized,
            user_id,
            require_terminal=(kind in ROUTABLE_METHOD_KINDS and normalized["status"] == "PROMOTED"),
        )
        self._assert_source_turn(source_turn_id, user_id)
        stored_provenance = dict(provenance)
        stored_provenance.update({
            "method_schema_version": METHOD_SCHEMA_VERSION,
            "admission": "method_memory:v1",
            "user_scope": user_id,
            "truth_authority": False,
            "effect_authority": False,
        })
        encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return self.db.add_memory(kind, subject.strip(), encoded, source_turn_id, user_id, stored_provenance)

    def promote(
        self,
        *,
        candidate_memory_id: str,
        evaluation: str,
        user_id: str,
        provenance: dict[str, Any],
        source_turn_id: str | None = None,
    ) -> dict[str, str]:
        if user_id not in {"gabriel", "andreas"}:
            raise MethodRecordError("promotion requires an explicit canonical user scope")
        candidate_memory_id = _bounded_string(candidate_memory_id, "candidate_memory_id")
        evaluation = _bounded_string(evaluation, "evaluation")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodRecordError("promotion requires provenance")
        self._assert_source_turn(source_turn_id, user_id)

        with self.db.tx() as db:
            row = db.execute(
                "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1",
                (candidate_memory_id,),
            ).fetchone()
            if row is None:
                raise MethodRecordError("promotion candidate does not exist")
            if str(row["kind"]) not in CANDIDATE_KINDS:
                raise MethodRecordError("promotion source must be a framework/heuristic candidate")
            if str(row["user_id"]) != user_id:
                raise MethodRecordError("promotion candidate crosses user scope")
            candidate, candidate_provenance = self._decode_method_row(row)
            if candidate["status"] != "CANDIDATE":
                raise MethodRecordError("promotion source is not CANDIDATE")
            if (
                candidate_provenance.get("admission") != "method_memory:v1"
                or candidate_provenance.get("user_scope") != user_id
            ):
                raise MethodRecordError("promotion source is not canonically admitted")
            self._assert_refs(candidate, user_id, require_terminal=True)

            from .method_validation import MethodValidationError, derive_promotion_stats
            try:
                validation = derive_promotion_stats(db, candidate_memory_id, candidate, user_id)
            except MethodValidationError as exc:
                raise MethodRecordError("promotion requires validated candidate-use outcome receipts") from exc

            receipt_subject = f"promotion:{candidate_memory_id}"
            prior_receipts = db.execute(
                "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts",
                (receipt_subject,),
            ).fetchall()
            for prior in prior_receipts:
                receipt = validate_method_receipt(
                    _parse_json_object(str(prior["value"]), "method receipt")
                )
                if receipt["action"] == "PROMOTE":
                    raise MethodRecordError("candidate already has a promotion receipt")

            now = time.time()
            promoted_kind = "framework" if str(row["kind"]) == "framework_candidate" else "heuristic"
            promoted_id = str(uuid.uuid4())
            receipt_id = str(uuid.uuid4())
            promoted_record = dict(candidate)
            promoted_record["status"] = "PROMOTED"
            promoted_record["support_count"] = validation["support_count"]
            promoted_record["success_count"] = validation["success_count"]
            promoted_record["failure_count"] = validation["failure_count"]
            promoted_record["calibration"] = validation["calibration"]
            promoted_record["last_validated_at"] = validation["last_validated_at"]
            promoted_record = validate_method_record(promoted_kind, promoted_record)
            receipt = validate_method_receipt({
                "schema": PROMOTION_RECEIPT_SCHEMA,
                "candidate_memory_id": candidate_memory_id,
                "promoted_memory_id": promoted_id,
                "action": "PROMOTE",
                "source_episode_ids": list(promoted_record["source_episode_ids"]),
                "supporting_memory_ids": list(promoted_record["supporting_memory_ids"]),
                "counterexample_memory_ids": list(promoted_record["counterexample_memory_ids"]),
                "evaluation": evaluation,
                "ts": now,
            })
            effective_source_turn = source_turn_id if source_turn_id is not None else row["source_turn_id"]
            self._assert_source_turn(effective_source_turn, user_id)
            receipt_provenance = dict(provenance)
            receipt_provenance.update({
                "method_schema_version": METHOD_SCHEMA_VERSION,
                "admission": "method_memory_receipt:v1",
                "user_scope": user_id,
                "promotion_source_memory_id": candidate_memory_id,
                "promoted_memory_id": promoted_id,
                "promotion_transaction_version": 1,
                "validation_receipt_ids": validation["validation_receipt_ids"],
                "validation_evidence_sha256": validation["validation_evidence_sha256"],
                "truth_authority": False,
                "effect_authority": False,
            })
            promoted_provenance = {
                **candidate_provenance,
                **provenance,
                "method_schema_version": METHOD_SCHEMA_VERSION,
                "admission": "method_memory:v1",
                "user_scope": user_id,
                "promotion_source_memory_id": candidate_memory_id,
                "promotion_receipt_id": receipt_id,
                "promotion_transaction_version": 1,
                "validation_receipt_ids": validation["validation_receipt_ids"],
                "validation_evidence_sha256": validation["validation_evidence_sha256"],
                "truth_authority": False,
                "effect_authority": False,
            }
            db.execute(
                "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    receipt_id,
                    "method_receipt",
                    receipt_subject,
                    json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False),
                    effective_source_turn,
                    user_id,
                    now,
                    json.dumps(receipt_provenance, sort_keys=True, separators=(",", ":"), allow_nan=False),
                ),
            )
            db.execute(
                "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    promoted_id,
                    promoted_kind,
                    str(row["subject"]),
                    json.dumps(promoted_record, sort_keys=True, separators=(",", ":"), allow_nan=False),
                    effective_source_turn,
                    user_id,
                    now,
                    json.dumps(promoted_provenance, sort_keys=True, separators=(",", ":"), allow_nan=False),
                ),
            )
            return {
                "candidate_memory_id": candidate_memory_id,
                "receipt_memory_id": receipt_id,
                "promoted_memory_id": promoted_id,
            }

    @staticmethod
    def strategy_intent(query: str) -> bool:
        return bool(_STRATEGY_PATTERN.search(query or ""))

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        evidence_status: str,
        resource_refs: list[str] | None = None,
        problem_signature: dict[str, list[str]] | None = None,
        limit: int = 6,
        min_score: float = 0.20,
    ) -> dict[str, Any]:
        if user_id not in {"gabriel", "andreas"}:
            raise MethodRecordError("invalid method retrieval user")
        if not 1 <= int(limit) <= 24:
            raise MethodRecordError("invalid method retrieval limit")
        if not 0.0 <= float(min_score) <= 1.0:
            raise MethodRecordError("invalid structural threshold")
        status = str(evidence_status).upper()
        if status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise MethodRecordError("invalid evidence status")
        if problem_signature is None:
            raise MethodRecordError("explicit problem_signature required for Stage-B serving")
        trigger = status in {"UNDERCOVERED", "UNKNOWN"} or self.strategy_intent(query)
        query_signature = canonical_problem_signature(problem_signature)
        if not trigger:
            return {
                "triggered": False,
                "evidence_status": status,
                "problem_signature": query_signature,
                "methods": [],
                "counterevidence": [],
                "factual_status_unchanged": status,
            }

        rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic','failure_pattern','counterexample') "
            "AND user_id=? ORDER BY ts DESC LIMIT 2000",
            (user_id,),
        ).fetchall()
        matches: list[MethodMatch] = []
        for row in rows:
            record, provenance = self._decode_method_row(row)
            if record["status"] != "PROMOTED":
                continue
            if provenance.get("admission") != "method_memory:v1" or provenance.get("user_scope") != user_id:
                raise MethodRecordError("unadmitted or scope-divergent method row")
            if str(row["kind"]) in PROMOTABLE_KINDS:
                self._assert_promotion_lineage(row, record, provenance, user_id)
            else:
                self._assert_refs(record, user_id, require_terminal=True)
            score = structural_score(query_signature, record["problem_signature"])
            if score <= 0.0:
                continue
            matches.append(MethodMatch(str(row["memory_id"]), str(row["kind"]), str(row["subject"]), score, record, provenance))

        limiting = [m for m in matches if m.kind in {"failure_pattern", "counterexample"}]
        methods = [m for m in matches if m.kind in {"framework", "heuristic"}]
        limited_ids = {
            target
            for limiter in limiting
            if limiter.score >= min_score
            for target in limiter.record.get("limits_method_ids", [])
        }
        methods = [m for m in methods if m.memory_id not in limited_ids and m.score >= min_score]
        methods.sort(key=lambda m: (m.score, m.record["calibration"], m.record["last_validated_at"], m.memory_id), reverse=True)
        limiting.sort(key=lambda m: (m.score, m.record["calibration"], m.memory_id), reverse=True)

        def public(match: MethodMatch) -> dict[str, Any]:
            return {
                "memory_id": match.memory_id,
                "kind": match.kind,
                "subject": match.subject,
                "structural_score": round(match.score, 6),
                "problem_signature": match.record["problem_signature"],
                "preconditions": match.record["preconditions"],
                "goal_shape": match.record["goal_shape"],
                "method_steps": match.record["method_steps"],
                "falsifiers": match.record["falsifiers"],
                "failure_modes": match.record["failure_modes"],
                "scope_limits": match.record["scope_limits"],
                "calibration": match.record["calibration"],
                "provenance": match.provenance,
                "truth_authority": False,
                "effect_authority": False,
            }

        return {
            "triggered": True,
            "evidence_status": status,
            "problem_signature": query_signature,
            "methods": [public(m) for m in methods[:limit]],
            "counterevidence": [public(m) for m in limiting[:limit]],
            "factual_status_unchanged": status,
            "generated_at": time.time(),
        }
