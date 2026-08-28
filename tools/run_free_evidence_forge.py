#!/usr/bin/env python3
"""Clay FREE Evidence Forge — third autonomous research/development swarm.

This process closes the gap between "many model tokens" and measured architecture
progress. It consumes machine-readable ARCHITECTURE_DELTA_JSON proposals from the
GO swarm, unresolved Distillery questions, and free/public research tools. It then:

1. discovers implementation evidence through OpenAlex, GitHub, Crossref,
   Semantic Scholar and Hugging Face Hub;
2. validates worker patches in disposable *local* clones of the private repo;
3. independently dissects/reproduces promising *public* GitHub repos in E2B when
   an E2B free-credit credential is available;
4. writes append-only evidence records that the dashboard can rank.

No model output becomes canonical truth. No provider may silently upgrade billing.
E2B is bounded by a cumulative sandbox-seconds budget in addition to its shared
concurrency gate. Credential values are never logged.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
FORGE_ROOT = ARTIFACT_ROOT / "forge"
DB_PATH = FORGE_ROOT / "forge.sqlite3"
STATUS_PATH = FORGE_ROOT / "STATUS.json"
EVAL_PATH = FORGE_ROOT / "architecture_delta_evaluations.jsonl"
DISCOVERY_PATH = FORGE_ROOT / "discoveries.jsonl"
DISTILLERY_DB = ARTIFACT_ROOT / "distillery/distillery.sqlite3"

import sys
sys.path.insert(0, str(ROOT / "tools"))
from free_swarm_quota import slot as quota_slot, observe as quota_observe, snapshot as quota_snapshot  # noqa: E402
from rae_secret_loader import get_secret  # noqa: E402

USER_AGENT = "ClayEvidenceForge/1.0 research entity; noncanonical candidate evidence"
SAFE_ENV = {"PATH": os.getenv("PATH", ""), "HOME": "/tmp", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
FORBIDDEN_COMMAND_FRAGMENTS = ("sudo ", "systemctl ", "shutdown", "reboot", "mkfs", "dd if=", "> /dev/", "rm -rf /", "podman ", "docker ")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def connect() -> sqlite3.Connection:
    FORGE_ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS candidates(
          candidate_hash TEXT PRIMARY KEY,
          delta_id TEXT, provider TEXT, model TEXT, role TEXT,
          worker_sha TEXT, proposal_json TEXT NOT NULL,
          ready INTEGER NOT NULL DEFAULT 0,
          state TEXT NOT NULL DEFAULT 'NEW',
          ingested_at TEXT NOT NULL, evaluated_at TEXT,
          last_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS discoveries(
          discovery_hash TEXT PRIMARY KEY,
          question_hash TEXT NOT NULL, question TEXT NOT NULL,
          provider TEXT NOT NULL, source_id TEXT, title TEXT, url TEXT,
          metadata_json TEXT NOT NULL, created_at TEXT NOT NULL,
          reproduced_state TEXT
        );
        CREATE TABLE IF NOT EXISTS counters(key TEXT PRIMARY KEY,value REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS processed_questions(question_hash TEXT PRIMARY KEY, processed_at TEXT NOT NULL);
        """
    )
    # Source identity is an additive migration because the long-lived Forge DB
    # predates repo_head_at_prompt. Never reinterpret a candidate against a
    # moving checkout when its exact producer head is already present in the
    # append-only worker receipt.
    columns = {str(row[1]) for row in con.execute("PRAGMA table_info(candidates)")}
    if "repo_head" not in columns:
        con.execute("ALTER TABLE candidates ADD COLUMN repo_head TEXT")
        con.commit()
    return con


def bump(con: sqlite3.Connection, key: str, delta: float = 1.0) -> None:
    con.execute("INSERT INTO counters(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=value+excluded.value", (key,float(delta)))


def count(con: sqlite3.Connection, key: str) -> float:
    row=con.execute("SELECT value FROM counters WHERE key=?",(key,)).fetchone()
    return float(row[0]) if row else 0.0


def balanced_json_after(text: str, marker: str) -> dict | None:
    pos=text.find(marker)
    if pos < 0:return None
    start=text.find("{",pos+len(marker))
    if start < 0:return None
    depth=0; in_str=False; esc=False
    for i in range(start,len(text)):
        c=text[i]
        if in_str:
            if esc:esc=False
            elif c=="\\":esc=True
            elif c=='"':in_str=False
            continue
        if c=='"':in_str=True
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                try:return json.loads(text[start:i+1])
                except Exception:return None
    return None


def ingest_worker_candidates(con: sqlite3.Connection, max_lines_per_file: int = 1200) -> int:
    added=0
    for path in sorted(ARTIFACT_ROOT.glob("active-*/workers.jsonl"), key=lambda p:p.stat().st_mtime if p.exists() else 0, reverse=True)[:8]:
        try: lines=path.read_text(encoding="utf-8",errors="replace").splitlines()[-max_lines_per_file:]
        except OSError:continue
        for line in lines:
            try:r=json.loads(line)
            except Exception:continue
            s=r.get("http_status")
            if not (isinstance(s,int) and 200<=s<300):continue
            text=str(r.get("text") or "")
            obj=balanced_json_after(text,"ARCHITECTURE_DELTA_JSON=")
            if not isinstance(obj,dict):continue
            worker_sha=str(r.get("text_sha256") or sha(text))
            repo_head=str(r.get("repo_head_at_prompt") or "").strip().lower()
            if not COMMIT_RE.fullmatch(repo_head):repo_head=""
            raw=json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"))
            ch=sha(worker_sha+raw)
            ready=bool(obj.get("ready_for_forge"))
            try:
                con.execute("INSERT INTO candidates(candidate_hash,delta_id,provider,model,role,worker_sha,repo_head,proposal_json,ready,state,ingested_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (ch,str(obj.get("delta_id") or ch[:16]),str(r.get("provider") or ""),str(r.get("model") or ""),str(r.get("role") or ""),worker_sha,repo_head,raw,int(ready),"NEW",now()))
                added+=1
            except sqlite3.IntegrityError:
                # Backfill old rows from their original append-only worker receipt
                # without overwriting an already bound source identity.
                if repo_head:
                    con.execute("UPDATE candidates SET repo_head=? WHERE candidate_hash=? AND (repo_head IS NULL OR repo_head='')",(repo_head,ch))
    con.commit(); bump(con,"candidates_ingested",added); con.commit(); return added


def open_questions(limit: int = 16) -> list[str]:
    out=[]
    if DISTILLERY_DB.exists():
        try:
            con=sqlite3.connect(DISTILLERY_DB,timeout=2)
            for (q,) in con.execute("SELECT question FROM questions WHERE status IN ('OPEN','CYCLIC') ORDER BY priority DESC,last_touched ASC LIMIT ?",(limit,)):
                if isinstance(q,str) and q.strip():out.append(q.strip())
            con.close()
        except Exception:pass
    if not out:
        out=[
            "How can EntityOS bind actual local model execution to loader consumption and J-Space provenance with one replay-safe causal receipt?",
            "Which existing open-source runtime patterns best support a ten-cell HCU simulation with deterministic shared-state authority?",
            "What minimal benchmark separates useful Global J-Space dynamics from prompt-only imitation?",
        ]
    return out[:limit]


def secret(name: str) -> str:
    try:return str(get_secret(name,required=False) or "").strip()
    except Exception:return ""


def http_json(provider: str, owner: str, url: str, *, headers: dict[str,str] | None=None, timeout: float=35) -> tuple[int,Any,dict[str,str]]:
    hdr={"User-Agent":USER_AGENT,"Accept":"application/json",**(headers or {})}
    try:
        with quota_slot(provider,owner,timeout_s=min(timeout,30),lease_s=max(60,timeout+15)):
            req=urllib.request.Request(url,headers=hdr)
            try:
                with urllib.request.urlopen(req,timeout=timeout) as resp:
                    h={k.lower():v for k,v in resp.headers.items()}; raw=resp.read(2_000_000)
                    status=int(resp.status)
            except urllib.error.HTTPError as exc:
                h={k.lower():v for k,v in exc.headers.items()} if exc.headers else {}; raw=exc.read(500_000); status=int(exc.code)
        quota_observe(provider,owner,status,h)
        try: body=json.loads(raw.decode("utf-8",errors="replace"))
        except Exception: body={}
        return status,body,h
    except Exception as exc:
        quota_observe(provider,owner,"NETWORK_EXCEPTION",{})
        return 0,{"error":type(exc).__name__},{}


def reconstruct_openalex_abstract(inv: Any) -> str:
    if not isinstance(inv,dict):return ""
    positions=[]
    for word,idxs in inv.items():
        if isinstance(idxs,list):
            for i in idxs:
                if isinstance(i,int):positions.append((i,str(word)))
    positions.sort()
    return " ".join(w for _,w in positions)[:2400]


async def discovery_for_question(con: sqlite3.Connection, q: str) -> list[dict]:
    qhash=sha(q)
    if con.execute("SELECT 1 FROM processed_questions WHERE question_hash=?",(qhash,)).fetchone():return []
    term=urllib.parse.quote(q[:240])
    results=[]

    async def openalex():
        key=secret("OPENALEX_API_KEY")
        suffix=("&api_key="+urllib.parse.quote(key)) if key else ""
        st,b,_=await asyncio.to_thread(http_json,"openalex",f"forge:{qhash[:8]}",f"https://api.openalex.org/works?search={term}&per_page=5{suffix}")
        out=[]
        if st==200 and isinstance(b,dict):
            for x in b.get("results",[])[:5]:
                if not isinstance(x,dict):continue
                out.append({"provider":"openalex","source_id":str(x.get("id") or ""),"title":str(x.get("title") or ""),"url":str((x.get("primary_location") or {}).get("landing_page_url") or x.get("doi") or x.get("id") or ""),"metadata":{"year":x.get("publication_year"),"type":x.get("type"),"abstract":reconstruct_openalex_abstract(x.get("abstract_inverted_index")),"citation_count_is_metadata_only":x.get("cited_by_count")}})
        return out

    async def crossref():
        st,b,_=await asyncio.to_thread(http_json,"crossref",f"forge:{qhash[:8]}",f"https://api.crossref.org/works?query.bibliographic={term}&rows=5")
        out=[]
        items=((b.get("message") or {}).get("items") or []) if isinstance(b,dict) else []
        for x in items[:5]:
            title=(x.get("title") or [""])[0] if isinstance(x,dict) else ""
            out.append({"provider":"crossref","source_id":str(x.get("DOI") or ""),"title":str(title),"url":str(x.get("URL") or ""),"metadata":{"type":x.get("type"),"publisher":x.get("publisher")}})
        return out

    async def semantic():
        fields=urllib.parse.quote("title,url,year,abstract,externalIds")
        st,b,_=await asyncio.to_thread(http_json,"semantic_scholar",f"forge:{qhash[:8]}",f"https://api.semanticscholar.org/graph/v1/paper/search?query={term}&limit=5&fields={fields}")
        out=[]
        if st==200 and isinstance(b,dict):
            for x in b.get("data",[])[:5]:
                out.append({"provider":"semantic_scholar","source_id":str(x.get("paperId") or ""),"title":str(x.get("title") or ""),"url":str(x.get("url") or ""),"metadata":{"year":x.get("year"),"abstract":str(x.get("abstract") or "")[:2400],"externalIds":x.get("externalIds")}})
        return out

    async def github():
        st,b,_=await asyncio.to_thread(http_json,"github",f"forge:{qhash[:8]}",f"https://api.github.com/search/repositories?q={term}&sort=updated&order=desc&per_page=5",headers={"Accept":"application/vnd.github+json"})
        out=[]
        if st==200 and isinstance(b,dict):
            for x in b.get("items",[])[:5]:
                out.append({"provider":"github","source_id":str(x.get("full_name") or ""),"title":str(x.get("full_name") or ""),"url":str(x.get("html_url") or ""),"metadata":{"clone_url":x.get("clone_url"),"description":x.get("description"),"language":x.get("language"),"stars_metadata_only":x.get("stargazers_count"),"default_branch":x.get("default_branch")}})
        return out

    async def hf():
        headers={}
        token=secret("HF_TOKEN")
        if token:headers["Authorization"]="Bearer "+token
        st,b,_=await asyncio.to_thread(http_json,"huggingface_hub",f"forge:{qhash[:8]}",f"https://huggingface.co/api/models?search={term}&limit=5&full=false",headers=headers)
        out=[]
        if st==200 and isinstance(b,list):
            for x in b[:5]:
                out.append({"provider":"huggingface_hub","source_id":str(x.get("id") or ""),"title":str(x.get("id") or ""),"url":"https://huggingface.co/"+str(x.get("id") or ""),"metadata":{"pipeline_tag":x.get("pipeline_tag"),"tags":x.get("tags",[])[:30],"downloads_metadata_only":x.get("downloads")}})
        return out

    groups=await asyncio.gather(openalex(),crossref(),semantic(),github(),hf(),return_exceptions=True)
    for g in groups:
        if isinstance(g,list):results.extend(g)
    for r in results:
        raw=json.dumps(r,sort_keys=True,ensure_ascii=False); dh=sha(qhash+raw)
        try:
            con.execute("INSERT INTO discoveries(discovery_hash,question_hash,question,provider,source_id,title,url,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (dh,qhash,q,r["provider"],r.get("source_id"),r.get("title"),r.get("url"),json.dumps(r.get("metadata") or {},ensure_ascii=False),now()))
            append_jsonl(DISCOVERY_PATH,{"question":q,**r,"created_at":now(),"ranking_rule":"source prestige/citations/stars not epistemic score"})
        except sqlite3.IntegrityError:pass
    con.execute("INSERT OR REPLACE INTO processed_questions(question_hash,processed_at) VALUES(?,?)",(qhash,now())); bump(con,"discovery_queries",1); bump(con,"discovery_hits",len(results)); con.commit()
    return results


def safe_command(cmd: str) -> bool:
    low=cmd.lower()
    return bool(cmd.strip()) and len(cmd)<2000 and not any(x in low for x in FORBIDDEN_COMMAND_FRAGMENTS)


def run_cmd(cwd: Path, cmd: str, timeout: int=120) -> dict:
    started=time.monotonic()
    try:
        p=subprocess.run(["bash","-lc",cmd],cwd=cwd,env={**os.environ,**SAFE_ENV},text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        return {"rc":p.returncode,"elapsed_s":time.monotonic()-started,"stdout":p.stdout[-4000:],"stderr":p.stderr[-4000:]}
    except subprocess.TimeoutExpired as e:
        return {"rc":124,"elapsed_s":time.monotonic()-started,"stdout":str(e.stdout or "")[-2000:],"stderr":"TIMEOUT"}
    except Exception as e:
        return {"rc":125,"elapsed_s":time.monotonic()-started,"stderr":f"{type(e).__name__}:{e}"}


def patch_paths_safe(patch: str, targets: list[str]) -> bool:
    if len(patch.encode("utf-8"))>250_000:return False
    for t in targets:
        p=Path(t)
        if p.is_absolute() or ".." in p.parts or str(p).startswith(".git"):return False
    for line in patch.splitlines():
        if line.startswith(("+++ ","--- ")):
            x=line[4:].split("\t",1)[0]
            if x=="/dev/null":continue
            x=re.sub(r"^[ab]/","",x)
            p=Path(x)
            if p.is_absolute() or ".." in p.parts or str(p).startswith(".git"):return False
    return True


def _git_text(cwd: Path, *args: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        p=subprocess.run(["git",*args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        return p.returncode,p.stdout.strip(),p.stderr.strip()
    except Exception as exc:
        return 125,"",f"{type(exc).__name__}:{exc}"


def _checkout_exact_source(dest: Path, source_head: str) -> tuple[bool, str]:
    rc,_,err=_git_text(dest,"cat-file","-e",source_head+"^{commit}")
    if rc!=0:return False,"SOURCE_COMMIT_NOT_PRESENT:"+err[-500:]
    rc,out,err=_git_text(dest,"checkout","--quiet","--detach",source_head)
    if rc!=0:return False,"SOURCE_CHECKOUT_FAILED:"+err[-500:]
    rc,got,err=_git_text(dest,"rev-parse","HEAD")
    if rc!=0 or got!=source_head:return False,"SOURCE_CHECKOUT_IDENTITY_MISMATCH:"+(got or err)[-500:]
    return True,""


def _target_blob_identities(repo: Path, source_head: str, targets: list[str]) -> dict[str,str]:
    out={}
    for target in targets:
        rc,blob,_=_git_text(repo,"rev-parse",f"{source_head}:{target}")
        out[target]=blob if rc==0 and re.fullmatch(r"[0-9a-f]{40,64}",blob or "") else "NEW_OR_MISSING_AT_SOURCE"
    return out


def validate_candidate(con: sqlite3.Connection, row: sqlite3.Row) -> dict:
    obj=json.loads(row["proposal_json"]); patch=str(obj.get("patch_unified_diff") or "")
    targets=[str(x) for x in obj.get("target_files",[]) if isinstance(x,str)]
    tests=[str(x) for x in obj.get("test_commands",[]) if isinstance(x,str) and safe_command(str(x))][:4]
    negatives=[str(x) for x in obj.get("negative_test_commands",[]) if isinstance(x,str) and safe_command(str(x))][:3]
    bench=str(obj.get("benchmark_command") or "")
    if bench and not safe_command(bench):bench=""
    source_head=str(row["repo_head"] or "").strip().lower() if "repo_head" in row.keys() else ""
    current_head=_git_text(ROOT,"rev-parse","HEAD")[1]
    base_record={
        "schema":"CLAY_FORGE_DELTA_EVALUATION/v1","delta_id":row["delta_id"],"source_class":"free_swarm",
        "provider":row["provider"],"model":row["model"],"role":row["role"],"worker_sha":row["worker_sha"],
        "source_repo_head":source_head or None,"evaluation_repo_head":current_head or None,
        "source_scope":"EXACT_WORKER_PROMPT_HEAD","evaluated_at":now(),
    }
    if not COMMIT_RE.fullmatch(source_head):
        return {**base_record,"status":"source_identity_unbound","reason":"valid repo_head_at_prompt required before patch validation"}
    if not patch or not targets or not tests or not patch_paths_safe(patch,targets):
        return {**base_record,"status":"needs_implementation","reason":"missing/safety-invalid patch, targets, or tests"}
    tmp=Path(tempfile.mkdtemp(prefix="clay-forge-",dir=FORGE_ROOT))
    baseline=tmp/"baseline"; patched=tmp/"patched"
    try:
        for dest in (baseline,patched):
            p=subprocess.run(["git","clone","--quiet","--no-hardlinks","--local",str(ROOT),str(dest)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
            if p.returncode!=0:return {**base_record,"status":"forge_error","reason":"local clone failed"}
            ok,reason=_checkout_exact_source(dest,source_head)
            if not ok:return {**base_record,"status":"source_identity_unavailable","reason":reason}
        target_blobs=_target_blob_identities(baseline,source_head,targets)
        ap=subprocess.run(["git","apply","--whitespace=nowarn","-"],cwd=patched,input=patch,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        if ap.returncode!=0:return {**base_record,"status":"patch_rejected","reason":ap.stderr[-1000:],"target_blob_identities":target_blobs}
        baseline_runs=[]; patch_runs=[]
        # Two runs make flaky "one lucky pass" less likely and satisfy reproducibility bookkeeping.
        for _ in range(2):
            baseline_runs.append([run_cmd(baseline,c,120) for c in tests])
            patch_runs.append([run_cmd(patched,c,120) for c in tests])
        base_pass=sum(int(x["rc"]==0) for run in baseline_runs for x in run)
        patch_pass=sum(int(x["rc"]==0) for run in patch_runs for x in run)
        total=max(1,len(tests)*2)
        neg_results=[run_cmd(patched,c,120) for c in negatives]
        static_results=[]
        for t in targets:
            p=patched/t
            if p.suffix==".py" and p.exists():static_results.append(run_cmd(patched,"python3 -m py_compile "+subprocess.list2cmdline([t]),60))
            elif p.suffix==".sh" and p.exists():static_results.append(run_cmd(patched,"bash -n "+subprocess.list2cmdline([t]),60))
        bench_base=[]; bench_patch=[]
        if bench:
            for _ in range(2):bench_base.append(run_cmd(baseline,bench,180)); bench_patch.append(run_cmd(patched,bench,180))
        benchmark_non_regression=all(x["rc"]==0 for x in bench_patch) if bench_patch else True
        improvement=0.0
        metric="test_pass_rate"
        if patch_pass>base_pass:
            improvement=100.0*(patch_pass-base_pass)/total
        elif bench_patch and all(x["rc"]==0 for x in bench_base+bench_patch):
            b=sum(x["elapsed_s"] for x in bench_base)/len(bench_base); p=sum(x["elapsed_s"] for x in bench_patch)/len(bench_patch)
            if b>0: improvement=100.0*(b-p)/b; metric="benchmark_wall_time"
        tests_passed=patch_pass; tests_failed=total-patch_pass
        neg_pass=sum(int(x["rc"]==0) for x in neg_results); neg_fail=len(neg_results)-neg_pass
        static_pass=sum(int(x["rc"]==0) for x in static_results); static_fail=len(static_results)-static_pass
        accepted=(tests_failed==0 and neg_fail==0 and static_fail==0 and benchmark_non_regression and improvement>0)
        return {
            **base_record,"status":"accepted" if accepted else "validated_not_better","metric":metric,
            "relative_improvement_pct":improvement,"reproducible_runs":2,"tests_passed":tests_passed,"tests_failed":tests_failed,
            "negative_tests_passed":neg_pass,"negative_tests_failed":neg_fail,"static_checks_passed":static_pass,"static_checks_failed":static_fail,
            "benchmark_non_regression":benchmark_non_regression,"survived_go_cycles":0,"reverted":False,"baseline_test_passes":base_pass,
            "patched_test_passes":patch_pass,"test_count_per_run":len(tests),"benchmark_runs":len(bench_patch),
            "proposal_hypothesis":obj.get("hypothesis"),"falsifier":obj.get("falsifier"),"target_blob_identities":target_blobs,
            "requires_rebase_to_evaluation_head":bool(current_head and current_head!=source_head),
        }
    finally:
        shutil.rmtree(tmp,ignore_errors=True)


async def e2b_reproduce(con: sqlite3.Connection, discovery: dict, seconds_budget: float) -> dict | None:
    if discovery.get("provider")!="github":return None
    used=count(con,"e2b_sandbox_seconds")
    if used>=seconds_budget:return None
    clone=str((discovery.get("metadata") or {}).get("clone_url") or "")
    if not clone.startswith("https://github.com/"):return None
    key=secret("E2B_API_KEY")
    if not key:return None
    try:
        from e2b import Sandbox
    except Exception:
        return {"state":"DEPENDENCY_MISSING","provider":"e2b"}
    command=("set -e; git clone --depth 1 --filter=blob:none "+subprocess.list2cmdline([clone])+" r >/dev/null 2>&1; cd r; "
             "echo REPO=$(basename \"$PWD\"); echo FILES=$(find . -type f | wc -l); "
             "if [ -f pyproject.toml ] || [ -f setup.py ]; then python3 -m compileall -q .; fi; "
             "if [ -f Cargo.toml ]; then cargo check -q; fi; "
             "echo FORGE_PUBLIC_REPRO_OK")
    owner="forge:e2b:"+sha(clone)[:10]; started=time.monotonic(); status="ERROR"; stdout=""; stderr=""
    try:
        with quota_slot("e2b",owner,timeout_s=60,lease_s=240):
            sb=await asyncio.to_thread(Sandbox.create,timeout=180)
            try:
                result=await asyncio.to_thread(sb.commands.run,command,timeout=150)
                status="200" if result.exit_code==0 else "422"; stdout=str(result.stdout)[-1200:]; stderr=str(result.stderr)[-1200:]
            finally:
                await asyncio.to_thread(sb.kill)
        quota_observe("e2b",owner,status,{})
    except Exception as exc:
        msg=str(exc).lower()
        status="402" if any(x in msg for x in ("credit","payment","quota")) else "500"
        quota_observe("e2b",owner,status,{})
        stderr=type(exc).__name__+":"+str(exc)[:500]
    elapsed=time.monotonic()-started; bump(con,"e2b_sandbox_seconds",elapsed); bump(con,"e2b_jobs",1); bump(con,"e2b_pass",int(status=="200")); con.commit()
    return {"state":"PASS" if status=="200" else "FAIL","provider":"e2b","elapsed_s":elapsed,"stdout":stdout,"stderr":stderr,"status":status}


def metrics(con: sqlite3.Connection, peak_parallel: int = 0) -> dict:
    states={r[0]:r[1] for r in con.execute("SELECT state,COUNT(*) FROM candidates GROUP BY state")}
    providers={r[0]:r[1] for r in con.execute("SELECT provider,COUNT(*) FROM discoveries GROUP BY provider")}
    evals=[]
    if EVAL_PATH.exists():
        for line in EVAL_PATH.read_text(encoding="utf-8",errors="replace").splitlines():
            try:evals.append(json.loads(line))
            except Exception:pass
    return {"schema":"CLAY_FREE_EVIDENCE_FORGE_STATUS/v1","generated_at":now(),"candidate_states":states,"discovery_sources":providers,"discovery_queries":int(count(con,"discovery_queries")),"discovery_hits":int(count(con,"discovery_hits")),"evaluations":len(evals),"accepted_deltas":sum(1 for x in evals if x.get("status")=="accepted"),"e2b_jobs":int(count(con,"e2b_jobs")),"e2b_pass":int(count(con,"e2b_pass")),"e2b_sandbox_seconds":round(count(con,"e2b_sandbox_seconds"),3),"peak_parallel_tasks":peak_parallel,"shared_provider_budget":quota_snapshot(),"db_bytes":DB_PATH.stat().st_size if DB_PATH.exists() else 0}


async def cycle(con: sqlite3.Connection, args: argparse.Namespace) -> int:
    ingest_worker_candidates(con)
    questions=open_questions(args.questions_per_cycle)
    todo=[q for q in questions if not con.execute("SELECT 1 FROM processed_questions WHERE question_hash=?",(sha(q),)).fetchone()]
    discoveries=[]
    sem=asyncio.Semaphore(args.discovery_parallel)
    active=0; peak=0; lock=asyncio.Lock()
    async def wrapped(q):
        nonlocal active,peak
        async with sem:
            async with lock: active+=1; peak=max(peak,active)
            try:return await discovery_for_question(con,q)
            finally:
                async with lock: active-=1
    if todo:
        groups=await asyncio.gather(*(wrapped(q) for q in todo[:args.discovery_parallel*2]),return_exceptions=True)
        for g in groups:
            if isinstance(g,list):discoveries.extend(g)
    rows=con.execute("SELECT * FROM candidates WHERE ready=1 AND state='NEW' ORDER BY ingested_at LIMIT ?",(args.candidates_per_cycle,)).fetchall()
    local_sem=asyncio.Semaphore(args.local_parallel)
    async def val(row):
        async with local_sem:return await asyncio.to_thread(validate_candidate,con,row)
    vals=await asyncio.gather(*(val(r) for r in rows),return_exceptions=True) if rows else []
    for row,res in zip(rows,vals):
        if isinstance(res,dict):
            append_jsonl(EVAL_PATH,res)
            con.execute("UPDATE candidates SET state=?,evaluated_at=?,last_reason=? WHERE candidate_hash=?",(str(res.get("status") or "EVALUATED").upper(),now(),str(res.get("reason") or "")[:1000],row["candidate_hash"]))
            bump(con,"evaluations",1); bump(con,"accepted_deltas",int(res.get("status")=="accepted"))
        else:
            con.execute("UPDATE candidates SET state='FORGE_ERROR',evaluated_at=?,last_reason=? WHERE candidate_hash=?",(now(),type(res).__name__,row["candidate_hash"]))
    con.commit()
    # Reproduce a bounded number of public GitHub donor repos in independent E2B sandboxes.
    github=[d for d in discoveries if d.get("provider")=="github"][:args.e2b_jobs_per_cycle]
    e2b_sem=asyncio.Semaphore(args.e2b_parallel)
    async def er(d):
        async with e2b_sem:return await e2b_reproduce(con,d,args.e2b_sandbox_seconds_budget)
    if github: await asyncio.gather(*(er(d) for d in github),return_exceptions=True)
    atomic_json(STATUS_PATH,metrics(con,max(peak,args.local_parallel if rows else 0)))
    return len(rows)+len(discoveries)


async def main(args: argparse.Namespace) -> int:
    con=connect(); deadline=time.monotonic()+max(1,args.hours*3600); cycles=0
    try:
        while time.monotonic()<deadline and (args.max_cycles<=0 or cycles<args.max_cycles):
            usage=shutil.disk_usage(ARTIFACT_ROOT); reserve=max(20*1024**3,int(usage.total*0.12))
            if usage.free<=reserve:break
            try: await cycle(con,args)
            except Exception as exc:
                append_jsonl(FORGE_ROOT/"errors.jsonl",{"ts":now(),"error":type(exc).__name__+":"+str(exc)[:1000]})
            cycles+=1; atomic_json(STATUS_PATH,metrics(con)); await asyncio.sleep(max(1,args.sleep_seconds))
    finally:
        atomic_json(STATUS_PATH,metrics(con)); con.close()
    return 0


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--hours",type=float,default=24.0)
    p.add_argument("--max-cycles",type=int,default=0)
    p.add_argument("--sleep-seconds",type=float,default=20.0)
    p.add_argument("--questions-per-cycle",type=int,default=12)
    p.add_argument("--discovery-parallel",type=int,default=8)
    p.add_argument("--candidates-per-cycle",type=int,default=8)
    p.add_argument("--local-parallel",type=int,default=4)
    p.add_argument("--e2b-parallel",type=int,default=int(os.getenv("CLAY_E2B_MAX_CONCURRENCY","20")))
    p.add_argument("--e2b-jobs-per-cycle",type=int,default=8)
    p.add_argument("--e2b-sandbox-seconds-budget",type=float,default=float(os.getenv("CLAY_E2B_MAX_SANDBOX_SECONDS","36000")))
    return p.parse_args()


if __name__=="__main__":
    raise SystemExit(asyncio.run(main(parse_args())))
