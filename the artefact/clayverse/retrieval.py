from __future__ import annotations
import json
from .method_stageb import AdmittedMethodRetriever
from .microclay_retrieval import MicroClayRetrieval
from .store import UnifiedDB


class WorldAssembler:
    """Bounded Stage-A evidence assembly plus optional admitted structural Stage B.

    Raw prompt text is never used as the canonical Stage-B method query. A caller must
    provide an explicit `method_query` that has the typed structural query shape enforced
    by `AdmittedMethodRetriever`. The normal TurnLifecycle currently provides no such
    object, so Stage B stays fail-closed until structural-signature derivation/admission is
    wired as a separate canonical subsystem.
    """

    CONTROL_MEMORY_KINDS = ("source_archive", "compression_receipt", "compression_clearance")

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = MicroClayRetrieval(db)
        self.methods = AdmittedMethodRetriever(db)

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
        method_query=None,
    ):
        session = self.db.db.execute(
            "SELECT user_id FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if not session:
            raise KeyError(session_id)
        user_id = session["user_id"]
        own = [dict(r) for r in self.db.recent_turns(session_id, 20)]

        # Another permanent perspective is loaded only when an explicit shared resource
        # collides. Neither Stage A nor Stage B may broaden this privacy/attention boundary.
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
            "fact_status": "UNKNOWN",
            "method_route": "NOT_EVALUATED",
            "method_status": "NOT_EVALUATED",
            "method_count": 0,
            "counterevidence_count": 0,
            "method_truth_authority": False,
            "method_effect_authority": False,
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
            fact_status = str(retrieval_receipt.get("status", "UNKNOWN")).upper()
            retrieval_receipt.update({
                "fact_status": fact_status,
                "method_route": "DEFERRED_NO_ADMITTED_SIGNATURE" if method_query is None else "STRUCTURAL_ADMISSION_PENDING",
                "method_status": "NOT_EVALUATED",
                "method_count": 0,
                "counterevidence_count": 0,
                "method_truth_authority": False,
                "method_effect_authority": False,
            })

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
                )
                method_context = list(methods["items"])
                counterevidence = list(methods["counterevidence"])
                method_receipt = methods["receipt"]
                retrieval_receipt.update({
                    "method_route": str(method_receipt["route"]),
                    "method_status": str(method_receipt["method_status"]),
                    "method_count": int(method_receipt["selected_count"]),
                    "counterevidence_count": int(method_receipt["counterevidence_count"]),
                    "method_policy_mode": str(method_receipt["policy_mode"]),
                    "method_query_schema": str(method_receipt["query_schema"]),
                    "method_query_sha256": str(method_receipt["query_sha256"]),
                    "method_truth_authority": False,
                    "method_effect_authority": False,
                })

            if fact_status != "PRESENT":
                unknowns = [{
                    "status": "FACT_UNKNOWN",
                    "query_sha256": retrieval_receipt.get("query_sha256"),
                    "method_present": bool(method_context),
                    "fact_status_unchanged": True,
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
