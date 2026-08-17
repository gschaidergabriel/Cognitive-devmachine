from __future__ import annotations
import json
from .microclay_retrieval import MicroClayRetrieval
from .store import UnifiedDB


class WorldAssembler:
    """Bounded world assembly with MicroClay retrieval and collision-only cross-session context."""

    CONTROL_MEMORY_KINDS = ("source_archive", "compression_receipt", "compression_clearance")

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = MicroClayRetrieval(db)

    def _extracted_fragments(self, turn_id):
        rows = self.db.db.execute(
            "SELECT kind,value,provenance FROM durable_memory "
            "WHERE source_turn_id=? AND kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
            "ORDER BY ts LIMIT 20",
            (turn_id,),
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
        # collides. MicroClay cannot broaden this privacy/attention boundary by learning.
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
        counterevidence = []
        unknowns = []
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
            retrieval_receipt = dict(result["receipt"])

            # Start with the strongest safe Stage-B trigger. More nuanced UNDERCOVERED,
            # strategy and novelty triggers require explicit later calibration.
            if retrieval_receipt.get("status") == "UNKNOWN":
                methods = self.microclay.retrieve_methods(
                    query=str(supplied["query"]),
                    user_id=user_id,
                    session_id=session_id,
                    turn_id=str(supplied["turn_id"]),
                    episode_id=str(supplied["episode_id"]),
                    causal_id=str(supplied["causal_id"]),
                    generation=int(supplied["generation"]),
                )
                method_context = [
                    item for item in methods["items"] if item.get("kind") != "counterexample"
                ]
                counterevidence = [
                    item for item in methods["items"] if item.get("kind") == "counterexample"
                ]
                retrieval_receipt["method"] = methods["receipt"]
                unknowns = [{
                    "status": "FACT_UNKNOWN",
                    "query_sha256": retrieval_receipt.get("query_sha256"),
                    "method_present": bool(method_context or counterevidence),
                }]
        else:
            # Compatibility path for legacy tests/non-product callers with no active
            # causal turn. Method memory is excluded here too: a reusable method must
            # never collapse into factual durable-memory context merely through fallback.
            excluded = tuple(sorted(
                set(self.CONTROL_MEMORY_KINDS) | set(MicroClayRetrieval.METHOD_KINDS)
            ))
            memories = [
                dict(r)
                for r in self.db.db.execute(
                    "SELECT * FROM durable_memory "
                    f"WHERE kind NOT IN ({','.join('?' for _ in excluded)}) "
                    "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 50",
                    (*excluded, user_id),
                )
            ]

        return {
            "own_recent": own,
            "cross_session_collision": other,
            "durable_memory": memories,
            "method_context": method_context,
            "unknowns": unknowns,
            "counterevidence": counterevidence,
            "retrieval_receipt": retrieval_receipt,
        }

    def credit(self, *, causal_id, generation, credit, signal_class):
        return self.microclay.credit(
            causal_id=str(causal_id),
            generation=int(generation),
            credit=float(credit),
            signal_class=str(signal_class),
        )
