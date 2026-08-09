#!/usr/bin/env python3
"""One-command ClayCode BASE target-host evidence runner.

This runner exists to collapse the remaining hosted-CI -> real-target gap. It MUST be
executed on Andreas' actual Ubuntu Linux developer system from a clean repository
checkout. It gathers target-host identity plus the current production parser/IR/compiler/
runtime/fuzz/corpus/FRANK integration evidence in one deterministic receipt.

Important: this runner never promotes ClayCode BASE by itself. Some included application
checks are explicitly proxy checks even when executed on the target machine (for example
the headless GUI proxy). Final CC-WP-10/14 promotion still requires real per-application
target receipts and the release-manifest audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_TARGET_GATE.json"
GRAMMAR = "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
EXPECTED_TARGET_ID = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_capture(argv: list[str], *, timeout: int = 900) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        cp = subprocess.run(
            argv,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "started_at": started,
            "returncode": cp.returncode,
            "pass": cp.returncode == 0,
            "stdout_tail": cp.stdout[-8000:],
            "stderr_tail": cp.stderr[-8000:],
        }
    except Exception as exc:
        return {
            "argv": argv,
            "started_at": started,
            "returncode": None,
            "pass": False,
            "exception": f"{type(exc).__name__}: {exc}",
        }


def git_text(*args: str) -> str:
    cp = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if cp.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {cp.stderr.strip()}")
    return cp.stdout.strip()


def read_os_release() -> dict[str, str]:
    result: dict[str, str] = {}
    p = Path("/etc/os-release")
    if not p.exists():
        return result
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        result[k] = v.strip().strip('"')
    return result


def executable_version(argv: list[str]) -> dict[str, Any]:
    if shutil.which(argv[0]) is None:
        return {"available": False, "argv": argv}
    cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)
    text = (cp.stdout or cp.stderr).strip().splitlines()
    return {"available": cp.returncode == 0, "argv": argv, "first_line": text[0] if text else ""}


def snapshot_receipts() -> dict[str, str]:
    roots = [
        ROOT / "research_entity/claycode/autonomous",
        ROOT / "research_entity/claycode/target_receipts",
        ROOT / "research_entity/claycode/corpus/base_v1",
    ]
    rows: dict[str, str] = {}
    for base in roots:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                rows[str(p.relative_to(ROOT))] = sha256_file(p)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUT)
    ap.add_argument(
        "--allow-dirty-input",
        action="store_true",
        help="Development-only escape hatch. A dirty input checkout cannot count as release target evidence.",
    )
    args = ap.parse_args()

    created_at = datetime.now(timezone.utc).isoformat()
    target_id = os.environ.get("CLAYCODE_TARGET_HOST_ID", "")
    os_release = read_os_release()
    ubuntu = os_release.get("ID", "").lower() == "ubuntu"
    linux = platform.system() == "Linux"
    target_attested = target_id == EXPECTED_TARGET_ID and linux and ubuntu

    try:
        git_head = git_text("rev-parse", "HEAD")
        git_branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
        dirty_lines = git_text("status", "--porcelain").splitlines()
    except Exception as exc:
        git_head, git_branch, dirty_lines = "", "", [f"GIT_ERROR:{exc}"]

    clean_input = not dirty_lines
    reproducible_input = clean_input or args.allow_dirty_input

    host = {
        "target_id_claim": target_id,
        "expected_target_id": EXPECTED_TARGET_ID,
        "target_attested": target_attested,
        "attestation_class": "OPERATOR_ENVIRONMENT_ASSERTION_PLUS_UBUNTU_HOST_FINGERPRINT",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "node": platform.node(),
        "kernel": platform.release(),
        "os_release": os_release,
        "python": executable_version([sys.executable, "--version"]),
        "cc": executable_version(["cc", "--version"]),
        "git": executable_version(["git", "--version"]),
        "git_head": git_head,
        "git_branch": git_branch,
        "input_checkout_clean": clean_input,
        "dirty_input_entries": dirty_lines[:100],
        "allow_dirty_input": bool(args.allow_dirty_input),
    }

    preconditions = {
        "target_id_exact": target_id == EXPECTED_TARGET_ID,
        "linux": linux,
        "ubuntu": ubuntu,
        "clean_or_explicit_dev_override": reproducible_input,
        "cc_available": bool(host["cc"]["available"]),
        "git_head_present": bool(git_head),
    }

    steps: list[dict[str, Any]] = []
    before = snapshot_receipts()

    # Do not execute and accidentally create target-looking receipts on a hosted/non-target host.
    can_execute = target_attested and reproducible_input and preconditions["cc_available"] and bool(git_head)
    if can_execute:
        commands: list[tuple[str, list[str], str, bool]] = [
            (
                "WP02_STRICT_V7",
                [sys.executable, "tools/claycode_strict_lalr_probe.py", "--grammar", GRAMMAR,
                 "--output", "research_entity/claycode/target_receipts/STRICT_LALR_D_V7_TARGET_RECEIPT.json"],
                "CC-WP-02-PARSER-CANON",
                True,
            ),
            (
                "WP02_FULL_CORPUS_V7",
                [sys.executable, "tools/claycode_base_frontend_validation.py", "--grammar", GRAMMAR,
                 "--output", "research_entity/claycode/target_receipts/BASE_FRONTEND_V7_TARGET_RECEIPT.json"],
                "CC-WP-02-PARSER-CANON",
                True,
            ),
            (
                "WP02_CANONICALIZER",
                [sys.executable, "tools/claycode_base_canonicalizer_validation.py"],
                "CC-WP-02-PARSER-CANON",
                True,
            ),
            (
                "WP03_TYPED_IR",
                [sys.executable, "tools/claycode_wp03_typed_ir_validation.py"],
                "CC-WP-03-IR-TYPES",
                True,
            ),
            (
                "WP03_06_PURE_NATIVE_DIFFERENTIAL",
                [sys.executable, "tools/claycode_base_pure_toolchain_validation.py"],
                "CC-WP-03..CC-WP-06",
                True,
            ),
            (
                "WP04_08_EFFECT_PIPELINE",
                [sys.executable, "tools/claycode_base_effect_pipeline.py", "--self-test",
                 "--output", "research_entity/claycode/target_receipts/BASE_EFFECT_PIPELINE_TARGET_RECEIPT.json"],
                "CC-WP-04..CC-WP-08",
                True,
            ),
            (
                "WP07_09_RUNTIME_ABI_FFI",
                [sys.executable, "tools/claycode_base_runtime_validation.py"],
                "CC-WP-07..CC-WP-09",
                True,
            ),
            (
                "WP11_FUZZ_CONFORMANCE",
                [sys.executable, "tools/claycode_base_fuzz_conformance.py"],
                "CC-WP-11-FUZZ-CONFORMANCE",
                True,
            ),
            (
                "WP12_CORPUS_HELDOUT",
                [sys.executable, "tools/claycode_base_corpus_generator.py"],
                "CC-WP-12-CORPUS-HELDOUT",
                True,
            ),
            (
                "WP13_FRANK_SCORE_HANDOFF",
                [sys.executable, "tools/claycode_frank_score_handoff_validation.py"],
                "CC-WP-13-HARNESS-HANDOFF",
                True,
            ),
            (
                "WP10_TEN_CLASS_PROXY_PREFLIGHT",
                [sys.executable, "tools/claycode_base_application_proxy_suite.py"],
                "CC-WP-10-GENERAL-APP-SUITE",
                False,
            ),
        ]
        for step_id, argv, supports, can_count_as_target_component in commands:
            row = run_capture(argv)
            row.update({
                "step_id": step_id,
                "supports": supports,
                "executed_on_attested_target": True,
                "can_count_as_target_component_evidence": can_count_as_target_component,
            })
            steps.append(row)
            # Continue after failure: one run should expose the full causal failure set.

    after = snapshot_receipts()
    changed = {
        path: digest
        for path, digest in after.items()
        if before.get(path) != digest
    }

    required_target_component_steps = [s for s in steps if s["can_count_as_target_component_evidence"]]
    component_steps_pass = bool(required_target_component_steps) and all(s["pass"] for s in required_target_component_steps)
    proxy_steps = [s for s in steps if not s["can_count_as_target_component_evidence"]]

    # Fail closed: WP10 has real target applications beyond the proxy suite, and WP14 is a
    # dependent final manifest/audit. This runner is the target evidence collector, not a
    # replacement for those acceptance laws.
    unresolved = []
    if not target_attested:
        unresolved.append("TARGET_HOST_NOT_ATTESTED_AS_ANDREAS_UBUNTU")
    if not reproducible_input:
        unresolved.append("DIRTY_INPUT_CHECKOUT")
    if not component_steps_pass:
        unresolved.append("ONE_OR_MORE_TARGET_COMPONENT_GATES_FAILED_OR_NOT_EXECUTED")
    unresolved.extend([
        "CC-WP-10_REQUIRES_REAL_NON_PROXY_PER_APPLICATION_TARGET_RECEIPTS",
        "CC-WP-14_REQUIRES_FINAL_GENERAL_PURPOSE_MANIFEST_AND_ZERO_P0_P1_AUDIT",
    ])

    report = {
        "schema_version": "1.0",
        "receipt_id": "ANDREAS_UBUNTU_BASE_TARGET_GATE",
        "created_at": created_at,
        "host": host,
        "preconditions": preconditions,
        "execution_allowed": can_execute,
        "steps": steps,
        "component_steps_pass": component_steps_pass,
        "proxy_steps_pass": bool(proxy_steps) and all(s["pass"] for s in proxy_steps),
        "changed_or_new_receipt_hashes": changed,
        "base_release_pass": False,
        "general_purpose_gate_pass": False,
        "unresolved": unresolved,
        "promotion_law": (
            "This receipt may support individual work-package target evidence only where the package acceptance law is fully met. "
            "It never promotes WP10 or WP14 from proxy execution, never treats model output as execution authority, and never "
            "replaces the final CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST audit."
        ),
        "operator_command": (
            "CLAYCODE_TARGET_HOST_ID=ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM "
            "python tools/claycode_andreas_ubuntu_target_gate.py"
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "target_attested": target_attested,
        "component_steps_pass": component_steps_pass,
        "base_release_pass": False,
        "unresolved": unresolved,
        "output": str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output),
    }, ensure_ascii=False))

    # Zero means the target component battery is green, not BASE release PASS.
    return 0 if target_attested and reproducible_input and component_steps_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
