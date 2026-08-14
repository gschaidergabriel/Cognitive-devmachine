#!/usr/bin/env python3
"""Deterministic cancellation/error semantics for ClayCode BASE async host adapters.

No caller-provided callable is accepted. Operation identity is selected from a finite
runtime registry and must also be present in the capability policy minted by the host.
Publication is always by input index, independent of worker completion order.
"""
from __future__ import annotations

import concurrent.futures
from typing import Any

from claycode_base_runtime import CapabilityFault, ClayRuntime, ResourceFault

CONCURRENCY_EXT_VERSION = "claycode-base-concurrency-ext/0.1"


def _operation(name: str, value: Any) -> Any:
    if name == "identity": return value
    if name == "square": return value * value
    if name == "negate": return -value
    if name == "inverse100": return 100 // value
    raise CapabilityFault(f"ASYNC_OPERATION_UNKNOWN:{name}")


def _cancellable_map(policy: dict[str, Any], operation: str, values: list[Any], cancel_after: int | None = None, max_workers: int = 4) -> dict[str, Any]:
    allowed = set(policy.get("operations", []))
    if operation not in allowed:
        raise CapabilityFault(f"ASYNC_OPERATION_NOT_ALLOWED:{operation}")
    if not isinstance(values, list):
        raise ResourceFault("ASYNC_VALUES_NOT_LIST")
    if not isinstance(max_workers, int) or max_workers < 1 or max_workers > int(policy.get("max_workers", 64)):
        raise ResourceFault("ASYNC_BAD_WORKER_COUNT")
    max_items = int(policy.get("max_items", 100000))
    if len(values) > max_items:
        raise ResourceFault("ASYNC_ITEM_LIMIT")
    if cancel_after is None:
        prefix = len(values)
    else:
        if not isinstance(cancel_after, int) or cancel_after < 0 or cancel_after > len(values):
            raise ResourceFault("ASYNC_BAD_CANCEL_AFTER")
        prefix = cancel_after

    rows: list[dict[str, Any] | None] = [None] * len(values)
    # The committed prefix is truly executed concurrently. Cancellation is an explicit
    # state transition after that prefix; the suffix is never dispatched, so no side
    # effect can race after a cancellation receipt has been published.
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_operation, operation, values[i]): i for i in range(prefix)}
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            try:
                rows[i] = {"index": i, "status": "OK", "value": future.result()}
            except Exception as exc:
                rows[i] = {"index": i, "status": "ERROR", "error_type": type(exc).__name__}
    for i in range(prefix, len(values)):
        rows[i] = {"index": i, "status": "CANCELLED"}

    result = [row for row in rows if row is not None]
    return {
        "operation": operation,
        "submitted": prefix,
        "cancelled": len(values) - prefix,
        "errors": sum(1 for row in result if row["status"] == "ERROR"),
        "rows": result,
        "publication_order": "INPUT_INDEX",
        "post_cancel_dispatch": 0,
    }


def install(rt: ClayRuntime) -> ClayRuntime:
    rt.register_adapter("async.cancellable_map", "async.cancellable", _cancellable_map)
    return rt


__all__ = ["install", "CONCURRENCY_EXT_VERSION"]
