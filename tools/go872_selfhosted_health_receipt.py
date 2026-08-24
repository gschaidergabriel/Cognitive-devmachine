#!/usr/bin/env python3
"""Emit a sanitized exact-source health receipt for Clay self-hosted execution lanes.

This probe is intentionally non-experimental: it observes runner/source/resource readiness
for the current Forge->Distillery and local Qwen3-0.6B gates without invoking a model,
provider, effect path, or unusual intervention.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_GO872_SELFHOSTED_HEALTH_RECEIPT/v1"
QWEN_MIN_AVAILABLE_KB = 3_000_000
PROVIDER_ENV_PREFIXES = (
    "OPENAI", "ANTHROPIC", "GROQ", "MISTRAL", "NVIDIA", "NGC",
    "OPENROUTER", "TOGETHER",
)
PROVIDER_ENV_EXACT = {"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"}


def run_text(args: list[str], cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def available_kb(path: Path) -> int:
    return int(shutil.disk_usage(path).free // 1024)


def meminfo() -> dict[str, int | None]:
    vals: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, rest = line.split(":", 1)
            vals[key] = int(rest.strip().split()[0]) * 1024
    except Exception:
        return {"mem_total_bytes": None, "mem_available_bytes": None}
    return {"mem_total_bytes": vals.get("MemTotal"), "mem_available_bytes": vals.get("MemAvailable")}


def provider_env_names(env: dict[str, str]) -> list[str]:
    names: list[str] = []
    for name in env:
        upper = name.upper()
        if upper in PROVIDER_ENV_EXACT or ("KEY" in upper and upper.startswith(PROVIDER_ENV_PREFIXES)):
            names.append(name)
    return sorted(set(names))


def build_receipt(repo: Path, output: Path) -> dict[str, Any]:
    repo = repo.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    sha_rc, source_sha, sha_err = run_text(["git", "rev-parse", "HEAD"], repo)
    tree_rc, source_tree, tree_err = run_text(["git", "rev-parse", "HEAD^{tree}"], repo)
    status_rc, dirty_text, status_err = run_text(["git", "status", "--porcelain=v1"], repo)
    disk_kb = available_kb(repo)
    runner_os = os.environ.get("RUNNER_OS") or platform.system()
    runner_arch = os.environ.get("RUNNER_ARCH") or platform.machine()
    runner_name = os.environ.get("RUNNER_NAME") or "unknown"
    qwen_launcher = repo / "tools" / "trigger1_local_qwen06_midlayer_causal.sh"
    qwen_executor = repo / "tools" / "trigger1_local_qwen06_midlayer_causal_execute.py"
    forge_gate = repo / "tools" / "run_go871_forge_distillery_runtime_gate.py"
    git_ok = sha_rc == 0 and tree_rc == 0 and status_rc == 0 and bool(source_sha) and bool(source_tree)
    source_clean = status_rc == 0 and dirty_text == ""
    linux_x64 = runner_os.lower() == "linux" and runner_arch.lower() in {"x64", "x86_64", "amd64"}
    qwen_disk_ready = disk_kb >= QWEN_MIN_AVAILABLE_KB
    qwen_source_ready = qwen_launcher.is_file() and qwen_executor.is_file()
    forge_source_ready = forge_gate.is_file()
    bwrap_path = shutil.which("bwrap")
    python_path = shutil.which("python3")
    bash_path = shutil.which("bash")
    bridge_health_pass = bool(git_ok and source_clean and linux_x64 and python_path and bash_path)
    qwen_preflight_ready = bool(bridge_health_pass and qwen_disk_ready and qwen_source_ready)
    forge_preflight_ready = bool(bridge_health_pass and forge_source_ready and bwrap_path)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "authority_epoch_expected": "8.72",
        "execution_mode": "FREE_ONLY",
        "probe_class": "ORDINARY_NON_EXPERIMENTAL_SELFHOSTED_HEALTH_OBSERVATION",
        "source": {
            "repository": "gschaidergabriel/clay-global-research-entity",
            "source_sha": source_sha or None,
            "source_tree": source_tree or None,
            "git_identity_ok": git_ok,
            "source_clean": source_clean,
            "git_errors": {
                "sha": sha_err[-500:] if sha_err else None,
                "tree": tree_err[-500:] if tree_err else None,
                "status": status_err[-500:] if status_err else None,
            },
        },
        "runner": {
            "name": runner_name,
            "os": runner_os,
            "arch": runner_arch,
            "linux_x64": linux_x64,
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "github_event_name": os.environ.get("GITHUB_EVENT_NAME"),
        },
        "resources": {
            "available_kb": disk_kb,
            "qwen_min_available_kb": QWEN_MIN_AVAILABLE_KB,
            "qwen_disk_ready": qwen_disk_ready,
            **meminfo(),
        },
        "tools": {
            "python3_present": bool(python_path),
            "bash_present": bool(bash_path),
            "bwrap_present": bool(bwrap_path),
        },
        "frontier_sources": {
            "qwen_launcher_present": qwen_launcher.is_file(),
            "qwen_executor_present": qwen_executor.is_file(),
            "forge_gate_present": forge_gate.is_file(),
        },
        "credential_fence_observation": {
            "provider_credential_environment_names_present": provider_env_names(dict(os.environ)),
            "secret_values_recorded": False,
            "scope": "NAMES_ONLY_OBSERVATION; downstream experiment/workflow must still scrub provider credentials before child execution",
        },
        "readiness": {
            "bridge_health_pass": bridge_health_pass,
            "qwen_preflight_ready": qwen_preflight_ready,
            "forge_preflight_ready": forge_preflight_ready,
            "current_frontier_any_lane_ready": qwen_preflight_ready or forge_preflight_ready,
        },
        "credit": {
            "runtime_credit_minted": 0,
            "entityos_whole_credit": 0,
            "hcu_full_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
        },
        "scope_guard": "This receipt proves only exact-source self-hosted health/readiness observations. It does not prove Forge->Distillery success, model execution, J-Space causality, training readiness, or whole-product PASS.",
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    payload = build_receipt(Path(args.repo), Path(args.output))
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["readiness"]["bridge_health_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
