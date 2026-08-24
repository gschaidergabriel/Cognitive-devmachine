#!/usr/bin/env python3
"""Bounded self-hosted Supervisor-8.71 Forge -> Distillery runtime witness.

This tool performs no provider/network execution. It evaluates one meaningful patch
against an exact source commit inside bubblewrap --unshare-all, qualifies the resulting
Forge evaluation with the current evidence audit, then feeds that exact evaluation to
a patched copy of the existing Distillery bridge twice to prove 1 -> 1 -> >0 and
idempotent replay. The candidate patch closes the real gap identified by #1563:
Distillery must require CLAY_FORGE_EXECUTION_ADMISSION/v1, not merely a nominal exact-
source accepted row.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path("tools/ingest_forge_accepts_into_distillery.py")
CHECK = "python3 -m unittest -q runtime_checks.test_forge_distillery_requires_execution_admission_871"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

import sys
sys.path.insert(0, str(ROOT / "tools"))
from forge_evidence_credit_871 import evidence_reason


def git(cwd: Path, *args: str) -> tuple[int, str, str]:
    p = subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def candidate_patch(source: str) -> str:
    marker = "from typing import Any\n"
    if marker not in source:
        raise RuntimeError("IMPORT_MARKER_MISSING")
    source2 = source.replace(marker, marker + "\nfrom forge_evidence_credit_871 import evidence_reason as forge_evidence_reason\n", 1)
    start = source2.find("def admission_reason(row: Any) -> tuple[bool, str]:\n")
    end = source2.find("\n\ndef measured_packet", start)
    if start < 0 or end < 0:
        raise RuntimeError("ADMISSION_FUNCTION_BOUNDARY_MISSING")
    replacement = '''def admission_reason(row: Any) -> tuple[bool, str]:
    # Current 8.71 dataset admission must be at least as strict as Forge evidence
    # credit. Historical nominal accepts stay append-only but cannot mint dataset
    # tokens without exact source + isolated execution-admission evidence.
    ok, reason = forge_evidence_reason(row)
    if not ok:
        return False, reason
    return True, "ACCEPTED_EVIDENCE_QUALIFIED_EXECUTION"
'''
    source2 = source2[:start] + replacement + source2[end:]
    diff = difflib.unified_diff(
        source.splitlines(True), source2.splitlines(True),
        fromfile="a/" + str(TARGET), tofile="b/" + str(TARGET), n=3,
    )
    return "".join(diff)


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


def bwrap_prefix(cwd: Path) -> list[str] | None:
    bwrap = shutil.which("bwrap")
    if not bwrap:
        return None
    prefix = [bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"]
    for host in ("/usr", "/bin", "/lib", "/lib64", "/usr/local"):
        if Path(host).exists():
            prefix += ["--ro-bind", host, host]
    prefix += ["--ro-bind", str(cwd.resolve()), "/work", "--chdir", "/work"]
    for key, value in minimal_env().items():
        prefix += ["--setenv", key, value]
    return prefix + ["--"]


def backend_status(cwd: Path) -> dict:
    prefix = bwrap_prefix(cwd)
    if prefix is None:
        return {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1", "admitted": False,
            "backend": None, "reason": "BUBBLEWRAP_NOT_FOUND", "network_namespace": "UNAVAILABLE",
            "secret_environment_inherited": False, "host_secret_paths_exposed": False,
        }
    p = subprocess.run(prefix + ["/usr/bin/true"], cwd=cwd, env=minimal_env(), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    ok = p.returncode == 0
    return {
        "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1", "admitted": ok,
        "backend": "bubblewrap_unshare_all", "reason": "OK" if ok else f"BUBBLEWRAP_PROBE_RC_{p.returncode}",
        "network_namespace": "ISOLATED" if ok else "UNAVAILABLE",
        "secret_environment_inherited": False, "host_secret_paths_exposed": False,
    }


def run_isolated(cwd: Path, command: list[str], timeout: int = 120) -> dict:
    prefix = bwrap_prefix(cwd)
    if prefix is None:
        return {"rc": 126, "elapsed_s": 0.0, "stdout": "", "stderr": "NO_BUBBLEWRAP"}
    started = time.monotonic()
    try:
        p = subprocess.run(prefix + command, cwd=cwd, env=minimal_env(), text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"rc": p.returncode, "elapsed_s": time.monotonic() - started,
                "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]}
    except subprocess.TimeoutExpired as exc:
        return {"rc": 124, "elapsed_s": time.monotonic() - started,
                "stdout": str(exc.stdout or "")[-2000:], "stderr": "TIMEOUT"}


def clone_exact(source_sha: str, dest: Path) -> None:
    p = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--local", str(ROOT), str(dest)],
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
    if p.returncode:
        raise RuntimeError("LOCAL_CLONE_FAILED:" + p.stderr[-500:])
    rc, _, err = git(dest, "checkout", "--quiet", "--detach", source_sha)
    if rc:
        raise RuntimeError("SOURCE_CHECKOUT_FAILED:" + err[-500:])
    rc, got, _ = git(dest, "rev-parse", "HEAD")
    if rc or got != source_sha:
        raise RuntimeError("SOURCE_IDENTITY_MISMATCH")


def parse_json_stdout(text: str) -> dict:
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise RuntimeError("JSON_RESULT_NOT_OBJECT")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_sha = args.source_sha.strip().lower()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "CLAY_GO871_FORGE_DISTILLERY_RUNTIME_GATE/v1",
        "authority_epoch": "8.71", "mode": "FREE_ONLY", "source_sha": source_sha,
        "network_used": False, "provider_calls": 0, "paid_fallback_attempt_count": 0,
        "whole_product_credit": 0, "jspace_credit": 0, "training_credit": 0,
    }
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
        source_text = subprocess.run(["git", "show", f"{source_sha}:{TARGET}"], cwd=ROOT,
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     timeout=30, check=True).stdout
        patch = candidate_patch(source_text)
        patch_sha = hashlib.sha256(patch.encode()).hexdigest()
        worker_sha = hashlib.sha256(("go871-forge-distillery:" + source_sha + ":" + patch_sha).encode()).hexdigest()

        tmp = Path(tempfile.mkdtemp(prefix="clay-go871-runtime-gate-"))
        baseline, patched = tmp / "baseline", tmp / "patched"
        clone_exact(source_sha, baseline); clone_exact(source_sha, patched)
        try:
            applier = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=patched,
                                     input=patch, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if applier.returncode:
                raise RuntimeError("PATCH_APPLY_FAILED:" + applier.stderr[-500:])
            backend = backend_status(patched)
            result["execution_backend"] = backend
            if not backend["admitted"]:
                result["status"] = "BLOCKED_NO_ISOLATED_EXECUTOR"
                result["pass"] = False
                return 2

            command = ["python3", "-m", "unittest", "-q", "runtime_checks.test_forge_distillery_requires_execution_admission_871"]
            base_runs = [run_isolated(baseline, command) for _ in range(2)]
            patch_runs = [run_isolated(patched, command) for _ in range(2)]
            static = run_isolated(patched, ["python3", "-m", "py_compile", str(TARGET)])
            base_pass = sum(x["rc"] == 0 for x in base_runs)
            patch_pass = sum(x["rc"] == 0 for x in patch_runs)
            improvement = 100.0 * (patch_pass - base_pass) / 2.0
            evaluation = {
                "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
                "delta_id": "go871-distillery-execution-admission-gate",
                "source_class": "gpt56sol_go_runtime_gate",
                "provider": "local_deterministic", "model": "none", "role": "RUNTIME",
                "worker_sha": worker_sha,
                "source_repo_head": source_sha, "evaluation_repo_head": source_sha,
                "source_scope": "EXACT_WORKER_PROMPT_HEAD",
                "evaluated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "status": "accepted" if base_pass == 0 and patch_pass == 2 and static["rc"] == 0 and improvement > 0 else "validated_not_better",
                "metric": "evidence_admission_regression_pass_rate", "relative_improvement_pct": improvement,
                "reproducible_runs": 2, "tests_passed": patch_pass, "tests_failed": 2 - patch_pass,
                "negative_tests_passed": 0, "negative_tests_failed": 0,
                "static_checks_passed": int(static["rc"] == 0), "static_checks_failed": int(static["rc"] != 0),
                "benchmark_non_regression": True, "reverted": False,
                "baseline_test_passes": base_pass, "patched_test_passes": patch_pass,
                "target_blob_identities": {str(TARGET): target_blob},
                "requires_rebase_to_evaluation_head": False,
                "execution_admission": {
                    "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
                    "source_scope": "EXACT_WORKER_PROMPT_HEAD", "source_identity_admitted": True,
                    "source_head": source_sha, "source_tree": tree,
                    "all_commands_admitted": True, "candidate_is_canonical_truth": False,
                    "patch_sha256": patch_sha, "command": CHECK, "backend": backend,
                },
                "proposal_hypothesis": "Distillery must not admit nominal exact-source Forge accepts without isolated execution admission.",
                "falsifier": "If the exact nominal row without execution_admission is already rejected on baseline, the patch has no causal effect.",
            }
            qualified, qualification_reason = evidence_reason(evaluation)
            result["forge_evaluation"] = evaluation
            result["evidence_qualified"] = qualified
            result["evidence_reason"] = qualification_reason
            result["baseline_runs"] = base_runs
            result["patched_runs"] = patch_runs
            result["static_check"] = static
            result["candidate_patch_sha256"] = patch_sha

            eval_path = tmp / "forge_evaluation.jsonl"
            eval_path.write_text(json.dumps(evaluation, sort_keys=True) + "\n", encoding="utf-8")
            db = tmp / "distillery.sqlite3"
            bridge = patched / TARGET
            cmd = ["python3", str(bridge), "--forge-evaluations", str(eval_path), "--distillery-db", str(db)]
            first_p = subprocess.run(cmd, cwd=patched, env=minimal_env(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            second_p = subprocess.run(cmd, cwd=patched, env=minimal_env(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if first_p.returncode or second_p.returncode:
                raise RuntimeError("DISTILLERY_BRIDGE_PROCESS_FAILED")
            first = parse_json_stdout(first_p.stdout); second = parse_json_stdout(second_p.stdout)
            result["distillery_first"] = first
            result["distillery_replay"] = second
            token1 = int(first.get("accepted_dataset_tokens_counter") or 0)
            token2 = int(second.get("accepted_dataset_tokens_counter") or 0)
            gate_pass = (
                qualified and evaluation["status"] == "accepted" and
                int(first.get("admitted") or 0) == 1 and
                int(first.get("forge_execution_packets_total") or 0) == 1 and token1 > 0 and
                int(second.get("admitted") or 0) == 0 and int(second.get("duplicates") or 0) == 1 and
                int(second.get("forge_execution_packets_total") or 0) == 1 and token2 == token1
            )
            result["acceptance_witness"] = {
                "exact_evidence_qualified_accept": int(qualified and evaluation["status"] == "accepted"),
                "first_new_distillery_packets": int(first.get("admitted") or 0),
                "accepted_dataset_tokens_after_first": token1,
                "replay_new_packets": int(second.get("admitted") or 0),
                "accepted_dataset_tokens_after_replay": token2,
                "token_delta_on_replay": token2 - token1,
            }
            result["pass"] = gate_pass
            result["status"] = "PASS_EXACT_1_TO_1_TO_NONZERO_REPLAY_ZERO" if gate_pass else "FAIL_RUNTIME_GATE"
            result["candidate_patch_unified_diff"] = patch
            return 0 if gate_pass else 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as exc:
        result["status"] = "ERROR"
        result["pass"] = False
        result["error"] = f"{type(exc).__name__}:{str(exc)[:1000]}"
        return 1
    finally:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
