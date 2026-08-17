from __future__ import annotations

import base64
import binascii
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .clerk_auth import ClerkConfig, ClerkTokenVerifier
from .entityos_bridge import EntityOSBridge, EntityOSIntegrityError
from .final_acceptance_probe import run_mistral_acceptance_probe
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .logical_snapshot import LogicalSnapshotManager
from .readiness import claude_readiness
from .recovery import recover_incomplete_episodes
from .runtime_identity import collect_runtime_identity
from .store import UnifiedDB
from .terminal_gateway import _PTY_INPUT_FRAME_MAX_BYTES, create_terminal_app
from .terminal_sessions import TerminalSessionManager


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


def _entityos_config() -> tuple[EntityOSBridge | None, dict[str, object]]:
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
    return {
        "service": "clayverse",
        "status": "probe_ok",
        "scope": "state_only",
        "ready": False,
        "checkpoint": checkpoint,
        "state_hash": state_hash,
    }


def _acceptance_bool(name: str, default: str = "0") -> bool:
    raw = os.environ.get(name, default)
    if raw not in {"0", "1"}:
        raise RuntimeError(f"{name} must be 0 or 1")
    return raw == "1"


def _acceptance_required_effect_capability() -> str | None:
    """Return the single final-test capability fence or fail closed."""

    raw = os.environ.get("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", "").strip()
    if not raw:
        return None
    if raw != "entityos.exec":
        raise RuntimeError(
            "CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY may only be entityos.exec"
        )
    return raw


def _acceptance_effect_policy() -> tuple[bool, str | None]:
    """Resolve final sandbox effect policy without allowing generic-effect credit."""

    require_effect = _acceptance_bool("CLAYVERSE_ACCEPTANCE_REQUIRE_EFFECT")
    required_capability = _acceptance_required_effect_capability()
    if require_effect and required_capability is None:
        required_capability = "entityos.exec"
    if required_capability is not None:
        require_effect = True
    return require_effect, required_capability


def _snapshot_restore_before_db_open(state_root: str) -> dict[str, object] | None:
    raw = os.environ.get("CLAYVERSE_RESTORE_SNAPSHOT_DIR", "").strip()
    if not raw:
        os.makedirs(state_root, exist_ok=True)
        return None
    if not os.path.isabs(raw) or any(char in raw for char in ("\x00", "\n", "\r")):
        raise RuntimeError("CLAYVERSE_RESTORE_SNAPSHOT_DIR must be an absolute single-line path")
    runtime_identity = collect_runtime_identity()
    return LogicalSnapshotManager(state_root).restore_fresh(
        Path(raw),
        runtime_identity=runtime_identity,
    )


def _acceptance_snapshot(db: UnifiedDB) -> dict[str, object] | None:
    if not _acceptance_bool("CLAYVERSE_ACCEPTANCE_CREATE_SNAPSHOT"):
        return None
    runtime_identity = collect_runtime_identity()
    manifest = LogicalSnapshotManager(db.path.parent).create(
        db,
        runtime_identity=runtime_identity,
        reason="mistral-final-sandbox-probe",
    )
    anchor = manifest["state"]["checkpoint_anchor"]
    return {
        "created": True,
        "snapshot_id": manifest["snapshot_id"],
        "database_sha256": manifest["database"]["sha256"],
        "checkpoint_id": anchor["checkpoint_id"],
        "state_hash": anchor["state_hash"],
        "entity_generation": manifest["state"]["entity_generation"],
    }


def _run_mistral_once(db: UnifiedDB) -> dict[str, object]:
    """Run the internal canonical Mistral turn used by the final sandbox controller."""

    recovery = recover_incomplete_episodes(db)
    ClayGraphProjection(db).rebuild()
    clerk_map = _clerk_map()
    clerk_subject = os.environ.get("CLAYVERSE_ACCEPTANCE_CLERK_SUBJECT", "")
    prompt = os.environ.get("CLAYVERSE_ACCEPTANCE_PROMPT", "")
    require_effect, required_effect_capability = _acceptance_effect_policy()
    entityos_bridge, entityos_status = _entityos_config()
    if required_effect_capability == "entityos.exec" and entityos_bridge is None:
        raise RuntimeError(
            "final EntityOS acceptance effect is required but EntityOS execution is disabled"
        )

    payload = run_mistral_acceptance_probe(
        db,
        clerk_map,
        clerk_subject,
        prompt,
        entityos_bridge=entityos_bridge,
        require_effect=require_effect,
        required_effect_capability=required_effect_capability,
    )
    checkpoint_id, state_hash = db.checkpoint("mistral-final-sandbox-probe")
    snapshot = _acceptance_snapshot(db)
    payload.update(
        {
            "checkpoint": checkpoint_id,
            "state_hash": state_hash,
            "recovery": recovery,
            "acceptance_snapshot": snapshot,
            "entityos": {
                "verified": bool(entityos_status.get("verified")),
                "execution_enabled": bool(entityos_status.get("execution_enabled")),
                "sha256": entityos_status.get("sha256"),
            },
        }
    )
    return payload


def main():
    import uvicorn

    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    restore_receipt = _snapshot_restore_before_db_open(state_root)
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})

    if "--once" in sys.argv:
        ClayGraphProjection(db).rebuild()
        cid, digest = db.checkpoint("state-probe")
        payload = _state_probe_payload(cid, digest)
        payload["snapshot_restore"] = restore_receipt
        print(json.dumps(payload, sort_keys=True), flush=True)
        db.close()
        return 0

    if "--mistral-once" in sys.argv:
        try:
            payload = _run_mistral_once(db)
            payload["snapshot_restore"] = restore_receipt
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        finally:
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
        "snapshot_restore": restore_receipt,
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
