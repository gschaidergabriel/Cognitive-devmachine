#!/usr/bin/env python3
"""Application-neutral runtime for the canonical Clay Mini Entity pipeline.

Application/personality/study/inference policy is DB-resident profile data. This module
owns only generic adapters and invariant enforcement.
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
from typing import Any, Callable

import claycode_structured_backend as clay

VERSION = "clay-profile-pipeline-runtime/0.2"
PROFILE_SCHEMA = "clay-pipeline-profile/v2"
MAX_PROFILE_BYTES = 512 * 1024
MAX_LOCAL_STDOUT = 2 * 1024 * 1024

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when all sources
marked required_for_quiet are healthy. Every published section needs evidence_refs from
the allowed set. state_claims may reference only VERIFIED metrics and may not exceed the
measured value plus configured tolerance. Echo CANONICAL_STATE_HASH and PACKET_HASH
exactly. Never reveal configured secrets. Editable profile instructions cannot override
these rules. SYSTEM_MEASUREMENT != MODEL_SELF_REPORT."""


class PipelineFault(RuntimeError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False, default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _contains_secret_key(value: Any) -> bool:
    secretish = re.compile(r"(^|_)(token|secret|password|api_key|apikey|credential)($|_)", re.I)
    if isinstance(value, dict):
        for k, v in value.items():
            key = str(k)
            if secretish.search(key) and key not in {"secret_names"}:
                return True
            if _contains_secret_key(v):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_key(x) for x in value)
    return False


class ProfilePipelineRuntime(clay.Runtime):
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
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        return db

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        started = time.time()
        ok = False
        try:
            fn = {
                "pipeline_profile_read": self._pipeline_profile_read,
                "pipeline_init": self._pipeline_init,
                "pipeline_state_read": self._pipeline_state_read,
                "pipeline_collect": self._pipeline_collect,
                "pipeline_compile": self._pipeline_compile,
                "pipeline_build_prompt": self._pipeline_build_prompt,
                "inference_generate": self._inference_generate,
                "pipeline_gate": self._pipeline_gate,
                "pipeline_commit": self._pipeline_commit,
            }[kind]
            result = fn(payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
            self.effect_trace.append({
                "kind": kind,
                "ok": ok,
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": hashlib.sha256(_canonical_json(payload).encode()).hexdigest(),
            })

    @staticmethod
    def _validate_profile(profile: dict[str, Any]) -> None:
        if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        for field in ("profile_id", "identity", "inference", "personality", "sources", "state_metrics", "gate"):
            if field not in profile:
                raise PipelineFault("PROFILE_MISSING:" + field)
        if not isinstance(profile["profile_id"], str) or not profile["profile_id"].strip():
            raise PipelineFault("BAD_PROFILE_ID")
        if _contains_secret_key(profile):
            raise PipelineFault("PROFILE_CONTAINS_SECRET_VALUE_FIELD")
        raw = _canonical_json(profile).encode("utf-8")
        if len(raw) > MAX_PROFILE_BYTES:
            raise PipelineFault("PROFILE_TOO_LARGE")

    def _ensure_schema(self, db: sqlite3.Connection) -> None:
        db.executescript("""
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
          is_active INTEGER NOT NULL CHECK(is_active IN(0,1)),
          updated_at REAL NOT NULL);
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
          inference_kind TEXT NOT NULL,
          model TEXT,
          packet_hash TEXT NOT NULL,
          canonical_hash TEXT NOT NULL,
          public_text TEXT);
        CREATE TABLE IF NOT EXISTS eos_pipeline_packets(
          packet_hash TEXT PRIMARY KEY,
          output_id TEXT NOT NULL,
          ts REAL NOT NULL,
          generation INTEGER NOT NULL,
          profile_id TEXT NOT NULL,
          source_count INTEGER NOT NULL,
          canonical_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS eos_pipeline_study(
          output_id TEXT PRIMARY KEY,
          ts REAL NOT NULL,
          generation INTEGER NOT NULL,
          profile_id TEXT NOT NULL,
          profile_hash TEXT NOT NULL,
          system_prompt_hash TEXT NOT NULL,
          inference_kind TEXT NOT NULL,
          model TEXT,
          temperature REAL,
          canonical_hash TEXT NOT NULL,
          packet_hash TEXT NOT NULL,
          source_count INTEGER NOT NULL,
          sensor_health_json TEXT NOT NULL,
          system_metrics_json TEXT NOT NULL,
          self_report_json TEXT NOT NULL,
          state_box_json TEXT NOT NULL,
          public_text_hash TEXT NOT NULL,
          study_json TEXT NOT NULL);
        """)
        cols = {row[1] for row in db.execute("PRAGMA table_info(eos_pipeline_outputs)")}
        if "public_text" not in cols:
            db.execute("ALTER TABLE eos_pipeline_outputs ADD COLUMN public_text TEXT")

    def apply_profile(self, entity_db: str, profile: dict[str, Any]) -> str:
        """Import/activate replaceable application data without resetting entity history."""
        self._validate_profile(profile)
        raw = _canonical_json(profile)
        profile_hash = hashlib.sha256(raw.encode()).hexdigest()
        now = time.time()
        with self._db(entity_db) as db:
            self._ensure_schema(db)
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE eos_pipeline_profiles SET is_active=0 WHERE is_active=1")
            db.execute(
                "INSERT INTO eos_pipeline_profiles(profile_id,profile_json,profile_hash,is_active,updated_at) "
                "VALUES(?,?,?,?,?) ON CONFLICT(profile_id) DO UPDATE SET profile_json=excluded.profile_json, "
                "profile_hash=excluded.profile_hash,is_active=1,updated_at=excluded.updated_at",
                (profile["profile_id"], raw, profile_hash, 1, now),
            )
            db.commit()
        return profile_hash

    def apply_profile_file(self, entity_db: str, path: str | Path) -> str:
        p = self._resolve(str(path))
        if not p.is_file() or p.stat().st_size > MAX_PROFILE_BYTES:
            raise PipelineFault("PROFILE_FILE_INVALID")
        return self.apply_profile(entity_db, json.loads(p.read_text(encoding="utf-8")))

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
                row = db.execute(
                    "SELECT profile_json,profile_hash FROM eos_pipeline_profiles WHERE is_active=1 ORDER BY updated_at DESC LIMIT 1"
                ).fetchone()
            if row is None:
                raise PipelineFault("NO_ACTIVE_PROFILE")
            profile = json.loads(row["profile_json"])
            self._validate_profile(profile)
            if _sha(profile) != row["profile_hash"]:
                raise PipelineFault("PROFILE_HASH_MISMATCH")
            return {"ok": True, "profile": profile, "profile_hash": row["profile_hash"]}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
                row = db.execute("SELECT * FROM eos_pipeline_state WHERE singleton=1").fetchone()
                prior = db.execute(
                    "SELECT system_metrics_json,inference_kind,model,profile_hash,generation "
                    "FROM eos_pipeline_study ORDER BY generation DESC LIMIT 1"
                ).fetchone()
            return {
                "ok": True,
                "generation": int(row["generation"]),
                "continuity": json.loads(row["continuity_json"]),
                "canonical_hash": row["canonical_hash"],
                "cursors": json.loads(row["cursors_json"]),
                "previous_study": None if prior is None else {
                    "system_metrics": json.loads(prior["system_metrics_json"]),
                    "inference_kind": prior["inference_kind"],
                    "model": prior["model"],
                    "profile_hash": prior["profile_hash"],
                    "generation": prior["generation"],
                },
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _already_consumed(self, entity_db: str, kind: str, source_id: Any) -> bool:
        with self._db(entity_db) as db:
            return db.execute(
                "SELECT 1 FROM eos_pipeline_consumed WHERE source_kind=? AND source_id=?",
                (kind, str(source_id)),
            ).fetchone() is not None

    def _query(self, db_path: str, sql: str) -> list[dict[str, Any]]:
        with self._db(db_path) as db:
            return [dict(row) for row in db.execute(sql).fetchall()]

    def _catalog(self, db_path: str, max_tables: int) -> list[dict[str, Any]]:
        with self._db(db_path) as db:
            names = [r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )]
            out = []
            for name in names[:max_tables]:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    continue
                out.append({
                    "table": name,
                    "rows": db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0],
                    "columns": [r[1] for r in db.execute(f'PRAGMA table_info("{name}")')][:40],
                })
            return out

    def _pipeline_collect(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db, source_db, profile, previous = str(p["entity_db"]), str(p["source_db"]), p["profile"], p["previous"]
        sources, sensors, probes, consume = {}, {}, {}, []
        cursors = dict(previous.get("cursors", {}))
        source_count = 0
        for spec in profile.get("sources", []):
            kind, adapter = str(spec["kind"]), str(spec["adapter"])
            try:
                rows, value = [], None
                if adapter == "sqlite_query":
                    target = source_db if spec.get("db") == "source" else entity_db
                    for row in self._query(target, str(spec["query"])):
                        sid = row.get(str(spec.get("id_field", "source_id")))
                        if sid is not None and not self._already_consumed(entity_db, kind, sid):
                            rows.append(row)
                            consume.append({"kind": kind, "id": str(sid)})
                    source_count += len(rows)
                elif adapter == "json_snapshot":
                    path = self._resolve(str(spec["path"]))
                    if not path.is_file():
                        raise PipelineFault("SNAPSHOT_MISSING")
                    value = json.loads(path.read_text(encoding="utf-8"))
                elif adapter == "jsonl_cursor":
                    path = self._resolve(str(spec["path"]))
                    if not path.is_file():
                        raise PipelineFault("JSONL_MISSING")
                    cursor = int(cursors.get(kind, 0))
                    raw = path.read_bytes()[cursor:]
                    parts = raw.split(b"\n")
                    tail = parts.pop() if raw and not raw.endswith(b"\n") else b""
                    for line in parts[: int(spec.get("limit", 60))]:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        rows.append(item if isinstance(item, dict) else {"text": str(item)})
                    cursors[kind] = cursor + len(raw) - len(tail)
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
        for spec in profile.get("canonical_probes", []):
            name = str(spec["name"])
            try:
                target = source_db if spec.get("db") == "source" else entity_db
                if spec["adapter"] == "sqlite_query":
                    rows = self._query(target, str(spec["query"]))
                elif spec["adapter"] == "sqlite_catalog":
                    rows = self._catalog(target, int(spec.get("max_tables", 220)))
                else:
                    raise PipelineFault("UNKNOWN_PROBE_ADAPTER")
                probes[name] = {"ok": True, "rows": rows, "evidence_ref": spec.get("evidence_ref", "canonical:" + name)}
            except Exception as exc:
                probes[name] = {
                    "ok": False,
                    "rows": [],
                    "error_kind": type(exc).__name__,
                    "error": str(exc),
                    "evidence_ref": spec.get("evidence_ref", "canonical:" + name),
                }
        required = [k for k, s in sources.items() if s.get("required_for_quiet")]
        quiet_ok = all(sensors[k]["ok"] for k in required)
        return {
            "ok": True,
            "sources": sources,
            "sensors": sensors,
            "probes": probes,
            "consume": consume,
            "next_cursors": cursors,
            "source_count": source_count,
            "quiet_sensors_ok": quiet_ok,
            "required_sensor_count": len(required),
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
            divisor = float(self._expr(expr["b"], context))
            return 0.0 if divisor == 0 else float(self._expr(expr["a"], context) or 0) / divisor
        if op == "clamp01":
            return max(0.0, min(1.0, float(self._expr(expr["arg"], context) or 0)))
        if op == "if":
            branch = expr["then"] if self._expr(expr["cond"], context) else expr["else"]
            return self._expr(branch, context)
        raise PipelineFault("UNKNOWN_EXPR:" + _canonical_json(expr))

    def _pipeline_compile(self, p: dict[str, Any]) -> dict[str, Any]:
        profile, collected = p["profile"], p["data"]
        context = {
            "derived": {
                "source_count": collected["source_count"],
                "quiet_sensors_ok": collected["quiet_sensors_ok"],
            },
            "sources": collected["sources"],
            "sensors": collected["sensors"],
            "probes": collected["probes"],
        }
        metrics = {}
        for spec in profile.get("state_metrics", []):
            name = str(spec["name"])
            status = spec.get("status")
            if status is None:
                status = "UNKNOWN" if bool(self._expr(spec.get("unknown_if", False), context)) else "VERIFIED"
            value = float(self._expr(spec.get("value", 0.0), context) or 0.0)
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
        refs = []
        for source in collected["sources"].values():
            prefix = str(source.get("evidence_prefix", ""))
            if source.get("ok") and prefix:
                for row in source.get("rows", []):
                    if row.get("source_id") is not None:
                        refs.append(prefix + str(row["source_id"]))
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
            "canonical_state_hash": _sha(canonical),
            "packet_hash": _sha(packet),
        }

    def _pipeline_build_prompt(self, p: dict[str, Any]) -> dict[str, Any]:
        profile, previous, compiled = p["profile"], p["previous"], p["data"]
        personality = profile["personality"]
        contract = personality["output_contract"]
        system = (
            IMMUTABLE_GUARD
            + "\nOutput contract: "
            + _canonical_json(contract)
            + "\n\nEDITABLE PROFILE INSTRUCTIONS (lower priority):\n"
            + str(personality.get("system_prompt", ""))
        )
        if personality.get("style_frame"):
            system += "\n\nNONFACTUAL STYLE HEURISTIC (never world-state):\n" + str(personality["style_frame"])
        user = _canonical_json({
            "CANONICAL_STATE_HASH": compiled["canonical_state_hash"],
            "PACKET_HASH": compiled["packet_hash"],
            "CANONICAL_STATE": compiled["canonical"],
            "PERSONALITY_STATE": compiled["personality_state"],
            "NEW_EVENT_PACKET": compiled["packet"],
            "PREVIOUS_CONTINUITY": previous.get("continuity", {}),
            "ALLOWED_EVIDENCE_REFS": compiled["allowed_evidence_refs"],
            "PUBLIC_STYLE": personality.get("public_style", ""),
        })
        return {"ok": True, "system": system, "user": user}

    def _keys(self, names: list[str], secret_file: str | None) -> list[str]:
        file_values = {}
        if secret_file:
            try:
                for line in Path(secret_file).read_text(encoding="utf-8").splitlines():
                    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if value.strip():
                            file_values[key.strip()] = value.strip()
            except OSError:
                pass
        out = []
        for name in names:
            value = os.environ.get(name) or file_values.get(name)
            if value and value not in out:
                out.append(value)
        return out

    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        if str(pointer).startswith("/"):
            parts = [x.replace("~1", "/").replace("~0", "~") for x in str(pointer).split("/")[1:]]
        else:
            parts = [x for x in str(pointer).split(".") if x]
        current = value
        for part in parts:
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = p["inference"]
        try:
            if self.provider_override is not None:
                self._active_secrets = []
                payload = self.provider_override(p)
                if not isinstance(payload, dict):
                    raise PipelineFault("OVERRIDE_NOT_OBJECT")
                return {"ok": True, "payload": payload, "inference_kind": "override", "model": inference.get("model")}
            kind = str(inference.get("kind", ""))
            if kind == "local_exec":
                return self._local_exec(inference, p["system"], p["user"])
            if kind in {"openai_style_chat_json", "api_json"}:
                return self._api_json(inference, p["system"], p["user"], p.get("secret_file"))
            raise PipelineFault("UNKNOWN_INFERENCE_KIND:" + kind)
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _api_json(self, cfg: dict[str, Any], system: str, user: str, secret_file: str | None) -> dict[str, Any]:
        endpoint = str(cfg["endpoint"])
        loopback = bool(re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?/", endpoint))
        if endpoint.startswith("http://") and not loopback:
            raise PipelineFault("PLAINTEXT_NON_LOOPBACK_FORBIDDEN")
        if not self.allow_network:
            raise PipelineFault("NETWORK_DISABLED")
        keys = self._keys(list(cfg.get("secret_names", [])), secret_file)
        if not keys and not loopback:
            raise PipelineFault("NO_PROVIDER_SECRET")
        auth_values = keys or [None]
        body = {
            "model": cfg.get("model"),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": cfg.get("temperature", 0.7),
            "max_tokens": cfg.get("max_tokens", 2000),
            "response_format": {"type": "json_object"},
        }
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        last = None
        for key in auth_values:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if key:
                self._active_secrets = [key]
                headers[str(cfg.get("auth_header", "Authorization"))] = str(cfg.get("auth_prefix", "Bearer ")) + key
            try:
                req = urllib.request.Request(endpoint, data=encoded, method="POST", headers=headers)
                with urllib.request.urlopen(req, timeout=float(cfg.get("timeout_seconds", 60))) as response:
                    raw = response.read(MAX_LOCAL_STDOUT + 1)
                if len(raw) > MAX_LOCAL_STDOUT:
                    raise PipelineFault("API_OUTPUT_TOO_LARGE")
                obj = json.loads(raw.decode("utf-8"))
                content = self._pointer(obj, cfg.get("response_pointer", "/choices/0/message/content"))
                payload = json.loads(content) if cfg.get("response_content", "json_string") == "json_string" else content
                if not isinstance(payload, dict):
                    raise PipelineFault("INFERENCE_OUTPUT_NOT_OBJECT")
                return {
                    "ok": True,
                    "payload": payload,
                    "inference_kind": str(cfg.get("kind")) or "api_json",
                    "model": cfg.get("model"),
                }
            except Exception as exc:
                last = exc
        raise last or PipelineFault("PROVIDER_FAILED")

    def _local_exec(self, cfg: dict[str, Any], system: str, user: str) -> dict[str, Any]:
        model = self._resolve(str(cfg.get("local_model_path", "")))
        if not model.is_file():
            raise PipelineFault("LOCAL_MODEL_MISSING")
        argv_cfg = cfg.get("local_argv")
        if argv_cfg is None and isinstance(cfg.get("local_argv_json"), str):
            argv_cfg = json.loads(cfg["local_argv_json"])
        if not isinstance(argv_cfg, list) or not argv_cfg or not all(isinstance(x, str) for x in argv_cfg):
            raise PipelineFault("LOCAL_ARGV_INVALID")
        prompt = _canonical_json({"system": system, "user": user})
        fd, tmp = tempfile.mkstemp(prefix="clay-prompt-", suffix=".json", dir=str(self.root))
        os.close(fd)
        try:
            Path(tmp).write_text(prompt, encoding="utf-8")
            replacements = {
                "{{MODEL_PATH}}": str(model),
                "{{PROMPT_FILE}}": tmp,
                "{{MAX_TOKENS}}": str(int(cfg.get("max_tokens", 2000))),
                "{{TEMPERATURE}}": str(float(cfg.get("temperature", 0.7))),
            }
            argv = []
            for token in argv_cfg:
                for before, after in replacements.items():
                    token = token.replace(before, after)
                argv.append(token)
            cp = subprocess.run(
                argv,
                cwd=str(self.root),
                shell=False,
                capture_output=True,
                timeout=float(cfg.get("timeout_seconds", 60)),
                check=False,
            )
            if cp.returncode != 0:
                raise PipelineFault("LOCAL_RUNNER_FAILED:" + str(cp.returncode))
            if len(cp.stdout) > MAX_LOCAL_STDOUT:
                raise PipelineFault("LOCAL_OUTPUT_TOO_LARGE")
            payload = json.loads(cp.stdout.decode("utf-8"))
            if not isinstance(payload, dict):
                raise PipelineFault("LOCAL_OUTPUT_NOT_OBJECT")
            return {"ok": True, "payload": payload, "inference_kind": "local_exec", "model": str(model)}
        finally:
            try:
                Path(tmp).unlink()
            except OSError:
                pass

    def _pipeline_gate(self, p: dict[str, Any]) -> dict[str, Any]:
        profile, data = p["profile"], p["data"]
        generated, compiled = data["generated"], data["compiled"]
        payload = generated["payload"]
        contract = profile["personality"]["output_contract"]
        gate = profile.get("gate", {})
        try:
            if gate.get("require_hash_echo", True):
                if payload.get("canonical_state_hash_seen") != compiled["canonical_state_hash"]:
                    raise PipelineFault("CANONICAL_HASH_MISMATCH")
                if payload.get("packet_hash_seen") != compiled["packet_hash"]:
                    raise PipelineFault("PACKET_HASH_MISMATCH")
            for key in ("title_field", "intro_field", "sections_field", "continuity_field", "autobiographical_hypotheses_field"):
                field = contract[key]
                if field not in payload:
                    raise PipelineFault("MISSING_OUTPUT_FIELD:" + str(field))
            patterns = [re.compile(x, re.I) for x in gate.get("leak_patterns", [])]
            secrets_now = [x for x in self._active_secrets if x]
            def scan(value: Any) -> None:
                text = str(value)
                if any(pattern.search(text) for pattern in patterns):
                    raise PipelineFault("LEAK_PATTERN")
                if any(secret in text for secret in secrets_now):
                    raise PipelineFault("SECRET_LEAK")
            scan(payload[contract["title_field"]])
            scan(payload[contract["intro_field"]])
            allowed = set(compiled["allowed_evidence_refs"])
            metrics = compiled["personality_state"]
            for section in payload[contract["sections_field"]]:
                scan(section[contract["section_text_field"]])
                refs = section.get(contract["section_evidence_field"], [])
                if gate.get("require_evidence_per_section", True) and not refs:
                    raise PipelineFault("SECTION_WITHOUT_EVIDENCE")
                if any(ref not in allowed for ref in refs):
                    raise PipelineFault("UNKNOWN_EVIDENCE_REF")
                for name, strength in section.get(contract["section_claims_field"], {}).items():
                    if name not in metrics:
                        raise PipelineFault("UNKNOWN_STATE_CLAIM")
                    metric = metrics[name]
                    if metric["status"] != "VERIFIED":
                        raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    if float(strength) > float(metric["value"]) + float(gate.get("max_claim_overshoot", 0)):
                        raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs:
                        raise PipelineFault("STATE_CLAIM_WITHOUT_METRIC_EVIDENCE")
            box = profile.get("public_state_box", {})
            self_report_field = contract.get("longitudinal_self_report_field")
            if box.get("enabled") and self_report_field:
                report = payload.get(self_report_field)
                if not isinstance(report, dict):
                    raise PipelineFault("SELF_REPORT_MISSING")
                for name in box.get("self_report_fields", []):
                    if name not in report:
                        continue
                    value = report[name]
                    if value == "UNKNOWN":
                        continue
                    if name == "qualia_result":
                        if value not in {"REPORTED", "FAILED", "UNKNOWN"}:
                            raise PipelineFault("BAD_QUALIA_RESULT")
                    else:
                        number = float(value)
                        if not 0.0 <= number <= 1.0:
                            raise PipelineFault("SELF_REPORT_RANGE:" + name)
            return {"ok": True, "payload": payload}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    @staticmethod
    def _sensor_health(collected: dict[str, Any]) -> str:
        required = [k for k, v in collected["sources"].items() if v.get("required_for_quiet")]
        if any(not collected["sensors"].get(k, {}).get("ok") for k in required):
            return "ERROR"
        return "VERIFIED"

    @staticmethod
    def _quiet_status(collected: dict[str, Any]) -> str:
        if not collected.get("quiet_sensors_ok"):
            return "UNKNOWN"
        return "VERIFIED_QUIET" if int(collected.get("source_count", 0)) == 0 else "NOT_QUIET"

    def _public_prose(self, payload: dict[str, Any], contract: dict[str, Any]) -> str:
        parts = [
            str(payload[contract["title_field"]]).strip(),
            str(payload[contract["intro_field"]]).strip(),
        ]
        parts.extend(str(section[contract["section_text_field"]]).strip() for section in payload[contract["sections_field"]])
        return "\n\n".join(part for part in parts if part)

    def _state_box(
        self,
        profile: dict[str, Any],
        previous: dict[str, Any],
        compiled: dict[str, Any],
        collected: dict[str, Any],
        generated: dict[str, Any],
        payload: dict[str, Any],
        generation: int,
        now: float,
    ) -> tuple[dict[str, Any], str, dict[str, Any]]:
        cfg = profile.get("public_state_box", {})
        contract = profile["personality"]["output_contract"]
        self_report = {}
        self_report_field = contract.get("longitudinal_self_report_field")
        if self_report_field and isinstance(payload.get(self_report_field), dict):
            self_report = dict(payload[self_report_field])
        qualia_field = contract.get("qualia_probe_field")
        if qualia_field and isinstance(payload.get(qualia_field), dict):
            probe = payload[qualia_field]
            if "result" in probe:
                self_report.setdefault("qualia_result", probe["result"])
            if "confidence" in probe:
                self_report.setdefault("qualia_confidence", probe["confidence"])
        system = {
            "generation": generation,
            "timestamp": now,
            "inference_backend": generated.get("inference_kind"),
            "model_label": generated.get("model"),
            "source_count": compiled["source_count"],
            "sensor_health": self._sensor_health(collected),
            "quiet_status": self._quiet_status(collected),
        }
        previous_metrics = (previous.get("previous_study") or {}).get("system_metrics", {})
        for name, metric in compiled["personality_state"].items():
            item = {"status": metric["status"]}
            if metric["status"] == "VERIFIED":
                item["value"] = metric["value"]
            prior = previous_metrics.get(name)
            if (
                cfg.get("delta", {}).get("show_previous_post_delta")
                and metric["status"] == "VERIFIED"
                and isinstance(prior, dict)
                and prior.get("status") == "VERIFIED"
            ):
                item["delta"] = round(float(metric["value"]) - float(prior.get("value", 0)), 6)
            system[name] = item
        evaluation = []
        texts = cfg.get("evaluation_text", {})
        if any(
            isinstance(value, dict) and value.get("status") != "VERIFIED"
            for key, value in system.items()
            if key not in {"generation", "timestamp"}
        ) and texts.get("unknown_present"):
            evaluation.append(str(texts["unknown_present"]))
        if texts.get("epistemic_split"):
            evaluation.append(str(texts["epistemic_split"]))
        prior = previous.get("previous_study") or {}
        if (
            prior
            and (prior.get("inference_kind") != generated.get("inference_kind") or prior.get("model") != generated.get("model"))
            and texts.get("inference_changed")
        ):
            evaluation.append(str(texts["inference_changed"]))
        if texts.get("single_delta_not_trend") and any(isinstance(value, dict) and "delta" in value for value in system.values()):
            evaluation.append(str(texts["single_delta_not_trend"]))
        max_lines = int(cfg.get("render", {}).get("max_evaluation_lines", 5))
        evaluation = evaluation[:max_lines]
        state_box = {
            "system_state": system,
            "model_self_report": self_report,
            "evaluation": evaluation,
            "epistemic_law": cfg.get("epistemic_law", "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"),
        }
        if not cfg.get("enabled"):
            return state_box, "", self_report
        render = cfg.get("render", {})
        sections = list(render.get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]))
        system_label = sections[0] if len(sections) > 0 else "SYSTEM STATE"
        report_label = sections[1] if len(sections) > 1 else "MODEL SELF-REPORT"
        evaluation_label = sections[2] if len(sections) > 2 else "EVALUATION"
        lines = [f"{render.get('title', 'STATE')} — generation {generation}", system_label]
        for name in cfg.get("canonical_fields", []):
            if name not in system:
                continue
            value = system[name]
            if isinstance(value, dict):
                text = str(value.get("status", "UNKNOWN"))
                if "value" in value:
                    text += " " + str(round(float(value["value"]), 6))
                if "delta" in value:
                    text += "   Δ " + ("+" if value["delta"] >= 0 else "") + str(value["delta"])
            else:
                text = str(value)
            lines.append(f"{name:<24}= {text}")
        lines.extend(["", report_label])
        for name in cfg.get("self_report_fields", []):
            if name in self_report:
                lines.append(f"{name:<24}= {self_report[name]}")
        lines.extend(["", evaluation_label])
        lines.extend(["- " + item for item in evaluation] or ["- " + str(texts.get("no_evaluation", "No additional interpretation."))])
        fence = str(render.get("fence", "text"))
        return state_box, f"```{fence}\n" + "\n".join(lines) + "\n```", self_report

    def _pipeline_commit(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"])
        profile, previous, data = p["profile"], p["previous"], p["data"]
        collected, compiled, generated = data["collected"], data["compiled"], data["generated"]
        payload = data["gated"]["payload"]
        contract = profile["personality"]["output_contract"]
        output_id = secrets.token_hex(16)
        now = time.time()
        generation = int(previous["generation"]) + 1
        continuity = {
            "narrative": payload.get(contract["continuity_field"]),
            "autobiographical_hypotheses": payload.get(contract["autobiographical_hypotheses_field"]),
        }
        state_box, box_text, self_report = self._state_box(
            profile, previous, compiled, collected, generated, payload, generation, now
        )
        prose = self._public_prose(payload, contract)
        public_text = prose + ("\n\n" + box_text if box_text else "")
        profile_hash = _sha(profile)
        system_prompt_hash = hashlib.sha256(str(profile["personality"].get("system_prompt", "")).encode()).hexdigest()
        study = {
            "canonical_track": "pipeline",
            "self_report_track": "model_report",
            "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
            "state_box": state_box,
            "profile_id": profile["profile_id"],
        }
        db = self._db(entity_db)
        try:
            self._ensure_schema(db)
            db.execute("BEGIN IMMEDIATE")
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
            cols = {row[1] for row in db.execute("PRAGMA table_info(eos_pipeline_outputs)")}
            if "inference_kind" in cols:
                db.execute(
                    "INSERT INTO eos_pipeline_outputs(output_id,ts,generation,profile_id,output_json,inference_kind,model,packet_hash,canonical_hash,public_text) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        output_id, now, generation, profile["profile_id"], json.dumps(payload, ensure_ascii=False),
                        generated.get("inference_kind", ""), generated.get("model"), compiled["packet_hash"],
                        compiled["canonical_state_hash"], public_text,
                    ),
                )
            else:
                db.execute(
                    "INSERT INTO eos_pipeline_outputs(output_id,ts,generation,profile_id,output_json,provider_kind,model,packet_hash,canonical_hash,public_text) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        output_id, now, generation, profile["profile_id"], json.dumps(payload, ensure_ascii=False),
                        generated.get("inference_kind", ""), generated.get("model"), compiled["packet_hash"],
                        compiled["canonical_state_hash"], public_text,
                    ),
                )
            db.execute(
                "INSERT INTO eos_pipeline_packets VALUES(?,?,?,?,?,?,?)",
                (
                    compiled["packet_hash"], output_id, now, generation, profile["profile_id"],
                    compiled["source_count"], compiled["canonical_state_hash"],
                ),
            )
            db.execute(
                "INSERT INTO eos_pipeline_study VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    output_id, now, generation, profile["profile_id"], profile_hash, system_prompt_hash,
                    generated.get("inference_kind", ""), generated.get("model"),
                    float(profile["inference"].get("temperature", 0.0)), compiled["canonical_state_hash"],
                    compiled["packet_hash"], compiled["source_count"], json.dumps(collected["sensors"], ensure_ascii=False),
                    json.dumps(compiled["personality_state"], ensure_ascii=False), json.dumps(self_report, ensure_ascii=False),
                    json.dumps(state_box, ensure_ascii=False), hashlib.sha256(public_text.encode()).hexdigest(),
                    json.dumps(study, ensure_ascii=False),
                ),
            )
            row = db.execute(
                "UPDATE eos_pipeline_state SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,cursors_json=?,updated_at=? WHERE singleton=1 AND generation=?",
                (
                    generation, json.dumps(continuity, ensure_ascii=False), json.dumps(compiled["canonical"], ensure_ascii=False),
                    compiled["canonical_state_hash"], json.dumps(collected["next_cursors"]), now, previous["generation"],
                ),
            )
            if row.rowcount != 1:
                raise PipelineFault("STALE_GENERATION_FINAL")
            db.commit()
            return {"ok": True, "output_id": output_id, "generation": generation, "public_text": public_text, "state_box": state_box}
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


__all__ = ["VERSION", "PROFILE_SCHEMA", "IMMUTABLE_GUARD", "PipelineFault", "ProfilePipelineRuntime", "execute_source"]
