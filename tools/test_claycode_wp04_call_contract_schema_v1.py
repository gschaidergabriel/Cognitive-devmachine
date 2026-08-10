#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path

import claycode_wp03_typed_ir_v2_state_identity as typed_v2

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
SCHEMA = ROOT / "research_entity/claycode/g9/CLAYCODE_CALL_CONTRACT_SCHEMA_V1_CANDIDATE.clay"


def main() -> int:
    ir = typed_v2.compile_sources([SCHEMA], GRAMMAR)
    assert ir["ir_schema"] == typed_v2.IR_SCHEMA
    assert ir["promotion"] == "NONE"
    assert ir["wp03_status"] == "OPEN"

    sums = {x["name"]: x for x in ir["declarations"] if x.get("kind") == "sum_type"}
    records = {x["name"]: x for x in ir["structural_records"]}
    expected_sums = {"CallEffectClass", "CallResolutionState", "CallBindingAuthority"}
    expected_records = {
        "CallParamContract",
        "CallRuntimeBinding",
        "CallContractIdentity",
        "CallContract",
        "CallContractObligation",
        "CallExecutionPrecondition",
    }
    assert expected_sums <= set(sums)
    assert expected_records <= set(records)

    contract = {
        "identity": {"target": "Needle.execute", "arity": 1},
        "params": [{"name": "intent", "type_name": "EffectIntent"}],
        "returns": "ReceiptRef",
        "effect_class": "EXTERNAL_EFFECT",
        "evidence_refs": ["evidence:b", "evidence:a"],
        "runtime_binding": {
            "binding_id": "runtime:needle-v1",
            "component_hash": "hash:component-a",
            "sealed": True,
            "authority_scope_ref": "scope:needle",
            "rollback_ref": "rollback:needle",
        },
        "binding_authority": "RUNTIME_BROKER_ONLY",
    }
    a = typed_v2.typed_state_identity(ir, "CallContract", contract)
    reordered = copy.deepcopy(contract)
    reordered["evidence_refs"] = list(reversed(reordered["evidence_refs"]))
    b = typed_v2.typed_state_identity(ir, "CallContract", reordered)
    assert a["state_identity_sha256"] == b["state_identity_sha256"]

    changed_binding = copy.deepcopy(contract)
    changed_binding["runtime_binding"]["component_hash"] = "hash:component-b"
    c = typed_v2.typed_state_identity(ir, "CallContract", changed_binding)
    assert c["state_identity_sha256"] != a["state_identity_sha256"]

    changed_target = copy.deepcopy(contract)
    changed_target["identity"]["target"] = "Needle.other"
    d = typed_v2.typed_state_identity(ir, "CallContract", changed_target)
    assert d["state_identity_sha256"] != a["state_identity_sha256"]

    obligation = {
        "identity": {"target": "verify", "arity": 1},
        "occurrences": 1,
        "resolution_state": "UNRESOLVED_SIGNATURE",
        "same_basename_candidates": ["Verifiable.verify"],
        "type_name_resemblance": None,
        "effect_boundary": False,
        "sealed_runtime_binding_required": False,
        "execution_admitted": False,
    }
    o = typed_v2.typed_state_identity(ir, "CallContractObligation", obligation)
    assert o["effect_authority"] == "NONE"

    precondition = {
        "contract_identity": {"target": "Needle.execute", "arity": 1},
        "contract_semantic_hash": a["state_identity_sha256"],
        "runtime_component_hash": "hash:component-a",
        "current_work_revision": "work-rev:current",
        "target_binary_build_hash": "hash:self-root-binary-a",
        "state_lineage_epoch": "state-epoch:41",
        "instance_lease_ref": "lease:self-root-current",
        "instance_lease_epoch": "lease-epoch:9",
        "effect_authority": "RUNTIME_BROKER_ONLY",
    }
    p = typed_v2.typed_state_identity(ir, "CallExecutionPrecondition", precondition)
    changed_binary = copy.deepcopy(precondition)
    changed_binary["target_binary_build_hash"] = "hash:self-root-binary-b"
    p_binary = typed_v2.typed_state_identity(ir, "CallExecutionPrecondition", changed_binary)
    assert p_binary["state_identity_sha256"] != p["state_identity_sha256"]
    changed_lineage = copy.deepcopy(precondition)
    changed_lineage["state_lineage_epoch"] = "state-epoch:42"
    p_lineage = typed_v2.typed_state_identity(ir, "CallExecutionPrecondition", changed_lineage)
    assert p_lineage["state_identity_sha256"] != p["state_identity_sha256"]
    changed_lease = copy.deepcopy(precondition)
    changed_lease["instance_lease_epoch"] = "lease-epoch:10"
    p_lease = typed_v2.typed_state_identity(ir, "CallExecutionPrecondition", changed_lease)
    assert p_lease["state_identity_sha256"] != p["state_identity_sha256"]
    assert "api_token" not in precondition

    report = {
        "status": "PASS",
        "scope": "WP04_CLAYCODE_NATIVE_CALL_CONTRACT_SCHEMA_V1_1_SELF_ROOT_INSTANCE_BOUND",
        "selected_grammar": "BASE_D_V18_REWARD_RELATIONS",
        "new_grammar_required": False,
        "sum_types": sorted(expected_sums),
        "records": sorted(expected_records),
        "call_contract_state_identity": a["state_identity_sha256"],
        "set_order_invariant": True,
        "runtime_component_hash_changes_identity": True,
        "target_changes_identity": True,
        "obligation_state_identity": o["state_identity_sha256"],
        "precondition_state_identity": p["state_identity_sha256"],
        "target_binary_build_hash_changes_precondition_identity": True,
        "state_lineage_epoch_changes_precondition_identity": True,
        "instance_lease_epoch_changes_precondition_identity": True,
        "api_token_in_identity": False,
        "execution_admitted": False,
        "effect_authority": "NONE_FROM_SCHEMA",
        "v19_fn_restoration_needed_for_contract_schema": False,
        "remaining_blocker": "POPULATE_EXACT_EVIDENCE_BACKED_CALL_CONTRACTS_AND_BIND_CURRENT_TARGET_VPS_BINARY_STATE_LEASE_RUNTIME_COMPONENTS",
        "promotion": "NONE",
        "wp03_status": "OPEN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
