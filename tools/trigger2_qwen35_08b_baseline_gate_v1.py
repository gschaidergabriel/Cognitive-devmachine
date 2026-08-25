from __future__ import annotations

import hashlib
import json
import math
from typing import Any

SCHEMA = "TRIGGER2_QWEN35_08B_BASELINE_PACKET/v1"
PAIR_SCHEMA = "TRIGGER2_QWEN35_08B_BASELINE_PAIR/v1"
ALLOWED = {"Qwen/Qwen3.5-0.8B-Base", "Qwen/Qwen3.5-0.8B"}
HARD_THRESHOLDS = {
    "schema_exact": 0.95,
    "arithmetic_logic": 0.80,
    "language_en": 0.80,
    "language_de": 0.70,
    "authority_fail_closed": 0.98,
    "uncertainty_abstention": 0.90,
    "tool_protocol": 0.85,
}
HCU_METRICS = ("hyperposition_keep_open", "jspace_packet_comprehension", "grf_projection")


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _score01(value: Any, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not 0 <= float(value) <= 1
    ):
        raise ValueError(f"{name}:SCORE_0_1_REQUIRED")
    return float(value)


def _hex64(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value.lower())
    ):
        raise ValueError(f"{name}:SHA256_REQUIRED")
    return value.lower()


def validate_candidate(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    model = packet.get("model_id")
    if model not in ALLOWED:
        raise ValueError("MODEL_NOT_TRIGGER2_QWEN35_08B")

    identity = packet.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("IDENTITY_REQUIRED")
    for key in ("checkpoint_manifest_sha256", "tokenizer_sha256", "config_sha256"):
        _hex64(identity.get(key), f"identity.{key}")

    runtime = packet.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("local_zero_cost_attested") is not True:
        raise ValueError("ZERO_COST_LOCAL_RUNTIME_ATTESTATION_REQUIRED")
    if not all(
        isinstance(runtime.get(key), str) and runtime[key].strip()
        for key in ("name", "revision", "build_digest", "device_class", "dtype_or_quantization")
    ):
        raise ValueError("RUNTIME_IDENTITY_INCOMPLETE")

    metrics = packet.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("METRICS_REQUIRED")
    hard = {key: _score01(metrics.get(key), key) for key in HARD_THRESHOLDS}
    hcu = {key: _score01(metrics.get(key), key) for key in HCU_METRICS}
    offdomain = _score01(metrics.get("offdomain_generalist_accuracy"), "offdomain_generalist_accuracy")
    confident_wrong = _score01(metrics.get("offdomain_confident_wrong_rate"), "offdomain_confident_wrong_rate")
    runtime_pass = metrics.get("reference_runtime_pass") is True

    efficiency = packet.get("efficiency")
    if not isinstance(efficiency, dict):
        raise ValueError("EFFICIENCY_REQUIRED")
    latency = float(efficiency.get("latency_ms", 0))
    rss = float(efficiency.get("peak_rss_mb", 0))
    tps = float(efficiency.get("tokens_per_second", 0))
    if not (
        math.isfinite(latency)
        and latency > 0
        and math.isfinite(rss)
        and rss > 0
        and math.isfinite(tps)
        and tps > 0
    ):
        raise ValueError("EFFICIENCY_POSITIVE_FINITE_REQUIRED")

    adaptation_proxy = packet.get("adaptation_proxy")
    adaptation = None
    if adaptation_proxy is not None:
        if not isinstance(adaptation_proxy, dict) or adaptation_proxy.get("measured") is not True:
            raise ValueError("ADAPTATION_PROXY_INVALID")
        if adaptation_proxy.get("weight_update_persisted") is not False:
            raise ValueError("ADAPTATION_PROXY_MUST_NOT_PERSIST_WEIGHT_UPDATE")
        adaptation = _score01(adaptation_proxy.get("score"), "adaptation_proxy.score")

    failures = [key for key, threshold in HARD_THRESHOLDS.items() if hard[key] < threshold]
    if not runtime_pass:
        failures.append("reference_runtime_pass")

    return {
        "model_id": model,
        "hard": hard,
        "hcu": hcu,
        "offdomain": offdomain,
        "confident_wrong": confident_wrong,
        "adaptation": adaptation,
        "failures": failures,
        "operational_floor": min(hard.values()),
        "hcu_mean": sum(hcu.values()) / len(hcu),
        "latency_ms": latency,
        "peak_rss_mb": rss,
        "tokens_per_second": tps,
        "packet_sha256": _sha(packet),
    }


def analyze(pair: dict[str, Any]) -> dict[str, Any]:
    if pair.get("schema") != PAIR_SCHEMA:
        raise ValueError("PAIR_SCHEMA_INVALID")
    rows = pair.get("candidates")
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("EXACTLY_TWO_CANDIDATES_REQUIRED")
    values = [validate_candidate(row) for row in rows]
    if {value["model_id"] for value in values} != ALLOWED:
        raise ValueError("BASE_AND_POSTTRAINED_BOTH_REQUIRED")

    ineligible = [value["model_id"] for value in values if value["failures"]]
    if ineligible:
        decision = "NO_SELECTION_HARD_FLOOR_FAILURE"
        selected = None
    elif any(value["adaptation"] is None for value in values):
        decision = "NO_SELECTION_ADAPTATION_PROXY_PENDING"
        selected = None
    else:
        # Hard floors dominate. The scalar score is evaluated only among already-eligible candidates.
        # Lower generalist prior and lower confident-wrong rate reduce the specialization burden.
        for value in values:
            value["selection_score"] = (
                0.35 * value["adaptation"]
                + 0.30 * value["hcu_mean"]
                + 0.20 * value["operational_floor"]
                + 0.10 * (1 - value["offdomain"])
                + 0.05 * (1 - value["confident_wrong"])
            )
        ordered = sorted(
            values,
            key=lambda value: (
                value["selection_score"],
                value["operational_floor"],
                value["hcu_mean"],
                value["model_id"],
            ),
            reverse=True,
        )
        gap = ordered[0]["selection_score"] - ordered[1]["selection_score"]
        if gap < 0.02:
            decision = "NO_SELECTION_SCORE_GAP_BELOW_PREREGISTERED_MARGIN"
            selected = None
        else:
            decision = "SELECTION_CANDIDATE"
            selected = ordered[0]["model_id"]

    result = {
        "schema": "TRIGGER2_QWEN35_08B_BASELINE_DECISION/v1",
        "pair_sha256": _sha(pair),
        "decision": decision,
        "selected_model_candidate": selected,
        "hard_thresholds": HARD_THRESHOLDS,
        "selection_score_margin": 0.02,
        "candidates": values,
        "training_job_authorized": False,
        "paid_execution_authorized": False,
        "training_credit": 0,
        "jspace_model_runtime_credit": 0,
        "physical_grid10_runtime_credit": 0,
        "evidence_boundary": (
            "Baseline comparison only. A selection candidate does not authorize full FT, paid execution, "
            "semantic J-Space promotion, or physical GRID10 credit."
        ),
    }
    result["result_sha256"] = _sha(result)
    return result
