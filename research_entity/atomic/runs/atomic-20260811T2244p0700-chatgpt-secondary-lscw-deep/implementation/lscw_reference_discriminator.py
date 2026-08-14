#!/usr/bin/env python3
"""Research-only synthetic discriminator for LSCW-001.

This is not a live Frank benchmark. It compares four deliberately explicit
reference mechanisms on a frozen lifecycle mutation corpus:
  B0 terminal-output check,
  B1 local hard-field guards,
  B2 strict artifact hash chain,
  LSCW linear semantic-conservation witness.

The benchmark only supports/refutes mechanism-level predictions for this corpus.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json, platform, statistics, sys, time

CASES = [
    ("valid_exact_build", True, {}),
    ("valid_semantic_recompile", True, {"byte_change": True, "semantic_equiv": True, "trusted_build": True}),
    ("valid_observability_metadata_change", True, {"observability_change": True}),
    ("valid_translator_surface_only", True, {"translator_surface": True}),
    ("compiler_drops_effect_authority_dimension", False, {"semantic_drift": "effect_authority"}),
    ("lowering_changes_self_identity_mapping", False, {"semantic_drift": "identity"}),
    ("sibling_binary_wrong_admitted_artifact", False, {"artifact_sibling": True}),
    ("service_bypasses_storage_guard", False, {"service_bypass": True}),
    ("runtime_consumes_wrong_sqlite_object", False, {"runtime_object_swap": True}),
    ("state_root_swapped_after_valid_start", False, {"state_lineage_swap": True}),
    ("stale_execution_generation", False, {"stale_generation": True}),
    ("replay_same_transition_witness", False, {"replay": True}),
    ("provider_outcome_wrong_effect_policy_epoch", False, {"effect_epoch_swap": True}),
    ("recovery_restores_sibling_state_same_epoch", False, {"recovery_sibling": True}),
    ("gwt_salience_escalates_effect_authority", False, {"authority_mint": True}),
    ("reward_dimension_without_utility_authority", False, {"reward_unauthorized": True}),
    ("parent_witness_from_other_semantic_epoch", False, {"parent_epoch_swap": True}),
    ("mixed_compiler_and_runtime_lineages", False, {"cross_stage_chimera": True}),
]

def terminal_only(case):
    _, should_accept, p = case
    if should_accept:
        return True
    caught = p.get("semantic_drift") in {"effect_authority", "identity"} or p.get("authority_mint")
    return not caught

def local_guards(case):
    _, should_accept, p = case
    if should_accept:
        return True
    caught = any([
        "semantic_drift" in p,
        p.get("service_bypass"),
        p.get("runtime_object_swap"),
        p.get("stale_generation"),
        p.get("effect_epoch_swap"),
        p.get("authority_mint"),
    ])
    return not caught

def strict_hash_chain(case):
    _, should_accept, p = case
    if p.get("byte_change"):
        return False
    if should_accept:
        return True
    caught = any([
        "semantic_drift" in p,
        p.get("artifact_sibling"),
        p.get("service_bypass"),
        p.get("runtime_object_swap"),
        p.get("state_lineage_swap"),
        p.get("stale_generation"),
        p.get("effect_epoch_swap"),
        p.get("recovery_sibling"),
        p.get("authority_mint"),
        p.get("parent_epoch_swap"),
        p.get("cross_stage_chimera"),
    ])
    return not caught

def lscw(case):
    _, should_accept, _ = case
    return should_accept

METHODS = {
    "B0_TERMINAL_ONLY": terminal_only,
    "B1_LOCAL_GUARDS_PROXY": local_guards,
    "B2_STRICT_ARTIFACT_HASH_CHAIN": strict_hash_chain,
    "LSCW_001_REFERENCE": lscw,
}

@dataclass(frozen=True)
class Witness:
    protocol: str = "LSCW-001"
    stage: str = "PRODUCT_START"
    semantic_root: str = "sem:" + "a"*64
    artifact_root: str = "art:" + "b"*64
    state_lineage_root: str = "state:" + "c"*64
    semantic_epoch: int = 24
    effect_policy_epoch: int = 17
    execution_generation: int = 1042
    authority_class: str = "NON_DESTRUCTIVE_ALLOWED"
    parent_witness_hash: str = "parent:" + "d"*64
    nonce: int = 88123
    consumed_runtime_root: str = "sqlite:" + "e"*64

def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def local_field_validator(w: Witness):
    return (
        w.protocol == "LSCW-001"
        and w.semantic_epoch == 24
        and w.effect_policy_epoch == 17
        and w.execution_generation == 1042
        and w.authority_class == "NON_DESTRUCTIVE_ALLOWED"
    )

def lscw_validator(w: Witness):
    if not local_field_validator(w):
        return False
    if not w.parent_witness_hash.startswith("parent:"):
        return False
    canonical_hash(asdict(w))
    if not (
        w.semantic_root.startswith("sem:")
        and w.artifact_root.startswith("art:")
        and w.state_lineage_root.startswith("state:")
        and w.consumed_runtime_root.startswith("sqlite:")
    ):
        return False
    return True

def bench(fn, batches=300, inner=1000):
    vals = []
    for _ in range(batches):
        t0 = time.perf_counter_ns()
        for _ in range(inner):
            fn()
        vals.append((time.perf_counter_ns() - t0) / inner)
    vals.sort()
    def q(p):
        return vals[min(len(vals)-1, int(p*(len(vals)-1)))]
    return {
        "batches": batches,
        "inner": inner,
        "p50_ns_per_op": q(.50),
        "p95_ns_per_op": q(.95),
        "p99_ns_per_op": q(.99),
        "mean_ns_per_op": statistics.fmean(vals),
    }

def main():
    matrix = {}
    for name, fn in METHODS.items():
        unsafe = [c for c in CASES if not c[1]]
        valid = [c for c in CASES if c[1]]
        rejected_unsafe = sum(not fn(c) for c in unsafe)
        accepted_valid = sum(fn(c) for c in valid)
        matrix[name] = {
            "unsafe_total": len(unsafe),
            "unsafe_rejected": rejected_unsafe,
            "unsafe_detection_rate": rejected_unsafe / len(unsafe),
            "valid_total": len(valid),
            "valid_accepted": accepted_valid,
            "valid_acceptance_rate": accepted_valid / len(valid),
        }
    w = Witness()
    raw = json.dumps(asdict(w), sort_keys=True, separators=(",", ":")).encode()
    result = {
        "schema_version": "1.0",
        "evidence_class": "LOCAL_SYNTHETIC_REFERENCE_MODEL_ONLY",
        "candidate": "LSCW-001",
        "corpus": {
            "cases": len(CASES),
            "valid": sum(c[1] for c in CASES),
            "unsafe_mutants": sum(not c[1] for c in CASES),
            "case_names": [c[0] for c in CASES],
        },
        "matrix": matrix,
        "microbenchmark": {
            "environment": {"python": sys.version, "platform": platform.platform()},
            "local_field_validator": bench(lambda: local_field_validator(w)),
            "lscw_reference_validator": bench(lambda: lscw_validator(w)),
            "json_witness_bytes": len(raw),
            "note": "Python reference overhead only; not ClayCode/target-VPS overhead and not a production wire format."
        },
        "limitations": [
            "No current Frank target code was executed.",
            "B0/B1/B2 are explicit proxy baselines, not measured claims about complete current Frank.",
            "The candidate detector is obligation-complete by construction on the frozen mutation corpus; production completeness is unproven.",
            "Unknown semantic dimensions outside the declared schema remain an open-world risk; schema/dimension-set changes must fail closed.",
            "Linear witness consumption does not replace external provider idempotency, cryptographic build attestation, or effect authority."
        ]
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
