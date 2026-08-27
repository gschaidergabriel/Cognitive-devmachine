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
import math
from decimal import Decimal, InvalidOperation
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

INT64_MIN = -(1 << 63)
INT64_MAX = (1 << 63) - 1


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
            if any(x in value for x in ".eE"):
                try:
                    decimal_value = Decimal(value)
                except InvalidOperation as exc:
                    raise CompileError(f"REAL_LITERAL_INVALID:{value}") from exc
                real_value = float(value)
                if not math.isfinite(real_value):
                    raise CompileError(f"REAL_LITERAL_OUT_OF_RANGE:{value}")
                if real_value == 0.0 and decimal_value != 0:
                    raise CompileError(f"REAL_LITERAL_UNDERFLOW:{value}")
                return {"k": "num", "v": real_value}
            int_value = int(value)
            if int_value < INT64_MIN or int_value > INT64_MAX:
                raise CompileError(f"INT_LITERAL_OUT_OF_RANGE:{value}")
            return {"k": "num", "v": int_value}
        if node.type == "BOOLEAN":
            return {"k": "bool", "v": str(node) == "true"}
        if node.type == "STRING":
            string_value = json.loads(str(node))
            try:
                string_value.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise CompileError("STRING_UTF8_INVALID_SCALAR") from exc
            return {"k": "str", "v": string_value}
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


def _infer_binary_types(left: str, right: str, op: str) -> str:
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


def infer(expr: dict, env: dict[str, str], signatures: dict[str, tuple[list[str], str]]) -> str:
    tasks: list[tuple] = [("eval", expr)]
    types: list[str] = []
    while tasks:
        task = tasks.pop()
        tag = task[0]
        if tag == "eval":
            current = task[1]
            kind = current["k"]
            if kind == "num":
                types.append("Real" if isinstance(current["v"], float) else "Int")
            elif kind == "bool":
                types.append("Bool")
            elif kind == "str":
                types.append("String")
            elif kind == "name":
                if current["v"] not in env:
                    raise CompileError(f"UNDEFINED_VARIABLE:{current['v']}")
                types.append(env[current["v"]])
            elif kind == "call":
                if current["f"] not in signatures:
                    raise CompileError(f"UNDEFINED_FUNCTION:{current['f']}")
                expected, return_type = signatures[current["f"]]
                tasks.append(("call", current["f"], expected, return_type, len(current["a"])))
                for arg in reversed(current["a"]):
                    tasks.append(("eval", arg))
            elif kind == "bin":
                tasks.append(("bin", current["op"]))
                tasks.append(("eval", current["r"]))
                tasks.append(("eval", current["l"]))
            else:
                raise CompileError(f"UNSUPPORTED_EXPR:{kind}")
        elif tag == "call":
            name, expected, return_type, argc = task[1], task[2], task[3], task[4]
            actual = types[-argc:] if argc else []
            if argc:
                del types[-argc:]
            if len(expected) != argc:
                raise CompileError(f"ARITY_MISMATCH:{name}")
            if actual != expected:
                raise CompileError(f"ARG_TYPE_MISMATCH:{name}:{actual}!={expected}")
            types.append(return_type)
        elif tag == "bin":
            right = types.pop()
            left = types.pop()
            types.append(_infer_binary_types(left, right, task[1]))
        else:
            raise CompileError(f"INFER_BAD_TASK:{tag}")
    if len(types) != 1:
        raise CompileError(f"INFER_RESULT_STACK:{len(types)}")
    return types[0]


def _called_function_names(expr: dict) -> set[str]:
    out: set[str] = set()
    pending = [expr]
    while pending:
        current = pending.pop()
        kind = current["k"]
        if kind == "call":
            out.add(current["f"])
            pending.extend(current["a"])
        elif kind == "bin":
            pending.extend((current["l"], current["r"]))
    return out


def _reject_recursive_call_cycles(functions: list[Function]) -> None:
    graph = {function.name: _called_function_names(function.body) for function in functions}
    state: dict[str, int] = {}
    for root in graph:
        if state.get(root, 0) != 0:
            continue
        state[root] = 1
        path = [root]
        positions = {root: 0}
        frames = [(root, iter(sorted(graph[root])))]
        while frames:
            name, edges = frames[-1]
            try:
                callee = next(edges)
            except StopIteration:
                state[name] = 2
                frames.pop()
                positions.pop(name, None)
                path.pop()
                continue
            mark = state.get(callee, 0)
            if mark == 0:
                state[callee] = 1
                positions[callee] = len(path)
                path.append(callee)
                frames.append((callee, iter(sorted(graph.get(callee, set())))))
            elif mark == 1:
                start = positions.get(callee, 0)
                cycle = path[start:] + [callee]
                raise CompileError("RECURSIVE_CALL_CYCLE:" + "->".join(cycle))


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
    _reject_recursive_call_cycles(functions)
    canonical = {"schema": "claycode.typed-ir.v0", "functions": []}
    for function in sorted(functions, key=lambda f: f.name):
        canonical["functions"].append({
            "name": function.name,
            "params": [{"name": p.name, "type": p.type} for p in function.params],
            "return": function.return_type,
            "body": function.body,
        })
    return canonical


def _checked_int64(value: int, error: str) -> int:
    if value < INT64_MIN or value > INT64_MAX:
        raise CompileError(error)
    return value


def _trunc_int_div(left: int, right: int) -> int:
    """Checked int64 truncation toward zero; matches the C11 backend error boundary."""
    if right == 0:
        raise CompileError("DIVISION_BY_ZERO")
    if left == INT64_MIN and right == -1:
        raise CompileError("INT_DIV_OVERFLOW")
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def _eval_binary(left: Any, right: Any, op: str) -> Any:
    if op == "+":
        return _checked_int64(left + right, "INT_ADD_OVERFLOW") if type(left) is int and type(right) is int else left + right
    if op == "-":
        return _checked_int64(left - right, "INT_SUB_OVERFLOW") if type(left) is int and type(right) is int else left - right
    if op == "*":
        return _checked_int64(left * right, "INT_MUL_OVERFLOW") if type(left) is int and type(right) is int else left * right
    if op == "/":
        if type(left) is int and type(right) is int:
            return _trunc_int_div(left, right)
        if right == 0.0:
            raise CompileError("REAL_DIVISION_BY_ZERO")
        return left / right
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
    raise CompileError(f"EVAL_UNSUPPORTED_OPERATOR:{op}")


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
        return _eval_binary(left, right, expr["op"])
    raise CompileError(f"EVAL_UNSUPPORTED:{expr}")


def _coerce_runtime_arg(value: Any, type_name_: str) -> Any:
    if type_name_ == "Int":
        if type(value) is not int or value < INT64_MIN or value > INT64_MAX:
            raise CompileError("INT_ARGUMENT_OUT_OF_RANGE_OR_TYPE")
        return value
    if type_name_ == "Real":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CompileError("REAL_ARGUMENT_TYPE")
        real_value = float(value)
        if not math.isfinite(real_value):
            raise CompileError("REAL_ARGUMENT_OUT_OF_RANGE")
        return real_value
    if type_name_ == "Bool":
        if type(value) is bool:
            return value
        if type(value) is int and value in (0, 1):
            return bool(value)
        raise CompileError("BOOL_ARGUMENT_TYPE")
    if type_name_ == "String":
        if not isinstance(value, str):
            raise CompileError("STRING_ARGUMENT_TYPE")
        return value
    raise CompileError(f"UNSUPPORTED_RUNTIME_TYPE:{type_name_}")


def eval_function(ir: dict, name: str, args: list[Any]) -> Any:
    functions = {f["name"]: f for f in ir["functions"]}
    if name not in functions:
        raise CompileError(f"UNDEFINED_FUNCTION:{name}")
    function = functions[name]
    if len(args) != len(function["params"]):
        raise CompileError(f"ARITY_MISMATCH:{name}")
    initial_values = [_coerce_runtime_arg(value, param["type"]) for value, param in zip(args, function["params"])]
    initial_env = dict(zip([p["name"] for p in function["params"]], initial_values))
    tasks: list[tuple] = [("eval", function["body"], initial_env)]
    values: list[Any] = []
    while tasks:
        task = tasks.pop()
        tag = task[0]
        if tag == "eval":
            expr, env = task[1], task[2]
            kind = expr["k"]
            if kind in ("num", "bool", "str"):
                values.append(expr["v"])
            elif kind == "name":
                values.append(env[expr["v"]])
            elif kind == "bin":
                tasks.append(("bin", expr["op"]))
                tasks.append(("eval", expr["r"], env))
                tasks.append(("eval", expr["l"], env))
            elif kind == "call":
                callee = functions[expr["f"]]
                tasks.append(("call", callee, len(expr["a"])))
                for arg in reversed(expr["a"]):
                    tasks.append(("eval", arg, env))
            else:
                raise CompileError(f"EVAL_UNSUPPORTED:{expr}")
        elif tag == "bin":
            right = values.pop()
            left = values.pop()
            values.append(_eval_binary(left, right, task[1]))
        elif tag == "call":
            callee, argc = task[1], task[2]
            call_values = values[-argc:] if argc else []
            if argc:
                del values[-argc:]
            next_env = dict(zip([p["name"] for p in callee["params"]], call_values))
            tasks.append(("eval", callee["body"], next_env))
        else:
            raise CompileError(f"EVAL_BAD_TASK:{tag}")
    if len(values) != 1:
        raise CompileError(f"EVAL_RESULT_STACK:{len(values)}")
    return values[0]


def c_type(type_name_: str) -> str:
    return {"Int": "int64_t", "Bool": "bool", "Real": "double", "String": "const char *"}[type_name_]


def c_var(name: str) -> str:
    return "ccv_" + name


def c_fn(name: str) -> str:
    return "ccf_" + name


def c_string_literal(value: str) -> str:
    if "\x00" in value:
        raise CompileError("C11_STRING_NUL_UNSUPPORTED")
    try:
        data = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CompileError("STRING_UTF8_INVALID_SCALAR") from exc
    return '"' + "".join(f"\\{byte:03o}" for byte in data) + '"'


def _render_c_expr(expr: dict, env: dict[str, str], signatures: dict[str, tuple[list[str], str]]) -> tuple[str, str, set[str]]:
    tasks: list[tuple] = [("eval", expr)]
    values: list[tuple[str, str, set[str]]] = []
    while tasks:
        task = tasks.pop()
        tag = task[0]
        if tag == "eval":
            current = task[1]
            kind = current["k"]
            if kind == "num":
                code = "INT64_MIN" if type(current["v"]) is int and current["v"] == INT64_MIN else repr(current["v"])
                values.append((code, "Real" if isinstance(current["v"], float) else "Int", set()))
            elif kind == "bool":
                values.append(("true" if current["v"] else "false", "Bool", set()))
            elif kind == "str":
                values.append((c_string_literal(current["v"]), "String", set()))
            elif kind == "name":
                if current["v"] not in env:
                    raise CompileError(f"UNDEFINED_VARIABLE:{current['v']}")
                values.append((c_var(current["v"]), env[current["v"]], set()))
            elif kind == "call":
                if current["f"] not in signatures:
                    raise CompileError(f"UNDEFINED_FUNCTION:{current['f']}")
                expected, return_type = signatures[current["f"]]
                tasks.append(("call", current["f"], expected, return_type, len(current["a"])))
                for arg in reversed(current["a"]):
                    tasks.append(("eval", arg))
            elif kind == "bin":
                tasks.append(("bin", current["op"]))
                tasks.append(("eval", current["r"]))
                tasks.append(("eval", current["l"]))
            else:
                raise CompileError(f"C_UNSUPPORTED:{kind}")
        elif tag == "call":
            name, expected, return_type, argc = task[1], task[2], task[3], task[4]
            args = values[-argc:] if argc else []
            if argc:
                del values[-argc:]
            actual = [item[1] for item in args]
            if len(expected) != argc:
                raise CompileError(f"ARITY_MISMATCH:{name}")
            if actual != expected:
                raise CompileError(f"ARG_TYPE_MISMATCH:{name}:{actual}!={expected}")
            helpers: set[str] = set()
            for _, _, item_helpers in args:
                helpers.update(item_helpers)
            values.append((f"{c_fn(name)}({','.join(item[0] for item in args)})", return_type, helpers))
        elif tag == "bin":
            right_code, right_type, right_helpers = values.pop()
            left_code, left_type, left_helpers = values.pop()
            op = task[1]
            result_type = _infer_binary_types(left_type, right_type, op)
            helpers = set(left_helpers) | set(right_helpers)
            if left_type == "String" and op in {"==", "!="}:
                cmp = "==" if op == "==" else "!="
                code = f"(strcmp({left_code},{right_code}) {cmp} 0)"
            elif result_type == "Int" and op in {"+", "-", "*", "/"}:
                helper = {"+": "cc_int_add", "-": "cc_int_sub", "*": "cc_int_mul", "/": "cc_int_div"}[op]
                helpers.add("int_" + {"+": "add", "-": "sub", "*": "mul", "/": "div"}[op])
                code = f"{helper}({left_code},{right_code})"
            elif result_type == "Real" and op == "/":
                helpers.add("real_div")
                code = f"cc_real_div({left_code},{right_code})"
            else:
                operator = {"or": "||", "iff": "==", "=>": "<="}.get(op, op)
                code = f"({left_code} {operator} {right_code})"
            values.append((code, result_type, helpers))
        else:
            raise CompileError(f"C_RENDER_BAD_TASK:{tag}")
    if len(values) != 1:
        raise CompileError(f"C_RENDER_RESULT_STACK:{len(values)}")
    return values[0]


def c_expr(expr: dict, env: dict[str, str], signatures: dict[str, tuple[list[str], str]]) -> str:
    return _render_c_expr(expr, env, signatures)[0]


def _entry_reachable_functions(ir: dict, entry: str | None) -> list[dict]:
    if entry is None:
        return list(ir["functions"])
    by_name = {f["name"]: f for f in ir["functions"]}
    if entry not in by_name:
        raise CompileError(f"UNDEFINED_ENTRY:{entry}")
    seen: set[str] = set()
    pending = [entry]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(sorted(_called_function_names(by_name[name]["body"]) - seen))
    return [f for f in ir["functions"] if f["name"] in seen]


def lower_c(ir: dict, entry: str | None = None) -> str:
    signatures = {f["name"]: ([p["type"] for p in f["params"]], f["return"]) for f in ir["functions"]}
    emitted_functions = _entry_reachable_functions(ir, entry)
    numeric_helpers: set[str] = set()
    rendered_bodies: dict[str, str] = {}
    for function in emitted_functions:
        env = {p["name"]: p["type"] for p in function["params"]}
        rendered, inferred_type, helpers = _render_c_expr(function["body"], env, signatures)
        if inferred_type != function["return"]:
            raise CompileError(f"RETURN_TYPE_MISMATCH:{function['name']}:{inferred_type}!={function['return']}")
        rendered_bodies[function["name"]] = rendered
        numeric_helpers.update(helpers)
    lines = [
        "#include <stdint.h>", "#include <stdbool.h>", "#include <stdio.h>", "#include <stdlib.h>", "#include <limits.h>",
        "#include <errno.h>", "#include <math.h>", "#include <string.h>", "",
    ]
    helper_lines = {
        "int_add": [
            "static int64_t cc_int_add(int64_t a,int64_t b){",
            "  if((b>0 && a>INT64_MAX-b)||(b<0 && a<INT64_MIN-b)){fputs(\"CC_INT_ADD_OVERFLOW\\n\",stderr);exit(67);}",
            "  return a+b;",
            "}", "",
        ],
        "int_sub": [
            "static int64_t cc_int_sub(int64_t a,int64_t b){",
            "  if((b<0 && a>INT64_MAX+b)||(b>0 && a<INT64_MIN+b)){fputs(\"CC_INT_SUB_OVERFLOW\\n\",stderr);exit(68);}",
            "  return a-b;",
            "}", "",
        ],
        "int_mul": [
            "static int64_t cc_int_mul(int64_t a,int64_t b){",
            "  if(a>0){",
            "    if((b>0 && a>INT64_MAX/b)||(b<0 && b<INT64_MIN/a)){fputs(\"CC_INT_MUL_OVERFLOW\\n\",stderr);exit(69);}",
            "  }else if(a<0){",
            "    if((b>0 && a<INT64_MIN/b)||(b<0 && b<INT64_MAX/a)){fputs(\"CC_INT_MUL_OVERFLOW\\n\",stderr);exit(69);}",
            "  }",
            "  return a*b;",
            "}", "",
        ],
        "int_div": [
            "static int64_t cc_int_div(int64_t a,int64_t b){",
            "  if(b==0){fputs(\"CC_INT_DIV_ZERO\\n\",stderr);exit(65);}",
            "  if(a==INT64_MIN && b==-1){fputs(\"CC_INT_DIV_OVERFLOW\\n\",stderr);exit(66);}",
            "  return a/b;",
            "}", "",
        ],
        "real_div": [
            "static double cc_real_div(double a,double b){",
            "  if(b==0.0){fputs(\"CC_REAL_DIV_ZERO\\n\",stderr);exit(73);}",
            "  return a/b;",
            "}", "",
        ],
    }
    for helper in ("int_add", "int_sub", "int_mul", "int_div", "real_div"):
        if helper in numeric_helpers:
            lines += helper_lines[helper]
    if entry:
        entry_function = next((f for f in ir["functions"] if f["name"] == entry), None)
        if not entry_function:
            raise CompileError(f"UNDEFINED_ENTRY:{entry}")
        entry_param_types = {p["type"] for p in entry_function["params"]}
        if "Int" in entry_param_types:
            lines += [
                "static int64_t cc_parse_int(const char*s){",
                "  errno=0; char*end=NULL; long long v=strtoll(s,&end,10);",
                "  if(errno==ERANGE||end==s||*end!='\\0'){fputs(\"CC_ARG_INT_INVALID\\n\",stderr);exit(70);}",
                "  return (int64_t)v;",
                "}", "",
            ]
        if "Real" in entry_param_types:
            lines += [
                "static double cc_parse_real(const char*s){",
                "  errno=0; char*end=NULL; double v=strtod(s,&end);",
                "  if(errno==ERANGE||end==s||*end!='\\0'||!isfinite(v)){fputs(\"CC_ARG_REAL_INVALID\\n\",stderr);exit(71);}",
                "  return v;",
                "}", "",
            ]
        if "Bool" in entry_param_types:
            lines += [
                "static bool cc_parse_bool(const char*s){",
                "  if(s[0]=='0'&&s[1]=='\\0') return false;",
                "  if(s[0]=='1'&&s[1]=='\\0') return true;",
                "  fputs(\"CC_ARG_BOOL_INVALID\\n\",stderr);exit(72);",
                "}", "",
            ]
    function_storage = "static " if entry else ""
    for function in emitted_functions:
        params = ", ".join(f"{c_type(p['type'])} {c_var(p['name'])}" for p in function["params"]) or "void"
        lines.append(f"{function_storage}{c_type(function['return'])} {c_fn(function['name'])}({params});")
    lines.append("")
    for function in emitted_functions:
        params = ", ".join(f"{c_type(p['type'])} {c_var(p['name'])}" for p in function["params"]) or "void"
        unused_marks = " ".join(f"(void){c_var(p['name'])};" for p in function["params"])
        prefix = (unused_marks + " ") if unused_marks else ""
        lines.append(f"{function_storage}{c_type(function['return'])} {c_fn(function['name'])}({params}) {{ {prefix}return {rendered_bodies[function['name']]}; }}")
    if entry:
        function = next((f for f in ir["functions"] if f["name"] == entry), None)
        if not function:
            raise CompileError(f"UNDEFINED_ENTRY:{entry}")
        if any(p["type"] not in ("Int", "Real", "Bool", "String") for p in function["params"]):
            raise CompileError("ENTRY_ARG_TYPE_UNSUPPORTED")
        args = []
        for index, param in enumerate(function["params"], 1):
            if param["type"] == "Int": args.append(f"cc_parse_int(argv[{index}])")
            elif param["type"] == "Real": args.append(f"cc_parse_real(argv[{index}])")
            elif param["type"] == "Bool": args.append(f"cc_parse_bool(argv[{index}])")
            else: args.append(f"argv[{index}]")
        return_type = function["return"]
        call = f"{c_fn(entry)}({','.join(args)})"
        fmt = {"Int": "%lld\\n", "Bool": "%d\\n", "Real": "%.17g\\n", "String": "%s\\n"}[return_type]
        cast = "(long long)" if return_type == "Int" else ""
        lines += [
            "", "int main(int argc,char**argv){",
            f"  if(argc!={len(function['params']) + 1}) return 64;",
            "  (void)argv;",
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