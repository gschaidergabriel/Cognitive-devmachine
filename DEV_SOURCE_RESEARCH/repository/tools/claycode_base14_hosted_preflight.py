#!/usr/bin/env python3
"""Hosted Ubuntu proxy preflight for the ClayCode BASE 14-work-package closure cascade.

This deliberately does NOT award any BASE work-package PASS and is not target-host
acceptance. It composes already-existing executable discriminators so shared regressions
are caught before the final Andreas Ubuntu production-chain run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark"
CHECK_PATHS = {
    "atomic_cas": ROOT / "research_entity/trigger_runs/spawn/spawn_20260809T111551Z/EXPERIMENT_ATOMIC_CAS.py",
    "module_init": ROOT / "research_entity/trigger_runs/spawn/spawn_20260809T1813p0700_claycode_module_init/EXPERIMENT_MODULE_INIT.py",
    "async_replay": ROOT / "research_entity/trigger_runs/spawn/spawn_20260809T1751p0700_claycode_async_replay/EXPERIMENT_ASYNC_REPLAY_CONTRACT.py",
    "http_sqlite": ROOT / "research_entity/trigger_runs/spawn/spawn-20260809T1814p0700-claycode-http-sqlite-0a7066/http_sqlite_vertical_probe.py",
}


def sh(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(cmd: list[str], timeout: int = 300) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    stdout = p.stdout or ""
    stderr = p.stderr or ""
    parsed = None
    try:
        parsed = json.loads(stdout)
    except Exception:
        pass
    return {
        "exit_code": p.returncode,
        "stdout_sha256": sh(stdout.encode("utf-8")),
        "stderr_sha256": sh(stderr.encode("utf-8")),
        "stderr_tail": stderr[-1200:],
        "parsed": parsed,
    }


def record(check_id: str, wp_refs: list[str], result: dict, passed: bool, evidence: dict | None = None) -> dict:
    return {
        "check_id": check_id,
        "supports_work_packages": wp_refs,
        "pass": bool(passed),
        "exit_code": result["exit_code"],
        "stdout_sha256": result["stdout_sha256"],
        "stderr_sha256": result["stderr_sha256"],
        "stderr_tail": result["stderr_tail"],
        "evidence": evidence or {},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    args = ap.parse_args()
    checks: list[dict] = []

    missing = [str(p.relative_to(ROOT)) for p in [GRAMMAR, *CHECK_PATHS.values()] if not p.exists()]
    if missing:
        raise SystemExit("missing preflight inputs: " + ", ".join(missing))

    with tempfile.TemporaryDirectory(prefix="claycode_base14_") as td:
        td = Path(td)

        strict_out = td / "strict.json"
        strict = run([
            sys.executable,
            "tools/claycode_strict_lalr_probe.py",
            "--grammar", str(GRAMMAR.relative_to(ROOT)),
            "--output", str(strict_out),
        ])
        strict_json = json.loads(strict_out.read_text(encoding="utf-8")) if strict_out.exists() else {}
        strict_pass = (
            strict["exit_code"] == 0
            and strict_json.get("strict_build_ok") is True
            and not strict_json.get("conflict_diagnostics")
        )
        checks.append(record(
            "WP02_STRICT_REPAIRED_LALR",
            ["CC-WP-02-PARSER-CANON"], strict, strict_pass,
            {
                "strict_build_ok": strict_json.get("strict_build_ok"),
                "strict_error": strict_json.get("strict_error"),
                "conflict_diagnostics": strict_json.get("conflict_diagnostics"),
                "grammar_sha256": strict_json.get("grammar_sha256"),
            },
        ))

        frontend_out = td / "frontend.json"
        frontend = run([
            sys.executable,
            "tools/claycode_base_frontend_validation.py",
            "--grammar", str(GRAMMAR.relative_to(ROOT)),
            "--output", str(frontend_out),
        ])
        frontend_json = json.loads(frontend_out.read_text(encoding="utf-8")) if frontend_out.exists() else {}
        frontend_pass = frontend["exit_code"] == 0 and frontend_json.get("pass") is True
        checks.append(record(
            "WP02_FULL_G9_DIALECT_BOUNDARY",
            ["CC-WP-02-PARSER-CANON", "CC-WP-11-FUZZ-CONFORMANCE"], frontend, frontend_pass,
            {
                "validator_pass": frontend_json.get("pass"),
                "source_count": len(frontend_json.get("sources") or []),
                "negative_cases_pass": all(x.get("pass") for x in (frontend_json.get("negative_cases") or [])),
                "positive_cases_pass": all(x.get("pass") for x in (frontend_json.get("positive_cases") or [])),
                "grammar_sha256": frontend_json.get("grammar_sha256"),
            },
        ))

    atomic = run([sys.executable, str(CHECK_PATHS["atomic_cas"].relative_to(ROOT))])
    aj = atomic.get("parsed") or {}
    atomic_checks = aj.get("checks") or {}
    atomic_pass = atomic["exit_code"] == 0 and bool(atomic_checks) and all(atomic_checks.values())
    checks.append(record(
        "WP03_WP09_ATOMIC_CAS_ABA",
        ["CC-WP-03-IR-TYPES", "CC-WP-09-CONCURRENCY-MEMORY", "CC-WP-11-FUZZ-CONFORMANCE"],
        atomic, atomic_pass,
        {"checks": atomic_checks, "seed": aj.get("seed")},
    ))

    module_init = run([sys.executable, str(CHECK_PATHS["module_init"].relative_to(ROOT))])
    mj = module_init.get("parsed") or {}
    mi = mj.get("module_init") or {}
    cr = mj.get("cycle_receipt") or {}
    module_pass = (
        module_init["exit_code"] == 0
        and mi.get("proposed_order_perturbation_failures") == 0
        and cr.get("canonical_receipt_order_mismatches") == 0
    )
    checks.append(record(
        "WP07_WP09_MODULE_INIT",
        ["CC-WP-07-RUNTIME-ABI-FFI", "CC-WP-09-CONCURRENCY-MEMORY", "CC-WP-11-FUZZ-CONFORMANCE"],
        module_init, module_pass,
        {
            "cases": mi.get("cases"),
            "order_perturbation_failures": mi.get("proposed_order_perturbation_failures"),
            "cycle_receipt_order_mismatches": cr.get("canonical_receipt_order_mismatches"),
        },
    ))

    async_replay = run([sys.executable, str(CHECK_PATHS["async_replay"].relative_to(ROOT))])
    arj = async_replay.get("parsed") or {}
    async_pass = async_replay["exit_code"] == 0 and arj.get("status") == "PASS"
    checks.append(record(
        "WP09_ASYNC_REPLAY",
        ["CC-WP-09-CONCURRENCY-MEMORY", "CC-WP-11-FUZZ-CONFORMANCE"],
        async_replay, async_pass,
        {"status": arj.get("status"), "seed": arj.get("seed")},
    ))

    httpdb = run([sys.executable, str(CHECK_PATHS["http_sqlite"].relative_to(ROOT))])
    hj = httpdb.get("parsed") or {}
    muts = hj.get("mutations") or {}
    http_pass = (
        httpdb["exit_code"] == 0
        and (hj.get("base") or {}).get("all_pass") is True
        and len(muts) >= 4
        and all(v.get("detected") is True for v in muts.values())
    )
    checks.append(record(
        "WP08_WP10_HTTP_SQLITE_PROXY",
        ["CC-WP-08-STDLIB-SDK", "CC-WP-10-GENERAL-APP-SUITE", "CC-WP-11-FUZZ-CONFORMANCE"],
        httpdb, http_pass,
        {
            "experiment_class": hj.get("experiment_class"),
            "base_tests_total": (hj.get("base") or {}).get("tests_total"),
            "base_tests_passed": (hj.get("base") or {}).get("tests_passed"),
            "mutations_detected": {k: v.get("detected") for k, v in muts.items()},
            "semantic_spec_hash": hj.get("semantic_spec_hash"),
            "generated_target_hash": hj.get("generated_target_hash"),
        },
    ))

    overall = all(x["pass"] for x in checks)
    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE14 hosted Ubuntu proxy preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": "chatgpt-secondary",
        "evidence_class": "HOSTED_UBUNTU_PROXY_NOT_TARGET_ACCEPTANCE",
        "target_acceptance_host": "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM",
        "counts_as_target_acceptance": False,
        "counts_as_work_package_pass": False,
        "runtime": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "checks": checks,
        "checks_passed": sum(1 for x in checks if x["pass"]),
        "checks_total": len(checks),
        "overall_pass": overall,
        "interpretation": (
            "PASS means the composed hosted proxy prerequisites survived together. It does not close any BASE work package, "
            "does not substitute for the production ClayCode chain, and does not substitute for execution on Andreas' Ubuntu target."
        ),
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")
    if not overall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
