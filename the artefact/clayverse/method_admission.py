from __future__ import annotations

import hashlib
import json
from typing import Any

from .method_transfer import MethodRecordError, MethodTransfer
from .store import StaleGeneration, UnifiedDB

CANDIDATE_TO_PROMOTED = {
    "framework_candidate": "framework",
    "heuristic_candidate": "heuristic",
}
TERMINAL_METHOD_ACTIONS = frozenset({"DEMOTE", "RETIRE"})


class MethodAdmissionError(RuntimeError):
    pass


class MethodAdmission:
    """External-validation gate for durable method candidates and method state changes.

    This organ never infers truth and never consumes ordinary Claude completion as
    promotion evidence. Promotion is append-only: the candidate is preserved, a new
    promoted record is written, and a durable method_receipt binds the decision.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _canonical(value: dict[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _row_for_user(self, memory_id: str, user_id: str):
        row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? AND (user_id IS NULL OR user_id=?)",
            (str(memory_id), str(user_id)),
        ).fetchone()
        if not row:
            raise MethodAdmissionError("method memory unavailable under user boundary")
        return row

    def create_candidate(
        self, *, kind: str, subject: str, record: dict[str, Any], source_turn_id: str,
        user_id: str, session_id: str, generation: int, provenance: dict[str, Any]
    ) -> str:
        if kind not in CANDIDATE_TO_PROMOTED:
            raise MethodAdmissionError("invalid method candidate kind")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 512:
            raise MethodAdmissionError("invalid method candidate subject")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodAdmissionError("candidate provenance required")
        self.db.assert_live_generation(session_id, generation)
        candidate = dict(record)
        candidate["status"] = "CANDIDATE"
        try:
            MethodTransfer.validate_record(kind, self._canonical(candidate))
            sig = MethodTransfer.normalize_signature(candidate["problem_signature"])
            if not isinstance(candidate.get("goal_shape"), str) or candidate["goal_shape"].strip().lower() != sig["goal_shape"]:
                raise MethodAdmissionError("candidate goal_shape mismatch")
            steps = candidate.get("method_steps")
            falsifiers = candidate.get("falsifiers")
            source_episodes = candidate.get("source_episode_ids")
            if not isinstance(steps, list) or not steps or not all(isinstance(x, str) and x.strip() for x in steps):
                raise MethodAdmissionError("candidate method_steps required")
            if not isinstance(falsifiers, list) or not falsifiers or not all(isinstance(x, str) and x.strip() for x in falsifiers):
                raise MethodAdmissionError("candidate falsifiers required")
            if not isinstance(source_episodes, list) or not source_episodes or not all(isinstance(x, str) and x.strip() for x in source_episodes):
                raise MethodAdmissionError("candidate source episodes required")
            if not isinstance(candidate.get("provenance"), dict) or not candidate["provenance"]:
                raise MethodAdmissionError("candidate record provenance required")
        except MethodRecordError as exc:
            raise MethodAdmissionError(str(exc)) from exc
        with self.db.tx():
            self.db.assert_live_generation(session_id, generation)
            return self.db.add_memory(
                kind, subject.strip(), self._canonical(candidate), source_turn_id, user_id,
                {**provenance, "source": "method_admission:candidate", "generation": int(generation)},
            )

    @staticmethod
    def _validate_external_promotion(validation: dict[str, Any]) -> None:
        if not isinstance(validation, dict):
            raise MethodAdmissionError("promotion validation receipt required")
        required_true = (
            "source_provenance_complete",
            "counterexample_search_performed",
            "held_out_or_cross_instance_passed",
        )
        required_false = (
            "contamination_increase",
            "stale_state_use",
            "privacy_leakage",
            "authority_leakage",
        )
        if any(validation.get(key) is not True for key in required_true):
            raise MethodAdmissionError("promotion evidence incomplete")
        if any(validation.get(key) is not False for key in required_false):
            raise MethodAdmissionError("promotion leakage/staleness gate failed")
        validator = validation.get("validated_by")
        if not isinstance(validator, str) or not validator.strip():
            raise MethodAdmissionError("validated_by required")
        if validator.strip().lower() in {"microclay", "claude", "claude_completion", "self"}:
            raise MethodAdmissionError("self-promotion is forbidden")
        episodes = validation.get("validation_episode_ids")
        if not isinstance(episodes, list) or not episodes or not all(isinstance(x, str) and x.strip() for x in episodes):
            raise MethodAdmissionError("external validation episodes required")

    def promote(
        self, *, candidate_memory_id: str, promoted_record: dict[str, Any],
        validation: dict[str, Any], user_id: str, session_id: str, turn_id: str,
        episode_id: str, causal_id: str, generation: int
    ) -> dict[str, Any]:
        if not all(isinstance(x, str) and x for x in (
            candidate_memory_id, user_id, session_id, turn_id, episode_id, causal_id
        )):
            raise MethodAdmissionError("promotion requires complete causal identity")
        self._validate_external_promotion(validation)
        candidate_row = self._row_for_user(candidate_memory_id, user_id)
        candidate_kind = str(candidate_row["kind"])
        promoted_kind = CANDIDATE_TO_PROMOTED.get(candidate_kind)
        if promoted_kind is None:
            raise MethodAdmissionError("source memory is not a candidate")
        try:
            candidate = MethodTransfer.validate_record(candidate_kind, str(candidate_row["value"]))
        except MethodRecordError as exc:
            raise MethodAdmissionError("candidate malformed") from exc

        promoted = dict(promoted_record)
        promoted["status"] = "PROMOTED"
        promoted_raw = self._canonical(promoted)
        try:
            MethodTransfer.validate_record(promoted_kind, promoted_raw)
        except MethodRecordError as exc:
            raise MethodAdmissionError(f"promoted record invalid: {exc}") from exc
        if MethodTransfer.normalize_signature(candidate["problem_signature"]) != MethodTransfer.normalize_signature(promoted["problem_signature"]):
            raise MethodAdmissionError("promotion changed candidate problem signature")
        source_episodes = {str(x) for x in promoted["source_episode_ids"]}
        if len(source_episodes) < 2 or int(promoted["support_count"]) < 2:
            raise MethodAdmissionError("single-instance promotion forbidden")

        validation_hash = hashlib.sha256(self._canonical(validation).encode("utf-8")).hexdigest()
        receipt_subject = f"method-promotion:{candidate_memory_id}:{causal_id}"
        with self.db.tx():
            self.db.assert_live_generation(session_id, generation)
            existing = self.db.db.execute(
                "SELECT memory_id,value FROM durable_memory WHERE kind='method_receipt' "
                "AND subject=? AND user_id=? ORDER BY ts DESC LIMIT 1",
                (receipt_subject, user_id),
            ).fetchone()
            if existing:
                try:
                    receipt = json.loads(existing["value"])
                except Exception as exc:
                    raise StaleGeneration("method_promotion_receipt") from exc
                if receipt.get("validation_sha256") != validation_hash:
                    raise StaleGeneration("method_promotion_identity")
                return {
                    "promoted_memory_id": receipt["promoted_memory_id"],
                    "receipt_memory_id": str(existing["memory_id"]),
                    "replayed": True,
                }

            promoted_memory_id = self.db.add_memory(
                promoted_kind, str(candidate_row["subject"]), promoted_raw, turn_id, user_id,
                {
                    "source": "method_admission:promotion",
                    "candidate_memory_id": candidate_memory_id,
                    "validation_sha256": validation_hash,
                    "episode_id": episode_id,
                    "causal_id": causal_id,
                    "generation": int(generation),
                },
            )
            receipt = {
                "action": "PROMOTE",
                "candidate_memory_id": candidate_memory_id,
                "promoted_memory_id": promoted_memory_id,
                "validation_sha256": validation_hash,
                "validated_by": validation["validated_by"],
                "turn_id": turn_id,
                "episode_id": episode_id,
                "causal_id": causal_id,
                "generation": int(generation),
                "truth_authority": False,
                "effect_authority": False,
            }
            receipt_memory_id = self.db.add_memory(
                "method_receipt", receipt_subject, self._canonical(receipt), turn_id, user_id,
                {"source": "method_admission:promotion_receipt", "generation": int(generation)},
            )
        return {
            "promoted_memory_id": promoted_memory_id,
            "receipt_memory_id": receipt_memory_id,
            "replayed": False,
        }

    def change_state(
        self, *, method_memory_id: str, action: str, reason: str,
        counterexample_memory_ids: list[str], user_id: str, session_id: str,
        turn_id: str, episode_id: str, causal_id: str, generation: int
    ) -> dict[str, Any]:
        action = str(action).upper()
        if action not in TERMINAL_METHOD_ACTIONS:
            raise MethodAdmissionError("method state action must be DEMOTE or RETIRE")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 4000:
            raise MethodAdmissionError("bounded demotion/retirement reason required")
        if not isinstance(counterexample_memory_ids, list) or not counterexample_memory_ids:
            raise MethodAdmissionError("negative evidence ids required")
        if any(not isinstance(x, str) or not x for x in counterexample_memory_ids):
            raise MethodAdmissionError("invalid negative evidence ids")
        row = self._row_for_user(method_memory_id, user_id)
        if str(row["kind"]) not in {"framework", "heuristic"}:
            raise MethodAdmissionError("only promoted method can change terminal state")
        receipt_subject = f"method-state:{method_memory_id}"
        receipt = {
            "action": action,
            "method_memory_id": method_memory_id,
            "reason": reason.strip(),
            "counterexample_memory_ids": sorted(set(counterexample_memory_ids)),
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        }
        receipt_raw = self._canonical(receipt)
        with self.db.tx():
            self.db.assert_live_generation(session_id, generation)
            latest = self.db.db.execute(
                "SELECT memory_id,value FROM durable_memory WHERE kind='method_receipt' "
                "AND subject=? AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 1",
                (receipt_subject, user_id),
            ).fetchone()
            if latest and str(latest["value"]) == receipt_raw:
                return {"receipt_memory_id": str(latest["memory_id"]), "replayed": True, "action": action}
            receipt_memory_id = self.db.add_memory(
                "method_receipt", receipt_subject, receipt_raw, turn_id, user_id,
                {"source": "method_admission:state", "generation": int(generation)},
            )
        return {"receipt_memory_id": receipt_memory_id, "replayed": False, "action": action}
