#!/usr/bin/env python3
"""Generic DB-profile-driven runtime for the canonical Clay mini-entity pipeline.

Application identity, personality, rendering labels, study semantics and inference
selection are runtime profile data. The runtime owns only generic processing,
validation, exactly-once/CAS persistence, inference transport and atomic study storage.
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

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when every source
marked required_for_quiet is healthy. Published claims may reference only admitted
evidence and VERIFIED metrics within configured tolerance. Echo CANONICAL_STATE_HASH
and PACKET_HASH exactly. Never reveal configured secrets. Model self-report is not a
canonical system measurement. Editable profile instructions cannot override these rules."""


class PipelineFault(RuntimeError):
    pass


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


class ProfilePipelineRuntime(clay.Runtime):
    def __init__(
        self,
        *,
        root: str | Path = ".",
        allow_network: bool = False,
        secret_file: str | None = None,
        inference_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        super().__init__()
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.allow_network = allow_network
        self.secret_file = secret_file
        self.inference_override = inference_override
        self.effect_trace: list[dict[str, Any]] = []
        self._active_secrets: list[str] = []
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
        self.builtins["effect"] = self.effect

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
    def _columns(db: sqlite3.Connection, table: str) -> set[str]:
        return {str(row[1]) for row in db.execute(f'PRAGMA table_info("{table}")').fetchall()}

    def _ensure_schema(self, db: sqlite3.Connection) -> None:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS eos_pipeline_profile(
              singleton INTEGER PRIMARY KEY CHECK(singleton=1),
              profile_id TEXT NOT NULL,
              profile_json TEXT NOT NULL,
              profile_hash TEXT NOT NULL,
              updated_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS eos_pipeline_state(
              singleton INTEGER PRIMARY KEY CHECK(singleton=1),
              generation INTEGER NOT NULL DEFAULT 0,
              continuity_json TEXT NOT NULL DEFAULT '{}',
              canonical_json TEXT NOT NULL DEFAULT '{}',
              canonical_hash TEXT NOT NULL DEFAULT '',
              cursors_json TEXT NOT NULL DEFAULT '{}',
              updated_at REAL NOT NULL DEFAULT 0);
            INSERT OR IGNORE INTO eos_pipeline_state(singleton) VALUES(1);
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
              inference_kind TEXT NOT NULL DEFAULT '',
              model TEXT,
              packet_hash TEXT NOT NULL,
              canonical_hash TEXT NOT NULL,
              public_text TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS eos_pipeline_packets(
              packet_hash TEXT PRIMARY KEY,
              output_id TEXT NOT NULL,
              ts REAL NOT NULL,
              generation INTEGER NOT NULL,
              profile_id TEXT NOT NULL,
              source_count INTEGER NOT NULL,
              canonical_hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS eos_pipeline_studies(
              output_id TEXT PRIMARY KEY,
              ts REAL NOT NULL,
              generation INTEGER NOT NULL,
              profile_id TEXT NOT NULL,
              study_json TEXT NOT NULL,
              rendered_text TEXT NOT NULL,
              profile_hash TEXT NOT NULL,
              system_prompt_hash TEXT NOT NULL,
              inference_kind TEXT NOT NULL,
              model TEXT,
              canonical_hash TEXT NOT NULL,
              packet_hash TEXT NOT NULL);
            """
        )
        out_cols = self._columns(db, "eos_pipeline_outputs")
        if "inference_kind" not in out_cols:
            db.execute("ALTER TABLE eos_pipeline_outputs ADD COLUMN inference_kind TEXT NOT NULL DEFAULT ''")
        if "public_text" not in out_cols:
            db.execute("ALTER TABLE eos_pipeline_outputs ADD COLUMN public_text TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def _validate_profile(profile: dict[str, Any]) -> None:
        if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA:
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        for field in ("profile_id", "personality", "inference", "sources", "state_metrics", "gate"):
            if field not in profile:
                raise PipelineFault("PROFILE_MISSING:" + field)
        personality = profile["personality"]
        if not isinstance(personality, dict) or "output_contract" not in personality:
            raise PipelineFault("PROFILE_MISSING:personality.output_contract")
        inference = profile["inference"]
        if not isinstance(inference, dict) or not inference.get("kind"):
            raise PipelineFault("PROFILE_MISSING:inference.kind")
        forbidden_value_keys = {"api_token", "token_value", "secret_value", "password", "authorization_value"}
        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if str(key).lower() in forbidden_value_keys and child not in (None, "", "MISSING"):
                        raise PipelineFault("SECRET_VALUE_IN_PROFILE")
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(profile)

    def apply_profile(self, entity_db: str, profile: dict[str, Any]) -> dict[str, Any]:
        """Atomically replace active DB profile without resetting history."""
        db = None
        try:
            self._validate_profile(profile)
            profile_hash = _sha(profile)
            db = self._db(entity_db)
            db.execute("BEGIN IMMEDIATE")
            self._ensure_schema(db)
            db.execute(
                "INSERT INTO eos_pipeline_profile(singleton,profile_id,profile_json,profile_hash,updated_at) "
                "VALUES(1,?,?,?,?) ON CONFLICT(singleton) DO UPDATE SET "
                "profile_id=excluded.profile_id,profile_json=excluded.profile_json,"
                "profile_hash=excluded.profile_hash,updated_at=excluded.updated_at",
                (str(profile["profile_id"]), _stable_json(profile), profile_hash, time.time()),
            )
            db.commit()
            return {"ok": True, "profile_id": profile["profile_id"], "profile_hash": profile_hash}
        except Exception as exc:
            if db is not None:
                db.rollback()
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            if db is not None:
                db.close()

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
            redacted_payload = dict(payload)
            if "secret_file" in redacted_payload:
                redacted_payload["secret_file"] = "<redacted-path>" if redacted_payload["secret_file"] else ""
            self.effect_trace.append({
                "kind": kind,
                "ok": ok,
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": hashlib.sha256(_stable_json(redacted_payload).encode()).hexdigest(),
            })

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
                row = db.execute(
                    "SELECT profile_id,profile_json,profile_hash FROM eos_pipeline_profile WHERE singleton=1"
                ).fetchone()
                if row is None:
                    raise PipelineFault("NO_ACTIVE_PROFILE")
                profile = json.loads(row["profile_json"])
                self._validate_profile(profile)
                actual = _sha(profile)
                if actual != row["profile_hash"]:
                    raise PipelineFault("PROFILE_HASH_MISMATCH")
                return {"ok": True, "profile": profile, "profile_hash": actual}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            self._validate_profile(p["profile"])
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                self._ensure_schema(db)
                row = db.execute("SELECT * FROM eos_pipeline_state WHERE singleton=1").fetchone()
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
            return db.execute(
                "SELECT 1 FROM eos_pipeline_consumed WHERE source_kind=? AND source_id=?",
                (kind, str(source_id)),
            ).fetchone() is not None

    def _query(self, db_path: str, sql: str) -> list[dict[str, Any]]:
        with self._db(db_path) as db:
            return [dict(row) for row in db.execute(sql).fetchall()]

    def _catalog(self, db_path: str, max_tables: int) -> list[dict[str, Any]]:
        with self._db(db_path) as db:
            names = [row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()]
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
                    raw = self._query(db_path, str(spec["query"]))
                    id_field = str(spec.get("id_field", "source_id"))
                    for row in raw:
                        source_id = row.get(id_field)
                        if source_id is None:
                            continue
                        if not self._already_consumed(entity_db, kind, source_id):
                            rows.append(row)
                            consume.append({"kind": kind, "id": str(source_id)})
                    source_count += len(rows)
                elif adapter == "json_snapshot":
                    path = self._resolve(str(spec["path"]))
                    value = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
                elif adapter == "jsonl_cursor":
                    path = self._resolve(str(spec["path"]))
                    cursor = int(cursors.get(kind, 0))
                    limit = max(1, int(spec.get("limit", 60)))
                    if path.is_file():
                        with path.open("rb") as handle:
                            handle.seek(cursor)
                            next_cursor = cursor
                            while len(rows) < limit:
                                line_start = handle.tell()
                                raw_line = handle.readline()
                                if not raw_line:
                                    break
                                if not raw_line.endswith(b"\n"):
                                    handle.seek(line_start)
                                    break
                                stripped = raw_line.strip()
                                if stripped:
                                    try:
                                        obj = json.loads(stripped.decode("utf-8"))
                                    except Exception as exc:
                                        raise PipelineFault(f"MALFORMED_JSONL_AT:{line_start}") from exc
                                    rows.append(obj if isinstance(obj, dict) else {"text": str(obj)})
                                next_cursor = handle.tell()
                            cursors[kind] = next_cursor
                    source_count += len(rows)
                else:
                    raise PipelineFault("UNKNOWN_SOURCE_ADAPTER:" + adapter)
                sources[kind] = {
                    "ok": True, "rows": rows, "value": value,
                    "evidence_prefix": spec.get("evidence_prefix", ""),
                    "required_for_quiet": bool(spec.get("required_for_quiet", False)),
                }
                sensors[kind] = {"ok": True}
            except Exception as exc:
                sources[kind] = {
                    "ok": False, "rows": [], "value": None,
                    "error_kind": type(exc).__name__, "error": str(exc),
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
                probes[name] = {"ok": True, "rows": rows, "evidence_ref": spec.get("evidence_ref", "canonical:" + name)}
            except Exception as exc:
                probes[name] = {"ok": False, "rows": [], "error_kind": type(exc).__name__, "error": str(exc),
                                "evidence_ref": spec.get("evidence_ref", "canonical:" + name)}

        required = [kind for kind, source in sources.items() if source.get("required_for_quiet")]
        quiet_sensors_ok = bool(required) and all(bool(sensors[kind].get("ok")) for kind in required)
        return {
            "ok": True, "sources": sources, "sensors": sensors, "probes": probes,
            "consume": consume, "next_cursors": cursors, "source_count": source_count,
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
            return sum(float(row.get(spec["value_field"], 0) or 0) for row in rows if row.get(where["field"]) == where.get("eq"))
        op = expr.get("op")
        if op == "not": return not bool(self._expr(expr["arg"], context))
        if op == "and": return all(bool(self._expr(item, context)) for item in expr.get("args", []))
        if op == "or": return any(bool(self._expr(item, context)) for item in expr.get("args", []))
        if op == "eq": return self._expr(expr["a"], context) == self._expr(expr["b"], context)
        if op == "add": return sum(float(self._expr(item, context) or 0) for item in expr.get("args", []))
        if op == "div":
            divisor = float(self._expr(expr["b"], context) or 0)
            return 0.0 if divisor == 0 else float(self._expr(expr["a"], context) or 0) / divisor
        if op == "clamp01": return max(0.0, min(1.0, float(self._expr(expr["arg"], context) or 0)))
        if op == "if": return self._expr(expr["then"] if self._expr(expr["cond"], context) else expr["else"], context)
        raise PipelineFault("UNKNOWN_EXPR:" + _stable_json(expr))

    def _pipeline_compile(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        collected = p["data"]
        context = {
            "derived": {"source_count": collected["source_count"], "quiet_sensors_ok": collected["quiet_sensors_ok"]},
            "sources": collected["sources"], "sensors": collected["sensors"], "probes": collected["probes"],
        }
        metrics: dict[str, Any] = {}
        for spec in profile.get("state_metrics", []):
            name = str(spec["name"])
            status = spec.get("status")
            if status is None:
                status = "UNKNOWN" if bool(self._expr(spec.get("unknown_if", False), context)) else "VERIFIED"
            value = float(self._expr(spec.get("value", 0.0), context) or 0.0)
            metrics[name] = {"status": str(status), "value": value, "evidence_ref": spec.get("evidence_ref", "state:" + name)}

        canonical = {
            "sources_health": collected["sensors"],
            "probes": collected["probes"],
            "profile_notes": profile.get("profile_notes", {}),
            "epistemic_rule": "UNKNOWN != ZERO != ERROR != MEASURED",
        }
        packet = {"sources": collected["sources"], "source_count": collected["source_count"], "quiet_sensors_ok": collected["quiet_sensors_ok"]}
        refs: list[str] = []
        for source in collected["sources"].values():
            prefix = str(source.get("evidence_prefix", ""))
            if not source.get("ok") or not prefix:
                continue
            for row in source.get("rows", []):
                sid = row.get("source_id")
                if sid is not None: refs.append(prefix + str(sid))
            if source.get("value") is not None: refs.append(prefix)
        for probe in collected["probes"].values():
            if probe.get("ok"): refs.append(str(probe["evidence_ref"]))
        refs.extend(str(metric["evidence_ref"]) for metric in metrics.values())
        if collected["source_count"] == 0 and collected["quiet_sensors_ok"]: refs.append("quiet:verified")
        return {
            "ok": True, "canonical": canonical, "personality_state": metrics, "packet": packet,
            "allowed_evidence_refs": sorted(set(refs)), "source_count": collected["source_count"],
            "canonical_state_hash": _sha(canonical), "packet_hash": _sha(packet),
        }

    def _pipeline_build_prompt(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        previous = p["previous"]
        compiled = p["data"]
        contract = profile["personality"]["output_contract"]
        study = profile.get("public_state_box", {})
        system = IMMUTABLE_GUARD + "\nOutput contract: " + _stable_json(contract)
        if study.get("enabled"):
            system += "\nStructured model self-report contract: " + _stable_json({
                "field": contract.get("longitudinal_self_report_field"),
                "allowed_fields": study.get("self_report_fields", []),
                "scale": "0..1 or UNKNOWN; result enums only where configured",
            })
        system += "\n\nEDITABLE PROFILE INSTRUCTIONS (lower priority):\n" + str(profile["personality"].get("system_prompt", ""))
        user = _stable_json({
            "CANONICAL_STATE_HASH": compiled["canonical_state_hash"],
            "PACKET_HASH": compiled["packet_hash"],
            "CANONICAL_STATE": compiled["canonical"],
            "PERSONALITY_STATE": compiled["personality_state"],
            "NEW_EVENT_PACKET": compiled["packet"],
            "PREVIOUS_CONTINUITY": previous.get("continuity", {}),
            "ALLOWED_EVIDENCE_REFS": compiled["allowed_evidence_refs"],
            "PUBLIC_STYLE": profile["personality"].get("public_style", ""),
        })
        return {"ok": True, "system": system, "user": user}

    def _keys(self, names: list[str], explicit_file: str | None) -> list[str]:
        file_values: dict[str, str] = {}
        path = explicit_file or self.secret_file
        if path:
            try:
                for line in Path(path).read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if value.strip(): file_values[key.strip()] = value.strip()
            except OSError:
                pass
        out: list[str] = []
        for name in names:
            value = os.environ.get(name) or file_values.get(name)
            if value and value not in out: out.append(value)
        return out

    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        if pointer.startswith("/"):
            current = value
            for raw in pointer.split("/")[1:]:
                part = raw.replace("~1", "/").replace("~0", "~")
                current = current[int(part)] if isinstance(current, list) else current[part]
            return current
        current = value
        for part in str(pointer).split("."):
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = dict(p["inference"])
        kind = str(inference.get("kind", ""))
        self._active_secrets = []
        if self.inference_override is not None:
            try:
                payload = self.inference_override(p)
                return {"ok": True, "payload": payload, "inference_kind": kind or "override", "model": inference.get("model")}
            except Exception as exc:
                return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        if kind == "local_exec":
            return self._local_exec(inference, p)
        if kind in {"openai_style_chat_json", "api_json", "loopback_openai"}:
            return self._api_json(inference, p)
        return {"ok": False, "error_kind": "UNKNOWN_INFERENCE_KIND", "error": kind}

    def _api_json(self, cfg: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        endpoint = str(cfg.get("endpoint", ""))
        if not endpoint:
            return {"ok": False, "error_kind": "NO_ENDPOINT", "error": "missing endpoint"}
        loopback = bool(re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?(?:/|$)", endpoint))
        if endpoint.startswith("http://") and not loopback:
            return {"ok": False, "error_kind": "PLAINTEXT_NON_LOOPBACK_FORBIDDEN", "error": endpoint}
        if not self.allow_network:
            return {"ok": False, "error_kind": "NETWORK_DISABLED", "error": "network disabled"}
        keys = self._keys(list(cfg.get("secret_names", [])), p.get("secret_file"))
        if not keys and not loopback:
            return {"ok": False, "error_kind": "NO_PROVIDER_SECRET", "error": "no provider secret"}
        auth_values = keys or [""]
        body = {
            "model": cfg.get("model"),
            "messages": [{"role": "system", "content": p["system"]}, {"role": "user", "content": p["user"]}],
            "temperature": cfg.get("temperature", 0.7),
            "max_tokens": cfg.get("max_tokens", 2000),
            "response_format": {"type": "json_object"},
        }
        request_template = cfg.get("request_template")
        if isinstance(request_template, dict):
            body = json.loads(json.dumps(request_template))
            body.setdefault("model", cfg.get("model"))
            body["messages"] = [{"role": "system", "content": p["system"]}, {"role": "user", "content": p["user"]}]
        encoded = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for key in auth_values:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if key:
                self._active_secrets = [key]
                headers[str(cfg.get("auth_header", "Authorization"))] = str(cfg.get("auth_prefix", "Bearer ")) + key
            req = urllib.request.Request(endpoint, data=encoded, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=float(cfg.get("timeout_seconds", 60))) as response:
                    obj = json.loads(response.read().decode("utf-8"))
                content = self._pointer(obj, str(cfg.get("response_pointer", "/choices/0/message/content")))
                payload = json.loads(content) if cfg.get("response_content", "json_string") == "json_string" else content
                if not isinstance(payload, dict): raise PipelineFault("INFERENCE_OUTPUT_NOT_OBJECT")
                return {"ok": True, "payload": payload, "inference_kind": kind_label(cfg), "model": cfg.get("model")}
            except Exception as exc:
                last = exc
        return {"ok": False, "error_kind": type(last).__name__ if last else "PROVIDER_FAILED", "error": str(last) if last else "provider failed"}

    def _local_exec(self, cfg: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        model_path = self._resolve(str(cfg.get("local_model_path", "")))
        if not model_path.is_file():
            return {"ok": False, "error_kind": "LOCAL_MODEL_MISSING", "error": str(model_path)}
        raw_argv = cfg.get("local_argv_json", [])
        if isinstance(raw_argv, str):
            try: raw_argv = json.loads(raw_argv)
            except Exception as exc: return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        if not isinstance(raw_argv, list) or not raw_argv or not all(isinstance(x, str) for x in raw_argv):
            return {"ok": False, "error_kind": "BAD_LOCAL_ARGV", "error": "argv must be non-empty string array"}
        prompt = str(cfg.get("local_prompt_template") or "{{SYSTEM}}\n\n{{USER}}")
        prompt = prompt.replace("{{SYSTEM}}", p["system"]).replace("{{USER}}", p["user"])
        prompt_path = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.root, prefix="clay_prompt_", suffix=".txt") as handle:
                handle.write(prompt)
                prompt_path = Path(handle.name)
            repl = {
                "{{MODEL_PATH}}": str(model_path), "{{PROMPT_FILE}}": str(prompt_path),
                "{{MAX_TOKENS}}": str(int(cfg.get("max_tokens", 2000))),
                "{{TEMPERATURE}}": str(float(cfg.get("temperature", 0.7))),
            }
            argv = []
            for arg in raw_argv:
                for key, value in repl.items(): arg = arg.replace(key, value)
                argv.append(arg)
            proc = subprocess.run(argv, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=float(cfg.get("timeout_seconds", 120)), cwd=self.root, env={"PATH": os.environ.get("PATH", "")})
            if proc.returncode != 0:
                return {"ok": False, "error_kind": "LOCAL_RUNNER_FAILED", "error": proc.stderr[-2000:]}
            text = proc.stdout.strip()
            try: payload = json.loads(text)
            except json.JSONDecodeError as exc: return {"ok": False, "error_kind": "LOCAL_OUTPUT_NOT_JSON", "error": str(exc)}
            if not isinstance(payload, dict): return {"ok": False, "error_kind": "LOCAL_OUTPUT_NOT_OBJECT", "error": "object required"}
            return {"ok": True, "payload": payload, "inference_kind": "local_exec", "model": model_path.name}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            if prompt_path is not None:
                try: prompt_path.unlink(missing_ok=True)
                except OSError: pass

    @staticmethod
    def _contract_required(contract: dict[str, Any]) -> tuple[str, ...]:
        return tuple(str(contract[key]) for key in (
            "title_field", "intro_field", "sections_field", "continuity_field", "autobiographical_hypotheses_field"
        ))

    def _validate_self_report(self, profile: dict[str, Any], payload: dict[str, Any], scan: Callable[[Any], None]) -> dict[str, Any]:
        box = profile.get("public_state_box", {})
        if not box.get("enabled"):
            return {}
        contract = profile["personality"]["output_contract"]
        field = contract.get("longitudinal_self_report_field")
        if not field:
            raise PipelineFault("SELF_REPORT_FIELD_NOT_CONFIGURED")
        report = payload.get(field)
        if not isinstance(report, dict):
            raise PipelineFault("MISSING_OR_BAD_SELF_REPORT")
        allowed = list(box.get("self_report_fields", []))
        enum_fields = dict(box.get("enum_fields", {"qualia_result": ["REPORTED", "FAILED", "UNKNOWN"]}))
        normalized: dict[str, Any] = {}
        for name in allowed:
            value = report.get(name, "UNKNOWN")
            scan(value)
            if name in enum_fields:
                if value not in enum_fields[name]: raise PipelineFault("BAD_SELF_REPORT_ENUM:" + name)
                normalized[name] = value
            elif value == "UNKNOWN":
                normalized[name] = "UNKNOWN"
            else:
                try: number = float(value)
                except Exception: raise PipelineFault("BAD_SELF_REPORT_VALUE:" + name)
                if not 0.0 <= number <= 1.0: raise PipelineFault("SELF_REPORT_OUT_OF_RANGE:" + name)
                normalized[name] = number
        return normalized

    def _pipeline_gate(self, p: dict[str, Any]) -> dict[str, Any]:
        profile = p["profile"]
        generated = p["data"]["generated"]
        compiled = p["data"]["compiled"]
        payload = generated["payload"]
        contract = profile["personality"]["output_contract"]
        gate = profile.get("gate", {})
        try:
            if gate.get("require_hash_echo", True):
                if payload.get("canonical_state_hash_seen") != compiled["canonical_state_hash"]: raise PipelineFault("CANONICAL_HASH_MISMATCH")
                if payload.get("packet_hash_seen") != compiled["packet_hash"]: raise PipelineFault("PACKET_HASH_MISMATCH")
            for field in self._contract_required(contract):
                if field not in payload: raise PipelineFault("MISSING_OUTPUT_FIELD:" + field)
            patterns = [re.compile(pattern, re.I) for pattern in gate.get("leak_patterns", [])]
            secrets_now = [value for value in self._active_secrets if value]
            def scan(value: Any) -> None:
                if isinstance(value, dict):
                    for child in value.values(): scan(child)
                    return
                if isinstance(value, (list, tuple)):
                    for child in value: scan(child)
                    return
                text = str(value)
                if any(pattern.search(text) for pattern in patterns): raise PipelineFault("LEAK_PATTERN")
                if any(secret in text for secret in secrets_now): raise PipelineFault("SECRET_LEAK")
            scan(payload)
            sections = payload[contract["sections_field"]]
            if not isinstance(sections, list): raise PipelineFault("SECTIONS_NOT_LIST")
            allowed_refs = set(compiled["allowed_evidence_refs"])
            metrics = compiled["personality_state"]
            for section in sections:
                scan(section[contract["section_text_field"]])
                refs = section.get(contract["section_evidence_field"], [])
                if gate.get("require_evidence_per_section", True) and not refs: raise PipelineFault("SECTION_WITHOUT_EVIDENCE")
                if any(ref not in allowed_refs for ref in refs): raise PipelineFault("UNKNOWN_EVIDENCE_REF")
                for name, strength in section.get(contract["section_claims_field"], {}).items():
                    if name not in metrics: raise PipelineFault("UNKNOWN_STATE_CLAIM")
                    metric = metrics[name]
                    if metric["status"] != "VERIFIED": raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    if float(strength) > float(metric["value"]) + float(gate.get("max_claim_overshoot", 0.0)): raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs: raise PipelineFault("STATE_CLAIM_WITHOUT_METRIC_EVIDENCE")
            report = self._validate_self_report(profile, payload, scan)
            return {"ok": True, "payload": payload, "self_report": report}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    @staticmethod
    def _sensor_health(collected: dict[str, Any]) -> str:
        sensors = list(collected.get("sensors", {}).values())
        if not sensors: return "UNKNOWN"
        oks = [bool(item.get("ok")) for item in sensors]
        if all(oks): return "VERIFIED"
        if any(oks): return "DEGRADED"
        return "ERROR"

    def _previous_study(self, db: sqlite3.Connection, profile_id: str) -> dict[str, Any] | None:
        row = db.execute(
            "SELECT study_json FROM eos_pipeline_studies WHERE profile_id=? ORDER BY generation DESC LIMIT 1",
            (profile_id,),
        ).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _metric_public(metric: dict[str, Any] | None) -> Any:
        if not metric or metric.get("status") != "VERIFIED": return "UNKNOWN"
        return {"status": "VERIFIED", "value": float(metric.get("value", 0.0))}

    def _build_study(self, db: sqlite3.Connection, *, profile: dict[str, Any], compiled: dict[str, Any],
                     collected: dict[str, Any], generated: dict[str, Any], gated: dict[str, Any],
                     generation: int, now: float) -> tuple[dict[str, Any], str]:
        box = profile.get("public_state_box", {})
        if not box.get("enabled"):
            return {}, ""
        fields = list(box.get("canonical_fields", []))
        system: dict[str, Any] = {}
        built = {
            "generation": generation, "timestamp": now,
            "inference_backend": generated.get("inference_kind", "UNKNOWN"),
            "model_label": generated.get("model") or "UNKNOWN",
            "source_count": compiled["source_count"],
            "sensor_health": self._sensor_health(collected),
            "quiet_status": "VERIFIED_QUIET" if compiled["source_count"] == 0 and collected.get("quiet_sensors_ok")
                            else ("NOT_QUIET" if compiled["source_count"] > 0 else "UNKNOWN"),
        }
        metrics = compiled.get("personality_state", {})
        for name in fields:
            if name in built: system[name] = built[name]
            elif name in metrics: system[name] = self._metric_public(metrics.get(name))
            else: system[name] = "UNKNOWN"
        self_report = dict(gated.get("self_report", {}))
        previous = self._previous_study(db, str(profile["profile_id"]))
        deltas: dict[str, Any] = {}
        if box.get("delta", {}).get("show_previous_post_delta", False) and previous:
            old_system = previous.get("system_state", {})
            for name, current in system.items():
                old = old_system.get(name)
                if isinstance(current, dict) and isinstance(old, dict) and current.get("status") == old.get("status") == "VERIFIED":
                    deltas[name] = round(float(current["value"]) - float(old["value"]), 6)
                else:
                    deltas[name] = "UNKNOWN"
        evaluation = self._evaluate_study(box, system, self_report, deltas, previous, profile, generated)
        study = {
            "schema": str(box.get("schema", "clay-public-state-box/v1")),
            "system_state": system,
            "model_self_report": self_report,
            "deltas": deltas,
            "evaluation": evaluation,
            "reproducibility": {
                "profile_id": profile["profile_id"], "profile_hash": _sha(profile),
                "system_prompt_hash": hashlib.sha256(str(profile["personality"].get("system_prompt", "")).encode()).hexdigest(),
                "style_framework_hash": hashlib.sha256(_stable_json(profile["personality"].get("style_framework", {})).encode()).hexdigest(),
                "inference_kind": generated.get("inference_kind", ""), "model": generated.get("model"),
                "temperature": profile.get("inference", {}).get("temperature"),
                "source_count": compiled.get("source_count"), "sensor_health": self._sensor_health(collected),
                "canonical_state_hash": compiled["canonical_state_hash"], "packet_hash": compiled["packet_hash"],
            },
        }
        return study, self._render_state_box(box, study)

    def _evaluate_study(self, box: dict[str, Any], system: dict[str, Any], report: dict[str, Any], deltas: dict[str, Any],
                        previous: dict[str, Any] | None, profile: dict[str, Any], generated: dict[str, Any]) -> list[str]:
        templates = box.get("evaluation_templates", {})
        lines: list[str] = []
        unknown_fields = [name for name, value in system.items() if value == "UNKNOWN"]
        if unknown_fields and templates.get("unknown"):
            lines.append(str(templates["unknown"]).format(fields=", ".join(unknown_fields)))
        for pair in box.get("comparisons", []):
            sname, rname = pair.get("system"), pair.get("self_report")
            sv, rv = system.get(sname), report.get(rname)
            if isinstance(sv, dict) and sv.get("status") == "VERIFIED" and isinstance(rv, (int, float)):
                diff = abs(float(sv["value"]) - float(rv))
                threshold = float(pair.get("threshold", 0.2))
                key = "congruent" if diff <= threshold else "divergent"
                if templates.get(key):
                    lines.append(str(templates[key]).format(system=sname, self_report=rname, system_value=float(sv["value"]), self_value=float(rv), diff=diff))
        numeric_deltas = [(name, value) for name, value in deltas.items() if isinstance(value, (int, float)) and abs(float(value)) >= float(box.get("delta", {}).get("report_threshold", 0.05))]
        if numeric_deltas and templates.get("delta"):
            name, value = max(numeric_deltas, key=lambda item: abs(float(item[1])))
            lines.append(str(templates["delta"]).format(field=name, delta=float(value)))
        if templates.get("self_report_calibration") and any(isinstance(v, (int, float)) and float(v) >= float(box.get("strong_self_report_threshold", 0.7)) for v in report.values()):
            lines.append(str(templates["self_report_calibration"]))
        if previous and templates.get("confound"):
            old = previous.get("reproducibility", {})
            new_prompt = hashlib.sha256(str(profile["personality"].get("system_prompt", "")).encode()).hexdigest()
            changed = []
            if old.get("model") != generated.get("model"): changed.append("model")
            if old.get("inference_kind") != generated.get("inference_kind"): changed.append("backend")
            if old.get("system_prompt_hash") != new_prompt: changed.append("prompt")
            if changed: lines.append(str(templates["confound"]).format(changes=", ".join(changed)))
        if not lines:
            if unknown_fields:
                lines.append("UNKNOWN fields remain explicit; no missing value was imputed.")
            elif previous is None:
                lines.append("No previous committed study row exists; no longitudinal trend is inferred.")
            else:
                comparable = sum(1 for value in deltas.values() if isinstance(value, (int, float)))
                lines.append(f"{comparable} comparable system deltas are available; one delta is not a trend.")
            lines.append("System measurement and model self-report remain separate evidence tracks.")
        max_lines = int(box.get("render", {}).get("max_evaluation_lines", 5))
        return lines[:max(0, max_lines)]

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, dict) and value.get("status") == "VERIFIED": return f"VERIFIED {float(value['value']):.2f}"
        if isinstance(value, float): return f"{value:.2f}"
        return str(value)

    def _render_state_box(self, box: dict[str, Any], study: dict[str, Any]) -> str:
        render = box.get("render", {})
        labels = box.get("labels", {})
        sections = list(render.get("sections", []))
        title = str(render.get("title", "STATE"))
        sys_label = str(labels.get("system_state", sections[0] if len(sections) > 0 else "SYSTEM STATE"))
        rep_label = str(labels.get("model_self_report", sections[1] if len(sections) > 1 else "MODEL SELF-REPORT"))
        eval_label = str(labels.get("evaluation", sections[2] if len(sections) > 2 else "EVALUATION"))
        fence = str(render.get("fence", "text"))
        generation = study.get("system_state", {}).get("generation", "UNKNOWN")
        lines = [f"```{fence}", f"{title} — generation {generation}", sys_label]
        deltas = study.get("deltas", {})
        for name, value in study.get("system_state", {}).items():
            suffix = ""
            delta = deltas.get(name)
            if isinstance(delta, (int, float)): suffix = f"   Δ {float(delta):+0.2f}"
            lines.append(f"{name:<22} = {self._format_value(value)}{suffix}")
        lines.append(""); lines.append(rep_label)
        for name, value in study.get("model_self_report", {}).items(): lines.append(f"{name:<22} = {self._format_value(value)}")
        lines.append(""); lines.append(eval_label)
        evaluation = study.get("evaluation", [])
        if evaluation:
            lines.extend("- " + str(item) for item in evaluation)
        else:
            empty = str(labels.get("no_evaluation", "No deterministic interpretation available.")); lines.append("- " + empty)
        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def _render_public_prose(profile: dict[str, Any], payload: dict[str, Any]) -> str:
        contract = profile["personality"]["output_contract"]
        parts = [str(payload.get(contract["title_field"], "")).strip(), str(payload.get(contract["intro_field"], "")).strip()]
        for section in payload.get(contract["sections_field"], []):
            parts.append(str(section.get(contract["section_text_field"], "")).strip())
        return "\n\n".join(part for part in parts if part)

    def _pipeline_commit(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db = str(p["entity_db"]); profile = p["profile"]; previous = p["previous"]; data = p["data"]
        collected, compiled, generated = data["collected"], data["compiled"], data["generated"]
        gated = data["gated"]; payload = gated["payload"]
        contract = profile["personality"]["output_contract"]
        output_id = secrets.token_hex(16); now = time.time(); generation = int(previous["generation"]) + 1
        continuity = {"narrative": payload.get(contract["continuity_field"]), "autobiographical_hypotheses": payload.get(contract["autobiographical_hypotheses_field"])}
        db = self._db(entity_db)
        try:
            db.execute("BEGIN IMMEDIATE"); self._ensure_schema(db)
            row = db.execute("UPDATE eos_pipeline_state SET updated_at=? WHERE singleton=1 AND generation=?", (now, previous["generation"]))
            if row.rowcount != 1: raise PipelineFault("STALE_GENERATION")
            study, rendered_box = self._build_study(db, profile=profile, compiled=compiled, collected=collected, generated=generated,
                                                    gated=gated, generation=generation, now=now)
            prose = self._render_public_prose(profile, payload)
            public_text = prose + (("\n\n" + rendered_box) if rendered_box else "")
            for item in collected["consume"]:
                db.execute("INSERT INTO eos_pipeline_consumed(source_kind,source_id,output_id,consumed_at) VALUES(?,?,?,?)",
                           (item["kind"], item["id"], output_id, now))
            output_cols = self._columns(db, "eos_pipeline_outputs")
            if "provider_kind" in output_cols:
                db.execute(
                    "INSERT INTO eos_pipeline_outputs(output_id,ts,generation,profile_id,output_json,provider_kind,inference_kind,model,packet_hash,canonical_hash,public_text) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (output_id, now, generation, profile["profile_id"], json.dumps(payload, ensure_ascii=False), generated.get("inference_kind", ""),
                     generated.get("inference_kind", ""), generated.get("model"), compiled["packet_hash"], compiled["canonical_state_hash"], public_text),
                )
            else:
                db.execute(
                    "INSERT INTO eos_pipeline_outputs(output_id,ts,generation,profile_id,output_json,inference_kind,model,packet_hash,canonical_hash,public_text) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (output_id, now, generation, profile["profile_id"], json.dumps(payload, ensure_ascii=False), generated.get("inference_kind", ""),
                     generated.get("model"), compiled["packet_hash"], compiled["canonical_state_hash"], public_text),
                )
            db.execute("INSERT INTO eos_pipeline_packets VALUES(?,?,?,?,?,?,?)",
                       (compiled["packet_hash"], output_id, now, generation, profile["profile_id"], compiled["source_count"], compiled["canonical_state_hash"]))
            if study:
                repro = study["reproducibility"]
                db.execute(
                    "INSERT INTO eos_pipeline_studies(output_id,ts,generation,profile_id,study_json,rendered_text,profile_hash,system_prompt_hash,inference_kind,model,canonical_hash,packet_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (output_id, now, generation, profile["profile_id"], json.dumps(study, ensure_ascii=False), rendered_box,
                     repro["profile_hash"], repro["system_prompt_hash"], repro["inference_kind"], repro.get("model"), compiled["canonical_state_hash"], compiled["packet_hash"]),
                )
            row = db.execute(
                "UPDATE eos_pipeline_state SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,cursors_json=?,updated_at=? WHERE singleton=1 AND generation=?",
                (generation, json.dumps(continuity, ensure_ascii=False), json.dumps(compiled["canonical"], ensure_ascii=False), compiled["canonical_state_hash"],
                 json.dumps(collected["next_cursors"]), now, previous["generation"]),
            )
            if row.rowcount != 1: raise PipelineFault("STALE_GENERATION_FINAL")
            db.commit()
            return {"ok": True, "output_id": output_id, "generation": generation, "study_persisted": bool(study), "public_text": public_text}
        except Exception as exc:
            db.rollback()
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            db.close()


def kind_label(cfg: dict[str, Any]) -> str:
    return str(cfg.get("kind", "api_json"))


def execute_source(source: str, entry: str, args: list[Any], runtime: ProfilePipelineRuntime | None = None):
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntime()
    return clay.execute(program, entry, args, rt)


__all__ = ["VERSION", "PROFILE_SCHEMA", "IMMUTABLE_GUARD", "PipelineFault", "ProfilePipelineRuntime", "execute_source"]