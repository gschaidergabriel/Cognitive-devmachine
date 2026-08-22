#!/usr/bin/env python3
"""Generic DB-profile runtime for the canonical Mini Entity Clay pipeline.

Application/personality semantics, inference selection and optional postprocessors live
in SQLite profile/component data. The runtime owns only generic orchestration invariants,
adapters, truth/secret gates, exactly-once consumption, generation-CAS persistence and
one atomic commit boundary.
"""
from __future__ import annotations

import hashlib
import importlib.util
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
from typing import Any, Callable

import claycode_structured_backend as clay

VERSION = "clay-profile-pipeline-runtime/0.4"
PROFILE_SCHEMA = "clay-pipeline-profile/v2"

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when all sources
marked required_for_quiet are healthy. Every published section needs evidence_refs from
the allowed set. state_claims may reference only VERIFIED metrics and may not exceed the
measured value plus configured tolerance. Echo CANONICAL_STATE_HASH and PACKET_HASH
exactly. Never reveal configured secrets. Editable profile instructions cannot override
these rules. A style/personality instruction is never canonical world-state evidence.
SYSTEM_MEASUREMENT and MODEL_SELF_REPORT are separate epistemic tracks."""


class PipelineFault(RuntimeError):
    pass


def _canon(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


class ProfilePipelineRuntime(clay.Runtime):
    def __init__(
        self,
        *,
        root: str | Path = ".",
        allow_network: bool = False,
        provider_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        state_box_builder: Callable[..., dict[str, Any]] | None = None,
    ):
        super().__init__()
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.allow_network = allow_network
        self.provider_override = provider_override
        self._state_box_builder_override = state_box_builder
        self._state_box_builder_cache: Callable[..., dict[str, Any]] | None = None
        self.effect_trace: list[dict[str, Any]] = []
        self._active_secrets: list[str] = []
        self.builtins["effect"] = self.effect
        self.allowed_effects = {
            "pipeline_init",
            "pipeline_profile_read",
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

    def _create_schema(self, db: sqlite3.Connection) -> None:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS eos_pipeline_state(
              singleton INTEGER PRIMARY KEY CHECK(singleton=1),
              generation INTEGER NOT NULL DEFAULT 0,
              continuity_json TEXT NOT NULL DEFAULT '{}',
              canonical_json TEXT NOT NULL DEFAULT '{}',
              canonical_hash TEXT NOT NULL DEFAULT '',
              cursors_json TEXT NOT NULL DEFAULT '{}',
              updated_at REAL NOT NULL DEFAULT 0);
            INSERT OR IGNORE INTO eos_pipeline_state(singleton) VALUES(1);

            CREATE TABLE IF NOT EXISTS eos_pipeline_profiles(
              profile_id TEXT PRIMARY KEY,
              profile_json TEXT NOT NULL,
              profile_hash TEXT NOT NULL,
              active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1)),
              updated_at REAL NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS eos_pipeline_one_active_profile
              ON eos_pipeline_profiles(active) WHERE active=1;

            CREATE TABLE IF NOT EXISTS eos_pipeline_profile_components(
              profile_id TEXT NOT NULL,
              component_kind TEXT NOT NULL,
              component_json TEXT NOT NULL,
              component_hash TEXT NOT NULL,
              updated_at REAL NOT NULL,
              PRIMARY KEY(profile_id,component_kind));

            CREATE TABLE IF NOT EXISTS eos_pipeline_consumed(
              source_kind TEXT NOT NULL,
              source_id TEXT NOT NULL,
              output_id TEXT NOT NULL,
              consumed_at REAL NOT NULL,
              PRIMARY KEY(source_kind,source_id));

            CREATE TABLE IF NOT EXISTS eos_pipeline_outputs(
              output_id TEXT PRIMARY KEY,
              ts REAL NOT NULL,
              generation INTEGER NOT NULL,
              profile_id TEXT NOT NULL,
              output_json TEXT NOT NULL,
              provider_kind TEXT NOT NULL,
              model TEXT,
              packet_hash TEXT NOT NULL,
              canonical_hash TEXT NOT NULL);

            CREATE TABLE IF NOT EXISTS eos_pipeline_packets(
              output_id TEXT PRIMARY KEY,
              packet_hash TEXT NOT NULL,
              ts REAL NOT NULL,
              generation INTEGER NOT NULL,
              profile_id TEXT NOT NULL,
              source_count INTEGER NOT NULL,
              canonical_hash TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS eos_pipeline_packets_hash
              ON eos_pipeline_packets(packet_hash);

            CREATE TABLE IF NOT EXISTS eos_pipeline_study_records(
              output_id TEXT PRIMARY KEY,
              ts REAL NOT NULL,
              generation INTEGER NOT NULL,
              profile_id TEXT NOT NULL,
              component_kind TEXT NOT NULL,
              component_hash TEXT NOT NULL,
              study_payload_json TEXT NOT NULL,
              study_payload_hash TEXT NOT NULL,
              rendered_append_text TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS eos_pipeline_study_profile_generation
              ON eos_pipeline_study_records(profile_id,generation);
            """
        )
        self._migrate_packet_ledger(db)

    @staticmethod
    def _migrate_packet_ledger(db: sqlite3.Connection) -> None:
        """Migrate the old content-hash-primary-key ledger without losing rows.

        A packet hash is content identity, not row identity: two quiet generations can
        legitimately have the same hash. output_id is therefore the ledger primary key.
        """
        info = db.execute("PRAGMA table_info(eos_pipeline_packets)").fetchall()
        if not info:
            raise PipelineFault("PACKET_LEDGER_SCHEMA_MISSING")
        names = {str(row[1]) for row in info}
        required = {"output_id", "packet_hash", "ts", "generation", "profile_id", "source_count", "canonical_hash"}
        if not required.issubset(names):
            raise PipelineFault("PACKET_LEDGER_SCHEMA_UNEXPECTED")
        pk_columns = [str(row[1]) for row in info if int(row[5]) > 0]
        if pk_columns == ["output_id"]:
            db.execute("CREATE INDEX IF NOT EXISTS eos_pipeline_packets_hash ON eos_pipeline_packets(packet_hash)")
            return
        if pk_columns != ["packet_hash"]:
            raise PipelineFault("PACKET_LEDGER_PRIMARY_KEY_UNEXPECTED")
        db.executescript(
            """
            DROP TABLE IF EXISTS eos_pipeline_packets_v2;
            CREATE TABLE eos_pipeline_packets_v2(
              output_id TEXT PRIMARY KEY,
              packet_hash TEXT NOT NULL,
              ts REAL NOT NULL,
              generation INTEGER NOT NULL,
              profile_id TEXT NOT NULL,
              source_count INTEGER NOT NULL,
              canonical_hash TEXT NOT NULL);
            INSERT INTO eos_pipeline_packets_v2(
              output_id,packet_hash,ts,generation,profile_id,source_count,canonical_hash)
            SELECT output_id,packet_hash,ts,generation,profile_id,source_count,canonical_hash
              FROM eos_pipeline_packets;
            DROP TABLE eos_pipeline_packets;
            ALTER TABLE eos_pipeline_packets_v2 RENAME TO eos_pipeline_packets;
            CREATE INDEX eos_pipeline_packets_hash ON eos_pipeline_packets(packet_hash);
            """
        )

    @staticmethod
    def _validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(profile, dict):
            raise PipelineFault("PROFILE_NOT_OBJECT")
        if profile.get("schema") != PROFILE_SCHEMA:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        for field in ("profile_id", "inference", "personality", "sources", "state_metrics", "gate"):
            if field not in profile:
                raise PipelineFault("PROFILE_MISSING:" + field)
        if not isinstance(profile["inference"], dict) or not profile["inference"].get("kind"):
            raise PipelineFault("PROFILE_BAD_INFERENCE")
        if not isinstance(profile["personality"], dict):
            raise PipelineFault("PROFILE_BAD_PERSONALITY")
        contract = profile["personality"].get("output_contract")
        if not isinstance(contract, dict):
            raise PipelineFault("PROFILE_MISSING_OUTPUT_CONTRACT")
        return profile

    @staticmethod
    def _validate_component(kind: str, component: dict[str, Any]) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,79}", str(kind)):
            raise PipelineFault("BAD_COMPONENT_KIND")
        if not isinstance(component, dict):
            raise PipelineFault("COMPONENT_NOT_OBJECT")
        return component

    def install_profile(
        self,
        entity_db: str,
        profile: dict[str, Any],
        *,
        activate: bool = True,
        components: dict[str, dict[str, Any]] | None = None,
        replace_components: bool = False,
    ) -> str:
        """Configuration/import surface. Canonical run() later reads only SQLite state."""
        profile = self._validate_profile(profile)
        raw = _canon(profile)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        now = time.time()
        db = self._db(entity_db)
        try:
            self._create_schema(db)
            db.execute("BEGIN IMMEDIATE")
            if activate:
                db.execute("UPDATE eos_pipeline_profiles SET active=0 WHERE active=1")
            db.execute(
                """INSERT INTO eos_pipeline_profiles(profile_id,profile_json,profile_hash,active,updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(profile_id) DO UPDATE SET
                     profile_json=excluded.profile_json,
                     profile_hash=excluded.profile_hash,
                     active=excluded.active,
                     updated_at=excluded.updated_at""",
                (str(profile["profile_id"]), raw, digest, 1 if activate else 0, now),
            )
            if replace_components:
                db.execute("DELETE FROM eos_pipeline_profile_components WHERE profile_id=?", (str(profile["profile_id"]),))
            for kind, component in (components or {}).items():
                component = self._validate_component(str(kind), component)
                component_raw = _canon(component)
                component_hash = hashlib.sha256(component_raw.encode("utf-8")).hexdigest()
                db.execute(
                    """INSERT INTO eos_pipeline_profile_components(profile_id,component_kind,component_json,component_hash,updated_at)
                       VALUES(?,?,?,?,?)
                       ON CONFLICT(profile_id,component_kind) DO UPDATE SET
                         component_json=excluded.component_json,
                         component_hash=excluded.component_hash,
                         updated_at=excluded.updated_at""",
                    (str(profile["profile_id"]), str(kind), component_raw, component_hash, now),
                )
            db.commit()
            return digest
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def install_component(self, entity_db: str, profile_id: str, kind: str, component: dict[str, Any]) -> str:
        component = self._validate_component(kind, component)
        raw = _canon(component)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        db = self._db(entity_db)
        try:
            self._create_schema(db)
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM eos_pipeline_profiles WHERE profile_id=?", (profile_id,)).fetchone() is None:
                raise PipelineFault("COMPONENT_PROFILE_MISSING")
            db.execute(
                """INSERT INTO eos_pipeline_profile_components(profile_id,component_kind,component_json,component_hash,updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(profile_id,component_kind) DO UPDATE SET
                     component_json=excluded.component_json,
                     component_hash=excluded.component_hash,
                     updated_at=excluded.updated_at""",
                (profile_id, kind, raw, digest, time.time()),
            )
            db.commit()
            return digest
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        started = time.time()
        ok = False
        try:
            dispatch = {
                "pipeline_init": self._pipeline_init,
                "pipeline_profile_read": self._pipeline_profile_read,
                "pipeline_state_read": self._pipeline_state_read,
                "pipeline_collect": self._pipeline_collect,
                "pipeline_compile": self._pipeline_compile,
                "pipeline_build_prompt": self._pipeline_build_prompt,
                "inference_generate": self._inference_generate,
                "pipeline_gate": self._pipeline_gate,
                "pipeline_commit": self._pipeline_commit,
            }
            result = dispatch[kind](payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
            self.effect_trace.append(
                {
                    "kind": kind,
                    "ok": ok,
                    "ms": round((time.time() - started) * 1000, 3),
                    "payload_hash": hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest(),
                }
            )

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._create_schema(db)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._create_schema(db)
                rows = db.execute(
                    "SELECT profile_id,profile_json,profile_hash FROM eos_pipeline_profiles WHERE active=1"
                ).fetchall()
                if len(rows) != 1:
                    raise PipelineFault("NO_ACTIVE_PROFILE" if not rows else "MULTIPLE_ACTIVE_PROFILES")
                row = rows[0]
                base_profile = self._validate_profile(json.loads(row["profile_json"]))
                observed = hashlib.sha256(_canon(base_profile).encode("utf-8")).hexdigest()
                if observed != row["profile_hash"]:
                    raise PipelineFault("PROFILE_HASH_MISMATCH")
                components: dict[str, Any] = {}
                component_hashes: dict[str, str] = {}
                for component_row in db.execute(
                    "SELECT component_kind,component_json,component_hash FROM eos_pipeline_profile_components WHERE profile_id=? ORDER BY component_kind",
                    (str(base_profile["profile_id"]),),
                ).fetchall():
                    component = json.loads(component_row["component_json"])
                    component = self._validate_component(str(component_row["component_kind"]), component)
                    component_hash = hashlib.sha256(_canon(component).encode("utf-8")).hexdigest()
                    if component_hash != component_row["component_hash"]:
                        raise PipelineFault("COMPONENT_HASH_MISMATCH:" + str(component_row["component_kind"]))
                    components[str(component_row["component_kind"])] = component
                    component_hashes[str(component_row["component_kind"])] = component_hash
            profile = dict(base_profile)
            profile["components"] = components
            return {
                "ok": True,
                "profile": profile,
                "profile_hash": observed,
                "component_hashes": component_hashes,
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                row = db.execute("SELECT * FROM eos_pipeline_state WHERE singleton=1").fetchone()
            if row is None:
                raise PipelineFault("PIPELINE_STATE_MISSING")
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
            return db.execute(
                "SELECT 1 FROM eos_pipeline_consumed WHERE source_kind=? AND source_id=?",
                (kind, str(source_id)),
            ).fetchone() is not None

    def _consumed_ids(self, entity_db: str, kind: str) -> set[str]:
        with self._db(entity_db) as db:
            return {
                str(row[0])
                for row in db.execute(
                    "SELECT source_id FROM eos_pipeline_consumed WHERE source_kind=?",
                    (kind,),
                ).fetchall()
            }

    def _query(self, db_path: str, sql: str) -> list[dict[str, Any]]:
        with self._db(db_path) as db:
            return [dict(row) for row in db.execute(sql).fetchall()]

    @staticmethod
    def _delivery_query(sql: str) -> tuple[str, int | None]:
        """Treat a simple terminal integer LIMIT as a post-dedupe delivery budget.

        This prevents already-consumed head rows from pinning later events forever while
        leaving non-terminal/complex SQL untouched rather than guessing its semantics.
        """
        match = re.search(r"(?is)\s+LIMIT\s+(\d+)\s*;?\s*$", str(sql))
        if not match:
            return str(sql), None
        base = str(sql)[: match.start()].rstrip()
        if not base:
            raise PipelineFault("SQLITE_QUERY_EMPTY_AFTER_LIMIT")
        return base, int(match.group(1))

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
                    query, delivery_limit = self._delivery_query(str(spec["query"]))
                    raw = self._query(db_path, query)
                    id_field = str(spec.get("id_field", "source_id"))
                    consumed = self._consumed_ids(entity_db, kind)
                    for row in raw:
                        source_id = row.get(id_field)
                        if source_id is None:
                            continue
                        source_key = str(source_id)
                        if source_key in consumed:
                            continue
                        rows.append(row)
                        consume.append({"kind": kind, "id": source_key})
                        if delivery_limit is not None and len(rows) >= delivery_limit:
                            break
                    source_count += len(rows)
                elif adapter == "json_snapshot":
                    path = self._resolve(str(spec["path"]))
                    if not path.is_file():
                        raise PipelineFault("SNAPSHOT_MISSING:" + str(path))
                    value = json.loads(path.read_text(encoding="utf-8"))
                elif adapter == "jsonl_cursor":
                    path = self._resolve(str(spec["path"]))
                    if not path.is_file():
                        raise PipelineFault("JSONL_MISSING:" + str(path))
                    cursor = int(cursors.get(kind, 0))
                    raw = path.read_bytes()[cursor:]
                    limit = max(0, int(spec.get("limit", 60)))
                    advanced = 0
                    emitted = 0
                    for chunk in raw.splitlines(keepends=True):
                        if emitted >= limit:
                            break
                        if not (chunk.endswith(b"\n") or chunk.endswith(b"\r")):
                            break
                        advanced += len(chunk)
                        line = chunk.strip()
                        if not line:
                            continue
                        try:
                            decoded = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        rows.append(decoded if isinstance(decoded, dict) else {"text": str(decoded)})
                        emitted += 1
                    cursors[kind] = cursor + advanced
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
                sensors[kind] = {"ok": False, "error_kind": type(exc).__name__}

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
                    raise PipelineFault("UNKNOWN_PROBE_ADAPTER:" + str(spec["adapter"]))
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

        required = [kind for kind, src in sources.items() if src.get("required_for_quiet")]
        quiet_sensors_ok = bool(required) and all(sensors[kind]["ok"] for kind in required)
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
            return sum(float(self._expr(item, context) or 0) for item in expr.get("args", []))
        if op == "div":
            divisor = float(self._expr(expr["b"], context) or 0)
            return 0.0 if divisor == 0 else float(self._expr(expr["a"], context) or 0) / divisor
        if op == "clamp01":
            return max(0.0, min(1.0, float(self._expr(expr["arg"], context) or 0)))
        if op == "if":
            branch = expr["then"] if self._expr(expr["cond"], context) else expr["else"]
            return self._expr(branch, context)
        raise PipelineFault("UNKNOWN_EXPR:" + _canon(expr))

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
                status = "UNKNOWN" if bool(self._expr(spec.get("unknown_if", False), context)) else "VERIFIED"
            value: Any = None
            if status == "VERIFIED":
                value = float(self._expr(spec.get("value", 0.0), context) or 0.0)
            metrics[name] = {
                "status": str(status),
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
        canonical_raw = _canon(canonical)
        packet_raw = _canon(packet)

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
            "canonical_state_hash": hashlib.sha256(canonical_raw.encode()).hexdigest(),
            "packet_hash": hashlib.sha256(packet_raw.encode()).hexdigest(),
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
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        return {"ok": True, "system": system, "user": user}

    def _keys(self, names: list[str], secret_file: str | None) -> list[str]:
        file_values: dict[str, str] = {}
        if secret_file:
            try:
                for line in Path(secret_file).read_text(encoding="utf-8").splitlines():
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
        pointer = str(pointer or "")
        if pointer.startswith("/"):
            parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
        else:
            parts = [part for part in pointer.split(".") if part]
        for part in parts:
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current

    @staticmethod
    def _is_loopback(endpoint: str) -> bool:
        return bool(re.match(r"^http://(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?(?:/|$)", endpoint))

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = dict(p["inference"])
        kind = str(inference.get("kind", ""))
        try:
            if self.provider_override is not None:
                self._active_secrets = []
                payload = self.provider_override(
                    {
                        "inference": inference,
                        "provider": inference,
                        "system": p["system"],
                        "user": p["user"],
                    }
                )
                return {
                    "ok": True,
                    "payload": payload,
                    "provider_kind": kind or "override",
                    "model": inference.get("model"),
                }
            if kind == "local_exec":
                return self._inference_local_exec(inference, p)
            if kind in {"openai_style_chat_json", "remote_api", "local_server"}:
                return self._inference_http_json(inference, p)
            raise PipelineFault("UNKNOWN_INFERENCE_KIND:" + kind)
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _inference_local_exec(self, inference: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        model_path = self._resolve(str(inference.get("local_model_path") or inference.get("model_path") or ""))
        if not model_path.is_file():
            raise PipelineFault("LOCAL_MODEL_MISSING")
        raw_argv: Any = inference.get("local_argv_json", inference.get("argv"))
        if isinstance(raw_argv, str):
            raw_argv = json.loads(raw_argv)
        if not isinstance(raw_argv, list) or not raw_argv or not all(isinstance(x, str) for x in raw_argv):
            raise PipelineFault("LOCAL_ARGV_INVALID")
        prompt_text = str(inference.get("local_prompt_template", "{{SYSTEM}}\n\n{{USER}}"))
        prompt_text = prompt_text.replace("{{SYSTEM}}", str(p["system"])).replace("{{USER}}", str(p["user"]))
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.root, prefix="mini-prompt-", suffix=".txt") as fh:
            fh.write(prompt_text)
            prompt_path = Path(fh.name)
        try:
            replacements = {
                "{{MODEL_PATH}}": str(model_path),
                "{{PROMPT_FILE}}": str(prompt_path),
                "{{MAX_TOKENS}}": str(int(inference.get("max_tokens", 2000))),
                "{{TEMPERATURE}}": str(float(inference.get("temperature", 0.7))),
            }
            argv = []
            for item in raw_argv:
                value = item
                for needle, replacement in replacements.items():
                    value = value.replace(needle, replacement)
                argv.append(value)
            completed = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                shell=False,
                timeout=float(inference.get("timeout_seconds", 120)),
                check=False,
            )
            if completed.returncode != 0:
                raise PipelineFault("LOCAL_EXEC_FAILED:" + str(completed.returncode))
            text = completed.stdout.strip()
            payload = json.loads(text) if inference.get("response_content", "json_string") == "json_string" else text
            return {
                "ok": True,
                "payload": payload,
                "provider_kind": "local_exec",
                "model": inference.get("model") or model_path.name,
            }
        finally:
            try:
                prompt_path.unlink()
            except OSError:
                pass

    def _inference_http_json(self, inference: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        if not self.allow_network:
            raise PipelineFault("NETWORK_DISABLED")
        endpoint = str(inference["endpoint"])
        loopback = self._is_loopback(endpoint)
        if endpoint.startswith("http://") and not loopback:
            raise PipelineFault("PLAINTEXT_NON_LOOPBACK_FORBIDDEN")
        keys = self._keys(list(inference.get("secret_names", [])), p.get("secret_file"))
        if not keys and not loopback:
            raise PipelineFault("NO_PROVIDER_SECRET")
        auth_values = keys or [None]
        body = {
            "model": inference.get("model"),
            "messages": [
                {"role": "system", "content": p["system"]},
                {"role": "user", "content": p["user"]},
            ],
            "temperature": inference.get("temperature", 0.7),
            "max_tokens": inference.get("max_tokens", 2000),
            "response_format": {"type": "json_object"},
        }
        template = inference.get("request_template")
        if isinstance(template, dict):
            body = json.loads(json.dumps(template))
            body.setdefault("model", inference.get("model"))
            body["messages"] = [
                {"role": "system", "content": p["system"]},
                {"role": "user", "content": p["user"]},
            ]
        encoded = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for key in auth_values:
            self._active_secrets = [key] if key else []
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if key:
                headers[str(inference.get("auth_header", "Authorization"))] = str(
                    inference.get("auth_prefix", "Bearer ")
                ) + key
            request = urllib.request.Request(endpoint, data=encoded, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=float(inference.get("timeout_seconds", 60))) as response:
                    response_obj = json.loads(response.read().decode("utf-8"))
                content = self._pointer(response_obj, inference.get("response_pointer", "/choices/0/message/content"))
                payload = json.loads(content) if inference.get("response_content", "json_string") == "json_string" else content
                return {
                    "ok": True,
                    "payload": payload,
                    "provider_kind": str(inference.get("kind", "json")),
                    "model": inference.get("model"),
                }
            except Exception as exc:
                last = exc
        raise last or PipelineFault("INFERENCE_FAILED")

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
                if payload.get("canonical_state_hash_seen") != compiled["canonical_state_hash"]:
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

            state_box = profile.get("components", {}).get("public_state_box")
            if isinstance(state_box, dict) and state_box.get("enabled"):
                self_report_field = contract.get("longitudinal_self_report_field")
                if not self_report_field:
                    raise PipelineFault("STATE_BOX_SELF_REPORT_FIELD_UNCONFIGURED")
                if self_report_field not in payload or not isinstance(payload[self_report_field], dict):
                    raise PipelineFault("STATE_BOX_SELF_REPORT_MISSING")

            patterns = [re.compile(pattern, re.I) for pattern in gate.get("leak_patterns", [])]
            secrets_now = [value for value in self._active_secrets if value]

            def scan(value: Any) -> None:
                text = str(value)
                if any(pattern.search(text) for pattern in patterns):
                    raise PipelineFault("LEAK_PATTERN")
                if any(secret in text for secret in secrets_now):
                    raise PipelineFault("SECRET_LEAK")

            scan(payload)
            allowed = set(compiled["allowed_evidence_refs"])
            metrics = compiled["personality_state"]
            for section in payload[contract["sections_field"]]:
                refs = section.get(contract["section_evidence_field"], [])
                if gate.get("require_evidence_per_section", True) and not refs:
                    raise PipelineFault("SECTION_WITHOUT_EVIDENCE")
                if any(ref not in allowed for ref in refs):
                    raise PipelineFault("UNKNOWN_EVIDENCE_REF")
                for name, strength in section.get(contract["section_claims_field"], {}).items():
                    if name not in metrics:
                        raise PipelineFault("UNKNOWN_STATE_CLAIM")
                    metric = metrics[name]
                    if metric["status"] != "VERIFIED" or metric["value"] is None:
                        raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    if float(strength) > float(metric["value"]) + float(gate.get("max_claim_overshoot", 0.0)):
                        raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs:
                        raise PipelineFault("STATE_CLAIM_WITHOUT_METRIC_EVIDENCE")
            return {"ok": True, "payload": payload}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _state_box_builder(self) -> Callable[..., dict[str, Any]]:
        if self._state_box_builder_override is not None:
            return self._state_box_builder_override
        if self._state_box_builder_cache is not None:
            return self._state_box_builder_cache
        path = Path(__file__).resolve().parents[1] / "the artefact" / "blogpost_entity" / "state_box_reference.py"
        if not path.is_file():
            raise PipelineFault("STATE_BOX_REFERENCE_MISSING")
        spec = importlib.util.spec_from_file_location("clay_state_box_reference", path)
        if spec is None or spec.loader is None:
            raise PipelineFault("STATE_BOX_REFERENCE_LOAD_FAILED")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        builder = getattr(module, "build_state_box", None)
        if not callable(builder):
            raise PipelineFault("STATE_BOX_BUILDER_MISSING")
        self._state_box_builder_cache = builder
        return builder

    @staticmethod
    def _quiet_status(collected: dict[str, Any]) -> str:
        if int(collected.get("source_count", 0)) > 0:
            return "ACTIVITY_PRESENT"
        if not collected.get("quiet_sensors_ok"):
            return "UNKNOWN_SENSOR_INCOMPLETE"
        return "VERIFIED_QUIET"

    def _build_state_box(
        self,
        db: sqlite3.Connection,
        *,
        profile: dict[str, Any],
        previous: dict[str, Any],
        payload: dict[str, Any],
        collected: dict[str, Any],
        compiled: dict[str, Any],
        generated: dict[str, Any],
        prompt: dict[str, Any],
        generation: int,
        now: float,
    ) -> dict[str, Any] | None:
        config = profile.get("components", {}).get("public_state_box")
        if not isinstance(config, dict) or not config.get("enabled"):
            return None
        contract = profile["personality"]["output_contract"]
        self_report_field = contract.get("longitudinal_self_report_field")
        if not self_report_field or not isinstance(payload.get(self_report_field), dict):
            raise PipelineFault("STATE_BOX_SELF_REPORT_MISSING")
        previous_row = db.execute(
            """SELECT study_payload_json FROM eos_pipeline_study_records
               WHERE profile_id=? AND component_kind='public_state_box' AND generation<?
               ORDER BY generation DESC LIMIT 1""",
            (str(profile["profile_id"]), generation),
        ).fetchone()
        previous_payload = json.loads(previous_row[0]) if previous_row else None
        system_state: dict[str, Any] = {
            "generation": generation,
            "timestamp": now,
            "inference_backend": generated.get("provider_kind") or profile.get("inference", {}).get("kind"),
            "model_label": generated.get("model") or profile.get("inference", {}).get("model") or "UNKNOWN",
            "source_count": compiled.get("source_count", 0),
            "sensor_health": collected.get("sensors", {}),
            "quiet_status": self._quiet_status(collected),
        }
        system_state.update(compiled.get("personality_state", {}))
        context = {
            "inference_backend": system_state["inference_backend"],
            "model_label": system_state["model_label"],
            "system_prompt_hash": hashlib.sha256(str(prompt.get("system", "")).encode("utf-8")).hexdigest(),
            "profile_hash": _sha({k: v for k, v in profile.items() if k != "components"}),
        }
        result = self._state_box_builder()(
            config,
            system_state,
            payload[self_report_field],
            previous_study_payload=previous_payload,
            context=context,
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise PipelineFault("STATE_BOX_BUILD_FAILED")
        study_payload = result.get("study_payload")
        if not isinstance(study_payload, dict):
            raise PipelineFault("STATE_BOX_STUDY_PAYLOAD_MISSING")
        return {
            "component_hash": _sha(config),
            "study_payload": study_payload,
            "study_payload_hash": str(result.get("study_payload_hash") or _sha(study_payload)),
            "rendered_text": str(result.get("rendered_text", "")),
        }

    def _pipeline_commit(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"])
        profile = p["profile"]
        previous = p["previous"]
        data = p["data"]
        collected = data["collected"]
        compiled = data["compiled"]
        generated = data["generated"]
        prompt = data.get("prompt", {})
        payload = data["gated"]["payload"]
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
            # Schema checks/migrations occur before the atomic data transaction. Python's
            # sqlite3 executescript may otherwise implicitly commit an open transaction.
            self._create_schema(db)
            db.execute("BEGIN IMMEDIATE")
            state_box = self._build_state_box(
                db,
                profile=profile,
                previous=previous,
                payload=payload,
                collected=collected,
                compiled=compiled,
                generated=generated,
                prompt=prompt,
                generation=generation,
                now=now,
            )
            row = db.execute(
                "UPDATE eos_pipeline_state SET updated_at=? WHERE singleton=1 AND generation=?",
                (now, previous["generation"]),
            )
            if row.rowcount != 1:
                raise PipelineFault("STALE_GENERATION")
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
                    json.dumps(payload, ensure_ascii=False),
                    generated.get("provider_kind", ""),
                    generated.get("model"),
                    compiled["packet_hash"],
                    compiled["canonical_state_hash"],
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
            if state_box is not None:
                db.execute(
                    """INSERT INTO eos_pipeline_study_records(
                       output_id,ts,generation,profile_id,component_kind,component_hash,
                       study_payload_json,study_payload_hash,rendered_append_text)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        output_id,
                        now,
                        generation,
                        profile["profile_id"],
                        "public_state_box",
                        state_box["component_hash"],
                        json.dumps(state_box["study_payload"], ensure_ascii=False),
                        state_box["study_payload_hash"],
                        state_box["rendered_text"],
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
            return {
                "ok": True,
                "output_id": output_id,
                "generation": generation,
                "state_box_text": state_box["rendered_text"] if state_box else "",
                "state_box_payload_hash": state_box["study_payload_hash"] if state_box else "",
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
):
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntime()
    return clay.execute(program, entry, args, rt)


__all__ = [
    "VERSION",
    "PROFILE_SCHEMA",
    "IMMUTABLE_GUARD",
    "PipelineFault",
    "ProfilePipelineRuntime",
    "execute_source",
]
