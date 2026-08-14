#!/usr/bin/env python3
"""ClayCode BASE typed canonical IR builder (CC-WP-03 implementation slice).

The frontend AST is syntax-faithful. This layer adds deterministic nominal type identity,
record/interface/function signatures and explicit external nominal types without ever
collapsing an unknown type to Any. Expressions remain syntax trees until CC-WP-04/05
checker/evaluator semantics consume them.

Authority invariant: IR description never mints capability/effect authority.
Identity invariant: typed semantic identity is independent of source/provenance identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import claycode_base_frontend as front  # noqa: E402

DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
DEFAULT_SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
DOMAIN = b"ClayCodeBaseTypedIR/v1\x00"

PRIMITIVES = {
    "Bool", "Boolean", "Int", "Float", "String", "Bytes", "Symbol", "Unit",
}
CONSTRUCTORS = {
    "Set", "Ordered", "List", "Map", "Result", "Option", "Ref", "Delta",
}
KEYWORDS = {
    "module", "version", "status", "parent", "import", "interface", "dialect", "law",
    "rule", "invariant", "class", "type", "record", "tensor", "codec", "surface",
    "metric", "hash", "needle", "cycle", "fn", "if", "true", "false",
}
PUNCT = {"(", ")", "{", "}", "[", "]", "<", ">", ",", ":", "=", "?", "|", ";", "->"}


class TypedIRError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def children(node: Any) -> list[Any]:
    return list(node.get("children", [])) if isinstance(node, dict) else []


def kind(node: Any) -> str | None:
    return node.get("kind") if isinstance(node, dict) else None


def token(node: Any) -> tuple[str, str] | None:
    if isinstance(node, dict) and "token" in node:
        return str(node["token"]), str(node.get("value", ""))
    return None


def walk(node: Any) -> Iterable[Any]:
    yield node
    for child in children(node):
        yield from walk(child)


def token_values(node: Any) -> list[str]:
    out: list[str] = []
    for x in walk(node):
        t = token(x)
        if t is not None:
            out.append(t[1])
    return out


def direct_token_values(node: Any) -> list[str]:
    out = []
    for x in children(node):
        t = token(x)
        if t is not None:
            out.append(t[1])
    return out


def direct_identifier(node: Any) -> str | None:
    """Return a direct grammar-admitted identifier and fail closed on alias corruption."""
    for child in children(node):
        t = token(child)
        if t is not None and t[0] == "NAME":
            return t[1]
        k = kind(child)
        if k is not None and k.startswith("ident_"):
            vals = token_values(child)
            expected = k.removeprefix("ident_")
            if len(vals) != 1:
                raise TypedIRError(f"malformed {k} identifier node: expected one token, got {vals!r}")
            if vals[0] != expected:
                raise TypedIRError(
                    f"identifier alias/token mismatch: {k} requires {expected!r}, got {vals[0]!r}"
                )
            return vals[0]
    return None


def first_name(node: Any, *, after: str | None = None) -> str:
    name = direct_identifier(node)
    if name:
        return name
    vals = token_values(node)
    raise TypedIRError(f"cannot find declaration name in {vals!r}")


def split_between(vals: list[str], left: str, right: str, *, start: int = 0) -> list[str]:
    try:
        i = vals.index(left, start) + 1
        j = vals.index(right, i)
    except ValueError as exc:
        raise TypedIRError(f"missing {left!r}/{right!r} in {vals!r}") from exc
    return vals[i:j]


def type_text(vals: list[str]) -> str:
    # Type grammar is punctuation-sensitive and whitespace-insensitive; compact spelling is canonical.
    return "".join(vals)


def base_type_names(type_spelling: str) -> list[str]:
    # Extract nominal identifiers without treating punctuation/operators as types.
    names: list[str] = []
    cur = ""
    for ch in type_spelling:
        if ch.isalnum() or ch in "_.":
            cur += ch
        else:
            if cur and (cur[0].isalpha() or cur[0] == "_"):
                names.append(cur)
            cur = ""
    if cur and (cur[0].isalpha() or cur[0] == "_"):
        names.append(cur)
    return names


def parse_field(node: Any) -> dict[str, Any]:
    vals = token_values(node)
    try:
        colon = vals.index(":")
    except ValueError as exc:
        raise TypedIRError(f"field without type annotation: {vals!r}") from exc
    name = direct_identifier(node)
    if not name:
        raise TypedIRError(f"field without name: {vals!r}")
    end = vals.index("=", colon + 1) if "=" in vals[colon + 1:] else len(vals)
    typ = type_text(vals[colon + 1:end])
    if not typ:
        raise TypedIRError(f"field without type: {vals!r}")
    default_ast = None
    if end < len(vals):
        default_ast = vals[end + 1:]
    return {"name": name, "type": typ, "default_tokens": default_ast}


def parse_typed_param(node: Any) -> dict[str, str]:
    vals = token_values(node)
    try:
        colon = vals.index(":")
    except ValueError as exc:
        raise TypedIRError(f"typed parameter without ':' in {vals!r}") from exc
    name = direct_identifier(node)
    typ = type_text(vals[colon + 1:])
    if not name or not typ:
        raise TypedIRError(f"invalid typed parameter: {vals!r}")
    return {"name": name, "type": typ}


def parse_fn(node: Any) -> dict[str, Any]:
    vals = token_values(node)
    name = first_name(node, after="fn")
    params = [parse_typed_param(x) for x in walk(node) if kind(x) == "typed_param"]
    try:
        arrow = vals.index("->")
        eq = vals.index("=", arrow + 1)
    except ValueError as exc:
        raise TypedIRError(f"function signature malformed: {vals!r}") from exc
    ret = type_text(vals[arrow + 1:eq])
    if not ret:
        raise TypedIRError(f"function missing return type: {vals!r}")
    body_tokens = vals[eq + 1:]
    return {
        "kind": "function",
        "name": name,
        "params": params,
        "returns": ret,
        "body_tokens": body_tokens,
        "effects": [],
        "authority": "NONE",
    }


def parse_record_like(node: Any, decl_kind: str) -> dict[str, Any]:
    vals = token_values(node)
    name = first_name(node, after="record" if decl_kind == "record" else "interface")
    fields = [parse_field(x) for x in walk(node) if kind(x) == "field"]
    seen: set[str] = set()
    dup = [f["name"] for f in fields if f["name"] in seen or seen.add(f["name"])]
    if dup:
        raise TypedIRError(f"duplicate {decl_kind} field(s) in {name}: {sorted(set(dup))}")
    methods = []
    for m in (x for x in walk(node) if kind(x) == "method_sig"):
        mv = token_values(m)
        mname = direct_identifier(m)
        if not mname:
            raise TypedIRError(f"method without name: {mv!r}")
        params = []
        for p in (x for x in walk(m) if kind(x) == "param"):
            pv = token_values(p)
            pname = direct_identifier(p)
            if ":" in pv:
                c = pv.index(":")
                params.append({"name": pname or "", "type": type_text(pv[c + 1:])})
            else:
                # Existing semantic registry permits untyped interface params; preserve explicitly.
                params.append({"name": pname or "", "type": "OpaqueParam"})
        try:
            a = mv.index("->")
            returns = type_text(mv[a + 1:])
        except ValueError:
            returns = "Unit"
        methods.append({"name": mname, "params": params, "returns": returns})
    return {"kind": decl_kind, "name": name, "fields": fields, "methods": methods, "authority": "NONE"}


def extract_owned_nominals(ast: Any) -> set[str]:
    owned: set[str] = set()
    # Dialect registry expresses nominal ownership using `owns=[A,B,...]`.
    # Restrict extraction to an expression subtree containing an owns relation and a list.
    for node in walk(ast):
        vals = token_values(node)
        if kind(node) not in {"expr", "dialect_stmt", "dotted_relation", "prefix_relation", "rule_decl"}:
            continue
        if "owns" not in vals and ".owns" not in vals:
            continue
        try:
            lb = vals.index("[")
            rb = vals.index("]", lb + 1)
        except ValueError:
            continue
        for value in vals[lb + 1:rb]:
            if value not in {",", "[", "]"} and value not in KEYWORDS and value and (value[0].isalpha() or value[0] == "_"):
                owned.add(value)
    return owned


@dataclass(frozen=True)
class SourceUnit:
    path: Path
    frontend: dict[str, Any]


def build_typed_ir(units: list[SourceUnit]) -> dict[str, Any]:
    declarations: list[dict[str, Any]] = []
    owned_nominals: set[str] = set()
    source_rows = []

    for unit in units:
        ast = unit.frontend["canonical_ast"]
        owned_nominals |= extract_owned_nominals(ast)
        for node in walk(ast):
            k = kind(node)
            if k == "record_decl":
                declarations.append(parse_record_like(node, "record"))
            elif k == "interface_decl":
                declarations.append(parse_record_like(node, "interface"))
            elif k == "fn_decl":
                declarations.append(parse_fn(node))
        source_rows.append({
            "path": str(unit.path.relative_to(ROOT)) if unit.path.is_relative_to(ROOT) else str(unit.path),
            "source_sha256": unit.frontend["source_sha256"],
            "frontend_semantic_hash": unit.frontend["semantic_hash"],
            "grammar_sha256": unit.frontend["grammar_sha256"],
        })

    # Symbol identity is deterministic and duplicate declarations fail closed.
    symbol_keys: set[tuple[str, str]] = set()
    for decl in declarations:
        key = (decl["kind"], decl["name"])
        if key in symbol_keys:
            raise TypedIRError(f"duplicate declaration identity: {key}")
        symbol_keys.add(key)

    declared_types = {d["name"] for d in declarations if d["kind"] in {"record", "interface"}}
    referenced_types: set[str] = set()
    for decl in declarations:
        for fld in decl.get("fields", []):
            referenced_types.update(base_type_names(fld["type"]))
        for meth in decl.get("methods", []):
            referenced_types.update(base_type_names(meth["returns"]))
            for p in meth.get("params", []):
                referenced_types.update(base_type_names(p["type"]))
        if decl["kind"] == "function":
            referenced_types.update(base_type_names(decl["returns"]))
            for p in decl["params"]:
                referenced_types.update(base_type_names(p["type"]))

    # Every type is classified. Nothing silently becomes Any/dynamic.
    type_universe = []
    for name in sorted(referenced_types | declared_types | owned_nominals):
        if name in PRIMITIVES:
            cls = "PRIMITIVE"
        elif name in CONSTRUCTORS:
            cls = "TYPE_CONSTRUCTOR"
        elif name in declared_types:
            cls = "DECLARED_NOMINAL"
        elif name in owned_nominals:
            cls = "DIALECT_OWNED_NOMINAL"
        else:
            cls = "EXTERNAL_NOMINAL"
        type_universe.append({"name": name, "class": cls})

    # Semantic identity deliberately excludes source path/hash and frontend-contract
    # provenance. Two semantically identical programs with different whitespace/source
    # bytes must converge here; provenance remains attached outside this hash domain.
    semantic_core = {
        "schema_version": "1.1",
        "ir_schema": "ClayCodeBaseTypedIR/v1",
        "types": type_universe,
        "declarations": sorted(declarations, key=lambda d: (d["kind"], d["name"])),
        "invariants": {
            "unknown_type_to_any": "FORBIDDEN",
            "model_output_execution_authority": "FORBIDDEN",
            "descriptive_capability_is_bearer_authority": "FORBIDDEN",
            "declaration_authority": "NONE_UNLESS_RUNTIME_BROKER_SUPPLIES_SEALED_CAPABILITY",
            "semantic_identity_includes_source_provenance": "FORBIDDEN",
        },
    }
    ir_hash = sha256(DOMAIN + canon_bytes(semantic_core))
    return {
        **semantic_core,
        "sources": source_rows,
        "typed_ir_sha256": ir_hash,
        "program_semantic_id": f"clayir:{ir_hash}",
    }


def compile_sources(paths: list[Path], grammar_path: Path) -> dict[str, Any]:
    grammar = grammar_path.read_text(encoding="utf-8")
    units = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        units.append(SourceUnit(path, front.compile_frontend(source, grammar)))
    a = build_typed_ir(units)
    b = build_typed_ir(units)
    if a["typed_ir_sha256"] != b["typed_ir_sha256"] or canon_bytes(a) != canon_bytes(b):
        raise TypedIRError("typed IR is not deterministic")
    return a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    ap.add_argument("--source", action="append", type=Path, dest="sources")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    paths = args.sources or list(DEFAULT_SOURCES)
    result = compile_sources(paths, args.grammar)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
