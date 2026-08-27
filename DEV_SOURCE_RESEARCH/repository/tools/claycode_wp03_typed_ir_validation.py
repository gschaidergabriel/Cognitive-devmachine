#!/usr/bin/env python3
"""Executable validation for the ClayCode BASE typed canonical IR slice.

Produces a receipt but never edits the release workspace. Promotion remains a separate
receipt review decision.

The validation is self-contained with respect to the active V7 typed-fn grammar: every
fixture must first pass the production frontend in strict LALR mode, and the complete
frozen G9 + Dialect sources must preserve the same frontend semantic identity under strict
and typed-IR input paths. This prevents callers such as the Andreas target collector from
silently relying on an external CI-only strict-grammar precheck.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import claycode_base_frontend as front  # noqa: E402
import claycode_base_typed_ir as tir  # noqa: E402

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
OUT = ROOT / "research_entity/claycode/autonomous/WP03_TYPED_IR_RECEIPT.json"


def check(rows: list[dict], name: str, ok: bool, detail=None) -> None:
    rows.append({"name": name, "pass": bool(ok), "detail": detail})


def compile_text(text: str, name: str, grammar_text: str) -> dict:
    # Fail closed on the exact V7 strict parser contract before typed lowering. Lark's
    # strict flag is a construction/collision gate; parsing the same fixture here also
    # proves that the typed-IR fixture is admitted by that strict contract.
    front.compile_frontend(text, grammar_text, strict=True)
    with tempfile.TemporaryDirectory(prefix="claycode-wp03-") as td:
        p = Path(td) / name
        p.write_text(text, encoding="utf-8")
        return tir.compile_sources([p], GRAMMAR)


def main() -> int:
    rows: list[dict] = []
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    grammar_sha256 = hashlib.sha256(grammar_text.encode("utf-8")).hexdigest()

    strict_full = {}
    strict_error = None
    try:
        # Use the production parser constructor, not an independent Lark configuration.
        strict_parser = front.build_parser(grammar_text, strict=True)
        strict_parser.parse(G9.read_text(encoding="utf-8"))
        strict_parser.parse(DIALECT.read_text(encoding="utf-8"))
        strict_full = {
            str(G9.relative_to(ROOT)): front.compile_frontend(G9.read_text(encoding="utf-8"), grammar_text, strict=True),
            str(DIALECT.relative_to(ROOT)): front.compile_frontend(DIALECT.read_text(encoding="utf-8"), grammar_text, strict=True),
        }
        strict_ok = True
    except Exception as exc:
        strict_ok = False
        strict_error = f"{type(exc).__name__}: {exc}"
    check(rows, "strict_v7_production_frontend_full_frozen_sources", strict_ok, strict_error)

    full_a = tir.compile_sources([G9, DIALECT], GRAMMAR)
    full_b = tir.compile_sources([G9, DIALECT], GRAMMAR)
    check(rows, "full_frozen_sources_compile", bool(full_a.get("declarations")), len(full_a.get("declarations", [])))
    check(rows, "deterministic_program_semantic_id", full_a["program_semantic_id"] == full_b["program_semantic_id"], full_a["program_semantic_id"])
    check(rows, "deterministic_exact_ir", tir.canon_bytes(full_a) == tir.canon_bytes(full_b))

    typed_source_frontend = {row["path"]: row["frontend_semantic_hash"] for row in full_a.get("sources", [])}
    strict_source_frontend = {path: result["semantic_hash"] for path, result in strict_full.items()}
    check(
        rows,
        "strict_and_typed_input_frontend_semantics_equal",
        strict_ok and strict_source_frontend == typed_source_frontend,
        {"strict": strict_source_frontend, "typed_input": typed_source_frontend},
    )

    classes = {x["class"] for x in full_a["types"]}
    check(rows, "dialect_owned_nominals_materialized", "DIALECT_OWNED_NOMINAL" in classes)
    check(rows, "external_nominals_explicit_not_any", all(x["class"] != "DYNAMIC" for x in full_a["types"]) and not any(x["name"] == "Any" for x in full_a["types"]))
    check(rows, "all_descriptive_declarations_non_authoritative", all(x.get("authority") == "NONE" for x in full_a["declarations"]))
    check(rows, "frozen_authority_invariant_present", full_a["invariants"].get("model_output_execution_authority") == "FORBIDDEN")

    add = compile_text("fn add(a:Int,b:Int)->Int=a+b\n", "add.clay", grammar_text)
    add_ws = compile_text("fn add ( a : Int , b : Int ) -> Int = a + b\n", "add_ws.clay", grammar_text)
    sub = compile_text("fn add(a:Int,b:Int)->Int=a-b\n", "sub.clay", grammar_text)
    fn = next(x for x in add["declarations"] if x["kind"] == "function")
    check(rows, "typed_fn_signature", fn["name"] == "add" and fn["params"] == [{"name":"a","type":"Int"},{"name":"b","type":"Int"}] and fn["returns"] == "Int", fn)
    check(rows, "layout_insensitive_typed_identity", add["program_semantic_id"] == add_ws["program_semantic_id"], {"compact": add["program_semantic_id"], "spaced": add_ws["program_semantic_id"]})
    check(rows, "operator_mutation_discriminated", add["program_semantic_id"] != sub["program_semantic_id"], {"add": add["program_semantic_id"], "sub": sub["program_semantic_id"]})

    ext = compile_text("fn carry(x:MysteryRef)->MysteryRef=x\n", "external_nominal.clay", grammar_text)
    ext_types = {x["name"]: x["class"] for x in ext["types"]}
    check(rows, "unknown_nominal_never_any", ext_types.get("MysteryRef") == "EXTERNAL_NOMINAL", ext_types)

    duplicate_rejected = False
    duplicate_error = None
    try:
        compile_text("record X {\n a:Int\n a:Int\n}\n", "dup.clay", grammar_text)
    except Exception as exc:
        duplicate_rejected = True
        duplicate_error = f"{type(exc).__name__}: {exc}"
    check(rows, "duplicate_record_field_fail_closed", duplicate_rejected, duplicate_error)

    # Descriptive capability spelling cannot mint authority in IR.
    cap = compile_text("record CapabilityToken {\n id:CapabilityRef\n}\n", "cap.clay", grammar_text)
    cap_decl = next(x for x in cap["declarations"] if x["kind"] == "record")
    check(rows, "capability_name_does_not_mint_authority", cap_decl.get("authority") == "NONE", cap_decl)

    failures = [r["name"] for r in rows if not r["pass"]]
    receipt = {
        "schema_version": "1.1",
        "scope": "CC-WP-03_TYPED_CANONICAL_IR_IMPLEMENTATION_SLICE",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": grammar_sha256,
        "strict_parser": True,
        "strict_parser_constructor": "claycode_base_frontend.build_parser",
        "frozen_sources": [str(G9.relative_to(ROOT)), str(DIALECT.relative_to(ROOT))],
        "strict_frontend_semantic_hashes": strict_source_frontend,
        "checks": rows,
        "passed": len(rows) - len(failures),
        "failed": len(failures),
        "failures": failures,
        "full_program_semantic_id": full_a["program_semantic_id"],
        "type_class_counts": {c: sum(1 for x in full_a["types"] if x["class"] == c) for c in sorted(classes)},
        "promotion": "NONE_AUTOMATIC",
        "scope_guard": "PASS validates strict V7 production-frontend admission for the complete frozen G9+Dialect sources and every positive typed-IR fixture, deterministic typed nominal IR/signature identity, explicit external nominals, mutation discrimination and authority non-minting. It does not prove CC-WP-04 checker/effect closure, evaluator, compiler/lowering, real Frank/adaptive-state acceptance, or Andreas Ubuntu release acceptance.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": not failures, "passed": receipt["passed"], "failed": receipt["failed"], "failures": failures, "strict_parser": True, "out": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
