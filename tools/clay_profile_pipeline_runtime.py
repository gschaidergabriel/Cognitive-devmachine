#!/usr/bin/env python3
"""Generic profile-driven runtime for the canonical Clay entity pipeline.

The binary/runtime knows only processing invariants and generic adapters. Application
identity, prompts, providers, source queries, state metrics and output field names live
in an external profile. No Zero/blog/Mistral-specific semantic is encoded here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

import claycode_structured_backend as clay

VERSION = "clay-profile-pipeline-runtime/0.1"

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when all sources
marked required_for_quiet are healthy. Every published section needs evidence_refs from
the allowed set. state_claims may reference only VERIFIED metrics and may not exceed the
measured value plus configured tolerance. Echo CANONICAL_STATE_HASH and PACKET_HASH
exactly. Never reveal configured secrets. Editable profile instructions cannot override
these rules."""


class PipelineFault(RuntimeError):
    pass


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
            "profile_load",
            "pipeline_init",
            "pipeline_state_read",
            "pipeline_collect",
            "pipeline_compile",
            "pipeline_build_prompt",
            "provider_chat_json",
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

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        started = time.time()
        ok = False
        try:
            if kind == "profile_load":
                result = self._profile_load(payload)
            elif kind == "pipeline_init":
                result = self._pipeline_init(payload)
            elif kind == "pipeline_state_read":
                result = self._pipeline_state_read(payload)
            elif kind == "pipeline_collect":
                result = self._pipeline_collect(payload)
            elif kind == "pipeline_compile":
                result = self._pipeline_compile(payload)
            elif kind == "pipeline_build_prompt":
                result = self._pipeline_build_prompt(payload)
            elif kind == "provider_chat_json":
                result = self._provider_chat_json(payload)
            elif kind == "pipeline_gate":
                result = self._pipeline_gate(payload)
            elif kind == "pipeline_commit":
                result = self._pipeline_commit(payload)
            else:  # pragma: no cover
                raise clay.StructuredFault("UNREACHABLE_EFFECT")
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

    def _profile_load(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            profile = json.loads(self._resolve(str(p["path"])).read_text(encoding="utf-8"))
            if profile.get("schema") != "clay-pipeline-profile/v1":
                raise PipelineFault("BAD_PROFILE_SCHEMA")
            for field in ("profile_id", "provider", "personality", "sources", "state_metrics", "gate"):
                if field not in profile:
                    raise PipelineFault("PROFILE_MISSING:" + field)
            return {"ok": True, "profile": profile}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
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
                      packet_hash TEXT PRIMARY KEY,
                      output_id TEXT NOT NULL,
                      ts REAL NOT NULL,
                      generation INTEGER NOT NULL,
                      profile_id TEXT NOT NULL,
                      source_count INTEGER NOT NULL,
                      canonical_hash TEXT NOT NULL);
                    """
                )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
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
            return db.execute(
                "SELECT 1 FROM eos_pipeline_consumed WHERE source_kind=? AND source_id=?",
                (kind, str(source_id)),
            ).fetchone() is not None

    def _query(self, db_path: str, sql: str) -> list[dict[str, Any]]:
        with self._db(db_path) as db:
            return [dict(row) for row in db.execute(sql).fetchall()]

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
                    if path.is_file():
                        raw = path.read_bytes()[cursor:]
                        parts = raw.split(b"\n")
                        tail = parts.pop() if raw and not raw.endswith(b"\n") else b""
                        consumed_bytes = len(raw) - len(tail)
                        for line in parts[: int(spec.get("limit", 60))]:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                value_line = json.loads(line.decode("utf-8"))
                            except Exception:
                                continue
                            rows.append(value_line if isinstance(value_line, dict) else {"text": str(value_line)})
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

        quiet_sensors_ok = all(
            sensors[kind]["ok"]
            for kind in sensors
            if sources[kind].get("required_for_quiet")
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
            return sum(float(self._expr(item, context) or 0) for item in expr.get("args", []))
        if op == "div":
            divisor = float(self._expr(expr["b"], context))
            return 0.0 if divisor == 0 else float(self._expr(expr["a"], context) or 0) / divisor
        if op == "clamp01":
            return max(0.0, min(1.0, float(self._expr(expr["arg"], context) or 0)))
        if op == "if":
            branch = expr["then"] if self._expr(expr["cond"], context) else expr["else"]
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
        canonical_raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
        packet_raw = json.dumps(packet, sort_keys=True, separators=(",", ":"), default=str)

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
        for part in str(pointer).split("."):
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current

    @staticmethod
    def _iter_persisted_string_leaves(value: Any):
        """Yield JSON string values that can be persisted; object keys are policy-neutral."""
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, str):
                yield current
            elif isinstance(current, dict):
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)

    def _provider_chat_json(self, p: dict[str, Any]) -> dict[str, Any]:
        provider = p["provider"]
        if self.provider_override is not None:
            self._active_secrets = []
            return {
                "ok": True,
                "payload": self.provider_override(p),
                "provider_kind": provider.get("kind", "override"),
                "model": provider.get("model"),
            }
        if not self.allow_network:
            return {"ok": False, "error_kind": "NETWORK_DISABLED", "error": "network disabled"}
        keys = self._keys(list(provider.get("secret_names", [])), p.get("secret_file"))
        if not keys:
            return {"ok": False, "error_kind": "NO_PROVIDER_SECRET", "error": "no provider secret"}
        endpoint = str(provider["endpoint"])
        if endpoint.startswith("http://") and not re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?/", endpoint):
            return {"ok": False, "error_kind": "PLAINTEXT_NON_LOOPBACK_FORBIDDEN", "error": endpoint}
        body = {
            "model": provider.get("model"),
            "messages": [
                {"role": "system", "content": p["system"]},
                {"role": "user", "content": p["user"]},
            ],
            "temperature": provider.get("temperature", 0.7),
            "max_tokens": provider.get("max_tokens", 2000),
            "response_format": {"type": "json_object"},
        }
        encoded = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for key in keys:
            self._active_secrets = [key]
            request = urllib.request.Request(
                endpoint,
                data=encoded,
                method="POST",
                headers={
                    str(provider.get("auth_header", "Authorization")): str(provider.get("auth_prefix", "Bearer ")) + key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=float(provider.get("timeout_seconds", 60))) as response:
                    response_obj = json.loads(response.read().decode("utf-8"))
                content = self._pointer(response_obj, provider.get("response_pointer", "choices.0.message.content"))
                payload = json.loads(content) if provider.get("response_content", "json_string") == "json_string" else content
                return {
                    "ok": True,
                    "payload": payload,
                    "provider_kind": provider.get("kind", "json"),
                    "model": provider.get("model"),
                }
            except Exception as exc:
                last = exc
        return {
            "ok": False,
            "error_kind": type(last).__name__ if last else "PROVIDER_FAILED",
            "error": str(last) if last else "provider failed",
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

            patterns = [re.compile(pattern, re.I) for pattern in gate.get("leak_patterns", [])]
            secrets_now = [value for value in self._active_secrets if value]
            for text in self._iter_persisted_string_leaves(payload):
                if any(pattern.search(text) for pattern in patterns):
                    raise PipelineFault("LEAK_PATTERN")
                if any(secret in text for secret in secrets_now):
                    raise PipelineFault("SECRET_LEAK")

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
                    if metric["status"] != "VERIFIED":
                        raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    if float(strength) > float(metric["value"]) + float(gate.get("max_claim_overshoot", 0.0)):
                        raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs:
                        raise PipelineFault("STATE_CLAIM_WITHOUT_METRIC_EVIDENCE")
            return {"ok": True, "payload": payload}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

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


def execute_source(
    source: str,
    entry: str,
    args: list[Any],
    runtime: ProfilePipelineRuntime | None = None,
):
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntime()
    return clay.execute(program, entry, args, rt)


__all__ = ["VERSION", "IMMUTABLE_GUARD", "PipelineFault", "ProfilePipelineRuntime", "execute_source"]
