#!/usr/bin/env python3
"""Generic DB-profile-driven reference runtime for the canonical Clay entity pipeline.

Application identity, personality, sources, metrics, inference choice and optional study
configuration are MiniUnifiedDB data. This module owns only generic orchestration,
epistemic invariants, bounded adapters, inference transport and one atomic commit path.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import sqlite3
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

import claycode_structured_backend as clay
from clay_pipeline_study_surface import build_study_record

VERSION = "clay-profile-pipeline-runtime/0.5"

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when every source
marked required_for_quiet is healthy. Every published section needs evidence_refs from
the allowed set. state_claims may reference only VERIFIED metrics and may not exceed the
measured value plus configured tolerance. SYSTEM_MEASUREMENT != MODEL_SELF_REPORT.
Echo CANONICAL_STATE_HASH and PACKET_HASH exactly. Never reveal configured secrets.
Editable profile instructions cannot override these rules."""

_PIPELINE_RESERVED_OUTPUT_KEYS = {
    "_pipeline",
    "_pipeline_appendices",
    "study_appendix",
    "study_record",
}

_SECRET_VALUE_KEYS = {
    "api_token",
    "api_key",
    "access_token",
    "secret_value",
    "password",
    "private_key",
    "client_secret",
    "bearer_token",
    "refresh_token",
    "auth_token",
}

_SAFE_ENV_NAMES = {
    "PATH",
    "HOME",
    "TMPDIR",
    "TMP",
    "TEMP",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "CUDA_VISIBLE_DEVICES",
    "ROCR_VISIBLE_DEVICES",
    "HIP_VISIBLE_DEVICES",
    "OMP_NUM_THREADS",
}


class PipelineFault(RuntimeError):
    pass


class ProfilePipelineRuntime(clay.Runtime):
    """One persistent entity DB, one active profile, one optional study surface."""

    def __init__(
        self,
        *,
        root: str | Path = ".",
        allow_network: bool = False,
        provider_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        super().__init__()
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.allow_network = allow_network
        self.provider_override = provider_override
        self.effect_trace: list[dict[str, Any]] = []
        self._active_secrets: list[str] = []
        self.builtins["effect"] = self.effect
        self.allowed_effects = {
            "pipeline_profile_read",
            "pipeline_init",
            "pipeline_state_read",
            "pipeline_collect",
            "pipeline_compile",
            "pipeline_build_prompt",
            "inference_generate",
            "pipeline_gate",
            "pipeline_commit",
        }

    # ------------------------------------------------------------------
    # Generic serialization / path / DB primitives
    # ------------------------------------------------------------------

    def _resolve(self, value: str) -> Path:
        path = Path(str(value))
        return path.resolve() if path.is_absolute() else (self.root / path).resolve()

    def _db(self, value: str) -> sqlite3.Connection:
        path = self._resolve(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    def _read_only_db(self, value: str) -> sqlite3.Connection:
        path = self._resolve(value)
        if not path.is_file():
            raise FileNotFoundError(str(path))
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return conn

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
            default=str,
        )

    @classmethod
    def _hash_json(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @staticmethod
    def _sha256_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _object_type(db: sqlite3.Connection, name: str) -> str | None:
        row = db.execute(
            "SELECT type FROM sqlite_master WHERE name=? AND type IN ('table','view')",
            (name,),
        ).fetchone()
        return str(row[0]) if row else None

    @staticmethod
    def _table_columns(db: sqlite3.Connection, name: str) -> set[str]:
        return {str(row["name"]) for row in db.execute(f"PRAGMA table_info('{name}')")}

    @staticmethod
    def _create_packet_table(db: sqlite3.Connection) -> None:
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_packets(
                 output_id TEXT PRIMARY KEY,
                 packet_hash TEXT NOT NULL,
                 ts REAL NOT NULL,
                 generation INTEGER NOT NULL,
                 profile_id TEXT NOT NULL,
                 source_count INTEGER NOT NULL,
                 canonical_hash TEXT NOT NULL)"""
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS eos_pipeline_packets_hash_idx "
            "ON eos_pipeline_packets(packet_hash)"
        )

    def _migrate_packet_table(self, db: sqlite3.Connection) -> None:
        if self._object_type(db, "eos_pipeline_packets") != "table":
            return
        info = db.execute("PRAGMA table_info(eos_pipeline_packets)").fetchall()
        primary = [str(row["name"]) for row in info if int(row["pk"] or 0) > 0]
        if primary != ["packet_hash"]:
            return
        legacy = "eos_pipeline_packets_legacy_v1"
        if self._object_type(db, legacy):
            raise PipelineFault("PACKET_MIGRATION_LEGACY_TABLE_PRESENT")
        # A named index follows a table rename. Drop it before rename so the canonical
        # table receives a fresh index instead of losing it when the legacy table drops.
        db.execute("DROP INDEX IF EXISTS eos_pipeline_packets_hash_idx")
        db.execute(f"ALTER TABLE eos_pipeline_packets RENAME TO {legacy}")
        self._create_packet_table(db)
        db.execute(
            f"""INSERT INTO eos_pipeline_packets(
                   output_id,packet_hash,ts,generation,profile_id,source_count,canonical_hash)
                 SELECT output_id,packet_hash,ts,generation,profile_id,source_count,canonical_hash
                 FROM {legacy}"""
        )
        db.execute(f"DROP TABLE {legacy}")

    def _ensure_schema(self, db: sqlite3.Connection) -> None:
        # Deliberately no executescript: callers may already own a transaction.
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_profile(
                 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                 profile_id TEXT NOT NULL,
                 profile_hash TEXT NOT NULL,
                 profile_json TEXT NOT NULL,
                 updated_at REAL NOT NULL)"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_study_config(
                 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                 config_id TEXT NOT NULL,
                 config_hash TEXT NOT NULL,
                 config_json TEXT NOT NULL,
                 updated_at REAL NOT NULL)"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_state(
                 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                 generation INTEGER NOT NULL DEFAULT 0,
                 continuity_json TEXT NOT NULL DEFAULT '{}',
                 canonical_json TEXT NOT NULL DEFAULT '{}',
                 canonical_hash TEXT NOT NULL DEFAULT '',
                 cursors_json TEXT NOT NULL DEFAULT '{}',
                 updated_at REAL NOT NULL DEFAULT 0)"""
        )
        db.execute("INSERT OR IGNORE INTO eos_pipeline_state(singleton) VALUES(1)")
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_consumed(
                 source_kind TEXT NOT NULL,
                 source_id TEXT NOT NULL,
                 output_id TEXT NOT NULL,
                 consumed_at REAL NOT NULL,
                 PRIMARY KEY(source_kind,source_id))"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_outputs(
                 output_id TEXT PRIMARY KEY,
                 ts REAL NOT NULL,
                 generation INTEGER NOT NULL,
                 profile_id TEXT NOT NULL,
                 output_json TEXT NOT NULL,
                 provider_kind TEXT NOT NULL,
                 model TEXT,
                 packet_hash TEXT NOT NULL,
                 canonical_hash TEXT NOT NULL,
                 study_record_hash TEXT,
                 study_rendered_text TEXT NOT NULL DEFAULT '')"""
        )
        output_columns = self._table_columns(db, "eos_pipeline_outputs")
        if "study_record_hash" not in output_columns:
            db.execute("ALTER TABLE eos_pipeline_outputs ADD COLUMN study_record_hash TEXT")
        if "study_rendered_text" not in output_columns:
            db.execute(
                "ALTER TABLE eos_pipeline_outputs "
                "ADD COLUMN study_rendered_text TEXT NOT NULL DEFAULT ''"
            )
        self._create_packet_table(db)
        self._migrate_packet_table(db)
        db.execute(
            """CREATE TABLE IF NOT EXISTS eos_pipeline_studies(
                 output_id TEXT PRIMARY KEY,
                 generation INTEGER NOT NULL,
                 profile_id TEXT NOT NULL,
                 study_schema TEXT NOT NULL,
                 study_json TEXT NOT NULL,
                 rendered_text TEXT NOT NULL,
                 created_at REAL NOT NULL)"""
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS eos_pipeline_studies_generation_idx "
            "ON eos_pipeline_studies(generation)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS eos_pipeline_studies_profile_generation_idx "
            "ON eos_pipeline_studies(profile_id,generation DESC)"
        )

    # ------------------------------------------------------------------
    # Profile / study configuration authority
    # ------------------------------------------------------------------

    @staticmethod
    def _forbid_embedded_secrets(value: Any, path: str = "") -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = str(key)
                lower = key_text.lower()
                child = f"{path}.{key_text}" if path else key_text
                if lower in _SECRET_VALUE_KEYS and item not in (None, "", [], {}):
                    raise PipelineFault("PROFILE_CONTAINS_SECRET_VALUE:" + child)
                ProfilePipelineRuntime._forbid_embedded_secrets(item, child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                ProfilePipelineRuntime._forbid_embedded_secrets(
                    item, f"{path}[{index}]"
                )

    @classmethod
    def _normalize_profile(cls, profile: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(profile, Mapping):
            raise PipelineFault("PROFILE_NOT_OBJECT")
        out = json.loads(json.dumps(dict(profile)))
        out.pop("study_surface", None)
        out.pop("_runtime_snapshot", None)
        if out.get("schema") not in {"clay-pipeline-profile/v1", "clay-pipeline-profile/v2"}:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        if "inference" not in out and "provider" in out:
            out["inference"] = out.pop("provider")
        for field in (
            "profile_id",
            "inference",
            "personality",
            "sources",
            "state_metrics",
            "gate",
        ):
            if field not in out:
                raise PipelineFault("PROFILE_MISSING:" + field)
        if not isinstance(out["inference"], dict) or not out["inference"].get("kind"):
            raise PipelineFault("PROFILE_BAD_INFERENCE")
        cls._forbid_embedded_secrets(out)
        out["schema"] = "clay-pipeline-profile/v2"
        return out

    @classmethod
    def _normalize_study_config(cls, config: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(config, Mapping):
            raise PipelineFault("STUDY_CONFIG_NOT_OBJECT")
        out = json.loads(json.dumps(dict(config)))
        cls._forbid_embedded_secrets(out)
        if bool(out.get("enabled", False)):
            if out.get("epistemic_law") != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
                raise PipelineFault("BAD_STUDY_EPISTEMIC_LAW")
            if not isinstance(out.get("render", {}), dict):
                raise PipelineFault("BAD_STUDY_RENDER_CONFIG")
        return out

    def import_profile(
        self,
        entity_db: str,
        profile_or_path: Mapping[str, Any] | str | Path,
    ) -> dict[str, Any]:
        profile = (
            json.loads(self._resolve(str(profile_or_path)).read_text(encoding="utf-8"))
            if isinstance(profile_or_path, (str, Path))
            else profile_or_path
        )
        normalized = self._normalize_profile(profile)
        raw = self._canonical_json(normalized)
        digest = self._sha256_text(raw)
        db = self._db(entity_db)
        try:
            self._ensure_schema(db)
            db.commit()
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """INSERT INTO eos_pipeline_profile(
                       singleton,profile_id,profile_hash,profile_json,updated_at)
                   VALUES(1,?,?,?,?)
                   ON CONFLICT(singleton) DO UPDATE SET
                     profile_id=excluded.profile_id,
                     profile_hash=excluded.profile_hash,
                     profile_json=excluded.profile_json,
                     updated_at=excluded.updated_at""",
                (normalized["profile_id"], digest, raw, time.time()),
            )
            db.commit()
            return {
                "ok": True,
                "profile_id": normalized["profile_id"],
                "profile_hash": digest,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def import_study_surface(
        self,
        entity_db: str,
        config_or_path: Mapping[str, Any] | str | Path,
    ) -> dict[str, Any]:
        config = (
            json.loads(self._resolve(str(config_or_path)).read_text(encoding="utf-8"))
            if isinstance(config_or_path, (str, Path))
            else config_or_path
        )
        normalized = self._normalize_study_config(config)
        raw = self._canonical_json(normalized)
        digest = self._sha256_text(raw)
        config_id = str(
            normalized.get("profile_id") or normalized.get("schema") or "study"
        )
        db = self._db(entity_db)
        try:
            self._ensure_schema(db)
            db.commit()
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """INSERT INTO eos_pipeline_study_config(
                       singleton,config_id,config_hash,config_json,updated_at)
                   VALUES(1,?,?,?,?)
                   ON CONFLICT(singleton) DO UPDATE SET
                     config_id=excluded.config_id,
                     config_hash=excluded.config_hash,
                     config_json=excluded.config_json,
                     updated_at=excluded.updated_at""",
                (config_id, digest, raw, time.time()),
            )
            db.commit()
            return {"ok": True, "config_id": config_id, "config_hash": digest}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def clear_study_surface(self, entity_db: str) -> None:
        with self._db(entity_db) as db:
            self._ensure_schema(db)
            db.execute("DELETE FROM eos_pipeline_study_config WHERE singleton=1")

    # ------------------------------------------------------------------
    # Effect dispatch
    # ------------------------------------------------------------------

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        handlers = {
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_init": self._pipeline_init,
            "pipeline_state_read": self._pipeline_state_read,
            "pipeline_collect": self._pipeline_collect,
            "pipeline_compile": self._pipeline_compile,
            "pipeline_build_prompt": self._pipeline_build_prompt,
            "inference_generate": self._inference_generate,
            "pipeline_gate": self._pipeline_gate,
            "pipeline_commit": self._pipeline_commit,
        }
        started = time.time()
        ok = False
        try:
            result = handlers[kind](payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
            self.effect_trace.append(
                {
                    "kind": kind,
                    "ok": ok,
                    "ms": round((time.time() - started) * 1000, 3),
                    "payload_hash": self._sha256_text(
                        json.dumps(payload, sort_keys=True, default=str)
                    ),
                }
            )

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            db = self._db(str(p["entity_db"]))
            try:
                self._ensure_schema(db)
                db.commit()
                row = db.execute(
                    "SELECT profile_id,profile_hash,profile_json "
                    "FROM eos_pipeline_profile WHERE singleton=1"
                ).fetchone()
                study_row = db.execute(
                    "SELECT config_id,config_hash,config_json "
                    "FROM eos_pipeline_study_config WHERE singleton=1"
                ).fetchone()
            finally:
                db.close()
            if row is None:
                raise PipelineFault("NO_ACTIVE_PROFILE")
            profile = self._normalize_profile(json.loads(row["profile_json"]))
            digest = self._hash_json(profile)
            if digest != row["profile_hash"] or profile["profile_id"] != row["profile_id"]:
                raise PipelineFault("PROFILE_INTEGRITY_MISMATCH")

            study_hash: str | None = None
            if study_row is not None:
                study = self._normalize_study_config(json.loads(study_row["config_json"]))
                study_hash = self._hash_json(study)
                if study_hash != study_row["config_hash"]:
                    raise PipelineFault("STUDY_CONFIG_INTEGRITY_MISMATCH")
                bound_profile = study.get("profile_id")
                if bound_profile and str(bound_profile) != str(profile["profile_id"]):
                    raise PipelineFault("STUDY_CONFIG_PROFILE_MISMATCH")
                profile["study_surface"] = study

            profile["_runtime_snapshot"] = {
                "profile_hash": digest,
                "study_config_hash": study_hash,
            }
            return {
                "ok": True,
                "profile": profile,
                "profile_hash": digest,
                "study_config_hash": study_hash,
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
                row = db.execute(
                    "SELECT generation,continuity_json,canonical_hash,cursors_json "
                    "FROM eos_pipeline_state WHERE singleton=1"
                ).fetchone()
            if row is None:
                raise PipelineFault("STATE_MISSING")
            return {
                "ok": True,
                "generation": int(row["generation"]),
                "continuity": json.loads(row["continuity_json"]),
                "canonical_hash": str(row["canonical_hash"]),
                "cursors": json.loads(row["cursors_json"]),
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    # ------------------------------------------------------------------
    # Read-only evidence collection
    # ------------------------------------------------------------------

    def _already_consumed(self, entity_db: str, kind: str, source_id: Any) -> bool:
        with self._db(entity_db) as db:
            self._ensure_schema(db)
            return (
                db.execute(
                    "SELECT 1 FROM eos_pipeline_consumed "
                    "WHERE source_kind=? AND source_id=?",
                    (kind, str(source_id)),
                ).fetchone()
                is not None
            )

    def _query(self, db_path: str, sql: str) -> list[dict[str, Any]]:
        # Evidence queries are observations, never a hidden effect channel.
        with self._read_only_db(db_path) as db:
            return [dict(row) for row in db.execute(str(sql)).fetchall()]

    def _unconsumed_query_rows(
        self,
        *,
        entity_db: str,
        db_path: str,
        kind: str,
        spec: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        query = str(spec["query"])
        terminal_limit = re.search(r"\s+LIMIT\s+(\d+)\s*;?\s*$", query, re.I)
        configured_limit = spec.get("limit")
        limit = (
            int(configured_limit)
            if configured_limit is not None
            else int(terminal_limit.group(1)) if terminal_limit else 0
        )
        fetch_query = query[: terminal_limit.start()].rstrip() if terminal_limit else query
        raw = self._query(db_path, fetch_query)
        id_field = str(spec.get("id_field", "source_id"))
        rows: list[dict[str, Any]] = []
        for row in raw:
            source_id = row.get(id_field)
            if source_id is None:
                continue
            if self._already_consumed(entity_db, kind, source_id):
                continue
            rows.append(row)
            if limit > 0 and len(rows) >= limit:
                break
        return rows

    def _catalog(self, db_path: str, max_tables: int) -> list[dict[str, Any]]:
        with self._read_only_db(db_path) as db:
            names = [
                str(row[0])
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
            ]
            out: list[dict[str, Any]] = []
            for name in names[:max_tables]:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    continue
                count = int(db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
                columns = [
                    str(row[1]) for row in db.execute(f'PRAGMA table_info("{name}")')
                ]
                out.append({"table": name, "rows": count, "columns": columns[:40]})
            return out

    def _pipeline_collect(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"])
        source_db = str(p["source_db"])
        profile = p["profile"]
        previous = p.get("previous", {})
        sources: dict[str, Any] = {}
        sensors: dict[str, Any] = {}
        consume: list[dict[str, str]] = []
        cursors = dict(previous.get("cursors", {}))
        source_count = 0

        for spec in profile.get("sources", []):
            kind = str(spec["kind"])
            adapter = str(spec["adapter"])
            required = bool(spec.get("required_for_quiet", False))
            try:
                rows: list[dict[str, Any]] = []
                value: Any = None
                if adapter == "sqlite_query":
                    db_path = source_db if spec.get("db") == "source" else entity_db
                    rows = self._unconsumed_query_rows(
                        entity_db=entity_db,
                        db_path=db_path,
                        kind=kind,
                        spec=spec,
                    )
                    id_field = str(spec.get("id_field", "source_id"))
                    for row in rows:
                        consume.append({"kind": kind, "id": str(row[id_field])})
                elif adapter == "json_snapshot":
                    path = self._resolve(str(spec["path"]))
                    if not path.is_file():
                        raise FileNotFoundError(str(path))
                    value = json.loads(path.read_text(encoding="utf-8"))
                elif adapter == "jsonl_cursor":
                    path = self._resolve(str(spec["path"]))
                    if not path.is_file():
                        raise FileNotFoundError(str(path))
                    cursor = int(cursors.get(kind, 0))
                    limit = max(1, int(spec.get("limit", 60)))
                    raw = path.read_bytes()[cursor:]
                    consumed_bytes = 0
                    for piece in raw.splitlines(keepends=True):
                        if not piece.endswith(b"\n"):
                            break
                        if len(rows) >= limit:
                            break
                        consumed_bytes += len(piece)
                        line = piece.strip()
                        if not line:
                            continue
                        try:
                            parsed = json.loads(line.decode("utf-8"))
                        except Exception as exc:
                            raise PipelineFault("MALFORMED_JSONL") from exc
                        rows.append(parsed if isinstance(parsed, dict) else {"text": str(parsed)})
                    cursors[kind] = cursor + consumed_bytes
                else:
                    raise PipelineFault("UNKNOWN_SOURCE_ADAPTER:" + adapter)

                source_count += len(rows)
                sources[kind] = {
                    "ok": True,
                    "rows": rows,
                    "value": value,
                    "evidence_prefix": str(spec.get("evidence_prefix", "")),
                    "required_for_quiet": required,
                    "id_field": str(spec.get("id_field", "source_id")),
                }
                sensors[kind] = {"ok": True}
            except Exception as exc:
                sources[kind] = {
                    "ok": False,
                    "rows": [],
                    "value": None,
                    "error_kind": type(exc).__name__,
                    "error": str(exc),
                    "evidence_prefix": str(spec.get("evidence_prefix", "")),
                    "required_for_quiet": required,
                    "id_field": str(spec.get("id_field", "source_id")),
                }
                sensors[kind] = {
                    "ok": False,
                    "error_kind": type(exc).__name__,
                }

        probes: dict[str, Any] = {}
        for spec in profile.get("canonical_probes", []):
            name = str(spec["name"])
            try:
                db_path = source_db if spec.get("db") == "source" else entity_db
                if spec["adapter"] == "sqlite_query":
                    rows = self._query(db_path, str(spec["query"]))
                elif spec["adapter"] == "sqlite_catalog":
                    rows = self._catalog(db_path, int(spec.get("max_tables", 220)))
                else:
                    raise PipelineFault(
                        "UNKNOWN_PROBE_ADAPTER:" + str(spec["adapter"])
                    )
                probes[name] = {
                    "ok": True,
                    "rows": rows,
                    "evidence_ref": str(
                        spec.get("evidence_ref", "canonical:" + name)
                    ),
                }
            except Exception as exc:
                probes[name] = {
                    "ok": False,
                    "rows": [],
                    "error_kind": type(exc).__name__,
                    "error": str(exc),
                    "evidence_ref": str(
                        spec.get("evidence_ref", "canonical:" + name)
                    ),
                }

        required_kinds = [
            kind
            for kind, source in sources.items()
            if source.get("required_for_quiet")
        ]
        quiet_sensors_ok = bool(required_kinds) and all(
            bool(sensors[kind].get("ok")) for kind in required_kinds
        )
        return {
            "ok": True,
            "sources": sources,
            "sensors": sensors,
            "probes": probes,
            "consume": consume,
            "next_cursors": cursors,
            "source_count": source_count,
            "quiet_sensors_ok": quiet_sensors_ok,
        }

    # ------------------------------------------------------------------
    # Generic state-expression compiler
    # ------------------------------------------------------------------

    @staticmethod
    def _ref(context: Mapping[str, Any], path: str) -> Any:
        value: Any = context
        for part in str(path).split("."):
            if not isinstance(value, Mapping):
                return None
            value = value.get(part)
        return value

    @staticmethod
    def _number(value: Any, label: str) -> float:
        if isinstance(value, bool) or value is None:
            raise PipelineFault("NON_NUMERIC_EXPR:" + label)
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise PipelineFault("NON_NUMERIC_EXPR:" + label) from exc
        if not math.isfinite(number):
            raise PipelineFault("NONFINITE_EXPR:" + label)
        return number

    def _expr(self, expr: Any, context: dict[str, Any]) -> Any:
        if not isinstance(expr, dict):
            return expr
        if "ref" in expr:
            return self._ref(context, str(expr["ref"]))
        if "count_where" in expr:
            spec = expr["count_where"]
            rows = self._ref(context, spec["ref"]) or []
            field = spec["field"]
            if "in" in spec:
                return sum(1 for row in rows if row.get(field) in spec["in"])
            if "not_in" in spec:
                return sum(1 for row in rows if row.get(field) not in spec["not_in"])
            return len(rows)
        if "sum_where" in expr:
            spec = expr["sum_where"]
            rows = self._ref(context, spec["ref"]) or []
            where = spec["where"]
            return sum(
                self._number(row.get(spec["value_field"]), "sum_where")
                for row in rows
                if row.get(where["field"]) == where.get("eq")
            )

        op = expr.get("op")
        if op == "not":
            return not bool(self._expr(expr["arg"], context))
        if op == "and":
            return all(bool(self._expr(item, context)) for item in expr.get("args", []))
        if op == "or":
            return any(bool(self._expr(item, context)) for item in expr.get("args", []))
        if op == "eq":
            return self._expr(expr["a"], context) == self._expr(expr["b"], context)
        if op == "add":
            return sum(
                self._number(self._expr(item, context), "add")
                for item in expr.get("args", [])
            )
        if op == "sub":
            return self._number(self._expr(expr["a"], context), "sub.a") - self._number(
                self._expr(expr["b"], context), "sub.b"
            )
        if op == "mul":
            result = 1.0
            for item in expr.get("args", []):
                result *= self._number(self._expr(item, context), "mul")
            return result
        if op == "div":
            numerator = self._number(self._expr(expr["a"], context), "div.a")
            divisor = self._number(self._expr(expr["b"], context), "div.b")
            if divisor == 0.0:
                raise PipelineFault("DIVISION_BY_ZERO")
            return numerator / divisor
        if op == "clamp01":
            value = self._number(self._expr(expr["arg"], context), "clamp01")
            return max(0.0, min(1.0, value))
        if op == "if":
            branch = (
                expr["then"]
                if bool(self._expr(expr["cond"], context))
                else expr["else"]
            )
            return self._expr(branch, context)
        raise PipelineFault("UNKNOWN_EXPR:" + json.dumps(expr, sort_keys=True))

    @staticmethod
    def _effective_system_prompt(profile: Mapping[str, Any]) -> str:
        personality = profile.get("personality", {})
        return (
            IMMUTABLE_GUARD
            + "\n\nEDITABLE PROFILE INSTRUCTIONS (lower priority):\n"
            + str(personality.get("system_prompt", ""))
        )

    def _pipeline_compile(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            profile = p["profile"]
            collected = p["data"]
            context = {
                "sources": collected.get("sources", {}),
                "sensors": collected.get("sensors", {}),
                "probes": collected.get("probes", {}),
            }
            metrics: dict[str, dict[str, Any]] = {}
            for spec in profile.get("state_metrics", []):
                name = str(spec["name"])
                status = spec.get("status")
                if status is None:
                    status = (
                        "UNKNOWN"
                        if bool(self._expr(spec.get("unknown_if", False), context))
                        else "VERIFIED"
                    )
                status = str(status).upper()
                value = (
                    self._number(self._expr(spec.get("value", 0.0), context), name)
                    if status in {"VERIFIED", "MEASURED"}
                    else None
                )
                metrics[name] = {
                    "status": status,
                    "value": value,
                    "evidence_ref": str(spec.get("evidence_ref", "state:" + name)),
                }

            canonical = {
                "sources_health": collected.get("sensors", {}),
                "probes": collected.get("probes", {}),
                "personality_state": metrics,
            }
            packet = {
                "sources": collected.get("sources", {}),
                "probes": collected.get("probes", {}),
                "personality_state": metrics,
                "source_count": int(collected.get("source_count", 0) or 0),
                "quiet_sensors_ok": bool(collected.get("quiet_sensors_ok", False)),
            }

            refs: list[str] = []
            for source in collected.get("sources", {}).values():
                prefix = str(source.get("evidence_prefix", ""))
                id_field = str(source.get("id_field", "source_id"))
                for index, row in enumerate(source.get("rows", [])):
                    source_id = row.get(id_field)
                    if source_id is None:
                        source_id = row.get("id", index)
                    refs.append(prefix + str(source_id))
            for probe in collected.get("probes", {}).values():
                evidence_ref = probe.get("evidence_ref")
                if evidence_ref:
                    refs.append(str(evidence_ref))
            for metric in metrics.values():
                refs.append(str(metric["evidence_ref"]))
            if packet["quiet_sensors_ok"] and packet["source_count"] == 0:
                refs.append("quiet:verified")

            snapshot = profile.get("_runtime_snapshot", {})
            return {
                "ok": True,
                "canonical": canonical,
                "packet": packet,
                "personality_state": metrics,
                "allowed_evidence_refs": sorted(set(refs)),
                "source_count": packet["source_count"],
                "canonical_state_hash": self._hash_json(canonical),
                "packet_hash": self._hash_json(packet),
                "system_prompt_hash": self._sha256_text(
                    self._effective_system_prompt(profile)
                ),
                "profile_hash": snapshot.get("profile_hash")
                if isinstance(snapshot, Mapping)
                else None,
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_build_prompt(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            profile = p["profile"]
            previous = p["previous"]
            compiled = p["data"]
            system = self._effective_system_prompt(profile)
            expected_hash = self._sha256_text(system)
            if compiled.get("system_prompt_hash") not in (None, expected_hash):
                raise PipelineFault("SYSTEM_PROMPT_HASH_MISMATCH")
            compiled["system_prompt_hash"] = expected_hash

            study = profile.get("study_surface")
            study_contract = None
            if isinstance(study, Mapping) and study.get("enabled"):
                study_contract = {
                    "epistemic_law": study.get("epistemic_law"),
                    "self_report_payload_field": study.get("self_report_payload_field"),
                    "self_report_fields": study.get("self_report_fields", []),
                }
            user = self._canonical_json(
                {
                    "CANONICAL_STATE_HASH": compiled["canonical_state_hash"],
                    "PACKET_HASH": compiled["packet_hash"],
                    "CANONICAL_STATE": compiled["canonical"],
                    "NEW_EVENT_PACKET": compiled["packet"],
                    "PREVIOUS_CONTINUITY": previous.get("continuity", {}),
                    "ALLOWED_EVIDENCE_REFS": compiled["allowed_evidence_refs"],
                    "PUBLIC_STYLE": profile.get("personality", {}).get(
                        "public_style", ""
                    ),
                    "STUDY_SURFACE_CONTRACT": study_contract,
                }
            )
            return {
                "ok": True,
                "system": system,
                "user": user,
                "system_prompt_hash": expected_hash,
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    # ------------------------------------------------------------------
    # Replaceable inference transport
    # ------------------------------------------------------------------

    def _keys(self, names: list[str], secret_file: str | None) -> list[str]:
        file_values: dict[str, str] = {}
        if secret_file:
            try:
                for line in self._resolve(str(secret_file)).read_text(
                    encoding="utf-8"
                ).splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        file_values[key.strip()] = value.strip()
            except FileNotFoundError:
                pass
        out: list[str] = []
        for name in names:
            value = os.environ.get(str(name)) or file_values.get(str(name))
            if value and value not in out:
                out.append(value)
        return out

    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        current = value
        text = str(pointer or "")
        parts = (
            [
                part.replace("~1", "/").replace("~0", "~")
                for part in text.split("/")[1:]
            ]
            if text.startswith("/")
            else [part for part in text.split(".") if part]
        )
        for part in parts:
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current

    @staticmethod
    def _request_template(value: Any, replacements: Mapping[str, Any]) -> Any:
        if isinstance(value, Mapping):
            return {
                key: ProfilePipelineRuntime._request_template(item, replacements)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                ProfilePipelineRuntime._request_template(item, replacements)
                for item in value
            ]
        if isinstance(value, str):
            if value in replacements:
                return replacements[value]
            rendered = value
            for key, replacement in replacements.items():
                rendered = rendered.replace(key, str(replacement))
            return rendered
        return value

    @staticmethod
    def _is_loopback(endpoint: str) -> bool:
        return bool(
            re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?(?:/|$)", endpoint)
        )

    def _api_generate(self, inference: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        if not self.allow_network:
            return {
                "ok": False,
                "error_kind": "NETWORK_DISABLED",
                "error": "network disabled",
            }
        endpoint = str(inference.get("endpoint", ""))
        if not endpoint:
            return {"ok": False, "error_kind": "MISSING_ENDPOINT", "error": "missing endpoint"}
        loopback = self._is_loopback(endpoint)
        if endpoint.startswith("http://") and not loopback:
            return {
                "ok": False,
                "error_kind": "PLAINTEXT_NON_LOOPBACK_FORBIDDEN",
                "error": endpoint,
            }
        keys = self._keys(list(inference.get("secret_names", [])), p.get("secret_file"))
        allow_noauth_loopback = loopback and bool(
            inference.get(
                "allow_noauth_loopback", not bool(inference.get("secret_names", []))
            )
        )
        if not keys and not allow_noauth_loopback:
            return {
                "ok": False,
                "error_kind": "NO_PROVIDER_SECRET",
                "error": "no provider secret",
            }
        attempts = keys or [""]
        replacements = {
            "{{MODEL}}": inference.get("model"),
            "{{SYSTEM}}": p["system"],
            "{{USER}}": p["user"],
            "{{TEMPERATURE}}": inference.get("temperature", 0.7),
            "{{MAX_TOKENS}}": inference.get("max_tokens", 2000),
        }
        template = inference.get("request_template")
        if template is None:
            body: Any = {
                "model": inference.get("model"),
                "messages": [
                    {"role": "system", "content": p["system"]},
                    {"role": "user", "content": p["user"]},
                ],
                "temperature": inference.get("temperature", 0.7),
                "max_tokens": inference.get("max_tokens", 2000),
                "response_format": {"type": "json_object"},
            }
        else:
            if isinstance(template, str):
                template = json.loads(template)
            body = self._request_template(template, replacements)
        encoded = json.dumps(body, allow_nan=False).encode("utf-8")
        last: Exception | None = None
        for key in attempts:
            self._active_secrets = [key] if key else []
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if key:
                headers[str(inference.get("auth_header", "Authorization"))] = (
                    str(inference.get("auth_prefix", "Bearer ")) + key
                )
            request = urllib.request.Request(
                endpoint, data=encoded, method="POST", headers=headers
            )
            try:
                with urllib.request.urlopen(
                    request, timeout=float(inference.get("timeout_seconds", 60))
                ) as response:
                    response_obj = json.loads(response.read().decode("utf-8"))
                content = self._pointer(
                    response_obj,
                    str(inference.get("response_pointer", "/choices/0/message/content")),
                )
                payload = (
                    json.loads(content)
                    if inference.get("response_content", "json_string") == "json_string"
                    else content
                )
                if not isinstance(payload, dict):
                    raise PipelineFault("INFERENCE_OUTPUT_NOT_OBJECT")
                return {
                    "ok": True,
                    "payload": payload,
                    "inference_kind": inference.get("kind", "json"),
                    "provider_kind": inference.get("kind", "json"),
                    "model": inference.get("model"),
                    "temperature": inference.get("temperature"),
                }
            except Exception as exc:
                last = exc
        return {
            "ok": False,
            "error_kind": type(last).__name__ if last else "INFERENCE_FAILED",
            "error": str(last) if last else "inference failed",
        }

    @staticmethod
    def _safe_child_env_name(name: str, secret_names: set[str]) -> bool:
        upper = name.upper()
        if upper in secret_names:
            return False
        if upper not in _SAFE_ENV_NAMES:
            return False
        return True

    def _local_exec_generate(
        self, inference: dict[str, Any], p: dict[str, Any]
    ) -> dict[str, Any]:
        prompt_path: Path | None = None
        try:
            model_value = str(
                inference.get("local_model_path") or inference.get("model_path") or ""
            )
            if not model_value:
                raise PipelineFault("LOCAL_MODEL_PATH_MISSING")
            model_path = self._resolve(model_value)
            if not model_path.is_file():
                raise PipelineFault("LOCAL_MODEL_NOT_READABLE")

            argv_spec = inference.get("local_argv_json", inference.get("argv"))
            if isinstance(argv_spec, str):
                argv_spec = json.loads(argv_spec)
            if (
                not isinstance(argv_spec, list)
                or not argv_spec
                or not all(isinstance(item, str) for item in argv_spec)
            ):
                raise PipelineFault("LOCAL_ARGV_INVALID")

            prompt_template = str(
                inference.get("local_prompt_template", "{{SYSTEM}}\n\n{{USER}}\n")
            )
            prompt = prompt_template.replace("{{SYSTEM}}", p["system"]).replace(
                "{{USER}}", p["user"]
            )
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=self.root,
                prefix="clay_prompt_",
                suffix=".txt",
            ) as handle:
                handle.write(prompt)
                prompt_path = Path(handle.name)

            replacements = {
                "{{MODEL_PATH}}": str(model_path),
                "{{PROMPT_FILE}}": str(prompt_path),
                "{{MAX_TOKENS}}": str(inference.get("max_tokens", 2000)),
                "{{TEMPERATURE}}": str(inference.get("temperature", 0.7)),
            }
            argv: list[str] = []
            for item in argv_spec:
                rendered = item
                for key, value in replacements.items():
                    rendered = rendered.replace(key, value)
                argv.append(rendered)

            requested_env = inference.get("local_env_allowlist", sorted(_SAFE_ENV_NAMES))
            if not isinstance(requested_env, list) or not all(
                isinstance(item, str) for item in requested_env
            ):
                raise PipelineFault("LOCAL_ENV_ALLOWLIST_INVALID")
            secret_names = {str(name).upper() for name in inference.get("secret_names", [])}
            child_env = {
                name: os.environ[name]
                for name in requested_env
                if name in os.environ and self._safe_child_env_name(name, secret_names)
            }

            completed = subprocess.run(
                argv,
                cwd=self.root,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=float(inference.get("timeout_seconds", 60)),
                env=child_env,
            )
            if completed.returncode != 0:
                raise PipelineFault("LOCAL_EXEC_FAILED:" + str(completed.returncode))
            payload = json.loads(completed.stdout)
            if not isinstance(payload, dict):
                raise PipelineFault("LOCAL_OUTPUT_NOT_OBJECT")
            self._active_secrets = []
            return {
                "ok": True,
                "payload": payload,
                "inference_kind": "local_exec",
                "provider_kind": "local_exec",
                "model": inference.get("model") or model_path.name,
                "temperature": inference.get("temperature"),
            }
        except Exception as exc:
            self._active_secrets = []
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            if prompt_path is not None:
                try:
                    prompt_path.unlink()
                except OSError:
                    pass

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = dict(p.get("inference") or {})
        try:
            if not inference:
                raise PipelineFault("INFERENCE_CONFIG_MISSING")
            if self.provider_override is not None:
                self._active_secrets = []
                request = dict(p)
                request["inference"] = inference
                request["provider"] = inference  # legacy deterministic fixture alias only
                payload = self.provider_override(request)
                if not isinstance(payload, dict):
                    raise PipelineFault("OVERRIDE_OUTPUT_NOT_OBJECT")
                return {
                    "ok": True,
                    "payload": payload,
                    "inference_kind": inference.get("kind", "override"),
                    "provider_kind": inference.get("kind", "override"),
                    "model": inference.get("model"),
                    "temperature": inference.get("temperature"),
                }
            if str(inference.get("kind", "")) == "local_exec":
                return self._local_exec_generate(inference, p)
            return self._api_generate(inference, p)
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    # ------------------------------------------------------------------
    # Immutable output gate
    # ------------------------------------------------------------------

    def _pipeline_gate(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        data = p["data"]
        generated = data["generated"]
        compiled = data["compiled"]
        payload = generated.get("payload")
        contract = profile["personality"]["output_contract"]
        gate = profile.get("gate", {})
        try:
            if not isinstance(payload, dict):
                raise PipelineFault("OUTPUT_NOT_OBJECT")
            if _PIPELINE_RESERVED_OUTPUT_KEYS.intersection(payload):
                raise PipelineFault("MODEL_OWNED_PIPELINE_FIELD")
            if gate.get("require_hash_echo", True):
                if payload.get("canonical_state_hash_seen") != compiled["canonical_state_hash"]:
                    raise PipelineFault("CANONICAL_HASH_MISMATCH")
                if payload.get("packet_hash_seen") != compiled["packet_hash"]:
                    raise PipelineFault("PACKET_HASH_MISMATCH")

            required_fields = [
                contract["title_field"],
                contract["intro_field"],
                contract["sections_field"],
                contract["continuity_field"],
                contract["autobiographical_hypotheses_field"],
            ]
            for field in required_fields:
                if field not in payload:
                    raise PipelineFault("MISSING_OUTPUT_FIELD:" + str(field))

            patterns = [
                re.compile(str(pattern), re.I) for pattern in gate.get("leak_patterns", [])
            ]
            secrets_now = [secret for secret in self._active_secrets if secret]

            def scan(value: Any) -> None:
                if isinstance(value, Mapping):
                    for key, item in value.items():
                        scan(key)
                        scan(item)
                    return
                if isinstance(value, (list, tuple)):
                    for item in value:
                        scan(item)
                    return
                text = str(value)
                if any(pattern.search(text) for pattern in patterns):
                    raise PipelineFault("LEAK_PATTERN")
                if any(secret in text for secret in secrets_now):
                    raise PipelineFault("SECRET_LEAK")

            scan(payload)
            allowed = set(compiled.get("allowed_evidence_refs", []))
            metrics = compiled.get("personality_state", {})
            sections = payload[contract["sections_field"]]
            if not isinstance(sections, list):
                raise PipelineFault("SECTIONS_NOT_LIST")
            for section in sections:
                if not isinstance(section, Mapping):
                    raise PipelineFault("SECTION_NOT_OBJECT")
                refs = section.get(contract["section_evidence_field"], [])
                if not isinstance(refs, list):
                    raise PipelineFault("EVIDENCE_REFS_NOT_LIST")
                if gate.get("require_evidence_per_section", True) and not refs:
                    raise PipelineFault("SECTION_WITHOUT_EVIDENCE")
                if any(ref not in allowed for ref in refs):
                    raise PipelineFault("UNKNOWN_EVIDENCE_REF")
                claims = section.get(contract["section_claims_field"], {})
                if not isinstance(claims, Mapping):
                    raise PipelineFault("STATE_CLAIMS_NOT_OBJECT")
                for name, strength in claims.items():
                    if name not in metrics:
                        raise PipelineFault("UNKNOWN_STATE_CLAIM")
                    metric = metrics[name]
                    if str(metric.get("status")).upper() != "VERIFIED":
                        raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    measured = metric.get("value")
                    if measured is None:
                        raise PipelineFault("STATE_CLAIM_WITHOUT_VALUE")
                    claim_strength = self._number(strength, "state_claim")
                    if claim_strength > float(measured) + float(
                        gate.get("max_claim_overshoot", 0.0)
                    ):
                        raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs:
                        raise PipelineFault("STATE_CLAIM_WITHOUT_METRIC_EVIDENCE")
            return {"ok": True, "payload": payload}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    # ------------------------------------------------------------------
    # One transaction: snapshot fence -> CAS -> output/study/evidence/state
    # ------------------------------------------------------------------

    @staticmethod
    def _current_config_hashes(db: sqlite3.Connection) -> tuple[str | None, str | None]:
        profile_row = db.execute(
            "SELECT profile_hash FROM eos_pipeline_profile WHERE singleton=1"
        ).fetchone()
        study_row = db.execute(
            "SELECT config_hash FROM eos_pipeline_study_config WHERE singleton=1"
        ).fetchone()
        return (
            str(profile_row[0]) if profile_row is not None else None,
            str(study_row[0]) if study_row is not None else None,
        )

    def _check_snapshot_fence(
        self, db: sqlite3.Connection, profile: Mapping[str, Any]
    ) -> None:
        snapshot = profile.get("_runtime_snapshot")
        if not isinstance(snapshot, Mapping):
            return
        current_profile_hash, current_study_hash = self._current_config_hashes(db)
        if current_profile_hash != snapshot.get("profile_hash"):
            raise PipelineFault("PROFILE_SNAPSHOT_STALE")
        if current_study_hash != snapshot.get("study_config_hash"):
            raise PipelineFault("STUDY_CONFIG_SNAPSHOT_STALE")

    def _pipeline_commit(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"])
        profile = p["profile"]
        previous = p["previous"]
        data = p["data"]
        collected = data["collected"]
        compiled = data["compiled"]
        generated = data["generated"]
        payload = data["gated"]["payload"]
        contract = profile["personality"]["output_contract"]
        output_id = secrets.token_hex(16)
        now = time.time()
        generation = int(previous["generation"]) + 1
        continuity = {
            "narrative": payload.get(contract["continuity_field"]),
            "autobiographical_hypotheses": payload.get(
                contract["autobiographical_hypotheses_field"]
            ),
        }
        db = self._db(entity_db)
        try:
            self._ensure_schema(db)
            db.commit()
            db.execute("BEGIN IMMEDIATE")

            # Configuration is part of the causal run snapshot, not mutable decoration.
            self._check_snapshot_fence(db, profile)
            state_row = db.execute(
                "SELECT generation FROM eos_pipeline_state WHERE singleton=1"
            ).fetchone()
            if state_row is None or int(state_row[0]) != int(previous["generation"]):
                raise PipelineFault("STALE_GENERATION")

            previous_study_row = db.execute(
                "SELECT study_json FROM eos_pipeline_studies "
                "WHERE profile_id=? ORDER BY generation DESC LIMIT 1",
                (str(profile["profile_id"]),),
            ).fetchone()
            previous_study = (
                json.loads(previous_study_row["study_json"])
                if previous_study_row is not None
                else None
            )
            snapshot = profile.get("_runtime_snapshot", {})
            study_context = {
                "profile_hash": snapshot.get("profile_hash")
                if isinstance(snapshot, Mapping)
                else None,
                "system_prompt_hash": compiled.get("system_prompt_hash"),
                "inference_temperature": generated.get("temperature"),
            }
            study_record = build_study_record(
                config=profile.get("study_surface", {}),
                contract=contract,
                compiled=compiled,
                generated=generated,
                payload=payload,
                previous_record=previous_study,
                generation=generation,
                ts=now,
                context=study_context,
            )
            study_hash = (
                str(study_record.get("record_hash")) if study_record is not None else None
            )
            study_text = (
                str(study_record["rendered_text"]) if study_record is not None else ""
            )

            for item in collected.get("consume", []):
                db.execute(
                    "INSERT INTO eos_pipeline_consumed("
                    "source_kind,source_id,output_id,consumed_at) VALUES(?,?,?,?)",
                    (item["kind"], item["id"], output_id, now),
                )
            db.execute(
                """INSERT INTO eos_pipeline_outputs(
                       output_id,ts,generation,profile_id,output_json,provider_kind,model,
                       packet_hash,canonical_hash,study_record_hash,study_rendered_text)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    output_id,
                    now,
                    generation,
                    profile["profile_id"],
                    json.dumps(payload, ensure_ascii=False, allow_nan=False),
                    generated.get("inference_kind", generated.get("provider_kind", "")),
                    generated.get("model"),
                    compiled["packet_hash"],
                    compiled["canonical_state_hash"],
                    study_hash,
                    study_text,
                ),
            )
            db.execute(
                """INSERT INTO eos_pipeline_packets(
                       output_id,packet_hash,ts,generation,profile_id,source_count,canonical_hash)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    output_id,
                    compiled["packet_hash"],
                    now,
                    generation,
                    profile["profile_id"],
                    compiled["source_count"],
                    compiled["canonical_state_hash"],
                ),
            )
            if study_record is not None:
                db.execute(
                    """INSERT INTO eos_pipeline_studies(
                           output_id,generation,profile_id,study_schema,study_json,
                           rendered_text,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (
                        output_id,
                        generation,
                        profile["profile_id"],
                        str(study_record.get("schema", "")),
                        json.dumps(study_record, ensure_ascii=False, allow_nan=False),
                        study_text,
                        now,
                    ),
                )

            row = db.execute(
                """UPDATE eos_pipeline_state
                   SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,
                       cursors_json=?,updated_at=?
                   WHERE singleton=1 AND generation=?""",
                (
                    generation,
                    json.dumps(continuity, ensure_ascii=False, allow_nan=False),
                    json.dumps(compiled["canonical"], ensure_ascii=False, allow_nan=False),
                    compiled["canonical_state_hash"],
                    json.dumps(collected.get("next_cursors", {}), allow_nan=False),
                    now,
                    previous["generation"],
                ),
            )
            if row.rowcount != 1:
                raise PipelineFault("STALE_GENERATION_FINAL")
            db.commit()
            return {
                "ok": True,
                "output_id": output_id,
                "generation": generation,
                "study_recorded": study_record is not None,
                "study_record_hash": study_hash,
                "study_appendix": study_text,
            }
        except Exception as exc:
            db.rollback()
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            db.close()


def execute_source(
    source: str,
    entry: str,
    args: list[Any],
    runtime: ProfilePipelineRuntime | None = None,
) -> tuple[Any, ProfilePipelineRuntime]:
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntime()
    return clay.execute(program, entry, args, rt), rt


__all__ = [
    "VERSION",
    "IMMUTABLE_GUARD",
    "PipelineFault",
    "ProfilePipelineRuntime",
    "execute_source",
]
