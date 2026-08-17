from __future__ import annotations

import hashlib
import json
import time
import uuid

from .effects import EffectGate, EffectRequest
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
    def __init__(self, db: UnifiedDB, clerk_map, inference=None, allow_process=False):
        self.db = db
        self.identity = IdentityRouter(db, clerk_map)
        self.memory = MemoryManager(db)
        self.world = WorldAssembler(db)
        self.workspace = Workspace(db)
        self.effects = EffectGate(db, allow_process)
        self.graph = ClayGraphProjection(db)
        self.inference = inference or DeterministicTestInference()

    def ingest(self, clerk_subject, content, *, resources=None, request_id=None):
        resources = resources or []
        uid, sid = self.identity.resolve(clerk_subject)
        tid = self.db.append_turn(
            sid,
            uid,
            "user",
            content,
            resources=resources,
            provenance={"source": "clerk-terminal", "request_id": request_id},
        )
        self.memory.extract_explicit(tid, uid, content)
        self.memory.compact(sid)
        world = self.world.assemble(sid, resources)
        ws = self.workspace.open(sid, tid, content, resources)
        decision = self.inference.reason(world, content)
        self.workspace.select(ws["episode_id"], decision.get("selection", "respond"))

        effect_id = None
        outcome = None
        eff = decision.get("effect")
        if eff:
            if not request_id:
                raise ValueError("request_id required for effectful requests")
            effect_id, outcome = self.effects.execute(
                EffectRequest(
                    uid,
                    sid,
                    eff["capability"],
                    eff["target"],
                    eff.get("argv"),
                    request_key=f"{uid}:{request_id}:effect:0",
                ),
                ws["episode_id"],
            )

        aid = self.db.append_turn(
            sid,
            uid,
            "assistant",
            decision.get("text", ""),
            resources=resources,
            causal_refs=[effect_id] if effect_id else [],
            provenance={"source": "inference-adapter", "request_id": request_id},
        )
        causal_id = str(uuid.uuid4())
        out_hash = (
            hashlib.sha256(json.dumps(outcome, sort_keys=True).encode()).hexdigest()
            if outcome is not None
            else None
        )
        # Every workspace decision causally re-enters canonical state. A
        # captured failed effect is still an observation, but earns no
        # positive success credit.
        credit = 1.0 if outcome is not None and bool(outcome.get("ok")) else 0.0
        self.db.db.execute(
            "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
            (
                causal_id,
                ws["episode_id"],
                effect_id,
                tid,
                out_hash,
                credit,
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
