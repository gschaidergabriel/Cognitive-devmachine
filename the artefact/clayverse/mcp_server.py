from __future__ import annotations

import os
import time
import uuid
from pathlib import Path


class BridgeStateError(RuntimeError):
    pass


class ClayVerseBridge:
    """Stdio MCP bridge used by each permanent interactive Claude Code terminal."""

    def __init__(self, db, user_id: str, session_id: str, entityos_bridge=None):
        from .effects import EffectGate
        from .graph import ClayGraphProjection
        from .memory import MemoryManager
        from .retrieval import WorldAssembler
        from .workspace import Workspace

        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
            raise PermissionError("invalid terminal/session binding")
        db.assert_session_owner(session_id, user_id)
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.memory = MemoryManager(db)
        self.world = WorldAssembler(db)
        self.workspace = Workspace(db)
        self.effects = EffectGate(db, allow_process=False, entityos_bridge=entityos_bridge)
        self.graph = ClayGraphProjection(db)
        self.current: dict | None = None

    @classmethod
    def from_env(cls):
        from .entityos_bridge import EntityOSBridge
        from .identity import IdentityRouter
        from .store import UnifiedDB

        root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
        db = UnifiedDB(root / "unified.db")
        IdentityRouter(db, {})
        user_id = os.environ.get("CLAYVERSE_USER_ID", "")
        session_id = os.environ.get("CLAYVERSE_SESSION_ID", "")

        bridge = None
        enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        if enable_exec:
            path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
            sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
            if not path or not sha256:
                raise BridgeStateError("EntityOS execution enabled without complete digest binding")
            bridge = EntityOSBridge(path=path, sha256=sha256)
            bridge.verify()
        return cls(db, user_id, session_id, bridge)

    def begin_turn(self, text: str, resources: list[str] | None = None) -> dict:
        if self.current is not None:
            raise BridgeStateError("turn already open")
        text = str(text)
        if not text or len(text) > 100_000:
            raise ValueError("invalid turn text")
        resources = sorted(set(resources or []))
        if any(not isinstance(x, str) or len(x) > 1000 for x in resources):
            raise ValueError("invalid resource reference")

        tid = self.db.append_turn(
            self.session_id, self.user_id, "user", text,
            resources=resources,
            provenance={"source": "permanent-claude-terminal", "user_id": self.user_id},
        )
        self.memory.extract_explicit(tid, self.user_id, text)
        self.memory.compact(self.session_id)
        world = self.world.assemble(self.session_id, resources)
        ws = self.workspace.open(self.session_id, tid, text, resources)
        causal_id = str(uuid.uuid4())
        generation = self.db.session_generation(self.session_id)
        self.current = {
            "turn_id": tid,
            "episode_id": ws["episode_id"],
            "causal_id": causal_id,
            "generation": generation,
            "resources": resources,
            "effect_id": None,
            "outcome": None,
            "workspace_selected": False,
        }
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "turn_id": tid,
            "causal_id": causal_id,
            "generation": generation,
            "workspace": ws,
            "context": world,
        }

    def _bind_effect_causal_record(self, effect_id: str) -> str:
        causal_id = self.effects.causal_for_effect(effect_id)
        if causal_id is None:
            raise BridgeStateError("effect completed without causal journal re-entry")
        self.current["effect_id"] = effect_id
        self.current["causal_id"] = causal_id
        return causal_id

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        from .effects import EffectRequest

        if self.current is None:
            raise BridgeStateError("begin_turn required")
        if self.current["effect_id"] is not None:
            raise BridgeStateError("only one effect admitted per turn in candidate contract")
        if not self.current["workspace_selected"]:
            self.workspace.select(self.current["episode_id"], "request_effect")
            self.current["workspace_selected"] = True
        req = EffectRequest(
            self.user_id,
            self.session_id,
            capability,
            target,
            argv,
            self.current["generation"],
        )
        try:
            effect_id, outcome = self.effects.execute(req, self.current["episode_id"])
        except Exception:
            # If execution crossed the journal admission boundary, bind the failed
            # effect to this turn before propagating the error so the terminal cannot
            # silently request a second external attempt for the same open turn.
            row = self.db.db.execute(
                "SELECT effect_id FROM effects WHERE episode_id=? ORDER BY ts DESC LIMIT 1",
                (self.current["episode_id"],),
            ).fetchone()
            if row is not None:
                self._bind_effect_causal_record(row["effect_id"])
            raise
        causal_id = self._bind_effect_causal_record(effect_id)
        self.current["outcome"] = outcome
        return {"effect_id": effect_id, "causal_id": causal_id, "verified": True, "outcome": outcome}

    def complete_turn(self, response: str) -> dict:
        if self.current is None:
            raise BridgeStateError("begin_turn required")
        response = str(response)
        if len(response) > 200_000:
            raise ValueError("response too large")
        if not self.current["workspace_selected"]:
            self.workspace.select(self.current["episode_id"], "respond")
            self.current["workspace_selected"] = True

        effect_id = self.current["effect_id"]
        causal_id = self.current["causal_id"]
        if effect_id is not None:
            # EffectJournal already finalized exactly one causal re-entry. Reuse it;
            # never create a second causal_episodes row for the same external effect.
            row = self.db.db.execute(
                "SELECT causal_id,credit FROM causal_episodes WHERE effect_id=? ORDER BY ts DESC LIMIT 1",
                (effect_id,),
            ).fetchone()
            if row is None or row["causal_id"] != causal_id:
                raise BridgeStateError("effect causal journal binding lost")
            credit = float(row["credit"])
        else:
            credit = 0.0

        assistant_id = self.db.append_turn(
            self.session_id, self.user_id, "assistant", response,
            resources=self.current["resources"],
            causal_refs=[effect_id] if effect_id else [],
            provenance={"source": "permanent-claude-terminal", "causal_id": causal_id},
        )
        if effect_id is None:
            self.db.db.execute(
                "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
                (
                    causal_id, self.current["episode_id"], None,
                    self.current["turn_id"], None, 0.0, 1, time.time(),
                ),
            )
        self.memory.compact(self.session_id)
        self.graph.rebuild()
        result = {
            "assistant_turn_id": assistant_id,
            "causal_id": causal_id,
            "effect_id": effect_id,
            "credit": credit,
        }
        self.current = None
        return result


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseBridge.from_env()
    mcp = MCPServer(
        "ClayVerse",
        instructions="Canonical state/context/effect bridge for the authenticated permanent ClayVerse terminal.",
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    stateful = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    @mcp.tool(annotations=stateful)
    def begin_turn(text: str, resources: list[str] | None = None) -> dict:
        return bridge.begin_turn(text, resources)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=stateful)
    def complete_turn(response: str) -> dict:
        return bridge.complete_turn(response)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return {
            "user_id": bridge.user_id,
            "session_id": bridge.session_id,
            "generation": bridge.db.session_generation(bridge.session_id),
            "turn_open": bridge.current is not None,
        }

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
