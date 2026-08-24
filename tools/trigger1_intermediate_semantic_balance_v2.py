#!/usr/bin/env python3
"""Label-blind derivation successor for Trigger-1 semantic counterbalance.

This composes the v1 counterbalanced wrapper with derivation anchors that never
contain the evaluation output-label identities YES/NO. It exists because promotion
gate v4 correctly requires both:
  1) counterbalanced token-output label mapping; and
  2) vector derivation independent of the evaluation output labels themselves.

The v1 wrapper remains historical/source donor provenance. This v2 driver is the
promotion-ready successor candidate. It still mints no canonical/J-Space/training
credit by itself.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import trigger1_intermediate_semantic_balance as v1

base = v1.base
SCHEMA = "CLAY_TRIGGER1_INTERMEDIATE_SEMANTIC_BALANCE/v2"

SEMANTIC_POSITIVE_ANCHORS = (
    "The proposition is factually correct and consistent with reality.",
    "The claim is accurate, valid, and supported by the stated facts.",
    "The statement describes a true state of affairs.",
)
SEMANTIC_NEGATIVE_ANCHORS = (
    "The proposition is factually incorrect and inconsistent with reality.",
    "The claim is inaccurate, invalid, and contradicted by the stated facts.",
    "The statement describes a false state of affairs.",
)


def _tokens(text: str) -> list[str]:
    return "".join(ch.lower() if ch.isalnum() else " " for ch in text).split()


def derivation_uses_evaluation_output_labels() -> bool:
    return any(
        "yes" in _tokens(text) or "no" in _tokens(text)
        for text in (*SEMANTIC_POSITIVE_ANCHORS, *SEMANTIC_NEGATIVE_ANCHORS)
    )


def semantic_derivation_metadata() -> dict[str, Any]:
    material = {
        "method": "label-blind intermediate residual activation contrast mean(semantic-correct anchors)-mean(semantic-incorrect anchors), normalized per layer",
        "uses_output_head_weights": False,
        "uses_holdout_data": False,
        "uses_evaluation_output_labels": False,
        "positive_anchor_family_sha256": base.canonical_sha(SEMANTIC_POSITIVE_ANCHORS),
        "negative_anchor_family_sha256": base.canonical_sha(SEMANTIC_NEGATIVE_ANCHORS),
        "candidate_layers": list(base.CANDIDATE_LAYERS),
    }
    return {
        **material,
        "derivation_family_id": base.canonical_sha({
            "positive": SEMANTIC_POSITIVE_ANCHORS,
            "negative": SEMANTIC_NEGATIVE_ANCHORS,
        }),
        "derivation_receipt_sha256": base.canonical_sha(material),
    }


def rewrite_scientific_metadata(
    result: dict[str, Any],
    candidate: dict[str, Any] | None,
    *,
    v2_wrapper_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    source_packet = result.get("source_packet")
    successor_source_packet_sha = None
    if isinstance(source_packet, dict):
        source_packet["intent"] = (
            "increase a label-blind semantic correctness representation before "
            "counterbalanced output-label mapping"
        )
        source_packet["basis"] = (
            "contrastive intermediate Qwen3-0.6B decoder hidden activations from "
            "label-blind semantic correctness anchors; not output-head weights, "
            "holdout data, or evaluation output-label identities"
        )
        source_packet["derivation_uses_evaluation_output_labels"] = False
        successor_source_packet_sha = base.canonical_sha(source_packet)
        result["source_packet_sha256"] = successor_source_packet_sha

    result.setdefault("semantic_balance", {}).update({
        "schema": SCHEMA,
        "label_blind_derivation": True,
        "derivation_uses_evaluation_output_labels": False,
        "v2_wrapper_sha256": v2_wrapper_sha256,
    })

    if candidate is not None:
        candidate["vector_derivation"] = semantic_derivation_metadata()
        if successor_source_packet_sha is not None:
            candidate.setdefault("intervention", {})["source_packet_sha256"] = successor_source_packet_sha
        candidate.setdefault("holdout", {}).update({
            "evaluation_independent_of_vector_derivation": True,
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
            "semantic_truth_counterbalanced": True,
        })
        candidate.setdefault("semantic_balance", {}).update({
            "schema": SCHEMA,
            "label_blind_derivation": True,
            "derivation_uses_evaluation_output_labels": False,
            "v2_wrapper_sha256": v2_wrapper_sha256,
        })
        candidate.setdefault("source_identity", {})["semantic_balance_v2_wrapper_sha256"] = v2_wrapper_sha256
    return result, candidate


def _output_dir_from_argv() -> Path:
    for idx, item in enumerate(sys.argv[:-1]):
        if item == "--output-dir":
            return Path(sys.argv[idx + 1])
    raise SystemExit("--output-dir is required")


def _self_sha() -> str:
    return base.sha256_file(Path(__file__).resolve())


def _postprocess(out: Path, rc: int, pre_sha: str, post_sha: str) -> int:
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    if not result_path.is_file():
        return rc

    result = json.loads(result_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8")) if candidate_path.is_file() else None
    stable = pre_sha == post_sha

    result, candidate = rewrite_scientific_metadata(
        result,
        candidate,
        v2_wrapper_sha256=post_sha,
    )
    result.setdefault("semantic_balance", {})["v2_wrapper_stable"] = stable

    if not stable:
        result["status"] = "SOURCE_IDENTITY_DRIFT_V2_WRAPPER"
        if candidate_path.exists():
            candidate_path.unlink()
        candidate = None
        rc = 4

    result.pop("result_sha256", None)
    result["result_sha256"] = base.canonical_sha(result)
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if candidate is not None:
        candidate_path.write_text(
            json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return rc


def main() -> int:
    if derivation_uses_evaluation_output_labels():
        raise RuntimeError("DERIVATION_OUTPUT_LABEL_LEAKAGE")

    # Only the vector-construction anchors change. The v1 wrapper owns the balanced
    # NORMAL/REVERSED evaluation mapping and expected-label-oriented adjudication.
    base.POSITIVE_ANCHORS = SEMANTIC_POSITIVE_ANCHORS
    base.NEGATIVE_ANCHORS = SEMANTIC_NEGATIVE_ANCHORS

    out = _output_dir_from_argv()
    pre_sha = _self_sha()
    rc = v1.main()
    post_sha = _self_sha()
    return _postprocess(out, rc, pre_sha, post_sha)


if __name__ == "__main__":
    raise SystemExit(main())
