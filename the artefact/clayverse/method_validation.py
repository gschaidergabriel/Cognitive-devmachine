from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from typing import Any

from .store import UnifiedDB

CANDIDATE_USE_SCHEMA = "clayverse.method-candidate-use/v1"
CANDIDATE_VALIDATION_SCHEMA = "clayverse.method-candidate-validation/v1"
_ALLOWED_USERS = frozenset({"gabriel", "andreas"})
_ALLOWED_EVIDENCE_STATUS = frozenset({"PRESENT", "UNDERCOVERED", "UNKNOWN"})
_ALLOWED_EVALUATION_MODES = frozenset({"SHADOW", "HELD_OUT"})
_FAILURE_EFFECT_STATUS = frozenset({"DENIED", "FAILED"})
_INELIGIBLE_EFFECT_STATUS = frozenset({"STALE_OUTCOME", "UNKNOWN_AFTER_RESTART"})


class MethodValidationError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodValidationError("method validation receipt must be finite canonical JSON") from exc


def _parse_object(raw: Any, label: str) -> dict[str, Any]:
    if isinstance(raw, str):
        try:
            value = json.loads(
                raw,
                parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)),
            )
        except Exception as exc:
            raise MethodValidationError(f"invalid {label} JSON") from exc
    else:
        value = raw
    if not isinstance(value, dict):
        raise MethodValidationError(f"{label} must be an object")
    _canonical_json(value)
    return value


def _bounded_string(value: Any, field: str, *, max_len: int = 2048) -> str:
    if not isinstance(value, str):
        raise MethodValidationError(f"{field} must be a string")
    text = value.strip()
    if not text or len(text) > max_len:
        raise MethodValidationError(f"invalid {field}")
    return text


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MethodValidationError(f"{field} must be a positive integer")
    return value


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MethodValidationError(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise MethodValidationError(f"{field} must be finite")
    return number


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_signature(raw: Any) -> dict[str, list[str]]:
    # Local canonicalization keeps this module independent from MethodMemory import cycles.
    if not isinstance(raw, dict) or not raw or len(raw) > 24:
        raise MethodValidationError("problem_signature must be a non-empty bounded object")
    result: dict[str, list[str]] = {}
    for key, values in raw.items():
        if not isinstance(key, str):
            raise MethodValidationError("problem_signature keys must be strings")
        key = " ".join(key.strip().lower().split())
        if not key or len(key) > 160:
            raise MethodValidationError("invalid problem_signature key")
        values = values if isinstance(values, list) else [values]
        if not values or len(values) > 32:
            raise MethodValidationError("invalid problem_signature facet")
        atoms: list[str] = []
        for value in values:
            if not isinstance(value, str):
                raise MethodValidationError("problem_signature values must be strings")
            atom = " ".join(value.strip().lower().split())
            if not atom or len(atom) > 160:
                raise MethodValidationError("invalid problem_signature atom")
            atoms.append(atom)
        result[key] = sorted(set(atoms))
    return dict(sorted(result.items()))


def validate_candidate_use_receipt(raw: Any) -> dict[str, Any]:
    value = _parse_object(raw, "candidate-use receipt")
    required = {
        "schema",
        "candidate_memory_id",
        "candidate_kind",
        "abstraction_version",
        "candidate_signature_sha256",
        "user_id",
        "session_id",
        "turn_id",
        "episode_id",
        "causal_id",
        "generation",
        "evidence_status",
        "problem_signature",
        "problem_signature_sha256",
        "evaluation_mode",
        "falsifier_checked",
        "truth_authority",
        "effect_authority",
        "ts",
    }
    unknown = sorted(set(value) - required)
    missing = sorted(required - set(value))
    if unknown:
        raise MethodValidationError("unknown candidate-use fields: " + ",".join(unknown))
    if missing:
        raise MethodValidationError("missing candidate-use fields: " + ",".join(missing))
    if value["schema"] != CANDIDATE_USE_SCHEMA:
        raise MethodValidationError("unsupported candidate-use schema")
    if value["candidate_kind"] not in {"framework_candidate", "heuristic_candidate"}:
        raise MethodValidationError("candidate-use kind is not promotable")
    for field in (
        "candidate_memory_id",
        "abstraction_version",
        "candidate_signature_sha256",
        "user_id",
        "session_id",
        "turn_id",
        "episode_id",
        "causal_id",
    ):
        value[field] = _bounded_string(value[field], field)
    if value["user_id"] not in _ALLOWED_USERS:
        raise MethodValidationError("invalid candidate-use user scope")
    value["generation"] = _positive_int(value["generation"], "generation")
    value["evidence_status"] = _bounded_string(value["evidence_status"], "evidence_status", max_len=32).upper()
    if value["evidence_status"] not in _ALLOWED_EVIDENCE_STATUS:
        raise MethodValidationError("invalid candidate-use evidence status")
    value["evaluation_mode"] = _bounded_string(value["evaluation_mode"], "evaluation_mode", max_len=32).upper()
    if value["evaluation_mode"] not in _ALLOWED_EVALUATION_MODES:
        raise MethodValidationError("invalid candidate-use evaluation mode")
    if not isinstance(value["falsifier_checked"], bool):
        raise MethodValidationError("falsifier_checked must be boolean")
    if value["truth_authority"] is not False or value["effect_authority"] is not False:
        raise MethodValidationError("candidate-use receipt cannot grant truth/effect authority")
    value["problem_signature"] = _canonical_signature(value["problem_signature"])
    if value["problem_signature_sha256"] != _sha256_json(value["problem_signature"]):
        raise MethodValidationError("candidate-use problem signature digest mismatch")
    if len(value["candidate_signature_sha256"]) != 64 or len(value["problem_signature_sha256"]) != 64:
        raise MethodValidationError("invalid signature digest")
    value["ts"] = _finite_number(value["ts"], "ts")
    if value["ts"] <= 0:
        raise MethodValidationError("invalid candidate-use ts")
    return value


def validate_candidate_validation_receipt(raw: Any) -> dict[str, Any]:
    value = _parse_object(raw, "candidate-validation receipt")
    required = {
        "schema",
        "candidate_memory_id",
        "candidate_use_receipt_id",
        "candidate_kind",
        "abstraction_version",
        "candidate_signature_sha256",
        "user_id",
        "session_id",
        "turn_id",
        "episode_id",
        "causal_id",
        "generation",
        "evidence_status",
        "problem_signature_sha256",
        "evaluation_mode",
        "falsifier_checked",
        "effect_id",
        "effect_capability",
        "effect_status",
        "outcome_hash",
        "causal_credit",
        "causal_receipt_id",
        "signal_class",
        "classification",
        "truth_authority",
        "effect_authority",
        "ts",
    }
    unknown = sorted(set(value) - required)
    missing = sorted(required - set(value))
    if unknown:
        raise MethodValidationError("unknown candidate-validation fields: " + ",".join(unknown))
    if missing:
        raise MethodValidationError("missing candidate-validation fields: " + ",".join(missing))
    if value["schema"] != CANDIDATE_VALIDATION_SCHEMA:
        raise MethodValidationError("unsupported candidate-validation schema")
    for field in (
        "candidate_memory_id",
        "candidate_use_receipt_id",
        "candidate_kind",
        "abstraction_version",
        "candidate_signature_sha256",
        "user_id",
        "session_id",
        "turn_id",
        "episode_id",
        "causal_id",
        "effect_id",
        "effect_capability",
        "effect_status",
        "outcome_hash",
        "causal_receipt_id",
        "signal_class",
        "classification",
        "problem_signature_sha256",
        "evaluation_mode",
    ):
        value[field] = _bounded_string(value[field], field)
    if value["user_id"] not in _ALLOWED_USERS:
        raise MethodValidationError("invalid candidate-validation user scope")
    value["generation"] = _positive_int(value["generation"], "generation")
    value["causal_credit"] = _finite_number(value["causal_credit"], "causal_credit")
    value["ts"] = _finite_number(value["ts"], "ts")
    if value["classification"] not in {"SUCCESS", "FAILURE"}:
        raise MethodValidationError("invalid candidate-validation classification")
    if value["truth_authority"] is not False or value["effect_authority"] is not False:
        raise MethodValidationError("candidate-validation receipt cannot grant truth/effect authority")
    if not isinstance(value["falsifier_checked"], bool):
        raise MethodValidationError("falsifier_checked must be boolean")
    if len(value["candidate_signature_sha256"]) != 64 or len(value["problem_signature_sha256"]) != 64:
        raise MethodValidationError("invalid signature digest")
    return value


class CandidateValidation:
    """Two-phase candidate evaluation receipts inside canonical UnifiedDB.

    `begin` proves the candidate was assigned to an exact active causal instance before
    its outcome exists. `finalize` derives SUCCESS/FAILURE only from a durable external
    EntityOS effect outcome. Normal Claude completion is therefore ineligible reward.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    def begin(
        self,
        *,
        candidate_memory_id: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        evidence_status: str,
        problem_signature: dict[str, Any],
        evaluation_mode: str,
        falsifier_checked: bool,
    ) -> str:
        if user_id not in _ALLOWED_USERS:
            raise MethodValidationError("candidate validation requires canonical user scope")
        candidate_memory_id = _bounded_string(candidate_memory_id, "candidate_memory_id")
        signature = _canonical_signature(problem_signature)
        from .method_memory import validate_method_record

        candidate_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1",
            (candidate_memory_id,),
        ).fetchone()
        if candidate_row is None or str(candidate_row["kind"]) not in {"framework_candidate", "heuristic_candidate"}:
            raise MethodValidationError("candidate-use source is not a method candidate")
        if str(candidate_row["user_id"] or "") != user_id:
            raise MethodValidationError("candidate-use source crosses user scope")
        candidate = validate_method_record(
            str(candidate_row["kind"]),
            _parse_object(str(candidate_row["value"]), "candidate method record"),
        )
        candidate_provenance = _parse_object(str(candidate_row["provenance"]), "candidate provenance")
        if candidate_provenance.get("admission") != "method_memory:v1" or candidate_provenance.get("user_scope") != user_id:
            raise MethodValidationError("candidate-use source is not canonically admitted")

        active = self.db.db.execute(
            "SELECT a.session_id,a.user_id,a.turn_id,a.episode_id,a.causal_id,a.generation,"
            "w.state,w.observation_turn_id,s.user_id AS session_user,t.user_id AS turn_user "
            "FROM active_turns a JOIN workspace_episodes w ON w.episode_id=a.episode_id "
            "JOIN sessions s ON s.session_id=a.session_id JOIN turns t ON t.turn_id=a.turn_id "
            "WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        expected = (user_id, turn_id, episode_id, causal_id, int(generation))
        observed = None if active is None else (
            str(active["user_id"]),
            str(active["turn_id"]),
            str(active["episode_id"]),
            str(active["causal_id"]),
            int(active["generation"]),
        )
        if active is None or observed != expected:
            raise MethodValidationError("candidate-use identity is not the exact active causal instance")
        if str(active["session_user"]) != user_id or str(active["turn_user"]) != user_id:
            raise MethodValidationError("candidate-use relational user identity diverged")
        if str(active["observation_turn_id"]) != turn_id or str(active["state"]) not in {"OPEN", "SELECTED"}:
            raise MethodValidationError("candidate-use workspace is not active")
        self.db.assert_live_generation(session_id, int(generation))

        now = time.time()
        value = validate_candidate_use_receipt({
            "schema": CANDIDATE_USE_SCHEMA,
            "candidate_memory_id": candidate_memory_id,
            "candidate_kind": str(candidate_row["kind"]),
            "abstraction_version": candidate["abstraction_version"],
            "candidate_signature_sha256": _sha256_json(candidate["problem_signature"]),
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "evidence_status": str(evidence_status).upper(),
            "problem_signature": signature,
            "problem_signature_sha256": _sha256_json(signature),
            "evaluation_mode": str(evaluation_mode).upper(),
            "falsifier_checked": bool(falsifier_checked),
            "truth_authority": False,
            "effect_authority": False,
            "ts": now,
        })
        subject = f"candidate_use:{candidate_memory_id}:{causal_id}"
        existing = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts LIMIT 1",
            (subject,),
        ).fetchone()
        if existing is not None:
            old = validate_candidate_use_receipt(str(existing["value"]))
            if _canonical_json(old) != _canonical_json(value):
                raise MethodValidationError("candidate-use replay identity drift")
            return str(existing["memory_id"])

        receipt_id = str(uuid.uuid4())
        provenance = {
            "schema": CANDIDATE_USE_SCHEMA,
            "admission": "method_candidate_use:v1",
            "candidate_memory_id": candidate_memory_id,
            "user_scope": user_id,
            "truth_authority": False,
            "effect_authority": False,
        }
        self.db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                receipt_id,
                "method_receipt",
                subject,
                _canonical_json(value),
                turn_id,
                user_id,
                now,
                _canonical_json(provenance),
            ),
        )
        return receipt_id

    def finalize(self, *, candidate_use_receipt_id: str) -> str:
        candidate_use_receipt_id = _bounded_string(candidate_use_receipt_id, "candidate_use_receipt_id")
        use_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt' LIMIT 1",
            (candidate_use_receipt_id,),
        ).fetchone()
        if use_row is None:
            raise MethodValidationError("candidate-use receipt does not exist")
        use = validate_candidate_use_receipt(str(use_row["value"]))
        if str(use_row["user_id"] or "") != use["user_id"]:
            raise MethodValidationError("candidate-use stored user scope diverged")

        row = self.db.db.execute(
            "SELECT w.session_id,w.state,w.observation_turn_id,s.user_id AS session_user,"
            "t.user_id AS turn_user,c.causal_id,c.episode_id AS causal_episode_id,c.effect_id,"
            "c.outcome_hash,c.credit,c.reentered,e.user_id AS effect_user,e.capability,e.status,"
            "e.requested_generation,e.verified_at "
            "FROM workspace_episodes w JOIN sessions s ON s.session_id=w.session_id "
            "JOIN turns t ON t.turn_id=w.observation_turn_id "
            "JOIN causal_episodes c ON c.episode_id=w.episode_id "
            "JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE w.episode_id=? AND c.causal_id=? LIMIT 1",
            (use["episode_id"], use["causal_id"]),
        ).fetchone()
        if row is None:
            raise MethodValidationError("candidate-use has no external causal effect outcome")
        if (
            str(row["session_id"]) != use["session_id"]
            or str(row["session_user"]) != use["user_id"]
            or str(row["turn_user"]) != use["user_id"]
            or str(row["observation_turn_id"]) != use["turn_id"]
            or str(row["causal_episode_id"]) != use["episode_id"]
            or str(row["effect_user"]) != use["user_id"]
            or int(row["requested_generation"]) != use["generation"]
        ):
            raise MethodValidationError("candidate-validation causal identity diverged")
        if str(row["state"]) not in {"COMPLETED", "ABORTED"} or not int(row["reentered"]):
            raise MethodValidationError("candidate-validation episode is not terminal and re-entered")
        if row["verified_at"] is None or not str(row["outcome_hash"] or ""):
            raise MethodValidationError("candidate-validation effect outcome is not durably verified")
        if str(row["capability"]) != "entityos.exec":
            raise MethodValidationError("candidate-validation v1 requires an external EntityOS effect")

        status = str(row["status"])
        credit = _finite_number(row["credit"], "causal_credit")
        if status == "VERIFIED" and credit > 0.0:
            classification = "SUCCESS"
        elif status in _FAILURE_EFFECT_STATUS:
            classification = "FAILURE"
        elif status in _INELIGIBLE_EFFECT_STATUS or credit == 0.0:
            raise MethodValidationError("effect outcome is ineligible as method utility evidence")
        else:
            raise MethodValidationError("unsupported effect outcome for method validation")

        causal_receipt_id = hashlib.sha256(
            f"{use['causal_id']}\x1f{row['effect_id']}\x1f{row['outcome_hash']}\x1f{credit:.9f}\x1f{status}".encode("utf-8")
        ).hexdigest()
        now = time.time()
        value = validate_candidate_validation_receipt({
            "schema": CANDIDATE_VALIDATION_SCHEMA,
            "candidate_memory_id": use["candidate_memory_id"],
            "candidate_use_receipt_id": candidate_use_receipt_id,
            "candidate_kind": use["candidate_kind"],
            "abstraction_version": use["abstraction_version"],
            "candidate_signature_sha256": use["candidate_signature_sha256"],
            "user_id": use["user_id"],
            "session_id": use["session_id"],
            "turn_id": use["turn_id"],
            "episode_id": use["episode_id"],
            "causal_id": use["causal_id"],
            "generation": use["generation"],
            "evidence_status": use["evidence_status"],
            "problem_signature_sha256": use["problem_signature_sha256"],
            "evaluation_mode": use["evaluation_mode"],
            "falsifier_checked": use["falsifier_checked"],
            "effect_id": str(row["effect_id"]),
            "effect_capability": str(row["capability"]),
            "effect_status": status,
            "outcome_hash": str(row["outcome_hash"]),
            "causal_credit": credit,
            "causal_receipt_id": causal_receipt_id,
            "signal_class": f"effect_outcome:{status}",
            "classification": classification,
            "truth_authority": False,
            "effect_authority": False,
            "ts": now,
        })
        subject = f"candidate_validation:{use['candidate_memory_id']}:{use['causal_id']}"
        existing = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts LIMIT 1",
            (subject,),
        ).fetchone()
        if existing is not None:
            old = validate_candidate_validation_receipt(str(existing["value"]))
            comparable_old = dict(old)
            comparable_new = dict(value)
            comparable_old.pop("ts", None)
            comparable_new.pop("ts", None)
            if _canonical_json(comparable_old) != _canonical_json(comparable_new):
                raise MethodValidationError("candidate-validation replay identity drift")
            return str(existing["memory_id"])

        receipt_id = str(uuid.uuid4())
        provenance = {
            "schema": CANDIDATE_VALIDATION_SCHEMA,
            "admission": "method_candidate_validation:v1",
            "candidate_memory_id": use["candidate_memory_id"],
            "candidate_use_receipt_id": candidate_use_receipt_id,
            "causal_receipt_id": causal_receipt_id,
            "user_scope": use["user_id"],
            "truth_authority": False,
            "effect_authority": False,
        }
        self.db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                receipt_id,
                "method_receipt",
                subject,
                _canonical_json(value),
                use["turn_id"],
                use["user_id"],
                now,
                _canonical_json(provenance),
            ),
        )
        return receipt_id


def derive_promotion_stats(db, candidate_memory_id: str, candidate: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Derive promotion counters only from durable HELD_OUT candidate-validation receipts."""
    candidate_memory_id = _bounded_string(candidate_memory_id, "candidate_memory_id")
    source_episode_ids = list(candidate.get("source_episode_ids") or [])
    if len(source_episode_ids) < 2 or len(set(source_episode_ids)) != len(source_episode_ids):
        raise MethodValidationError("promotion requires distinct candidate source episodes")
    rows = db.execute(
        "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject LIKE ? AND user_id=? ORDER BY ts,memory_id",
        (f"candidate_validation:{candidate_memory_id}:%", user_id),
    ).fetchall()
    receipts: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        receipt = validate_candidate_validation_receipt(str(row["value"]))
        if receipt["candidate_memory_id"] != candidate_memory_id or receipt["user_id"] != user_id:
            raise MethodValidationError("candidate-validation receipt identity diverged")
        if receipt["candidate_kind"] not in {"framework_candidate", "heuristic_candidate"}:
            raise MethodValidationError("candidate-validation receipt kind is invalid")
        if receipt["abstraction_version"] != candidate.get("abstraction_version"):
            raise MethodValidationError("candidate-validation abstraction version diverged")
        if receipt["candidate_signature_sha256"] != _sha256_json(candidate.get("problem_signature")):
            raise MethodValidationError("candidate-validation candidate signature diverged")
        if receipt["truth_authority"] is not False or receipt["effect_authority"] is not False:
            raise MethodValidationError("candidate-validation authority broadening detected")
        if receipt["evaluation_mode"] != "HELD_OUT":
            raise MethodValidationError("promotion requires HELD_OUT candidate-validation receipts")
        receipts.append((str(row["memory_id"]), receipt))

    by_episode: dict[str, tuple[str, dict[str, Any]]] = {}
    for item in receipts:
        episode_id = item[1]["episode_id"]
        if episode_id in by_episode:
            raise MethodValidationError("multiple validation receipts for one promotion episode")
        by_episode[episode_id] = item
    if set(by_episode) != set(source_episode_ids):
        raise MethodValidationError("promotion lacks validation receipts for every source episode")
    causal_ids = [item[1]["causal_id"] for item in by_episode.values()]
    if len(set(causal_ids)) != len(causal_ids):
        raise MethodValidationError("promotion validation receipts do not span distinct causal instances")
    if not any(item[1]["falsifier_checked"] for item in by_episode.values()):
        raise MethodValidationError("promotion requires at least one falsifier-checked validation instance")

    ordered = [by_episode[episode_id] for episode_id in source_episode_ids]
    success_count = sum(1 for _, receipt in ordered if receipt["classification"] == "SUCCESS")
    failure_count = sum(1 for _, receipt in ordered if receipt["classification"] == "FAILURE")
    support_count = len(ordered)
    if success_count < 1:
        raise MethodValidationError("promotion requires at least one validated success")
    calibration = success_count / support_count
    last_validated_at = max(receipt["ts"] for _, receipt in ordered)
    receipt_ids = [memory_id for memory_id, _ in ordered]
    evidence_digest = hashlib.sha256(
        _canonical_json([
            {
                "memory_id": memory_id,
                "candidate_memory_id": receipt["candidate_memory_id"],
                "causal_receipt_id": receipt["causal_receipt_id"],
                "classification": receipt["classification"],
                "episode_id": receipt["episode_id"],
            }
            for memory_id, receipt in ordered
        ]).encode("utf-8")
    ).hexdigest()
    return {
        "support_count": support_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "calibration": calibration,
        "last_validated_at": last_validated_at,
        "validation_receipt_ids": receipt_ids,
        "validation_evidence_sha256": evidence_digest,
    }
