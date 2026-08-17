from __future__ import annotations

import hashlib
import json
from typing import Any

from .adapters import MistralInference
from .engine import ClayVerseEngine
from .entityos_bridge import EntityOSBridge
from .final_acceptance_mistral_config import validate_final_mistral_runtime_config
from .store import StaleGeneration, UnifiedDB


def _bounded_string(value: Any, name: str, *, max_length: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or "\x00" in value:
        raise RuntimeError(f"invalid {name}")
    return value


def _mistral_receipt_from_assistant(
    db: UnifiedDB, assistant_turn_id: str
) -> tuple[dict[str, Any], str, int, int, str]:
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

    reasoning_generation = provenance.get("reasoning_generation")
    if (
        isinstance(reasoning_generation, bool)
        or not isinstance(reasoning_generation, int)
        or reasoning_generation < 1
    ):
        raise RuntimeError("acceptance probe reasoning generation is invalid")
    workspace_episode_id = _bounded_string(
        provenance.get("workspace_episode_id"),
        "acceptance workspace episode id",
        max_length=256,
    )

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
    return (
        dict(receipt),
        hashlib.sha256(content_bytes).hexdigest(),
        len(content_bytes),
        reasoning_generation,
        workspace_episode_id,
    )


def run_mistral_acceptance_probe(
    db: UnifiedDB,
    clerk_map: dict[str, str],
    clerk_subject: str,
    content: str,
    *,
    entityos_bridge: EntityOSBridge | None = None,
    inference: Any | None = None,
    require_effect: bool = False,
    required_effect_capability: str | None = None,
) -> dict[str, Any]:
    """Run one canonical Mistral turn through the real ClayVerse causal spine.

    This is an internal final-sandbox probe, not a public chat surface and not an
    authentication test. It uses the same UnifiedDB, ClayVerseEngine and EffectGate
    as the product. The caller must separately establish the final Clerk/browser/PTTY
    gate. No provider secret is accepted as an argument or returned in this payload.

    ``required_effect_capability`` strengthens the generic effect requirement for
    final gates that must prove a specific EffectGate capability (notably
    ``entityos.exec``). It validates the persisted canonical effect row, so a
    successful ``state.noop`` cannot masquerade as an EntityOS round-trip.
    """

    subject = _bounded_string(clerk_subject, "acceptance Clerk subject", max_length=2048)
    prompt = _bounded_string(content, "acceptance prompt", max_length=100_000)
    if subject not in clerk_map:
        raise PermissionError("acceptance Clerk subject is not in the canonical mapping")

    required_capability = None
    if required_effect_capability is not None:
        required_capability = _bounded_string(
            required_effect_capability,
            "required acceptance effect capability",
            max_length=128,
        )
        require_effect = True

    if inference is None:
        fixed_model = validate_final_mistral_runtime_config()
        adapter = MistralInference(model=fixed_model)
        if not adapter.available():
            raise RuntimeError("Mistral acceptance provider is not locally configured")
    else:
        adapter = inference

    result = ClayVerseEngine(
        db,
        clerk_map,
        inference=adapter,
        entityos_bridge=entityos_bridge,
    ).ingest(subject, prompt, resources=["acceptance:mistral-final-sandbox"])

    (
        receipt,
        assistant_sha256,
        assistant_bytes,
        reasoning_generation,
        provenance_workspace_episode_id,
    ) = _mistral_receipt_from_assistant(db, result["assistant_turn_id"])

    workspace = result.get("workspace")
    result_workspace_episode_id = (
        workspace.get("episode_id") if isinstance(workspace, dict) else None
    )
    if provenance_workspace_episode_id != result_workspace_episode_id:
        raise RuntimeError("Mistral acceptance probe workspace episode identity mismatch")

    try:
        db.assert_live_generation(result["session_id"], reasoning_generation)
    except StaleGeneration as exc:
        raise RuntimeError("Mistral acceptance probe reasoning generation is stale") from exc
    session_generation = db.session_generation(result["session_id"])
    entity_generation = db.entity_generation()

    outcome = result.get("outcome")
    effect_id = result.get("effect_id")
    effect_capability = None
    if effect_id:
        effect_row = db.db.execute(
            "SELECT capability FROM effects WHERE effect_id=?",
            (effect_id,),
        ).fetchone()
        if effect_row is None:
            raise RuntimeError("Mistral acceptance probe effect journal row is missing")
        effect_capability = _bounded_string(
            effect_row["capability"],
            "acceptance effect capability",
            max_length=128,
        )

    if require_effect:
        if not effect_id:
            raise RuntimeError("Mistral acceptance probe required an effect but none was requested")
        if not isinstance(outcome, dict) or outcome.get("ok") is not True:
            raise RuntimeError("Mistral acceptance probe required a verified successful effect")
    if required_capability is not None and effect_capability != required_capability:
        raise RuntimeError(
            "Mistral acceptance probe required effect capability "
            f"{required_capability} but observed {effect_capability or 'none'}"
        )

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
        "workspace_episode_id": result_workspace_episode_id,
        "reasoning_generation": reasoning_generation,
        "session_generation": session_generation,
        "entity_generation": entity_generation,
        "assistant_content_sha256": assistant_sha256,
        "assistant_content_bytes": assistant_bytes,
        "inference_receipt": receipt,
        "effect": {
            "required": bool(require_effect),
            "required_capability": required_capability,
            "capability": effect_capability,
            "effect_id": effect_id,
            "present": effect_id is not None,
            "verified_ok": isinstance(outcome, dict) and outcome.get("ok") is True,
        },
    }
