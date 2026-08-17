from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from .store import UnifiedDB

_TOKEN = re.compile(r"[\w.-]{2,}", re.UNICODE)

METHOD_SCHEMA = "clayverse.method/v1"
PROMOTION_RECEIPT_SCHEMA = "clayverse.method-promotion-receipt/v1"
METHOD_ACTIVE_KINDS = frozenset({
    "framework", "heuristic", "failure_pattern", "counterexample"
})
METHOD_CANDIDATE_KINDS = frozenset({
    "framework_candidate", "heuristic_candidate"
})
METHOD_CONTROL_KINDS = frozenset({"method_receipt"})
METHOD_KINDS = METHOD_ACTIVE_KINDS | METHOD_CANDIDATE_KINDS | METHOD_CONTROL_KINDS

_METHOD_FIELDS = frozenset({
    "schema",
    "problem_signature",
    "preconditions",
    "goal_shape",
    "method_steps",
    "invariants",
    "expected_observations",
    "falsifiers",
    "failure_modes",
    "scope_limits",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
    "abstraction_version",
    "support_count",
    "success_count",
    "failure_count",
    "calibration",
    "last_validated_at",
    "status",
})
_PROMOTION_RECEIPT_FIELDS = frozenset({
    "schema",
    "action",
    "method_memory_id",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
    "ts",
})


class MicroClayMethodRetrieval:
    """Deterministic Stage-B method retrieval with no factual/effect authority.

    Stage B is separate from Stage-A evidence retrieval. This reader admits only a
    user-bound, fully shaped PROMOTED record whose promotion receipt exists and whose
    source episodes are terminal, causally re-entered episodes for the same user.

    Important: promotion itself is intentionally NOT implemented here. A lone
    `status=PROMOTED` flag is not admission authority. The current query-to-signature
    matcher remains token based and therefore remains a SHADOW/source-candidate
    mechanism until held-out structural transfer gates are satisfied.
    """

    MAX_SOURCE_ROWS = 5000
    MAX_QUERY_TOKENS = 64

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.lower() for x in _TOKEN.findall(text or "")[:256]}

    @staticmethod
    def _safe_provenance(raw: str) -> dict[str, Any]:
        try:
            value = json.loads(raw)
        except Exception as exc:
            raise ValueError("malformed method provenance") from exc
        if not isinstance(value, dict):
            raise ValueError("method provenance must be an object")
        return value

    @staticmethod
    def _string(value: Any, *, field: str, max_chars: int = 4096) -> str:
        if not isinstance(value, str):
            raise ValueError(f"malformed method record field: {field}")
        normalized = " ".join(value.strip().split())
        if not normalized or len(normalized) > max_chars:
            raise ValueError(f"invalid method record field: {field}")
        return normalized

    @classmethod
    def _string_list(
        cls,
        value: Any,
        *,
        field: str,
        min_items: int = 0,
        max_items: int = 256,
    ) -> list[str]:
        if not isinstance(value, list) or not min_items <= len(value) <= max_items:
            raise ValueError(f"malformed method record field: {field}")
        items = [cls._string(item, field=field, max_chars=1024) for item in value]
        if len(set(items)) != len(items):
            raise ValueError(f"duplicate method record values: {field}")
        return items

    @staticmethod
    def _count(value: Any, *, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid method record count: {field}")
        return value

    @staticmethod
    def _finite_float(value: Any, *, field: str, low: float | None = None, high: float | None = None) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"invalid method record number: {field}")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"non-finite method record number: {field}")
        if low is not None and number < low:
            raise ValueError(f"method record number below bound: {field}")
        if high is not None and number > high:
            raise ValueError(f"method record number above bound: {field}")
        return number

    def _method_record(self, row, *, user_id: str) -> dict[str, Any]:
        try:
            record = json.loads(str(row["value"]))
        except Exception as exc:
            raise ValueError(
                f"malformed method memory {row['memory_id']}: value is not JSON"
            ) from exc
        if not isinstance(record, dict):
            raise ValueError(
                f"malformed method memory {row['memory_id']}: record must be an object"
            )
        if set(record) != _METHOD_FIELDS:
            missing = sorted(_METHOD_FIELDS - set(record))
            extra = sorted(set(record) - _METHOD_FIELDS)
            raise ValueError(
                f"malformed method memory {row['memory_id']}: fields mismatch "
                f"missing={missing} extra={extra}"
            )
        if record["schema"] != METHOD_SCHEMA:
            raise ValueError(f"method memory {row['memory_id']} has unsupported schema")
        if self._string(record["status"], field="status", max_chars=32).upper() != "PROMOTED":
            raise ValueError(f"method memory {row['memory_id']} is not PROMOTED")

        normalized = dict(record)
        normalized["problem_signature"] = self._string_list(
            record["problem_signature"], field="problem_signature", min_items=1, max_items=64
        )
        normalized["preconditions"] = self._string_list(
            record["preconditions"], field="preconditions", min_items=1, max_items=64
        )
        normalized["goal_shape"] = self._string(
            record["goal_shape"], field="goal_shape", max_chars=1024
        )
        normalized["method_steps"] = self._string_list(
            record["method_steps"], field="method_steps", min_items=1, max_items=128
        )
        normalized["invariants"] = self._string_list(
            record["invariants"], field="invariants", min_items=1, max_items=64
        )
        normalized["expected_observations"] = self._string_list(
            record["expected_observations"], field="expected_observations", min_items=1, max_items=64
        )
        normalized["falsifiers"] = self._string_list(
            record["falsifiers"], field="falsifiers", min_items=1, max_items=64
        )
        normalized["failure_modes"] = self._string_list(
            record["failure_modes"], field="failure_modes", min_items=1, max_items=64
        )
        normalized["scope_limits"] = self._string_list(
            record["scope_limits"], field="scope_limits", min_items=1, max_items=64
        )
        normalized["source_episode_ids"] = self._string_list(
            record["source_episode_ids"], field="source_episode_ids", min_items=2, max_items=128
        )
        normalized["supporting_memory_ids"] = self._string_list(
            record["supporting_memory_ids"], field="supporting_memory_ids", max_items=256
        )
        normalized["counterexample_memory_ids"] = self._string_list(
            record["counterexample_memory_ids"], field="counterexample_memory_ids", max_items=256
        )

        abstraction_version = self._count(record["abstraction_version"], field="abstraction_version")
        if abstraction_version < 1:
            raise ValueError("abstraction_version must be >= 1")
        support_count = self._count(record["support_count"], field="support_count")
        success_count = self._count(record["success_count"], field="success_count")
        failure_count = self._count(record["failure_count"], field="failure_count")
        if support_count < 2 or support_count < len(normalized["source_episode_ids"]):
            raise ValueError("promoted method lacks multi-episode support")
        if success_count + failure_count > support_count:
            raise ValueError("method success/failure counts exceed support_count")
        if success_count < 1:
            raise ValueError("promoted method lacks a successful validation episode")
        normalized["abstraction_version"] = abstraction_version
        normalized["support_count"] = support_count
        normalized["success_count"] = success_count
        normalized["failure_count"] = failure_count
        normalized["calibration"] = self._finite_float(
            record["calibration"], field="calibration", low=0.0, high=1.0
        )
        normalized["last_validated_at"] = self._finite_float(
            record["last_validated_at"], field="last_validated_at", low=0.0
        )
        normalized["status"] = "PROMOTED"

        # A method is never admitted merely because its record says PROMOTED.
        provenance = self._safe_provenance(row["provenance"])
        if provenance.get("method_schema") != METHOD_SCHEMA:
            raise ValueError(f"method memory {row['memory_id']} lacks admitted method schema provenance")
        receipt_id = provenance.get("promotion_receipt_id")
        if not isinstance(receipt_id, str) or not receipt_id.strip():
            raise ValueError(f"method memory {row['memory_id']} lacks promotion receipt provenance")

        self._assert_source_episodes(
            normalized["source_episode_ids"], user_id=user_id
        )
        self._assert_referenced_memories(normalized, user_id=user_id)
        self._assert_promotion_receipt(
            row=row,
            record=normalized,
            receipt_id=receipt_id,
            user_id=user_id,
        )
        return normalized

    def _assert_source_episodes(self, episode_ids: list[str], *, user_id: str) -> None:
        placeholders = ",".join("?" for _ in episode_ids)
        rows = self.db.db.execute(
            f"SELECT w.episode_id,w.state,s.user_id,"
            "EXISTS(SELECT 1 FROM causal_episodes c "
            "WHERE c.episode_id=w.episode_id AND c.reentered=1) AS reentered "
            "FROM workspace_episodes w JOIN sessions s ON s.session_id=w.session_id "
            f"WHERE w.episode_id IN ({placeholders})",
            tuple(episode_ids),
        ).fetchall()
        found = {str(row["episode_id"]): row for row in rows}
        missing = sorted(set(episode_ids) - set(found))
        if missing:
            raise ValueError(f"method source episodes missing: {missing}")
        for episode_id, row in found.items():
            if str(row["user_id"]) != user_id:
                raise ValueError(f"method source episode crosses user boundary: {episode_id}")
            if str(row["state"]) not in {"COMPLETED", "ABORTED"} or not int(row["reentered"]):
                raise ValueError(f"method source episode is not terminal and causally re-entered: {episode_id}")

    def _assert_referenced_memories(self, record: dict[str, Any], *, user_id: str) -> None:
        memory_ids = list(dict.fromkeys(
            record["supporting_memory_ids"] + record["counterexample_memory_ids"]
        ))
        if not memory_ids:
            return
        placeholders = ",".join("?" for _ in memory_ids)
        rows = self.db.db.execute(
            f"SELECT memory_id,kind,user_id FROM durable_memory WHERE memory_id IN ({placeholders})",
            tuple(memory_ids),
        ).fetchall()
        found = {str(row["memory_id"]): row for row in rows}
        missing = sorted(set(memory_ids) - set(found))
        if missing:
            raise ValueError(f"method referenced memories missing: {missing}")
        for memory_id, row in found.items():
            if str(row["user_id"]) != user_id:
                raise ValueError(f"method referenced memory crosses user boundary: {memory_id}")
        for memory_id in record["counterexample_memory_ids"]:
            if str(found[memory_id]["kind"]) not in {"counterexample", "failure_pattern"}:
                raise ValueError(f"method counterexample reference has wrong kind: {memory_id}")

    def _assert_promotion_receipt(
        self,
        *,
        row,
        record: dict[str, Any],
        receipt_id: str,
        user_id: str,
    ) -> None:
        receipt_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt' AND user_id=? LIMIT 1",
            (receipt_id, user_id),
        ).fetchone()
        if receipt_row is None:
            raise ValueError(f"method memory {row['memory_id']} promotion receipt is missing")
        try:
            receipt = json.loads(str(receipt_row["value"]))
        except Exception as exc:
            raise ValueError("malformed method promotion receipt") from exc
        if not isinstance(receipt, dict) or set(receipt) != _PROMOTION_RECEIPT_FIELDS:
            raise ValueError("malformed method promotion receipt fields")
        if receipt["schema"] != PROMOTION_RECEIPT_SCHEMA or receipt["action"] != "PROMOTE":
            raise ValueError("invalid method promotion receipt contract")
        if receipt["method_memory_id"] != str(row["memory_id"]):
            raise ValueError("method promotion receipt targets another method")
        if self._string_list(
            receipt["source_episode_ids"], field="promotion_receipt.source_episode_ids", min_items=2, max_items=128
        ) != record["source_episode_ids"]:
            raise ValueError("method promotion receipt source episode identity mismatch")
        if self._string_list(
            receipt["supporting_memory_ids"], field="promotion_receipt.supporting_memory_ids", max_items=256
        ) != record["supporting_memory_ids"]:
            raise ValueError("method promotion receipt supporting-memory identity mismatch")
        if self._string_list(
            receipt["counterexample_memory_ids"], field="promotion_receipt.counterexample_memory_ids", max_items=256
        ) != record["counterexample_memory_ids"]:
            raise ValueError("method promotion receipt counterexample identity mismatch")
        self._finite_float(receipt["ts"], field="promotion_receipt.ts", low=0.0)

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
        limit: int = 8,
        budget_chars: int = 6_000,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("method retrieval requires a non-empty query")
        if limit < 1 or limit > 32:
            raise ValueError("invalid method retrieval limit")
        if budget_chars < 256 or budget_chars > 100_000:
            raise ValueError("invalid method retrieval budget")
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)

        active = tuple(sorted(METHOD_ACTIVE_KINDS))
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            f"WHERE kind IN ({','.join('?' for _ in active)}) "
            "AND user_id=? "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (*active, user_id, turn_id, self.MAX_SOURCE_ROWS),
        ).fetchall()
        qtokens = set(sorted(self._tokens(query))[: self.MAX_QUERY_TOKENS])
        ranked: list[tuple[float, float, str, dict[str, Any]]] = []
        for row in rows:
            record = self._method_record(row, user_id=user_id)
            signature_tokens = self._tokens(" ".join(record["problem_signature"]))
            overlap = len(qtokens.intersection(signature_tokens))
            if overlap <= 0:
                continue
            coverage = overlap / max(1, len(qtokens))
            precision = overlap / max(1, len(signature_tokens))
            score = min(1.0, 0.70 * coverage + 0.30 * precision)
            public = {
                "memory_id": str(row["memory_id"]),
                "kind": str(row["kind"]),
                "subject": str(row["subject"]),
                "method_record": record,
                "structural_match": score,
                "provenance": self._safe_provenance(row["provenance"]),
                "truth_authority": False,
                "effect_authority": False,
            }
            ranked.append((score, float(row["ts"]), str(row["memory_id"]), public))

        ranked.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        selected: list[dict[str, Any]] = []
        chars = 0
        for _, _, _, item in ranked:
            item_chars = len(
                json.dumps(item["method_record"], sort_keys=True, separators=(",", ":"))
            )
            if chars + item_chars > budget_chars:
                continue
            selected.append(item)
            chars += item_chars
            if len(selected) >= limit:
                break

        selected_ids = [item["memory_id"] for item in selected]
        return {
            "items": selected,
            "receipt": {
                "route": "method",
                "matcher": "signature_token_v2_strict_promoted",
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "session_id": session_id,
                "turn_id": turn_id,
                "episode_id": episode_id,
                "causal_id": causal_id,
                "generation": int(generation),
                "selected_memory_ids_sha256": hashlib.sha256(
                    json.dumps(selected_ids, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                "candidate_count": len(ranked),
                "selected_count": len(selected),
                "limit_requested": int(limit),
                "budget_chars": int(budget_chars),
                "chars_selected": chars,
                "status": "METHOD_PRESENT" if selected else "METHOD_UNKNOWN",
                "truth_authority": False,
                "effect_authority": False,
                "adaptive": False,
                "persisted": False,
                "promotion_verified": bool(selected),
            },
        }
