#!/usr/bin/env python3
"""Standalone exact Git source identity: HEAD/tree + tracked diff + untracked bytes."""
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path

def _git(root: Path, *args: str) -> bytes:
    p=subprocess.run(["git","-C",str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=15)
    if p.returncode:
        raise RuntimeError(f"git {args[0]} failed rc={p.returncode}")
    return p.stdout

def _sha_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def identity(root: Path) -> dict:
    root=root.resolve()
    head=_git(root,"rev-parse","HEAD").strip().decode()
    tree=_git(root,"rev-parse","HEAD^{tree}").strip().decode()
    diff=_git(root,"diff","--binary","--no-ext-diff","HEAD","--")
    raw=_git(root,"ls-files","--others","--exclude-standard","-z")
    entries=[]
    for rp in sorted(x for x in raw.split(b"\0") if x):
        p=root/os.fsdecode(rp)
        if not p.is_file():
            raise RuntimeError("unsupported untracked entry")
        entries.append({"path_sha256":hashlib.sha256(rp).hexdigest(),"content_sha256":_sha_file(p),"size":p.stat().st_size})
    dirty={"tracked_diff_sha256":hashlib.sha256(diff).hexdigest(),"tracked_diff_bytes":len(diff),"untracked":entries,"dirty":bool(diff or entries)}
    canonical=json.dumps({"head":head,"tree":tree,"dirty":dirty},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return {"schema":"ACCEPTANCE_KIT_SOURCE_IDENTITY/v1","repo_head":head,"repo_tree":tree,"dirty_state":dirty,"source_identity_sha256":hashlib.sha256(canonical).hexdigest()}
