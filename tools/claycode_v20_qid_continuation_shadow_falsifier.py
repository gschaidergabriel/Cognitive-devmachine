#!/usr/bin/env python3
"""Bounded counterexample test for V20's word-boundary Needle.owns terminal.

V20 uses /Needle\.owns\b/ to avoid stealing alphanumeric/underscore suffixes.  In the
selected V17 surface, however, `owns` is an ordinary NAME segment and qids may continue
through `.`; NAME itself may also contain `-`, and a qid may take postfix `?`.
A Python-regex word boundary exists before all three of those non-word characters.
Therefore V20 can steal a prefix that V17 still treats as one qid/postfix-qid.

Negative evidence only.  A confirmed counterexample refutes this exact V20 token design;
it does not promote another grammar or close CC-WP-02/03.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V20 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V20_WORD_BOUNDARY_RULE_PRIORITY.lark"
DOMAIN = b"ClayCodeBaseFrontendAST/v1\x00"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parser(path: Path) -> Lark:
    return Lark(path.read_text(encoding="utf-8"), parser="lalr", lexer="contextual",
                strict=True, start="start", keep_all_tokens=True, maybe_placeholders=False)


def canonical(node: Any) -> Any:
    if isinstance(node, Tree):
        children = []
        for child in node.children:
            value = canonical(child)
            if value is not None:
                children.append(value)
        return {"kind": str(node.data), "children": children}
    if isinstance(node, Token):
        if node.type in {"NEWLINE", "SEMICOLON"} or str(node) == ";":
            return None
        return {"token": node.type, "value": str(node)}
    raise TypeError(type(node))


def semantic_hash(tree: Tree) -> str:
    payload = json.dumps(canonical(tree), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha(DOMAIN + payload)


def run(p: Lark, source: str) -> dict[str, Any]:
    try:
        tree = p.parse(source)
        return {"accepted": True, "tree": tree.pretty(), "semantic_hash": semantic_hash(tree)}
    except Exception as exc:
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    p17, p20 = parser(V17), parser(V20)

    # All three are admitted by selected V17.  V20 must preserve acceptance AND meaning.
    regressions = {
        "dotted_qid_continuation": "rule Needle.owns.more\n",
        "hyphenated_name_continuation": "rule Needle.owns-more\n",
        "postfix_optional_qid": "rule Needle.owns?\n",
    }
    controls = {
        "bare_owns": "rule Needle.owns\n",
        "owns_relation": "rule Needle.owns X\n",
        "owns_call": "rule Needle.owns(X)\n",
        "underscore_suffix": "rule Needle.owns_extra\n",
        "alpha_suffix": "rule Needle.ownsX\n",
        "digit_suffix": "rule Needle.owns2\n",
    }

    rows: dict[str, Any] = {}
    regressions_found = []
    for name, source in {**regressions, **controls}.items():
        a, b = run(p17, source), run(p20, source)
        equal = bool(a.get("accepted") and b.get("accepted") and a.get("semantic_hash") == b.get("semantic_hash"))
        rows[name] = {"source": source, "v17": a, "v20": b, "raw_tree_hash_equal": equal}
        if name in regressions and a.get("accepted") and not equal:
            regressions_found.append(name)

    # Controls only require acceptance parity here; exact V20 normalization is covered by the
    # main discriminator.  This falsifier is intentionally narrow around qid continuation.
    controls_preserved = all(rows[name]["v17"]["accepted"] == rows[name]["v20"]["accepted"] for name in controls)
    refuted = bool(regressions_found) and controls_preserved

    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode V20 qid-continuation word-boundary shadow falsifier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_NEGATIVE_RESEARCH_DISCRIMINATOR",
        "runtime": {
            "platform": platform.platform(), "machine": platform.machine(),
            "python": platform.python_version(), "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "lark": pkg("lark"), "interegular": pkg("interegular"),
            "strict": True, "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"), "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "inputs": {
            "v17_path": str(V17.relative_to(ROOT)), "v17_sha256": sha(V17.read_bytes()),
            "v20_path": str(V20.relative_to(ROOT)), "v20_sha256": sha(V20.read_bytes()),
        },
        "rows": rows,
        "regressions_found": regressions_found,
        "controls_preserved": controls_preserved,
        "result": "REFUTED" if refuted else "UNRESOLVED",
        "interpretation": (
            "V20's \\b boundary is not an identifier-boundary contract for the V17 qid language: '.', '-' and '?' are non-word characters, so the high-priority Needle.owns token can steal prefixes that V17 keeps inside qid/postfix-qid semantics."
            if refuted else "The predicted bounded qid-continuation regression was not established with preserved controls."
        ),
        "architecture_delta": "NO_CHANGE_KEEP_V17_SELECTED" if refuted else "NO_CHANGE_PENDING_MORE_EVIDENCE",
        "promotion": "NONE",
        "scope_guard": "REFUTED applies only to the exact current V20 word-boundary token design. It does not prove V17 globally optimal, close WP02/WP03, or authorize Frank Harness changes.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if refuted else 1


if __name__ == "__main__":
    raise SystemExit(main())
