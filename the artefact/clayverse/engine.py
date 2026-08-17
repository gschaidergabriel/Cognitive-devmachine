from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid

from .agency import AgencyState
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
        self.agency = AgencyState(db)
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
            provenance["inference_receipt"] = receipt
        return provenance

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
        # Identity/goals/autonomy are canonical state, not prose instructions. Every
        # inference receives the same grounded snapshot derived from UnifiedDB.
        world["agency"] = self.agency.snapshot(max_goals=8, max_attempts_per_milestone=5)
        world["runtime_capabilities"] = list(self.effects.available_capabilities())
        ws = self.workspace.open(sid, tid, content, resources)
        reasoning_generation = self.db.session_generation(sid)
        decision = self.inference.reason(world, content)
        self.workspace.select(ws["episode_id"], decision.get("selection", "respond"))

        # SECURITY / CAUSALITY LAW:
        # The model/provider response is canonicalized into UnifiedDB before any
        # requested external/state-changing effect is allowed to reach EffectGate.
        # This prevents a provider from becoming a direct action authority and makes
        # the exact proposal observable under the same session/generation even if the
        # subsequent effect is denied, fails, or crashes.
        aid = self.db.append_turn(
            sid,
            uid,
            "assistant",
            decision.get("text", ""),
            resources=resources,
            provenance=self._inference_provenance(
                decision, reasoning_generation, ws["episode_id"]
            ),
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
