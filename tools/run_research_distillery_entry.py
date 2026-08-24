#!/usr/bin/env python3
"""Stable entrypoint for run_research_distillery.py.

Keeps the large distillery implementation isolated while providing a small,
easily-audited admission fix for question rows. The underlying module is
imported without executing its __main__ block, then the corrected function is
installed before main() runs.
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
