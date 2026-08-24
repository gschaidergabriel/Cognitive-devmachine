#!/usr/bin/env python3
"""Successor guard for Clay GO collective metrics.

v1 remains the raw evidence/parser implementation. v2 adds two fail-closed properties
required by the active metrics protocol:

1. one derived GO aggregate is scoped to one exact reproducible macrocycle id;
2. verified utility/CQS/VIS are aggregated by evidence lineage, not worker count.

This module performs no provider call and cannot mint runtime/model/training credit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
import statistics
from typing import Any, Callable

SCHEMA = "CLAY_GO_COLLECTIVE_METRICS/v2"
UNRESOLVED_IDS = {"", "MACROCYCLE_ID_UNRESOLVED", "UNKNOWN", "UNRESOLVED", "NONE"}


def _fnum(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _inum(value: Any) -> int | None:
    value = _fnum(value)
    return int(value) if value is not None else None


def exact_macrocycle_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value.upper() in UNRESOLVED_IDS:
        return None
    return value


def select_macrocycle(workers: list[dict[str, Any]], macrocycle_id: str) -> list[dict[str, Any]]:
    wanted = exact_macrocycle_id(macrocycle_id)
    if wanted is None:
        raise ValueError("EXACT_REPRODUCIBLE_MACROCYCLE_ID_REQUIRED")
    return [r for r in workers if exact_macrocycle_id(r.get("macrocycle_id")) == wanted]


def worker_lineage(row: dict[str, Any]) -> str:
    value = row.get("evidence_lineage_resolved", row.get("evidence_lineage"))
    if isinstance(value, list):
        parts = sorted(str(x).strip() for x in value if str(x).strip())
        if parts:
            return "|".join(parts)
    elif value:
        return str(value)
    return "UNRESOLVED_LINEAGE"


def lineage_groups(workers: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in workers:
        groups.setdefault(worker_lineage(row), []).append(row)
    return groups


def _group_stat(
    groups: dict[str, list[dict[str, Any]]],
    field: str,
    within: Callable[[list[float]], float] = statistics.median,
) -> float | None:
    per_lineage: list[float] = []
    for rows in groups.values():
        vals = [_fnum(r.get(field)) for r in rows]
        vals = [v for v in vals if v is not None]
        if vals:
            per_lineage.append(float(within(vals)))
    return statistics.fmean(per_lineage) if per_lineage else None


def apply_lineage_collapse(
    workers: list[dict[str, Any]], legacy_aggregate: dict[str, Any]
) -> dict[str, Any]:
    """Collapse correlated evidence without hiding the token cost of duplicate work."""
    out = dict(legacy_aggregate)
    groups = lineage_groups(workers)

    token_values = [_inum(r.get("total_tokens")) for r in workers]
    known_tokens = [v for v in token_values if v is not None]
    total_tokens = sum(known_tokens) if known_tokens else None

    utility_by_lineage: dict[str, float] = {}
    for lineage, rows in groups.items():
        vals = [_fnum(r.get("verified_utility_units")) for r in rows]
        vals = [max(0.0, v) for v in vals if v is not None]
        utility_by_lineage[lineage] = max(vals) if vals else 0.0
    utility = sum(utility_by_lineage.values())

    out["worker_records"] = len(workers)
    out["exact_token_rows"] = len(known_tokens)
    out["total_tokens"] = total_tokens
    out["lineage_count"] = len(groups)
    out["lineage_ids"] = sorted(groups)
    out["verified_utility_units_raw_worker_sum"] = sum(
        max(0.0, _fnum(r.get("verified_utility_units")) or 0.0) for r in workers
    )
    out["verified_utility_units"] = utility
    out["token_quality_efficiency"] = (
        1000.0 * utility / total_tokens if total_tokens is not None and total_tokens > 0 else None
    )
    out["code_quality_score"] = _group_stat(groups, "code_quality_score")
    out["verified_innovation_score"] = _group_stat(groups, "verified_innovation_score")
    out["missing_token_fraction"] = (
        1.0 - len(known_tokens) / len(workers) if workers else None
    )
    out["lineage_collapse_applied"] = True
    out["lineage_collapse_rule"] = (
        "UTILITY_MAX_WITHIN_LINEAGE_THEN_SUM; CQS_VIS_MEDIAN_WITHIN_LINEAGE_THEN_MEAN; "
        "ALL_KNOWN_TOKENS_REMAIN_IN_DENOMINATOR"
    )
    return out


def load_v1(repo: Path):
    path = repo / "free swarm/go_collective_metrics.py"
    spec = importlib.util.spec_from_file_location("clay_go_collective_metrics_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"CANNOT_LOAD_V1:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_markdown(result: dict[str, Any]) -> str:
    a = result["aggregate"]
    lines = [
        "# GO Collective Recursive-Improvement Metrics v2",
        "",
        f"Macrocycle: `{result['macrocycle_id']}`  ",
        f"Generated: `{result['generated_at']}`  ",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Scoped worker records | {a.get('worker_records', 0)} |",
        f"| Evidence lineages | {a.get('lineage_count', 0)} |",
        f"| Total exact tokens | {a.get('total_tokens', 'UNKNOWN')} |",
        f"| Worker-summed utility (diagnostic only) | {a.get('verified_utility_units_raw_worker_sum', 0)} |",
        f"| Lineage-collapsed verified utility | {a.get('verified_utility_units', 0)} |",
        f"| TQE / 1k tokens | {a.get('token_quality_efficiency', 'UNKNOWN')} |",
        f"| Lineage-collapsed CQS | {a.get('code_quality_score', 'UNKNOWN')} |",
        f"| Lineage-collapsed VIS | {a.get('verified_innovation_score', 'UNKNOWN')} |",
        "",
        "Fail-closed scope: only the exact requested macrocycle is aggregated. Unresolved macrocycle identities are excluded and cannot be silently grouped.",
        "",
        "Lineage rule: correlated workers do not gain utility/quality/innovation voting weight by fanout; their known token cost remains visible in TQE.",
        "",
        "This is derived measurement only and adds zero runtime/model/training credit.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--macrocycle-id", required=True)
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    args = ap.parse_args()

    macrocycle_id = exact_macrocycle_id(args.macrocycle_id)
    if macrocycle_id is None:
        raise SystemExit("EXACT_REPRODUCIBLE_MACROCYCLE_ID_REQUIRED")

    repo = args.repo.resolve()
    v1 = load_v1(repo)
    config = v1.load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise SystemExit("GO_METRICS_CONFIG_REQUIRED")

    workers = v1.explicit_worker_rows(repo)
    workers.extend(v1.free_swarm_rows(args.artifacts))
    all_worker_count = len(workers)
    deltas = v1.delta_rows(repo)
    v1.attach_delta_metrics(workers, deltas, config)
    workers = select_macrocycle(workers, macrocycle_id)

    legacy_aggregate = v1.aggregate(workers, config)
    aggregate = apply_lineage_collapse(workers, legacy_aggregate)
    aggregate["hcu_confidence"] = v1.hcu_forecast(workers, config)

    result = {
        "schema": SCHEMA,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "macrocycle_id": macrocycle_id,
        "all_worker_records_observed_before_scope": all_worker_count,
        "worker_record_count": len(workers),
        "aggregate": aggregate,
        "workers": workers,
        "scope_policy": "EXACT_MACROCYCLE_ONLY_FAIL_CLOSED",
        "runtime_credit_added": 0,
        "note": "Derived measurement only; no canonical truth or runtime/model/training promotion.",
    }

    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS_V2.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS_V2.md")
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA,
        "macrocycle_id": macrocycle_id,
        "workers": len(workers),
        "lineages": aggregate.get("lineage_count"),
        "tqe": aggregate.get("token_quality_efficiency"),
        "output_json": str(out_json),
        "output_md": str(out_md),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
