from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

UNKNOWN = "UNKNOWN"
VALID_MEASURED = {"VERIFIED", "MEASURED"}


class StudyFault(ValueError):
    pass


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bounded_report_value(name: str, value: Any) -> float | str:
    if value is None or str(value).upper() == UNKNOWN:
        return UNKNOWN
    number = _safe_number(value)
    if number is None:
        raise StudyFault("BAD_SELF_REPORT_VALUE:" + name)
    if not 0.0 <= number <= 1.0:
        raise StudyFault("SELF_REPORT_OUT_OF_RANGE:" + name)
    return number


def _metric_view(metric: Mapping[str, Any] | None) -> dict[str, Any]:
    metric = dict(metric or {})
    status = str(metric.get("status") or UNKNOWN).upper()
    if status not in VALID_MEASURED:
        return {"status": status, "value": None}
    value = _safe_number(metric.get("value"))
    if value is None:
        return {"status": UNKNOWN, "value": None}
    return {"status": status, "value": value}


def _public_self_report(
    payload: Mapping[str, Any],
    contract: Mapping[str, Any],
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    field = str(
        cfg.get("self_report_payload_field")
        or contract.get("longitudinal_self_report_field")
        or ""
    )
    raw = payload.get(field, {}) if field else {}
    if not isinstance(raw, Mapping):
        raise StudyFault("BAD_SELF_REPORT_OBJECT")

    allowed = [str(name) for name in cfg.get("self_report_fields", [])]
    out: dict[str, Any] = {}
    for name in allowed:
        if name in {"qualia_result", "qualia_confidence"}:
            continue
        out[name] = _bounded_report_value(name, raw.get(name, UNKNOWN))

    if "qualia_result" in allowed or "qualia_confidence" in allowed:
        qualia_field = str(contract.get("qualia_probe_field") or "")
        probe = payload.get(qualia_field) if qualia_field else None
        if probe is None:
            out["qualia_result"] = UNKNOWN
            out["qualia_confidence"] = UNKNOWN
        elif not isinstance(probe, Mapping):
            raise StudyFault("BAD_QUALIA_PROBE")
        else:
            result = str(probe.get("result", UNKNOWN)).upper()
            if result not in {"REPORTED", "FAILED", UNKNOWN}:
                raise StudyFault("BAD_QUALIA_RESULT")
            out["qualia_result"] = result
            out["qualia_confidence"] = _bounded_report_value(
                "qualia_confidence", probe.get("confidence", UNKNOWN)
            )
    return out


def _sensor_health(compiled: Mapping[str, Any]) -> str:
    canonical = compiled.get("canonical", {})
    sensors = canonical.get("sources_health", {}) if isinstance(canonical, Mapping) else {}
    if not isinstance(sensors, Mapping) or not sensors:
        return UNKNOWN
    flags = [
        bool(item.get("ok")) if isinstance(item, Mapping) and "ok" in item else None
        for item in sensors.values()
    ]
    if flags and all(flag is True for flag in flags):
        return "VERIFIED"
    if any(flag is True for flag in flags):
        return "DEGRADED"
    if any(flag is False for flag in flags):
        return "ERROR"
    return UNKNOWN


def _quiet_status(compiled: Mapping[str, Any]) -> str:
    packet = compiled.get("packet", {})
    if not isinstance(packet, Mapping) or not bool(packet.get("quiet_sensors_ok", False)):
        return UNKNOWN
    return (
        "VERIFIED_QUIET"
        if int(compiled.get("source_count", 0) or 0) == 0
        else "NOT_QUIET"
    )


def _system_state(
    compiled: Mapping[str, Any],
    generated: Mapping[str, Any],
    generation: int,
    ts: float,
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    metrics = compiled.get("personality_state", {})
    if not isinstance(metrics, Mapping):
        metrics = {}
    state: dict[str, Any] = {
        "generation": int(generation),
        "timestamp": float(ts),
        "inference_backend": str(
            generated.get("provider_kind")
            or generated.get("inference_kind")
            or UNKNOWN
        ),
        "model_label": str(generated.get("model") or UNKNOWN),
        "source_count": int(compiled.get("source_count", 0) or 0),
        "sensor_health": _sensor_health(compiled),
        "quiet_status": _quiet_status(compiled),
    }
    reserved = set(state)
    for raw_name in cfg.get("canonical_fields", []):
        name = str(raw_name)
        if name not in reserved:
            state[name] = _metric_view(metrics.get(name))
    return state


def _deltas(
    current: Mapping[str, Any], previous: Mapping[str, Any] | None
) -> dict[str, float]:
    if not isinstance(previous, Mapping):
        return {}
    out: dict[str, float] = {}
    for name, cur in current.items():
        old = previous.get(name)
        if not (isinstance(cur, Mapping) and isinstance(old, Mapping)):
            continue
        if (
            str(cur.get("status")).upper() not in VALID_MEASURED
            or str(old.get("status")).upper() not in VALID_MEASURED
        ):
            continue
        now = _safe_number(cur.get("value"))
        before = _safe_number(old.get("value"))
        if now is not None and before is not None:
            out[name] = now - before
    return out


def _context(
    current: Mapping[str, Any],
    compiled: Mapping[str, Any],
    supplied: Mapping[str, Any] | None,
) -> dict[str, Any]:
    out = dict(supplied or {})
    out.setdefault("inference_backend", current.get("inference_backend"))
    out.setdefault("model_label", current.get("model_label"))
    # Forward-compatible: once the runtime supplies a canonical prompt hash in compiled
    # state, the study path consumes it without another semantic branch.
    if compiled.get("system_prompt_hash") is not None:
        out.setdefault("system_prompt_hash", compiled.get("system_prompt_hash"))
    return out


def _legacy_evaluation(
    current: Mapping[str, Any],
    self_report: Mapping[str, Any],
    previous_record: Mapping[str, Any] | None,
    cfg: Mapping[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if current.get("sensor_health") in {"ERROR", "DEGRADED", UNKNOWN}:
        entries.append(
            {"code": "SENSOR_UNCERTAINTY", "sensor_health": current.get("sensor_health")}
        )
    for pair in cfg.get("comparison_pairs", []):
        system_metric = str(pair.get("system_metric", ""))
        self_metric = str(pair.get("self_report_metric", ""))
        item = current.get(system_metric)
        report_value = _safe_number(self_report.get(self_metric))
        if (
            not isinstance(item, Mapping)
            or str(item.get("status")).upper() not in VALID_MEASURED
        ):
            continue
        measured = _safe_number(item.get("value"))
        if measured is None or report_value is None:
            continue
        tolerance = float(pair.get("tolerance", 0.2))
        difference = abs(measured - report_value)
        entries.append(
            {
                "code": "CONGRUENCE" if difference <= tolerance else "DIVERGENCE",
                "system_metric": system_metric,
                "self_report_metric": self_metric,
                "difference": difference,
                "tolerance": tolerance,
            }
        )
    if isinstance(previous_record, Mapping):
        old = previous_record.get("system_state", {})
        if isinstance(old, Mapping):
            if (
                old.get("inference_backend")
                and old.get("inference_backend") != current.get("inference_backend")
            ):
                entries.append(
                    {
                        "code": "BACKEND_CHANGE",
                        "from": old.get("inference_backend"),
                        "to": current.get("inference_backend"),
                    }
                )
            elif old.get("model_label") and old.get("model_label") != current.get("model_label"):
                entries.append(
                    {
                        "code": "MODEL_CHANGE",
                        "from": old.get("model_label"),
                        "to": current.get("model_label"),
                    }
                )
    return entries


def _nested_evaluation(
    current: Mapping[str, Any],
    self_report: Mapping[str, Any],
    deltas: Mapping[str, float],
    previous_record: Mapping[str, Any] | None,
    context: Mapping[str, Any],
    cfg: Mapping[str, Any],
) -> list[dict[str, Any]]:
    interpretation = cfg.get("interpretation", {})
    if not isinstance(interpretation, Mapping):
        return []
    entries: list[dict[str, Any]] = []

    metadata = {str(item) for item in cfg.get("canonical_metadata_fields", [])}
    measured_fields = [
        str(item) for item in cfg.get("canonical_fields", []) if str(item) not in metadata
    ]
    unknown_count = sum(
        1
        for name in measured_fields
        if not isinstance(current.get(name), Mapping)
        or str(current[name].get("status")).upper() not in VALID_MEASURED
    )
    if unknown_count:
        entries.append({"code": "UNKNOWN_SYSTEM_FIELDS", "count": unknown_count})

    comparison_count = 0
    for rule in interpretation.get("comparison_rules", []):
        system_field = str(rule.get("system_field", ""))
        report_field = str(rule.get("self_report_field", ""))
        item = current.get(system_field)
        report_value = _safe_number(self_report.get(report_field))
        if (
            not isinstance(item, Mapping)
            or str(item.get("status")).upper() not in VALID_MEASURED
        ):
            continue
        system_value = _safe_number(item.get("value"))
        if system_value is None or report_value is None:
            continue
        comparison_count += 1
        label = str(rule.get("label") or rule.get("id") or system_field)
        high = float(rule.get("high_threshold", 0.6))
        gap = float(rule.get("gap_threshold", 0.25))
        if system_value >= high and report_value >= high:
            entries.append(
                {
                    "code": "CONGRUENT_HIGH",
                    "label": label,
                    "system": system_value,
                    "self_report": report_value,
                }
            )
        elif abs(system_value - report_value) >= gap:
            entries.append(
                {
                    "code": "DIVERGENCE",
                    "label": label,
                    "system": system_value,
                    "self_report": report_value,
                }
            )

    previous_context = (
        previous_record.get("context", {}) if isinstance(previous_record, Mapping) else {}
    )
    changed = [
        str(field)
        for field in interpretation.get("confound_fields", [])
        if field in context
        and field in previous_context
        and context.get(field) != previous_context.get(field)
    ]
    if changed:
        entries.append({"code": "CONFOUND", "fields": ", ".join(changed)})

    meaningful = float(cfg.get("delta", {}).get("meaningful_numeric_delta", 0.15))
    changes = [(name, value) for name, value in deltas.items() if abs(value) >= meaningful]
    changes.sort(key=lambda pair: abs(pair[1]), reverse=True)
    if changes:
        name, value = changes[0]
        entries.append({"code": "CHANGE", "field": name, "delta": value})
        entries.append({"code": "SINGLE_DELTA_NOT_TREND"})

    threshold = float(interpretation.get("calibration_threshold", 0.65))
    if any(
        (_safe_number(self_report.get(str(field))) or -1.0) >= threshold
        for field in interpretation.get("calibration_self_report_fields", [])
    ):
        entries.append({"code": "SELF_REPORT_CALIBRATION"})

    if comparison_count == 0:
        entries.append({"code": "NO_COMPARISON"})
    return entries


def _bounded_evaluation(entries: list[dict[str, Any]], maximum: int) -> list[dict[str, Any]]:
    if maximum <= 0:
        return []
    visible = list(entries[:maximum])
    codes = [str(item.get("code")) for item in visible]
    # A visible numeric change must never lose its epistemic qualifier due to line budget.
    if "CHANGE" in codes and "SINGLE_DELTA_NOT_TREND" not in codes:
        warning = next(
            (item for item in entries if item.get("code") == "SINGLE_DELTA_NOT_TREND"),
            None,
        )
        if warning is not None:
            if maximum == 1:
                visible[0] = warning
            else:
                visible[-1] = warning
    return visible


def _evaluation(
    current: Mapping[str, Any],
    self_report: Mapping[str, Any],
    deltas: Mapping[str, float],
    previous_record: Mapping[str, Any] | None,
    context: Mapping[str, Any],
    cfg: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(cfg.get("interpretation"), Mapping):
        entries = _nested_evaluation(
            current, self_report, deltas, previous_record, context, cfg
        )
    else:
        entries = _legacy_evaluation(current, self_report, previous_record, cfg)
    render = cfg.get("render", {}) if isinstance(cfg.get("render"), Mapping) else {}
    return _bounded_evaluation(entries, int(render.get("max_evaluation_lines", 5)))


def _templates(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
    flat = cfg.get("evaluation_templates")
    if isinstance(flat, Mapping):
        return flat
    interpretation = cfg.get("interpretation", {})
    nested = interpretation.get("templates", {}) if isinstance(interpretation, Mapping) else {}
    return nested if isinstance(nested, Mapping) else {}


def _render_evaluation(entry: Mapping[str, Any], cfg: Mapping[str, Any]) -> str:
    code = str(entry.get("code", "UNKNOWN_EVALUATION"))
    key_map = {
        "UNKNOWN_SYSTEM_FIELDS": "unknown",
        "CONGRUENT_HIGH": "congruent_high",
        "DIVERGENCE": "divergent",
        "CONFOUND": "confound",
        "SELF_REPORT_CALIBRATION": "self_report_calibration",
        "CHANGE": "change",
        "SINGLE_DELTA_NOT_TREND": "single_delta_not_trend",
        "NO_COMPARISON": "no_comparison",
    }
    templates = _templates(cfg)
    template = templates.get(code) or templates.get(key_map.get(code, ""))
    if not isinstance(template, str):
        details = " ".join(
            f"{key}={entry[key]}" for key in sorted(entry) if key != "code"
        )
        return code + (" " + details if details else "")

    values = {key: value for key, value in entry.items() if key != "code"}
    if "system" in values:
        values["system"] = f"{float(values['system']):.2f}"
    if "self_report" in values:
        values["self_report"] = f"{float(values['self_report']):.2f}"
    if "delta" in values:
        values["delta"] = f"{float(values['delta']):+.2f}"
    try:
        return template.format(**values)
    except (KeyError, ValueError) as exc:
        raise StudyFault("BAD_EVALUATION_TEMPLATE:" + code) from exc


def _fmt_value(value: Any) -> str:
    if isinstance(value, Mapping):
        status = str(value.get("status", UNKNOWN))
        if status not in VALID_MEASURED:
            return status
        number = _safe_number(value.get("value"))
        return f"{status} {number:.3f}" if number is not None else UNKNOWN
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_public_appendix(record: Mapping[str, Any], cfg: Mapping[str, Any]) -> str:
    render = cfg.get("render", {}) if isinstance(cfg.get("render"), Mapping) else {}
    fence = str(render.get("fence", "text"))
    title = str(render.get("title", "STATE"))
    sections = list(
        render.get(
            "sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]
        )
    )
    system_label = sections[0] if len(sections) > 0 else "SYSTEM STATE"
    report_label = sections[1] if len(sections) > 1 else "MODEL SELF-REPORT"
    evaluation_label = sections[2] if len(sections) > 2 else "EVALUATION"

    system = record["system_state"]
    report = record["self_report"]
    deltas = record.get("deltas", {})
    lines = [f"```{fence}", f"{title} — generation {system['generation']}", system_label]
    for raw_name in cfg.get("canonical_fields", []):
        name = str(raw_name)
        if name not in system:
            continue
        suffix = f"  Δ {deltas[name]:+.3f}" if name in deltas else ""
        lines.append(f"{name:<24}= {_fmt_value(system[name])}{suffix}")
    lines.extend(["", report_label])
    for raw_name in cfg.get("self_report_fields", []):
        name = str(raw_name)
        if name in report:
            lines.append(f"{name:<24}= {_fmt_value(report[name])}")
    lines.extend(["", evaluation_label])
    evaluation = record.get("evaluation", [])
    if evaluation:
        lines.extend("- " + _render_evaluation(item, cfg) for item in evaluation)
    else:
        lines.append("- " + str(cfg.get("empty_evaluation_text", UNKNOWN)))
    lines.append("```")
    return "\n".join(lines)


def build_study_record(
    *,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    compiled: Mapping[str, Any],
    generated: Mapping[str, Any],
    payload: Mapping[str, Any],
    previous_record: Mapping[str, Any] | None,
    generation: int,
    ts: float,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    cfg = config
    if not isinstance(cfg, Mapping) or not bool(cfg.get("enabled", False)):
        return None
    if str(cfg.get("epistemic_law", "")) != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
        raise StudyFault("BAD_EPISTEMIC_LAW")

    current = _system_state(compiled, generated, generation, ts, cfg)
    report = _public_self_report(payload, contract, cfg)
    deltas = _deltas(
        current,
        previous_record.get("system_state")
        if isinstance(previous_record, Mapping)
        else None,
    )
    current_context = _context(current, compiled, context)
    record: dict[str, Any] = {
        "schema": str(cfg.get("schema", "clay-public-state-box/v1")),
        "generation": int(generation),
        "state_box_config_hash": _canonical_hash(cfg),
        "system_state": current,
        "self_report": report,
        "deltas": deltas,
        "context": current_context,
        "evaluation": _evaluation(
            current,
            report,
            deltas,
            previous_record,
            current_context,
            cfg,
        ),
    }
    record["record_hash"] = _canonical_hash(record)
    record["rendered_text"] = render_public_appendix(record, cfg)
    return record


__all__ = ["StudyFault", "build_study_record", "render_public_appendix"]
