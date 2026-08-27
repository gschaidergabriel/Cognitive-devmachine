#!/usr/bin/env python3
"""Strict optional-window metrics for GateFlow v1.1.

All rates remain null until their numerator and denominator are explicitly
materialized in the conversion window. This avoids turning missing telemetry
into fabricated efficiency claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CAUSAL_STATUSES = {"OPEN", "SUPPORTED", "TERMINAL_ACCEPTED", "UNMEASURED"}


def safe_ratio(numerator: Any, denominator: Any) -> float | None:
    if numerator is None or denominator is None:
        return None
    n = float(numerator)
    d = float(denominator)
    if n < 0 or d < 0 or n > d:
        raise ValueError(f"invalid ratio counters: {n}/{d}")
    if d == 0:
        return None
    return n / d


def compile_window_metrics(window: dict[str, Any]) -> dict[str, Any]:
    counts = window.get("window_counts", {})
    chain = window.get("e2e_causal_chain", [])

    supported = 0
    terminal = 0
    measured = 0
    for item in chain:
        status = item.get("status")
        if status not in CAUSAL_STATUSES:
            raise ValueError(f"invalid causal-chain status: {status}")
        if status != "UNMEASURED":
            measured += 1
        if status in {"SUPPORTED", "TERMINAL_ACCEPTED"}:
            supported += 1
        if status == "TERMINAL_ACCEPTED":
            terminal += 1

    chain_total = len(chain)
    return {
        "stale_evidence_rate": safe_ratio(
            counts.get("stale_evidence_count"), counts.get("evidence_items_count")
        ),
        "duplicate_superseded_ratio": safe_ratio(
            counts.get("duplicate_superseded_count"), counts.get("work_items_count")
        ),
        "target_queue_yield": safe_ratio(
            counts.get("target_jobs_pass"), counts.get("target_jobs_completed")
        ),
        "e2e_causal_chain_supported_fraction": (
            supported / chain_total if chain_total else None
        ),
        "e2e_causal_chain_terminal_fraction": (
            terminal / chain_total if chain_total else None
        ),
        "e2e_causal_chain_measured_fraction": (
            measured / chain_total if chain_total else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("window", type=Path)
    args = parser.parse_args()
    window = json.loads(args.window.read_text())
    print(json.dumps(compile_window_metrics(window), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
