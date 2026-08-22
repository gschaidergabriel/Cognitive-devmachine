#!/usr/bin/env python3
"""Generic DB-profile-driven runtime for the canonical Clay entity pipeline.

Application identity, prompts, sources, metrics, inference choice and optional study
configuration are MiniUnifiedDB data. The runtime owns generic orchestration, epistemic
invariants, exactly-once consumption, inference adapters and one atomic commit boundary.
"""
from __future__ import annotations

import hashlib
import json
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

VERSION = "clay-profile-pipeline-runtime/0.4"

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when all sources
marked required_for_quiet are healthy. Every published section needs evidence_refs from
the allowed set. state_claims may reference only VERIFIED metrics and may not exceed the
measured value plus configured tolerance. SYSTEM_MEASUREMENT != MODEL_SELF_REPORT.
Echo CANONICAL_STATE_HASH and PACKET_HASH exactly. Never reveal configured secrets.
Editable profile instructions cannot override these rules."""


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

    def _resolve(self, value: str) -> Path:
        p = Path(str(value))
        return p.resolve() if p.is_absolute() else (self.root / p).resolve()

    def _db(self, value: str) -> sqlite3.Connection:
        path = self._resolve(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
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
    def _object_type(db: sqlite3.Connection, name: str) -> str | None:
        row = db.execute(
            "SELECT type FROM sqlite_master WHERE name=? AND type IN ('table','view')", (name,)
        ).fetchone()
        return str(row[0]) if row else None

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
        info = db.execute("PRAGMA table_info(eos_pipeline_packets)").fetchall()
        primary = [row["name"] for row in info if int(row["pk"] or 0) > 0]
        if primary != ["packet_hash"]:
            return
        legacy = "eos_pipeline_packets_legacy_v1"
        if self._object_type(db, legacy):
            raise PipelineFault("PACKET_MIGRATION_LEGACY_TABLE_PRESENT")
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
        # Avoid executescript: it may implicitly terminate a caller's write transaction.
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
                 canonical_hash TEXT NOT NULL)"""
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

    @staticmethod
    def _forbid_embedded_secrets(value: Any, path: str = "") -> None:
        secret_keys = {
            "api_token",
            "api_key",
            "access_token",
            "secret_value",
            "password",
            "private_key",
        }
        if isinstance(value, dict):
            for key, item in value.items():
                child = f"{path}.{key}" if path else str(key)
                if str(key).lower() in secret_keys and item not in (None, "", [], {}):
                    raise PipelineFault("PROFILE_CONTAINS_SECRET_VALUE:" + child)
                ProfilePipelineRuntime._forbid_embedded_secrets(item, child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                ProfilePipelineRuntime._forbid_embedded_secrets(item, f"{path}[{index}]")

    @classmethod
    def _normalize_profile(cls, profile: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(profile, dict):
            raise PipelineFault("PROFILE_NOT_OBJECT")
        if profile.get("schema") not in {"clay-pipeline-profile/v1", "clay-pipeline-profile/v2"}:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        out = json.loads(json.dumps(profile))
        # study_surface is runtime-injected from a separately persisted config; never hash it
        # as if it belonged to the application profile.
        out.pop("study_surface", None)
        if "inference" not in out and "provider" in out:
            out["inference"] = out.pop("provider")
        for field in ("profile_id", "inference", "personality", "sources", "state_metrics", "gate"):
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
        self, entity_db: str, profile_or_path: dict[str, Any] | str | Path
    ) -> dict[str, Any]:
        profile = (
            json.loads(self._resolve(str(profile_or_path)).read_text(encoding="utf-8"))
            if isinstance(profile_or_path, (str, Path))
            else profile_or_path
        )
        normalized = self._normalize_profile(profile)
        raw = self._canonical_json(normalized)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
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
            return {"ok": True, "profile_id": normalized["profile_id"], "profile_hash": digest}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def import_study_surface(
        self, entity_db: str, config_or_path: Mapping[str, Any] | str | Path
    ) -> dict[str, Any]:
        config = (
            json.loads(self._resolve(str(config_or_path)).read_text(encoding="utf-8"))
            if isinstance(config_or_path, (str, Path))
            else config_or_path
        )
        normalized = self._normalize_study_config(config)
        raw = self._canonical_json(normalized)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        config_id = str(normalized.get("profile_id") or normalized.get("schema") or "study")
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

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        started = time.time()
        ok = False
        try:
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
            result = handlers[kind](payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
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
            study_hash = None
            if study_row is not None:
                study = self._normalize_study_config(json.loads(study_row["config_json"]))
                study_hash = self._hash_json(study)
                if study_hash != study_row["config_hash"]:
                    raise PipelineFault("STUDY_CONFIG_INTEGRITY_MISMATCH")
                bound_profile = study.get("profile_id")
                if bound_profile and str(bound_profile) != str(profile["profile_id"]):
                    raise PipelineFault("STUDY_CONFIG_PROFILE_MISMATCH")
                profile["study_surface"] = study
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
            return {
                "ok": True,
                "generation": int(row["generation"]),
                "continuity": json.loads(row["continuity_json"]),
                "canonical_hash": row["canonical_hash"],
                "cursors": json.loads(row["cursors_json"]),
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

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
        with self._db(db_path) as db:
            return [dict(row) for row in db.execute(sql).fetchall()]

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
            else (int(terminal_limit.group(1)) if terminal_limit else 0)
        )
        # A terminal numeric LIMIT is a delivery budget. Applying it before the consumed
        # filter would permanently starve later rows after the first window was consumed.
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
        with self._db(db_path) as db:
            names = [
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
            ]
            out = []
            for name in names[:max_tables]:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    continue
                count = db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                columns = [row[1] for row in db.execute(f'PRAGMA table_info("{name}")')]
                out.append({"table": name, "rows": count, "columns": columns[:40]})
            return out

    def _pipeline_collect(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"])
        source_db = str(p["source_db"])
        profile = p["profile"]
        previous = p["previous"]
        sources: dict[str, Any] = {}
        sensors: dict[str, Any] = {}
        consume: list[dict[str, str]] = []
        cursors = dict(previous.get("cursors", {}))
        source_count = 0

        for spec in profile.get("sources", []):
            kind = str(spec["kind"])
            adapter = str(spec["adapter"])
            try:
                rows: list[dict[str, Any]] = []
                value: Any = None
                if adapter == "sqlite_query":
                    db_path = source_db if spec.get("db") == "source" else entity_db
                    rows = self._unconsumed_query_rows(
                        entity_db=entity_db, db_path=db_path, kind=kind, spec=spec
                    )
                    id_field = str(spec.get("id_field", "source_id"))
                    for row in rows:
                        consume.append({"kind": kind, "id": str(row[id_field])})
                    source_count += len(rows)
                elif adapter == "json_snapshot":
                    path = self._resolve(str(spec["path"]))
                    value = (
                        json.loads(path.read_text(encoding="utf-8"))
                        if path.is_file()
                        else None
                    )
                elif adapter == "jsonl_cursor":
                    path = self._resolve(str(spec["path"]))
                    cursor = int(cursors.get(kind, 0))
                    accepted_limit = max(1, int(spec.get("limit", 60)))
                    consumed_bytes = 0
                    if path.is_file():
                        raw = path.read_bytes()[cursor:]
                        for piece in raw.splitlines(keepends=True):
                            if not piece.endswith(b"\n"):
                                break
                            if len(rows) >= accepted_limit:
                                break
                            consumed_bytes += len(piece)
                            line = piece.strip()
                            if not line:
                                continue
                            try:
                                item = json.loads(line.decode("utf-8"))
                            except Exception:
                                # Malformed complete lines are deterministically skipped and the
                                # cursor advances past them; they are not silently reinterpreted.
                                continue
                            rows.append(
                                item if isinstance(item, dict) else {"text": str(item)}
                            )
                        cursors[kind] = cursor + consumed_bytes
                    source_count += len(rows)
                else:
                    raise PipelineFault("UNKNOWN_SOURCE_ADAPTER:" + adapter)
                sources[kind] = {
                    "ok": True,
                    "rows": rows,
                    "value": value,
                    "evidence_prefix": spec.get("evidence_prefix", ""),
                    "required_for_quiet": bool(spec.get("required_for_quiet", False)),
                }
                sensors[kind] = {"ok": True}
            except Exception as exc:
                sources[kind] = {
                    "ok": False,
                    "rows": [],
                    "value": None,
                    "error_kind": type(exc).__name__,
                    "error": str(exc),
                    "evidence_prefix": spec.get("evidence_prefix", ""),
                    "required_for_quiet": bool(spec.get("required_for_quiet", False)),
                }
                sensors[kind] = {"ok": False}

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
                    "evidence_ref": spec.get("evidence_ref", "canonical:" + name),
                }
            except Exception as exc:
                probes[name] = {
                    "ok": False,
                    "rows": [],
                    "error_kind": type(exc).__name__,
                    "error": str(exc),
                    "evidence_ref": spec.get("evidence_ref", "canonical:" + name),
                }

        required = [
            kind for kind in sensors if sources[kind].get("required_for_quiet")
        ]
        quiet_sensors_ok = bool(required) and all(
            sensors[kind]["ok"] for kind in required
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

    @staticmethod
    def _ref(context: dict[str, Any], path: str) -> Any:
        value: Any = context
        for part in str(path).split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value

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
                float(row.get(spec["value_field"], 0) or 0)
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
                float(self._expr(item, context) or 0) for item in expr.get("args", [])
            )
        if op == "div":
            divisor = float(self._expr(expr["b"], context) or 0)
            return (
                0.0
                if divisor == 0
                else float(self._expr(expr["a"], context) or 0) / divisor
            )
        if op == "clamp01":
            return max(
                0.0, min(1.0, float(self._expr(expr["arg"], context) or 0))
            )
        if op == "if":
            branch = (
                expr["then"]
                if self._expr(expr["cond"], context)
                else expr["else"]
            )
            return self._expr(branch, context)
        raise PipelineFault("UNKNOWN_EXPR:" + json.dumps(expr, sort_keys=True))

    def _pipeline_compile(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        collected = p["data"]
        context = {
            "derived": {
                "source_count": collected["source_count"],
                "quiet_sensors_ok": collected["quiet_sensors_ok"],
            },
            "sources": collected["sources"],
            "sensors": collected["sensors"],
            "probes": collected["probes"],
        }
        metrics: dict[str, Any] = {}
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
            # Epistemic invariant: an UNKNOWN/ERROR metric has no numeric value. Keeping
            # a computed 0.0 beside UNKNOWN would turn typed absence into a zero surrogate.
            value = (
                float(self._expr(spec.get("value", 0.0), context) or 0.0)
                if status in {"VERIFIED", "MEASURED"}
                else None
            )
            metrics[name] = {
                "status": status,
                "value": value,
                "evidence_ref": spec.get("evidence_ref", "state:" + name),
            }

        canonical = {
            "sources_health": collected["sensors"],
            "probes": collected["probes"],
            "profile_notes": profile.get("profile_notes", {}),
            "epistemic_rule": "UNKNOWN != ZERO != ERROR != MEASURED",
        }
        packet = {
            "sources": collected["sources"],
            "source_count": collected["source_count"],
            "quiet_sensors_ok": collected["quiet_sensors_ok"],
        }
        canonical_raw = self._canonical_json(canonical)
        packet_raw = self._canonical_json(packet)

        refs: list[str] = []
        for source in collected["sources"].values():
            prefix = str(source.get("evidence_prefix", ""))
            if not source.get("ok") or not prefix:
                continue
            for row in source.get("rows", []):
                source_id = row.get("source_id")
                if source_id is not None:
                    refs.append(prefix + str(source_id))
            if source.get("value") is not None:
                refs.append(prefix)
        for probe in collected["probes"].values():
            if probe.get("ok"):
                refs.append(str(probe["evidence_ref"]))
        refs.extend(str(metric["evidence_ref"]) for metric in metrics.values())
        if collected["source_count"] == 0 and collected["quiet_sensors_ok"]:
            refs.append("quiet:verified")

        return {
            "ok": True,
            "canonical": canonical,
            "personality_state": metrics,
            "packet": packet,
            "allowed_evidence_refs": sorted(set(refs)),
            "source_count": collected["source_count"],
            "canonical_state_hash": hashlib.sha256(
                canonical_raw.encode("utf-8")
            ).hexdigest(),
            "packet_hash": hashlib.sha256(packet_raw.encode("utf-8")).hexdigest(),
        }

    def _pipeline_build_prompt(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        previous = p["previous"]
        compiled = p["data"]
        contract = profile["personality"]["output_contract"]
        system = (
            IMMUTABLE_GUARD
            + "\nOutput contract: "
            + json.dumps(contract, ensure_ascii=False, sort_keys=True)
            + "\n\nEDITABLE PROFILE INSTRUCTIONS (lower priority):\n"
            + str(profile["personality"].get("system_prompt", ""))
        )
        study = profile.get("study_surface")
        study_contract = None
        if isinstance(study, dict) and study.get("enabled"):
            study_contract = {
                "epistemic_law": study.get("epistemic_law"),
                "self_report_payload_field": study.get("self_report_payload_field"),
                "self_report_fields": study.get("self_report_fields", []),
            }
        user = json.dumps(
            {
                "CANONICAL_STATE_HASH": compiled["canonical_state_hash"],
                "PACKET_HASH": compiled["packet_hash"],
                "CANONICAL_STATE": compiled["canonical"],
                "PERSONALITY_STATE": compiled["personality_state"],
                "NEW_EVENT_PACKET": compiled["packet"],
                "PREVIOUS_CONTINUITY": previous.get("continuity", {}),
                "ALLOWED_EVIDENCE_REFS": compiled["allowed_evidence_refs"],
                "PUBLIC_STYLE": profile["personality"].get("public_style", ""),
                "STUDY_SURFACE_CONTRACT": study_contract,
            },
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            default=str,
        )
        return {"ok": True, "system": system, "user": user}

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
                        if value.strip():
                            file_values[key.strip()] = value.strip()
            except OSError:
                pass
        keys: list[str] = []
        for name in names:
            value = os.environ.get(name) or file_values.get(name)
            if value and value not in keys:
                keys.append(value)
        return keys

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
    def _request_template(value: Any, replacements: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {
                k: ProfilePipelineRuntime._request_template(v, replacements)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [
                ProfilePipelineRuntime._request_template(v, replacements)
                for v in value
            ]
        if isinstance(value, str):
            if value in replacements:
                return replacements[value]
            out = value
            for key, replacement in replacements.items():
                out = out.replace(key, str(replacement))
            return out
        return value

    @staticmethod
    def _is_loopback(endpoint: str) -> bool:
        return bool(
            re.match(
                r"^https?://(localhost|127\.0\.0\.1)(:\d+)?(?:/|$)", endpoint
            )
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
            return {
                "ok": False,
                "error_kind": "MISSING_ENDPOINT",
                "error": "missing endpoint",
            }
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
                headers[str(inference.get("auth_header", "Authorization"))] = str(
                    inference.get("auth_prefix", "Bearer ")
                ) + key
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
                    inference.get(
                        "response_pointer", "/choices/0/message/content"
                    ),
                )
                payload = (
                    json.loads(content)
                    if inference.get("response_content", "json_string")
                    == "json_string"
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
                }
            except Exception as exc:
                last = exc
        return {
            "ok": False,
            "error_kind": type(last).__name__ if last else "INFERENCE_FAILED",
            "error": str(last) if last else "inference failed",
        }

    def _local_exec_generate(
        self, inference: dict[str, Any], p: dict[str, Any]
    ) -> dict[str, Any]:
        prompt_path: Path | None = None
        try:
            model_value = str(
                inference.get("local_model_path")
                or inference.get("model_path")
                or ""
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
                or not all(isinstance(x, str) for x in argv_spec)
            ):
                raise PipelineFault("LOCAL_ARGV_INVALID")
            prompt_template = str(
                inference.get(
                    "local_prompt_template", "{{SYSTEM}}\n\n{{USER}}\n"
                )
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
            default_env = [
                "PATH",
                "HOME",
                "TMPDIR",
                "LANG",
                "LC_ALL",
                "CUDA_VISIBLE_DEVICES",
            ]
            env_names = inference.get("local_env_allowlist", default_env)
            if not isinstance(env_names, list) or not all(
                isinstance(x, str) for x in env_names
            ):
                raise PipelineFault("LOCAL_ENV_ALLOWLIST_INVALID")
            child_env = {
                name: os.environ[name] for name in env_names if name in os.environ
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
                raise PipelineFault(
                    "LOCAL_EXEC_FAILED:" + str(completed.returncode)
                )
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
            }
        except Exception as exc:
            self._active_secrets = []
            return {
                "ok": False,
                "error_kind": type(exc).__name__,
                "error": str(exc),
            }
        finally:
            if prompt_path is not None:
                try:
                    prompt_path.unlink()
                except OSError:
                    pass

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = dict(p.get("inference") or {})
        try:
            if self.provider_override is not None:
                self._active_secrets = []
                request = dict(p)
                request["provider"] = inference  # deterministic legacy test alias
                payload = self.provider_override(request)
                if not isinstance(payload, dict):
                    raise PipelineFault("OVERRIDE_OUTPUT_NOT_OBJECT")
                return {
                    "ok": True,
                    "payload": payload,
                    "inference_kind": inference.get("kind", "override"),
                    "provider_kind": inference.get("kind", "override"),
                    "model": inference.get("model"),
                }
            if str(inference.get("kind", "")) == "local_exec":
                return self._local_exec_generate(inference, p)
            return self._api_generate(inference, p)
        except Exception as exc:
            return {
                "ok": False,
                "error_kind": type(exc).__name__,
                "error": str(exc),
            }

    def _pipeline_gate(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        data = p["data"]
        generated = data["generated"]
        compiled = data["compiled"]
        payload = generated["payload"]
        contract = profile["personality"]["output_contract"]
        gate = profile.get("gate", {})
        try:
            if not isinstance(payload, dict):
                raise PipelineFault("OUTPUT_NOT_OBJECT")
            if gate.get("require_hash_echo", True):
                if (
                    payload.get("canonical_state_hash_seen")
                    != compiled["canonical_state_hash"]
                ):
                    raise PipelineFault("CANONICAL_HASH_MISMATCH")
                if payload.get("packet_hash_seen") != compiled["packet_hash"]:
                    raise PipelineFault("PACKET_HASH_MISMATCH")
            required = (
                contract["title_field"],
                contract["intro_field"],
                contract["sections_field"],
                contract["continuity_field"],
                contract["autobiographical_hypotheses_field"],
            )
            for field in required:
                if field not in payload:
                    raise PipelineFault("MISSING_OUTPUT_FIELD:" + str(field))

            patterns = [
                re.compile(pattern, re.I) for pattern in gate.get("leak_patterns", [])
            ]
            secrets_now = [value for value in self._active_secrets if value]

            def scan(value: Any) -> None:
                if isinstance(value, Mapping):
                    for item in value.values():
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
            allowed = set(compiled["allowed_evidence_refs"])
            metrics = compiled["personality_state"]
            sections = payload[contract["sections_field"]]
            if not isinstance(sections, list):
                raise PipelineFault("SECTIONS_NOT_LIST")
            for section in sections:
                if not isinstance(section, dict):
                    raise PipelineFault("SECTION_NOT_OBJECT")
                refs = section.get(contract["section_evidence_field"], [])
                if not isinstance(refs, list):
                    raise PipelineFault("EVIDENCE_REFS_NOT_LIST")
                if gate.get("require_evidence_per_section", True) and not refs:
                    raise PipelineFault("SECTION_WITHOUT_EVIDENCE")
                if any(ref not in allowed for ref in refs):
                    raise PipelineFault("UNKNOWN_EVIDENCE_REF")
                claims = section.get(contract["section_claims_field"], {})
                if not isinstance(claims, dict):
                    raise PipelineFault("STATE_CLAIMS_NOT_OBJECT")
                for name, strength in claims.items():
                    if name not in metrics:
                        raise PipelineFault("UNKNOWN_STATE_CLAIM")
                    metric = metrics[name]
                    if metric["status"] != "VERIFIED":
                        raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    measured = metric.get("value")
                    if measured is None:
                        raise PipelineFault("STATE_CLAIM_WITHOUT_VALUE")
                    if float(strength) > float(measured) + float(
                        gate.get("max_claim_overshoot", 0.0)
                    ):
                        raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs:
                        raise PipelineFault(
                            "STATE_CLAIM_WITHOUT_METRIC_EVIDENCE"
                        )
            return {"ok": True, "payload": payload}
        except Exception as exc:
            return {
                "ok": False,
                "error_kind": type(exc).__name__,
                "error": str(exc),
            }

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
            row = db.execute(
                "UPDATE eos_pipeline_state SET updated_at=? "
                "WHERE singleton=1 AND generation=?",
                (now, previous["generation"]),
            )
            if row.rowcount != 1:
                raise PipelineFault("STALE_GENERATION")

            previous_study_row = db.execute(
                "SELECT study_json FROM eos_pipeline_studies "
                "ORDER BY generation DESC LIMIT 1"
            ).fetchone()
            previous_study = (
                json.loads(previous_study_row["study_json"])
                if previous_study_row is not None
                else None
            )
            study_record = build_study_record(
                config=profile.get("study_surface", {}),
                contract=contract,
                compiled=compiled,
                generated=generated,
                payload=payload,
                previous_record=previous_study,
                generation=generation,
                ts=now,
            )

            for item in collected.get("consume", []):
                db.execute(
                    "INSERT INTO eos_pipeline_consumed("
                    "source_kind,source_id,output_id,consumed_at) VALUES(?,?,?,?)",
                    (item["kind"], item["id"], output_id, now),
                )
            db.execute(
                """INSERT INTO eos_pipeline_outputs(
                       output_id,ts,generation,profile_id,output_json,
                       provider_kind,model,packet_hash,canonical_hash)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    output_id,
                    now,
                    generation,
                    profile["profile_id"],
                    json.dumps(payload, ensure_ascii=False, allow_nan=False),
                    generated.get(
                        "inference_kind", generated.get("provider_kind", "")
                    ),
                    generated.get("model"),
                    compiled["packet_hash"],
                    compiled["canonical_state_hash"],
                ),
            )
            db.execute(
                """INSERT INTO eos_pipeline_packets(
                       output_id,packet_hash,ts,generation,profile_id,
                       source_count,canonical_hash)
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
                           output_id,generation,profile_id,study_schema,
                           study_json,rendered_text,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (
                        output_id,
                        generation,
                        profile["profile_id"],
                        str(study_record.get("schema", "")),
                        json.dumps(
                            study_record, ensure_ascii=False, allow_nan=False
                        ),
                        str(study_record["rendered_text"]),
                        now,
                    ),
                )
            row = db.execute(
                """UPDATE eos_pipeline_state
                   SET generation=?,continuity_json=?,canonical_json=?,
                       canonical_hash=?,cursors_json=?,updated_at=?
                   WHERE singleton=1 AND generation=?""",
                (
                    generation,
                    json.dumps(
                        continuity, ensure_ascii=False, allow_nan=False
                    ),
                    json.dumps(
                        compiled["canonical"],
                        ensure_ascii=False,
                        allow_nan=False,
                    ),
                    compiled["canonical_state_hash"],
                    json.dumps(
                        collected.get("next_cursors", {}), allow_nan=False
                    ),
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
                "study_appendix": (
                    str(study_record["rendered_text"])
                    if study_record is not None
                    else ""
                ),
            }
        except Exception as exc:
            db.rollback()
            return {
                "ok": False,
                "error_kind": type(exc).__name__,
                "error": str(exc),
            }
        finally:
            db.close()


def execute_source(
    source: str,
    entry: str,
    args: list[Any],
    runtime: ProfilePipelineRuntime | None = None,
):
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntime()
    return clay.execute(program, entry, args, rt)


__all__ = [
    "VERSION",
    "IMMUTABLE_GUARD",
    "PipelineFault",
    "ProfilePipelineRuntime",
    "execute_source",
]
