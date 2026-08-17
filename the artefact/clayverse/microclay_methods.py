from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .store import UnifiedDB

_TOKEN = re.compile(r"[\w.-]{2,}", re.UNICODE)

METHOD_ACTIVE_KINDS = frozenset({
    "framework", "heuristic", "failure_pattern", "counterexample"
})
METHOD_CANDIDATE_KINDS = frozenset({
    "framework_candidate", "heuristic_candidate"
})
METHOD_CONTROL_KINDS = frozenset({"method_receipt"})
METHOD_KINDS = METHOD_ACTIVE_KINDS | METHOD_CANDIDATE_KINDS | METHOD_CONTROL_KINDS


class MicroClayMethodRetrieval:
    """Deterministic Stage-B method retrieval with no factual/effect authority.

    This is intentionally separate from Stage-A evidence retrieval. It may expose only
    explicitly PROMOTED structured method records. Candidate/control records never
    serve. The current signature-token matcher is a conservative first structural
    discriminator; held-out lexically-dissimilar transfer remains an acceptance gate.
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
            return value if isinstance(value, dict) else {"raw_type": type(value).__name__}
        except Exception:
            return {"parse_error": True}

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
            raise ValueError(
                f"malformed method memory {row['memory_id']}: record must be an object"
            )
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
        self.db.assert_live_generation(session_id, generation)

        active = tuple(sorted(METHOD_ACTIVE_KINDS))
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
            precision = overlap / max(1, len(signature_tokens))
            signature_match = min(1.0, 0.70 * coverage + 0.30 * precision)
            surface_tokens = self._tokens(str(row["subject"]) + " " + str(row["value"]))
            surface_overlap = len(qtokens.intersection(surface_tokens)) / max(1, len(qtokens))
            score = 0.90 * signature_match + 0.10 * surface_overlap
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
                "matcher": "signature_token_v1",
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
            },
        }
