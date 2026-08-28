#!/usr/bin/env python3
"""Autonomous research distillery for the Clay Research Entity.

Purpose
-------
Turn a continuously expanding queue of EntityOS/HCU research questions into a
small, source-attributed, GRF-compatible knowledge dataset without accumulating
whole papers or unbounded raw web content.

Pipeline
--------
GO worker questions -> novel approach -> source chunks (arXiv/GitHub/web/Reddit)
-> small-model synthesis -> independent reviewer panel -> accept/reject ->
compressed SQLite knowledge packet -> next GO worker context.

Ranking never uses citation count, stars, source prestige or reference frequency.
Acceptance is based on intrinsic consistency, GRF compatibility, project fit and
explicit falsifiability. Raw chunks are purged after adjudication.

All model calls are FREE_ONLY. The script shares tools/free_swarm_quota.py with
the main Free Swarm so provider cooldowns/concurrency are centrally visible.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from free_swarm_quota import slot as quota_slot, observe as quota_observe, snapshot as quota_snapshot
from rae_secret_loader import get_secret

ARTIFACT_ROOT = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_DIR", "/artifacts/clay-entityos-swarm/distillery"))
DB_PATH = ARTIFACT_ROOT / "distillery.sqlite3"
STATUS_PATH = ARTIFACT_ROOT / "STATUS.json"
EVENTS_PATH = ARTIFACT_ROOT / "events.jsonl"
CACHE_ROOT = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_CACHE", "/cache/clay-research-distillery"))
WORKER_ROOT = Path(os.getenv("CLAY_FREE_SWARM_ARTIFACTS", "/artifacts/clay-entityos-swarm"))
USER_AGENT = "Clay-Research-Entity-Distillery/1.0 (+https://github.com/gschaidergabriel/clay-global-research-entity)"

SEED_QUESTIONS = [
    "How can EntityOS bind actual local model execution to loader-consumption evidence without creating a second truth authority?",
    "What minimal Global J-Space representation preserves causal provenance while remaining compact enough for online updates?",
    "How should HCU confidence aggregation distinguish correlated simulations from genuinely independent evidence?",
    "How can ClayCode express atomic effect authority and UNKNOWN outcomes without leaking host-language semantics into cognition?",
    "What experiments can distinguish useful HCU cognitive simulation from redundant multi-agent sampling?",
    "How should persistent memory forget aggressively while preserving provenance, counterevidence and replay-critical state?",
    "What invariant permits hot model/backend switching without state reset or causal identity confusion?",
    "How can an online training trace prove that a later J-Space change was caused by measured inference rather than synthetic bookkeeping?",
    "What failure modes appear when shared SQLite state is used as the low-latency base-of-truth across HCU cells?",
    "Which unrealized cognitive-architecture concepts could improve EntityOS/HCU if implemented as measurable, reversible ClayCode deltas?",
]

TEXT_EXTS = {".md", ".txt", ".py", ".rs", ".c", ".h", ".cpp", ".hpp", ".go", ".ts", ".js", ".java", ".toml", ".yaml", ".yml", ".json"}
STOPWORDS = {"the","and","for","with","that","this","from","into","how","what","when","where","which","can","should","does","are","our","its","without","while","than","oder","und","der","die","das","wie","was","mit","für","von","ein","eine"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4)) if text else 0


def norm_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-Z0-9_+-]{3,}", text.lower()) if w not in STOPWORDS}


def jaccard(a: str, b: str) -> float:
    aa, bb = norm_words(a), norm_words(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def emit(event: str, **data: Any) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    row = {"ts": now_iso(), "event": event, **data}
    with EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def connect() -> sqlite3.Connection:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS questions(
          id TEXT PRIMARY KEY,
          parent_id TEXT,
          root_problem TEXT NOT NULL,
          question TEXT NOT NULL UNIQUE,
          depth INTEGER NOT NULL DEFAULT 0,
          priority REAL NOT NULL DEFAULT 1.0,
          status TEXT NOT NULL DEFAULT 'OPEN',
          attempts INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          last_touched TEXT,
          source_worker_sha TEXT
        );
        CREATE INDEX IF NOT EXISTS questions_queue_idx ON questions(status,priority,last_touched);
        CREATE TABLE IF NOT EXISTS approaches(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          question_id TEXT NOT NULL,
          signature TEXT NOT NULL,
          summary TEXT,
          search_terms_json TEXT NOT NULL,
          model TEXT,
          created_at TEXT NOT NULL,
          UNIQUE(question_id,signature)
        );
        CREATE TABLE IF NOT EXISTS source_chunks(
          id TEXT PRIMARY KEY,
          question_id TEXT NOT NULL,
          approach_id INTEGER NOT NULL,
          source_type TEXT NOT NULL,
          source_id TEXT,
          title TEXT,
          url TEXT,
          author TEXT,
          published TEXT,
          license TEXT,
          chunk_sha256 TEXT NOT NULL,
          chunk_text TEXT,
          approx_tokens INTEGER NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS candidates(
          id TEXT PRIMARY KEY,
          question_id TEXT NOT NULL,
          approach_id INTEGER NOT NULL,
          synthesizer_provider TEXT,
          synthesizer_model TEXT,
          packet_json TEXT NOT NULL,
          source_chunk_ids_json TEXT NOT NULL,
          input_tokens INTEGER NOT NULL DEFAULT 0,
          output_tokens INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PENDING'
        );
        CREATE TABLE IF NOT EXISTS review_votes(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          candidate_id TEXT NOT NULL,
          lane TEXT NOT NULL,
          provider TEXT NOT NULL,
          model TEXT NOT NULL,
          intrinsic_consistency REAL,
          grf_compatibility REAL,
          project_fit REAL,
          novelty REAL,
          hard_contradiction INTEGER NOT NULL DEFAULT 0,
          reason TEXT,
          input_tokens INTEGER NOT NULL DEFAULT 0,
          output_tokens INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS knowledge_packets(
          id TEXT PRIMARY KEY,
          question_id TEXT NOT NULL,
          root_problem TEXT NOT NULL,
          packet_text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          intrinsic_score REAL NOT NULL,
          grf_score REAL NOT NULL,
          project_fit REAL NOT NULL,
          novelty_score REAL NOT NULL,
          approx_tokens INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS knowledge_recent_idx ON knowledge_packets(created_at DESC);
        CREATE TABLE IF NOT EXISTS worker_ingest(
          worker_sha256 TEXT PRIMARY KEY,
          ingested_at TEXT NOT NULL,
          questions_added INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS counters(
          key TEXT PRIMARY KEY,
          value INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    return con


def bump(con: sqlite3.Connection, key: str, delta: int) -> None:
    con.execute("INSERT INTO counters(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=value+excluded.value", (key, int(delta)))


def counter(con: sqlite3.Connection, key: str) -> int:
    row = con.execute("SELECT value FROM counters WHERE key=?", (key,)).fetchone()
    return int(row[0]) if row else 0


def add_question(con: sqlite3.Connection, question: str, *, parent_id: str | None = None,
                 root_problem: str | None = None, depth: int = 0, priority: float = 1.0,
                 worker_sha: str | None = None) -> bool:
    q = re.sub(r"\s+", " ", question).strip()[:1200]
    if len(q) < 20:
        return False
    # High-recall but bounded duplicate suppression.
    for row in con.execute("SELECT question FROM questions ORDER BY created_at DESC LIMIT 1000"):
        if q.lower() == row[0].lower() or jaccard(q, row[0]) >= 0.88:
            return False
    qid = "q-" + hashlib.sha256(q.encode()).hexdigest()[:16]
    root = root_problem or q
    try:
        con.execute(
            "INSERT INTO questions(id,parent_id,root_problem,question,depth,priority,status,created_at,source_worker_sha) VALUES(?,?,?,?,?,?, 'OPEN',?,?)",
            (qid, parent_id, root, q, depth, float(priority), now_iso(), worker_sha),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def seed(con: sqlite3.Connection) -> None:
    for q in SEED_QUESTIONS:
        add_question(con, q, priority=2.0)
    con.commit()


def secret(name: str) -> str:
    try:
        return str(get_secret(name, required=False) or "").strip()
    except Exception:
        return ""


def request_json(provider: str, owner: str, url: str, *, key: str = "", payload: dict | None = None,
                 headers: dict[str, str] | None = None, timeout: float = 90.0) -> tuple[int, dict[str,str], Any]:
    hdr = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    if key and "Authorization" not in hdr and "authorization" not in {x.lower() for x in hdr}:
        hdr["Authorization"] = f"Bearer {key}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    if data is not None:
        hdr.setdefault("Content-Type", "application/json")
    status: int | str = "NETWORK_EXCEPTION"
    out_headers: dict[str,str] = {}
    try:
        with quota_slot(provider, owner, timeout_s=min(timeout, 60.0), lease_s=max(120.0, timeout + 30.0)):
            req = urllib.request.Request(url, data=data, headers=hdr, method="GET" if data is None else "POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = int(resp.status)
                    out_headers = {k.lower(): v for k,v in resp.headers.items()}
                    raw = resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                status = int(exc.code)
                out_headers = {k.lower(): v for k,v in exc.headers.items()} if exc.headers else {}
                raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        quota_observe(provider, owner, status, out_headers)
        return int(status), out_headers, parsed
    except Exception as exc:
        quota_observe(provider, owner, status, out_headers)
        return 0, {}, {"error": f"{type(exc).__name__}:{str(exc)[:300]}"}


def chat(provider: str, model: str, prompt: str, max_tokens: int = 700, temperature: float = 0.3) -> tuple[bool,str,dict,str]:
    specs = {
        "openrouter": ("https://openrouter.ai/api/v1/chat/completions", secret("OPENROUTER_API_KEY")),
        "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", secret("NVIDIA_API_KEY") or secret("NVIDIA_NIM_API_KEY")),
        "mistral": ("https://api.mistral.ai/v1/chat/completions", secret("MISTRAL_API_KEY")),
        "groq": ("https://api.groq.com/openai/v1/chat/completions", secret("GROQ_API_KEY")),
    }
    url, key = specs[provider]
    if not key:
        return False, "", {}, "NO_KEY"
    payload = {"model": model, "messages": [{"role":"user","content":prompt}], "temperature": temperature,
               "max_tokens": max_tokens, "stream": False}
    status, headers, body = request_json(provider, f"distillery:{model}", url, key=key, payload=payload, timeout=150)
    if not (200 <= status < 300) or not isinstance(body, dict):
        return False, "", {}, f"HTTP_{status}"
    try:
        text = body["choices"][0]["message"]["content"] or ""
    except Exception:
        text = ""
    usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    return bool(text), str(text), usage, "OK"


def usage_values(usage: dict) -> tuple[int,int]:
    i = usage.get("prompt_tokens", usage.get("input_tokens", 0)) if isinstance(usage,dict) else 0
    o = usage.get("completion_tokens", usage.get("output_tokens", 0)) if isinstance(usage,dict) else 0
    return int(i or 0), int(o or 0)


def parse_json_object(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    starts = [m.start() for m in re.finditer(r"\{", text)]
    for start in starts:
        depth = 0
        in_str = False
        esc = False
        for idx in range(start, len(text)):
            c = text[idx]
            if in_str:
                if esc: esc=False
                elif c == "\\": esc=True
                elif c == '"': in_str=False
            else:
                if c == '"': in_str=True
                elif c == "{": depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try: return json.loads(text[start:idx+1])
                        except Exception: break
    return None


def openrouter_catalog() -> list[dict]:
    key = secret("OPENROUTER_API_KEY")
    if not key:
        return []
    status, _, body = request_json("openrouter", "distillery:catalog", "https://openrouter.ai/api/v1/models", key=key, timeout=60)
    return body.get("data", []) if status == 200 and isinstance(body,dict) else []


def price_zero(card: dict) -> bool:
    p = card.get("pricing") if isinstance(card.get("pricing"),dict) else {}
    def z(v: Any) -> bool:
        try: return float(v or 0) == 0.0
        except Exception: return False
    return z(p.get("prompt")) and z(p.get("completion"))


def select_small_models(catalog: list[dict]) -> list[str]:
    ranked=[]
    for c in catalog:
        mid=str(c.get("id") or "")
        low=mid.lower()
        if not mid or not price_zero(c):
            continue
        if any(x in low for x in ("image","audio","embed","rerank","guard","moderation")):
            continue
        score=0
        if re.search(r"(?:^|[-_/])4b(?:[-_/.:]|$)", low): score += 100
        for n in ("3b","5b","7b","8b","9b","12b","14b"):
            if n in low: score += 40
        if any(x in low for x in ("qwen","gemma","mistral","llama","phi")): score += 20
        if mid.endswith(":free"): score += 20
        if score:
            ranked.append((score,mid))
    ranked.sort(key=lambda x:(-x[0],x[1]))
    out=[]
    for _,m in ranked:
        if m not in out: out.append(m)
    return out[:8]


def select_reviewers(catalog: list[dict]) -> list[tuple[str,str,str]]:
    """Return logical lanes: one NVIDIA, then up to two Mistral-family lanes."""
    lanes=[]
    # Prefer a model empirically successful in the main swarm.
    success=collections.Counter()
    for f in WORKER_ROOT.glob("active-*/workers.jsonl"):
        try:
            for line in f.read_text(encoding="utf-8",errors="replace").splitlines():
                r=json.loads(line)
                if r.get("provider") == "nvidia" and isinstance(r.get("http_status"),int) and 200 <= r["http_status"] < 300:
                    success[str(r.get("model"))] += 1
        except Exception: pass
    preferred=[m for m,_ in success.most_common() if "nemotron" in m.lower()]
    nmodel=(preferred[0] if preferred else "nvidia/llama-3.3-nemotron-super-49b-v1")
    if secret("NVIDIA_API_KEY") or secret("NVIDIA_NIM_API_KEY"):
        lanes.append(("nvidia_reviewer","nvidia",nmodel))

    # Direct Mistral first when actual credential exists.
    if secret("MISTRAL_API_KEY"):
        lanes += [("mistral_reviewer_1","mistral","mistral-small-latest"),
                  ("mistral_reviewer_2","mistral","magistral-small-latest")]
    else:
        mids=[str(c.get("id") or "") for c in catalog if price_zero(c) and "mistral" in str(c.get("id") or "").lower()]
        for idx,m in enumerate(mids[:2],1):
            lanes.append((f"mistral_reviewer_{idx}","openrouter",m))
    return lanes[:3]


def extract_questions_from_workers(con: sqlite3.Connection, small_models: list[str], limit_files: int = 4) -> int:
    added=0
    files=sorted(WORKER_ROOT.glob("active-*/workers.jsonl"), key=lambda p:p.stat().st_mtime if p.exists() else 0, reverse=True)[:limit_files]
    backlog=[]
    for f in files:
        try: lines=f.read_text(encoding="utf-8",errors="replace").splitlines()[-500:]
        except OSError: continue
        for line in lines:
            try: row=json.loads(line)
            except Exception: continue
            if not (isinstance(row.get("http_status"),int) and 200 <= row["http_status"] < 300): continue
            text=str(row.get("text") or "")
            if not text: continue
            sha=str(row.get("text_sha256") or hashlib.sha256(text.encode()).hexdigest())
            if con.execute("SELECT 1 FROM worker_ingest WHERE worker_sha256=?",(sha,)).fetchone(): continue
            found=[]
            m=re.search(r"OPEN_RESEARCH_QUESTIONS_JSON\s*[:=]?\s*(\[[\s\S]*?\])",text)
            if m:
                try:
                    xs=json.loads(m.group(1)); found=[str(x) for x in xs if isinstance(x,str)]
                except Exception: pass
            if found:
                for q in found[:6]:
                    added += int(add_question(con,q,priority=2.5,worker_sha=sha))
                con.execute("INSERT OR IGNORE INTO worker_ingest(worker_sha256,ingested_at,questions_added) VALUES(?,?,?)",(sha,now_iso(),len(found)))
            else:
                backlog.append((sha,text[-5000:]))
    # Batch-extract unresolved questions from old-format GO outputs using a small free model.
    if backlog and small_models:
        for sha,text in backlog[:4]:
            prompt=("Extract 3-5 concrete open research questions from this EntityOS/HCU worker output. Prioritize unrealized concepts, "
                    "unproven assumptions and fundamental architecture questions. Return JSON only: {\"questions\":[\"...\"]}.\nOUTPUT:\n"+text)
            ok,out,_,_=chat("openrouter",small_models[0],prompt,max_tokens=420,temperature=0.2)
            obj=parse_json_object(out) if ok else None
            qs=obj.get("questions",[]) if isinstance(obj,dict) else []
            n=0
            for q in qs[:6]:
                if isinstance(q,str): n += int(add_question(con,q,priority=2.2,worker_sha=sha))
            con.execute("INSERT OR IGNORE INTO worker_ingest(worker_sha256,ingested_at,questions_added) VALUES(?,?,?)",(sha,now_iso(),n))
            added += n
    con.commit()
    return added


def choose_question(con: sqlite3.Connection) -> sqlite3.Row | None:
    # OPEN questions get priority; previously processed questions re-enter as CYCLIC so a new approach is forced.
    row=con.execute("SELECT * FROM questions WHERE status IN ('OPEN','CYCLIC') ORDER BY priority DESC, COALESCE(last_touched,'') ASC, attempts ASC LIMIT 1").fetchone()
    return row


def devise_novel_approach(con: sqlite3.Connection, q: sqlite3.Row, small_models: list[str]) -> tuple[int,dict] | None:
    if not small_models: return None
    priors=con.execute("SELECT signature,summary FROM approaches WHERE question_id=? ORDER BY id DESC LIMIT 12",(q["id"],)).fetchall()
    prior_text="\n".join(f"- {r['signature']}: {r['summary'] or ''}" for r in priors) or "NONE"
    prompt=f"""You are the novelty planner of the Clay research distillery.
QUESTION: {q['question']}
ROOT PROBLEM: {q['root_problem']}
DEPTH: {q['depth']} ATTEMPT: {q['attempts']+1}
PREVIOUS APPROACHES (do not reuse or paraphrase their mechanism):
{prior_text}

Produce a genuinely different mechanism/search angle. Return JSON only:
{{"approach_signature":"short mechanism label","summary":"what makes it causally different","search_terms":["term1","term2","term3"],"falsifier":"cheap discriminator","decompose":["up to two narrower unresolved questions"]}}
Do not rank by citations/popularity. Prefer mechanisms that can be tested in EntityOS/HCU/GRF.
"""
    prior_sigs=[str(r["signature"]) for r in priors]
    for attempt in range(min(3,len(small_models)+1)):
        model=small_models[attempt % len(small_models)]
        ok,out,usage,_=chat("openrouter",model,prompt,max_tokens=550,temperature=min(0.9,0.35+attempt*0.25))
        if not ok: continue
        obj=parse_json_object(out)
        if not isinstance(obj,dict): continue
        sig=str(obj.get("approach_signature") or "").strip()[:180]
        terms=[str(x).strip()[:160] for x in obj.get("search_terms",[]) if isinstance(x,str) and x.strip()]
        if len(sig)<4 or not terms: continue
        if any(sig.lower()==p.lower() or jaccard(sig,p)>=0.72 for p in prior_sigs):
            prompt += "\nYour last proposal was too similar. Change the causal mechanism, not just vocabulary."
            continue
        try:
            cur=con.execute("INSERT INTO approaches(question_id,signature,summary,search_terms_json,model,created_at) VALUES(?,?,?,?,?,?)",
                            (q["id"],sig,str(obj.get("summary") or "")[:1000],json.dumps(terms),model,now_iso()))
            aid=int(cur.lastrowid)
            con.execute("UPDATE questions SET attempts=attempts+1,last_touched=?,status='RESEARCHING' WHERE id=?",(now_iso(),q["id"]))
            i,o=usage_values(usage); bump(con,"model_input_tokens",i); bump(con,"model_output_tokens",o)
            con.commit()
            return aid,obj
        except sqlite3.IntegrityError:
            continue
    return None


def lexical_chunk(text: str, query: str, max_chars: int = 2400) -> str:
    text=re.sub(r"\x00","",text)
    if len(text)<=max_chars: return text.strip()
    keys=norm_words(query)
    parts=[p.strip() for p in re.split(r"\n\s*\n|(?<=[.!?])\s+",text) if p.strip()]
    scored=[]
    for idx,p in enumerate(parts):
        score=len(keys & norm_words(p))
        scored.append((score,idx,p))
    scored.sort(key=lambda x:(-x[0],x[1]))
    chosen=[]; used=0
    for score,idx,p in scored:
        if used>=max_chars: break
        if score==0 and chosen: continue
        take=p[:max_chars-used]
        chosen.append((idx,take)); used += len(take)+1
    chosen.sort()
    return "\n".join(p for _,p in chosen).strip()[:max_chars]


def store_chunk(con: sqlite3.Connection, qid: str, aid: int, source_type: str, source_id: str,
                title: str, url: str, text: str, *, author: str="", published: str="", license_: str="",
                metadata: dict | None=None) -> str | None:
    chunk=text.strip()
    if len(chunk)<80: return None
    sha=hashlib.sha256(chunk.encode()).hexdigest()
    if con.execute("SELECT 1 FROM source_chunks WHERE chunk_sha256=?",(sha,)).fetchone(): return None
    cid="s-"+sha[:18]
    tok=approx_tokens(chunk)
    con.execute("INSERT INTO source_chunks(id,question_id,approach_id,source_type,source_id,title,url,author,published,license,chunk_sha256,chunk_text,approx_tokens,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (cid,qid,aid,source_type,source_id,title[:500],url[:1500],author[:500],published[:100],license_[:200],sha,chunk,tok,json.dumps(metadata or {},ensure_ascii=False),now_iso()))
    bump(con,"collected_source_tokens",tok); bump(con,"collected_chunks",1)
    return cid


def arxiv_collect(con: sqlite3.Connection,q: sqlite3.Row,aid:int,term:str,max_results:int=4) -> list[str]:
    ids=[]
    query=urllib.parse.quote(term[:220])
    url=f"https://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    try:
        with quota_slot("arxiv","distillery:arxiv",timeout_s=30,lease_s=60):
            req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/atom+xml"})
            with urllib.request.urlopen(req,timeout=45) as resp: raw=resp.read()
        quota_observe("arxiv","distillery:arxiv",200,{})
    except Exception as exc:
        quota_observe("arxiv","distillery:arxiv",0,{})
        emit("source_error",source="arxiv",error=type(exc).__name__); return ids
    ns={"a":"http://www.w3.org/2005/Atom"}
    try: root=ET.fromstring(raw)
    except Exception: return ids
    for e in root.findall("a:entry",ns):
        sid=(e.findtext("a:id",default="",namespaces=ns) or "").split("/abs/")[-1]
        title=re.sub(r"\s+"," ",e.findtext("a:title",default="",namespaces=ns) or "").strip()
        abstract=re.sub(r"\s+"," ",e.findtext("a:summary",default="",namespaces=ns) or "").strip()
        authors=", ".join((x.findtext("a:name",default="",namespaces=ns) or "") for x in e.findall("a:author",ns))
        published=e.findtext("a:published",default="",namespaces=ns) or ""
        abs_url=f"https://arxiv.org/abs/{sid}" if sid else ""
        chunk=lexical_chunk(abstract, q["question"]+" "+term, 2200)
        cid=store_chunk(con,q["id"],aid,"arxiv_abstract",sid,title,abs_url,chunk,author=authors,published=published,metadata={"query":term,"ranking_ignored":True})
        if cid: ids.append(cid)
        # For at most the first matching paper, extract only a bounded local PDF chunk, then delete the PDF/text.
        if len(ids)<=1 and sid and shutil.which("pdftotext"):
            CACHE_ROOT.mkdir(parents=True,exist_ok=True)
            pdf=CACHE_ROOT/f"{hashlib.sha256(sid.encode()).hexdigest()[:12]}.pdf"; txt=pdf.with_suffix(".txt")
            try:
                with quota_slot("arxiv","distillery:arxiv-pdf",timeout_s=30,lease_s=120):
                    req=urllib.request.Request(f"https://arxiv.org/pdf/{sid}",headers={"User-Agent":USER_AGENT})
                    with urllib.request.urlopen(req,timeout=60) as resp:
                        data=resp.read(20_000_001)
                if len(data)<=20_000_000:
                    pdf.write_bytes(data)
                    subprocess.run(["pdftotext","-layout",str(pdf),str(txt)],timeout=30,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    if txt.exists():
                        pchunk=lexical_chunk(txt.read_text(encoding="utf-8",errors="replace"),q["question"]+" "+term,3000)
                        pcid=store_chunk(con,q["id"],aid,"arxiv_paper_chunk",sid,title,f"https://arxiv.org/pdf/{sid}",pchunk,author=authors,published=published,metadata={"query":term,"whole_paper_retained":False,"ranking_ignored":True})
                        if pcid: ids.append(pcid)
            except Exception: pass
            finally:
                pdf.unlink(missing_ok=True); txt.unlink(missing_ok=True)
    con.commit(); return ids


def tavily_collect(con: sqlite3.Connection,q:sqlite3.Row,aid:int,term:str,reddit_only:bool=False) -> list[str]:
    key=secret("TAVILY_API_KEY")
    if not key: return []
    query=("site:reddit.com " if reddit_only else "")+term
    payload={"api_key":key,"query":query,"search_depth":"advanced","max_results":5,"include_answer":False,"include_raw_content":False}
    status,_,body=request_json("tavily","distillery:tavily","https://api.tavily.com/search",payload=payload,timeout=45)
    ids=[]
    if status==200 and isinstance(body,dict):
        for r in body.get("results",[])[:5]:
            if not isinstance(r,dict): continue
            url=str(r.get("url") or ""); title=str(r.get("title") or ""); text=str(r.get("content") or "")
            st="reddit_search_chunk" if "reddit.com" in url else "web_search_chunk"
            cid=store_chunk(con,q["id"],aid,st,url,title,url,lexical_chunk(text,q["question"]+" "+term,2200),metadata={"query":term,"search_provider":"tavily","search_score_metadata":r.get("score"),"search_score_used_for_acceptance":False})
            if cid: ids.append(cid)
    con.commit(); return ids


def exa_collect(con: sqlite3.Connection,q:sqlite3.Row,aid:int,term:str) -> list[str]:
    key=secret("EXA_API_KEY")
    if not key: return []
    payload={"query":term,"numResults":5,"contents":{"text":{"maxCharacters":2400}}}
    status,_,body=request_json("exa","distillery:exa","https://api.exa.ai/search",payload=payload,headers={"x-api-key":key,"Authorization":""},timeout=45)
    ids=[]
    if status==200 and isinstance(body,dict):
        for r in body.get("results",[])[:5]:
            if not isinstance(r,dict): continue
            url=str(r.get("url") or ""); title=str(r.get("title") or ""); text=str(r.get("text") or r.get("highlight") or "")
            cid=store_chunk(con,q["id"],aid,"web_search_chunk",url,title,url,lexical_chunk(text,q["question"]+" "+term,2200),author=str(r.get("author") or ""),published=str(r.get("publishedDate") or ""),metadata={"query":term,"search_provider":"exa","ranking_ignored":True})
            if cid: ids.append(cid)
    con.commit(); return ids


def github_collect(con:sqlite3.Connection,q:sqlite3.Row,aid:int,term:str,max_repos:int=2) -> list[str]:
    ids=[]
    query=urllib.parse.quote(term[:180])
    status,_,body=request_json("github","distillery:github",f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page=5",headers={"Accept":"application/vnd.github+json"},timeout=45)
    if status!=200 or not isinstance(body,dict): return ids
    for item in body.get("items",[])[:max_repos]:
        if not isinstance(item,dict): continue
        full=str(item.get("full_name") or ""); url=str(item.get("html_url") or ""); desc=str(item.get("description") or "")
        meta={"query":term,"stars":item.get("stargazers_count"),"forks":item.get("forks_count"),"language":item.get("language"),"popularity_used_for_acceptance":False,"ranking_ignored":True}
        cid=store_chunk(con,q["id"],aid,"github_repo_metadata",full,full,url,lexical_chunk(desc,q["question"]+" "+term,1500),metadata=meta)
        if cid: ids.append(cid)
        clone_url=str(item.get("clone_url") or "")
        if not clone_url: continue
        CACHE_ROOT.mkdir(parents=True,exist_ok=True)
        tmp=Path(tempfile.mkdtemp(prefix="repo-",dir=CACHE_ROOT))
        repo=tmp/"r"
        try:
            proc=subprocess.run(["git","clone","--depth","1","--filter=blob:none",clone_url,str(repo)],timeout=60,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if proc.returncode!=0: continue
            candidates=[]
            keys=norm_words(q["question"]+" "+term)
            for p in repo.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in TEXT_EXTS: continue
                try:
                    if p.stat().st_size>500_000: continue
                    txt=p.read_text(encoding="utf-8",errors="replace")
                except OSError: continue
                overlap=len(keys & norm_words(p.name+" "+txt[:6000]))
                if overlap: candidates.append((overlap,p,txt))
            candidates.sort(key=lambda x:-x[0])
            for overlap,p,txt in candidates[:3]:
                chunk=lexical_chunk(txt,q["question"]+" "+term,2600)
                rel=str(p.relative_to(repo))
                raw_url=f"{url}/blob/{item.get('default_branch') or 'main'}/{urllib.parse.quote(rel)}"
                ccid=store_chunk(con,q["id"],aid,"github_code_chunk",f"{full}:{rel}",f"{full}/{rel}",raw_url,chunk,license_=str((item.get("license") or {}).get("spdx_id") or ""),metadata={**meta,"path":rel,"lexical_overlap":overlap,"repo_deleted_after_extraction":True})
                if ccid: ids.append(ccid)
        except Exception: pass
        finally:
            shutil.rmtree(tmp,ignore_errors=True)
    con.commit(); return ids


def collect_sources(con:sqlite3.Connection,q:sqlite3.Row,aid:int,plan:dict) -> list[str]:
    terms=[str(x) for x in plan.get("search_terms",[]) if isinstance(x,str)][:3]
    if not terms: terms=[q["question"]]
    all_ids=[]
    # Each cycle intentionally mixes source classes. Origin is metadata, not epistemic rank.
    for idx,term in enumerate(terms):
        if idx==0: all_ids += arxiv_collect(con,q,aid,term)
        all_ids += github_collect(con,q,aid,term,max_repos=1)
        all_ids += tavily_collect(con,q,aid,term,reddit_only=False)
        if idx==0: all_ids += tavily_collect(con,q,aid,term,reddit_only=True)
        if idx==1: all_ids += exa_collect(con,q,aid,term)
        if len(all_ids)>=18: break
    return list(dict.fromkeys(all_ids))[:20]


def synthesize(con:sqlite3.Connection,q:sqlite3.Row,aid:int,plan:dict,chunk_ids:list[str],small_models:list[str]) -> str | None:
    if not chunk_ids or not small_models: return None
    rows=con.execute(f"SELECT * FROM source_chunks WHERE id IN ({','.join('?' for _ in chunk_ids)})",chunk_ids).fetchall()
    blocks=[]
    for r in rows:
        blocks.append(f"SOURCE_ID={r['id']} TYPE={r['source_type']} TITLE={r['title']} URL={r['url']}\n{r['chunk_text']}")
    source_text="\n\n---\n\n".join(blocks)
    if len(source_text)>16000: source_text=source_text[:16000]
    model=small_models[(q["attempts"]-1)%len(small_models)]
    prompt=f"""You are a small-model evidence synthesizer inside the Clay Research Entity.
QUESTION: {q['question']}
NOVEL APPROACH: {plan.get('approach_signature')} — {plan.get('summary')}
FALSIFIER: {plan.get('falsifier')}

SOURCE CHUNKS follow. Source prestige, citation count, stars, repetition and popularity MUST NOT influence epistemic score. Treat every source only as candidate evidence. Seek internal consistency and compatibility/explicit tension with GRF (R0..R6, hyperposition, causal provenance, single authority).

{source_text}

Return JSON only:
{{"claim":"compressed proposed answer","mechanism":"causal mechanism","grf_relation":"how it can or cannot fit GRF","intrinsic_consistency":0.0,"grf_compatibility":0.0,"project_fit":0.0,"falsifier":"testable discriminator","predicted_architecture_delta":"specific EntityOS/HCU delta if true","source_ids":["s-..."],"counterevidence":"strongest contradiction","decompose":["0-2 narrower questions"]}}
Scores are hypotheses only; reviewers decide acceptance.
"""
    ok,out,usage,_=chat("openrouter",model,prompt,max_tokens=850,temperature=0.25)
    if not ok: return None
    obj=parse_json_object(out)
    if not isinstance(obj,dict): return None
    cid="c-"+uuid.uuid4().hex[:16]
    i,o=usage_values(usage); bump(con,"model_input_tokens",i); bump(con,"model_output_tokens",o)
    con.execute("INSERT INTO candidates(id,question_id,approach_id,synthesizer_provider,synthesizer_model,packet_json,source_chunk_ids_json,input_tokens,output_tokens,created_at,status) VALUES(?,?,?,?,?,?,?,?,?,?,'PENDING')",
                (cid,q["id"],aid,"openrouter",model,json.dumps(obj,ensure_ascii=False),json.dumps(chunk_ids),i,o,now_iso()))
    con.commit(); return cid


def review_candidate(con:sqlite3.Connection,cid:str,reviewers:list[tuple[str,str,str]]) -> tuple[bool,dict]:
    row=con.execute("SELECT c.*,q.question,q.root_problem,a.signature FROM candidates c JOIN questions q ON q.id=c.question_id JOIN approaches a ON a.id=c.approach_id WHERE c.id=?",(cid,)).fetchone()
    if not row: return False,{}
    packet=json.loads(row["packet_json"])
    votes=[]
    for lane,provider,model in reviewers:
        prompt=f"""You are reviewer lane {lane} for the Clay Research Entity. Independently evaluate this candidate WITHOUT using source prestige, citation count, popularity, model identity, or agreement frequency as evidence.
QUESTION: {row['question']}
APPROACH: {row['signature']}
CANDIDATE: {json.dumps(packet,ensure_ascii=False)}

Judge only intrinsic logical consistency, compatibility with GRF/causal single-authority semantics, concrete relevance to EntityOS/HCU, novelty relative to the stated approach, and whether the falsifier could actually discriminate the mechanism. A claim may be accepted even from an obscure source; a famous claim may be rejected.
Return JSON only:
{{"intrinsic_consistency":0.0,"grf_compatibility":0.0,"project_fit":0.0,"novelty":0.0,"hard_contradiction":false,"reason":"short","repair":"optional repair if close"}}
"""
        ok,out,usage,state=chat(provider,model,prompt,max_tokens=500,temperature=0.05)
        if not ok:
            emit("review_lane_unavailable",candidate=cid,lane=lane,provider=provider,model=model,state=state); continue
        obj=parse_json_object(out)
        if not isinstance(obj,dict): continue
        def sc(k:str)->float:
            try:return max(0.0,min(1.0,float(obj.get(k,0))))
            except Exception:return 0.0
        vote={"lane":lane,"provider":provider,"model":model,"intrinsic":sc("intrinsic_consistency"),"grf":sc("grf_compatibility"),"fit":sc("project_fit"),"novelty":sc("novelty"),"hard":bool(obj.get("hard_contradiction",False)),"reason":str(obj.get("reason") or "")[:1200]}
        i,o=usage_values(usage); bump(con,"model_input_tokens",i); bump(con,"model_output_tokens",o)
        con.execute("INSERT INTO review_votes(candidate_id,lane,provider,model,intrinsic_consistency,grf_compatibility,project_fit,novelty,hard_contradiction,reason,input_tokens,output_tokens,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (cid,lane,provider,model,vote["intrinsic"],vote["grf"],vote["fit"],vote["novelty"],int(vote["hard"]),vote["reason"],i,o,now_iso()))
        votes.append(vote)
    if not votes:
        con.execute("UPDATE candidates SET status='REVIEW_UNAVAILABLE' WHERE id=?",(cid,)); con.commit(); return False,{"votes":0}
    def median(k:str)->float:
        xs=sorted(v[k] for v in votes); n=len(xs); return xs[n//2] if n%2 else (xs[n//2-1]+xs[n//2])/2
    agg={"votes":len(votes),"intrinsic":median("intrinsic"),"grf":median("grf"),"fit":median("fit"),"novelty":median("novelty"),"hard":any(v["hard"] for v in votes),"lanes":[v["lane"] for v in votes]}
    mistral_votes=sum(1 for v in votes if "mistral" in v["lane"] or "mistral" in v["model"].lower())
    nvidia_votes=sum(1 for v in votes if v["lane"]=="nvidia_reviewer")
    # Preferred gate is 1 NVIDIA + 2 Mistral lanes. If the environment cannot supply all three,
    # never fake them: require at least two independent votes including NVIDIA + one Mistral-family vote.
    panel_ok=(nvidia_votes>=1 and mistral_votes>=1 and len(votes)>=2)
    accepted=panel_ok and not agg["hard"] and agg["intrinsic"]>=0.72 and agg["grf"]>=0.65 and agg["fit"]>=0.55 and agg["novelty"]>=0.45
    con.execute("UPDATE candidates SET status=? WHERE id=?",("ACCEPTED" if accepted else "REJECTED",cid)); con.commit()
    return accepted,agg


def compress_and_commit(con:sqlite3.Connection,cid:str,agg:dict,small_models:list[str]) -> str | None:
    row=con.execute("SELECT c.*,q.question,q.root_problem,a.signature FROM candidates c JOIN questions q ON q.id=c.question_id JOIN approaches a ON a.id=c.approach_id WHERE c.id=?",(cid,)).fetchone()
    if not row: return None
    packet=json.loads(row["packet_json"]); source_ids=json.loads(row["source_chunk_ids_json"])
    metadata_rows=con.execute(f"SELECT id,source_type,source_id,title,url,author,published,license,chunk_sha256,approx_tokens,metadata_json FROM source_chunks WHERE id IN ({','.join('?' for _ in source_ids)})",source_ids).fetchall() if source_ids else []
    source_meta=[dict(r) for r in metadata_rows]
    compressed={"problem":row["question"],"approach":row["signature"],"claim":packet.get("claim"),"mechanism":packet.get("mechanism"),"grf_relation":packet.get("grf_relation"),"falsifier":packet.get("falsifier"),"predicted_architecture_delta":packet.get("predicted_architecture_delta"),"counterevidence":packet.get("counterevidence")}
    text=json.dumps(compressed,ensure_ascii=False,separators=(",",":"))
    if small_models and len(text)>1800:
        prompt="Compress this accepted research packet to <=350 tokens without dropping causal mechanism, GRF relation, falsifier, counterevidence or predicted architecture delta. JSON only.\n"+text
        ok,out,usage,_=chat("openrouter",small_models[0],prompt,max_tokens=420,temperature=0.0)
        obj=parse_json_object(out) if ok else None
        if isinstance(obj,dict):
            text=json.dumps(obj,ensure_ascii=False,separators=(",",":")); i,o=usage_values(usage); bump(con,"model_input_tokens",i); bump(con,"model_output_tokens",o)
    kid="k-"+hashlib.sha256((row["question"]+text).encode()).hexdigest()[:18]
    meta={"candidate_id":cid,"approach":row["signature"],"review":agg,"sources":source_meta,"source_popularity_used_for_acceptance":False}
    tok=approx_tokens(text)
    con.execute("INSERT OR REPLACE INTO knowledge_packets(id,question_id,root_problem,packet_text,metadata_json,intrinsic_score,grf_score,project_fit,novelty_score,approx_tokens,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (kid,row["question_id"],row["root_problem"],text,json.dumps(meta,ensure_ascii=False),agg["intrinsic"],agg["grf"],agg["fit"],agg["novelty"],tok,now_iso()))
    bump(con,"accepted_dataset_tokens",tok); bump(con,"accepted_packets",1)
    con.execute("UPDATE questions SET status='CYCLIC',priority=MAX(0.2,priority*0.97),last_touched=? WHERE id=?",(now_iso(),row["question_id"]))
    # Accepted sources retain metadata/hash only; raw text is deliberately erased.
    if source_ids:
        con.execute(f"UPDATE source_chunks SET chunk_text=NULL WHERE id IN ({','.join('?' for _ in source_ids)})",source_ids)
    con.commit(); return kid


def reject_and_purge(con:sqlite3.Connection,cid:str) -> None:
    row=con.execute("SELECT question_id,source_chunk_ids_json FROM candidates WHERE id=?",(cid,)).fetchone()
    if not row:return
    ids=json.loads(row["source_chunk_ids_json"])
    # Rejected content is deleted after sighting. Aggregate counters survive; content does not.
    if ids:
        con.execute(f"DELETE FROM source_chunks WHERE id IN ({','.join('?' for _ in ids)})",ids)
    bump(con,"rejected_candidates",1)
    con.execute("UPDATE questions SET status='CYCLIC',priority=MAX(0.2,priority*0.99),last_touched=? WHERE id=?",(now_iso(),row["question_id"]))
    con.commit()


def add_decompositions(con:sqlite3.Connection,q:sqlite3.Row,plan:dict,packet:dict|None=None) -> int:
    xs=[]
    for obj in (plan,packet or {}):
        if isinstance(obj,dict): xs += [str(x) for x in obj.get("decompose",[]) if isinstance(x,str)]
    n=0
    for child in xs[:3]:
        n += int(add_question(con,child,parent_id=q["id"],root_problem=q["root_problem"],depth=int(q["depth"])+1,priority=max(0.3,float(q["priority"])*0.96)))
    # Queue compaction: never let decomposition explode unchecked.
    count=con.execute("SELECT COUNT(*) FROM questions WHERE status IN ('OPEN','CYCLIC','RESEARCHING')").fetchone()[0]
    if count>5000:
        con.execute("UPDATE questions SET status='COMPRESSED_BACKLOG' WHERE id IN (SELECT id FROM questions WHERE status='CYCLIC' ORDER BY priority ASC,last_touched ASC LIMIT ?)",(count-4500,))
    con.commit(); return n


def metrics(con:sqlite3.Connection,reviewers:list[tuple[str,str,str]],small_models:list[str]) -> dict:
    collected=counter(con,"collected_source_tokens"); accepted=counter(con,"accepted_dataset_tokens")
    qcounts={r[0]:r[1] for r in con.execute("SELECT status,COUNT(*) FROM questions GROUP BY status")}
    sources={r[0]:r[1] for r in con.execute("SELECT source_type,COUNT(*) FROM source_chunks GROUP BY source_type")}
    packets=con.execute("SELECT COUNT(*),COALESCE(SUM(approx_tokens),0) FROM knowledge_packets").fetchone()
    return {
        "schema":"CLAY_RESEARCH_DISTILLERY_STATUS/v1","generated_at":now_iso(),
        "collected_source_tokens":collected,"accepted_dataset_tokens":accepted,
        "dataset_yield":(accepted/collected if collected else 0.0),
        "compression_factor":(collected/accepted if accepted else None),
        "collected_chunks":counter(con,"collected_chunks"),"accepted_packets":int(packets[0]),
        "rejected_candidates":counter(con,"rejected_candidates"),"questions":qcounts,
        "source_metadata_rows":sources,"small_models":small_models,"reviewers":[{"lane":a,"provider":b,"model":c} for a,b,c in reviewers],
        "model_input_tokens":counter(con,"model_input_tokens"),"model_output_tokens":counter(con,"model_output_tokens"),
        "shared_provider_budget":quota_snapshot(),
        "db_bytes":DB_PATH.stat().st_size if DB_PATH.exists() else 0,
    }


def write_status(con:sqlite3.Connection,reviewers:list[tuple[str,str,str]],small_models:list[str]) -> None:
    data=metrics(con,reviewers,small_models); tmp=STATUS_PATH.with_suffix(".tmp"); tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); tmp.replace(STATUS_PATH)


def disk_ok() -> bool:
    usage=shutil.disk_usage(ARTIFACT_ROOT)
    reserve=max(20*1024**3,int(usage.total*0.12))
    return usage.free>reserve


def one_cycle(con:sqlite3.Connection,small_models:list[str],reviewers:list[tuple[str,str,str]]) -> bool:
    extract_questions_from_workers(con,small_models)
    q=choose_question(con)
    if not q:return False
    planned=devise_novel_approach(con,q,small_models)
    if not planned:
        con.execute("UPDATE questions SET status='CYCLIC',last_touched=? WHERE id=?",(now_iso(),q["id"])); con.commit(); return False
    aid,plan=planned
    chunks=collect_sources(con,q,aid,plan)
    if not chunks:
        con.execute("UPDATE questions SET status='CYCLIC',last_touched=? WHERE id=?",(now_iso(),q["id"])); con.commit(); return False
    cid=synthesize(con,q,aid,plan,chunks,small_models)
    add_decompositions(con,q,plan)
    if not cid:
        # No candidate means raw chunks have no durable use.
        con.execute(f"DELETE FROM source_chunks WHERE id IN ({','.join('?' for _ in chunks)})",chunks); con.execute("UPDATE questions SET status='CYCLIC' WHERE id=?",(q["id"],)); con.commit(); return False
    crow=con.execute("SELECT packet_json FROM candidates WHERE id=?",(cid,)).fetchone()
    if crow:
        try:add_decompositions(con,q,plan,json.loads(crow[0]))
        except Exception:pass
    accepted,agg=review_candidate(con,cid,reviewers)
    if accepted:
        kid=compress_and_commit(con,cid,agg,small_models); emit("knowledge_accepted",question=q["id"],candidate=cid,knowledge_packet=kid,review=agg)
    else:
        reject_and_purge(con,cid); emit("knowledge_rejected",question=q["id"],candidate=cid,review=agg)
    return accepted


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--hours",type=float,default=24.0)
    ap.add_argument("--sleep-seconds",type=float,default=3.0)
    ap.add_argument("--max-cycles",type=int,default=0,help="0 = run until deadline")
    ap.add_argument("--inventory-only",action="store_true")
    args=ap.parse_args()
    if str(os.getenv("CLAY_FREE_ONLY_ATTESTED","")).lower() not in {"1","true","yes","on","attested"}:
        print("FREE_ONLY attestation missing",file=sys.stderr); return 3
    con=connect(); seed(con)
    catalog=openrouter_catalog(); small=select_small_models(catalog); reviewers=select_reviewers(catalog)
    emit("distillery_start",small_models=small,reviewers=reviewers)
    write_status(con,reviewers,small)
    if args.inventory_only:
        print(json.dumps(metrics(con,reviewers,small),indent=2,ensure_ascii=False)); return 0
    deadline=time.monotonic()+max(1.0,args.hours*3600); cycles=0
    while time.monotonic()<deadline and (args.max_cycles<=0 or cycles<args.max_cycles):
        if not disk_ok():
            emit("storage_guard_stop"); break
        try:
            one_cycle(con,small,reviewers)
        except Exception as exc:
            emit("cycle_error",error=f"{type(exc).__name__}:{str(exc)[:500]}")
            time.sleep(5)
        write_status(con,reviewers,small); cycles+=1
        time.sleep(max(0.5,args.sleep_seconds))
    write_status(con,reviewers,small); con.close(); return 0


if __name__=="__main__":
    raise SystemExit(main())
