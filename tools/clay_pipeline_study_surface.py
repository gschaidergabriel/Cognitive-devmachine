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
        raw = {}
    out: dict[str, Any] = {}
    for name in cfg.get("self_report_fields", []):
        value = raw.get(name, UNKNOWN)
        number = _safe_number(value)
        if number is not None:
            out[str(name)] = max(0.0, min(1.0, number))
        elif str(value).upper() == UNKNOWN:
            out[str(name)] = UNKNOWN
        else:
            out[str(name)] = UNKNOWN
    qualia_field = contract.get("qualia_probe_field")
    if qualia_field and isinstance(payload.get(qualia_field), Mapping):
        probe = payload[qualia_field]
        result = str(probe.get("result", UNKNOWN)).upper()
        if result not in {"REPORTED", "FAILED", UNKNOWN}:
            result = UNKNOWN
        out["qualia_result"] = result
        conf = _safe_number(probe.get("confidence"))
        out["qualia_confidence"] = max(0.0, min(1.0, conf)) if conf is not None else UNKNOWN
    return out


def _sensor_health(compiled: Mapping[str, Any]) -> str:
    canonical = compiled.get("canonical", {})
    sensors = canonical.get("sources_health", {}) if isinstance(canonical, Mapping) else {}
    if not isinstance(sensors, Mapping) or not sensors:
        return UNKNOWN
    values = []
    for item in sensors.values():
        values.append(bool(item.get("ok")) if isinstance(item, Mapping) and "ok" in item else None)
    if all(v is True for v in values):
        return "VERIFIED"
    if any(v is True for v in values):
        return "DEGRADED"
    if any(v is False for v in values):
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
        a, b = _safe_number(cur.get("value")), _safe_number(old.get("value"))
        if a is not None and b is not None:
            out[name] = a - b
    return out


def _evaluation(current: Mapping[str, Any], self_report: Mapping[str, Any], previous_record: Mapping[str, Any] | None, cfg: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    if current.get("sensor_health") in {"ERROR", "DEGRADED", UNKNOWN}:
        lines.append("UNCERTAINTY: canonical sensor health is not fully verified.")
    for pair in cfg.get("comparison_pairs", []):
        sm = str(pair.get("system_metric", ""))
        rm = str(pair.get("self_report_metric", ""))
        sys_metric = current.get(sm)
        report = _safe_number(self_report.get(rm))
        if not isinstance(sys_metric, Mapping) or str(sys_metric.get("status")).upper() not in VALID_MEASURED:
            continue
        measured = _safe_number(sys_metric.get("value"))
        if measured is None or report is None:
            continue
        tolerance = float(pair.get("tolerance", 0.2))
        label = "CONGRUENCE" if abs(measured - report) <= tolerance else "DIVERGENCE"
        lines.append(f"{label}: {sm} vs self-report {rm}; no causal interpretation.")
    if isinstance(previous_record, Mapping):
        previous_system = previous_record.get("system_state", {})
        prior_backend = previous_system.get("inference_backend") if isinstance(previous_system, Mapping) else None
        prior_model = previous_system.get("model_label") if isinstance(previous_system, Mapping) else None
        if prior_backend and prior_backend != current.get("inference_backend"):
            lines.append("CONFOUND: inference backend changed since previous study record.")
        elif prior_model and prior_model != current.get("model_label"):
            lines.append("CONFOUND: model changed since previous study record.")
    render = cfg.get("render", {}) if isinstance(cfg.get("render"), Mapping) else {}
    return lines[: max(0, int(render.get("max_evaluation_lines", 5)))]


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
    sections = list(render.get("sections", ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"]))
    sys_label = sections[0] if len(sections) > 0 else "SYSTEM STATE"
    rep_label = sections[1] if len(sections) > 1 else "MODEL SELF-REPORT"
    eval_label = sections[2] if len(sections) > 2 else "EVALUATION"
    system = record["system_state"]
    report = record["self_report"]
    deltas = record.get("deltas", {})
    lines = [f"```{fence}", f"{title} — generation {system['generation']}", sys_label]
    for name in [x for x in cfg.get("canonical_fields", []) if x in system]:
        suffix = f"  Δ {deltas[name]:+.3f}" if name in deltas else ""
        lines.append(f"{name:<24}= {_fmt_value(system[name])}{suffix}")
    lines.append("")
    lines.append(rep_label)
    for name in cfg.get("self_report_fields", []):
        if name in report:
            lines.append(f"{str(name):<24}= {_fmt_value(report[name])}")
    if "qualia_result" in report:
        lines.append(f"{'qualia_result':<24}= {_fmt_value(report['qualia_result'])}")
        lines.append(f"{'qualia_confidence':<24}= {_fmt_value(report['qualia_confidence'])}")
    lines.append("")
    lines.append(eval_label)
    evaluation = record.get("evaluation", [])
    lines.extend([f"- {line}" for line in evaluation] if evaluation else ["- No deterministic comparison available."])
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
