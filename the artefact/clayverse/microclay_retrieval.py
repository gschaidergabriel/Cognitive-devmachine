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

    Stage A retrieves evidence memory only. Stage B retrieves method memory only.
    The channels are non-substitutable: METHOD_PRESENT can improve investigation but
    can never convert a factual UNKNOWN into PRESENT.

    MicroClay changes accessibility, entry-point priors and context packing only.
    It cannot alter semantic truth, durable memory contents, provenance, user rights,
    effect authority or EntityOS capabilities.

    The adaptive evidence policy starts in SHADOW. Classical evidence retrieval remains
    the serving path until an explicit externally validated promotion changes the mode.
    """

    POLICY_VERSION = 1
    DEFAULT_MODE = "SHADOW"
    MAX_SOURCE_ROWS = 5000
    MAX_QUERY_TOKENS = 64
    MAX_ENTRY_KEYS = 24
    CAPITAL_MIN = -2.0
    CAPITAL_MAX = 4.0
    LEARNING_RATE = 0.20
    REWARD_EMA_ALPHA = 0.10
    ACCESS_RENT = 0.005

    METHOD_ACTIVE_KINDS = frozenset({
        "framework", "heuristic", "failure_pattern", "counterexample"
    })
    METHOD_CANDIDATE_KINDS = frozenset({
        "framework_candidate", "heuristic_candidate"
    })
    METHOD_CONTROL_KINDS = frozenset({"method_receipt"})
    METHOD_KINDS = METHOD_ACTIVE_KINDS | METHOD_CANDIDATE_KINDS | METHOD_CONTROL_KINDS
    CONTROL_KINDS = frozenset({
        "source_archive", "compression_receipt", "compression_clearance"
    })

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.lower() for x in _TOKEN.findall(text or "")[:256]}

    @staticmethod
    def _token_key(token: str) -> str:
        return "cue:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]

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
    ) -> tuple[list[RetrievalCandidate], int]:
        """Apply the same relevance, count and character budget to any evidence ranking."""
        selected: list[RetrievalCandidate] = []
        chars = 0
        for item in candidates:
            if item.baseline_score <= 0.0:
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
            "SELECT mode FROM retrieval_policy_state WHERE singleton=1"
        ).fetchone()
        return row["mode"] if row else self.DEFAULT_MODE

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
        keys = [f"kind:{kind}", f"subject:{subject}"]
        for token in sorted(query_tokens.intersection(value_tokens))[: self.MAX_ENTRY_KEYS - 2]:
            keys.append(self._token_key(token))
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
        # No cue match means UNKNOWN, not "probably relevant because recent". The
        # recent 20-turn working window handles conversational continuity separately.
        baseline = (
            (0.82 * lexical) + (0.12 * recency) + (0.06 * structured)
            if lexical > 0.0 else 0.0
        )

        keys = self._entry_keys(kind, subject, query_tokens, value_tokens)
        learned = sum(
            max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, capitals.get(k, 0.0)))
            for k in keys
        )
        learned /= max(1, len(keys))
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
            entry_keys=keys,
        )

    @staticmethod
    def _as_string_list(value: Any, *, field: str) -> list[str]:
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, list) and all(isinstance(x, str) for x in value):
            items = value
        else:
            raise ValueError(f"malformed method record field: {field}")
        cleaned = [x.strip() for x in items if x.strip()]
        if not cleaned:
            raise ValueError(f"empty method record field: {field}")
        return cleaned

    def _method_record(self, row) -> dict[str, Any]:
        provenance = self._safe_provenance(row["provenance"])
        record = provenance.get("method_record")
        if record is None:
            try:
                record = json.loads(str(row["value"]))
            except Exception as exc:
                raise ValueError(
                    f"malformed method memory {row['memory_id']}: no structured record"
                ) from exc
        if not isinstance(record, dict):
            raise ValueError(f"malformed method memory {row['memory_id']}: record must be an object")
        if str(record.get("lifecycle_status", "")).upper() != "PROMOTED":
            raise ValueError(f"method memory {row['memory_id']} is not PROMOTED")

        normalized = dict(record)
        normalized["problem_signature"] = self._as_string_list(
            record.get("problem_signature"), field="problem_signature"
        )
        normalized["scope_limits"] = self._as_string_list(
            record.get("scope_limits"), field="scope_limits"
        )
        kind = str(row["kind"])
        if kind in {"framework", "heuristic"}:
            normalized["preconditions"] = self._as_string_list(
                record.get("preconditions"), field="preconditions"
            )
            normalized["method_steps"] = self._as_string_list(
                record.get("method_steps"), field="method_steps"
            )
            normalized["falsifiers"] = self._as_string_list(
                record.get("falsifiers"), field="falsifiers"
            )
        elif kind == "failure_pattern":
            normalized["failure_modes"] = self._as_string_list(
                record.get("failure_modes"), field="failure_modes"
            )
        elif kind == "counterexample":
            normalized["counterevidence"] = self._as_string_list(
                record.get("counterevidence"), field="counterevidence"
            )
        else:
            raise ValueError(f"unsupported active method kind: {kind}")
        return normalized

    def learn_from_verified_outcomes(self, *, session_id: str, generation: int) -> dict[str, int]:
        """Consume new canonical effect-outcome receipts from evidence retrieval episodes."""
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
        """Stage A: evidence-only retrieval and adaptive evidence-route learning."""
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
                or existing["query_hash"] != query_hash
                or int(existing["budget_chars"]) != int(budget_chars)
                or existing["limit_items"] is None
                or int(existing["limit_items"]) != int(limit)
            ):
                raise StaleGeneration("retrieval_identity")

        # Request identity is fail-closed before any adaptive state mutation.
        learned_outcomes = self.learn_from_verified_outcomes(
            session_id=session_id,
            generation=generation,
        )

        if existing:
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
                    if str(row["kind"]) in self.METHOD_KINDS:
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
                    "route": "evidence",
                    "query_sha256": existing["query_hash"],
                    "candidate_count": None,
                    "selected_count": len(items),
                    "limit_requested": int(existing["limit_items"]),
                    "budget_chars": int(existing["budget_chars"]),
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
        excluded = tuple(sorted(self.CONTROL_KINDS | self.METHOD_KINDS))
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            f"WHERE kind NOT IN ({','.join('?' for _ in excluded)}) "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (*excluded, user_id, turn_id, self.MAX_SOURCE_ROWS),
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
            adaptive, limit=limit, budget_chars=budget_chars
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
        entry_keys = sorted({k for item in selected for k in item.entry_keys})[:256]

        self.db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                retrieval_id, turn_id, episode_id, causal_id, session_id, user_id, int(generation),
                self.POLICY_VERSION, mode, query_hash, json.dumps(token_hashes),
                json.dumps(selected_ids), json.dumps(shadow_ids), json.dumps(entry_keys),
                int(budget_chars), int(limit), int(chars),
                "PRESENT" if selected else "UNKNOWN", now,
            ),
        )

        return {
            "items": [x.public() for x in selected],
            "receipt": {
                "retrieval_id": retrieval_id,
                "policy_version": self.POLICY_VERSION,
                "mode": mode,
                "route": "evidence",
                "query_sha256": query_hash,
                "candidate_count": len(candidates),
                "selected_count": len(selected),
                "limit_requested": int(limit),
                "budget_chars": int(budget_chars),
                "chars_selected": chars,
                "status": "PRESENT" if selected else "UNKNOWN",
                "shadow_differs": selected_ids != shadow_ids,
                "truth_authority": False,
                "effect_authority": False,
                "outcome_learning_applied": learned_outcomes["applied"],
            },
        }

    def retrieve_methods(
        self,
        *,
        query: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        limit: int = 8,
        budget_chars: int = 6_000,
    ) -> dict[str, Any]:
        """Stage B: bounded promoted-method retrieval by structural problem signature.

        This route never writes a factual retrieval episode and never changes Stage-A
        status. Candidate/control method kinds are not served. Under-specified promoted
        method records fail closed instead of being guessed into a reusable method.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("method retrieval requires a non-empty query")
        if limit < 1 or limit > 32:
            raise ValueError("invalid method retrieval limit")
        if budget_chars < 256 or budget_chars > 100_000:
            raise ValueError("invalid method retrieval budget")
        self.db.assert_live_generation(session_id, generation)
        session = self.db.db.execute(
            "SELECT user_id FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if not session or session["user_id"] != user_id:
            raise PermissionError("session/user identity mismatch")

        active = tuple(sorted(self.METHOD_ACTIVE_KINDS))
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            f"WHERE kind IN ({','.join('?' for _ in active)}) "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (*active, user_id, turn_id, self.MAX_SOURCE_ROWS),
        ).fetchall()
        qtokens = set(sorted(self._tokens(query))[: self.MAX_QUERY_TOKENS])
        ranked: list[tuple[float, float, str, dict[str, Any]]] = []
        for row in rows:
            record = self._method_record(row)
            signature_tokens = self._tokens(" ".join(record["problem_signature"]))
            overlap = len(qtokens.intersection(signature_tokens))
            if overlap <= 0:
                continue
            coverage = overlap / max(1, len(qtokens))
            signature_precision = overlap / max(1, len(signature_tokens))
            structural = min(1.0, 0.70 * coverage + 0.30 * signature_precision)
            surface_tokens = self._tokens(str(row["subject"]) + " " + str(row["value"]))
            lexical_overlap = len(qtokens.intersection(surface_tokens)) / max(1, len(qtokens))
            score = 0.90 * structural + 0.10 * lexical_overlap
            ranked.append((score, float(row["ts"]), str(row["memory_id"]), {
                "memory_id": str(row["memory_id"]),
                "kind": str(row["kind"]),
                "subject": str(row["subject"]),
                "method_record": record,
                "structural_match": score,
                "provenance": self._safe_provenance(row["provenance"]),
                "truth_authority": False,
                "effect_authority": False,
            }))

        ranked.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        selected: list[dict[str, Any]] = []
        chars = 0
        for _, _, _, item in ranked:
            item_chars = len(json.dumps(
                item["method_record"], sort_keys=True, separators=(",", ":")
            ))
            if chars + item_chars > budget_chars:
                continue
            selected.append(item)
            chars += item_chars
            if len(selected) >= limit:
                break

        return {
            "items": selected,
            "receipt": {
                "route": "method",
                "session_id": session_id,
                "user_id": user_id,
                "turn_id": turn_id,
                "episode_id": episode_id,
                "causal_id": causal_id,
                "generation": int(generation),
                "policy_version": self.POLICY_VERSION,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "candidate_count": len(ranked),
                "selected_count": len(selected),
                "limit_requested": int(limit),
                "budget_chars": int(budget_chars),
                "chars_selected": chars,
                "status": "METHOD_PRESENT" if selected else "METHOD_UNKNOWN",
                "truth_authority": False,
                "effect_authority": False,
                "adaptive": False,
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
        """Apply only the canonical causally re-entered effect outcome to evidence policy.

        Caller-supplied credit, signal class and receipt identity are treated as claims
        to verify against UnifiedDB, not as learning authority. Replays are idempotent;
        stale generations and forged/missing outcome evidence fail closed. Durable
        memory content and semantic truth remain untouched.
        """
        row = self.db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=? ORDER BY ts DESC LIMIT 1",
            (causal_id,),
        ).fetchone()
        if not row:
            return {"applied": False, "reason": "no_retrieval_episode"}
        if int(row["generation"]) != int(generation):
            raise StaleGeneration("retrieval_generation")
        self.db.assert_live_generation(row["session_id"], generation)

        outcome = self.db.db.execute(
            "SELECT c.credit,e.status FROM causal_episodes c "
            "JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE c.causal_id=? AND c.reentered=1",
            (causal_id,),
        ).fetchone()
        if not outcome:
            return {"applied": False, "reason": "unverified_outcome"}

        value = max(-1.0, min(1.0, float(outcome["credit"])))
        expected_signal = f"effect_outcome:{outcome['status']}"
        try:
            claimed_value = max(-1.0, min(1.0, float(credit)))
        except (TypeError, ValueError):
            return {"applied": False, "reason": "outcome_claim_mismatch"}
        if claimed_value != value or str(signal_class) != expected_signal:
            return {"applied": False, "reason": "outcome_claim_mismatch"}

        rid = hashlib.sha256(
            f"{row['retrieval_id']}\x1f{causal_id}\x1f{generation}\x1f{expected_signal}\x1f{value:.9f}".encode()
        ).hexdigest()
        if receipt_id is not None and str(receipt_id) != rid:
            return {"applied": False, "reason": "receipt_identity_mismatch", "receipt_id": rid}
        exists = self.db.db.execute(
            "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?", (rid,)
        ).fetchone()
        if exists:
            return {"applied": False, "reason": "duplicate_receipt", "receipt_id": rid}

        keys = json.loads(row["entry_keys"])
        now = time.time()
        for key in keys:
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
            new_ema = (1.0 - self.REWARD_EMA_ALPHA) * old_ema + self.REWARD_EMA_ALPHA * value
            delta = self.LEARNING_RATE * (value - old_ema) - self.ACCESS_RENT
            new_capital = max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, old_capital + delta))
            self.db.db.execute(
                "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
                "VALUES(?,?,?,?,?) ON CONFLICT(entry_key) DO UPDATE SET "
                "capital=excluded.capital,reward_ema=excluded.reward_ema,"
                "pulls=excluded.pulls,updated_at=excluded.updated_at",
                (key, new_capital, new_ema, pulls + 1, now),
            )

        self.db.db.execute(
            "INSERT INTO retrieval_feedback(receipt_id,retrieval_id,causal_id,generation,"
            "credit,signal_class,ts) VALUES(?,?,?,?,?,?,?)",
            (rid, row["retrieval_id"], causal_id, int(generation), value, expected_signal, now),
        )
        return {
            "applied": True,
            "receipt_id": rid,
            "policy_version": self.POLICY_VERSION,
            "mode": row["mode"],
            "updated_entrypoints": len(keys),
            "truth_authority": False,
            "effect_authority": False,
        }
