#!/usr/bin/env python3
"""Freshness-gated publisher for Clay GO collective metrics.

This module preserves the original CLAY_GO_COLLECTIVE_METRICS/v1 collector as a
byte-identical legacy implementation module and layers the Supervisor 8.76+
freshness/authority/snapshot publication law on the existing publisher path.

It performs no provider/model call and mints no runtime/model/training credit.
"""
from __future__ import annotations

import argparse as _argparse
import datetime as _dt
import hashlib as _hashlib
import importlib.util as _importlib_util
import json as _json
from pathlib import Path as _Path
from typing import Any as _Any

_LEGACY_PATH = _Path(__file__).with_name("go_collective_metrics_legacy_v1.py")
_LEGACY_SPEC = _importlib_util.spec_from_file_location("_clay_go_collective_metrics_legacy_v1", _LEGACY_PATH)
if _LEGACY_SPEC is None or _LEGACY_SPEC.loader is None:
    raise RuntimeError("GO_COLLECTIVE_METRICS_LEGACY_REQUIRED")
_legacy = _importlib_util.module_from_spec(_LEGACY_SPEC)
_LEGACY_SPEC.loader.exec_module(_legacy)

# Preserve the established public helper API used by existing tests and callers.
for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

FRESHNESS_RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_BOUNDED_SNAPSHOT/v1"
LIVE_INPUT_PATHS = {
    "swarm": "free swarm/LIVE_METRICS.json",
    "forge": "free swarm/FORGE_LIVE.json",
    "distillery": "free swarm/DISTILLERY_LIVE.json",
}


def _canonical_json_bytes(value: _Any) -> bytes:
    return _json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return _hashlib.sha256(data).hexdigest()


def _epoch_key(value: _Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        return ()
    out: list[int] = []
    for part in text.split("."):
        try:
            out.append(int(part))
        except ValueError:
            return ()
    return tuple(out)


def selected_authority(repo: _Path) -> dict[str, _Any]:
    inbox = read_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    epoch = str(inbox.get("schema_version") or "").strip()
    steering = str(inbox.get("steering") or "").strip()
    if not epoch or not steering:
        return {
            "state": "UNMEASURED",
            "reason": "SUPERVISOR_INBOX_SELECTION_UNRESOLVED",
            "authority_epoch": epoch or None,
            "steering": steering or None,
        }
    return {
        "state": "CURRENT",
        "reason": "INBOX_SELECTED_STEERING",
        "authority_epoch": epoch,
        "steering": steering,
    }


def _read_live_input(repo: _Path, logical_name: str, relpath: str) -> dict[str, _Any]:
    path = repo / relpath
    try:
        raw = path.read_bytes()
        value = _json.loads(raw.decode("utf-8"))
    except Exception as exc:
        return {
            "name": logical_name,
            "path": relpath,
            "state": "UNMEASURED",
            "reason": f"READ_OR_JSON_FAILED:{type(exc).__name__}",
            "sha256": None,
            "generated_at": None,
        }
    if not isinstance(value, dict):
        return {
            "name": logical_name,
            "path": relpath,
            "state": "UNMEASURED",
            "reason": "ROOT_NOT_OBJECT",
            "sha256": _sha256_bytes(raw),
            "generated_at": None,
        }
    ts = parse_ts(value.get("generated_at"))
    if ts is None:
        return {
            "name": logical_name,
            "path": relpath,
            "state": "UNMEASURED",
            "reason": "GENERATED_AT_INVALID_OR_MISSING",
            "sha256": _sha256_bytes(raw),
            "generated_at": value.get("generated_at"),
        }
    return {
        "name": logical_name,
        "path": relpath,
        "state": "MEASURED",
        "reason": "OK",
        "sha256": _sha256_bytes(raw),
        "generated_at": ts.astimezone(_dt.timezone.utc).isoformat(),
        "value": value,
    }


def build_bounded_snapshot(repo: _Path) -> dict[str, _Any]:
    authority = selected_authority(repo)
    sources = {
        name: _read_live_input(repo, name, relpath)
        for name, relpath in LIVE_INPUT_PATHS.items()
    }
    measured = authority.get("state") == "CURRENT" and all(
        source.get("state") == "MEASURED" for source in sources.values()
    )
    if not measured:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "state": "UNMEASURED",
            "reason": (
                authority.get("reason")
                if authority.get("state") != "CURRENT"
                else "LIVE_INPUT_UNMEASURED"
            ),
            "authority_epoch": authority.get("authority_epoch"),
            "steering": authority.get("steering"),
            "sources": {
                key: {k: v for k, v in source.items() if k != "value"}
                for key, source in sources.items()
            },
            "snapshot_id": None,
            "latest_input_at": None,
            "observations": None,
        }

    source_identity = {
        key: {
            "path": source["path"],
            "sha256": source["sha256"],
            "generated_at": source["generated_at"],
        }
        for key, source in sources.items()
    }
    latest = max(
        parse_ts(source["generated_at"]) for source in sources.values()
    )
    assert latest is not None

    snapshot_preimage = {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": authority["authority_epoch"],
        "steering": authority["steering"],
        "sources": source_identity,
    }
    snapshot_id = _sha256_bytes(_canonical_json_bytes(snapshot_preimage))

    swarm = sources["swarm"]["value"]
    forge = sources["forge"]["value"]
    distillery = sources["distillery"]["value"]
    observations = {
        "swarm": {
            "snapshot_id": snapshot_id,
            "generated_at": sources["swarm"]["generated_at"],
            "worker_records": (swarm.get("workers") or {}).get("worker_records"),
            "total_tokens": (swarm.get("workers") or {}).get("total_tokens"),
            "nominal_accepted_deltas": (swarm.get("deltas") or {}).get("nominal_accepted"),
            "qualified_accepted_deltas": (swarm.get("deltas") or {}).get("accepted"),
        },
        "forge": {
            "snapshot_id": snapshot_id,
            "generated_at": sources["forge"]["generated_at"],
            "evaluations": forge.get("evaluations"),
            "accepted_deltas": forge.get("accepted_deltas"),
            "state": forge.get("state"),
        },
        "distillery": {
            "snapshot_id": snapshot_id,
            "generated_at": sources["distillery"]["generated_at"],
            "accepted_packets": distillery.get("accepted_packets"),
            "accepted_dataset_tokens": distillery.get("accepted_dataset_tokens"),
            "state": distillery.get("state"),
        },
    }
    return {
        "schema": SNAPSHOT_SCHEMA,
        "state": "CURRENT",
        "reason": "BOUNDED_LIVE_INPUTS_MEASURED",
        "authority_epoch": authority["authority_epoch"],
        "steering": authority["steering"],
        "sources": source_identity,
        "snapshot_id": snapshot_id,
        "latest_input_at": latest.astimezone(_dt.timezone.utc).isoformat(),
        "observations": observations,
    }


def classify_publication(existing: dict[str, _Any], snapshot: dict[str, _Any]) -> str:
    if snapshot.get("state") != "CURRENT" or not snapshot.get("snapshot_id"):
        return "UNMEASURED"
    if not isinstance(existing, dict) or not existing:
        return "ABSENT"

    old_epoch = str(existing.get("authority_epoch") or "")
    current_epoch = str(snapshot.get("authority_epoch") or "")
    if old_epoch != current_epoch:
        return "HISTORICAL_AUTHORITY_EPOCH"

    old_snapshot = existing.get("bounded_snapshot")
    if not isinstance(old_snapshot, dict):
        return "STALE_UNBOUND_LEGACY"
    if old_snapshot.get("snapshot_id") == snapshot.get("snapshot_id"):
        return "CURRENT"

    old_ts = parse_ts(old_snapshot.get("latest_input_at"))
    new_ts = parse_ts(snapshot.get("latest_input_at"))
    if old_ts is None or new_ts is None:
        return "UNMEASURED"
    if old_ts < new_ts:
        return "STALE_LIVE_INPUT"
    if old_ts > new_ts:
        return "NEWER_PUBLICATION_PRESENT"
    return "DIVERGENT_SAME_TIME_SNAPSHOT"


def publication_guard(existing: dict[str, _Any], candidate: dict[str, _Any]) -> tuple[bool, str]:
    snapshot = candidate.get("bounded_snapshot")
    if not isinstance(snapshot, dict) or snapshot.get("state") != "CURRENT":
        return False, "CANDIDATE_SNAPSHOT_UNMEASURED"

    candidate_epoch = _epoch_key(candidate.get("authority_epoch"))
    existing_epoch = _epoch_key(existing.get("authority_epoch")) if isinstance(existing, dict) else ()
    if existing and existing_epoch and candidate_epoch and existing_epoch > candidate_epoch:
        return False, "STALE_WRITER_AUTHORITY_EPOCH"

    if not existing:
        return True, "NO_EXISTING_PUBLICATION"

    old_snapshot = existing.get("bounded_snapshot")
    if not isinstance(old_snapshot, dict):
        return True, "REPLACE_UNBOUND_LEGACY_PUBLICATION"

    old_ts = parse_ts(old_snapshot.get("latest_input_at"))
    new_ts = parse_ts(snapshot.get("latest_input_at"))
    if old_ts is not None and new_ts is not None:
        if old_ts > new_ts and existing_epoch == candidate_epoch:
            return False, "STALE_WRITER_SUPERSEDED"
        if (
            old_ts == new_ts
            and old_snapshot.get("snapshot_id") != snapshot.get("snapshot_id")
            and existing_epoch == candidate_epoch
        ):
            return False, "SNAPSHOT_CONFLICT_SAME_TIME"
    return True, "PUBLICATION_MONOTONIC"


def measurement_digest(result: dict[str, _Any]) -> str:
    bounded = dict(result)
    bounded.pop("generated_at", None)
    bounded.pop("measurement_digest_sha256", None)
    return _sha256_bytes(_canonical_json_bytes(bounded))


def make_freshness_receipt(result: dict[str, _Any], guard_reason: str) -> dict[str, _Any]:
    snapshot = result["bounded_snapshot"]
    return {
        "schema": FRESHNESS_RECEIPT_SCHEMA,
        "authority_epoch": result["authority_epoch"],
        "steering": snapshot.get("steering"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "snapshot_latest_input_at": snapshot.get("latest_input_at"),
        "source_identities": snapshot.get("sources"),
        "result_digest_sha256": result.get("measurement_digest_sha256"),
        "publication_guard": guard_reason,
        "runtime_credit_added": 0,
        "scope": "COLLECTIVE_METRICS_FRESHNESS_AND_PUBLICATION_ONLY",
    }


def _freshness_markdown_prefix(result: dict[str, _Any]) -> str:
    snapshot = result["bounded_snapshot"]
    return "\n".join([
        "<!-- GO_COLLECTIVE_FRESHNESS:BEGIN -->",
        "## GO Collective Metrics Freshness",
        f"- Authority epoch: `{result['authority_epoch']}`",
        f"- Bounded snapshot: `{snapshot['snapshot_id']}`",
        f"- Latest bounded live input: `{snapshot['latest_input_at']}`",
        "- Freshness: `CURRENT`",
        "- Forge / Distillery / Swarm observations below are bound to the same snapshot identity.",
        "<!-- GO_COLLECTIVE_FRESHNESS:END -->",
        "",
    ])


def main() -> int:
    ap = _argparse.ArgumentParser()
    ap.add_argument("--repo", type=_Path, default=_Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=_Path, default=_Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=_Path, default=None)
    ap.add_argument("--output-md", type=_Path, default=None)
    ap.add_argument("--freshness-receipt", type=_Path, default=None)
    ap.add_argument("--update-readme", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    config = load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise SystemExit("GO_METRICS_CONFIG_REQUIRED")

    snapshot = build_bounded_snapshot(repo)
    if snapshot.get("state") != "CURRENT":
        raise SystemExit("GO_COLLECTIVE_METRICS_SNAPSHOT_UNMEASURED")

    workers = explicit_worker_rows(repo)
    workers.extend(free_swarm_rows(args.artifacts))
    deltas = delta_rows(repo)
    attach_delta_metrics(workers, deltas, config)

    result = {
        "schema": SCHEMA,
        # Deterministic for the same bounded live inputs instead of wall-clock publication time.
        "generated_at": snapshot["latest_input_at"],
        "authority_epoch": snapshot["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "config_sha256": sha256_json(config),
        "worker_record_count": len(workers),
        "aggregate": aggregate(workers, config),
        "workers": workers,
        "bounded_snapshot": snapshot,
        "live_observations": snapshot["observations"],
        "freshness": {
            "state": "CURRENT",
            "reason": "BOUNDED_SNAPSHOT_CURRENT_AT_PUBLICATION",
            "snapshot_id": snapshot["snapshot_id"],
        },
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "runtime_credit_added": 0,
        "note": (
            "Derived measurement only. Freshness is fail-closed and publication-monotonic; "
            "this cannot mint canonical truth or runtime/model/training credit."
        ),
    }
    result["measurement_digest_sha256"] = measurement_digest(result)

    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    receipt_path = args.freshness_receipt or (
        repo / "free swarm/COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json"
    )

    existing = read_json(out_json) if out_json.exists() else {}
    allowed, guard_reason = publication_guard(existing, result)
    if not allowed:
        raise SystemExit(guard_reason)

    md = _freshness_markdown_prefix(result) + markdown(result)
    receipt = make_freshness_receipt(result, guard_reason)

    out_json.write_text(
        _json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    out_md.write_text(md, encoding="utf-8")
    receipt_path.write_text(
        _json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.update_readme:
        readme = repo / "free swarm/README.md"
        current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
        readme.write_text(replace_block(current, md), encoding="utf-8")

    print(out_json)
    print(out_md)
    print(receipt_path)
    h = result["aggregate"]["hcu_confidence"]
    print(_json.dumps({
        "workers": len(workers),
        "snapshot_id": snapshot["snapshot_id"],
        "authority_epoch": snapshot["authority_epoch"],
        "tqe": result["aggregate"]["token_quality_efficiency"],
        "cqs": result["aggregate"]["code_quality_score"],
        "vis": result["aggregate"]["verified_innovation_score"],
        "cilr": result["aggregate"]["capability_information_latency_ratio"],
        "hcu_forecast_probability": h.get("forecast_probability"),
        "calibration_state": h.get("calibration_state"),
        "publication_guard": guard_reason,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
