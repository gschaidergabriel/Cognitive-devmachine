#!/usr/bin/env python3
"""Resolve NEXT LEVEL and program-wide targets such as DOOMSDAY.

Stage order, progress contracts and target composition are data-driven from
PROGRAM_STATE.json. Level 0 may use exact frozen archive obligations.
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
        raise ValueError(f"expected object: {path}")
    return data


def _nested(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def _complete_set(program: dict[str, Any]) -> set[str]:
    vals = (program.get("progress_semantics") or {}).get(
        "complete_statuses", ["PASS", "COMPLETE", "COMPLETED", "DONE", "CLOSED"]
    )
    return {str(x).upper() for x in vals}


def _is_complete(value: Any, complete: set[str]) -> bool:
    return str(value or "").upper() in complete


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


def _selected_packages(packages: dict[str, Any], source: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    prefixes = [str(x) for x in source.get("include_prefixes", [])]
    out: list[tuple[str, dict[str, Any]]] = []
    for package_id, payload in packages.items():
        pid = str(package_id)
        if prefixes and not any(pid.startswith(prefix) for prefix in prefixes):
            continue
        out.append((pid, payload if isinstance(payload, dict) else {"status": str(payload)}))
    return out


def stage_progress(program: dict[str, Any], stage_id: str, stage: dict[str, Any]) -> dict[str, Any]:
    complete = _complete_set(program)
    if _is_complete(stage.get("status"), complete):
        return {"percent": 100, "exact_percent": 100.0, "completed_weight": 1.0, "total_weight": 1.0, "open_weight": 0.0, "basis": "stage_status_pass"}

    source = stage.get("progress_source") or {}
    kind = source.get("kind", "gate")

    if kind == "terminal":
        exact = max(0.0, min(100.0, float(source.get("value", 100))))
        return {"percent": int(round(exact)), "exact_percent": exact, "completed_weight": exact, "total_weight": 100.0, "open_weight": 100.0-exact, "basis": "terminal"}

    if kind == "archive_assimilation":
        rel = source.get("path")
        if not rel:
            raise ValueError(f"{stage_id}: archive progress_source.path missing")
        path = ROOT / str(rel)
        if not path.exists():
            fallback = float(source.get("fallback_percent", 0))
            return {"percent": int(round(fallback)), "exact_percent": fallback, "completed_weight": 0.0, "total_weight": 0.0, "open_weight": 1.0, "basis": f"missing:{rel}", "denominator_state": "MISSING"}
        workspace = _load(path)
        exact = float(_nested(workspace, str(source.get("percent_field", "combined_progress.exact_coverage_percent"))))
        denominator_state = str(_nested(workspace, str(source.get("denominator_state_field", "combined_progress.denominator_state"))))
        combined = workspace.get("combined_progress") or {}
        completed = float(combined.get("completed_atomic_obligations", 0) or 0)
        total = float(combined.get("total_atomic_obligations", 0) or 0)
        return {
            "percent": max(0, min(100, int(round(exact)))),
            "exact_percent": max(0.0, min(100.0, exact)),
            "completed_weight": completed,
            "total_weight": total,
            "open_weight": max(0.0, total-completed) if total > 0 else 1.0,
            "basis": f"{rel}:frozen_atomic_obligations",
            "denominator_state": denominator_state,
            "eta_override": workspace.get("eta") if isinstance(workspace.get("eta"), dict) else None,
        }

    if kind in {"work_packages", "stage_workspace"}:
        rel = source.get("path")
        if not rel:
            raise ValueError(f"{stage_id}: progress_source.path missing")
        path = ROOT / str(rel)
        if not path.exists():
            exact = float(source.get("missing_means", 0))
            return {"percent": int(round(exact)), "exact_percent": exact, "completed_weight": 0.0, "total_weight": 0.0, "open_weight": 0.0, "basis": f"missing:{rel}", "workspace_missing": True}
        workspace = _load(path)
        field = str(source.get("field", "work_packages"))
        packages = _nested(workspace, field)
        if not isinstance(packages, dict):
            raise ValueError(f"{stage_id}: {rel}:{field} is not an object")
        selected = _selected_packages(packages, source)
        default_weight = float((program.get("progress_semantics") or {}).get("default_work_package_weight", 1.0))
        done = total = 0.0
        for _, payload in selected:
            weight = float(payload.get("weight", default_weight))
            done += weight * _package_fraction(payload, complete)
            total += weight
        exact = 100.0 * done / total if total else 0.0
        return {
            "percent": max(0, min(100, int(round(exact)))),
            "exact_percent": max(0.0, min(100.0, exact)),
            "completed_weight": done,
            "total_weight": total,
            "open_weight": max(0.0, total-done),
            "basis": f"{rel}:{field}",
        }

    return {"percent": 0, "exact_percent": 0.0, "completed_weight": 0.0, "total_weight": 1.0, "open_weight": 1.0, "basis": f"unsupported:{kind}"}


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


def _measured_velocity(throughput: dict[str, Any], stage_id: str) -> tuple[float | None, int]:
    rates: list[float] = []
    for row in throughput.get("observations") or []:
        if not isinstance(row, dict) or row.get("stage_id") not in {None, stage_id}:
            continue
        try:
            completed = float(row.get("completed_weight"))
            hours = float(row.get("owner_active_hours"))
        except (TypeError, ValueError):
            continue
        if completed > 0 and hours > 0:
            rates.append(completed * 10.0 / hours)
    if not rates:
        return None, 0
    rates.sort()
    n = len(rates)
    median = rates[n//2] if n % 2 else (rates[n//2-1] + rates[n//2]) / 2.0
    return median, n


def estimate_stage_eta(stage_id: str, progress: dict[str, Any], throughput: dict[str, Any]) -> dict[str, Any]:
    hours_per_day = float(throughput.get("user_active_hours_per_day", 10.0) or 10.0)
    if progress.get("exact_percent", 0.0) >= 100.0:
        return {"low_days": 0.0, "high_days": 0.0, "confidence": "HIGH", "basis": "stage_complete", "hours_per_day": hours_per_day}

    override = progress.get("eta_override")
    if isinstance(override, dict):
        low = override.get("calibrated_low_days", override.get("bootstrap_low_days"))
        high = override.get("calibrated_high_days", override.get("bootstrap_high_days"))
        return {
            "low_days": float(low) if low is not None else None,
            "high_days": float(high) if high is not None else None,
            "confidence": str(override.get("confidence", "LOW")),
            "basis": str(override.get("basis", "stage_workspace_eta")),
            "hours_per_day": float(override.get("owner_active_hours_per_day", hours_per_day) or hours_per_day),
        }

    open_weight = float(progress.get("open_weight", 0.0))
    velocity, count = _measured_velocity(throughput, stage_id)
    if velocity and velocity > 0 and open_weight > 0:
        center_days = open_weight / velocity
        return {
            "low_days": max(0.1, center_days * 0.65),
            "high_days": max(0.2, center_days * 1.6),
            "confidence": "HIGH" if count >= 5 else "MEDIUM",
            "basis": "measured_completed_weight_per_10h_owner_day",
            "hours_per_day": hours_per_day,
        }

    prior = (throughput.get("bootstrap_stage_priors") or {}).get(stage_id)
    if isinstance(prior, dict) and open_weight > 0:
        serial_low = float(prior.get("serial_hours_per_open_weight_low", 1.0))
        serial_high = float(prior.get("serial_hours_per_open_weight_high", serial_low))
        par_low = max(1.0, float(prior.get("effective_parallelism_low", 1.0)))
        par_high = max(par_low, float(prior.get("effective_parallelism_high", par_low)))
        return {
            "low_days": (open_weight * serial_low / par_high) / hours_per_day,
            "high_days": (open_weight * serial_high / par_low) / hours_per_day,
            "confidence": str(prior.get("confidence", "LOW")),
            "basis": "bootstrap_stage_priors",
            "hours_per_day": hours_per_day,
        }

    return {"low_days": None, "high_days": None, "confidence": "UNAVAILABLE", "basis": "no_stage_eta", "hours_per_day": hours_per_day}


def target_progress(program: dict[str, Any], target_id: str, throughput: dict[str, Any]) -> dict[str, Any]:
    target = (program.get("program_targets") or {}).get(target_id)
    if not isinstance(target, dict):
        raise KeyError(f"program target not found: {target_id}")
    gates = program.get("stage_gates") or {}
    required = [str(x) for x in target.get("required_stages", [])]
    if not required:
        raise ValueError(f"target {target_id} has no required_stages")

    weight = float(target.get("stage_weight", 1.0))
    weighted_done = weighted_total = 0.0
    stage_rows: list[dict[str, Any]] = []
    eta_low = eta_high = 0.0
    eta_basis: list[str] = []
    eta_bootstrap = target.get("eta_bootstrap_days_by_stage") or {}

    for stage_id in required:
        stage = gates.get(stage_id) or {}
        progress = stage_progress(program, stage_id, stage)
        frac = float(progress.get("exact_percent", 0.0)) / 100.0
        weighted_done += weight * frac
        weighted_total += weight
        row = {"stage_id": stage_id, "exact_percent": progress.get("exact_percent", 0.0), "basis": progress.get("basis")}
        stage_rows.append(row)

        if frac >= 1.0:
            continue

        stage_eta = estimate_stage_eta(stage_id, progress, throughput)
        low = stage_eta.get("low_days")
        high = stage_eta.get("high_days")
        # For not-yet-materialized future workspaces use the explicit target bootstrap.
        if (low is None or high is None) and isinstance(eta_bootstrap.get(stage_id), dict):
            b = eta_bootstrap[stage_id]
            remaining = max(0.0, 1.0-frac)
            low = float(b.get("low", 0.0)) * remaining
            high = float(b.get("high", 0.0)) * remaining
            eta_basis.append(f"{stage_id}:target_bootstrap")
        else:
            eta_basis.append(f"{stage_id}:{stage_eta.get('basis')}")
        if low is not None:
            eta_low += float(low)
        if high is not None:
            eta_high += float(high)

    exact = 100.0 * weighted_done / weighted_total if weighted_total else 0.0
    return {
        "target_id": target_id,
        "label": str(target.get("label", target_id)),
        "exact_percent": exact,
        "percent": int(round(exact)),
        "stage_rows": stage_rows,
        "eta": {
            "low_days": eta_low,
            "high_days": eta_high,
            "confidence": str(target.get("eta_confidence", "LOW")),
            "basis": ";".join(eta_basis),
            "hours_per_day": float(throughput.get("user_active_hours_per_day", 10.0) or 10.0),
        },
    }


def progress_bar(percent: int, cells: int) -> str:
    cells = max(5, min(60, int(cells)))
    filled = int(round(cells * percent / 100.0))
    return "[" + "#" * filled + "." * (cells-filled) + "]"


def resolve(program_path: Path = DEFAULT_PROGRAM, throughput_path: Path = DEFAULT_THROUGHPUT) -> dict[str, Any]:
    program = _load(program_path)
    throughput = _load(throughput_path) if throughput_path.exists() else {"user_active_hours_per_day": 10, "observations": [], "bootstrap_stage_priors": {}}
    stage_id, stage = next_unpassed(program)
    progress = stage_progress(program, stage_id, stage)
    eta = estimate_stage_eta(stage_id, progress, throughput)
    cells = int((program.get("progress_semantics") or {}).get("bar_cells", 20))
    result = {
        "program_id": program.get("program_id"),
        "stage_id": stage_id,
        "label": stage.get("label", stage_id),
        "stage_status": stage.get("status", "UNKNOWN"),
        "percent": progress["percent"],
        "exact_percent": progress.get("exact_percent", float(progress["percent"])),
        "bar": progress_bar(int(progress["percent"]), cells),
        "progress_basis": progress.get("basis"),
        "denominator_state": progress.get("denominator_state"),
        "eta": eta,
        "targets": {},
    }
    for target_id in (program.get("program_targets") or {}):
        target = target_progress(program, str(target_id), throughput)
        target["bar"] = progress_bar(int(target["percent"]), cells)
        result["targets"][str(target_id)] = target
    return result


def _fmt_days(value: float | None, hours_per_day: float) -> str:
    if value is None:
        return "?"
    if value <= 0:
        return "0h"
    if value < 1.0:
        return f"~{max(1, int(round(value * hours_per_day)))}h"
    if value < 10:
        return f"{value:.1f}d"
    return f"{math.ceil(value)}d"


def render_text(result: dict[str, Any]) -> str:
    eta = result["eta"]
    hpd = float(eta["hours_per_day"])
    lines = [
        "NEXT LEVEL",
        f"Stage: {result['label']}",
        f"Progress: {result['bar']} {result['percent']}%",
        f"ETA @ {hpd:g}h/day: {_fmt_days(eta['low_days'], hpd)} - {_fmt_days(eta['high_days'], hpd)}",
        f"ETA confidence: {eta['confidence']} ({eta['basis']})",
    ]
    for target in result.get("targets", {}).values():
        teta = target["eta"]
        thpd = float(teta["hours_per_day"])
        lines.extend([
            "",
            str(target["label"]),
            f"Progress: {target['bar']} {target['percent']}%",
            f"ETA @ {thpd:g}h/day: {_fmt_days(teta['low_days'], thpd)} - {_fmt_days(teta['high_days'], thpd)}",
            f"ETA confidence: {teta['confidence']}",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", default=str(DEFAULT_PROGRAM))
    parser.add_argument("--throughput", default=str(DEFAULT_THROUGHPUT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = resolve(Path(args.program), Path(args.throughput))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))


if __name__ == "__main__":
    main()
