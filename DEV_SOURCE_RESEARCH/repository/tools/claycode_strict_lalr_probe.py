#!/usr/bin/env python3
"""Deterministically expose strict-LALR conflicts in the active ClayCode D candidate.

This is a diagnostic probe, not a parser selection or semantic promotion. It separates
actual grammar conflicts from missing strict-mode dependencies, because Lark strict mode
requires interegular for regex-collision checks. It also flags regex lookaround, whose
collisions may not be fully detectable by interegular and therefore require metamorphic
lexical boundary tests in addition to a strict construction pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark
from lark import logger as lark_logger
from lark.exceptions import GrammarError, LexError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    text = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", text)
    return re.sub(r"\s+", " ", text).strip()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def probe(path: Path) -> dict:
    grammar = path.read_text(encoding="utf-8")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    old_level = lark_logger.level
    lark_logger.setLevel(logging.DEBUG)
    lark_logger.addHandler(handler)

    nonstrict_ok = False
    nonstrict_error = None
    try:
        Lark(grammar, parser="lalr", lexer="contextual", strict=False, debug=True)
        nonstrict_ok = True
    except Exception as exc:
        nonstrict_error = normalize(f"{type(exc).__name__}: {exc}")
    finally:
        lark_logger.removeHandler(handler)
        lark_logger.setLevel(old_level)

    diagnostics = [normalize(x) for x in stream.getvalue().splitlines() if x.strip()]
    conflict_lines = [x for x in diagnostics if "conflict" in x.lower() or "collision" in x.lower()]

    strict_ok = False
    strict_error = None
    strict_evidence_state = "UNKNOWN"
    try:
        Lark(grammar, parser="lalr", lexer="contextual", strict=True, debug=True)
        strict_ok = True
        strict_evidence_state = "PASS_STRICT_CONSTRUCTION"
    except LexError as exc:
        strict_error = normalize(f"LexError: {exc}")
        if "interegular" in str(exc).lower():
            strict_evidence_state = "BLOCKED_MISSING_INTEREGULAR"
        else:
            strict_evidence_state = "FAIL_LEXER"
    except GrammarError as exc:
        strict_error = normalize(str(exc))
        strict_evidence_state = "FAIL_GRAMMAR_CONFLICT"
    except Exception as exc:
        strict_error = normalize(f"{type(exc).__name__}: {exc}")
        strict_evidence_state = "FAIL_OTHER"

    regex_lookaround_present = "(?=" in grammar or "(?<=" in grammar or "(?!" in grammar or "(?<!" in grammar
    if strict_evidence_state == "BLOCKED_MISSING_INTEREGULAR":
        interpretation = (
            "Strict evidence is blocked by a missing runtime dependency; do not repair the grammar from this result. "
            "Install/pin interegular (for example via lark[interegular]) on the target test lane and re-run."
        )
    elif strict_evidence_state == "FAIL_GRAMMAR_CONFLICT":
        interpretation = (
            "Strict construction found a grammar conflict. Repair only the reported conflict surface and re-run; "
            "this probe does not authorize semantic change or parser selection."
        )
    elif strict_evidence_state == "PASS_STRICT_CONSTRUCTION" and regex_lookaround_present:
        interpretation = (
            "Strict construction passed, but the grammar contains regex lookaround. Treat collision coverage as partial "
            "and require explicit metamorphic lexical-boundary tests before promoting the grammar."
        )
    elif strict_evidence_state == "PASS_STRICT_CONSTRUCTION":
        interpretation = (
            "Strict construction passed. This remains parser-construction evidence only and does not prove typed IR, "
            "semantic equivalence, or parser selection."
        )
    else:
        interpretation = "Strict evidence is unresolved; preserve the exact error and do not infer a grammar repair."

    return {
        "schema_version": "1.1",
        "experiment": "ClayCode D strict-LALR conflict localization",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "grammar_sha256": sha256(path),
        "runtime": {
            "parser": "lark",
            "mode": "lalr/contextual",
            "strict_test": True,
            "lark_version": package_version("lark"),
            "interegular_version": package_version("interegular"),
        },
        "nonstrict_build_ok": nonstrict_ok,
        "nonstrict_error": nonstrict_error,
        "strict_build_ok": strict_ok,
        "strict_evidence_state": strict_evidence_state,
        "strict_error": strict_error,
        "regex_lookaround_present": regex_lookaround_present,
        "strict_collision_scope_guard": (
            "Regex lookaround can limit interegular collision detection; strict=True is not sufficient by itself when lookaround is present."
            if regex_lookaround_present
            else "No regex lookaround detected by this static guard."
        ),
        "diagnostic_count": len(diagnostics),
        "conflict_diagnostics": conflict_lines,
        "all_diagnostics": diagnostics,
        "interpretation": interpretation,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT))
    ap.add_argument("--output")
    a = ap.parse_args()
    out = probe(Path(a.grammar))
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if a.output:
        p = Path(a.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
