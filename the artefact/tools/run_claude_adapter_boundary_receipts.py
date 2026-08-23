#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from pathlib import Path

SCHEMA = "CLAUDE_CODE_ADAPTER_BOUNDARY_RECEIPT_SET/v1"
NODE_TIMEOUT_SECONDS = 120
NODES = (
    "tests/test_runtime_adapters.py::test_claude_code_adapter_toolless_receipt_v1",
    "tests/test_runtime_adapters.py::test_claude_code_adapter_ephemeral_receipt_v1",
    "tests/test_runtime_adapters.py::test_claude_code_adapter_structured_output_receipt_v1",
    "tests/test_runtime_adapters.py::test_claude_code_adapter_env_isolation_receipt_v1",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args], cwd=repo, shell=False, capture_output=True, text=True, check=False
    )
    if cp.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed rc={cp.returncode} "
            f"stderr_sha256={sha256_bytes(cp.stderr.encode('utf-8', errors='replace'))}"
        )
    return cp.stdout.strip()


def command_version(argv: list[str]) -> dict:
    cp = subprocess.run(argv, shell=False, capture_output=True, check=False, timeout=10)
    raw = cp.stdout + b"\x00" + cp.stderr
    return {
        "argv": argv,
        "returncode": int(cp.returncode),
        "output_sha256": sha256_bytes(raw),
        "output_bytes": len(raw),
        "text": raw.decode("utf-8", errors="replace").strip()[:512],
    }


def git_blob(repo: Path, relative: str) -> str:
    return git(repo, "rev-parse", f"HEAD:{relative}")


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_bytes(encoded)
    os.replace(tmp, path)


def tree_status(repo: Path) -> str:
    return git(repo, "status", "--porcelain=v1", "--untracked-files=all")


def build_source_identity(repo: Path, artefact: Path, runner_path: Path) -> dict:
    dirty = tree_status(repo)
    if dirty:
        raise RuntimeError(
            "DIRTY_TREE_REJECTED:" + sha256_bytes(dirty.encode("utf-8", errors="replace"))
        )

    test_path = artefact / "tests/test_runtime_adapters.py"
    adapter_path = artefact / "clayverse/adapters.py"
    for path in (test_path, adapter_path, runner_path):
        if not path.is_file():
            raise RuntimeError(f"required file missing: {path}")

    rel_test = test_path.relative_to(repo).as_posix()
    rel_adapter = adapter_path.relative_to(repo).as_posix()
    rel_runner = runner_path.relative_to(repo).as_posix()

    return {
        "commit": git(repo, "rev-parse", "HEAD"),
        "tree": git(repo, "rev-parse", "HEAD^{tree}"),
        "dirty_before": False,
        "dirty_after": None,
        "files": {
            "test": {
                "path": rel_test,
                "git_blob": git_blob(repo, rel_test),
                "sha256": sha256_file(test_path),
            },
            "adapter": {
                "path": rel_adapter,
                "git_blob": git_blob(repo, rel_adapter),
                "sha256": sha256_file(adapter_path),
            },
            "runner": {
                "path": rel_runner,
                "git_blob": git_blob(repo, rel_runner),
                "sha256": sha256_file(runner_path),
            },
        },
    }


def run_node(artefact: Path, node: str) -> dict:
    started_ns = time.time_ns()
    try:
        cp = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", node],
            cwd=artefact,
            shell=False,
            capture_output=True,
            check=False,
            timeout=NODE_TIMEOUT_SECONDS,
        )
        stdout = cp.stdout
        stderr = cp.stderr
        returncode = int(cp.returncode)
        status = "PASS" if returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        returncode = 124
        status = "TIMEOUT"

    ended_ns = time.time_ns()
    signature = stdout + b"\x00" + stderr
    return {
        "node_id": node,
        "returncode": returncode,
        "status": status,
        "timeout_seconds": NODE_TIMEOUT_SECONDS,
        "duration_ms": round((ended_ns - started_ns) / 1_000_000, 3),
        "stdout_sha256": sha256_bytes(stdout),
        "stdout_bytes": len(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stderr_bytes": len(stderr),
        "failure_signature_sha256": None if status == "PASS" else sha256_bytes(signature),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    runner_path = Path(__file__).resolve()
    repo = runner_path.parents[2]
    artefact = repo / "the artefact"
    started_ns = time.time_ns()
    python_path = Path(sys.executable).resolve()

    receipt = {
        "schema": SCHEMA,
        "run_id": str(uuid.uuid4()),
        "started_unix_ns": started_ns,
        "source": None,
        "executor": {
            "python_executable_path_sha256": sha256_bytes(str(python_path).encode("utf-8")),
            "python_executable_file_sha256": sha256_file(python_path) if python_path.is_file() else None,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "pytest": command_version([sys.executable, "-m", "pytest", "--version"]),
            "git": command_version(["git", "--version"]),
            "pytest_invocation": "python -m pytest -q <fixed-node-id>",
            "real_claude_cli_exercised": False,
            "note": "The four canonical boundary tests use a fixture Claude binary; provider/network execution is not part of this receipt.",
        },
        "nodes": [],
        "overall": "UNRESOLVED",
        "evidence_scope": "EXACT_CHECKOUT_DETERMINISTIC_BOUNDARY_TESTS_ONLY",
    }

    try:
        receipt["source"] = build_source_identity(repo, artefact, runner_path)
        receipt["nodes"] = [run_node(artefact, node) for node in NODES]

        dirty_after = tree_status(repo)
        if dirty_after:
            receipt["source"]["dirty_after"] = True
            raise RuntimeError(
                "POSTRUN_DIRTY_TREE_REJECTED:"
                + sha256_bytes(dirty_after.encode("utf-8", errors="replace"))
            )
        receipt["source"]["dirty_after"] = False

        receipt["overall"] = (
            "PASS" if all(item["returncode"] == 0 for item in receipt["nodes"]) else "FAIL"
        )
        exit_code = 0 if receipt["overall"] == "PASS" else 1
    except Exception as exc:
        raw = f"{type(exc).__name__}:{exc}".encode("utf-8", errors="replace")
        receipt["overall"] = "PROVENANCE_OR_RUNNER_REJECTED"
        receipt["runner_error_type"] = type(exc).__name__
        receipt["runner_error_sha256"] = sha256_bytes(raw)
        exit_code = 2

    receipt["ended_unix_ns"] = time.time_ns()
    receipt["receipt_payload_sha256"] = sha256_bytes(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )

    if args.output is None:
        print(json.dumps(receipt, sort_keys=True, indent=2))
    else:
        atomic_write_json(args.output, receipt)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
