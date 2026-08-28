#!/usr/bin/env python3
"""Fixed exact-head acceptance probe for retained PR430 UNKNOWN_OUTCOME semantics.

This runner is intentionally narrow. It checks out one hard-pinned candidate commit and
runs only the retained UNKNOWN_OUTCOME regression file. It does not accept caller commands,
provider/model routes, credentials, or real-effect parameters.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

SCHEMA = "TRIGGER4_PR430_UNKNOWN_OUTCOME_ACCEPTANCE_RECEIPT/v1"
EXPECTED_HEAD = "2f99e400f1c0ea1b8598573ab0fab993885cba5e"
REPOSITORY = "https://github.com/gschaidergabriel/clay-global-research-entity.git"
TEST_PATH = "the artefact/tests/test_effect_unknown_outcome.py"
EXPECTED_TESTS = 8
BOUND_PATHS = (
    "the artefact/clayverse/effect_journal.py",
    "the artefact/clayverse/effects.py",
    "the artefact/clayverse/entityos_bridge.py",
    TEST_PATH,
)
ARTIFACT = Path("artifacts/pr430-unknown-outcome-acceptance/receipt.json")


def _run(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git(args: list[str], *, cwd: Path) -> str:
    proc = _run(["git", *args], cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed rc={proc.returncode}: {proc.stderr[-1000:]}")
    return proc.stdout.strip()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _write(receipt: dict) -> None:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    started = time.time()
    dispatch_root = Path.cwd().resolve()
    receipt: dict = {
        "schema": SCHEMA,
        "probe_contract": "TRIGGER4_PR430_UNKNOWN_OUTCOME_ACCEPTANCE/v1",
        "authority_epoch": "8.78",
        "repository": "gschaidergabriel/clay-global-research-entity",
        "candidate_pr": 430,
        "candidate_expected_head": EXPECTED_HEAD,
        "candidate_test": TEST_PATH,
        "expected_tests": EXPECTED_TESTS,
        "sandbox_expected": "clay-direct-dev",
        "status": "BLOCKED",
        "bundle_pass": False,
        "tests_started": False,
        "real_external_effect": False,
        "provider_or_model_calls": 0,
        "arbitrary_command_dispatch": False,
        "canonical_effect_authority_promotion": False,
        "runtime_credit_scope": 0,
        "physical_grid10_runtime_credit": 0,
        "whole_hcu_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "training_credit": 0,
    }

    try:
        if shutil.which("git") is None:
            raise RuntimeError("git unavailable")
        dispatch_head = _git(["rev-parse", "HEAD"], cwd=dispatch_root)
        dispatch_tree = _git(["rev-parse", "HEAD^{tree}"], cwd=dispatch_root)
        dispatch_dirty = bool(_git(["status", "--porcelain"], cwd=dispatch_root))
        receipt.update(
            dispatch_head=dispatch_head,
            dispatch_tree=dispatch_tree,
            dispatch_dirty=dispatch_dirty,
        )
        if dispatch_dirty:
            raise RuntimeError("dispatch checkout is dirty")

        with tempfile.TemporaryDirectory(prefix="trigger4-pr430-unknown-") as td:
            candidate = Path(td) / "candidate"
            clone = _run(["git", "clone", "--no-checkout", REPOSITORY, str(candidate)])
            if clone.returncode != 0:
                raise RuntimeError(f"candidate clone failed rc={clone.returncode}: {clone.stderr[-1000:]}")
            fetch = _run(["git", "fetch", "--no-tags", "origin", EXPECTED_HEAD], cwd=candidate)
            if fetch.returncode != 0:
                raise RuntimeError(f"candidate fetch failed rc={fetch.returncode}: {fetch.stderr[-1000:]}")
            checkout = _run(["git", "checkout", "--detach", EXPECTED_HEAD], cwd=candidate)
            if checkout.returncode != 0:
                raise RuntimeError(f"candidate checkout failed rc={checkout.returncode}: {checkout.stderr[-1000:]}")

            head = _git(["rev-parse", "HEAD"], cwd=candidate)
            tree = _git(["rev-parse", "HEAD^{tree}"], cwd=candidate)
            dirty = bool(_git(["status", "--porcelain"], cwd=candidate))
            if head != EXPECTED_HEAD or dirty:
                raise RuntimeError("candidate identity/cleanliness mismatch")
            blobs = {path: _git(["rev-parse", f"HEAD:{path}"], cwd=candidate) for path in BOUND_PATHS}
            receipt.update(candidate_head=head, candidate_tree=tree, candidate_dirty=dirty, bound_git_blobs=blobs)

            pytest_probe = _run([sys.executable, "-c", "import pytest; print(pytest.__version__)"])
            if pytest_probe.returncode != 0:
                receipt["pytest_probe_stderr_sha256"] = _sha256_text(pytest_probe.stderr)
                raise RuntimeError("pytest unavailable in sandbox")
            receipt["pytest_version"] = pytest_probe.stdout.strip()

            env = os.environ.copy()
            env["PYTHONPATH"] = str(candidate / "the artefact")
            collect = _run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", TEST_PATH],
                cwd=candidate,
                env=env,
            )
            receipt.update(
                collect_exit_code=collect.returncode,
                collect_stdout_sha256=_sha256_text(collect.stdout),
                collect_stderr_sha256=_sha256_text(collect.stderr),
            )
            if collect.returncode != 0:
                raise RuntimeError("pytest collection failed before semantic execution")
            match = re.search(r"(?:^|\n)(\d+) tests? collected(?:\s|$)", collect.stdout + "\n" + collect.stderr)
            if match is None:
                # pytest -q may omit the summary in some versions; count exact collected node ids.
                collected = sum(1 for line in collect.stdout.splitlines() if "::test_" in line)
            else:
                collected = int(match.group(1))
            receipt["collected_tests"] = collected
            if collected != EXPECTED_TESTS:
                raise RuntimeError(f"exact-head test count mismatch: expected {EXPECTED_TESTS}, got {collected}")

            receipt["tests_started"] = True
            test = _run([sys.executable, "-m", "pytest", "-q", TEST_PATH], cwd=candidate, env=env)
            receipt.update(
                test_exit_code=test.returncode,
                test_stdout_sha256=_sha256_text(test.stdout),
                test_stderr_sha256=_sha256_text(test.stderr),
                test_stdout_tail=test.stdout[-2000:],
                test_stderr_tail=test.stderr[-2000:],
            )
            if test.returncode != 0:
                receipt["status"] = "FAIL"
                receipt["failure_class"] = "EXACT_CANDIDATE_REGRESSION_FAILURE"
                return_code = 1
            else:
                receipt["status"] = "PASS"
                receipt["bundle_pass"] = True
                receipt["runtime_credit_scope"] = "EXACT_PR430_UNKNOWN_OUTCOME_COMPONENT_RUNTIME_ONLY"
                return_code = 0

    except Exception as exc:  # fail closed; transport/setup failures are not semantic negatives
        receipt["status"] = "BLOCKED"
        receipt["blocker"] = f"{type(exc).__name__}: {exc}"
        return_code = 20
    finally:
        receipt["elapsed_seconds"] = round(time.time() - started, 6)
        receipt["evidence_boundary"] = {
            "exact_candidate_component_execution": bool(receipt.get("bundle_pass")),
            "canonical_effect_authority_promotion": False,
            "real_external_effect": False,
            "physical_grid10_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
            "training_credit": 0,
        }
        _write(receipt)

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
