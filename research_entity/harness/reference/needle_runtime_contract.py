from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Mapping, Iterable
import hashlib, json, re

AUTHORITY_NONE = "NONE"
SCHEMA_VERSION = "h1-needle-runtime-contract-0.2"

class NeedleAdapterError(ValueError):
    pass

def canonical_json(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha256_json(v: Any) -> str:
    return hashlib.sha256(canonical_json(v).encode("utf-8")).hexdigest()

def to_snake_case(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"_+", "_", s)
    return s.lower().strip("_")

@dataclass(frozen=True)
class AliasProfile:
    tool_aliases: Mapping[str, str]
    param_aliases: Mapping[str, Mapping[str, str]]

    def validate(self, source_tool_names: Iterable[str]) -> None:
        source = set(source_tool_names)
        unknown = set(self.tool_aliases) - source
        if unknown:
            raise NeedleAdapterError(f"tool aliases reference unknown source tools: {sorted(unknown)}")
        target_to_source: dict[str, str] = {}
        for src in source:
            tgt = self.tool_aliases.get(src, to_snake_case(src))
            if not tgt:
                raise NeedleAdapterError(f"empty normalized tool name for {src}")
            if tgt in target_to_source and target_to_source[tgt] != src:
                raise NeedleAdapterError(f"tool alias collision: {target_to_source[tgt]} and {src} -> {tgt}")
            target_to_source[tgt] = src
        for tool, aliases in self.param_aliases.items():
            if tool not in source:
                raise NeedleAdapterError(f"param alias references unknown tool: {tool}")
            rev: dict[str, str] = {}
            for src, tgt in aliases.items():
                if not tgt:
                    raise NeedleAdapterError(f"empty param alias: {tool}.{src}")
                if tgt in rev and rev[tgt] != src:
                    raise NeedleAdapterError(f"param alias collision: {tool}.{rev[tgt]} and {tool}.{src} -> {tgt}")
                rev[tgt] = src

    def needle_tool_name(self, frank_name: str) -> str:
        return self.tool_aliases.get(frank_name, to_snake_case(frank_name))

    def frank_tool_name(self, needle_name: str, source_tool_names: Iterable[str]) -> str | None:
        for src in source_tool_names:
            if self.needle_tool_name(src) == needle_name:
                return src
        return None

    def needle_param_name(self, frank_tool: str, frank_param: str) -> str:
        return self.param_aliases.get(frank_tool, {}).get(frank_param, frank_param)

    def frank_param_name(self, frank_tool: str, needle_param: str) -> str | None:
        aliases = self.param_aliases.get(frank_tool, {})
        for src, tgt in aliases.items():
            if tgt == needle_param:
                return src
        return needle_param

DEFAULT_ALIASES = AliasProfile(
    tool_aliases={"moeglichkeiten": "list_capabilities", "wissen": "search_knowledge"},
    param_aliases={"calc": {"ausdruck": "expression"}, "claude_code": {"auftrag": "task"}},
)

def _openai_properties(parameters: Any) -> tuple[dict[str, Any], set[str]]:
    """Return direct property map + required set from OpenAI/JSON-Schema or Needle-flat input."""
    if not isinstance(parameters, dict):
        raise NeedleAdapterError("parameters must be an object")
    if "properties" in parameters:
        props = parameters.get("properties")
        if not isinstance(props, dict):
            raise NeedleAdapterError("parameters.properties must be an object")
        required = parameters.get("required", [])
        if required is None:
            required = []
        if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
            raise NeedleAdapterError("parameters.required must be a string list")
        return dict(props), set(required)
    props = {}
    required = set()
    for k, spec in parameters.items():
        if not isinstance(k, str) or not isinstance(spec, dict):
            raise NeedleAdapterError("Needle-flat parameter map must contain object specs")
        props[k] = dict(spec)
        if spec.get("required") is True:
            required.add(k)
    return props, required

def canonicalize_tools(tools: list[dict[str, Any]], aliases: AliasProfile = DEFAULT_ALIASES) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Canonicalize schemas to the flat parameter map expected by Needle constrained.py."""
    names = [t.get("name") for t in tools if isinstance(t, dict) and isinstance(t.get("name"), str)]
    aliases.validate(names)
    out = []
    contract = {}
    seen = set()
    for tool in tools:
        if not isinstance(tool, dict):
            raise NeedleAdapterError("each tool must be an object")
        frank_name = tool.get("name")
        if not isinstance(frank_name, str) or not frank_name:
            raise NeedleAdapterError("tool.name must be non-empty")
        needle_name = aliases.needle_tool_name(frank_name)
        if needle_name in seen:
            raise NeedleAdapterError(f"duplicate Needle tool name: {needle_name}")
        seen.add(needle_name)
        props, required = _openai_properties(tool.get("parameters", {}))
        needle_props = {}
        reverse = {}
        needle_required = set()
        for p, spec in props.items():
            np = aliases.needle_param_name(frank_name, p)
            if np in reverse and reverse[np] != p:
                raise NeedleAdapterError(f"parameter alias collision in {frank_name}: {np}")
            reverse[np] = p
            nspec = dict(spec)
            if p in required:
                nspec["required"] = True
                needle_required.add(np)
            elif nspec.get("required") is True:
                needle_required.add(np)
            needle_props[np] = nspec
        nt = {"name": needle_name, "description": str(tool.get("description", "")), "parameters": needle_props}
        out.append(nt)
        contract[needle_name] = {"frank_name": frank_name, "params": needle_props, "reverse_param_map": reverse, "required": sorted(needle_required)}
    return out, contract

def assert_complete_encoder_budget(query_token_count: int, tools_token_count: int, max_enc_len: int = 1024, min_headroom: int = 0) -> int:
    total = int(query_token_count) + 1 + int(tools_token_count)
    if total + int(min_headroom) > int(max_enc_len):
        raise NeedleAdapterError(f"encoder budget exceeded: total={total}, headroom_required={min_headroom}, max={max_enc_len}")
    return total

def _type_ok(value: Any, spec: Mapping[str, Any]) -> bool:
    t = spec.get("type")
    if t is None:
        return True
    if isinstance(t, list):
        return any(_type_ok(value, {"type": one}) for one in t)
    if t == "string": return isinstance(value, str)
    if t == "integer": return isinstance(value, int) and not isinstance(value, bool)
    if t == "number": return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean": return isinstance(value, bool)
    if t == "object": return isinstance(value, dict)
    if t == "array": return isinstance(value, list)
    if t == "null": return value is None
    return True

@dataclass(frozen=True)
class NeedleDecisionReceipt:
    schema_version: str
    needle_id: str
    needle_version: str
    toolset_sha256: str
    raw_output_sha256: str
    outcome: str
    accepted: bool
    frank_calls: tuple[dict[str, Any], ...]
    rejection_reasons: tuple[str, ...]
    authority: str
    effect_eligible: bool
    effect_gate_required: bool
    preconstraint_margin: float | None = None
    preconstraint_entropy: float | None = None

def validate_output(raw_output: str, needle_tools: list[dict[str, Any]], contract: Mapping[str, Mapping[str, Any]], aliases: AliasProfile = DEFAULT_ALIASES, needle_id: str = "cactus-compute/needle", needle_version: str = "UNPINNED", preconstraint_margin: float | None = None, preconstraint_entropy: float | None = None) -> NeedleDecisionReceipt:
    reasons: list[str] = []
    calls_out: list[dict[str, Any]] = []
    toolset_hash = sha256_json(needle_tools)
    raw_hash = hashlib.sha256(raw_output.encode("utf-8")).hexdigest()
    try:
        decoded = json.loads(raw_output)
    except Exception as e:
        decoded = None
        reasons.append(f"JSON_PARSE:{type(e).__name__}")
    if decoded is not None and not isinstance(decoded, list):
        reasons.append("TOP_LEVEL_NOT_LIST")
    if isinstance(decoded, list):
        for i, call in enumerate(decoded):
            if not isinstance(call, dict):
                reasons.append(f"CALL_{i}_NOT_OBJECT"); continue
            if set(call) != {"name", "arguments"}:
                reasons.append(f"CALL_{i}_FIELDS_INVALID"); continue
            name, args = call.get("name"), call.get("arguments")
            if not isinstance(name, str) or name not in contract:
                reasons.append(f"CALL_{i}_UNAVAILABLE_TOOL"); continue
            if not isinstance(args, dict):
                reasons.append(f"CALL_{i}_ARGUMENTS_NOT_OBJECT"); continue
            tc = contract[name]
            specs, required = tc["params"], set(tc["required"])
            unknown, missing = set(args) - set(specs), required - set(args)
            if unknown: reasons.append(f"CALL_{i}_UNKNOWN_ARGS:{','.join(sorted(unknown))}")
            if missing: reasons.append(f"CALL_{i}_MISSING_REQUIRED:{','.join(sorted(missing))}")
            for key, value in args.items():
                if key in specs and not _type_ok(value, specs[key]): reasons.append(f"CALL_{i}_TYPE:{key}")
            if unknown or missing or any(r.startswith(f"CALL_{i}_TYPE:") for r in reasons): continue
            frank_name = tc["frank_name"]
            frank_args = {}
            for nk, v in args.items():
                fk = tc["reverse_param_map"].get(nk, aliases.frank_param_name(frank_name, nk))
                if fk is None:
                    reasons.append(f"CALL_{i}_REVERSE_ALIAS"); break
                frank_args[fk] = v
            else:
                calls_out.append({"name": frank_name, "arguments": frank_args})
    accepted = not reasons
    outcome = "NO_TOOL_PROPOSAL" if accepted and isinstance(decoded, list) and len(decoded) == 0 else ("ROUTE_PROPOSAL" if accepted else "REJECTED")
    return NeedleDecisionReceipt(schema_version=SCHEMA_VERSION, needle_id=needle_id, needle_version=needle_version, toolset_sha256=toolset_hash, raw_output_sha256=raw_hash, outcome=outcome, accepted=accepted, frank_calls=tuple(calls_out if accepted else []), rejection_reasons=tuple(reasons), authority=AUTHORITY_NONE, effect_eligible=False, effect_gate_required=True, preconstraint_margin=preconstraint_margin, preconstraint_entropy=preconstraint_entropy)
