#!/usr/bin/env python3
"""Deterministic intake/finalization helper for the RAE project-wide `dump` command.

This tool does NOT interpret evidence and does NOT promote claims. It freezes the input
queue, computes content identities, creates a batch receipt, and moves originals to the
verified archive only after an explicit finalize step.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "dump"
ARCHIVE = ROOT / "dump archive"
RUNTIME = ROOT / ".rae_runtime" / "dump"
CANON = ROOT / "research_entity" / "continuity" / "RESEARCH_ENTITY_CANONICAL.json"
CONTROL_NAMES = {"README.md", ".gitkeep", ".DS_Store"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def payload_files() -> list[Path]:
    if not INBOX.exists():
        return []
    out=[]
    for p in sorted(INBOX.rglob("*")):
        if not p.is_file():
            continue
        if p.name in CONTROL_NAMES:
            continue
        if any(part.startswith(".") for part in p.relative_to(INBOX).parts):
            continue
        out.append(p)
    return out


def canonical_parent() -> dict:
    if not CANON.exists():
        return {"status":"UNAVAILABLE"}
    x=json.loads(CANON.read_text(encoding="utf-8"))
    return {"entity_version":x.get("entity_version"),"revision":x.get("revision"),"state_hash":x.get("state_hash")}


def build_manifest(actor: str, session_id: str|None, prompt_run_id: str|None) -> dict:
    rows=[]
    for p in payload_files():
        rel=p.relative_to(INBOX).as_posix()
        rows.append({"relative_path":rel,"bytes":p.stat().st_size,"sha256":sha256_file(p),"suffix":p.suffix.lower()})
    root_material="\n".join(f"{r['relative_path']}\0{r['bytes']}\0{r['sha256']}" for r in rows).encode()
    root_hash=hashlib.sha256(root_material).hexdigest()
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_id=f"dump-{stamp}-{root_hash[:12]}"
    return {
        "schema_version":"1.0",
        "batch_id":batch_id,
        "created_at":utc_now(),
        "trigger":"dump",
        "origin_class":"DUMP",
        "default_epistemic_class":"DUMP_DERIVED_PREPROCESSED_HYPOTHESIS",
        "promotion_allowed_without_independent_support":False,
        "actor_id":actor,
        "session_id":session_id,
        "prompt_run_id":prompt_run_id,
        "canonical_parent":canonical_parent(),
        "input_root":"dump/",
        "payload_count":len(rows),
        "payload_bytes":sum(r["bytes"] for r in rows),
        "batch_root_sha256":root_hash,
        "files":rows,
        "state":"FROZEN_FOR_ANALYSIS" if rows else "EMPTY"
    }


def cmd_prepare(args):
    INBOX.mkdir(parents=True,exist_ok=True); ARCHIVE.mkdir(parents=True,exist_ok=True); RUNTIME.mkdir(parents=True,exist_ok=True)
    m=build_manifest(args.actor,args.session_id,args.prompt_run_id)
    out=RUNTIME/f"{m['batch_id']}.json"
    out.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({**m,"runtime_manifest":str(out.relative_to(ROOT)),"protocol":"research_entity/global/DUMP_PROTOCOL.md"},ensure_ascii=False,indent=2))


def load_manifest(batch_id: str) -> tuple[Path,dict]:
    p=RUNTIME/f"{batch_id}.json"
    if not p.exists(): raise RuntimeError(f"unknown batch manifest: {batch_id}")
    return p,json.loads(p.read_text(encoding="utf-8"))


def cmd_verify(args):
    _,m=load_manifest(args.batch_id); failures=[]
    for row in m["files"]:
        p=INBOX/row["relative_path"]
        if not p.exists(): failures.append({"path":row["relative_path"],"error":"missing"}); continue
        got=sha256_file(p)
        if got!=row["sha256"]: failures.append({"path":row["relative_path"],"error":"hash_mismatch","expected":row["sha256"],"got":got})
    print(json.dumps({"ok":not failures,"batch_id":args.batch_id,"failures":failures},ensure_ascii=False,indent=2))
    raise SystemExit(0 if not failures else 2)


def cmd_finalize(args):
    mp,m=load_manifest(args.batch_id)
    if not m.get("files"): raise RuntimeError("cannot finalize an empty dump batch")
    failures=[]
    for row in m["files"]:
        p=INBOX/row["relative_path"]
        if not p.exists(): failures.append({"path":row["relative_path"],"error":"missing"}); continue
        got=sha256_file(p)
        if got!=row["sha256"]: failures.append({"path":row["relative_path"],"error":"hash_mismatch","expected":row["sha256"],"got":got})
    if failures: raise RuntimeError("input changed after freeze: "+json.dumps(failures,ensure_ascii=False))
    if not args.result or not Path(args.result).exists():
        raise RuntimeError("finalize requires --result pointing to a completed DUMP_RESULT.json")
    result=json.loads(Path(args.result).read_text(encoding="utf-8"))
    if result.get("batch_id")!=args.batch_id: raise RuntimeError("result batch_id mismatch")
    if not result.get("pipeline_complete"): raise RuntimeError("DUMP_RESULT does not assert pipeline_complete=true")
    dest=ARCHIVE/args.batch_id
    if dest.exists(): raise RuntimeError(f"archive batch already exists: {dest}")
    originals=dest/"original"; originals.mkdir(parents=True)
    moved=[]
    try:
        for row in m["files"]:
            src=INBOX/row["relative_path"]; dst=originals/row["relative_path"]; dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(str(src),str(dst)); moved.append((src,dst))
        # Verify the archived bytes before declaring success.
        for row in m["files"]:
            dst=originals/row["relative_path"]
            got=sha256_file(dst)
            if got!=row["sha256"]: raise RuntimeError(f"archive hash mismatch: {row['relative_path']}")
        m["state"]="ARCHIVED_VERIFIED"; m["archived_at"]=utc_now(); m["archive_root"]=str(dest.relative_to(ROOT))
        (dest/"MANIFEST.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        shutil.copy2(args.result,dest/"DUMP_RESULT.json")
        if args.delta:
            shutil.copy2(args.delta,dest/"RESEARCH_DELTA.md")
        elif not (dest/"RESEARCH_DELTA.md").exists():
            (dest/"RESEARCH_DELTA.md").write_text("# Research Delta\n\nSee DUMP_RESULT.json and Research Entity events for this batch.\n",encoding="utf-8")
        mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except Exception:
        # Best-effort rollback to the inbox if archiving fails midway.
        for src,dst in reversed(moved):
            if dst.exists() and not src.exists():
                src.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(dst),str(src))
        if dest.exists(): shutil.rmtree(dest,ignore_errors=True)
        raise
    print(json.dumps({"ok":True,"batch_id":args.batch_id,"archived_files":len(m["files"]),"archive_root":str(dest.relative_to(ROOT)),"inbox_payload_remaining":len(payload_files())},ensure_ascii=False,indent=2))


def parser():
    p=argparse.ArgumentParser(description="RAE dump queue freezer/verifier/archiver")
    s=p.add_subparsers(dest="cmd",required=True)
    x=s.add_parser("prepare"); x.add_argument("--actor",required=True); x.add_argument("--session-id"); x.add_argument("--prompt-run-id"); x.set_defaults(fn=cmd_prepare)
    x=s.add_parser("verify"); x.add_argument("batch_id"); x.set_defaults(fn=cmd_verify)
    x=s.add_parser("finalize"); x.add_argument("batch_id"); x.add_argument("--result",required=True); x.add_argument("--delta"); x.set_defaults(fn=cmd_finalize)
    return p


def main():
    try: parser().parse_args().__dict__["fn"](parser().parse_args())
    except (RuntimeError,ValueError) as e:
        print(json.dumps({"ok":False,"error":str(e)},ensure_ascii=False),file=sys.stderr); raise SystemExit(2)


if __name__=="__main__":
    # Parse once; keep explicit to avoid hidden state.
    args=parser().parse_args()
    try: args.fn(args)
    except (RuntimeError,ValueError) as e:
        print(json.dumps({"ok":False,"error":str(e)},ensure_ascii=False),file=sys.stderr); raise SystemExit(2)
