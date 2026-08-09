from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json, re

from .needle_runtime_contract import (
    NeedleAdapterError,
    canonical_json,
    canonicalize_tools,
    AliasProfile,
    DEFAULT_ALIASES,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class NeedleRuntimeIdentity:
    runtime_profile: str
    runtime_source_ref: str
    runtime_source_sha: str
    checkpoint_sha256: str
    tokenizer_sha256: str

    def validate(self) -> None:
        if self.runtime_profile not in {"JAX_PYTHON", "CACTUS_CPP"}:
            raise NeedleAdapterError(f"unknown runtime profile: {self.runtime_profile}")
        if not self.runtime_source_ref or not self.runtime_source_sha:
            raise NeedleAdapterError("runtime source identity required")
        for label, value in (
            ("checkpoint_sha256", self.checkpoint_sha256),
            ("tokenizer_sha256", self.tokenizer_sha256),
        ):
            if not _SHA256_RE.fullmatch(value):
                raise NeedleAdapterError(f"{label} must be a pinned lowercase SHA256")

    @property
    def identity_sha256(self) -> str:
        self.validate()
        return hashlib.sha256(canonical_json(asdict(self)).encode("utf-8")).hexdigest()


def _reject_cactus_unsafe_string(value: str, field: str) -> None:
    # Current Cactus parse_tools_json / schema-extraction helpers are string scanners.
    if '"' in value or "\\" in value:
        raise NeedleAdapterError(
            f"Cactus profile cannot safely represent escaped quote/backslash in {field}"
        )


def _cactus_property_spec(spec: dict[str, Any], field: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "type" in spec:
        t = spec["type"]
        if not isinstance(t, str) or t not in {
            "string",
            "integer",
            "number",
            "boolean",
            "object",
            "array",
        }:
            raise NeedleAdapterError(f"unsupported Cactus parameter type at {field}: {t!r}")
        out["type"] = t
    else:
        out["type"] = "string"
    if "description" in spec:
        d = str(spec["description"])
        _reject_cactus_unsafe_string(d, field + ".description")
        if "{" in d or "}" in d:
            raise NeedleAdapterError(f"Cactus profile rejects braces in {field}.description")
        out["description"] = d
    if "enum" in spec:
        enum = spec["enum"]
        if not isinstance(enum, list) or not all(isinstance(x, str) for x in enum):
            raise NeedleAdapterError(f"Cactus profile supports only string enums at {field}")
        for i, x in enumerate(enum):
            _reject_cactus_unsafe_string(x, f"{field}.enum[{i}]")
        out["enum"] = enum
    return out


def build_jax_tools_payload(
    source_tools: list[dict[str, Any]],
    aliases: AliasProfile = DEFAULT_ALIASES,
):
    needle_tools, contract = canonicalize_tools(source_tools, aliases)
    payload = canonical_json(needle_tools)
    return payload, needle_tools, contract


def build_cactus_tools_payload(
    source_tools: list[dict[str, Any]],
    aliases: AliasProfile = DEFAULT_ALIASES,
):
    needle_tools, contract = canonicalize_tools(source_tools, aliases)
    wrapped = []
    for tool in needle_tools:
        desc = tool.get("description", "")
        _reject_cactus_unsafe_string(desc, f"tool[{tool['name']}].description")
        properties = {}
        required = []
        for name, spec in tool.get("parameters", {}).items():
            properties[name] = _cactus_property_spec(
                spec, f"tool[{tool['name']}].parameters[{name}]"
            )
            if spec.get("required") is True:
                required.append(name)
        schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = sorted(required)
        wrapped.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": desc,
                    "parameters": schema,
                },
            }
        )
    # Compact form is intentional: current Cactus extraction searches exact no-space markers.
    payload = json.dumps(
        wrapped,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if '"properties" :' in payload or '"type": ' in payload or '"description": ' in payload:
        raise AssertionError("non-compact Cactus payload emitted")
    return payload, needle_tools, contract


def build_runtime_payload(
    profile: str,
    source_tools: list[dict[str, Any]],
    aliases: AliasProfile = DEFAULT_ALIASES,
):
    if profile == "JAX_PYTHON":
        return build_jax_tools_payload(source_tools, aliases)
    if profile == "CACTUS_CPP":
        return build_cactus_tools_payload(source_tools, aliases)
    raise NeedleAdapterError(f"unknown runtime profile: {profile}")
