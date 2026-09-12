#!/usr/bin/env python3
"""TITAN-MC — person-continuity retrieval for conversation mode.

MC = Memory Companion.  It is a second TITAN module next to TITAN-MX:

  TITAN-MX: global/temporal associative memory + HyperMirror
  TITAN-MC: speaker-scoped personal continuity + query retrieval

Both live in the SAME canonical UnifiedDB.  MC never creates a side DB and
never treats retrieved memory as authority.  It only selects already stored,
person-scoped evidence and emits a bounded context capsule for the model.

Primary use case: conversation mode already knows whether the current human
is Gabriel or Andreas.  Pass that selector to build_person_context(); MC then
retrieves only that person's memories so Frank can converse with long-term
continuity without leaking the other person's context.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Optional, Sequence

SCHEMA = "F2WP1207_TITAN_MC/v1"
DEFAULT_CHAR_BUDGET = 4200
DEFAULT_RELEVANT = 10
DEFAULT_STABLE = 8
DEFAULT_RECENT = 6

_DDL = """
CREATE TABLE IF NOT EXISTS f2_titan_mc_alias(
 alias TEXT PRIMARY KEY,
 person_id TEXT NOT NULL,
 source TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS f2_titan_mc_retrieval(
 retrieval_id TEXT PRIMARY KEY,
 person_id TEXT NOT NULL,
 session_id TEXT,
 query_sha256 TEXT NOT NULL,
 candidate_count INTEGER NOT NULL,
 selected_json TEXT NOT NULL,
 context_sha256 TEXT NOT NULL,
 created_at TEXT NOT NULL,
 schema TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_f2_titan_mc_retrieval_person
 ON f2_titan_mc_retrieval(person_id,created_at);
CREATE TABLE IF NOT EXISTS f2_titan_mc_context(
 context_id TEXT PRIMARY KEY,
 retrieval_id TEXT NOT NULL REFERENCES f2_titan_mc_retrieval(retrieval_id),
 person_id TEXT NOT NULL,
 clay_text TEXT NOT NULL,
 char_count INTEGER NOT NULL,
 digest TEXT NOT NULL,
 source_refs_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 schema TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_f2_titan_mc_context_person
 ON f2_titan_mc_context(person_id,created_at);
"""

_STOP = {
    "aber","alle","alles","also","auch","auf","aus","bei","bin","bis","das","dass","dein","dem","den","der","des","die","dir","du","ein","eine","einer","er","es","für","fuer","hat","ich","ihm","ihn","im","in","ist","ja","mit","mir","mich","nicht","noch","oder","sein","sie","so","und","von","was","wie","wir","zu",
    "a","an","and","are","as","at","be","by","for","from","he","her","him","his","i","in","is","it","me","my","of","on","or","she","that","the","their","they","this","to","we","with","you","your",
}


@dataclass(frozen=True)
class PersonCandidate:
    source: str
    ref: str
    kind: str
    subject: str
    value: str
    ts: float
    provenance: str
    score: float = 0.0


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canon(v: object) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_DDL)
    now = _now()
    aliases = {
        "gabriel": "gabriel",
        "gschaidergabriel": "gabriel",
        "ai-core-node": "gabriel",
        "ai-core-node-projekt-frankenstein": "gabriel",
        "andreas": "andreas",
        "andreas-maco": "andreas",
        "andreas_maco": "andreas",
    }
    for alias, person in aliases.items():
        conn.execute(
            "INSERT INTO f2_titan_mc_alias(alias,person_id,source,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(alias) DO UPDATE SET person_id=excluded.person_id,updated_at=excluded.updated_at",
            (alias, person, "builtin-host-person-map", now),
        )
    conn.commit()


def resolve_person_id(conn: sqlite3.Connection, raw: str) -> str:
    ensure_schema(conn)
    key = (raw or "").strip().lower()
    if not key:
        raise ValueError("empty person selector")
    row = conn.execute(
        "SELECT person_id FROM f2_titan_mc_alias WHERE lower(alias)=?", (key,)
    ).fetchone()
    return str(row[0]) if row else key


def _tokens(text: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-zA-ZÀ-ÿ0-9_\-]{2,}", (text or "").lower())
        if x not in _STOP
    }


def _safe_text(text: object, limit: int = 700) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    return s[:limit]


def _coerce_ts(v: object) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v or "").strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _durable_candidates(conn: sqlite3.Connection, person_id: str, limit: int = 500) -> list[PersonCandidate]:
    cols = _columns(conn, "durable_memory")
    required = {"memory_id","kind","subject","value","user_id","ts","provenance"}
    if not required.issubset(cols):
        return []
    rows = conn.execute(
        "SELECT memory_id,kind,subject,value,ts,provenance FROM durable_memory "
        "WHERE lower(COALESCE(user_id,''))=lower(?) ORDER BY ts DESC LIMIT ?",
        (person_id, limit),
    ).fetchall()
    return [
        PersonCandidate("durable_memory", str(r[0]), str(r[1] or "memory"),
                        _safe_text(r[2], 220), _safe_text(r[3]), _coerce_ts(r[4]),
                        _safe_text(r[5], 260))
        for r in rows
    ]


def _generic_scoped_candidates(conn: sqlite3.Connection, table: str, person_id: str,
                               *, limit: int = 160) -> list[PersonCandidate]:
    """Read only tables that have an explicit person/user scope column.

    This is intentionally conservative: a table without user_id/person_id is
    skipped rather than risking Gabriel/Andreas cross-contamination.
    """
    cols = _columns(conn, table)
    scope = next((c for c in ("user_id","person_id","speaker_id","owner") if c in cols), None)
    if not scope:
        return []
    text_col = next((c for c in (
        "memory_text","value","content","text","user_text","prompt","input_text",
        "summary","beschreibung","note","payload"
    ) if c in cols), None)
    if not text_col:
        return []
    id_col = next((c for c in (
        "memory_id","turn_id","id","event_id","retrieval_id","episode_id"
    ) if c in cols), None)
    if not id_col:
        return []
    ts_col = next((c for c in ("ts","created_at","erstellt_am","updated_at") if c in cols), None)
    subject_col = next((c for c in ("subject","kind","type","event_type") if c in cols), None)
    q = (
        f"SELECT {id_col},{text_col},"
        + (f"{ts_col}" if ts_col else "0") + ","
        + (f"{subject_col}" if subject_col else "''")
        + f" FROM {table} WHERE lower(COALESCE({scope},''))=lower(?)"
        + (f" ORDER BY {ts_col} DESC" if ts_col else "") + " LIMIT ?"
    )
    try:
        rows = conn.execute(q, (person_id, limit)).fetchall()
    except sqlite3.Error:
        return []
    return [
        PersonCandidate(table, str(r[0]), table, _safe_text(r[3], 180),
                        _safe_text(r[1]), _coerce_ts(r[2]), f"{table}:{r[0]}")
        for r in rows if _safe_text(r[1])
    ]


def collect_candidates(conn: sqlite3.Connection, person_id: str) -> list[PersonCandidate]:
    out = _durable_candidates(conn, person_id)
    for table in (
        "turns","memory_tabelle","retrieval_episodes_semantisch",
        "workspace_episodes","f2_person_memory","person_memory",
    ):
        out.extend(_generic_scoped_candidates(conn, table, person_id))
    # Deduplicate exact semantic repeats while retaining the newest evidence.
    seen: set[str] = set()
    unique: list[PersonCandidate] = []
    for c in sorted(out, key=lambda x: x.ts, reverse=True):
        key = _sha((c.subject + "\0" + c.value).lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    return unique


def _score(c: PersonCandidate, query_tokens: set[str], now_ts: float) -> float:
    hay = _tokens(c.subject + " " + c.value + " " + c.kind)
    overlap = len(query_tokens & hay)
    lexical = overlap / max(1.0, math.sqrt(max(1, len(query_tokens)) * max(1, len(hay))))
    age_days = max(0.0, (now_ts - c.ts) / 86400.0) if c.ts > 0 else 9999.0
    recency = 1.0 / (1.0 + age_days / 45.0)
    kind = c.kind.lower()
    stable_boost = 0.32 if any(k in kind for k in (
        "profile","identity","preference","relationship","constraint","project","memory"
    )) else 0.0
    return 2.8 * lexical + 0.55 * recency + stable_boost


def _pick(candidates: Sequence[PersonCandidate], query: str) -> tuple[list[PersonCandidate],list[PersonCandidate],list[PersonCandidate]]:
    now_ts = time.time()
    qt = _tokens(query)
    scored = [PersonCandidate(**{**c.__dict__, "score": _score(c, qt, now_ts)}) for c in candidates]
    relevant = sorted(scored, key=lambda c: (c.score, c.ts), reverse=True)[:DEFAULT_RELEVANT]
    stable = sorted(
        scored,
        key=lambda c: (
            1 if any(k in c.kind.lower() for k in ("profile","identity","preference","relationship","constraint","project","memory")) else 0,
            c.score, c.ts,
        ), reverse=True
    )[:DEFAULT_STABLE]
    recent = sorted(scored, key=lambda c: c.ts, reverse=True)[:DEFAULT_RECENT]
    return stable, recent, relevant


def _entry(c: PersonCandidate) -> str:
    label = _safe_text(c.subject or c.kind, 90).replace(";", ",")
    value = _safe_text(c.value, 420).replace(";", ",")
    return f"{label}={value}<{c.source}:{c.ref[:18]}>"


def build_person_context(conn: sqlite3.Connection, person_selector: str, query: str, *,
                         session_id: str = "", char_budget: int = DEFAULT_CHAR_BUDGET,
                         record: bool = True) -> str:
    """Build a strict speaker-scoped old-friend context capsule.

    No selector => no context.  There is deliberately no fallback to 'all users'.
    """
    ensure_schema(conn)
    person_id = resolve_person_id(conn, person_selector)
    candidates = collect_candidates(conn, person_id)
    stable, recent, relevant = _pick(candidates, query)

    # Union source refs for traceability.
    ordered: list[PersonCandidate] = []
    seen: set[tuple[str,str]] = set()
    for group in (stable, relevant, recent):
        for c in group:
            k = (c.source, c.ref)
            if k not in seen:
                seen.add(k); ordered.append(c)

    stable_s = "|".join(_entry(c) for c in stable) or "-"
    recent_s = "|".join(_entry(c) for c in recent) or "-"
    relevant_s = "|".join(_entry(c) for c in relevant if c.score > 0.05) or "-"
    text = (
        f"mc@1{{person:{person_id}!;mode:old_friend_person_scoped;"
        f"stable:[{stable_s}];relevant:[{relevant_s}];recent:[{recent_s}];"
        "inv:[person_scope_strict,memory!=authority,no_cross_person_leak,provenance_required]}}"
    )
    if len(text) > char_budget:
        # Relevance wins when the budget is tight; stable continuity remains present.
        text = (
            f"mc@1{{person:{person_id}!;mode:old_friend;"
            f"stable:[{'|'.join(_entry(c) for c in stable[:4]) or '-'}];"
            f"relevant:[{'|'.join(_entry(c) for c in relevant[:6]) or '-'}];"
            "inv:[person_scope_strict,memory!=authority,no_cross_person_leak]}}"
        )[:char_budget]

    if record:
        rid = uuid.uuid4().hex
        digest = _sha(text)
        refs = [{"source": c.source, "ref": c.ref} for c in ordered]
        selected = {
            "stable": [c.ref for c in stable],
            "recent": [c.ref for c in recent],
            "relevant": [c.ref for c in relevant],
        }
        conn.execute(
            "INSERT INTO f2_titan_mc_retrieval VALUES(?,?,?,?,?,?,?,?,?)",
            (rid, person_id, session_id or None, _sha(query or ""), len(candidates),
             _canon(selected), digest, _now(), SCHEMA),
        )
        conn.execute(
            "INSERT INTO f2_titan_mc_context VALUES(?,?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, rid, person_id, text, len(text), digest,
             _canon(refs), _now(), SCHEMA),
        )
        conn.commit()
    return text


def injection_text(conn: sqlite3.Connection, person_selector: str, query: str, *,
                   session_id: str = "", char_budget: int = DEFAULT_CHAR_BUDGET) -> str:
    text = build_person_context(
        conn, person_selector, query, session_id=session_id,
        char_budget=char_budget, record=True,
    )
    if not text:
        return ""
    return "<titan-mc-person-context>\n" + text + "\n</titan-mc-person-context>"


__all__ = [
    "SCHEMA","ensure_schema","resolve_person_id","collect_candidates",
    "build_person_context","injection_text","PersonCandidate",
]
