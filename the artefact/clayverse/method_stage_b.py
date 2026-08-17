from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .method_memory import MethodMemory, MethodRecordError
from .method_signature import MethodSignatureAuthority
from .store import StaleGeneration, UnifiedDB


class StageBMethodRetrieval:
    """Causal Stage-B retrieval from an admitted structural-signature receipt only."""

    POLICY_VERSION = 3
    RECEIPT_SCHEMA = "clayverse-stage-b-method-use/v3"
    DEFAULT_BUDGET_CHARS = 6_000
    MAX_BUDGET_CHARS = 60_000
    MAX_RESOURCE_REFS = 128
    MAX_RESOURCE_REF_CHARS = 1024

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.methods = MethodMemory(db)
        self.signatures = MethodSignatureAuthority(db)

    @staticmethod
    def _canonical_json(value: Any) -> str:
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise MethodRecordError("non-canonical Stage-B value") from exc

    @classmethod
    def _digest_json(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @staticmethod
    def _receipt_memory_id(causal_id: str) -> str:
        return "method-stage-b-receipt:" + hashlib.sha256(str(causal_id).encode("utf-8")).hexdigest()

    @classmethod
    def _canonical_resource_refs(cls, refs: list[str] | None) -> list[str]:
        raw = refs or []
        if not isinstance(raw, list) or len(raw) > cls.MAX_RESOURCE_REFS:
            raise MethodRecordError("invalid Stage-B resource_refs")
        result: list[str] = []
        for ref in raw:
            if not isinstance(ref, str):
                raise MethodRecordError("Stage-B resource_refs must be strings")
            value = ref.strip()
            if not value or len(value) > cls.MAX_RESOURCE_REF_CHARS:
                raise MethodRecordError("invalid Stage-B resource_ref")
            result.append(value)
        return sorted(set(result))

    @classmethod
    def _bound_context(cls, methods: list[dict[str, Any]], counterevidence: list[dict[str, Any]], *,
                       budget_chars: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        kept_counter: list[dict[str, Any]] = []
        kept_methods: list[dict[str, Any]] = []
        chars = 0
        for target, items in ((kept_counter, counterevidence), (kept_methods, methods)):
            for item in items:
                cost = len(cls._canonical_json(item))
                if cost > budget_chars - chars:
                    continue
                target.append(item)
                chars += cost
        return kept_methods, kept_counter, chars

    def _request_identity(self, *, query: str, user_id: str, session_id: str, turn_id: str,
                          episode_id: str, causal_id: str, generation: int, evidence_status: str,
                          resource_refs: list[str], signature: dict[str, Any], limit: int,
                          budget_chars: int) -> dict[str, Any]:
        payload = signature["payload"]
        return {
            "receipt_schema": self.RECEIPT_SCHEMA,
            "policy_version": self.POLICY_VERSION,
            "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "user_id": user_id, "session_id": session_id, "turn_id": turn_id,
            "episode_id": episode_id, "causal_id": causal_id, "generation": int(generation),
            "evidence_status": evidence_status,
            "resource_refs_sha256": self._digest_json(resource_refs),
            "resource_ref_count": len(resource_refs),
            "signature_receipt_id": signature["memory_id"],
            "signature_schema": payload["schema"],
            "signature_policy_version": int(payload["policy_version"]),
            "signature_sha256": payload["signature_sha256"],
            "signature_producer": payload["producer"],
            "limit": int(limit), "budget_chars": int(budget_chars),
        }

    def _load_existing(self, *, memory_id: str, expected_identity: dict[str, Any], user_id: str,
                       turn_id: str) -> dict[str, Any] | None:
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        if row is None:
            return None
        if str(row["kind"]) != "method_receipt" or str(row["user_id"]) != user_id or str(row["source_turn_id"]) != turn_id:
            raise StaleGeneration("method_retrieval_identity")
        try:
            payload = json.loads(str(row["value"])); provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise StaleGeneration("method_retrieval_receipt") from exc
        if not isinstance(payload, dict) or not isinstance(provenance, dict) or payload.get("schema") != self.RECEIPT_SCHEMA:
            raise StaleGeneration("method_retrieval_receipt")
        if provenance.get("source") != "method_stage_b:v3" or payload.get("identity") != expected_identity:
            raise StaleGeneration("method_retrieval_identity")
        methods, counterevidence = payload.get("methods"), payload.get("counterevidence")
        if not isinstance(methods, list) or not isinstance(counterevidence, list):
            raise StaleGeneration("method_retrieval_receipt")
        selected = [item.get("memory_id") for item in methods if isinstance(item, dict)]
        counters = [item.get("memory_id") for item in counterevidence if isinstance(item, dict)]
        if selected != payload.get("selected_method_ids") or counters != payload.get("counterevidence_ids"):
            raise StaleGeneration("method_retrieval_selection_identity")
        selection_sha = self._digest_json({"methods": methods, "counterevidence": counterevidence})
        if payload.get("selection_sha256") != selection_sha:
            raise StaleGeneration("method_retrieval_selection_identity")
        expected_chars = sum(len(self._canonical_json(item)) for item in counterevidence + methods)
        if payload.get("chars_selected") != expected_chars or expected_chars > int(expected_identity["budget_chars"]):
            raise StaleGeneration("method_retrieval_receipt")
        if payload.get("factual_status_unchanged") != expected_identity["evidence_status"]:
            raise StaleGeneration("method_retrieval_receipt")
        if payload.get("truth_authority") is not False or payload.get("effect_authority") is not False:
            raise StaleGeneration("method_retrieval_receipt")
        receipt = self._compact_receipt(payload, memory_id, replayed=True)
        return {"methods": methods, "counterevidence": counterevidence,
                "problem_signature": payload.get("problem_signature"), "receipt": receipt}

    @classmethod
    def _compact_receipt(cls, payload: dict[str, Any], memory_id: str, *, replayed: bool) -> dict[str, Any]:
        identity = payload["identity"]
        return {
            "receipt_id": memory_id, "schema": cls.RECEIPT_SCHEMA, "policy_version": cls.POLICY_VERSION,
            "status": str(payload["status"]), "triggered": bool(payload["triggered"]),
            "causal_id": identity["causal_id"], "generation": int(identity["generation"]),
            "signature_receipt_id": identity["signature_receipt_id"],
            "signature_sha256": identity["signature_sha256"],
            "request_identity_sha256": cls._digest_json(identity),
            "selection_sha256": payload["selection_sha256"],
            "selected_count": len(payload["selected_method_ids"]),
            "counterevidence_count": len(payload["counterevidence_ids"]),
            "chars_selected": int(payload["chars_selected"]),
            "factual_status_unchanged": payload["factual_status_unchanged"],
            "truth_authority": False, "effect_authority": False, "replayed": bool(replayed),
        }

    def _persist_or_replay(self, *, memory_id: str, payload: dict[str, Any], identity: dict[str, Any],
                           user_id: str, turn_id: str, causal_id: str) -> dict[str, Any]:
        value = self._canonical_json(payload)
        provenance = self._canonical_json({
            "source": "method_stage_b:v3", "policy_version": self.POLICY_VERSION,
            "causal_id": causal_id, "user_scope": user_id,
            "truth_authority": False, "effect_authority": False,
        })

        def insert(db) -> bool:
            cursor = db.execute(
                "INSERT OR IGNORE INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) VALUES(?,?,?,?,?,?,?,?)",
                (memory_id, "method_receipt", f"stage_b_method_use:{causal_id}", value,
                 turn_id, user_id, time.time(), provenance),
            )
            return int(cursor.rowcount or 0) == 1

        if self.db.db.in_transaction:
            inserted = insert(self.db.db)
        else:
            with self.db.tx() as db:
                inserted = insert(db)
        if not inserted:
            replay = self._load_existing(memory_id=memory_id, expected_identity=identity,
                                         user_id=user_id, turn_id=turn_id)
            if replay is None:
                raise StaleGeneration("method_retrieval_receipt")
            return replay
        return {"methods": payload["methods"], "counterevidence": payload["counterevidence"],
                "problem_signature": payload["problem_signature"],
                "receipt": self._compact_receipt(payload, memory_id, replayed=False)}

    def retrieve(self, *, query: str, user_id: str, session_id: str, turn_id: str, episode_id: str,
                 causal_id: str, generation: int, evidence_status: str,
                 resource_refs: list[str] | None = None,
                 signature_receipt_id: str | None = None,
                 problem_signature: dict[str, list[str]] | None = None,
                 limit: int = 6, budget_chars: int = DEFAULT_BUDGET_CHARS) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise MethodRecordError("Stage-B retrieval requires a non-empty query")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 24:
            raise MethodRecordError("invalid Stage-B limit")
        if not isinstance(budget_chars, int) or isinstance(budget_chars, bool) or not 256 <= budget_chars <= self.MAX_BUDGET_CHARS:
            raise MethodRecordError("invalid Stage-B budget_chars")
        factual_status = str(evidence_status).upper()
        if factual_status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise MethodRecordError("invalid Stage-B evidence status")
        refs = self._canonical_resource_refs(resource_refs)

        # Old callers may still pass a raw structured dict. It is intentionally not a
        # serving authority and does not consume the causal USE receipt identity.
        if signature_receipt_id is None:
            return {
                "methods": [], "counterevidence": [], "problem_signature": None,
                "receipt": {
                    "schema": self.RECEIPT_SCHEMA, "policy_version": self.POLICY_VERSION,
                    "status": "SIGNATURE_REQUIRED", "triggered": False,
                    "causal_id": causal_id, "generation": int(generation),
                    "factual_status_unchanged": factual_status,
                    "truth_authority": False, "effect_authority": False, "replayed": False,
                },
            }

        signature = self.signatures.load(
            memory_id=signature_receipt_id, user_id=user_id, session_id=session_id,
            turn_id=turn_id, episode_id=episode_id, causal_id=causal_id, generation=generation,
        )
        identity = self._request_identity(
            query=query, user_id=user_id, session_id=session_id, turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation,
            evidence_status=factual_status, resource_refs=refs, signature=signature,
            limit=limit, budget_chars=budget_chars,
        )
        memory_id = self._receipt_memory_id(causal_id)

        # Identity is checked before a drifted trigger can return NOT_TRIGGERED.
        existing = self._load_existing(memory_id=memory_id, expected_identity=identity,
                                       user_id=user_id, turn_id=turn_id)
        if existing is not None:
            return existing

        trigger = factual_status in {"UNKNOWN", "UNDERCOVERED"} or self.methods.strategy_intent(query)
        if trigger:
            result = self.methods.retrieve(
                query=query, user_id=user_id, evidence_status=factual_status,
                resource_refs=refs, problem_signature=signature["payload"]["problem_signature"],
                limit=limit,
            )
            methods, counterevidence, chars_selected = self._bound_context(
                list(result["methods"]), list(result["counterevidence"]), budget_chars=budget_chars,
            )
        else:
            methods, counterevidence, chars_selected = [], [], 0
        selected_ids = [str(item["memory_id"]) for item in methods]
        counter_ids = [str(item["memory_id"]) for item in counterevidence]
        payload = {
            "schema": self.RECEIPT_SCHEMA, "identity": identity,
            "triggered": bool(trigger),
            "status": "METHOD_PRESENT" if selected_ids else ("METHOD_UNKNOWN" if trigger else "NOT_TRIGGERED"),
            "methods": methods, "counterevidence": counterevidence,
            "problem_signature": signature["payload"]["problem_signature"],
            "selected_method_ids": selected_ids, "counterevidence_ids": counter_ids,
            "selection_sha256": self._digest_json({"methods": methods, "counterevidence": counterevidence}),
            "chars_selected": int(chars_selected), "factual_status_unchanged": factual_status,
            "truth_authority": False, "effect_authority": False,
        }
        return self._persist_or_replay(memory_id=memory_id, payload=payload, identity=identity,
                                       user_id=user_id, turn_id=turn_id, causal_id=causal_id)
