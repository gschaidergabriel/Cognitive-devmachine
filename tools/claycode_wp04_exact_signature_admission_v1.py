#!/usr/bin/env python3
"""ClayCode WP04 research candidate: exact static callable-signature admission.

This module never imports or executes candidate runtime code. It parses pinned source bytes,
requires an explicit target->qualified-symbol mapping plus an explicit annotation->Clay type
map, and emits a non-executable CallContract candidate only when every identity/signature
condition is exact. Missing or ambiguous evidence fails closed.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from typing import Any

SCHEMA = "ClayCodeExactSignatureAdmission/v1-research"
DOMAIN = b"ClayCodeExactSignatureAdmission/v1-research\x00"
CONTRACT_DOMAIN = b"ClayCodeCallContract/v1-candidate\x00"
ALLOWED_EFFECT_CLASSES = {"PURE", "READ_STATE", "DERIVED_STATE", "RESEARCH_ONLY", "EXTERNAL_EFFECT"}


class SignatureAdmissionError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + stable_json(value)).hexdigest()


def source_sha256(source_text: str) -> str:
    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def annotation_text(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception as exc:  # pragma: no cover
        raise SignatureAdmissionError(f"annotation cannot be normalized: {exc}") from exc


@dataclass(frozen=True)
class CallableDecl:
    qualname: str
    lineno: int
    params: tuple[tuple[str, str], ...]
    returns: str
    is_async: bool


class _Collector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.decls: dict[str, list[CallableDecl]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        qualname = ".".join([*self.stack, node.name])
        args = node.args
        if args.vararg is not None or args.kwarg is not None or args.kwonlyargs:
            raise SignatureAdmissionError(f"{qualname}: variadic/keyword-only callable is not exact-arity admissible")
        if args.defaults or args.kw_defaults:
            raise SignatureAdmissionError(f"{qualname}: defaulted parameters are not exact-arity admissible")
        params: list[tuple[str, str]] = []
        for arg in [*args.posonlyargs, *args.args]:
            ann = annotation_text(arg.annotation)
            if ann is None:
                raise SignatureAdmissionError(f"{qualname}: parameter {arg.arg} lacks annotation")
            params.append((arg.arg, ann))
        returns = annotation_text(node.returns)
        if returns is None:
            raise SignatureAdmissionError(f"{qualname}: return annotation missing")
        self.decls.setdefault(qualname, []).append(CallableDecl(qualname, node.lineno, tuple(params), returns, is_async))
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, True)


def collect_callables(source_text: str) -> dict[str, list[CallableDecl]]:
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise SignatureAdmissionError(f"source parse failed: {exc.msg} at {exc.lineno}:{exc.offset}") from exc
    collector = _Collector()
    collector.visit(tree)
    return collector.decls


def _map_annotation(annotation: str, mapping: dict[str, str], *, where: str) -> str:
    clay = mapping.get(annotation)
    if not isinstance(clay, str) or not clay:
        raise SignatureAdmissionError(f"{where}: annotation {annotation!r} has no explicit Clay type mapping")
    return clay


def admit_exact_signature(*, source_text: str, request: dict[str, Any]) -> dict[str, Any]:
    required = {
        "target", "arity", "python_qualname", "implicit_receiver_count", "expected_source_sha256",
        "effect_class", "annotation_to_clay", "expected_params", "expected_return", "evidence_refs"
    }
    missing = sorted(required - request.keys())
    if missing:
        raise SignatureAdmissionError(f"request missing required keys: {missing}")

    target = request["target"]
    arity = request["arity"]
    qualname = request["python_qualname"]
    receiver_count = request["implicit_receiver_count"]
    effect_class = request["effect_class"]
    ann_map = request["annotation_to_clay"]
    expected_params = request["expected_params"]
    expected_return = request["expected_return"]
    evidence_refs = request["evidence_refs"]

    if not isinstance(target, str) or not target:
        raise SignatureAdmissionError("target must be non-empty exact symbol")
    if not isinstance(arity, int) or arity < 0:
        raise SignatureAdmissionError("arity must be non-negative int")
    if not isinstance(qualname, str) or not qualname:
        raise SignatureAdmissionError("python_qualname must be non-empty")
    if receiver_count not in (0, 1):
        raise SignatureAdmissionError("implicit_receiver_count must be 0 or 1")
    if effect_class not in ALLOWED_EFFECT_CLASSES:
        raise SignatureAdmissionError(f"invalid effect_class: {effect_class!r}")
    if not isinstance(ann_map, dict) or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in ann_map.items()):
        raise SignatureAdmissionError("annotation_to_clay must be explicit string->string mapping")
    if not isinstance(expected_params, list) or not all(isinstance(x, dict) and isinstance(x.get("name"), str) and isinstance(x.get("type_name"), str) for x in expected_params):
        raise SignatureAdmissionError("expected_params must explicitly declare Clay parameter names/types")
    if not isinstance(expected_return, str) or not expected_return:
        raise SignatureAdmissionError("expected_return must explicitly declare Clay return type")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(isinstance(x, str) and x for x in evidence_refs):
        raise SignatureAdmissionError("evidence_refs must be non-empty string list")

    observed_source_sha = source_sha256(source_text)
    if request["expected_source_sha256"] != observed_source_sha:
        raise SignatureAdmissionError("stale or wrong source bytes: SHA-256 mismatch")

    candidates = collect_callables(source_text).get(qualname, [])
    if not candidates:
        raise SignatureAdmissionError(f"exact qualified symbol not found: {qualname}")
    if len(candidates) != 1:
        raise SignatureAdmissionError(f"ambiguous qualified symbol: {qualname} has {len(candidates)} declarations")
    decl = candidates[0]

    if receiver_count > len(decl.params):
        raise SignatureAdmissionError("implicit receiver exceeds declared parameter count")
    visible_params = decl.params[receiver_count:]
    if len(visible_params) != arity:
        raise SignatureAdmissionError(
            f"exact arity mismatch: Clay {target}/{arity} vs static callable {qualname}/{len(visible_params)}"
        )

    mapped_params = [
        {"name": name, "type_name": _map_annotation(ann, ann_map, where=f"parameter {name}")}
        for name, ann in visible_params
    ]
    mapped_return = _map_annotation(decl.returns, ann_map, where="return")
    if mapped_params != expected_params:
        raise SignatureAdmissionError(f"runtime parameter contract mismatch: observed {mapped_params!r} expected {expected_params!r}")
    if mapped_return != expected_return:
        raise SignatureAdmissionError(f"runtime return contract mismatch: observed {mapped_return!r} expected {expected_return!r}")

    contract_core = {
        "identity": {"target": target, "arity": arity},
        "params": expected_params,
        "returns": expected_return,
        "effect_class": effect_class,
        "evidence_refs": sorted(set(evidence_refs)),
        "runtime_binding": None,
        "binding_authority": "NONE",
    }
    contract_hash = digest(CONTRACT_DOMAIN, contract_core)
    core = {
        "schema": SCHEMA,
        "source_sha256": observed_source_sha,
        "python_qualname": qualname,
        "python_lineno": decl.lineno,
        "python_async": decl.is_async,
        "implicit_receiver_count": receiver_count,
        "call_contract": contract_core,
        "contract_semantic_hash": contract_hash,
        "resolution_state": "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING",
        "execution_admitted": False,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "invariants": {
            "imports_candidate_runtime": "FORBIDDEN",
            "executes_candidate_runtime": "FORBIDDEN",
            "fuzzy_or_suffix_resolution": "FORBIDDEN",
            "caller_constraint_type_inference": "FORBIDDEN",
            "runtime_source_mints_clay_contract": "FORBIDDEN",
            "unmapped_annotation_inference": "FORBIDDEN",
            "source_hash_drift_admission": "FORBIDDEN",
            "contract_alone_admits_execution": "FORBIDDEN"
        }
    }
    return {**core, "admission_sha256": digest(DOMAIN, core), "promotion": "NONE"}
