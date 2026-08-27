#!/usr/bin/env python3
"""Weighted selector for exact `spawn` research trigger.

This tool performs only stochastic selection and emits a receipt payload. Research execution
remains governed by SPAWN_RESEARCH_PROTOCOL.md and the Research Center mesh protocols.
"""
from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHTS = ROOT / "research_entity" / "global" / "SPAWN_RESEARCH_WEIGHTS.json"


def load_weights(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    weights = cfg.get("weights_percent") or {}
    if not isinstance(weights, dict) or not weights:
        raise ValueError("weights_percent missing")
    cooked = {str(k): int(v) for k, v in weights.items()}
    if any(v <= 0 for v in cooked.values()):
        raise ValueError("all weights must be positive integers")
    if sum(cooked.values()) != 100:
        raise ValueError("spawn weights must sum to 100")
    if cooked.get("claycode", 0) <= max(v for k, v in cooked.items() if k != "claycode"):
        raise ValueError("claycode must be strictly more likely than any other branch")
    return {**cfg, "weights_percent": cooked}


def draw(cfg: dict) -> dict:
    rng = secrets.SystemRandom()
    ticket = rng.randrange(100)
    cursor = 0
    selected = None
    interval = None
    for branch, weight in cfg["weights_percent"].items():
        start = cursor
        cursor += weight
        if ticket < cursor:
            selected = branch
            interval = [start, cursor - 1]
            break
    if selected is None:
        raise RuntimeError("weight traversal failed")
    return {
        "schema_version": "1.0",
        "trigger": "spawn",
        "selected_origin_branch": selected,
        "ticket_0_99": ticket,
        "selected_interval": interval,
        "weights_percent": cfg["weights_percent"],
        "distribution_schema_version": cfg.get("schema_version"),
        "rng": "python.secrets.SystemRandom",
        "drawn_at": datetime.now(timezone.utc).isoformat(),
        "note": "Selection probability is routing only, never evidence weight or truth authority.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=str(DEFAULT_WEIGHTS))
    args = ap.parse_args()
    print(json.dumps(draw(load_weights(Path(args.weights))), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
