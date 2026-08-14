#!/usr/bin/env python3
"""Full frozen FRANK ActiveAssembly -> generic structured ClayCode differential.

Proxy mode writes autonomous evidence only. --target additionally requires the manually
registered Andreas Ubuntu host and writes FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json only
when reference, structured interpreter and lowered executable agree on all positive and
negative cases with no FRANK-specific builtin/effect escape hatch.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_structured_backend import Runtime, StructuredFault, VERSION, compile_source, execute, execute_lowered
from claycode_target_host_identity import DEFAULT_REGISTRATION, verify

SOURCE = ROOT / "research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_FULL_V1.clay"
REFERENCE = ROOT / "research_entity/harness/reference/active_assembly.py"
BACKEND = ROOT / "tools/claycode_structured_backend.py"
PROXY_OUT = ROOT / "research_entity/claycode/autonomous/FULL_FRANK_ACTIVE_ASSEMBLY_STRUCTURED_RECEIPT.json"
TARGET_OUT = ROOT / "research_entity/claycode/target/FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_reference():
    spec = importlib.util.spec_from_file_location("frank_active_assembly_h1", REFERENCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("REFERENCE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def packet(ref, packet_id, ancestry, relevance, impact, novelty, uncertainty, epoch, **kw):
    return ref.AssemblyPacket(
        packet_id=packet_id,
        ancestry_family=ancestry,
        kind=kw.pop("kind", "memory"),
        relevance=relevance,
        impact=impact,
        novelty=novelty,
        uncertainty=uncertainty,
        valid_epoch=epoch,
        **kw,
    )


def as_input(rows):
    return [dataclasses.asdict(x) for x in rows]


def positive_cases(ref):
    return [
        {
            "name": "basic_rank_ancestry_stale",
            "packets": [
                packet(ref,"a1","A",.95,.8,.3,.1,7,reexpand_ref="ra1",origin_actor="mem"),
                packet(ref,"a2","A",.90,.7,.4,.1,7,reexpand_ref="ra2",origin_actor="mem"),
                packet(ref,"a3","A",.85,.6,.5,.2,7,reexpand_ref="ra3",origin_actor="mem"),
                packet(ref,"b1","B",.70,.9,.8,.2,7,reexpand_ref="rb1",origin_actor="tool"),
                packet(ref,"stale","C",1.0,1.0,1.0,0.0,6,reexpand_ref="rstale"),
            ],
            "kwargs": {"current_epoch":7,"max_items":3,"max_per_ancestry":2,"max_context_cost":None},
        },
        {
            "name": "conflict_visibility_same_ancestry",
            "packets": [
                packet(ref,"p-yes","shared",.95,.9,.5,.1,9,claim_key="door",claim_value="open"),
                packet(ref,"p-no","shared",.94,.9,.5,.1,9,claim_key="door",claim_value="closed"),
                packet(ref,"p-yes-dup-value","other",.70,.7,.7,.2,9,claim_key="door",claim_value="open"),
                packet(ref,"other","Z",.8,.8,.8,.2,9),
            ],
            "kwargs": {"current_epoch":9,"max_items":3,"max_per_ancestry":1,"max_context_cost":None},
        },
        {
            "name": "context_cost_budget",
            "packets": [
                packet(ref,"x1","A",.9,.9,.9,.1,4,context_cost=3,reexpand_ref="rx1"),
                packet(ref,"x2","B",.8,.8,.8,.1,4,context_cost=3,reexpand_ref="rx2"),
                packet(ref,"x3","C",.7,.7,.7,.1,4,context_cost=1,reexpand_ref="rx3"),
            ],
            "kwargs": {"current_epoch":4,"max_items":8,"max_per_ancestry":2,"max_context_cost":4},
        },
        {
            "name": "exact_duplicate_delivery",
            "packets": [],
            "kwargs": {"current_epoch":2,"max_items":8,"max_per_ancestry":2,"max_context_cost":None},
            "duplicate_fixture": True,
        },
        {
            "name": "unicode_provenance_and_nulls",
            "packets": [
                packet(ref,"ü-1","familie-ß",.81,.62,.44,.18,11,claim_key="α",claim_value="β",origin_actor="外部",reexpand_ref=None),
                packet(ref,"ü-2","familie-γ",.79,.61,.43,.19,11,claim_key="α",claim_value="γ",origin_actor=None,reexpand_ref="再展開"),
            ],
            "kwargs": {"current_epoch":11,"max_items":8,"max_per_ancestry":2,"max_context_cost":None},
        },
    ]


def run_positive(ref, built, case):
    rows = list(case["packets"])
    if case.get("duplicate_fixture"):
        p = packet(ref,"dup","A",.6,.7,.8,.2,2,origin_actor="same")
        rows = [p, p]
    kw = dict(case["kwargs"])
    expected = ref.compile_active_assembly(rows, **kw)
    args = [as_input(rows), kw["current_epoch"], kw["max_items"], kw["max_per_ancestry"], kw["max_context_cost"]]
    interpreted, rt1 = execute(built["program"], "compile_active_assembly", args, Runtime())
    lowered, rt2, artifact_hash = execute_lowered(built["program"], "compile_active_assembly", args, Runtime())
    return {
        "name": case["name"],
        "pass": expected == interpreted == lowered,
        "reference_sha256": hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
        "interpreter_sha256": hashlib.sha256(json.dumps(interpreted,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
        "lowered_sha256": hashlib.sha256(json.dumps(lowered,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
        "lowered_artifact_sha256": artifact_hash,
        "generic_builtin_trace_interpreter": rt1.trace,
        "generic_builtin_trace_lowered": rt2.trace,
        "selected_ids": [x["packet_id"] for x in lowered.get("items",[])],
        "assembly_sha256": lowered.get("assembly_sha256"),
    }


def reject_triplet(ref, built, name, packets, kwargs, expected_fragment):
    states = {}
    try:
        ref.compile_active_assembly(packets, **kwargs)
        states["reference"] = "ACCEPTED"
    except Exception as exc:
        states["reference"] = type(exc).__name__ + ":" + str(exc)
    args = [as_input(packets), kwargs["current_epoch"], kwargs["max_items"], kwargs["max_per_ancestry"], kwargs["max_context_cost"]]
    try:
        execute(built["program"], "compile_active_assembly", args, Runtime())
        states["interpreter"] = "ACCEPTED"
    except Exception as exc:
        states["interpreter"] = type(exc).__name__ + ":" + str(exc)
    try:
        execute_lowered(built["program"], "compile_active_assembly", args, Runtime())
        states["lowered"] = "ACCEPTED"
    except Exception as exc:
        states["lowered"] = type(exc).__name__ + ":" + str(exc)
    rejected = all(v != "ACCEPTED" for v in states.values())
    semantic = expected_fragment in states["reference"] and expected_fragment in states["interpreter"] and expected_fragment in states["lowered"]
    # Generic require failures intentionally normalize BAD_SCORE/BAD_BUDGET; explicit
    # collision/authority errors must preserve the discriminating semantic identifier.
    return {"name":name,"pass":rejected and semantic,"states":states,"expected_fragment":expected_fragment}


def negative_cases(ref, built):
    base = {"current_epoch":1,"max_items":8,"max_per_ancestry":2,"max_context_cost":None}
    p1 = packet(ref,"collision","A",.5,.5,.5,.5,1,origin_actor="one")
    p2 = packet(ref,"collision","A",.5,.5,.5,.5,1,origin_actor="two")
    authority = packet(ref,"auth","A",.5,.5,.5,.5,1,kind="model_output",proposed_authority=True)
    return [
        reject_triplet(ref,built,"packet_id_collision",[p1,p2],base,"PACKET_ID_COLLISION"),
        reject_triplet(ref,built,"authority_mint_attempt",[authority],base,"AUTHORITY_MINT_ATTEMPT"),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", action="store_true")
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()

    ref = load_reference()
    source = SOURCE.read_text(encoding="utf-8")
    built = compile_source(source)
    positives = [run_positive(ref,built,c) for c in positive_cases(ref)]
    negatives = negative_cases(ref,built)

    generic_only = all(not name.startswith(("frank","active_assembly","packet_")) for name in built["validation"]["generic_builtin_calls"])
    no_effect_authority = built["validation"]["effect_authority_surface"] == []
    pass_ = all(x["pass"] for x in positives + negatives) and generic_only and no_effect_authority

    target_verified = False
    target_identity: dict[str, Any] = {}
    if args.target:
        target_verified, target_identity = verify(args.registration)
        pass_ = pass_ and target_verified and platform.system() == "Linux"

    repo_head = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True,check=False).stdout.strip()
    report = {
        "schema_version":"1.0",
        "experiment":"full frozen FRANK ActiveAssembly through generic structured ClayCode backend",
        "pass":bool(pass_),
        "target_host":TARGET if args.target else "HOSTED_OR_LOCAL_PROXY",
        "target_identity_verified":target_verified,
        "target_identity":target_identity if args.target else None,
        "repository_commit":repo_head,
        "frozen_frank_source_hashes":{"active_assembly.py":sha(REFERENCE)},
        "claycode_source_hashes":{"FRANK_ACTIVE_ASSEMBLY_FULL_V1.clay":sha(SOURCE)},
        "production_chain_receipts":{
            "backend_sha256":sha(BACKEND),
            "semantic_ir_sha256":built["semantic_hash"],
            "lowered_artifact_sha256":built["artifact_hash"],
            "backend_version":VERSION,
        },
        "validation":built["validation"],
        "positive_differentials":positives,
        "negative_differentials":negatives,
        "semantic_escape_hatches":[],
        "generic_builtin_surface":built["validation"]["generic_builtin_calls"],
        "authority_boundary_preserved":no_effect_authority,
        "h2_h3_handoff_ready":bool(pass_ and args.target),
        "counts_as_target_acceptance":bool(pass_ and args.target),
        "counts_as_wp13_pass":bool(pass_ and args.target),
        "scope":"complete frozen H1 ActiveAssembly compile_active_assembly behavior including identity/provenance payload, epoch validity, deterministic bounded selection, ancestry caps, conflict retention, re-expansion refs, context-cost budget, deterministic assembly hash and authority non-minting",
        "note":"No builtin implements FRANK selection semantics; all domain logic is visible in the Clay source. Runtime builtins are generic collections/sort/hash/string/numeric primitives.",
    }
    out = TARGET_OUT if args.target else PROXY_OUT
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"pass":report["pass"],"target":args.target,"positive":sum(x["pass"] for x in positives),"positive_total":len(positives),"negative":sum(x["pass"] for x in negatives),"negative_total":len(negatives),"output":str(out.relative_to(ROOT))}))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
