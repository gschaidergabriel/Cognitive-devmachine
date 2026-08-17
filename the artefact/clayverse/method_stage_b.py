from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .method_memory import (
    ACTIVE_METHOD_KINDS,
    COUNTER_METHOD_KINDS,
    METHOD_RECEIPT_SCHEMA,
    MethodRecord,
    MethodRecordError,
    canonical_problem_signature,
    structural_similarity,
)
from .store import UnifiedDB

STAGE_B_TRIGGERS = frozenset({"UNKNOWN", "UNDERCOVERED", "OOD", "CONFLICT", "STRATEGY"})


class StageBShadowRetrieval:
    """Non-serving structural method transfer with durable causal replay identity.

    V1 accepts only a persisted ProblemSignatureAdmission receipt. It has no free-text
    structural parser and never injects method output into Claude context. Selected
    methods are recorded in SHADOW for held-out transfer/calibration evidence only.
    """

    POLICY_VERSION = 1
    MIN_STRUCTURAL_SCORE = 0.50
    COUNTEREXAMPLE_BLOCK_SCORE = 0.75
    MAX_SCAN = 2000

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.methods = db.method_manager()
        self.signatures = db.problem_signature_admission()

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @staticmethod
    def _public(record: MethodRecord, score: float) -> dict[str, Any]:
        result = record.public(score=score)
        result["served"] = False
        return result

    @staticmethod
    def _refs(resource_refs: list[str] | None) -> list[str]:
        if resource_refs is None:
            return []
        if not isinstance(resource_refs, list) or len(resource_refs) > 50:
            raise MethodRecordError("Stage-B resource refs invalid")
        refs = []
        for ref in resource_refs:
            if not isinstance(ref, str) or not ref.strip() or len(ref) > 1000:
                raise MethodRecordError("Stage-B resource ref invalid")
            refs.append(ref.strip())
        return sorted(set(refs))

    def _assert_active_identity(
        self,
        *,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
    ) -> None:
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        row = self.db.db.execute(
            "SELECT user_id,turn_id,episode_id,causal_id,generation FROM active_turns WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise MethodRecordError("Stage-B requires active canonical turn")
        expected = (user_id, turn_id, episode_id, causal_id, int(generation))
        observed = (
            str(row["user_id"]),
            str(row["turn_id"]),
            str(row["episode_id"]),
            str(row["causal_id"]),
            int(row["generation"]),
        )
        if observed != expected:
            raise MethodRecordError("Stage-B causal identity mismatch")

    def _active_records(self, user_id: str) -> list[MethodRecord]:
        kinds = tuple(sorted(ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS))
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN (%s) AND user_id=? ORDER BY ts DESC LIMIT ?"
            % ",".join("?" for _ in kinds),
            (*kinds, user_id, self.MAX_SCAN),
        ).fetchall()
        records: list[MethodRecord] = []
        for row in rows:
            record = self.methods.decode_row(row)
            self.methods._assert_references(record, user_id)
            if record.status == "PROMOTED":
                records.append(record)
        return records

    def _decode_selected(
        self,
        ids: list[str],
        user_id: str,
        signature: dict[str, tuple[str, ...]],
        allowed_kinds: frozenset[str],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for memory_id in ids:
            row = self.methods.row_by_id(memory_id, user_id)
            record = self.methods.decode_row(row)
            self.methods._assert_references(record, user_id)
            if record.kind not in allowed_kinds or record.status != "PROMOTED":
                raise MethodRecordError("replayed method kind/status diverged")
            score = structural_similarity(signature, record.problem_signature)
            if score < self.MIN_STRUCTURAL_SCORE:
                raise MethodRecordError("replayed method no longer matches admitted signature")
            items.append(self._public(record, score))
        return items

    def retrieve_shadow(
        self,
        *,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        evidence_status: str,
        signature_receipt_id: str | None,
        resource_refs: list[str] | None,
        trigger: str | None = None,
        limit: int = 4,
        budget_chars: int = 12_000,
    ) -> dict[str, Any]:
        self._assert_active_identity(
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        evidence_status = str(evidence_status).upper()
        if evidence_status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise MethodRecordError("invalid Stage-B evidence status")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 16:
            raise MethodRecordError("invalid Stage-B limit")
        if not isinstance(budget_chars, int) or isinstance(budget_chars, bool) or not 256 <= budget_chars <= 100_000:
            raise MethodRecordError("invalid Stage-B budget")
        if trigger is None:
            trigger = evidence_status if evidence_status in {"UNKNOWN", "UNDERCOVERED"} else None
        trigger = trigger.upper() if isinstance(trigger, str) else None
        if trigger is not None and trigger not in STAGE_B_TRIGGERS:
            raise MethodRecordError("invalid Stage-B trigger")
        refs = self._refs(resource_refs)

        if signature_receipt_id is None:
            return {
                "fact_status": evidence_status,
                "method_context": [],
                "counterevidence": [],
                "shadow_method_context": [],
                "shadow_counterevidence": [],
                "receipt": {
                    "mode": "SHADOW_METHOD_V1",
                    "policy_version": self.POLICY_VERSION,
                    "signature_status": "MISSING_NOT_SERVED",
                    "trigger": trigger,
                    "served": False,
                    "truth_authority": False,
                    "effect_authority": False,
                    "fact_status_unchanged": evidence_status,
                },
            }

        signature_receipt = self.signatures.load_for_active(
            receipt_id=signature_receipt_id,
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        if signature_receipt["resource_refs"] != refs:
            raise MethodRecordError("Stage-B current resource refs diverge from admitted signature receipt")
        signature = canonical_problem_signature(signature_receipt["problem_signature"])
        signature_json = self._canonical({key: list(values) for key, values in signature.items()})
        signature_hash = hashlib.sha256(signature_json.encode("utf-8")).hexdigest()
        refs_hash = hashlib.sha256(self._canonical(refs).encode("utf-8")).hexdigest()

        if trigger not in STAGE_B_TRIGGERS:
            return {
                "fact_status": evidence_status,
                "method_context": [],
                "counterevidence": [],
                "shadow_method_context": [],
                "shadow_counterevidence": [],
                "receipt": {
                    "mode": "SHADOW_METHOD_V1",
                    "policy_version": self.POLICY_VERSION,
                    "signature_status": "ADMITTED_NO_TRIGGER",
                    "signature_receipt_id": signature_receipt_id,
                    "trigger": None,
                    "problem_signature_sha256": signature_hash,
                    "resource_refs_sha256": refs_hash,
                    "served": False,
                    "truth_authority": False,
                    "effect_authority": False,
                    "fact_status_unchanged": evidence_status,
                },
            }

        request_identity = {
            "policy_version": self.POLICY_VERSION,
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "evidence_status": evidence_status,
            "trigger": trigger,
            "signature_receipt_id": signature_receipt_id,
            "signature_identity_sha256": signature_receipt["signature_identity_sha256"],
            "problem_signature_sha256": signature_hash,
            "resource_refs_sha256": refs_hash,
            "limit": limit,
            "budget_chars": budget_chars,
        }
        request_hash = hashlib.sha256(self._canonical(request_identity).encode("utf-8")).hexdigest()
        subject = f"method_use:{causal_id}"
        replay = self.methods.read_use_receipt(subject=subject, user_id=user_id)
        if replay is not None:
            receipt_id, receipt = replay
            expected_receipt_identity = {
                "signature_receipt_id": signature_receipt_id,
                "signature_identity_sha256": signature_receipt["signature_identity_sha256"],
                "problem_signature_sha256": signature_hash,
                "resource_refs_sha256": refs_hash,
                "request_identity_sha256": request_hash,
            }
            for field, expected in expected_receipt_identity.items():
                if receipt[field] != expected:
                    raise MethodRecordError(f"Stage-B replay {field} mismatch")
            selected = self._decode_selected(
                list(receipt["selected_method_ids"]), user_id, signature, ACTIVE_METHOD_KINDS
            )
            counters = self._decode_selected(
                list(receipt["counterexample_memory_ids"]), user_id, signature, COUNTER_METHOD_KINDS
            )
            return {
                "fact_status": evidence_status,
                "method_context": [],
                "counterevidence": [],
                "shadow_method_context": selected,
                "shadow_counterevidence": counters,
                "receipt": {
                    **receipt,
                    "memory_id": receipt_id,
                    "mode": "SHADOW_METHOD_V1",
                    "policy_version": self.POLICY_VERSION,
                    "signature_status": "ADMITTED",
                    "fact_status_unchanged": evidence_status,
                    "replayed": True,
                },
            }

        methods: list[tuple[float, MethodRecord]] = []
        counters: list[tuple[float, MethodRecord]] = []
        for record in self._active_records(user_id):
            score = structural_similarity(signature, record.problem_signature)
            if score < self.MIN_STRUCTURAL_SCORE:
                continue
            if record.kind in ACTIVE_METHOD_KINDS:
                methods.append((score, record))
            else:
                counters.append((score, record))
        methods.sort(
            key=lambda pair: (
                pair[0], pair[1].calibration, pair[1].support_count, pair[1].memory_id or ""
            ),
            reverse=True,
        )
        counters.sort(
            key=lambda pair: (
                pair[0], pair[1].calibration, pair[1].support_count, pair[1].memory_id or ""
            ),
            reverse=True,
        )
        counter_by_id = {record.memory_id: (score, record) for score, record in counters}

        selected: list[tuple[float, MethodRecord]] = []
        blockers: list[tuple[float, MethodRecord]] = []
        chars = 0
        for score, record in methods:
            linked = [
                counter_by_id[mid]
                for mid in record.counterexample_memory_ids
                if mid in counter_by_id
            ]
            linked_blockers = [
                pair for pair in linked if pair[0] >= self.COUNTEREXAMPLE_BLOCK_SCORE
            ]
            if linked_blockers:
                blockers.extend(linked_blockers)
                continue
            public = self._public(record, score)
            cost = len(self._canonical(public))
            if chars + cost > budget_chars:
                continue
            selected.append((score, record))
            chars += cost
            if len(selected) >= limit:
                break

        counter_map: dict[str, tuple[float, MethodRecord]] = {}
        for score, record in counters[:limit]:
            if record.memory_id is not None:
                counter_map[record.memory_id] = (score, record)
        for score, record in blockers:
            if record.memory_id is not None:
                counter_map[record.memory_id] = (score, record)
        counter_selected = sorted(
            counter_map.values(), key=lambda pair: (pair[0], pair[1].memory_id or ""), reverse=True
        )[:limit]

        receipt_payload = {
            "schema": METHOD_RECEIPT_SCHEMA,
            "receipt_type": "USE",
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "evidence_status": evidence_status,
            "trigger": trigger,
            "signature_receipt_id": signature_receipt_id,
            "signature_identity_sha256": signature_receipt["signature_identity_sha256"],
            "problem_signature_sha256": signature_hash,
            "resource_refs_sha256": refs_hash,
            "request_identity_sha256": request_hash,
            "selected_method_ids": [
                record.memory_id for _, record in selected if record.memory_id is not None
            ],
            "counterexample_memory_ids": [
                record.memory_id for _, record in counter_selected if record.memory_id is not None
            ],
            "limit": limit,
            "budget_chars": budget_chars,
            "served": False,
            "ts": time.time(),
            "truth_authority": False,
            "effect_authority": False,
        }
        receipt_id = self.methods.write_use_receipt(
            receipt_payload, source_turn_id=turn_id, user_id=user_id, subject=subject
        )
        return {
            "fact_status": evidence_status,
            "method_context": [],
            "counterevidence": [],
            "shadow_method_context": [self._public(record, score) for score, record in selected],
            "shadow_counterevidence": [
                self._public(record, score) for score, record in counter_selected
            ],
            "receipt": {
                **receipt_payload,
                "memory_id": receipt_id,
                "mode": "SHADOW_METHOD_V1",
                "policy_version": self.POLICY_VERSION,
                "signature_status": "ADMITTED",
                "fact_status_unchanged": evidence_status,
                "replayed": False,
            },
        }
