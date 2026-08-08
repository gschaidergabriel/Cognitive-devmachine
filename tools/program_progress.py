#!/usr/bin/env python3
"""Resolve next FRANK Research Center milestone, progress bar and ETA.

The stage order, labels and progress sources are data-driven from
research_entity/rooms/PROGRAM_STATE.json. ETA prefers measured throughput
observations and falls back to explicit bootstrap priors from
PROGRAM_THROUGHPUT.json.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROGRAM = ROOT / "research_entity" / "rooms" / "PROGRAM_STATE.json"
DEFAULT_THROUGHPUT = ROOT / "research_entity" / "rooms" / "PROGRAM_THROUGHPUT.json"


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _nested(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def _complete_set(program: dict[str, Any]) -> set[str]:
    values = (program.get("progress_semantics") or {}).get(
        "complete_statuses", ["PASS", "COMPLETE", "COMPLETED", "DONE", "CLOSED"]
    )
    return {str(x).upper() for x in values}


def _is_complete(status: Any, complete: set[str]) -> bool:
    return str(status or "").upper() in complete


def _select_packages(packages: dict[str, Any], source: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    prefixes = [str(x) for x in source.get("include_prefixes", [])]
    selected: list[tuple[str, dict[str, Any]]] = []
    for package_id, payload in packages.items():
        pid = str(package_id)
        if prefixes and not any(pid.startswith(prefix) for prefix in prefixes):
            continue
        if not isinstance(payload, dict):
            payload = {"status": str(payload)}
        selected.append((pid, payload))
    return selected


def _package_fraction(payload: dict[str, Any], complete: set[str]) -> float:
    subchecks = payload.get("subchecks")
    if isinstance(subchecks, dict) and subchecks:
        done = total = 0.0
        for item in subchecks.values():
            if isinstance(item, dict):
                status = item.get("status", "OPEN")
                weight = float(item.get("weight", 1.0))
            else:
                status = item
                weight = 1.0
            total += weight
            if _is_complete(status, complete):
                done += weight
        return done / total if total else 0.0
    return 1.0 if _is_complete(payload.get("status"), complete) else 0.0


def stage_progress(program: dict[str, Any], stage_id: str, stage: dict[str, Any]) -> dict[str, Any]:
    complete = _complete_set(program)
    if _is_complete(stage.get("status"), complete):
        return {
            "percent": 100,
            "completed_weight": 1.0,
            "total_weight": 1.0,
            "open_weight": 0.0,
            "basis": "stage_status_pass",
        }

    source = stage.get("progress_source") or {}
    kind = source.get("kind", "gate")

    if kind == "terminal":
        percent = max(0, min(100, int(source.get("value", 100))))
        return {
            "percent": percent,
            "completed_weight": float(percent),
            "total_weight": 100.0,
            "open_weight": float(100 - percent),
            "basis": "terminal",
        }

    if kind in {"work_packages", "stage_workspace"}:
        rel = source.get("path")
        if not rel:
            raise ValueError(f"{stage_id}: progress_source.path missing")
        path = ROOT / str(rel)
        if not path.exists():
            percent = int(source.get("missing_means", 0))
            return {
                "percent": percent,
                "completed_weight": 0.0,
                "total_weight": 0.0,
                "open_weight": 0.0,
                "basis": f"missing:{rel}",
            }
        workspace = _load(path)
        field = str(source.get("field", "work_packages"))
        packages = _nested(workspace, field)
        if not isinstance(packages, dict):
            raise ValueError(f"{stage_id}: {rel}:{field} is not an object")
        selected = _select_packages(packages, source)
        default_weight = float((program.get("progress_semantics") or {}).get("default_work_package_weight", 1.0))
        done = total = 0.0
        rows: list[dict[str, Any]] = []
        for package_id, payload in selected:
            weight = float(payload.get("weight", default_weight))
            fraction = _package_fraction(payload, complete)
            done += weight * fraction
            total += weight
            rows.append({
                "id": package_id,
                "status": str(payload.get("status", "OPEN")),
                "weight": weight,
                "fraction": fraction,
            })
        percent = int(round(100.0 * done / total)) if total else 0
        return {
            "percent": max(0, min(100, percent)),
            "completed_weight": done,
            "total_weight": total,
            "open_weight": max(0.0, total - done),
            "basis": f"{rel}:{field}",
            "packages": rows,
        }

    return {
        "percent": 0,
        "completed_weight": 0.0,
        "total_weight": 1.0,
        "open_weight": 1.0,
        "basis": f"unsupported:{kind}",
    }


def next_unpassed(program: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    complete = _complete_set(program)
    gates = program.get("stage_gates") or {}
    order = [str(x) for x in program.get("stage_order", [])]
    if not order:
        raise ValueError("PROGRAM_STATE.stage_order is empty")
    for stage_id in order:
        stage = gates.get(stage_id) or {}
        if not _is_complete(stage.get("status"), complete):
            return stage_id, stage
    final_id = order[-1]
    return final_id, gates.get(final_id) or {}


def _measured_velocity(throughput: dict[str, Any], stage_id: str) -> tuple[float | None, str | None]:
    """Return measured completed-weight per 10h owner day if enough data exists."""
    rows = throughput.get("observations") or []
    weighted_rates: list[float] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("stage_id") not in {None, stage_id}:
            continue
        completed = row.get("completed_weight")
        hours = row.get("owner_active_hours")
        if completed is None or hours in {None, 0}:
            continue
        try:
            completed_f = float(completed)
            hours_f = float(hours)
        except (TypeError, ValueError):
            continue
        if completed_f <= 0 or hours_f <= 0:
            continue
        weighted_rates.append(completed_f * 10.0 / hours_f)
    if not weighted_rates:
        return None, None
    # Median is robust to unusually productive/slow single days.
    weighted_rates.sort()
    n = len(weighted_rates)
    if n % 2:
        median = weighted_rates[n // 2]
    else:
        median = (weighted_rates[n // 2 - 1] + weighted_rates[n // 2]) / 2.0
    return median, "measured_completed_weight_per_10h_owner_day"


def estimate_eta(stage_id: str, progress: dict[str, Any], throughput: dict[str, Any]) -> dict[str, Any]:
    open_weight = float(progress.get("open_weight", 0.0))
    hours_per_day = float(throughput.get("user_active_hours_per_day", 10.0) or 10.0)
    if open_weight <= 0:
        return {
            "low_days": 0.0,
            "high_days": 0.0,
            "confidence": "HIGH",
            "basis": "no_open_weight",
            "hours_per_day": hours_per_day,
        }

    measured, basis = _measured_velocity(throughput, stage_id)
    if measured and measured > 0:
        center_days = open_weight / measured
        # Early measured estimates remain ranges because package difficulty varies.
        return {
            "low_days": max(0.1, center_days * 0.65),
            "high_days": max(0.2, center_days * 1.6),
            "confidence": "MEDIUM" if len(throughput.get("observations") or []) < 5 else "HIGH",
            "basis": basis,
            "hours_per_day": hours_per_day,
        }

    prior = (throughput.get("bootstrap_stage_priors") or {}).get(stage_id)
    if not isinstance(prior, dict):
        return {
            "low_days": None,
            "high_days": None,
            "confidence": "UNAVAILABLE",
            "basis": "no_measured_or_prior_throughput",
            "hours_per_day": hours_per_day,
        }

    serial_low = float(prior.get("serial_hours_per_open_weight_low", 1.0))
    serial_high = float(prior.get("serial_hours_per_open_weight_high", serial_low))
    par_low = max(1.0, float(prior.get("effective_parallelism_low", 1.0)))
    par_high = max(par_low, float(prior.get("effective_parallelism_high", par_low)))

    # Optimistic bound uses lower serial cost and stronger proven/effective parallelism.
    low_hours = open_weight * serial_low / par_high
    # Conservative bound uses higher serial cost and weaker effective parallelism.
    high_hours = open_weight * serial_high / par_low
    return {
        "low_days": low_hours / hours_per_day,
        "high_days": high_hours / hours_per_day,
        "confidence": str(prior.get("confidence", "LOW")),
        "basis": "bootstrap_stage_priors",
        "hours_per_day": hours_per_day,
    }


def progress_bar(percent: int, cells: int) -> str:
    cells = max(5, min(60, int(cells)))
    filled = int(round(cells * percent / 100.0))
    return "[" + "#" * filled + "." * (cells - filled) + "]"


def resolve(program_path: Path = DEFAULT_PROGRAM, throughput_path: Path = DEFAULT_THROUGHPUT) -> dict[str, Any]:
    program = _load(program_path)
    throughput = _load(throughput_path) if throughput_path.exists() else {
        "user_active_hours_per_day": 10,
        "observations": [],
        "bootstrap_stage_priors": {},
    }
    stage_id, stage = next_unpassed(program)
    progress = stage_progress(program, stage_id, stage)
    eta = estimate_eta(stage_id, progress, throughput)
    cells = int((program.get("progress_semantics") or {}).get("bar_cells", 20))
    bar = progress_bar(int(progress["percent"]), cells)
    token_state = throughput.get("token_telemetry") or {}
    return {
        "program_id": program.get("program_id"),
        "stage_id": stage_id,
        "label": stage.get("label", stage_id),
        "stage_status": stage.get("status", "UNKNOWN"),
        "percent": progress["percent"],
        "bar": bar,
        "progress_basis": progress.get("basis"),
        "completed_weight": progress.get("completed_weight"),
        "total_weight": progress.get("total_weight"),
        "open_weight": progress.get("open_weight"),
        "eta": eta,
        "canonical_24h_token_total_available": bool(token_state.get("canonical_24h_total_available", False)),
        "token_note": token_state.get("note"),
    }


def _fmt_days(value: float | None) -> str:
    if value is None:
        return "?"
    if value < 1.0:
        hours = max(1, int(round(value * 10)))
        return f"~{hours}h"
    if value < 10:
        return f"{value:.1f}d"
    return f"{math.ceil(value)}d"


def render_text(result: dict[str, Any]) -> str:
    eta = result["eta"]
    return "\n".join([
        f"Next milestone: {result['label']}",
        f"Progress: {result['bar']} {result['percent']}%",
        f"ETA @ {eta['hours_per_day']:g}h/day: {_fmt_days(eta['low_days'])} - {_fmt_days(eta['high_days'])}",
        f"ETA confidence: {eta['confidence']} ({eta['basis']})",
    ])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--program", default=str(DEFAULT_PROGRAM))
    ap.add_argument("--throughput", default=str(DEFAULT_THROUGHPUT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = resolve(Path(args.program), Path(args.throughput))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))


if __name__ == "__main__":
    main()
