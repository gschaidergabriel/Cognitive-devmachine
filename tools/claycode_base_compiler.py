#!/usr/bin/env python3
"""Integrated ClayCode BASE pure-function compiler candidate.

Pipeline: V7 source -> canonical typed IR -> exact symbol/type check -> reference
interpreter -> C11 lowering. This intentionally excludes effects/FFI/async; those must
cross the external authority/runtime boundary in later BASE work packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree


class CompileError(Exception):
    pass


OP_MAP = {
    "op_ge": ">=", "op_le": "<=", "op_ne": "!=", "op_eqeq": "==",
    "op_arrow": "->", "op_implies": "=>", "op_gt": ">", "op_lt": "<",
    "op_eq": "=", "op_union": "|", "op_add": "+", "op_sub": "-",
    "op_mul": "*", "op_div": "/", "op_and": "&&", "op_oror": "||",
    "op_or": "or", "op_iff": "iff", "op_requires": "requires",
    "op_in": "in", "op_subset_of": "subset_of",
}


@dataclass(frozen=True)
class Param:
    name: str
    type: str


@dataclass
class Function:
    name: str
    params: list[Param]
    return_type: str
    body: Any


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def qid_name(node: Any) -> str:
    if isinstance(node, Token):
        return str(node)
    if not isinstance(node, Tree):
        raise CompileError(f"EXPECTED_QID:{node!r}")
    if str(node.data) == "qid":
        parts = []
        for child in node.children:
            if child is None:
                continue
            if isinstance(child, Token):
                parts.append(str(child))
            elif isinstance(child, Tree):
                data = str(child.data)
                if data.startswith("ident_"):
                    parts.append(data[6:])
                else:
                    parts.append(qid_name(child))
        return ".".join(parts)
    data = str(node.data)
    if data.startswith("ident_"):
        return data[6:]
    if len(node.children) == 1:
        return qid_name(node.children[0])
    raise CompileError(f"CANNOT_DECODE_QID:{node.data}")


def type_name(node: Any) -> str:
    if isinstance(node, Token):
        return str(node)
    if not isinstance(node, Tree):
        raise CompileError("BAD_TYPE")
    data = str(node.data)
    if data == "type_atom":
        child = next((c for c in node.children if isinstance(c, (Tree, Token))), None)
        return type_name(child)
    if data == "qid":
        return qid_name(node)
    if data == "type_expr":
        return "|".join(type_name(c) for c in node.children if c is not None)
    return qid_name(node)


def canonical_expr(node: Any) -> Any:
    if isinstance(node, Token):
        if node.type == "SIGNED_NUMBER":
            value = str(node)
            return {"k": "num", "v": float(value) if any(x in value for x in ".eE") else int(value)}
        if node.type == "BOOLEAN":
            return {"k": "bool", "v": str(node) == "true"}
        if node.type == "STRING":
            return {"k": "str", "v": json.loads(str(node))}
        if node.type == "NAME":
            return {"k": "name", "v": str(node)}
        return {"k": "tok", "t": node.type, "v": str(node)}
    if not isinstance(node, Tree):
        raise CompileError(f"BAD_EXPR_NODE:{node!r}")
    data = str(node.data)
    if data == "qid":
        return {"k": "name", "v": qid_name(node)}
    if data == "call":
        children = [c for c in node.children if c is not None]
        return {"k": "call", "f": qid_name(children[0]), "a": [canonical_expr(x) for x in children[1:]]}
    if data == "expr":
        children = [c for c in node.children if c is not None]
        if not children:
            raise CompileError("EMPTY_EXPR")
        current = canonical_expr(children[0])
        index = 1
        while index < len(children):
            op_node = children[index]
            if not isinstance(op_node, Tree) or str(op_node.data) not in OP_MAP:
                raise CompileError(f"OPERATOR_IDENTITY_MISSING:{op_node!r}")
            if index + 1 >= len(children):
                raise CompileError("DANGLING_OPERATOR")
            current = {
                "k": "bin",
                "op": OP_MAP[str(op_node.data)],
                "l": current,
                "r": canonical_expr(children[index + 1]),
            }
            index += 2
        return current
    if data in ("postfix_optional", "list", "set", "dotted_relation", "prefix_relation", "postfix_relation"):
        raise CompileError(f"NOT_EXECUTABLE_IN_PURE_FN_SLICE:{data}")
    if len(node.children) == 1:
        return canonical_expr(node.children[0])
    raise CompileError(f"UNSUPPORTED_EXPRESSION_NODE:{data}")


def parse_program(source: str, grammar_text: str) -> dict:
    parser = Lark(grammar_text, parser="lalr", lexer="contextual", strict=False, start="start")
    tree = parser.parse(source)
    functions = []
    for node in tree.find_data("fn_decl"):
        children = [c for c in node.children if c is not None]
        name = qid_name(children[0])
        index = 1
        params = []
        if isinstance(children[index], Tree) and str(children[index].data) == "typed_params":
            for param in children[index].children:
                if not isinstance(param, Tree) or str(param.data) != "typed_param":
                    continue
                pieces = [c for c in param.children if c is not None]
                params.append(Param(qid_name(pieces[0]), type_name(pieces[1])))
            index += 1
        return_type = type_name(children[index])
        index += 1
        functions.append(Function(name, params, return_type, canonical_expr(children[index])))
    if not functions:
        raise CompileError("NO_FUNCTIONS")
    seen = set()
    for function in functions:
        if function.name in seen:
            raise CompileError(f"DUPLICATE_FUNCTION:{function.name}")
        seen.add(function.name)
        param_names = set()
        for param in function.params:
            if param.name in param_names:
                raise CompileError(f"DUPLICATE_PARAM:{function.name}:{param.name}")
            param_names.add(param.name)
    return {"functions": functions}


def infer(expr: dict, env: dict[str, str], signatures: dict[str, tuple[list[str], str]]) -> str:
    kind = expr["k"]
    if kind == "num":
        return "Real" if isinstance(expr["v"], float) else "Int"
    if kind == "bool":
        return "Bool"
    if kind == "str":
        return "String"
    if kind == "name":
        if expr["v"] not in env:
            raise CompileError(f"UNDEFINED_VARIABLE:{expr['v']}")
        return env[expr["v"]]
    if kind == "call":
        if expr["f"] not in signatures:
            raise CompileError(f"UNDEFINED_FUNCTION:{expr['f']}")
        expected, return_type = signatures[expr["f"]]
        if len(expected) != len(expr["a"]):
            raise CompileError(f"ARITY_MISMATCH:{expr['f']}")
        actual = [infer(arg, env, signatures) for arg in expr["a"]]
        if actual != expected:
            raise CompileError(f"ARG_TYPE_MISMATCH:{expr['f']}:{actual}!={expected}")
        return return_type
    if kind == "bin":
        left = infer(expr["l"], env, signatures)
        right = infer(expr["r"], env, signatures)
        op = expr["op"]
        if op in ("+", "-", "*", "/"):
            if left != right or left not in ("Int", "Real"):
                raise CompileError(f"ARITH_TYPE:{op}:{left}:{right}")
            return left
        if op in (">", "<", ">=", "<="):
            if left != right or left not in ("Int", "Real"):
                raise CompileError(f"ORDER_TYPE:{op}:{left}:{right}")
            return "Bool"
        if op in ("==", "!="):
            if left != right:
                raise CompileError(f"EQ_TYPE:{left}:{right}")
            return "Bool"
        if op in ("&&", "||", "or", "iff", "=>"):
            if left != "Bool" or right != "Bool":
                raise CompileError(f"BOOL_TYPE:{op}:{left}:{right}")
            return "Bool"
        raise CompileError(f"UNSUPPORTED_OPERATOR:{op}")
    raise CompileError(f"UNSUPPORTED_EXPR:{kind}")


def compile_ir(program: dict) -> dict:
    functions = program["functions"]
    signatures = {f.name: ([p.type for p in f.params], f.return_type) for f in functions}
    allowed = {"Int", "Real", "Bool", "String"}
    for function in functions:
        if function.return_type not in allowed or any(param.type not in allowed for param in function.params):
            raise CompileError(f"UNSUPPORTED_TYPE:{function.name}")
        actual = infer(function.body, {p.name: p.type for p in function.params}, signatures)
        if actual != function.return_type:
            raise CompileError(f"RETURN_TYPE_MISMATCH:{function.name}:{actual}!={function.return_type}")
    canonical = {"schema": "claycode.typed-ir.v0", "functions": []}
    for function in sorted(functions, key=lambda f: f.name):
        canonical["functions"].append({
            "name": function.name,
            "params": [{"name": p.name, "type": p.type} for p in function.params],
            "return": function.return_type,
            "body": function.body,
        })
    return canonical


def eval_expr(expr: dict, env: dict[str, Any], functions: dict[str, dict], depth: int = 0) -> Any:
    if depth > 128:
        raise CompileError("RECURSION_LIMIT")
    kind = expr["k"]
    if kind in ("num", "bool", "str"):
        return expr["v"]
    if kind == "name":
        return env[expr["v"]]
    if kind == "call":
        function = functions[expr["f"]]
        values = [eval_expr(arg, env, functions, depth + 1) for arg in expr["a"]]
        next_env = dict(zip([p["name"] for p in function["params"]], values))
        return eval_expr(function["body"], next_env, functions, depth + 1)
    if kind == "bin":
        left = eval_expr(expr["l"], env, functions, depth)
        right = eval_expr(expr["r"], env, functions, depth)
        op = expr["op"]
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/": return int(left / right) if isinstance(left, int) and isinstance(right, int) else left / right
        if op == ">": return left > right
        if op == "<": return left < right
        if op == ">=": return left >= right
        if op == "<=": return left <= right
        if op == "==": return left == right
        if op == "!=": return left != right
        if op == "&&": return bool(left) and bool(right)
        if op in ("||", "or"): return bool(left) or bool(right)
        if op == "iff": return bool(left) == bool(right)
        if op == "=>": return (not bool(left)) or bool(right)
    raise CompileError(f"EVAL_UNSUPPORTED:{expr}")


def eval_function(ir: dict, name: str, args: list[Any]) -> Any:
    functions = {f["name"]: f for f in ir["functions"]}
    if name not in functions:
        raise CompileError(f"UNDEFINED_FUNCTION:{name}")
    function = functions[name]
    if len(args) != len(function["params"]):
        raise CompileError(f"ARITY_MISMATCH:{name}")
    env = dict(zip([p["name"] for p in function["params"]], args))
    return eval_expr(function["body"], env, functions)


def c_type(type_name_: str) -> str:
    return {"Int": "int64_t", "Bool": "bool", "Real": "double", "String": "const char *"}[type_name_]


def c_var(name: str) -> str:
    return "ccv_" + name


def c_fn(name: str) -> str:
    return "ccf_" + name


def c_expr(expr: dict) -> str:
    kind = expr["k"]
    if kind == "num": return repr(expr["v"])
    if kind == "bool": return "true" if expr["v"] else "false"
    if kind == "str": return json.dumps(expr["v"])
    if kind == "name": return c_var(expr["v"])
    if kind == "call": return f"{c_fn(expr['f'])}({','.join(c_expr(a) for a in expr['a'])})"
    if kind == "bin":
        operator = {"or": "||", "iff": "==", "=>": "<="}.get(expr["op"], expr["op"])
        return f"({c_expr(expr['l'])} {operator} {c_expr(expr['r'])})"
    raise CompileError(f"C_UNSUPPORTED:{kind}")


def lower_c(ir: dict, entry: str | None = None) -> str:
    lines = ["#include <stdint.h>", "#include <stdbool.h>", "#include <stdio.h>", "#include <stdlib.h>", ""]
    for function in ir["functions"]:
        params = ", ".join(f"{c_type(p['type'])} {c_var(p['name'])}" for p in function["params"]) or "void"
        lines.append(f"static {c_type(function['return'])} {c_fn(function['name'])}({params});")
    lines.append("")
    for function in ir["functions"]:
        params = ", ".join(f"{c_type(p['type'])} {c_var(p['name'])}" for p in function["params"]) or "void"
        lines.append(f"static {c_type(function['return'])} {c_fn(function['name'])}({params}) {{ return {c_expr(function['body'])}; }}")
    if entry:
        function = next((f for f in ir["functions"] if f["name"] == entry), None)
        if not function:
            raise CompileError(f"UNDEFINED_ENTRY:{entry}")
        if any(p["type"] not in ("Int", "Real", "Bool") for p in function["params"]):
            raise CompileError("ENTRY_ARG_TYPE_UNSUPPORTED")
        args = []
        for index, param in enumerate(function["params"], 1):
            if param["type"] == "Int": args.append(f"(int64_t)strtoll(argv[{index}],NULL,10)")
            elif param["type"] == "Real": args.append(f"strtod(argv[{index}],NULL)")
            else: args.append(f"(atoi(argv[{index}])!=0)")
        return_type = function["return"]
        call = f"{c_fn(entry)}({','.join(args)})"
        fmt = {"Int": "%lld\\n", "Bool": "%d\\n", "Real": "%.17g\\n", "String": "%s\\n"}[return_type]
        cast = "(long long)" if return_type == "Int" else ""
        lines += [
            "", "int main(int argc,char**argv){",
            f"  if(argc!={len(function['params']) + 1}) return 64;",
            f"  {c_type(return_type)} out={call};",
            f"  printf(\"{fmt}\",{cast}out);",
            "  return 0;", "}",
        ]
    return "\n".join(lines) + "\n"


def build(source: str, grammar_text: str) -> dict:
    ir = compile_ir(parse_program(source, grammar_text))
    semantic = json.dumps(ir, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "ir": ir,
        "semantic_hash": sha256(semantic),
        "source_hash": sha256(source.encode("utf-8")),
        "grammar_hash": sha256(grammar_text.encode("utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--grammar", required=True)
    parser.add_argument("--emit-ir")
    parser.add_argument("--emit-c")
    parser.add_argument("--entry")
    args = parser.parse_args()
    source = Path(args.source).read_text(encoding="utf-8")
    grammar = Path(args.grammar).read_text(encoding="utf-8")
    result = build(source, grammar)
    if args.emit_ir:
        Path(args.emit_ir).write_text(json.dumps(result["ir"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.emit_c:
        Path(args.emit_c).write_text(lower_c(result["ir"], args.entry), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("semantic_hash", "source_hash", "grammar_hash")}, sort_keys=True))


if __name__ == "__main__":
    main()
