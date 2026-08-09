#!/usr/bin/env python3
"""Compiler/lowering -> host authority integration validation for ClayCode BASE."""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import claycode_base_effect_pipeline as ep  # noqa: E402
from claycode_base_authority_runtime import AuthorityDenied, AuthorityGateway, HostAuthorityRuntime, _issue  # noqa: E402

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
OUT = ROOT / "research_entity/claycode/autonomous/BASE_AUTHORITY_INTEGRATION_RECEIPT.json"

SOURCE = """module app.effect_bridge
fn read(x:Int)->Int=host.fs_read(x)
fn store(x:Int)->Int=host.db_put(read(x))
fn main(x:Int)->Int=store(x)+host.http_send(x)
"""


def make_gateway(budget: int):
    context = {"origin": "origin:base-integration", "basis_epoch": 23, "selection_id": "sel:base", "closure_id": "closure:base"}
    runtime = HostAuthorityRuntime()
    handles = {
        "cap.fs.read": _issue(runtime, "cap.fs.read", "FS_READ", budget, context),
        "cap.db.write": _issue(runtime, "cap.db.write", "DB_WRITE", budget, context),
        "cap.http": _issue(runtime, "cap.http", "HTTP", budget, context),
    }
    return runtime, AuthorityGateway(runtime, handles, context)


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    built = ep.build(SOURCE, grammar)
    rng = random.Random(202608091925)
    vectors = [rng.randint(-100000, 100000) for _ in range(4000)]
    output_mismatches = 0
    trace_mismatches = 0
    for value in vectors:
        _, g1 = make_gateway(10)
        _, g2 = make_gateway(10)
        expected = ep.eval_function(built["ir"], "main", [value], g1)
        observed = ep.exec_lowered(built["artifact"], "main", [value], g2)
        output_mismatches += int(expected != observed)
        trace_mismatches += int(g1.trace != g2.trace)

    missing_handle_rejected = False
    runtime, gw = make_gateway(10)
    del gw.handles["cap.http"]
    try:
        ep.eval_function(built["ir"], "main", [1], gw)
    except AuthorityDenied:
        missing_handle_rejected = True

    revoked_rejected = False
    runtime, gw = make_gateway(10)
    runtime.revoke(gw.handles["cap.db.write"])
    try:
        ep.eval_function(built["ir"], "main", [1], gw)
    except AuthorityDenied:
        revoked_rejected = True

    restart_rejected = False
    runtime, gw = make_gateway(10)
    runtime.restart_epoch()
    try:
        ep.eval_function(built["ir"], "main", [1], gw)
    except AuthorityDenied:
        restart_rejected = True

    budget_rejected = False
    runtime, gw = make_gateway(1)
    try:
        ep.eval_function(built["ir"], "main", [1], gw)
    except AuthorityDenied:
        budget_rejected = True

    main_ir = next(f for f in built["ir"]["functions"] if f["name"] == "main")
    effect_manifest_matches = main_ir["effect_summary"] == ["DB_WRITE", "FS_READ", "HTTP"] and main_ir["required_capabilities"] == ["cap.db.write", "cap.fs.read", "cap.http"]
    checks = {
        "effect_manifest_matches": effect_manifest_matches,
        "translation_outputs_match": output_mismatches == 0,
        "translation_effect_traces_match": trace_mismatches == 0,
        "missing_handle_rejected": missing_handle_rejected,
        "revoked_handle_rejected": revoked_rejected,
        "restart_stale_handle_rejected": restart_rejected,
        "aggregate_budget_exhaustion_rejected": budget_rejected,
    }
    receipt = {
        "schema_version": "1.0",
        "scope": "CLAYCODE_BASE_COMPILER_TO_OPAQUE_AUTHORITY_RUNTIME_PROXY",
        "pass": all(checks.values()),
        "checks": checks,
        "vectors": len(vectors),
        "output_mismatches": output_mismatches,
        "trace_mismatches": trace_mismatches,
        "semantic_hash": built["semantic_hash"],
        "artifact_hash": built["artifact_hash"],
        "translation_contract_hash": built["translation_contract_hash"],
        "counts_as_work_package_pass": False,
        "counts_as_target_acceptance": False,
        "scope_guard": "Compiler-to-broker integration proxy only. No ambient OS child process, real FFI, filesystem/network containment or Andreas Ubuntu APP-08 execution is claimed.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
