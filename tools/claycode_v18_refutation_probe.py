#!/usr/bin/env python3
"""Deterministic causal refutation probe for ClayCode BASE D V18.

Expected result: V18 is NOT a strict-LALR replacement for V17. The bare NEEDLE_OWNS
operand required by frozen G9 creates a shift/reduce conflict with NEEDLE_OWNS <rhs>.
Lesioning only the bare operand removes that grammar-conflict family but breaks the frozen
`4B_need_not_learn Needle.owns` program. This turns a failed candidate into durable
negative evidence instead of treating red CI as an unexplained failure.
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
from lark.exceptions import GrammarError, LexError

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_NO_LOOKAHEAD.lark"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def strict_state(grammar: str) -> dict:
    try:
        Lark(
            grammar,
            parser="lalr",
            lexer="contextual",
            strict=True,
            debug=True,
            keep_all_tokens=True,
            maybe_placeholders=False,
        )
        return {"state": "PASS_STRICT_CONSTRUCTION", "error": None}
    except GrammarError as exc:
        return {"state": "FAIL_GRAMMAR_CONFLICT", "error": str(exc)}
    except LexError as exc:
        if "interegular" in str(exc).lower():
            return {"state": "BLOCKED_MISSING_INTEREGULAR", "error": str(exc)}
        return {"state": "FAIL_LEXER", "error": str(exc)}
    except Exception as exc:
        return {"state": "FAIL_OTHER", "error": f"{type(exc).__name__}: {exc}"}


def accepts(grammar: str, source: str) -> bool:
    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=False,
        keep_all_tokens=True,
        maybe_placeholders=False,
    )
    try:
        parser.parse(source)
        return True
    except Exception:
        return False


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    grammar_sha = hashlib.sha256(grammar.encode("utf-8")).hexdigest()

    v18 = strict_state(grammar)
    lesion = grammar.replace(" | needle_owns_atom", "").replace("\nneedle_owns_atom: NEEDLE_OWNS", "")
    lesion_state = strict_state(lesion)

    frozen_bare = "rule 4B_need_not_learn Needle.owns\n"
    relation = "rule Needle.owns X\n"
    call = "rule Needle.owns(X)\n"
    lowers_paren = "rule Needle.lowers (X)\n"

    behavior = {
        "v18_frozen_bare_accept": accepts(grammar, frozen_bare),
        "lesion_frozen_bare_accept": accepts(lesion, frozen_bare),
        "v18_relation_accept": accepts(grammar, relation),
        "lesion_relation_accept": accepts(lesion, relation),
        "v18_call_accept": accepts(grammar, call),
        "lesion_call_accept": accepts(lesion, call),
        "v18_lowers_paren_accept": accepts(grammar, lowers_paren),
        "lesion_lowers_paren_accept": accepts(lesion, lowers_paren),
    }

    v18_conflict_is_bare_owns = (
        v18["state"] == "FAIL_GRAMMAR_CONFLICT"
        and v18["error"] is not None
        and "needle_owns_atom : NEEDLE_OWNS" in v18["error"]
    )
    lesion_removed_same_grammar_conflict = lesion_state["state"] in {
        "PASS_STRICT_CONSTRUCTION",
        "BLOCKED_MISSING_INTEREGULAR",
    }
    semantic_cost_observed = behavior["v18_frozen_bare_accept"] and not behavior["lesion_frozen_bare_accept"]
    boundary_preserved = (
        behavior["v18_relation_accept"]
        and behavior["lesion_relation_accept"]
        and behavior["v18_call_accept"]
        and behavior["lesion_call_accept"]
        and not behavior["v18_lowers_paren_accept"]
        and not behavior["lesion_lowers_paren_accept"]
    )

    refuted = v18_conflict_is_bare_owns and lesion_removed_same_grammar_conflict and semantic_cost_observed and boundary_preserved
    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode V18 no-lookahead causal refutation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": grammar_sha,
        "runtime": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "v18_strict": v18,
        "bare_owns_lesion_strict": lesion_state,
        "behavior": behavior,
        "causal_checks": {
            "v18_conflict_localized_to_bare_owns": v18_conflict_is_bare_owns,
            "lesion_removes_same_grammar_conflict": lesion_removed_same_grammar_conflict,
            "lesion_breaks_frozen_bare_owns_usage": semantic_cost_observed,
            "other_boundary_cases_preserved": boundary_preserved,
        },
        "result": "REFUTED" if refuted else "UNRESOLVED",
        "promotion": "NONE",
        "architecture_delta": "NO_CHANGE_KEEP_V17_SELECTED_FOR_WP02",
        "scope_guard": (
            "REFUTED means the exact V18 no-lookahead candidate cannot replace the V17 lexical membrane without either retaining a strict LALR conflict or breaking frozen G9 bare-Needle.owns usage. "
            "It does not prove V17 globally optimal, close CC-WP-02/WP03, or authorize a Frank Harness change."
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if refuted else 1


if __name__ == "__main__":
    raise SystemExit(main())
