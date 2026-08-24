#!/usr/bin/env python3
"""Supervisor-8.72 anti-circularity successor for Trigger-1 promotion.

The v2 gate proves runtime identity/control/split mechanics, but it does not distinguish
a genuinely upstream latent intervention from a readout construction that is algebraically
coupled to the measured logits. In particular, a vector built from lm_head/output-embedding
rows and injected after the final model norm immediately before lm_head can manufacture the
measured A-vs-B/C logit shift by construction.

This successor delegates all existing v2 requirements, then fails closed for local PyTorch
activation interventions unless the candidate proves a weight-independent or activation-
derived basis, an upstream residual-stream site, and at least one transformer layer of
separation from the final readout. It mints no canonical/HCU/J-Space/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate as base

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v3"
LOCAL_PYTORCH_CLASS = "LOCAL_PYTORCH_ACTIVATION_INTERVENTION"
ALLOWED_VECTOR_BASIS_CLASSES = {
    "DETERMINISTIC_WEIGHT_INDEPENDENT_PROBE",
    "CALIBRATION_ACTIVATION_CONTRAST",
}


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def anti_circularity_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return whether a local PyTorch candidate is separated from its measured readout."""
    if candidate.get("runtime_intervention_class") != LOCAL_PYTORCH_CLASS:
        return True, []

    failures: list[str] = []
    intervention = candidate.get("intervention")
    if not isinstance(intervention, dict):
        return False, ["ANTI_CIRCULARITY_INTERVENTION_REQUIRED"]

    basis = intervention.get("vector_basis_class")
    if basis not in ALLOWED_VECTOR_BASIS_CLASSES:
        failures.append("ANTI_CIRCULARITY_VECTOR_BASIS_REQUIRED")
    if intervention.get("derived_from_output_embeddings") is not False:
        failures.append("OUTPUT_EMBEDDING_DERIVED_VECTOR_FORBIDDEN")
    if intervention.get("injected_after_final_norm") is not False:
        failures.append("POST_FINAL_NORM_INJECTION_FORBIDDEN")

    separation = intervention.get("readout_separation_layers")
    if not isinstance(separation, int) or isinstance(separation, bool) or separation < 1:
        failures.append("UPSTREAM_READOUT_LAYER_SEPARATION_REQUIRED")

    if not _sha256(intervention.get("vector_derivation_receipt_sha256")):
        failures.append("VECTOR_DERIVATION_RECEIPT_REQUIRED")

    site = str(intervention.get("activation_site") or "").lower()
    if not site:
        failures.append("ANTI_CIRCULARITY_ACTIVATION_SITE_REQUIRED")
    if "lm_head" in site or ".norm" in site or ":norm" in site or "final_norm" in site:
        failures.append("READOUT_ADJACENT_ACTIVATION_SITE_FORBIDDEN")
    if ".layers." not in site and "layers[" not in site:
        failures.append("INTERMEDIATE_TRANSFORMER_LAYER_REQUIRED")

    return not failures, failures


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    verdict = dict(base.adjudicate(candidate))
    anti_ok, anti_failures = anti_circularity_evidence(candidate)
    all_failures = sorted(set(list(verdict.get("failures") or []) + anti_failures))

    if not anti_ok:
        verdict["mechanism_runtime_vector_credit_candidate"] = False
        verdict["owner_trigger1_goal_credit_candidate"] = False
        verdict["owner_trigger1_direct_free_api_model_credit_candidate"] = False

    verdict.update(
        {
            "schema": VERDICT_SCHEMA,
            "anti_circularity_pass": bool(anti_ok),
            "anti_circularity_failures": sorted(set(anti_failures)),
            "failures": all_failures,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "evidence_boundary": (
                "PASS is a promotion-candidate boundary only. For local PyTorch activation interventions, "
                "the steering basis must not be derived from output-embedding/lm_head rows and the injection "
                "must occur in an intermediate transformer residual stream with downstream layer separation."
            ),
        }
    )
    return verdict


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "anti_circularity_pass": False,
            "anti_circularity_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "owner_target_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "anti_circularity_pass": False,
            "anti_circularity_failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "owner_target_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    goal = any(item.get("owner_trigger1_goal_credit_candidate") is True for item in verdicts)
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v3",
        "candidate_files_seen": len(paths),
        "mechanism_runtime_vector_credit_candidate": any(
            item.get("mechanism_runtime_vector_credit_candidate") is True for item in verdicts
        ),
        "owner_trigger1_goal_credit_candidate": goal,
        "owner_trigger1_direct_free_api_model_credit_candidate": goal,
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = parser.parse_args()
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
