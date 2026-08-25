#!/usr/bin/env python3
"""Freshness-gated publisher for the existing GO collective metrics collector.

The historical metric computation remains byte-identical in
``go_collective_metrics_core_v1.py``. This wrapper adds only the supervisor-8.77
bounded-input, authority, publication-order and receipt gates; it does not create a
second metrics authority and grants no runtime/model/training credit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_UNAVAILABLE:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


_HERE = Path(__file__).resolve().parent
_CORE_PATH = _HERE / "go_collective_metrics_core_v1.py"
_FRESHNESS_PATH = _HERE / "go_collective_freshness.py"
core = _load_module("go_collective_metrics_core_v1", _CORE_PATH)
freshness = _load_module("go_collective_freshness", _FRESHNESS_PATH)

# Preserve the established module API for tests and downstream imports. main() is the
# only intentionally replaced symbol.
for _name in dir(core):
    if not _name.startswith("__") and _name != "main":
        globals().setdefault(_name, getattr(core, _name))


def _live_value(snapshot: dict[str, Any], name: str) -> Any:
    fields = snapshot.get("fields") if isinstance(snapshot.get("fields"), dict) else {}
    item = fields.get(name) if isinstance(fields.get(name), dict) else {}
    return item.get("value")


def _assert_snapshot_matches_sources(
    snapshot: dict[str, Any], free_workers: list[dict[str, Any]], deltas: list[dict[str, Any]]
) -> None:
    """Do not publish a live label over stale/missing artifact inputs."""
    exact_tokens = [core.inum(row.get("total_tokens")) for row in free_workers]
    observed_tokens = sum(value for value in exact_tokens if value is not None)
    live_tokens = core.inum(_live_value(snapshot, "free_swarm_total_tokens"))
    live_rows = core.inum(_live_value(snapshot, "free_swarm_worker_records"))
    if live_tokens is None or observed_tokens != live_tokens:
        raise RuntimeError("GO_COLLECTIVE_METRICS_SWARM_TOKEN_SNAPSHOT_MISMATCH")
    if live_rows is None or len(free_workers) != live_rows:
        raise RuntimeError("GO_COLLECTIVE_METRICS_SWARM_ROW_SNAPSHOT_MISMATCH")

    forge_evaluations = core.inum(_live_value(snapshot, "forge_evaluations"))
    if forge_evaluations is None or len(deltas) != forge_evaluations:
        raise RuntimeError("GO_COLLECTIVE_METRICS_FORGE_EVALUATION_SNAPSHOT_MISMATCH")


def _freshness_markdown(result: dict[str, Any]) -> str:
    base = core.markdown(result)
    snap = result["bounded_live_snapshot"]
    header = (
        f"Authority epoch: `{result['authority_epoch']}`  \n"
        f"Freshness: `FRESH`  \n"
        f"Bounded snapshot: `{snap['snapshot_id']}`  \n"
        f"Snapshot max input: `{snap['max_input_generated_at']}`  \n"
    )
    marker = f"Schema: `{core.SCHEMA}`  \n"
    return base.replace(marker, marker + header, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--update-readme", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    config = core.load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise SystemExit("GO_METRICS_CONFIG_REQUIRED")

    first_snapshot = freshness.build_live_snapshot(repo)
    workers = core.explicit_worker_rows(repo)
    free_workers = core.free_swarm_rows(args.artifacts)
    workers.extend(free_workers)
    deltas = core.delta_rows(repo)
    _assert_snapshot_matches_sources(first_snapshot, free_workers, deltas)
    core.attach_delta_metrics(workers, deltas, config)

    result = {
        "schema": core.SCHEMA,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authority_epoch": first_snapshot["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "config_sha256": core.sha256_json(config),
        "collector_sha256": _sha256_file(Path(__file__)),
        "collector_core_sha256": _sha256_file(_CORE_PATH),
        "bounded_live_snapshot": first_snapshot,
        "freshness": {
            "schema": freshness.FRESHNESS_SCHEMA,
            "status": "FRESH",
            "snapshot_id": first_snapshot["snapshot_id"],
            "max_input_generated_at": first_snapshot["max_input_generated_at"],
            "publication_rule": "FAIL_CLOSED_MONOTONIC_AUTHORITY_AND_SHARED_SNAPSHOT",
        },
        "worker_record_count": len(workers),
        "aggregate": core.aggregate(workers, config),
        "workers": workers,
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "runtime_credit_added": 0,
        "note": "Derived measurement only. It cannot mint canonical truth or runtime/model/training credit.",
    }
    result["result_digest_sha256"] = freshness.deterministic_result_digest(result)
    md = _freshness_markdown(result)

    # Re-read canonical live inputs and authority after the full computation. Any movement
    # makes this run stale before publication instead of silently labeling it current.
    second_snapshot = freshness.build_live_snapshot(repo)
    if second_snapshot.get("snapshot_id") != first_snapshot.get("snapshot_id"):
        raise SystemExit("GO_COLLECTIVE_METRICS_INPUT_CHANGED_DURING_COMPUTE")
    if freshness.selected_authority_epoch(repo) != result["authority_epoch"]:
        raise SystemExit("GO_COLLECTIVE_METRICS_AUTHORITY_CHANGED_DURING_COMPUTE")

    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    readme_path = None
    readme_text = None
    if args.update_readme:
        readme_path = repo / "free swarm/README.md"
        current = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# Free Swarm\n"
        readme_text = core.replace_block(current, md)

    decision = freshness.publish_bundle(
        out_json=out_json,
        out_md=out_md,
        result=result,
        markdown=md,
        readme_path=readme_path,
        readme_text=readme_text,
    )

    print(out_json)
    print(out_md)
    h = result["aggregate"]["hcu_confidence"]
    print(json.dumps({
        "workers": len(workers),
        "tqe": result["aggregate"]["token_quality_efficiency"],
        "cqs": result["aggregate"]["code_quality_score"],
        "vis": result["aggregate"]["verified_innovation_score"],
        "cilr": result["aggregate"]["capability_information_latency_ratio"],
        "hcu_forecast_probability": h.get("forecast_probability"),
        "calibration_state": h.get("calibration_state"),
        "authority_epoch": result["authority_epoch"],
        "snapshot_id": first_snapshot["snapshot_id"],
        "publication": decision,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
