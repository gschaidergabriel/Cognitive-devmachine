#!/usr/bin/env python3
"""Generic audited effect runtime for structured ClayCode programs.

Domain semantics stay in the `.clay` source. This module only exposes generic data
helpers and explicit effects (SQLite, bounded files, clock/UUID, Mistral JSON).
Secrets are resolved inside the effect boundary and are never returned to ClayCode.
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

VERSION = "clay-effect-runtime/0.1"


class EffectRuntime(clay.Runtime):
    def __init__(self, *, root: str | Path = ".", allow_network: bool = False,
                 secret_file: str | None = None,
                 mistral_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None):
        super().__init__()
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.allow_network = allow_network
        self.secret_file = secret_file
        self.mistral_override = mistral_override
        self.effect_trace: list[dict[str, Any]] = []
        self.allowed_effects = {
            "clock_now", "uuid_hex", "sqlite_exec", "sqlite_query",
            "sqlite_transaction", "sqlite_catalog_snapshot", "file_read_json",
            "file_read_jsonl_from_cursor", "mistral_chat_json",
        }
        self.builtins.update({
            "map_items": lambda m: [[k, v] for k, v in m.items()],
            "pair_first": lambda p: p[0],
            "pair_second": lambda p: p[1],
            "list_first": lambda p: p[0],
            "list_contains": lambda xs, x: x in xs,
            "list_join": lambda xs, sep: str(sep).join(str(x) for x in xs),
            "sha256": lambda x: hashlib.sha256(str(x).encode("utf-8")).hexdigest(),
            "json_stringify": lambda x: json.dumps(
                x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
            ),
            "json_parse": json.loads,
            "regex_search": lambda pattern, text: bool(re.search(str(pattern), str(text), re.I)),
            "str_len": lambda x: len(str(x)),
            "str_slice": lambda x, a, b: str(x)[int(a):int(b)],
            "str_contains": lambda x, y: str(y) in str(x),
            "clamp01": lambda x: max(0.0, min(1.0, float(x))),
            "min2": min,
            "max2": max,
            "effect": self.effect,
        })

    def _resolve(self, value: str) -> Path:
        p = Path(value)
        return p.resolve() if p.is_absolute() else (self.root / p).resolve()

    def _db(self, value: str) -> sqlite3.Connection:
        p = self._resolve(value)
        p.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(p)
        conn.row_factory = sqlite3.Row
        return conn

    def _keys(self, names: list[str], explicit_file: str | None = None) -> list[str]:
        file_values: dict[str, str] = {}
        path = explicit_file or self.secret_file
        if path:
            try:
                for line in Path(path).read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if v.strip():
                            file_values[k.strip()] = v.strip()
            except OSError:
                pass
        out: list[str] = []
        seen: set[str] = set()
        for name in names:
            value = os.environ.get(name) or file_values.get(name)
            if value and value not in seen:
                seen.add(value)
                out.append(value)
        return out

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        started = time.time()
        ok = False
        try:
            if kind == "clock_now":
                result = {"ok": True, "epoch": time.time()}
            elif kind == "uuid_hex":
                result = {"ok": True, "value": secrets.token_hex(16)}
            elif kind == "sqlite_exec":
                result = self._sqlite_exec(payload)
            elif kind == "sqlite_query":
                result = self._sqlite_query(payload)
            elif kind == "sqlite_transaction":
                result = self._sqlite_transaction(payload)
            elif kind == "sqlite_catalog_snapshot":
                result = self._sqlite_catalog(payload)
            elif kind == "file_read_json":
                result = self._file_json(payload)
            elif kind == "file_read_jsonl_from_cursor":
                result = self._file_jsonl(payload)
            elif kind == "mistral_chat_json":
                result = self._mistral(payload)
            else:  # pragma: no cover
                raise clay.StructuredFault("UNREACHABLE_EFFECT")
            ok = bool(result.get("ok", True))
            return result
        finally:
            self.effect_trace.append({
                "kind": kind,
                "ok": ok,
                "ms": round((time.time() - started) * 1000, 3),
                "payload_hash": hashlib.sha256(
                    json.dumps(payload, sort_keys=True, default=str).encode()
                ).hexdigest(),
            })

    def _sqlite_exec(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["db_path"])) as db:
                cur = db.execute(str(p["sql"]), tuple(p.get("params", [])))
                db.commit()
                return {"ok": True, "rowcount": cur.rowcount}
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _sqlite_query(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["db_path"])) as db:
                rows = [dict(row) for row in db.execute(
                    str(p["sql"]), tuple(p.get("params", []))
                ).fetchall()]
                return {"ok": True, "rows": rows}
        except Exception as exc:
            return {"ok": False, "rows": [], "error_kind": type(exc).__name__, "error": str(exc)}

    def _sqlite_transaction(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            db = self._db(str(p["db_path"]))
            try:
                db.execute("BEGIN IMMEDIATE")
                counts: list[int] = []
                for op in p.get("ops", []):
                    cur = db.execute(str(op["sql"]), tuple(op.get("params", [])))
                    if "expect_rowcount" in op and cur.rowcount != int(op["expect_rowcount"]):
                        raise RuntimeError(
                            f"ROWCOUNT_MISMATCH:{cur.rowcount}!={op['expect_rowcount']}"
                        )
                    counts.append(cur.rowcount)
                db.commit()
                return {"ok": True, "rowcounts": counts}
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _sqlite_catalog(self, p: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._db(str(p["db_path"])) as db:
                names = [r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()]
                tables = []
                for name in names[:int(p.get("max_tables", 220))]:
                    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                        continue
                    try:
                        count = db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    except Exception:
                        count = None
                    columns = [r[1] for r in db.execute(
                        f'PRAGMA table_info("{name}")'
                    ).fetchall()]
                    tables.append({"table": name, "rows": count, "columns": columns[:40]})
                return {"ok": True, "tables": tables}
        except Exception as exc:
            return {"ok": False, "tables": [], "error_kind": type(exc).__name__, "error": str(exc)}

    def _file_json(self, p: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(str(p["path"]))
        try:
            if not path.is_file():
                return {"ok": True, "exists": False, "value": None}
            return {"ok": True, "exists": True, "value": json.loads(path.read_text(encoding="utf-8"))}
        except Exception as exc:
            return {"ok": False, "exists": path.exists(), "value": None,
                    "error_kind": type(exc).__name__, "error": str(exc)}

    def _file_jsonl(self, p: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(str(p["path"]))
        cursor = int(p.get("cursor", 0))
        limit = int(p.get("limit", 60))
        try:
            if not path.is_file():
                return {"ok": True, "exists": False, "lines": [], "next_cursor": cursor}
            with path.open("rb") as handle:
                handle.seek(cursor)
                raw = handle.read()
            if not raw:
                return {"ok": True, "exists": True, "lines": [], "next_cursor": cursor}
            parts = raw.split(b"\n")
            tail = parts.pop() if not raw.endswith(b"\n") else b""
            consumed = len(raw) - len(tail)
            lines = []
            for line in parts:
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line.decode("utf-8"))
                except Exception:
                    continue
                lines.append(value if isinstance(value, dict) else {"text": str(value)})
                if len(lines) >= limit:
                    break
            return {"ok": True, "exists": True, "lines": lines,
                    "next_cursor": cursor + consumed}
        except Exception as exc:
            return {"ok": False, "exists": path.exists(), "lines": [],
                    "next_cursor": cursor, "error_kind": type(exc).__name__, "error": str(exc)}

    def _mistral(self, p: dict[str, Any]) -> dict[str, Any]:
        if self.mistral_override is not None:
            return {"ok": True, "payload": self.mistral_override(p), "provider": "override"}
        if not self.allow_network:
            return {"ok": False, "error_kind": "NETWORK_DISABLED", "error": "network disabled"}
        names = list(p.get("secret_names", [
            "MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY"
        ]))
        keys = self._keys(names, p.get("secret_file"))
        if not keys:
            return {"ok": False, "error_kind": "NO_MISTRAL_KEY", "error": "no configured Mistral key"}
        body = {
            "model": p.get("model", "mistral-medium-latest"),
            "messages": [
                {"role": "system", "content": p["system"]},
                {"role": "user", "content": p["user"]},
            ],
            "temperature": float(p.get("temperature", 0.75)),
            "max_tokens": int(p.get("max_tokens", 2600)),
            "response_format": {"type": "json_object"},
        }
        encoded = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for key in keys:
            request = urllib.request.Request(
                "https://api.mistral.ai/v1/chat/completions",
                data=encoded,
                headers={
                    "Authorization": "Bearer " + key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=float(p.get("timeout", 60))) as response:
                    obj = json.loads(response.read().decode("utf-8"))
                content = obj["choices"][0]["message"]["content"]
                return {"ok": True, "payload": json.loads(content), "provider": "mistral"}
            except Exception as exc:
                last = exc
        return {"ok": False, "error_kind": type(last).__name__ if last else "MISTRAL_FAILED",
                "error": str(last) if last else "mistral failed"}


def execute_source(source: str, entry: str, args: list[Any], runtime: EffectRuntime | None = None):
    program = clay.parse(source)
    rt = runtime or EffectRuntime()
    return clay.execute(program, entry, args, rt)


__all__ = ["VERSION", "EffectRuntime", "execute_source"]
