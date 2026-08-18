from __future__ import annotations
import pathlib

import base64
import binascii
import json
import os
import sys
from urllib.parse import urlsplit

from .clerk_auth import ClerkConfig, ClerkTokenVerifier
from .entityos_bridge import EntityOSBridge, EntityOSIntegrityError
from .graph import ClayGraphProjection
from .identity import IdentityRouter
from .readiness import claude_readiness
from .autonomy_activation import AutonomyActivationError, install_attested_autonomy_pulse
from .autonomy_pulse import AutonomyPulse
from .recovery import recover_incomplete_episodes
from .wirte import aufnehmen as wirte_aufnehmen
from .profile import grundstock as profil_grundstock
from .baunotizen import sicherstellen as baunotizen_sicherstellen
from .erfolge import grundstock as erfolge_grundstock
from .raum import sicherstellen as raum_sicherstellen
from .arbeitspaket import sicherstellen as arbeitspaket_sicherstellen
from .tresor import stand as tresor_stand
from .store import UnifiedDB, resolve_db_path
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
    required = os.environ.get("CLAYVERSE_REQUIRE_ENTITYOS", "0") == "1"
    path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
    sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()

    if not path and not sha256:
        if required:
            raise RuntimeError(
                "EntityOS is required (CLAYVERSE_REQUIRE_ENTITYOS=1) but "
                "CLAYVERSE_ENTITYOS_PATH/CLAYVERSE_ENTITYOS_SHA256 are not set"
            )
        return None, {"required": False, "bound": False}

    if not path or not sha256:
        raise RuntimeError(
            "EntityOS binding is incomplete: both CLAYVERSE_ENTITYOS_PATH and "
            "CLAYVERSE_ENTITYOS_SHA256 must be set together"
        )
    if not os.path.isabs(path):
        raise RuntimeError("CLAYVERSE_ENTITYOS_PATH must be absolute")

    candidate = EntityOSBridge(path=path, sha256=sha256)
    try:
        verified = candidate.verify()
    except (EntityOSIntegrityError, OSError, ValueError) as exc:
        raise RuntimeError(f"EntityOS verification failed: {exc}") from exc
    status = {
        "required": required,
        "bound": required,
        "staged": True,
        "verified": True,
        **verified,
    }
    return (candidate if required else None), status


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



STATIC_RUNTIME_CONTRACT = "/opt/clayverse/runtime/CLAUDE.md"


def render_runtime_prompt(db, state_root: str) -> str:
    """Write identity(from DB) + contract(from image) to the loaded prompt file.

    The order matters: identity first. It is what the entity IS; everything after
    it describes how it must operate.
    """
    identity = db.canonical_identity()
    static = pathlib.Path(STATIC_RUNTIME_CONTRACT).read_text(encoding="utf-8")
    target_dir = pathlib.Path(state_root) / "runtime"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "CLAUDE.md"
    body = (
        "# Canonical identity (UnifiedDB root state, level 0)\n\n"
        "This block is not conversation. It is loaded from canonical state on every\n"
        "boot and cannot be compacted away.\n\n"
        f"{identity}\n\n"
        "---\n\n"
        f"{static}"
    )
    tmp = target.with_suffix(".md.tmp")
    tmp.write_text(body, encoding="utf-8")
    tmp.replace(target)
    target.chmod(0o444)
    return str(target)


def main():
    import uvicorn

    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    os.makedirs(state_root, exist_ok=True)
    db = UnifiedDB(resolve_db_path(state_root))
    IdentityRouter(db, {})
    rendered_prompt = render_runtime_prompt(db, state_root)
    # Verbundene Rechner beim Start einlesen. Der Herzschlag kommt ohnehin an --
    # bisher landete er nur in einer Datei, die niemand liest.
    try:
        # Schemaanlage gehoert hierher, an den Start -- nicht in eine Lesefunktion.
        profil_stand = profil_grundstock(db)
    except Exception as exc:
        profil_stand = {"_fehler": f"{type(exc).__name__}: {exc}"}
    try:
        wirte_stand = wirte_aufnehmen(db)
    except Exception as exc:
        wirte_stand = {"_fehler": f"{type(exc).__name__}: {exc}"}
    try:
        # Auch hier nur Schema/Index -- die eigentliche Aufnahme (aufnehmen())
        # laeuft eigenstaendig ueber den entityos-baunotizen.timer, nicht im
        # Bootpfad. Gleiche Regel wie bei profil_grundstock: Schemaanlage ist
        # eine Startaufgabe, keine Leseaufgabe.
        baunotizen_sicherstellen(db)
    except Exception as exc:
        baunotizen_stand = {"_fehler": f"{type(exc).__name__}: {exc}"}
    else:
        baunotizen_stand = {"index": "sichergestellt"}
    try:
        # Der Raum der vier Plaetze. Schemaanlage gehoert an den Start --
        # executescript committet implizit und hat heute schon zweimal eine
        # laufende Transaktion aufgerissen.
        raum_sicherstellen(db)
        arbeitspaket_sicherstellen(db)
    except Exception as exc:
        print(f"  Raum/Pakete: {type(exc).__name__}: {exc}")
    try:
        # Kein Anlegen, nur melden: ein fehlender Tresorschluessel soll beim
        # Start auffallen und nicht erst, wenn ein Dienst einen Wert braucht.
        tresor_lage = tresor_stand()
    except Exception as exc:
        print(f"  Raum: {type(exc).__name__}: {exc}")
    try:
        # Die Ausbeutetabelle der Gedaechtnisextraktion. Sie entstand frueher
        # in der Extraktion selbst -- mitten in der Zug-Transaktion, per
        # executescript, das implizit committet. Das legte den Chat lahm.
        # Schemaanlage ist eine Startaufgabe, keine Leseaufgabe.
        from .gedaechtnis import AUSBEUTE_SCHEMA
        db.db.executescript(AUSBEUTE_SCHEMA)
    except Exception as exc:
        print(f"  Ausbeutetabelle: {type(exc).__name__}: {exc}")
    try:
        # Erfolge UND Fehlschlaege. Beide Haelften oder keine -- eine Bilanz,
        # die nur Gelungenes fuehrt, ist ein Werbeblatt, und hier waere sie
        # ausserdem ein falsches Bild davon, wie dieses System kaputtgeht.
        erfolge_stand = erfolge_grundstock(db)
    except Exception as exc:
        erfolge_stand = {"_fehler": f"{type(exc).__name__}: {exc}"}

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
        # Both canonical users' Claude Code CLI share one OAuth credential
        # (TerminalSessionManager._link_shared_credentials symlinks it into each
        # user's home on ensure()). Checking the shared source file directly here
        # does not depend on ensure() having run yet.
        claude_status = claude_readiness(
            required=require_claude,
            credentials_path=TerminalSessionManager.CREDENTIALS_SOURCE,
        )
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
        terminals=terminals,
    )

    # ── Initiative ────────────────────────────────────────────────────────
    # Persistent goals, intermediate steps, feedback, replanning and continuity
    # were all already built. Initiative was the one property with no wire:
    # nothing ever woke next_runnable(). This is that wire.
    #
    # It is inert until a goal exists, and a durable goal can only originate
    # from a canonical human turn -- so switching it on does not by itself make
    # anything happen. It also may not preempt a live human turn; the pulse
    # checks the terminal arbiter for that, which is why it must share the very
    # same TerminalSessionManager the browser attaches through.
    autonomy_pulse_status = {"installed": False, "reason": "disabled"}
    if os.environ.get("CLAYVERSE_AUTONOMY_PULSE", "1") == "1":
        try:
            interval = float(os.environ.get("CLAYVERSE_AUTONOMY_PULSE_SECONDS", "30"))
            pulse = AutonomyPulse(state_root, terminals, interval_seconds=interval)
            install_attested_autonomy_pulse(app, web_terminals=terminals, pulse=pulse)
            attestation = app.state.autonomy_activation
            autonomy_pulse_status = {
                "installed": True,
                "interval_seconds": interval,
                "shared_arbiter": attestation.pulse_uses_web_terminal_manager,
                "shared_activity_registry": attestation.shared_activity_registry,
                "shared_state_root": attestation.shared_state_root,
            }
        except AutonomyActivationError as exc:
            # Fail loud, not silent. An autonomy pulse that quietly did not start
            # is worse than none: the system would look autonomous and never act.
            autonomy_pulse_status = {"installed": False, "reason": f"attestation_denied: {exc}"}
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
        "autonomy_pulse": autonomy_pulse_status,
        "wirte": wirte_stand,
        "profile": profil_stand,
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
