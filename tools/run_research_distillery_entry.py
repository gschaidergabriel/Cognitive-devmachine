#!/usr/bin/env python3
"""Stable entrypoint for run_research_distillery.py.

Keeps the large distillery implementation isolated while installing two small,
easily-audited fixes before main(): corrected question admission and the canonical
FREE_ONLY provider boundary before credential lookup/provider network I/O.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sqlite3
import sys

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_research_distillery as d
from free_provider_admission import ALLOWED_PROVIDERS, provider_is_admitted_free


SECRET_PROVIDER = {
    "GROQ_API_KEY": "groq",
    "GROQ_API_KEYS": "groq",
    "MISTRAL_API_KEY": "mistral",
    "MISTRAL_API_KEYS": "mistral",
    "NVIDIA_API_KEY": "nvidia",
    "NVIDIA_API_KEYS": "nvidia",
    "NVIDIA_NIM_API_KEY": "nvidia",
    "NGC_API_KEY": "nvidia",
    "OPENROUTER_API_KEY": "openrouter",
    "TAVILY_API_KEY": "tavily",
    "EXA_API_KEY": "exa",
}

_original_get_secret = d.get_secret
_original_request_json = d.request_json


def gated_get_secret(name: str, *args, **kwargs):
    provider = SECRET_PROVIDER.get(str(name).strip().upper())
    if provider is not None and not provider_is_admitted_free(provider):
        return ""
    return _original_get_secret(name, *args, **kwargs)


def gated_request_json(provider: str, *args, **kwargs):
    normalized = str(provider).strip().lower()
    if normalized in ALLOWED_PROVIDERS and not provider_is_admitted_free(normalized):
        return 0, {}, {"error": "TYPED_FREE_PROVIDER_ADMISSION_REQUIRED_BEFORE_NETWORK"}
    return _original_request_json(provider, *args, **kwargs)


# run_research_distillery.secret() resolves the module-global get_secret at call time,
# so replacing d.get_secret closes all current model/search credential lookups without
# copying the large distillery implementation.
d.get_secret = gated_get_secret
d.request_json = gated_request_json


def add_question(con: sqlite3.Connection, question: str, *, parent_id: str | None = None,
                 root_problem: str | None = None, depth: int = 0, priority: float = 1.0,
                 worker_sha: str | None = None) -> bool:
    q = re.sub(r"\s+", " ", question).strip()[:1200]
    if len(q) < 20:
        return False
    for row in con.execute("SELECT question FROM questions ORDER BY created_at DESC LIMIT 1000"):
        if q.lower() == row[0].lower() or d.jaccard(q, row[0]) >= 0.88:
            return False
    qid = "q-" + hashlib.sha256(q.encode()).hexdigest()[:16]
    root = root_problem or q
    try:
        con.execute(
            "INSERT INTO questions(id,parent_id,root_problem,question,depth,priority,status,created_at,last_touched,source_worker_sha) VALUES(?,?,?,?,?,?,'OPEN',?,?,?)",
            (qid, parent_id, root, q, depth, float(priority), d.now_iso(), None, worker_sha),
        )
    except sqlite3.IntegrityError:
        return False
    return True


d.add_question = add_question

if __name__ == "__main__":
    raise SystemExit(d.main())
