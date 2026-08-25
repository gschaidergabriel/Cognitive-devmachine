#!/usr/bin/env python3
"""Host-local attribution probe for post-HARD_OFF provider drift.

This tool performs NO provider/model/network calls and NO process termination.
It is intended to identify provider-capable process candidates on a host when
shared provider-budget counters continue moving after FREE_PROVIDER_ADMISSION
is HARD_OFF.

Privacy/safety boundary:
- never records secret values;
- reads /proc/<pid>/environ only to report the NAMES of known provider-key vars;
- hashes machine-id instead of emitting it;
- permission-denied process metadata is counted, not treated as absence.

A candidate process is not automatically the causal source of counter drift.
This probe only narrows host/process attribution. Causal attribution requires a
bounded before/after counter window plus process disappearance/reappearance or
other independently bound evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import socket
import time
from typing import Any, Iterable

SCHEMA = "CLAY_PROVIDER_CAPABILITY_HOST_ATTRIBUTION/v1"
REQUIRED_EXECUTION_STATE = "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF"
DEFAULT_DB = os.getenv("CLAY_FREE_PROVIDER_BUDGET_DB", "/artifacts/clay-entityos-swarm/provider_budget.sqlite3")

PROVIDER_ENV_NAMES = {
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "NVIDIA_API_KEY",
    "NGC_API_KEY",
    "MISTRAL_API_KEY",
    "TOGETHER_API_KEY",
}

KNOWN_PROVIDER_PROCESS_NEEDLES = (
    "run_6000_free_swarm_supervisor.sh",
    "run_24h_entityos_swarm_supervisor.sh",
    "run_24h_entityos_swarm.py",
    "run_free_go_swarm.py",
    "run_free_evidence_forge.py",
    "run_research_distillery_local.py",
    "run_research_distillery_entry.py",
    "free swarm/evaluate.py",
    "openrouter",
    "groq",
    "mistral",
    "nvidia",
)

class ProbeError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file_if_present(path: Path) -> str | None:
    try:
        return sha256_bytes(path.read_bytes())
    except Exception:
        return None


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ProbeError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProbeError(f"JSON root is not object: {path}")
    return value


def canonical_provider_names(admission: dict[str, Any]) -> tuple[str, ...]:
    providers = admission.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise ProbeError("FREE_PROVIDER_ADMISSION providers missing")
    out = []
    for name, value in providers.items():
        if not isinstance(value, dict) or "admitted" not in value:
            raise ProbeError(f"provider {name!r} missing admitted")
        out.append(str(name))
    return tuple(sorted(out))


def authority_snapshot(path: Path) -> dict[str, Any]:
    obj = read_json(path)
    names = canonical_provider_names(obj)
    providers = obj["providers"]
    states = {name: bool(providers[name].get("admitted")) for name in names}
    execution_state = obj.get("execution_state")
    return {
        "path": str(path),
        "sha256": hash_file_if_present(path),
        "execution_state": execution_state,
        "providers": states,
        "hard_off": execution_state == REQUIRED_EXECUTION_STATE and all(v is False for v in states.values()),
    }


def budget_snapshot(path: Path, providers: Iterable[str]) -> dict[str, Any]:
    provider_set = set(str(x) for x in providers)
    if not path.exists():
        raise ProbeError(f"provider budget DB missing: {path}")
    try:
        con = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True, timeout=2)
        try:
            rows = con.execute(
                "SELECT provider,total_requests,total_success,total_429,total_errors FROM provider_state ORDER BY provider"
            ).fetchall()
            leases = con.execute(
                "SELECT lease_id,provider,owner,acquired_at,expires_at FROM leases WHERE expires_at > ? ORDER BY provider,lease_id",
                (time.time(),),
            ).fetchall()
        finally:
            con.close()
    except Exception as exc:
        raise ProbeError(f"cannot read provider budget DB: {exc}") from exc
    counters = {}
    for provider, total_requests, total_success, total_429, total_errors in rows:
        p = str(provider)
        if p not in provider_set:
            continue
        counters[p] = {
            "total_requests": int(total_requests),
            "total_success": int(total_success),
            "total_429": int(total_429),
            "total_errors": int(total_errors),
        }
    active_leases = [
        {
            "lease_id": str(lease_id),
            "provider": str(provider),
            "owner": str(owner),
            "acquired_at": float(acquired_at),
            "expires_at": float(expires_at),
        }
        for lease_id, provider, owner, acquired_at, expires_at in leases
        if str(provider) in provider_set
    ]
    return {"counters": counters, "unexpired_leases": active_leases}


def parse_environ_names(raw: bytes) -> list[str]:
    names = []
    for item in raw.split(b"\0"):
        if not item or b"=" not in item:
            continue
        key = item.split(b"=", 1)[0].decode("utf-8", errors="ignore")
        if key in PROVIDER_ENV_NAMES:
            names.append(key)
    return sorted(set(names))


def read_text_soft(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return None


def process_snapshot(proc_root: Path = Path("/proc")) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    permission_denied_environ = 0
    scanned = 0
    for pid_dir in sorted((p for p in proc_root.iterdir() if p.name.isdigit()), key=lambda p: int(p.name)):
        pid = int(pid_dir.name)
        if pid in {os.getpid(), os.getppid()}:
            continue
        scanned += 1
        cmd_raw = b""
        try:
            cmd_raw = (pid_dir / "cmdline").read_bytes()
        except Exception:
            pass
        cmdline = cmd_raw.replace(b"\0", b" ").decode("utf-8", errors="replace").strip()
        env_names: list[str] = []
        try:
            env_names = parse_environ_names((pid_dir / "environ").read_bytes())
        except PermissionError:
            permission_denied_environ += 1
        except Exception:
            pass
        matched_needles = [needle for needle in KNOWN_PROVIDER_PROCESS_NEEDLES if needle.lower() in cmdline.lower()]
        if not env_names and not matched_needles:
            continue
        ppid = None
        status = read_text_soft(pid_dir / "status") or ""
        for line in status.splitlines():
            if line.startswith("PPid:"):
                try:
                    ppid = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
                break
        exe = None
        try:
            exe = os.readlink(pid_dir / "exe")
        except Exception:
            pass
        cgroup = read_text_soft(pid_dir / "cgroup")
        candidates.append({
            "pid": pid,
            "ppid": ppid,
            "exe": exe,
            "cmdline": cmdline,
            "provider_env_names_present": env_names,
            "matched_needles": matched_needles,
            "cgroup": cgroup,
        })
    return {
        "scanned_processes": scanned,
        "permission_denied_environ": permission_denied_environ,
        "candidates": candidates,
        "zero_candidates": not candidates,
    }


def host_fingerprint() -> dict[str, Any]:
    machine_id_hash = hash_file_if_present(Path("/etc/machine-id"))
    boot_id = read_text_soft(Path("/proc/sys/kernel/random/boot_id"))
    pid_ns = None
    try:
        pid_ns = os.readlink("/proc/self/ns/pid")
    except Exception:
        pass
    return {
        "hostname": socket.gethostname(),
        "machine_id_sha256": machine_id_hash,
        "boot_id": boot_id,
        "pid_namespace": pid_ns,
    }


def counter_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    out = {}
    b = before.get("counters", {})
    a = after.get("counters", {})
    for provider in sorted(set(b) | set(a)):
        br = b.get(provider, {})
        ar = a.get(provider, {})
        out[provider] = {
            key: int(ar.get(key, 0)) - int(br.get(key, 0))
            for key in ("total_requests", "total_success", "total_429", "total_errors")
        }
    return out


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    authority = authority_snapshot(repo / args.admission)
    if not authority["hard_off"]:
        raise ProbeError("canonical provider admission is not HARD_OFF")
    providers = tuple(authority["providers"].keys())
    before = budget_snapshot(Path(args.provider_budget_db), providers)
    process_before = process_snapshot(Path(args.proc_root))
    start = time.time()
    time.sleep(args.window_seconds)
    process_after = process_snapshot(Path(args.proc_root))
    after = budget_snapshot(Path(args.provider_budget_db), providers)
    end = time.time()
    delta = counter_delta(before, after)
    moved = any(any(v != 0 for v in row.values()) for row in delta.values())
    candidates = process_before["candidates"] or process_after["candidates"]
    status = "HOST_COUNTER_DRIFT_WITH_PROVIDER_CAPABLE_CANDIDATES" if moved and candidates else (
        "HOST_COUNTER_DRIFT_NO_LOCAL_CANDIDATE" if moved else (
            "HOST_QUIET_WITH_PROVIDER_CAPABLE_CANDIDATES" if candidates else "HOST_QUIET_ZERO_CANDIDATES"
        )
    )
    return {
        "schema": SCHEMA,
        "source": {"path": str(Path(__file__).resolve()), "sha256": hash_file_if_present(Path(__file__).resolve())},
        "host": host_fingerprint(),
        "authority": authority,
        "observation": {
            "start_unix": start,
            "end_unix": end,
            "requested_window_seconds": args.window_seconds,
            "provider_budget_before": before,
            "provider_budget_after": after,
            "provider_counter_delta": delta,
            "counter_moved": moved,
            "process_before": process_before,
            "process_after": process_after,
        },
        "decision": {
            "status": status,
            "candidate_is_causal_proof": False,
            "fleet_quiescence_credit": 0,
            "note": "Run on every execution host sharing or capable of exercising the provider path; compare host fingerprints and bounded deltas.",
        },
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--admission", default="research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")
    p.add_argument("--provider-budget-db", default=DEFAULT_DB)
    p.add_argument("--proc-root", default="/proc")
    p.add_argument("--window-seconds", type=float, default=60.0)
    p.add_argument("--out")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = run(args)
    except ProbeError as exc:
        print(json.dumps({"schema": SCHEMA, "decision": {"status": "FAIL_CLOSED", "reason": str(exc)}}, indent=2))
        return 2
    encoded = json.dumps(receipt, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
