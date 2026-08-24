#!/usr/bin/env python3
"""Reconcile the live 6000 Free-Swarm runtime with current EntityOS/HCU authority.

This script intentionally exists at the path already called by
``tools/run_6000_free_swarm_supervisor.sh`` every supervisor cycle. It is a
credential-blind recovery/truth bridge:

* prefer the live ``SUPERVISOR_6000.json`` over the legacy supervisor snapshot;
* resolve canonical provider admission from the current checkout, never from a
  cached dashboard file;
* kill only a stale external-provider fabric child whose run manifest is bound
  to an older provider-admission epoch; the parent supervisor restarts it on the
  next cycle under current admission/economic gates;
* restart the zero-provider-billing loopback local model only when it is neither
  healthy nor currently bootstrapping;
* mirror a compatibility ``SUPERVISOR.json`` for older dashboard code;
* run the existing system-analysis publisher and then overwrite only its runtime
  view with current 6000 truth, preventing legacy 8.69/STOPPED/NOT_READY ghosts.

No provider credential value is read. No paid route or Together path is used.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Any
import urllib.request

RUNTIME_SCHEMA = "CLAY_RUNTIME_RECONCILIATION/v1"
FRESH_SUPERVISOR_SECONDS = 90.0


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def age_seconds(snapshot: dict[str, Any], now: dt.datetime | None = None) -> float | None:
    ts = parse_time(snapshot.get("observed_at") or snapshot.get("updated_at") or snapshot.get("generated_at"))
    if ts is None:
        return None
    current = now or dt.datetime.now(dt.timezone.utc)
    return max(0.0, (current - ts.astimezone(dt.timezone.utc)).total_seconds())


def proc_cmdlines() -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for p in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            raw = p.read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
            rows.append((int(p.parent.name), raw))
        except Exception:
            continue
    return rows


def matching_pids(*needles: str) -> list[int]:
    me = os.getpid()
    return [pid for pid, cmd in proc_cmdlines() if pid != me and any(n in cmd for n in needles)]


def proc_has(*needles: str) -> bool:
    return bool(matching_pids(*needles))


def git_head(repo: Path) -> str | None:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
        value = p.stdout.strip().lower()
        return value if p.returncode == 0 and len(value) == 40 else None
    except Exception:
        return None


def canonical_admission(repo: Path) -> dict[str, Any]:
    tool = repo / "tools/free_provider_admission.py"
    if not tool.is_file():
        return {"schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1", "ok": False, "status": "ADMISSION_TOOL_MISSING"}
    try:
        p = subprocess.run(
            [sys.executable, str(tool), "--json"], cwd=repo, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, check=False,
            env={**os.environ, "PYTHONPATH": str(repo / "tools") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        value = json.loads(p.stdout.strip() or "{}")
        if isinstance(value, dict):
            if p.returncode != 0:
                value.setdefault("ok", False)
                value.setdefault("status", "ADMISSION_TOOL_NONZERO")
            return value
    except Exception as exc:
        return {"schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1", "ok": False, "status": f"ADMISSION_RESOLVE_ERROR:{type(exc).__name__}"}
    return {"schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1", "ok": False, "status": "ADMISSION_RESOLVE_INVALID_OUTPUT"}


def latest_path(root: Path, pattern: str, leaf: str) -> Path | None:
    rows = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    for directory in rows:
        candidate = directory / leaf
        if candidate.exists():
            return candidate
    return None


def latest_fabric_manifest(artifacts: Path) -> dict[str, Any]:
    path = latest_path(artifacts, "active-fabric6000-v2-*", "run_manifest.json")
    return load_json(path) if path else {}


def latest_fabric_status(artifacts: Path) -> dict[str, Any]:
    path = latest_path(artifacts, "active-fabric6000-v2-*", "status.json")
    return load_json(path) if path else {}


def loopback_health(port: int = 8088) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.5) as response:
            return 200 <= int(response.status) < 300
    except Exception:
        return False


def local_model_state_candidates(artifacts: Path) -> list[Path]:
    candidates = [artifacts / "local-model.json"]
    home = Path.home()
    candidates.append(home / ".local/state/clay-entityos-swarm/local-model.json")
    xdg = os.getenv("XDG_STATE_HOME")
    if xdg:
        candidates.append(Path(xdg) / "clay-entityos-swarm/local-model.json")
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def newest_local_model_state(artifacts: Path) -> tuple[dict[str, Any], str | None]:
    present = [p for p in local_model_state_candidates(artifacts) if p.exists()]
    if not present:
        return {}, None
    present.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return load_json(present[0]), str(present[0])


def compatibility_supervisor(
    sup6000: dict[str, Any],
    canonical: dict[str, Any],
    *,
    supervisor_running: bool,
    fabric_running: bool,
    local_ready: bool,
) -> dict[str, Any]:
    """Map current 6000 fields into the legacy dashboard contract without hiding source."""
    result = dict(sup6000)
    result["schema"] = "CLAY_RUNTIME_SUPERVISOR_COMPAT/v1"
    result["compat_source_schema"] = sup6000.get("schema")
    result["compat_source"] = "SUPERVISOR_6000.json"
    result["supervisor_running"] = bool(supervisor_running)
    result["go_swarm_running"] = bool(fabric_running)
    result["local_research_model_ready"] = bool(local_ready)
    result["local_model_ready"] = bool(local_ready)
    result["provider_admission_runtime"] = sup6000.get("provider_admission")
    result["provider_admission"] = canonical
    result["policy"] = (
        "FREE_ONLY; CREDENTIAL_BLIND_CONTROL_PARENT; SWARM_CHILD_ONLY_SECRET_SCOPE; "
        "CURRENT_CANONICAL_PROVIDER_ADMISSION; NO_PAID_FALLBACK; TOGETHER_FORBIDDEN"
    )
    result["observed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return result


def classify_authority(
    canonical: dict[str, Any],
    runtime_admission: dict[str, Any],
    manifest: dict[str, Any],
    *,
    supervisor_running: bool,
    fabric_running: bool,
) -> dict[str, Any]:
    canonical_epoch = str(canonical.get("authority_epoch") or "") if canonical.get("ok") else ""
    runtime_epoch = str(runtime_admission.get("authority_epoch") or "") if runtime_admission else ""
    fabric_epoch = str(manifest.get("provider_admission_epoch") or "") if manifest else ""
    if not canonical.get("ok"):
        state = "CANONICAL_ADMISSION_INVALID_FAIL_CLOSED"
    elif not supervisor_running:
        state = "SUPERVISOR_NOT_RUNNING"
    elif runtime_epoch and runtime_epoch != canonical_epoch:
        state = "SUPERVISOR_RUNTIME_ADMISSION_STALE"
    elif fabric_running and fabric_epoch and fabric_epoch != canonical_epoch:
        state = "FABRIC_RESTART_REQUIRED_ADMISSION_EPOCH_STALE"
    elif fabric_running and not fabric_epoch:
        state = "FABRIC_MANIFEST_EPOCH_UNBOUND"
    else:
        state = "ALIGNED" if runtime_epoch == canonical_epoch else "SUPERVISOR_STATUS_PENDING_CURRENT_EPOCH"
    return {
        "state": state,
        "canonical_epoch": canonical_epoch or None,
        "runtime_supervisor_epoch": runtime_epoch or None,
        "fabric_manifest_epoch": fabric_epoch or None,
        "canonical_admission_ok": bool(canonical.get("ok")),
    }


def terminate_stale_fabric_if_needed(authority: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if authority.get("state") != "FABRIC_RESTART_REQUIRED_ADMISSION_EPOCH_STALE":
        return actions
    for pid in matching_pids("run_6000_free_swarm_fast.py"):
        try:
            os.kill(pid, signal.SIGTERM)
            actions.append({"action": "TERM_STALE_FABRIC", "pid": pid, "reason": authority.get("state")})
        except (ProcessLookupError, PermissionError) as exc:
            actions.append({"action": "TERM_STALE_FABRIC_FAILED", "pid": pid, "error": type(exc).__name__})
    return actions


def start_local_model_if_needed(repo: Path, artifacts: Path, *, healthy: bool, bootstrapping: bool) -> list[dict[str, Any]]:
    if healthy or bootstrapping:
        return []
    launcher = repo / "tools/local_research_model_server.sh"
    if not launcher.is_file():
        return [{"action": "LOCAL_MODEL_START_SKIPPED", "reason": "LAUNCHER_MISSING"}]
    log = artifacts / "local-model-bootstrap.log"
    artifacts.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["CLAY_LOCAL_RESEARCH_STATE_DIR"] = str(artifacts)
    cache = Path("/cache/clay-local-research-model")
    if Path("/cache").exists() and os.access("/cache", os.W_OK):
        env.setdefault("CLAY_LOCAL_MODEL_CACHE", str(cache))
    try:
        with log.open("ab", buffering=0) as out:
            process = subprocess.Popen(
                ["bash", str(launcher)], cwd=repo, env=env,
                stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        (artifacts / "local-model-bootstrap.pid").write_text(str(process.pid) + "\n", encoding="utf-8")
        return [{"action": "LOCAL_MODEL_BOOTSTRAP_STARTED", "pid": process.pid, "state_dir": str(artifacts)}]
    except Exception as exc:
        return [{"action": "LOCAL_MODEL_BOOTSTRAP_FAILED", "error": f"{type(exc).__name__}:{str(exc)[:300]}"}]


def patch_readme_runtime(readme: Path, truth: dict[str, Any]) -> None:
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    runtime = truth["runtime"]
    authority = runtime["authority_alignment"]
    rewritten: list[str] = []
    inserted = False
    for line in lines:
        if line.startswith("| **24h Supervisor**") or line.startswith("| **6000 Supervisor**"):
            rewritten.append(
                f"| **6000 Supervisor** `run_6000_free_swarm_supervisor.sh` | hält Fabric/Distillery/Forge/Dashboard/Local-Model am Leben und reconciled FREE_ONLY authority | {runtime['supervisor']} | authority `{authority['state']}`; canonical epoch `{authority.get('canonical_epoch') or 'UNKNOWN'}` |"
            )
            continue
        if line.startswith("| **GO Free Swarm**"):
            rewritten.append(
                f"| **GO Free Swarm** `run_6000_free_swarm_fast.py` | global work-stealing architecture/code/falsification organs | {runtime['go_swarm']} | 6000 logical organs; external calls remain route/credential FREE-gated |"
            )
            continue
        if line.startswith("| **Local 4B lane**"):
            rewritten.append(
                f"| **Local 4B lane** `local_research_model_server.sh` | provider-independent local synthesis/pre-filter | {runtime['local_model']} | direct loopback health; bootstrap `{runtime['local_model_bootstrap']}` |"
            )
            continue
        rewritten.append(line)
        if line.strip() == "### 3. Script-by-Script — live" and not inserted:
            rewritten.append(
                f"Runtime authority alignment: **{authority['state']}** — canonical `{authority.get('canonical_epoch') or 'UNKNOWN'}`, supervisor `{authority.get('runtime_supervisor_epoch') or 'PENDING'}`, fabric `{authority.get('fabric_manifest_epoch') or 'PENDING'}`."
            )
            inserted = True
    readme.write_text("\n".join(rewritten).rstrip() + "\n", encoding="utf-8")


def run_legacy_system_analysis(repo: Path, artifacts: Path) -> dict[str, Any]:
    script = repo / "free swarm/update_system_analysis.py"
    if not script.is_file():
        return {"ran": False, "reason": "SCRIPT_MISSING"}
    try:
        p = subprocess.run(
            [sys.executable, str(script), "--repo", str(repo), "--artifacts", str(artifacts)],
            cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=60, check=False,
        )
        return {"ran": True, "returncode": p.returncode, "stdout_tail": p.stdout[-500:], "stderr_tail": p.stderr[-500:]}
    except Exception as exc:
        return {"ran": False, "reason": f"{type(exc).__name__}:{str(exc)[:300]}"}


def reconcile(repo: Path, artifacts: Path, *, mutate_processes: bool = True) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc)
    sup6000 = load_json(artifacts / "SUPERVISOR_6000.json")
    legacy = load_json(artifacts / "SUPERVISOR.json")
    canonical = canonical_admission(repo)
    manifest = latest_fabric_manifest(artifacts)
    fabric_status = latest_fabric_status(artifacts)

    supervisor_pids = matching_pids("run_6000_free_swarm_supervisor.sh")
    fabric_pids = matching_pids("run_6000_free_swarm_fast.py")
    dist_running = proc_has("run_research_distillery_local.py", "run_research_distillery_entry.py")
    forge_running = proc_has("run_free_evidence_forge.py")
    dashboard_running = proc_has("free swarm/evaluate.py", "update_fabric_live.py")
    supervisor_age = age_seconds(sup6000, now)
    supervisor_fresh = supervisor_age is not None and supervisor_age <= FRESH_SUPERVISOR_SECONDS
    supervisor_running = bool(supervisor_pids) or supervisor_fresh
    fabric_running = bool(fabric_pids) or bool(supervisor_fresh and sup6000.get("fabric_running"))

    direct_local_ready = loopback_health()
    local_bootstrapping = proc_has("local_research_model_server.sh", "cmake --build")
    local_state, local_state_path = newest_local_model_state(artifacts)

    runtime_admission = sup6000.get("provider_admission") if isinstance(sup6000.get("provider_admission"), dict) else {}
    authority = classify_authority(
        canonical, runtime_admission, manifest,
        supervisor_running=supervisor_running, fabric_running=fabric_running,
    )

    actions: list[dict[str, Any]] = []
    if mutate_processes:
        actions.extend(terminate_stale_fabric_if_needed(authority))
        local_bootstrapping = proc_has("local_research_model_server.sh", "cmake --build")
        actions.extend(start_local_model_if_needed(repo, artifacts, healthy=direct_local_ready, bootstrapping=local_bootstrapping))

    compat_source = sup6000 or legacy
    compat = compatibility_supervisor(
        compat_source, canonical,
        supervisor_running=supervisor_running,
        fabric_running=fabric_running,
        local_ready=direct_local_ready,
    )
    compat["runtime_authority_alignment"] = authority
    compat["runtime_reconciliation_actions"] = actions
    atomic_json(artifacts / "SUPERVISOR.json", compat)

    legacy_publish = run_legacy_system_analysis(repo, artifacts)
    system_path = repo / "free swarm/SYSTEM_ANALYSIS_LIVE.json"
    system = load_json(system_path)

    if direct_local_ready:
        local_label = "READY"
    elif local_bootstrapping or any(x.get("action") == "LOCAL_MODEL_BOOTSTRAP_STARTED" for x in actions):
        local_label = "BUILDING/BOOTSTRAPPING"
    elif local_state.get("state"):
        local_label = f"NOT_READY:{local_state.get('state')}"
    else:
        local_label = "NOT_READY:NO_RUNTIME_OR_STATE"

    runtime = system.get("runtime") if isinstance(system.get("runtime"), dict) else {}
    runtime.update({
        "supervisor": "RUNNING" if supervisor_running else "STOPPED/QUARANTINED",
        "go_swarm": "RUNNING" if fabric_running else "STOPPED/QUARANTINED",
        "distillery": "RUNNING" if dist_running or bool(sup6000.get("distillery_running")) else "STOPPED/QUARANTINED",
        "evidence_forge": "RUNNING" if forge_running or bool(sup6000.get("forge_running")) else "STOPPED/QUARANTINED",
        "dashboard": "RUNNING" if dashboard_running or bool(sup6000.get("dashboard_running")) else "STOPPED/QUARANTINED",
        "local_model": local_label,
        "local_model_bootstrap": "ACTIVE" if local_bootstrapping else "IDLE",
        "local_model_state_path": local_state_path,
        "local_model_state": local_state,
        "provider_admission": canonical,
        "provider_admission_runtime": runtime_admission or None,
        "authority_alignment": authority,
        "runtime_truth_source": "SUPERVISOR_6000_PLUS_DIRECT_PROCESS_LOOPBACK_PLUS_CANONICAL_ADMISSION",
        "supervisor_snapshot_age_seconds": supervisor_age,
        "supervisor_snapshot_fresh": supervisor_fresh,
        "supervisor_pids": supervisor_pids,
        "fabric_pids": fabric_pids,
        "fabric_run_manifest": {
            "run_id": manifest.get("run_id"),
            "repo_head": manifest.get("repo_head"),
            "provider_admission_epoch": manifest.get("provider_admission_epoch"),
        },
        "fabric_status_schema": fabric_status.get("schema"),
        "policy": compat.get("policy"),
    })
    system["runtime"] = runtime
    system["runtime_reconciliation"] = {
        "schema": RUNTIME_SCHEMA,
        "generated_at": now.isoformat(),
        "repo_head": git_head(repo),
        "actions": actions,
        "legacy_system_analysis": legacy_publish,
        "evidence_boundary": "RUNTIME_HEALTH_AND_AUTHORITY_ALIGNMENT_ONLY; DOES_NOT_MINT_PROVIDER_HCU_JSPACE_OR_TRAINING_CREDIT",
    }
    if system:
        atomic_json(system_path, system)
        patch_readme_runtime(repo / "free swarm/README.md", system)

    receipt = {
        "schema": RUNTIME_SCHEMA,
        "generated_at": now.isoformat(),
        "repo_head": git_head(repo),
        "runtime": runtime,
        "actions": actions,
        "legacy_system_analysis": legacy_publish,
    }
    atomic_json(artifacts / "RUNTIME_RECONCILIATION.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="/workspace/clay-global-research-entity")
    parser.add_argument("--artifacts", default="/artifacts/clay-entityos-swarm")
    parser.add_argument("--no-process-mutations", action="store_true")
    args = parser.parse_args()
    result = reconcile(Path(args.repo).resolve(), Path(args.artifacts).resolve(), mutate_processes=not args.no_process_mutations)
    print(json.dumps({
        "schema": result.get("schema"),
        "generated_at": result.get("generated_at"),
        "authority_alignment": ((result.get("runtime") or {}).get("authority_alignment") or {}).get("state"),
        "supervisor": (result.get("runtime") or {}).get("supervisor"),
        "go_swarm": (result.get("runtime") or {}).get("go_swarm"),
        "local_model": (result.get("runtime") or {}).get("local_model"),
        "actions": result.get("actions"),
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
