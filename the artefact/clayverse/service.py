from __future__ import annotations

import base64
import binascii
import json
import os
import stat
import sys
from urllib.parse import urlsplit

from .clerk_auth import ClerkConfig, ClerkTokenVerifier
from .entityos_bridge import EntityOSBridge, EntityOSIntegrityError
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .readiness import claude_readiness
from .recovery import recover_incomplete_episodes
from .store import UnifiedDB
from .terminal_gateway import _PTY_INPUT_FRAME_MAX_BYTES, create_terminal_app
from .terminal_sessions import TerminalSessionManager


_ENTITYOS_PATH = "/opt/entityos/EntityOS"
_ENTITYOS_LOCK_PATH = "/opt/entityos/entityos.lock.json"
_ENTITYOS_LOCK_SCHEMA = "ClayVerseEntityOSArtifactLock/v1"
_ENTITYOS_LOCK_MAX_BYTES = 64 * 1024


def _clerk_map() -> dict[str, str]:
    raw = os.environ.get("CLAYVERSE_CLERK_MAP_JSON", "")
    if not raw:
        raise RuntimeError("CLAYVERSE_CLERK_MAP_JSON is required")
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("CLAYVERSE_CLERK_MAP_JSON is invalid JSON") from exc
    if not isinstance(mapping, dict) or len(mapping) != 2:
        raise RuntimeError("CLAYVERSE_CLERK_MAP_JSON must contain exactly two subject mappings")
    if any(
        not isinstance(subject, str)
        or not subject.strip()
        or user_id not in {"gabriel", "andreas"}
        for subject, user_id in mapping.items()
    ):
        raise RuntimeError("Clerk mapping subjects must be non-empty strings and may only target gabriel/andreas")
    if set(mapping.values()) != {"gabriel", "andreas"}:
        raise RuntimeError("Clerk mapping must identify each canonical user exactly once")
    return mapping


def _clerk_frontend_api_from_publishable_key(publishable_key: str) -> str:
    """Derive the direct Clerk FAPI URL encoded by a publishable key or fail closed."""
    encoded = ""
    for prefix in ("pk_test_", "pk_live_"):
        if publishable_key.startswith(prefix):
            encoded = publishable_key[len(prefix):]
            break
    if not encoded:
        raise RuntimeError("CLERK_PUBLISHABLE_KEY must be a Clerk test/live publishable key")
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        decoded = base64.b64decode(padded, validate=True).decode("ascii")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise RuntimeError("CLERK_PUBLISHABLE_KEY contains invalid FAPI encoding") from exc
    if not decoded.endswith("$"):
        raise RuntimeError("CLERK_PUBLISHABLE_KEY FAPI encoding is malformed")
    domain = decoded[:-1]
    if not domain or not domain.isascii() or any(char.isspace() for char in domain):
        raise RuntimeError("CLERK_PUBLISHABLE_KEY FAPI domain is invalid")
    try:
        parsed = urlsplit(f"https://{domain}")
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError("CLERK_PUBLISHABLE_KEY FAPI domain is invalid") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.hostname != domain.lower()
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("CLERK_PUBLISHABLE_KEY FAPI domain is invalid")
    return f"https://{domain}"


def _web_config(issuer: str) -> tuple[str, str]:
    publishable_key = os.environ.get("CLERK_PUBLISHABLE_KEY", "").strip()
    frontend_api = os.environ.get("CLERK_FRONTEND_API_URL", "").strip().rstrip("/")
    if not publishable_key or not frontend_api:
        raise RuntimeError("CLERK_PUBLISHABLE_KEY and CLERK_FRONTEND_API_URL are required")
    expected_frontend_api = _clerk_frontend_api_from_publishable_key(publishable_key)
    if frontend_api != expected_frontend_api:
        raise RuntimeError("CLERK_FRONTEND_API_URL must match the publishable-key Clerk instance")
    if issuer.strip().rstrip("/") != expected_frontend_api:
        raise RuntimeError("CLERK_ISSUER must match the publishable-key Clerk instance")
    return publishable_key, expected_frontend_api


def _load_embedded_entityos_lock() -> dict[str, object]:
    """Read the image-owned EntityOS lock without following a replacement symlink."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(_ENTITYOS_LOCK_PATH, flags)
    except OSError as exc:
        raise RuntimeError(f"embedded EntityOS lock open failed: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise RuntimeError("embedded EntityOS lock must be a regular file")
        if st.st_size <= 0 or st.st_size > _ENTITYOS_LOCK_MAX_BYTES:
            raise RuntimeError("embedded EntityOS lock size is invalid")
        raw = bytearray()
        while len(raw) <= _ENTITYOS_LOCK_MAX_BYTES:
            chunk = os.read(fd, min(8192, _ENTITYOS_LOCK_MAX_BYTES + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) != st.st_size or len(raw) > _ENTITYOS_LOCK_MAX_BYTES:
            raise RuntimeError("embedded EntityOS lock read was inconsistent")
    finally:
        os.close(fd)

    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("embedded EntityOS lock is invalid JSON") from exc
    if not isinstance(doc, dict) or doc.get("schema") != _ENTITYOS_LOCK_SCHEMA:
        raise RuntimeError("embedded EntityOS lock schema is invalid")

    sha256 = doc.get("sha256")
    size_bytes = doc.get("size_bytes")
    if (
        not isinstance(sha256, str)
        or len(sha256) != 64
        or any(char not in "0123456789abcdef" for char in sha256)
    ):
        raise RuntimeError("embedded EntityOS lock sha256 is invalid")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes <= 0:
        raise RuntimeError("embedded EntityOS lock size_bytes is invalid")
    return doc


def _entityos_config() -> tuple[EntityOSBridge | None, dict[str, object]]:
    enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
    lock = _load_embedded_entityos_lock()
    sha256 = str(lock["sha256"])
    expected_size = int(lock["size_bytes"])

    candidate = EntityOSBridge(path=_ENTITYOS_PATH, sha256=sha256)
    try:
        verified = candidate.verify()
    except (EntityOSIntegrityError, OSError, ValueError) as exc:
        raise RuntimeError(f"EntityOS verification failed: {exc}") from exc
    if int(verified["size"]) != expected_size:
        raise RuntimeError("EntityOS verification failed: embedded size does not match image lock")

    status = {
        "staged": True,
        "verified": True,
        "execution_enabled": enable_exec,
        "authority": "image_embedded_lock",
        "lock_path": _ENTITYOS_LOCK_PATH,
        "lock_schema": _ENTITYOS_LOCK_SCHEMA,
        **verified,
    }
    return (candidate if enable_exec else None), status


def _state_probe_payload(checkpoint: str, state_hash: str) -> dict[str, object]:
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

    if "--once" in sys.argv:
        ClayGraphProjection(db).rebuild()
        cid, digest = db.checkpoint("state-probe")
        print(json.dumps(_state_probe_payload(cid, digest)), flush=True)
        db.close()
        return 0

    recovery = recover_incomplete_episodes(db)
    ClayGraphProjection(db).rebuild()
    cid, digest = db.checkpoint("boot")

    clerk_map = _clerk_map()
    clerk_config = ClerkConfig.from_env()
    publishable_key, frontend_api = _web_config(clerk_config.issuer)
    verifier = ClerkTokenVerifier(clerk_config)
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
                "generation": db.session_generation(binding.session_id),
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
        "entity_generation": db.entity_generation(),
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
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=1,
            access_log=False,
            ws_max_size=_PTY_INPUT_FRAME_MAX_BYTES,
        )
    finally:
        db.checkpoint("shutdown")
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
