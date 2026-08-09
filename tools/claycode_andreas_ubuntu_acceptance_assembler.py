#!/usr/bin/env python3
"""Assemble the one canonical Andreas-Ubuntu ClayCode BASE acceptance receipt.

This is deliberately fail-closed. It is intended to run only on the manually registered
Andreas Ubuntu developer system after the component target gate and the real ten-app
suite. It does not infer target evidence from hosted CI, does not accept proxy apps, and
does not accept a bounded FRANK subsystem as FULL_FRANK_HANDOFF.

On failure it writes only a diagnostic under target_receipts/. It creates the canonical
research_entity/claycode/target/ANDREAS_UBUNTU_BASE_ACCEPTANCE.json only when every hard
rule in ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json is satisfied.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
CONTRACT = ROOT / "research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json"
TARGET_GATE = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_TARGET_GATE.json"
APPS = ROOT / "research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json"
FULL_FRANK = ROOT / "research_entity/claycode/target/FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json"
COUNTEREXAMPLES = ROOT / "research_entity/claycode/base/UNRESOLVED_LANGUAGE_COUNTEREXAMPLES.json"
FINAL = ROOT / "research_entity/claycode/target/ANDREAS_UBUNTU_BASE_ACCEPTANCE.json"
DIAGNOSTIC = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_ACCEPTANCE_ASSEMBLY_DIAGNOSTIC.json"
COMPILER = ROOT / "tools/claycode_base_compiler.py"
EFFECT_PIPELINE = ROOT / "tools/claycode_base_effect_pipeline.py"

WP_REQUIREMENTS = {
    "CC-WP-02-PARSER-CANON": ["WP02_STRICT_V7", "WP02_FULL_CORPUS_V7", "WP02_CANONICALIZER"],
    "CC-WP-03-IR-TYPES": ["WP03_TYPED_IR", "WP03_06_PURE_NATIVE_DIFFERENTIAL"],
    "CC-WP-04-TYPE-EFFECT": ["WP04_08_EFFECT_PIPELINE", "WP04_08_REAL_SEALED_EFFECT_BRIDGE"],
    "CC-WP-05-EVALUATOR": ["WP03_06_PURE_NATIVE_DIFFERENTIAL"],
    "CC-WP-06-COMPILER-LOWERING": ["WP03_06_PURE_NATIVE_DIFFERENTIAL", "WP04_08_REAL_SEALED_EFFECT_BRIDGE"],
    "CC-WP-07-RUNTIME-ABI-FFI": ["WP04_08_REAL_SEALED_EFFECT_BRIDGE", "WP07_08_PACKAGE_LINK", "WP07_09_RUNTIME_ABI_FFI"],
    "CC-WP-08-STDLIB-SDK": ["WP04_08_REAL_SEALED_EFFECT_BRIDGE", "WP07_08_PACKAGE_LINK", "WP07_09_RUNTIME_ABI_FFI"],
    "CC-WP-09-CONCURRENCY-MEMORY": ["WP07_09_RUNTIME_ABI_FFI"],
    "CC-WP-10-GENERAL-APP-SUITE": [],
    "CC-WP-11-FUZZ-CONFORMANCE": ["WP11_FUZZ_CONFORMANCE"],
    "CC-WP-12-CORPUS-HELDOUT": ["WP12_CORPUS_HELDOUT"],
    "CC-WP-13-HARNESS-HANDOFF": ["WP13_FRANK_SCORE_HANDOFF"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def host_identity() -> tuple[bool, dict[str, Any]]:
    tool = ROOT / "tools/claycode_target_host_identity.py"
    cp = subprocess.run(
        [sys.executable, str(tool), "verify", "--json"],
        cwd=ROOT, text=True, capture_output=True, timeout=15, check=False,
    )
    try:
        payload = json.loads(cp.stdout)
    except Exception:
        payload = {"verified": False, "errors": ["HOST_IDENTITY_OUTPUT_INVALID"], "stdout": cp.stdout[-1000:], "stderr": cp.stderr[-1000:]}
    return cp.returncode == 0 and payload.get("verified") is True, payload


def step_map(gate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(x.get("step_id")): x for x in gate.get("steps", []) if isinstance(x, dict) and x.get("step_id")}


def step_evidence(step: dict[str, Any]) -> dict[str, Any]:
    sem = step.get("semantic_check") if isinstance(step.get("semantic_check"), dict) else {}
    return {
        "test_id": step.get("step_id"),
        "argv": step.get("argv"),
        "semantic_pass": step.get("semantic_pass"),
        "process_pass": step.get("process_pass"),
        "executed_on_attested_target": step.get("executed_on_attested_target"),
        "can_count_as_target_component_evidence": step.get("can_count_as_target_component_evidence"),
        "receipt_path": sem.get("path"),
        "receipt_sha256": sem.get("sha256"),
        "stdout_sha256": step.get("stdout_sha256"),
        "stderr_sha256": step.get("stderr_sha256"),
    }


def main() -> int:
    failures: list[str] = []
    missing = [str(p.relative_to(ROOT)) for p in (CONTRACT, TARGET_GATE, APPS, COUNTEREXAMPLES, COMPILER, EFFECT_PIPELINE) if not p.exists()]
    if missing:
        failures.extend("MISSING:" + x for x in missing)

    contract = load(CONTRACT) if CONTRACT.exists() else {}
    gate = load(TARGET_GATE) if TARGET_GATE.exists() else {}
    apps_doc = load(APPS) if APPS.exists() else {}
    ledger = load(COUNTEREXAMPLES) if COUNTEREXAMPLES.exists() else {}
    frank = load(FULL_FRANK) if FULL_FRANK.exists() else {}
    host_ok, host = host_identity()

    if not host_ok:
        failures.append("OWNER_REGISTERED_TARGET_HOST_NOT_VERIFIED")
    if contract.get("target_host") != TARGET:
        failures.append("CONTRACT_TARGET_MISMATCH")
    if gate.get("receipt_id") != "ANDREAS_UBUNTU_BASE_TARGET_GATE":
        failures.append("TARGET_GATE_WRONG_RECEIPT")
    gate_host = gate.get("host") or {}
    if gate_host.get("target_attested") is not True:
        failures.append("TARGET_GATE_NOT_ATTESTED")
    if gate.get("target_component_steps_pass") is not True and gate.get("component_steps_pass") is not True:
        failures.append("TARGET_COMPONENT_BATTERY_NOT_PASS")
    if gate_host.get("input_checkout_clean") is not True:
        failures.append("TARGET_GATE_DIRTY_CHECKOUT")

    # Known executable semantic discriminator: until the float-mediated evaluator site is
    # removed, large Int division is observably not equivalent to C11 int64 division.
    for path in (COMPILER, EFFECT_PIPELINE):
        if path.exists() and "int(left / right) if isinstance(left, int) and isinstance(right, int)" in path.read_text(encoding="utf-8"):
            failures.append("KNOWN_LARGE_INT_DIVISION_SEMANTIC_BUG:" + str(path.relative_to(ROOT)))

    unresolved = ledger.get("unresolved_language_counterexamples")
    if unresolved is None:
        failures.append("COUNTEREXAMPLE_LEDGER_MISSING_FIELD")
        unresolved = []
    elif unresolved:
        failures.append(f"UNRESOLVED_LANGUAGE_COUNTEREXAMPLES:{len(unresolved)}")

    steps = step_map(gate)
    work_packages: dict[str, Any] = {}
    for wp in contract.get("required_work_packages", []):
        required = WP_REQUIREMENTS.get(wp)
        if required is None:
            failures.append("UNMAPPED_WORK_PACKAGE:" + wp)
            required = []
        evidence = []
        wp_pass = True
        for step_id in required:
            step = steps.get(step_id)
            if not step:
                wp_pass = False
                evidence.append({"test_id": step_id, "missing": True})
                continue
            ok = (
                step.get("semantic_pass") is True
                and step.get("executed_on_attested_target") is True
                and step.get("can_count_as_target_component_evidence") is True
            )
            wp_pass = wp_pass and ok
            evidence.append(step_evidence(step))

        if wp == "CC-WP-09-CONCURRENCY-MEMORY":
            # The target convergence gate must include cancellation/error semantics, not
            # merely successful publication/ABA behavior. A separate hosted receipt is not
            # target evidence and therefore cannot silently satisfy this row.
            cancellation = steps.get("WP09_CANCELLATION_ERROR")
            if cancellation:
                ok = cancellation.get("semantic_pass") is True and cancellation.get("executed_on_attested_target") is True and cancellation.get("can_count_as_target_component_evidence") is True
                evidence.append(step_evidence(cancellation)); wp_pass = wp_pass and ok
            else:
                wp_pass = False
                evidence.append({"test_id": "WP09_CANCELLATION_ERROR", "missing": True})

        if wp == "CC-WP-10-GENERAL-APP-SUITE":
            app_rows = apps_doc.get("applications") if isinstance(apps_doc.get("applications"), dict) else {}
            app_names = contract.get("required_applications", [])
            app_ok = apps_doc.get("target_host") == TARGET and all(isinstance(app_rows.get(name), dict) and app_rows[name].get("pass") is True for name in app_names)
            wp_pass = wp_pass and app_ok
            evidence.append({"test_id": "tools/claycode_base_target_application_suite.py", "path": str(APPS.relative_to(ROOT)), "sha256": sha(APPS) if APPS.exists() else None, "all_ten_real_apps_pass": app_ok})

        if wp == "CC-WP-13-HARNESS-HANDOFF":
            frank_ok = (
                bool(frank)
                and frank.get("pass") is True
                and frank.get("target_host") == TARGET
                and frank.get("h2_h3_handoff_ready") is True
                and frank.get("semantic_escape_hatches") in ([], None, 0)
            )
            wp_pass = wp_pass and frank_ok
            evidence.append({"test_id": "FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT", "path": str(FULL_FRANK.relative_to(ROOT)), "sha256": sha(FULL_FRANK) if FULL_FRANK.exists() else None, "full_handoff_pass": frank_ok})

        work_packages[wp] = {"pass": bool(wp_pass), "evidence": evidence}
        if not wp_pass:
            failures.append("WORK_PACKAGE_NOT_ACCEPTED:" + wp)

    applications = apps_doc.get("applications") if isinstance(apps_doc.get("applications"), dict) else {}
    for app in contract.get("required_applications", []):
        row = applications.get(app)
        if not isinstance(row, dict):
            failures.append("APPLICATION_MISSING:" + app)
            continue
        for field in contract.get("application_row_required", []):
            if field not in row:
                failures.append(f"APPLICATION_FIELD_MISSING:{app}:{field}")
        if row.get("pass") is not True:
            failures.append("APPLICATION_NOT_PASS:" + app)
        if row.get("authority_boundary_preserved") is not True:
            failures.append("APPLICATION_AUTHORITY_BOUNDARY_FAIL:" + app)
    gui = applications.get("GUI_INTERACTIVE") or {}
    if (gui.get("observed") or {}).get("io_mode") != "REAL_KERNEL_FD_EVENT_LOOP":
        failures.append("GUI_NOT_REAL_KERNEL_EVENT_LOOP")

    full_app = applications.get("FULL_FRANK_HANDOFF") or {}
    if full_app.get("pass") is not True or not frank:
        failures.append("FULL_FRANK_APP_NOT_PRODUCTION_HANDOFF")

    frank_handoff = {
        "pass": bool(frank.get("pass") is True and frank.get("h2_h3_handoff_ready") is True and frank.get("semantic_escape_hatches") in ([], None, 0)),
        "frozen_frank_source_hashes": frank.get("frozen_frank_source_hashes"),
        "claycode_source_hashes": frank.get("claycode_source_hashes"),
        "production_chain_receipts": frank.get("production_chain_receipts"),
        "semantic_escape_hatches": frank.get("semantic_escape_hatches"),
        "h2_h3_handoff_ready": frank.get("h2_h3_handoff_ready") is True,
    }
    for field in contract.get("frank_handoff_required", []):
        if field not in frank_handoff:
            failures.append("FRANK_FIELD_MISSING:" + field)
    if not frank_handoff["pass"]:
        failures.append("FULL_FRANK_HANDOFF_NOT_ACCEPTED")

    host_fp = host.get("host_fingerprint") if isinstance(host.get("host_fingerprint"), dict) else {}
    for field in contract.get("host_fingerprint_required", []):
        if not host_fp.get(field):
            failures.append("HOST_FINGERPRINT_FIELD_MISSING:" + field)

    repo_commit = (gate_host.get("git_head") or ((gate.get("repo_head") or {}).get("stdout_tail") if isinstance(gate.get("repo_head"), dict) else None))
    if not repo_commit:
        failures.append("REPOSITORY_COMMIT_MISSING")

    compiler_runtime = {
        "compiler_sha256": sha(COMPILER) if COMPILER.exists() else None,
        "effect_pipeline_sha256": sha(EFFECT_PIPELINE) if EFFECT_PIPELINE.exists() else None,
        "target_gate_sha256": sha(TARGET_GATE) if TARGET_GATE.exists() else None,
        "application_suite_sha256": sha(APPS) if APPS.exists() else None,
        "versions": apps_doc.get("compiler_runtime"),
    }

    receipt = {
        "schema_version": "1.0",
        "target_host": TARGET,
        "repository_commit": repo_commit,
        "host_fingerprint": host_fp,
        "compiler_runtime": compiler_runtime,
        "work_packages": work_packages,
        "applications": applications,
        "frank_handoff": frank_handoff,
        "unresolved_language_counterexamples": unresolved,
        "overall_pass": not failures,
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "contract_path": str(CONTRACT.relative_to(ROOT)),
        "contract_sha256": sha(CONTRACT) if CONTRACT.exists() else None,
        "authority_invariant": "model_output != execution_authority",
    }

    diagnostic = {"schema_version": "1.0", "pass": not failures, "failures": failures, "candidate": receipt}
    DIAGNOSTIC.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if failures:
        # Never leave a stale prior PASS receipt in place after a failed re-assembly.
        if FINAL.exists():
            FINAL.unlink()
        print(json.dumps({"overall_pass": False, "failures": failures, "diagnostic": str(DIAGNOSTIC.relative_to(ROOT))}, ensure_ascii=False))
        return 2

    FINAL.parent.mkdir(parents=True, exist_ok=True)
    FINAL.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall_pass": True, "receipt": str(FINAL.relative_to(ROOT)), "sha256": sha(FINAL)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
