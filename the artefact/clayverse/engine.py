from __future__ import annotations

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
from .store import StaleGeneration, UnifiedDB
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

    def _begin_engine_turn(self, uid, sid, content, resources):
        causal_id = str(uuid.uuid4())
        with self.db.tx() as db:
            if db.execute(
                "SELECT 1 FROM active_turns WHERE session_id=?", (sid,)
            ).fetchone() is not None:
                raise RuntimeError("canonical session already has an active turn")
            generation = self.db.session_generation(sid)
            self.db.assert_live_generation(sid, generation)
            tid = self.db.append_turn_in_tx(
                sid,
                uid,
                "user",
                content,
                resources=resources,
                provenance={"source": "clerk-terminal"},
                expected_generation=generation,
            )
            ws = self.workspace.open(sid, tid, content, resources)
            now = time.time()
            db.execute(
                "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    sid,
                    uid,
                    tid,
                    ws["episode_id"],
                    causal_id,
                    generation,
                    json.dumps(sorted(set(resources))),
                    None,
                    None,
                    0,
                    now,
                ),
            )
            # Memory extraction/compression are canonical writes derived from this user
            # turn. Keep them under the same BEGIN IMMEDIATE generation transaction so
            # recovery cannot advance the global generation between turn admission and
            # durable-memory mutation. Any memory failure rolls back the entire admitted
            # turn/workspace/active spine rather than leaving stale canonical memory.
            self.memory.extract_explicit(tid, uid, content)
            self.memory.compact(sid)
        return tid, ws, generation, causal_id

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
        tid, ws, reasoning_generation, causal_id = self._begin_engine_turn(
            uid, sid, content, resources
        )

        world = self.world.assemble(sid, resources)
        world["runtime_capabilities"] = list(self.effects.available_capabilities())
        decision = self.inference.reason(world, content)
        selection = decision.get("selection", "respond")
        eff = decision.get("effect")
        if bool(eff) != (selection == "request_effect"):
            raise RuntimeError("inference selection/effect intent mismatch")

        # SECURITY / CAUSALITY LAW:
        # Provider inference may overlap recovery/generation advancement. Workspace
        # selection and provider-response persistence therefore collapse atomically
        # under the generation captured before the provider call. If that generation
        # is stale, the whole post-inference mutation rolls back before EffectGate.
        with self.db.tx() as db:
            active = db.execute(
                "SELECT * FROM active_turns WHERE session_id=?", (sid,)
            ).fetchone()
            if (
                active is None
                or active["causal_id"] != causal_id
                or active["turn_id"] != tid
                or active["episode_id"] != ws["episode_id"]
                or int(active["generation"]) != int(reasoning_generation)
            ):
                raise StaleGeneration("engine_active_turn")
            self.workspace.select_in_tx(ws["episode_id"], selection)
            cur = db.execute(
                "UPDATE active_turns SET workspace_selected=? WHERE session_id=? AND causal_id=?",
                (1 if selection == "request_effect" else 0, sid, causal_id),
            )
            if cur.rowcount != 1:
                raise StaleGeneration("engine_active_turn")
            aid = self.db.append_turn_in_tx(
                sid,
                uid,
                "assistant",
                decision.get("text", ""),
                resources=resources,
                provenance=self._inference_provenance(
                    decision, reasoning_generation, ws["episode_id"]
                ),
                expected_generation=reasoning_generation,
            )
            if not eff:
                db.execute(
                    "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,0,1,?)",
                    (causal_id, ws["episode_id"], None, tid, None, time.time()),
                )
                # ClayGraph is derived/rebuildable, but a projection failure must not be
                # reported after the canonical turn has already retired its replay fence.
                # Rebuild before completion inside the same transaction: failure rolls
                # back this completion while the admitted active turn remains recoverable.
                self.graph.rebuild_in_tx()
                cur = db.execute(
                    "UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=? AND state='SELECTED'",
                    (ws["episode_id"],),
                )
                if cur.rowcount != 1:
                    raise RuntimeError("workspace did not terminalize after engine response")
                cur = db.execute(
                    "DELETE FROM active_turns WHERE session_id=? AND causal_id=?",
                    (sid, causal_id),
                )
                if cur.rowcount != 1:
                    raise StaleGeneration("engine_active_turn")

        effect_id = None
        outcome = None
        effect_notice_turn_id = None
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
            effect_causal_id = self.effects.causal_for_effect(effect_id)
            if effect_causal_id != causal_id:
                raise RuntimeError("effect re-entered through wrong causal identity")

            # The journal has durably re-entered the outcome. Terminalize the workspace
            # and retire the ephemeral active row only under the same live generation.
            # A crash or generation change before this commit intentionally leaves the
            # selected workspace + active row for canonical Recovery.
            with self.db.tx() as db:
                self.db.assert_live_generation(sid, reasoning_generation)
                active = db.execute(
                    "SELECT causal_id FROM active_turns WHERE session_id=?", (sid,)
                ).fetchone()
                if active is None or active["causal_id"] != causal_id:
                    raise StaleGeneration("engine_active_turn")
                causal = db.execute(
                    "SELECT effect_id FROM causal_episodes WHERE causal_id=? AND episode_id=?",
                    (causal_id, ws["episode_id"]),
                ).fetchone()
                if causal is None or causal["effect_id"] != effect_id:
                    raise RuntimeError("effect causal re-entry is missing or mismatched")
                if isinstance(outcome, dict) and outcome.get("denied") is True:
                    notice = (
                        "Requested action was not executed "
                        f"({outcome.get('reason', 'effect_denied')})."
                    )
                    effect_notice_turn_id = self.db.append_turn_in_tx(
                        sid,
                        uid,
                        "system",
                        notice,
                        resources=resources,
                        causal_refs=[effect_id],
                        provenance={
                            "source": "effect-gate",
                            "phase": "effect-outcome-reentry",
                            "reasoning_generation": int(reasoning_generation),
                            "workspace_episode_id": ws["episode_id"],
                        },
                        expected_generation=reasoning_generation,
                    )
                    decision = dict(decision)
                    prior = str(decision.get("text", "")).strip()
                    decision["text"] = f"{prior}\n\n{notice}" if prior else notice
                # The effect outcome is already durable at this point. Keep the derived
                # graph refresh inside the active-turn retirement transaction so a graph
                # fault cannot surface as a post-effect failure after the replay fence is
                # gone. On failure, Recovery sees the same causal re-entry and closes it
                # without re-executing the external effect.
                self.graph.rebuild_in_tx()
                cur = db.execute(
                    "UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=? AND state='SELECTED'",
                    (ws["episode_id"],),
                )
                if cur.rowcount != 1:
                    raise RuntimeError("workspace did not terminalize after effect re-entry")
                cur = db.execute(
                    "DELETE FROM active_turns WHERE session_id=? AND causal_id=?",
                    (sid, causal_id),
                )
                if cur.rowcount != 1:
                    raise StaleGeneration("engine_active_turn")

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
