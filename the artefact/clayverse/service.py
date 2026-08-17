from __future__ import annotations

import json
import os
import sys

from .adapters import ClerkConfig, ClerkTokenVerifier
from .entityos_bridge import EntityOSBridge, EntityOSIntegrityError
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .readiness import claude_readiness
from .recovery import recover_incomplete_episodes
from .store import UnifiedDB
from .terminal_gateway import create_terminal_app
from .terminal_sessions import TerminalSessionManager


def _clerk_map() -> dict[str, str]:
    raw = os.environ.get("CLAYVERSE_CLERK_MAP_JSON", "")
    if not raw:
        raise RuntimeError("CLAYVERSE_CLERK_MAP_JSON is required")
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("CLAYVERSE_CLERK_MAP_JSON is invalid JSON") from exc
    if not isinstance(mapping, dict) or not mapping:
        raise RuntimeError("CLAYVERSE_CLERK_MAP_JSON must be a non-empty object")
    if any(not isinstance(k, str) or v not in {"gabriel", "andreas"} for k, v in mapping.items()):
        raise RuntimeError("Clerk mapping may only target gabriel/andreas")
    if set(mapping.values()) != {"gabriel", "andreas"}:
        raise RuntimeError("Clerk mapping must identify both canonical users")
    return mapping


def _web_config() -> tuple[str, str]:
    publishable_key = os.environ.get("CLERK_PUBLISHABLE_KEY", "").strip()
    frontend_api = os.environ.get("CLERK_FRONTEND_API_URL", "").strip().rstrip("/")
    if not publishable_key or not frontend_api:
        raise RuntimeError("CLERK_PUBLISHABLE_KEY and CLERK_FRONTEND_API_URL are required")
    if not frontend_api.startswith("https://"):
        raise RuntimeError("CLERK_FRONTEND_API_URL must use https")
    return publishable_key, frontend_api


def _entityos_config() -> tuple[EntityOSBridge | None, dict[str, object]]:
    # The single-container artifact always carries digest-bound EntityOS bytes once
    # built. Execution authority remains a separate fail-closed gate until the exact
    # embedded artifact has the required acceptance evidence.
    enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
    path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
    sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
    if not path or not sha256:
        raise RuntimeError("embedded EntityOS path and SHA-256 are required")
    if not os.path.isabs(path):
        raise RuntimeError("CLAYVERSE_ENTITYOS_PATH must be absolute")

    candidate = EntityOSBridge(path=path, sha256=sha256)
    try:
        verified = candidate.verify()
    except (EntityOSIntegrityError, OSError, ValueError) as exc:
        raise RuntimeError(f"EntityOS verification failed: {exc}") from exc
    status = {
        "staged": True,
        "verified": True,
        "execution_enabled": enable_exec,
        **verified,
    }
    return (candidate if enable_exec else None), status


def _state_probe_payload(checkpoint: str, state_hash: str) -> dict[str, object]:
    """Describe the bounded --once probe without implying product readiness."""
    return {
        "service": "clayverse",
        "status": "probe_ok",
        "scope": "state_only",
        "ready": False,
        "checkpoint": checkpoint,
        "state_hash": state_hash,
    }


def main():
    import uvicorn

    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    os.makedirs(state_root, exist_ok=True)
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})
    recovery = recover_incomplete_episodes(db)
    ClayGraphProjection(db).rebuild()
    cid, digest = db.checkpoint("boot")

    if "--once" in sys.argv:
        print(json.dumps(_state_probe_payload(cid, digest)), flush=True)
        db.close()
        return 0

    clerk_map = _clerk_map()
    publishable_key, frontend_api = _web_config()
    verifier = ClerkTokenVerifier(ClerkConfig.from_env())
    require_claude = os.environ.get("CLAYVERSE_REQUIRE_CLAUDE", "1") == "1"
    try:
        claude_status = claude_readiness(required=require_claude)
        _, entityos_status = _entityos_config()
        terminals = TerminalSessionManager(state_root, os.environ.get("CLAYVERSE_WORKSPACE", "/workspace"))
        terminal_status = {}
        for user_id in ("gabriel", "andreas"):
            binding = terminals.ensure(user_id)
            terminal_status[user_id] = {
                "session_id": binding.session_id,
                "tmux_name": binding.tmux_name,
                "home": str(binding.home),
            }
    except Exception:
        db.close()
        raise

    app = create_terminal_app(
        db=db,
        clerk_map=clerk_map,
        verifier=verifier,
        state_root=state_root,
        publishable_key=publishable_key,
        frontend_api_url=frontend_api,
    )
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "3000"))
    print(json.dumps({
        "service": "clayverse",
        "status": "candidate_ready",
        "surface": "clerk-browser-pty-normal-claude-code-cli",
        "state_root": state_root,
        "checkpoint": cid,
        "state_hash": digest,
        "users": ["gabriel", "andreas"],
        "rights": "equal",
        "claude_code": claude_status.as_dict(),
        "terminals": terminal_status,
        "auth": "clerk",
        "recovery": recovery,
        "entityos": entityos_status,
        "consciousness_daemon": False,
        "port": port,
    }), flush=True)

    try:
        uvicorn.run(app, host=host, port=port, workers=1, access_log=False)
    finally:
        db.checkpoint("shutdown")
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
