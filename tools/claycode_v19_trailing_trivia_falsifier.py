#!/usr/bin/env python3
"""Bounded semantic-regression falsifier for both current ClayCode V19 delimiter candidates.

V17 deliberately leaves bare `Needle.owns` on the qid path when horizontal trivia is
followed by newline/comment/end-of-statement. Both concurrent V19 candidates use relation
terminals that consume any horizontal whitespace after `Needle.owns`; that can force a
missing RHS and reject a previously valid bare qid.

This probe compares exact current V17 and both V19 grammar bytes under the same Lark
runtime. It is negative evidence only: REFUTED applies to the exact tested delimiter-token
designs and does not select a replacement grammar or close CC-WP-02/03.
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

from lark import Lark

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
CANDIDATES = {
    "V19_DELIMITER_NORMALIZABLE": ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V19_DELIMITER_NORMALIZABLE.lark",
    "V19_DELIMITED_NO_LOOKAHEAD": ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V19_DELIMITED_NO_LOOKAHEAD.lark",
}


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parser(path: Path) -> Lark:
    return Lark(
        path.read_text(encoding="utf-8"),
        parser="lalr",
        lexer="contextual",
        strict=False,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
    )


def run_case(p: Lark, source: str) -> dict:
    try:
        tree = p.parse(source)
        return {"accepted": True, "tree": tree.pretty()}
    except Exception as exc:
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    p17 = parser(V17)
    candidate_parsers = {name: parser(path) for name, path in CANDIDATES.items()}

    regressions = {
        "bare_owns_spaces_before_newline": "rule Needle.owns   \n",
        "bare_owns_tab_before_newline": "rule Needle.owns\t\n",
        "bare_owns_spaces_before_comment": "rule Needle.owns   // trailing comment\n",
        "bare_owns_tab_before_comment": "rule Needle.owns\t// trailing comment\n",
    }
    controls = {
        "bare_owns_tight": "rule Needle.owns\n",
        "owns_relation": "rule Needle.owns X\n",
        "owns_call_tight": "rule Needle.owns(X)\n",
        "owns_call_spaced": "rule Needle.owns (X)\n",
        "longer_qid_owns_extra": "rule Needle.owns_extra\n",
        "longer_qid_ownsX": "rule Needle.ownsX\n",
        "longer_qid_lowers_more": "rule Needle.lowers_more\n",
    }

    rows = {}
    for name, source in {**regressions, **controls}.items():
        rows[name] = {"source": source, "v17": run_case(p17, source)}
        for candidate_name, p in candidate_parsers.items():
            rows[name][candidate_name] = run_case(p, source)

    candidate_results = {}
    for candidate_name in CANDIDATES:
        regression_names = [
            name for name in regressions
            if rows[name]["v17"]["accepted"] and not rows[name][candidate_name]["accepted"]
        ]
        controls_preserved = all(
            rows[name]["v17"]["accepted"] == rows[name][candidate_name]["accepted"]
            for name in controls
        )
        refuted = bool(regression_names) and controls_preserved
        candidate_results[candidate_name] = {
            "result": "REFUTED" if refuted else "UNRESOLVED",
            "regression_cases": regression_names,
            "controls_preserved": controls_preserved,
        }

    all_refuted = all(x["result"] == "REFUTED" for x in candidate_results.values())
    out = {
        "schema_version": "1.1",
        "experiment": "ClayCode V19 trailing-trivia semantic-regression falsifier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline": "V17_DECLARATIVE_TRIVIA_SAFE",
        "grammar_paths": {
            "v17": str(V17.relative_to(ROOT)),
            **{name: str(path.relative_to(ROOT)) for name, path in CANDIDATES.items()},
        },
        "grammar_sha256": {
            "v17": sha256(V17),
            **{name: sha256(path) for name, path in CANDIDATES.items()},
        },
        "runtime": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "strict": False,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "rows": rows,
        "candidate_results": candidate_results,
        "result": "REFUTED_BOTH" if all_refuted else "PARTIAL_OR_UNRESOLVED",
        "interpretation": (
            "Both current V19 delimiter candidates consume horizontal trivia after bare Needle.owns as a relation token, forcing a missing RHS and rejecting V17-valid bare-qid statements before newline/comment while preserving bounded positive controls."
            if all_refuted
            else "At least one tested V19 candidate did not reproduce the predicted bounded regression with preserved controls."
        ),
        "promotion": "NONE",
        "architecture_delta": (
            "NO_CHANGE_KEEP_V17_SELECTED; neither current V19 delimiter candidate should be promoted until its relation token excludes end-of-statement/comment trivia while retaining call/relation discrimination, then strict/full-corpus/canonical differential replay is required."
            if all_refuted
            else "NO_CHANGE_PENDING_MORE_EVIDENCE"
        ),
        "scope_guard": "REFUTED applies only to the exact current V19 delimiter-token semantics tested. It does not prove V17 globally optimal, close CC-WP-02/03, or authorize Frank Harness changes.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all_refuted else 1


if __name__ == "__main__":
    raise SystemExit(main())
