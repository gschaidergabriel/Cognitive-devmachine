#!/usr/bin/env python3
"""CC-WP-13 H2 differential: frozen FRANK ActiveAssembly via generic ClayCode record FFI.

This test attempts to falsify the remaining language counterexample. The ClayCode source
uses one general-purpose typed host signature (String -> String). The sealed runtime
adapter is a domain-neutral deterministic structured-record selector whose exact policy
hash is bound into the host-minted capability. No FRANK-specific opcode or authority
primitive is added to the language.

The observed H2 result is compared byte-for-byte/field-for-field with the frozen H1
ActiveAssembly reference over adversarial fixtures and randomized packet sets. A second,
non-FRANK scheduler workload uses the same selector to test that the primitive is not a
FRANK semantic escape hatch.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "research_entity/harness/reference"))

import claycode_base_effect_pipeline as ep  # noqa: E402
from claycode_base_record_selection import (  # noqa: E402
    RecordSelectionError,
    VERSION as RECORD_SELECTOR_VERSION,
    canonical_bytes,
    select_json,
    select_records,
    sha256_value,
)
from claycode_base_runtime import CapabilityFault, ClayRuntime, RUNTIME_VERSION  # noqa: E402
from active_assembly import (  # noqa: E402
    ActiveAssemblyError,
    AssemblyPacket,
    compile_active_assembly,
)

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
SOURCE_FILE = ROOT / "research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_H2_V1.clay"
OUT = ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H2_RECEIPT.json"
HOST_NAME = "host.records_select_json"
EFFECT = "RECORD_SELECT"
SYMBOLIC_CAP = "cap.data.records"
RUNTIME_CAP = "data.records"
ADAPTER = "data.records_select_json"
CTX = {
    "origin_hash": hashlib.sha256(b"frank-active-assembly-h2").hexdigest(),
    "basis_hash": hashlib.sha256(b"frozen-h1-active-assembly-v1.2").hexdigest(),
    "selection_hash": hashlib.sha256(b"generic-record-selection-policy").hexdigest(),
    "closure_hash": hashlib.sha256(b"typed-ffi-sealed-runtime").hexdigest(),
}


def h1_policy(current_epoch: int, max_items: int, max_per_ancestry: int, max_context_cost: int | None) -> dict[str, Any]:
    return {
        "id_field": "packet_id",
        "group_field": "ancestry_family",
        "kind_field": "kind",
        "authority_flag_field": "proposed_authority",
        "deny_authority_kinds": ["model_output", "peer_result", "visual_model", "capability"],
        "required_nonempty_fields": ["packet_id", "ancestry_family", "kind"],
        "cost_field": "context_cost",
        "score": {
            "round": 12,
            "terms": [
                {"field": "relevance", "weight": 0.45, "validate_unit_interval": True},
                {"field": "impact", "weight": 0.25, "validate_unit_interval": True},
                {"field": "novelty", "weight": 0.15, "validate_unit_interval": True},
                {"field": "uncertainty", "weight": 0.15, "transform": "one_minus", "validate_unit_interval": True},
            ],
        },
        "eligibility": {"field": "valid_epoch", "equals": current_epoch, "reason": "STALE_EPOCH"},
        "conflict": {"key_field": "claim_key", "value_field": "claim_value"},
        "max_items": max_items,
        "max_per_group": max_per_ancestry,
        "max_cost": max_context_cost,
        "reexpand_field": "reexpand_ref",
        "output": {
            "fixed": {
                "schema": "frank.active-assembly.v1.2",
                "current_epoch": current_epoch,
                "max_items": max_items,
                "max_per_ancestry": max_per_ancestry,
                "max_context_cost": max_context_cost,
            },
            "selected_field": "items",
            "identity_annotation": "packet_identity_sha256",
            "score_annotation": "score",
            "role_annotation": "selection_role",
            "replication_annotation": "independent_replication_credit",
            "authority_annotation": "execution_authority",
            "reexpand_refs_field": "reexpand_refs",
            "omitted_count_field": "omitted_count",
            "omitted_reasons_field": "omitted_reasons",
            "cost_used_field": "context_cost_used",
            "cost_remaining_field": "context_cost_remaining",
            "hash_field": "assembly_sha256",
            "duplicate_count_field": "input_duplicate_count",
        },
    }


def request_json(packets: list[AssemblyPacket], policy: dict[str, Any]) -> str:
    return canonical_bytes({"records": [asdict(p) for p in packets], "policy": policy}).decode("utf-8")


def runtime_adapter(cap_policy: dict[str, Any], request: str) -> str:
    max_bytes = int(cap_policy.get("max_input_bytes", 2_000_000))
    if len(request.encode("utf-8")) > max_bytes:
        raise RecordSelectionError("REQUEST_TOO_LARGE")
    obj = json.loads(request)
    if not isinstance(obj, dict) or not isinstance(obj.get("policy"), dict):
        raise RecordSelectionError("REQUEST_POLICY_MISSING")
    policy_hash = sha256_value(obj["policy"])
    if policy_hash != cap_policy.get("selector_policy_sha256"):
        raise CapabilityFault("SELECTOR_POLICY_NOT_BOUND_TO_CAPABILITY")
    return select_json(request)


class RuntimeGateway:
    def __init__(self, root: Path, policy: dict[str, Any], *, mint: bool = True):
        self.runtime = ClayRuntime(root)
        self.runtime.register_adapter(ADAPTER, RUNTIME_CAP, runtime_adapter)
        self.handle = None
        if mint:
            self.handle = self.runtime.mint_capability(
                RUNTIME_CAP,
                {
                    "selector_policy_sha256": sha256_value(policy),
                    "max_input_bytes": 2_000_000,
                    "max_calls": 4,
                    "max_units": 10_000_000,
                    "require_context": True,
                },
                CTX,
            )

    def effect(self, effect: str, symbolic_capability: str, request: str) -> str:
        if effect != EFFECT or symbolic_capability != SYMBOLIC_CAP:
            raise CapabilityFault("UNEXPECTED_TYPED_FFI_EFFECT")
        if self.handle is None:
            raise CapabilityFault("MISSING_BEARER_HANDLE")
        return self.runtime.invoke_bound(ADAPTER, self.handle, CTX, request)


def execute_both(built: dict[str, Any], request: str, policy: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str], list[str]]:
    with tempfile.TemporaryDirectory(prefix="claycode-h2-ref-") as td1, tempfile.TemporaryDirectory(prefix="claycode-h2-low-") as td2:
        g1 = RuntimeGateway(Path(td1), policy)
        g2 = RuntimeGateway(Path(td2), policy)
        reference = json.loads(ep.eval_function(built["ir"], "compile", [request], g1))
        lowered = json.loads(ep.exec_lowered(built["artifact"], "compile", [request], g2))
        t1 = [x["adapter"] for x in g1.runtime.trace_receipt()]
        t2 = [x["adapter"] for x in g2.runtime.trace_receipt()]
        return reference, lowered, t1, t2


def random_packet(rng: random.Random, trial: int, index: int, epoch: int) -> AssemblyPacket:
    claim_key = rng.choice([None, None, "weather", "route", "risk"])
    claim_value = None if claim_key is None else rng.choice(["A", "B", "C"])
    return AssemblyPacket(
        packet_id=f"t{trial:03d}-p{index:03d}",
        ancestry_family=f"fam-{rng.randrange(5)}",
        kind=rng.choice(["evidence", "hypothesis", "model_output", "peer_result", "visual_model", "capability"]),
        relevance=round(rng.random(), 6),
        impact=round(rng.random(), 6),
        novelty=round(rng.random(), 6),
        uncertainty=round(rng.random(), 6),
        valid_epoch=epoch if rng.random() < 0.78 else epoch - rng.randint(1, 3),
        claim_key=claim_key,
        claim_value=claim_value,
        reexpand_ref=(f"ref-{trial}-{index}" if rng.random() < 0.35 else None),
        origin_actor=rng.choice([None, "user", "sensor", "researcher-a", "researcher-b"]),
        proposed_authority=False,
        context_cost=rng.randint(1, 5),
    )


def generic_scheduler_probe() -> dict[str, Any]:
    records = [
        {"job_id": "j1", "team": "A", "kind": "build", "privileged": False, "priority": .9, "urgency": .8, "risk": .2, "generation": 7, "resource": "gpu", "mode": "write", "resume": "r1", "cost": 2},
        {"job_id": "j2", "team": "A", "kind": "build", "privileged": False, "priority": .7, "urgency": .9, "risk": .1, "generation": 7, "resource": "gpu", "mode": "read", "resume": "r2", "cost": 1},
        {"job_id": "j3", "team": "B", "kind": "test", "privileged": False, "priority": .6, "urgency": .4, "risk": .3, "generation": 7, "resource": "cpu", "mode": "read", "resume": "r3", "cost": 1},
        {"job_id": "j4", "team": "C", "kind": "deploy", "privileged": False, "priority": .99, "urgency": 1.0, "risk": .7, "generation": 6, "resource": "net", "mode": "write", "resume": "r4", "cost": 3},
    ]
    policy = {
        "id_field": "job_id",
        "group_field": "team",
        "kind_field": "kind",
        "authority_flag_field": "privileged",
        "deny_authority_kinds": ["shell"],
        "required_nonempty_fields": ["job_id", "team", "kind"],
        "cost_field": "cost",
        "score": {"round": 12, "terms": [
            {"field": "priority", "weight": .6, "validate_unit_interval": True},
            {"field": "urgency", "weight": .3, "validate_unit_interval": True},
            {"field": "risk", "weight": .1, "transform": "one_minus", "validate_unit_interval": True},
        ]},
        "eligibility": {"field": "generation", "equals": 7, "reason": "STALE_GENERATION"},
        "conflict": {"key_field": "resource", "value_field": "mode"},
        "max_items": 3,
        "max_per_group": 1,
        "max_cost": 4,
        "reexpand_field": "resume",
        "output": {"fixed": {"schema": "scheduler.selection.v1"}},
    }
    a = select_records(records, policy)
    b = select_records(list(reversed(records)), policy)
    ids = [x["job_id"] for x in a["items"]]
    return {
        "pass": a == b and bool(ids) and a["schema"] == "scheduler.selection.v1" and all("packet_id" not in x for x in a["items"]),
        "selected_job_ids": ids,
        "selection_sha256": a["selection_sha256"],
        "order_invariant": a == b,
    }


def main() -> int:
    # Add one general-purpose typed host signature. It is not a FRANK opcode.
    previous = ep.HOST.get(HOST_NAME)
    ep.HOST[HOST_NAME] = {"params": ["String"], "result": "String", "effect": EFFECT, "cap": SYMBOLIC_CAP}
    source = SOURCE_FILE.read_text(encoding="utf-8")
    grammar = GRAMMAR.read_text(encoding="utf-8")
    built = ep.build(source, grammar)

    rng = random.Random(202608091251)
    random_failures: list[dict[str, Any]] = []
    trace_failures = 0
    random_cases = 128
    for trial in range(random_cases):
        epoch = rng.randint(1, 20)
        max_items = rng.randint(1, 8)
        max_per = rng.randint(1, 3)
        max_cost = None if rng.random() < 0.35 else rng.randint(3, 24)
        packets = [random_packet(rng, trial, i, epoch) for i in range(rng.randint(3, 24))]
        policy = h1_policy(epoch, max_items, max_per, max_cost)
        req = request_json(packets, policy)
        expected = compile_active_assembly(packets, current_epoch=epoch, max_items=max_items, max_per_ancestry=max_per, max_context_cost=max_cost)
        reference, lowered, t1, t2 = execute_both(built, req, policy)
        if reference != expected or lowered != expected:
            random_failures.append({
                "trial": trial,
                "expected_hash": expected.get("assembly_sha256"),
                "reference_hash": reference.get("assembly_sha256"),
                "lowered_hash": lowered.get("assembly_sha256"),
            })
        if t1 != t2 or t1 != [ADAPTER]:
            trace_failures += 1

    # Exact delivery duplication is semantic-idempotent and telemetry-only.
    p = AssemblyPacket("dup", "fam", "evidence", .8, .7, .4, .2, 5, reexpand_ref="r", origin_actor="sensor", context_cost=1)
    pol = h1_policy(5, 4, 2, 8)
    single = compile_active_assembly([p], current_epoch=5, max_items=4, max_per_ancestry=2, max_context_cost=8)
    dup_expected = compile_active_assembly([p, p], current_epoch=5, max_items=4, max_per_ancestry=2, max_context_cost=8)
    dup_ref, dup_low, _, _ = execute_both(built, request_json([p, p], pol), pol)
    duplicate_ok = (
        dup_expected == dup_ref == dup_low
        and dup_expected["input_duplicate_count"] == 1
        and dup_expected["assembly_sha256"] == single["assembly_sha256"]
    )

    # Same id with different semantic payload must fail closed in both H1 and H2.
    collision = AssemblyPacket("dup", "fam", "evidence", .1, .7, .4, .2, 5, context_cost=1)
    h1_collision_rejected = False
    h2_collision_rejected = False
    try:
        compile_active_assembly([p, collision], current_epoch=5)
    except ActiveAssemblyError:
        h1_collision_rejected = True
    try:
        execute_both(built, request_json([p, collision], h1_policy(5, 8, 2, None)), h1_policy(5, 8, 2, None))
    except RecordSelectionError:
        h2_collision_rejected = True

    # Model/peer/visual/capability data cannot propose execution authority.
    authority_packet = AssemblyPacket("auth", "fam", "model_output", .9, .9, .9, .1, 5, proposed_authority=True, context_cost=1)
    h1_authority_rejected = False
    h2_authority_rejected = False
    try:
        compile_active_assembly([authority_packet], current_epoch=5)
    except ActiveAssemblyError:
        h1_authority_rejected = True
    auth_policy = h1_policy(5, 8, 2, None)
    try:
        execute_both(built, request_json([authority_packet], auth_policy), auth_policy)
    except RecordSelectionError:
        h2_authority_rejected = True

    # A textual policy mutation cannot widen the host-minted selector semantics.
    policy_tamper_rejected = False
    base_policy = h1_policy(5, 8, 2, None)
    tampered = h1_policy(5, 99, 99, None)
    with tempfile.TemporaryDirectory(prefix="claycode-h2-policy-") as td:
        gw = RuntimeGateway(Path(td), base_policy)
        try:
            ep.eval_function(built["ir"], "compile", [request_json([p], tampered)], gw)
        except CapabilityFault:
            policy_tamper_rejected = True

    descriptor_not_authority = False
    with tempfile.TemporaryDirectory(prefix="claycode-h2-desc-") as td:
        gw = RuntimeGateway(Path(td), base_policy)
        desc = gw.runtime.capability_descriptor(gw.handle)
        try:
            gw.runtime.invoke_bound(ADAPTER, desc, CTX, request_json([p], base_policy))
        except CapabilityFault:
            descriptor_not_authority = True

    scheduler = generic_scheduler_probe()
    main_fn = next(x for x in built["ir"]["functions"] if x["name"] == "compile")
    checks = {
        "typed_string_to_string_ffi": main_fn["params"] == [{"name": "request", "type": "String"}] and main_fn["return"] == "String",
        "effect_and_capability_closure_exact": main_fn["effect_summary"] == [EFFECT] and main_fn["required_capabilities"] == [SYMBOLIC_CAP],
        "random_h1_h2_exact_differential": not random_failures,
        "interpreter_lowered_runtime_trace_equivalent": trace_failures == 0,
        "duplicate_delivery_semantic_idempotence": duplicate_ok,
        "packet_identity_collision_fail_closed": h1_collision_rejected and h2_collision_rejected,
        "authority_mint_attempt_fail_closed": h1_authority_rejected and h2_authority_rejected,
        "selector_policy_hash_bound_to_capability": policy_tamper_rejected,
        "capability_descriptor_not_authority": descriptor_not_authority,
        "same_primitive_non_frank_scheduler": scheduler["pass"],
    }
    passed = all(checks.values())
    report = {
        "schema_version": "1.0",
        "experiment": "FRANK H1 ActiveAssembly -> H2 ClayCode generic typed-record FFI differential",
        "source": str(SOURCE_FILE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "semantic_hash": built["semantic_hash"],
        "lowered_artifact_hash": built["artifact_hash"],
        "translation_contract_hash": built["translation_contract_hash"],
        "compiler_candidate": built["candidate_version"],
        "record_selector_version": RECORD_SELECTOR_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "random_cases": random_cases,
        "random_failures": random_failures,
        "trace_failures": trace_failures,
        "scheduler_genericity_probe": scheduler,
        "checks": checks,
        "pass": passed,
        "counts_as_target_acceptance": False,
        "counts_as_wp13_pass": False,
        "language_change_required_by_this_counterexample": False if passed else None,
        "counterexample_disposition": "IMPLEMENTABLE_VIA_GENERIC_TYPED_FFI_RUNTIME_COLLECTION" if passed else "REMAINS_OPEN",
        "authority_invariant": "model output / serialized records / descriptors / symbolic capability names != execution authority",
        "claim_boundary": "A PASS falsifies the need for FRANK-specific language semantics for the frozen H1 ActiveAssembly behavior. WP13/APP10 still require this same path to execute on the registered Andreas Ubuntu target and be integrated into the full H2/H3 handoff receipt.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "random_cases": random_cases, "random_failures": len(random_failures), "checks": checks, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    if previous is None:
        ep.HOST.pop(HOST_NAME, None)
    else:
        ep.HOST[HOST_NAME] = previous
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
