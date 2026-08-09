#!/usr/bin/env python3
"""Bounded out-of-the-box WP02 experiment: metamorphic horizontal-trivia topology.

Research-only discriminator. It never edits/promotes the grammar. For the contract-selected
V17 grammar it checks that horizontal space/tab perturbations before a call parenthesis are
semantic trivia, while the dotted-prefix relation remains a distinct parse. The relation
form is the lesion/counterfactual. NO_BENEFIT/REFUTED is an accepted outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(node):
    if isinstance(node, Tree):
        return [str(node.data), [canon(x) for x in node.children]]
    return [getattr(node, "type", type(node).__name__), str(node)]


def tree_hash(parser: Lark, source: str) -> str:
    payload = json.dumps(canon(parser.parse(source)), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--seed", type=int, default=170217)
    ap.add_argument("--cases", type=int, default=512)
    args = ap.parse_args()

    grammar = args.grammar.read_text(encoding="utf-8")
    parser = Lark(grammar, parser="lalr", lexer="contextual", strict=True, start="start", keep_all_tokens=True)
    rng = random.Random(args.seed)

    baseline_call = "rule Needle.owns(X)\n"
    baseline_relation = "rule Needle.owns X\n"
    call_hash = tree_hash(parser, baseline_call)
    relation_hash = tree_hash(parser, baseline_relation)

    failures = []
    observed = []
    for i in range(args.cases):
        # WS_INLINE in Lark is horizontal ASCII space/tab; perturb only that admitted trivia class.
        trivia = "".join(rng.choice([" ", "\t"]) for _ in range(rng.randint(1, 24)))
        call_src = f"rule Needle.owns{trivia}(X)\n"
        rel_src = f"rule Needle.owns{trivia}X\n"
        ch = tree_hash(parser, call_src)
        rh = tree_hash(parser, rel_src)
        ok = ch == call_hash and rh == relation_hash and ch != rh
        if i < 8:
            observed.append({"i": i, "trivia_repr": repr(trivia), "call_hash": ch, "relation_hash": rh, "pass": ok})
        if not ok:
            failures.append({"i": i, "trivia_repr": repr(trivia), "call_hash": ch, "relation_hash": rh})
            if len(failures) >= 16:
                break

    passed = not failures and call_hash != relation_hash
    out = {
        "schema_version": "1.0",
        "experiment_id": "GO-OOB-WP02-TRIVIA-METAMORPHIC-V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "class": "BOUNDED_OUT_OF_THE_BOX_EXPERIMENT",
        "hypothesis": "For selected V17, admitted horizontal trivia before '(' does not change call semantics, while the dotted-prefix relation remains distinct.",
        "counterhypothesis": "The V17 lookahead still leaks horizontal trivia into call-vs-relation parse identity for at least one bounded perturbation.",
        "grammar_path": str(args.grammar.relative_to(ROOT)),
        "grammar_sha256": sha256_bytes(grammar.encode("utf-8")),
        "seed": args.seed,
        "requested_cases": args.cases,
        "executed_cases": args.cases if not failures else failures[-1]["i"] + 1,
        "baseline_call_hash": call_hash,
        "lesion_relation_hash": relation_hash,
        "baseline_vs_lesion_distinct": call_hash != relation_hash,
        "sample": observed,
        "failures": failures,
        "pass": passed,
        "promotion": "NONE",
        "rollback": "Remove this research-only probe/workflow step; selected grammar bytes are untouched.",
        "scope_guard": "This is metamorphic parser evidence only. It cannot promote WP02, BASE, Frank Harness, or target-host acceptance."
    }
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
