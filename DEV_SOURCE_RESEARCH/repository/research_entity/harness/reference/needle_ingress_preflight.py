from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from needle_runtime_contract import NeedleAdapterError, assert_complete_encoder_budget

SCHEMA_VERSION = "h1-needle-ingress-preflight-0.1"

@dataclass(frozen=True)
class NeedleIngressPreflight:
    schema_version: str
    normalized_intent_sha256: str
    toolset_sha256: str
    context_resolved: bool
    retrieval_mode: str
    retrieval_succeeded: bool
    selected_tool_count: int
    query_token_count: int
    tools_token_count: int
    max_enc_len: int
    min_headroom: int
    total_encoder_tokens: int | None
    needle_eligible: bool
    fallback_required: bool
    rejection_reasons: tuple[str, ...]


def _sha256_json(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def preflight_needle_ingress(
    normalized_intent: str,
    selected_tools: list[dict],
    *,
    context_resolved: bool,
    query_token_count: int,
    tools_token_count: int,
    max_enc_len: int = 1024,
    min_headroom: int = 200,
    retrieval_mode: str = "NONE",
    retrieval_succeeded: bool = True,
) -> NeedleIngressPreflight:
    reasons=[]
    if not isinstance(normalized_intent, str) or not normalized_intent.strip():
        reasons.append("EMPTY_NORMALIZED_INTENT")
    if not context_resolved:
        reasons.append("CONTEXT_NOT_RESOLVED")
    if not isinstance(selected_tools, list) or len(selected_tools) == 0:
        reasons.append("NO_SELECTED_TOOLS")
    if retrieval_mode != "NONE" and not retrieval_succeeded:
        reasons.append("RETRIEVAL_FAILED")
    total=None
    try:
        total=assert_complete_encoder_budget(query_token_count, tools_token_count, max_enc_len, min_headroom)
    except NeedleAdapterError as e:
        reasons.append("ENCODER_BUDGET:"+str(e))
    eligible=not reasons
    intent_hash=hashlib.sha256(normalized_intent.encode("utf-8")).hexdigest() if isinstance(normalized_intent,str) else hashlib.sha256(b"").hexdigest()
    toolset_hash=_sha256_json(selected_tools if isinstance(selected_tools,list) else [])
    return NeedleIngressPreflight(
        schema_version=SCHEMA_VERSION,
        normalized_intent_sha256=intent_hash,
        toolset_sha256=toolset_hash,
        context_resolved=bool(context_resolved),
        retrieval_mode=retrieval_mode,
        retrieval_succeeded=bool(retrieval_succeeded),
        selected_tool_count=len(selected_tools) if isinstance(selected_tools,list) else 0,
        query_token_count=int(query_token_count),
        tools_token_count=int(tools_token_count),
        max_enc_len=int(max_enc_len),
        min_headroom=int(min_headroom),
        total_encoder_tokens=total,
        needle_eligible=eligible,
        fallback_required=not eligible,
        rejection_reasons=tuple(reasons),
    )
