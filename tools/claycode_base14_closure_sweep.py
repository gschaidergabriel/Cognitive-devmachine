#!/usr/bin/env python3
"""Fail-closed ClayCode BASE14 closure sweep.

This consolidates already-existing executable evidence into one reproducible CI run.
It is deliberately unable to mark a BASE work package PASS: project acceptance still
requires the production ClayCode pipeline and, where specified, Andreas' Ubuntu target.
The sweep's job is to turn undifferentiated OPEN state into exact failing boundaries.
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTONOMOUS = ROOT / "research_entity" / "claycode" / "autonomous"


def run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout[-200000:],
        "stderr": p.stderr[-100000:],
    }


def parse_json_stdout(row: dict) -> dict:
    try:
        return json.loads(row["stdout"])
    except Exception:
        return {}


def parse_python_literal_stdout(row: dict) -> dict:
    try:
        value = ast.literal_eval(row["stdout"].strip().splitlines()[-1])
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(AUTONOMOUS / "BASE14_CLOSURE_SWEEP_RECEIPT.json"))
    args = ap.parse_args()
    AUTONOMOUS.mkdir(parents=True, exist_ok=True)

    strict_out = AUTONOMOUS / "STRICT_LALR_D_REPAIR_RECEIPT.json"
    front_out = AUTONOMOUS / "BASE_FRONTEND_REPAIR_VALIDATION_RECEIPT.json"
    diff_out = AUTONOMOUS / "BASE_GRAMMAR_DIFFERENTIAL_RECEIPT.json"

    commands = {
        "strict_lalr": run([
            sys.executable, "tools/claycode_strict_lalr_probe.py",
            "--grammar", "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark",
            "--output", str(strict_out.relative_to(ROOT)),
        ]),
        "frontend": run([
            sys.executable, "tools/claycode_base_frontend_validation.py",
            "--grammar", "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark",
            "--output", str(front_out.relative_to(ROOT)),
        ]),
        "grammar_differential": run([
            sys.executable, "tools/claycode_base_grammar_differential.py",
            "--baseline", "research_entity/trigger_runs/claycode/claycode-20260809T1717p0700-all-workers-production-parser/D_LALR_GRAMMAR_CANDIDATE_V3.lark",
            "--repair", "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark",
            "--output", str(diff_out.relative_to(ROOT)),
        ]),
        "atomic_cas": run([
            sys.executable,
            "research_entity/trigger_runs/spawn/spawn_20260809T111551Z/EXPERIMENT_ATOMIC_CAS.py",
        ]),
        "http_sqlite": run([
            sys.executable,
            "research_entity/trigger_runs/spawn/spawn-20260809T1814p0700-claycode-http-sqlite-0a7066/http_sqlite_vertical_probe.py",
        ]),
        "frank_loop_native_shadow": run([
            sys.executable,
            "research_entity/trigger_runs/spawn/spawn-20260809T1742p0700-claycode-loop-eval-lowering/EXPERIMENT_REPRODUCER.py",
        ]),
    }

    strict = json.loads(strict_out.read_text()) if strict_out.exists() else {}
    frontend = json.loads(front_out.read_text()) if front_out.exists() else {}
    differential = json.loads(diff_out.read_text()) if diff_out.exists() else {}
    atomic = parse_json_stdout(commands["atomic_cas"])
    httpdb = parse_json_stdout(commands["http_sqlite"])
    frank_loop = parse_python_literal_stdout(commands["frank_loop_native_shadow"])

    effect_receipt_path = ROOT / "research_entity/trigger_runs/claycode/claycode-20260809T1728p0700-effect-closure-lowering/EXECUTABLE_RESEARCH_RECEIPT.json"
    effect = json.loads(effect_receipt_path.read_text()) if effect_receipt_path.exists() else {}

    checks = {
        "strict_lalr_repair": bool(strict.get("strict_build_ok") and not strict.get("conflict_diagnostics")),
        "full_current_frontend": bool(frontend.get("pass")),
        "baseline_repair_differential": bool(differential.get("pass")),
        "effect_closure_proxy": bool(
            effect.get("results", {}).get("graph_closure_mismatches") == 0
            and effect.get("results", {}).get("interpreter_vs_lowered_output_mismatches") == 0
            and effect.get("results", {}).get("interpreter_vs_lowered_trace_mismatches") == 0
        ),
        "atomic_cas_proxy": bool(atomic.get("checks") and all(atomic["checks"].values())),
        "http_sqlite_proxy": bool(
            httpdb.get("base", {}).get("all_pass")
            and httpdb.get("mutations")
            and all(x.get("detected") for x in httpdb["mutations"].values())
        ),
        "frank_loop_native_shadow": bool(frank_loop.get("mismatches") == 0 and frank_loop.get("cases", 0) >= 100000),
    }

    wp = {
        "CC-WP-01-SPEC-FREEZE": {"release_pass": False, "remaining": ["freeze one production semantic contract after frontend/typed-IR integration"]},
        "CC-WP-02-PARSER-CANON": {"release_pass": False, "evidence_checks": ["strict_lalr_repair", "full_current_frontend", "baseline_repair_differential"], "remaining": ["typed canonical AST + semantic-hash integration", "production parser selection/freeze"]},
        "CC-WP-03-IR-TYPES": {"release_pass": False, "remaining": ["production typed canonical IR integration across admitted G9/Dialect"]},
        "CC-WP-04-TYPE-EFFECT": {"release_pass": False, "evidence_checks": ["effect_closure_proxy"], "remaining": ["integrate verified effect closure into production checker"]},
        "CC-WP-05-EVALUATOR": {"release_pass": False, "evidence_checks": ["frank_loop_native_shadow"], "remaining": ["production evaluator consumes production typed IR"]},
        "CC-WP-06-COMPILER-LOWERING": {"release_pass": False, "evidence_checks": ["effect_closure_proxy", "frank_loop_native_shadow"], "remaining": ["real ClayCode backend lowering, not hand-emitted/proxy Python/C", "translation-validation receipts"]},
        "CC-WP-07-RUNTIME-ABI-FFI": {"release_pass": False, "evidence_checks": ["http_sqlite_proxy"], "remaining": ["opaque typed host resource ABI", "OS/runtime authority enforcement", "Ubuntu runtime receipt"]},
        "CC-WP-08-STDLIB-SDK": {"release_pass": False, "evidence_checks": ["http_sqlite_proxy"], "remaining": ["production stdlib adapters for files/process/HTTP/DB/UI/backend interop"]},
        "CC-WP-09-CONCURRENCY-MEMORY": {"release_pass": False, "evidence_checks": ["atomic_cas_proxy", "http_sqlite_proxy"], "remaining": ["production async/cancellation/atomic/resource-memory implementation", "Ubuntu differential"]},
        "CC-WP-10-GENERAL-APP-SUITE": {"release_pass": False, "remaining": ["APP-01..APP-10 through production compiler on Ubuntu; proxies do not count"]},
        "CC-WP-11-FUZZ-CONFORMANCE": {"release_pass": False, "evidence_checks": ["baseline_repair_differential", "effect_closure_proxy", "atomic_cas_proxy", "http_sqlite_proxy"], "remaining": ["whole production compiler/runtime mutation/fuzz/roundtrip/conformance suite"]},
        "CC-WP-12-CORPUS-HELDOUT": {"release_pass": False, "remaining": ["semantics-derived positive/negative generator and leak-resistant held-out suite"]},
        "CC-WP-13-HARNESS-HANDOFF": {"release_pass": False, "evidence_checks": ["frank_loop_native_shadow"], "remaining": ["compile real frozen FRANK subsystem through production chain", "prove no semantic escape hatch"]},
        "CC-WP-14-BASE-AUDIT": {"release_pass": False, "remaining": ["general-purpose manifest", "Ubuntu application receipts", "unresolved-language-counterexample audit", "explicit GENERAL_PURPOSE_GATE decision"]},
    }
    for payload in wp.values():
        ev = payload.get("evidence_checks", [])
        payload["evidence_regression_pass"] = bool(ev) and all(checks.get(x, False) for x in ev)

    regressions = [name for name, ok in checks.items() if not ok]
    out = {
        "schema_version": "1.0",
        "run": "ClayCode BASE14 machine closure sweep",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": {"actor_id": "chatgpt-secondary", "provider": "OpenAI", "model": "GPT-5.6 Sol"},
        "scope": "Regression consolidation and exact blocker localization; never automatic BASE promotion.",
        "checks": checks,
        "regressions": regressions,
        "work_packages": wp,
        "release_packages_passed": 0,
        "release_packages_total": 14,
        "external_acceptance_boundary": [
            "Andreas Ubuntu developer host is not this GitHub Actions runner",
            "production ClayCode frontend->typed IR->checker->evaluator->lowerer->runtime is not yet one integrated release artifact",
            "APP-01..APP-10 need production-pipeline Ubuntu execution receipts",
        ],
        "commands": commands,
        "verdict": "REGRESSION_SWEEP_PASS_NO_BASE_PROMOTION" if not regressions else "REGRESSION_SWEEP_FAILED",
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "checks": checks, "regressions": regressions}, indent=2))
    return 0 if not regressions else 1


if __name__ == "__main__":
    raise SystemExit(main())
