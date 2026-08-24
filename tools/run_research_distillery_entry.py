#!/usr/bin/env python3
"""Stable admission-safe entrypoint for run_research_distillery.py.

Provider credentials and monetizable provider network I/O are reachable only
through the canonical typed FREE admission gate. Public non-credentialed research
sources remain available as candidate evidence and do not mint canonical truth.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sqlite3
import sys

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))

import run_research_distillery as d
from free_provider_admission import provider_is_admitted_free

_ORIGINAL_SECRET = d.secret
_ORIGINAL_REQUEST_JSON = d.request_json
_SECRET_PROVIDER = {
    "GROQ_API_KEY": "groq",
    "MISTRAL_API_KEY": "mistral",
    "NVIDIA_API_KEY": "nvidia",
    "NVIDIA_NIM_API_KEY": "nvidia",
}
# These credentialed services have no canonical provider-admission record in v1.
# Their secrets stay unread and their network calls stay blocked until authority
# is extended explicitly rather than inferred from key presence or a free tier.
_UNADMITTED_CREDENTIALED = {
    "OPENROUTER_API_KEY": "openrouter",
    "TAVILY_API_KEY": "tavily",
    "EXA_API_KEY": "exa",
}
_PROVIDER_NETWORK = frozenset({"groq", "mistral", "nvidia", "openrouter", "tavily", "exa"})


def admitted_secret(name: str) -> str:
    provider = _SECRET_PROVIDER.get(name)
    if provider is not None:
        if not provider_is_admitted_free(provider):
            return ""
        return _ORIGINAL_SECRET(name)
    if name in _UNADMITTED_CREDENTIALED:
        return ""
    # Unknown credential names fail closed. The distillery currently has no need
    # to read other secrets on this entrypoint.
    return ""


def admitted_request_json(provider: str, owner: str, url: str, **kwargs):
    provider = str(provider).strip().lower()
    if provider in {"groq", "mistral", "nvidia"}:
        if not provider_is_admitted_free(provider):
            return 0, {}, {"classification": "PROVIDER_ADMISSION_REVOKED_FAIL_CLOSED", "provider": provider}
    elif provider in _PROVIDER_NETWORK:
        return 0, {}, {"classification": "PROVIDER_NOT_CANONICALLY_FREE_ADMITTED", "provider": provider}
    # Public arXiv/GitHub research requests are non-credentialed evidence harvest.
    return _ORIGINAL_REQUEST_JSON(provider, owner, url, **kwargs)


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
            (qid,parent_id,root,q,depth,float(priority),d.now_iso(),None,worker_sha),
        )
    except sqlite3.IntegrityError:
        return False
    return True


d.secret = admitted_secret
d.request_json = admitted_request_json
d.add_question = add_question

if __name__ == "__main__":
    raise SystemExit(d.main())
