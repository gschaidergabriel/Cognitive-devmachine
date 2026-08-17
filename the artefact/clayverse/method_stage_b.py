from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .method_memory import MethodMemory, canonical_problem_signature
from .problem_signature import ProblemSignatureAdmission
from .store import StaleGeneration, UnifiedDB


class StageBMethodRetrieval:
    """Causal-identity wrapper around admitted structural method retrieval.

    Stage B never changes factual status and never gains truth/effect authority. A
    bounded method-use receipt is persisted by causal identity so re-entry cannot
    silently replay context produced for a drifted request.

    Raw prompt text and a caller-supplied problem_signature are not serving authority.
    The only serving signature is a persisted ProblemSignatureAdmission receipt bound
    to the active canonical user/session/turn/episode/causal/generation/resource identity.

    The active-turn identity check is relational, not merely referential: the active row,
    referenced session, turn and workspace episode must all agree on the same canonical
    user/session boundary before any method retrieval is allowed.
    """

    POLICY_VERSION = 3
    RECEIPT_SCHEMA = "clayverse-stage-b-method-use/v3"
    DEFAULT_BUDGET_CHARS = 6_000
    MAX_BUDGET_CHARS = 60_000
    MAX_RESOURCE_REFS = 128
    MAX_RESOURCE_REF_CHARS = 1024

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.methods = MethodMemory(db)
        self.problem_signatures = ProblemSignatureAdmission(db)

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def _canonical_resource_refs(cls, refs: list[str] | None) -> list[str]:
        raw = refs or []
        if not isinstance(raw, list) or len(raw) > cls.MAX_RESOURCE_REFS:
            raise ValueError("invalid Stage-B resource_refs")
        normalized: list[str] = []
        for ref in raw:
            if not isinstance(ref, str):
                raise ValueError("Stage-B resource_refs must be strings")
            item = ref.strip()
            if not item or len(item) > cls.MAX_RESOURCE_REF_CHARS:
                raise ValueError("invalid Stage-B resource_ref")
            normalized.append(item)
        return sorted(set(normalized))

    @classmethod
    def _digest_json(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @staticmethod
    def _receipt_memory_id(causal_id: str) -> str:
        digest = hashlib.sha256(str(causal_id).encode("utf-8")).hexdigest()
        return f"method-stage-b-receipt:{digest}"

    @classmethod
    def _bound_context(
        cls,
        methods: list[dict[str, Any]],
        counterevidence: list[dict[str, Any]],
        *,
        budget_chars: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        """Keep whole method records under one deterministic context budget.

        Counterevidence is packed first because losing a known limiting case is less safe
        than losing an optional positive analogy. Oversized records are skipped whole;
        method envelopes are never truncated into ambiguous partial semantics.
        """
        kept_counter: list[dict[str, Any]] = []
        kept_methods: list[dict[str, Any]] = []
        chars = 0
        for target, items in ((kept_counter, counterevidence), (kept_methods, methods)):
            for item in items:
                item_chars = len(cls._canonical_json(item))
                if chars + item_chars > budget_chars:
                    continue
                target.append(item)
                chars += item_chars
        return kept_methods, kept_counter, chars

    def _request_identity(
        self,
        *,
        query: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        evidence_status: str,
        resource_refs: list[str],
        problem_signature: dict[str, list[str]] | None,
        signature_admission: dict[str, Any] | None,
        limit: int,
        budget_chars: int,
    ) -> dict[str, Any]:
        admission = signature_admission or {}
        return {
            "receipt_schema": self.RECEIPT_SCHEMA,
            "policy_version": self.POLICY_VERSION,
            "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "evidence_status": evidence_status,
            "resource_refs_sha256": self._digest_json(resource_refs),
            "resource_ref_count": len(resource_refs),
            "problem_signature_sha256": (
                self._digest_json(problem_signature) if problem_signature is not None else None
            ),
            "signature_source": admission.get("signature_source", "NONE"),
            "signature_abstraction_version": admission.get("abstraction_version"),
            "signature_receipt_id": admission.get("memory_id"),
            "signature_identity_sha256": admission.get("signature_identity_sha256"),
            "signature_provenance_sha256": admission.get("signature_provenance_sha256"),
            "limit": int(limit),
            "budget_chars": int(budget_chars),
        }

    def _load_existing(
        self,
        *,
        memory_id: str,
        expected_identity: dict[str, Any],
        user_id: str,
        turn_id: str,
    ) -> dict[str, Any] | None:
        row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=?",
            (memory_id,),
        ).fetchone()
        if row is None:
            return None
        if str(row["kind"]) != "method_receipt":
            raise StaleGeneration("method_retrieval_identity")
        if str(row["user_id"]) != user_id or str(row["source_turn_id"]) != turn_id:
            raise StaleGeneration("method_retrieval_identity")
        try:
            payload = json.loads(str(row["value"]))
            provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise StaleGeneration("method_retrieval_receipt") from exc
        if not isinstance(payload, dict) or not isinstance(provenance, dict):
            raise StaleGeneration("method_retrieval_receipt")
        if provenance.get("source") != "method_stage_b:v3":
            raise StaleGeneration("method_retrieval_receipt")
        if payload.get("identity") != expected_identity:
            raise StaleGeneration("method_retrieval_identity")
        receipt = payload.get("receipt")
        methods = payload.get("methods")
        counterevidence = payload.get("counterevidence")
        problem_signature = payload.get("problem_signature")
        if not isinstance(receipt, dict) or not isinstance(methods, list) or not isinstance(counterevidence, list):
            raise StaleGeneration("method_retrieval_receipt")

        def bound_ids(items: list[Any]) -> list[str]:
            result: list[str] = []
            for item in items:
                if not isinstance(item, dict):
                    raise StaleGeneration("method_retrieval_receipt")
                memory_id_value = item.get("memory_id")
                if not isinstance(memory_id_value, str) or not memory_id_value:
                    raise StaleGeneration("method_retrieval_receipt")
                result.append(memory_id_value)
            return result

        selected_ids = bound_ids(methods)
        counter_ids = bound_ids(counterevidence)
        if receipt.get("selected_method_ids") != selected_ids:
            raise StaleGeneration("method_retrieval_receipt")
        if receipt.get("counterevidence_ids") != counter_ids:
            raise StaleGeneration("method_retrieval_receipt")
        if receipt.get("factual_status_unchanged") != expected_identity.get("evidence_status"):
            raise StaleGeneration("method_retrieval_receipt")
        if receipt.get("truth_authority") is not False or receipt.get("effect_authority") is not False:
            raise StaleGeneration("method_retrieval_receipt")
        for field in (
            "signature_source",
            "signature_abstraction_version",
            "signature_receipt_id",
            "signature_identity_sha256",
            "signature_provenance_sha256",
        ):
            if receipt.get(field) != expected_identity.get(field):
                raise StaleGeneration("method_retrieval_receipt")

        expected_chars = sum(len(self._canonical_json(item)) for item in counterevidence + methods)
        if receipt.get("chars_selected") != expected_chars:
            raise StaleGeneration("method_retrieval_receipt")
        if expected_chars > int(expected_identity["budget_chars"]):
            raise StaleGeneration("method_retrieval_receipt")

        replay_receipt = dict(receipt)
        replay_receipt["replayed"] = True
        return {
            "methods": methods,
            "counterevidence": counterevidence,
            "problem_signature": problem_signature,
            "receipt": replay_receipt,
        }

    def _persist_or_replay(
        self,
        *,
        memory_id: str,
        identity: dict[str, Any],
        receipt: dict[str, Any],
        methods: list[dict[str, Any]],
        counterevidence: list[dict[str, Any]],
        problem_signature: dict[str, list[str]] | None,
        user_id: str,
        turn_id: str,
        causal_id: str,
    ) -> dict[str, Any]:
        payload = {
            "identity": identity,
            "receipt": receipt,
            "methods": methods,
            "counterevidence": counterevidence,
            "problem_signature": problem_signature,
        }
        value = self._canonical_json(payload)
        provenance = self._canonical_json({
            "source": "method_stage_b:v3",
            "policy_version": self.POLICY_VERSION,
            "causal_id": causal_id,
            "user_scope": user_id,
            "truth_authority": False,
            "effect_authority": False,
        })

        def insert(db) -> bool:
            cursor = db.execute(
                "INSERT OR IGNORE INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    memory_id,
                    "method_receipt",
                    f"stage_b_method_use:{causal_id}",
                    value,
                    turn_id,
                    user_id,
                    time.time(),
                    provenance,
                ),
            )
            return int(cursor.rowcount or 0) == 1

        # Product turn admission already owns the canonical UnifiedDB transaction. Join
        # it instead of opening a nested BEGIN IMMEDIATE; standalone callers still get
        # one atomic transaction. This keeps receipt rollback coupled to turn rollback.
        if self.db.db.in_transaction:
            inserted = insert(self.db.db)
        else:
            with self.db.tx() as db:
                inserted = insert(db)

        if not inserted:
            replay = self._load_existing(
                memory_id=memory_id,
                expected_identity=identity,
                user_id=user_id,
                turn_id=turn_id,
            )
            if replay is None:
                raise StaleGeneration("method_retrieval_receipt")
            return replay
        return {
            "methods": methods,
            "counterevidence": counterevidence,
            "problem_signature": problem_signature,
            "receipt": receipt,
        }

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
        evidence_status: str,
        resource_refs: list[str] | None = None,
        problem_signature: dict[str, list[str]] | None = None,
        limit: int = 6,
        budget_chars: int = DEFAULT_BUDGET_CHARS,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Stage-B retrieval requires a non-empty query")
        if not 1 <= int(limit) <= 24:
            raise ValueError("invalid Stage-B limit")
        if not 256 <= int(budget_chars) <= self.MAX_BUDGET_CHARS:
            raise ValueError("invalid Stage-B budget_chars")

        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        active = self.db.db.execute(
            "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,a.user_id AS active_user_id,"
            "s.user_id AS session_user_id,t.session_id AS turn_session_id,t.user_id AS turn_user_id,"
            "w.session_id AS episode_session_id "
            "FROM active_turns a "
            "JOIN sessions s ON s.session_id=a.session_id "
            "JOIN turns t ON t.turn_id=a.turn_id "
            "JOIN workspace_episodes w ON w.episode_id=a.episode_id "
            "WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        if active is None:
            raise RuntimeError("Stage-B retrieval requires an active canonical turn")
        if (
            str(active["active_user_id"]) != str(user_id)
            or str(active["session_user_id"]) != str(user_id)
            or str(active["turn_session_id"]) != str(session_id)
            or str(active["turn_user_id"]) != str(user_id)
            or str(active["episode_session_id"]) != str(session_id)
            or str(active["turn_id"]) != str(turn_id)
            or str(active["episode_id"]) != str(episode_id)
            or str(active["causal_id"]) != str(causal_id)
            or int(active["generation"]) != int(generation)
        ):
            raise RuntimeError("Stage-B retrieval identity mismatch")

        factual_status = str(evidence_status).upper()
        if factual_status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise ValueError("invalid Stage-B evidence status")
        refs = self._canonical_resource_refs(resource_refs)

        admission = self.problem_signatures.load_active(session_id=session_id, user_id=user_id)
        if admission is None:
            signature = None
        else:
            if admission["resource_refs"] != refs:
                raise StaleGeneration("method_retrieval_identity")
            signature = canonical_problem_signature(admission["problem_signature"])
            if problem_signature is not None:
                caller_signature = canonical_problem_signature(problem_signature)
                if caller_signature != signature:
                    raise StaleGeneration("method_retrieval_identity")

        # A caller-supplied dict is at most a consistency assertion. It cannot become
        # serving authority without the persisted active-turn admission receipt above.
        identity = self._request_identity(
            query=query,
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
            evidence_status=factual_status,
            resource_refs=refs,
            problem_signature=signature,
            signature_admission=admission,
            limit=int(limit),
            budget_chars=int(budget_chars),
        )
        memory_id = self._receipt_memory_id(causal_id)

        existing = self._load_existing(
            memory_id=memory_id,
            expected_identity=identity,
            user_id=user_id,
            turn_id=turn_id,
        )
        if existing is not None:
            return existing

        if signature is None:
            receipt = {
                **identity,
                "triggered": False,
                "status": "SIGNATURE_REQUIRED",
                "selected_method_ids": [],
                "counterevidence_ids": [],
                "chars_selected": 0,
                "factual_status_unchanged": factual_status,
                "truth_authority": False,
                "effect_authority": False,
                "replayed": False,
            }
            return self._persist_or_replay(
                memory_id=memory_id,
                identity=identity,
                receipt=receipt,
                methods=[],
                counterevidence=[],
                problem_signature=None,
                user_id=user_id,
                turn_id=turn_id,
                causal_id=causal_id,
            )

        result = self.methods.retrieve(
            query=query,
            user_id=user_id,
            evidence_status=factual_status,
            resource_refs=refs,
            problem_signature=signature,
            limit=int(limit),
        )
        methods, counterevidence, chars_selected = self._bound_context(
            list(result["methods"]),
            list(result["counterevidence"]),
            budget_chars=int(budget_chars),
        )
        selected_method_ids = [str(item["memory_id"]) for item in methods]
        counterevidence_ids = [str(item["memory_id"]) for item in counterevidence]
        receipt = {
            **identity,
            "triggered": bool(result["triggered"]),
            "status": "METHOD_PRESENT" if selected_method_ids else "METHOD_UNKNOWN",
            "selected_method_ids": selected_method_ids,
            "counterevidence_ids": counterevidence_ids,
            "chars_selected": chars_selected,
            "factual_status_unchanged": str(result["factual_status_unchanged"]),
            "truth_authority": False,
            "effect_authority": False,
            "replayed": False,
        }
        return self._persist_or_replay(
            memory_id=memory_id,
            identity=identity,
            receipt=receipt,
            methods=methods,
            counterevidence=counterevidence,
            problem_signature=result["problem_signature"],
            user_id=user_id,
            turn_id=turn_id,
            causal_id=causal_id,
        )
