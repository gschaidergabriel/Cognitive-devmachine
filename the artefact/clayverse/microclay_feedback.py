from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any

from .microclay_retrieval import MicroClayRetrieval, _NON_EVIDENCE_KINDS
from .store import StaleGeneration, UnifiedDB

_FEEDBACK_SCHEMA = "ClayVerseRetrievalFeedback/v1"
_FEEDBACK_SOURCE = "clayverse:retrieval-feedback"
_FEEDBACK_CLASSES = frozenset({
    "USER_RELEVANT",
    "USER_IRRELEVANT",
    "USER_MISS_TARGET",
    "USER_NO_MEMORY",
})
_CUE_HASH = re.compile(r"^[0-9a-f]{16}$")


class MicroClayExplicitFeedback:
    """Apply authenticated canonical user feedback to SHADOW retrieval access only.

    The feedback authority is a later canonical user turn whose stored provenance is
    typed as ClayVerseRetrievalFeedback/v1 and binds the exact retrieval id, feedback
    class and optional target memory id. Free caller strings, Claude completion and
    effect outcomes are not explicit-user provenance.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.organ = MicroClayRetrieval(db)

    @staticmethod
    def _json_list(raw: str, *, name: str, limit: int) -> list[str]:
        try:
            value = json.loads(raw)
        except Exception as exc:
            raise StaleGeneration(f"retrieval_feedback_{name}") from exc
        if (
            not isinstance(value, list)
            or len(value) > limit
            or not all(isinstance(item, str) and item for item in value)
        ):
            raise StaleGeneration(f"retrieval_feedback_{name}")
        return value

    @classmethod
    def _cue_hashes(cls, row) -> list[str]:
        values = cls._json_list(
            row["query_token_hashes"],
            name="query_tokens",
            limit=MicroClayRetrieval.MAX_QUERY_TOKENS,
        )
        if not all(_CUE_HASH.fullmatch(value) for value in values):
            raise StaleGeneration("retrieval_feedback_query_tokens")
        return list(dict.fromkeys(values))

    @staticmethod
    def _safe_provenance(raw: str) -> dict[str, Any]:
        try:
            value = json.loads(raw)
        except Exception as exc:
            raise PermissionError("explicit feedback provenance is malformed") from exc
        if not isinstance(value, dict):
            raise PermissionError("explicit feedback provenance must be an object")
        return value

    def _assert_feedback_turn(
        self,
        db,
        *,
        row,
        feedback_turn_id: str,
        feedback_class: str,
        target_memory_id: str | None,
    ) -> None:
        original = db.execute(
            "SELECT turn_id,session_id,user_id,role,content,ordinal FROM turns WHERE turn_id=?",
            (row["turn_id"],),
        ).fetchone()
        if original is None:
            raise StaleGeneration("retrieval_feedback_original_turn")
        if (
            str(original["session_id"]) != str(row["session_id"])
            or str(original["user_id"]) != str(row["user_id"])
            or str(original["role"]) != "user"
        ):
            raise StaleGeneration("retrieval_feedback_original_turn")
        if hashlib.sha256(str(original["content"]).encode("utf-8")).hexdigest() != str(row["query_hash"]):
            raise StaleGeneration("retrieval_feedback_query_identity")

        feedback = db.execute(
            "SELECT turn_id,session_id,user_id,role,ordinal,provenance FROM turns WHERE turn_id=?",
            (feedback_turn_id,),
        ).fetchone()
        if feedback is None:
            raise KeyError(feedback_turn_id)
        if (
            str(feedback["session_id"]) != str(row["session_id"])
            or str(feedback["user_id"]) != str(row["user_id"])
            or str(feedback["role"]) != "user"
        ):
            raise PermissionError("feedback turn is outside the canonical user session")
        if int(feedback["ordinal"]) <= int(original["ordinal"]):
            raise PermissionError("feedback turn must follow the retrieval turn")

        provenance = self._safe_provenance(feedback["provenance"])
        expected = {
            "schema": _FEEDBACK_SCHEMA,
            "source": _FEEDBACK_SOURCE,
            "retrieval_id": str(row["retrieval_id"]),
            "feedback_class": feedback_class,
            "target_memory_id": target_memory_id,
        }
        for key, value in expected.items():
            if provenance.get(key) != value:
                raise PermissionError(f"feedback provenance mismatch: {key}")

    def _assert_request(
        self,
        row,
        *,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        query_sha256: str,
        budget_chars: int,
    ) -> None:
        try:
            expected = (
                str(row["user_id"]),
                str(row["session_id"]),
                str(row["turn_id"]),
                str(row["episode_id"]),
                str(row["causal_id"]),
                int(row["generation"]),
                str(row["query_hash"]),
                int(row["budget_chars"]),
            )
            supplied = (
                str(user_id),
                str(session_id),
                str(turn_id),
                str(episode_id),
                str(causal_id),
                int(generation),
                str(query_sha256),
                int(budget_chars),
            )
        except (TypeError, ValueError) as exc:
            raise StaleGeneration("retrieval_feedback_identity") from exc
        if supplied != expected:
            raise StaleGeneration("retrieval_feedback_identity")
        if int(row["policy_version"]) != self.organ.POLICY_VERSION:
            raise StaleGeneration("retrieval_feedback_policy_version")
        if str(row["mode"]) != "SHADOW" or self.organ.mode() != "SHADOW":
            raise PermissionError("explicit retrieval feedback is SHADOW-only")
        self.db.assert_live_generation(session_id, generation)

    @staticmethod
    def _target(db, *, row, user_id: str, target_memory_id: str):
        target = db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=?",
            (target_memory_id,),
        ).fetchone()
        if target is None:
            raise KeyError(target_memory_id)
        if str(target["kind"]) in _NON_EVIDENCE_KINDS:
            raise PermissionError("feedback target is not Stage-A evidence")
        if target["user_id"] is not None and str(target["user_id"]) != str(user_id):
            raise PermissionError("feedback target is outside user visibility")
        try:
            target_ts = float(target["ts"])
            retrieval_ts = float(row["ts"])
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise StaleGeneration("retrieval_feedback_temporal_identity") from exc
        if target_ts > retrieval_ts:
            raise PermissionError("feedback target did not exist at retrieval time")
        if (
            target["source_turn_id"] is not None
            and str(target["source_turn_id"]) == str(row["turn_id"])
        ):
            raise PermissionError("current-turn echo cannot train retrieval")
        return target

    @staticmethod
    def _receipt_id(row, *, feedback_class: str, target_memory_id: str | None) -> str:
        # Equivalent repeated feedback for the same retrieval/class/target is one
        # logical signal even if the user emits another canonical feedback turn.
        payload = {
            "schema": _FEEDBACK_SCHEMA,
            "retrieval_id": str(row["retrieval_id"]),
            "turn_id": str(row["turn_id"]),
            "episode_id": str(row["episode_id"]),
            "causal_id": str(row["causal_id"]),
            "session_id": str(row["session_id"]),
            "user_id": str(row["user_id"]),
            "generation": int(row["generation"]),
            "policy_version": int(row["policy_version"]),
            "query_hash": str(row["query_hash"]),
            "budget_chars": int(row["budget_chars"]),
            "feedback_class": feedback_class,
            "target_memory_id": target_memory_id,
        }
        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _apply_capital(self, db, *, key: str, value: float, now: float) -> None:
        current = db.execute(
            "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (key,),
        ).fetchone()
        if current:
            old_capital = float(current["capital"])
            old_ema = float(current["reward_ema"])
            pulls = int(current["pulls"])
        else:
            old_capital, old_ema, pulls = 0.0, 0.0, 0
        new_ema = (
            (1.0 - self.organ.REWARD_EMA_ALPHA) * old_ema
            + self.organ.REWARD_EMA_ALPHA * value
        )
        delta = self.organ.LEARNING_RATE * (value - old_ema) - self.organ.ACCESS_RENT
        new_capital = max(
            self.organ.CAPITAL_MIN,
            min(self.organ.CAPITAL_MAX, old_capital + delta),
        )
        db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES(?,?,?,?,?) ON CONFLICT(entry_key) DO UPDATE SET "
            "capital=excluded.capital,reward_ema=excluded.reward_ema,"
            "pulls=excluded.pulls,updated_at=excluded.updated_at",
            (key, new_capital, new_ema, pulls + 1, now),
        )

    def apply(
        self,
        *,
        retrieval_id: str,
        feedback_turn_id: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        query_sha256: str,
        budget_chars: int,
        feedback_class: str,
        target_memory_id: str | None = None,
    ) -> dict[str, Any]:
        feedback_class = str(feedback_class)
        if feedback_class not in _FEEDBACK_CLASSES:
            raise ValueError("unsupported retrieval feedback class")
        if feedback_class == "USER_NO_MEMORY":
            if target_memory_id is not None:
                raise ValueError("USER_NO_MEMORY cannot name a target memory")
        elif not isinstance(target_memory_id, str) or not target_memory_id:
            raise ValueError("target memory is required for this feedback class")

        with self.organ._credit_tx() as db:
            row = db.execute(
                "SELECT * FROM retrieval_episodes WHERE retrieval_id=?",
                (str(retrieval_id),),
            ).fetchone()
            if row is None:
                raise KeyError(retrieval_id)
            self._assert_request(
                row,
                user_id=user_id,
                session_id=session_id,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
                query_sha256=query_sha256,
                budget_chars=budget_chars,
            )
            self._assert_feedback_turn(
                db,
                row=row,
                feedback_turn_id=feedback_turn_id,
                feedback_class=feedback_class,
                target_memory_id=target_memory_id,
            )

            selected = self._json_list(row["selected_memory_ids"], name="selected", limit=100)
            self._json_list(row["shadow_memory_ids"], name="shadow", limit=100)
            cue_hashes = self._cue_hashes(row)

            target = None
            if target_memory_id is not None:
                target = self._target(
                    db,
                    row=row,
                    user_id=user_id,
                    target_memory_id=target_memory_id,
                )
                if feedback_class in {"USER_RELEVANT", "USER_IRRELEVANT"}:
                    if target_memory_id not in selected:
                        raise PermissionError("relevance feedback target was not served")
                elif feedback_class == "USER_MISS_TARGET" and target_memory_id in selected:
                    raise ValueError("miss target was already served")
                if not cue_hashes:
                    raise ValueError("original retrieval has no routable query cues")

            receipt_id = self._receipt_id(
                row,
                feedback_class=feedback_class,
                target_memory_id=target_memory_id,
            )
            if db.execute(
                "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?",
                (receipt_id,),
            ).fetchone():
                return {
                    "applied": False,
                    "reason": "duplicate_receipt",
                    "receipt_id": receipt_id,
                }

            value = (
                1.0 if feedback_class in {"USER_RELEVANT", "USER_MISS_TARGET"}
                else -1.0 if feedback_class == "USER_IRRELEVANT"
                else 0.0
            )
            route_keys: list[str] = []
            now = time.time()
            if target is not None:
                route_keys = [
                    self.organ._route_key_from_cue_hash(cue_hash, str(target["memory_id"]))
                    for cue_hash in cue_hashes[: self.organ.MAX_ENTRY_KEYS]
                ]
                for key in route_keys:
                    self._apply_capital(db, key=key, value=value, now=now)

            target_suffix = target_memory_id or "none"
            db.execute(
                "INSERT INTO retrieval_feedback(receipt_id,retrieval_id,causal_id,generation,"
                "credit,signal_class,ts) VALUES(?,?,?,?,?,?,?)",
                (
                    receipt_id,
                    str(row["retrieval_id"]),
                    str(row["causal_id"]),
                    int(row["generation"]),
                    value,
                    f"user_explicit:{feedback_class.lower()}:target={target_suffix}:turn={feedback_turn_id}",
                    now,
                ),
            )

        return {
            "applied": True,
            "receipt_id": receipt_id,
            "feedback_turn_id": feedback_turn_id,
            "feedback_class": feedback_class,
            "target_memory_id": target_memory_id,
            "updated_entrypoints": len(route_keys),
            "policy_version": self.organ.POLICY_VERSION,
            "mode": "SHADOW",
            "truth_authority": False,
            "effect_authority": False,
        }
