#!/usr/bin/env python3
"""Current-contract adapter for the generic Clay profile pipeline.

This module is application-neutral. It converges the retained structured reference
runtime on the current DB-resident profile + ``inference_generate`` Clay contract and
adds an optional config-driven study surface inside the same SQLite commit boundary.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from typing import Any

import clay_pipeline_study_surface as study_surface
from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime

VERSION = "clay-profile-pipeline-runtime-current/0.4"
PROFILE_SCHEMA = "clay-pipeline-profile/v2"


class CurrentProfilePipelineRuntime(ProfilePipelineRuntime):
    """Convergence layer; the inherited runtime remains the generic processing engine."""

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
            result = self._pipeline_profile_read(payload) if kind == "pipeline_profile_read" else self._inference_generate(payload)
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
        forbidden = {"api_key", "token", "secret", "bearer"}
        for key, value in inference.items():
            if str(key).lower() in forbidden and value not in (None, "", False):
                raise PipelineFault("PROFILE_CONTAINS_SECRET_VALUE")

    @staticmethod
    def _validate_study_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise PipelineFault("BAD_STUDY_CONFIG")
        if not str(config.get("profile_id", "")).strip():
            raise PipelineFault("STUDY_CONFIG_PROFILE_REQUIRED")
        if config.get("epistemic_law") != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
            raise PipelineFault("BAD_STUDY_EPISTEMIC_LAW")

    def _materialize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        out = json.loads(json.dumps(profile))
        surface = out.get("study_surface")
        if isinstance(surface, dict) and surface.get("config_file"):
            path = self._resolve(str(surface["config_file"]))
            config = json.loads(path.read_text(encoding="utf-8"))
            self._validate_study_config(config)
            if str(config["profile_id"]) != str(out.get("profile_id")):
                raise PipelineFault("STUDY_PROFILE_MISMATCH")
            raw = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            out["study_surface"] = {
                "config": config,
                "config_source": str(surface["config_file"]),
                "config_hash": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            }
        return out

    @staticmethod
    def _profile_tables(db) -> None:
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
            CREATE TABLE IF NOT EXISTS eos_pipeline_study_config(
              profile_id TEXT PRIMARY KEY,
              config_json TEXT NOT NULL,
              config_hash TEXT NOT NULL,
              updated_at REAL NOT NULL)
            """
        )

    def install_profile(self, entity_db: str, profile: dict[str, Any]) -> str:
        """Install/replace active runtime configuration without resetting entity history."""
        profile = self._materialize_profile(profile)
        self._validate_profile(profile)
        raw = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        with self._db(entity_db) as db:
            self._profile_tables(db)
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

    def install_study_config(self, entity_db: str, config: dict[str, Any]) -> str:
        """Install a profile-bound study config as DB-resident application data."""
        self._validate_study_config(config)
        raw = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        with self._db(entity_db) as db:
            self._profile_tables(db)
            db.execute(
                """
                INSERT INTO eos_pipeline_study_config(profile_id,config_json,config_hash,updated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(profile_id) DO UPDATE SET
                  config_json=excluded.config_json,
                  config_hash=excluded.config_hash,
                  updated_at=excluded.updated_at
                """,
                (str(config["profile_id"]), raw, digest, time.time()),
            )
        return digest

    def install_study_config_file(self, entity_db: str, path: str) -> str:
        config = json.loads(self._resolve(path).read_text(encoding="utf-8"))
        return self.install_study_config(entity_db, config)

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
                table_exists = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='eos_pipeline_study_config'"
                ).fetchone()
                config_row = None
                if table_exists:
                    config_row = db.execute(
                        "SELECT config_json,config_hash FROM eos_pipeline_study_config WHERE profile_id=?",
                        (str(profile["profile_id"]),),
                    ).fetchone()
            if config_row is not None:
                if isinstance(profile.get("study_surface"), dict):
                    raise PipelineFault("MULTIPLE_STUDY_CONFIG_AUTHORITIES")
                config = json.loads(config_row["config_json"])
                self._validate_study_config(config)
                config_raw = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                config_hash = hashlib.sha256(config_raw.encode("utf-8")).hexdigest()
                if config_hash != config_row["config_hash"]:
                    raise PipelineFault("STUDY_CONFIG_HASH_MISMATCH")
                profile["study_surface"] = {"config": config, "config_hash": config_hash}
            return {"ok": True, "profile": profile, "profile_hash": digest}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        result = super()._pipeline_init(p)
        if not result.get("ok"):
            return result
        try:
            with self._db(str(p["entity_db"])) as db:
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS eos_pipeline_studies(
                      output_id TEXT PRIMARY KEY,
                      ts REAL NOT NULL,
                      generation INTEGER NOT NULL,
                      profile_id TEXT NOT NULL,
                      study_schema TEXT NOT NULL,
                      system_json TEXT NOT NULL,
                      self_report_json TEXT NOT NULL,
                      evaluation_json TEXT NOT NULL,
                      rendered_text TEXT NOT NULL)
                    """
                )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = dict(p.get("inference") or {})
        try:
            if not inference:
                raise PipelineFault("INFERENCE_CONFIG_MISSING")
            return self._provider_chat_json(
                {
                    "provider": inference,
                    "system": p["system"],
                    "user": p["user"],
                    "secret_file": p.get("secret_file"),
                }
            )
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    @staticmethod
    def _surface_config(profile: dict[str, Any]) -> dict[str, Any] | None:
        surface = profile.get("study_surface")
        if not isinstance(surface, dict):
            return None
        config = surface.get("config")
        return config if isinstance(config, dict) and config.get("enabled", False) else None

    def _pipeline_commit(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"])
        profile = p["profile"]
        previous = p["previous"]
        data = p["data"]
        collected = data["collected"]
        compiled = data["compiled"]
        generated = data["generated"]
        payload = data["gated"]["payload"]
        if "_pipeline_appendices" in payload:
            return {"ok": False, "error_kind": "PipelineFault", "error": "MODEL_OWNED_PIPELINE_APPENDIX"}
        contract = profile["personality"]["output_contract"]
        output_id = secrets.token_hex(16)
        now = time.time()
        generation = int(previous["generation"]) + 1
        continuity = {
            "narrative": payload.get(contract["continuity_field"]),
            "autobiographical_hypotheses": payload.get(contract["autobiographical_hypotheses_field"]),
        }
        db = self._db(entity_db)
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "UPDATE eos_pipeline_state SET updated_at=? WHERE singleton=1 AND generation=?",
                (now, previous["generation"]),
            )
            if row.rowcount != 1:
                raise PipelineFault("STALE_GENERATION")

            public_payload = json.loads(json.dumps(payload))
            config = self._surface_config(profile)
            study = None
            if config is not None:
                previous_row = db.execute(
                    "SELECT system_json FROM eos_pipeline_studies WHERE profile_id=? ORDER BY generation DESC LIMIT 1",
                    (profile["profile_id"],),
                ).fetchone()
                previous_system = json.loads(previous_row["system_json"]) if previous_row else {}
                study = study_surface.build(
                    config,
                    profile,
                    payload,
                    compiled,
                    generated,
                    generation,
                    now,
                    previous_system,
                )
                public_payload["_pipeline_appendices"] = [
                    {"kind": "study_surface", "rendered": study["rendered"]}
                ]

            for item in collected["consume"]:
                db.execute(
                    "INSERT INTO eos_pipeline_consumed(source_kind,source_id,output_id,consumed_at) VALUES(?,?,?,?)",
                    (item["kind"], item["id"], output_id, now),
                )
            db.execute(
                "INSERT INTO eos_pipeline_outputs VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    output_id,
                    now,
                    generation,
                    profile["profile_id"],
                    json.dumps(public_payload, ensure_ascii=False),
                    generated.get("provider_kind", ""),
                    generated.get("model"),
                    compiled["packet_hash"],
                    compiled["canonical_state_hash"],
                ),
            )
            if study is not None:
                db.execute(
                    "INSERT INTO eos_pipeline_studies VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        output_id,
                        now,
                        generation,
                        profile["profile_id"],
                        str(study.get("schema", "")),
                        json.dumps(study["system_state"], ensure_ascii=False),
                        json.dumps(study["model_self_report"], ensure_ascii=False),
                        json.dumps(study["evaluation"], ensure_ascii=False),
                        study["rendered"],
                    ),
                )
            db.execute(
                "INSERT INTO eos_pipeline_packets VALUES(?,?,?,?,?,?,?)",
                (
                    compiled["packet_hash"],
                    output_id,
                    now,
                    generation,
                    profile["profile_id"],
                    compiled["source_count"],
                    compiled["canonical_state_hash"],
                ),
            )
            row = db.execute(
                "UPDATE eos_pipeline_state SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,cursors_json=?,updated_at=? WHERE singleton=1 AND generation=?",
                (
                    generation,
                    json.dumps(continuity, ensure_ascii=False),
                    json.dumps(compiled["canonical"], ensure_ascii=False),
                    compiled["canonical_state_hash"],
                    json.dumps(collected["next_cursors"]),
                    now,
                    previous["generation"],
                ),
            )
            if row.rowcount != 1:
                raise PipelineFault("STALE_GENERATION_FINAL")
            db.commit()
            return {"ok": True, "output_id": output_id, "generation": generation}
        except Exception as exc:
            db.rollback()
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            db.close()


__all__ = ["VERSION", "PROFILE_SCHEMA", "CurrentProfilePipelineRuntime"]
