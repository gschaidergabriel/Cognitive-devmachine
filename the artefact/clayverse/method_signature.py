from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .method_memory import MethodRecordError, canonical_problem_signature
from .store import StaleGeneration, UnifiedDB

SIGNATURE_SCHEMA = "clayverse-stage-b-signature/v1"
SIGNATURE_POLICY_VERSION = 1
ALLOWED_PRODUCERS = frozenset({"clayverse:problem-signature:v1"})


class MethodSignatureAuthority:
    """Admit structural Stage-B signatures as canonical causal control receipts.

    Signatures are stored as `method_receipt` durable memory, so they are already on the
    canonical UnifiedDB/checkpoint path and are excluded from factual Stage-A retrieval.
    They carry no truth/effect authority and can only be reused by the exact active turn
    identity that admitted them.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise MethodRecordError("non-canonical problem signature") from exc

    @staticmethod
    def _memory_id(causal_id: str) -> str:
        digest = hashlib.sha256(str(causal_id).encode("utf-8")).hexdigest()
        return f"method-stage-b-signature:{digest}"

    def _assert_active(self, *, user_id: str, session_id: str, turn_id: str, episode_id: str,
                       causal_id: str, generation: int) -> None:
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        row = self.db.db.execute(
            "SELECT a.user_id AS active_user,a.turn_id,a.episode_id,a.causal_id,a.generation,"
            "s.user_id AS session_user,t.user_id AS turn_user,t.session_id AS turn_session,"
            "w.session_id AS episode_session FROM active_turns a "
            "JOIN sessions s ON s.session_id=a.session_id "
            "JOIN turns t ON t.turn_id=a.turn_id "
            "JOIN workspace_episodes w ON w.episode_id=a.episode_id WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        if row is None or any((
            str(row["active_user"]) != user_id,
            str(row["session_user"]) != user_id,
            str(row["turn_user"]) != user_id,
            str(row["turn_session"]) != session_id,
            str(row["episode_session"]) != session_id,
            str(row["turn_id"]) != turn_id,
            str(row["episode_id"]) != episode_id,
            str(row["causal_id"]) != causal_id,
            int(row["generation"]) != int(generation),
        )):
            raise StaleGeneration("method_signature_identity")

    def _decode(self, row) -> dict[str, Any]:
        if row is None or str(row["kind"]) != "method_receipt":
            raise StaleGeneration("method_signature_missing")
        try:
            payload = json.loads(str(row["value"]))
            provenance = json.loads(str(row["provenance"]))
        except Exception as exc:
            raise StaleGeneration("method_signature_malformed") from exc
        if not isinstance(payload, dict) or payload.get("schema") != SIGNATURE_SCHEMA:
            raise StaleGeneration("method_signature_schema")
        if not isinstance(provenance, dict) or provenance.get("source") != "method_signature:v1":
            raise StaleGeneration("method_signature_provenance")
        signature = canonical_problem_signature(payload.get("problem_signature"))
        signature_sha = hashlib.sha256(self._json(signature).encode("utf-8")).hexdigest()
        if payload.get("signature_sha256") != signature_sha:
            raise StaleGeneration("method_signature_digest")
        if payload.get("truth_authority") is not False or payload.get("effect_authority") is not False:
            raise StaleGeneration("method_signature_authority")
        if provenance.get("truth_authority") is not False or provenance.get("effect_authority") is not False:
            raise StaleGeneration("method_signature_authority")
        return {"memory_id": str(row["memory_id"]), "payload": {**payload, "problem_signature": signature},
                "provenance": provenance, "user_id": row["user_id"], "source_turn_id": row["source_turn_id"]}

    def admit(self, *, problem_signature: dict[str, Any], producer: str, user_id: str,
              session_id: str, turn_id: str, episode_id: str, causal_id: str,
              generation: int) -> str:
        if producer not in ALLOWED_PRODUCERS:
            raise MethodRecordError("unrecognized structural-signature producer")
        self._assert_active(user_id=user_id, session_id=session_id, turn_id=turn_id,
                            episode_id=episode_id, causal_id=causal_id, generation=generation)
        signature = canonical_problem_signature(problem_signature)
        signature_sha = hashlib.sha256(self._json(signature).encode("utf-8")).hexdigest()
        payload = {
            "schema": SIGNATURE_SCHEMA,
            "policy_version": SIGNATURE_POLICY_VERSION,
            "producer": producer,
            "problem_signature": signature,
            "signature_sha256": signature_sha,
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "truth_authority": False,
            "effect_authority": False,
        }
        value = self._json(payload)
        memory_id = self._memory_id(causal_id)
        provenance = self._json({
            "source": "method_signature:v1",
            "schema": SIGNATURE_SCHEMA,
            "policy_version": SIGNATURE_POLICY_VERSION,
            "producer": producer,
            "causal_id": causal_id,
            "generation": int(generation),
            "user_scope": user_id,
            "signature_sha256": signature_sha,
            "truth_authority": False,
            "effect_authority": False,
        })

        def insert(db) -> bool:
            cursor = db.execute(
                "INSERT OR IGNORE INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (memory_id, "method_receipt", f"stage_b_signature:{causal_id}", value,
                 turn_id, user_id, time.time(), provenance),
            )
            return int(cursor.rowcount or 0) == 1

        if self.db.db.in_transaction:
            inserted = insert(self.db.db)
        else:
            with self.db.tx() as db:
                inserted = insert(db)
        if not inserted:
            row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
            decoded = self._decode(row)
            if decoded["payload"] != payload or decoded["user_id"] != user_id or decoded["source_turn_id"] != turn_id:
                raise StaleGeneration("method_signature_identity")
        return memory_id

    def load(self, *, memory_id: str, user_id: str, session_id: str, turn_id: str,
             episode_id: str, causal_id: str, generation: int) -> dict[str, Any]:
        self._assert_active(user_id=user_id, session_id=session_id, turn_id=turn_id,
                            episode_id=episode_id, causal_id=causal_id, generation=generation)
        expected = self._memory_id(causal_id)
        if memory_id != expected:
            raise StaleGeneration("method_signature_identity")
        row = self.db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        decoded = self._decode(row)
        payload = decoded["payload"]
        if decoded["user_id"] != user_id or decoded["source_turn_id"] != turn_id or any((
            payload.get("user_id") != user_id,
            payload.get("session_id") != session_id,
            payload.get("turn_id") != turn_id,
            payload.get("episode_id") != episode_id,
            payload.get("causal_id") != causal_id,
            int(payload.get("generation", -1)) != int(generation),
            payload.get("producer") not in ALLOWED_PRODUCERS,
            int(payload.get("policy_version", -1)) != SIGNATURE_POLICY_VERSION,
        )):
            raise StaleGeneration("method_signature_identity")
        return decoded
