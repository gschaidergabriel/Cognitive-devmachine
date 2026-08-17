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
            "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,t.content,"
            "a.user_id AS active_user_id,s.user_id AS session_user_id,"
            "t.session_id AS turn_session_id,t.user_id AS turn_user_id,"
            "w.session_id AS episode_session_id,w.observation_turn_id AS episode_turn_id "
            "FROM active_turns a "
            "JOIN sessions s ON s.session_id=a.session_id "
            "JOIN turns t ON t.turn_id=a.turn_id "
            "JOIN workspace_episodes w ON w.episode_id=a.episode_id "
            "WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            active = self.db.db.execute(
                "SELECT 1 FROM active_turns WHERE session_id=?", (session_id,)
            ).fetchone()
            if active:
                raise RuntimeError("active causal identity join incomplete")
            return None
        if (
            row["active_user_id"] != row["session_user_id"]
            or row["turn_session_id"] != session_id
            or row["turn_user_id"] != row["active_user_id"]
            or row["episode_session_id"] != session_id
            or row["episode_turn_id"] != row["turn_id"]
        ):
            raise RuntimeError("active causal identity mismatch")
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
        retrieval_receipt = {"mode":"LEGACY_COMPATIBILITY","status":"UNKNOWN","truth_authority":False,"effect_authority":False}
        supplied = {"query":query,"turn_id":turn_id,"episode_id":episode_id,"causal_id":causal_id,"generation":generation}
        if not all(value is not None for value in supplied.values()):
            active = self._active_identity(session_id)
            if active is not None:
                supplied = active
        if all(value is not None for value in supplied.values()):
            result = self.microclay.retrieve(
                query=str(supplied["query"]), user_id=user_id, session_id=session_id,
                turn_id=str(supplied["turn_id"]), episode_id=str(supplied["episode_id"]),
                causal_id=str(supplied["causal_id"]), generation=int(supplied["generation"]),
            )
            memories = result["items"]
            retrieval_receipt = result["receipt"]
        else:
            memories = [dict(r) for r in self.db.db.execute(
                "SELECT * FROM durable_memory WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
                "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 50", (user_id,),
            )]
        return {"own_recent":own,"cross_session_collision":other,"durable_memory":memories,"retrieval_receipt":retrieval_receipt}

    def credit(self, *, causal_id, generation, credit, signal_class):
        return self.microclay.credit(causal_id=str(causal_id), generation=int(generation), credit=float(credit), signal_class=str(signal_class))
