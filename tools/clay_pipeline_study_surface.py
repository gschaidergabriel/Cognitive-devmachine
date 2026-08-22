from __future__ import annotations

import math
from typing import Any, Mapping

UNKNOWN = "UNKNOWN"
VALID_MEASURED = {"VERIFIED", "MEASURED"}


class StudyFault(ValueError):
    pass


def _safe_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bounded_report_value(name: str, value: Any) -> float | str:
    if str(value).upper() == UNKNOWN:
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


def _public_self_report(payload: Mapping[str, Any], contract: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    field = str(cfg.get("self_report_payload_field") or contract.get("longitudinal_self_report_field") or "")
    raw = payload.get(field, {}) if field else {}
    if not isinstance(raw, Mapping):
        raise StudyFault("BAD_SELF_REPORT_OBJECT")
    out: dict[str, Any] = {}
    for name in cfg.get("self_report_fields", []):
        name = str(name)
        if name in {"qualia_result", "qualia_confidence"}:
            continue
        out[name] = _bounded_report_value(name, raw.get(name, UNKNOWN))
    qualia_field = contract.get("qualia_probe_field")
    if qualia_field:
        probe = payload.get(qualia_field)
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
            out["qualia_confidence"] = _bounded_report_value("qualia_confidence", probe.get("confidence", UNKNOWN))
    return out


def _sensor_health(compiled: Mapping[str, Any]) -> str:
    canonical = compiled.get("canonical", {})
    sensors = canonical.get("sources_health", {}) if isinstance(canonical, Mapping) else {}
    if not isinstance(sensors, Mapping) or not sensors:
        return UNKNOWN
    values = [
        bool(item.get("ok")) if isinstance(item, Mapping) and "ok" in item else None
        for item in sensors.values()
    ]
    if values and all(value is True for value in values):
        return "VERIFIED"
    if any(value is True for value in values):
        return "DEGRADED"
    if any(value is False for value in values):
        return "ERROR"
    return UNKNOWN


def _quiet_status(compiled: Mapping[str, Any]) -> str:
    packet = compiled.get("packet", {})
    if not isinstance(packet, Mapping) or not bool(packet.get("quiet_sensors_ok", False)):
        return UNKNOWN
    return "VERIFIED_QUIET" if int(compiled.get("source_count", 0) or 0) == 0 else "NOT_QUIET"


def _system_state(compiled: Mapping[str, Any], generated: Mapping[str, Any], generation: int, ts: float, cfg: Mapping[str, Any]) -> dict[str, Any]:
    metrics = compiled.get("personality_state", {})
    if not isinstance(metrics, Mapping):
        metrics = {}
    state: dict[str, Any] = {
        "generation": int(generation),
        "timestamp": float(ts),
        "inference_backend": str(generated.get("provider_kind") or generated.get("inference_kind") or UNKNOWN),
        "model_label": str(generated.get("model") or UNKNOWN),
        "source_count": int(compiled.get("source_count", 0) or 0),
        "sensor_health": _sensor_health(compiled),
        "quiet_status": _quiet_status(compiled),
    }
    reserved = set(state)
    for name in cfg.get("canonical_fields", []):
        name = str(name)
        if name in reserved:
            continue
        state[name] = _metric_view(metrics.get(name) if isinstance(metrics, Mapping) else None)
    return state


def _deltas(current: Mapping[str, Any], previous: Mapping[str, Any] | None) -> dict[str, float]:
    if not isinstance(previous, Mapping):
        return {}
    out: dict[str, float] = {}
    for name, cur in current.items():
        old = previous.get(name)
        if not (isinstance(cur, Mapping) and isinstance(old, Mapping)):
            continue
        if str(cur.get("status")).upper() not in VALID_MEASURED or str(old.get("status")).upper() not in VALID_MEASURED:
            continue
        current_value = _safe_number(cur.get("value"))
        previous_value = _safe_number(old.get("value"))
        if current_value is not None and previous_value is not None:
            out[name] = current_value - previous_value
    return out


def _evaluation(current: Mapping[str, Any], self_report: Mapping[str, Any], previous_record: Mapping[str, Any] | None, cfg: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if current.get("sensor_health") in {"ERROR", "DEGRADED", UNKNOWN}:
        entries.append({"code": "SENSOR_UNCERTAINTY", "sensor_health": current.get("sensor_health")})
    for pair in cfg.get("comparison_pairs", []):
        system_metric = str(pair.get("system_metric", ""))
        self_report_metric = str(pair.get("self_report_metric", ""))
        system_value = current.get(system_metric)
        report_value = _safe_number(self_report.get(self_report_metric))
        if not isinstance(system_value, Mapping) or str(system_value.get("status")).upper() not in VALID_MEASURED:
            continue
        measured = _safe_number(system_value.get("value"))
        if measured is None or report_value is None:
            continue
        tolerance = float(pair.get("tolerance", 0.2))
        difference = abs(measured - report_value)
        entries.append(
            {
                "code": "CONGRUENCE" if difference <= tolerance else "DIVERGENCE",
                "system_metric": system_metric,
                "self_report_metric": self_report_metric,
                "difference": difference,
                "tolerance": tolerance,
            }
        )
    if isinstance(previous_record, Mapping):
        previous_system = previous_record.get("system_state", {})
        previous_backend = previous_system.get("inference_backend") if isinstance(previous_system, Mapping) else None
        previous_model = previous_system.get("model_label") if isinstance(previous_system, Mapping) else None
        if previous_backend and previous_backend != current.get("inference_backend"):
            entries.append({"code": "BACKEND_CHANGE", "from": previous_backend, "to": current.get("inference_backend")})
        elif previous_model and previous_model != current.get("model_label"):
            entries.append({"code": "MODEL_CHANGE", "from": previous_model, "to": current.get("model_label")})
    render = cfg.get("render", {}) if isinstance(cfg.get("render"), Mapping) else {}
    return entries[: max(0, int(render.get("max_evaluation_lines", 5)))]


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


def _render_evaluation(entry: Mapping[str, Any], cfg: Mapping[str, Any]) -> str:
    code = str(entry.get("code", "UNKNOWN_EVALUATION"))
    templates = cfg.get("evaluation_templates", {})
    template = templates.get(code) if isinstance(templates, Mapping) else None
    if isinstance(template, str):
        safe_values = {key: value for key, value in entry.items() if key != "code"}
        try:
            return template.format(**safe_values)
        except (KeyError, ValueError):
            raise StudyFault("BAD_EVALUATION_TEMPLATE:" + code)
    details = " ".join(f"{key}={entry[key]}" for key in sorted(entry) if key != "code")
    return code + (" " + details if details else "")


def render_public_appendix(record: Mapping[str, Any], cfg: Mapping[str, Any]) -> str:
    render = cfg.get("render", {}) if isinstance(cfg.get("render"), Mapping) else {}
    fence = str(render.get("fence", "text"))
    title = str(render.get("title", "STATE"))
    sections = list(render.get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]))
    system_label = sections[0] if len(sections) > 0 else "SYSTEM STATE"
    report_label = sections[1] if len(sections) > 1 else "MODEL SELF-REPORT"
    evaluation_label = sections[2] if len(sections) > 2 else "EVALUATION"
    system = record["system_state"]
    report = record["self_report"]
    deltas = record.get("deltas", {})
    lines = [f"```{fence}", f"{title} — generation {system['generation']}", system_label]
    for name in [field for field in cfg.get("canonical_fields", []) if field in system]:
        suffix = f"  Δ {deltas[name]:+.3f}" if name in deltas else ""
        lines.append(f"{name:<24}= {_fmt_value(system[name])}{suffix}")
    lines.append("")
    lines.append(report_label)
    for name in cfg.get("self_report_fields", []):
        if name in report:
            lines.append(f"{str(name):<24}= {_fmt_value(report[name])}")
    lines.append("")
    lines.append(evaluation_label)
    evaluation = record.get("evaluation", [])
    empty_text = str(cfg.get("empty_evaluation_text", "NO_DETERMINISTIC_COMPARISON"))
    lines.extend(["- " + _render_evaluation(entry, cfg) for entry in evaluation] if evaluation else ["- " + empty_text])
    lines.append("```")
    return "\n".join(lines)


def build_study_record(*, config: Mapping[str, Any], contract: Mapping[str, Any], compiled: Mapping[str, Any], generated: Mapping[str, Any], payload: Mapping[str, Any], previous_record: Mapping[str, Any] | None, generation: int, ts: float) -> dict[str, Any] | None:
    cfg = config
    if not isinstance(cfg, Mapping) or not bool(cfg.get("enabled", False)):
        return None
    if str(cfg.get("epistemic_law", "")) != "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT":
        raise StudyFault("BAD_EPISTEMIC_LAW")
    current = _system_state(compiled, generated, generation, ts, cfg)
    self_report = _public_self_report(payload, contract, cfg)
    record = {
        "schema": str(cfg.get("schema", "clay-public-state-box/v1")),
        "generation": int(generation),
        "system_state": current,
        "self_report": self_report,
        "deltas": _deltas(current, previous_record.get("system_state") if isinstance(previous_record, Mapping) else None),
        "evaluation": _evaluation(current, self_report, previous_record, cfg),
    }
    record["rendered_text"] = render_public_appendix(record, cfg)
    return record


__all__ = ["StudyFault", "build_study_record", "render_public_appendix"]
