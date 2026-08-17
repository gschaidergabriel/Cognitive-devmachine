from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid

from .effects import EffectGate, EffectRequest
from .entityos_bridge import EntityOSBridge
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .memory import MemoryManager
from .retrieval import WorldAssembler
from .store import UnifiedDB
from .workspace import Workspace


class InferenceAdapter:
    def reason(self, world, observation):
        raise NotImplementedError


class DeterministicTestInference(InferenceAdapter):
    def reason(self, world, observation):
        return {"text": f"ack:{observation}", "selection": "respond", "effect": None}


class ClayVerseEngine:
    def __init__(
        self,
        db: UnifiedDB,
        clerk_map,
        inference=None,
        allow_process=False,
        entityos_bridge: EntityOSBridge | None = None,
    ):
        self.db = db
        self.identity = IdentityRouter(db, clerk_map)
        self.memory = MemoryManager(db)
        self.world = WorldAssembler(db)
        self.workspace = Workspace(db)
        self.effects = EffectGate(db, allow_process, entityos_bridge)
        self.graph = ClayGraphProjection(db)
        self.inference = inference or DeterministicTestInference()
        self._turn_lock = threading.RLock()

    @staticmethod
    def _causal_credit(outcome):
        return 1.0 if isinstance(outcome, dict) and outcome.get("ok") is True else 0.0

    @staticmethod
    def _inference_provenance(decision, reasoning_generation, episode_id):
        """Build non-secret provenance for the pre-effect model-response re-ingest."""
        provenance = {
            "source": "inference-adapter",
            "phase": "pre-effect-reingest",
            "reasoning_generation": int(reasoning_generation),
            "workspace_episode_id": episode_id,
        }
        receipt = decision.get("inference_receipt") if isinstance(decision, dict) else None
        if isinstance(receipt, dict):
            # Provider adapters may attach non-secret identity/digest metadata only.
            # UnifiedDB serialisation remains the independent fail-closed boundary.
            provenance["inference_receipt"] = receipt
        return provenance

    def _reingest_inference_if_live(
        self,
        sid,
        uid,
        decision,
        resources,
        reasoning_generation,
        episode_id,
    ):
        """Atomically fence generation, select workspace and persist model output.

        Inference may block on an external provider while recovery advances the one
        global entity generation. The response must therefore be generation-checked
        *after* inference and in the same write transaction that makes it canonical.
        BEGIN IMMEDIATE prevents another generation advance from interleaving between
        the live-generation check and this response re-ingest.
        """
        with self.db.tx() as db:
            self.db.assert_live_generation(sid, reasoning_generation)
            self.workspace.select_in_tx(
                episode_id, decision.get("selection", "respond")
            )
            self.db.assert_session_owner(sid, uid)
            ordinal = int(
                db.execute(
                    "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",
                    (sid,),
                ).fetchone()[0]
            )
            aid = str(uuid.uuid4())
            now = time.time()
            db.execute(
                "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    aid,
                    sid,
                    uid,
                    ordinal,
                    now,
                    "assistant",
                    str(decision.get("text", "")),
                    json.dumps(sorted(set(resources))),
                    "[]",
                    json.dumps(
                        self._inference_provenance(
                            decision, reasoning_generation, episode_id
                        ),
                        sort_keys=True,
                    ),
                ),
            )
            db.execute(
                "UPDATE sessions SET updated_at=? WHERE session_id=?", (now, sid)
            )
        return aid

    def ingest(self, clerk_subject, content, *, resources=None):
        # One persistent ClayVerse entity has one causal turn frontier. Requests may
        # arrive through multiple authenticated surfaces, but observation -> cognition
        # -> model-response re-ingest -> effect -> causal outcome re-entry is serialized
        # inside the engine itself.
        with self._turn_lock:
            return self._ingest_locked(clerk_subject, content, resources=resources)

    def _ingest_locked(self, clerk_subject, content, *, resources=None):
        resources = resources or []
        uid, sid = self.identity.resolve(clerk_subject)
        tid = self.db.append_turn(
            sid,
            uid,
            "user",
            content,
            resources=resources,
            provenance={"source": "clerk-terminal"},
        )
        self.memory.extract_explicit(tid, uid, content)
        self.memory.compact(sid)

        world = self.world.assemble(sid, resources)
        world["runtime_capabilities"] = list(self.effects.available_capabilities())
        ws = self.workspace.open(sid, tid, content, resources)
        reasoning_generation = self.db.session_generation(sid)
        decision = self.inference.reason(world, content)

        # SECURITY / CAUSALITY LAW:
        # The model/provider response is canonicalized into UnifiedDB before any
        # requested external/state-changing effect is allowed to reach EffectGate.
        # The live generation is re-checked after the potentially slow provider call
        # and atomically with workspace selection + response insertion. A response
        # from a pre-recovery generation can therefore never become canonical merely
        # because it carries no effect (or before a later EffectGate fence rejects it).
        aid = self._reingest_inference_if_live(
            sid,
            uid,
            decision,
            resources,
            reasoning_generation,
            ws["episode_id"],
        )

        effect_id = None
        outcome = None
        effect_notice_turn_id = None
        eff = decision.get("effect")
        if eff:
            effect_id, outcome = self.effects.execute(
                EffectRequest(
                    uid,
                    sid,
                    eff["capability"],
                    eff["target"],
                    eff.get("argv"),
                    reasoning_generation,
                ),
                ws["episode_id"],
            )

        if isinstance(outcome, dict) and outcome.get("denied") is True:
            decision = dict(decision)
            notice = (
                "Requested action was not executed "
                f"({outcome.get('reason', 'effect_denied')})."
            )
            prior = str(decision.get("text", "")).strip()
            decision["text"] = f"{prior}\n\n{notice}" if prior else notice
            effect_notice_turn_id = self.db.append_turn(
                sid,
                uid,
                "system",
                notice,
                resources=resources,
                causal_refs=[effect_id] if effect_id else [],
                provenance={
                    "source": "effect-gate",
                    "phase": "effect-outcome-reentry",
                    "reasoning_generation": int(reasoning_generation),
                    "workspace_episode_id": ws["episode_id"],
                },
            )

        causal_id = self.effects.causal_for_effect(effect_id) if effect_id else None
        if causal_id is None:
            causal_id = str(uuid.uuid4())
            out_hash = (
                hashlib.sha256(json.dumps(outcome, sort_keys=True).encode()).hexdigest()
                if outcome is not None
                else None
            )
            self.db.db.execute(
                "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
                (
                    causal_id,
                    ws["episode_id"],
                    effect_id,
                    tid,
                    out_hash,
                    self._causal_credit(outcome),
                    1,
                    time.time(),
                ),
            )

        self.graph.rebuild()
        return {
            "user_id": uid,
            "session_id": sid,
            "turn_id": tid,
            "assistant_turn_id": aid,
            "effect_notice_turn_id": effect_notice_turn_id,
            "workspace": ws,
            "decision": decision,
            "effect_id": effect_id,
            "outcome": outcome,
            "causal_id": causal_id,
            "collision_count": len(world["cross_session_collision"]),
        }
