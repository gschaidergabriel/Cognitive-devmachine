from __future__ import annotations

import json
import math
import re
import time
from typing import Any

METHOD_SCHEMA_VERSION = 1
METHOD_KINDS = {
    "framework_candidate", "framework", "heuristic_candidate", "heuristic",
    "failure_pattern", "counterexample", "method_receipt",
}
CANDIDATE_KINDS = {"framework_candidate", "heuristic_candidate"}
PROMOTABLE_KINDS = {"framework", "heuristic"}
NEGATIVE_METHOD_KINDS = {"failure_pattern", "counterexample"}
LIFECYCLE = {"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"}
_SIGNATURE_KEY = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

_METHOD_FIELDS = {
    "problem_signature", "preconditions", "goal_shape", "method_steps", "invariants",
    "expected_observations", "falsifiers", "failure_modes", "scope_limits",
    "source_episode_ids", "supporting_memory_ids", "counterexample_memory_ids",
    "abstraction_version", "support_count", "success_count", "failure_count",
    "calibration", "last_validated_at", "status",
}
_LIFECYCLE_RECEIPT_REQUIRED = {
    "method_memory_id", "action", "source_episode_ids", "supporting_memory_ids",
    "counterexample_memory_ids", "evaluation", "ts",
}
_LIFECYCLE_RECEIPT_OPTIONAL = {"validation_receipt_ids", "validation_evidence_sha256"}
_RECEIPT_ACTIONS = {"ABSTRACT", "PROMOTE", "DEMOTE", "RETIRE", "USE", "REJECT"}


class MethodMemoryValidationError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodMemoryValidationError("method memory must be canonical JSON") from exc


def _as_object(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except Exception as exc:
            raise MethodMemoryValidationError("method memory value must be valid finite JSON") from exc
    else:
        parsed = value
    if not isinstance(parsed, dict): raise MethodMemoryValidationError("method memory value must be an object")
    _canonical_json(parsed)
    return parsed


def _str(value: Any, field: str, *, max_len: int = 4096) -> str:
    if not isinstance(value, str): raise MethodMemoryValidationError(f"{field} must be a string")
    value = value.strip()
    if not value or len(value) > max_len: raise MethodMemoryValidationError(f"{field} must be non-empty and bounded")
    return value


def _str_list(value: Any, field: str, *, min_items: int = 0, max_items: int = 256) -> list[str]:
    if not isinstance(value, list) or not min_items <= len(value) <= max_items:
        raise MethodMemoryValidationError(f"{field} has invalid item count")
    result = [_str(item, field, max_len=1024) for item in value]
    if len(set(result)) != len(result): raise MethodMemoryValidationError(f"{field} contains duplicates")
    return result


def _count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MethodMemoryValidationError(f"{field} must be a non-negative integer")
    return value


def _calibration(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MethodMemoryValidationError("calibration must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise MethodMemoryValidationError("calibration must be finite and in [0,1]")
    return result


def _timestamp(value: Any, field: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable: return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MethodMemoryValidationError(f"{field} must be a unix timestamp")
    result = float(value)
    if not math.isfinite(result) or result <= 0: raise MethodMemoryValidationError(f"{field} must be positive and finite")
    return result


def canonical_problem_signature(value: Any) -> dict[str, tuple[str, ...]]:
    """Structured signature only. Free-form prompt text is never inferred here."""
    if not isinstance(value, dict) or not 2 <= len(value) <= 24:
        raise MethodMemoryValidationError("problem_signature requires 2..24 structural facets")
    normalized: dict[str, tuple[str, ...]] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not _SIGNATURE_KEY.fullmatch(key):
            raise MethodMemoryValidationError("problem_signature keys must be bounded snake_case identifiers")
        values = [raw] if isinstance(raw, str) else raw
        items = _str_list(values, f"problem_signature.{key}", min_items=1, max_items=32)
        norm = tuple(sorted({" ".join(item.lower().split()) for item in items}))
        if len(norm) != len(items): raise MethodMemoryValidationError(f"problem_signature.{key} contains normalized duplicates")
        normalized[key] = norm
    return dict(sorted(normalized.items()))


def structural_similarity(query: dict[str, tuple[str, ...]], candidate: dict[str, tuple[str, ...]]) -> float:
    """Symmetric facet-aware overlap; missing/extra facets count against the match."""
    scores: list[float] = []
    for facet in sorted(set(query) | set(candidate)):
        q_values, c_values = query.get(facet), candidate.get(facet)
        if not q_values or not c_values:
            scores.append(0.0); continue
        q, c = set(q_values), set(c_values)
        scores.append(len(q & c) / max(1, len(q | c)))
    return sum(scores) / max(1, len(scores))


def _validate_provenance(provenance: Any, *, promoted: bool = False) -> dict[str, Any]:
    if not isinstance(provenance, dict) or not provenance:
        raise MethodMemoryValidationError("method memory provenance must be a non-empty object")
    canonical = json.loads(_canonical_json(provenance))
    if promoted and not isinstance(canonical.get("promotion_receipt_id"), str):
        raise MethodMemoryValidationError("promoted method requires promotion_receipt_id provenance")
    return canonical


def validate_method_record(kind: str, value: Any, provenance: Any) -> dict[str, Any]:
    if kind not in METHOD_KINDS - {"method_receipt"}: raise MethodMemoryValidationError("unsupported method memory kind")
    record = _as_object(value); unknown = set(record) - _METHOD_FIELDS; missing = _METHOD_FIELDS - set(record)
    if unknown: raise MethodMemoryValidationError(f"unknown method fields: {','.join(sorted(unknown))}")
    if missing: raise MethodMemoryValidationError(f"missing method fields: {','.join(sorted(missing))}")
    canonical_problem_signature(record["problem_signature"])
    _str_list(record["preconditions"], "preconditions", min_items=1); _str(record["goal_shape"], "goal_shape", max_len=1024)
    _str_list(record["method_steps"], "method_steps", min_items=1); _str_list(record["invariants"], "invariants", min_items=1)
    _str_list(record["expected_observations"], "expected_observations", min_items=1); _str_list(record["falsifiers"], "falsifiers", min_items=1)
    _str_list(record["failure_modes"], "failure_modes", min_items=1); _str_list(record["scope_limits"], "scope_limits", min_items=1)
    source_episode_ids = _str_list(record["source_episode_ids"], "source_episode_ids", min_items=1)
    _str_list(record["supporting_memory_ids"], "supporting_memory_ids"); _str_list(record["counterexample_memory_ids"], "counterexample_memory_ids")
    _str(record["abstraction_version"], "abstraction_version", max_len=128)
    support_count = _count(record["support_count"], "support_count"); success_count = _count(record["success_count"], "success_count")
    failure_count = _count(record["failure_count"], "failure_count"); calibration = _calibration(record["calibration"])
    status = _str(record["status"], "status", max_len=32).upper()
    if status not in LIFECYCLE: raise MethodMemoryValidationError("invalid method lifecycle status")
    if support_count < success_count + failure_count: raise MethodMemoryValidationError("support_count cannot be smaller than success_count + failure_count")
    if kind in CANDIDATE_KINDS:
        if status != "CANDIDATE": raise MethodMemoryValidationError("candidate kind must remain CANDIDATE")
        _timestamp(record["last_validated_at"], "last_validated_at", nullable=True); _validate_provenance(provenance)
    elif kind in PROMOTABLE_KINDS:
        if status == "CANDIDATE": raise MethodMemoryValidationError("framework/heuristic cannot retain CANDIDATE status")
        _timestamp(record["last_validated_at"], "last_validated_at"); promoted = status == "PROMOTED"; _validate_provenance(provenance, promoted=promoted)
        if promoted:
            if support_count < 2 or success_count < 2 or len(source_episode_ids) < 2:
                raise MethodMemoryValidationError("promoted reusable method requires multi-episode support and repeated validated success")
            if calibration <= 0.0: raise MethodMemoryValidationError("promoted method requires non-zero calibration")
    else:
        if status == "CANDIDATE": raise MethodMemoryValidationError("negative method evidence cannot be CANDIDATE")
        _timestamp(record["last_validated_at"], "last_validated_at"); _validate_provenance(provenance)
    canonical = json.loads(_canonical_json(record)); canonical["status"] = status; return canonical


def validate_lifecycle_receipt(value: Any, provenance: Any) -> dict[str, Any]:
    receipt = _as_object(value); allowed = _LIFECYCLE_RECEIPT_REQUIRED | _LIFECYCLE_RECEIPT_OPTIONAL
    unknown = set(receipt) - allowed; missing = _LIFECYCLE_RECEIPT_REQUIRED - set(receipt)
    if unknown: raise MethodMemoryValidationError(f"unknown method receipt fields: {','.join(sorted(unknown))}")
    if missing: raise MethodMemoryValidationError(f"missing method receipt fields: {','.join(sorted(missing))}")
    _str(receipt["method_memory_id"], "method_memory_id", max_len=256); action = _str(receipt["action"], "action", max_len=32).upper()
    if action not in _RECEIPT_ACTIONS: raise MethodMemoryValidationError("invalid method receipt action")
    _str_list(receipt["source_episode_ids"], "source_episode_ids", min_items=1); _str_list(receipt["supporting_memory_ids"], "supporting_memory_ids")
    _str_list(receipt["counterexample_memory_ids"], "counterexample_memory_ids"); _str(receipt["evaluation"], "evaluation", max_len=8192); _timestamp(receipt["ts"], "ts")
    if action == "PROMOTE":
        ids = _str_list(receipt.get("validation_receipt_ids"), "validation_receipt_ids", min_items=2)
        digest = _str(receipt.get("validation_evidence_sha256"), "validation_evidence_sha256", max_len=64)
        if len(digest) != 64: raise MethodMemoryValidationError("promotion validation digest must be sha256")
        receipt["validation_receipt_ids"] = ids; receipt["validation_evidence_sha256"] = digest
    elif set(receipt) & _LIFECYCLE_RECEIPT_OPTIONAL:
        raise MethodMemoryValidationError("validation evidence fields are reserved for PROMOTE receipts")
    _validate_provenance(provenance); canonical = json.loads(_canonical_json(receipt)); canonical["action"] = action; return canonical


def validate_method_receipt(value: Any, provenance: Any) -> dict[str, Any]:
    receipt = _as_object(value)
    if "schema" in receipt:
        from .method_validation import MethodValidationError, validate_validation_method_receipt
        try: validation = validate_validation_method_receipt(receipt)
        except MethodValidationError as exc: raise MethodMemoryValidationError(str(exc)) from exc
        if validation is None: raise MethodMemoryValidationError("unsupported method receipt schema")
        _validate_provenance(provenance); return validation
    return validate_lifecycle_receipt(receipt, provenance)


def canonical_method_value(kind: str, value: Any, provenance: Any) -> str:
    canonical = validate_method_receipt(value, provenance) if kind == "method_receipt" else validate_method_record(kind, value, provenance)
    return _canonical_json(canonical)


class MethodMemoryManager:
    """Canonical durable-memory admission, held-out validation and append-only lifecycle."""
    def __init__(self, db): self.db = db
    @staticmethod
    def _canonical_user(user_id: Any) -> str:
        if user_id not in {"gabriel", "andreas"}: raise MethodMemoryValidationError("method memory v1 requires explicit canonical user scope")
        return str(user_id)

    def admit(self, kind: str, subject: str, value: Any, source_turn_id: str | None, user_id: str | None, provenance: dict[str, Any]) -> str:
        if kind not in METHOD_KINDS: raise MethodMemoryValidationError("kind is not method memory")
        user_id = self._canonical_user(user_id)
        if kind in PROMOTABLE_KINDS: raise MethodMemoryValidationError("framework/heuristic admission requires the dedicated promotion lifecycle")
        _str(subject, "subject", max_len=1024)
        canonical_provenance = {**_validate_provenance(provenance), "method_schema_version": METHOD_SCHEMA_VERSION,
                                "admission": provenance.get("admission", "method_memory:v1"), "user_scope": user_id,
                                "truth_authority": False, "effect_authority": False}
        canonical_value = canonical_method_value(kind, value, canonical_provenance)
        return self.db.add_memory(kind, subject, canonical_value, source_turn_id, user_id, canonical_provenance)

    def _assert_promotion_references(self, candidate: dict[str, Any]) -> None:
        record = candidate["value"]; user_id = self._canonical_user(candidate["user_id"]); source_ids = list(record["source_episode_ids"])
        placeholders = ",".join("?" for _ in source_ids)
        rows = self.db.db.execute(
            "SELECT w.episode_id,w.state,w.session_id,s.user_id,EXISTS(SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id AND c.reentered=1) AS reentered "
            "FROM workspace_episodes w JOIN sessions s ON s.session_id=w.session_id " + f"WHERE w.episode_id IN ({placeholders})", tuple(source_ids)).fetchall()
        found = {str(row["episode_id"]): row for row in rows}
        if set(found) != set(source_ids): raise MethodMemoryValidationError("promotion source episode evidence is incomplete")
        for episode_id, row in found.items():
            if row["state"] not in {"COMPLETED", "ABORTED"} or not int(row["reentered"]):
                raise MethodMemoryValidationError(f"promotion source episode is not terminal and causally re-entered: {episode_id}")
            if str(row["user_id"]) != user_id or str(row["session_id"]) != f"session:{user_id}":
                raise MethodMemoryValidationError("promotion source episode crosses user/session scope")
        evidence_ids = list(dict.fromkeys(list(record["supporting_memory_ids"]) + list(record["counterexample_memory_ids"])))
        if evidence_ids:
            placeholders = ",".join("?" for _ in evidence_ids)
            memory_rows = self.db.db.execute(f"SELECT memory_id,kind,user_id FROM durable_memory WHERE memory_id IN ({placeholders})", tuple(evidence_ids)).fetchall()
            by_id = {str(row["memory_id"]): row for row in memory_rows}
            if set(by_id) != set(evidence_ids): raise MethodMemoryValidationError("promotion referenced memory evidence is incomplete")
            for memory_id, row in by_id.items():
                if str(row["user_id"] or "") != user_id: raise MethodMemoryValidationError("promotion referenced memory lacks exact user scope")
                if memory_id in record["supporting_memory_ids"] and str(row["kind"]) in METHOD_KINDS:
                    raise MethodMemoryValidationError("supporting evidence cannot be method memory")
                if memory_id in record["counterexample_memory_ids"] and str(row["kind"]) not in NEGATIVE_METHOD_KINDS:
                    raise MethodMemoryValidationError("counterexample_memory_ids must reference counterexample/failure_pattern memory")

    def _receipt_rows(self, method_memory_id: str):
        return self.db.db.execute("SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts,memory_id", (method_memory_id,)).fetchall()

    def lifecycle_action(self, method_memory_id: str) -> str | None:
        action = None
        for row in self._receipt_rows(method_memory_id):
            decoded = self.decode_row(row)["value"]
            if "action" in decoded: action = decoded["action"]
        return action

    def promote(self, candidate_memory_id: str, *, evaluation: str, provenance: dict[str, Any], source_turn_id: str | None = None) -> dict[str, str]:
        _str(candidate_memory_id, "candidate_memory_id", max_len=256); _str(evaluation, "evaluation", max_len=8192); base_prov = _validate_provenance(provenance)
        with self.db.tx():
            row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1", (candidate_memory_id,)).fetchone()
            if row is None: raise MethodMemoryValidationError("promotion candidate does not exist")
            candidate = self.decode_row(row)
            if candidate["kind"] not in CANDIDATE_KINDS: raise MethodMemoryValidationError("promotion source must be a method candidate")
            self._assert_promotion_references(candidate)
            if any(self.decode_row(receipt)["value"].get("action") == "PROMOTE" for receipt in self._receipt_rows(candidate_memory_id)):
                raise MethodMemoryValidationError("candidate already has a promotion receipt")
            from .method_validation import MethodValidationError, derive_promotion_stats
            try: stats = derive_promotion_stats(self.db.db, candidate_memory_id, candidate["value"], candidate["user_id"])
            except MethodValidationError as exc: raise MethodMemoryValidationError("promotion requires held-out causal validation receipts") from exc
            record = dict(candidate["value"]); now = time.time(); promoted_kind = "framework" if candidate["kind"] == "framework_candidate" else "heuristic"
            record.update({"status": "PROMOTED", "support_count": stats["support_count"], "success_count": stats["success_count"],
                           "failure_count": stats["failure_count"], "calibration": stats["calibration"], "last_validated_at": stats["last_validated_at"]})
            receipt_value = {"method_memory_id": candidate_memory_id, "action": "PROMOTE", "source_episode_ids": list(record["source_episode_ids"]),
                             "supporting_memory_ids": list(record["supporting_memory_ids"]), "counterexample_memory_ids": list(record["counterexample_memory_ids"]),
                             "evaluation": evaluation, "ts": now, "validation_receipt_ids": stats["validation_receipt_ids"],
                             "validation_evidence_sha256": stats["validation_evidence_sha256"]}
            receipt_prov = {**base_prov, "promotion_source_memory_id": candidate_memory_id, "promotion_transaction_version": 2,
                            "validation_receipt_ids": stats["validation_receipt_ids"], "validation_evidence_sha256": stats["validation_evidence_sha256"]}
            receipt_id = self.admit("method_receipt", candidate_memory_id, receipt_value,
                                    source_turn_id if source_turn_id is not None else candidate["source_turn_id"], candidate["user_id"], receipt_prov)
            promoted_prov = {**candidate["provenance"], **base_prov, "promotion_source_memory_id": candidate_memory_id,
                             "promotion_receipt_id": receipt_id, "promotion_transaction_version": 2,
                             "validation_receipt_ids": stats["validation_receipt_ids"], "validation_evidence_sha256": stats["validation_evidence_sha256"],
                             "method_schema_version": METHOD_SCHEMA_VERSION, "admission": "method_memory:v1", "user_scope": candidate["user_id"],
                             "truth_authority": False, "effect_authority": False}
            promoted_value = canonical_method_value(promoted_kind, record, promoted_prov)
            promoted_id = self.db.add_memory(promoted_kind, candidate["subject"], promoted_value,
                                             source_turn_id if source_turn_id is not None else candidate["source_turn_id"], candidate["user_id"], promoted_prov)
            return {"candidate_memory_id": candidate_memory_id, "receipt_memory_id": receipt_id, "promoted_memory_id": promoted_id}

    def transition(self, method_memory_id: str, *, action: str, evaluation: str, provenance: dict[str, Any], source_turn_id: str | None = None) -> str:
        action = _str(action, "action", max_len=32).upper()
        if action not in {"DEMOTE", "RETIRE", "REJECT"}: raise MethodMemoryValidationError("unsupported lifecycle transition")
        _str(evaluation, "evaluation", max_len=8192)
        with self.db.tx():
            row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (method_memory_id,)).fetchone()
            if row is None: raise MethodMemoryValidationError("method does not exist")
            method = self.decode_row(row)
            if method["kind"] not in PROMOTABLE_KINDS or method["value"]["status"] != "PROMOTED":
                raise MethodMemoryValidationError("only PROMOTED framework/heuristic can transition")
            if self.lifecycle_action(method_memory_id) in {"DEMOTE", "RETIRE", "REJECT"}:
                raise MethodMemoryValidationError("method already has a terminal lifecycle receipt")
            record = method["value"]
            receipt = {"method_memory_id": method_memory_id, "action": action, "source_episode_ids": list(record["source_episode_ids"]),
                       "supporting_memory_ids": list(record["supporting_memory_ids"]), "counterexample_memory_ids": list(record["counterexample_memory_ids"]),
                       "evaluation": evaluation, "ts": time.time()}
            return self.admit("method_receipt", method_memory_id, receipt,
                              source_turn_id if source_turn_id is not None else method["source_turn_id"], method["user_id"],
                              {**_validate_provenance(provenance), "lifecycle_transaction_version": 1})

    def _assert_promoted_lineage(self, result: dict[str, Any]) -> None:
        if result["kind"] not in PROMOTABLE_KINDS or result["value"]["status"] != "PROMOTED": return
        prov = result["provenance"]; source_id = prov.get("promotion_source_memory_id"); receipt_id = prov.get("promotion_receipt_id")
        if not isinstance(source_id, str) or not isinstance(receipt_id, str): raise MethodMemoryValidationError("promoted method lacks promotion lineage")
        candidate_row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (source_id,)).fetchone()
        receipt_row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt'", (receipt_id,)).fetchone()
        if candidate_row is None or receipt_row is None: raise MethodMemoryValidationError("promotion source/receipt missing")
        candidate = self.decode_row(candidate_row); receipt = self.decode_row(receipt_row)["value"]
        if candidate["kind"] not in CANDIDATE_KINDS or receipt.get("action") != "PROMOTE" or receipt.get("method_memory_id") != source_id:
            raise MethodMemoryValidationError("promotion lineage mismatch")
        lineage_fields = ("source_episode_ids", "supporting_memory_ids", "counterexample_memory_ids")
        if any(receipt.get(field) != result["value"].get(field) or result["value"].get(field) != candidate["value"].get(field) for field in lineage_fields):
            raise MethodMemoryValidationError("promotion receipt source/support/counterexample drift")
        from .method_validation import MethodValidationError, derive_promotion_stats
        try: stats = derive_promotion_stats(self.db.db, source_id, candidate["value"], result["user_id"])
        except MethodValidationError as exc: raise MethodMemoryValidationError("promotion validation evidence is invalid") from exc
        for field in ("support_count", "success_count", "failure_count", "calibration", "last_validated_at"):
            if result["value"][field] != stats[field]: raise MethodMemoryValidationError("promoted method statistics drifted from validation receipts")
        if receipt.get("validation_receipt_ids") != stats["validation_receipt_ids"] or receipt.get("validation_evidence_sha256") != stats["validation_evidence_sha256"]:
            raise MethodMemoryValidationError("promotion receipt validation evidence drift")
        if prov.get("validation_receipt_ids") != stats["validation_receipt_ids"] or prov.get("validation_evidence_sha256") != stats["validation_evidence_sha256"]:
            raise MethodMemoryValidationError("promotion provenance validation evidence drift")

    def decode_row(self, row) -> dict[str, Any]:
        kind = str(row["kind"])
        if kind not in METHOD_KINDS: raise MethodMemoryValidationError("row is not method memory")
        try: provenance = json.loads(row["provenance"], parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except Exception as exc: raise MethodMemoryValidationError("stored method provenance is invalid JSON") from exc
        if not isinstance(provenance, dict) or provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION:
            raise MethodMemoryValidationError("stored method memory has unknown schema version")
        canonical_value = canonical_method_value(kind, row["value"], provenance)
        result = {"memory_id": str(row["memory_id"]), "kind": kind, "subject": str(row["subject"]), "value": json.loads(canonical_value),
                  "source_turn_id": row["source_turn_id"], "user_id": row["user_id"], "ts": float(row["ts"]), "provenance": provenance}
        self._assert_promoted_lineage(result)
        return result