#!/usr/bin/env python3
"""Lease-bound current-result view for EntityOS/HCU Xeno S1 compression.

This is a narrow, noncanonical projection over the single persisted S1/result store.
It deliberately does not create another database or truth authority. The underlying
SQLite adapter first proves that the supplied coordinator lease is currently admitted;
this view then exposes only NODE_RESULT rows bound to that same lease epoch+digest.

Why this exists: persisted result history is useful evidence, but historical rows must
never silently enter current-epoch compression/integration after S1 advances. A state
advance invalidates the lease used for any later write, while this filter prevents stale
rows from even becoming current compression candidates.
"""
from __future__ import annotations

from typing import Any

from xeno_shared_state_boot_v1 import CoordinatorLease
from xeno_s1_sqlite_cas_v1 import list_ingested_results

CURRENT_RESULT_VIEW_SCHEMA = "ENTITYOS_HCU_S1_CURRENT_RESULT_VIEW/v1"


class CurrentResultViewError(ValueError):
    pass


def _validate_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise CurrentResultViewError("RESULT_ROW_MAPPING_REQUIRED")
    required = {
        "result_id",
        "schema",
        "node_id",
        "task_id",
        "state_epoch",
        "state_digest",
        "payload_ref",
        "payload_sha256",
        "ingested_by",
    }
    missing = required - set(row)
    if missing:
        raise CurrentResultViewError(
            f"RESULT_ROW_MISSING_FIELDS:{','.join(sorted(missing))}"
        )
    return row


def list_current_result_candidates(
    db: Any,
    lease: CoordinatorLease,
    *,
    coordinator_node_id: str,
    expected_authority_binding_sha256: str,
) -> list[dict[str, Any]]:
    """Return only persisted results causally bound to the current admitted lease.

    `list_ingested_results` is intentionally called first: it proves the lease is
    persisted, current, node-bound, scope-authorized and capability-authority-bound.
    Rows from older S1 epochs remain durable in the store but are excluded here.
    """
    if not isinstance(lease, CoordinatorLease):
        raise CurrentResultViewError("COORDINATOR_LEASE_REQUIRED")

    rows = list_ingested_results(
        db,
        lease,
        coordinator_node_id=coordinator_node_id,
        expected_authority_binding_sha256=expected_authority_binding_sha256,
    )

    selected: list[dict[str, Any]] = []
    for raw in rows:
        row = _validate_row(raw)
        if (
            row["state_epoch"] == lease.state_epoch
            and row["state_digest"] == lease.state_digest
        ):
            selected.append(dict(row))
    return selected
