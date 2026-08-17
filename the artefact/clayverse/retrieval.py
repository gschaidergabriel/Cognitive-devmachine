from __future__ import annotations

import json
from dataclasses import replace

from .method_transfer import METHOD_MEMORY_KINDS, MethodTransfer
from .microclay_retrieval import MicroClayRetrieval
from .store import UnifiedDB


class EvidenceMicroClayRetrieval(MicroClayRetrieval):
    """MicroClay evidence lane with method-memory kinds made non-servable."""

    def _score_candidate(self, row, query_tokens, now, capitals):
        candidate = super()._score_candidate(row, query_tokens, now, capitals)
        if candidate.kind in METHOD_MEMORY_KINDS:
            return replace(candidate, baseline_score=0.0, adaptive_score=0.0, entry_keys=())
        return candidate


class WorldAssembler:
    """Bounded evidence + optional method assembly with collision-only cross-session context."""

    CONTROL_MEMORY_KINDS = tuple(sorted({
        "source_archive",
        "compression_receipt",
        "compression_clearance",
        *METHOD_MEMORY_KINDS,
    }))

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = EvidenceMicroClayRetrieval(db)
        self.methods = MethodTransfer(db)

    @classmethod
    def _not_control_clause(cls):
        return ",".join("?" for _ in cls.CONTROL_MEMORY_KINDS)

    def _extracted_fragments(self, turn_id):
        rows = self.db.db.execute(
            "SELECT kind,value,provenance FROM durable_memory "
            f"WHERE source_turn_id=? AND kind NOT IN ({self._not_control_clause()}) "
            "ORDER BY ts LIMIT 20",
            (turn_id, *self.CONTROL_MEMORY_KINDS),
        ).fetchall()
        return [dict(r) for r in rows]

    def _active_identity(self, session_id):
        row = self.db.db.execute(
            "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,t.content "
            "FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
            "WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "query": row["content"],
            "turn_id": row["turn_id"],
            "episode_id": row["episode_id"],
            "causal_id": row["causal_id"],
            "generation": int(row["generation"]),
        }

    def assemble(
        self,
        session_id,
        resource_refs,
        *,
        query=None,
        turn_id=None,
        episode_id=None,
        causal_id=None,
        generation=None,
    ):
        session = self.db.db.execute(
            "SELECT user_id FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if not session:
            raise KeyError(session_id)
        user_id = session["user_id"]
        own = [dict(r) for r in self.db.recent_turns(session_id, 20)]

        # Another permanent perspective is loaded only when an explicit shared resource
        # collides. Adaptive retrieval cannot broaden this privacy/attention boundary.
        other = []
        if resource_refs:
            wanted = set(resource_refs)
            for r in self.db.db.execute(
                "SELECT * FROM turns WHERE session_id<>? ORDER BY ts DESC LIMIT 200",
                (session_id,),
            ).fetchall():
                if wanted.intersection(json.loads(r["resource_refs"])):
                    item = dict(r)
                    if int(r["compression_generation"]) > 0:
                        item["retrieval_fidelity"] = "compressed_with_extracted_fragments"
                        item["extracted_fragments"] = self._extracted_fragments(r["turn_id"])
                    other.append(item)
                    if len(other) >= 10:
                        break

        retrieval_receipt = {
            "mode": "LEGACY_COMPATIBILITY",
            "status": "UNKNOWN",
            "truth_authority": False,
            "effect_authority": False,
        }
        method_context = []
        method_retrieval_receipt = {
            "policy_version": MethodTransfer.POLICY_VERSION,
            "status": "NOT_TRIGGERED",
            "trigger": "NO_CAUSAL_TURN",
            "truth_authority": False,
            "effect_authority": False,
            "replayed": False,
        }
        supplied = {
            "query": query,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": generation,
        }
        if not all(value is not None for value in supplied.values()):
            active = self._active_identity(session_id)
            if active is not None:
                supplied = active

        if all(value is not None for value in supplied.values()):
            result = self.microclay.retrieve(
                query=str(supplied["query"]),
                user_id=user_id,
                session_id=session_id,
                turn_id=str(supplied["turn_id"]),
                episode_id=str(supplied["episode_id"]),
                causal_id=str(supplied["causal_id"]),
                generation=int(supplied["generation"]),
            )
            memories = result["items"]
            retrieval_receipt = result["receipt"]
            method_result = self.methods.retrieve(
                query=str(supplied["query"]),
                evidence_status=str(retrieval_receipt.get("status", "UNKNOWN")),
                user_id=user_id,
                session_id=session_id,
                turn_id=str(supplied["turn_id"]),
                episode_id=str(supplied["episode_id"]),
                causal_id=str(supplied["causal_id"]),
                generation=int(supplied["generation"]),
                resource_refs=list(resource_refs or []),
            )
            method_context = method_result["items"]
            method_retrieval_receipt = method_result["receipt"]
        else:
            # Compatibility path for legacy tests/non-product callers with no active
            # causal turn. Product Claude hooks always have an active turn here.
            memories = [
                dict(r)
                for r in self.db.db.execute(
                    "SELECT * FROM durable_memory "
                    f"WHERE kind NOT IN ({self._not_control_clause()}) "
                    "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 50",
                    (*self.CONTROL_MEMORY_KINDS, user_id),
                )
            ]

        return {
            "own_recent": own,
            "cross_session_collision": other,
            "durable_memory": memories,
            "retrieval_receipt": retrieval_receipt,
            "method_context": method_context,
            "method_retrieval_receipt": method_retrieval_receipt,
        }

    def credit(self, *, causal_id, generation, credit, signal_class):
        return self.microclay.credit(
            causal_id=str(causal_id),
            generation=int(generation),
            credit=float(credit),
            signal_class=str(signal_class),
        )
