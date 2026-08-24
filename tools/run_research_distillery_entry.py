#!/usr/bin/env python3
"""Stable fail-closed entrypoint for run_research_distillery.py.

Besides the bounded question-row repair, this entrypoint installs the canonical
EntityOS/HCU FREE provider-admission boundary before the large distillery module
can retrieve any credentialed-provider secret. Public unauthenticated research
sources remain available; credentialed model/search providers are closed unless
FREE_PROVIDER_ADMISSION.json explicitly admits that provider as FREE at the
current supervisor epoch.
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

from free_provider_admission_gate import resolve as resolve_provider_admission
import run_research_distillery as d

_SECRET_PROVIDER = {
    "OPENROUTER_API_KEY": "openrouter",
    "NVIDIA_API_KEY": "nvidia",
    "NVIDIA_NIM_API_KEY": "nvidia",
    "MISTRAL_API_KEY": "mistral",
    "GROQ_API_KEY": "groq",
    "TAVILY_API_KEY": "tavily",
    "EXA_API_KEY": "exa",
}
_ORIGINAL_SECRET = d.secret


def admitted_secret(name: str) -> str:
    provider = _SECRET_PROVIDER.get(name)
    if provider is not None:
        decision = resolve_provider_admission(provider)
        if not decision.allowed:
            return ""
    return _ORIGINAL_SECRET(name)


# This assignment happens before d.main(), so chat/catalog/reviewer/search
# helpers resolve through the guarded secret function. Missing provider entries
# (including OpenRouter/Tavily/Exa at authority 8.67) are UNKNOWN and closed.
d.secret = admitted_secret


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


d.add_question = add_question

if __name__ == "__main__":
    raise SystemExit(d.main())
