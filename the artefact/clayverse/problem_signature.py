from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .method_memory import MethodRecordError, canonical_problem_signature
from .store import UnifiedDB

PROBLEM_SIGNATURE_RECEIPT_SCHEMA = "clayverse.problem_signature_receipt/v1"


class ProblemSignatureAdmission:
    """Admission boundary for structured Stage-B query signatures.

    This class deliberately has no free-text parser. A future abstraction mechanism may
    propose a structured signature, but it becomes Stage-B input only after this exact
    causal/user/generation-bound receipt is persisted.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _canonical(value: Any) -> str:
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise MethodRecordError("problem-signature receipt must be finite canonical JSON") from exc

    @staticmethod
    def _resource_refs(resource_refs: list[str] | None) -> list[str]:
        if resource_refs is None:
            return []
        if not isinstance(resource_refs, list) or len(resource_refs) > 50:
            raise MethodRecordError("problem-signature resource refs invalid")
        refs: list[str] = []
        for ref in resource_refs:
            if not isinstance(ref, str) or not ref.strip() or len(ref) > 1000:
                raise MethodRecordError("problem-signature resource ref invalid")
            refs.append(ref.strip())
        return sorted(set(refs))

    def _assert_identity(
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
            raise MethodRecordError("problem-signature admission requires active canonical turn")
        observed = (str(row["user_id"]), str(row["turn_id"]), str(row["episode_id"]), str(row["causal_id"]), int(row["generation"]))
        expected = (user_id, turn_id, episode_id, causal_id, int(generation))
        if observed != expected:
            raise MethodRecordError("problem-signature admission identity mismatch")

    def admit(
        self,
        *,
        problem_signature: dict[str, Any],
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        resource_refs: list[str] | None,
        source: str,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        self._assert_identity(
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        if source not in {"EXPLICIT_STRUCTURED", "VALIDATED_ABSTRACTION"}:
            raise MethodRecordError("problem-signature admission source is not authorized")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodRecordError("problem-signature admission requires provenance")
        forbidden = {"truth_authority", "effect_authority"}.intersection(provenance)
        if forbidden:
            raise MethodRecordError("problem-signature caller cannot mint authority")
        signature = canonical_problem_signature(problem_signature)
        signature_public = {key: list(values) for key, values in signature.items()}
        refs = self._resource_refs(resource_refs)
        identity = {
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "problem_signature": signature_public,
            "resource_refs": refs,
            "source": source,
        }
        identity_hash = hashlib.sha256(self._canonical(identity).encode("utf-8")).hexdigest()
        subject = f"problem_signature:{causal_id}"
        existing = self.db.db.execute(
            "SELECT memory_id,value FROM durable_memory WHERE kind='method_receipt' AND subject=? AND user_id=? ORDER BY ts LIMIT 2",
            (subject, user_id),
        ).fetchall()
        if existing:
            if len(existing) != 1:
                raise MethodRecordError("duplicate problem-signature receipts fail closed")
            receipt = self.decode(existing[0]["value"])
            if receipt["signature_identity_sha256"] != identity_hash:
                raise MethodRecordError("problem-signature replay identity mismatch")
            return {"memory_id": str(existing[0]["memory_id"]), **receipt, "replayed": True}

        payload = {
            "schema": PROBLEM_SIGNATURE_RECEIPT_SCHEMA,
            **identity,
            "signature_identity_sha256": identity_hash,
            "ts": time.time(),
            "truth_authority": False,
            "effect_authority": False,
        }
        receipt_id = self.db.add_memory(
            "method_receipt",
            subject,
            self._canonical(payload),
            turn_id,
            user_id,
            {
                **provenance,
                "problem_signature_receipt_schema": PROBLEM_SIGNATURE_RECEIPT_SCHEMA,
                "truth_authority": False,
                "effect_authority": False,
            },
        )
        return {"memory_id": receipt_id, **payload, "replayed": False}

    def decode(self, raw: Any) -> dict[str, Any]:
        if isinstance(raw, str):
            try:
                payload = json.loads(raw, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
            except Exception as exc:
                raise MethodRecordError("invalid problem-signature receipt JSON") from exc
        elif isinstance(raw, dict):
            payload = raw
        else:
            raise MethodRecordError("problem-signature receipt must be an object")
        expected = {
            "schema", "user_id", "session_id", "turn_id", "episode_id", "causal_id", "generation",
            "problem_signature", "resource_refs", "source", "signature_identity_sha256", "ts",
            "truth_authority", "effect_authority",
        }
        if not isinstance(payload, dict) or set(payload) != expected:
            raise MethodRecordError("problem-signature receipt fields mismatch")
        if payload["schema"] != PROBLEM_SIGNATURE_RECEIPT_SCHEMA:
            raise MethodRecordError("problem-signature receipt schema mismatch")
        if payload["user_id"] not in {"gabriel", "andreas"}:
            raise MethodRecordError("problem-signature receipt user invalid")
        if payload["source"] not in {"EXPLICIT_STRUCTURED", "VALIDATED_ABSTRACTION"}:
            raise MethodRecordError("problem-signature receipt source invalid")
        signature = canonical_problem_signature(payload["problem_signature"])
        refs = self._resource_refs(payload["resource_refs"])
        if not isinstance(payload["generation"], int) or isinstance(payload["generation"], bool) or payload["generation"] < 1:
            raise MethodRecordError("problem-signature receipt generation invalid")
        if not isinstance(payload["ts"], (int, float)) or isinstance(payload["ts"], bool) or float(payload["ts"]) <= 0:
            raise MethodRecordError("problem-signature receipt timestamp invalid")
        if payload["truth_authority"] is not False or payload["effect_authority"] is not False:
            raise MethodRecordError("problem-signature receipt cannot mint authority")
        identity = {
            "user_id": payload["user_id"],
            "session_id": payload["session_id"],
            "turn_id": payload["turn_id"],
            "episode_id": payload["episode_id"],
            "causal_id": payload["causal_id"],
            "generation": payload["generation"],
            "problem_signature": {key: list(values) for key, values in signature.items()},
            "resource_refs": refs,
            "source": payload["source"],
        }
        expected_hash = hashlib.sha256(self._canonical(identity).encode("utf-8")).hexdigest()
        if payload["signature_identity_sha256"] != expected_hash:
            raise MethodRecordError("problem-signature receipt hash mismatch")
        return json.loads(self._canonical(payload))

    def load_for_active(
        self,
        *,
        receipt_id: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
    ) -> dict[str, Any]:
        self._assert_identity(
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        row = self.db.db.execute(
            "SELECT value,user_id,source_turn_id,provenance FROM durable_memory WHERE memory_id=? AND kind='method_receipt'",
            (receipt_id,),
        ).fetchone()
        if row is None or str(row["user_id"]) != user_id or str(row["source_turn_id"]) != turn_id:
            raise MethodRecordError("problem-signature receipt missing or outside active user/turn")
        receipt = self.decode(str(row["value"]))
        identity = (user_id, session_id, turn_id, episode_id, causal_id, int(generation))
        observed = (
            receipt["user_id"], receipt["session_id"], receipt["turn_id"], receipt["episode_id"],
            receipt["causal_id"], int(receipt["generation"]),
        )
        if observed != identity:
            raise MethodRecordError("problem-signature receipt active identity mismatch")
        provenance = json.loads(str(row["provenance"]))
        if not isinstance(provenance, dict) or provenance.get("problem_signature_receipt_schema") != PROBLEM_SIGNATURE_RECEIPT_SCHEMA:
            raise MethodRecordError("problem-signature receipt provenance invalid")
        return receipt
