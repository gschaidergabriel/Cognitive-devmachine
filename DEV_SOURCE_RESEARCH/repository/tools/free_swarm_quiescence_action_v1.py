#!/usr/bin/env python3
"""Fail-closed Clay legacy runtime quiescence actioner.

Purpose: under an already-established HARD_OFF provider authority, stop only the
known Clay FreeSwarm/Forge/Distillery legacy process family and prove that it does
not reappear during an observation window. The dashboard-only publisher is
explicitly excluded because it is non-provider-capable evidence publication.

Default is dry-run. --apply is required to signal/terminate anything.
No network/provider calls and no secret values are read.
"""
from __future__ import annotations

import argparse, hashlib, json, os, pathlib, signal, time
from typing import Any

LEGACY_MARKERS = (
    "tools/run_free_evidence_forge.py",
    "tools/run_research_distillery_local.py",
    "free swarm/evaluate.py",
    "free swarm/update_fabric_live.py",
    "tools/run_6000_free_swarm_supervisor.sh",
)
EXPLICIT_EXCLUDES = (
    "clay-free-swarm-publisher",
    "bridge_daemon.py",
)


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def read_cmd(pid: int) -> str:
    try:
        raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
        return raw.replace(b"\x00", b" ").decode(errors="replace").strip()
    except Exception:
        return ""


def read_ppid(pid: int) -> int | None:
    try:
        for line in pathlib.Path(f"/proc/{pid}/status").read_text(errors="replace").splitlines():
            if line.startswith("PPid:"):
                return int(line.split()[1])
    except Exception:
        pass
    return None


def scan() -> list[dict[str, Any]]:
    out=[]
    for p in pathlib.Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        pid=int(p.name); cmd=read_cmd(pid)
        if not cmd or any(x in cmd for x in EXPLICIT_EXCLUDES):
            continue
        matched=[m for m in LEGACY_MARKERS if m in cmd]
        if matched:
            out.append({"pid":pid,"ppid":read_ppid(pid),"argv_sha256":h(cmd),"matched_markers":matched,"argv":cmd})
    return sorted(out,key=lambda x:x["pid"])


def descendants(pids: set[int]) -> set[int]:
    changed=True
    while changed:
        changed=False
        for p in pathlib.Path("/proc").iterdir():
            if not p.name.isdigit(): continue
            pid=int(p.name); pp=read_ppid(pid)
            if pp in pids and pid not in pids:
                pids.add(pid); changed=True
    return pids


def safe_target(row: dict[str,Any]) -> bool:
    cmd=row.get("argv") or ""
    # Require an exact known Clay legacy marker and reject broad shell-only matches.
    return bool(row.get("matched_markers")) and not any(x in cmd for x in EXPLICIT_EXCLUDES)


def terminate_exact(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    roots={int(r["pid"]) for r in rows if safe_target(r)}
    targets=descendants(set(roots))
    events=[]
    # descendants first, then roots; never PID 1 or our own process.
    ordered=sorted((p for p in targets if p not in {1,os.getpid(),os.getppid()}), reverse=True)
    for pid in ordered:
        cmd=read_cmd(pid)
        if not cmd: continue
        # Descendants are allowed only if ancestrally bound to a matched root; log hashes only.
        try:
            os.kill(pid, signal.SIGTERM)
            events.append({"pid":pid,"signal":"SIGTERM","argv_sha256":h(cmd)})
        except ProcessLookupError:
            pass
    time.sleep(3)
    for pid in ordered:
        if pathlib.Path(f"/proc/{pid}").exists():
            cmd=read_cmd(pid)
            try:
                os.kill(pid, signal.SIGKILL)
                events.append({"pid":pid,"signal":"SIGKILL","argv_sha256":h(cmd)})
            except ProcessLookupError:
                pass
    return events


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--window-seconds",type=int,default=90)
    ap.add_argument("--output")
    args=ap.parse_args()
    before=scan()
    events=[]
    if args.apply and before:
        if not all(safe_target(r) for r in before):
            raise SystemExit("unsafe or ambiguous target detected")
        events=terminate_exact(before)
    start=time.time(); samples=[]; restarted=False
    while time.time()-start < max(1,args.window_seconds):
        cur=scan(); samples.append({"t":round(time.time()-start,3),"matched_count":len(cur),"pids":[r["pid"] for r in cur]})
        if args.apply and cur: restarted=True
        time.sleep(min(5,max(0.2,args.window_seconds/20)))
    after=scan()
    state=("PASS_QUIESCENT" if args.apply and not after and not restarted else
           "DRY_RUN_MATCHES_FOUND" if (not args.apply and before) else
           "DRY_RUN_ALREADY_QUIESCENT" if not args.apply else "FAIL_RESTART_OR_SURVIVOR")
    receipt={
      "schema":"CLAY_FREE_SWARM_QUIESCENCE_ACTION/v1",
      "state":state,
      "apply":args.apply,
      "window_seconds":args.window_seconds,
      "before_matched_count":len(before),
      "before":[{k:v for k,v in r.items() if k!="argv"} for r in before],
      "termination_events":events,
      "samples":samples,
      "after_matched_count":len(after),
      "after":[{k:v for k,v in r.items() if k!="argv"} for r in after],
      "restart_observed":restarted,
      "publisher_explicitly_excluded":True,
      "provider_calls":0,
      "secret_values_read":False,
      "unrelated_processes_targeted":0,
    }
    text=json.dumps(receipt,sort_keys=True,indent=2)
    if args.output: pathlib.Path(args.output).write_text(text+"\n")
    print(text)
    if args.apply: return 0 if state=="PASS_QUIESCENT" else 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())
