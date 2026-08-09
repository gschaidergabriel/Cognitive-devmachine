from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
PROJECTION_SCHEMA = "NeedleProjectionV1-flat"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_NAME = re.compile(r"[^a-zA-Z0-9_]+")


class BoundaryError(ValueError):
    pass


class ProjectionError(BoundaryError):
    pass


class DecodeRejected(BoundaryError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_name(name: str) -> str:
    value = SAFE_NAME.sub("_", name.strip()).strip("_").lower()
    value = re.sub(r"_+", "_", value)
    if not value:
        raise ProjectionError("capability name normalizes to empty")
    return value


def _pairs_no_duplicates(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise DecodeRejected(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def strict_json_loads(raw: str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_pairs_no_duplicates)
    except DecodeRejected:
        raise
    except Exception as exc:
        raise DecodeRejected(f"malformed JSON: {exc}") from exc


def _check_hex64(value: Any, field: str) -> None:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise ProjectionError(f"{field} must be lowercase sha256 hex")


def _validate_parameter_schema(schema: dict[str, Any], *, path: str = "parameters") -> None:
    if not isinstance(schema, dict):
        raise ProjectionError(f"{path} must be object")
    allowed_types = {"string", "integer", "number", "boolean", "object", "array"}
    for name, spec in schema.items():
        if not isinstance(name, str) or not name:
            raise ProjectionError(f"{path}: parameter name required")
        if not isinstance(spec, dict):
            raise ProjectionError(f"{path}.{name} must be object")
        t = spec.get("type")
        if t not in allowed_types:
            raise ProjectionError(f"{path}.{name}.type unsupported: {t!r}")
        unknown = set(spec) - {"type", "required", "enum", "minimum", "maximum", "items", "properties", "additionalProperties"}
        if unknown:
            raise ProjectionError(f"{path}.{name}: unknown schema keys: {sorted(unknown)}")
        if "enum" in spec and (not isinstance(spec["enum"], list) or not spec["enum"]):
            raise ProjectionError(f"{path}.{name}.enum must be non-empty list")
        if t == "array" and "items" in spec:
            item_spec = spec["items"]
            if not isinstance(item_spec, dict) or item_spec.get("type") not in allowed_types - {"object", "array"}:
                raise ProjectionError(f"{path}.{name}.items must have scalar type")
        if t == "object" and "properties" in spec:
            _validate_parameter_schema(spec["properties"], path=f"{path}.{name}.properties")


def _minimal_parameter_schema(schema: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in sorted(schema):
        spec = schema[key]
        item = {"type": spec["type"]}
        for field in ("required", "enum", "minimum", "maximum"):
            if field in spec:
                item[field] = spec[field]
        if spec["type"] == "array" and "items" in spec:
            item["items"] = {"type": spec["items"]["type"]}
        if spec["type"] == "object" and "properties" in spec:
            item["properties"] = _minimal_parameter_schema(spec["properties"])
            item["additionalProperties"] = bool(spec.get("additionalProperties", False))
        out[key] = item
    return out


def build_projection(capabilities: list[dict[str, Any]], *, source_commit: str) -> dict[str, Any]:
    """Build deterministic, fail-closed Clay -> historical Needle flat projection.

    Unavailable/locked capabilities are omitted before inference. Semantic identity is
    capability_id; normalized Needle names are only transport aliases.
    """
    if not isinstance(capabilities, list):
        raise ProjectionError("capabilities must be list")
    if not isinstance(source_commit, str) or len(source_commit) != 40 or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ProjectionError("source_commit must be lowercase 40-hex git commit")

    eligible: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    normalized_to_id: dict[str, str] = {}
    for raw in capabilities:
        if not isinstance(raw, dict):
            raise ProjectionError("capability entry must be object")
        cid = raw.get("capability_id")
        name = raw.get("name")
        if not isinstance(cid, str) or not cid:
            raise ProjectionError("capability_id required")
        if cid in seen_ids:
            raise ProjectionError(f"duplicate capability_id: {cid}")
        seen_ids.add(cid)
        if not isinstance(name, str) or not name:
            raise ProjectionError(f"{cid}: name required")
        available = raw.get("available", True)
        locked = raw.get("locked", False)
        if not isinstance(available, bool) or not isinstance(locked, bool):
            raise ProjectionError(f"{cid}: available/locked must be bool")
        if not available or locked:
            continue
        norm = normalize_name(name)
        prior = normalized_to_id.get(norm)
        if prior is not None and prior != cid:
            raise ProjectionError(f"normalization collision: {prior} and {cid} -> {norm}")
        normalized_to_id[norm] = cid
        params = raw.get("parameters", {})
        _validate_parameter_schema(params)
        eligible.append({
            "capability_id": cid,
            "needle_name": norm,
            "parameters": _minimal_parameter_schema(params),
        })

    eligible.sort(key=lambda x: (x["capability_id"], x["needle_name"]))
    semantic_registry = [
        {"capability_id": x["capability_id"], "needle_name": x["needle_name"], "parameters": x["parameters"]}
        for x in eligible
    ]
    registry_hash = sha256_obj(semantic_registry)
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_schema": PROJECTION_SCHEMA,
        "source_commit": source_commit,
        "registry_hash": registry_hash,
        "tools": [
            {"name": x["needle_name"], "parameters": x["parameters"]}
            for x in eligible
        ],
        "reverse_map": {x["needle_name"]: x["capability_id"] for x in eligible},
        "capability_schema": {x["capability_id"]: x["parameters"] for x in eligible},
    }


def _type_ok(value: Any, type_name: str) -> bool:
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    return False


def _validate_value(value: Any, spec: dict[str, Any], path: str) -> None:
    type_name = spec["type"]
    if not _type_ok(value, type_name):
        raise DecodeRejected(f"{path}: expected {type_name}")
    if "enum" in spec and value not in spec["enum"]:
        raise DecodeRejected(f"{path}: value not in enum")
    if type_name in {"integer", "number"}:
        if "minimum" in spec and value < spec["minimum"]:
            raise DecodeRejected(f"{path}: below minimum")
        if "maximum" in spec and value > spec["maximum"]:
            raise DecodeRejected(f"{path}: above maximum")
    if type_name == "array" and "items" in spec:
        for i, item in enumerate(value):
            _validate_value(item, spec["items"], f"{path}[{i}]")
    if type_name == "object" and "properties" in spec:
        props = spec["properties"]
        for key, child in props.items():
            if child.get("required") and key not in value:
                raise DecodeRejected(f"{path}.{key}: required")
        unknown = set(value) - set(props)
        if unknown and not spec.get("additionalProperties", False):
            raise DecodeRejected(f"{path}: unknown keys {sorted(unknown)}")
        for key in set(value) & set(props):
            _validate_value(value[key], props[key], f"{path}.{key}")


def validate_route(
    *,
    raw_json: str,
    projection: dict[str, Any],
    decoder_receipt: dict[str, Any],
    provenance: dict[str, Any],
    max_calls: int = 1,
) -> dict[str, Any]:
    """Validate untrusted Needle output and return non-authoritative Clay proposal envelope."""
    if max_calls != 1:
        raise ProjectionError("NeedleBoundaryV1 currently freezes max_calls=1")
    if decoder_receipt.get("constraint_exhausted") is True:
        raise DecodeRejected("decoder constraint exhaustion -> ABSTAIN")
    if decoder_receipt.get("off_trie") is True:
        raise DecodeRejected("decoder off-trie -> ABSTAIN")
    if decoder_receipt.get("status") not in {"OK", "CONSTRAINED_OK"}:
        raise DecodeRejected("decoder status not trustworthy -> ABSTAIN")

    expected_prov = {
        "source_commit": projection["source_commit"],
        "registry_hash": projection["registry_hash"],
        "projection_schema": projection["projection_schema"],
    }
    for key, expected in expected_prov.items():
        if provenance.get(key) != expected:
            raise DecodeRejected(f"provenance mismatch: {key}")
    for key in ("model_hash", "tokenizer_hash", "input_hash"):
        try:
            _check_hex64(provenance.get(key), key)
        except ProjectionError as exc:
            raise DecodeRejected(str(exc)) from exc
    if provenance.get("language_path") not in {"de_direct", "translated_to_en", "en_direct", "other_explicit"}:
        raise DecodeRejected("invalid language_path")

    decoded = strict_json_loads(raw_json)
    if not isinstance(decoded, dict):
        raise DecodeRejected("route must be JSON object")
    allowed_top = {"tool", "arguments"}
    unknown_top = set(decoded) - allowed_top
    if unknown_top:
        raise DecodeRejected(f"unknown route fields: {sorted(unknown_top)}")
    tool = decoded.get("tool")
    arguments = decoded.get("arguments")
    if not isinstance(tool, str) or not tool:
        raise DecodeRejected("tool required")
    if not isinstance(arguments, dict):
        raise DecodeRejected("arguments must be object")

    reverse = projection["reverse_map"]
    if tool not in reverse:
        raise DecodeRejected("unknown or unavailable projected tool")
    capability_id = reverse[tool]
    schema = projection["capability_schema"][capability_id]
    required = {k for k, spec in schema.items() if spec.get("required")}
    missing = required - set(arguments)
    if missing:
        raise DecodeRejected(f"missing required arguments: {sorted(missing)}")
    unknown = set(arguments) - set(schema)
    if unknown:
        raise DecodeRejected(f"unknown arguments: {sorted(unknown)}")
    for key, value in arguments.items():
        _validate_value(value, schema[key], f"arguments.{key}")

    route_semantics = {
        "capability_id": capability_id,
        "arguments": arguments,
        "registry_hash": projection["registry_hash"],
        "input_hash": provenance["input_hash"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "ClayToolProposal",
        "capability_id": capability_id,
        "arguments": arguments,
        "route_semantic_hash": sha256_obj(route_semantics),
        "provenance": {
            "source_commit": provenance["source_commit"],
            "model_hash": provenance["model_hash"],
            "tokenizer_hash": provenance["tokenizer_hash"],
            "registry_hash": provenance["registry_hash"],
            "projection_schema": provenance["projection_schema"],
            "input_hash": provenance["input_hash"],
            "language_path": provenance["language_path"],
        },
        "authority": "NONE",
        "effect_permit": None,
        "effect_commit_allowed": False,
        "next_boundary": "SAFE_EFFECT_CAPABILITY_OWNER_AUTHORITY_REVALIDATION",
    }
