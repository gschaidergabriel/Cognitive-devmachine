#!/usr/bin/env python3
"""Executable validation for the independent exact CallContract/runtime-binding probe."""
from __future__ import annotations

import copy
import hashlib
import json

from claycode_base_call_contract_resolver import (
    CallContract,
    CallContractError,
    CallSite,
    CurrentExecutionIdentity,
    RuntimeBinding,
    admit_call,
    diagnostic_alternatives,
)

REAL_G9_PAIRS = [
    ("resolve_latest", 3), ("task", 1), ("load_dialects", 1), ("verify", 5),
    ("normalize", 1), ("observe_changes", 2), ("apply_incremental", 1),
    ("task_relevant", 1), ("state.query", 1), ("graph.project", 1),
    ("preserve_conflict_unknown", 1), ("state.open_pressures", 1), ("emerge", 1),
    ("gwt.select", 1), ("state.answer_capsule", 1), ("cognitive_choice", 1),
    ("EffectIntent", 1), ("Needle.execute", 1), ("verify", 1), ("causal_credit", 2),
    ("frank_reward.derive_typed_reward_outcome_evidence", 3), ("frank_reward.update", 1),
    ("frank_reward.control", 2), ("admit_slow_plasticity", 3), ("Delta", 1),
    ("reenter", 1), ("meta.analyze_explicit_turn", 0),
]


def expect_reject(label, fn):
    try:
        fn()
    except CallContractError as exc:
        return {"case": label, "pass": True, "error": str(exc)}
    return {"case": label, "pass": False, "error": "unexpected_accept"}


def main() -> int:
    current = CurrentExecutionIdentity(
        work_revision="WORK-CALLCONTRACT-v1",
        target_binary_sha256="b" * 64,
        state_lineage_epoch="42",
        instance_lease_ref="lease:self.root:current",
        instance_lease_epoch="9",
    )
    pure = CallContract(
        target="clay.test.echo",
        param_types=("String",),
        return_type="String",
        effect_class="PURE",
        evidence_refs=("fixture:typed-contract",),
    )
    pure_binding = RuntimeBinding(
        target=pure.target, arity=pure.arity, contract_semantic_hash=pure.semantic_hash,
        component_sha256="c" * 64, work_revision=current.work_revision,
        target_binary_sha256=current.target_binary_sha256,
        state_lineage_epoch=current.state_lineage_epoch,
        instance_lease_ref=current.instance_lease_ref,
        instance_lease_epoch=current.instance_lease_epoch,
    )
    positive = admit_call(CallSite("clay.test.echo", ("String",)), [pure], [pure_binding], current)

    effect = CallContract(
        target="clay.test.effect", param_types=("IntentRef",), return_type="EffectReceipt",
        effect_class="EXTERNAL_EFFECT", evidence_refs=("fixture:effect-contract",),
    )
    effect_binding = RuntimeBinding(
        target=effect.target, arity=effect.arity, contract_semantic_hash=effect.semantic_hash,
        component_sha256="d" * 64, work_revision=current.work_revision,
        target_binary_sha256=current.target_binary_sha256,
        state_lineage_epoch=current.state_lineage_epoch,
        instance_lease_ref=current.instance_lease_ref,
        instance_lease_epoch=current.instance_lease_epoch,
        authority_scope="fixture:safe-effect", rollback_ref="fixture:rollback",
    )
    effect_positive = admit_call(CallSite(effect.target, ("IntentRef",)), [effect], [effect_binding], current)

    negatives = []
    negatives.append(expect_reject("suffix_shadow", lambda: admit_call(
        CallSite("echo", ("String",)), [pure], [pure_binding], current)))
    negatives.append(expect_reject("wrong_arity", lambda: admit_call(
        CallSite(pure.target, ("String", "String")), [pure], [pure_binding], current)))
    negatives.append(expect_reject("wrong_arg_type", lambda: admit_call(
        CallSite(pure.target, ("Bytes",)), [pure], [pure_binding], current)))
    dynamic = CallContract("clay.test.dynamic", ("Any",), "String", "PURE", ("fixture",))
    negatives.append(expect_reject("dynamic_param", lambda: admit_call(
        CallSite(dynamic.target, ("Any",)), [dynamic], [], current)))
    dynamic_ret = CallContract("clay.test.dynamicret", ("String",), "Dynamic", "PURE", ("fixture",))
    negatives.append(expect_reject("dynamic_return", lambda: admit_call(
        CallSite(dynamic_ret.target, ("String",)), [dynamic_ret], [], current)))
    duplicate = copy.deepcopy(pure)
    negatives.append(expect_reject("duplicate_exact_contract", lambda: admit_call(
        CallSite(pure.target, ("String",)), [pure, duplicate], [pure_binding], current)))
    stale_binding = copy.deepcopy(pure_binding)
    object.__setattr__(stale_binding, "work_revision", "STALE")
    negatives.append(expect_reject("stale_work_revision", lambda: admit_call(
        CallSite(pure.target, ("String",)), [pure], [stale_binding], current)))
    no_scope = copy.deepcopy(effect_binding)
    object.__setattr__(no_scope, "authority_scope", None)
    negatives.append(expect_reject("effect_missing_scope", lambda: admit_call(
        CallSite(effect.target, ("IntentRef",)), [effect], [no_scope], current)))
    no_rollback = copy.deepcopy(effect_binding)
    object.__setattr__(no_rollback, "rollback_ref", None)
    negatives.append(expect_reject("effect_missing_rollback", lambda: admit_call(
        CallSite(effect.target, ("IntentRef",)), [effect], [no_rollback], current)))
    non_effect_scope = copy.deepcopy(pure_binding)
    object.__setattr__(non_effect_scope, "authority_scope", "unexpected")
    negatives.append(expect_reject("non_effect_authority_metadata", lambda: admit_call(
        CallSite(pure.target, ("String",)), [pure], [non_effect_scope], current)))

    # Real G9 identities remain fail-closed because this validation deliberately supplies no
    # invented production CallContracts. Diagnostic shadows can be suggested but never admitted.
    real_negative = []
    shadow_contracts = [
        CallContract("Shadow." + t, tuple("T" for _ in range(a)), "Unit", "PURE", ("adversarial",))
        for t, a in REAL_G9_PAIRS if t != "Needle.execute"
    ]
    for target, arity in REAL_G9_PAIRS:
        site = CallSite(target, tuple("T" for _ in range(arity)))
        real_negative.append(expect_reject(
            f"real_unresolved::{target}/{arity}",
            lambda s=site: admit_call(s, shadow_contracts, [], current),
        ))
    diagnostics = diagnostic_alternatives(CallSite("verify", ("T",)), shadow_contracts)

    passed = positive["admitted"] and effect_positive["admitted"] and all(
        x["pass"] for x in negatives + real_negative
    )
    out = {
        "schema_version": "1.0",
        "test": "CC_BASE_EXACT_CALLCONTRACT_RUNTIME_BINDING",
        "pass": passed,
        "positive_non_effect": positive,
        "positive_external_effect": effect_positive,
        "negative_controls": {
            "passed": sum(x["pass"] for x in negatives),
            "total": len(negatives),
            "cases": negatives,
        },
        "real_g9_unresolved_fail_closed": {
            "passed": sum(x["pass"] for x in real_negative),
            "total": len(real_negative),
        },
        "diagnostic_alternatives_are_non_authoritative": diagnostics,
        "production_contracts_invented": False,
        "needle_execute_production_authority_changed": False,
        "scope": "Mechanism validation only; production G9 CallContracts and target-VPS bindings remain required.",
    }
    canonical = json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    out["result_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
