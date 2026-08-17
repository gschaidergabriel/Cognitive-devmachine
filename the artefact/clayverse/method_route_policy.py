from __future__ import annotations

import contextlib
import hashlib
import json
import math
import time
from typing import Any

from .store import StaleGeneration, UnifiedDB


class MethodRoutePolicy:
    """SHADOW-only adaptive entry-point policy for analogical method retrieval.

    Served method selection remains structural-baseline only. Verified causally
    re-entered effect outcomes may change namespaced method:* route capital, which is
    observed only as a shadow ranking until a later externally validated promotion.
    """

    POLICY_VERSION = 1
    MODE = "SHADOW"
    CAPITAL_MIN = -2.0
    CAPITAL_MAX = 4.0
    LEARNING_RATE = 0.20
    REWARD_EMA_ALPHA = 0.10
    ACCESS_RENT = 0.005
    SHADOW_WEIGHT = 0.08
    MAX_PENDING = 100

    def __init__(self, db: UnifiedDB):
        self.db = db

    @contextlib.contextmanager
    def _maybe_tx(self):
        if self.db.db.in_transaction:
            yield self.db.db
        else:
            with self.db.tx() as conn:
                yield conn

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def entry_keys(cls, memory_id: str, problem_signature: dict[str, Any]) -> tuple[str, ...]:
        goal = str(problem_signature.get("goal_shape", "")).strip().lower()
        facets = sorted({str(x).strip().lower() for x in problem_signature.get("facets", []) if str(x).strip()})[:16]
        resources = sorted({str(x).strip().lower() for x in problem_signature.get("resource_shapes", []) if str(x).strip()})[:8]
        sig_payload = {"goal_shape": goal, "facets": facets, "resource_shapes": resources}
        sig_hash = hashlib.sha256(cls._canonical(sig_payload).encode("utf-8")).hexdigest()[:16]
        return (
            f"method:id:{memory_id}",
            f"method:goal:{memory_id}:{goal or 'unknown'}",
            f"method:sig:{memory_id}:{sig_hash}",
        )

    def capitals(self) -> dict[str, float]:
        return {
            str(row["entry_key"]): float(row["capital"])
            for row in self.db.db.execute(
                "SELECT entry_key,capital FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'method:%'"
            ).fetchall()
        }

    @classmethod
    def shadow_bonus(cls, keys: tuple[str, ...], capitals: dict[str, float]) -> float:
        if not keys:
            return 0.0
        values = [
            max(cls.CAPITAL_MIN, min(cls.CAPITAL_MAX, float(capitals.get(key, 0.0))))
            for key in keys
        ]
        mean = sum(values) / len(values)
        return cls.SHADOW_WEIGHT * math.tanh(mean)

    def _feedback_subject(self, use_receipt_id: str, causal_id: str, generation: int, signal: str, credit: float) -> str:
        digest = hashlib.sha256(
            f"{use_receipt_id}\x1f{causal_id}\x1f{generation}\x1f{signal}\x1f{credit:.9f}".encode("utf-8")
        ).hexdigest()
        return f"method-route-feedback:{digest}"

    def learn_from_verified_outcomes(self, *, session_id: str, generation: int) -> dict[str, int]:
        self.db.assert_live_generation(session_id, generation)
        rows = self.db.db.execute(
            "SELECT memory_id,value,user_id,source_turn_id FROM durable_memory "
            "WHERE kind='method_receipt' AND subject LIKE 'method-use:%' "
            "ORDER BY ts LIMIT ?", (self.MAX_PENDING,)
        ).fetchall()
        eligible = 0
        applied = 0
        for row in rows:
            try:
                use = json.loads(row["value"])
            except Exception:
                continue
            if not isinstance(use, dict):
                continue
            try:
                use_generation = int(use.get("generation", -1))
            except (TypeError, ValueError):
                continue
            if use.get("session_id") != session_id or use_generation != int(generation):
                continue
            causal_id = use.get("causal_id")
            entry_keys = use.get("entry_keys")
            if not isinstance(causal_id, str) or not causal_id:
                continue
            if not isinstance(entry_keys, list) or any(not isinstance(k, str) or not k.startswith("method:") for k in entry_keys):
                continue
            outcome = self.db.db.execute(
                "SELECT c.credit,e.status FROM causal_episodes c "
                "JOIN effects e ON e.effect_id=c.effect_id "
                "WHERE c.causal_id=? AND c.reentered=1", (causal_id,)
            ).fetchone()
            if not outcome:
                continue
            eligible += 1
            credit = max(-1.0, min(1.0, float(outcome["credit"])))
            signal = f"effect_outcome:{outcome['status']}"
            subject = self._feedback_subject(str(row["memory_id"]), causal_id, generation, signal, credit)
            if self.db.db.execute(
                "SELECT 1 FROM durable_memory WHERE kind='method_receipt' AND subject=? LIMIT 1", (subject,)
            ).fetchone():
                continue
            with self._maybe_tx():
                now = time.time()
                for key in sorted(set(entry_keys))[:32]:
                    current = self.db.db.execute(
                        "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
                        (key,),
                    ).fetchone()
                    if current:
                        old_capital = float(current["capital"])
                        old_ema = float(current["reward_ema"])
                        pulls = int(current["pulls"])
                    else:
                        old_capital, old_ema, pulls = 0.0, 0.0, 0
                    new_ema = (1.0 - self.REWARD_EMA_ALPHA) * old_ema + self.REWARD_EMA_ALPHA * credit
                    delta = self.LEARNING_RATE * (credit - old_ema) - self.ACCESS_RENT
                    new_capital = max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, old_capital + delta))
                    self.db.db.execute(
                        "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
                        "VALUES(?,?,?,?,?) ON CONFLICT(entry_key) DO UPDATE SET "
                        "capital=excluded.capital,reward_ema=excluded.reward_ema,"
                        "pulls=excluded.pulls,updated_at=excluded.updated_at",
                        (key, new_capital, new_ema, pulls + 1, now),
                    )
                feedback = {
                    "action": "METHOD_ROUTE_CREDIT",
                    "use_receipt_memory_id": str(row["memory_id"]),
                    "causal_id": causal_id,
                    "generation": int(generation),
                    "credit": credit,
                    "signal_class": signal,
                    "entry_keys": sorted(set(entry_keys))[:32],
                    "truth_authority": False,
                    "effect_authority": False,
                }
                self.db.add_memory(
                    "method_receipt", subject, self._canonical(feedback), row["source_turn_id"], row["user_id"],
                    {"source": "method_route_policy:verified_outcome", "generation": int(generation)},
                )
            applied += 1
        return {"eligible": eligible, "applied": applied}
