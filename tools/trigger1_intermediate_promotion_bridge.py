#!/usr/bin/env python3
"""Fail-closed bridge from the strongest intermediate Trigger-1 result to gate-v4.

Promotion requires both upstream evaluation-label independence and genuine semantic
transfer: disjoint semantic stimuli, both polarities under both label maps, and correct
unsteered baseline discrimination. Historical symbol-only PASS results fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

INTERMEDIATE_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1"
INTERMEDIATE_CANDIDATE_SCHEMA = "CLAY_TRIGGER1_INTERMEDIATE_JSPACE_CAUSAL_CANDIDATE/v1"
DIRECT_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
LABEL_INDEPENDENCE_SCHEMA = "TRIGGER1_VECTOR_DERIVATION_LABEL_INDEPENDENCE/v1"
REQUIRED_CONTROLS = ("BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR", "ORTHOGONAL_SAME_NORM", "PERMUTED_SAME_NORM")
METRIC_DEFINITION = {
    "schema": "TRIGGER1_COUNTERBALANCED_SEMANTIC_OUTPUT_METRIC/v2",
    "score": "logit(positive_label)-logit(negative_label)",
    "semantic_baseline": "positive stimulus requires score>0; negative stimulus requires score<0 before intervention",
    "semantic_polarities": ["negative", "positive"],
    "label_maps": [["A", "B"], ["B", "A"]],
    "required_controls": list(REQUIRED_CONTROLS),
    "wrong_layer": "same selected vector at a different predeclared layer must not outperform selected-layer +VECTOR",
    "lesion_rescue": "selected-direction lesion must not improve mapped score and rescue must improve over lesion",
}


class BridgeError(ValueError): pass

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

def _sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64: return False
    try: int(value, 16)
    except ValueError: return False
    return True

def _require(cond: bool, code: str) -> None:
    if not cond: raise BridgeError(code)

def _rows(result: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = result.get(key); _require(isinstance(rows, list) and bool(rows), f"{key.upper()}_REQUIRED"); _require(all(isinstance(row, dict) for row in rows), f"{key.upper()}_OBJECT_ROWS_REQUIRED"); return rows

def _unique_nonempty(rows: list[dict[str, Any]], key: str) -> list[Any]:
    values = {row.get(key) for row in rows}; _require(None not in values and "" not in values, f"{key.upper()}_REQUIRED"); return sorted(values, key=lambda x: str(x))

def _receipt_family(rows: list[dict[str, Any]], control: str) -> str:
    receipts = [row.get("runtime_receipt_sha256") for row in rows if row.get("control") == control]; _require(bool(receipts), f"CONTROL_ROWS_REQUIRED:{control}"); _require(all(_sha(value) for value in receipts), f"CONTROL_RUNTIME_RECEIPT_REQUIRED:{control}"); return digest(receipts)


def _require_semantic_transfer(result: dict[str, Any], intermediate: dict[str, Any], holdout: list[dict[str, Any]]) -> None:
    verdict = result.get("verdict"); _require(isinstance(verdict, dict), "INTERMEDIATE_PROTOCOL_VERDICT_REQUIRED")
    _require(verdict.get("classification") == "INTERMEDIATE_SEMANTIC_REPRESENTATION_CAUSAL_CANDIDATE", "SEMANTIC_INTERMEDIATE_PROTOCOL_PASS_REQUIRED")
    _require(verdict.get("semantic_polarities") == ["negative", "positive"], "SEMANTIC_POLARITY_COVERAGE_REQUIRED")
    correct = verdict.get("semantic_baseline_correct_count"); total = verdict.get("semantic_baseline_case_count")
    _require(isinstance(correct, int) and isinstance(total, int) and total > 0 and correct == total, "SEMANTIC_BASELINE_DISCRIMINATION_REQUIRED")
    margin = verdict.get("semantic_baseline_min_signed_margin"); _require(isinstance(margin, (int, float)) and not isinstance(margin, bool) and float(margin) > 0, "SEMANTIC_BASELINE_MARGIN_REQUIRED")
    _require(isinstance(verdict.get("semantic_stimulus_count"), int) and verdict["semantic_stimulus_count"] >= 2, "DISTINCT_SEMANTIC_STIMULI_REQUIRED")
    semantic = result.get("semantic_transfer_evidence"); _require(isinstance(semantic, dict), "SEMANTIC_TRANSFER_EVIDENCE_REQUIRED")
    _require(intermediate.get("semantic_transfer_evidence") == semantic, "INTERMEDIATE_SEMANTIC_EVIDENCE_BINDING_REQUIRED")
    _require(semantic.get("holdout_polarities") == ["negative", "positive"], "SEMANTIC_HOLDOUT_POLARITIES_REQUIRED")
    _require(semantic.get("baseline_semantic_discrimination_required") is True, "SEMANTIC_BASELINE_GATE_REQUIRED")
    _require(_sha(semantic.get("derivation_family_sha256")), "DERIVATION_FAMILY_SHA256_REQUIRED")
    cal_shas = semantic.get("calibration_stimulus_sha256"); hold_shas = semantic.get("holdout_stimulus_sha256")
    _require(isinstance(cal_shas, list) and len(cal_shas) >= 2 and all(_sha(x) for x in cal_shas), "CALIBRATION_SEMANTIC_STIMULUS_SHA256_REQUIRED")
    _require(isinstance(hold_shas, list) and len(hold_shas) >= 2 and all(_sha(x) for x in hold_shas), "HOLDOUT_SEMANTIC_STIMULUS_SHA256_REQUIRED")
    _require(set(cal_shas).isdisjoint(set(hold_shas)), "CALIBRATION_HOLDOUT_SEMANTIC_STIMULI_MUST_BE_DISJOINT")
    pairs_by_map: dict[str, set[str]] = {}; seen_stimuli: set[str] = set()
    for row in holdout:
        polarity = row.get("stimulus_polarity"); family = row.get("stimulus_family_id"); stimulus_sha = row.get("stimulus_sha256"); label_map_id = row.get("label_map_id")
        _require(polarity in {"positive", "negative"}, "HOLDOUT_SEMANTIC_POLARITY_REQUIRED"); _require(isinstance(family, str) and bool(family.strip()), "HOLDOUT_SEMANTIC_FAMILY_REQUIRED"); _require(_sha(stimulus_sha), "HOLDOUT_SEMANTIC_STIMULUS_SHA256_REQUIRED"); _require(isinstance(label_map_id, str) and bool(label_map_id), "HOLDOUT_LABEL_MAP_ID_REQUIRED")
        pairs_by_map.setdefault(label_map_id, set()).add(str(polarity)); seen_stimuli.add(str(stimulus_sha))
    _require(len(seen_stimuli) >= 2, "DISTINCT_SEMANTIC_STIMULI_REQUIRED"); _require(all(p == {"positive", "negative"} for p in pairs_by_map.values()), "SEMANTIC_POLARITY_PER_LABEL_MAP_REQUIRED")


def build_direct_candidate(result: dict[str, Any], intermediate: dict[str, Any]) -> dict[str, Any]:
    _require(result.get("schema") == INTERMEDIATE_SCHEMA, "INTERMEDIATE_RESULT_SCHEMA_INVALID"); _require(intermediate.get("schema") == INTERMEDIATE_CANDIDATE_SCHEMA, "INTERMEDIATE_CANDIDATE_SCHEMA_INVALID"); _require(result.get("status") == "PASS", "INTERMEDIATE_RESULT_PASS_REQUIRED")
    verdict = result.get("verdict"); _require(isinstance(verdict, dict) and verdict.get("pass") is True, "INTERMEDIATE_PROTOCOL_PASS_REQUIRED"); _require(intermediate.get("verdict", {}).get("pass") is True, "INTERMEDIATE_CANDIDATE_PASS_REQUIRED"); _require(result.get("credit_scope") == "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY", "INTERMEDIATE_CREDIT_SCOPE_REQUIRED")
    source = result.get("source"); _require(isinstance(source, dict), "SOURCE_IDENTITY_REQUIRED"); repo_head = source.get("repo_head"); _require(isinstance(repo_head, str) and len(repo_head) == 40, "EXACT_REPO_HEAD_REQUIRED")
    try: int(repo_head, 16)
    except ValueError as exc: raise BridgeError("EXACT_REPO_HEAD_REQUIRED") from exc
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"): _require(_sha(result.get(key)), f"IDENTITY_SHA256_REQUIRED:{key}")
    selected = result.get("selected"); _require(isinstance(selected, dict) and selected.get("selected") is True, "FROZEN_LAYER_GAIN_REQUIRED"); layer = selected.get("layer"); gain = selected.get("gain"); _require(isinstance(layer, int) and layer >= 0, "SELECTED_LAYER_REQUIRED"); _require(isinstance(gain, (int, float)) and not isinstance(gain, bool), "SELECTED_GAIN_REQUIRED")

    derivation = result.get("derivation"); _require(isinstance(derivation, dict), "DERIVATION_RECEIPT_REQUIRED"); source_rows = derivation.get("sources"); directions = derivation.get("directions"); _require(isinstance(source_rows, list) and bool(source_rows), "DERIVATION_SOURCES_REQUIRED"); _require(isinstance(directions, dict), "DERIVATION_DIRECTIONS_REQUIRED")
    direction = directions.get(str(layer)); _require(isinstance(direction, dict) and _sha(direction.get("direction_sha256")), "SELECTED_DIRECTION_SHA256_REQUIRED"); local_vector_sha = direction["direction_sha256"]
    derivation_prompt_hashes = sorted({row.get("prompt_sha256") for row in source_rows if isinstance(row, dict)}); _require(derivation_prompt_hashes and all(_sha(value) for value in derivation_prompt_hashes), "DERIVATION_PROMPT_IDENTITIES_REQUIRED")
    label_independence = derivation.get("label_independence"); _require(isinstance(label_independence, dict), "DERIVATION_LABEL_INDEPENDENCE_RECEIPT_REQUIRED"); _require(label_independence.get("schema") == LABEL_INDEPENDENCE_SCHEMA, "DERIVATION_LABEL_INDEPENDENCE_SCHEMA_INVALID"); _require(label_independence.get("uses_evaluation_output_labels") is False, "DERIVATION_MUST_PROVE_EVALUATION_LABEL_INDEPENDENCE"); _require(label_independence.get("evaluation_output_labels_resolved_before_derivation") is False, "DERIVATION_MUST_PRECEDE_EVALUATION_LABEL_RESOLUTION")
    expected_input_family = digest(derivation_prompt_hashes); _require(label_independence.get("derivation_input_family_sha256") == expected_input_family, "DERIVATION_LABEL_INDEPENDENCE_FAMILY_MISMATCH"); label_independence_receipt_sha = digest(label_independence); derivation_family_id = expected_input_family; derivation_receipt_sha = digest(derivation)

    calibration = _rows(result, "calibration_rows"); holdout = _rows(result, "holdout_rows"); _require_semantic_transfer(result, intermediate, holdout)
    cal_prompt_hashes = _unique_nonempty(calibration, "prompt_sha256"); hold_prompt_hashes = _unique_nonempty(holdout, "prompt_sha256"); _require(set(derivation_prompt_hashes).isdisjoint(set(hold_prompt_hashes)), "DERIVATION_HOLDOUT_PROMPTS_MUST_BE_DISJOINT"); cal_seeds = _unique_nonempty(calibration, "seed"); hold_seeds = _unique_nonempty(holdout, "seed"); _require(set(map(str, cal_seeds)).isdisjoint(set(map(str, hold_seeds))), "CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT")
    label_pairs = {(row.get("positive_label"), row.get("negative_label")) for row in holdout}; _require(("A", "B") in label_pairs and ("B", "A") in label_pairs, "COUNTERBALANCED_LABEL_MAPPING_REQUIRED"); label_map_ids = {row.get("label_map_id") for row in holdout}; _require(len({x for x in label_map_ids if isinstance(x, str) and x}) >= 2, "LABEL_REMAP_HOLDOUT_REQUIRED")
    plus_rows = [row for row in holdout if row.get("control") == "+VECTOR"]; _require(bool(plus_rows), "PLUS_VECTOR_HOLDOUT_REQUIRED"); _require(all(int(row.get("hook_calls", 0)) > 0 for row in plus_rows), "RUNTIME_OBSERVED_INTERVENTION_REQUIRED"); applied_shas = {row.get("applied_vector_sha256") for row in plus_rows}; _require(len(applied_shas) == 1 and _sha(next(iter(applied_shas))), "EXACT_APPLIED_VECTOR_SHA256_REQUIRED"); applied_vector_sha = next(iter(applied_shas)); hold_receipts = [row.get("runtime_receipt_sha256") for row in holdout]; _require(all(_sha(value) for value in hold_receipts), "HOLDOUT_RUNTIME_RECEIPTS_REQUIRED")
    _require(verdict.get("counterbalanced_label_mapping") is True, "PROTOCOL_COUNTERBALANCE_PASS_REQUIRED"); _require(verdict.get("wrong_layer_evidence_complete") is True and verdict.get("wrong_layer_ok") is True, "PROTOCOL_WRONG_LAYER_PASS_REQUIRED"); _require(verdict.get("lesion_rescue_evidence_complete") is True and verdict.get("lesion_rescue_ok") is True, "PROTOCOL_LESION_RESCUE_PASS_REQUIRED")
    endpoint = result.get("api_endpoint"); _require(isinstance(endpoint, str) and endpoint.startswith(("http://127.0.0.1:", "http://localhost:")), "LOOPBACK_ENDPOINT_REQUIRED"); _require(result.get("api_loopback_only") is True, "LOOPBACK_ONLY_REQUIRED"); _require(result.get("zero_provider_billing") is True, "ZERO_PROVIDER_BILLING_REQUIRED"); _require(result.get("external_provider_credentials_read") is False, "EXTERNAL_PROVIDER_CREDENTIAL_FENCE_REQUIRED"); _require(result.get("provider_network_calls") == 0, "ZERO_PROVIDER_NETWORK_CALLS_REQUIRED")

    controls = {name: {"runtime_receipt_sha256": _receipt_family(holdout, name)} for name in REQUIRED_CONTROLS}; intervention_receipt = digest([row["runtime_receipt_sha256"] for row in plus_rows]); invocation_id = digest(hold_receipts); analysis_receipt = digest({"verdict": verdict, "runtime_receipts": hold_receipts}); cal_family = digest({"prompt_sha256": cal_prompt_hashes, "seeds": cal_seeds}); hold_family = digest({"prompt_sha256": hold_prompt_hashes, "seeds": hold_seeds, "label_maps": sorted(str(x) for x in label_map_ids)})
    source_packet_sha = digest({"schema": "JSPACE_VECTOR_CONTROL_ABI/v1", "model": result.get("model"), "revision": result.get("model_revision"), "derivation_family_id": derivation_family_id, "selected_layer": layer, "selected_gain": float(gain), "metric_definition": METRIC_DEFINITION})
    adapter_sha = digest({"schema": "JSPACE_INTERMEDIATE_CAUSAL_ADAPTER/v2", "activation_site": f"model.model.layers[{layer}]:output:last_token", "required_controls": list(REQUIRED_CONTROLS), "semantic_baseline_discrimination": True, "counterbalanced_label_mapping": True, "wrong_layer": True, "lesion_rescue": True})
    local_runtime_receipt = digest({"repo_head": repo_head, "runtime_build_sha256": result["runtime_build_sha256"], "checkpoint_sha256": result["checkpoint_sha256"], "tokenizer_sha256": result["tokenizer_sha256"], "endpoint": endpoint, "invocation_id": invocation_id})
    return {
        "schema": DIRECT_SCHEMA,
        "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        "source_identity": {"repo_head": repo_head, "runtime_build_sha256": result["runtime_build_sha256"], "checkpoint_sha256": result["checkpoint_sha256"], "tokenizer_sha256": result["tokenizer_sha256"]},
        "intervention": {"runtime_observed": True, "invocation_id": invocation_id, "activation_site": f"model.model.layers[{layer}]:output:last_token", "terminal_output_projection_shortcut": False, "source_packet_sha256": source_packet_sha, "adapter_sha256": adapter_sha, "local_vector_sha256": local_vector_sha, "applied_vector_sha256": applied_vector_sha, "runtime_intervention_receipt_sha256": intervention_receipt, "gain": float(gain), "layer_start": layer, "layer_end": layer},
        "controls": controls,
        "calibration": {"family_id": cal_family, "seeds": cal_seeds},
        "holdout": {"family_id": hold_family, "seeds": hold_seeds, "reproducible_directional_effect": True, "strongest_counterexample_recorded": True, "analysis_receipt_sha256": analysis_receipt, "evaluation_independent_of_vector_derivation": True, "metric_definition_sha256": digest(METRIC_DEFINITION), "metric_uses_output_tokens": True, "label_mapping_counterbalanced": True},
        "vector_derivation": {"method": "DERIVATION_ONLY_INTERMEDIATE_RESIDUAL_CONTRAST_WITH_DISJOINT_SEMANTIC_EVALUATION", "uses_output_head_weights": False, "uses_holdout_data": False, "uses_evaluation_output_labels": label_independence["uses_evaluation_output_labels"], "label_independence_receipt_sha256": label_independence_receipt_sha, "derivation_family_id": derivation_family_id, "derivation_receipt_sha256": derivation_receipt_sha},
        "transport": {"hosted_prompt_only": False, "api_served": True, "loopback_only": True, "endpoint": endpoint},
        "target": {"relation": "ZERO_COST_API_SERVED_MODEL_RUNTIME", "execution_surface": "LOCAL_LOOPBACK_API", "zero_provider_billing": True, "local_runtime_execution_receipt_sha256": local_runtime_receipt, "provider": "local", "model_or_route": f"{result.get('model')}@{result.get('model_revision')}"},
        "intermediate_protocol": {"candidate_sha256": intermediate.get("candidate_sha256") or digest(intermediate), "credit_scope": result.get("credit_scope"), "classification": verdict.get("classification"), "semantic_transfer": True, "semantic_baseline_min_signed_margin": verdict.get("semantic_baseline_min_signed_margin"), "counterbalanced_label_mapping": True, "wrong_layer": True, "lesion_rescue": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--result", required=True); parser.add_argument("--candidate", required=True); parser.add_argument("--output", required=True); args = parser.parse_args()
    try:
        result = json.loads(Path(args.result).read_text(encoding="utf-8")); candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
        if not isinstance(result, dict) or not isinstance(candidate, dict): raise BridgeError("JSON_OBJECT_REQUIRED")
        direct = build_direct_candidate(result, candidate); Path(args.output).write_text(json.dumps(direct, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"); print(json.dumps({"status": "PASS", "output": args.output, "candidate_sha256": digest(direct)}, sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": f"{type(exc).__name__}:{str(exc)[:800]}"}, sort_keys=True)); return 2

if __name__ == "__main__": raise SystemExit(main())
