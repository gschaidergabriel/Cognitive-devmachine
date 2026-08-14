#!/usr/bin/env python3
"""Out-of-box bounded discriminator: semantic identity vs diagnostic source provenance.

V19 can normalize its delimiter-consuming tokens back to the selected V17 canonical AST.
That is necessary but not sufficient for a compiler frontend: precise diagnostics and later
IR provenance also need recoverable source spans. The current canonical AST intentionally
hashes only semantics and carries no positions.

This probe tests a dual-rail design without changing ClayCode semantics:
  semantic rail: V17/V19 normalized canonical AST + existing semantic hash;
  provenance rail: separate source-span sidecar derived from the exact source and parser
                   token positions.

PASS means the selected fixtures preserve semantic hashes while exact source anchors remain
recoverable and the sidecar can vary independently with trivia. It does NOT promote V19,
close WP02/WP03/WP04, or change Frank's Harness.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

import claycode_v19_delimiter_normalization_probe as norm

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V19 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V19_DELIMITER_NORMALIZABLE.lark"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parser(grammar: str) -> Lark:
    return Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=True,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
        propagate_positions=True,
    )


def tokens(tree: Tree) -> list[Token]:
    return list(tree.scan_values(lambda x: isinstance(x, Token)))


def tok_row(t: Token) -> dict[str, Any]:
    return {
        "type": t.type,
        "value": str(t),
        "start": getattr(t, "start_pos", None),
        "end": getattr(t, "end_pos", None),
        "line": getattr(t, "line", None),
        "column": getattr(t, "column", None),
        "end_line": getattr(t, "end_line", None),
        "end_column": getattr(t, "end_column", None),
    }


def canonical_has_span_metadata(node: Any) -> bool:
    if isinstance(node, dict):
        if any(k in node for k in ("start", "end", "line", "column", "start_pos", "end_pos", "source_span")):
            return True
        return any(canonical_has_span_metadata(v) for v in node.values())
    if isinstance(node, list):
        return any(canonical_has_span_metadata(v) for v in node)
    return False


def expected_anchors(source: str) -> list[dict[str, Any]]:
    op = "Needle.owns" if "Needle.owns" in source else "Needle.lowers"
    op_start = source.index(op)
    rows = [{"name": "operator", "start": op_start, "end": op_start + len(op), "text": op}]
    if "(" in source:
        p = source.index("(", op_start)
        rows.append({"name": "open_paren", "start": p, "end": p + 1, "text": "("})
    # Selected fixtures use X as the first semantic RHS/argument when present.
    x = source.find("X", op_start + len(op))
    if x >= 0:
        rows.append({"name": "rhs_X", "start": x, "end": x + 1, "text": "X"})
    return rows


def recoverable(anchor: dict[str, Any], ts: list[Token]) -> dict[str, Any]:
    a, b = anchor["start"], anchor["end"]
    covering = []
    for t in ts:
        s = getattr(t, "start_pos", None)
        e = getattr(t, "end_pos", None)
        if s is None or e is None:
            continue
        if s < b and e > a:
            covering.append(tok_row(t))
    if not covering:
        return {**anchor, "recoverable": False, "covering": []}
    left = min(r["start"] for r in covering)
    right = max(r["end"] for r in covering)
    return {**anchor, "recoverable": left <= a and right >= b, "covering": covering}


def source_map(source: str, tree: Tree) -> dict[str, Any]:
    ts = tokens(tree)
    anchors = [recoverable(a, ts) for a in expected_anchors(source)]
    semantic_positions = [{k: a[k] for k in ("name", "start", "end", "text")} for a in anchors]
    payload = json.dumps(semantic_positions, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "anchors": anchors,
        "all_recoverable": all(a["recoverable"] for a in anchors),
        "sidecar_sha256": sha(payload),
    }


def token_partition(tree: Tree) -> list[tuple[str, str, int | None, int | None]]:
    return [(t.type, str(t), getattr(t, "start_pos", None), getattr(t, "end_pos", None)) for t in tokens(tree) if t.type != "NEWLINE"]


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g19 = V19.read_text(encoding="utf-8")
    p17 = parser(g17)
    p19 = parser(g19)

    groups = {
        "owns_call": [
            "rule Needle.owns(X)\n",
            "rule Needle.owns (X)\n",
            "rule Needle.owns\t(X)\n",
            "rule Needle.owns \t (X)\n",
        ],
        "owns_relation": [
            "rule Needle.owns X\n",
            "rule Needle.owns  X\n",
            "rule Needle.owns\tX\n",
            "rule Needle.owns \t X\n",
        ],
        "lowers_relation": [
            "rule Needle.lowers X\n",
            "rule Needle.lowers  X\n",
            "rule Needle.lowers\tX\n",
            "rule Needle.lowers \t X\n",
        ],
    }

    rows = []
    raw_partition_difference_seen = False
    canonical_span_metadata_seen = False
    for group, variants in groups.items():
        for source in variants:
            t17 = p17.parse(source)
            t19 = p19.parse(source)
            a17 = norm.canonical(t17, v19=False)
            a19 = norm.canonical(t19, v19=True)
            h17 = norm.semantic_hash(a17)
            h19 = norm.semantic_hash(a19)
            m17 = source_map(source, t17)
            m19 = source_map(source, t19)
            part17 = token_partition(t17)
            part19 = token_partition(t19)
            raw_partition_difference_seen = raw_partition_difference_seen or (part17 != part19)
            canonical_span_metadata_seen = canonical_span_metadata_seen or canonical_has_span_metadata(a17) or canonical_has_span_metadata(a19)
            rows.append({
                "group": group,
                "source": source,
                "source_sha256": sha(source.encode("utf-8")),
                "v17_semantic_hash": h17,
                "v19_semantic_hash": h19,
                "semantic_hash_equal": h17 == h19,
                "normalized_ast_equal": a17 == a19,
                "v17_source_map": m17,
                "v19_source_map": m19,
                "source_map_equal": m17["sidecar_sha256"] == m19["sidecar_sha256"],
                "raw_token_partition_equal": part17 == part19,
                "v17_tokens": [tok_row(t) for t in tokens(t17)],
                "v19_tokens": [tok_row(t) for t in tokens(t19)],
                "canonical_contains_span_metadata": canonical_has_span_metadata(a17) or canonical_has_span_metadata(a19),
            })

    group_summary = []
    for group in groups:
        rs = [r for r in rows if r["group"] == group]
        semantic_hashes = {r["v19_semantic_hash"] for r in rs}
        sidecar_hashes = {r["v19_source_map"]["sidecar_sha256"] for r in rs}
        group_summary.append({
            "group": group,
            "semantic_hash_stable_across_trivia": len(semantic_hashes) == 1,
            "source_sidecar_changes_with_trivia": len(sidecar_hashes) > 1,
            "all_anchors_recoverable_v17": all(r["v17_source_map"]["all_recoverable"] for r in rs),
            "all_anchors_recoverable_v19": all(r["v19_source_map"]["all_recoverable"] for r in rs),
            "all_v17_v19_semantics_equal": all(r["semantic_hash_equal"] and r["normalized_ast_equal"] for r in rs),
            "all_v17_v19_source_maps_equal": all(r["source_map_equal"] for r in rs),
        })

    passed = (
        all(g["semantic_hash_stable_across_trivia"] for g in group_summary)
        and all(g["source_sidecar_changes_with_trivia"] for g in group_summary)
        and all(g["all_anchors_recoverable_v17"] and g["all_anchors_recoverable_v19"] for g in group_summary)
        and all(g["all_v17_v19_semantics_equal"] for g in group_summary)
        and all(g["all_v17_v19_source_maps_equal"] for g in group_summary)
        and raw_partition_difference_seen
        and not canonical_span_metadata_seen
    )

    out = {
        "schema_version": "1.0",
        "experiment": "V19_SEMANTIC_HASH_VS_SOURCE_SPAN_DUAL_RAIL",
        "evidence_class": "BOUNDED_OUT_OF_BOX_EXECUTABLE_DISCRIMINATOR",
        "runtime": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "lark": norm.pkg("lark"),
            "interegular": norm.pkg("interegular"),
        },
        "inputs": {
            "v17_sha256": sha(g17.encode("utf-8")),
            "v19_sha256": sha(g19.encode("utf-8")),
        },
        "hypothesis": "V19 can preserve V17 semantic identity while a separate non-semantic span sidecar preserves precise diagnostic provenance despite different token partitions.",
        "counterhypothesis": "Delimiter-consuming V19 destroys exact source anchoring or forces source positions into the semantic hash, coupling formatting to semantic identity.",
        "rows": rows,
        "groups": group_summary,
        "raw_partition_difference_seen": raw_partition_difference_seen,
        "current_canonical_contains_span_metadata": canonical_span_metadata_seen,
        "pass": passed,
        "adjudication": "SUPPORTED_DUAL_RAIL_SOURCE_MAP_SIDECAR" if passed else "REFUTED_OR_INCOMPLETE",
        "architecture_delta": "If confirmed on Ubuntu/full corpus, preserve the existing semantic hash contract and add a separately hashed/replayable source-span sidecar for parser->typed-IR diagnostics/provenance. Do not put trivia-dependent spans into semantic identity.",
        "rollback": "Delete this research probe; no production parser, canonical hash, typed IR, Frank Harness, or authority semantics are changed.",
        "scope_guard": "PASS is bounded evidence for three Needle delimiter families only. It does not prove full-corpus source mapping, Unicode byte/character offset policy, diagnostic UX, WP02/WP03/WP04 acceptance, or target-host release evidence.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
