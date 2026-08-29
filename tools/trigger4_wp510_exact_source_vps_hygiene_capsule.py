#!/usr/bin/env python3
"""Fixed-purpose Triggerword-4 WP510 G3 exact-source hygiene capsule.

This capsule never cleans or resets the existing VPS workspace, never invokes a
provider/model/effect path, and never grants physical GRID10/GWT/J-Space/training/
whole-system credit. It prepares exact-source target-environment evidence for the
canonical WP510 generation-3 closure snapshot.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from typing import Any

F2_REPO_URL = "https://github.com/gschaidergabriel/frankenstein-2.0.git"
WP510_G3_SOURCE_SHA = "731816a370a0c4fa9bcd63ba05fbf6013433acfe"
WP510_G3_TREE_SHA = "156953a665a451f6307c4c3e89de0e365f90bcdc"
SCHEMA = "TRIGGER4_WP510_EXACT_SOURCE_VPS_HYGIENE_RECEIPT/v2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(argv: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_readonly_state(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "mutated": False,
        "git_repository": False,
        "head": None,
        "tree": None,
        "dirty": None,
        "status_porcelain_sample": [],
        "error": None,
    }
    if not path.exists():
        return result
    try:
        inside = run(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"]).stdout.strip()
        if inside != "true":
            return result
        result["git_repository"] = True
        result["head"] = run(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()
        result["tree"] = run(["git", "-C", str(path), "rev-parse", "HEAD^{tree}"]).stdout.strip()
        status = run(["git", "-C", str(path), "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines()
        result["dirty"] = bool(status)
        result["status_porcelain_sample"] = status[:100]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def cgroup_observation() -> dict[str, Any]:
    proc = Path("/proc/self/cgroup")
    text = proc.read_text(encoding="utf-8", errors="replace") if proc.exists() else None
    return {
        "proc_self_cgroup_present": proc.exists(),
        "proc_self_cgroup": text,
        "container_cgroup_health": "UNKNOWN",
        "isolation_credit": 0,
        "reason": "PROC_CGROUP_VISIBILITY_IS_NOT_SUFFICIENT_TO_PROVE_DEDICATED_CONTAINER_CGROUP_HEALTH",
    }


class _Raises:
    def __init__(self, expected: type[BaseException], match: str | None = None) -> None:
        self.expected = expected
        self.match = match

    def __enter__(self) -> "_Raises":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            raise AssertionError(f"expected {self.expected.__name__} to be raised")
        if not issubclass(exc_type, self.expected):
            return False
        if self.match is not None and re.search(self.match, str(exc)) is None:
            raise AssertionError(
                f"exception message {str(exc)!r} does not match {self.match!r}"
            )
        return True


def _minimal_pytest_module() -> types.ModuleType:
    module = types.ModuleType("pytest")
    module.raises = lambda expected, match=None: _Raises(expected, match)  # type: ignore[attr-defined]
    return module


def execute_fixed_wp510_probe(repo: Path) -> dict[str, Any]:
    source_path = repo / "src/frankenstein2/gwt_causal_path.py"
    test_path = repo / "tests/test_gwt_causal_path.py"
    g3_test_path = repo / "tests/test_wp510_g3_not_computed_status.py"
    for path in (source_path, test_path, g3_test_path):
        if not path.is_file():
            raise RuntimeError(f"canonical WP510 G3 source/test path missing: {path.relative_to(repo)}")

    src_dir = str(repo / "src")
    tests_dir = str(repo / "tests")
    sys.path.insert(0, src_dir)
    sys.path.insert(0, tests_dir)

    old_pytest = sys.modules.get("pytest")
    old_test_module = sys.modules.get("test_gwt_causal_path")
    capture = io.StringIO()
    positive_ns: dict[str, Any] = {}
    g3_ns: dict[str, Any] = {}
    try:
        sys.modules["pytest"] = _minimal_pytest_module()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            exec(compile(test_path.read_text(encoding="utf-8"), str(test_path), "exec"), positive_ns, positive_ns)
            required = [
                "test_positive_exact_chain_seals_without_minting_runtime_or_truth_credit",
                "make_fixture",
                "seal",
            ]
            missing = [name for name in required if name not in positive_ns]
            if missing:
                raise RuntimeError(f"fixed WP510 positive-probe ABI missing names: {missing}")

            positive_ns["test_positive_exact_chain_seals_without_minting_runtime_or_truth_credit"]()
            fixture = positive_ns["make_fixture"]()
            sealed = positive_ns["seal"](fixture)
            payload = sealed.as_dict()

            synthetic = types.ModuleType("test_gwt_causal_path")
            synthetic.__dict__.update(positive_ns)
            sys.modules["test_gwt_causal_path"] = synthetic

            exec(
                compile(g3_test_path.read_text(encoding="utf-8"), str(g3_test_path), "exec"),
                g3_ns,
                g3_ns,
            )
            negative_name = "test_not_computed_downstream_cannot_seal_positive_causal_path"
            if negative_name not in g3_ns:
                raise RuntimeError(f"fixed WP510 G3 negative-probe ABI missing name: {negative_name}")
            g3_ns[negative_name]()
    finally:
        if old_pytest is None:
            sys.modules.pop("pytest", None)
        else:
            sys.modules["pytest"] = old_pytest
        if old_test_module is None:
            sys.modules.pop("test_gwt_causal_path", None)
        else:
            sys.modules["test_gwt_causal_path"] = old_test_module
        for path in (tests_dir, src_dir):
            with contextlib.suppress(ValueError):
                sys.path.remove(path)

    return {
        "positive_probe": "test_positive_exact_chain_seals_without_minting_runtime_or_truth_credit",
        "positive_status": "PASS",
        "g3_negative_probe": "test_not_computed_downstream_cannot_seal_positive_causal_path",
        "g3_negative_status": "PASS",
        "path_status": payload.get("path_status"),
        "causal_status": payload.get("causal_status"),
        "uptaken_cell_ids": payload.get("uptaken_cell_ids"),
        "reentry_binding_ids": payload.get("reentry_binding_ids"),
        "seal_sha256": sealed.sha256(),
        "source_file_sha256": sha256_file(source_path),
        "positive_test_file_sha256": sha256_file(test_path),
        "g3_test_file_sha256": sha256_file(g3_test_path),
        "captured_output": capture.getvalue()[-4000:],
    }


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="wp510_g3_exact_source_vps_hygiene_receipt.json",
        help="Receipt output path. No source/runtime state is written elsewhere except a disposable temporary clone.",
    )
    parser.add_argument(
        "--observed-workspace",
        default="/workspace",
        help="Existing workspace to inspect read-only for dirty-state accounting; never cleaned/reset by this capsule.",
    )
    args = parser.parse_args()

    for name, value in (
        ("WP510_G3_SOURCE_SHA", WP510_G3_SOURCE_SHA),
        ("WP510_G3_TREE_SHA", WP510_G3_TREE_SHA),
    ):
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise SystemExit(f"internal fixed {name} is invalid")

    output = Path(args.output).expanduser().resolve()
    observed_workspace = Path(args.observed_workspace).expanduser().resolve()
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "created_at_utc": utc_now(),
        "purpose": "WP510_G3_EXACT_SOURCE_HYGIENE_AND_FIXED_COMPONENT_EXECUTION_PREPARATION",
        "repository": F2_REPO_URL,
        "requested_source_sha": WP510_G3_SOURCE_SHA,
        "requested_tree_sha": WP510_G3_TREE_SHA,
        "observed_existing_workspace": git_readonly_state(observed_workspace),
        "existing_workspace_mutation_performed": False,
        "provider_or_model_invocation": False,
        "external_effect_invocation": False,
        "host": {
            "python": sys.version,
            "platform": platform.platform(),
            "hostname": platform.node(),
        },
        "cgroup": cgroup_observation(),
        "source_binding": {
            "observed_sha": None,
            "observed_tree": None,
            "clean": None,
            "status_porcelain": None,
        },
        "probe": {"status": "NOT_RUN"},
        "status": "FAIL",
        "classification": "PREPARATION_ONLY",
        "credits": {
            "repository_component": 0,
            "target_environment_component_runtime": 0,
            "physical_grid10": 0,
            "semantic_gwt_runtime": 0,
            "jspace_runtime": 0,
            "provider_model_runtime": 0,
            "effect": 0,
            "completion": 0,
            "training": 0,
            "whole_frankenstein2": 0,
            "whole_entityos_hcu": 0,
        },
        "evidence_law": [
            "DIRTY_EXISTING_WORKSPACE_IS_PRESERVED_NOT_CLEANED",
            "EXACT_SOURCE_SHA_AND_TREE_ARE_OBSERVED_IN_A_DISPOSABLE_CLONE",
            "WP510_G3_POSITIVE_CHAIN_AND_NOT_COMPUTED_NEGATIVE_REGRESSION_BOTH_MUST_PASS",
            "MISSING_OR_AMBIGUOUS_CGROUP_TELEMETRY_REMAINS_UNKNOWN",
            "FIXED_COMPONENT_EXECUTION_DOES_NOT_MINT_PHYSICAL_GRID10_OR_SEMANTIC_GWT_JSPACE_CREDIT",
            "TARGET_ENVIRONMENT_CREDIT_REQUIRES_SEPARATE_ENVIRONMENT_ADMISSION_AND_RECEIPT_BINDING",
        ],
    }

    rc = 1
    try:
        with tempfile.TemporaryDirectory(prefix="f2-wp510-g3-exact-source-") as tmpdir:
            clone = Path(tmpdir) / "frankenstein-2.0"
            run(["git", "clone", "--quiet", "--no-checkout", F2_REPO_URL, str(clone)])
            run(["git", "-C", str(clone), "checkout", "--quiet", "--detach", WP510_G3_SOURCE_SHA])
            observed_sha = run(["git", "-C", str(clone), "rev-parse", "HEAD"]).stdout.strip()
            observed_tree = run(["git", "-C", str(clone), "rev-parse", "HEAD^{tree}"]).stdout.strip()
            status = run(["git", "-C", str(clone), "status", "--porcelain=v1", "--untracked-files=all"]).stdout
            receipt["source_binding"] = {
                "observed_sha": observed_sha,
                "observed_tree": observed_tree,
                "clean": status == "",
                "status_porcelain": status.splitlines(),
            }
            if observed_sha != WP510_G3_SOURCE_SHA:
                raise RuntimeError(f"exact-source mismatch: {observed_sha} != {WP510_G3_SOURCE_SHA}")
            if observed_tree != WP510_G3_TREE_SHA:
                raise RuntimeError(f"exact-tree mismatch: {observed_tree} != {WP510_G3_TREE_SHA}")
            if status:
                raise RuntimeError("disposable exact-source clone is unexpectedly dirty before probe")

            receipt["probe"] = execute_fixed_wp510_probe(clone)
            post_status = run(["git", "-C", str(clone), "status", "--porcelain=v1", "--untracked-files=all"]).stdout
            if post_status:
                raise RuntimeError("fixed probe mutated the disposable exact-source checkout")

            receipt["status"] = "PASS"
            receipt["classification"] = "WP510_G3_EXACT_SOURCE_HYGIENE_PLUS_FIXED_COMPONENT_EXECUTION_OBSERVED_PENDING_TARGET_ENVIRONMENT_ADMISSION"
            rc = 0
    except Exception as exc:
        receipt["status"] = "FAIL"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"
        rc = 1
    finally:
        receipt["completed_at_utc"] = utc_now()
        write_receipt(output, receipt)

    print(json.dumps({"status": receipt["status"], "receipt": str(output), "source_sha": WP510_G3_SOURCE_SHA}, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
