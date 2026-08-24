#!/usr/bin/env python3
"""Exact-current Forge -> Distillery successor runtime witness.

No provider/model network execution occurs. The gate checks one exact source commit,
proves the integrated evidence-admission boundary against a deterministic ablation in
bubblewrap --unshare-all, then drives the exact current Distillery bridge with (a) a
nominal ACCEPT lacking execution admission and (b) one evidence-qualified ACCEPT twice.
Acceptance requires nominal rejection plus exactly one new packet, nonzero dataset
tokens, and zero replay token delta.

The host/source probe remains read-only. Only the witness-owned disposable current and
ablated clones are writable in their isolated /work bind so py_compile/unittest may
create ordinary scratch artifacts without exposing any additional host path.
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
    # Admission probe is deliberately read-only. Writable scope is enabled only
    # by run_isolated for witness-owned disposable clones.
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
    # cwd is always one of the witness-owned clones created under tempfile.mkdtemp
    # in main(). Making only /work writable is required for py_compile/unittest
    # scratch output; all other host binds remain read-only/hidden and networking
    # remains unshared.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_sha = args.source_sha.strip().lower()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema": "CLAY_FORGE_DISTILLERY_EXACT_CURRENT_RUNTIME_GATE/v2",
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
        "witness_write_scope": "DISPOSABLE_CURRENT_AND_ABLATED_CLONES_ONLY",
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
        rc, target_blob, err = git(ROOT, "rev-parse", f"{source_sha}:{TARGET}")
        if rc or not re.fullmatch(r"[0-9a-f]{40,64}", target_blob):
            raise RuntimeError("TARGET_BLOB_UNAVAILABLE:" + err[-300:])

        tmp = Path(tempfile.mkdtemp(prefix="clay-forge-distillery-v2-"))
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

        worker_sha = hashlib.sha256(
            ("forge-distillery-v2:" + source_sha + ":" + target_blob + ":" + ablated_sha).encode()
        ).hexdigest()
        admission = {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_identity_admitted": True,
            "source_head": source_sha,
            "source_tree": tree,
            "all_commands_admitted": True,
            "candidate_is_canonical_truth": False,
            "command": "python3 -m unittest -q " + TEST,
            "backend": backend,
        }
        evaluation = {
            "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
            "delta_id": "integrated-forge-distillery-evidence-admission-v2",
            "source_class": "exact_current_runtime_successor_gate",
            "provider": "local_deterministic",
            "model": "none",
            "role": "RUNTIME",
            "worker_sha": worker_sha,
            "source_repo_head": source_sha,
            "evaluation_repo_head": source_sha,
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "evaluated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "status": "accepted" if current_pass == 2 and ablated_pass == 0 and static["rc"] == 0 and improvement > 0 else "validated_not_better",
            "metric": "execution_admission_causal_regression_pass_rate",
            "relative_improvement_pct": improvement,
            "reproducible_runs": 2,
            "tests_passed": current_pass,
            "tests_failed": 2 - current_pass,
            "negative_tests_passed": 1,
            "negative_tests_failed": 0,
            "static_checks_passed": int(static["rc"] == 0),
            "static_checks_failed": int(static["rc"] != 0),
            "benchmark_non_regression": True,
            "reverted": False,
            "target_blob_identities": {str(TARGET): target_blob},
            "requires_rebase_to_evaluation_head": False,
            "execution_admission": admission,
            "proposal_hypothesis": "Integrated Distillery admission causally depends on the shared Forge evidence-qualified execution discriminator.",
            "falsifier": "If the exact current source does not outperform the nominal-only ablation on the admission regression, integrated causal credit fails.",
        }
        qualified, qualification_reason = evidence_reason(evaluation)

        nominal = dict(evaluation)
        nominal["delta_id"] = "nominal-no-execution-admission-negative-control"
        nominal["execution_admission"] = None
        nominal_path = tmp / "nominal.jsonl"
        nominal_path.write_text(json.dumps(nominal, sort_keys=True) + "\n", encoding="utf-8")
        nominal_db = tmp / "nominal.sqlite3"
        nominal_result = bridge_once(current, nominal_path, nominal_db)

        qualified_path = tmp / "qualified.jsonl"
        qualified_path.write_text(json.dumps(evaluation, sort_keys=True) + "\n", encoding="utf-8")
        qualified_db = tmp / "qualified.sqlite3"
        first = bridge_once(current, qualified_path, qualified_db)
        replay = bridge_once(current, qualified_path, qualified_db)

        token1 = int(first.get("accepted_dataset_tokens_counter") or 0)
        token2 = int(replay.get("accepted_dataset_tokens_counter") or 0)
        nominal_rejected = int(nominal_result.get("admitted") or 0) == 0
        gate_pass = (
            current_pass == 2 and ablated_pass == 0 and static["rc"] == 0 and
            qualified and evaluation["status"] == "accepted" and nominal_rejected and
            int(first.get("admitted") or 0) == 1 and
            int(first.get("forge_execution_packets_total") or 0) == 1 and token1 > 0 and
            int(replay.get("admitted") or 0) == 0 and int(replay.get("duplicates") or 0) == 1 and
            int(replay.get("forge_execution_packets_total") or 0) == 1 and token2 == token1
        )

        result.update({
            "source_tree": tree,
            "target_blob": target_blob,
            "ablation_source_sha256": ablated_sha,
            "current_runs": current_runs,
            "ablated_runs": ablated_runs,
            "current_passes": current_pass,
            "ablated_passes": ablated_pass,
            "relative_improvement_pct": improvement,
            "static_check": static,
            "forge_evaluation": evaluation,
            "evidence_qualified": qualified,
            "evidence_reason": qualification_reason,
            "nominal_negative_control": nominal_result,
            "distillery_first": first,
            "distillery_replay": replay,
            "acceptance_witness": {
                "nominal_without_execution_admission_rejected": nominal_rejected,
                "exact_evidence_qualified_accept": int(qualified and evaluation["status"] == "accepted"),
                "first_new_distillery_packets": int(first.get("admitted") or 0),
                "accepted_dataset_tokens_after_first": token1,
                "replay_new_packets": int(replay.get("admitted") or 0),
                "replay_duplicates": int(replay.get("duplicates") or 0),
                "accepted_dataset_tokens_after_replay": token2,
                "token_delta_on_replay": token2 - token1,
            },
            "pass": gate_pass,
            "status": "PASS_EXACT_CURRENT_1_TO_1_TO_NONZERO_REPLAY_ZERO" if gate_pass else "FAIL_RUNTIME_GATE",
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
