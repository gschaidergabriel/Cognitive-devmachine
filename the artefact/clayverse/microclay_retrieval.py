from __future__ import annotations

import contextlib
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
_NON_EVIDENCE_KINDS = frozenset({
    "source_archive",
    "compression_receipt",
    "compression_clearance",
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
    "method_receipt",
})


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
    """Persistent bounded online-adaptive Stage-A retrieval organ.

    MicroClay changes accessibility, entry-point priors and context packing only.
    It cannot alter semantic truth, durable memory contents, provenance, user rights,
    effect authority or EntityOS capabilities.

    Policy version 2 adds learned query-cue -> exact-memory entry routes. Generic
    v1 kind/subject/cue capital remains ranking-only; only versioned positive route
    capital may open a lexical miss. SHADOW remains the serving default until the
    exact v2 policy is explicitly promoted.
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

    @contextlib.contextmanager
    def _credit_tx(self):
        """Join a canonical outer transaction or create one standalone transaction."""
        if self.db.db.in_transaction:
            yield self.db.db
        else:
            with self.db.tx() as db:
                yield db

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.lower() for x in _TOKEN.findall(text or "")[:256]}

    @staticmethod
    def _token_key(token: str) -> str:
        return "cue:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _route_key_from_cue_hash(cue_hash: str, memory_id: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{16}", str(cue_hash)):
            raise ValueError("invalid MicroClay cue hash")
        target = hashlib.sha256(memory_id.encode("utf-8")).hexdigest()[:16]
        return f"route:v2:{cue_hash}:{target}"

    @classmethod
    def _route_key(cls, token: str, memory_id: str) -> str:
        cue_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
        return cls._route_key_from_cue_hash(cue_hash, memory_id)

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
        selected: list[RetrievalCandidate] = []
        chars = 0
        for item in candidates:
            if item.baseline_score <= 0.0 and not (
                allow_learned_route and item.learned_route_score > 0.0
            ):
                continue
            item_chars = len(item.value)
            if chars + item_chars > budget_chars:
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
            if row["mode"] == "ACTIVE":
                raise StaleGeneration("retrieval_policy_version")
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
        memory_id: str,
        query_tokens: set[str],
        value_tokens: set[str],
    ) -> tuple[str, ...]:
        keys = [f"kind:{kind}", f"subject:{subject}"]
        for token in sorted(query_tokens.intersection(value_tokens)):
            if len(keys) >= self.MAX_ENTRY_KEYS:
                break
            keys.append(self._token_key(token))
        for token in sorted(query_tokens.difference(value_tokens)):
            if len(keys) >= self.MAX_ENTRY_KEYS:
                break
            keys.append(self._route_key(token, memory_id))
        return tuple(keys)

    def _score_candidate(
        self,
        row,
        query_tokens: set[str],
        now: float,
        capitals: dict[str, float],
    ) -> RetrievalCandidate:
        memory_id = str(row["memory_id"])
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
        baseline = (
            (0.82 * lexical) + (0.12 * recency) + (0.06 * structured)
            if lexical > 0.0 else 0.0
        )

        keys = self._entry_keys(kind, subject, memory_id, query_tokens, value_tokens)
        bounded_capitals = {
            key: max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, capitals.get(key, 0.0)))
            for key in keys
        }
        learned = sum(bounded_capitals.values()) / max(1, len(keys))
        learned_route = max(
            (
                capital
                for key, capital in bounded_capitals.items()
                if key.startswith("route:v2:")
            ),
            default=0.0,
        )
        adaptive = baseline + 0.08 * learned

        return RetrievalCandidate(
            memory_id=memory_id,
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
        """Consume only verified, non-zero-credit canonical external outcomes."""
        self.db.assert_live_generation(session_id, generation)
        rows = self.db.db.execute(
            "SELECT r.causal_id,r.generation,c.credit,e.status "
            "FROM retrieval_episodes r "
            "JOIN causal_episodes c ON c.causal_id=r.causal_id "
            "JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE r.session_id=? AND r.generation=? AND c.reentered=1 "
            "AND e.status='VERIFIED' AND c.credit != 0.0 "
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

        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        existing = self.db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        if existing:
            if (
                existing["session_id"] != session_id
                or existing["user_id"] != user_id
                or existing["turn_id"] != turn_id
                or existing["episode_id"] != episode_id
                or int(existing["generation"]) != int(generation)
                or int(existing["policy_version"]) != self.POLICY_VERSION
                or existing["query_hash"] != query_hash
                or int(existing["budget_chars"]) != int(budget_chars)
            ):
                raise StaleGeneration("retrieval_identity")

        # Rejected replay identity must fail before any adaptive mutation.
        learned_outcomes = self.learn_from_verified_outcomes(
            session_id=session_id,
            generation=generation,
        )

        if existing:
            try:
                ids = json.loads(existing["selected_memory_ids"])
            except Exception as exc:
                raise StaleGeneration("retrieval_route_contract") from exc
            if not isinstance(ids, list) or not all(isinstance(x, str) and x for x in ids):
                raise StaleGeneration("retrieval_route_contract")
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
                if row is None:
                    raise StaleGeneration("retrieval_route_contract")
                if str(row["kind"]) in _NON_EVIDENCE_KINDS:
                    raise StaleGeneration("retrieval_route_contract")
                if row["user_id"] is not None and str(row["user_id"]) != str(user_id):
                    raise StaleGeneration("retrieval_route_contract")
                if row["source_turn_id"] is not None and str(row["source_turn_id"]) == str(turn_id):
                    raise StaleGeneration("retrieval_route_contract")
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
        marks = ",".join("?" for _ in _NON_EVIDENCE_KINDS)
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            f"WHERE kind NOT IN ({marks}) "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (*sorted(_NON_EVIDENCE_KINDS), user_id, turn_id, self.MAX_SOURCE_ROWS),
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
            baseline, limit=limit, budget_chars=budget_chars
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

        non_route_keys = {
            key
            for item in selected
            for key in item.entry_keys
            if not key.startswith("route:v2:")
        }
        rank1_route_keys = {
            key
            for key in (selected[0].entry_keys if selected else ())
            if key.startswith("route:v2:")
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
        """Atomically apply provenance-bound credit to retrieval policy only."""
        value = max(-1.0, min(1.0, float(credit)))
        with self._credit_tx() as db:
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
            if db.execute(
                "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?", (rid,)
            ).fetchone():
                return {"applied": False, "reason": "duplicate_receipt", "receipt_id": rid}

            try:
                keys = json.loads(row["entry_keys"])
            except Exception as exc:
                raise StaleGeneration("retrieval_credit_contract") from exc
            if not isinstance(keys, list) or len(keys) > 256 or not all(
                isinstance(key, str) and key for key in keys
            ):
                raise StaleGeneration("retrieval_credit_contract")

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
                new_ema = (
                    (1.0 - self.REWARD_EMA_ALPHA) * old_ema
                    + self.REWARD_EMA_ALPHA * value
                )
                delta = self.LEARNING_RATE * (value - old_ema) - self.ACCESS_RENT
                new_capital = max(
                    self.CAPITAL_MIN,
                    min(self.CAPITAL_MAX, old_capital + delta),
                )
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
            return {
                "applied": True,
                "receipt_id": rid,
                "policy_version": int(row["policy_version"]),
                "mode": row["mode"],
                "updated_entrypoints": len(keys),
                "truth_authority": False,
                "effect_authority": False,
            }
