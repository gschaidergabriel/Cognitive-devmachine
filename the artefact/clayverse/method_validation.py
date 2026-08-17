from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Any

from .store import StaleGeneration, UnifiedDB

VALIDATION_USE_SCHEMA = "clayverse.method-validation-use/v1"
VALIDATION_RESULT_SCHEMA = "clayverse.method-validation-result/v1"
VALIDATION_EVALUATOR = "clayverse:method-validator:v1"
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
MIN_PROMOTION_VALIDATIONS = 2


class MethodValidationError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodValidationError("method validation value is not canonical JSON") from exc


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _bounded(value: Any, label: str, limit: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise MethodValidationError(f"invalid {label}")
    return value.strip()


class MethodValidationAuthority:
    """Admit causal method-use/outcome evidence for promotion.

    This is intentionally narrower than general reward learning. A candidate can receive
    promotion credit only when a candidate-use receipt was persisted before an effect on
    the same active causal turn and that exact effect later reached EffectJournal status
    VERIFIED. Normal Claude completion, bare causal re-entry, caller-supplied counters,
    FAILED/DENIED/STALE/UNKNOWN effects, and unbound held-out claims are not eligible.

    Both use and result receipts are canonical `durable_memory(kind='method_receipt')`
    state, so UnifiedDB checkpoint/recovery already binds them. They never carry factual
    truth authority or effect authority.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _use_id(candidate_memory_id: str, causal_id: str) -> str:
        return "method-validation-use:" + hashlib.sha256(
            f"{candidate_memory_id}\0{causal_id}".encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _result_id(candidate_memory_id: str, causal_id: str) -> str:
        return "method-validation-result:" + hashlib.sha256(
            f"{candidate_memory_id}\0{causal_id}".encode("utf-8")
        ).hexdigest()

    def _candidate(self, candidate_memory_id: str, user_id: str) -> tuple[Any, dict[str, Any], str]:
        candidate_memory_id = _bounded(candidate_memory_id, "candidate_memory_id")
        row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1", (candidate_memory_id,)
        ).fetchone()
        if row is None or str(row["kind"]) not in CANDIDATE_KINDS:
            raise MethodValidationError("validation target is not a method candidate")
        if str(row["user_id"] or "") != user_id:
            raise MethodValidationError("validation candidate crosses user scope")
        try:
            record = json.loads(str(row["value"])); provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise MethodValidationError("malformed validation candidate") from exc
        if not isinstance(record, dict) or str(record.get("status", "")).upper() != "CANDIDATE":
            raise MethodValidationError("validation target is not CANDIDATE")
        if not isinstance(provenance, dict) or provenance.get("admission") != "method_memory:v1" or provenance.get("user_scope") != user_id:
            raise MethodValidationError("validation target is not canonically admitted")
        envelope = {
            "memory_id": candidate_memory_id,
            "kind": str(row["kind"]),
            "subject": str(row["subject"]),
            "value": record,
            "source_turn_id": row["source_turn_id"],
            "user_id": str(row["user_id"]),
            "provenance": provenance,
        }
        return row, envelope, _sha(envelope)

    def _active_identity(self, *, user_id: str, session_id: str, turn_id: str, episode_id: str,
                         causal_id: str, generation: int) -> None:
        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
            raise MethodValidationError("invalid validation user/session scope")
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        row = self.db.db.execute(
            "SELECT a.user_id,a.turn_id,a.episode_id,a.causal_id,a.generation,"
            "t.user_id AS turn_user,t.session_id AS turn_session,w.session_id AS episode_session "
            "FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
            "JOIN workspace_episodes w ON w.episode_id=a.episode_id WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        if row is None or any((
            str(row["user_id"]) != user_id,
            str(row["turn_user"]) != user_id,
            str(row["turn_session"]) != session_id,
            str(row["episode_session"]) != session_id,
            str(row["turn_id"]) != turn_id,
            str(row["episode_id"]) != episode_id,
            str(row["causal_id"]) != causal_id,
            int(row["generation"]) != int(generation),
        )):
            raise StaleGeneration("method_validation_identity")

    def begin_candidate_use(self, *, candidate_memory_id: str, user_id: str, session_id: str,
                            turn_id: str, episode_id: str, causal_id: str, generation: int,
                            evaluator: str = VALIDATION_EVALUATOR) -> str:
        if evaluator != VALIDATION_EVALUATOR:
            raise MethodValidationError("unrecognized method evaluator")
        self._active_identity(user_id=user_id, session_id=session_id, turn_id=turn_id,
                              episode_id=episode_id, causal_id=causal_id, generation=generation)
        _, _, candidate_sha = self._candidate(candidate_memory_id, user_id)
        payload = {
            "schema": VALIDATION_USE_SCHEMA,
            "candidate_memory_id": candidate_memory_id,
            "candidate_sha256": candidate_sha,
            "evaluator": evaluator,
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        }
        memory_id = self._use_id(candidate_memory_id, causal_id)
        value = _canonical_json(payload)
        provenance = _canonical_json({
            "source": "method_validation_use:v1",
            "schema": VALIDATION_USE_SCHEMA,
            "candidate_memory_id": candidate_memory_id,
            "candidate_sha256": candidate_sha,
            "evaluator": evaluator,
            "user_scope": user_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        })

        def insert(db) -> bool:
            cur = db.execute(
                "INSERT OR IGNORE INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (memory_id, "method_receipt", f"validation-use:{candidate_memory_id}:{causal_id}",
                 value, turn_id, user_id, time.time(), provenance),
            )
            return int(cur.rowcount or 0) == 1

        if self.db.db.in_transaction:
            inserted = insert(self.db.db)
        else:
            with self.db.tx() as db:
                inserted = insert(db)
        if not inserted:
            existing = self._decode_use(memory_id)
            if existing != payload:
                raise StaleGeneration("method_validation_use_identity")
        return memory_id

    def _decode_use(self, memory_id: str) -> dict[str, Any]:
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        if row is None or str(row["kind"]) != "method_receipt":
            raise MethodValidationError("method validation use receipt missing")
        try:
            payload = json.loads(str(row["value"])); provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise MethodValidationError("malformed method validation use receipt") from exc
        if not isinstance(payload, dict) or payload.get("schema") != VALIDATION_USE_SCHEMA:
            raise MethodValidationError("unsupported method validation use schema")
        if not isinstance(provenance, dict) or provenance.get("source") != "method_validation_use:v1":
            raise MethodValidationError("invalid method validation use provenance")
        required = {
            "candidate_memory_id", "candidate_sha256", "evaluator", "user_id", "session_id",
            "turn_id", "episode_id", "causal_id", "generation", "truth_authority", "effect_authority",
        }
        if not required.issubset(payload):
            raise MethodValidationError("incomplete method validation use receipt")
        if payload["evaluator"] != VALIDATION_EVALUATOR or payload["truth_authority"] is not False or payload["effect_authority"] is not False:
            raise MethodValidationError("invalid method validation use authority")
        if provenance.get("truth_authority") is not False or provenance.get("effect_authority") is not False:
            raise MethodValidationError("invalid method validation use provenance authority")
        _, _, current_sha = self._candidate(str(payload["candidate_memory_id"]), str(payload["user_id"]))
        if current_sha != payload["candidate_sha256"]:
            raise MethodValidationError("validation candidate drifted after use admission")
        expected_id = self._use_id(str(payload["candidate_memory_id"]), str(payload["causal_id"]))
        if expected_id != memory_id:
            raise MethodValidationError("method validation use id mismatch")
        return payload

    def finalize_verified_effect(self, *, use_receipt_id: str, effect_id: str,
                                 user_id: str, session_id: str, generation: int) -> str:
        use_receipt_id = _bounded(use_receipt_id, "use_receipt_id")
        effect_id = _bounded(effect_id, "effect_id")
        use = self._decode_use(use_receipt_id)
        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
            raise MethodValidationError("invalid validation result scope")
        if use["user_id"] != user_id or use["session_id"] != session_id or int(use["generation"]) != int(generation):
            raise StaleGeneration("method_validation_result_identity")
        # Generation is checked at finalization. Old/stale outcomes can never mint new method credit.
        self.db.assert_live_generation(session_id, generation)
        row = self.db.db.execute(
            "SELECT e.effect_id,e.episode_id,e.user_id,e.requested_generation,e.status,e.outcome,e.ts AS effect_ts,e.verified_at,"
            "c.causal_id,c.observation_turn_id,c.outcome_hash,c.credit,c.reentered,w.session_id,w.state "
            "FROM effects e JOIN causal_episodes c ON c.effect_id=e.effect_id "
            "JOIN workspace_episodes w ON w.episode_id=e.episode_id WHERE e.effect_id=? LIMIT 1",
            (effect_id,),
        ).fetchone()
        if row is None:
            raise MethodValidationError("validation effect lacks causal outcome")
        if any((
            str(row["episode_id"]) != use["episode_id"],
            str(row["causal_id"]) != use["causal_id"],
            str(row["observation_turn_id"] or "") != use["turn_id"],
            str(row["user_id"]) != user_id,
            str(row["session_id"]) != session_id,
            int(row["requested_generation"]) != int(generation),
            not int(row["reentered"]),
            str(row["state"]) not in {"COMPLETED", "ABORTED"},
            str(row["status"]) != "VERIFIED",
            row["verified_at"] is None,
        )):
            raise MethodValidationError("effect is not eligible terminal verified method evidence")
        use_row = self.db.db.execute("SELECT ts FROM durable_memory WHERE memory_id=?", (use_receipt_id,)).fetchone()
        if use_row is None or float(use_row["ts"]) > float(row["effect_ts"]):
            raise MethodValidationError("candidate use was not admitted before effect execution")
        try:
            outcome = json.loads(str(row["outcome"]))
        except Exception as exc:
            raise MethodValidationError("malformed verified effect outcome receipt") from exc
        if not isinstance(outcome, dict) or outcome.get("audit") != "redacted-outcome-v1" or not isinstance(outcome.get("ok"), bool):
            raise MethodValidationError("verified effect lacks objective ok signal")
        utility = 1 if outcome["ok"] is True else 0
        if float(row["credit"]) != float(utility):
            raise MethodValidationError("causal credit diverges from verified effect outcome")
        candidate_id = str(use["candidate_memory_id"])
        payload = {
            "schema": VALIDATION_RESULT_SCHEMA,
            "signal_class": "VERIFIED_EFFECT_OUTCOME",
            "candidate_memory_id": candidate_id,
            "candidate_sha256": use["candidate_sha256"],
            "use_receipt_id": use_receipt_id,
            "effect_id": effect_id,
            "effect_outcome_sha256": str(outcome.get("sha256", "")),
            "causal_outcome_hash": str(row["outcome_hash"] or ""),
            "utility": utility,
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": use["turn_id"],
            "episode_id": use["episode_id"],
            "causal_id": use["causal_id"],
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        }
        if not payload["effect_outcome_sha256"] or not payload["causal_outcome_hash"]:
            raise MethodValidationError("verified effect evidence lacks outcome identity")
        memory_id = self._result_id(candidate_id, str(use["causal_id"]))
        value = _canonical_json(payload)
        provenance = _canonical_json({
            "source": "method_validation_result:v1",
            "schema": VALIDATION_RESULT_SCHEMA,
            "signal_class": "VERIFIED_EFFECT_OUTCOME",
            "candidate_memory_id": candidate_id,
            "candidate_sha256": use["candidate_sha256"],
            "use_receipt_id": use_receipt_id,
            "effect_id": effect_id,
            "user_scope": user_id,
            "causal_id": use["causal_id"],
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        })

        def insert(db) -> bool:
            cur = db.execute(
                "INSERT OR IGNORE INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (memory_id, "method_receipt", f"validation-result:{candidate_id}:{use['causal_id']}",
                 value, use["turn_id"], user_id, time.time(), provenance),
            )
            return int(cur.rowcount or 0) == 1

        if self.db.db.in_transaction:
            inserted = insert(self.db.db)
        else:
            with self.db.tx() as db:
                inserted = insert(db)
        if not inserted:
            existing = self._decode_result(memory_id)
            if existing != payload:
                raise StaleGeneration("method_validation_result_identity")
        return memory_id

    def _decode_result(self, memory_id: str) -> dict[str, Any]:
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        if row is None or str(row["kind"]) != "method_receipt":
            raise MethodValidationError("method validation result receipt missing")
        try:
            payload = json.loads(str(row["value"])); provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise MethodValidationError("malformed method validation result receipt") from exc
        if not isinstance(payload, dict) or payload.get("schema") != VALIDATION_RESULT_SCHEMA:
            raise MethodValidationError("unsupported method validation result schema")
        if not isinstance(provenance, dict) or provenance.get("source") != "method_validation_result:v1":
            raise MethodValidationError("invalid method validation result provenance")
        if payload.get("signal_class") != "VERIFIED_EFFECT_OUTCOME" or payload.get("utility") not in {0, 1}:
            raise MethodValidationError("unsupported method validation utility")
        candidate_id = _bounded(payload.get("candidate_memory_id"), "candidate_memory_id")
        user_id = _bounded(payload.get("user_id"), "user_id")
        _, _, candidate_sha = self._candidate(candidate_id, user_id)
        if candidate_sha != payload.get("candidate_sha256"):
            raise MethodValidationError("validation result candidate digest mismatch")
        use = self._decode_use(_bounded(payload.get("use_receipt_id"), "use_receipt_id"))
        if any((
            use["candidate_memory_id"] != candidate_id,
            use["candidate_sha256"] != candidate_sha,
            use["user_id"] != user_id,
            use["session_id"] != payload.get("session_id"),
            use["turn_id"] != payload.get("turn_id"),
            use["episode_id"] != payload.get("episode_id"),
            use["causal_id"] != payload.get("causal_id"),
            int(use["generation"]) != int(payload.get("generation", -1)),
        )):
            raise MethodValidationError("validation use/result identity mismatch")
        effect = self.db.db.execute(
            "SELECT e.effect_id,e.episode_id,e.user_id,e.requested_generation,e.status,e.outcome,e.ts AS effect_ts,e.verified_at,"
            "c.causal_id,c.observation_turn_id,c.outcome_hash,c.credit,c.reentered,w.session_id,w.state "
            "FROM effects e JOIN causal_episodes c ON c.effect_id=e.effect_id "
            "JOIN workspace_episodes w ON w.episode_id=e.episode_id WHERE e.effect_id=? LIMIT 1",
            (_bounded(payload.get("effect_id"), "effect_id"),),
        ).fetchone()
        if effect is None or any((
            str(effect["episode_id"]) != payload.get("episode_id"),
            str(effect["causal_id"]) != payload.get("causal_id"),
            str(effect["observation_turn_id"] or "") != payload.get("turn_id"),
            str(effect["user_id"]) != user_id,
            str(effect["session_id"]) != payload.get("session_id"),
            int(effect["requested_generation"]) != int(payload.get("generation", -1)),
            str(effect["status"]) != "VERIFIED",
            not int(effect["reentered"]),
            str(effect["state"]) not in {"COMPLETED", "ABORTED"},
        )):
            raise MethodValidationError("validation result no longer has eligible effect evidence")
        try:
            outcome = json.loads(str(effect["outcome"]))
        except Exception as exc:
            raise MethodValidationError("validation effect outcome became malformed") from exc
        utility = 1 if isinstance(outcome, dict) and outcome.get("ok") is True else 0
        if not isinstance(outcome, dict) or outcome.get("audit") != "redacted-outcome-v1" or not isinstance(outcome.get("ok"), bool):
            raise MethodValidationError("validation effect lost objective ok signal")
        if utility != int(payload["utility"]) or float(effect["credit"]) != float(utility):
            raise MethodValidationError("validation utility drifted from effect evidence")
        if str(outcome.get("sha256", "")) != str(payload.get("effect_outcome_sha256", "")) or str(effect["outcome_hash"] or "") != str(payload.get("causal_outcome_hash", "")):
            raise MethodValidationError("validation outcome identity drifted")
        use_row = self.db.db.execute("SELECT ts FROM durable_memory WHERE memory_id=?", (use["use_receipt_id"] if "use_receipt_id" in use else payload["use_receipt_id"],)).fetchone()
        if use_row is None or float(use_row["ts"]) > float(effect["effect_ts"]):
            raise MethodValidationError("validation candidate-use ordering drifted")
        if provenance.get("candidate_memory_id") != candidate_id or provenance.get("candidate_sha256") != candidate_sha or provenance.get("effect_id") != payload.get("effect_id") or provenance.get("causal_id") != payload.get("causal_id") or provenance.get("user_scope") != user_id:
            raise MethodValidationError("validation result provenance mismatch")
        if provenance.get("truth_authority") is not False or provenance.get("effect_authority") is not False or payload.get("truth_authority") is not False or payload.get("effect_authority") is not False:
            raise MethodValidationError("validation result authority mismatch")
        expected_id = self._result_id(candidate_id, str(payload.get("causal_id")))
        if memory_id != expected_id:
            raise MethodValidationError("validation result id mismatch")
        return payload

    def aggregate(self, *, candidate_memory_id: str, user_id: str) -> dict[str, Any]:
        _, _, candidate_sha = self._candidate(candidate_memory_id, user_id)
        rows = self.db.db.execute(
            "SELECT memory_id FROM durable_memory WHERE kind='method_receipt' AND user_id=? "
            "AND subject LIKE ? ORDER BY ts,memory_id",
            (user_id, f"validation-result:{candidate_memory_id}:%"),
        ).fetchall()
        receipts: list[tuple[str, dict[str, Any]]] = []
        seen_causal: set[str] = set()
        seen_episode: set[str] = set()
        for row in rows:
            memory_id = str(row["memory_id"])
            payload = self._decode_result(memory_id)
            if payload["candidate_memory_id"] != candidate_memory_id or payload["candidate_sha256"] != candidate_sha:
                raise MethodValidationError("validation receipt targets different candidate")
            causal_id = str(payload["causal_id"]); episode_id = str(payload["episode_id"])
            if causal_id in seen_causal or episode_id in seen_episode:
                raise MethodValidationError("duplicate validation problem instance")
            seen_causal.add(causal_id); seen_episode.add(episode_id); receipts.append((memory_id, payload))
        support = len(receipts)
        success = sum(int(payload["utility"]) for _, payload in receipts)
        failure = support - success
        calibration = (success / support) if support else 0.0
        last_validated = max((float(self.db.db.execute("SELECT ts FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()[0]) for memory_id, _ in receipts), default=0.0)
        if not math.isfinite(calibration):
            raise MethodValidationError("non-finite derived method calibration")
        return {
            "candidate_memory_id": candidate_memory_id,
            "candidate_sha256": candidate_sha,
            "validation_receipt_ids": [memory_id for memory_id, _ in receipts],
            "validation_episode_ids": [str(payload["episode_id"]) for _, payload in receipts],
            "validation_causal_ids": [str(payload["causal_id"]) for _, payload in receipts],
            "support_count": support,
            "success_count": success,
            "failure_count": failure,
            "calibration": calibration,
            "last_validated_at": last_validated,
            "signal_class": "VERIFIED_EFFECT_OUTCOME",
        }

    def promotion_aggregate(self, *, candidate_memory_id: str, user_id: str) -> dict[str, Any]:
        aggregate = self.aggregate(candidate_memory_id=candidate_memory_id, user_id=user_id)
        if aggregate["support_count"] < MIN_PROMOTION_VALIDATIONS:
            raise MethodValidationError("promotion requires at least two distinct validated method uses")
        if aggregate["success_count"] < 1 or aggregate["calibration"] <= 0.0:
            raise MethodValidationError("promotion lacks positive validated method utility")
        return aggregate
