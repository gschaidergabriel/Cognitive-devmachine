#!/usr/bin/env python3
"""Generic public study-surface support for persistent Clay pipeline profiles.

This module is deliberately application-neutral. Labels, visible fields, comparison
pairs and evaluation wording are profile data. Canonical measurements and model
self-reports stay structurally separate and are never promoted across that boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import sqlite3
from typing import Any, Mapping, Sequence

VERSION = "clay-study-surface/0.1"

_ALLOWED_STATUS = {"VERIFIED", "DEGRADED", "ERROR", "UNKNOWN"}
_SELF_REPORT_ENUM = {"REPORTED", "FAILED", "UNKNOWN"}


class StudySurfaceError(ValueError):
    pass


@dataclass(frozen=True)
class Measurement:
    status: str
    value: float | None


def _finite_scale01(value: Any) -> float:
    if isinstance(value, bool):
        raise StudySurfaceError("BOOLEAN_NOT_SCALE")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise StudySurfaceError("NOT_NUMERIC_SCALE") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise StudySurfaceError("SCALE_OUT_OF_RANGE")
    return number


def _measurement(value: Any) -> Measurement | None:
    if not isinstance(value, Mapping) or "status" not in value:
        return None
    status = str(value.get("status", "UNKNOWN")).upper()
    if status not in _ALLOWED_STATUS:
        raise StudySurfaceError("BAD_MEASUREMENT_STATUS:" + status)
    if status != "VERIFIED":
        # An implementation may carry a numeric placeholder internally for UNKNOWN.
        # The public/study surface must erase it so UNKNOWN can never look measured.
        return Measurement(status=status, value=None)
    raw = value.get("value")
    if raw is None:
        raise StudySurfaceError("VERIFIED_WITHOUT_VALUE")
    return Measurement(status=status, value=_finite_scale01(raw))


def normalize_canonical(
    raw: Mapping[str, Any],
    allowed_fields: Sequence[str],
) -> dict[str, Any]:
    """Allowlist public canonical values while preserving epistemic typing."""
    out: dict[str, Any] = {}
    for field in allowed_fields:
        if field not in raw:
            out[field] = {"status": "UNKNOWN", "value": None}
            continue
        value = raw[field]
        measured = _measurement(value)
        if measured is not None:
            out[field] = {"status": measured.status, "value": measured.value}
        elif isinstance(value, (str, int, float)) or value is None:
            # Metadata fields such as generation/model/source_count are admitted by
            # profile allowlist and are not silently interpreted as measurements.
            if isinstance(value, float) and not math.isfinite(value):
                raise StudySurfaceError("NONFINITE_CANONICAL_METADATA")
            out[field] = value
        else:
            raise StudySurfaceError("UNSAFE_CANONICAL_VALUE:" + field)
    return out


def normalize_self_report(
    raw: Mapping[str, Any] | None,
    allowed_fields: Sequence[str],
) -> dict[str, Any]:
    """Validate model self-report without turning it into canonical evidence."""
    raw = raw or {}
    out: dict[str, Any] = {}
    for field in allowed_fields:
        value = raw.get(field, "UNKNOWN")
        if isinstance(value, str):
            upper = value.upper()
            if upper not in _SELF_REPORT_ENUM:
                raise StudySurfaceError("BAD_SELF_REPORT_ENUM:" + field)
            out[field] = upper
        else:
            out[field] = _finite_scale01(value)
    return out


def _verified_number(value: Any) -> float | None:
    if not isinstance(value, Mapping):
        return None
    if str(value.get("status", "")).upper() != "VERIFIED":
        return None
    raw = value.get("value")
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def metric_deltas(
    current: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
) -> dict[str, float]:
    """Compute deltas only when both sides are explicitly VERIFIED measurements."""
    if not previous:
        return {}
    out: dict[str, float] = {}
    for field, now in current.items():
        before = previous.get(field)
        a = _verified_number(now)
        b = _verified_number(before)
        if a is not None and b is not None:
            out[field] = round(a - b, 6)
    return out


def context_confounds(
    current: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    fields: Sequence[str],
) -> list[str]:
    if not previous:
        return []
    changed: list[str] = []
    for field in fields:
        if field in current and field in previous and current[field] != previous[field]:
            changed.append(field)
    return changed


def deterministic_evaluation(
    *,
    canonical: Mapping[str, Any],
    self_report: Mapping[str, Any],
    config: Mapping[str, Any],
    deltas: Mapping[str, float],
    confounds: Sequence[str],
) -> list[str]:
    """Return bounded profile-driven comparison statements.

    The engine supplies comparison categories, but all semantic field pairing and
    visible wording come from profile configuration.
    """
    rules = config.get("deterministic_evaluation", {})
    lines: list[str] = []

    uncertain = [
        field
        for field, value in canonical.items()
        if isinstance(value, Mapping) and str(value.get("status", "")).upper() in {"UNKNOWN", "ERROR", "DEGRADED"}
    ]
    if uncertain:
        template = str(rules.get("uncertainty_template", "Uncertainty: {fields}."))
        lines.append(template.format(fields=", ".join(uncertain)))

    for pair in rules.get("comparisons", []):
        system_field = str(pair["system"])
        report_field = str(pair["report"])
        system_value = _verified_number(canonical.get(system_field))
        report_raw = self_report.get(report_field)
        report_value = report_raw if isinstance(report_raw, (int, float)) and not isinstance(report_raw, bool) else None
        if system_value is None or report_value is None:
            continue
        high = float(pair.get("high", 0.65))
        low = float(pair.get("low", 0.35))
        if system_value >= high and report_value >= high:
            text = pair.get("both_high")
        elif system_value <= low and report_value <= low:
            text = pair.get("both_low")
        elif (system_value >= high and report_value <= low) or (system_value <= low and report_value >= high):
            text = pair.get("divergent")
        else:
            text = pair.get("mixed")
        if text:
            lines.append(str(text))

    if deltas:
        threshold = float(rules.get("delta_threshold", 0.0))
        changed = [(name, delta) for name, delta in sorted(deltas.items()) if abs(delta) >= threshold]
        if changed:
            template = str(rules.get("delta_template", "Change vs previous: {changes}."))
            rendered = ", ".join(f"{name} {delta:+.2f}" for name, delta in changed)
            lines.append(template.format(changes=rendered))

    if confounds:
        template = str(rules.get("confound_template", "Longitudinal confound changed: {fields}."))
        lines.append(template.format(fields=", ".join(confounds)))

    calibration = rules.get("calibration_line")
    if calibration:
        lines.append(str(calibration))

    max_lines = int(config.get("render", {}).get("max_evaluation_lines", 5))
    if max_lines < 0 or max_lines > 20:
        raise StudySurfaceError("BAD_MAX_EVALUATION_LINES")
    return lines[:max_lines]


def build_record(
    *,
    config: Mapping[str, Any],
    canonical_values: Mapping[str, Any],
    self_report_values: Mapping[str, Any] | None,
    context: Mapping[str, Any],
    previous_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not bool(config.get("enabled", False)):
        return {"enabled": False}
    if str(config.get("epistemic_law", "")) != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
        raise StudySurfaceError("EPISTEMIC_LAW_MISSING")

    canonical = normalize_canonical(canonical_values, list(config.get("canonical_fields", [])))
    self_report = normalize_self_report(self_report_values, list(config.get("self_report_fields", [])))
    previous_canonical = previous_record.get("canonical") if previous_record else None
    deltas = metric_deltas(canonical, previous_canonical)
    previous_context = previous_record.get("context") if previous_record else None
    confound_fields = list(config.get("deterministic_evaluation", {}).get("confound_fields", []))
    confounds = context_confounds(context, previous_context, confound_fields)
    evaluation = deterministic_evaluation(
        canonical=canonical,
        self_report=self_report,
        config=config,
        deltas=deltas,
        confounds=confounds,
    )
    return {
        "enabled": True,
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
        "canonical": canonical,
        "self_report": self_report,
        "deltas": deltas,
        "context": dict(context),
        "confounds": confounds,
        "evaluation": evaluation,
    }


def extract_self_report(payload: Mapping[str, Any], field_name: str | None) -> dict[str, Any]:
    """Read a profile-named self-report object without granting it canonical status."""
    if not field_name:
        return {}
    value = payload.get(str(field_name))
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise StudySurfaceError("SELF_REPORT_NOT_OBJECT")
    return dict(value)


def ensure_study_schema(db: sqlite3.Connection) -> None:
    """Install the generic study-record table; never commits the caller transaction."""
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS eos_pipeline_study_records(
          output_id TEXT PRIMARY KEY,
          ts REAL NOT NULL,
          generation INTEGER NOT NULL,
          profile_id TEXT NOT NULL,
          record_json TEXT NOT NULL,
          record_hash TEXT NOT NULL,
          rendered_box TEXT NOT NULL,
          canonical_hash TEXT NOT NULL,
          packet_hash TEXT NOT NULL
        )
        """
    )


def insert_study_record(
    db: sqlite3.Connection,
    *,
    output_id: str,
    ts: float,
    generation: int,
    profile_id: str,
    record: Mapping[str, Any],
    rendered_box: str,
    canonical_hash: str,
    packet_hash: str,
) -> str:
    """Insert one output-bound study record into the caller's existing transaction.

    This function intentionally never calls commit/rollback. Atomicity belongs to the
    canonical pipeline commit that also owns output persistence, source consumption and
    generation CAS.
    """
    if not output_id or not profile_id or not canonical_hash or not packet_hash:
        raise StudySurfaceError("STUDY_BINDING_MISSING")
    if not record.get("enabled"):
        raise StudySurfaceError("STUDY_RECORD_DISABLED")
    record_json = stable_record_json(record)
    record_hash = hashlib.sha256(record_json.encode("utf-8")).hexdigest()
    db.execute(
        "INSERT INTO eos_pipeline_study_records VALUES(?,?,?,?,?,?,?,?,?)",
        (
            output_id,
            float(ts),
            int(generation),
            profile_id,
            record_json,
            record_hash,
            rendered_box,
            canonical_hash,
            packet_hash,
        ),
    )
    return record_hash


def _render_value(value: Any, delta: float | None = None) -> str:
    if isinstance(value, Mapping) and "status" in value:
        status = str(value.get("status", "UNKNOWN"))
        number = value.get("value")
        text = status if number is None else f"{status} {float(number):.2f}"
    elif isinstance(value, float):
        text = f"{value:.2f}"
    elif value is None:
        text = "UNKNOWN"
    else:
        text = str(value)
    if delta is not None:
        text += f"   Δ {delta:+.2f}"
    return text


def render_state_box(config: Mapping[str, Any], record: Mapping[str, Any]) -> str:
    if not record.get("enabled"):
        return ""
    render = config.get("render", {})
    sections = list(render.get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]))
    if len(sections) != 3:
        raise StudySurfaceError("RENDER_REQUIRES_THREE_SECTIONS")
    title = str(render.get("title", "STATE"))
    fence = str(render.get("fence", "text"))
    if not fence.replace("_", "").isalnum():
        raise StudySurfaceError("BAD_FENCE")

    canonical = record["canonical"]
    report = record["self_report"]
    deltas = record.get("deltas", {})
    lines = [f"```{fence}", title, sections[0]]
    for field in config.get("canonical_fields", []):
        lines.append(f"{field:<24}= {_render_value(canonical[field], deltas.get(field))}")
    lines.append("")
    lines.append(sections[1])
    for field in config.get("self_report_fields", []):
        lines.append(f"{field:<24}= {_render_value(report[field])}")
    lines.append("")
    lines.append(sections[2])
    for line in record.get("evaluation", []):
        lines.append("- " + str(line))
    lines.append("```")
    return "\n".join(lines)


def append_state_box(public_text: str, box: str) -> str:
    """Append exactly one pipeline-owned box after validated public prose."""
    text = public_text.rstrip()
    if not box:
        return text
    return text + "\n\n" + box.strip() + "\n"


def stable_record_json(record: Mapping[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "VERSION",
    "StudySurfaceError",
    "normalize_canonical",
    "normalize_self_report",
    "metric_deltas",
    "context_confounds",
    "deterministic_evaluation",
    "build_record",
    "render_state_box",
    "append_state_box",
    "stable_record_json",
    "extract_self_report",
    "ensure_study_schema",
    "insert_study_record",
]
