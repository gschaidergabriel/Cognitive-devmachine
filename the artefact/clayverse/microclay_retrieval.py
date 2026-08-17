from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .store import StaleGeneration, UnifiedDB

_TOKEN = re.compile(r"[\w.-]{2,}", re.UNICODE)


@dataclass(frozen=True)
class RetrievalCandidate:
    memory_id: str
    kind: str
    subject: str
    value: str
    ts: float
    provenance: dict[str, Any]
    baseline_score: float
    adaptive_score: float
    learned_route_score: float
    entry_keys: tuple[str, ...]

    def public(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "kind": self.kind,
            "subject": self.subject,
            "value": self.value,
            "ts": self.ts,
            "provenance": self.provenance,
            "retrieval_score": self.baseline_score,
        }


class MicroClayRetrieval:
    """Persistent bounded online-adaptive retrieval organ.

    MicroClay changes accessibility, entry-point priors and context packing only.
    It cannot alter semantic truth, durable memory contents, provenance, user rights,
    effect authority or EntityOS capabilities.

    The adaptive policy starts in SHADOW. Classical retrieval remains the serving
    path until an explicit externally validated promotion changes the mode.

    Policy version 2 adds learned query-cue -> subject entry routes. Entry-policy
    keys are version-scoped so persisted v1 capital cannot silently change v2
    behavior. A persisted ACTIVE mode from a different policy version is treated
    as SHADOW until that exact policy version is explicitly promoted.
    """

    POLICY_VERSION = 2
    DEFAULT_MODE = "SHADOW"
    MAX_SOURCE_ROWS = 5000
    MAX_QUERY_TOKENS = 64
    MAX_ENTRY_KEYS = 24
    CAPITAL_MIN = -2.0
    CAPITAL_MAX = 4.0
    LEARNING_RATE = 0.20
    REWARD_EMA_ALPHA = 0.10
    ACCESS_RENT = 0.005

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.lower() for x in _TOKEN.findall(text or "")[:256]}

    @staticmethod
    def _token_key(token: str) -> str:
        return "cue:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _policy_key(cls, key: str) -> str:
        return f"v{cls.POLICY_VERSION}:{key}"

    @classmethod
    def _route_key(cls, token: str, subject: str) -> str:
        cue = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
        target = hashlib.sha256(subject.encode("utf-8")).hexdigest()[:16]
        return cls._policy_key(f"route:{cue}:{target}")

    @staticmethod
    def _safe_provenance(raw: str) -> dict[str, Any]:
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {"raw_type": type(value).__name__}
        except Exception:
            return {"parse_error": True}

    @staticmethod
    def _pack_candidates(
        candidates: list[RetrievalCandidate],
        *,
        limit: int,
        budget_chars: int,
        allow_learned_route: bool = False,
    ) -> tuple[list[RetrievalCandidate], int]:
        """Apply the existing count/character budget to one ranked candidate list."""
        selected: list[RetrievalCandidate] = []
        chars = 0
        for item in candidates:
            if item.baseline_score <= 0.0 and not (
                allow_learned_route and item.learned_route_score > 0.0
            ):
                continue
            item_chars = len(item.value)
            # Preserve the current serving contract: the first item may exceed the
            # retrieval-local budget; the later whole-context bound remains the
            # final fail-closed envelope.
            if selected and chars + item_chars > budget_chars:
                continue
            selected.append(item)
            chars += item_chars
            if len(selected) >= limit:
                break
        return selected, chars

    def mode(self) -> str:
        row = self.db.db.execute(
            "SELECT mode,policy_version FROM retrieval_policy_state WHERE singleton=1"
        ).fetchone()
        if not row:
            return self.DEFAULT_MODE
        if int(row["policy_version"]) != self.POLICY_VERSION:
            return self.DEFAULT_MODE
        return row["mode"]

    def _policy_capitals(self) -> dict[str, float]:
        return {
            str(row["entry_key"]): float(row["capital"])
            for row in self.db.db.execute(
                "SELECT entry_key,capital FROM retrieval_entrypoint_policy"
            ).fetchall()
        }

    def _entry_keys(
        self,
        kind: str,
        subject: str,
        query_tokens: set[str],
        value_tokens: set[str],
    ) -> tuple[str, ...]:
        keys = [
            self._policy_key(f"kind:{kind}"),
            self._policy_key(f"subject:{subject}"),
        ]
        for token in sorted(query_tokens.intersection(value_tokens)):
            if len(keys) >= self.MAX_ENTRY_KEYS:
                break
            keys.append(self._policy_key(self._token_key(token)))
        # Query-only cues are bounded hashed proposals to this subject. They are
        # learned only when this evidence was actually served and later receives
        # canonical outcome credit. Generic kind/subject capital therefore cannot
        # open a lexical miss on its own.
        for token in sorted(query_tokens.difference(value_tokens)):
            if len(keys) >= self.MAX_ENTRY_KEYS:
                break
            keys.append(self._route_key(token, subject))
        return tuple(keys)

    def _score_candidate(
        self,
        row,
        query_tokens: set[str],
        now: float,
        capitals: dict[str, float],
    ) -> RetrievalCandidate:
        value = str(row["value"])
        subject = str(row["subject"])
        kind = str(row["kind"])
        value_tokens = self._tokens(value + " " + subject + " " + kind)
        if query_tokens:
            overlap = len(query_tokens.intersection(value_tokens))
            coverage = overlap / max(1, len(query_tokens))
            precision = overlap / max(1, len(value_tokens))
            lexical = min(1.0, 0.75 * coverage + 0.25 * precision)
        else:
            lexical = 0.0

        age_days = max(0.0, (now - float(row["ts"])) / 86400.0)
        recency = math.exp(-age_days / 30.0)
        structured = 1.0 if kind in {
            "fact", "decision", "task", "commitment", "preference", "open", "open_question"
        } else 0.4
        # No cue match means UNKNOWN on the deterministic serving baseline. The
        # adaptive policy may only propose a miss via a positively learned route.
        baseline = (
            (0.82 * lexical) + (0.12 * recency) + (0.06 * structured)
            if lexical > 0.0 else 0.0
        )

        keys = self._entry_keys(kind, subject, query_tokens, value_tokens)
        bounded_capitals = {
            key: max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, capitals.get(key, 0.0)))
            for key in keys
        }
        learned = sum(bounded_capitals.values()) / max(1, len(keys))
        learned_route = max(
            (
                capital
                for key, capital in bounded_capitals.items()
                if key.startswith(self._policy_key("route:"))
            ),
            default=0.0,
        )
        adaptive = baseline + 0.08 * learned

        return RetrievalCandidate(
            memory_id=str(row["memory_id"]),
            kind=kind,
            subject=subject,
            value=value,
            ts=float(row["ts"]),
            provenance=self._safe_provenance(row["provenance"]),
            baseline_score=baseline,
            adaptive_score=adaptive,
            learned_route_score=learned_route,
            entry_keys=keys,
        )

    def learn_from_verified_outcomes(self, *, session_id: str, generation: int) -> dict[str, int]:
        """Consume new effect-outcome receipts from earlier retrieval episodes.

        Learning is delayed until a causally re-entered external outcome exists. Pure
        conversational completion is not treated as reward, avoiding self-reinforcing
        "the retriever liked its own result" feedback.
        """
        self.db.assert_live_generation(session_id, generation)
        rows = self.db.db.execute(
            "SELECT r.causal_id,r.generation,c.credit,e.status "
            "FROM retrieval_episodes r "
            "JOIN causal_episodes c ON c.causal_id=r.causal_id "
            "JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE r.session_id=? AND r.generation=? AND c.reentered=1 "
            "AND NOT EXISTS(SELECT 1 FROM retrieval_feedback f "
            "WHERE f.retrieval_id=r.retrieval_id AND f.signal_class LIKE 'effect_outcome:%') "
            "ORDER BY r.ts LIMIT 100",
            (session_id, int(generation)),
        ).fetchall()
        applied = 0
        for row in rows:
            result = self.credit(
                causal_id=row["causal_id"],
                generation=int(row["generation"]),
                credit=float(row["credit"]),
                signal_class=f"effect_outcome:{row['status']}",
            )
            applied += int(bool(result.get("applied")))
        return {"eligible": len(rows), "applied": applied}

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        limit: int = 24,
        budget_chars: int = 12_000,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("MicroClay retrieval requires a non-empty query")
        if limit < 1 or limit > 100:
            raise ValueError("invalid retrieval limit")
        if budget_chars < 256 or budget_chars > 200_000:
            raise ValueError("invalid retrieval budget")
        self.db.assert_live_generation(session_id, generation)
        learned_outcomes = self.learn_from_verified_outcomes(
            session_id=session_id,
            generation=generation,
        )

        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        existing = self.db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        if existing:
            if (
                existing["session_id"] != session_id
                or int(existing["generation"]) != int(generation)
                or existing["query_hash"] != query_hash
            ):
                raise StaleGeneration("retrieval_identity")
            ids = json.loads(existing["selected_memory_ids"])
            by_id = {
                str(row["memory_id"]): row
                for row in self.db.db.execute(
                    "SELECT * FROM durable_memory WHERE memory_id IN (%s)"
                    % ",".join("?" for _ in ids),
                    tuple(ids),
                ).fetchall()
            } if ids else {}
            items = []
            for memory_id in ids:
                row = by_id.get(memory_id)
                if row is not None:
                    items.append({
                        "memory_id": memory_id,
                        "kind": row["kind"],
                        "subject": row["subject"],
                        "value": row["value"],
                        "ts": float(row["ts"]),
                        "provenance": self._safe_provenance(row["provenance"]),
                        "retrieval_score": None,
                    })
            return {
                "items": items,
                "receipt": {
                    "retrieval_id": existing["retrieval_id"],
                    "policy_version": int(existing["policy_version"]),
                    "mode": existing["mode"],
                    "query_sha256": existing["query_hash"],
                    "candidate_count": None,
                    "selected_count": len(items),
                    "chars_selected": int(existing["chars_selected"]),
                    "status": existing["status"],
                    "shadow_differs": json.loads(existing["selected_memory_ids"]) != json.loads(existing["shadow_memory_ids"]),
                    "truth_authority": False,
                    "effect_authority": False,
                    "outcome_learning_applied": learned_outcomes["applied"],
                    "replayed": True,
                },
            }

        query_tokens = set(sorted(self._tokens(query))[: self.MAX_QUERY_TOKENS])
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            "WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (user_id, turn_id, self.MAX_SOURCE_ROWS),
        ).fetchall()
        now = time.time()
        capitals = self._policy_capitals()
        candidates = [self._score_candidate(row, query_tokens, now, capitals) for row in rows]
        baseline = sorted(
            candidates,
            key=lambda x: (x.baseline_score, x.ts, x.memory_id),
            reverse=True,
        )
        adaptive = sorted(
            candidates,
            key=lambda x: (x.adaptive_score, x.ts, x.memory_id),
            reverse=True,
        )

        baseline_selected, baseline_chars = self._pack_candidates(
            baseline,
            limit=limit,
            budget_chars=budget_chars,
        )
        adaptive_selected, adaptive_chars = self._pack_candidates(
            adaptive,
            limit=limit,
            budget_chars=budget_chars,
            allow_learned_route=True,
        )
        mode = self.mode()
        if mode == "ACTIVE":
            selected, chars = adaptive_selected, adaptive_chars
        else:
            selected, chars = baseline_selected, baseline_chars

        retrieval_id = str(uuid.uuid4())
        token_hashes = [self._token_key(x)[4:] for x in sorted(query_tokens)]
        selected_ids = [x.memory_id for x in selected]
        shadow_ids = [x.memory_id for x in adaptive_selected]

        # Generic cue/kind/subject priors may learn from all served evidence. New
        # query->subject routes are more dangerous: bind them to rank-1 served
        # evidence only so one successful turn cannot spray an alias over the pack.
        route_prefix = self._policy_key("route:")
        non_route_keys = {
            key
            for item in selected
            for key in item.entry_keys
            if not key.startswith(route_prefix)
        }
        rank1_route_keys = {
            key
            for key in (selected[0].entry_keys if selected else ())
            if key.startswith(route_prefix)
        }
        entry_keys = sorted(non_route_keys | rank1_route_keys)[:256]

        self.db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                retrieval_id, turn_id, episode_id, causal_id, session_id, user_id, int(generation),
                self.POLICY_VERSION, mode, query_hash, json.dumps(token_hashes),
                json.dumps(selected_ids), json.dumps(shadow_ids), json.dumps(entry_keys),
                int(budget_chars), int(chars),
                "PRESENT" if selected else "UNKNOWN", now,
            ),
        )

        return {
            "items": [x.public() for x in selected],
            "receipt": {
                "retrieval_id": retrieval_id,
                "policy_version": self.POLICY_VERSION,
                "mode": mode,
                "query_sha256": query_hash,
                "candidate_count": len(candidates),
                "selected_count": len(selected),
                "chars_selected": chars,
                "status": "PRESENT" if selected else "UNKNOWN",
                "shadow_differs": selected_ids != shadow_ids,
                "truth_authority": False,
                "effect_authority": False,
                "outcome_learning_applied": learned_outcomes["applied"],
            },
        }

    def credit(
        self,
        *,
        causal_id: str,
        generation: int,
        credit: float,
        signal_class: str,
        receipt_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically apply provenance-bound outcome credit to retrieval policy only.

        The duplicate-receipt check, all policy-capital mutations and the feedback
        receipt are one BEGIN IMMEDIATE transaction. A crash/failure before the
        receipt insert therefore rolls back the capital mutations as well.
        Replaying the same receipt is idempotent; stale generations are rejected.
        No durable-memory row is changed.
        """
        value = max(-1.0, min(1.0, float(credit)))
        with self.db.tx() as db:
            row = db.execute(
                "SELECT * FROM retrieval_episodes WHERE causal_id=? ORDER BY ts DESC LIMIT 1",
                (causal_id,),
            ).fetchone()
            if not row:
                return {"applied": False, "reason": "no_retrieval_episode"}
            if int(row["generation"]) != int(generation):
                raise StaleGeneration("retrieval_generation")
            self.db.assert_live_generation(row["session_id"], generation)

            rid = receipt_id or hashlib.sha256(
                f"{row['retrieval_id']}\x1f{causal_id}\x1f{generation}\x1f{signal_class}\x1f{value:.9f}".encode()
            ).hexdigest()
            exists = db.execute(
                "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?", (rid,)
            ).fetchone()
            if exists:
                return {"applied": False, "reason": "duplicate_receipt", "receipt_id": rid}

            keys = json.loads(row["entry_keys"])
            now = time.time()
            for key in keys:
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
                new_ema = (1.0 - self.REWARD_EMA_ALPHA) * old_ema + self.REWARD_EMA_ALPHA * value
                delta = self.LEARNING_RATE * (value - old_ema) - self.ACCESS_RENT
                new_capital = max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, old_capital + delta))
                db.execute(
                    "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
                    "VALUES(?,?,?,?,?) ON CONFLICT(entry_key) DO UPDATE SET "
                    "capital=excluded.capital,reward_ema=excluded.reward_ema,"
                    "pulls=excluded.pulls,updated_at=excluded.updated_at",
                    (key, new_capital, new_ema, pulls + 1, now),
                )

            db.execute(
                "INSERT INTO retrieval_feedback(receipt_id,retrieval_id,causal_id,generation,"
                "credit,signal_class,ts) VALUES(?,?,?,?,?,?,?)",
                (rid, row["retrieval_id"], causal_id, int(generation), value, str(signal_class)[:80], now),
            )
            result = {
                "applied": True,
                "receipt_id": rid,
                "policy_version": int(row["policy_version"]),
                "mode": row["mode"],
                "updated_entrypoints": len(keys),
                "truth_authority": False,
                "effect_authority": False,
            }
        return result
