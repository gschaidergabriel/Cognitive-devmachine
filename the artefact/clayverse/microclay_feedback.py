from __future__ import annotations

import contextlib
import hashlib
import json
import re
import time
from typing import Any

from .microclay_methods import METHOD_KINDS
from .microclay_retrieval import MicroClayRetrieval
from .store import StaleGeneration, UnifiedDB

_CONTROL_KINDS = frozenset({
    "source_archive", "compression_receipt", "compression_clearance"
})
_FEEDBACK_CLASSES = frozenset({
    "USER_RELEVANT", "USER_IRRELEVANT", "USER_MISS_TARGET", "USER_NO_MEMORY"
})
_CUE_HASH = re.compile(r"^[0-9a-f]{16}$")


class MicroClayExplicitFeedback:
    """Trusted typed Stage-A retrieval correction; accessibility only, never truth.

    A normal Claude completion or verified downstream effect cannot identify an
    unserved memory that should have been retrieved. This SHADOW-only organ admits
    only explicit typed user feedback bound to the exact original retrieval request.
    It may change bounded cue->memory route capital; it cannot mutate memory content,
    provenance, user rights, method truth, effect authority or serving mode.
    """

    SOURCE = "USER_EXPLICIT"

    def __init__(self, db: UnifiedDB):
        self.db = db

    @contextlib.contextmanager
    def _tx(self):
        if self.db.db.in_transaction:
            yield self.db.db
        else:
            with self.db.tx() as db:
                yield db

    @staticmethod
    def _list(raw: str, *, name: str, limit: int) -> list[str]:
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
        values = cls._list(
            row["query_token_hashes"],
            name="query_tokens",
            limit=MicroClayRetrieval.MAX_QUERY_TOKENS,
        )
        if not all(_CUE_HASH.fullmatch(value) for value in values):
            raise StaleGeneration("retrieval_feedback_query_tokens")
        return list(dict.fromkeys(values))

    @staticmethod
    def _route_key(cue_hash: str, memory_id: str) -> str:
        target = hashlib.sha256(memory_id.encode("utf-8")).hexdigest()[:16]
        return f"route:{cue_hash}:{target}"

    @staticmethod
    def _receipt_id(row, feedback_class: str, target_memory_id: str | None) -> str:
        payload = {
            "schema": "ClayVerseMicroClayExplicitFeedback/v2",
            "source": MicroClayExplicitFeedback.SOURCE,
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
            "limit_items": int(row["limit_items"]),
            "feedback_class": feedback_class,
            "target_memory_id": target_memory_id,
        }
        raw = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

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
        limit_items: int,
    ) -> None:
        try:
            expected = (
                str(row["user_id"]), str(row["session_id"]), str(row["turn_id"]),
                str(row["episode_id"]), str(row["causal_id"]), int(row["generation"]),
                str(row["query_hash"]), int(row["budget_chars"]), int(row["limit_items"]),
            )
            supplied = (
                str(user_id), str(session_id), str(turn_id), str(episode_id), str(causal_id),
                int(generation), str(query_sha256), int(budget_chars), int(limit_items),
            )
        except (TypeError, ValueError) as exc:
            raise StaleGeneration("retrieval_feedback_identity") from exc
        if supplied != expected:
            raise StaleGeneration("retrieval_feedback_identity")
        if int(row["policy_version"]) != MicroClayRetrieval.POLICY_VERSION:
            raise StaleGeneration("retrieval_feedback_policy_version")
        if str(row["mode"]) != "SHADOW" or MicroClayRetrieval(self.db).mode() != "SHADOW":
            raise PermissionError("explicit retrieval feedback v2 is SHADOW-only")
        self.db.assert_live_generation(session_id, generation)

    @staticmethod
    def _target(db, *, row, user_id: str, target_memory_id: str):
        target = db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=?", (target_memory_id,)
        ).fetchone()
        if target is None:
            raise KeyError(target_memory_id)
        if str(target["kind"]) in METHOD_KINDS | _CONTROL_KINDS:
            raise PermissionError("target memory kind is not Stage-A evidence")
        if target["user_id"] is not None and str(target["user_id"]) != str(user_id):
            raise PermissionError("target memory is outside user visibility")
        try:
            target_ts = float(target["ts"])
            retrieval_ts = float(row["ts"])
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise StaleGeneration("retrieval_feedback_temporal_identity") from exc
        if target_ts > retrieval_ts:
            raise PermissionError("target memory did not exist at retrieval time")
        if (
            target["source_turn_id"] is not None
            and str(target["source_turn_id"]) == str(row["turn_id"])
        ):
            raise PermissionError("current-turn echo cannot train retrieval")
        return target

    @staticmethod
    def _apply_capital(db, key: str, value: float, now: float) -> None:
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
            (1.0 - MicroClayRetrieval.REWARD_EMA_ALPHA) * old_ema
            + MicroClayRetrieval.REWARD_EMA_ALPHA * value
        )
        delta = MicroClayRetrieval.LEARNING_RATE * (value - old_ema) - MicroClayRetrieval.ACCESS_RENT
        new_capital = max(
            MicroClayRetrieval.CAPITAL_MIN,
            min(MicroClayRetrieval.CAPITAL_MAX, old_capital + delta),
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
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        query_sha256: str,
        budget_chars: int,
        limit_items: int,
        feedback_class: str,
        source: str,
        target_memory_id: str | None = None,
    ) -> dict[str, Any]:
        if str(source) != self.SOURCE:
            raise PermissionError("retrieval feedback requires explicit user provenance")
        feedback_class = str(feedback_class)
        if feedback_class not in _FEEDBACK_CLASSES:
            raise ValueError("unsupported retrieval feedback class")
        if feedback_class == "USER_NO_MEMORY":
            if target_memory_id is not None:
                raise ValueError("USER_NO_MEMORY cannot name a target memory")
        elif not isinstance(target_memory_id, str) or not target_memory_id:
            raise ValueError("target memory is required for this feedback class")

        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM retrieval_episodes WHERE retrieval_id=?", (str(retrieval_id),)
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
                limit_items=limit_items,
            )
            retrieval = MicroClayRetrieval(self.db)
            retrieval._assert_replay_route(row)
            selected = self._list(row["selected_memory_ids"], name="selected", limit=100)
            self._list(row["shadow_memory_ids"], name="shadow", limit=100)
            cue_hashes = self._cue_hashes(row)

            target = None
            if target_memory_id is not None:
                target = self._target(
                    db, row=row, user_id=user_id, target_memory_id=target_memory_id
                )
                if feedback_class in {"USER_RELEVANT", "USER_IRRELEVANT"}:
                    if target_memory_id not in selected:
                        raise PermissionError("relevance feedback target was not served")
                elif feedback_class == "USER_MISS_TARGET" and target_memory_id in selected:
                    raise ValueError("miss target was already served")
                if not cue_hashes:
                    raise ValueError("original retrieval has no routable query cues")

            receipt_id = self._receipt_id(row, feedback_class, target_memory_id)
            if db.execute(
                "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?", (receipt_id,)
            ).fetchone():
                return {"applied": False, "reason": "duplicate_receipt", "receipt_id": receipt_id}

            value = (
                1.0 if feedback_class in {"USER_RELEVANT", "USER_MISS_TARGET"}
                else -1.0 if feedback_class == "USER_IRRELEVANT"
                else 0.0
            )
            route_keys: list[str] = []
            now = time.time()
            if target is not None:
                route_keys = [
                    self._route_key(cue_hash, str(target["memory_id"]))
                    for cue_hash in cue_hashes[: MicroClayRetrieval.MAX_ENTRY_KEYS]
                ]
                for key in route_keys:
                    self._apply_capital(db, key, value, now)

            target_suffix = target_memory_id or "none"
            db.execute(
                "INSERT INTO retrieval_feedback(receipt_id,retrieval_id,causal_id,generation,"
                "credit,signal_class,ts) VALUES(?,?,?,?,?,?,?)",
                (
                    receipt_id, str(row["retrieval_id"]), str(row["causal_id"]),
                    int(row["generation"]), value,
                    f"user_explicit:{feedback_class.lower()}:{target_suffix}", now,
                ),
            )

        return {
            "applied": True,
            "receipt_id": receipt_id,
            "feedback_class": feedback_class,
            "target_memory_id": target_memory_id,
            "updated_entrypoints": len(route_keys),
            "mode": "SHADOW",
            "truth_authority": False,
            "effect_authority": False,
        }