#!/usr/bin/env python3
"""ClayCode BASE typed declaration IR prototype for CC-WP-03.

This component lowers accepted declarative BASE-D V9 syntax into a deterministic
declaration/type IR while keeping semantic identity, source identity and parser-contract
identity distinct. Procedural structured functions are handled by the generic structured
backend; this module intentionally does not silently discard or reinterpret that dialect.
It is not the full evaluator/compiler IR and does not close CC-WP-03 by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
IR_SCHEMA = "claycode-base-typed-decl-ir/1"
DECL_RULES = {
    "record_decl", "interface_decl", "class_decl", "needle_decl", "cycle_decl",
    "import_decl", "dialect_decl", "module_decl", "version_decl", "status_decl",
    "parent_decl", "tensor_decl", "codec_decl", "surface_decl", "metric_decl",
    "hash_decl", "law_decl", "rule_decl", "invariant_decl",
}
PRESENTATION_TOKENS = {"NEWLINE", "SEMICOLON"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_syntax(node: Any) -> Any | None:
    if node is None:
        return {"literal": None}
    if isinstance(node, Token):
        if str(node.type) in PRESENTATION_TOKENS:
            return None
        return {"token": str(node.type), "value": str(node)}
    if isinstance(node, Tree):
        children = []
        for child in node.children:
            cooked = canonical_syntax(child)
            if cooked is not None:
                children.append(cooked)
        return {"kind": str(node.data), "children": children}
    return {"literal": str(node)}


def token_text(node: Any) -> str | None:
    if isinstance(node, Token):
        return str(node)
    if isinstance(node, Tree):
        vals = [str(x) for x in node.scan_values(lambda x: isinstance(x, Token))]
        return "".join(vals) if vals else None
    return None


def qid_text(node: Tree) -> str:
    if not isinstance(node, Tree) or str(node.data) != "qid":
        raise TypeError("qid tree required")
    parts = []
    for child in node.children:
        if isinstance(child, Token):
            if str(child.type) == "DOT":
                continue
            parts.append(str(child))
        elif isinstance(child, Tree):
            text = token_text(child)
            if text:
                parts.append(text)
    return ".".join(parts)


def first_tree(node: Tree, name: str) -> Tree | None:
    for child in node.children:
        if isinstance(child, Tree) and str(child.data) == name:
            return child
    return None


def type_params_ir(node: Tree | None) -> list[dict[str, Any]]:
    if node is None:
        return []
    out = []
    for child in node.children:
        if isinstance(child, Tree) and str(child.data) in {"type_atom", "type_expr", "qid"}:
            out.append(type_ir(child))
    return out


def type_ir(node: Any) -> dict[str, Any]:
    if isinstance(node, Tree) and str(node.data) == "type_expr":
        members = [
            type_ir(child)
            for child in node.children
            if isinstance(child, Tree) and str(child.data) in {"type_atom", "type_expr", "qid"}
        ]
        if len(members) == 1:
            return members[0]
        return {"kind": "union", "members": members}
    if isinstance(node, Tree) and str(node.data) == "type_atom":
        qid = next((x for x in node.children if isinstance(x, Tree) and str(x.data) == "qid"), None)
        if qid is None:
            raise ValueError("type_atom without qid")
        params = next((x for x in node.children if isinstance(x, Tree) and str(x.data) == "type_params"), None)
        optional = any(isinstance(x, Token) and str(x.type) == "QMARK" for x in node.children)
        return {"kind": "named", "name": qid_text(qid), "args": type_params_ir(params), "optional": optional}
    if isinstance(node, Tree) and str(node.data) == "qid":
        return {"kind": "named", "name": qid_text(node), "args": [], "optional": False}
    raise TypeError(f"unsupported type node {getattr(node, 'data', type(node))!r}")


def simple_param_names(params: list[dict[str, Any]]) -> list[str]:
    out = []
    for p in params:
        if p.get("kind") != "named" or p.get("args") or p.get("optional"):
            raise ValueError(f"generic parameter must be a simple name: {p}")
        out.append(str(p["name"]))
    return out


def name_after_keyword(node: Tree) -> str:
    for child in node.children[1:]:
        if isinstance(child, Token):
            return str(child)
        if isinstance(child, Tree) and str(child.data).startswith("ident_"):
            text = token_text(child)
            if text:
                return text
    raise ValueError(f"no declaration name in {node.data}")


def field_ir(node: Tree) -> dict[str, Any]:
    name = token_text(node.children[0])
    type_node = next(
        (x for x in node.children if isinstance(x, Tree) and str(x.data) in {"type_atom", "type_expr", "qid"}),
        None,
    )
    if not name or type_node is None:
        raise ValueError("malformed field")
    default_expr = None
    eq_seen = False
    for child in node.children:
        if isinstance(child, Token) and str(child.type) == "EQUAL":
            eq_seen = True
            continue
        if eq_seen and isinstance(child, Tree):
            default_expr = canonical_syntax(child)
            break
    return {"name": name, "type": type_ir(type_node), "default": default_expr}


def param_ir(node: Tree) -> dict[str, Any]:
    name = token_text(node.children[0])
    type_node = next(
        (x for x in node.children if isinstance(x, Tree) and str(x.data) in {"type_atom", "type_expr", "qid"}),
        None,
    )
    return {"name": name, "type": type_ir(type_node) if type_node is not None else None}


def params_ir(node: Tree | None) -> list[dict[str, Any]]:
    if node is None:
        return []
    return [param_ir(x) for x in node.children if isinstance(x, Tree) and str(x.data) == "param"]


def method_ir(node: Tree) -> dict[str, Any]:
    name = token_text(node.children[0])
    params = first_tree(node, "params")
    type_nodes = [
        x for x in node.children
        if isinstance(x, Tree) and str(x.data) in {"type_atom", "type_expr", "qid"}
    ]
    if not type_nodes:
        raise ValueError("method signature missing return type")
    return {"name": name, "params": params_ir(params), "returns": type_ir(type_nodes[-1])}


def lower_decl(node: Tree) -> dict[str, Any]:
    kind = str(node.data)
    if kind == "record_decl":
        name = name_after_keyword(node)
        params = next((x for x in node.children if isinstance(x, Tree) and str(x.data) == "type_params"), None)
        block = first_tree(node, "record_block")
        fields = [field_ir(x) for x in block.children if isinstance(x, Tree) and str(x.data) == "field"] if block else []
        return {"kind": "record", "name": name, "type_params": simple_param_names(type_params_ir(params)), "fields": fields}
    if kind == "interface_decl":
        name = name_after_keyword(node)
        block = first_tree(node, "interface_block")
        fields, methods = [], []
        if block:
            for child in block.children:
                if isinstance(child, Tree) and str(child.data) == "field":
                    fields.append(field_ir(child))
                elif isinstance(child, Tree) and str(child.data) == "method_sig":
                    methods.append(method_ir(child))
        return {"kind": "interface", "name": name, "fields": fields, "methods": methods}
    if kind == "needle_decl":
        name = name_after_keyword(node)
        params = first_tree(node, "params")
        type_nodes = [
            x for x in node.children
            if isinstance(x, Tree) and str(x.data) in {"type_atom", "type_expr", "qid"}
        ]
        if not type_nodes:
            raise ValueError("needle missing return type")
        return {"kind": "needle", "name": name, "params": params_ir(params), "returns": type_ir(type_nodes[-1])}
    if kind == "cycle_decl":
        return {"kind": "cycle", "name": "cycle", "params": params_ir(first_tree(node, "params")), "body": canonical_syntax(first_tree(node, "cycle_block"))}
    if kind == "class_decl":
        name = name_after_keyword(node)
        params = next((x for x in node.children if isinstance(x, Tree) and str(x.data) == "type_params"), None)
        rhs = next((x for x in reversed(node.children) if isinstance(x, Tree)), None)
        return {"kind": "type_alias", "name": name, "type_params": simple_param_names(type_params_ir(params)), "definition": canonical_syntax(rhs)}
    if kind == "import_decl":
        return {"kind": "import", "name": name_after_keyword(node), "syntax": canonical_syntax(node)}
    return {"kind": kind.removesuffix("_decl"), "syntax": canonical_syntax(node)}


def iter_top_decls(tree: Tree):
    for child in tree.children:
        if isinstance(child, Tree) and str(child.data) in DECL_RULES:
            yield child


def walk_types(value: Any):
    if isinstance(value, dict):
        if value.get("kind") in {"named", "union"}:
            yield value
        for child in value.values():
            yield from walk_types(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_types(child)


def classify_type_uses(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    local = {d["name"] for d in declarations if d.get("kind") in {"record", "interface", "type_alias"} and d.get("name")}
    rows = []
    seen = set()
    for index, decl in enumerate(declarations):
        owner = str(decl.get("name") or f"{decl.get('kind','decl')}#{index}")
        generics = set(decl.get("type_params", []))
        for t in walk_types(decl):
            if t.get("kind") != "named":
                continue
            name = str(t["name"])
            scope = "LOCAL_DECLARED" if name in local else ("GENERIC_PARAM" if name in generics else "EXTERNAL_OR_BUILTIN_UNRESOLVED")
            key = (owner, name, scope)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"owner": owner, "name": name, "resolution": scope})
    return sorted(rows, key=lambda x: (x["owner"], x["name"], x["resolution"]))


def lower_program(source: str, grammar: str, *, strict: bool = True) -> dict[str, Any]:
    parser = Lark(grammar, parser="lalr", lexer="contextual", strict=strict, start="start", keep_all_tokens=True)
    tree = parser.parse(source)
    declarations = [lower_decl(x) for x in iter_top_decls(tree)]
    named = [d["name"] for d in declarations if d.get("name")]
    duplicates = sorted({x for x in named if named.count(x) > 1})
    if duplicates:
        raise ValueError(f"duplicate declaration names: {duplicates}")
    grammar_sha = sha256_bytes(grammar.encode("utf-8"))
    semantic_payload = {"schema": IR_SCHEMA, "declarations": declarations}
    semantic_identity = sha256_bytes(stable_bytes(semantic_payload))
    return {
        "schema_version": IR_SCHEMA,
        "surface": "BASE_D_V9_DECLARATIVE",
        "identity": {
            "semantic_ir_sha256": semantic_identity,
            "source_sha256": sha256_bytes(source.encode("utf-8")),
            "grammar_sha256": grammar_sha,
        },
        "declarations": declarations,
        "type_uses": classify_type_uses(declarations),
    }


def self_test(grammar: str, *, strict: bool) -> dict[str, Any]:
    a = """record Box<T> {
 value:T
 maybe:Ref?
 choices:Int|String
}
interface Verifiable {
 expected:Set<Predicate>
 verify(receipt:ReceiptRef)->Verification
}
needle lower(x:Box<Int>)->Result<Int|Error>
"""
    b = """// presentation variant
record Box<T> { value:T; maybe:Ref?; choices:Int|String }
interface Verifiable { expected:Set<Predicate>; verify(receipt:ReceiptRef)->Verification }
needle lower(x:Box<Int>)->Result<Int|Error>
"""
    mutation = a.replace("choices:Int|String", "choices:Int|Bool")
    ira = lower_program(a, grammar, strict=strict)
    irb = lower_program(b, grammar, strict=strict)
    irm = lower_program(mutation, grammar, strict=strict)
    same_semantics = ira["identity"]["semantic_ir_sha256"] == irb["identity"]["semantic_ir_sha256"]
    source_distinct = ira["identity"]["source_sha256"] != irb["identity"]["source_sha256"]
    mutation_distinct = ira["identity"]["semantic_ir_sha256"] != irm["identity"]["semantic_ir_sha256"]
    type_rows = {(x["owner"], x["name"]): x["resolution"] for x in ira["type_uses"]}
    type_resolution_ok = (
        type_rows.get(("lower", "Box")) == "LOCAL_DECLARED"
        and type_rows.get(("Box", "T")) == "GENERIC_PARAM"
        and type_rows.get(("Verifiable", "ReceiptRef")) == "EXTERNAL_OR_BUILTIN_UNRESOLVED"
    )
    duplicate_rejected = False
    try:
        lower_program("record X {a:Int}\nrecord X {b:Int}\n", grammar, strict=strict)
    except ValueError:
        duplicate_rejected = True
    scoped = lower_program("record A<T> {x:T}\nrecord B {x:T}\n", grammar, strict=strict)
    scoped_rows = {(x["owner"], x["name"]): x["resolution"] for x in scoped["type_uses"]}
    generic_scope_local = (
        scoped_rows.get(("A", "T")) == "GENERIC_PARAM"
        and scoped_rows.get(("B", "T")) == "EXTERNAL_OR_BUILTIN_UNRESOLVED"
    )
    passed = same_semantics and source_distinct and mutation_distinct and type_resolution_ok and duplicate_rejected and generic_scope_local
    return {
        "schema_version": "1.1",
        "component": "ClayCode BASE typed declaration IR",
        "surface": "BASE_D_V9_DECLARATIVE",
        "strict_parser": strict,
        "same_semantics_across_layout": same_semantics,
        "source_identity_remains_distinct": source_distinct,
        "semantic_mutation_changes_identity": mutation_distinct,
        "type_resolution_classification": type_resolution_ok,
        "duplicate_declaration_rejected": duplicate_rejected,
        "generic_scope_is_declaration_local": generic_scope_local,
        "pass": passed,
        "scope_guard": "PASS covers typed declaration lowering/identity invariants in this fixture only; it is sandbox/proxy evidence if strict_parser=false and does not close CC-WP-03."
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?")
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--output")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--relaxed-parser-for-test", action="store_true")
    args = ap.parse_args()
    grammar = Path(args.grammar).read_text(encoding="utf-8")
    strict = not args.relaxed_parser_for_test
    if args.self_test:
        out = self_test(grammar, strict=strict)
    else:
        if not args.source:
            raise SystemExit("source path required unless --self-test")
        source_path = Path(args.source)
        out = lower_program(source_path.read_text(encoding="utf-8"), grammar, strict=strict)
        out["source_path"] = str(source_path)
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.self_test and not out["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
