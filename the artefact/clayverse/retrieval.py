from __future__ import annotations
import json

from .method_memory import METHOD_KINDS
from .method_stageb import AdmittedMethodRetriever
from .microclay_retrieval import MicroClayRetrieval
from .store import StaleGeneration, UnifiedDB


class WorldAssembler:
    """One Stage-A evidence path plus one explicitly admitted SHADOW Stage-B path."""

    CONTROL_MEMORY_KINDS = ("source_archive", "compression_receipt", "compression_clearance")

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = MicroClayRetrieval(db)
        self.methods = AdmittedMethodRetriever(db)

    def _extracted_fragments(self, turn_id):
        excluded = tuple(sorted(set(self.CONTROL_MEMORY_KINDS) | set(METHOD_KINDS)))
        rows = self.db.db.execute(
            "SELECT kind,value,provenance FROM durable_memory "
            "WHERE source_turn_id=? "
            f"AND kind NOT IN ({','.join('?' for _ in excluded)}) "
            "ORDER BY ts LIMIT 20",
            (turn_id, *excluded),
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

    @staticmethod
    def _identity_value_matches(field, supplied, active):
        if field == "generation":
            try:
                return int(supplied) == int(active)
            except (TypeError, ValueError):
                return False
        return str(supplied) == str(active)

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
        method_query=None,
        method_trigger=None,
        method_limit=4,
        method_budget_chars=24_000,
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

        retrieval_receipt = {
            "mode": "LEGACY_COMPATIBILITY",
            "status": "UNKNOWN",
            "truth_authority": False,
            "effect_authority": False,
        }
        method_receipt = {
            "route": "method_structural_admitted",
            "mode": "SHADOW_METHOD_V1",
            "status": "METHOD_NOT_REQUESTED",
            "truth_authority": False,
            "effect_authority": False,
            "served": False,
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
        supplied_any = any(value is not None for value in supplied.values())
        supplied_all = all(value is not None for value in supplied.values())
        if not supplied_all:
            active = self._active_identity(session_id)
            if active is not None:
                if supplied_any:
                    for field, value in supplied.items():
                        if value is None:
                            continue
                        if not self._identity_value_matches(field, value, active[field]):
                            raise StaleGeneration(f"active_turn_identity:{field}")
                    supplied = {
                        field: active[field] if value is None else value
                        for field, value in supplied.items()
                    }
                else:
                    supplied = active
            elif supplied_any:
                raise StaleGeneration("partial_turn_identity_without_active_turn")

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
            fact_status = str(retrieval_receipt.get("status", "UNKNOWN")).upper()

            if method_query is not None:
                methods = self.methods.retrieve(
                    problem_query=method_query,
                    user_id=user_id,
                    session_id=session_id,
                    turn_id=str(supplied["turn_id"]),
                    episode_id=str(supplied["episode_id"]),
                    causal_id=str(supplied["causal_id"]),
                    generation=int(supplied["generation"]),
                    fact_status=fact_status,
                    resource_refs=list(resource_refs or []),
                    trigger=method_trigger,
                    limit=int(method_limit),
                    budget_chars=int(method_budget_chars),
                )
                method_context = list(methods["items"])
                counterevidence = list(methods["counterevidence"])
                method_receipt = dict(methods["receipt"])
            elif fact_status != "PRESENT":
                method_receipt = {
                    "route": "method_structural_admitted",
                    "mode": "SHADOW_METHOD_V1",
                    "status": "METHOD_NOT_SERVED_SIGNATURE_ADMISSION_REQUIRED",
                    "causal_id": str(supplied["causal_id"]),
                    "generation": int(supplied["generation"]),
                    "truth_authority": False,
                    "effect_authority": False,
                    "served": False,
                }

            if fact_status != "PRESENT":
                unknowns = [{
                    "status": "FACT_UNKNOWN",
                    "query_sha256": retrieval_receipt.get("query_sha256"),
                    "method_present": bool(method_context),
                    "fact_status_unchanged": True,
                }]
        else:
            excluded = tuple(sorted(set(self.CONTROL_MEMORY_KINDS) | set(METHOD_KINDS)))
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
            "method_receipt": method_receipt,
        }

    def credit(self, *, causal_id, generation, credit, signal_class):
        return self.microclay.credit(
            causal_id=str(causal_id),
            generation=int(generation),
            credit=float(credit),
            signal_class=str(signal_class),
        )
