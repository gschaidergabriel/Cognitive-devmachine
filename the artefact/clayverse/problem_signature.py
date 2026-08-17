from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any

from .method_memory import MethodRecordError, canonical_problem_signature

PROBLEM_SIGNATURE_RECEIPT_SCHEMA = "clayverse.problem_signature_admission/v1"
_ALLOWED_SOURCES = frozenset({"VALIDATED_ABSTRACTION", "OWNER_EXPLICIT_STRUCTURED"})
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ProblemSignatureAdmission:
    """One turn-bound authority for Stage-B structural problem signatures.

    The admitted signature is a routing/abstraction signal only. It carries no
    factual truth or effect authority and is bound to the active canonical turn,
    entity generation and normalized resource set before Stage-B can consume it.
    """

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _canonical(value: Any) -> str:
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise MethodRecordError("problem-signature admission must be finite canonical JSON") from exc

    @staticmethod
    def _refs(resource_refs: list[str] | None) -> list[str]:
        refs = resource_refs or []
        if not isinstance(refs, list) or len(refs) > 50:
            raise MethodRecordError("problem-signature resource refs invalid")
        normalized: list[str] = []
        for ref in refs:
            if not isinstance(ref, str) or not ref.strip() or len(ref) > 1000:
                raise MethodRecordError("problem-signature resource ref invalid")
            normalized.append(ref.strip())
        return sorted(set(normalized))

    @staticmethod
    def _provenance(value: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise MethodRecordError("problem-signature provenance must be an object")
        expected = {"source", "producer", "abstraction_version", "producer_sha256"}
        if set(value) != expected:
            raise MethodRecordError("problem-signature provenance fields mismatch")
        source = value["source"]
        if source not in _ALLOWED_SOURCES:
            raise MethodRecordError("problem-signature provenance source is not admitted")
        producer = value["producer"]
        abstraction_version = value["abstraction_version"]
        digest = value["producer_sha256"]
        if not isinstance(producer, str) or not producer.strip() or len(producer) > 300:
            raise MethodRecordError("problem-signature producer invalid")
        if not isinstance(abstraction_version, str) or not abstraction_version.strip() or len(abstraction_version) > 160:
            raise MethodRecordError("problem-signature abstraction version invalid")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise MethodRecordError("problem-signature producer digest invalid")
        return {
            "source": source,
            "producer": producer.strip(),
            "abstraction_version": abstraction_version.strip(),
            "producer_sha256": digest,
        }

    @staticmethod
    def _receipt_id(user_id: str, causal_id: str) -> str:
        digest = hashlib.sha256(f"{user_id}\x1f{causal_id}".encode("utf-8")).hexdigest()
        return f"problem-signature:{digest}"

    def _active_identity(self, session_id: str, user_id: str):
        self.db.assert_session_owner(session_id, user_id)
        row = self.db.db.execute(
            "SELECT user_id,turn_id,episode_id,causal_id,generation,resource_refs FROM active_turns WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise MethodRecordError("problem-signature admission requires active canonical turn")
        self.db.assert_live_generation(session_id, int(row["generation"]))
        if str(row["user_id"]) != user_id:
            raise MethodRecordError("problem-signature active user mismatch")
        try:
            refs = self._refs(json.loads(str(row["resource_refs"])))
        except (TypeError, json.JSONDecodeError) as exc:
            raise MethodRecordError("active turn resource refs invalid") from exc
        return row, refs

    def admit_in_tx(
        self,
        *,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        resource_refs: list[str] | None,
        problem_signature: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.db.db.in_transaction:
            raise MethodRecordError("problem-signature admission must join the canonical turn transaction")
        active, active_refs = self._active_identity(session_id, user_id)
        expected = (turn_id, episode_id, causal_id, int(generation))
        observed = (str(active["turn_id"]), str(active["episode_id"]), str(active["causal_id"]), int(active["generation"]))
        if observed != expected:
            raise MethodRecordError("problem-signature causal identity mismatch")
        refs = self._refs(resource_refs)
        if refs != active_refs:
            raise MethodRecordError("problem-signature resources diverge from active turn")

        signature = canonical_problem_signature(problem_signature)
        signature_public = {key: list(values) for key, values in signature.items()}
        admitted_provenance = self._provenance(provenance)
        provenance_sha256 = hashlib.sha256(self._canonical(admitted_provenance).encode("utf-8")).hexdigest()
        identity = {
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "resource_refs": refs,
            "problem_signature": signature_public,
            "signature_source": admitted_provenance["source"],
            "abstraction_version": admitted_provenance["abstraction_version"],
            "signature_provenance_sha256": provenance_sha256,
        }
        identity_sha256 = hashlib.sha256(self._canonical(identity).encode("utf-8")).hexdigest()
        receipt_id = self._receipt_id(user_id, causal_id)
        payload = {
            "schema": PROBLEM_SIGNATURE_RECEIPT_SCHEMA,
            **identity,
            "signature_identity_sha256": identity_sha256,
            "provenance": admitted_provenance,
            "ts": time.time(),
            "truth_authority": False,
            "effect_authority": False,
        }
        stored_provenance = {
            "source": "problem_signature_admission:v1",
            "schema": PROBLEM_SIGNATURE_RECEIPT_SCHEMA,
            "signature_identity_sha256": identity_sha256,
            "truth_authority": False,
            "effect_authority": False,
        }
        self.db.db.execute(
            "INSERT OR IGNORE INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) VALUES(?,?,?,?,?,?,?,?)",
            (receipt_id, "method_receipt", f"problem_signature:{causal_id}", self._canonical(payload), turn_id, user_id, time.time(), self._canonical(stored_provenance)),
        )
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (receipt_id,)).fetchone()
        if row is None:
            raise MethodRecordError("problem-signature receipt persistence failed")
        receipt = self.decode_row(row)
        if receipt["signature_identity_sha256"] != identity_sha256:
            raise MethodRecordError("problem-signature replay identity mismatch")
        return receipt

    def decode_row(self, row) -> dict[str, Any]:
        if row is None or str(row["kind"]) != "method_receipt":
            raise MethodRecordError("problem-signature receipt row missing or wrong kind")
        try:
            payload = json.loads(str(row["value"]), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
            stored_provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise MethodRecordError("problem-signature receipt JSON invalid") from exc
        required = {
            "schema", "user_id", "session_id", "turn_id", "episode_id", "causal_id", "generation",
            "resource_refs", "problem_signature", "signature_source", "abstraction_version",
            "signature_provenance_sha256", "signature_identity_sha256", "provenance", "ts",
            "truth_authority", "effect_authority",
        }
        if not isinstance(payload, dict) or set(payload) != required:
            raise MethodRecordError("problem-signature receipt fields mismatch")
        if payload["schema"] != PROBLEM_SIGNATURE_RECEIPT_SCHEMA:
            raise MethodRecordError("problem-signature receipt schema mismatch")
        if payload["truth_authority"] is not False or payload["effect_authority"] is not False:
            raise MethodRecordError("problem-signature receipt cannot mint authority")
        admitted_provenance = self._provenance(payload["provenance"])
        expected_provenance_sha = hashlib.sha256(self._canonical(admitted_provenance).encode("utf-8")).hexdigest()
        if payload["signature_provenance_sha256"] != expected_provenance_sha:
            raise MethodRecordError("problem-signature provenance hash mismatch")
        signature = canonical_problem_signature(payload["problem_signature"])
        refs = self._refs(payload["resource_refs"])
        identity = {
            "user_id": payload["user_id"],
            "session_id": payload["session_id"],
            "turn_id": payload["turn_id"],
            "episode_id": payload["episode_id"],
            "causal_id": payload["causal_id"],
            "generation": int(payload["generation"]),
            "resource_refs": refs,
            "problem_signature": {key: list(values) for key, values in signature.items()},
            "signature_source": payload["signature_source"],
            "abstraction_version": payload["abstraction_version"],
            "signature_provenance_sha256": expected_provenance_sha,
        }
        expected_identity_sha = hashlib.sha256(self._canonical(identity).encode("utf-8")).hexdigest()
        if payload["signature_identity_sha256"] != expected_identity_sha:
            raise MethodRecordError("problem-signature identity hash mismatch")
        if not isinstance(stored_provenance, dict) or stored_provenance != {
            "source": "problem_signature_admission:v1",
            "schema": PROBLEM_SIGNATURE_RECEIPT_SCHEMA,
            "signature_identity_sha256": expected_identity_sha,
            "truth_authority": False,
            "effect_authority": False,
        }:
            raise MethodRecordError("problem-signature durable provenance mismatch")
        if str(row["memory_id"]) != self._receipt_id(str(payload["user_id"]), str(payload["causal_id"])):
            raise MethodRecordError("problem-signature receipt id mismatch")
        if str(row["source_turn_id"]) != str(payload["turn_id"]) or str(row["user_id"]) != str(payload["user_id"]):
            raise MethodRecordError("problem-signature durable identity mismatch")
        return {**payload, "memory_id": str(row["memory_id"])}

    def load_active(self, *, session_id: str, user_id: str) -> dict[str, Any] | None:
        active, active_refs = self._active_identity(session_id, user_id)
        receipt_id = self._receipt_id(user_id, str(active["causal_id"]))
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (receipt_id,)).fetchone()
        if row is None:
            return None
        receipt = self.decode_row(row)
        observed = (receipt["turn_id"], receipt["episode_id"], receipt["causal_id"], int(receipt["generation"]))
        expected = (str(active["turn_id"]), str(active["episode_id"]), str(active["causal_id"]), int(active["generation"]))
        if observed != expected or receipt["resource_refs"] != active_refs:
            raise MethodRecordError("problem-signature receipt no longer matches active turn")
        return receipt
