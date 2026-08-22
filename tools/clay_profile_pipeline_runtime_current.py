#!/usr/bin/env python3
"""Current-contract adapter for the generic Clay profile pipeline.

This module is intentionally application-neutral. It bridges the retained generic
runtime implementation to the current DB-resident profile + ``inference_generate``
Clay contract without reintroducing application/provider identity into the pipeline.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime

VERSION = "clay-profile-pipeline-runtime-current/0.2"
PROFILE_SCHEMA = "clay-pipeline-profile/v2"


class CurrentProfilePipelineRuntime(ProfilePipelineRuntime):
    """Compatibility-convergence layer for the current canonical Clay program.

    The inherited implementation remains the single gate/collection/commit engine.
    This layer only owns the newer DB-resident profile read and generic inference
    dispatch contracts. Application meaning remains profile data.
    """

    def _record_current_effect(self, kind: str, payload: dict[str, Any], started: float, ok: bool) -> None:
        self.effect_trace.append(
            {
                "kind": kind,
                "ok": ok,
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": hashlib.sha256(
                    json.dumps(payload, sort_keys=True, default=str).encode()
                ).hexdigest(),
            }
        )

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if kind not in {"pipeline_profile_read", "inference_generate"}:
            return super().effect(kind, payload)
        started = time.time()
        ok = False
        try:
            if kind == "pipeline_profile_read":
                result = self._pipeline_profile_read(payload)
            else:
                result = self._inference_generate(payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
            self._record_current_effect(kind, payload, started, ok)

    @staticmethod
    def _validate_profile(profile: dict[str, Any]) -> None:
        if profile.get("schema") != PROFILE_SCHEMA:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        for field in ("profile_id", "inference", "personality", "sources", "state_metrics", "gate"):
            if field not in profile:
                raise PipelineFault("PROFILE_MISSING:" + field)
        inference = profile.get("inference") or {}
        # Presets/config may name secret environment variables, but may not carry secret values.
        forbidden = {"api_key", "token", "secret", "bearer"}
        for key, value in inference.items():
            if str(key).lower() in forbidden and value not in (None, "", False):
                raise PipelineFault("PROFILE_CONTAINS_SECRET_VALUE")

    def install_profile(self, entity_db: str, profile: dict[str, Any]) -> str:
        """Install/replace the active runtime profile without touching entity history."""
        self._validate_profile(profile)
        raw = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        with self._db(entity_db) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS eos_pipeline_profile(
                  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                  profile_id TEXT NOT NULL,
                  profile_json TEXT NOT NULL,
                  profile_hash TEXT NOT NULL,
                  updated_at REAL NOT NULL)
                """
            )
            db.execute(
                """
                INSERT INTO eos_pipeline_profile(singleton,profile_id,profile_json,profile_hash,updated_at)
                VALUES(1,?,?,?,?)
                ON CONFLICT(singleton) DO UPDATE SET
                  profile_id=excluded.profile_id,
                  profile_json=excluded.profile_json,
                  profile_hash=excluded.profile_hash,
                  updated_at=excluded.updated_at
                """,
                (profile["profile_id"], raw, digest, time.time()),
            )
        return digest

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                row = db.execute(
                    "SELECT profile_json,profile_hash FROM eos_pipeline_profile WHERE singleton=1"
                ).fetchone()
            if row is None:
                raise PipelineFault("NO_ACTIVE_PROFILE")
            profile = json.loads(row["profile_json"])
            self._validate_profile(profile)
            raw = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if digest != row["profile_hash"]:
                raise PipelineFault("PROFILE_HASH_MISMATCH")
            return {"ok": True, "profile": profile, "profile_hash": digest}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        """Map the current generic inference contract onto the retained backend engine."""
        inference = dict(p.get("inference") or {})
        try:
            if not inference:
                raise PipelineFault("INFERENCE_CONFIG_MISSING")
            # Keep the inherited provider implementation as one backend mechanism.
            # Local-exec/native product acceptance remains separate from this structured harness.
            request = {
                "provider": inference,
                "system": p["system"],
                "user": p["user"],
                "secret_file": p.get("secret_file"),
            }
            return self._provider_chat_json(request)
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}


__all__ = ["VERSION", "PROFILE_SCHEMA", "CurrentProfilePipelineRuntime"]
