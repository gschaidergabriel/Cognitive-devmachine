from __future__ import annotations

import hashlib
import json
from typing import Any

from .adapters import MistralInference
from .engine import ClayVerseEngine
from .entityos_bridge import EntityOSBridge
from .store import UnifiedDB


def _bounded_string(value: Any, name: str, *, max_length: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or "\x00" in value:
        raise RuntimeError(f"invalid {name}")
    return value


def _mistral_receipt_from_assistant(db: UnifiedDB, assistant_turn_id: str) -> tuple[dict[str, Any], str, int]:
    row = db.db.execute(
        "SELECT content,provenance FROM turns WHERE turn_id=? AND role='assistant'",
        (assistant_turn_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("acceptance probe assistant turn is missing")

    try:
        provenance = json.loads(row["provenance"])
    except json.JSONDecodeError as exc:
        raise RuntimeError("acceptance probe assistant provenance is invalid") from exc
    if not isinstance(provenance, dict) or provenance.get("phase") != "pre-effect-reingest":
        raise RuntimeError("Mistral response was not re-ingested before effect admission")

    receipt = provenance.get("inference_receipt")
    if not isinstance(receipt, dict) or receipt.get("provider") != "mistral":
        raise RuntimeError("canonical Mistral inference receipt is missing")

    # Revalidate the non-secret receipt before serialising it outside the product.
    expected_keys = {
        "provider",
        "model_requested",
        "model_returned",
        "response_id",
        "finish_reason",
        "request_sha256",
        "response_sha256",
    }
    if set(receipt) != expected_keys:
        raise RuntimeError("canonical Mistral inference receipt has unexpected fields")
    _bounded_string(receipt["model_requested"], "Mistral requested model", max_length=256)
    _bounded_string(receipt["model_returned"], "Mistral returned model", max_length=256)
    _bounded_string(receipt["response_id"], "Mistral response id", max_length=512)
    if receipt["finish_reason"] != "stop":
        raise RuntimeError("canonical Mistral inference receipt is not a complete response")
    for name in ("request_sha256", "response_sha256"):
        digest = receipt[name]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise RuntimeError(f"invalid Mistral {name}")

    content = row["content"]
    content_bytes = content.encode("utf-8")
    return dict(receipt), hashlib.sha256(content_bytes).hexdigest(), len(content_bytes)


def run_mistral_acceptance_probe(
    db: UnifiedDB,
    clerk_map: dict[str, str],
    clerk_subject: str,
    content: str,
    *,
    entityos_bridge: EntityOSBridge | None = None,
    inference: Any | None = None,
    require_effect: bool = False,
) -> dict[str, Any]:
    """Run one canonical Mistral turn through the real ClayVerse causal spine.

    This is an internal final-sandbox probe, not a public chat surface and not an
    authentication test. It uses the same UnifiedDB, ClayVerseEngine and EffectGate
    as the product. The caller must separately establish the final Clerk/browser/PTTY
    gate. No provider secret is accepted as an argument or returned in this payload.
    """

    subject = _bounded_string(clerk_subject, "acceptance Clerk subject", max_length=2048)
    prompt = _bounded_string(content, "acceptance prompt", max_length=100_000)
    if subject not in clerk_map:
        raise PermissionError("acceptance Clerk subject is not in the canonical mapping")

    adapter = inference if inference is not None else MistralInference()
    if inference is None and not adapter.available():
        raise RuntimeError("Mistral acceptance provider is not locally configured")

    result = ClayVerseEngine(
        db,
        clerk_map,
        inference=adapter,
        entityos_bridge=entityos_bridge,
    ).ingest(subject, prompt, resources=["acceptance:mistral-final-sandbox"])

    receipt, assistant_sha256, assistant_bytes = _mistral_receipt_from_assistant(
        db, result["assistant_turn_id"]
    )

    outcome = result.get("outcome")
    effect_id = result.get("effect_id")
    if require_effect:
        if not effect_id:
            raise RuntimeError("Mistral acceptance probe required an effect but none was requested")
        if not isinstance(outcome, dict) or outcome.get("ok") is not True:
            raise RuntimeError("Mistral acceptance probe required a verified successful effect")

    return {
        "service": "clayverse",
        "status": "mistral_canonical_turn_pass",
        "scope": "internal_final_sandbox_probe",
        "auth_credit": False,
        "whole_product_pass": False,
        "user_id": result["user_id"],
        "session_id": result["session_id"],
        "turn_id": result["turn_id"],
        "assistant_turn_id": result["assistant_turn_id"],
        "causal_id": result["causal_id"],
        "entity_generation": db.entity_generation(),
        "assistant_content_sha256": assistant_sha256,
        "assistant_content_bytes": assistant_bytes,
        "inference_receipt": receipt,
        "effect": {
            "required": bool(require_effect),
            "effect_id": effect_id,
            "present": effect_id is not None,
            "verified_ok": isinstance(outcome, dict) and outcome.get("ok") is True,
        },
    }
