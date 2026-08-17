from __future__ import annotations

import hashlib
import json
from typing import Any

from .method_memory import MethodMemory
from .store import UnifiedDB


class StageBMethodRetrieval:
    """Causal-identity wrapper around deterministic method-memory retrieval.

    It does not change factual status. The receipt binds the selected method IDs to the
    same session/turn/episode/causal/generation identity as the evidence retrieval path.
    """

    POLICY_VERSION = 1

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.methods = MethodMemory(db)

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
    ) -> dict[str, Any]:
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        active = self.db.db.execute(
            "SELECT turn_id,episode_id,causal_id,generation FROM active_turns WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if active is None:
            raise RuntimeError("Stage-B retrieval requires an active canonical turn")
        if (
            str(active["turn_id"]) != str(turn_id)
            or str(active["episode_id"]) != str(episode_id)
            or str(active["causal_id"]) != str(causal_id)
            or int(active["generation"]) != int(generation)
        ):
            raise RuntimeError("Stage-B retrieval identity mismatch")

        result = self.methods.retrieve(
            query=query,
            user_id=user_id,
            evidence_status=evidence_status,
            resource_refs=resource_refs,
            problem_signature=problem_signature,
            limit=limit,
        )
        signature_bytes = json.dumps(
            result["problem_signature"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        selected_method_ids = [str(item["memory_id"]) for item in result["methods"]]
        counterevidence_ids = [str(item["memory_id"]) for item in result["counterevidence"]]
        receipt = {
            "policy_version": self.POLICY_VERSION,
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": int(generation),
            "evidence_status": str(result["evidence_status"]),
            "triggered": bool(result["triggered"]),
            "problem_signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
            "selected_method_ids": selected_method_ids,
            "counterevidence_ids": counterevidence_ids,
            "factual_status_unchanged": str(result["factual_status_unchanged"]),
            "truth_authority": False,
            "effect_authority": False,
        }
        return {
            "methods": result["methods"],
            "counterevidence": result["counterevidence"],
            "problem_signature": result["problem_signature"],
            "receipt": receipt,
        }
