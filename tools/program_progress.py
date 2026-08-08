#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROGRAM = ROOT / "research_entity" / "rooms" / "PROGRAM_STATE.json"
DEFAULT_THROUGHPUT = ROOT / "research_entity" / "rooms" / "PROGRAM_THROUGHPUT.json"
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import doomsday_forecast as df


def load(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def complete(program):
    return {str(x).upper() for x in (program.get("progress_semantics") or {}).get("complete_statuses", ["PASS", "COMPLETE", "COMPLETED", "DONE", "CLOSED"])}


def is_done(value, statuses):
    return str(value or "").upper() in statuses


def next_stage(program):
    statuses = complete(program)
    gates = program.get("stage_gates") or {}
    order = [str(x) for x in program.get("stage_order", [])]
    if not order:
        raise ValueError("PROGRAM_STATE.stage_order is empty")
    for stage_id in order:
        stage = gates.get(stage_id) or {}
        if not is_done(stage.get("status"), statuses):
            return stage_id, stage
    return order[-1], gates.get(order[-1]) or {}


def package_progress(workspace, field, prefixes, statuses):
    packages = df.nested(workspace, field, {})
    if not isinstance(packages, dict) or not packages:
        return 0.0, 0.0, 0.0
    done = total = 0.0
    for package_id, payload in packages.items():
        if prefixes and not any(str(package_id).startswith(prefix) for prefix in prefixes):
            continue
        payload = payload if isinstance(payload, dict) else {"status": str(payload)}
        weight = float(payload.get("weight", 1) or 1)
        fraction = 1.0 if is_done(payload.get("status"), statuses) else 0.0
        subchecks = payload.get("subchecks")
        if isinstance(subchecks, dict) and subchecks:
            sub_done = sub_total = 0.0
            for item in subchecks.values():
                if isinstance(item, dict):
                    sub_weight = float(item.get("weight", 1) or 1)
                    sub_status = item.get("status")
                else:
                    sub_weight = 1.0
                    sub_status = item
                sub_total += sub_weight
                if is_done(sub_status, statuses):
                    sub_done += sub_weight
            fraction = sub_done / sub_total if sub_total else 0.0
        done += weight * fraction
        total += weight
    return (100.0 * done / total if total else 0.0), done, total


def next_progress(program, stage_id, stage):
    statuses = complete(program)
    if is_done(stage.get("status"), statuses):
        return {"percent": 100.0, "basis": "stage_pass", "open_weight": 0.0, "eta_override": None}
    source = stage.get("progress_source") or {}
    kind = source.get("kind")
    if kind == "archive_assimilation":
        path = ROOT / str(source.get("path", ""))
        workspace = load(path) if path.exists() else {}
        pct = float(df.nested(workspace, str(source.get("percent_field", "combined_progress.exact_coverage_percent")), source.get("fallback_percent", 0)) or 0)
        return {
            "percent": pct,
            "basis": f"{source.get('path')}:frozen_atomic_obligations",
            "open_weight": max(0.0, 100.0 - pct),
            "eta_override": workspace.get("eta") if isinstance(workspace.get("eta"), dict) else None,
            "denominator_state": df.nested(workspace, str(source.get("denominator_state_field", "combined_progress.denominator_state")), "MISSING"),
        }
    if kind in {"work_packages", "stage_workspace"}:
        path = ROOT / str(source.get("path", ""))
        if not path.exists():
            return {"percent": float(source.get("missing_means", 0) or 0), "basis": f"missing:{source.get('path')}", "open_weight": 1.0, "eta_override": None}
        pct, done, total = package_progress(load(path), str(source.get("field", "work_packages")), [str(x) for x in source.get("include_prefixes", [])] or None, statuses)
        return {"percent": pct, "basis": f"{source.get('path')}:{source.get('field', 'work_packages')}", "open_weight": max(0.0, total-done), "eta_override": None}
    if kind == "terminal":
        return {"percent": float(source.get("value", 100) or 100), "basis": "terminal", "open_weight": 0.0, "eta_override": None}
    return {"percent": 0.0, "basis": f"unsupported:{kind}", "open_weight": 1.0, "eta_override": None}


def next_eta(stage_id, progress, throughput):
    hours_per_day = float(throughput.get("user_active_hours_per_day", 10) or 10)
    if progress["percent"] >= 100:
        return {"low": 0.0, "high": 0.0, "confidence": "HIGH", "basis": "complete", "hours_per_day": hours_per_day}
    override = progress.get("eta_override")
    if isinstance(override, dict):
        low_value = override.get("calibrated_low_days", override.get("bootstrap_low_days"))
        high_value = override.get("calibrated_high_days", override.get("bootstrap_high_days"))
        return {
            "low": float(low_value) if low_value is not None else None,
            "high": float(high_value) if high_value is not None else None,
            "confidence": str(override.get("confidence", "LOW")),
            "basis": str(override.get("basis", "workspace_eta")),
            "hours_per_day": float(override.get("owner_active_hours_per_day", hours_per_day) or hours_per_day),
        }
    prior = (throughput.get("bootstrap_stage_priors") or {}).get(stage_id)
    if isinstance(prior, dict):
        open_weight = float(progress.get("open_weight", 1))
        low_hours = float(prior.get("serial_hours_per_open_weight_low", 1))
        high_hours = float(prior.get("serial_hours_per_open_weight_high", low_hours))
        parallel_low = max(1.0, float(prior.get("effective_parallelism_low", 1)))
        parallel_high = max(parallel_low, float(prior.get("effective_parallelism_high", parallel_low)))
        return {
            "low": open_weight * low_hours / parallel_high / hours_per_day,
            "high": open_weight * high_hours / parallel_low / hours_per_day,
            "confidence": str(prior.get("confidence", "LOW")),
            "basis": "bootstrap_stage_priors",
            "hours_per_day": hours_per_day,
        }
    return {"low": None, "high": None, "confidence": "UNAVAILABLE", "basis": "no_eta", "hours_per_day": hours_per_day}


def bar(percent, cells=20):
    filled = max(0, min(cells, round(cells * float(percent) / 100.0)))
    return "[" + "#" * filled + "." * (cells - filled) + "]"


def fmt_days(value, hours_per_day):
    if value is None:
        return "?"
    if value <= 0:
        return "0h"
    if value < 1:
        return f"~{max(1, round(value * hours_per_day))}h"
    if value < 10:
        return f"{value:.1f}d"
    return f"{math.ceil(value)}d"


def resolve(program_path=DEFAULT_PROGRAM, throughput_path=DEFAULT_THROUGHPUT, as_of=None):
    program = load(program_path)
    throughput = load(throughput_path) if throughput_path.exists() else {"user_active_hours_per_day": 10}
    stage_id, stage = next_stage(program)
    progress = next_progress(program, stage_id, stage)
    eta = next_eta(stage_id, progress, throughput)
    forecast_date = df.parse_iso_date(as_of) if as_of else df.date.today()
    doomsday = df.resolve(ROOT, forecast_date)
    cells = int((program.get("progress_semantics") or {}).get("bar_cells", 20))
    return {
        "stage_id": stage_id,
        "label": stage.get("label", stage_id),
        "percent": round(float(progress["percent"]), 1),
        "bar": bar(progress["percent"], cells),
        "progress_basis": progress["basis"],
        "denominator_state": progress.get("denominator_state"),
        "eta": eta,
        "doomsday": {**doomsday, "bar": bar(doomsday["progress_percent"], cells)},
    }


def render_text(result):
    eta = result["eta"]
    doom = result["doomsday"]
    hpd = float(eta["hours_per_day"])
    conditional = "yes" if doom["conditional_on_immediate_training_authorization"] else "no"
    return "\n".join([
        "NEXT LEVEL",
        f"Stage: {result['label']}",
        f"Progress: {result['bar']} {result['percent']:g}%",
        f"ETA @ {hpd:g}h/day: {fmt_days(eta['low'], hpd)} - {fmt_days(eta['high'], hpd)}",
        f"ETA confidence: {eta['confidence']} ({eta['basis']})",
        "",
        "DOOMSDAY / Clay 0.1",
        f"Progress: {doom['bar']} {doom['progress_percent']:g}%",
        f"Forecast: {doom['forecast_low']} - {doom['forecast_high']}",
        f"Center: {doom['forecast_center']}",
        f"Confidence: {doom['confidence']}",
        f"Conditional on immediate training authorization when data is ready: {conditional}",
        f"Forecast basis: {len(doom['rows'])}-row dynamic critical path + live capabilities/APIs",
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--as-of")
    args = parser.parse_args()
    result = resolve(as_of=args.as_of)
    print(json.dumps(result, default=df.serializable, indent=2) if args.json else render_text(result))


if __name__ == "__main__":
    main()
