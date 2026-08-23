from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from .entry_fabric_v1 import EntryAdmissionError, ResourceBudget, admit_payload
    from .grid10_runtime_v1 import Grid10Scheduler
except ImportError:  # direct path execution
    from entry_fabric_v1 import EntryAdmissionError, ResourceBudget, admit_payload
    from grid10_runtime_v1 import Grid10Scheduler


def _parse_budget(raw: Any) -> ResourceBudget:
    if raw is None:
        return ResourceBudget()
    if not isinstance(raw, dict):
        raise EntryAdmissionError("resource_budget must be an object")
    return ResourceBudget(
        max_cells=raw.get("max_cells", 10),
        max_tokens=raw.get("max_tokens", 4096),
        max_wall_ms=raw.get("max_wall_ms", 30000),
    )


def run_request(request: dict[str, Any], *, current_generation: int, physical_workers: int) -> dict[str, Any]:
    required = {
        "payload",
        "causal_id",
        "generation",
        "source",
        "provenance",
        "modality",
        "observed_at",
        "received_at",
        "permissions",
    }
    missing = sorted(required - request.keys())
    if missing:
        raise EntryAdmissionError(f"missing required fields: {','.join(missing)}")

    packet = admit_payload(
        payload=request["payload"],
        causal_id=request["causal_id"],
        generation=request["generation"],
        source=request["source"],
        provenance=request["provenance"],
        modality=request["modality"],
        observed_at=request["observed_at"],
        received_at=request["received_at"],
        permissions=tuple(request["permissions"]),
        capability_scope=tuple(request.get("capability_scope", ())),
        resource_budget=_parse_budget(request.get("resource_budget")),
        parent_or_stream_id=request.get("parent_or_stream_id"),
        payload_ref=request.get("payload_ref"),
    )
    decision = Grid10Scheduler(
        current_generation=current_generation,
        physical_worker_budget=physical_workers,
    ).route(packet)
    return {
        "schema_id": "XENO_ENTRY_GRID10_RESULT/v1",
        "ingress_id": packet.ingress_id,
        "event_sha256": packet.event_sha256,
        "causal_id": packet.causal_id,
        "generation": packet.generation,
        "mode": decision.mode,
        "route_decision_sha256": decision.decision_sha256,
        "logical_cell_count": len(decision.selected_cells),
        "physical_worker_budget": decision.physical_worker_budget,
        "selected_cells": list(decision.selected_cells),
        "selected_functions": list(decision.selected_functions),
        "reason_code": decision.reason_code,
        "effect_authority": "NONE_CANDIDATE_ONLY",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Xeno typed Entry Fabric -> GRID10 deterministic route")
    parser.add_argument("--generation", required=True, type=int, help="current canonical entity generation")
    parser.add_argument("--physical-workers", type=int, default=1, help="physical worker ceiling; separate from logical cells")
    args = parser.parse_args(argv)

    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise EntryAdmissionError("stdin request must be a JSON object")
        result = run_request(
            request,
            current_generation=args.generation,
            physical_workers=args.physical_workers,
        )
    except (EntryAdmissionError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps({"ok": True, "result": result}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
