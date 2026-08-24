#!/usr/bin/env python3
"""Conversion-focused successor wrapper for the strict Evidence Forge.

The base Forge remains the acceptance authority. This wrapper only repairs the
transport representation/source drift of worker patches and gives historical
PATCH_REJECTED rows one bounded retry:
- strip accidental Markdown fences around otherwise literal unified diffs;
- recover the exact source base from the worker record's deterministic
  ``repo_head_at_prompt`` field, never from model self-report;
- prove the patch applied at that recorded base;
- try Git's own 3-way application on current main and regenerate a canonical
  current-tree diff;
- pass the result back through the unmodified strict base validator.
No model output is accepted by this wrapper. Final acceptance still requires the
base Forge's reproducible tests, negative tests, static checks and measured
baseline improvement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from typing import Any

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))
import run_free_evidence_forge as f

_ORIGINAL_VALIDATE=f.validate_candidate
_ORIGINAL_CYCLE=f.cycle


def normalize_patch(patch: str) -> str:
    text=str(patch or "").replace("\r\n","\n").strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:diff|patch)?\s*\n?","",text,flags=re.I)
        text=re.sub(r"\n?```\s*$","",text)
    return text.strip()+("\n" if text.strip() else "")


def _git_commit_exists(commit: str) -> bool:
    if not re.fullmatch(r"[0-9a-fA-F]{40}",commit or ""):return False
    p=subprocess.run(["git","-C",str(f.ROOT),"cat-file","-e",f"{commit}^{{commit}}"],
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False,timeout=10)
    return p.returncode==0


def _worker_base_commit(worker_sha: str) -> str | None:
    """Recover source identity from runtime-owned worker telemetry, not model text."""
    want=str(worker_sha or "").strip()
    if not want:return None
    paths=sorted(f.ARTIFACT_ROOT.glob("active-*/workers.jsonl"),
                 key=lambda p:p.stat().st_mtime if p.exists() else 0,reverse=True)[:16]
    for path in paths:
        try:
            # Records are JSONL; stream them so large swarm logs do not need one
            # unbounded in-memory read. The first exact text hash match is enough.
            with path.open("r",encoding="utf-8",errors="replace") as fh:
                for line in fh:
                    try:row=json.loads(line)
                    except json.JSONDecodeError:continue
                    if not isinstance(row,dict):continue
                    text=str(row.get("text") or "")
                    observed=str(row.get("text_sha256") or (hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""))
                    if observed!=want:continue
                    commit=str(row.get("repo_head_at_prompt") or "").strip()
                    return commit if re.fullmatch(r"[0-9a-fA-F]{40}",commit) else None
        except OSError:continue
    return None


def _apply_check_at(commit: str, patch: str) -> bool:
    tmp=Path(tempfile.mkdtemp(prefix="clay-forge-v2-base-",dir=f.FORGE_ROOT))
    try:
        repo=tmp/"r"
        p=subprocess.run(["git","clone","--quiet","--no-hardlinks","--local",str(f.ROOT),str(repo)],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
        if p.returncode!=0:return False
        p=subprocess.run(["git","checkout","--quiet",commit],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
        if p.returncode!=0:return False
        p=subprocess.run(["git","apply","--check","--whitespace=nowarn","-"],cwd=repo,input=patch,text=True,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        return p.returncode==0
    finally:shutil.rmtree(tmp,ignore_errors=True)


def _three_way_rebase_to_current(patch: str) -> str | None:
    tmp=Path(tempfile.mkdtemp(prefix="clay-forge-v2-current-",dir=f.FORGE_ROOT))
    try:
        repo=tmp/"r"
        p=subprocess.run(["git","clone","--quiet","--no-hardlinks","--local",str(f.ROOT),str(repo)],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
        if p.returncode!=0:return None
        p=subprocess.run(["git","apply","--3way","--whitespace=nowarn","-"],cwd=repo,input=patch,text=True,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
        if p.returncode!=0:return None
        # --3way may update the index. Diff against HEAD so staged and unstaged
        # changes are both retained in the canonicalized patch.
        d=subprocess.run(["git","diff","HEAD","--binary","--full-index","--no-ext-diff"],cwd=repo,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
        out=d.stdout if d.returncode==0 else ""
        return out if out.strip() else None
    finally:shutil.rmtree(tmp,ignore_errors=True)


def _row_with_patch(row: Any,obj: dict[str,Any],patch: str) -> dict[str,Any]:
    data=dict(row);copy=dict(obj);copy["patch_unified_diff"]=patch
    data["proposal_json"]=json.dumps(copy,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return data


def validate_candidate_v2(con: sqlite3.Connection,row: sqlite3.Row) -> dict:
    obj=json.loads(row["proposal_json"]);raw=str(obj.get("patch_unified_diff") or "");patch=normalize_patch(raw)
    first=_ORIGINAL_VALIDATE(con,_row_with_patch(row,obj,patch))
    if str(first.get("status"))!="patch_rejected":return first

    base_commit=_worker_base_commit(str(row["worker_sha"] or ""))
    declared=str(obj.get("base_commit") or "").strip()
    if declared and base_commit and declared!=base_commit:
        return {**first,"reason":"V2_FINAL:MODEL_BASE_COMMIT_MISMATCH_RUNTIME_RECORD",
                "worker_base_commit":base_commit,"declared_base_commit":declared,"v2_retry":True}
    if not base_commit or not _git_commit_exists(base_commit):
        return {**first,"reason":"V2_FINAL:NO_VALID_RECORDED_REPO_HEAD_AT_PROMPT:"+str(first.get("reason") or "")[:600],
                "worker_base_commit":base_commit,"v2_retry":True}
    if not _apply_check_at(base_commit,patch):
        return {**first,"reason":"V2_FINAL:PATCH_INVALID_AT_RECORDED_WORKER_BASE:"+str(first.get("reason") or "")[:600],
                "worker_base_commit":base_commit,"v2_retry":True}

    rebased=_three_way_rebase_to_current(patch)
    if not rebased:
        return {**first,"status":"stale_patch","reason":"V2_FINAL:VALID_AT_RECORDED_BASE_BUT_NOT_3WAY_APPLICABLE_TO_CURRENT_MAIN",
                "worker_base_commit":base_commit,"v2_retry":True}

    final=_ORIGINAL_VALIDATE(con,_row_with_patch(row,obj,rebased))
    final["worker_base_commit"]=base_commit;final["v2_retry"]=True;final["v2_three_way_rebased"]=True
    if str(final.get("status"))=="patch_rejected":
        final["reason"]="V2_FINAL:CANONICAL_REBASE_STILL_REJECTED:"+str(final.get("reason") or "")[:700]
    return final


async def cycle_v2(con: sqlite3.Connection,args: argparse.Namespace) -> int:
    # Every historical rejected row gets exactly one successor retry. Runtime
    # telemetry supplies source identity; V2_FINAL makes the retry terminal.
    con.execute("UPDATE candidates SET state='NEW',last_reason='V2_RETRY_PENDING' "
                "WHERE state='PATCH_REJECTED' AND COALESCE(last_reason,'') NOT LIKE 'V2_FINAL:%'")
    con.commit()
    return await _ORIGINAL_CYCLE(con,args)


f.validate_candidate=validate_candidate_v2
f.cycle=cycle_v2


def parse_args() -> argparse.Namespace:
    # Keep a compatibility token in argv so the existing shell supervisor's
    # pgrep('[r]un_free_evidence_forge.py') recognizes this successor process and
    # does not spawn the legacy entrypoint beside it.
    argv=list(sys.argv[1:])
    if "--compat-name" in argv:
        i=argv.index("--compat-name");del argv[i:i+2]
    old=sys.argv
    try:
        sys.argv=[old[0],*argv]
        return f.parse_args()
    finally:sys.argv=old


if __name__=="__main__":raise SystemExit(__import__("asyncio").run(f.main(parse_args())))
