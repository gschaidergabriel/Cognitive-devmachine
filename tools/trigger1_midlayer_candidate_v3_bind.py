#!/usr/bin/env python3
"""Truth-preserving binder for Trigger-1 midlayer runtime candidates.

The midlayer executor can establish a useful mechanism candidate before it satisfies the
full Trigger-1 scientific-independence contract. This helper closes only evidence fields
that can be derived from the exact runtime result without inventing counterbalance or
independence that the experiment did not perform.

The current midlayer experiment still has two deliberate scientific limitations:

* the steering basis is built from A/B/C-labelled prompts, i.e. it uses the exact
  evaluation output-label identities even though it does not use output-head weights;
* the promotion score is an A-vs-(B,C) output-token logit metric without counterbalanced
  token-label mapping.

Those facts MUST remain visible to successor promotion gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RESULT_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
BINDING_SCHEMA = "TRIGGER1_MIDLAYER_TRUTH_BINDING/v2"
METRIC_SCHEMA = "TRIGGER1_OUTPUT_TOKEN_LOGIT_METRIC/v1"


class TruthBindingError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _prompt_hashes(rows: Any, *, field: str = "prompt_sha256") -> set[str]:
    if not isinstance(rows, list) or not rows:
        raise TruthBindingError("NONEMPTY_PROMPT_RECEIPTS_REQUIRED")
    hashes: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not _sha256(row.get(field)):
            raise TruthBindingError("PROMPT_RECEIPT_SHA256_REQUIRED")
        hashes.add(str(row[field]))
    return hashes


def _basis_labels(rows: Any) -> set[str]:
    if not isinstance(rows, list) or not rows:
        raise TruthBindingError("NONEMPTY_BASIS_RECEIPTS_REQUIRED")
    labels: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TruthBindingError("BASIS_RECEIPT_OBJECT_REQUIRED")
        label = row.get("label")
        if not isinstance(label, str) or not label:
            raise TruthBindingError("BASIS_LABEL_REQUIRED")
        labels.add(label)
    return labels


def bind_candidate(result: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if result.get("schema") != RESULT_SCHEMA:
        raise TruthBindingError("MIDDLAYER_RESULT_SCHEMA_REQUIRED")
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise TruthBindingError("TRIGGER1_CANDIDATE_SCHEMA_REQUIRED")
    if result.get("basis_constructed_without_output_head") is not True:
        raise TruthBindingError("OUTPUT_HEAD_INDEPENDENT_BASIS_NOT_PROVEN")
    if result.get("terminal_output_projection_shortcut") is not False:
        raise TruthBindingError("NONTERMINAL_INTERVENTION_REQUIRED")

    intervention = candidate.get("intervention")
    calibration = candidate.get("calibration")
    holdout = candidate.get("holdout")
    if not isinstance(intervention, dict):
        raise TruthBindingError("INTERVENTION_OBJECT_REQUIRED")
    if not isinstance(calibration, dict):
        raise TruthBindingError("CALIBRATION_OBJECT_REQUIRED")
    if not isinstance(holdout, dict):
        raise TruthBindingError("HOLDOUT_OBJECT_REQUIRED")
    if intervention.get("basis_constructed_without_output_head") is not True:
        raise TruthBindingError("CANDIDATE_OUTPUT_HEAD_INDEPENDENT_BASIS_NOT_PROVEN")
    if intervention.get("terminal_output_projection_shortcut") is not False:
        raise TruthBindingError("CANDIDATE_NONTERMINAL_INTERVENTION_REQUIRED")

    basis_receipts = result.get("basis_receipts")
    holdout_rows = result.get("holdout_rows")
    basis_hashes = _prompt_hashes(basis_receipts)
    holdout_hashes = _prompt_hashes(holdout_rows)
    overlap = sorted(basis_hashes & holdout_hashes)
    if overlap:
        raise TruthBindingError("VECTOR_DERIVATION_HOLDOUT_PROMPT_OVERLAP")

    derivation_family_id = calibration.get("basis_family_id")
    holdout_family_id = holdout.get("family_id")
    if not isinstance(derivation_family_id, str) or not derivation_family_id:
        raise TruthBindingError("BASIS_FAMILY_ID_REQUIRED")
    if not isinstance(holdout_family_id, str) or not holdout_family_id:
        raise TruthBindingError("HOLDOUT_FAMILY_ID_REQUIRED")
    if derivation_family_id == holdout_family_id:
        raise TruthBindingError("VECTOR_DERIVATION_HOLDOUT_FAMILY_OVERLAP")

    token_ids = result.get("token_ids")
    token_labels = result.get("token_labels")
    if not isinstance(token_ids, dict) or not isinstance(token_labels, dict):
        raise TruthBindingError("OUTPUT_TOKEN_METRIC_IDENTITY_REQUIRED")
    evaluation_label_identities = set(map(str, token_ids.keys()))
    basis_label_identities = _basis_labels(basis_receipts)
    uses_evaluation_output_labels = bool(basis_label_identities & evaluation_label_identities)
    if not uses_evaluation_output_labels:
        raise TruthBindingError("EXPECTED_CURRENT_LABEL_IDENTITY_COUPLING_NOT_OBSERVED")

    derivation_material = {
        "schema": "TRIGGER1_ACTIVATION_CONTRAST_DERIVATION/v2",
        "method": "INTERMEDIATE_ACTIVATION_CONTRAST_MEAN",
        "basis_family_id": derivation_family_id,
        "basis_prompt_sha256": sorted(basis_hashes),
        "basis_activation_receipts": basis_receipts,
        "basis_label_identities": sorted(basis_label_identities),
        "evaluation_output_label_identities": sorted(evaluation_label_identities),
        "local_vector_sha256": intervention.get("local_vector_sha256"),
        "activation_site": intervention.get("activation_site"),
        "uses_output_head_weights": False,
        "uses_holdout_data": False,
        "uses_evaluation_output_labels": uses_evaluation_output_labels,
    }
    derivation_receipt_sha = canonical_sha(derivation_material)

    metric_definition = {
        "schema": METRIC_SCHEMA,
        "formula": "logit(A)-0.5*(logit(B)+logit(C))",
        "token_ids": token_ids,
        "token_labels": token_labels,
        "executor_sha256": (result.get("source") or {}).get("executor_sha256") if isinstance(result.get("source"), dict) else None,
        "uses_output_tokens": True,
        "label_mapping_counterbalanced": False,
    }
    metric_definition_sha = canonical_sha(metric_definition)

    bound = json.loads(json.dumps(candidate))
    bound["vector_derivation"] = {
        "method": "INTERMEDIATE_ACTIVATION_CONTRAST_MEAN",
        "uses_output_head_weights": False,
        "uses_holdout_data": False,
        "uses_evaluation_output_labels": True,
        "derivation_family_id": derivation_family_id,
        "derivation_receipt_sha256": derivation_receipt_sha,
    }
    bound_holdout = bound.setdefault("holdout", {})
    bound_holdout["evaluation_independent_of_vector_derivation"] = True
    bound_holdout["metric_definition_sha256"] = metric_definition_sha
    bound_holdout["metric_uses_output_tokens"] = True
    bound_holdout["label_mapping_counterbalanced"] = False

    bound["scientific_evidence_binding"] = {
        "schema": BINDING_SCHEMA,
        "derivation_prompt_count": len(basis_hashes),
        "holdout_prompt_count": len(holdout_hashes),
        "derivation_holdout_prompt_overlap": overlap,
        "basis_label_identities": sorted(basis_label_identities),
        "evaluation_output_label_identities": sorted(evaluation_label_identities),
        "uses_evaluation_output_labels": True,
        "derivation_family_id": derivation_family_id,
        "holdout_family_id": holdout_family_id,
        "derivation_receipt_sha256": derivation_receipt_sha,
        "metric_definition_sha256": metric_definition_sha,
        "metric_uses_output_tokens": True,
        "label_mapping_counterbalanced": False,
        "expected_remaining_scientific_blockers": [
            "VECTOR_DERIVATION_MUST_NOT_USE_EVALUATION_OUTPUT_LABELS",
            "TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING",
        ],
        "evidence_boundary": (
            "This binding proves only source/result-level derivation-vs-holdout disjointness and the exact "
            "output-token metric identity. It deliberately records current A/B/C evaluation-label coupling "
            "and absence of counterbalanced output-token mapping instead of upgrading either condition."
        ),
    }
    return bound


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()

    result_path = Path(args.result)
    candidate_path = Path(args.candidate)
    output_path = Path(args.output) if args.output else candidate_path
    result = json.loads(result_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or not isinstance(candidate, dict):
        raise TruthBindingError("JSON_OBJECTS_REQUIRED")
    bound = bind_candidate(result, candidate)
    output_path.write_text(
        json.dumps(bound, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
