from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .method_memory import MethodMemory, MethodRecordError
from .store import StaleGeneration, UnifiedDB


class StageBMethodRetrieval:
    """Causal Stage-B wrapper over admitted structural signatures only.

    A raw query may decide whether Stage B is relevant, but it never creates the
    structural serving key. The key must already exist as a `method_signature` record
    bound to the exact active turn. Durable USE receipts replay only on byte-equivalent
    normalized request identity and selection payload.
    """

    POLICY_VERSION = 3
    RECEIPT_SCHEMA = "clayverse-stage-b-method-use/v3"
    DEFAULT_LIMIT = 6
    DEFAULT_BUDGET_CHARS = 24_000
    MAX_BUDGET_CHARS = 64_000

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.methods = MethodMemory(db)

    @staticmethod
    def _canonical_json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise MethodRecordError("non-canonical Stage-B value") from exc

    @classmethod
    def _sha(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @staticmethod
    def _normalized_refs(resource_refs: list[str] | tuple[str, ...] | None) -> list[str]:
        if resource_refs is None:
            return []
        if not isinstance(resource_refs, (list, tuple)):
            raise MethodRecordError("resource_refs must be a bounded sequence")
        refs: list[str] = []
        for item in resource_refs:
            if not isinstance(item, str) or not item.strip() or len(item) > 2048:
                raise MethodRecordError("invalid resource_ref")
            refs.append(item.strip())
        if len(refs) > 128:
            raise MethodRecordError("too many resource_refs")
        return sorted(set(refs))

    def _assert_active(self, *, user_id: str, session_id: str, turn_id: str, episode_id: str,
                       causal_id: str, generation: int) -> None:
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        row = self.db.db.execute("SELECT * FROM active_turns WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            raise StaleGeneration("method_retrieval_no_active_turn")
        if (
            str(row["user_id"]) != user_id or str(row["turn_id"]) != turn_id or
            str(row["episode_id"]) != episode_id or str(row["causal_id"]) != causal_id or
            int(row["generation"]) != int(generation)
        ):
            raise StaleGeneration("method_retrieval_identity")

    @classmethod
    def _identity(cls, *, query: str, evidence_status: str, refs: list[str], limit: int,
                  budget_chars: int, signature: dict[str, Any], signature_memory_id: str,
                  user_id: str, session_id: str, turn_id: str, episode_id: str,
                  causal_id: str, generation: int) -> dict[str, Any]:
        return {
            "policy_version": cls.POLICY_VERSION,
            "query_sha256": hashlib.sha256(str(query).encode("utf-8")).hexdigest(),
            "evidence_status": evidence_status,
            "resource_refs_sha256": cls._sha(refs),
            "limit": int(limit),
            "budget_chars": int(budget_chars),
            "signature_memory_id": signature_memory_id,
            "signature_schema_version": int(signature["value"]["signature_schema_version"]),
            "signature_sha256": str(signature["value"]["signature_sha256"]),
            "signature_producer": str(signature["value"]["producer"]),
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
        }

    def _receipt_rows(self, causal_id: str):
        return self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts,memory_id",
            (f"USE:{causal_id}",),
        ).fetchall()

    def _decode_use_receipt(self, row) -> dict[str, Any]:
        try:
            payload = json.loads(row["value"])
            provenance = json.loads(row["provenance"])
        except Exception as exc:
            raise StaleGeneration("method_retrieval_receipt_malformed") from exc
        if not isinstance(payload, dict) or payload.get("schema") != self.RECEIPT_SCHEMA:
            raise StaleGeneration("method_retrieval_receipt_schema")
        if not isinstance(provenance, dict) or provenance.get("admission") != "method_stage_b:v3":
            raise StaleGeneration("method_retrieval_receipt_provenance")
        required = {"identity", "methods", "counterevidence", "selected_method_ids", "counterevidence_ids",
                    "selection_sha256", "status", "chars_selected", "factual_status_unchanged"}
        if not required.issubset(payload):
            raise StaleGeneration("method_retrieval_receipt_malformed")
        if not isinstance(payload["identity"], dict) or not isinstance(payload["methods"], list) or not isinstance(payload["counterevidence"], list):
            raise StaleGeneration("method_retrieval_receipt_malformed")
        selected = [item.get("memory_id") for item in payload["methods"] if isinstance(item, dict)]
        counters = [item.get("memory_id") for item in payload["counterevidence"] if isinstance(item, dict)]
        if selected != payload["selected_method_ids"] or counters != payload["counterevidence_ids"]:
            raise StaleGeneration("method_retrieval_selection_identity")
        if self._sha({"methods": payload["methods"], "counterevidence": payload["counterevidence"]}) != payload["selection_sha256"]:
            raise StaleGeneration("method_retrieval_selection_identity")
        return payload

    @staticmethod
    def _compact_receipt(payload: dict[str, Any], receipt_id: str, *, replayed: bool) -> dict[str, Any]:
        identity = payload["identity"]
        return {
            "receipt_id": receipt_id,
            "schema": StageBMethodRetrieval.RECEIPT_SCHEMA,
            "policy_version": StageBMethodRetrieval.POLICY_VERSION,
            "status": str(payload["status"]),
            "trigger": str(payload.get("trigger", "STRUCTURAL_SIGNATURE")),
            "causal_id": str(identity["causal_id"]),
            "generation": int(identity["generation"]),
            "signature_memory_id": str(identity["signature_memory_id"]),
            "signature_sha256": str(identity["signature_sha256"]),
            "request_identity_sha256": StageBMethodRetrieval._sha(identity),
            "selection_sha256": str(payload["selection_sha256"]),
            "selected_count": len(payload["selected_method_ids"]),
            "counterevidence_count": len(payload["counterevidence_ids"]),
            "chars_selected": int(payload["chars_selected"]),
            "factual_status_unchanged": str(payload["factual_status_unchanged"]),
            "truth_authority": False,
            "effect_authority": False,
            "replayed": bool(replayed),
        }

    @classmethod
    def _pack(cls, methods: list[dict[str, Any]], counterevidence: list[dict[str, Any]], *,
              budget_chars: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        packed_methods: list[dict[str, Any]] = []
        packed_counter: list[dict[str, Any]] = []
        used = 0
        # Counterevidence is packed first so a positive method cannot crowd out a known limiter.
        for target, items in ((packed_counter, counterevidence), (packed_methods, methods)):
            for item in items:
                encoded = cls._canonical_json(item)
                cost = len(encoded)
                if cost > budget_chars - used:
                    continue
                target.append(item)
                used += cost
        return packed_methods, packed_counter, used

    def retrieve(self, *, query: str, user_id: str, session_id: str, turn_id: str,
                 episode_id: str, causal_id: str, generation: int, evidence_status: str,
                 resource_refs: list[str] | tuple[str, ...] | None = None,
                 signature_memory_id: str | None = None,
                 problem_signature: dict[str, Any] | None = None,
                 limit: int = DEFAULT_LIMIT, budget_chars: int = DEFAULT_BUDGET_CHARS) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip() or len(query) > 100_000:
            raise MethodRecordError("invalid Stage-B query")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 24:
            raise MethodRecordError("invalid Stage-B limit")
        if not isinstance(budget_chars, int) or isinstance(budget_chars, bool) or not 256 <= budget_chars <= self.MAX_BUDGET_CHARS:
            raise MethodRecordError("invalid Stage-B budget")
        status = str(evidence_status).upper()
        if status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise MethodRecordError("invalid evidence status")
        refs = self._normalized_refs(resource_refs)
        self._assert_active(user_id=user_id, session_id=session_id, turn_id=turn_id,
                            episode_id=episode_id, causal_id=causal_id, generation=generation)

        # Raw structured dictionaries remain non-serving input. They are accepted only
        # to make the refusal explicit to old callers during migration.
        if signature_memory_id is None:
            return {
                "methods": [], "counterevidence": [],
                "receipt": {
                    "schema": self.RECEIPT_SCHEMA, "policy_version": self.POLICY_VERSION,
                    "status": "SIGNATURE_REQUIRED", "trigger": "NO_ADMITTED_SIGNATURE",
                    "causal_id": causal_id, "generation": int(generation),
                    "factual_status_unchanged": status, "truth_authority": False,
                    "effect_authority": False, "replayed": False,
                },
            }

        signature = self.methods.load_signature(
            signature_memory_id, user_id=user_id, session_id=session_id, turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation,
        )
        identity = self._identity(
            query=query, evidence_status=status, refs=refs, limit=limit, budget_chars=budget_chars,
            signature=signature, signature_memory_id=signature_memory_id, user_id=user_id,
            session_id=session_id, turn_id=turn_id, episode_id=episode_id,
            causal_id=causal_id, generation=generation,
        )

        existing = self._receipt_rows(causal_id)
        if len(existing) > 1:
            raise StaleGeneration("method_retrieval_duplicate_receipt")
        if existing:
            payload = self._decode_use_receipt(existing[0])
            if payload["identity"] != identity:
                raise StaleGeneration("method_retrieval_identity")
            return {
                "methods": payload["methods"], "counterevidence": payload["counterevidence"],
                "receipt": self._compact_receipt(payload, str(existing[0]["memory_id"]), replayed=True),
            }

        trigger = status in {"UNKNOWN", "UNDERCOVERED"} or self.methods.strategy_intent(query)
        if trigger:
            result = self.methods.retrieve(
                query=query, user_id=user_id, evidence_status=status, resource_refs=refs,
                problem_signature=signature["value"]["problem_signature"], limit=limit,
            )
            methods, counterevidence, chars_selected = self._pack(
                result["methods"], result["counterevidence"], budget_chars=budget_chars,
            )
        else:
            methods, counterevidence, chars_selected = [], [], 0

        selected_ids = [str(item["memory_id"]) for item in methods]
        counter_ids = [str(item["memory_id"]) for item in counterevidence]
        payload = {
            "schema": self.RECEIPT_SCHEMA,
            "identity": identity,
            "trigger": "STRUCTURAL_SIGNATURE" if trigger else "NOT_TRIGGERED",
            "status": "PRESENT" if methods else ("UNKNOWN" if trigger else "NOT_TRIGGERED"),
            "methods": methods,
            "counterevidence": counterevidence,
            "selected_method_ids": selected_ids,
            "counterevidence_ids": counter_ids,
            "selection_sha256": self._sha({"methods": methods, "counterevidence": counterevidence}),
            "chars_selected": int(chars_selected),
            "factual_status_unchanged": status,
            "truth_authority": False,
            "effect_authority": False,
            "ts": time.time(),
        }
        provenance = {
            "admission": "method_stage_b:v3", "policy_version": self.POLICY_VERSION,
            "causal_id": causal_id, "generation": int(generation), "user_scope": user_id,
            "truth_authority": False, "effect_authority": False,
        }
        with self.db.tx() as db:
            rows = db.execute(
                "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts,memory_id",
                (f"USE:{causal_id}",),
            ).fetchall()
            if rows:
                if len(rows) > 1:
                    raise StaleGeneration("method_retrieval_duplicate_receipt")
                stored = self._decode_use_receipt(rows[0])
                if stored["identity"] != identity:
                    raise StaleGeneration("method_retrieval_identity")
                return {"methods": stored["methods"], "counterevidence": stored["counterevidence"],
                        "receipt": self._compact_receipt(stored, str(rows[0]["memory_id"]), replayed=True)}
            receipt_id = self.db.add_memory(
                "method_receipt", f"USE:{causal_id}", self._canonical_json(payload), turn_id, user_id, provenance,
            )
        return {"methods": methods, "counterevidence": counterevidence,
                "receipt": self._compact_receipt(payload, receipt_id, replayed=False)}
