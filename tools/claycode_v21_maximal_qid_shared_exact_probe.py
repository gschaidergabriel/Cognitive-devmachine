#!/usr/bin/env python3
"""Strict V17-equivalence discriminator for ClayCode V21 maximal-qid/shared-exact grammar.

V21 is research-only. It removes the dedicated Needle relation lookahead by sharing the
exact Needle.owns token between qid/relation syntax while giving every V17-valid longer
Needle.owns/lowers qid a maximal whole-qid token. Any parity counterexample refutes the
candidate; PASS never promotes WP02/WP03 or mutates Frank.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V21 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V21_MAXIMAL_QID_SHARED_EXACT.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
DOMAIN = b"ClayCodeBaseFrontendAST/v1\x00"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parser(grammar: str) -> Lark:
    return Lark(grammar, parser="lalr", lexer="contextual", strict=True,
                start="start", keep_all_tokens=True, maybe_placeholders=False)


def tok(kind: str, value: str) -> dict[str, str]:
    return {"token": kind, "value": value}


def qid_from_text(text: str) -> dict[str, Any]:
    parts = text.split(".")
    children: list[Any] = []
    for i, part in enumerate(parts):
        if i:
            children.append(tok("DOT", "."))
        children.append(tok("NAME", part))
    return {"kind": "qid", "children": children}


def canonical(node: Any, *, v21: bool) -> Any:
    if isinstance(node, Tree):
        kind = str(node.data)
        if v21 and kind in {"qid_needle_owns_exact", "qid_needle_owns_long", "qid_needle_lowers_long"}:
            values = [str(x) for x in node.children if isinstance(x, Token)]
            if len(values) != 1:
                raise AssertionError(f"malformed specialized qid {kind}: {values!r}")
            return qid_from_text(values[0])
        children = []
        for child in node.children:
            value = canonical(child, v21=v21)
            if value is not None:
                children.append(value)
        return {"kind": kind, "children": children}
    if isinstance(node, Token):
        if node.type in {"NEWLINE", "SEMICOLON"} or str(node) == ";":
            return None
        if v21 and node.type in {"NEEDLE_OWNS_EXACT", "NEEDLE_LOWERS_EXACT"}:
            return tok("DOTTED_PREFIX_REL", str(node))
        if v21 and node.type in {"NEEDLE_OWNS_LONG_QID", "NEEDLE_LOWERS_LONG_QID"}:
            raise AssertionError(f"specialized qid token escaped parent normalization: {node.type}")
        return tok(node.type, str(node))
    raise TypeError(type(node))


def semantic_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha(DOMAIN + payload)


def parse(p: Lark, source: str, *, v21: bool) -> dict[str, Any]:
    try:
        tree = p.parse(source)
        value = canonical(tree, v21=v21)
        return {"accepted": True, "semantic_hash": semantic_hash(value), "canonical": value}
    except Exception as exc:
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    g17, g21 = V17.read_text(encoding="utf-8"), V21.read_text(encoding="utf-8")
    strict_rows, parsers = [], {}
    for name, grammar in (("v17", g17), ("v21", g21)):
        t0 = time.perf_counter_ns()
        try:
            parsers[name] = parser(grammar)
            strict_rows.append({"grammar": name, "pass": True, "error": None,
                                "elapsed_ms": (time.perf_counter_ns() - t0) / 1_000_000})
        except Exception as exc:
            strict_rows.append({"grammar": name, "pass": False,
                                "error": f"{type(exc).__name__}: {exc}",
                                "elapsed_ms": (time.perf_counter_ns() - t0) / 1_000_000})
    strict_pass = all(x["pass"] for x in strict_rows)

    source_rows, fixture_rows = [], []
    if strict_pass:
        p17, p21 = parsers["v17"], parsers["v21"]
        for path in SOURCES:
            text = path.read_text(encoding="utf-8")
            a, b = parse(p17, text, v21=False), parse(p21, text, v21=True)
            source_rows.append({
                "path": str(path.relative_to(ROOT)), "source_sha256": sha(text.encode("utf-8")),
                "v17_accept": a["accepted"], "v21_accept": b["accepted"],
                "v17_semantic_hash": a.get("semantic_hash"), "v21_semantic_hash": b.get("semantic_hash"),
                "pass": a["accepted"] and b["accepted"] and a.get("semantic_hash") == b.get("semantic_hash"),
                "v17_error": a.get("error"), "v21_error": b.get("error"),
            })

        fixtures = [
            "rule Needle.owns\n",
            "rule Needle.owns   \n",
            "rule Needle.owns   // trailing comment\n",
            "rule Needle.owns X\n",
            "rule Needle.owns [tool_schema,api_wire]\n",
            "rule Needle.owns(X)\n",
            "rule Needle.owns (X)\n",
            "rule Needle.owns\t(X)\n",
            "rule Needle.owns?\n",
            "rule Needle.ownership\n",
            "rule Needle.owns_extra\n",
            "rule Needle.ownsX\n",
            "rule Needle.owns2\n",
            "rule Needle.owns-more\n",
            "rule Needle.owns.more\n",
            "rule Needle.owns.more.deep\n",
            "rule Needle.owns-more.more\n",
            "rule Needle.owns.more(X)\n",
            "rule Needle.owns-more(X)\n",
            "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
            "rule Needle.lowers\tEffectIntent -> concrete_adapter_plan\n",
            "rule Needle.lowers_more\n",
            "rule Needle.lowersX\n",
            "rule Needle.lowers2\n",
            "rule Needle.lowers_more.deep\n",
            "rule Needle.lowers_more(X)\n",
            "rule Needle.lowers\n",
            "rule Needle.lowers   \n",
            "rule Needle.lowers   // trailing comment\n",
            "rule Needle.lowers(X)\n",
            "rule Needle.lowers (X)\n",
            "rule Needle.lowers?\n",
            "rule Needle.lowers.more\n",
            "rule Needle.lowers-more\n",
            "rule Needle.owns.more X\n",
            "rule Needle.owns? X\n",
        ]
        for source in fixtures:
            a, b = parse(p17, source, v21=False), parse(p21, source, v21=True)
            same = a["accepted"] == b["accepted"] and (not a["accepted"] or a.get("semantic_hash") == b.get("semantic_hash"))
            fixture_rows.append({
                "source": source, "v17_accept": a["accepted"], "v21_accept": b["accepted"],
                "v17_semantic_hash": a.get("semantic_hash"), "v21_semantic_hash": b.get("semantic_hash"),
                "v17_error": a.get("error"), "v21_error": b.get("error"), "pass": same,
            })

    relation_lines = [line for line in g21.splitlines() if line.lstrip().startswith(("NEEDLE_OWNS_EXACT", "NEEDLE_LOWERS_EXACT"))]
    relation_lookaround_present = any(marker in line for line in relation_lines for marker in ("(?=", "(?<=", "(?!", "(?<!"))
    source_pass = bool(source_rows) and all(x["pass"] for x in source_rows)
    fixture_pass = bool(fixture_rows) and all(x["pass"] for x in fixture_rows)
    passed = strict_pass and source_pass and fixture_pass and not relation_lookaround_present
    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode V21 maximal-qid shared-exact strict V17-equivalence discriminator",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_RESEARCH_DIFFERENTIAL",
        "runtime": {"platform": platform.platform(), "machine": platform.machine(),
                    "python": platform.python_version(), "cpu_count": os.cpu_count(),
                    "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    "lark": pkg("lark"), "interegular": pkg("interegular"),
                    "github_sha": os.environ.get("GITHUB_SHA"),
                    "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                    "runner_name": os.environ.get("RUNNER_NAME")},
        "inputs": {"v17_path": str(V17.relative_to(ROOT)), "v17_sha256": sha(g17.encode("utf-8")),
                   "v21_path": str(V21.relative_to(ROOT)), "v21_sha256": sha(g21.encode("utf-8"))},
        "strict_construction": strict_rows,
        "frozen_sources": source_rows,
        "focused_equivalence": fixture_rows,
        "relation_lookaround_present": relation_lookaround_present,
        "strict_pass": strict_pass, "source_semantic_pass": source_pass, "fixture_pass": fixture_pass,
        "pass": passed,
        "adjudication": "SUPPORTED_RESEARCH_CANDIDATE" if passed else "REFUTED_OR_INCOMPLETE",
        "promotion": "NONE",
        "architecture_delta": "TESTING_ONLY; keep V17 selected until source-span, property/fuzz and WP03 replay pass" if passed else "NO_CHANGE_KEEP_V17_SELECTED",
        "scope_guard": "PASS is bounded parser/canonical semantic evidence only. It does not close WP02/WP03, change frozen language semantics, authorize Frank Harness mutation, or substitute for registered Andreas Ubuntu acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
