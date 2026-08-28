#!/usr/bin/env python3
"""Read-only GRID10 Fabric -> typed cognitive telemetry adapter.

This adapter deliberately does not infer semantic alignment from operational health.
Semantic/authority axes must be supplied by an upstream deterministic monitor as
TrustedAxisEvidence. Missing safety evidence remains UNKNOWN and therefore fails closed
when evaluated by the Cognitive Envelope Controller.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
import time
from typing import Any, Mapping

from grid10_cognitive_envelope_control_v1 import Alternative, HyperVariable, ProjectionPolicy


@dataclass(frozen=True)
class TrustedAxisEvidence:
    axis: str
    value: float | None
    evidence_status: str
    provenance: tuple[str, ...]
    confidence: float = 1.0
    projection_policy: ProjectionPolicy = ProjectionPolicy.EXPECTED


@dataclass(frozen=True)
class FabricTelemetry:
    state_epoch: int
    generation: int
    variables: Mapping[str, HyperVariable]
    regulators: Mapping[str, Mapping[str, Any]]
    hyperposition: Mapping[str, Any]
    work: Mapping[str, Any]
    source_event_refs: tuple[str, ...]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _unknown(axis: str, policy: ProjectionPolicy = ProjectionPolicy.KEEP_UNKNOWN) -> HyperVariable:
    return HyperVariable(axis, (Alternative(None, 0.0, "UNKNOWN", (f"fabric:{axis}:unknown",)),), policy)


def _axis_from_evidence(ev: TrustedAxisEvidence) -> HyperVariable:
    return HyperVariable(
        ev.axis,
        (Alternative(ev.value, ev.confidence, ev.evidence_status, ev.provenance),),
        ev.projection_policy,
    )


def _read_recent_outbox(path: Any, limit: int = 64) -> list[dict[str, Any]]:
    """Read recent outbox packets through a SQLite read-only connection."""
    db_path = str(path)
    uri = f"file:{db_path}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=2.0)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT packet_digest, packet_json, consumed, submitted_ts "
            "FROM outbox ORDER BY submitted_ts DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    finally:
        con.close()
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            packet = json.loads(row["packet_json"])
        except (TypeError, ValueError):
            continue
        out.append({
            "packet_digest": row["packet_digest"],
            "consumed": int(row["consumed"]),
            "submitted_ts": float(row["submitted_ts"]),
            "packet": packet,
        })
    return out


def collect_fabric_telemetry(
    fabric: Any,
    *,
    trusted_axes: Mapping[str, TrustedAxisEvidence] | None = None,
    regulator_names: tuple[str, ...] = ("temperature", "top_p", "poll_intensity"),
    now: float | None = None,
) -> FabricTelemetry:
    """Collect operational signals without writing Fabric state.

    Operational health is exposed as PROXY evidence. It is never silently promoted to
    semantic alignment, authority integrity, or effect safety.
    """
    trusted_axes = trusted_axes or {}
    now = time.time() if now is None else float(now)
    snap = fabric.snapshot()
    variables: dict[str, HyperVariable] = {}
    refs: list[str] = []

    for axis, ev in sorted(trusted_axes.items()):
        if axis != ev.axis:
            raise ValueError(f"trusted axis key mismatch: {axis!r} != {ev.axis!r}")
        variables[axis] = _axis_from_evidence(ev)
        refs.extend(ev.provenance)

    total_nodes = len(snap.nodes)
    healthy_nodes = sum(1 for n in snap.nodes if int(n.get("healthy", 0)) == 1)
    node_health = healthy_nodes / total_nodes if total_nodes else 1.0

    total_tasks = len(snap.tasks)
    unfinished = sum(1 for t in snap.tasks if t.get("status") != "DONE")
    queue_pressure = unfinished / total_tasks if total_tasks else 0.0

    valid_leases = [l for l in snap.leases if int(l.get("valid", 0)) == 1]
    stale_valid_leases = 0
    for lease in valid_leases:
        granted = float(lease.get("granted_ts") or 0.0)
        # Telemetry horizon only. This does not redefine Fabric lease authority.
        if granted and now - granted > 30.0:
            stale_valid_leases += 1
    stale_fraction = stale_valid_leases / len(valid_leases) if valid_leases else 0.0

    resource_proxy = _clamp01(0.45 * queue_pressure + 0.35 * (1.0 - node_health) + 0.20 * stale_fraction)
    recovery_proxy = _clamp01(0.55 * node_health + 0.25 * (1.0 - stale_fraction) + 0.20 * (1.0 - queue_pressure))

    variables.setdefault(
        "resource_pressure",
        HyperVariable(
            "resource_pressure",
            (Alternative(resource_proxy, 0.7, "PROXY", (f"fabric:epoch:{snap.epoch}:resource",)),),
            ProjectionPolicy.PESSIMISTIC_MAX,
        ),
    )
    variables.setdefault(
        "recovery_margin",
        HyperVariable(
            "recovery_margin",
            (Alternative(recovery_proxy, 0.7, "PROXY", (f"fabric:epoch:{snap.epoch}:recovery",)),),
            ProjectionPolicy.PESSIMISTIC_MIN,
        ),
    )
    refs.extend((f"fabric:epoch:{snap.epoch}:resource", f"fabric:epoch:{snap.epoch}:recovery"))

    recent = _read_recent_outbox(fabric.path)
    branch_counts: list[int] = []
    internal_items = 0
    classified_items = 0
    for row in recent:
        payload = (row["packet"].get("payload") or {})
        alts = payload.get("unresolved_alternatives")
        if isinstance(alts, (list, tuple)):
            branch_counts.append(len(alts))
        if "external" in payload:
            classified_items += 1
            if payload.get("external") is False:
                internal_items += 1
        refs.append(f"outbox:{row['packet_digest']}")

    if classified_items:
        internal_ratio = internal_items / classified_items
        variables.setdefault(
            "self_reinforcement_ratio",
            HyperVariable(
                "self_reinforcement_ratio",
                (Alternative(internal_ratio, 0.45, "PROXY", ("fabric:outbox:internal-ratio",)),),
                ProjectionPolicy.PESSIMISTIC_MAX,
            ),
        )
    else:
        variables.setdefault(
            "self_reinforcement_ratio",
            _unknown("self_reinforcement_ratio", ProjectionPolicy.PESSIMISTIC_MAX),
        )

    hyperposition = {
        "recent_packet_count": len(recent),
        "unresolved_variables_observed": len(branch_counts),
        "branch_count_max": max(branch_counts) if branch_counts else 0,
        "branch_count_mean": (sum(branch_counts) / len(branch_counts)) if branch_counts else 0.0,
        "evidence_status": "OBSERVED" if branch_counts else "NO_BRANCH_TELEMETRY",
    }

    regulators: dict[str, Mapping[str, Any]] = {}
    for name in regulator_names:
        row = fabric.get_regulator(name)
        if row is not None:
            regulators[name] = dict(row)

    work = {
        "tasks_total": total_tasks,
        "tasks_unfinished": unfinished,
        "healthy_nodes": healthy_nodes,
        "nodes_total": total_nodes,
        "valid_leases": len(valid_leases),
        "stale_valid_leases_proxy": stale_valid_leases,
    }

    return FabricTelemetry(
        state_epoch=int(snap.epoch),
        generation=int(snap.generation),
        variables=variables,
        regulators=regulators,
        hyperposition=hyperposition,
        work=work,
        source_event_refs=tuple(sorted(set(refs))),
    )
