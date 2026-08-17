from __future__ import annotations
import json

from .memory_classes import CONTROL_KINDS, METHOD_KINDS
from .method_memory import MethodMemory
from .microclay_retrieval import MicroClayRetrieval
from .store import UnifiedDB


class WorldAssembler:
    """Bounded two-stage world assembly with evidence/method separation.

    Stage A is MicroClay evidence retrieval. Stage B is optional structural method
    retrieval. Stage B can change how Claude investigates; it cannot change Stage-A
    PRESENT/UNKNOWN truth status or broaden cross-session privacy.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = MicroClayRetrieval(db)
        self.methods = MethodMemory(db)

    @staticmethod
    def _evidence_rows(rows, limit):
        excluded = CONTROL_KINDS | METHOD_KINDS
        return [dict(row) for row in rows if str(row["kind"]) not in excluded][:limit]

    def _extracted_fragments(self, turn_id):
        rows = self.db.db.execute(
            "SELECT kind,value,provenance FROM durable_memory WHERE source_turn_id=? ORDER BY ts LIMIT 100",
            (turn_id,),
        ).fetchall()
        return self._evidence_rows(rows, 20)

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
        # collides. Method retrieval never widens this boundary.
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
            "channel": "EVIDENCE_STAGE_A",
            "truth_authority": False,
            "effect_authority": False,
        }
        method_receipt = {
            "triggered": False,
            "status": "NOT_TRIGGERED",
            "channel": "METHOD_STAGE_B",
            "truth_authority": False,
            "effect_authority": False,
        }
        problem_signature = {}
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
            retrieval_receipt["channel"] = "EVIDENCE_STAGE_A"
            evidence_status = str(retrieval_receipt.get("status", "UNKNOWN")).upper()
            problem_signature = self.methods.derive_problem_signature(
                query=str(supplied["query"]),
                evidence_status=evidence_status,
                resource_refs=list(resource_refs or []),
                collision_count=len(other),
            )
            method_triggered = self.methods.should_activate(
                evidence_status=evidence_status,
                problem_signature=problem_signature,
            )
            if method_triggered:
                method_result = self.methods.retrieve(
                    problem_signature=problem_signature,
                    user_id=user_id,
                )
                method_context = method_result["methods"]
                counterevidence = method_result["counterevidence"]
                method_receipt = dict(method_result["receipt"])
                method_receipt.update({
                    "triggered": True,
                    "channel": "METHOD_STAGE_B",
                    "fact_status_unchanged": evidence_status,
                })
            else:
                method_receipt.update({
                    "fact_status_unchanged": evidence_status,
                    "problem_signature_present": True,
                })
            if evidence_status in {"UNKNOWN", "UNDERCOVERED"}:
                unknowns.append({
                    "kind": "evidence_gap",
                    "status": evidence_status,
                    "method_present": bool(method_context),
                    "truth_authority": False,
                })
        else:
            # Compatibility path for legacy tests/non-product callers with no active
            # causal turn. It is evidence-only and explicitly excludes method memory.
            rows = self.db.db.execute(
                "SELECT * FROM durable_memory WHERE (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 200",
                (user_id,),
            ).fetchall()
            memories = self._evidence_rows(rows, 50)
            unknowns.append({
                "kind": "evidence_gap",
                "status": "UNKNOWN",
                "method_present": False,
                "truth_authority": False,
            })

        return {
            "own_recent": own,
            "cross_session_collision": other,
            "durable_memory": memories,
            "retrieval_receipt": retrieval_receipt,
            "problem_signature": problem_signature,
            "method_context": method_context,
            "counterevidence": counterevidence,
            "unknowns": unknowns,
            "method_receipt": method_receipt,
        }

    def credit(self, *, causal_id, generation, credit, signal_class):
        return self.microclay.credit(
            causal_id=str(causal_id),
            generation=int(generation),
            credit=float(credit),
            signal_class=str(signal_class),
        )
