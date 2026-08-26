#!/usr/bin/env python3
"""Read-only restart-authority attribution for Clay legacy FreeSwarm processes.

Purpose: identify *why* a matched legacy process can restart before any kill action.
This probe never terminates processes, never reads secret values, and never performs
provider/network calls. It emits host/process/restart-authority evidence only.
"""
from __future__ import annotations

import argparse, hashlib, json, os, pathlib, platform, re, subprocess, time
from typing import Any

LEGACY_PATTERNS = (
    "run_free_evidence_forge.py",
    "run_research_distillery_local.py",
    "free swarm/evaluate.py",
    "update_fabric_live.py",
    "run_6000_free_swarm_supervisor.sh",
)
PROVIDER_ENV_NAMES = {
    "OPENROUTER_API_KEY", "GROQ_API_KEY", "MISTRAL_API_KEY", "NVIDIA_API_KEY",
    "TOGETHER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
}

def read_text(p: pathlib.Path) -> str:
    try: return p.read_text(errors="replace")
    except Exception: return ""

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def boot_id() -> str:
    return read_text(pathlib.Path("/proc/sys/kernel/random/boot_id")).strip()

def ns_id(pid: int, name: str) -> str | None:
    try: return os.readlink(f"/proc/{pid}/ns/{name}")
    except Exception: return None

def proc_record(pid: int) -> dict[str, Any]:
    base = pathlib.Path(f"/proc/{pid}")
    cmd = read_text(base/"cmdline").replace("\x00", " ").strip()
    status = read_text(base/"status")
    stat = read_text(base/"stat").split()
    ppid = int(stat[3]) if len(stat) > 4 and stat[3].isdigit() else None
    try: exe = os.readlink(base/"exe")
    except Exception: exe = None
    try: cwd = os.readlink(base/"cwd")
    except Exception: cwd = None
    uid = None
    m = re.search(r"^Uid:\s+(\d+)", status, re.M)
    if m: uid = int(m.group(1))
    cgroup = read_text(base/"cgroup").strip()
    env_names: list[str] = []
    try:
        raw = (base/"environ").read_bytes().split(b"\x00")
        names = {x.split(b"=",1)[0].decode(errors="ignore") for x in raw if b"=" in x}
        env_names = sorted(PROVIDER_ENV_NAMES & names)
    except Exception:
        pass
    return {"pid": pid, "ppid": ppid, "argv": cmd, "exe": exe, "cwd": cwd,
            "uid": uid, "cgroup": cgroup, "pid_ns": ns_id(pid,"pid"),
            "mnt_ns": ns_id(pid,"mnt"), "provider_env_names": env_names}

def parent_chain(pid: int, limit: int = 32) -> list[dict[str, Any]]:
    out=[]; seen=set(); cur=pid
    while cur and cur not in seen and len(out)<limit:
        seen.add(cur)
        r=proc_record(cur); out.append(r)
        cur=r.get("ppid") or 0
    return out

def run_readonly(cmd: list[str]) -> tuple[int,str]:
    try:
        p=subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return p.returncode, (p.stdout+p.stderr)[:20000]
    except Exception as e:
        return 127, repr(e)

def classify_restart_authority(rec: dict[str,Any], chain: list[dict[str,Any]]) -> dict[str,Any]:
    cg = rec.get("cgroup") or ""
    evidence=[]
    # systemd unit from cgroup is strongest local signal
    units = re.findall(r"(?:^|/)([^/]+\.(?:service|scope))", cg)
    if units:
        for u in units:
            rc,out=run_readonly(["systemctl","show",u,"--property=Id,ActiveState,SubState,Restart,FragmentPath"])
            evidence.append({"kind":"systemd_show","unit":u,"rc":rc,"output_sha256":sha256_text(out),"output":out})
        return {"class":"SYSTEMD_OR_SCOPE","confidence":"HIGH","evidence":evidence}
    # container cgroups
    if any(x in cg for x in ("docker", "libpod", "kubepods", "containerd")):
        return {"class":"CONTAINER_ORCHESTRATION","confidence":"MEDIUM","evidence":[{"cgroup":cg}]}
    # shell/nohup/supervisor ancestry
    av=" | ".join((x.get("argv") or "") for x in chain[1:])
    if re.search(r"tmux|screen", av, re.I):
        return {"class":"TMUX_OR_SCREEN","confidence":"MEDIUM","evidence":[{"ancestor_argv_sha256":sha256_text(av)}]}
    if re.search(r"nohup|supervis|while\s+true|run_6000_free_swarm_supervisor", av, re.I):
        return {"class":"SHELL_OR_NOHUP_SUPERVISOR","confidence":"MEDIUM","evidence":[{"ancestor_argv_sha256":sha256_text(av)}]}
    # cron is not reliably visible from ancestry; inspect scheduler listings read-only
    cron_hits=[]
    for cmd in (["crontab","-l"], ["systemctl","list-timers","--all","--no-pager"]):
        rc,out=run_readonly(list(cmd))
        if any(p.lower() in out.lower() for p in LEGACY_PATTERNS):
            cron_hits.append({"cmd":cmd,"rc":rc,"output_sha256":sha256_text(out)})
    if cron_hits:
        return {"class":"CRON_OR_TIMER","confidence":"HIGH","evidence":cron_hits}
    return {"class":"UNKNOWN","confidence":"NONE","evidence":[]}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output"); args=ap.parse_args()
    matches=[]
    for p in pathlib.Path("/proc").iterdir():
        if not p.name.isdigit(): continue
        pid=int(p.name); rec=proc_record(pid); argv=rec.get("argv") or ""
        pats=[x for x in LEGACY_PATTERNS if x.lower() in argv.lower()]
        if not pats: continue
        chain=parent_chain(pid)
        rec["matched_patterns"]=pats
        rec["parent_chain"]=chain
        rec["restart_authority"]=classify_restart_authority(rec,chain)
        matches.append(rec)
    receipt={
        "schema":"FREE_SWARM_RESTART_AUTHORITY_ATTRIBUTION/v1",
        "timestamp_unix":time.time(), "hostname":platform.node(), "boot_id":boot_id(),
        "self_pid_ns":ns_id(os.getpid(),"pid"), "matched_roots":matches,
        "matched_count":len(matches),
        "unknown_restart_authority_count":sum(1 for x in matches if x["restart_authority"]["class"]=="UNKNOWN"),
        "safe_to_kill_from_this_receipt": False,
        "network_or_provider_calls_performed": False,
        "secret_values_exposed": False,
    }
    text=json.dumps(receipt,sort_keys=True,indent=2)
    if args.output: pathlib.Path(args.output).write_text(text+"\n")
    print(text)
    # fail closed if anything is matched but restart authority is unknown
    return 2 if receipt["unknown_restart_authority_count"] else 0

if __name__ == "__main__": raise SystemExit(main())
