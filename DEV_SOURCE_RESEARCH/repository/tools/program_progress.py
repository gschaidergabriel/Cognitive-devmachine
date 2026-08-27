#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "research_entity" / "rooms" / "PROGRAM_STATE.json"
WORKSPACE = ROOT / "research_entity" / "frank_v0_1" / "FRANK_V0_1_WORKSPACE.json"
THROUGHPUT = ROOT / "research_entity" / "rooms" / "PROGRAM_THROUGHPUT.json"
DOOMSDAY_MODEL = ROOT / "research_entity" / "forecast" / "DOOMSDAY_FORECAST_MODEL.json"
HISTORICAL_EARNED = ROOT / "research_entity" / "forecast" / "HISTORICAL_EARNED_WORK.json"

COMPLETE = {"PASS", "COMPLETE", "COMPLETED", "DONE", "CLOSED"}


def load(path: Path, default=None):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else (default if default is not None else {})
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def is_done(value) -> bool:
    return str(value or "").upper() in COMPLETE


def work_progress(workspace: dict) -> tuple[float, float, float]:
    packages = workspace.get("work_packages") or {}
    done = total = 0.0
    for payload in packages.values():
        if not isinstance(payload, dict):
            payload = {"status": str(payload)}
        weight = float(payload.get("weight", 1) or 1)
        subchecks = payload.get("subchecks")
        if isinstance(subchecks, dict) and subchecks:
            sub_done = sub_total = 0.0
            for item in subchecks.values():
                if isinstance(item, dict):
                    sw = float(item.get("weight", 1) or 1)
                    status = item.get("status")
                else:
                    sw = 1.0
                    status = item
                sub_total += sw
                if is_done(status):
                    sub_done += sw
            fraction = sub_done / sub_total if sub_total else 0.0
        else:
            fraction = 1.0 if is_done(payload.get("status")) else 0.0
        done += weight * fraction
        total += weight
    return (100.0 * done / total if total else 0.0), done, total


def primary_blockers(workspace: dict, limit: int = 4) -> list[str]:
    blockers = []
    for pid, payload in (workspace.get("work_packages") or {}).items():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "")
        blocker = payload.get("blocker")
        if blocker:
            blockers.append(f"{pid}: {blocker}")
        elif status.startswith("BLOCKED"):
            blockers.append(f"{pid}: {status}")
        if len(blockers) >= limit:
            break
    return blockers


def bar(percent: float, cells: int = 20) -> str:
    filled = max(0, min(cells, round(cells * percent / 100.0)))
    return "[" + "#" * filled + "." * (cells - filled) + "]"


def apply_historical_earned(raw: dict, hours_per_day: float) -> dict:
    result = dict(raw)
    earned = load(HISTORICAL_EARNED, {})
    current = max(0.0, min(1.0, float(raw.get("progress_percent", 0.0) or 0.0) / 100.0))
    mapped = earned.get("evidence_mapped_avoided_future_hours")
    baseline = 0.0
    basis = "current_unified_scope_only"
    if isinstance(mapped, dict) and mapped.get("center") is not None:
        historical_hours = max(0.0, float(mapped.get("center") or 0.0))
        current_scope_hours = max(0.0, float(raw.get("scope_center_days", 0.0) or 0.0) * hours_per_day)
        denom = historical_hours + current_scope_hours
        baseline = historical_hours / denom if denom else 0.0
        basis = "evidence_mapped_historical_equivalent_hours_plus_unified_frank_v0_1_scope"
    else:
        cal = earned.get("pre_level0_calibration") or {}
        if cal.get("progress_center_percent") is not None:
            baseline = max(0.0, min(1.0, float(cal["progress_center_percent"]) / 100.0))
            basis = "historical_calibration_prior_plus_unified_frank_v0_1_scope"
    result["remaining_scope_progress_percent"] = round(current * 100.0, 1)
    result["historical_baseline_percent"] = round(baseline * 100.0, 1)
    result["progress_percent"] = round((baseline + (1.0 - baseline) * current) * 100.0, 1)
    result["historical_progress_basis"] = basis
    return result


def resolve(as_of: str | None = None) -> dict:
    program = load(PROGRAM, {})
    workspace = load(WORKSPACE, {})
    throughput = load(THROUGHPUT, {"user_active_hours_per_day": 10})
    model = load(DOOMSDAY_MODEL, {})

    percent, done, total = work_progress(workspace)
    cells = int((program.get("progress_semantics") or {}).get("bar_cells", 20) or 20)
    hours_per_day = float(throughput.get("user_active_hours_per_day", 10) or 10)

    row = (model.get("rows") or {}).get("FRANK_V0_1") or {}
    prior = row.get("prior_days") or {}
    remaining = max(0.0, 1.0 - percent / 100.0)
    eta_low = float(prior.get("low", 0) or 0) * remaining
    eta_high = float(prior.get("high", 0) or 0) * remaining
    eta_conf = str(row.get("confidence") or "UNRESOLVED")

    try:
        import sys
        tools = ROOT / "tools"
        if str(tools) not in sys.path:
            sys.path.insert(0, str(tools))
        import doomsday_forecast as df

        forecast_date = df.parse_iso_date(as_of) if as_of else date.today()
        raw_doom = df.resolve(ROOT, forecast_date)
        doom = apply_historical_earned(raw_doom, hours_per_day)
    except Exception as exc:
        doom = {
            "progress_percent": percent,
            "forecast_low": None,
            "forecast_high": None,
            "forecast_center": None,
            "confidence": "UNRESOLVED",
            "conditional_on_immediate_training_authorization": not bool(workspace.get("training_authorized")),
            "historical_progress_basis": f"resolver_error:{type(exc).__name__}",
        }

    return {
        "program": "FRANK_V0_1",
        "label": "Frank v0.1",
        "stage_status": ((program.get("stage_gates") or {}).get("FRANK_V0_1") or {}).get("status", "UNKNOWN"),
        "percent": round(percent, 1),
        "bar": bar(percent, cells),
        "done_weight": round(done, 3),
        "total_weight": round(total, 3),
        "primary_blockers": primary_blockers(workspace),
        "eta": {
            "low_days": round(eta_low, 2),
            "high_days": round(eta_high, 2),
            "hours_per_day": hours_per_day,
            "confidence": eta_conf,
            "basis": "unified_frank_v0_1_remaining_scope_prior_until_measured_velocity"
        },
        "doomsday": {
            **doom,
            "bar": bar(float(doom.get("progress_percent", 0.0) or 0.0), cells)
        }
    }


def fmt_days(value):
    if value is None:
        return "UNRESOLVED"
    value = float(value)
    if value <= 0:
        return "0d"
    if value < 1:
        return f"{value:.1f}d"
    return f"{value:.1f}d"


def render_text(result: dict) -> str:
    eta = result["eta"]
    doom = result["doomsday"]
    blockers = "; ".join(result.get("primary_blockers") or []) or "none recorded"
    conditional = "yes" if doom.get("conditional_on_immediate_training_authorization", True) else "no"
    return "\n".join([
        "FRANK v0.1",
        f"Progress: {result['bar']} {result['percent']:g}%",
        f"Acceptance: {result['stage_status']}",
        f"Primary blockers: {blockers}",
        f"ETA @ {eta['hours_per_day']:g}h/day: {fmt_days(eta['low_days'])} - {fmt_days(eta['high_days'])}",
        f"ETA confidence: {eta['confidence']} ({eta['basis']})",
        "",
        "DOOMSDAY / finished Frank v0.1",
        f"Progress: {doom['bar']} {float(doom.get('progress_percent',0) or 0):g}%",
        f"Forecast: {doom.get('forecast_low') or 'UNRESOLVED'} - {doom.get('forecast_high') or 'UNRESOLVED'}",
        f"Center: {doom.get('forecast_center') or 'UNRESOLVED'}",
        f"Confidence: {doom.get('confidence') or 'UNRESOLVED'}",
        f"Conditional on owner authorization for final training when required: {conditional}",
        f"Forecast basis: {doom.get('historical_progress_basis','unified Frank v0.1 critical path')}"
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--as-of")
    parser.add_argument("--trigger", help="accepted for compatibility; no trigger-specific Harness progress block exists")
    args = parser.parse_args()
    result = resolve(args.as_of)
    print(json.dumps(result, indent=2, default=str) if args.json else render_text(result))


if __name__ == "__main__":
    main()
