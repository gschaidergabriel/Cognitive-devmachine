from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient


class AuthenticationError(PermissionError):
    pass


@dataclass(frozen=True)
class ClerkConfig:
    issuer: str
    jwt_key: str | None = None
    jwks_url: str | None = None
    audience: str | None = None
    authorized_parties: tuple[str, ...] = ()
    leeway_seconds: int = 5

    @classmethod
    def from_env(cls) -> "ClerkConfig":
        issuer = os.environ.get("CLERK_ISSUER", "").strip().rstrip("/")
        jwt_key = os.environ.get("CLERK_JWT_KEY") or None
        jwks_url = os.environ.get("CLERK_JWKS_URL") or (f"{issuer}/.well-known/jwks.json" if issuer else None)
        audience = os.environ.get("CLERK_AUDIENCE") or None
        parties = tuple(x.strip() for x in os.environ.get("CLERK_AUTHORIZED_PARTIES", "").split(",") if x.strip())
        if not issuer:
            raise RuntimeError("CLERK_ISSUER is required")
        if not jwt_key and not jwks_url:
            raise RuntimeError("CLERK_JWT_KEY or CLERK_JWKS_URL is required")
        if not parties:
            raise RuntimeError("CLERK_AUTHORIZED_PARTIES is required")
        return cls(issuer=issuer, jwt_key=jwt_key, jwks_url=jwks_url, audience=audience, authorized_parties=parties)


class ClerkTokenVerifier:
    """Fail-closed verifier for Clerk session JWTs.

    Networkless verification is preferred when CLERK_JWT_KEY is supplied. Otherwise
    PyJWKClient fetches/caches the instance JWKS. Only RS256 is accepted.
    """

    def __init__(self, config: ClerkConfig):
        self.config = config
        self._jwks = PyJWKClient(config.jwks_url, cache_keys=True) if not config.jwt_key else None

    def verify(self, token: str) -> dict[str, Any]:
        if not token:
            raise AuthenticationError("missing session token")
        try:
            key: Any = self.config.jwt_key
            if key is None:
                key = self._jwks.get_signing_key_from_jwt(token).key
            kwargs: dict[str, Any] = {
                "algorithms": ["RS256"],
                "issuer": self.config.issuer,
                "leeway": self.config.leeway_seconds,
                "options": {"require": ["exp", "sub"]},
            }
            if self.config.audience:
                kwargs["audience"] = self.config.audience
            else:
                kwargs["options"]["verify_aud"] = False
            claims = jwt.decode(token, key=key, **kwargs)
        except Exception as exc:
            raise AuthenticationError("invalid Clerk session token") from exc
        azp = claims.get("azp")
        if azp not in self.config.authorized_parties:
            raise AuthenticationError("unauthorized Clerk party")
        if not claims.get("sub"):
            raise AuthenticationError("Clerk token missing subject")
        return claims

    @staticmethod
    def bearer(authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthenticationError("missing bearer token")
        token = authorization[7:].strip()
        if not token:
            raise AuthenticationError("missing bearer token")
        return token


class ClaudeCodeInference:
    """Tool-less Claude Code cognition boundary for ClayVerse.

    Cognition runs with auto-discovery disabled, all built-in tools disabled and no
    Claude session persistence. UnifiedDB/WorldAssembler remains the sole durable
    memory/world authority and the ClayVerse EffectGate owns all external actions.
    """

    def __init__(self, binary: str | None = None, cwd: str | None = None, timeout: int | None = None):
        self.binary = binary or os.environ.get("CLAUDE_CODE_BIN", "claude")
        self.cwd = cwd or os.environ.get("CLAYVERSE_WORKSPACE", "/workspace")
        self.timeout = int(timeout or os.environ.get("CLAYVERSE_CLAUDE_TIMEOUT_SECONDS", "120"))
        self._lock = threading.Lock()

    def available(self) -> bool:
        executable = shutil.which(self.binary)
        if executable is None:
            return False
        try:
            cp = subprocess.run([executable, "--version"], shell=False, capture_output=True, timeout=5)
            return cp.returncode == 0
        except Exception:
            return False

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        world_json = json.dumps(world, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(world_json) > 600_000:
            raise RuntimeError("assembled world exceeds Claude Code boundary")
        system = (
            "You are the cognition engine inside ClayVerse, one persistent central entity shared by authenticated users. "
            "UnifiedDB is the authoritative state and the supplied WORLD is the only persisted context for this turn. "
            "ClayGraph is a derived projection. You have no tool authority in this cognition call. Return reasoning/output "
            "only; any external action must be requested through the ClayVerse EffectGate."
        )
        prompt = f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}"
        args = [
            self.binary,
            "--bare",
            "-p",
            prompt,
            "--output-format",
            "json",
            "--max-turns",
            "1",
            "--permission-mode",
            "plan",
            "--tools",
            "",
            "--no-session-persistence",
            "--append-system-prompt",
            system,
        ]
        env = {**os.environ, "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1"}
        with self._lock:
            try:
                cp = subprocess.run(
                    args,
                    shell=False,
                    cwd=self.cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Claude Code inference timeout") from exc
        if cp.returncode != 0:
            raise RuntimeError(f"Claude Code inference failed rc={cp.returncode}: {cp.stderr[-2000:]}")
        try:
            payload = json.loads(cp.stdout)
            text = payload.get("result") or payload.get("text") or payload.get("message")
            if isinstance(text, dict):
                text = text.get("content") or json.dumps(text, ensure_ascii=False)
            if not isinstance(text, str):
                text = cp.stdout.strip()
        except json.JSONDecodeError:
            text = cp.stdout.strip()
        if not text:
            raise RuntimeError("Claude Code returned empty inference")
        return {"text": text, "selection": "respond", "effect": None}
