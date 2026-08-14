#!/usr/bin/env python3
"""Effect/authority extension for the integrated ClayCode BASE compiler candidate.

Consumes the same V7 parser/function representation as tools/claycode_base_compiler.py,
then adds typed host signatures, transitive effect/capability closure, a host-rooted
Gateway, reference evaluation, Python lowering and translation-validation receipts.

This is executable integration evidence for CC-WP-03..08. It is not authority by itself,
not a package PASS, and not Andreas Ubuntu target acceptance.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from claycode_base_compiler import CompileError, _trunc_int_div, infer, parse_program, sha256

VERSION = "claycode-base-effect-pipeline-0.2"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"

HOST = {
    "host.fs_read": {"params": ["Int"], "result": "Int", "effect": "FS_READ", "cap": "cap.fs.read"},
    "host.fs_write": {"params": ["Int"], "result": "Int", "effect": "FS_WRITE", "cap": "cap.fs.write"},
    "host.db_put": {"params": ["Int"], "result": "Int", "effect": "DB_WRITE", "cap": "cap.db.write"},
    "host.http_send": {"params": ["Int"], "result": "Int", "effect": "HTTP", "cap": "cap.http"},
}


class CapabilityDenied(CompileError):
    pass


def walk(expr: dict):
    yield expr
    kind = expr.get("k")
    if kind == "bin":
        yield from walk(expr["l"])
        yield from walk(expr["r"])
    elif kind == "call":
        for arg in expr["a"]:
            yield from walk(arg)


def compile_effect_ir(program: dict) -> dict:
    functions = program["functions"]
    user_signatures = {f.name: ([p.type for p in f.params], f.return_type) for f in functions}
    signatures = dict(user_signatures)
    signatures.update({name: (spec["params"], spec["result"]) for name, spec in HOST.items()})
    allowed = {"Int", "Real", "Bool", "String"}

    direct: dict[str, dict[str, set[str]]] = {}
    for function in functions:
        if function.name.startswith("host."):
            raise CompileError(f"RESERVED_HOST_NAMESPACE:{function.name}")
        if function.return_type not in allowed or any(p.type not in allowed for p in function.params):
            raise CompileError(f"UNSUPPORTED_TYPE:{function.name}")
        actual = infer(function.body, {p.name: p.type for p in function.params}, signatures)
        if actual != function.return_type:
            raise CompileError(f"RETURN_TYPE_MISMATCH:{function.name}:{actual}!={function.return_type}")
        effects: set[str] = set()
        caps: set[str] = set()
        calls: set[str] = set()
        for node in walk(function.body):
            if node.get("k") != "call":
                continue
            callee = node["f"]
            if callee in HOST:
                effects.add(HOST[callee]["effect"])
                caps.add(HOST[callee]["cap"])
            elif callee in user_signatures:
                calls.add(callee)
            else:
                raise CompileError(f"UNDEFINED_FUNCTION:{callee}")
        direct[function.name] = {"effects": effects, "caps": caps, "calls": calls}

    closure = {name: {"effects": set(v["effects"]), "caps": set(v["caps"])} for name, v in direct.items()}
    changed = True
    rounds = 0
    while changed:
        rounds += 1
        if rounds > len(functions) + 1:
            raise CompileError("EFFECT_CLOSURE_NONCONVERGENCE")
        changed = False
        for name, row in direct.items():
            effects = set(row["effects"])
            caps = set(row["caps"])
            for callee in row["calls"]:
                effects |= closure[callee]["effects"]
                caps |= closure[callee]["caps"]
            if effects != closure[name]["effects"] or caps != closure[name]["caps"]:
                closure[name] = {"effects": effects, "caps": caps}
                changed = True

    ir = {"schema": "claycode.typed-effect-ir.v0", "functions": []}
    for function in sorted(functions, key=lambda f: f.name):
        ir["functions"].append({
            "name": function.name,
            "params": [{"name": p.name, "type": p.type} for p in function.params],
            "return": function.return_type,
            "body": function.body,
            "effect_summary": sorted(closure[function.name]["effects"]),
            "required_capabilities": sorted(closure[function.name]["caps"]),
        })
    return {"ir": ir, "effect_lfp_rounds": rounds}


class Gateway:
    """Opaque host-rooted authority boundary for deterministic test adapters."""
    def __init__(self, capabilities=()):
        self._caps = frozenset(capabilities)
        self.trace: list[list[Any]] = []

    def effect(self, effect: str, capability: str, value: int) -> int:
        if capability not in self._caps:
            raise CapabilityDenied(f"MISSING_CAPABILITY:{capability}")
        self.trace.append([effect, capability, value])
        if effect == "FS_READ": return value + 1000
        if effect == "FS_WRITE": return value
        if effect == "DB_WRITE": return value * 2
        if effect == "HTTP": return value + 7
        raise CompileError(f"UNKNOWN_HOST_EFFECT:{effect}")


def _functions(ir: dict) -> dict[str, dict]:
    return {f["name"]: f for f in ir["functions"]}


def eval_expr(expr: dict, env: dict[str, Any], functions: dict[str, dict], gw: Gateway, depth=0) -> Any:
    if depth > 256:
        raise CompileError("RECURSION_LIMIT")
    kind = expr["k"]
    if kind in {"num", "bool", "str"}: return expr["v"]
    if kind == "name": return env[expr["v"]]
    if kind == "call":
        values = [eval_expr(a, env, functions, gw, depth + 1) for a in expr["a"]]
        if expr["f"] in HOST:
            spec = HOST[expr["f"]]
            return gw.effect(spec["effect"], spec["cap"], values[0])
        fn = functions[expr["f"]]
        next_env = dict(zip([p["name"] for p in fn["params"]], values))
        return eval_expr(fn["body"], next_env, functions, gw, depth + 1)
    if kind == "bin":
        op = expr["op"]
        if op == "&&":
            return bool(eval_expr(expr["l"], env, functions, gw, depth)) and bool(eval_expr(expr["r"], env, functions, gw, depth))
        if op in {"||", "or"}:
            return bool(eval_expr(expr["l"], env, functions, gw, depth)) or bool(eval_expr(expr["r"], env, functions, gw, depth))
        left = eval_expr(expr["l"], env, functions, gw, depth)
        right = eval_expr(expr["r"], env, functions, gw, depth)
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/": return _trunc_int_div(left, right) if isinstance(left, int) and isinstance(right, int) else left / right
        if op == ">": return left > right
        if op == "<": return left < right
        if op == ">=": return left >= right
        if op == "<=": return left <= right
        if op == "==": return left == right
        if op == "!=": return left != right
        if op == "iff": return bool(left) == bool(right)
        if op == "=>": return (not bool(left)) or bool(right)
    raise CompileError(f"EVAL_UNSUPPORTED:{expr}")


def eval_function(ir: dict, name: str, args: list[Any], gw: Gateway) -> Any:
    functions = _functions(ir)
    if name not in functions:
        raise CompileError(f"UNDEFINED_FUNCTION:{name}")
    fn = functions[name]
    if len(args) != len(fn["params"]):
        raise CompileError(f"ARITY_MISMATCH:{name}")
    env = dict(zip([p["name"] for p in fn["params"]], args))
    return eval_expr(fn["body"], env, functions, gw)


def py_name(value: str) -> str:
    return value.replace(".", "_").replace("-", "_")


def py_expr(expr: dict, env: dict[str, str], signatures: dict[str, tuple[list[str], str]]) -> str:
    kind = expr["k"]
    if kind in {"num", "str"}: return repr(expr["v"])
    if kind == "bool": return "True" if expr["v"] else "False"
    if kind == "name": return py_name(expr["v"])
    if kind == "call":
        args = ",".join(py_expr(a, env, signatures) for a in expr["a"])
        if expr["f"] in HOST:
            spec = HOST[expr["f"]]
            return f"gw.effect({spec['effect']!r},{spec['cap']!r},{args})"
        suffix = ("," + args) if args else ""
        return f"fn_{py_name(expr['f'])}(gw{suffix})"
    if kind == "bin":
        left = py_expr(expr["l"], env, signatures)
        right = py_expr(expr["r"], env, signatures)
        if expr["op"] == "/" and infer(expr, env, signatures) == "Int":
            return f"_cc_int_div({left},{right})"
        op = {"&&": "and", "||": "or", "or": "or", "iff": "==", "=>": "<="}.get(expr["op"], expr["op"])
        return f"({left} {op} {right})"
    raise CompileError(f"LOWER_UNSUPPORTED:{kind}")


def lower_python(ir: dict) -> str:
    signatures = {f["name"]: ([p["type"] for p in f["params"]], f["return"]) for f in ir["functions"]}
    signatures.update({name: (spec["params"], spec["result"]) for name, spec in HOST.items()})
    lines = [
        f"# generated by {VERSION}",
        "def _cc_int_div(a,b):",
        "    if b == 0: raise ZeroDivisionError('DIVISION_BY_ZERO')",
        "    if a == -(1 << 63) and b == -1: raise OverflowError('INT_DIV_OVERFLOW')",
        "    q = abs(a) // abs(b)",
        "    return -q if (a < 0) != (b < 0) else q",
        "",
    ]
    for fn in ir["functions"]:
        params = ",".join(py_name(p["name"]) for p in fn["params"])
        suffix = ("," + params) if params else ""
        env = {p["name"]: p["type"] for p in fn["params"]}
        lines.append(f"def fn_{py_name(fn['name'])}(gw{suffix}):")
        lines.append("    return " + py_expr(fn["body"], env, signatures))
    return "\n".join(lines) + "\n"


def exec_lowered(code: str, entry: str, args: list[Any], gw: Gateway) -> Any:
    ns: dict[str, Any] = {}
    exec(compile(code, "<claycode-base-effect-lowered>", "exec"), ns, ns)
    fn = ns.get("fn_" + py_name(entry))
    if fn is None:
        raise CompileError(f"UNDEFINED_ENTRY:{entry}")
    return fn(gw, *args)


def build(source: str, grammar_text: str) -> dict:
    compiled = compile_effect_ir(parse_program(source, grammar_text))
    ir = compiled["ir"]
    semantic_bytes = json.dumps(ir, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    code = lower_python(ir)
    semantic_hash = sha256(semantic_bytes)
    artifact_hash = sha256(code.encode("utf-8"))
    return {
        "candidate_version": VERSION,
        "ir": ir,
        "semantic_hash": semantic_hash,
        "source_hash": sha256(source.encode("utf-8")),
        "grammar_hash": sha256(grammar_text.encode("utf-8")),
        "effect_lfp_rounds": compiled["effect_lfp_rounds"],
        "target": "python3",
        "artifact": code,
        "artifact_hash": artifact_hash,
        "translation_contract_hash": sha256(json.dumps({
            "candidate": VERSION,
            "semantic_hash": semantic_hash,
            "target": "python3",
            "artifact_hash": artifact_hash,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")),
    }


def translation_validate(source: str, grammar_text: str, entry: str, vectors: list[list[Any]], caps=()) -> dict:
    built = build(source, grammar_text)
    rows = []
    mismatches = 0
    trace_mismatches = 0
    for args in vectors:
        g1, g2 = Gateway(caps), Gateway(caps)
        expected = eval_function(built["ir"], entry, args, g1)
        observed = exec_lowered(built["artifact"], entry, args, g2)
        same = expected == observed
        trace_same = g1.trace == g2.trace
        mismatches += int(not same)
        trace_mismatches += int(not trace_same)
        rows.append({"args": args, "expected": expected, "observed": observed, "trace_hash": sha256(json.dumps(g1.trace).encode()), "same": same, "trace_same": trace_same})
    return {
        "candidate_version": VERSION,
        "semantic_hash": built["semantic_hash"],
        "artifact_hash": built["artifact_hash"],
        "translation_contract_hash": built["translation_contract_hash"],
        "vectors": len(rows),
        "output_mismatches": mismatches,
        "trace_mismatches": trace_mismatches,
        "pass": mismatches == 0 and trace_mismatches == 0,
        "rows": rows,
    }


def self_test(grammar_text: str) -> dict:
    source = """module app.effect_bridge
fn read(x:Int)->Int=host.fs_read(x)
fn store(x:Int)->Int=host.db_put(read(x))
fn mix(x:Int)->Int=store(x)+host.http_send(x)
fn main(x:Int)->Int=mix(x)+read(x)
"""
    formatted = """// presentation-only variant
module app.effect_bridge
fn read ( x : Int ) -> Int = host.fs_read ( x )
fn store(x:Int)->Int = host.db_put(read(x))
fn mix(x:Int)->Int = store(x) + host.http_send(x)
fn main(x:Int)->Int = mix(x) + read(x)
"""
    b1, b2 = build(source, grammar_text), build(formatted, grammar_text)
    if b1["semantic_hash"] != b2["semantic_hash"]:
        raise AssertionError("formatting changed semantic hash")
    main = next(f for f in b1["ir"]["functions"] if f["name"] == "main")
    if main["effect_summary"] != ["DB_WRITE", "FS_READ", "HTTP"]:
        raise AssertionError(main["effect_summary"])
    if main["required_capabilities"] != ["cap.db.write", "cap.fs.read", "cap.http"]:
        raise AssertionError(main["required_capabilities"])

    rng = random.Random(20260809)
    vectors = [[rng.randint(-100000, 100000)] for _ in range(10000)]
    tv = translation_validate(source, grammar_text, "main", vectors, {"cap.fs.read", "cap.db.write", "cap.http"})
    if not tv["pass"]:
        raise AssertionError("translation differential mismatch")

    div_source = """module app.division
fn main(a:Int,b:Int)->Int=a/b
"""
    div_vectors = [[9223372036854775807, 3], [9223372036854775807, -3], [-9223372036854775807, 3], [9007199254740993, 7], [-9007199254740993, 7]]
    div_tv = translation_validate(div_source, grammar_text, "main", div_vectors)
    if not div_tv["pass"]:
        raise AssertionError("effect lowering Int division mismatch")
    div_built = build(div_source, grammar_text)
    if "_cc_int_div" not in div_built["artifact"]:
        raise AssertionError("Int division did not lower through checked helper")
    div_zero_reference = div_zero_lowered = div_overflow_reference = div_overflow_lowered = False
    try: eval_function(div_built["ir"], "main", [1, 0], Gateway())
    except CompileError as exc: div_zero_reference = "DIVISION_BY_ZERO" in str(exc)
    try: exec_lowered(div_built["artifact"], "main", [1, 0], Gateway())
    except ZeroDivisionError as exc: div_zero_lowered = "DIVISION_BY_ZERO" in str(exc)
    try: eval_function(div_built["ir"], "main", [-(1 << 63), -1], Gateway())
    except CompileError as exc: div_overflow_reference = "INT_DIV_OVERFLOW" in str(exc)
    try: exec_lowered(div_built["artifact"], "main", [-(1 << 63), -1], Gateway())
    except OverflowError as exc: div_overflow_lowered = "INT_DIV_OVERFLOW" in str(exc)
    if not all((div_zero_reference, div_zero_lowered, div_overflow_reference, div_overflow_lowered)):
        raise AssertionError("checked Int division error boundary mismatch")

    missing_cap_rejected = False
    try:
        eval_function(b1["ir"], "main", [7], Gateway({"cap.fs.read", "cap.db.write"}))
    except CapabilityDenied:
        missing_cap_rejected = True
    if not missing_cap_rejected:
        raise AssertionError("missing HTTP capability accepted")

    textual = """module app.forge
fn cap(x:Int)->Int=x
fn main(x:Int)->Int=host.fs_read(cap(x))
"""
    forged = build(textual, grammar_text)
    textual_cap_rejected = False
    try:
        eval_function(forged["ir"], "main", [3], Gateway())
    except CapabilityDenied:
        textual_cap_rejected = True
    if not textual_cap_rejected:
        raise AssertionError("textual capability-like program data minted authority")

    recursive = """module app.rec
fn a(x:Int)->Int=b(x)
fn b(x:Int)->Int=a(host.http_send(x))
"""
    rb = build(recursive, grammar_text)
    rfa = next(f for f in rb["ir"]["functions"] if f["name"] == "a")
    rfb = next(f for f in rb["ir"]["functions"] if f["name"] == "b")
    recursive_closure = rfa["effect_summary"] == ["HTTP"] and rfb["effect_summary"] == ["HTTP"]
    if not recursive_closure:
        raise AssertionError("recursive effect closure failed")

    return {
        "schema_version": "1.1",
        "candidate_version": VERSION,
        "pass": True,
        "semantic_format_equivalence": True,
        "transitive_effect_closure": True,
        "recursive_effect_closure": True,
        "translation_vectors": tv["vectors"],
        "translation_output_mismatches": tv["output_mismatches"],
        "translation_trace_mismatches": tv["trace_mismatches"],
        "int_division_vectors": div_tv["vectors"],
        "int_division_output_mismatches": div_tv["output_mismatches"],
        "int_division_error_boundary_match": True,
        "missing_capability_rejected": missing_cap_rejected,
        "textual_capability_not_authority": textual_cap_rejected,
        "semantic_hash": b1["semantic_hash"],
        "artifact_hash": b1["artifact_hash"],
        "counts_as_work_package_pass": False,
        "counts_as_target_acceptance": False,
        "scope_guard": "Integrated BASE candidate evidence only. Real runtime adapters, opaque/sealed handles, cumulative budgets, async and Andreas Ubuntu application receipts remain separate gates.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?")
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()
    grammar_text = Path(args.grammar).read_text(encoding="utf-8")
    if args.self_test:
        out = self_test(grammar_text)
    else:
        if not args.source:
            ap.error("source required unless --self-test")
        source = Path(args.source).read_text(encoding="utf-8")
        out = build(source, grammar_text)
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()