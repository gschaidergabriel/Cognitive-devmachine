#!/usr/bin/env python3
"""Fail-closed final auditor for ClayCode BASE CC-WP-01..14.

The auditor does not execute compiler/runtime tests. It verifies that the evidence already
exists and satisfies the release accounting law. In particular:
- hosted/proxy receipts can never satisfy target-host requirements;
- WP10 requires ten real per-application Andreas Ubuntu receipts;
- WP13 requires a full FRANK handoff receipt in addition to subsystem evidence;
- WP14 passes only when WP01..13 pass, no P0/P1 defect remains open, and every referenced
  evidence object is content-hashed into the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json"
TARGET_GATE = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_TARGET_GATE.json"
SPEC_FREEZE = ROOT / "research_entity/claycode/base/BASE_SEMANTIC_FREEZE_V1.json"
APP_DIR = ROOT / "research_entity/claycode/target_receipts/apps"
FULL_FRANK = ROOT / "research_entity/claycode/target_receipts/FULL_FRANK_HANDOFF_RECEIPT.json"
DEFECT_LEDGER = ROOT / "research_entity/claycode/BASE_DEFECT_LEDGER.json"
TARGET_ID = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"

APPS = [
    "CLI", "HTTP_WEBSITE", "DB_SERVICE", "CONCURRENT_SERVICE", "GUI_INTERACTIVE",
    "COMPILER_TOOL", "GPU_ML_NUMERICAL", "SYSTEM_EFFECT_SANDBOX", "FRANK_COMPONENT",
    "FULL_FRANK_HANDOFF",
]

TARGET_STEP_REQUIREMENTS = {
    "CC-WP-02-PARSER-CANON": {"WP02_STRICT_V7", "WP02_FULL_CORPUS_V7", "WP02_CANONICALIZER"},
    "CC-WP-03-IR-TYPES": {"WP03_TYPED_IR", "WP03_06_PURE_NATIVE_DIFFERENTIAL"},
    "CC-WP-04-TYPE-EFFECT": {"WP04_08_EFFECT_PIPELINE", "WP04_08_REAL_SEALED_EFFECT_BRIDGE"},
    "CC-WP-05-EVALUATOR": {"WP03_06_PURE_NATIVE_DIFFERENTIAL", "WP04_08_REAL_SEALED_EFFECT_BRIDGE"},
    "CC-WP-06-COMPILER-LOWERING": {"WP03_06_PURE_NATIVE_DIFFERENTIAL", "WP04_08_REAL_SEALED_EFFECT_BRIDGE"},
    "CC-WP-07-RUNTIME-ABI-FFI": {"WP04_08_REAL_SEALED_EFFECT_BRIDGE", "WP07_08_PACKAGE_LINK", "WP07_09_RUNTIME_ABI_FFI"},
    "CC-WP-08-STDLIB-SDK": {"WP04_08_REAL_SEALED_EFFECT_BRIDGE", "WP07_08_PACKAGE_LINK", "WP07_09_RUNTIME_ABI_FFI"},
    "CC-WP-09-CONCURRENCY-MEMORY": {"WP07_09_RUNTIME_ABI_FFI"},
    "CC-WP-11-FUZZ-CONFORMANCE": {"WP11_FUZZ_CONFORMANCE"},
    "CC-WP-12-CORPUS-HELDOUT": {"WP12_CORPUS_HELDOUT"},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "MISSING"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"INVALID_JSON:{type(exc).__name__}"
    if not isinstance(value, dict):
        return None, "NOT_OBJECT"
    return value, None


def target_steps(gate: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not gate:
        return {}
    result = {}
    for row in gate.get("steps", []):
        if isinstance(row, dict) and isinstance(row.get("step_id"), str):
            result[row["step_id"]] = row
    return result


def target_gate_identity_ok(gate: dict[str, Any] | None) -> bool:
    if not gate:
        return False
    host = gate.get("host", {})
    pre = gate.get("preconditions", {})
    return bool(
        host.get("target_attested") is True
        and host.get("target_id_claim") == TARGET_ID
        and pre.get("target_id_exact") is True
        and pre.get("linux") is True
        and pre.get("ubuntu") is True
        and pre.get("not_ci") is True
        and pre.get("clean_release_input") is True
    )


def step_requirement_status(gate: dict[str, Any] | None, required: set[str]) -> tuple[bool, list[str]]:
    steps = target_steps(gate)
    missing = []
    for name in sorted(required):
        row = steps.get(name)
        if not row:
            missing.append(name + ":MISSING")
        elif row.get("semantic_pass") is not True:
            missing.append(name + ":NOT_PASS")
        elif row.get("can_count_as_target_component_evidence") is not True:
            missing.append(name + ":NOT_TARGET_EVIDENCE")
    return not missing and target_gate_identity_ok(gate), missing


def real_app_receipt(app: str) -> tuple[bool, dict[str, Any]]:
    path = APP_DIR / f"{app}.json"
    data, error = read_json(path)
    reasons = []
    if error:
        reasons.append(error)
    if data:
        if data.get("pass") is not True:
            reasons.append("PASS_NOT_TRUE")
        if data.get("target_host") != TARGET_ID:
            reasons.append("WRONG_TARGET_HOST")
        if data.get("evidence_class") != "ANDREAS_UBUNTU_REAL_APPLICATION":
            reasons.append("NOT_REAL_APPLICATION_EVIDENCE")
        if data.get("model_output_is_execution_authority") is not False:
            reasons.append("AUTHORITY_INVARIANT_NOT_PROVEN")
        for key in ("source_sha256", "artifact_sha256", "expected", "observed", "positive_test", "negative_test"):
            if key not in data:
                reasons.append("MISSING_FIELD:" + key)
    return not reasons, {
        "app": app,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path) if path.exists() else None,
        "reasons": reasons,
    }


def full_frank_status() -> tuple[bool, dict[str, Any]]:
    data, error = read_json(FULL_FRANK)
    reasons = []
    if error:
        reasons.append(error)
    if data:
        if data.get("pass") is not True:
            reasons.append("PASS_NOT_TRUE")
        if data.get("target_host") != TARGET_ID:
            reasons.append("WRONG_TARGET_HOST")
        if data.get("evidence_class") != "ANDREAS_UBUNTU_FULL_FRANK_HANDOFF":
            reasons.append("NOT_FULL_FRANK_HANDOFF_EVIDENCE")
        if data.get("semantic_escape_hatch_used") is not False:
            reasons.append("SEMANTIC_ESCAPE_HATCH_NOT_FALSE")
        if data.get("model_output_is_execution_authority") is not False:
            reasons.append("AUTHORITY_INVARIANT_NOT_PROVEN")
        for key in ("frank_input_sha256", "clay_source_sha256", "artifact_sha256", "expected", "observed"):
            if key not in data:
                reasons.append("MISSING_FIELD:" + key)
    return not reasons, {
        "path": str(FULL_FRANK.relative_to(ROOT)),
        "sha256": sha256_file(FULL_FRANK) if FULL_FRANK.exists() else None,
        "reasons": reasons,
    }


def defect_status() -> tuple[bool, dict[str, Any]]:
    data, error = read_json(DEFECT_LEDGER)
    if error == "MISSING":
        return False, {"path": str(DEFECT_LEDGER.relative_to(ROOT)), "reasons": ["MISSING_DEFECT_LEDGER"]}
    if error:
        return False, {"path": str(DEFECT_LEDGER.relative_to(ROOT)), "reasons": [error]}
    defects = data.get("defects", [])
    open_high = [d for d in defects if isinstance(d, dict) and d.get("severity") in {"P0", "P1"} and d.get("status") not in {"CLOSED", "REFUTED", "NOT_APPLICABLE"}]
    return not open_high, {
        "path": str(DEFECT_LEDGER.relative_to(ROOT)),
        "sha256": sha256_file(DEFECT_LEDGER),
        "open_p0_p1": open_high,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gate, gate_error = read_json(TARGET_GATE)
    spec, spec_error = read_json(SPEC_FREEZE)
    wp: dict[str, dict[str, Any]] = {}

    wp1_ok = bool(spec and spec.get("status") == "PASS" and spec_error is None)
    wp["CC-WP-01-SPEC-FREEZE"] = {
        "pass": wp1_ok,
        "evidence": str(SPEC_FREEZE.relative_to(ROOT)),
        "reason": None if wp1_ok else (spec_error or "SPEC_FREEZE_NOT_PASS"),
    }

    for name, required in TARGET_STEP_REQUIREMENTS.items():
        ok, missing = step_requirement_status(gate, required)
        wp[name] = {
            "pass": ok,
            "requires_target_steps": sorted(required),
            "missing_or_failed": missing,
            "target_gate": str(TARGET_GATE.relative_to(ROOT)),
        }

    app_rows = [real_app_receipt(app) for app in APPS]
    wp10_ok = all(ok for ok, _ in app_rows)
    wp["CC-WP-10-GENERAL-APP-SUITE"] = {
        "pass": wp10_ok,
        "applications": [row for _, row in app_rows],
    }

    frank_ok, frank = full_frank_status()
    # A real frozen subsystem target step is necessary but not sufficient for full handoff.
    subsystem_ok, subsystem_missing = step_requirement_status(gate, {"WP13_FRANK_SCORE_HANDOFF"})
    wp13_ok = subsystem_ok and frank_ok
    wp["CC-WP-13-HARNESS-HANDOFF"] = {
        "pass": wp13_ok,
        "subsystem_target_pass": subsystem_ok,
        "subsystem_missing_or_failed": subsystem_missing,
        "full_frank": frank,
    }

    wp01_13 = [f"CC-WP-{i:02d}-" for i in range(1, 14)]
    prior_ok = True
    for prefix in wp01_13:
        match = next((v for k, v in wp.items() if k.startswith(prefix)), None)
        if not match or match.get("pass") is not True:
            prior_ok = False
    defects_ok, defects = defect_status()
    wp14_ok = prior_ok and defects_ok
    wp["CC-WP-14-BASE-AUDIT"] = {
        "pass": wp14_ok,
        "wp01_13_all_pass": prior_ok,
        "zero_open_p0_p1": defects_ok,
        "defect_ledger": defects,
    }

    evidence_files = [SPEC_FREEZE, TARGET_GATE, FULL_FRANK, DEFECT_LEDGER]
    evidence_files += [APP_DIR / f"{app}.json" for app in APPS]
    evidence_hashes = {}
    for path in evidence_files:
        if path.exists():
            evidence_hashes[str(path.relative_to(ROOT))] = sha256_file(path)

    failed = [name for name, row in wp.items() if row.get("pass") is not True]
    manifest = {
        "schema_version": "1.0",
        "manifest": "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_host": TARGET_ID,
        "authority_invariant": "model_output != execution_authority",
        "target_gate_error": gate_error,
        "target_gate_identity_pass": target_gate_identity_ok(gate),
        "work_packages": wp,
        "failed_work_packages": failed,
        "evidence_sha256": evidence_hashes,
        "general_purpose_gate_pass": not failed,
        "claycode_release_gate_pass": not failed,
        "promotion_allowed": not failed,
        "scope_guard": "PASS requires all 14 receipt laws. Hosted/proxy evidence is deliberately insufficient for WP10, full WP13, or WP14.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": not failed, "failed_work_packages": failed, "output": str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output)}))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
