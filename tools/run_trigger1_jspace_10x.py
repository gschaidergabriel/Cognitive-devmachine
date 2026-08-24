#!/usr/bin/env python3
"""Launch ten dynamically reallocatable Trigger-1 V2 convergence slots.

The primary local API experiment is attempted by trigger1_jspace_research.sh before
this runner. These slots exist to repair or route around the exact remaining blocker,
not to preserve ten fixed hypotheses. External-provider children stay vault-isolated
and share one quota database; provider availability never gates the local primary path.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from trigger1_jspace_promotion_gate import scan_batch

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOT = Path("/artifacts/clay-entityos-trigger1")
DEFAULT_BUDGET_DB = Path("/artifacts/clay-entityos-swarm/provider_budget.sqlite3")
VAULT_EXEC = ROOT / "tools/free_swarm_exec_with_vault.py"
LANE_EXEC = ROOT / "tools/run_trigger1_jspace_lane.py"

# Ten work slots remain for parallelism/identity, but their contract is now explicitly
# reallocatable toward the highest-information unblocked dependency.
EXPERIMENTS = (
    ("local_runtime_repair", "Repair or simplify the exact zero-cost local Qwen3-0.6B execution surface. If the local fast path already runs, reallocate immediately to its next failing gate."),
    ("vector_adapter_repair", "Close the shortest exact source-packet -> model-specific vector/adapter path for the local runtime. Prefer executable code and exact byte identities over architecture prose."),
    ("layer_calibration", "Close calibration-only activation-site/layer selection. Never inspect holdout while choosing the site; if already closed, move to the highest remaining local blocker."),
    ("gain_calibration", "Close calibration-only signed gain selection and reject generic-energy explanations. If already closed, move to the highest remaining local blocker."),
    ("matched_controls", "Ensure BASELINE, +VECTOR, SIGN_FLIP, NULL_VECTOR, ORTHOGONAL_SAME_NORM and PERMUTED_SAME_NORM all execute on the exact same runtime identity."),
    ("holdout_reproduction", "Run or repair disjoint fixed-seed holdout reproduction and record the strongest counterexample. Do not weaken the directional-effect criterion."),
    ("runtime_identity_receipts", "Bind exact repo/runtime/model/tokenizer/source-packet/adapter/vector/applied-intervention/API-execution receipts. Repair missing identity rather than blocking on a provider."),
    ("local_api_boundary", "Make the exact intervention-capable runtime callable through loopback-only API transport and bind that API execution to the same runtime/model bytes."),
    ("hosted_replication", "Use admitted FREE hosted routes only as optional independent component evidence. Never let credential, entitlement, rate-limit, route or parameter blockers gate local completion."),
    ("blocker_killer_and_forge", "Classify the current blocker as REPAIR_NOW, ROUTE_AROUND, EXTERNAL_TRANSIENT, SCIENTIFIC_NEGATIVE or HARD_AUTHORITY_BOUNDARY; execute the smallest authorized elimination and emit a Forge-ready delta."),
)

_SECRET_NAME = re.compile(r"^(?:GROQ|MISTRAL|NVIDIA|NGC|OPENROUTER|TOGETHER).*KEY.*$")


def git_text(*args: str) -> str:
    try:
        p = subprocess.run(["git", "-C", str(ROOT), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
        return p.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def scrub_parent_provider_secrets() -> None:
    for name in list(os.environ):
        if _SECRET_NAME.match(name):
            os.environ.pop(name, None)


def local_fastpath_state() -> dict:
    raw = os.getenv("CLAY_TRIGGER1_LOCAL_FASTPATH_RESULT", "").strip()
    if not raw:
        return {"status": "NOT_ATTEMPTED_OR_PATH_NOT_EXPORTED"}
    path = Path(raw)
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            return {
                "path": str(path),
                "status": obj.get("status"),
                "reason": obj.get("reason"),
                "verdict": obj.get("verdict"),
                "selected_gain": obj.get("selected_gain"),
                "result_sha256": obj.get("result_sha256"),
            }
    except Exception as exc:
        return {"path": str(path), "status": "UNREADABLE", "reason": type(exc).__name__}
    return {"path": str(path), "status": "INVALID_OBJECT"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run ten dynamically reallocatable Trigger-1 V2 convergence slots")
    p.add_argument("--minutes", type=float, default=float(os.getenv("CLAY_TRIGGER1_MINUTES", "12")))
    p.add_argument("--logical-workers-per-lane", type=int, default=int(os.getenv("CLAY_TRIGGER1_LOGICAL_WORKERS_PER_LANE", "64")))
    p.add_argument("--max-tokens", type=int, default=int(os.getenv("CLAY_TRIGGER1_MAX_TOKENS", "1000")))
    p.add_argument("--context-chars", type=int, default=int(os.getenv("CLAY_TRIGGER1_CONTEXT_CHARS", "14000")))
    p.add_argument("--timeout", type=float, default=float(os.getenv("CLAY_TRIGGER1_TIMEOUT", "150")))
    p.add_argument("--drain-seconds", type=float, default=float(os.getenv("CLAY_TRIGGER1_DRAIN_SECONDS", "180")))
    p.add_argument("--artifact-root", default=os.getenv("CLAY_TRIGGER1_ARTIFACT_ROOT", str(DEFAULT_ARTIFACT_ROOT)))
    return p.parse_args()


async def run_child(batch_id: str, lane_index: int, name: str, focus: str, lane_id: str, args: argparse.Namespace, batch_dir: Path, common_env: dict[str, str]) -> dict:
    lane_dir = batch_dir / f"{lane_index:02d}_{name}_{lane_id[:12]}"
    lane_dir.mkdir(parents=True, exist_ok=False)
    cmd = [
        sys.executable, str(VAULT_EXEC),
        sys.executable, str(LANE_EXEC),
        "--batch-id", batch_id,
        "--lane-index", str(lane_index),
        "--experiment-id", lane_id,
        "--experiment-name", name,
        "--focus", focus,
        "--minutes", str(args.minutes),
        "--logical-workers", str(args.logical_workers_per_lane),
        "--max-tokens", str(args.max_tokens),
        "--context-chars", str(args.context_chars),
        "--timeout", str(args.timeout),
        "--drain-seconds", str(args.drain_seconds),
        "--output-dir", str(lane_dir),
    ]
    child_env = dict(common_env)
    child_env["CLAY_TRIGGER1_EXPERIMENT_ID"] = lane_id
    child_env["CLAY_PROVIDER_CREDENTIAL_SCOPE"] = "SWARM_CHILD_ONLY/v1"
    log_path = lane_dir / "launcher.log"
    with log_path.open("wb") as log:
        proc = await asyncio.create_subprocess_exec(*cmd, cwd=str(ROOT), env=child_env, stdout=log, stderr=asyncio.subprocess.STDOUT)
        rc = await proc.wait()
    return {
        "lane_index": lane_index,
        "experiment_name": name,
        "experiment_id": lane_id,
        "exit_code": rc,
        "artifact_dir": str(lane_dir),
        "launcher_log": str(log_path),
    }


async def amain() -> int:
    args = parse_args()
    if len(EXPERIMENTS) != 10 or len({x[0] for x in EXPERIMENTS}) != 10:
        raise SystemExit("Trigger-1 V2 requires exactly ten unique work-slot identities")
    if args.minutes <= 0 or args.logical_workers_per_lane <= 0:
        raise SystemExit("minutes and logical-workers-per-lane must be positive")
    if not VAULT_EXEC.is_file() or not LANE_EXEC.is_file():
        raise SystemExit("Trigger-1 vault or lane executable missing")

    scrub_parent_provider_secrets()

    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    nonce = uuid.uuid4().hex
    fastpath = local_fastpath_state()
    contract_payload = json.dumps(EXPERIMENTS, ensure_ascii=False, separators=(",", ":"))
    contract_sha = hashlib.sha256(contract_payload.encode("utf-8")).hexdigest()
    batch_material = json.dumps({"started_at": started, "repo_head": head, "repo_tree": tree, "nonce": nonce, "contract_sha256": contract_sha, "local_fastpath": fastpath}, sort_keys=True, separators=(",", ":"))
    batch_digest = hashlib.sha256(batch_material.encode("utf-8")).hexdigest()
    batch_id = f"trigger1v2_{batch_digest}"

    artifact_root = Path(args.artifact_root)
    try:
        artifact_root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        artifact_root = Path(os.getenv("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "clay-entityos-trigger1"
        artifact_root.mkdir(parents=True, exist_ok=True)
    batch_dir = artifact_root / batch_id
    batch_dir.mkdir(parents=False, exist_ok=False)

    budget_db = Path(os.getenv("CLAY_FREE_PROVIDER_BUDGET_DB", str(DEFAULT_BUDGET_DB)))
    common_env = dict(os.environ)
    common_env["CLAY_FREE_PROVIDER_BUDGET_DB"] = str(budget_db)
    common_env["CLAY_TRIGGER1_BATCH_ID"] = batch_id
    common_env["CLAY_TRIGGER1_RESEARCH_CONTINGENT"] = "OWNER_AUTHORIZED_ZERO_COST"
    common_env["CLAY_PROVIDER_CREDENTIAL_SCOPE"] = "SWARM_CHILD_ONLY/v1"
    common_env["CLAY_TRIGGER1_LOCAL_FASTPATH_STATE_JSON"] = json.dumps(fastpath, separators=(",", ":"), ensure_ascii=False)

    lane_rows = []
    fast_context = f"Current provider-independent local fast-path state: {json.dumps(fastpath, ensure_ascii=False)}. "
    for idx, (name, focus) in enumerate(EXPERIMENTS):
        effective_focus = fast_context + focus + " If this focus is already satisfied, reallocate this slot to the highest-information remaining blocker instead of returning NO_CHANGE."
        lane_material = f"{batch_id}\n{idx}\n{name}\n{contract_sha}".encode("utf-8")
        lane_id = hashlib.sha256(lane_material).hexdigest()
        lane_rows.append({"lane_index": idx, "experiment_name": name, "experiment_id": lane_id, "focus": effective_focus})

    manifest = {
        "schema": "CLAY_TRIGGER1_JSPACE_10X_BATCH/v2",
        "batch_id": batch_id,
        "batch_identity_sha256": batch_digest,
        "started_at": started,
        "repo_head": head,
        "repo_tree": tree,
        "contract_sha256": contract_sha,
        "work_slots": 10,
        "slots_dynamically_reallocatable": True,
        "local_fastpath": fastpath,
        "logical_workers_per_lane": args.logical_workers_per_lane,
        "configured_logical_workers_total": 10 * args.logical_workers_per_lane,
        "minutes": args.minutes,
        "max_tokens_per_model_call": args.max_tokens,
        "zero_cost_only": True,
        "orchestrator_credential_scope": "BLIND",
        "provider_lane_credential_scope": "SWARM_CHILD_ONLY/v1",
        "vault_credentials_child_only_and_not_logged": True,
        "shared_provider_budget_db": str(budget_db),
        "shared_quota_gate_required": True,
        "credential_rotation_to_evade_limits": False,
        "together": "FORBIDDEN",
        "paid_or_unknown_cost": "FAIL_CLOSED",
        "lanes": lane_rows,
    }
    (batch_dir / "batch_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tasks = [
        asyncio.create_task(run_child(batch_id, row["lane_index"], row["experiment_name"], row["focus"], row["experiment_id"], args, batch_dir, common_env))
        for row in lane_rows
    ]
    results = await asyncio.gather(*tasks)
    finished = dt.datetime.now(dt.timezone.utc).isoformat()
    promotion = scan_batch(batch_dir)
    final = {
        "schema": "CLAY_TRIGGER1_JSPACE_10X_FINAL/v2",
        "batch_id": batch_id,
        "finished_at": finished,
        "work_slots": 10,
        "slots_dynamically_reallocatable": True,
        "local_fastpath": fastpath,
        "successful_processes": sum(1 for r in results if r["exit_code"] == 0),
        "failed_processes": sum(1 for r in results if r["exit_code"] != 0),
        "results": results,
        "promotion_gate": promotion,
        "mechanism_runtime_vector_credit_candidate": bool(promotion["mechanism_runtime_vector_credit_candidate"]),
        "trigger1_goal_credit_candidate": bool(promotion.get("owner_trigger1_goal_credit_candidate")),
        "direct_model_steering_credit": bool(promotion["owner_trigger1_direct_free_api_model_credit_candidate"]),
        "direct_model_steering_credit_rule": (
            "Exact zero-cost API-served model runtime + runtime-observed internal vector intervention + "
            "six matched controls + disjoint fixed-seed holdout. The API surface may be exact FREE external "
            "or loopback-only local. Prompting, token volume and provider availability are insufficient."
        ),
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
    }
    (batch_dir / "batch_final.json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(final, ensure_ascii=False), flush=True)
    return 0 if all(r["exit_code"] == 0 for r in results) else 2


def main() -> int:
    return int(asyncio.run(amain()))


if __name__ == "__main__":
    raise SystemExit(main())
