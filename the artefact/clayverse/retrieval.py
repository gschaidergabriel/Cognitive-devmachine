from __future__ import annotations
import json
from .microclay import MicroClayRetrieval
from .store import UnifiedDB


class WorldAssembler:
    """Assemble bounded context with collision-triggered cross-session fragments only."""

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

    def assemble(self, session_id, resource_refs):
        session = self.db.db.execute(
            "SELECT user_id FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if not session:
            raise KeyError(session_id)
        user_id = session["user_id"]
        decision = self.microclay.decision(session_id, user_id, resource_refs)
        limits = decision["limits"]
        own_limit = int(limits["own_turn_window"])
        cross_limit = int(limits["cross_session_limit"])
        memory_limit = int(limits["memory_limit"])

        own = [dict(r) for r in self.db.recent_turns(session_id, own_limit)]
        other = []
        if resource_refs and cross_limit > 0:
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
                    if len(other) >= cross_limit:
                        break
        memories = [
            dict(r)
            for r in self.db.db.execute(
                "SELECT * FROM durable_memory WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
                "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT ?",
                (user_id, memory_limit),
            )
        ]
        return {
            "own_recent": own,
            "cross_session_collision": other,
            "durable_memory": memories,
            "retrieval_policy": decision,
        }
