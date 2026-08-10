#!/usr/bin/env python3
"""CC-WP-03 candidate: structural type declarations + typed runtime-state identity.

This layer extends the receipt-bound production TypedIR bridge without changing Clay syntax.
It lowers only closed `type Name = A|B|...` declarations into nominal sum types, parses
canonical field type spellings into structural type expressions, and provides deterministic
canonical typed-value/state identity.

Key laws implemented here:
- source/provenance identity is separate from semantic type/state identity;
- every record field participates in typed state-value identity;
- Epoch/Version/ResourceRef are explicitly reported as identity-sensitive components, so
  A->B->A with a changed epoch cannot collapse to the original state identity;
- Set is order-insensitive, Ordered/List are order-sensitive, Map keys are canonicalized,
  Option and Result retain their discriminator;
- CapabilityRef is descriptive data here and never bearer/effect authority;
- execution trace is outside the state-identity hash domain;
- arbitrary class expressions and control flow remain outside this WP03 lowerer.

Candidate only: no WP03/BASE promotion is implied by this module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as residual

IR_SCHEMA = "ClayCodeTypedIR/v2-state-identity-candidate"
IR_DOMAIN = b"ClayCodeTypedIR/v2-state-identity-candidate\x00"
TYPE_DOMAIN = b"ClayCodeTypeDefinition/v1\x00"
STATE_DOMAIN = b"ClayCodeTypedStateIdentity/v1\x00"

COLLECTION_ROLES = {
    "Set": "COLLECTION_SET_UNORDERED",
    "Ordered": "COLLECTION_ORDERED",
    "List": "COLLECTION_LIST",
    "Map": "COLLECTION_MAP",
}
CONSTRUCTOR_ROLES = {
    **COLLECTION_ROLES,
    "Result": "RESULT_DISCRIMINATED",
    "Option": "OPTIONAL_DISCRIMINATED",
    "Ref": "REFERENCE_CONSTRUCTOR",
    "Delta": "DELTA_CONSTRUCTOR",
}
NOMINAL_ROLES = {
    "Epoch": "VERSION_IDENTITY_COMPONENT",
    "Version": "VERSION_IDENTITY_COMPONENT",
    "ResourceRef": "RESOURCE_IDENTITY_COMPONENT",
    "CapabilityRef": "CAPABILITY_DESCRIPTOR_NON_BEARER",
    "Hash": "SEMANTIC_HASH_VALUE",
    "ReceiptRef": "RECEIPT_REFERENCE",
    "TraceRef": "EXECUTION_TRACE_REFERENCE",
    "EvidenceRef": "EVIDENCE_REFERENCE",
}
IDENTITY_COMPONENT_TYPES = {"Epoch", "Version", "ResourceRef"}
CAPABILITY_DESCRIPTOR_TYPES = {"CapabilityRef"}


class TypedIRV2Error(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class TypeCursor:
    text: str
    pos: int = 0


class TypeParser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def take(self, ch: str) -> bool:
        if self.text.startswith(ch, self.pos):
            self.pos += len(ch)
            return True
        return False

    def identifier(self) -> str:
        start = self.pos
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch.isalnum() or ch in "_.-":
                self.pos += 1
            else:
                break
        value = self.text[start:self.pos]
        if not value or not (value[0].isalpha() or value[0] == "_"):
            raise TypedIRV2Error(f"invalid type identifier at {start} in {self.text!r}")
        return value

    def atom(self) -> dict[str, Any]:
        name = self.identifier()
        args: list[dict[str, Any]] = []
        if self.take("<"):
            if self.peek() == ">":
                raise TypedIRV2Error(f"empty type argument list in {self.text!r}")
            while True:
                args.append(self.union())
                if self.take(","):
                    continue
                if not self.take(">"):
                    raise TypedIRV2Error(f"unterminated type arguments in {self.text!r}")
                break
        optional = self.take("?")
        return {"kind": "nominal", "name": name, "args": args, "optional": optional}

    def union(self) -> dict[str, Any]:
        members = [self.atom()]
        while self.take("|"):
            members.append(self.atom())
        if len(members) == 1:
            return members[0]
        return {"kind": "union", "members": members}

    def parse(self) -> dict[str, Any]:
        if not self.text:
            raise TypedIRV2Error("empty type expression")
        out = self.union()
        if self.pos != len(self.text):
            raise TypedIRV2Error(f"trailing type syntax {self.text[self.pos:]!r} in {self.text!r}")
        return out


def parse_type_expr(text: str) -> dict[str, Any]:
    return TypeParser(text).parse()


def type_names(expr: dict[str, Any]) -> set[str]:
    if expr.get("kind") == "union":
        out: set[str] = set()
        for member in expr.get("members", []):
            out |= type_names(member)
        return out
    if expr.get("kind") != "nominal":
        raise TypedIRV2Error(f"unknown structural type node {expr!r}")
    out = {expr["name"]}
    for arg in expr.get("args", []):
        out |= type_names(arg)
    return out


def _class_decl_keyword(ast: dict[str, Any]) -> str:
    vals = typed.token_values(ast)
    if not vals:
        raise TypedIRV2Error("class/type declaration without tokens")
    return vals[0]


def parse_closed_sum_type(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("kind") != "class_decl":
        return None
    ast = row.get("canonical_ast")
    if not isinstance(ast, dict):
        raise TypedIRV2Error("class_decl missing canonical AST")
    if _class_decl_keyword(ast) != "type":
        return None
    vals = typed.token_values(ast)
    name = typed.first_name(ast)
    try:
        eq = vals.index("=")
    except ValueError as exc:
        raise TypedIRV2Error(f"type declaration {name!r} missing '='") from exc
    rhs = vals[eq + 1 :]
    if not rhs:
        raise TypedIRV2Error(f"type declaration {name!r} has empty RHS")
    variants: list[str] = []
    expect_value = True
    for item in rhs:
        if expect_value:
            if item in typed.PUNCT or item in typed.KEYWORDS or not (item[0].isalpha() or item[0] == "_"):
                return None
            variants.append(item)
            expect_value = False
        else:
            if item != "|":
                return None
            expect_value = True
    if expect_value:
        raise TypedIRV2Error(f"type declaration {name!r} ends with '|'")
    if len(variants) < 2:
        return None
    if len(set(variants)) != len(variants):
        raise TypedIRV2Error(f"duplicate closed-sum variant in {name}: {variants!r}")
    core = {"kind": "sum_type", "name": name, "variants": variants, "authority": "NONE"}
    return {**core, "type_semantic_id": f"claytype:{sha256(TYPE_DOMAIN + stable_json(core))}"}


def _structural_record(decl: dict[str, Any]) -> dict[str, Any]:
    fields = []
    for field in decl.get("fields", []):
        expr = parse_type_expr(field["type"])
        names = type_names(expr)
        fields.append(
            {
                "name": field["name"],
                "type": field["type"],
                "type_expr": expr,
                "identity_component_types": sorted(names & IDENTITY_COMPONENT_TYPES),
                "capability_descriptor": bool(names & CAPABILITY_DESCRIPTOR_TYPES),
            }
        )
    core = {"kind": "record", "name": decl["name"], "fields": fields, "authority": "NONE"}
    return {**core, "type_semantic_id": f"claytype:{sha256(TYPE_DOMAIN + stable_json(core))}"}


def _type_roles(types: list[dict[str, Any]], sum_types: list[dict[str, Any]]) -> list[dict[str, str]]:
    sum_names = {x["name"] for x in sum_types}
    out = []
    for row in types:
        name = row["name"]
        if name in sum_names:
            role = "DECLARED_CLOSED_SUM_TYPE"
        elif name in CONSTRUCTOR_ROLES:
            role = CONSTRUCTOR_ROLES[name]
        elif name in NOMINAL_ROLES:
            role = NOMINAL_ROLES[name]
        else:
            role = "NOMINAL_OR_PRIMITIVE_VALUE"
        out.append({"name": name, "role": role, "authority": "NONE"})
    return sorted(out, key=lambda x: x["name"])


def build_typed_ir_v2(units: list[typed.SourceUnit]) -> dict[str, Any]:
    base = residual.build_typed_ir(units)
    sum_types: list[dict[str, Any]] = []
    remaining_opaque: list[dict[str, Any]] = []
    for row in base.get("opaque_unlowered_semantics", []):
        lowered = parse_closed_sum_type(row)
        if lowered is None:
            remaining_opaque.append(row)
        else:
            sum_types.append(lowered)

    seen = {d["name"] for d in base["declarations"]}
    for item in sum_types:
        if item["name"] in seen:
            raise TypedIRV2Error(f"duplicate declaration identity across typed IR: {item['name']!r}")
        seen.add(item["name"])
    sum_names = {x["name"] for x in sum_types}
    if len(sum_names) != len(sum_types):
        raise TypedIRV2Error("duplicate closed-sum type declaration")

    types_by_name = {row["name"]: dict(row) for row in base["types"]}
    for item in sum_types:
        types_by_name[item["name"]] = {"name": item["name"], "class": "DECLARED_SUM_TYPE"}
    types = sorted(types_by_name.values(), key=lambda x: x["name"])

    structural_records = [
        _structural_record(d) for d in base["declarations"] if d.get("kind") == "record"
    ]
    declarations = sorted(
        [*base["declarations"], *sum_types], key=lambda d: (d["kind"], d["name"])
    )
    semantic_core = {
        "schema_version": "2.0-candidate",
        "ir_schema": IR_SCHEMA,
        "types": types,
        "type_roles": _type_roles(types, sum_types),
        "declarations": declarations,
        "structural_records": sorted(structural_records, key=lambda x: x["name"]),
        "opaque_unlowered_semantics": remaining_opaque,
        "invariants": {
            **base["invariants"],
            "closed_sum_type_variants_are_unique": "REQUIRED",
            "typed_state_identity_includes_all_fields": "REQUIRED",
            "epoch_version_resource_identity_may_be_dropped": "FORBIDDEN",
            "execution_trace_in_state_identity": "FORBIDDEN",
            "capability_descriptor_mints_bearer_authority": "FORBIDDEN",
            "unknown_type_to_any": "FORBIDDEN",
        },
    }
    ir_hash = sha256(IR_DOMAIN + stable_json(semantic_core))
    return {
        **semantic_core,
        "sources": base["sources"],
        "typed_ir_sha256": ir_hash,
        "program_semantic_id": f"clayir-v2:{ir_hash}",
        "promotion": "NONE",
        "wp03_status": "OPEN",
    }


def _decl_maps(ir: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = {x["name"]: x for x in ir.get("structural_records", [])}
    sums = {x["name"]: x for x in ir.get("declarations", []) if x.get("kind") == "sum_type"}
    return records, sums


def _sort_unique(values: list[Any]) -> list[Any]:
    rows = sorted((stable_json(v), v) for v in values)
    out = []
    last: bytes | None = None
    for raw, value in rows:
        if raw != last:
            out.append(value)
            last = raw
    return out


def canonicalize_typed_value(
    ir: dict[str, Any], type_expr: dict[str, Any], value: Any, *, type_vars: dict[str, dict[str, Any]] | None = None
) -> Any:
    type_vars = type_vars or {}
    if type_expr.get("kind") == "union":
        successes = []
        for member in type_expr["members"]:
            try:
                successes.append(canonicalize_typed_value(ir, member, value, type_vars=type_vars))
            except TypedIRV2Error:
                pass
        if len(successes) != 1:
            raise TypedIRV2Error(f"union value matched {len(successes)} alternatives, expected exactly one")
        return {"union_value": successes[0]}
    if type_expr.get("kind") != "nominal":
        raise TypedIRV2Error(f"unsupported type expression {type_expr!r}")
    if type_expr.get("optional"):
        if value is None:
            return None
        inner = dict(type_expr)
        inner["optional"] = False
        return canonicalize_typed_value(ir, inner, value, type_vars=type_vars)

    name = type_expr["name"]
    args = type_expr.get("args", [])
    if name in type_vars:
        return canonicalize_typed_value(ir, type_vars[name], value, type_vars=type_vars)
    records, sums = _decl_maps(ir)
    if name in sums:
        if not isinstance(value, str) or value not in sums[name]["variants"]:
            raise TypedIRV2Error(f"invalid {name} variant: {value!r}")
        return value
    if name in records:
        if not isinstance(value, dict):
            raise TypedIRV2Error(f"record {name} requires object value")
        schema = records[name]
        allowed = {f["name"] for f in schema["fields"]}
        extra = set(value) - allowed
        if extra:
            raise TypedIRV2Error(f"record {name} has unknown fields: {sorted(extra)!r}")
        out = {}
        for field in schema["fields"]:
            fname = field["name"]
            fexpr = field["type_expr"]
            if fname not in value:
                if fexpr.get("kind") == "nominal" and fexpr.get("optional"):
                    raw = None
                else:
                    raise TypedIRV2Error(f"record {name} missing field {fname!r}")
            else:
                raw = value[fname]
            out[fname] = canonicalize_typed_value(ir, fexpr, raw, type_vars=type_vars)
        return out

    if name == "Set":
        if len(args) != 1 or not isinstance(value, (list, tuple, set)):
            raise TypedIRV2Error("Set<T> requires one type argument and sequence/set value")
        vals = [canonicalize_typed_value(ir, args[0], x, type_vars=type_vars) for x in value]
        return {"set": _sort_unique(vals)}
    if name in {"Ordered", "List"}:
        if len(args) != 1 or not isinstance(value, (list, tuple)):
            raise TypedIRV2Error(f"{name}<T> requires one type argument and ordered sequence")
        return {name.lower(): [canonicalize_typed_value(ir, args[0], x, type_vars=type_vars) for x in value]}
    if name == "Map":
        if len(args) != 2:
            raise TypedIRV2Error("Map<K,V> requires two type arguments")
        entries = list(value.items()) if isinstance(value, dict) else value
        if not isinstance(entries, list):
            raise TypedIRV2Error("Map<K,V> requires dict or pair list")
        rows = []
        for pair in entries:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise TypedIRV2Error("Map entry must be key/value pair")
            key = canonicalize_typed_value(ir, args[0], pair[0], type_vars=type_vars)
            val = canonicalize_typed_value(ir, args[1], pair[1], type_vars=type_vars)
            rows.append((stable_json(key), key, val))
        rows.sort(key=lambda x: x[0])
        for a, b in zip(rows, rows[1:]):
            if a[0] == b[0]:
                raise TypedIRV2Error("duplicate canonical Map key")
        return {"map": [[key, val] for _, key, val in rows]}
    if name == "Option":
        if len(args) != 1:
            raise TypedIRV2Error("Option<T> requires one type argument")
        if value is None:
            return {"none": True}
        return {"some": canonicalize_typed_value(ir, args[0], value, type_vars=type_vars)}
    if name == "Result":
        if len(args) != 2 or not isinstance(value, dict):
            raise TypedIRV2Error("Result<T,E> requires two type arguments and tagged object")
        keys = set(value)
        if keys == {"ok"}:
            return {"ok": canonicalize_typed_value(ir, args[0], value["ok"], type_vars=type_vars)}
        if keys == {"err"}:
            return {"err": canonicalize_typed_value(ir, args[1], value["err"], type_vars=type_vars)}
        raise TypedIRV2Error("Result value must contain exactly one of ok/err")

    if isinstance(value, (dict, list)):
        raise TypedIRV2Error(f"nominal scalar {name} cannot accept structured value without declaration")
    if name in {"Int"} and (not isinstance(value, int) or isinstance(value, bool)):
        raise TypedIRV2Error(f"{name} requires integer")
    if name in {"Bool", "Boolean"} and not isinstance(value, bool):
        raise TypedIRV2Error(f"{name} requires boolean")
    if name in {"Float", "Number"} and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise TypedIRV2Error(f"{name} requires numeric scalar")
    if name in {"String", "Bytes", "Symbol"} and not isinstance(value, str):
        raise TypedIRV2Error(f"{name} requires string scalar in canonical JSON form")
    return value


def typed_state_identity(ir: dict[str, Any], type_name: str, value: Any) -> dict[str, Any]:
    records, sums = _decl_maps(ir)
    if type_name not in records and type_name not in sums:
        raise TypedIRV2Error(f"state identity requires declared record/sum type, got {type_name!r}")
    if type_name in records:
        definition = records[type_name]
        type_expr = {"kind": "nominal", "name": type_name, "args": [], "optional": False}
    else:
        definition = sums[type_name]
        type_expr = {"kind": "nominal", "name": type_name, "args": [], "optional": False}
    canonical = canonicalize_typed_value(ir, type_expr, value)
    type_id = definition["type_semantic_id"]
    core = {"type_semantic_id": type_id, "canonical_typed_value": canonical}
    identity = sha256(STATE_DOMAIN + stable_json(core))
    identity_fields = []
    capability_fields = []
    if type_name in records:
        for field in records[type_name]["fields"]:
            if field["identity_component_types"]:
                identity_fields.append(
                    {"field": field["name"], "types": field["identity_component_types"]}
                )
            if field["capability_descriptor"]:
                capability_fields.append(field["name"])
    return {
        "type": type_name,
        "type_semantic_id": type_id,
        "state_identity_sha256": identity,
        "canonical_typed_value": canonical,
        "identity_sensitive_fields": identity_fields,
        "capability_descriptor_fields": capability_fields,
        "effect_authority": "NONE",
        "execution_trace_in_identity": False,
    }


def compile_sources(paths: list[Path], grammar_path: Path) -> dict[str, Any]:
    grammar = grammar_path.read_text(encoding="utf-8")
    units = []
    for path in paths:
        doc = typed.front.compile_frontend(path.read_text(encoding="utf-8"), grammar, strict=True)
        units.append(typed.SourceUnit(path, doc))
    first = build_typed_ir_v2(units)
    second = build_typed_ir_v2(units)
    if first["typed_ir_sha256"] != second["typed_ir_sha256"] or stable_json(first) != stable_json(second):
        raise TypedIRV2Error("TypedIR v2 is not deterministic")
    return first
