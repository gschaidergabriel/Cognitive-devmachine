#!/usr/bin/env python3
"""Exact-current Forge -> Distillery successor runtime witness.

No provider/model network execution occurs. The gate checks one exact source commit,
proves the integrated evidence-admission boundary against a deterministic ablation in
bubblewrap --unshare-all, obtains one ACCEPT from the real current safe Forge producer,
then drives the exact current Distillery bridge with (a) a nominal ACCEPT lacking
execution admission and (b) that producer-generated evidence-qualified ACCEPT twice.
Acceptance requires producer ACCEPT, nominal rejection, exactly one new packet,
nonzero dataset tokens, and zero replay token delta.

The host/source probe remains read-only. Candidate execution is delegated to the
current safe Forge validator, whose model-authored commands are bubblewrap-isolated
and may write only inside its witness-owned disposable Forge scratch children.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path("tools/ingest_forge_accepts_into_distillery.py")
FORGE_PRODUCER = Path("tools/run_go872_forge_single_candidate.py")
SAFE_FORGE = Path("tools/run_free_evidence_forge_safe_871.py")
TEST = "runtime_checks.test_forge_distillery_requires_execution_admission_871"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

import sys
sys.path.insert(0, str(ROOT / "tools"))
from forge_evidence_credit_871 import evidence_reason


def git(cwd: Path, *args: str) -> tuple[int, str, str]:
    p = subprocess.run(
        ["git", *args], cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def minimal_env() -> dict[str, str]:
    return {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/tmp",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "NO_PROXY": "*",
        "TMPDIR": "/tmp",
    }


def bwrap_prefix(cwd: Path, *, writable_workdir: bool = False) -> list[str] | None:
    bwrap = shutil.which("bwrap")
    if not bwrap:
        return None
    prefix = [
        bwrap, "--unshare-all", "--die-with-parent", "--new-session",
        "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
    ]
    for host in ("/usr", "/bin", "/lib", "/lib64", "/usr/local"):
        if Path(host).exists():
            prefix += ["--ro-bind", host, host]
    work_bind = "--bind" if writable_workdir else "--ro-bind"
    prefix += [work_bind, str(cwd.resolve()), "/work", "--chdir", "/work"]
    for key, value in minimal_env().items():
        prefix += ["--setenv", key, value]
    return prefix + ["--"]


def backend_status(cwd: Path) -> dict[str, Any]:
    prefix = bwrap_prefix(cwd, writable_workdir=False)
    if prefix is None:
        return {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
            "admitted": False,
            "backend": None,
            "reason": "BUBBLEWRAP_NOT_FOUND",
            "network_namespace": "UNAVAILABLE",
            "secret_environment_inherited": False,
            "host_secret_paths_exposed": False,
        }
    p = subprocess.run(
        prefix + ["/usr/bin/true"], cwd=cwd, env=minimal_env(), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
    )
    ok = p.returncode == 0
    return {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
        "admitted": ok,
        "backend": "bubblewrap_unshare_all",
        "reason": "OK" if ok else f"BUBBLEWRAP_PROBE_RC_{p.returncode}",
        "network_namespace": "ISOLATED" if ok else "UNAVAILABLE",
        "secret_environment_inherited": False,
        "host_secret_paths_exposed": False,
        "probe_workdir_writable": False,
        "witness_disposable_workdir_writable": True,
    }


def run_isolated(cwd: Path, command: list[str], timeout: int = 120) -> dict[str, Any]:
    prefix = bwrap_prefix(cwd, writable_workdir=True)
    if prefix is None:
        return {"rc": 126, "elapsed_s": 0.0, "stdout": "", "stderr": "NO_BUBBLEWRAP"}
    started = time.monotonic()
    try:
        p = subprocess.run(
            prefix + command, cwd=cwd, env=minimal_env(), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        )
        return {
            "rc": p.returncode,
            "elapsed_s": time.monotonic() - started,
            "stdout": p.stdout[-3000:],
            "stderr": p.stderr[-3000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "rc": 124,
            "elapsed_s": time.monotonic() - started,
            "stdout": str(exc.stdout or "")[-2000:],
            "stderr": "TIMEOUT",
        }


def clone_exact(source_sha: str, dest: Path) -> None:
    p = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", "--local", str(ROOT), str(dest)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90,
    )
    if p.returncode:
        raise RuntimeError("LOCAL_CLONE_FAILED:" + p.stderr[-500:])
    rc, _, err = git(dest, "checkout", "--quiet", "--detach", source_sha)
    if rc:
        raise RuntimeError("SOURCE_CHECKOUT_FAILED:" + err[-500:])
    rc, got, _ = git(dest, "rev-parse", "HEAD")
    if rc or got != source_sha:
        raise RuntimeError("SOURCE_IDENTITY_MISMATCH")


def ablate_admission(copy_root: Path) -> str:
    path = copy_root / TARGET
    source = path.read_text(encoding="utf-8")
    old = '''def admission_reason(row: Any) -> tuple[bool, str]:
    """Use the single current Forge evidence-credit discriminator."""
    return evidence_reason(row)
'''
    new = '''def admission_reason(row: Any) -> tuple[bool, str]:
    # Deterministic lesion used only inside the disposable runtime witness.
    ok = isinstance(row, dict) and str(row.get("status", "")).lower() == "accepted"
    return (ok, "ABLATION_NOMINAL_ACCEPT") if ok else (False, "NOT_NOMINAL_ACCEPT")
'''
    if old not in source:
        raise RuntimeError("CURRENT_ADMISSION_FUNCTION_NOT_FOUND")
    changed = source.replace(old, new, 1)
    path.write_text(changed, encoding="utf-8")
    return sha256_text(changed)


def parse_json_stdout(text: str) -> dict[str, Any]:
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise RuntimeError("JSON_RESULT_NOT_OBJECT")
    return obj


def bridge_once(root: Path, eval_path: Path, db: Path) -> dict[str, Any]:
    p = subprocess.run(
        ["python3", str(root / TARGET), "--forge-evaluations", str(eval_path), "--distillery-db", str(db)],
        cwd=root, env=minimal_env(), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
    )
    if p.returncode:
        raise RuntimeError("DISTILLERY_BRIDGE_PROCESS_FAILED:" + p.stderr[-500:])
    return parse_json_stdout(p.stdout)


def produce_forge_evaluation(
    root: Path,
    source_sha: str,
    output_path: Path,
    artifact_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    env = minimal_env()
    env["CLAY_SWARM_ARTIFACT_ROOT"] = str(artifact_root)
    started = time.monotonic()
    p = subprocess.run(
        ["python3", str(root / FORGE_PRODUCER), "--source-sha", source_sha, "--output", str(output_path)],
        cwd=root, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300,
    )
    producer = {
        "rc": p.returncode,
        "elapsed_s": time.monotonic() - started,
        "stdout": p.stdout[-3000:],
        "stderr": p.stderr[-3000:],
        "producer_path": str(FORGE_PRODUCER),
        "safe_forge_path": str(SAFE_FORGE),
        "artifact_root_scope": "WITNESS_OWNED_DISPOSABLE",
    }
    if p.returncode:
        raise RuntimeError("SAFE_FORGE_PRODUCER_FAILED:" + p.stderr[-800:] + p.stdout[-800:])
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError("SAFE_FORGE_PRODUCER_RESULT_CARDINALITY")
    return rows[0], producer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_sha = args.source_sha.strip().lower()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema": "CLAY_FORGE_DISTILLERY_EXACT_CURRENT_RUNTIME_GATE/v3",
        "authority_epoch": "8.72",
        "mode": "FREE_ONLY",
        "source_sha": source_sha,
        "network_used": False,
        "provider_calls": 0,
        "paid_fallback_attempt_count": 0,
        "whole_product_credit": 0,
        "hcu_full_credit": 0,
        "jspace_credit": 0,
        "training_credit": 0,
        "witness_write_scope": "DISPOSABLE_CURRENT_ABLATED_AND_FORGE_SCRATCH_ONLY",
        "forge_accept_origin_required": "REAL_SAFE_FORGE_VALIDATOR",
    }
    tmp: Path | None = None
    try:
        if not COMMIT_RE.fullmatch(source_sha):
            raise RuntimeError("SOURCE_SHA_INVALID")
        rc, _, err = git(ROOT, "cat-file", "-e", source_sha + "^{commit}")
        if rc:
            raise RuntimeError("SOURCE_COMMIT_UNAVAILABLE:" + err[-300:])
        rc, tree, err = git(ROOT, "rev-parse", source_sha + "^{tree}")
        if rc or not tree:
            raise RuntimeError("SOURCE_TREE_UNAVAILABLE:" + err[-300:])

        blob_ids: dict[str, str] = {}
        for material in (TARGET, FORGE_PRODUCER, SAFE_FORGE):
            rc, blob, err = git(ROOT, "rev-parse", f"{source_sha}:{material}")
            if rc or not re.fullmatch(r"[0-9a-f]{40,64}", blob):
                raise RuntimeError(f"MATERIAL_BLOB_UNAVAILABLE:{material}:{err[-300:]}")
            blob_ids[str(material)] = blob

        tmp = Path(tempfile.mkdtemp(prefix="clay-forge-distillery-v3-"))
        current = tmp / "current"
        ablated = tmp / "ablated"
        clone_exact(source_sha, current)
        clone_exact(source_sha, ablated)
        ablated_sha = ablate_admission(ablated)

        backend = backend_status(current)
        result["execution_backend"] = backend
        if not backend["admitted"]:
            result["status"] = "BLOCKED_NO_ISOLATED_EXECUTOR"
            result["pass"] = False
            return 2

        command = ["python3", "-m", "unittest", "-q", TEST]
        current_runs = [run_isolated(current, command) for _ in range(2)]
        ablated_runs = [run_isolated(ablated, command) for _ in range(2)]
        static = run_isolated(current, ["python3", "-m", "py_compile", str(TARGET)])
        current_pass = sum(x["rc"] == 0 for x in current_runs)
        ablated_pass = sum(x["rc"] == 0 for x in ablated_runs)
        improvement = 100.0 * (current_pass - ablated_pass) / 2.0

        qualified_path = tmp / "qualified.jsonl"
        forge_artifacts = tmp / "forge-artifacts"
        evaluation, producer = produce_forge_evaluation(current, source_sha, qualified_path, forge_artifacts)
        producer_accept = str(evaluation.get("status", "")).lower() == "accepted"
        qualified, qualification_reason = evidence_reason(evaluation)

        nominal = dict(evaluation)
        nominal["delta_id"] = "nominal-no-execution-admission-negative-control"
        nominal["execution_admission"] = None
        nominal_path = tmp / "nominal.jsonl"
        nominal_path.write_text(json.dumps(nominal, sort_keys=True) + "\n", encoding="utf-8")
        nominal_db = tmp / "nominal.sqlite3"
        nominal_result = bridge_once(current, nominal_path, nominal_db)

        qualified_db = tmp / "qualified.sqlite3"
        first = bridge_once(current, qualified_path, qualified_db)
        replay = bridge_once(current, qualified_path, qualified_db)

        token1 = int(first.get("accepted_dataset_tokens_counter") or 0)
        token2 = int(replay.get("accepted_dataset_tokens_counter") or 0)
        nominal_rejected = int(nominal_result.get("admitted") or 0) == 0
        gate_pass = (
            current_pass == 2 and ablated_pass == 0 and static["rc"] == 0 and
            producer_accept and qualified and nominal_rejected and
            int(first.get("admitted") or 0) == 1 and
            int(first.get("forge_execution_packets_total") or 0) == 1 and token1 > 0 and
            int(replay.get("admitted") or 0) == 0 and int(replay.get("duplicates") or 0) == 1 and
            int(replay.get("forge_execution_packets_total") or 0) == 1 and token2 == token1
        )

        result.update({
            "source_tree": tree,
            "material_blobs": blob_ids,
            "ablation_source_sha256": ablated_sha,
            "current_runs": current_runs,
            "ablated_runs": ablated_runs,
            "current_passes": current_pass,
            "ablated_passes": ablated_pass,
            "relative_improvement_pct": improvement,
            "static_check": static,
            "forge_producer": producer,
            "forge_evaluation": evaluation,
            "forge_producer_accept_observed": producer_accept,
            "evidence_qualified": qualified,
            "evidence_reason": qualification_reason,
            "nominal_negative_control": nominal_result,
            "distillery_first": first,
            "distillery_replay": replay,
            "acceptance_witness": {
                "safe_forge_producer_accept": int(producer_accept),
                "nominal_without_execution_admission_rejected": nominal_rejected,
                "exact_evidence_qualified_accept": int(qualified and producer_accept),
                "first_new_distillery_packets": int(first.get("admitted") or 0),
                "accepted_dataset_tokens_after_first": token1,
                "replay_new_packets": int(replay.get("admitted") or 0),
                "replay_duplicates": int(replay.get("duplicates") or 0),
                "accepted_dataset_tokens_after_replay": token2,
                "token_delta_on_replay": token2 - token1,
            },
            "pass": gate_pass,
            "status": "PASS_REAL_FORGE_1_TO_1_TO_NONZERO_REPLAY_ZERO" if gate_pass else "FAIL_RUNTIME_GATE",
        })
        return 0 if gate_pass else 1
    except Exception as exc:
        result["status"] = "ERROR"
        result["pass"] = False
        result["error"] = f"{type(exc).__name__}:{str(exc)[:1000]}"
        return 1
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
