#!/usr/bin/env python3
"""Generic structured ClayCode backend for the frozen BASE universal-core subset.

This backend is intentionally domain-neutral. It adds typed function blocks, let/if/for,
continue, deterministic mutable List/Map/Set values, canonical hashing and generic stable
sorting. It has no FRANK/ActiveAssembly primitive and no effect authority. Programs lower
to executable host code that may call only the audited generic builtin table below.

It exists to test whether the open H2 ActiveAssembly counterexample can be solved by
realizing already-frozen generic semantics rather than by inventing a FRANK-specific
escape hatch. Target promotion remains receipt-gated.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any

from lark import Lark, Transformer

VERSION = "claycode-structured-backend/0.1"

GRAMMAR = r'''
start: module_decl? fn_decl+
module_decl: "module" qid
fn_decl: "fn" NAME "(" [typed_params] ")" "->" type_expr block
typed_params: typed_param ("," typed_param)*
typed_param: NAME ":" type_expr
type_expr: NAME ["?"]
block: "{" stmt* "}"
?stmt: let_stmt | require_stmt | return_stmt | if_stmt | for_stmt | continue_stmt | expr_stmt
let_stmt: "let" NAME [":" type_expr] "=" expr ";"?
require_stmt: "require" expr ";"?
return_stmt: "return" expr ";"?
if_stmt: "if" expr block ["else" block]
for_stmt: "for" NAME "in" expr block
continue_stmt: "continue" ";"?
expr_stmt: expr ";"?
?expr: or_expr
?or_expr: and_expr (OR_OP and_expr)*
?and_expr: eq_expr (AND_OP eq_expr)*
?eq_expr: rel_expr (EQ_OP rel_expr)*
?rel_expr: add_expr (REL_OP add_expr)*
?add_expr: mul_expr (ADD_OP mul_expr)*
?mul_expr: unary (MUL_OP unary)*
?unary: NOT_OP unary -> unary_not
      | primary
?primary: call
        | qid -> var
        | STRING -> string
        | SIGNED_NUMBER -> number
        | "true" -> true
        | "false" -> false
        | "null" -> null
        | "(" expr ")"
call: qid "(" [call_args] ")"
call_args: expr ("," expr)*
qid: NAME ("." NAME)*
OR_OP: "||" | "or"
AND_OP: "&&" | "and"
EQ_OP: "==" | "!="
REL_OP: ">=" | "<=" | ">" | "<"
ADD_OP: "+" | "-"
MUL_OP: "*" | "/"
NOT_OP: "!"
NAME: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS
%ignore /\/\/[^\n]*/
'''

PARSER = Lark(GRAMMAR, parser="lalr", start="start")


class StructuredFault(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Expr:
    kind: str
    value: Any = None
    args: tuple[Any, ...] = ()


@dataclasses.dataclass(frozen=True)
class Stmt:
    kind: str
    name: str | None = None
    expr: Expr | None = None
    body: tuple[Any, ...] = ()
    alt: tuple[Any, ...] = ()


@dataclasses.dataclass(frozen=True)
class Function:
    name: str
    params: tuple[str, ...]
    param_types: tuple[str, ...]
    return_type: str
    body: tuple[Stmt, ...]


@dataclasses.dataclass(frozen=True)
class Program:
    module: str
    functions: tuple[Function, ...]


class Build(Transformer):
    def qid(self, xs):
        return ".".join(map(str, xs))

    def type_expr(self, xs):
        return str(xs[0]) + ("?" if len(xs) > 1 else "")

    def typed_param(self, xs):
        return str(xs[0]), str(xs[1])

    def typed_params(self, xs):
        return list(xs)

    def number(self, xs):
        raw = str(xs[0])
        return Expr("lit", float(raw) if any(c in raw for c in ".eE") else int(raw))

    def string(self, xs):
        return Expr("lit", json.loads(str(xs[0])))

    def true(self, _):
        return Expr("lit", True)

    def false(self, _):
        return Expr("lit", False)

    def null(self, _):
        return Expr("lit", None)

    def var(self, xs):
        return Expr("var", str(xs[0]))

    def call_args(self, xs):
        return list(xs)

    def call(self, xs):
        args = xs[1] if len(xs) > 1 and isinstance(xs[1], list) else []
        return Expr("call", str(xs[0]), tuple(args))

    @staticmethod
    def _fold(xs):
        if len(xs) == 1:
            return xs[0]
        left = xs[0]
        i = 1
        while i < len(xs):
            left = Expr("bin", str(xs[i]), (left, xs[i + 1]))
            i += 2
        return left

    or_expr = _fold
    and_expr = _fold
    eq_expr = _fold
    rel_expr = _fold
    add_expr = _fold
    mul_expr = _fold

    def unary_not(self, xs):
        return Expr("unary", "!", (xs[-1],))

    def let_stmt(self, xs):
        return Stmt("let", str(xs[0]), xs[-1])

    def require_stmt(self, xs):
        return Stmt("require", expr=xs[0])

    def return_stmt(self, xs):
        return Stmt("return", expr=xs[0])

    def expr_stmt(self, xs):
        return Stmt("expr", expr=xs[0])

    def continue_stmt(self, _):
        return Stmt("continue")

    def block(self, xs):
        return tuple(xs)

    def if_stmt(self, xs):
        return Stmt("if", expr=xs[0], body=xs[1], alt=(xs[2] if len(xs) > 2 else ()))

    def for_stmt(self, xs):
        return Stmt("for", name=str(xs[0]), expr=xs[1], body=xs[2])

    def fn_decl(self, xs):
        name = str(xs[0])
        idx = 1
        params: list[tuple[str, str]] = []
        if idx < len(xs) and isinstance(xs[idx], list):
            params = xs[idx]
            idx += 1
        return Function(
            name=name,
            params=tuple(p[0] for p in params),
            param_types=tuple(p[1] for p in params),
            return_type=str(xs[idx]),
            body=xs[idx + 1],
        )

    def module_decl(self, xs):
        return ("module", str(xs[0]))

    def start(self, xs):
        module = "anonymous"
        funcs: list[Function] = []
        for item in xs:
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "module":
                module = item[1]
            elif isinstance(item, Function):
                funcs.append(item)
        return Program(module, tuple(funcs))


def parse(source: str) -> Program:
    return Build().transform(PARSER.parse(source))


def _expr_obj(e: Expr) -> dict[str, Any]:
    return {"kind": e.kind, "value": e.value, "args": [_expr_obj(x) for x in e.args]}


def _stmt_obj(s: Stmt) -> dict[str, Any]:
    return {
        "kind": s.kind,
        "name": s.name,
        "expr": _expr_obj(s.expr) if s.expr else None,
        "body": [_stmt_obj(x) for x in s.body],
        "alt": [_stmt_obj(x) for x in s.alt],
    }


def canonical_ir(program: Program) -> tuple[dict[str, Any], str]:
    obj = {
        "schema": "claycode.structured-ir.v1",
        "module": program.module,
        "functions": [
            {
                "name": f.name,
                "params": list(zip(f.params, f.param_types)),
                "return_type": f.return_type,
                "body": [_stmt_obj(s) for s in f.body],
            }
            for f in program.functions
        ],
    }
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return obj, hashlib.sha256(raw).hexdigest()


def _get(value: Any, field: str) -> Any:
    if isinstance(value, dict):
        return value[field]
    return getattr(value, field)


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _sort_by(values: list[Any], *spec: Any) -> list[Any]:
    if len(spec) == 0 or len(spec) % 2:
        raise StructuredFault("SORT_SPEC_INVALID")
    out = list(values)
    pairs = [(str(spec[i]), str(spec[i + 1])) for i in range(0, len(spec), 2)]
    for field, direction in reversed(pairs):
        if direction not in {"asc", "desc"}:
            raise StructuredFault("SORT_DIRECTION_INVALID")
        out.sort(key=lambda x, f=field: _get(x, f), reverse=direction == "desc")
    return out


def _trunc_div(left: int, right: int) -> int:
    if right == 0:
        raise StructuredFault("DIVISION_BY_ZERO")
    q = abs(left) // abs(right)
    return -q if (left < 0) != (right < 0) else q


class Runtime:
    """Domain-neutral builtin surface. No builtin name or implementation mentions FRANK."""

    def __init__(self):
        self.trace: list[str] = []
        self.builtins = {
            "list_new": lambda: [],
            "map_new": lambda: {},
            "set_new": lambda: set(),
            "list_len": lambda x: len(x),
            "list_push": self._list_push,
            "list_push_unique_by": self._list_push_unique_by,
            "map_has": lambda m, k: k in m,
            "map_get": lambda m, k: m[k],
            "map_get_default": lambda m, k, d: m.get(k, d),
            "map_set": self._map_set,
            "map_setdefault": self._map_setdefault,
            "map_inc": self._map_inc,
            "map_with": self._map_with,
            "map_without": self._map_without,
            "set_has": lambda s, x: x in s,
            "set_add": self._set_add,
            "set_values": lambda s: list(s),
            "sort_by": _sort_by,
            "sort_scalar": lambda x: sorted(x),
            "pair": lambda a, b: (a, b),
            "pair_first": lambda p: p[0],
            "pair_second": lambda p: p[1],
            "canonical_sha256": _canonical_sha256,
            "round12": lambda x: round(float(x), 12),
            "concat": lambda *xs: "".join(str(x) for x in xs),
            "fail": self._fail,
        }

    @staticmethod
    def _list_push(seq, value):
        seq.append(value)
        return value

    @staticmethod
    def _list_push_unique_by(seq, value, field):
        target = _get(value, str(field))
        if not any(_get(x, str(field)) == target for x in seq):
            seq.append(value)
        return value

    @staticmethod
    def _map_set(m, k, v):
        m[k] = v
        return v

    @staticmethod
    def _map_setdefault(m, k, v):
        return m.setdefault(k, v)

    @staticmethod
    def _map_inc(m, k, amount):
        m[k] = m.get(k, 0) + amount
        return m[k]

    @staticmethod
    def _map_with(m, k, v):
        out = dict(m)
        out[k] = v
        return out

    @staticmethod
    def _map_without(m, k):
        return {a: b for a, b in m.items() if a != k}

    @staticmethod
    def _set_add(s, value):
        s.add(value)
        return value

    @staticmethod
    def _fail(message):
        raise StructuredFault(str(message))

    def get(self, value, field):
        return _get(value, field)

    def call_builtin(self, name: str, args: list[Any]) -> Any:
        fn = self.builtins.get(name)
        if fn is None:
            raise StructuredFault("UNKNOWN_BUILTIN:" + name)
        self.trace.append(name)
        return fn(*args)

    @staticmethod
    def require(value: Any):
        if not value:
            raise StructuredFault("REQUIRE_FAILED")


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class _Continue(Exception):
    pass


def _lookup(env: dict[str, Any], name: str) -> Any:
    parts = name.split(".")
    if parts[0] not in env:
        raise StructuredFault("UNKNOWN_VARIABLE:" + parts[0])
    value = env[parts[0]]
    for field in parts[1:]:
        value = _get(value, field)
    return value


def _eval_expr(expr: Expr, env: dict[str, Any], funcs: dict[str, Function], rt: Runtime, depth: int = 0) -> Any:
    if depth > 512:
        raise StructuredFault("RECURSION_LIMIT")
    if expr.kind == "lit":
        return expr.value
    if expr.kind == "var":
        return _lookup(env, str(expr.value))
    if expr.kind == "unary":
        value = _eval_expr(expr.args[0], env, funcs, rt, depth + 1)
        if expr.value == "!":
            return not bool(value)
        raise StructuredFault("UNKNOWN_UNARY:" + str(expr.value))
    if expr.kind == "call":
        args = [_eval_expr(x, env, funcs, rt, depth + 1) for x in expr.args]
        if expr.value in funcs:
            return _run_function(funcs[str(expr.value)], args, funcs, rt, depth + 1)
        return rt.call_builtin(str(expr.value), args)
    if expr.kind == "bin":
        op = str(expr.value)
        if op in {"&&", "and"}:
            left = _eval_expr(expr.args[0], env, funcs, rt, depth + 1)
            return bool(left) and bool(_eval_expr(expr.args[1], env, funcs, rt, depth + 1))
        if op in {"||", "or"}:
            left = _eval_expr(expr.args[0], env, funcs, rt, depth + 1)
            return bool(left) or bool(_eval_expr(expr.args[1], env, funcs, rt, depth + 1))
        left = _eval_expr(expr.args[0], env, funcs, rt, depth + 1)
        right = _eval_expr(expr.args[1], env, funcs, rt, depth + 1)
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/": return _trunc_div(left, right) if isinstance(left, int) and isinstance(right, int) else left / right
        if op == "==": return left == right
        if op == "!=": return left != right
        if op == ">": return left > right
        if op == "<": return left < right
        if op == ">=": return left >= right
        if op == "<=": return left <= right
        raise StructuredFault("UNKNOWN_BINARY:" + op)
    raise StructuredFault("UNKNOWN_EXPR:" + expr.kind)


def _exec_block(stmts: tuple[Stmt, ...], env: dict[str, Any], funcs: dict[str, Function], rt: Runtime, depth: int) -> None:
    for stmt in stmts:
        if stmt.kind == "let":
            env[str(stmt.name)] = _eval_expr(stmt.expr, env, funcs, rt, depth + 1)
        elif stmt.kind == "require":
            rt.require(_eval_expr(stmt.expr, env, funcs, rt, depth + 1))
        elif stmt.kind == "return":
            raise _Return(_eval_expr(stmt.expr, env, funcs, rt, depth + 1))
        elif stmt.kind == "expr":
            _eval_expr(stmt.expr, env, funcs, rt, depth + 1)
        elif stmt.kind == "continue":
            raise _Continue()
        elif stmt.kind == "if":
            branch = stmt.body if _eval_expr(stmt.expr, env, funcs, rt, depth + 1) else stmt.alt
            _exec_block(branch, env, funcs, rt, depth + 1)
        elif stmt.kind == "for":
            values = _eval_expr(stmt.expr, env, funcs, rt, depth + 1)
            for value in list(values):
                env[str(stmt.name)] = value
                try:
                    _exec_block(stmt.body, env, funcs, rt, depth + 1)
                except _Continue:
                    continue
        else:
            raise StructuredFault("UNKNOWN_STMT:" + stmt.kind)


def _run_function(fn: Function, args: list[Any], funcs: dict[str, Function], rt: Runtime, depth: int = 0) -> Any:
    if len(args) != len(fn.params):
        raise StructuredFault(f"ARITY:{fn.name}:{len(args)}!={len(fn.params)}")
    env = dict(zip(fn.params, args))
    try:
        _exec_block(fn.body, env, funcs, rt, depth + 1)
    except _Return as ret:
        return ret.value
    raise StructuredFault("FUNCTION_DID_NOT_RETURN:" + fn.name)


def execute(program: Program, entry: str, args: list[Any], runtime: Runtime | None = None) -> tuple[Any, Runtime]:
    funcs = {f.name: f for f in program.functions}
    if entry not in funcs:
        raise StructuredFault("ENTRY_NOT_FOUND:" + entry)
    rt = runtime or Runtime()
    return _run_function(funcs[entry], args, funcs, rt), rt


def _walk_expr(e: Expr):
    yield e
    for child in e.args:
        yield from _walk_expr(child)


def _walk_stmt(s: Stmt):
    if s.expr:
        yield from _walk_expr(s.expr)
    for child in s.body:
        yield from _walk_stmt(child)
    for child in s.alt:
        yield from _walk_stmt(child)


def validate(program: Program) -> dict[str, Any]:
    names = [f.name for f in program.functions]
    errors: list[str] = []
    if len(names) != len(set(names)):
        errors.append("DUPLICATE_FUNCTION")
    builtin_names = set(Runtime().builtins)
    function_names = set(names)
    calls: set[str] = set()
    for fn in program.functions:
        if len(fn.params) != len(set(fn.params)):
            errors.append("DUPLICATE_PARAM:" + fn.name)
        for stmt in fn.body:
            for expr in _walk_stmt(stmt):
                if expr.kind == "call":
                    calls.add(str(expr.value))
                    if expr.value not in function_names and expr.value not in builtin_names:
                        errors.append("UNKNOWN_CALL:" + str(expr.value))
    return {
        "pass": not errors,
        "errors": sorted(set(errors)),
        "function_count": len(program.functions),
        "calls": sorted(calls),
        "generic_builtin_calls": sorted(calls & builtin_names),
        "source_function_calls": sorted(calls & function_names),
        "effect_authority_surface": [],
    }


class LowerPython:
    def __init__(self, program: Program):
        self.function_names = {f.name for f in program.functions}

    def expr(self, e: Expr) -> str:
        if e.kind == "lit":
            return repr(e.value)
        if e.kind == "var":
            parts = str(e.value).split(".")
            code = parts[0]
            for field in parts[1:]:
                code = f"rt.get({code},{field!r})"
            return code
        if e.kind == "unary":
            return f"(not bool({self.expr(e.args[0])}))"
        if e.kind == "call":
            args = ", ".join(self.expr(x) for x in e.args)
            if e.value in self.function_names:
                return f"{e.value}(rt{', ' if args else ''}{args})"
            return f"rt.call_builtin({str(e.value)!r}, [{args}])"
        if e.kind == "bin":
            op = str(e.value)
            left, right = self.expr(e.args[0]), self.expr(e.args[1])
            if op in {"&&", "and"}: return f"(bool({left}) and bool({right}))"
            if op in {"||", "or"}: return f"(bool({left}) or bool({right}))"
            if op == "/": return f"rt.div({left}, {right})"
            return f"({left} {op} {right})"
        raise StructuredFault("LOWER_EXPR:" + e.kind)

    def stmts(self, stmts: tuple[Stmt, ...], indent: int = 1) -> list[str]:
        p = "    " * indent
        out: list[str] = []
        for s in stmts:
            if s.kind == "let": out.append(f"{p}{s.name} = {self.expr(s.expr)}")
            elif s.kind == "require": out.append(f"{p}rt.require({self.expr(s.expr)})")
            elif s.kind == "return": out.append(f"{p}return {self.expr(s.expr)}")
            elif s.kind == "expr": out.append(f"{p}{self.expr(s.expr)}")
            elif s.kind == "continue": out.append(f"{p}continue")
            elif s.kind == "if":
                out.append(f"{p}if {self.expr(s.expr)}:")
                out.extend(self.stmts(s.body, indent + 1) or [p + "    pass"])
                if s.alt:
                    out.append(f"{p}else:")
                    out.extend(self.stmts(s.alt, indent + 1) or [p + "    pass"])
            elif s.kind == "for":
                out.append(f"{p}for {s.name} in list({self.expr(s.expr)}):")
                out.extend(self.stmts(s.body, indent + 1) or [p + "    pass"])
            else: raise StructuredFault("LOWER_STMT:" + s.kind)
        return out

    def program(self, program: Program) -> str:
        chunks = ["# generated by " + VERSION]
        for fn in program.functions:
            sig = ", ".join(fn.params)
            chunks.append(f"def {fn.name}(rt{', ' if sig else ''}{sig}):")
            chunks.extend(self.stmts(fn.body) or ["    pass"])
            chunks.append("")
        return "\n".join(chunks)


def lower_python(program: Program) -> tuple[str, str]:
    source = LowerPython(program).program(program)
    return source, hashlib.sha256(source.encode()).hexdigest()


def execute_lowered(program: Program, entry: str, args: list[Any], runtime: Runtime | None = None) -> tuple[Any, Runtime, str]:
    source, artifact_hash = lower_python(program)
    namespace: dict[str, Any] = {}
    exec(compile(source, "<claycode-structured-lowered>", "exec"), namespace, namespace)
    rt = runtime or Runtime()
    if entry not in namespace:
        raise StructuredFault("LOWERED_ENTRY_NOT_FOUND:" + entry)
    return namespace[entry](rt, *args), rt, artifact_hash


# Lowered code routes integer division through this method so interpreter/backend agree.
Runtime.div = staticmethod(lambda left, right: _trunc_div(left, right) if isinstance(left, int) and isinstance(right, int) else left / right)


def compile_source(source: str) -> dict[str, Any]:
    program = parse(source)
    validation = validate(program)
    if not validation["pass"]:
        raise StructuredFault("VALIDATION:" + json.dumps(validation["errors"]))
    ir, semantic_hash = canonical_ir(program)
    lowered, artifact_hash = lower_python(program)
    return {
        "program": program,
        "ir": ir,
        "semantic_hash": semantic_hash,
        "lowered_source": lowered,
        "artifact_hash": artifact_hash,
        "validation": validation,
        "backend_version": VERSION,
    }


__all__ = [
    "VERSION", "StructuredFault", "Runtime", "Program", "parse", "validate",
    "canonical_ir", "compile_source", "execute", "lower_python", "execute_lowered",
]
