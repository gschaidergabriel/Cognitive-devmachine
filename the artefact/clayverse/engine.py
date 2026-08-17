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
    def _inference_provenance(decision, generation):
        provenance = {
            "source": "inference-adapter",
            "entity_generation": int(generation),
        }
        provider = decision.get("provider")
        model = decision.get("model")
        if isinstance(provider, str) and 0 < len(provider) <= 128:
            provenance["provider"] = provider
        if isinstance(model, str) and 0 < len(model) <= 256:
            provenance["model"] = model
        return provenance

    def ingest(self, clerk_subject, content, *, resources=None):
        # One persistent ClayVerse entity has one causal turn frontier. Requests may
        # arrive through multiple authenticated surfaces, but observation -> cognition
        # / effect -> causal re-entry is serialized inside the engine itself.
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

        # The provider response is not authority by itself. Bind it back to the same
        # live ClayVerse generation and persist it in UnifiedDB before any requested
        # effect is allowed to cross EffectGate.
        self.db.assert_live_generation(sid, reasoning_generation)
        self.workspace.select(ws["episode_id"], decision.get("selection", "respond"))
        aid = self.db.append_turn(
            sid,
            uid,
            "assistant",
            decision.get("text", ""),
            resources=resources,
            provenance=self._inference_provenance(decision, reasoning_generation),
        )

        effect_id = None
        outcome = None
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

        # Causal effect identity/outcome only becomes known after EffectGate. Update
        # the already re-ingested provider turn with that causal reference and any
        # deterministic denial notice; do not create a parallel response ledger.
        if effect_id or decision.get("text", "") != str(
            self.db.db.execute(
                "SELECT content FROM turns WHERE turn_id=?", (aid,)
            ).fetchone()[0]
        ):
            with self.db.tx() as db:
                db.execute(
                    "UPDATE turns SET content=?, causal_refs=? WHERE turn_id=?",
                    (
                        decision.get("text", ""),
                        json.dumps([effect_id] if effect_id else []),
                        aid,
                    ),
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
            "workspace": ws,
            "decision": decision,
            "effect_id": effect_id,
            "outcome": outcome,
            "causal_id": causal_id,
            "collision_count": len(world["cross_session_collision"]),
        }
