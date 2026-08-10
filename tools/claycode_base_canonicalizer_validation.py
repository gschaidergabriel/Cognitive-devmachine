#!/usr/bin/env python3
"""Executable validation for the production BASE surface canonicalizer.

The receipt now also couples the production frontend to the standalone syntax canonicalizer
through an executable cross-parity tripwire. This prevents two individually green validators
from hiding different parser-construction semantics.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from lark.exceptions import UnexpectedInput

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
# Never hardcode an older grammar here: this receipt validates the grammar actually selected
# by the production frontend. Candidate-specific strict/full-corpus gates remain separate.
GRAMMAR = front.DEFAULT_GRAMMAR
OUT = ROOT / "research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json"
PARITY_OUT = ROOT / "research_entity/claycode/autonomous/BASE_CROSS_CANON_PARITY_RECEIPT.json"


def run() -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    checks = []

    def result(name, ok, detail=None):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    # Layout/comments must not alter semantic identity.
    a = front.compile_frontend("module clay.demo\nlaw residual >= 0\n", grammar)
    b = front.compile_frontend("// ignored comment\nmodule   clay.demo\n\nlaw residual>=0\n", grammar)
    result("layout_comment_semantic_equivalence", a["semantic_hash"] == b["semantic_hash"], {"a": a["semantic_hash"], "b": b["semantic_hash"]})
    result("source_identity_remains_exact", a["source_sha256"] != b["source_sha256"])

    # V17 repair invariant: horizontal trivia before a call parenthesis cannot change a
    # qualified `owns` call into a dotted-prefix relation. The prefix relation remains a
    # semantically distinct program.
    owns_call_tight = front.compile_frontend("rule Needle.owns(X)\n", grammar)
    owns_call_spaced = front.compile_frontend("rule Needle.owns (X)\n", grammar)
    owns_call_long = front.compile_frontend("rule Needle.owns          (X)\n", grammar)
    owns_prefix = front.compile_frontend("rule Needle.owns X\n", grammar)
    result(
        "qualified_owns_call_horizontal_trivia_equivalence",
        owns_call_tight["semantic_hash"] == owns_call_spaced["semantic_hash"] == owns_call_long["semantic_hash"],
        {"tight": owns_call_tight["semantic_hash"], "spaced": owns_call_spaced["semantic_hash"], "long": owns_call_long["semantic_hash"]},
    )
    result("qualified_owns_call_distinct_from_prefix_relation", owns_call_tight["semantic_hash"] != owns_prefix["semantic_hash"])

    # Semantic operator/order mutations must remain distinguishable in this surface AST.
    gt = front.compile_frontend("module clay.demo\nlaw residual > 0\n", grammar)
    lt = front.compile_frontend("module clay.demo\nlaw residual < 0\n", grammar)
    result("operator_mutation_discriminated", a["semantic_hash"] != gt["semantic_hash"] and gt["semantic_hash"] != lt["semantic_hash"])
    ordered_a = front.compile_frontend("module clay.demo\nrule external_effect lifecycle=[REQUESTED,AUTHORIZED,EXECUTED]\n", grammar)
    ordered_b = front.compile_frontend("module clay.demo\nrule external_effect lifecycle=[AUTHORIZED,REQUESTED,EXECUTED]\n", grammar)
    result("ordered_sequence_mutation_discriminated", ordered_a["semantic_hash"] != ordered_b["semantic_hash"])

    # Generic String identity is exact after escape decoding: escape spelling can vary, scalar sequence cannot.
    literal = front.compile_frontend('module clay.demo\nrule label="é"\n', grammar)
    escaped = front.compile_frontend('module clay.demo\nrule label="\\u00e9"\n', grammar)
    decomposed = front.compile_frontend('module clay.demo\nrule label="e\\u0301"\n', grammar)
    result("string_escape_equivalence", literal["semantic_hash"] == escaped["semantic_hash"])
    result("string_exact_scalar_identity", literal["semantic_hash"] != decomposed["semantic_hash"])

    # Canonical serialization must be byte-stable.
    again = front.compile_frontend("module clay.demo\nlaw residual >= 0\n", grammar)
    result("repeat_determinism", a["semantic_hash"] == again["semantic_hash"] and a["contract_hash"] == again["contract_hash"])
    result("canonical_json_repeat_determinism", front.canonical_bytes(a["canonical_ast"]) == front.canonical_bytes(again["canonical_ast"]))

    # Invalid syntax / reserved-keyword misuse must reject.
    for name, source in {
        "reserved_if_identifier_rejected": "module clay.demo\nsurface if\n",
        "dangling_operator_rejected": "module clay.demo\nlaw residual >=\n",
        "reserved_lowers_call_with_trivia_rejected": "rule Needle.lowers (X)\n",
    }.items():
        try:
            front.compile_frontend(source, grammar)
            result(name, False, "unexpected_accept")
        except UnexpectedInput as exc:
            result(name, True, type(exc).__name__)

    # Lone surrogate is syntactically escaped JSON but is not a Unicode scalar value.
    try:
        front.compile_frontend('module clay.demo\nrule label="\\ud800"\n', grammar)
        result("lone_surrogate_rejected", False, "unexpected_accept")
    except front.CanonicalizationError as exc:
        result("lone_surrogate_rejected", True, str(exc))

    # Cross-path closure: execute the standalone canonicalizer through its real CLI, compare
    # its full-corpus canonical hashes against the same canonicalizer fed by the production
    # parser constructor, and require its bounded placeholder lesion/rescue tripwire to pass.
    if PARITY_OUT.exists():
        PARITY_OUT.unlink()
    cp = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/claycode_wp02_cross_canonicalizer_parity.py"),
            "--grammar",
            str(GRAMMAR),
            "--output",
            str(PARITY_OUT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    parity = json.loads(PARITY_OUT.read_text(encoding="utf-8")) if PARITY_OUT.exists() else {}
    result(
        "standalone_production_parser_contract_cross_parity",
        cp.returncode == 0 and parity.get("pass") is True and parity.get("parser_contract_bound") is True,
        {
            "returncode": cp.returncode,
            "receipt": str(PARITY_OUT.relative_to(ROOT)),
            "receipt_exists": PARITY_OUT.exists(),
            "parser_contract_bound": parity.get("parser_contract_bound"),
            "mutation_tripwire_pass": (parity.get("out_of_box_experiment") or {}).get("pass") if isinstance(parity.get("out_of_box_experiment"), dict) else None,
            "stdout_tail": cp.stdout[-1000:],
            "stderr_tail": cp.stderr[-1000:],
        },
    )

    failures = [x["name"] for x in checks if not x["pass"]]
    return {
        "schema_version": "1.3",
        "scope": "PRODUCTION_BASE_SURFACE_PARSER_CANONICALIZER_ACTIVE_GRAMMAR_WITH_CROSS_PATH_PARITY",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "checks": checks,
        "v9_trivia_counterexample_guard_present": True,
        "cross_canonicalizer_parser_contract_guard_present": True,
        "cross_canonicalizer_receipt": str(PARITY_OUT.relative_to(ROOT)),
        "passed": len(checks) - len(failures),
        "total": len(checks),
        "failures": failures,
        "pass": not failures,
        "limitations": [
            "typed collection Set/Ordered normalization belongs to CC-WP-03 typed IR",
            "strict LALR conflict freedom is proven by the separate strict frontend/target gate",
            "this receipt alone does not promote CC-WP-02 until full admitted G9+Dialect and strict grammar-bound receipts also pass",
            "the mutation tripwire is a bounded parser-contract falsifier, not evidence that all future parser-construction drift is impossible"
        ]
    }


def main() -> int:
    report = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"], "failures": report["failures"]}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
