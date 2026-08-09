#!/usr/bin/env python3
"""One-command ClayCode BASE evidence runner for Andreas' Ubuntu developer host.

This runner is a target-host diagnostic/convergence gate. It executes the current
parser/canonicalizer, typed IR, pure compiler, effect compiler -> sealed runtime bridge,
package linker, runtime, fuzz, corpus, real FRANK subsystem handoff, and the hardened
10-class application preflight on the attested Ubuntu developer system.

It never promotes BASE by itself. WP10 still requires real non-proxy per-application
target receipts, and WP14 requires the final manifest plus zero-P0/P1 audit.

Grammar contract:
- WP02 strict/full-corpus evidence is pinned to declarative V9 and hash-checked.
- Dedicated executable typed-fn/compiler validators retain their own versioned grammar
  contract until a later candidate (for example V10/V13) is explicitly promoted.
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
WP02_GRAMMAR = "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
EXPECTED_TARGET_ID = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
STRICT_OUT = ROOT / "research_entity/claycode/target_receipts/STRICT_LALR_D_V9_TARGET_RECEIPT.json"
FRONTEND_OUT = ROOT / "research_entity/claycode/target_receipts/BASE_FRONTEND_V9_TARGET_RECEIPT.json"
EFFECT_OUT = ROOT / "research_entity/claycode/target_receipts/BASE_EFFECT_PIPELINE_TARGET_RECEIPT.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def run_capture(argv: list[str], *, timeout: int = 900) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "argv": argv,
            "started_at": started,
            "returncode": cp.returncode,
            "process_pass": cp.returncode == 0,
            "stdout_tail": cp.stdout[-8000:],
            "stderr_tail": cp.stderr[-8000:],
        }
    except Exception as exc:
        return {
            "argv": argv,
            "started_at": started,
            "returncode": None,
            "process_pass": False,
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
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                result[k] = v.strip().strip('"')
    return result


def executable_version(argv: list[str]) -> dict[str, Any]:
    if shutil.which(argv[0]) is None:
        return {"available": False, "argv": argv}
    cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)
    lines = (cp.stdout or cp.stderr).strip().splitlines()
    return {"available": cp.returncode == 0, "argv": argv, "first_line": lines[0] if lines else ""}


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


def receipt_semantic_pass(path: Path) -> tuple[bool, dict[str, Any]]:
    data = json_file(path)
    return data.get("pass") is True, {
        "path": str(path.relative_to(ROOT)),
        "pass": data.get("pass"),
        "sha256": sha256_file(path) if path.exists() else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUT)
    ap.add_argument(
        "--allow-dirty-input",
        action="store_true",
        help="Run diagnostics from a dirty checkout, but never count that run as release target evidence.",
    )
    args = ap.parse_args()

    created_at = datetime.now(timezone.utc).isoformat()
    target_id = os.environ.get("CLAYCODE_TARGET_HOST_ID", "")
    os_release = read_os_release()
    linux = platform.system() == "Linux"
    ubuntu = os_release.get("ID", "").lower() == "ubuntu"
    not_ci = os.environ.get("GITHUB_ACTIONS", "").lower() != "true" and os.environ.get("CI", "").lower() not in {"1", "true", "yes"}
    target_attested = target_id == EXPECTED_TARGET_ID and linux and ubuntu and not_ci

    try:
        git_head = git_text("rev-parse", "HEAD")
        git_branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
        dirty_lines = git_text("status", "--porcelain").splitlines()
    except Exception as exc:
        git_head, git_branch, dirty_lines = "", "", [f"GIT_ERROR:{exc}"]

    clean_input = not dirty_lines
    diagnostic_input_allowed = clean_input or args.allow_dirty_input
    release_quality_input = clean_input

    wp02_path = ROOT / WP02_GRAMMAR
    wp02_grammar_sha256 = sha256_file(wp02_path) if wp02_path.exists() else None

    host = {
        "target_id_claim": target_id,
        "expected_target_id": EXPECTED_TARGET_ID,
        "target_attested": target_attested,
        "attestation_class": "OPERATOR_ENVIRONMENT_ASSERTION_PLUS_UBUNTU_HOST_FINGERPRINT_AND_NON_CI_GATE",
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
        "github_actions": os.environ.get("GITHUB_ACTIONS"),
        "ci": os.environ.get("CI"),
    }
    preconditions = {
        "target_id_exact": target_id == EXPECTED_TARGET_ID,
        "linux": linux,
        "ubuntu": ubuntu,
        "not_ci": not_ci,
        "clean_release_input": release_quality_input,
        "cc_available": bool(host["cc"]["available"]),
        "git_head_present": bool(git_head),
        "wp02_v9_grammar_present": wp02_path.exists(),
    }

    before = snapshot_receipts()
    steps: list[dict[str, Any]] = []
    can_execute = target_attested and diagnostic_input_allowed and preconditions["cc_available"] and bool(git_head) and wp02_path.exists()

    if can_execute:
        commands: list[tuple[str, list[str], str, bool, Path | None]] = [
            (
                "WP02_STRICT_V9",
                [sys.executable, "tools/claycode_strict_lalr_probe.py", "--grammar", WP02_GRAMMAR, "--output", str(STRICT_OUT.relative_to(ROOT))],
                "CC-WP-02-PARSER-CANON", True, STRICT_OUT,
            ),
            (
                "WP02_FULL_CORPUS_V9",
                [sys.executable, "tools/claycode_base_frontend_validation.py", "--grammar", WP02_GRAMMAR, "--output", str(FRONTEND_OUT.relative_to(ROOT))],
                "CC-WP-02-PARSER-CANON", True, FRONTEND_OUT,
            ),
            ("WP02_CANONICALIZER_ACTIVE_GRAMMAR", [sys.executable, "tools/claycode_base_canonicalizer_validation.py"], "CC-WP-02-PARSER-CANON", True, ROOT / "research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json"),
            ("WP03_TYPED_IR_EXECUTABLE_SLICE", [sys.executable, "tools/claycode_wp03_typed_ir_validation.py"], "CC-WP-03-IR-TYPES", True, ROOT / "research_entity/claycode/autonomous/WP03_TYPED_IR_RECEIPT.json"),
            ("WP03_06_PURE_NATIVE_DIFFERENTIAL", [sys.executable, "tools/claycode_base_pure_toolchain_validation.py"], "CC-WP-03..CC-WP-06", True, ROOT / "research_entity/claycode/autonomous/BASE_PURE_TOOLCHAIN_RECEIPT.json"),
            ("WP05_06_LARGE_INT_DIVISION", [sys.executable, "tools/claycode_int_division_regression.py"], "CC-WP-05..CC-WP-06", True, ROOT / "research_entity/claycode/autonomous/BASE_INT_DIVISION_REGRESSION_RECEIPT.json"),
            (
                "WP04_08_EFFECT_PIPELINE",
                [sys.executable, "tools/claycode_base_effect_pipeline.py", "--self-test", "--output", str(EFFECT_OUT.relative_to(ROOT))],
                "CC-WP-04..CC-WP-08", True, EFFECT_OUT,
            ),
            (
                "WP04_08_REAL_SEALED_EFFECT_BRIDGE",
                [sys.executable, "tools/claycode_effect_runtime_bridge_validation.py"],
                "CC-WP-04..CC-WP-08", True, ROOT / "research_entity/claycode/autonomous/BASE_EFFECT_REAL_RUNTIME_BRIDGE_RECEIPT.json",
            ),
            ("WP07_08_PACKAGE_LINK", [sys.executable, "tools/claycode_base_package_validation.py"], "CC-WP-07..CC-WP-08", True, ROOT / "research_entity/claycode/autonomous/BASE_PACKAGE_LINK_RECEIPT.json"),
            ("WP07_09_RUNTIME_ABI_FFI", [sys.executable, "tools/claycode_base_runtime_validation.py"], "CC-WP-07..CC-WP-09", True, ROOT / "research_entity/claycode/autonomous/BASE_RUNTIME_CAPABILITY_RECEIPT.json"),
            ("WP09_CANCELLATION_ERROR", [sys.executable, "tools/claycode_base_concurrency_validation.py"], "CC-WP-09-CONCURRENCY-MEMORY", True, ROOT / "research_entity/claycode/autonomous/BASE_CONCURRENCY_CANCELLATION_RECEIPT.json"),
            ("WP11_FUZZ_CONFORMANCE", [sys.executable, "tools/claycode_base_fuzz_conformance.py"], "CC-WP-11-FUZZ-CONFORMANCE", True, ROOT / "research_entity/claycode/autonomous/BASE_FUZZ_CONFORMANCE_RECEIPT.json"),
            ("WP12_CORPUS_HELDOUT", [sys.executable, "tools/claycode_base_corpus_generator.py"], "CC-WP-12-CORPUS-HELDOUT", True, ROOT / "research_entity/claycode/corpus/base_v1/CORPUS_MANIFEST.json"),
            ("WP13_FRANK_SCORE_HANDOFF", [sys.executable, "tools/claycode_frank_score_handoff_validation.py"], "CC-WP-13-HARNESS-HANDOFF", True, ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_SCORE_HANDOFF_RECEIPT.json"),
            (
                "WP10_TEN_CLASS_PROXY_PREFLIGHT_V2",
                [sys.executable, "tools/claycode_base_application_proxy_suite_v2.py"],
                "CC-WP-10-GENERAL-APP-SUITE", False, ROOT / "research_entity/claycode/autonomous/BASE_APPLICATION_PROXY_SUITE_V2_RECEIPT.json",
            ),
        ]

        for step_id, argv, supports, target_component_candidate, receipt_path in commands:
            row = run_capture(argv)
            semantic_pass = bool(row["process_pass"])
            semantic_check: dict[str, Any] | None = None

            if step_id == "WP02_STRICT_V9":
                strict = json_file(STRICT_OUT)
                grammar_bound = strict.get("grammar_path") == WP02_GRAMMAR and strict.get("grammar_sha256") == wp02_grammar_sha256
                semantic_pass = bool(row["process_pass"] and strict.get("strict_build_ok") is True and not strict.get("conflict_diagnostics") and grammar_bound)
                semantic_check = {
                    "strict_build_ok": strict.get("strict_build_ok"),
                    "conflict_diagnostics": strict.get("conflict_diagnostics"),
                    "strict_error": strict.get("strict_error"),
                    "grammar_path": strict.get("grammar_path"),
                    "grammar_sha256": strict.get("grammar_sha256"),
                    "grammar_bound_to_wp02_v9": grammar_bound,
                }
            elif step_id == "WP02_FULL_CORPUS_V9":
                front = json_file(FRONTEND_OUT)
                grammar_bound = front.get("grammar_path") == WP02_GRAMMAR and front.get("grammar_sha256") == wp02_grammar_sha256
                semantic_pass = bool(row["process_pass"] and front.get("pass") is True and grammar_bound)
                semantic_check = {
                    "pass": front.get("pass"),
                    "grammar_path": front.get("grammar_path"),
                    "grammar_sha256": front.get("grammar_sha256"),
                    "grammar_bound_to_wp02_v9": grammar_bound,
                }
            elif step_id == "WP02_CANONICALIZER_ACTIVE_GRAMMAR":
                canonical = json_file(ROOT / "research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json")
                grammar_bound = canonical.get("grammar") == WP02_GRAMMAR
                semantic_pass = bool(row["process_pass"] and canonical.get("pass") is True and grammar_bound)
                semantic_check = {"pass": canonical.get("pass"), "grammar": canonical.get("grammar"), "grammar_bound_to_wp02_v9": grammar_bound}
            elif receipt_path is not None:
                embedded_pass, embedded = receipt_semantic_pass(receipt_path)
                semantic_pass = bool(row["process_pass"] and embedded_pass)
                semantic_check = embedded

            row.update({
                "step_id": step_id,
                "supports": supports,
                "executed_on_attested_target": True,
                "semantic_pass": semantic_pass,
                "semantic_check": semantic_check,
                "can_count_as_target_component_evidence": bool(target_component_candidate and release_quality_input),
            })
            steps.append(row)

    after = snapshot_receipts()
    changed = {path: digest for path, digest in after.items() if before.get(path) != digest}

    target_component_steps = [s for s in steps if s["can_count_as_target_component_evidence"]]
    component_steps_pass = bool(target_component_steps) and all(s["semantic_pass"] for s in target_component_steps)
    proxy_steps = [s for s in steps if not s["can_count_as_target_component_evidence"] and s["step_id"].startswith("WP10_")]

    unresolved: list[str] = []
    if not target_attested:
        unresolved.append("TARGET_HOST_NOT_ATTESTED_AS_ANDREAS_UBUNTU_NON_CI")
    if not clean_input:
        unresolved.append("DIRTY_INPUT_CHECKOUT_NOT_RELEASE_EVIDENCE")
    if not component_steps_pass:
        unresolved.append("ONE_OR_MORE_TARGET_COMPONENT_GATES_FAILED_OR_NOT_EXECUTED")
    unresolved += [
        "CC-WP-10_REQUIRES_REAL_NON_PROXY_PER_APPLICATION_TARGET_RECEIPTS",
        "CC-WP-13_FULL_FRANK_HANDOFF_REMAINS_BEYOND_SCORE_SUBSYSTEM",
        "CC-WP-14_REQUIRES_FINAL_GENERAL_PURPOSE_MANIFEST_AND_ZERO_P0_P1_AUDIT",
    ]

    report = {
        "schema_version": "1.4",
        "receipt_id": "ANDREAS_UBUNTU_BASE_TARGET_GATE",
        "created_at": created_at,
        "host": host,
        "preconditions": preconditions,
        "execution_allowed": can_execute,
        "wp02_parser_contract": {
            "grammar_path": WP02_GRAMMAR,
            "grammar_sha256": wp02_grammar_sha256,
            "strict_receipt_path": str(STRICT_OUT.relative_to(ROOT)),
            "frontend_receipt_path": str(FRONTEND_OUT.relative_to(ROOT)),
            "scope": "CC-WP-02 declarative strict/full-corpus only; executable typed-fn evidence remains separately versioned",
        },
        "steps": steps,
        "target_component_steps_pass": component_steps_pass,
        "wp10_proxy_preflight_pass": bool(proxy_steps) and all(s["semantic_pass"] for s in proxy_steps),
        "changed_or_new_receipt_hashes": changed,
        "base_release_pass": False,
        "general_purpose_gate_pass": False,
        "unresolved": unresolved,
        "promotion_law": (
            "Individual target components count only when their own semantic receipt is PASS on a clean attested non-CI Andreas Ubuntu checkout. "
            "WP02 strict/full-corpus/canonicalizer evidence must be bound to V9. WP10/WP13-full/WP14 are never promoted from proxy execution. "
            "Model output, descriptors, package text and symbolic capability names are not execution authority."
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
        "clean_input": clean_input,
        "wp02_grammar": WP02_GRAMMAR,
        "wp02_grammar_sha256": wp02_grammar_sha256,
        "target_component_steps_pass": component_steps_pass,
        "wp10_proxy_preflight_pass": report["wp10_proxy_preflight_pass"],
        "base_release_pass": False,
        "unresolved": unresolved,
        "output": str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output),
    }, ensure_ascii=False))

    return 0 if target_attested and clean_input and component_steps_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())