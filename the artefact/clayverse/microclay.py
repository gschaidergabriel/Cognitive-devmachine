from __future__ import annotations

import json
import math
import re
import time
from typing import Any


class MicroClayRetrieval:
    """Tiny persistent controller that learns a bounded retrieval entry policy.

    The controller never promotes semantic truth. It only chooses among fixed,
    inspectable context budgets and learns from strong causal or explicit feedback.
    State lives in UnifiedDB.meta; each decision/feedback receipt is attached to the
    originating user turn provenance so the mechanism is auditable and reversible.
    """

    VERSION = 1
    CONTROLLER_ID = "microclay-retrieval-v1"
    DISCOUNT = 0.90
    EXPLORATION = 1.50
    BASELINE = "balanced"
    PROFILES = {
        "balanced": {"own_turn_window": 20, "cross_session_limit": 10, "memory_limit": 50},
        "focused": {"own_turn_window": 8, "cross_session_limit": 2, "memory_limit": 12},
        "shared": {"own_turn_window": 12, "cross_session_limit": 10, "memory_limit": 20},
        "memory": {"own_turn_window": 12, "cross_session_limit": 3, "memory_limit": 50},
    }
    EXPLORATION_ORDER = ("focused", "shared", "memory", "balanced")

    _NEGATIVE = re.compile(
        r"^\s*(?:falsch\b|das\s+ist\s+falsch\b|stimmt\s+nicht\b|"
        r"wrong\b|incorrect\b|that(?:'s|\s+is)\s+wrong\b|not\s+what\s+i\s+asked\b)",
        re.IGNORECASE,
    )
    _POSITIVE = re.compile(
        r"^\s*(?:genau\b|richtig\b|passt\b|stimmt\b|perfekt\b|"
        r"correct\b|exactly\b|that(?:'s|\s+is)\s+right\b)",
        re.IGNORECASE,
    )

    def __init__(self, db):
        self.db = db

    @classmethod
    def baseline_decision(cls, bucket: str = "local") -> dict[str, Any]:
        return {
            "controller": cls.CONTROLLER_ID,
            "version": cls.VERSION,
            "bucket": bucket,
            "policy_id": cls.BASELINE,
            "limits": dict(cls.PROFILES[cls.BASELINE]),
            "feedback_count": 0,
            "adaptive": False,
            "state_recovered": False,
            "persisted": False,
        }

    @classmethod
    def _bucket(cls, resource_refs) -> str:
        return "shared" if resource_refs else "local"

    @classmethod
    def _state_key(cls, user_id: str, bucket: str) -> str:
        return f"microclay.retrieval.v{cls.VERSION}.{user_id}.{bucket}"

    @classmethod
    def _fresh_state(cls) -> dict[str, Any]:
        return {
            "version": cls.VERSION,
            "feedback_count": 0,
            "profiles": {
                policy_id: {"weight": 0.0, "reward_sum": 0.0}
                for policy_id in cls.PROFILES
            },
            "updated_at": 0.0,
        }

    def _load_state(self, user_id: str, bucket: str) -> tuple[dict[str, Any], bool]:
        row = self.db.db.execute(
            "SELECT value FROM meta WHERE key=?", (self._state_key(user_id, bucket),)
        ).fetchone()
        if not row:
            return self._fresh_state(), False
        try:
            state = json.loads(row[0])
            if not isinstance(state, dict) or int(state.get("version", -1)) != self.VERSION:
                raise ValueError("version")
            profiles = state.get("profiles")
            if not isinstance(profiles, dict) or set(profiles) != set(self.PROFILES):
                raise ValueError("profiles")
            feedback_count = int(state.get("feedback_count", 0))
            if feedback_count < 0:
                raise ValueError("feedback_count")
            cleaned = self._fresh_state()
            cleaned["feedback_count"] = feedback_count
            cleaned["updated_at"] = float(state.get("updated_at", 0.0))
            for policy_id in self.PROFILES:
                raw = profiles[policy_id]
                weight = float(raw.get("weight", 0.0))
                reward_sum = float(raw.get("reward_sum", 0.0))
                if not math.isfinite(weight) or not math.isfinite(reward_sum) or weight < 0.0:
                    raise ValueError("non-finite policy state")
                cleaned["profiles"][policy_id] = {
                    "weight": min(weight, 1_000_000.0),
                    "reward_sum": max(-1_000_000.0, min(1_000_000.0, reward_sum)),
                }
            return cleaned, False
        except (TypeError, ValueError, json.JSONDecodeError, OverflowError):
            return self._fresh_state(), True

    def _save_state(self, user_id: str, bucket: str, state: dict[str, Any]) -> None:
        payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
        self.db.db.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (self._state_key(user_id, bucket), payload),
        )

    @staticmethod
    def _parse_provenance(row) -> dict[str, Any]:
        try:
            value = json.loads(row["provenance"])
            return value if isinstance(value, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def _select_policy(self, state: dict[str, Any]) -> str:
        if int(state.get("feedback_count", 0)) <= 0:
            return self.BASELINE
        profiles = state["profiles"]
        for policy_id in self.EXPLORATION_ORDER:
            if float(profiles[policy_id]["weight"]) < 0.25:
                return policy_id
        total_weight = sum(float(v["weight"]) for v in profiles.values())
        log_total = math.log(max(1.0, total_weight) + 1.0)
        scores: dict[str, float] = {}
        for policy_id, values in profiles.items():
            weight = max(float(values["weight"]), 1e-9)
            mean = float(values["reward_sum"]) / weight
            bonus = math.sqrt(self.EXPLORATION * log_total / weight)
            scores[policy_id] = mean + bonus
        rank = {name: -index for index, name in enumerate(self.EXPLORATION_ORDER)}
        return max(self.PROFILES, key=lambda name: (scores[name], rank.get(name, -999)))

    def _apply_feedback(self, user_id: str, bucket: str, policy_id: str, reward: float) -> dict[str, Any]:
        if policy_id not in self.PROFILES:
            return {"applied": False, "reason": "unknown_policy"}
        reward = max(-1.0, min(1.0, float(reward)))
        state, recovered = self._load_state(user_id, bucket)
        for values in state["profiles"].values():
            values["weight"] *= self.DISCOUNT
            values["reward_sum"] *= self.DISCOUNT
        target = state["profiles"][policy_id]
        target["weight"] += 1.0
        target["reward_sum"] += reward
        state["feedback_count"] = int(state["feedback_count"]) + 1
        state["updated_at"] = time.time()
        self._save_state(user_id, bucket, state)
        return {
            "applied": True,
            "reward": reward,
            "feedback_count": state["feedback_count"],
            "state_recovered": recovered,
        }

    def _explicit_feedback(self, prompt: str) -> float | None:
        if self._NEGATIVE.search(prompt):
            return -0.70
        if self._POSITIVE.search(prompt):
            return 0.70
        return None

    def _observe_previous(self, session_id: str, current_row, current_prompt: str) -> dict[str, Any] | None:
        previous = self.db.db.execute(
            "SELECT * FROM turns WHERE session_id=? AND role='user' AND ordinal<? "
            "ORDER BY ordinal DESC LIMIT 1",
            (session_id, int(current_row["ordinal"])),
        ).fetchone()
        if previous is None:
            return None
        provenance = self._parse_provenance(previous)
        decision = provenance.get("retrieval_policy")
        if not isinstance(decision, dict) or decision.get("controller") != self.CONTROLLER_ID:
            return None
        if isinstance(provenance.get("retrieval_feedback"), dict):
            return None
        policy_id = decision.get("policy_id")
        bucket = decision.get("bucket")
        if policy_id not in self.PROFILES or bucket not in {"local", "shared"}:
            return None

        reward: float | None = None
        source: str | None = None
        causal = self.db.db.execute(
            "SELECT effect_id,credit FROM causal_episodes WHERE observation_turn_id=? AND reentered=1 "
            "ORDER BY ts DESC LIMIT 1",
            (previous["turn_id"],),
        ).fetchone()
        if causal is not None and causal["effect_id"] is not None:
            reward = 1.0 if float(causal["credit"]) > 0.0 else -1.0
            source = "causal_effect"
        else:
            reward = self._explicit_feedback(current_prompt)
            source = "explicit_next_prompt" if reward is not None else None
        if reward is None or source is None:
            return None

        applied = self._apply_feedback(previous["user_id"], bucket, policy_id, reward)
        if not applied.get("applied"):
            return applied
        receipt = {
            "controller": self.CONTROLLER_ID,
            "source": source,
            "reward": applied["reward"],
            "observed_at": time.time(),
        }
        provenance["retrieval_feedback"] = receipt
        self.db.db.execute(
            "UPDATE turns SET provenance=? WHERE turn_id=?",
            (json.dumps(provenance, sort_keys=True), previous["turn_id"]),
        )
        return receipt

    def decision(self, session_id: str, user_id: str, resource_refs) -> dict[str, Any]:
        bucket = self._bucket(resource_refs)
        current = self.db.db.execute(
            "SELECT * FROM turns WHERE session_id=? AND role='user' ORDER BY ordinal DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if current is None:
            return self.baseline_decision(bucket)

        current_provenance = self._parse_provenance(current)
        existing = current_provenance.get("retrieval_policy")
        if (
            isinstance(existing, dict)
            and existing.get("controller") == self.CONTROLLER_ID
            and existing.get("policy_id") in self.PROFILES
        ):
            return existing

        feedback = self._observe_previous(session_id, current, str(current["content"]))
        state, recovered = self._load_state(user_id, bucket)
        policy_id = self._select_policy(state)
        decision = {
            "controller": self.CONTROLLER_ID,
            "version": self.VERSION,
            "bucket": bucket,
            "policy_id": policy_id,
            "limits": dict(self.PROFILES[policy_id]),
            "feedback_count": int(state["feedback_count"]),
            "adaptive": int(state["feedback_count"]) > 0,
            "state_recovered": recovered,
            "persisted": True,
        }
        if feedback is not None:
            decision["feedback_applied"] = feedback
        current_provenance["retrieval_policy"] = decision
        self.db.db.execute(
            "UPDATE turns SET provenance=? WHERE turn_id=?",
            (json.dumps(current_provenance, sort_keys=True), current["turn_id"]),
        )
        return decision
