#!/usr/bin/env python3
"""Deterministic reference algorithm for configurable public state boxes.

This module is a donor/reference implementation for the Mini Entity pipeline. It is NOT
a second runtime authority and performs no persistence. Canonical/native integration must
build the same payload from the admitted canonical snapshot and persist the post,
self-report, state-box payload, event consumption, continuity and generation CAS in one
transaction.

Hard epistemic rule: SYSTEM_MEASUREMENT != MODEL_SELF_REPORT.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any


UNKNOWN_WORDS = {"UNKNOWN", "MISSING", "UNMEASURED"}
ERROR_WORDS = {"ERROR", "FAILED_SENSOR", "DEGRADED_ERROR"}


class StateBoxError(ValueError):
    pass


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _clean_text(value: Any, limit: int = 160) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    f = float(value)
    return f if math.isfinite(f) else None


def _normalize_system_field(value: Any, *, metadata: bool) -> dict[str, Any]:
    if metadata:
        if value is None:
            return {"status": "UNKNOWN", "value": None}
        if isinstance(value, dict) and "status" in value:
            status = str(value.get("status", "UNKNOWN")).upper()
            return {"status": status, "value": value.get("value") if status == "VERIFIED" else None}
        return {"status": "META", "value": value}

    if not isinstance(value, dict) or "status" not in value:
        return {"status": "UNKNOWN", "value": None}
    status = str(value.get("status", "UNKNOWN")).upper()
    if status != "VERIFIED":
        return {"status": status, "value": None}
    return {"status": "VERIFIED", "value": value.get("value")}


def _normalize_self_report_field(value: Any) -> dict[str, Any]:
    if value is None:
        return {"status": "UNKNOWN", "value": None}
    if isinstance(value, dict):
        status = str(value.get("status", "REPORTED")).upper()
        if status in UNKNOWN_WORDS:
            return {"status": "UNKNOWN", "value": None}
        if status not in {"REPORTED", "VERIFIED"}:
            return {"status": status, "value": value.get("value")}
        value = value.get("value")
    if isinstance(value, str) and value.upper() in UNKNOWN_WORDS:
        return {"status": "UNKNOWN", "value": None}
    number = _finite_number(value)
    if number is not None:
        if number < 0.0 or number > 1.0:
            raise StateBoxError("SELF_REPORT_NUMBER_OUT_OF_RANGE")
        return {"status": "REPORTED", "value": number}
    return {"status": "REPORTED", "value": _clean_text(value)}


def _available_number(item: dict[str, Any], *, system: bool) -> float | None:
    allowed = {"VERIFIED"} if system else {"REPORTED", "VERIFIED"}
    if item.get("status") not in allowed:
        return None
    return _finite_number(item.get("value"))


def _delta(current: dict[str, Any], previous: dict[str, Any] | None, *, system: bool) -> float | None:
    if previous is None:
        return None
    now = _available_number(current, system=system)
    before = _available_number(previous, system=system)
    if now is None or before is None:
        return None
    return now - before


def _fmt_number(value: float) -> str:
    return f"{value:.2f}"


def _fmt_delta(value: float | None) -> str:
    if value is None:
        return ""
    return f"   Δ {value:+.2f}"


def _fmt_system(item: dict[str, Any], delta: float | None) -> str:
    status = str(item.get("status", "UNKNOWN"))
    value = item.get("value")
    if status == "VERIFIED":
        number = _finite_number(value)
        rendered = _fmt_number(number) if number is not None else _clean_text(value)
        return f"VERIFIED {rendered}{_fmt_delta(delta)}"
    if status == "META":
        return _clean_text(value)
    if status in ERROR_WORDS or status.startswith("ERROR"):
        return "ERROR"
    return "UNKNOWN"


def _fmt_self(item: dict[str, Any], delta: float | None) -> str:
    if item.get("status") not in {"REPORTED", "VERIFIED"}:
        return "UNKNOWN"
    value = item.get("value")
    number = _finite_number(value)
    rendered = _fmt_number(number) if number is not None else _clean_text(value)
    return rendered + _fmt_delta(delta)


def _previous_track(previous: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not isinstance(previous, dict):
        return {}
    track = previous.get(name)
    return track if isinstance(track, dict) else {}


def build_state_box(
    config: dict[str, Any],
    system_state: dict[str, Any],
    model_self_report: dict[str, Any],
    *,
    previous_study_payload: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build public-safe rendered text and machine-readable study payload.

    `system_state` must be constructed by the pipeline. Non-metadata canonical fields
    require explicit `{status: VERIFIED, value: ...}` to become measured values. Missing,
    malformed or non-VERIFIED fields remain UNKNOWN/ERROR and are never imputed.
    """
    if not config.get("enabled"):
        return {"ok": True, "enabled": False, "rendered_text": "", "study_payload": None}
    if config.get("epistemic_law") != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
        raise StateBoxError("EPISTEMIC_LAW_MISSING")

    canonical_fields = [str(x) for x in config.get("canonical_fields", [])]
    metadata_fields = {str(x) for x in config.get("canonical_metadata_fields", [])}
    self_fields = [str(x) for x in config.get("self_report_fields", [])]
    if not canonical_fields or not self_fields:
        raise StateBoxError("EMPTY_FIELD_ALLOWLIST")

    normalized_system = {
        field: _normalize_system_field(system_state.get(field), metadata=field in metadata_fields)
        for field in canonical_fields
    }
    normalized_self = {
        field: _normalize_self_report_field(model_self_report.get(field))
        for field in self_fields
    }

    previous_system = _previous_track(previous_study_payload, "system_state")
    previous_self = _previous_track(previous_study_payload, "model_self_report")

    system_deltas: dict[str, float] = {}
    self_deltas: dict[str, float] = {}
    if config.get("delta", {}).get("show_previous_post_delta", True):
        for field, item in normalized_system.items():
            d = _delta(item, previous_system.get(field), system=True)
            if d is not None:
                system_deltas[field] = d
        for field, item in normalized_self.items():
            d = _delta(item, previous_self.get(field), system=False)
            if d is not None:
                self_deltas[field] = d

    ctx = dict(context or {})
    for field in config.get("interpretation", {}).get("confound_fields", []):
        if field not in ctx and field in system_state:
            raw = system_state.get(field)
            if isinstance(raw, dict):
                ctx[field] = raw.get("value")
            else:
                ctx[field] = raw

    previous_context = _previous_track(previous_study_payload, "context")
    evaluation_lines: list[str] = []
    interpretation = config.get("interpretation", {})
    templates = interpretation.get("templates", {})

    measured_fields = [f for f in canonical_fields if f not in metadata_fields]
    unknown_count = sum(1 for f in measured_fields if normalized_system[f].get("status") != "VERIFIED")
    if unknown_count and templates.get("unknown"):
        evaluation_lines.append(str(templates["unknown"]).format(count=unknown_count))

    comparison_count = 0
    for rule in interpretation.get("comparison_rules", []):
        sf = str(rule.get("system_field", ""))
        rf = str(rule.get("self_report_field", ""))
        if sf not in normalized_system or rf not in normalized_self:
            continue
        sv = _available_number(normalized_system[sf], system=True)
        rv = _available_number(normalized_self[rf], system=False)
        if sv is None or rv is None:
            continue
        comparison_count += 1
        label = _clean_text(rule.get("label", rule.get("id", sf)))
        high = float(rule.get("high_threshold", 0.6))
        gap = float(rule.get("gap_threshold", 0.25))
        if sv >= high and rv >= high and templates.get("congruent_high"):
            evaluation_lines.append(str(templates["congruent_high"]).format(label=label))
        elif abs(sv - rv) >= gap and templates.get("divergent"):
            evaluation_lines.append(
                str(templates["divergent"]).format(
                    label=label,
                    system=_fmt_number(sv),
                    self_report=_fmt_number(rv),
                )
            )

    changed_confounds: list[str] = []
    for field in interpretation.get("confound_fields", []):
        if field not in ctx or field not in previous_context:
            continue
        if ctx[field] != previous_context[field]:
            changed_confounds.append(str(field))
    if changed_confounds and templates.get("confound"):
        evaluation_lines.append(str(templates["confound"]).format(fields=", ".join(changed_confounds)))

    calibration_fields = interpretation.get("calibration_self_report_fields", [])
    threshold = float(interpretation.get("calibration_threshold", 0.65))
    strong_report = any(
        (_available_number(normalized_self.get(str(field), {}), system=False) or -1.0) >= threshold
        for field in calibration_fields
    )
    if strong_report and templates.get("self_report_calibration"):
        evaluation_lines.append(str(templates["self_report_calibration"]))

    meaningful = float(config.get("delta", {}).get("meaningful_numeric_delta", 0.15))
    candidates = [(field, delta) for field, delta in system_deltas.items() if abs(delta) >= meaningful]
    candidates.sort(key=lambda pair: abs(pair[1]), reverse=True)
    if candidates and templates.get("change"):
        field, d = candidates[0]
        evaluation_lines.append(str(templates["change"]).format(field=field, delta=f"{d:+.2f}"))
        if templates.get("single_delta_not_trend"):
            evaluation_lines.append(str(templates["single_delta_not_trend"]))

    if comparison_count == 0 and templates.get("no_comparison"):
        evaluation_lines.append(str(templates["no_comparison"]))

    max_lines = int(config.get("render", {}).get("max_evaluation_lines", 5))
    if max_lines < 1:
        raise StateBoxError("INVALID_MAX_EVALUATION_LINES")
    evaluation_lines = evaluation_lines[:max_lines]

    config_hash = _canonical_hash(config)
    study_payload = {
        "schema": "clay-state-box-study-payload/v1",
        "profile_id": config.get("profile_id"),
        "state_box_config_hash": config_hash,
        "epistemic_law": config["epistemic_law"],
        "system_state": normalized_system,
        "model_self_report": normalized_self,
        "system_deltas": system_deltas,
        "self_report_deltas": self_deltas,
        "context": {str(k): ctx.get(k) for k in interpretation.get("confound_fields", []) if k in ctx},
        "evaluation": {
            "comparison_count": comparison_count,
            "unknown_system_measurement_count": unknown_count,
            "changed_confounds": changed_confounds,
            "lines": evaluation_lines,
        },
    }
    payload_hash = _canonical_hash(study_payload)
    study_payload["payload_hash"] = payload_hash

    title = _clean_text(config.get("render", {}).get("title", "STATE"))
    generation = normalized_system.get("generation", {}).get("value")
    if generation is not None:
        title += " — generation " + _clean_text(generation)

    sections = config.get("render", {}).get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "AUSWERTUNG"])
    system_heading = _clean_text(sections[0]) if len(sections) > 0 else "SYSTEM STATE"
    self_heading = _clean_text(sections[1]) if len(sections) > 1 else "MODEL SELF-REPORT"
    evaluation_heading = _clean_text(sections[2]) if len(sections) > 2 else "EVALUATION"

    lines = [title, system_heading]
    width = max([len(f) for f in canonical_fields] + [1])
    for field in canonical_fields:
        lines.append(f"{field.ljust(width)} = {_fmt_system(normalized_system[field], system_deltas.get(field))}")
    lines.append("")
    lines.append(self_heading)
    width = max([len(f) for f in self_fields] + [1])
    for field in self_fields:
        lines.append(f"{field.ljust(width)} = {_fmt_self(normalized_self[field], self_deltas.get(field))}")
    lines.append("")
    lines.append(evaluation_heading)
    if evaluation_lines:
        lines.extend("- " + _clean_text(line, 500) for line in evaluation_lines)
    else:
        lines.append("- UNKNOWN")

    box_content = "\n".join(lines)
    fence = _clean_text(config.get("render", {}).get("fence", "text"), 24)
    rendered_text = f"```{fence}\n{box_content}\n```"

    return {
        "ok": True,
        "enabled": True,
        "rendered_text": rendered_text,
        "box_content": box_content,
        "study_payload": study_payload,
        "study_payload_hash": payload_hash,
    }


__all__ = ["StateBoxError", "build_state_box"]
