from __future__ import annotations

import json
import os
from pathlib import Path


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Managed stdio MCP; hooks own turns and EffectGate owns real state changes."""

    METHOD_SIGNATURE_SOURCE = "clayverse:claude-explicit-mcp:v1"

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle
        self.db = lifecycle.db
        self.user_id = lifecycle.user_id
        self.session_id = lifecycle.session_id

    @classmethod
    def from_env(cls):
        from .entityos_bridge import EntityOSBridge
        from .identity import IdentityRouter
        from .store import UnifiedDB
        from .turn_lifecycle import TurnLifecycle

        root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
        db = UnifiedDB(root / "unified.db")
        IdentityRouter(db, {})
        user_id = os.environ.get("CLAYVERSE_USER_ID", "").strip()
        session_id = os.environ.get("CLAYVERSE_SESSION_ID", "").strip()

        entityos = None
        enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
        sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
        if enable_exec:
            if not path or not sha256 or not os.path.isabs(path):
                db.close()
                raise BridgeStateError("EntityOS execution enabled without complete digest binding")
            entityos = EntityOSBridge(path=path, sha256=sha256)
            entityos.verify()
        return cls(TurnLifecycle(db, user_id, session_id, entityos_bridge=entityos))

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        if capability not in {"entityos.exec", "state.noop"}:
            raise PermissionError("capability denied")
        if not isinstance(target, str) or not target or len(target) > 2048 or "\x00" in target:
            raise ValueError("invalid effect target")
        if capability == "entityos.exec":
            if not isinstance(argv, list) or not argv or len(argv) > 128:
                raise ValueError("entityos.exec requires bounded argv")
            if any(not isinstance(x, str) or not x or len(x) > 8192 or "\x00" in x for x in argv):
                raise ValueError("invalid effect argv")
        elif argv not in (None, []):
            raise ValueError("state.noop does not accept argv")
        else:
            argv = None
        result = self.lifecycle.request_effect(capability, target, argv)
        result["boundary"] = "ClayVerse EffectGate -> EntityOS" if capability == "entityos.exec" else "ClayVerse EffectGate"
        return result

    def session_state(self) -> dict:
        active = self.lifecycle.active()
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "generation": self.db.session_generation(self.session_id),
            "active_turn": {
                "turn_id": active["turn_id"],
                "episode_id": active["episode_id"],
                "causal_id": active["causal_id"],
                "generation": int(active["generation"]),
                "effect_id": active["effect_id"],
            } if active else None,
            "capabilities": self.lifecycle.effects.available_capabilities(),
            "entityos_execution_enabled": self.lifecycle.effects.entityos_bridge is not None,
            "turn_ingestion": "automatic_claude_hooks",
        }

    @staticmethod
    def _active_resource_refs(active) -> list[str]:
        try:
            refs = json.loads(str(active["resource_refs"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise BridgeStateError("active turn resource refs are invalid") from exc
        if not isinstance(refs, list) or len(refs) > 50:
            raise BridgeStateError("active turn resource refs violate canonical bound")
        if any(not isinstance(ref, str) or not ref or len(ref) > 2048 for ref in refs):
            raise BridgeStateError("active turn resource ref is invalid")
        return refs

    def method_context(
        self,
        problem_signature: dict[str, list[str]],
        goal_shape: str,
        trigger: str | None = None,
        limit: int = 4,
        budget_chars: int = 24_000,
    ) -> dict:
        """Admit one same-turn structural Stage-B query with bridge-owned provenance.

        The caller supplies only structural facets and routing intent. ClayVerse binds the
        canonical user/session/turn/episode/causal/generation and the producer class; the
        caller cannot supply or override those authority fields. The returned method context
        is advisory SHADOW context only and cannot change factual or effect authority.
        """
        from .method_stageb import QUERY_ADMISSION_VERSION, QUERY_SCHEMA, admit_problem_query

        with self.db.tx() as db:
            active = self.lifecycle.active()
            if active is None:
                raise BridgeStateError("method context requires an active canonical turn")
            if str(active["user_id"]) != self.user_id:
                raise BridgeStateError("active turn user identity diverged")
            generation = int(active["generation"])
            self.db.assert_session_owner(self.session_id, self.user_id)
            self.db.assert_live_generation(self.session_id, generation)
            refs = self._active_resource_refs(active)

            problem_query = {
                "schema": QUERY_SCHEMA,
                "problem_signature": problem_signature,
                "goal_shape": goal_shape,
                "provenance": {
                    "source": self.METHOD_SIGNATURE_SOURCE,
                    "turn_id": str(active["turn_id"]),
                    "episode_id": str(active["episode_id"]),
                    "causal_id": str(active["causal_id"]),
                    "generation": generation,
                    "admission_version": QUERY_ADMISSION_VERSION,
                },
            }
            admitted = admit_problem_query(problem_query)
            signature_receipt = admitted.receipt()

            world = self.lifecycle.world.assemble(
                self.session_id,
                refs,
                method_query=problem_query,
                method_trigger=trigger,
                method_limit=limit,
                method_budget_chars=budget_chars,
            )
            method_receipt = dict(world.get("method_receipt") or {})
            if method_receipt.get("truth_authority") is not False or method_receipt.get("effect_authority") is not False:
                raise BridgeStateError("Stage-B context attempted to gain authority")
            if method_receipt.get("signature_sha256") != signature_receipt["signature_sha256"]:
                raise BridgeStateError("Stage-B receipt does not bind admitted signature")

            durable = db.execute(
                "SELECT problem_signature_hash,query_schema,admission_version,turn_id,episode_id,session_id,user_id,generation "
                "FROM method_use_receipts WHERE causal_id=?",
                (str(active["causal_id"]),),
            ).fetchone()
            if durable is None:
                raise BridgeStateError("Stage-B request receipt was not persisted")
            if (
                str(durable["problem_signature_hash"]) != signature_receipt["signature_sha256"]
                or str(durable["query_schema"]) != QUERY_SCHEMA
                or int(durable["admission_version"]) != QUERY_ADMISSION_VERSION
                or str(durable["turn_id"]) != str(active["turn_id"])
                or str(durable["episode_id"]) != str(active["episode_id"])
                or str(durable["session_id"]) != self.session_id
                or str(durable["user_id"]) != self.user_id
                or int(durable["generation"]) != generation
            ):
                raise BridgeStateError("durable Stage-B receipt identity diverged")

            return {
                "method_context": list(world.get("method_context") or []),
                "counterevidence": list(world.get("counterevidence") or []),
                "unknowns": list(world.get("unknowns") or []),
                "retrieval_receipt": dict(world.get("retrieval_receipt") or {}),
                "method_receipt": method_receipt,
                "signature_receipt": signature_receipt,
                "truth_authority": False,
                "effect_authority": False,
                "served_automatically": False,
            }


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseEffectBridge.from_env()
    mcp = MCPServer(
        "ClayVerse",
        instructions=(
            "UserPromptSubmit and Stop hooks own turn ingestion/context/completion automatically. "
            "Use method_context only for an explicit same-turn structural method query; its output is advisory SHADOW context, never factual or effect authority. "
            "Use request_effect only for a real external/state-changing action; never bypass it with host execution."
        ),
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    receipt_writing_read = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return bridge.session_state()

    @mcp.tool(annotations=receipt_writing_read)
    def method_context(
        problem_signature: dict[str, list[str]],
        goal_shape: str,
        trigger: str | None = None,
        limit: int = 4,
        budget_chars: int = 24_000,
    ) -> dict:
        return bridge.method_context(problem_signature, goal_shape, trigger, limit, budget_chars)

    try:
        mcp.run(transport="stdio")
    finally:
        bridge.db.close()


if __name__ == "__main__":
    main()
