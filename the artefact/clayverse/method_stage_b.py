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

    Stage-B deliberately does not infer a structural signature from raw prompt text at
    this boundary. Without an explicit structured problem_signature it fails closed to
    no method context, preventing lexical heuristics from silently becoming analogy
    selection authority. Signature derivation/admission remains a separate gate.

    The active-turn identity check is relational, not merely referential: the active row,
    referenced session, turn and workspace episode must all agree on the same canonical
    user/session boundary before any method retrieval is allowed.
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

        if problem_signature is None:
            return {
                "methods": [],
                "counterevidence": [],
                "problem_signature": None,
                "receipt": {
                    "policy_version": self.POLICY_VERSION,
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "episode_id": episode_id,
                    "causal_id": causal_id,
                    "generation": int(generation),
                    "evidence_status": factual_status,
                    "triggered": False,
                    "status": "SIGNATURE_REQUIRED",
                    "problem_signature_sha256": None,
                    "selected_method_ids": [],
                    "counterevidence_ids": [],
                    "factual_status_unchanged": factual_status,
                    "signature_source": "NONE",
                    "truth_authority": False,
                    "effect_authority": False,
                },
            }

        result = self.methods.retrieve(
            query=query,
            user_id=user_id,
            evidence_status=factual_status,
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
            "status": "METHOD_PRESENT" if selected_method_ids else "METHOD_UNKNOWN",
            "problem_signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
            "selected_method_ids": selected_method_ids,
            "counterevidence_ids": counterevidence_ids,
            "factual_status_unchanged": str(result["factual_status_unchanged"]),
            "signature_source": "EXPLICIT_STRUCTURED_INPUT",
            "truth_authority": False,
            "effect_authority": False,
        }
        return {
            "methods": result["methods"],
            "counterevidence": result["counterevidence"],
            "problem_signature": result["problem_signature"],
            "receipt": receipt,
        }
