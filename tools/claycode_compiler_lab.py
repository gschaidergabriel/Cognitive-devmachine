#!/usr/bin/env python3
"""Executable ClayCode research compiler lab for CC-RC1.5 ICSL.

This is an experimental textual authoring surface, not canonical ClayCode syntax.
It exists to turn current ClayCode semantic hypotheses into executable parser,
type/adequacy checks and deterministic lowering experiments.

Pipeline:
  ClayCode-Lab source -> IntentProposal-like AST -> adequacy gate ->
  IntentContract-like canonical IR -> generated Python -> execution/test receipt
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from typing import Any

VERSION = "claycode-lab-0.1-cc-rc1.5"
EFFECTS = {"READ_ONLY", "REVERSIBLE", "IRREVERSIBLE"}


def canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def h(tag: str, obj: Any) -> str:
    return hashlib.sha256((tag + ":" + canon(obj)).encode("utf-8")).hexdigest()


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
            kind = {"hard":"REQUIREMENT","prohibit":"PROHIBITION","soft":"PREFERENCE","assume":"ASSUMPTION"}[head]
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
        "surface":"ClayCode-Lab/0.1",
        "compiler_version":VERSION,
        "intent_id":intent_id,
        "requested_effect_class":effect,
        "clauses":[c.__dict__ for c in clauses],
        "authority_refs":authority_refs,
    }
    ast["proposal_hash"] = h("intent-proposal:v1", ast)
    return ast


def adequacy_gate(ast: dict[str, Any]) -> dict[str, Any]:
    critical_unknown = [i for i,c in enumerate(ast["clauses"]) if c["kind"] == "UNKNOWN" and c["effect_critical"]]
    status = "VERIFIED_FOR_LAB" if not critical_unknown else "BLOCKED_EFFECT_CRITICAL_UNKNOWN"
    return {
        "proposal_hash":ast["proposal_hash"],
        "status":status,
        "unresolved_effect_critical":critical_unknown,
        "checks":["STRUCTURAL_PARSE","LAB_SOURCE_GROUNDING"],
        "verifier_semantics_hash":h("adequacy-verifier:v1", {"version":VERSION,"rule":"critical unknown blocks commit"}),
    }


def commit_contract(ast: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt["proposal_hash"] != ast["proposal_hash"]:
        raise CompileError("adequacy receipt is not bound to this proposal")
    if receipt["status"] != "VERIFIED_FOR_LAB":
        raise CompileError("cannot commit intent with effect-critical unknown")
    clauses = ast["clauses"]
    contract = {
        "state_id":"S.INTENT_CONTRACT",
        "intent_id":ast["intent_id"],
        "effect_class":ast["requested_effect_class"],
        "hard_requirements":[c["semantic"] for c in clauses if c["kind"] == "REQUIREMENT"],
        "prohibitions":[c["semantic"] for c in clauses if c["kind"] == "PROHIBITION"],
        "soft_preferences":[c["semantic"] for c in clauses if c["kind"] == "PREFERENCE"],
        "assumptions":[c["semantic"] for c in clauses if c["kind"] == "ASSUMPTION"],
        "unresolved_noncritical":[c["semantic"] for c in clauses if c["kind"] == "UNKNOWN"],
        "authority_requirements":list(ast["authority_refs"]),
        "source_proposal_hash":ast["proposal_hash"],
        "adequacy_hash":h("intent-adequacy:v1", receipt),
        "compiler_version":VERSION,
    }
    contract["contract_hash"] = h("intent-contract:v1", contract)
    return contract


def lower_to_python(contract: dict[str, Any]) -> str:
    payload = canon(contract)
    expected = contract["contract_hash"]
    return (
        "import json,hashlib\n"
        f"CONTRACT=json.loads({payload!r})\n"
        f"EXPECTED={expected!r}\n"
        "assert CONTRACT['contract_hash']==EXPECTED\n"
        "assert not (set(CONTRACT['soft_preferences']) & set(CONTRACT['hard_requirements']))\n"
        "print(json.dumps({'ok':True,'intent':CONTRACT['intent_id'],'effect':CONTRACT['effect_class'],"
        "'hard':len(CONTRACT['hard_requirements']),'soft':len(CONTRACT['soft_preferences']),"
        "'caps':len(CONTRACT['authority_requirements']),'contract_hash':EXPECTED},sort_keys=True))\n"
    )


def compile_source(source: str) -> dict[str, Any]:
    ast = parse(source)
    adequacy = adequacy_gate(ast)
    contract = commit_contract(ast, adequacy)
    generated = lower_to_python(contract)
    return {
        "compiler_version":VERSION,
        "source_hash":hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "proposal":ast,
        "adequacy":adequacy,
        "contract":contract,
        "generated_language":"python3",
        "generated_code":generated,
        "generated_code_hash":hashlib.sha256(generated.encode("utf-8")).hexdigest(),
    }


def self_test() -> dict[str, Any]:
    good = """\nintent remember-safe\neffect REVERSIBLE\nhard preserve exact truth\nsoft minimize tokens\nassume graph epoch pinned\nauthority cap:memory.write\nunknown noncritical preferred compression\nend\n"""
    compiled = compile_source(good)
    c = compiled["contract"]
    assert c["hard_requirements"] == ["preserve exact truth"]
    assert c["soft_preferences"] == ["minimize tokens"]
    assert c["authority_requirements"] == ["cap:memory.write"]
    assert c["authority_requirements"][0] not in c["hard_requirements"]
    assert compile_source(good)["contract"]["contract_hash"] == c["contract_hash"]
    blocked = """\nintent dangerous\neffect IRREVERSIBLE\nhard keep audit log\nunknown critical target account ambiguous\nauthority cap:payments.write\nend\n"""
    rejected = False
    try:
        compile_source(blocked)
    except CompileError:
        rejected = True
    assert rejected
    return {
        "status":"PASS",
        "compiler_version":VERSION,
        "soft_not_hard":True,
        "authority_reference_not_minted":True,
        "critical_unknown_blocks_commit":True,
        "deterministic_contract_hash":True,
        "generated_python_hash":compiled["generated_code_hash"],
        "generated_python":compiled["generated_code"],
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
