#!/usr/bin/env python3
"""Standalone adaptation of the repo's preimage-bound edit guard.

A proposal is accepted only when the expected preimage hash matches the actual
current bytes and every changed old-file span falls inside an explicit range.
"""
from __future__ import annotations
import hashlib
from difflib import SequenceMatcher
from pathlib import PurePosixPath

SCHEMA = "ACCEPTANCE_KIT_PREIMAGE_GUARD/v1"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _safe(path: str) -> bool:
    p = PurePosixPath(path)
    return bool(path) and not p.is_absolute() and ".." not in p.parts

def evaluate(path: str, preimage: str, proposed: str, expected_sha256: str, ranges: list[list[int]], current: str | None = None) -> dict:
    if not _safe(path):
        return {"schema": SCHEMA, "pass": False, "reason": "UNSAFE_PATH"}
    actual = sha256_text(preimage)
    current_text = preimage if current is None else current
    if expected_sha256 != actual:
        return {"schema": SCHEMA, "pass": False, "reason": "EXPECTED_PREIMAGE_HASH_MISMATCH"}
    if sha256_text(current_text) != actual:
        return {"schema": SCHEMA, "pass": False, "reason": "STALE_PREIMAGE"}
    old = preimage.splitlines(keepends=True)
    new = proposed.splitlines(keepends=True)
    normalized=[]
    for item in ranges:
        if len(item)!=2:
            return {"schema": SCHEMA, "pass": False, "reason": "INVALID_SCOPE"}
        a,b=map(int,item)
        if a < 1 or b < a or b > max(1,len(old)):
            return {"schema": SCHEMA, "pass": False, "reason": "INVALID_SCOPE"}
        normalized.append((a,b))
    if not normalized:
        return {"schema": SCHEMA, "pass": False, "reason": "NO_SCOPE"}
    changed=[]
    for tag,i1,i2,j1,j2 in SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
        if tag=="equal":
            continue
        if i1==i2:
            anchor=1 if i1==0 else min(max(1,len(old)),i1)
            allowed=any(a<=anchor<=b for a,b in normalized)
        else:
            start,end=i1+1,i2
            allowed=any(a<=start and end<=b for a,b in normalized)
        changed.append({"tag":tag,"old_start":i1+1,"old_end":i2,"allowed":allowed})
        if not allowed:
            return {"schema": SCHEMA, "pass": False, "reason": "CHANGE_OUTSIDE_SCOPE", "changed": changed}
    if preimage == proposed:
        return {"schema": SCHEMA, "pass": False, "reason": "NO_CHANGE"}
    return {"schema": SCHEMA, "pass": True, "reason": "ACCEPTED", "changed": changed}
