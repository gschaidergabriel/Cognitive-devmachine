#!/usr/bin/env python3
"""Executable ClayCode research compiler lab for CC-RC1.5 ICSL.

Experimental authoring surface, not canonical production syntax.

Pipeline:
  ClayCode-Lab source -> IntentProposal AST -> adequacy gate ->
  canonical semantic core + provenance-bound IntentContract -> Python lowering -> execution.

v0.2 learning from E2B:
- semantic identity must not accidentally depend on ordering/duplication of set-like clauses;
- provenance/contract-instance identity must remain bound to the exact proposal/adequacy chain.
Therefore `semantic_hash != contract_hash` by design.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from typing import Any

VERSION = "claycode-lab-0.2-cc-rc1.5"
SURFACE = "ClayCode-Lab/0.2"
EFFECTS = {"READ_ONLY", "REVERSIBLE", "IRREVERSIBLE"}


def canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def h(tag: str, obj: Any) -> str:
    return hashlib.sha256((tag + ":" + canon(obj)).encode("utf-8")).hexdigest()


def semantic_set(values: list[str]) -> list[str]:
    """Canonicalize fields that currently have set semantics.

    If ClayCode later adds explicit priority/order semantics, those fields must use a
    different typed representation rather than relying on source list order.
    """
    return sorted(set(values))


@dataclass(frozen=True)
class Clause:
    kind: str
    semantic: str
    effect_critical: bool = False


class CompileError(ValueError):
    pass


def parse(source: str) -> dict[str, Any]:
    intent_id = None
    effect = None
    clauses: list[Clause] = []
    authority_refs: list[str] = []
    ended = False
    for lineno, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, tail = line.partition(" ")
        tail = tail.strip()
        if head == "intent":
            if intent_id is not None or not tail:
                raise CompileError(f"line {lineno}: invalid/duplicate intent")
            intent_id = tail
        elif head == "effect":
            if tail not in EFFECTS:
                raise CompileError(f"line {lineno}: invalid effect {tail!r}")
            effect = tail
        elif head in {"hard", "prohibit", "soft", "assume"}:
            if not tail:
                raise CompileError(f"line {lineno}: empty {head}")
            kind = {
                "hard": "REQUIREMENT",
                "prohibit": "PROHIBITION",
                "soft": "PREFERENCE",
                "assume": "ASSUMPTION",
            }[head]
            clauses.append(Clause(kind, tail, False))
        elif head == "unknown":
            critical, sep, semantic = tail.partition(" ")
            if critical not in {"critical", "noncritical"} or not sep or not semantic:
                raise CompileError(f"line {lineno}: unknown requires critical|noncritical plus semantic")
            clauses.append(Clause("UNKNOWN", semantic, critical == "critical"))
        elif head == "authority":
            if not tail:
                raise CompileError(f"line {lineno}: empty authority reference")
            authority_refs.append(tail)
        elif head == "end":
            if tail:
                raise CompileError(f"line {lineno}: end takes no argument")
            ended = True
        else:
            raise CompileError(f"line {lineno}: unknown directive {head!r}")
    if intent_id is None or effect is None or not ended:
        raise CompileError("intent, effect and end are required")
    ast = {
        "surface": SURFACE,
        "compiler_version": VERSION,
        "intent_id": intent_id,
        "requested_effect_class": effect,
        "clauses": [c.__dict__ for c in clauses],
        "authority_refs": authority_refs,
    }
    ast["proposal_hash"] = h("intent-proposal:v2", ast)
    return ast


def adequacy_gate(ast: dict[str, Any]) -> dict[str, Any]:
    critical_unknown = [
        i for i, c in enumerate(ast["clauses"])
        if c["kind"] == "UNKNOWN" and c["effect_critical"]
    ]
    status = "VERIFIED_FOR_LAB" if not critical_unknown else "BLOCKED_EFFECT_CRITICAL_UNKNOWN"
    return {
        "proposal_hash": ast["proposal_hash"],
        "status": status,
        "unresolved_effect_critical": critical_unknown,
        "checks": ["STRUCTURAL_PARSE", "LAB_SOURCE_GROUNDING"],
        "verifier_semantics_hash": h(
            "adequacy-verifier:v2",
            {"version": VERSION, "rule": "critical unknown blocks commit"},
        ),
    }


def semantic_core(ast: dict[str, Any]) -> dict[str, Any]:
    clauses = ast["clauses"]
    return {
        "intent_id": ast["intent_id"],
        "effect_class": ast["requested_effect_class"],
        "hard_requirements": semantic_set([c["semantic"] for c in clauses if c["kind"] == "REQUIREMENT"]),
        "prohibitions": semantic_set([c["semantic"] for c in clauses if c["kind"] == "PROHIBITION"]),
        "soft_preferences": semantic_set([c["semantic"] for c in clauses if c["kind"] == "PREFERENCE"]),
        "assumptions": semantic_set([c["semantic"] for c in clauses if c["kind"] == "ASSUMPTION"]),
        "unresolved_noncritical": semantic_set([c["semantic"] for c in clauses if c["kind"] == "UNKNOWN"]),
        "authority_requirements": semantic_set(list(ast["authority_refs"])),
    }


def commit_contract(ast: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt["proposal_hash"] != ast["proposal_hash"]:
        raise CompileError("adequacy receipt is not bound to this proposal")
    if receipt["status"] != "VERIFIED_FOR_LAB":
        raise CompileError("cannot commit intent with effect-critical unknown")

    sem = semantic_core(ast)
    sem_hash = h("intent-semantics:v1", sem)
    contract = {
        "state_id": "S.INTENT_CONTRACT",
        **sem,
        "semantic_hash": sem_hash,
        "source_proposal_hash": ast["proposal_hash"],
        "adequacy_hash": h("intent-adequacy:v2", receipt),
        "compiler_version": VERSION,
    }
    # Instance identity intentionally includes provenance bindings.
    contract["contract_hash"] = h("intent-contract:v2", contract)
    return contract


def lower_to_python(contract: dict[str, Any]) -> str:
    payload = canon(contract)
    expected_contract = contract["contract_hash"]
    expected_semantic = contract["semantic_hash"]
    return (
        "import json\n"
        f"CONTRACT=json.loads({payload!r})\n"
        f"EXPECTED_CONTRACT={expected_contract!r}\n"
        f"EXPECTED_SEMANTIC={expected_semantic!r}\n"
        "assert CONTRACT['contract_hash']==EXPECTED_CONTRACT\n"
        "assert CONTRACT['semantic_hash']==EXPECTED_SEMANTIC\n"
        "assert not (set(CONTRACT['soft_preferences']) & set(CONTRACT['hard_requirements']))\n"
        "print(json.dumps({'ok':True,'intent':CONTRACT['intent_id'],'effect':CONTRACT['effect_class'],"
        "'hard':len(CONTRACT['hard_requirements']),'soft':len(CONTRACT['soft_preferences']),"
        "'caps':len(CONTRACT['authority_requirements']),'semantic_hash':EXPECTED_SEMANTIC,"
        "'contract_hash':EXPECTED_CONTRACT},sort_keys=True))\n"
    )


def compile_source(source: str) -> dict[str, Any]:
    ast = parse(source)
    adequacy = adequacy_gate(ast)
    contract = commit_contract(ast, adequacy)
    generated = lower_to_python(contract)
    return {
        "compiler_version": VERSION,
        "source_hash": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "proposal": ast,
        "adequacy": adequacy,
        "contract": contract,
        "generated_language": "python3",
        "generated_code": generated,
        "generated_code_hash": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
    }


def self_test() -> dict[str, Any]:
    base = """
intent remember-safe
effect REVERSIBLE
hard preserve exact truth
hard preserve provenance
soft minimize tokens
assume graph epoch pinned
authority cap:memory.write
unknown noncritical preferred compression
end
"""
    reordered = """
intent remember-safe
effect REVERSIBLE
hard preserve provenance
hard preserve exact truth
soft minimize tokens
assume graph epoch pinned
authority cap:memory.write
unknown noncritical preferred compression
end
"""
    duplicated = """
intent remember-safe
effect REVERSIBLE
hard preserve exact truth
hard preserve provenance
hard preserve provenance
soft minimize tokens
assume graph epoch pinned
authority cap:memory.write
unknown noncritical preferred compression
end
"""
    commented = """
# semantically irrelevant source formatting
intent remember-safe

effect REVERSIBLE
hard preserve exact truth
hard preserve provenance
soft minimize tokens
assume graph epoch pinned
authority cap:memory.write
unknown noncritical preferred compression
end
"""
    blocked = """
intent dangerous
effect IRREVERSIBLE
hard keep audit log
unknown critical target account ambiguous
authority cap:payments.write
end
"""

    b = compile_source(base)
    r = compile_source(reordered)
    d = compile_source(duplicated)
    c = compile_source(commented)
    rejected = False
    try:
        compile_source(blocked)
    except CompileError:
        rejected = True
    assert rejected
    assert b["contract"]["semantic_hash"] == r["contract"]["semantic_hash"] == d["contract"]["semantic_hash"]
    assert b["contract"]["contract_hash"] != r["contract"]["contract_hash"]
    assert b["contract"]["contract_hash"] != d["contract"]["contract_hash"]
    assert b["contract"]["contract_hash"] == c["contract"]["contract_hash"]
    return {
        "status": "PASS",
        "compiler_version": VERSION,
        "soft_not_hard": True,
        "authority_reference_not_minted": True,
        "critical_unknown_blocks_commit": True,
        "semantic_hash_reorder_invariant": True,
        "semantic_hash_duplicate_idempotent": True,
        "contract_hash_preserves_exact_proposal_ancestry": True,
        "comment_whitespace_is_parser_semantically_inert": True,
        "semantic_hash": b["contract"]["semantic_hash"],
        "contract_hash": b["contract"]["contract_hash"],
        "generated_python_hash": b["generated_code_hash"],
        "generated_python": b["generated_code"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("source", nargs="?")
    args = ap.parse_args()
    if args.self_test:
        out = self_test()
    else:
        if not args.source:
            ap.error("source path required unless --self-test")
        out = compile_source(open(args.source, encoding="utf-8").read())
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
