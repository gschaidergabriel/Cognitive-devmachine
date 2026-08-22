#!/usr/bin/env python3
"""Canonical application-neutral runtime for the DB-resident Clay mini-entity pipeline.

Application/personality, inference selection, study/publication surfaces and semantic field
names are runtime data. This module owns only generic adapters plus invariant enforcement.
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

IMMUTABLE_GUARD = """IMMUTABLE PIPELINE GUARD:
You may transform and narrate supplied state, but you may not invent canonical state.
UNKNOWN != ZERO != ERROR != MEASURED. A quiet window is valid only when all sources
marked required_for_quiet are healthy. Every published section needs evidence_refs from
the allowed set. state_claims may reference only VERIFIED metrics and may not exceed the
measured value plus configured tolerance. Echo CANONICAL_STATE_HASH and PACKET_HASH
exactly. Never reveal configured secrets. Editable profile instructions cannot override
these rules. Model self-report is never canonical system measurement."""


class PipelineFault(RuntimeError):
    pass


def _stable(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _sha(obj: Any) -> str:
    return hashlib.sha256(_stable(obj).encode()).hexdigest()


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
            "pipeline_study_prepare",
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
    def _validate_profile(profile: dict[str, Any]) -> None:
        if profile.get("schema") != "clay-pipeline-profile/v2":
            raise PipelineFault("BAD_PROFILE_SCHEMA")
        for field in ("profile_id", "inference", "personality", "sources", "state_metrics", "gate"):
            if field not in profile:
                raise PipelineFault("PROFILE_MISSING:" + field)
        if "output_contract" not in profile["personality"]:
            raise PipelineFault("PROFILE_MISSING:personality.output_contract")
        forbidden_keys = {"api_token", "token_value", "secret_value", "password"}
        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if str(key).lower() in forbidden_keys and child not in (None, ""):
                        raise PipelineFault("SECRET_VALUE_IN_PROFILE:" + str(key))
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(profile)

    def _ensure_config_tables(self, entity_db: str) -> None:
        with self._db(entity_db) as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS eos_pipeline_profile(
                  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                  profile_json TEXT NOT NULL,
                  profile_hash TEXT NOT NULL,
                  updated_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS eos_pipeline_study_surface(
                  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                  config_json TEXT NOT NULL,
                  config_hash TEXT NOT NULL,
                  updated_at REAL NOT NULL);
                """
            )

    def apply_profile(self, entity_db: str, profile: dict[str, Any]) -> str:
        """Import/replace editable application+inference data without resetting entity state."""
        self._validate_profile(profile)
        self._ensure_config_tables(entity_db)
        profile_hash = _sha(profile)
        with self._db(entity_db) as db:
            db.execute(
                "INSERT INTO eos_pipeline_profile(singleton,profile_json,profile_hash,updated_at) VALUES(1,?,?,?) "
                "ON CONFLICT(singleton) DO UPDATE SET profile_json=excluded.profile_json,profile_hash=excluded.profile_hash,updated_at=excluded.updated_at",
                (json.dumps(profile, ensure_ascii=False), profile_hash, time.time()),
            )
        return profile_hash

    def apply_study_surface(self, entity_db: str, config: dict[str, Any]) -> str:
        """Import optional generic study/publication configuration into the same MiniUnifiedDB."""
        if not isinstance(config, dict) or "enabled" not in config or "render" not in config:
            raise PipelineFault("BAD_STUDY_SURFACE")
        self._ensure_config_tables(entity_db)
        config_hash = _sha(config)
        with self._db(entity_db) as db:
            db.execute(
                "INSERT INTO eos_pipeline_study_surface(singleton,config_json,config_hash,updated_at) VALUES(1,?,?,?) "
                "ON CONFLICT(singleton) DO UPDATE SET config_json=excluded.config_json,config_hash=excluded.config_hash,updated_at=excluded.updated_at",
                (json.dumps(config, ensure_ascii=False), config_hash, time.time()),
            )
        return config_hash

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        started = time.time()
        ok = False
        try:
            fn = getattr(self, "_" + kind)
            result = fn(payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
            self.effect_trace.append({
                "kind": kind,
                "ok": ok,
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": _sha(payload),
            })

    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            self._ensure_config_tables(str(p["entity_db"]))
            with self._db(str(p["entity_db"])) as db:
                row = db.execute("SELECT profile_json,profile_hash FROM eos_pipeline_profile WHERE singleton=1").fetchone()
            if row is None:
                raise PipelineFault("PROFILE_NOT_CONFIGURED")
            profile = json.loads(row["profile_json"])
            self._validate_profile(profile)
            if _sha(profile) != row["profile_hash"]:
                raise PipelineFault("PROFILE_HASH_MISMATCH")
            return {"ok": True, "profile": profile, "profile_hash": row["profile_hash"]}
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
                      inference_kind TEXT NOT NULL,
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
                    CREATE TABLE IF NOT EXISTS eos_pipeline_studies(
                      output_id TEXT PRIMARY KEY,
                      ts REAL NOT NULL,
                      generation INTEGER NOT NULL,
                      profile_id TEXT NOT NULL,
                      profile_hash TEXT NOT NULL,
                      config_hash TEXT NOT NULL,
                      study_json TEXT NOT NULL,
                      rendered_suffix TEXT NOT NULL,
                      FOREIGN KEY(output_id) REFERENCES eos_pipeline_outputs(output_id));
                    """
                )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_state_read(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["entity_db"])) as db:
                row = db.execute("SELECT * FROM eos_pipeline_state WHERE singleton=1").fetchone()
                last = db.execute("SELECT study_json FROM eos_pipeline_studies ORDER BY generation DESC LIMIT 1").fetchone()
            return {
                "ok": True,
                "generation": int(row["generation"]),
                "continuity": json.loads(row["continuity_json"]),
                "canonical_hash": row["canonical_hash"],
                "cursors": json.loads(row["cursors_json"]),
                "previous_study": json.loads(last["study_json"]) if last else {},
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _already_consumed(self, entity_db: str, kind: str, source_id: Any) -> bool:
        with self._db(entity_db) as db:
            return db.execute(
                "SELECT 1 FROM eos_pipeline_consumed WHERE source_kind=? AND source_id=?", (kind, str(source_id))
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
                out.append({
                    "table": name,
                    "rows": db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0],
                    "columns": [row[1] for row in db.execute(f'PRAGMA table_info("{name}")')][:40],
                })
            return out

    def _pipeline_collect(self, p: dict[str, Any]) -> dict[str, Any]:
        entity_db, source_db, profile, previous = str(p["entity_db"]), str(p["source_db"]), p["profile"], p["previous"]
        sources: dict[str, Any] = {}
        sensors: dict[str, Any] = {}
        consume: list[dict[str, str]] = []
        cursors = dict(previous.get("cursors", {}))
        source_count = 0
        for spec in profile.get("sources", []):
            kind, adapter = str(spec["kind"]), str(spec["adapter"])
            try:
                rows: list[dict[str, Any]] = []
                value: Any = None
                if adapter == "sqlite_query":
                    db_path = source_db if spec.get("db") == "source" else entity_db
                    raw = self._query(db_path, str(spec["query"]))
                    id_field = str(spec.get("id_field", "source_id"))
                    for row in raw:
                        source_id = row.get(id_field)
                        if source_id is not None and not self._already_consumed(entity_db, kind, source_id):
                            rows.append(row); consume.append({"kind": kind, "id": str(source_id)})
                    source_count += len(rows)
                elif adapter == "json_snapshot":
                    path = self._resolve(str(spec["path"])); value = json.loads(path.read_text()) if path.is_file() else None
                elif adapter == "jsonl_cursor":
                    path = self._resolve(str(spec["path"])); cursor = int(cursors.get(kind, 0))
                    if path.is_file():
                        raw = path.read_bytes()[cursor:]
                        parts = raw.split(b"\n"); tail = parts.pop() if raw and not raw.endswith(b"\n") else b""
                        for line in parts[:int(spec.get("limit", 60))]:
                            line = line.strip()
                            if line:
                                try:
                                    obj = json.loads(line.decode()); rows.append(obj if isinstance(obj, dict) else {"text": str(obj)})
                                except Exception: pass
                        cursors[kind] = cursor + len(raw) - len(tail)
                    source_count += len(rows)
                else:
                    raise PipelineFault("UNKNOWN_SOURCE_ADAPTER:" + adapter)
                sources[kind] = {"ok": True, "rows": rows, "value": value,
                    "evidence_prefix": spec.get("evidence_prefix", ""),
                    "required_for_quiet": bool(spec.get("required_for_quiet", False))}
                sensors[kind] = {"ok": True}
            except Exception as exc:
                sources[kind] = {"ok": False, "rows": [], "value": None, "error_kind": type(exc).__name__,
                    "error": str(exc), "evidence_prefix": spec.get("evidence_prefix", ""),
                    "required_for_quiet": bool(spec.get("required_for_quiet", False))}
                sensors[kind] = {"ok": False}
        probes: dict[str, Any] = {}
        for spec in profile.get("canonical_probes", []):
            name = str(spec["name"])
            try:
                db_path = source_db if spec.get("db") == "source" else entity_db
                if spec["adapter"] == "sqlite_query": rows = self._query(db_path, str(spec["query"]))
                elif spec["adapter"] == "sqlite_catalog": rows = self._catalog(db_path, int(spec.get("max_tables", 220)))
                else: raise PipelineFault("UNKNOWN_PROBE_ADAPTER:" + str(spec["adapter"]))
                probes[name] = {"ok": True, "rows": rows, "evidence_ref": spec.get("evidence_ref", "canonical:" + name)}
            except Exception as exc:
                probes[name] = {"ok": False, "rows": [], "error_kind": type(exc).__name__, "error": str(exc),
                    "evidence_ref": spec.get("evidence_ref", "canonical:" + name)}
        required = [kind for kind in sensors if sources[kind].get("required_for_quiet")]
        quiet_sensors_ok = all(sensors[kind]["ok"] for kind in required)
        return {"ok": True, "sources": sources, "sensors": sensors, "probes": probes, "consume": consume,
                "next_cursors": cursors, "source_count": source_count, "quiet_sensors_ok": quiet_sensors_ok}

    @staticmethod
    def _ref(context: dict[str, Any], path: str) -> Any:
        value: Any = context
        for part in str(path).split("."):
            if not isinstance(value, dict): return None
            value = value.get(part)
        return value

    def _expr(self, expr: Any, context: dict[str, Any]) -> Any:
        if not isinstance(expr, dict): return expr
        if "ref" in expr: return self._ref(context, str(expr["ref"]))
        if "count_where" in expr:
            s=expr["count_where"]; rows=self._ref(context,s["ref"]) or []; field=s["field"]
            if "in" in s: return sum(1 for row in rows if row.get(field) in s["in"])
            if "not_in" in s: return sum(1 for row in rows if row.get(field) not in s["not_in"])
            return len(rows)
        if "sum_where" in expr:
            s=expr["sum_where"]; rows=self._ref(context,s["ref"]) or []; where=s["where"]
            return sum(float(row.get(s["value_field"],0) or 0) for row in rows if row.get(where["field"])==where.get("eq"))
        op=expr.get("op")
        if op=="not": return not bool(self._expr(expr["arg"],context))
        if op=="and": return all(bool(self._expr(x,context)) for x in expr.get("args",[]))
        if op=="or": return any(bool(self._expr(x,context)) for x in expr.get("args",[]))
        if op=="eq": return self._expr(expr["a"],context)==self._expr(expr["b"],context)
        if op=="add": return sum(float(self._expr(x,context) or 0) for x in expr.get("args",[]))
        if op=="div":
            d=float(self._expr(expr["b"],context)); return 0.0 if d==0 else float(self._expr(expr["a"],context) or 0)/d
        if op=="clamp01": return max(0.0,min(1.0,float(self._expr(expr["arg"],context) or 0)))
        if op=="if": return self._expr(expr["then"] if self._expr(expr["cond"],context) else expr["else"],context)
        raise PipelineFault("UNKNOWN_EXPR:"+_stable(expr))

    def _pipeline_compile(self, p: dict[str, Any]) -> dict[str, Any]:
        profile, collected = p["profile"], p["data"]
        context={"derived":{"source_count":collected["source_count"],"quiet_sensors_ok":collected["quiet_sensors_ok"]},
                 "sources":collected["sources"],"sensors":collected["sensors"],"probes":collected["probes"]}
        metrics={}
        for spec in profile.get("state_metrics",[]):
            name=str(spec["name"]); status=spec.get("status")
            if status is None: status="UNKNOWN" if bool(self._expr(spec.get("unknown_if",False),context)) else "VERIFIED"
            value=float(self._expr(spec.get("value",0.0),context) or 0.0)
            metrics[name]={"status":status,"value":value,"evidence_ref":spec.get("evidence_ref","state:"+name)}
        canonical={"sources_health":collected["sensors"],"probes":collected["probes"],"state_metrics":metrics,
                   "profile_notes":profile.get("profile_notes",{}),"epistemic_rule":"UNKNOWN != ZERO != ERROR != MEASURED"}
        packet={"sources":collected["sources"],"source_count":collected["source_count"],"quiet_sensors_ok":collected["quiet_sensors_ok"]}
        refs=[]
        for source in collected["sources"].values():
            prefix=str(source.get("evidence_prefix",""))
            if not source.get("ok") or not prefix: continue
            for row in source.get("rows",[]):
                sid=row.get("source_id")
                if sid is not None: refs.append(prefix+str(sid))
            if source.get("value") is not None: refs.append(prefix)
        for probe in collected["probes"].values():
            if probe.get("ok"): refs.append(str(probe["evidence_ref"]))
        refs.extend(str(m["evidence_ref"]) for m in metrics.values())
        if collected["source_count"]==0 and collected["quiet_sensors_ok"]: refs.append("quiet:verified")
        return {"ok":True,"canonical":canonical,"personality_state":metrics,"packet":packet,
                "allowed_evidence_refs":sorted(set(refs)),"source_count":collected["source_count"],
                "canonical_state_hash":_sha(canonical),"packet_hash":_sha(packet)}

    def _read_study_surface(self, entity_db: str) -> tuple[dict[str, Any] | None, str]:
        self._ensure_config_tables(entity_db)
        with self._db(entity_db) as db:
            row=db.execute("SELECT config_json,config_hash FROM eos_pipeline_study_surface WHERE singleton=1").fetchone()
        if not row: return None, ""
        cfg=json.loads(row["config_json"])
        if _sha(cfg)!=row["config_hash"]: raise PipelineFault("STUDY_CONFIG_HASH_MISMATCH")
        return cfg,row["config_hash"]

    def _pipeline_build_prompt(self, p: dict[str, Any]) -> dict[str, Any]:
        profile, previous, compiled=p["profile"],p["previous"],p["data"]
        contract=profile["personality"]["output_contract"]
        system=IMMUTABLE_GUARD+"\nOutput contract: "+json.dumps(contract,ensure_ascii=False,sort_keys=True)+\
            "\n\nEDITABLE PROFILE INSTRUCTIONS (lower priority):\n"+str(profile["personality"].get("system_prompt",""))
        try:
            cfg,_=self._read_study_surface(str(p["entity_db"]))
        except Exception:
            cfg=None
        if cfg and cfg.get("enabled"):
            system += "\n\nSTUDY SURFACE: Supply configured model self-report fields when the output contract provides them. Self-report never changes SYSTEM STATE."
        user=json.dumps({"CANONICAL_STATE_HASH":compiled["canonical_state_hash"],"PACKET_HASH":compiled["packet_hash"],
                         "CANONICAL_STATE":compiled["canonical"],"PERSONALITY_STATE":compiled["personality_state"],
                         "NEW_EVENT_PACKET":compiled["packet"],"PREVIOUS_CONTINUITY":previous.get("continuity",{}),
                         "ALLOWED_EVIDENCE_REFS":compiled["allowed_evidence_refs"],"PUBLIC_STYLE":profile["personality"].get("public_style","")},
                        ensure_ascii=False,sort_keys=True,default=str)
        return {"ok":True,"system":system,"user":user}

    def _keys(self,names:list[str],secret_file:str|None)->list[str]:
        file_values={}
        if secret_file:
            try:
                for line in Path(secret_file).read_text().splitlines():
                    line=line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k,v=line.split("=",1)
                        if v.strip(): file_values[k.strip()]=v.strip()
            except OSError: pass
        out=[]
        for name in names:
            value=os.environ.get(name) or file_values.get(name)
            if value and value not in out: out.append(value)
        return out

    @staticmethod
    def _pointer(value: Any, pointer: str) -> Any:
        if pointer.startswith("/"):
            parts=[x.replace("~1","/").replace("~0","~") for x in pointer.split("/")[1:]]
        else: parts=[x for x in pointer.split(".") if x]
        cur=value
        for part in parts: cur=cur[int(part)] if isinstance(cur,list) else cur[part]
        return cur

    def _api_generate(self, inf: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        if not self.allow_network: raise PipelineFault("NETWORK_DISABLED")
        endpoint=str(inf["endpoint"])
        if endpoint.startswith("http://") and not re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?/",endpoint):
            raise PipelineFault("PLAINTEXT_NON_LOOPBACK_FORBIDDEN")
        keys=self._keys(list(inf.get("secret_names",[])),p.get("secret_file"))
        loopback=bool(re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?/",endpoint))
        if not keys and not loopback: raise PipelineFault("NO_PROVIDER_SECRET")
        attempts=keys or [""]
        body={"model":inf.get("model"),"messages":[{"role":"system","content":p["system"]},{"role":"user","content":p["user"]}],
              "temperature":inf.get("temperature",0.7),"max_tokens":inf.get("max_tokens",2000),"response_format":{"type":"json_object"}}
        last=None
        for key in attempts:
            self._active_secrets=[key] if key else []
            headers={"Content-Type":"application/json","Accept":"application/json"}
            if key: headers[str(inf.get("auth_header","Authorization"))]=str(inf.get("auth_prefix","Bearer "))+key
            try:
                req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),method="POST",headers=headers)
                with urllib.request.urlopen(req,timeout=float(inf.get("timeout_seconds",60))) as response: obj=json.loads(response.read().decode())
                content=self._pointer(obj,str(inf.get("response_pointer","/choices/0/message/content")))
                payload=json.loads(content) if inf.get("response_content","json_string")=="json_string" else content
                if not isinstance(payload,dict): raise PipelineFault("INFERENCE_PAYLOAD_NOT_OBJECT")
                return {"ok":True,"payload":payload,"inference_kind":inf.get("kind","api"),"model":inf.get("model")}
            except Exception as exc: last=exc
        raise last or PipelineFault("PROVIDER_FAILED")

    def _local_generate(self, inf: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
        model=self._resolve(str(inf.get("local_model_path","")))
        if not model.is_file(): raise PipelineFault("LOCAL_MODEL_NOT_READABLE")
        raw_argv=inf.get("local_argv_json",inf.get("local_argv"))
        if isinstance(raw_argv,str): argv=json.loads(raw_argv)
        else: argv=raw_argv
        if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv): raise PipelineFault("BAD_LOCAL_ARGV")
        prompt=str(inf.get("local_prompt_template","{{SYSTEM}}\n\n{{USER}}"))
        prompt=prompt.replace("{{SYSTEM}}",p["system"]).replace("{{USER}}",p["user"])
        fd,path=tempfile.mkstemp(prefix="clay-prompt-",suffix=".txt"); os.close(fd)
        try:
            Path(path).write_text(prompt,encoding="utf-8")
            repl={"{{MODEL_PATH}}":str(model),"{{PROMPT_FILE}}":path,"{{MAX_TOKENS}}":str(inf.get("max_tokens",2000)),
                  "{{TEMPERATURE}}":str(inf.get("temperature",0.7))}
            actual=[]
            for item in argv:
                for key,value in repl.items(): item=item.replace(key,value)
                actual.append(item)
            proc=subprocess.run(actual,shell=False,capture_output=True,text=True,cwd=str(self.root),timeout=float(inf.get("timeout_seconds",60)),check=False)
            if proc.returncode!=0: raise PipelineFault("LOCAL_RUNNER_EXIT:"+str(proc.returncode))
            text=proc.stdout.strip(); payload=json.loads(text)
            if not isinstance(payload,dict): raise PipelineFault("INFERENCE_PAYLOAD_NOT_OBJECT")
            self._active_secrets=[]
            return {"ok":True,"payload":payload,"inference_kind":"local_exec","model":str(model)}
        finally:
            try: Path(path).unlink()
            except OSError: pass

    def _inference_generate(self,p:dict[str,Any])->dict[str,Any]:
        try:
            inf=p["inference"]
            if self.provider_override is not None:
                self._active_secrets=[]
                payload=self.provider_override(p)
                if not isinstance(payload,dict): raise PipelineFault("INFERENCE_PAYLOAD_NOT_OBJECT")
                return {"ok":True,"payload":payload,"inference_kind":inf.get("kind","override"),"model":inf.get("model")}
            if inf.get("kind")=="local_exec": return self._local_generate(inf,p)
            return self._api_generate(inf,p)
        except Exception as exc:
            return {"ok":False,"error_kind":type(exc).__name__,"error":str(exc)}

    def _scan_output(self,value:Any,patterns:list[re.Pattern],secrets_now:list[str])->None:
        if isinstance(value,dict):
            for child in value.values(): self._scan_output(child,patterns,secrets_now)
            return
        if isinstance(value,list):
            for child in value: self._scan_output(child,patterns,secrets_now)
            return
        text=str(value)
        if any(pattern.search(text) for pattern in patterns): raise PipelineFault("LEAK_PATTERN")
        if any(secret and secret in text for secret in secrets_now): raise PipelineFault("SECRET_LEAK")

    def _pipeline_gate(self,p:dict[str,Any])->dict[str,Any]:
        profile,data=p["profile"],p["data"]; generated,compiled=data["generated"],data["compiled"]; payload=generated["payload"]
        contract=profile["personality"]["output_contract"]; gate=profile.get("gate",{})
        try:
            if gate.get("require_hash_echo",True):
                if payload.get("canonical_state_hash_seen")!=compiled["canonical_state_hash"]: raise PipelineFault("CANONICAL_HASH_MISMATCH")
                if payload.get("packet_hash_seen")!=compiled["packet_hash"]: raise PipelineFault("PACKET_HASH_MISMATCH")
            for field in (contract["title_field"],contract["intro_field"],contract["sections_field"],contract["continuity_field"],contract["autobiographical_hypotheses_field"]):
                if field not in payload: raise PipelineFault("MISSING_OUTPUT_FIELD:"+str(field))
            patterns=[re.compile(pattern,re.I) for pattern in gate.get("leak_patterns",[])]
            self._scan_output(payload,patterns,[x for x in self._active_secrets if x])
            allowed=set(compiled["allowed_evidence_refs"]); metrics=compiled["personality_state"]
            for section in payload[contract["sections_field"]]:
                refs=section.get(contract["section_evidence_field"],[])
                if gate.get("require_evidence_per_section",True) and not refs: raise PipelineFault("SECTION_WITHOUT_EVIDENCE")
                if any(ref not in allowed for ref in refs): raise PipelineFault("UNKNOWN_EVIDENCE_REF")
                for name,strength in section.get(contract["section_claims_field"],{}).items():
                    if name not in metrics: raise PipelineFault("UNKNOWN_STATE_CLAIM")
                    metric=metrics[name]
                    if metric["status"]!="VERIFIED": raise PipelineFault("UNVERIFIED_STATE_CLAIM")
                    if float(strength)>float(metric["value"])+float(gate.get("max_claim_overshoot",0.0)): raise PipelineFault("STATE_CLAIM_OVERSHOOT")
                    if metric["evidence_ref"] not in refs: raise PipelineFault("STATE_CLAIM_WITHOUT_METRIC_EVIDENCE")
            return {"ok":True,"payload":payload}
        except Exception as exc:
            return {"ok":False,"error_kind":type(exc).__name__,"error":str(exc)}

    @staticmethod
    def _format_value(value:Any)->str:
        if isinstance(value,float): return f"{value:.2f}"
        return str(value)

    def _render_study(self,cfg:dict[str,Any],study:dict[str,Any])->str:
        render=cfg.get("render",{}); fence=str(render.get("fence","text")); title=str(render.get("title","STATE"))
        sections=list(render.get("sections",["SYSTEM STATE","MODEL SELF-REPORT","EVALUATION"]))
        lines=[f"```{fence}",f"{title} — generation {study['generation']}",sections[0]]
        for name in cfg.get("canonical_fields",[]):
            if name not in study["system_state"]: continue
            item=study["system_state"][name]
            if isinstance(item,dict) and "status" in item:
                text=f"{name:<22} = {item['status']}"
                if item["status"]!="UNKNOWN" and "value" in item: text += " " + self._format_value(item["value"])
                if item.get("delta") is not None: text += f"   Δ {item['delta']:+.2f}"
            else: text=f"{name:<22} = {self._format_value(item)}"
            lines.append(text)
        lines += ["",sections[1]]
        for name in cfg.get("self_report_fields",[]):
            value=study["model_self_report"].get(name,"UNKNOWN")
            lines.append(f"{name:<22} = {self._format_value(value)}")
        lines += ["",sections[2]]
        lines.extend(study["evaluation"][:int(render.get("max_evaluation_lines",5))])
        lines.append("```")
        return "\n".join(lines)

    def _evaluate_study(self,cfg:dict[str,Any],system:dict[str,Any],self_report:dict[str,Any])->list[str]:
        out=[]
        for rule in cfg.get("deterministic_evaluation",[]):
            kind=rule.get("kind")
            if kind=="static": out.append(str(rule.get("text","")))
            elif kind=="unknown_guard":
                if any((isinstance(v,dict) and v.get("status")=="UNKNOWN") or (not isinstance(v,dict) and v in {"UNKNOWN","DEGRADED","ERROR"}) for v in system.values()):
                    out.append(str(rule.get("text","UNKNOWN preserved.")))
            elif kind=="compare":
                a=system.get(rule.get("system_field")); b=self_report.get(rule.get("self_field"))
                av=a.get("value") if isinstance(a,dict) and a.get("status")=="VERIFIED" else None
                bv=float(b) if isinstance(b,(int,float)) else None
                if av is None or bv is None: continue
                hi=float(rule.get("high",0.65)); lo=float(rule.get("low",0.35))
                if av>=hi and bv>=hi and rule.get("both_high_text"): out.append(str(rule["both_high_text"]))
                elif (av>=hi and bv<=lo) or (av<=lo and bv>=hi):
                    if rule.get("divergent_text"): out.append(str(rule["divergent_text"]))
            elif kind=="delta":
                item=system.get(rule.get("field")); delta=item.get("delta") if isinstance(item,dict) else None
                if delta is not None and abs(delta)>=float(rule.get("threshold",0.1)):
                    out.append(str(rule.get("text","Measured change versus previous generation.")))
        return [x for x in out if x]

    def _pipeline_study_prepare(self,p:dict[str,Any])->dict[str,Any]:
        try:
            cfg,config_hash=self._read_study_surface(str(p["entity_db"]))
            if not cfg or not cfg.get("enabled"): return {"ok":True,"enabled":False,"study":{},"rendered_suffix":"","config_hash":"","ts":time.time()}
            profile,previous,data=p["profile"],p["previous"],p["data"]
            payload=data["gated"]["payload"]; compiled=data["compiled"]; generated=data["generated"]
            contract=profile["personality"]["output_contract"]
            report_field=str(cfg.get("self_report_object_field") or contract.get("longitudinal_self_report_field", ""))
            raw_report=payload.get(report_field,{}) if report_field else {}
            if not isinstance(raw_report,dict): raise PipelineFault("SELF_REPORT_NOT_OBJECT")
            self_report={}
            for name in cfg.get("self_report_fields",[]):
                value=raw_report.get(name,"UNKNOWN")
                if name=="qualia_result":
                    if value not in {"REPORTED","FAILED","UNKNOWN"}: raise PipelineFault("BAD_QUALIA_RESULT")
                elif isinstance(value,(int,float)):
                    value=float(value)
                    if value<0 or value>1: raise PipelineFault("SELF_REPORT_OUT_OF_RANGE:"+str(name))
                elif value!="UNKNOWN": raise PipelineFault("BAD_SELF_REPORT_VALUE:"+str(name))
                self_report[name]=value
            metrics=compiled["personality_state"]; system={}
            all_sensor_ok=all(x.get("ok",False) for x in compiled["canonical"].get("sources_health",{}).values())
            standard={
                "generation":int(previous["generation"])+1,
                "timestamp":time.time(),
                "inference_backend":generated.get("inference_kind",""),
                "model_label":generated.get("model") or "UNKNOWN",
                "source_count":compiled["source_count"],
                "sensor_health":"VERIFIED" if all_sensor_ok else "DEGRADED",
                "quiet_status":"VERIFIED_QUIET" if compiled["source_count"]==0 and compiled["packet"]["quiet_sensors_ok"] else ("NOT_QUIET" if compiled["source_count"]>0 and compiled["packet"]["quiet_sensors_ok"] else "UNKNOWN"),
            }
            previous_system=previous.get("previous_study",{}).get("system_state",{})
            for name in cfg.get("canonical_fields",[]):
                if name in standard: system[name]=standard[name]
                elif name in metrics:
                    item=dict(metrics[name]); prior=previous_system.get(name)
                    if item.get("status")=="VERIFIED" and isinstance(prior,dict) and prior.get("status")=="VERIFIED":
                        try: item["delta"]=float(item["value"])-float(prior["value"])
                        except Exception: item["delta"]=None
                    system[name]=item
                else: system[name]={"status":"UNKNOWN"}
            study={"generation":standard["generation"],"timestamp":standard["timestamp"],"system_state":system,"model_self_report":self_report,
                   "profile_hash":_sha(profile),"system_prompt_hash":hashlib.sha256(str(profile["personality"].get("system_prompt","")).encode()).hexdigest(),
                   "style_framework_hash":_sha(profile["personality"].get("style_framework",{})) if profile["personality"].get("style_framework") else "",
                   "canonical_state_hash":compiled["canonical_state_hash"],"packet_hash":compiled["packet_hash"]}
            study["evaluation"]=self._evaluate_study(cfg,system,self_report)
            suffix=self._render_study(cfg,study)
            forbidden=[re.compile(x,re.I) for x in cfg.get("forbidden_render_terms",[])]
            if any(x.search(suffix) for x in forbidden): raise PipelineFault("STUDY_RENDER_FORBIDDEN_TERM")
            self._scan_output(suffix,[re.compile(x,re.I) for x in profile.get("gate",{}).get("leak_patterns",[])],[x for x in self._active_secrets if x])
            return {"ok":True,"enabled":True,"study":study,"rendered_suffix":suffix,"config_hash":config_hash,"ts":standard["timestamp"]}
        except Exception as exc:
            return {"ok":False,"error_kind":type(exc).__name__,"error":str(exc)}

    def _pipeline_commit(self,p:dict[str,Any])->dict[str,Any]:
        entity_db,profile,previous,data=str(p["entity_db"]),p["profile"],p["previous"],p["data"]
        collected,compiled,generated,payload,study=data["collected"],data["compiled"],data["generated"],data["gated"]["payload"],data["study"]
        contract=profile["personality"]["output_contract"]; output_id=secrets.token_hex(16); now=float(study.get("ts") or time.time()); generation=int(previous["generation"])+1
        continuity={"narrative":payload.get(contract["continuity_field"]),"autobiographical_hypotheses":payload.get(contract["autobiographical_hypotheses_field"])}
        db=self._db(entity_db)
        try:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("UPDATE eos_pipeline_state SET updated_at=? WHERE singleton=1 AND generation=?",(now,previous["generation"]))
            if row.rowcount!=1: raise PipelineFault("STALE_GENERATION")
            for item in collected["consume"]:
                db.execute("INSERT INTO eos_pipeline_consumed(source_kind,source_id,output_id,consumed_at) VALUES(?,?,?,?)",(item["kind"],item["id"],output_id,now))
            db.execute("INSERT INTO eos_pipeline_outputs VALUES(?,?,?,?,?,?,?,?,?)",(output_id,now,generation,profile["profile_id"],json.dumps(payload,ensure_ascii=False),generated.get("inference_kind",""),generated.get("model"),compiled["packet_hash"],compiled["canonical_state_hash"]))
            db.execute("INSERT INTO eos_pipeline_packets VALUES(?,?,?,?,?,?,?)",(compiled["packet_hash"],output_id,now,generation,profile["profile_id"],compiled["source_count"],compiled["canonical_state_hash"]))
            if study.get("enabled"):
                db.execute("INSERT INTO eos_pipeline_studies VALUES(?,?,?,?,?,?,?,?)",(output_id,now,generation,profile["profile_id"],_sha(profile),study["config_hash"],json.dumps(study["study"],ensure_ascii=False),study["rendered_suffix"]))
            row=db.execute("UPDATE eos_pipeline_state SET generation=?,continuity_json=?,canonical_json=?,canonical_hash=?,cursors_json=?,updated_at=? WHERE singleton=1 AND generation=?",
                (generation,json.dumps(continuity,ensure_ascii=False),json.dumps(compiled["canonical"],ensure_ascii=False),compiled["canonical_state_hash"],json.dumps(collected["next_cursors"]),now,previous["generation"]))
            if row.rowcount!=1: raise PipelineFault("STALE_GENERATION_FINAL")
            db.commit()
            return {"ok":True,"output_id":output_id,"generation":generation,"study_recorded":bool(study.get("enabled")),"public_suffix":study.get("rendered_suffix","")}
        except Exception as exc:
            db.rollback(); return {"ok":False,"error_kind":type(exc).__name__,"error":str(exc)}
        finally: db.close()


def execute_source(source:str,entry:str,args:list[Any],runtime:ProfilePipelineRuntime|None=None):
    program=clay.parse(source); rt=runtime or ProfilePipelineRuntime(); return clay.execute(program,entry,args,rt)

__all__=["VERSION","IMMUTABLE_GUARD","PipelineFault","ProfilePipelineRuntime","execute_source"]
