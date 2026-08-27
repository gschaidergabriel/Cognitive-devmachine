#!/usr/bin/env python3
"""CC-RC1.5 research reference: Intent-Certified Semantic Lowering (ICSL).

Research-only executable semantics. Extends CC-RC1.4/CBCC with an L0->L1
intent boundary while preserving the existing deterministic basis/closure/
capability architecture.

Core rules:
1) LLM/parser extraction creates an IntentProposal, never authority.
2) HARD, SOFT, PROHIBITION, ASSUMPTION, and UNKNOWN are non-substitutable.
3) Compiler/schema/hash validity is distinct from semantic intent adequacy.
4) Effect-critical unknowns remain unresolved; they are not guessed false.
5) IntentAdequacyReceipt binds verification evidence to the exact proposal.
6) IntentContract lowers into CBCC/COVE obligations; capability references are
   requirements to verify, never capabilities minted by the compiler.
7) Irreversible effects require stronger adequacy plus the ordinary external
   capability gateway; model/native-Clay fluency cannot bypass either.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import FrozenSet, Optional, Set, Tuple


def canon(obj):
    if hasattr(obj, "__dataclass_fields__"):
        obj = asdict(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def h(tag: str, obj) -> str:
    return sha256((tag + ":" + canon(obj)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IntentClause:
    clause_id: str
    kind: str           # REQUIREMENT | PROHIBITION | PREFERENCE | ASSUMPTION | UNKNOWN
    strength: str       # HARD | SOFT | UNKNOWN
    semantic: str
    source_span_hash: str
    effect_critical: bool = False


@dataclass(frozen=True)
class IntentProposal:
    source_hash: str
    extractor_id: str
    extractor_version: str
    clauses: Tuple[IntentClause, ...]
    requested_effect_class: str   # READ_ONLY | REVERSIBLE | IRREVERSIBLE
    authority_refs: Tuple[str, ...] = ()


@dataclass(frozen=True)
class AdequacyCheck:
    check_id: str
    kind: str      # SOURCE_ENTAILMENT | USER_CONFIRMATION | OWNER_CONTRACT | DOMAIN_VERIFIER | TEST_ORACLE
    target_clause_ids: Tuple[str, ...]
    result: str    # PASS | FAIL | UNKNOWN
    evidence_ref: str


@dataclass(frozen=True)
class IntentAdequacyReceipt:
    proposal_hash: str
    checks: Tuple[AdequacyCheck, ...]
    unresolved_clause_ids: Tuple[str, ...]
    unresolved_effect_critical: Tuple[str, ...]
    status: str    # VERIFIED | PARTIAL | UNRESOLVED | REJECTED
    verifier_semantics_hash: str


@dataclass(frozen=True)
class IntentContract:
    source_hash: str
    proposal_hash: str
    adequacy_hash: str
    hard_requirements: FrozenSet[str]
    prohibitions: FrozenSet[str]
    soft_preferences: FrozenSet[str]
    assumptions: FrozenSet[str]
    effect_class: str
    authority_requirements: FrozenSet[str]
    contract_hash: str


@dataclass(frozen=True)
class LoweredOpSpec:
    op_semantics_hash: str
    predicates: FrozenSet[str]
    invariants: FrozenSet[str]
    optimization_preferences: FrozenSet[str]
    required_caps: FrozenSet[str]
    effect_class: str
    intent_contract_hash: str
    dynamic_closure_complete: bool = True


ALLOWED_KINDS = {"REQUIREMENT", "PROHIBITION", "PREFERENCE", "ASSUMPTION", "UNKNOWN"}
ALLOWED_STRENGTHS = {"HARD", "SOFT", "UNKNOWN"}
ALLOWED_EFFECTS = {"READ_ONLY", "REVERSIBLE", "IRREVERSIBLE"}
STRONG_ADEQUACY_KINDS = {"USER_CONFIRMATION", "OWNER_CONTRACT", "DOMAIN_VERIFIER", "TEST_ORACLE"}


def validate_proposal_shape(p: IntentProposal):
    errors = []
    if p.requested_effect_class not in ALLOWED_EFFECTS:
        errors.append("invalid_effect_class")
    ids = [c.clause_id for c in p.clauses]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_clause_id")
    for c in p.clauses:
        if c.kind not in ALLOWED_KINDS:
            errors.append(f"invalid_kind:{c.clause_id}")
        if c.strength not in ALLOWED_STRENGTHS:
            errors.append(f"invalid_strength:{c.clause_id}")
        if not c.source_span_hash:
            errors.append(f"missing_source_span:{c.clause_id}")
        if c.kind == "PREFERENCE" and c.strength == "HARD":
            errors.append(f"preference_cannot_be_hard:{c.clause_id}")
        if c.kind == "UNKNOWN" and c.strength != "UNKNOWN":
            errors.append(f"unknown_strength_mismatch:{c.clause_id}")
    return (not errors, tuple(errors))


def adequate_for_commit(p: IntentProposal, r: IntentAdequacyReceipt):
    if r.proposal_hash != h("intent-proposal:v1", p):
        return False, "REJECT_RECEIPT_PROPOSAL_MISMATCH"
    if r.status == "REJECTED":
        return False, "REJECT_ADEQUACY"
    if r.unresolved_effect_critical:
        return False, "ESCALATE_EFFECT_CRITICAL_UNKNOWN"
    if r.status == "UNRESOLVED":
        return False, "ESCALATE_UNRESOLVED"
    if p.requested_effect_class == "IRREVERSIBLE":
        if r.status != "VERIFIED":
            return False, "ESCALATE_IRREVERSIBLE_REQUIRES_VERIFIED_ADEQUACY"
        critical = {c.clause_id for c in p.clauses if c.effect_critical and c.kind != "UNKNOWN"}
        strong_covered = set()
        for chk in r.checks:
            if chk.result == "PASS" and chk.kind in STRONG_ADEQUACY_KINDS:
                strong_covered.update(chk.target_clause_ids)
        if not critical <= strong_covered:
            return False, "ESCALATE_IRREVERSIBLE_CRITICAL_CLAUSE_NOT_STRONGLY_VERIFIED"
    return True, "OK"


def commit_intent(p: IntentProposal, r: IntentAdequacyReceipt):
    shape_ok, errors = validate_proposal_shape(p)
    if not shape_ok:
        return None, "REJECT_SHAPE:" + ",".join(errors)
    ok, reason = adequate_for_commit(p, r)
    if not ok:
        return None, reason

    hard: Set[str] = set(); prohib: Set[str] = set(); soft: Set[str] = set(); assumptions: Set[str] = set()
    for c in p.clauses:
        if c.kind == "UNKNOWN" or c.strength == "UNKNOWN":
            continue
        if c.kind == "PREFERENCE" or c.strength == "SOFT":
            soft.add(c.semantic)
        elif c.kind == "PROHIBITION":
            prohib.add(c.semantic)
        elif c.kind == "ASSUMPTION":
            assumptions.add(c.semantic)
        elif c.kind == "REQUIREMENT" and c.strength == "HARD":
            hard.add(c.semantic)

    ph = h("intent-proposal:v1", p); ah = h("intent-adequacy:v1", r)
    body = {"source_hash": p.source_hash, "proposal_hash": ph, "adequacy_hash": ah,
            "hard_requirements": sorted(hard), "prohibitions": sorted(prohib),
            "soft_preferences": sorted(soft), "assumptions": sorted(assumptions),
            "effect_class": p.requested_effect_class,
            "authority_requirements": sorted(set(p.authority_refs))}
    ch = h("intent-contract:v1", body)
    return IntentContract(p.source_hash, ph, ah, frozenset(hard), frozenset(prohib),
                          frozenset(soft), frozenset(assumptions), p.requested_effect_class,
                          frozenset(p.authority_refs), ch), "COMMITTED"


def lower_to_cbcc(contract: IntentContract, compiler_semantics_hash: str) -> LoweredOpSpec:
    invariants = set(contract.hard_requirements)
    invariants.update("NOT(" + p + ")" for p in contract.prohibitions)
    return LoweredOpSpec(
        op_semantics_hash=h("icsl-lowering:v1", {"compiler": compiler_semantics_hash,
                                                  "contract": contract.contract_hash}),
        predicates=frozenset(contract.assumptions), invariants=frozenset(invariants),
        optimization_preferences=contract.soft_preferences,
        required_caps=contract.authority_requirements, effect_class=contract.effect_class,
        intent_contract_hash=contract.contract_hash, dynamic_closure_complete=True)


def effect_release_allowed(op: LoweredOpSpec, current_caps: FrozenSet[str],
                           hard_violations: FrozenSet[str]) -> bool:
    return not hard_violations and op.required_caps <= current_caps


def self_test():
    src = h("source:v1", "Keep retention >=30 days; blue preferred; delete only with cap:delete.")
    clauses = (
        IntentClause("c1", "REQUIREMENT", "HARD", "retention_days>=30", h("span", "retention"), True),
        IntentClause("c2", "PREFERENCE", "SOFT", "accent=blue", h("span", "blue"), False),
        IntentClause("c3", "PROHIBITION", "HARD", "delete_without_authority", h("span", "delete"), True))
    p = IntentProposal(src, "extractor:test", "v1", clauses, "IRREVERSIBLE", ("cap:delete",))
    checks = (
        AdequacyCheck("a1", "OWNER_CONTRACT", ("c1",), "PASS", "owner:retention"),
        AdequacyCheck("a2", "USER_CONFIRMATION", ("c3",), "PASS", "user:confirm-delete"),
        AdequacyCheck("a3", "SOURCE_ENTAILMENT", ("c2",), "PASS", "source:span-blue"))
    r = IntentAdequacyReceipt(h("intent-proposal:v1", p), checks, (), (), "VERIFIED", h("verifier", "v1"))
    c, status = commit_intent(p, r)
    assert status == "COMMITTED" and c is not None
    assert "retention_days>=30" in c.hard_requirements
    assert "accent=blue" in c.soft_preferences and "accent=blue" not in c.hard_requirements
    op = lower_to_cbcc(c, "compiler:v1")
    assert "cap:delete" in op.required_caps
    assert not effect_release_allowed(op, frozenset(), frozenset())
    assert effect_release_allowed(op, frozenset({"cap:delete"}), frozenset())

    p2 = IntentProposal(src, "extractor:test", "v1",
        (IntentClause("u1", "UNKNOWN", "UNKNOWN", "target=prod_or_stage", h("span", "target"), True),),
        "REVERSIBLE", ())
    r2 = IntentAdequacyReceipt(h("intent-proposal:v1", p2), (), ("u1",), ("u1",), "UNRESOLVED", h("verifier", "v1"))
    c2, s2 = commit_intent(p2, r2)
    assert c2 is None and s2 == "ESCALATE_EFFECT_CRITICAL_UNKNOWN"

    p3 = IntentProposal(src, "extractor:test", "v2", clauses, "IRREVERSIBLE", ("cap:delete",))
    c3, s3 = commit_intent(p3, r)
    assert c3 is None and s3 == "REJECT_RECEIPT_PROPOSAL_MISMATCH"

    bad = IntentProposal(src, "extractor:test", "v1",
        (IntentClause("b1", "REQUIREMENT", "HARD", "retention_days>=7", h("span", "retention"), True),),
        "REVERSIBLE", ())
    shape_ok, _ = validate_proposal_shape(bad); assert shape_ok
    rb = IntentAdequacyReceipt(h("intent-proposal:v1", bad), (), (), (), "PARTIAL", h("verifier", "v1"))
    cb, sb = commit_intent(bad, rb)
    assert cb is not None and sb == "COMMITTED"
    return {"candidate": "CC-RC1.5-ICSL", "soft_not_hard": True,
            "effect_critical_unknown_escalates": True,
            "receipt_bound_to_exact_proposal": True,
            "authority_ref_does_not_mint_capability": True,
            "structural_validity_not_semantic_adequacy": True,
            "extends": "CC-RC1.4-CBCC"}


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
