from __future__ import annotations

import json
import os
import signal
import sys
from http.server import ThreadingHTTPServer

from .adapters import ClerkConfig, ClerkTokenVerifier, ClaudeCodeInference
from .api import ClayVerseAPI
from .engine import ClayVerseEngine
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .store import UnifiedDB


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
    return mapping


def _web_config() -> tuple[str, str]:
    publishable_key = os.environ.get("CLERK_PUBLISHABLE_KEY", "").strip()
    frontend_api = os.environ.get("CLERK_FRONTEND_API_URL", "").strip().rstrip("/")
    if not publishable_key or not frontend_api:
        raise RuntimeError("CLERK_PUBLISHABLE_KEY and CLERK_FRONTEND_API_URL are required")
    if not frontend_api.startswith("https://"):
        raise RuntimeError("CLERK_FRONTEND_API_URL must use https")
    return publishable_key, frontend_api


def main():
    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    os.makedirs(state_root, exist_ok=True)
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})
    ClayGraphProjection(db).rebuild()
    cid, digest = db.checkpoint("boot")

    if "--once" in sys.argv:
        print(json.dumps({"service": "clayverse", "status": "ok", "checkpoint": cid, "state_hash": digest}), flush=True)
        db.close()
        return 0

    clerk_map = _clerk_map()
    publishable_key, frontend_api = _web_config()
    verifier = ClerkTokenVerifier(ClerkConfig.from_env())
    inference = ClaudeCodeInference()
    require_claude = os.environ.get("CLAYVERSE_REQUIRE_CLAUDE", "1") == "1"
    claude_available = inference.available()
    if require_claude and not claude_available:
        db.close()
        raise RuntimeError("Claude Code CLI is required but unavailable")

    engine = ClayVerseEngine(db, clerk_map, inference=inference, allow_process=False)
    api = ClayVerseAPI(engine, verifier, publishable_key=publishable_key, frontend_api_url=frontend_api)
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "3000"))
    server = ThreadingHTTPServer((host, port), api.handler())
    server.timeout = 1.0
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(json.dumps({
        "service": "clayverse",
        "status": "ready",
        "state_root": state_root,
        "checkpoint": cid,
        "state_hash": digest,
        "users": ["gabriel", "andreas"],
        "claude_code": claude_available,
        "auth": "clerk",
        "port": port,
    }), flush=True)

    try:
        while running:
            server.handle_request()
    finally:
        server.server_close()
        db.checkpoint("shutdown")
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
