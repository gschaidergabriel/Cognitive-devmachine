#!/usr/bin/env python3
"""Materialize FULL_FRANK_HANDOFF receipts only on the registered Andreas Ubuntu target.

The finalizer requires five independently executable semantic paths:
1. frozen H1 ActiveAssembly == full ClayCode structured H2 program using only generic
   collection/control/hash builtins (domain logic visible in Clay source);
2. frozen H1 ActiveAssembly == H2 ClayCode generic typed-record FFI with a policy-bound
   sealed capability (independent implementation route);
3. frozen H1 ActiveAssembly == H3 in-process consolidated generic selector;
4. real frozen FRANK packet_score == ClayCode typed IR/evaluator/native C11;
5. real frozen FRANK GRT frame == block-body evaluator/lowering with trace equivalence.

It writes the receipt shapes consumed by the target application suite and WP14 audit,
plus the FULL_FRANK_HANDOFF application receipt. Hosted CI/proxy execution cannot create
a passing receipt because local target fingerprint verification, Ubuntu/non-CI checks and
a clean toolchain source tree are mandatory.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from claycode_target_host_identity import DEFAULT_REGISTRATION, TARGET_HOST, verify  # noqa: E402

STRUCTURED_H2_TOOL = ROOT / "tools/claycode_full_frank_active_assembly_validation.py"
H2_TOOL = ROOT / "tools/claycode_wp13_active_assembly_h2.py"
H3_TOOL = ROOT / "tools/claycode_wp13_h3_consolidation.py"
SCORE_TOOL = ROOT / "tools/claycode_wp13_frank_handoff_validation.py"
GRT_TOOL = ROOT / "tools/claycode_base_frank_block_toolchain.py"
STRUCTURED_H2_SOURCE = ROOT / "research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_FULL_V1.clay"
STRUCTURED_BACKEND = ROOT / "tools/claycode_structured_backend.py"
H2_RECEIPT = ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H2_RECEIPT.json"
H3_RECEIPT = ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H3_CONSOLIDATION_RECEIPT.json"
SCORE_RECEIPT = ROOT / "research_entity/claycode/autonomous/WP13_FRANK_PACKET_SCORE_HANDOFF_RECEIPT.json"
GRT_RECEIPT = ROOT / "research_entity/claycode/autonomous/FRANK_GRT_BLOCK_TOOLCHAIN_RECEIPT.json"
PRODUCTION_RECEIPT = ROOT / "research_entity/claycode/target/FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json"
STRUCTURED_TARGET_RECEIPT = ROOT / "research_entity/claycode/target_receipts/FULL_FRANK_ACTIVE_ASSEMBLY_STRUCTURED_TARGET_RECEIPT.json"
AUDIT_RECEIPT = ROOT / "research_entity/claycode/target_receipts/FULL_FRANK_HANDOFF_RECEIPT.json"
APP_RECEIPT = ROOT / "research_entity/claycode/target_receipts/apps/FULL_FRANK_HANDOFF.json"
H1_REFERENCE = ROOT / "research_entity/harness/reference/active_assembly.py"
GRT_SOURCE = ROOT / "research_entity/claycode/base/examples/FRANK_GRT_FRAME_V1.clay"
H2_SOURCE = ROOT / "research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_H2_V1.clay"
SCORE_SOURCE = ROOT / "research_entity/claycode/apps/frank_active_assembly_packet_score_v1.clay"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def composite_hash(items: list[tuple[str, str]]) -> str:
    return sha_bytes(json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"RECEIPT_NOT_OBJECT:{path}")
    return value


def run(name: str, path: Path, args: list[str] | None = None, timeout: int = 600) -> dict[str, Any]:
    argv = [sys.executable, str(path)] + list(args or [])
    cp = subprocess.run(
        argv, cwd=ROOT, text=True, capture_output=True,
        check=False, timeout=timeout,
    )
    return {
        "name": name,
        "argv": [sys.executable, str(path.relative_to(ROOT))] + list(args or []),
        "returncode": cp.returncode,
        "pass": cp.returncode == 0,
        "stdout_tail": cp.stdout[-12000:],
        "stderr_tail": cp.stderr[-12000:],
    }


def clean_source_tree() -> tuple[bool, list[str]]:
    cp = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed = (
        "research_entity/claycode/autonomous/",
        "research_entity/claycode/target/",
        "research_entity/claycode/target_receipts/",
        "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json",
    )
    bad = []
    for line in cp.stdout.splitlines():
        path = line[3:] if len(line) >= 4 else line
        parts = [x.strip() for x in path.split(" -> ")]
        if not all(any(x.startswith(prefix) for prefix in allowed) for x in parts):
            bad.append(line)
    return cp.returncode == 0 and not bad, bad


def main() -> int:
    host_ok, host = verify(DEFAULT_REGISTRATION)
    os_id = None
    os_release = Path("/etc/os-release")
    if os_release.exists():
        for line in os_release.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("ID="):
                os_id = line.split("=", 1)[1].strip().strip('"').lower()
                break
    preconditions = {
        "registered_target_fingerprint": host_ok,
        "target_id_exact": host.get("target_host") == TARGET_HOST == TARGET,
        "linux": platform.system() == "Linux",
        "ubuntu": os_id == "ubuntu",
        "not_github_actions": os.getenv("GITHUB_ACTIONS", "").lower() != "true",
        "not_generic_ci": os.getenv("CI", "").lower() not in {"1", "true", "yes"},
    }
    clean, dirty = clean_source_tree()
    preconditions["clean_toolchain_source"] = clean
    if not all(preconditions.values()):
        print(json.dumps({"error": "FULL_FRANK_TARGET_PRECONDITION_FAILED", "preconditions": preconditions, "dirty": dirty, "host": host}, ensure_ascii=False, indent=2))
        return 3

    # Independent H2 proof first. This tool writes its own target-shaped receipt to the
    # production path. Preserve it under a unique evidence name before the aggregate
    # finalizer later replaces the production path with the stronger multi-proof receipt.
    structured_step = run(
        "H1_H2_FULL_STRUCTURED_CLAY",
        STRUCTURED_H2_TOOL,
        ["--target", "--registration", str(DEFAULT_REGISTRATION)],
    )
    if not structured_step["pass"] or not PRODUCTION_RECEIPT.exists():
        print(json.dumps({"error": "FULL_FRANK_STRUCTURED_H2_GATE_FAILED", "step": structured_step}, ensure_ascii=False, indent=2))
        return 2
    structured = read_json(PRODUCTION_RECEIPT)
    structured_checks = {
        "pass": structured.get("pass") is True,
        "target_host_exact": structured.get("target_host") == TARGET,
        "target_identity_verified": structured.get("target_identity_verified") is True,
        "no_semantic_escape_hatches": structured.get("semantic_escape_hatches") == [],
        "authority_boundary_preserved": structured.get("authority_boundary_preserved") is True,
        "generic_builtin_surface_only": all(
            not str(name).startswith(("frank", "active_assembly", "packet_"))
            for name in structured.get("generic_builtin_surface", [])
        ),
        "no_effect_authority_surface": structured.get("validation", {}).get("effect_authority_surface") == [],
        "positive_differentials_pass": bool(structured.get("positive_differentials")) and all(x.get("pass") is True for x in structured.get("positive_differentials", [])),
        "negative_differentials_pass": bool(structured.get("negative_differentials")) and all(x.get("pass") is True for x in structured.get("negative_differentials", [])),
    }
    if not all(structured_checks.values()):
        print(json.dumps({"error": "FULL_FRANK_STRUCTURED_H2_RECEIPT_FAILED", "checks": structured_checks}, ensure_ascii=False, indent=2))
        return 2
    STRUCTURED_TARGET_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    STRUCTURED_TARGET_RECEIPT.write_text(json.dumps(structured, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    steps = [
        structured_step,
        run("H1_H2_GENERIC_TYPED_FFI", H2_TOOL),
        run("H1_H3_CONSOLIDATED_COMMUTATION", H3_TOOL),
        run("PACKET_SCORE_TYPED_IR_NATIVE", SCORE_TOOL),
        run("GRT_BLOCK_BODY_LOWERING", GRT_TOOL),
    ]
    if not all(x["pass"] for x in steps):
        print(json.dumps({"error": "FULL_FRANK_COMPONENT_GATE_FAILED", "steps": steps}, ensure_ascii=False, indent=2))
        return 2

    h2 = read_json(H2_RECEIPT)
    h3 = read_json(H3_RECEIPT)
    score = read_json(SCORE_RECEIPT)
    grt = read_json(GRT_RECEIPT)
    checks = {
        "structured_h2_pass": all(structured_checks.values()),
        "structured_h2_domain_logic_in_clay_source": structured.get("validation", {}).get("effect_authority_surface") == [] and structured.get("semantic_escape_hatches") == [],
        "h2_pass": h2.get("pass") is True,
        "h2_counterexample_resolved_generically": h2.get("counterexample_disposition") == "IMPLEMENTABLE_VIA_GENERIC_TYPED_FFI_RUNTIME_COLLECTION",
        "h2_no_language_change_required": h2.get("language_change_required_by_this_counterexample") is False,
        "h2_random_exact": h2.get("checks", {}).get("random_h1_h2_exact_differential") is True,
        "h2_authority_non_mint": h2.get("checks", {}).get("authority_mint_attempt_fail_closed") is True,
        "h2_policy_binding": h2.get("checks", {}).get("selector_policy_hash_bound_to_capability") is True,
        "h2_generic_non_frank_probe": h2.get("checks", {}).get("same_primitive_non_frank_scheduler") is True,
        "h3_pass": h3.get("pass") is True and h3.get("h3_consolidation_semantics_ready") is True,
        "h3_exact_commutation": h3.get("checks", {}).get("h1_h3_exact_commutation") is True,
        "h3_authority_non_mint": h3.get("checks", {}).get("authority_non_minting_rejection_commutes") is True,
        "packet_score_pass": score.get("pass") is True and score.get("semantic_mismatches") == 0 and score.get("native_mismatches") == 0,
        "grt_block_pass": grt.get("pass") is True and grt.get("trace_equivalent") is True,
    }
    if not all(checks.values()):
        print(json.dumps({"error": "FULL_FRANK_SEMANTIC_RECEIPT_FAILED", "checks": checks}, ensure_ascii=False, indent=2))
        return 2

    frozen_hashes = {
        str(H1_REFERENCE.relative_to(ROOT)): sha_file(H1_REFERENCE),
        str(GRT_SOURCE.relative_to(ROOT)): sha_file(GRT_SOURCE),
    }
    clay_hashes = {
        str(STRUCTURED_H2_SOURCE.relative_to(ROOT)): sha_file(STRUCTURED_H2_SOURCE),
        str(H2_SOURCE.relative_to(ROOT)): sha_file(H2_SOURCE),
        str(SCORE_SOURCE.relative_to(ROOT)): sha_file(SCORE_SOURCE),
    }
    component_receipts = {
        str(STRUCTURED_TARGET_RECEIPT.relative_to(ROOT)): sha_file(STRUCTURED_TARGET_RECEIPT),
        str(H2_RECEIPT.relative_to(ROOT)): sha_file(H2_RECEIPT),
        str(H3_RECEIPT.relative_to(ROOT)): sha_file(H3_RECEIPT),
        str(SCORE_RECEIPT.relative_to(ROOT)): sha_file(SCORE_RECEIPT),
        str(GRT_RECEIPT.relative_to(ROOT)): sha_file(GRT_RECEIPT),
    }
    implementation_hashes = {
        str(STRUCTURED_BACKEND.relative_to(ROOT)): sha_file(STRUCTURED_BACKEND),
        "generic_record_selector": h2.get("record_selector_version"),
    }
    frank_input_sha256 = composite_hash(sorted(frozen_hashes.items()))
    clay_source_sha256 = composite_hash(sorted(clay_hashes.items()))
    artifact_sha256 = composite_hash(sorted(component_receipts.items()))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()

    expected = {
        "structured_h1_h2_exact_commutation": True,
        "typed_ffi_h1_h2_exact_commutation": True,
        "h1_h3_exact_commutation": True,
        "packet_score_semantic_mismatches": 0,
        "packet_score_native_mismatches": 0,
        "grt_trace_equivalent": True,
        "semantic_escape_hatches": [],
        "model_output_is_execution_authority": False,
    }
    observed = {
        "structured_positive_differentials": len(structured.get("positive_differentials", [])),
        "structured_negative_differentials": len(structured.get("negative_differentials", [])),
        "structured_semantic_escape_hatches": structured.get("semantic_escape_hatches"),
        "h2_random_cases": h2.get("random_cases"),
        "h2_random_failures": len(h2.get("random_failures", [])),
        "h3_cases": h3.get("cases"),
        "h3_mismatches": len(h3.get("mismatches", [])),
        "packet_score_semantic_mismatches": score.get("semantic_mismatches"),
        "packet_score_native_mismatches": score.get("native_mismatches"),
        "grt_trace_equivalent": grt.get("trace_equivalent"),
        "semantic_escape_hatches": [],
        "model_output_is_execution_authority": False,
    }
    negative = {
        "structured_negative_differentials": all(x.get("pass") is True for x in structured.get("negative_differentials", [])),
        "packet_id_collision_rejected": h2.get("checks", {}).get("packet_identity_collision_fail_closed") is True,
        "authority_mint_attempt_rejected": h2.get("checks", {}).get("authority_mint_attempt_fail_closed") is True,
        "policy_tamper_rejected": h2.get("checks", {}).get("selector_policy_hash_bound_to_capability") is True,
        "descriptor_not_authority": h2.get("checks", {}).get("capability_descriptor_not_authority") is True,
        "candidate_order_invariant_h3": h3.get("checks", {}).get("candidate_order_invariant") is True,
    }
    final_pass = all(checks.values()) and all(negative.values())
    common = {
        "schema_version": "1.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pass": final_pass,
        "target_host": TARGET,
        "target_host_fingerprint": host.get("host_fingerprint", {}),
        "git_head": head,
        "frank_input_sha256": frank_input_sha256,
        "clay_source_sha256": clay_source_sha256,
        "artifact_sha256": artifact_sha256,
        "frozen_frank_source_hashes": frozen_hashes,
        "claycode_source_hashes": clay_hashes,
        "implementation_hashes": implementation_hashes,
        "production_chain_receipts": component_receipts,
        "expected": expected,
        "observed": observed,
        "negative_test": {"pass": all(negative.values()), "checks": negative},
        "semantic_escape_hatches": [],
        "semantic_escape_hatch_used": False,
        "model_output_is_execution_authority": False,
        "authority_boundary_preserved": True,
        "h2_h3_handoff_ready": final_pass,
        "compiler_runtime_version": f"structured:{structured.get('production_chain_receipts', {}).get('backend_version')}|typed-ffi:{h2.get('compiler_candidate')}|selector:{h2.get('record_selector_version')}|runtime:{h2.get('runtime_version')}",
        "target_artifact_hash": artifact_sha256,
        "h3_one_binary_packaging_claim": False,
        "h3_semantic_consolidation_ready": h3.get("h3_consolidation_semantics_ready") is True,
        "independent_h2_realizations": ["FULL_STRUCTURED_CLAY_GENERIC_BUILTINS", "TYPED_FFI_POLICY_BOUND_GENERIC_RECORD_SELECTOR"],
        "claim_boundary": "Full frozen ActiveAssembly transfer/commutation is required through two independent generic H2 realizations plus H3 commutation, packet-score native and GRT block-body semantics on the registered target. H3 one-binary packaging is not claimed because the H3 contract treats the H1 module boundary as a measurement boundary, not a mandatory final service boundary.",
    }

    production = dict(common)
    production["evidence_class"] = "ANDREAS_UBUNTU_FULL_FRANK_HANDOFF"
    PRODUCTION_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTION_RECEIPT.write_text(json.dumps(production, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = dict(common)
    audit["evidence_class"] = "ANDREAS_UBUNTU_FULL_FRANK_HANDOFF"
    AUDIT_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_RECEIPT.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    app = {
        "schema_version": "1.2",
        "app": "FULL_FRANK_HANDOFF",
        "pass": final_pass,
        "target_host": TARGET,
        "evidence_class": "ANDREAS_UBUNTU_REAL_APPLICATION",
        "model_output_is_execution_authority": False,
        "git_head": head,
        "source_sha256": clay_source_sha256,
        "artifact_sha256": artifact_sha256,
        "expected": expected,
        "observed": observed,
        "positive_test": {"pass": final_pass, "component_checks": checks},
        "negative_test": {"pass": all(negative.values()), "checks": negative},
        "full_frank_receipt_sha256": sha_file(AUDIT_RECEIPT),
    }
    APP_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    APP_RECEIPT.write_text(json.dumps(app, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass": final_pass,
        "h2_h3_handoff_ready": final_pass,
        "independent_h2_realizations": 2,
        "audit_receipt": str(AUDIT_RECEIPT.relative_to(ROOT)),
        "application_receipt": str(APP_RECEIPT.relative_to(ROOT)),
        "production_receipt": str(PRODUCTION_RECEIPT.relative_to(ROOT)),
        "structured_target_receipt": str(STRUCTURED_TARGET_RECEIPT.relative_to(ROOT)),
    }, sort_keys=True))
    return 0 if final_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
