#!/usr/bin/env python3
"""Launch exactly ten distinct Trigger-1 J-Space research experiments in parallel.

The orchestrator is credential-blind. Each external-provider lane is materialized
through the repository vault wrapper only in the child that performs provider
work. All children share one cross-process provider-budget SQLite database, so
parallel research diversity cannot bypass provider limits or cooldowns.
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

EXPERIMENTS = (
    ("runtime_surface", "Find or implement the shortest actually instrumentable FREE model execution surface. Distinguish hosted text inference from real hidden-state/native-cvec intervention and produce an executable discriminator."),
    ("adapter_identity", "Close exact identity from JSPACE_VECTOR_CONTROL_ABI/v1 source packet through model/version-specific JSPACE_LATENT_BASIS_ADAPTER/v1 to the local control vector. Detect any dimension/model/tokenizer/build mismatch before execution."),
    ("layer_localization", "Design/execute calibration-split-only layer or layer-range localization for the vector intervention. Freeze the selected range before holdout and emit exact selection evidence."),
    ("gain_calibration", "Design/execute signed gain/alpha calibration only on the calibration split. Freeze gain before holdout; reject unstable or monotonic-energy-only effects."),
    ("sign_flip_control", "Test directional causality with +VECTOR versus SIGN_FLIP on fixed seeds. Require a directional gap rather than generic response variance."),
    ("null_control", "Test exact NULL_VECTOR against BASELINE and bound drift. Any substantial null drift invalidates steering attribution and must become a blocker/delta."),
    ("orthogonal_control", "Test same-norm orthogonal vector control to reject generic activation magnitude or perturbation-energy explanations."),
    ("permuted_control", "Test same-norm coordinate-permuted control to reject coordinate-insensitive or norm-only effects."),
    ("seed_holdout_reproduction", "Evaluate frozen layer/gain on disjoint holdout across fixed seeds. Quantify effect direction, variance, replication rate and strongest counterexample."),
    ("receipt_chain_and_delta_forge", "Bind exact model/checkpoint/tokenizer/runtime/build/source-packet/adapter/local-vector/native-cvec or hook/execution identities. Convert positive or negative evidence into the smallest executable repo delta and falsifier."),
)

_SECRET_NAME = re.compile(r"^(?:GROQ|MISTRAL|NVIDIA|NGC|OPENROUTER|TOGETHER).*KEY.*$")


def git_text(*args: str) -> str:
    try:
        p = subprocess.run(["git", "-C", str(ROOT), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
        return p.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def scrub_parent_provider_secrets() -> None:
    """Keep the Trigger-1 orchestration process credential-blind."""
    for name in list(os.environ):
        if _SECRET_NAME.match(name):
            os.environ.pop(name, None)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the exact ten-lane Trigger-1 J-Space research batch")
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
        raise SystemExit("Trigger-1 contract requires exactly ten unique experiment lanes")
    if args.minutes <= 0 or args.logical_workers_per_lane <= 0:
        raise SystemExit("minutes and logical-workers-per-lane must be positive")
    if not VAULT_EXEC.is_file() or not LANE_EXEC.is_file():
        raise SystemExit("Trigger-1 vault or lane executable missing")

    # Do this before constructing child environments. The vault wrapper, not this
    # orchestration process, is the only code allowed to materialize candidate
    # provider credentials for each external-provider lane.
    scrub_parent_provider_secrets()

    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    nonce = uuid.uuid4().hex
    contract_payload = json.dumps(EXPERIMENTS, ensure_ascii=False, separators=(",", ":"))
    contract_sha = hashlib.sha256(contract_payload.encode("utf-8")).hexdigest()
    batch_material = json.dumps({"started_at": started, "repo_head": head, "repo_tree": tree, "nonce": nonce, "contract_sha256": contract_sha}, sort_keys=True, separators=(",", ":"))
    batch_digest = hashlib.sha256(batch_material.encode("utf-8")).hexdigest()
    batch_id = f"trigger1_{batch_digest}"

    artifact_root = Path(args.artifact_root)
    artifact_root.mkdir(parents=True, exist_ok=True)
    batch_dir = artifact_root / batch_id
    batch_dir.mkdir(parents=False, exist_ok=False)

    budget_db = Path(os.getenv("CLAY_FREE_PROVIDER_BUDGET_DB", str(DEFAULT_BUDGET_DB)))
    common_env = dict(os.environ)
    common_env["CLAY_FREE_PROVIDER_BUDGET_DB"] = str(budget_db)
    common_env["CLAY_TRIGGER1_BATCH_ID"] = batch_id
    common_env["CLAY_TRIGGER1_RESEARCH_CONTINGENT"] = "OWNER_AUTHORIZED_FREE_ONLY"
    common_env["CLAY_PROVIDER_CREDENTIAL_SCOPE"] = "SWARM_CHILD_ONLY/v1"

    lane_rows = []
    for idx, (name, focus) in enumerate(EXPERIMENTS):
        lane_material = f"{batch_id}\n{idx}\n{name}\n{contract_sha}".encode("utf-8")
        lane_id = hashlib.sha256(lane_material).hexdigest()
        lane_rows.append({"lane_index": idx, "experiment_name": name, "experiment_id": lane_id, "focus": focus})

    manifest = {
        "schema": "CLAY_TRIGGER1_JSPACE_10X_BATCH/v1",
        "batch_id": batch_id,
        "batch_identity_sha256": batch_digest,
        "started_at": started,
        "repo_head": head,
        "repo_tree": tree,
        "contract_sha256": contract_sha,
        "parallel_experiments": 10,
        "logical_workers_per_lane": args.logical_workers_per_lane,
        "configured_logical_workers_total": 10 * args.logical_workers_per_lane,
        "minutes": args.minutes,
        "max_tokens_per_model_call": args.max_tokens,
        "free_only": True,
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

    # Create all subprocess tasks before awaiting results: ten distinct hypotheses
    # overlap in wall-clock time while each provider-capable process is vault-
    # isolated and all calls share the one provider quota database.
    tasks = [
        asyncio.create_task(run_child(batch_id, row["lane_index"], row["experiment_name"], row["focus"], row["experiment_id"], args, batch_dir, common_env))
        for row in lane_rows
    ]
    results = await asyncio.gather(*tasks)
    finished = dt.datetime.now(dt.timezone.utc).isoformat()
    promotion = scan_batch(batch_dir)
    final = {
        "schema": "CLAY_TRIGGER1_JSPACE_10X_FINAL/v1",
        "batch_id": batch_id,
        "finished_at": finished,
        "parallel_experiments": 10,
        "successful_processes": sum(1 for r in results if r["exit_code"] == 0),
        "failed_processes": sum(1 for r in results if r["exit_code"] != 0),
        "results": results,
        "promotion_gate": promotion,
        "mechanism_runtime_vector_credit_candidate": bool(
            promotion["mechanism_runtime_vector_credit_candidate"]
        ),
        "direct_model_steering_credit": bool(
            promotion["owner_trigger1_direct_free_api_model_credit_candidate"]
        ),
        "direct_model_steering_credit_rule": (
            "Exact admitted FREE API-model runtime + runtime-observed internal vector intervention + "
            "six matched controls + disjoint fixed-seed holdout. Process exit zero, hosted prompting, "
            "model agreement, token volume, and local surrogate steering are insufficient."
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
