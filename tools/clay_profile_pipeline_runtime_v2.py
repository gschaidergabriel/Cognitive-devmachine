#!/usr/bin/env python3
"""DB-resident v2 adapter for the canonical generic Clay entity pipeline.

This module converges the current BLOGPOST_ENTITY.clay contract onto the existing
profile-driven runtime without embedding application/personality semantics. It adds:

- clay-pipeline-profile/v2 DB-resident active profile state;
- current effect names: pipeline_profile_read + inference_generate;
- tokenless loopback API and direct local_exec inference;
- generic, configurable longitudinal study/publication materialization;
- one atomic commit boundary for output, consumption, state, study record and publication.

Zero/blog/Gasthaus semantics remain profile data. This module never hard-codes them.
"""
from __future__ import annotations

import hashlib
import json
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
from clay_profile_pipeline_runtime import ProfilePipelineRuntime as LegacyProfilePipelineRuntime

VERSION = "clay-profile-pipeline-runtime-v2/0.2"
PROFILE_SCHEMA = "clay-pipeline-profile/v2"
STUDY_SCHEMA = "clay-public-study-record/v1"


class PipelineV2Fault(RuntimeError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_loopback_http(endpoint: str) -> bool:
    return bool(re.match(r"^http://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/|$)", endpoint))


def _walk_forbidden_secret_values(value: Any, path: str = "") -> list[str]:
    """Reject secret material in persisted profile/study JSON while allowing secret names."""
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_l = str(key).lower()
            child = f"{path}.{key}" if path else str(key)
            if key_l in {"api_token", "access_token", "bearer_token", "secret_value", "password"} and item:
                errors.append(child)
            errors.extend(_walk_forbidden_secret_values(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            errors.extend(_walk_forbidden_secret_values(item, f"{path}[{idx}]"))
    return errors


class ProfilePipelineRuntimeV2(LegacyProfilePipelineRuntime):
    """Canonical v2 adapter. Application semantics remain DB/profile data."""

    def __init__(
        self,
        *,
        root: str | Path = ".",
        allow_network: bool = False,
        provider_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        max_local_output_bytes: int = 4 * 1024 * 1024,
    ):
        super().__init__(root=root, allow_network=allow_network, provider_override=provider_override)
        self.max_local_output_bytes = int(max_local_output_bytes)
        self.allowed_effects.update({"pipeline_profile_read", "inference_generate"})

    @staticmethod
    def _validate_profile(profile: dict[str, Any]) -> None:
        if profile.get("schema") != PROFILE_SCHEMA:
            raise PipelineV2Fault("BAD_PROFILE_SCHEMA")
        for field in ("profile_id", "inference", "personality", "sources", "state_metrics", "gate"):
            if field not in profile:
                raise PipelineV2Fault("PROFILE_MISSING:" + field)
        if not isinstance(profile.get("inference"), dict):
            raise PipelineV2Fault("BAD_INFERENCE_CONFIG")
        forbidden = _walk_forbidden_secret_values(profile)
        if forbidden:
            raise PipelineV2Fault("PROFILE_CONTAINS_SECRET_VALUE:" + ",".join(forbidden))

    @staticmethod
    def _validate_study_surface(surface: dict[str, Any] | None) -> None:
        if not surface:
            return
        if not isinstance(surface, dict):
            raise PipelineV2Fault("BAD_STUDY_SURFACE")
        if surface.get("enabled", True) and not isinstance(surface.get("render", {}), dict):
            raise PipelineV2Fault("BAD_STUDY_RENDER_CONFIG")
        forbidden = _walk_forbidden_secret_values(surface)
        if forbidden:
            raise PipelineV2Fault("STUDY_SURFACE_CONTAINS_SECRET_VALUE:" + ",".join(forbidden))

    def _ensure_profile_table(self, entity_db: str) -> None:
        with self._db(entity_db) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS eos_pipeline_profile(
                  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                  profile_id TEXT NOT NULL,
                  profile_json TEXT NOT NULL,
                  profile_hash TEXT NOT NULL,
                  study_surface_json TEXT NOT NULL DEFAULT '{}',
                  updated_at REAL NOT NULL)
                """
            )
            db.commit()

    def apply_profile(
        self,
        entity_db: str,
        profile: dict[str, Any],
        *,
        study_surface: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist/replace active application+inference config without resetting entity history."""
        self._validate_profile(profile)
        self._validate_study_surface(study_surface)
        self._ensure_profile_table(entity_db)
        raw = _canonical_json(profile)
        surface_raw = _canonical_json(study_surface or {})
        now = time.time()
        with self._db(entity_db) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                INSERT INTO eos_pipeline_profile(singleton,profile_id,profile_json,profile_hash,study_surface_json,updated_at)
                VALUES(1,?,?,?,?,?)
                ON CONFLICT(singleton) DO UPDATE SET
                  profile_id=excluded.profile_id,
                  profile_json=excluded.profile_json,
                  profile_hash=excluded.profile_hash,
                  study_surface_json=excluded.study_surface_json,
                  updated_at=excluded.updated_at
                """,
                (str(profile["profile_id"]), raw, hashlib.sha256(raw.encode()).hexdigest(), surface_raw, now),
            )
            db.commit()
        return {"ok": True, "profile_id": profile["profile_id"], "profile_hash": hashlib.sha256(raw.encode()).hexdigest()}

    def apply_profile_file(
        self,
        entity_db: str,
        profile_path: str | Path,
        *,
        study_surface_path: str | Path | None = None,
    ) -> dict[str, Any]:
        profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
        surface = None
        if study_surface_path is not None:
            surface = json.loads(Path(study_surface_path).read_text(encoding="utf-8"))
        return self.apply_profile(entity_db, profile, study_surface=surface)

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            entity_db = str(p["entity_db"])
            self._ensure_profile_table(entity_db)
            with self._db(entity_db) as db:
                row = db.execute("SELECT * FROM eos_pipeline_profile WHERE singleton=1").fetchone()
            if row is None:
                raise PipelineV2Fault("NO_ACTIVE_PROFILE")
            profile = json.loads(row["profile_json"])
            self._validate_profile(profile)
            if str(row["profile_id"]) != str(profile["profile_id"]):
                raise PipelineV2Fault("PROFILE_ID_MISMATCH")
            if hashlib.sha256(_canonical_json(profile).encode()).hexdigest() != str(row["profile_hash"]):
                raise PipelineV2Fault("PROFILE_HASH_MISMATCH")
            surface = json.loads(row["study_surface_json"] or "{}")
            self._validate_study_surface(surface)
            profile = dict(profile)
            profile["public_study_surface"] = surface
            return {"ok": True, "profile": profile}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if kind == "pipeline_profile_read":
            started = time.time()
            result = self._pipeline_profile_read(payload)
            self.effect_trace.append({
                "kind": kind,
                "ok": bool(result.get("ok")),
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": hashlib.sha256(_canonical_json(payload).encode()).hexdigest(),
            })
            return result
        if kind == "inference_generate":
            started = time.time()
            result = self._inference_generate(payload)
            self.effect_trace.append({
                "kind": kind,
                "ok": bool(result.get("ok")),
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": hashlib.sha256(_canonical_json(payload).encode()).hexdigest(),
            })
            return result
        return super().effect(kind, payload)

    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        pointer = str(pointer or "")
        if pointer.startswith("/"):
            current = value
            for raw in pointer.split("/")[1:]:
                part = raw.replace("~1", "/").replace("~0", "~")
                current = current[int(part)] if isinstance(current, list) else current[part]
            return current
        current = value
        for part in pointer.split(".") if pointer else []:
            current = current[int(part)] if isinstance(current, list) else current[part]
        return current

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        inference = dict(p["inference"])
        kind = str(inference.get("kind", ""))
        if self.provider_override is not None:
            self._active_secrets = []
            request = dict(p)
            request["provider"] = inference
            return {
                "ok": True,
                "payload": self.provider_override(request),
                "provider_kind": kind or "override",
                "model": inference.get("model"),
            }
        if kind == "local_exec":
            return self._local_exec(inference, p)
        if kind in {"openai_style_chat_json", "api", "json_api"}:
            return self._api_inference(inference, p)
        return {"ok": False, "error_kind": "UNKNOWN_INFERENCE_KIND", "error": kind}

    def _api_inference(self, inference: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        if not self.allow_network:
            return {"ok": False, "error_kind": "NETWORK_DISABLED", "error": "network disabled"}
        endpoint = str(inference.get("endpoint", ""))
        if not endpoint:
            return {"ok": False, "error_kind": "NO_ENDPOINT", "error": "missing endpoint"}
        loopback = _is_loopback_http(endpoint)
        if endpoint.startswith("http://") and not loopback:
            return {"ok": False, "error_kind": "PLAINTEXT_NON_LOOPBACK_FORBIDDEN", "error": endpoint}

        keys = self._keys(list(inference.get("secret_names", [])), p.get("secret_file"))
        if not keys and not loopback:
            return {"ok": False, "error_kind": "NO_PROVIDER_SECRET", "error": "no provider secret"}
        candidates: list[str | None] = keys or [None]
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
        encoded = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for key in candidates:
            self._active_secrets = [key] if key else []
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if key:
                headers[str(inference.get("auth_header", "Authorization"))] = str(inference.get("auth_prefix", "Bearer ")) + key
            req = urllib.request.Request(endpoint, data=encoded, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=float(inference.get("timeout_seconds", 60))) as response:
                    obj = json.loads(response.read().decode("utf-8"))
                content = self._pointer(obj, str(inference.get("response_pointer", "/choices/0/message/content")))
                payload = json.loads(content) if inference.get("response_content", "json_string") == "json_string" else content
                return {"ok": True, "payload": payload, "provider_kind": kind_or(inference, "api"), "model": inference.get("model")}
            except Exception as exc:
                last = exc
        return {"ok": False, "error_kind": type(last).__name__ if last else "PROVIDER_FAILED", "error": str(last) if last else "provider failed"}

    def _local_exec(self, inference: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        model_path = Path(str(inference.get("local_model_path", ""))).expanduser()
        if not model_path.is_file():
            return {"ok": False, "error_kind": "LOCAL_MODEL_MISSING", "error": str(model_path)}
        argv_cfg = inference.get("local_argv_json", inference.get("local_argv"))
        if isinstance(argv_cfg, str):
            try:
                argv_cfg = json.loads(argv_cfg)
            except Exception as exc:
                return {"ok": False, "error_kind": "BAD_LOCAL_ARGV_JSON", "error": str(exc)}
        if not isinstance(argv_cfg, list) or not argv_cfg or not all(isinstance(x, str) for x in argv_cfg):
            return {"ok": False, "error_kind": "BAD_LOCAL_ARGV", "error": "argv must be a non-empty string array"}

        prompt_template = str(inference.get("local_prompt_template", "{system}\n\n{user}"))
        prompt_text = prompt_template.replace("{system}", str(p["system"])).replace("{user}", str(p["user"]))
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.root, prefix="clay-prompt-", suffix=".txt") as handle:
                handle.write(prompt_text)
                temp_name = handle.name
            replacements = {
                "{{MODEL_PATH}}": str(model_path.resolve()),
                "{{PROMPT_FILE}}": str(Path(temp_name).resolve()),
                "{{MAX_TOKENS}}": str(inference.get("max_tokens", 2000)),
                "{{TEMPERATURE}}": str(inference.get("temperature", 0.7)),
            }
            argv: list[str] = []
            for item in argv_cfg:
                rendered = item
                for token, value in replacements.items():
                    rendered = rendered.replace(token, value)
                argv.append(rendered)
            completed = subprocess.run(
                argv,
                cwd=self.root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=float(inference.get("timeout_seconds", 120)),
                shell=False,
                check=False,
            )
            if completed.returncode != 0:
                return {
                    "ok": False,
                    "error_kind": "LOCAL_EXEC_FAILED",
                    "error": completed.stderr[:4096].decode("utf-8", "replace"),
                    "returncode": completed.returncode,
                }
            if len(completed.stdout) > self.max_local_output_bytes:
                return {"ok": False, "error_kind": "LOCAL_OUTPUT_TOO_LARGE", "error": str(len(completed.stdout))}
            text = completed.stdout.decode("utf-8", "strict").strip()
            payload = json.loads(text)
            self._active_secrets = []
            return {"ok": True, "payload": payload, "provider_kind": "local_exec", "model": inference.get("model") or model_path.name}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            if temp_name:
                try:
                    Path(temp_name).unlink()
                except OSError:
                    pass

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        base = super()._pipeline_init(p)
        if not base.get("ok"):
            return base
        try:
            entity_db = str(p["entity_db"])
            self._ensure_profile_table(entity_db)
            with self._db(entity_db) as db:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS eos_pipeline_study_records(
                      output_id TEXT PRIMARY KEY,
                      ts REAL NOT NULL,
                      generation INTEGER NOT NULL,
                      profile_id TEXT NOT NULL,
                      study_json TEXT NOT NULL,
                      rendered_state_box TEXT NOT NULL,
                      profile_hash TEXT NOT NULL,
                      system_prompt_hash TEXT NOT NULL,
                      style_framework_hash TEXT NOT NULL,
                      inference_kind TEXT NOT NULL,
                      model TEXT);
                    CREATE TABLE IF NOT EXISTS eos_pipeline_publications(
                      output_id TEXT PRIMARY KEY,
                      ts REAL NOT NULL,
                      generation INTEGER NOT NULL,
                      profile_id TEXT NOT NULL,
                      public_text TEXT NOT NULL,
                      state_box_text TEXT NOT NULL);
                    """
                )
                db.commit()
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        base = super()._pipeline_state_read(p)
        if not base.get("ok"):
            return base
        try:
            with self._db(str(p["entity_db"])) as db:
                row = db.execute("SELECT study_json,inference_kind,model FROM eos_pipeline_study_records ORDER BY generation DESC LIMIT 1").fetchone()
            base["previous_study"] = json.loads(row["study_json"]) if row else None
            base["previous_inference_kind"] = row["inference_kind"] if row else None
            base["previous_model"] = row["model"] if row else None
            return base
        except sqlite3.OperationalError:
            base["previous_study"] = None
            base["previous_inference_kind"] = None
            base["previous_model"] = None
            return base

    def _pipeline_gate(self, p: dict[str, Any]) -> dict[str, Any]:
        base = super()._pipeline_gate(p)
        if not base.get("ok"):
            return base
        try:
            profile = p["profile"]
            surface = profile.get("public_study_surface") or {}
            if not surface.get("enabled"):
                return base
            contract = profile["personality"]["output_contract"]
            field = contract.get("longitudinal_self_report_field")
            if not field:
                raise PipelineV2Fault("STUDY_SELF_REPORT_FIELD_MISSING")
            report = base["payload"].get(field)
            if not isinstance(report, dict):
                raise PipelineV2Fault("STUDY_SELF_REPORT_MISSING")
            allowed = set(surface.get("self_report_fields", []))
            declared = set(profile.get("longitudinal_study", {}).get("self_report_dimensions", []))
            accepted = allowed | declared | {"qualia_result", "qualia_confidence"}
            for name, value in report.items():
                if accepted and name not in accepted:
                    raise PipelineV2Fault("UNKNOWN_SELF_REPORT_FIELD:" + str(name))
                if name == "qualia_result":
                    if value not in {"REPORTED", "FAILED", "UNKNOWN"}:
                        raise PipelineV2Fault("BAD_QUALIA_RESULT")
                elif value != "UNKNOWN":
                    number = float(value)
                    if not 0.0 <= number <= 1.0:
                        raise PipelineV2Fault("SELF_REPORT_OUT_OF_RANGE:" + str(name))
            return base
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    @staticmethod
    def _sensor_health(profile: dict[str, Any], compiled: dict[str, Any]) -> str:
        sensors = compiled.get("canonical", {}).get("sources_health", {})
        required = [str(s.get("kind")) for s in profile.get("sources", []) if s.get("required_for_quiet")]
        if not required:
            return "UNKNOWN"
        values = [bool(sensors.get(name, {}).get("ok")) for name in required]
        if all(values):
            return "VERIFIED"
        if any(values):
            return "DEGRADED"
        return "ERROR"

    @staticmethod
    def _quiet_status(compiled: dict[str, Any], sensor_health: str) -> str:
        if sensor_health != "VERIFIED":
            return "UNKNOWN"
        if int(compiled.get("source_count", 0)) == 0:
            return "VERIFIED_QUIET"
        return "NOT_QUIET"

    def _study_record(
        self,
        profile: dict[str, Any],
        previous: dict[str, Any],
        compiled: dict[str, Any],
        generated: dict[str, Any],
        payload: dict[str, Any],
        generation: int,
        now: float,
    ) -> tuple[dict[str, Any] | None, str]:
        surface = profile.get("public_study_surface") or {}
        if not surface.get("enabled"):
            return None, ""
        contract = profile["personality"]["output_contract"]
        report_field = contract.get("longitudinal_self_report_field")
        model_report = payload.get(report_field, {}) if report_field else {}
        metrics = compiled.get("personality_state", {})
        sensor_health = self._sensor_health(profile, compiled)
        quiet_status = self._quiet_status(compiled, sensor_health)

        system: dict[str, Any] = {
            "generation": generation,
            "timestamp": now,
            "inference_backend": generated.get("provider_kind") or profile.get("inference", {}).get("kind"),
            "model_label": generated.get("model") or profile.get("inference", {}).get("model"),
            "source_count": int(compiled.get("source_count", 0)),
            "sensor_health": sensor_health,
            "quiet_status": quiet_status,
        }
        previous_study = previous.get("previous_study") or {}
        previous_system = previous_study.get("system_state", {}) if isinstance(previous_study, dict) else {}
        deltas: dict[str, float] = {}
        fixed = set(system)
        for field in surface.get("canonical_fields", []):
            if field in fixed:
                continue
            metric = metrics.get(field)
            if metric is None:
                system[field] = {"status": "UNKNOWN"}
                continue
            status = str(metric.get("status", "UNKNOWN"))
            entry: dict[str, Any] = {"status": status}
            if status == "VERIFIED":
                entry["value"] = float(metric.get("value", 0.0))
                old = previous_system.get(field)
                if isinstance(old, dict) and old.get("status") == "VERIFIED" and isinstance(old.get("value"), (int, float)):
                    deltas[field] = entry["value"] - float(old["value"])
                    entry["delta"] = deltas[field]
            system[field] = entry

        public_self: dict[str, Any] = {}
        for field in surface.get("self_report_fields", []):
            public_self[field] = model_report.get(field, "UNKNOWN")

        evaluation: list[str] = ["SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"]
        if sensor_health != "VERIFIED":
            evaluation.append("sensor_uncertainty=" + sensor_health)
        for field in sorted(deltas):
            evaluation.append(f"delta:{field}={deltas[field]:+.6f}")
        current_kind = str(system.get("inference_backend") or "")
        current_model = str(system.get("model_label") or "")
        if previous.get("previous_inference_kind") and previous.get("previous_inference_kind") != current_kind:
            evaluation.append("confound=inference_backend_changed")
        if previous.get("previous_model") and previous.get("previous_model") != current_model:
            evaluation.append("confound=model_changed")
        max_lines = int(surface.get("render", {}).get("max_evaluation_lines", 5))
        evaluation = evaluation[:max(1, max_lines)]

        record = {
            "schema": STUDY_SCHEMA,
            "profile_id": profile["profile_id"],
            "system_state": system,
            "model_self_report": public_self,
            "evaluation": evaluation,
            "deltas": deltas,
            "epistemic_law": surface.get("epistemic_law", "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"),
        }
        return record, self._render_state_box(surface, record)

    @staticmethod
    def _format_state_value(value: Any) -> str:
        if isinstance(value, dict):
            status = str(value.get("status", "UNKNOWN"))
            if status != "VERIFIED" or "value" not in value:
                return status
            suffix = ""
            if "delta" in value:
                suffix = f"  delta {float(value['delta']):+.3f}"
            return f"VERIFIED {float(value['value']):.3f}{suffix}"
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value)

    def _render_state_box(self, surface: dict[str, Any], record: dict[str, Any]) -> str:
        render = surface.get("render", {})
        title = str(render.get("title", "STATE"))
        fence = str(render.get("fence", "text"))
        sections = list(render.get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]))
        while len(sections) < 3:
            sections.append("EVALUATION")
        lines = [f"```{fence}", f"{title} — generation {record['system_state']['generation']}", sections[0]]
        for field in surface.get("canonical_fields", []):
            if field in record["system_state"]:
                lines.append(f"{field:<24}= {self._format_state_value(record['system_state'][field])}")
        lines.extend(["", sections[1]])
        for field in surface.get("self_report_fields", []):
            lines.append(f"{field:<24}= {self._format_state_value(record['model_self_report'].get(field, 'UNKNOWN'))}")
        lines.extend(["", sections[2]])
        lines.extend("- " + str(item) for item in record["evaluation"])
        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def _render_public_prose(payload: dict[str, Any], contract: dict[str, Any]) -> str:
        parts = [str(payload.get(contract["title_field"], "")).strip(), str(payload.get(contract["intro_field"], "")).strip()]
        for section in payload.get(contract["sections_field"], []):
            parts.append(str(section.get(contract["section_text_field"], "")).strip())
        return "\n\n".join(part for part in parts if part)

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
        study, state_box = self._study_record(profile, previous, compiled, generated, payload, generation, now)
        public_prose = self._render_public_prose(payload, contract)
        public_text = public_prose + (("\n\n" + state_box) if state_box else "")
        profile_for_hash = dict(profile)
        profile_for_hash.pop("public_study_surface", None)
        profile_hash = _sha(profile_for_hash)
        system_prompt_hash = hashlib.sha256(str(profile.get("personality", {}).get("system_prompt", "")).encode()).hexdigest()
        style_framework_hash = _sha(profile.get("personality", {}).get("style_framework", {}))

        db = self._db(entity_db)
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("UPDATE eos_pipeline_state SET updated_at=? WHERE singleton=1 AND generation=?", (now, previous["generation"]))
            if row.rowcount != 1:
                raise PipelineV2Fault("STALE_GENERATION")
            for item in collected["consume"]:
                db.execute(
                    "INSERT INTO eos_pipeline_consumed(source_kind,source_id,output_id,consumed_at) VALUES(?,?,?,?)",
                    (item["kind"], item["id"], output_id, now),
                )
            db.execute(
                "INSERT INTO eos_pipeline_outputs VALUES(?,?,?,?,?,?,?,?,?)",
                (output_id, now, generation, profile["profile_id"], json.dumps(payload, ensure_ascii=False), generated.get("provider_kind", ""), generated.get("model"), compiled["packet_hash"], compiled["canonical_state_hash"]),
            )
            db.execute(
                "INSERT INTO eos_pipeline_packets VALUES(?,?,?,?,?,?,?)",
                (compiled["packet_hash"], output_id, now, generation, profile["profile_id"], compiled["source_count"], compiled["canonical_state_hash"]),
            )
            db.execute(
                "INSERT INTO eos_pipeline_publications VALUES(?,?,?,?,?,?)",
                (output_id, now, generation, profile["profile_id"], public_text, state_box),
            )
            if study is not None:
                db.execute(
                    "INSERT INTO eos_pipeline_study_records VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (output_id, now, generation, profile["profile_id"], json.dumps(study, ensure_ascii=False), state_box, profile_hash, system_prompt_hash, style_framework_hash, generated.get("provider_kind", ""), generated.get("model")),
                )
            row = db.execute(
                "UPDATE eos_pipeline_state SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,cursors_json=?,updated_at=? WHERE singleton=1 AND generation=?",
                (generation, json.dumps(continuity, ensure_ascii=False), json.dumps(compiled["canonical"], ensure_ascii=False), compiled["canonical_state_hash"], json.dumps(collected["next_cursors"]), now, previous["generation"]),
            )
            if row.rowcount != 1:
                raise PipelineV2Fault("STALE_GENERATION_FINAL")
            db.commit()
            return {"ok": True, "output_id": output_id, "generation": generation, "study_recorded": study is not None, "state_box_appended": bool(state_box)}
        except Exception as exc:
            db.rollback()
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            db.close()


def kind_or(config: dict[str, Any], fallback: str) -> str:
    return str(config.get("kind") or fallback)


def execute_source(
    source: str,
    entry: str,
    args: list[Any],
    runtime: ProfilePipelineRuntimeV2 | None = None,
):
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntimeV2()
    return clay.execute(program, entry, args, rt)


__all__ = [
    "VERSION",
    "PROFILE_SCHEMA",
    "STUDY_SCHEMA",
    "PipelineV2Fault",
    "ProfilePipelineRuntimeV2",
    "execute_source",
]
