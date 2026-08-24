#!/usr/bin/env python3
"""Stable entrypoint for run_research_distillery.py.

Provides small, auditable overrides for question admission, efficient free-model
selection and fail-soft reviewer behavior. The preferred panel remains exactly
1 NVIDIA + 2 Mistral-family reviewers. When current FREE_ONLY routes cannot
supply two Mistral-family models, two independent zero-priced OpenRouter models
may form a clearly marked PROVISIONAL fallback panel so research does not stall.
Provisional packets remain candidate research and can be re-reviewed later.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sqlite3
import statistics
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


def _size_hint(model_id: str) -> float | None:
    low=model_id.lower()
    # MoE active-parameter marker A4B is more relevant for cheap semantic readers.
    m=re.search(r"a(\d+(?:\.\d+)?)b",low)
    if m:
        return float(m.group(1))
    vals=[]
    for x in re.findall(r"(?:^|[-_/])(\d+(?:\.\d+)?)b(?:[-_/.:]|$)",low):
        try: vals.append(float(x))
        except ValueError: pass
    return min(vals) if vals else None


def select_small_models(catalog: list[dict]) -> list[str]:
    ranked=[]
    for card in catalog:
        mid=str(card.get("id") or "")
        low=mid.lower()
        if not mid or not d.price_zero(card):
            continue
        if any(x in low for x in ("image","audio","embed","rerank","guard","moderation")):
            continue
        size=_size_hint(mid)
        # Exact/active 4B first, then smallest known models. Unknown-size free models
        # are retained only after known small models.
        if size is not None:
            distance=abs(size-4.0)
            rank=(0 if distance < 0.6 else 1, distance, size, mid)
        else:
            rank=(2,999.0,999.0,mid)
        ranked.append((rank,mid))
    ranked.sort(key=lambda x:x[0])
    out=[]
    for _,m in ranked:
        if m not in out: out.append(m)
    return out[:8]


def select_reviewers(catalog: list[dict]) -> list[tuple[str,str,str]]:
    preferred=d.select_reviewers(catalog)
    mistral=sum(1 for lane,provider,model in preferred if "mistral" in lane.lower() or "mistral" in model.lower())
    if mistral >= 2:
        return preferred[:3]
    nvidia=next((x for x in preferred if x[0]=="nvidia_reviewer"),None)
    out=[nvidia] if nvidia else []
    small=select_small_models(catalog)
    used={x[2] for x in out}
    for model in small:
        if model in used: continue
        out.append((f"fallback_reviewer_{len(out)}","openrouter",model)); used.add(model)
        if len(out)>=3: break
    return out


_ORIGINAL_REVIEW=d.review_candidate


def review_candidate(con: sqlite3.Connection, cid: str, reviewers: list[tuple[str,str,str]]):
    accepted,agg=_ORIGINAL_REVIEW(con,cid,reviewers)
    if accepted:
        agg["panel_class"]="PREFERRED_NVIDIA_PLUS_MISTRAL"
        return True,agg
    # If the preferred Mistral lanes are unavailable, the original reviewer has
    # already inserted any successful votes. Re-evaluate only when three distinct
    # lanes actually voted; do not fabricate missing reviewers.
    rows=con.execute("SELECT lane,provider,model,intrinsic_consistency,grf_compatibility,project_fit,novelty,hard_contradiction FROM review_votes WHERE candidate_id=?",(cid,)).fetchall()
    latest={}
    for r in rows: latest[str(r[0])]=r
    votes=list(latest.values())
    if len(votes)<3:
        agg["panel_class"]="UNDERFILLED"
        return False,agg
    has_nvidia=any(str(r[0])=="nvidia_reviewer" for r in votes)
    actual_mistral=sum(1 for r in votes if "mistral" in str(r[0]).lower() or "mistral" in str(r[2]).lower())
    if not has_nvidia:
        agg["panel_class"]="UNDERFILLED_NO_NVIDIA"
        return False,agg
    def med(idx:int)->float:
        return float(statistics.median(float(r[idx] or 0.0) for r in votes))
    provisional={
        "votes":len(votes),"intrinsic":med(3),"grf":med(4),"fit":med(5),"novelty":med(6),
        "hard":any(bool(r[7]) for r in votes),"lanes":[str(r[0]) for r in votes],
        "panel_class":"PREFERRED_NVIDIA_PLUS_MISTRAL" if actual_mistral>=2 else "PROVISIONAL_NON_MISTRAL_FALLBACK",
    }
    if actual_mistral>=2:
        ok=(not provisional["hard"] and provisional["intrinsic"]>=0.72 and provisional["grf"]>=0.65 and provisional["fit"]>=0.55 and provisional["novelty"]>=0.45)
    else:
        # Stricter thresholds for provisional fallback because it lacks the requested
        # Mistral-family diversity. It remains candidate research, never canonical truth.
        ok=(not provisional["hard"] and provisional["intrinsic"]>=0.80 and provisional["grf"]>=0.75 and provisional["fit"]>=0.65 and provisional["novelty"]>=0.55)
    if ok:
        con.execute("UPDATE candidates SET status=? WHERE id=?",("ACCEPTED" if actual_mistral>=2 else "PROVISIONAL_ACCEPTED",cid)); con.commit()
        return True,provisional
    return False,provisional


d.add_question = add_question
d.select_small_models = select_small_models
d.select_reviewers = select_reviewers
d.review_candidate = review_candidate

if __name__ == "__main__":
    raise SystemExit(d.main())
