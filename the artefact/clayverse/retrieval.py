from __future__ import annotations
import json
from .method_memory import MethodMemoryRetriever
from .microclay_retrieval import MicroClayRetrieval
from .store import UnifiedDB


class WorldAssembler:
    """Bounded world assembly with factual MicroClay retrieval plus shadow Stage-B evaluation."""

    CONTROL_MEMORY_KINDS = ("source_archive", "compression_receipt", "compression_clearance")

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = MicroClayRetrieval(db)
        self.methods = MethodMemoryRetriever(db)

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

    @staticmethod
    def _evidence_context(items):
        out = []
        for item in items:
            value = dict(item)
            value["context_class"] = "evidence_context"
            value["retrieval_is_truth_authority"] = False
            out.append(value)
        return out

    @staticmethod
    def _unknown_context(fact_status):
        status = str(fact_status).upper()
        if status == "PRESENT":
            return []
        return [{
            "memory_id": "runtime:fact-status",
            "kind": "runtime_unknown",
            "subject": "fact_status",
            "value": status,
            "context_class": "unknowns",
            "truth_authority": False,
            "effect_authority": False,
        }]

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
        # collides. Method retrieval cannot broaden this privacy/attention boundary.
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
            "method_status": "NOT_SERVED",
            "method_shadow_status": "NOT_EVALUATED",
            "method_triggered": False,
            "method_count": 0,
            "method_shadow_count": 0,
            "counterevidence_count": 0,
            "counterevidence_shadow_count": 0,
            "method_policy_mode": "SHADOW",
            "method_served": False,
            "truth_authority": False,
            "effect_authority": False,
        }
        evidence_context = []
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
            factual = self.microclay.retrieve(
                query=str(supplied["query"]),
                user_id=user_id,
                session_id=session_id,
                turn_id=str(supplied["turn_id"]),
                episode_id=str(supplied["episode_id"]),
                causal_id=str(supplied["causal_id"]),
                generation=int(supplied["generation"]),
            )
            evidence_context = self._evidence_context(factual["items"])
            retrieval_receipt = dict(factual["receipt"])
            fact_status = str(retrieval_receipt.get("status", "UNKNOWN")).upper()
            methods = self.methods.retrieve(
                query=str(supplied["query"]),
                user_id=user_id,
                fact_status=fact_status,
            )
            policy_mode = str(methods.get("policy_mode", "")).upper()
            if policy_mode != "SHADOW":
                # ACTIVE serving is not admitted until causal method-use receipts bind
                # request identity, replay, generation and downstream verified utility.
                raise RuntimeError("method serving requires admitted causal receipt gate")

            # SHADOW may measure/rank methods, but it must not alter the context delivered
            # to Claude. Only compact observation counts enter the factual retrieval receipt.
            shadow_method_count = len(methods.get("items", []))
            shadow_counter_count = len(methods.get("counterevidence", []))
            method_context = []
            counterevidence = []
            unknowns = self._unknown_context(fact_status)
            retrieval_receipt.update({
                "fact_status": fact_status,
                "method_triggered": bool(methods["triggered"]),
                "method_status": "NOT_SERVED",
                "method_shadow_status": str(methods["method_status"]),
                "method_count": 0,
                "method_shadow_count": shadow_method_count,
                "counterevidence_count": 0,
                "counterevidence_shadow_count": shadow_counter_count,
                "method_policy_mode": policy_mode,
                "method_served": False,
                "method_invalid_count": len(methods.get("invalid_method_ids", [])),
            })
            # TurnLifecycle packs durable_memory into Claude context. SHADOW observations
            # therefore stay out of this carrier entirely.
            memories = evidence_context + unknowns
        else:
            # Compatibility path for legacy tests/non-product callers with no active
            # causal turn. Product Claude hooks always have an active turn here.
            evidence_context = [
                dict(r)
                for r in self.db.db.execute(
                    "SELECT * FROM durable_memory WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
                    "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 50",
                    (user_id,),
                )
            ]
            evidence_context = self._evidence_context(evidence_context)
            memories = evidence_context
            unknowns = self._unknown_context("UNKNOWN")

        return {
            "own_recent": own,
            "cross_session_collision": other,
            "durable_memory": memories,
            "evidence_context": evidence_context,
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