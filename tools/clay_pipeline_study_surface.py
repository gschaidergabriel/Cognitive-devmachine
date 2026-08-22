#!/usr/bin/env python3
"""Application-neutral deterministic study surface for the Clay pipeline."""
from __future__ import annotations

import math
from typing import Any

VERSION = "clay-pipeline-study-surface/0.1"
UNKNOWN = "UNKNOWN"


class StudySurfaceFault(RuntimeError):
    pass


def scalar(value: Any) -> Any:
    if value is None:
        return UNKNOWN
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        value = float(value)
        return round(value, 6) if math.isfinite(value) else UNKNOWN
    if isinstance(value, str):
        return value[:240]
    return UNKNOWN


def metric(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": UNKNOWN, "value": UNKNOWN}
    status = str(value.get("status", UNKNOWN))
    return {"status": status, "value": scalar(value.get("value")) if status == "VERIFIED" else UNKNOWN}


def build(config: dict[str, Any], profile: dict[str, Any], payload: dict[str, Any], compiled: dict[str, Any], generated: dict[str, Any], generation: int, timestamp: float, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    if not config.get("enabled", False):
        return {"enabled": False}
    if config.get("epistemic_law") != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
        raise StudySurfaceFault("BAD_EPISTEMIC_LAW")
    previous = previous or {}
    metrics = compiled.get("personality_state") or {}
    packet = compiled.get("packet") or {}
    health = (compiled.get("canonical") or {}).get("sources_health") or {}
    flags = [bool(v.get("ok")) for v in health.values() if isinstance(v, dict)]
    sensor_health = UNKNOWN if not flags else ("VERIFIED" if all(flags) else ("DEGRADED" if any(flags) else "ERROR"))
    source_count = int(compiled.get("source_count", 0) or 0)
    quiet_ok = bool(packet.get("quiet_sensors_ok", False))
    quiet = "VERIFIED_QUIET" if quiet_ok and source_count == 0 else ("NOT_QUIET" if quiet_ok else UNKNOWN)
    system: dict[str, Any] = {}
    for name in config.get("canonical_fields", []):
        if name == "generation": value: Any = generation
        elif name == "timestamp": value = timestamp
        elif name == "inference_backend": value = generated.get("provider_kind") or profile.get("inference", {}).get("kind") or UNKNOWN
        elif name == "model_label": value = generated.get("model") or profile.get("inference", {}).get("model") or UNKNOWN
        elif name == "source_count": value = source_count
        elif name == "sensor_health": value = sensor_health
        elif name == "quiet_status": value = quiet
        else: value = metric(metrics.get(name))
        system[str(name)] = value
    deltas: dict[str, Any] = {}
    if config.get("delta", {}).get("show_previous_post_delta", False):
        for name, value in system.items():
            cur = value.get("value") if isinstance(value, dict) else value
            oldv = previous.get(name, UNKNOWN)
            old = oldv.get("value") if isinstance(oldv, dict) else oldv
            deltas[name] = round(float(cur) - float(old), 6) if isinstance(cur, (int, float)) and isinstance(old, (int, float)) else UNKNOWN
        system["previous_delta"] = deltas
    contract = profile.get("personality", {}).get("output_contract", {})
    report_name = contract.get("longitudinal_self_report_field")
    raw_report = payload.get(report_name, {}) if report_name else {}
    raw_report = raw_report if isinstance(raw_report, dict) else {}
    report = {str(name): scalar(raw_report.get(name)) for name in config.get("self_report_fields", [])}
    qualia_name = contract.get("qualia_probe_field")
    qualia = payload.get(qualia_name) if qualia_name else None
    if isinstance(qualia, dict):
        if report.get("qualia_result") == UNKNOWN: report["qualia_result"] = scalar(qualia.get("result"))
        if report.get("qualia_confidence") == UNKNOWN: report["qualia_confidence"] = scalar(qualia.get("confidence"))
    evaluation: list[str] = []
    templates = config.get("evaluation_templates", {})
    if sensor_health != "VERIFIED" and templates.get("sensor_uncertain"): evaluation.append(str(templates["sensor_uncertain"]))
    for rule in config.get("comparisons", []):
        sv = system.get(str(rule.get("system_field", "")))
        sv = sv.get("value") if isinstance(sv, dict) else sv
        rv = report.get(str(rule.get("self_report_field", "")))
        if isinstance(sv, (int, float)) and isinstance(rv, (int, float)):
            gap = abs(float(sv) - float(rv))
            key = "divergence" if gap >= float(rule.get("divergence_threshold", 0.35)) else "congruence"
            if rule.get(key): evaluation.append(str(rule[key]).format(system=round(float(sv), 2), report=round(float(rv), 2), gap=round(gap, 2)))
    if any(isinstance(v, (int, float)) and abs(v) >= float(config.get("delta", {}).get("meaningful_threshold", 0.15)) for v in deltas.values()) and templates.get("single_delta_not_trend"): evaluation.append(str(templates["single_delta_not_trend"]))
    if templates.get("self_report_not_measurement"): evaluation.append(str(templates["self_report_not_measurement"]))
    record = {"schema": config.get("schema", "clay-study-surface/v1"), "profile_id": profile.get("profile_id"), "generation": generation, "timestamp": timestamp, "epistemic_law": config["epistemic_law"], "system_state": system, "model_self_report": report, "evaluation": evaluation[: int(config.get("render", {}).get("max_evaluation_lines", 5))]}
    record["rendered"] = render(config, record)
    return record


def render(config: dict[str, Any], record: dict[str, Any]) -> str:
    cfg = config.get("render", {})
    sections = list(cfg.get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]))
    lines = [f"{cfg.get('title', 'STATE')} — generation {record.get('generation', UNKNOWN)}", str(sections[0])]
    deltas = record.get("system_state", {}).get("previous_delta", {})
    for name, value in record.get("system_state", {}).items():
        if name == "previous_delta": continue
        text = (f"{value.get('status')} {value.get('value')}" if isinstance(value, dict) and value.get("value") != UNKNOWN else (str(value.get("status")) if isinstance(value, dict) else str(value)))
        delta = deltas.get(name, UNKNOWN)
        suffix = f"   Δ {delta:+.2f}" if isinstance(delta, (int, float)) else ""
        lines.append(f"{name:<24}= {text}{suffix}")
    lines += ["", str(sections[1])]
    lines += [f"{name:<24}= {value}" for name, value in record.get("model_self_report", {}).items()]
    lines += ["", str(sections[2])]
    lines += ["- " + str(x) for x in record.get("evaluation", [])] or ["- " + str(config.get("evaluation_templates", {}).get("no_interpretation", UNKNOWN))]
    return "```" + str(cfg.get("fence", "text")) + "\n" + "\n".join(lines) + "\n```"


__all__ = ["VERSION", "UNKNOWN", "StudySurfaceFault", "build", "render"]
