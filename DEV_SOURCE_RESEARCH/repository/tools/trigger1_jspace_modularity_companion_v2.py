#!/usr/bin/env python3
"""Evidence-bound successor to Trigger-1 modularity companion v1.

v2 composes v1 and can only reduce its stronger modular-control candidate. It closes a
summary self-attestation gap by reconstructing cross-effect statistics from per-family
rows, binding the exact family universe and full matrix to deterministic digests, and—if
rank-2 is required—reconstructing the declared composition residual from bound
combination-by-family rows.

This verifies internal evidence-object consistency only. It does not authenticate the
external runtime receipts referenced by their digests, run a model, or mint canonical,
J-Space-model, HCU-full, EntityOS-whole, training, BASE, or real-effect credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import trigger1_jspace_modularity_companion_v1 as v1

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_COMPANION/v2"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_COMPANION_BATCH/v2"
TOL = 1e-9


def canonical_json_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _close(a: Any, b: Any) -> bool:
    return _finite(a) and _finite(b) and abs(float(a) - float(b)) <= TOL


def _protocol_contract(candidate: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    return {
        "semantic_rank_decision": candidate.get("semantic_rank_decision"),
        "frozen_before_holdout": protocol.get("frozen_before_holdout"),
        "equal_family_weighting": protocol.get("equal_family_weighting"),
        "family_level_signed_effects_preserved": protocol.get("family_level_signed_effects_preserved"),
        "sentinel_endpoints": sorted(protocol.get("sentinel_endpoints", [])) if isinstance(protocol.get("sentinel_endpoints"), list) else None,
        "modular_intervention_ids": sorted(protocol.get("modular_intervention_ids", [])) if isinstance(protocol.get("modular_intervention_ids"), list) else None,
        "preregistered_max_abs_standardized_cross_effect": protocol.get("preregistered_max_abs_standardized_cross_effect"),
    }


def _bound_family_rows(cell: dict[str, Any], *, pair: str) -> tuple[list[dict[str, Any]], set[str], list[str]]:
    failures: list[str] = []
    rows = cell.get("per_family_standardized_deltas")
    if not isinstance(rows, list) or len(rows) < 3:
        return [], set(), [f"BOUND_PER_FAMILY_ROWS_REQUIRED:{pair}"]
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            failures.append(f"BOUND_FAMILY_ROW_OBJECT_REQUIRED:{pair}")
            continue
        family = row.get("scenario_family_id")
        delta = row.get("standardized_delta")
        receipt = row.get("evidence_receipt_sha256")
        if not isinstance(family, str) or not family.strip():
            failures.append(f"BOUND_SCENARIO_FAMILY_ID_REQUIRED:{pair}")
            continue
        family = family.strip()
        if family in seen:
            failures.append(f"BOUND_DUPLICATE_SCENARIO_FAMILY:{pair}:{family}")
        seen.add(family)
        if not _finite(delta):
            failures.append(f"BOUND_FAMILY_DELTA_FINITE_REQUIRED:{pair}:{family}")
            continue
        if not _sha256(receipt):
            failures.append(f"BOUND_FAMILY_RUNTIME_RECEIPT_DIGEST_REQUIRED:{pair}:{family}")
            continue
        normalized.append({
            "scenario_family_id": family,
            "standardized_delta": float(delta),
            "evidence_receipt_sha256": receipt,
        })
    normalized.sort(key=lambda row: row["scenario_family_id"])
    return normalized, seen, failures


def _evidence_binding(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    protocol = candidate.get("modularity_protocol")
    if not isinstance(protocol, dict):
        return False, ["MODULARITY_PROTOCOL_REQUIRED"], {}

    contract = _protocol_contract(candidate, protocol)
    expected_protocol_sha = canonical_json_sha(contract)
    if protocol.get("protocol_sha256") != expected_protocol_sha:
        failures.append("MODULARITY_PROTOCOL_DIGEST_MISMATCH")

    cells = protocol.get("cross_effect_matrix")
    if not isinstance(cells, list) or not cells:
        return False, sorted(set(failures + ["BOUND_CROSS_EFFECT_MATRIX_REQUIRED"])), {
            "protocol_contract_sha256": expected_protocol_sha,
        }

    normalized_matrix: list[dict[str, Any]] = []
    family_universe: set[str] | None = None
    for cell in cells:
        if not isinstance(cell, dict):
            failures.append("BOUND_CROSS_EFFECT_CELL_OBJECT_REQUIRED")
            continue
        intervention = cell.get("intervention_id")
        sentinel = cell.get("sentinel_id")
        pair = f"{intervention}:{sentinel}"
        rows, families, row_failures = _bound_family_rows(cell, pair=pair)
        failures.extend(row_failures)
        if families:
            if family_universe is None:
                family_universe = set(families)
            elif families != family_universe:
                failures.append(f"CROSS_EFFECT_FAMILY_UNIVERSE_MISMATCH:{pair}")
        if rows:
            mean = sum(row["standardized_delta"] for row in rows) / len(rows)
            maximum = max(abs(row["standardized_delta"]) for row in rows)
            if not _close(cell.get("equal_family_weighted_standardized_delta"), mean):
                failures.append(f"CROSS_EFFECT_POOLED_MEAN_RECOMPUTE_MISMATCH:{pair}")
            if not _close(cell.get("max_abs_family_standardized_delta"), maximum):
                failures.append(f"CROSS_EFFECT_FAMILY_MAX_RECOMPUTE_MISMATCH:{pair}")
            if cell.get("family_count") != len(rows):
                failures.append(f"CROSS_EFFECT_FAMILY_COUNT_RECOMPUTE_MISMATCH:{pair}")
        normalized_matrix.append({
            "intervention_id": intervention,
            "sentinel_id": sentinel,
            "per_family_standardized_deltas": rows,
        })

    normalized_matrix.sort(key=lambda row: (str(row["intervention_id"]), str(row["sentinel_id"])))
    family_ids = sorted(family_universe or set())
    expected_family_sha = canonical_json_sha(family_ids)
    if protocol.get("scenario_family_universe_sha256") != expected_family_sha:
        failures.append("SCENARIO_FAMILY_UNIVERSE_DIGEST_MISMATCH")
    expected_matrix_sha = canonical_json_sha(normalized_matrix)
    if protocol.get("cross_effect_matrix_receipt_sha256") != expected_matrix_sha:
        failures.append("CROSS_EFFECT_MATRIX_DIGEST_MISMATCH")

    rank = candidate.get("semantic_rank_decision")
    composition_sha: str | None = None
    composition_max: float | None = None
    if rank == "TWO_DIMENSIONAL_REQUIRED":
        composition = candidate.get("rank2_composition")
        if not isinstance(composition, dict):
            failures.append("BOUND_RANK2_COMPOSITION_REQUIRED")
        else:
            residuals = composition.get("combination_residuals")
            if not isinstance(residuals, list) or not residuals:
                failures.append("BOUND_RANK2_COMBINATION_RESIDUALS_REQUIRED")
            else:
                normalized_residuals: list[dict[str, Any]] = []
                combination_ids: set[str] = set()
                seen_pairs: set[tuple[str, str]] = set()
                residual_family_universe: set[str] = set()
                for row in residuals:
                    if not isinstance(row, dict):
                        failures.append("BOUND_RANK2_RESIDUAL_ROW_OBJECT_REQUIRED")
                        continue
                    combo = row.get("combination_id")
                    family = row.get("scenario_family_id")
                    residual = row.get("standardized_residual")
                    receipt = row.get("evidence_receipt_sha256")
                    if not isinstance(combo, str) or not combo.strip() or not isinstance(family, str) or not family.strip():
                        failures.append("BOUND_RANK2_COMBINATION_AND_FAMILY_IDS_REQUIRED")
                        continue
                    combo, family = combo.strip(), family.strip()
                    key = (combo, family)
                    if key in seen_pairs:
                        failures.append(f"BOUND_DUPLICATE_RANK2_RESIDUAL:{combo}:{family}")
                    seen_pairs.add(key)
                    if not _finite(residual):
                        failures.append(f"BOUND_RANK2_RESIDUAL_FINITE_REQUIRED:{combo}:{family}")
                        continue
                    if not _sha256(receipt):
                        failures.append(f"BOUND_RANK2_RUNTIME_RECEIPT_DIGEST_REQUIRED:{combo}:{family}")
                        continue
                    combination_ids.add(combo)
                    residual_family_universe.add(family)
                    normalized_residuals.append({
                        "combination_id": combo,
                        "scenario_family_id": family,
                        "standardized_residual": float(residual),
                        "evidence_receipt_sha256": receipt,
                    })
                normalized_residuals.sort(key=lambda row: (row["combination_id"], row["scenario_family_id"]))
                if len(combination_ids) < 4:
                    failures.append("BOUND_RANK2_AT_LEAST_FOUR_COMBINATIONS_REQUIRED")
                if family_universe is not None and residual_family_universe != family_universe:
                    failures.append("RANK2_COMPOSITION_FAMILY_UNIVERSE_MISMATCH")
                if normalized_residuals:
                    composition_max = max(abs(row["standardized_residual"]) for row in normalized_residuals)
                    if not _close(composition.get("max_abs_standardized_residual"), composition_max):
                        failures.append("RANK2_COMPOSITION_MAX_RESIDUAL_RECOMPUTE_MISMATCH")
                composition_sha = canonical_json_sha(normalized_residuals)
                if composition.get("composition_receipt_sha256") != composition_sha:
                    failures.append("RANK2_COMPOSITION_DIGEST_MISMATCH")

    details = {
        "protocol_contract_sha256": expected_protocol_sha,
        "scenario_family_universe_sha256": expected_family_sha,
        "cross_effect_matrix_sha256": expected_matrix_sha,
        "scenario_family_count": len(family_ids),
        "rank2_composition_sha256": composition_sha,
        "rank2_recomputed_max_abs_standardized_residual": composition_max,
        "runtime_receipt_authentication": "NOT_PERFORMED_DIGEST_REFERENCES_ONLY",
    }
    return not failures, sorted(set(failures)), details


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v1.adjudicate(candidate)
    binding_ok, binding_failures, binding = _evidence_binding(candidate)
    upstream_modular = base.get("modular_hcu_jspace_control_candidate") is True
    modular = bool(upstream_modular and binding_ok)
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v1_modular_hcu_jspace_control_candidate": upstream_modular,
        "modularity_evidence_bound_candidate": bool(binding_ok),
        "modular_hcu_jspace_control_candidate": modular,
        "modularity_binding_failures": binding_failures,
        "modularity_evidence_binding": binding,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "hcu_full_runtime_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v2 recomputes and digest-binds the modularity evidence object but does not authenticate external runtime "
            "receipt digests. A PASS is therefore only an internally evidence-bound modular-control candidate layered "
            "on v1; it mints no canonical semantics, model-runtime, HCU-full, EntityOS-whole, training, BASE, or effect credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "modular_hcu_jspace_control_candidate": False,
            "modularity_evidence_bound_candidate": False,
            "canonical_credit_minted": False,
            "modularity_binding_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "modular_hcu_jspace_control_candidate": False,
            "modularity_evidence_bound_candidate": False,
            "canonical_credit_minted": False,
            "modularity_binding_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "modular_hcu_jspace_control_candidate": any(v.get("modular_hcu_jspace_control_candidate") is True for v in verdicts),
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
