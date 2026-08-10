#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_base_frontend as front

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
PREFIX = ROOT / "research_entity/claycode/base/fixtures/WP03_OWNER_AGENCY_WEB_PREFIX_V1.clay"


def error_record(exc: BaseException) -> dict:
    out = {
        "error_type": type(exc).__name__,
        "message": str(exc),
        "line": getattr(exc, "line", None),
        "column": getattr(exc, "column", None),
        "token_type": str(getattr(getattr(exc, "token", None), "type", "")),
        "token_value": str(getattr(getattr(exc, "token", None), "value", "")),
        "expected": sorted(str(x) for x in (getattr(exc, "expected", None) or [])),
    }
    return out


def compile_text(source: str):
    return front.compile_frontend(source, GRAMMAR.read_text(encoding="utf-8"), strict=True)


def main() -> int:
    source = PREFIX.read_text(encoding="utf-8")
    lines = source.splitlines()
    assert lines[0] == "module self.root.autotelic_proactive_agency"
    assert lines[1] == 'version "0.1-owner-fixed-2026-08-10"'
    assert lines[2] == "status PROJECT_OWNER_FIXED_DIRECTIVE"
    assert lines[5].startswith("target=@research_entity/global/")

    try:
        compile_text(source)
    except Exception as exc:
        raw = error_record(exc)
    else:
        raise AssertionError("exact owner prefix unexpectedly admitted by V18")

    assert raw["line"] == 6, raw
    assert raw["token_value"] == "target", raw

    # Diagnostic-only surface rewrite of the five free Ref bindings into existing V18 import
    # syntax. This is NOT a semantic promotion; it isolates the next unsupported owner-surface
    # construct while keeping the right-hand references byte-identical.
    lowered_lines = list(lines)
    for index in range(5, 10):
        lowered_lines[index] = "import " + lowered_lines[index]
    import_lowered = "\n".join(lowered_lines) + "\n"
    try:
        compile_text(import_lowered)
    except Exception as exc:
        after_import = error_record(exc)
    else:
        after_import = {"status": "PASS"}

    assert after_import.get("status") != "PASS", after_import
    assert after_import["line"] > raw["line"], after_import

    report = {
        "status": "PASS_COUNTEREXAMPLE",
        "scope": "WP03_OWNER_AGENCY_WEB_EXACT_PREFIX_V18_COUNTEREXAMPLE",
        "prefix_lines": len(lines),
        "raw_v18": "REJECTED",
        "raw_first_counterexample": raw,
        "free_ref_binding_existing_surface_rewrite": "DIAGNOSTIC_IMPORT_ONLY_NOT_PROMOTED",
        "post_import_rewrite": "REJECTED_AT_NEXT_SURFACE_GAP",
        "post_import_counterexample": after_import,
        "core_v18_language_change_required": "NOT_YET_DECIDED",
        "surface_lowering_path_viable": "PARTIAL_FIRST_GAP_ONLY",
        "promotion": "NONE",
        "effect_authority": "NONE",
        "truth_authority": "NONE",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
