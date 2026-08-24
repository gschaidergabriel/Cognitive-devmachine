#!/usr/bin/env python3
"""One bounded Trigger-1 J-Space research lane.

The process reuses the current FREE_ONLY v3 request gate and shared provider quota
machinery. It deliberately disables provider catalog discovery/preflight for this
research path: only already-declared model routes may reach the exact per-route
FREE gate immediately before model network I/O.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

import run_6000_free_swarm_v3 as gated
import run_6000_free_swarm as fabric

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run one focused Trigger-1 J-Space FREE research lane")
    p.add_argument("--batch-id", required=True)
    p.add_argument("--lane-index", required=True, type=int)
    p.add_argument("--experiment-id", required=True)
    p.add_argument("--experiment-name", required=True)
    p.add_argument("--focus", required=True)
    p.add_argument("--minutes", type=float, default=12.0)
    p.add_argument("--logical-workers", type=int, default=64)
    p.add_argument("--max-tokens", type=int, default=1000)
    p.add_argument("--context-chars", type=int, default=14000)
    p.add_argument("--timeout", type=float, default=150.0)
    p.add_argument("--drain-seconds", type=float, default=180.0)
    p.add_argument("--output-dir", required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.lane_index < 0 or args.lane_index >= 10:
        raise SystemExit("lane-index must be 0..9")
    if not os.getenv("CLAY_FREE_PROVIDER_BUDGET_DB"):
        raise SystemExit("CLAY_FREE_PROVIDER_BUDGET_DB must bind all Trigger-1 lanes to one shared quota database")

    # Trigger-1 never performs provider model-catalog probing. Existing declared
    # model routes still pass through v3 current_lane_binding immediately before
    # network I/O, so UNKNOWN/PAID/unbound routes fail closed.
    fabric.opt.discover_and_export = lambda timeout: {
        "trigger1_catalog_policy": "NO_PROVIDER_CATALOG_PREFLIGHT",
        "timeout_argument_ignored": float(timeout),
    }

    previous_prompt = fabric.base.worker_prompt
    focus_digest = hashlib.sha256(args.focus.encode("utf-8")).hexdigest()

    def focused_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        base_text = previous_prompt(protocol, role, task, state_context, serial)
        return base_text + f"""

TRIGGER-1 GLOBAL J-SPACE STEERING LANE — MANDATORY
batch_id={args.batch_id}
lane_index={args.lane_index}
experiment_id={args.experiment_id}
experiment_name={args.experiment_name}
focus_sha256={focus_digest}
focus={args.focus}

PRIMARY GOAL
Reach direct reproducible vector-based control of an admitted FREE API model through the Global J-Space path as quickly as executable evidence permits.

MECHANISM TO PRESERVE
Global J-Space/control intent -> JSPACE_VECTOR_CONTROL_ABI/v1 -> model/version/layer-specific JSPACE_LATENT_BASIS_ADAPTER/v1 -> model-specific local control packet -> instrumentable runtime/native cvec or equivalent consumed intervention -> immutable receipts.

EVIDENCE RULES
- Hosted text prompting is NOT direct vector steering.
- Do not claim hidden-state/cvec control unless the runtime actually consumes the intervention and binds its identity.
- Prefer one executable patch/test/discriminator over prose.
- Preserve exact model/checkpoint/tokenizer/runtime/build/adapter/source-packet/local-packet/cvec identities where applicable.
- Calibration split may choose layer/gain; holdout must remain disjoint.
- Matched controls: BASELINE, +VECTOR, SIGN_FLIP, exact NULL_VECTOR, ORTHOGONAL_SAME_NORM, PERMUTED_SAME_NORM across fixed seeds.
- A positive claim requires reproducible directional holdout effect plus execution/native-hook receipt.
- If the provider exposes no instrumentable activation/cvec surface, prove that boundary and create the smallest executable bridge/alternative discriminator instead of pretending prompting is steering.
- Return a concrete delta or exact blocker suitable for the forge.
"""

    fabric.base.worker_prompt = focused_prompt

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    lane_manifest = {
        "schema": "CLAY_TRIGGER1_JSPACE_LANE/v1",
        "batch_id": args.batch_id,
        "lane_index": args.lane_index,
        "experiment_id": args.experiment_id,
        "experiment_name": args.experiment_name,
        "focus_sha256": focus_digest,
        "focus": args.focus,
        "free_only": True,
        "catalog_network_preflight": False,
        "together": "FORBIDDEN",
        "paid_or_unknown_cost": "FAIL_CLOSED",
        "shared_provider_budget_db": os.environ["CLAY_FREE_PROVIDER_BUDGET_DB"],
    }
    (out / "trigger1_lane_manifest.json").write_text(
        json.dumps(lane_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    fabric_args = argparse.Namespace(
        logical_workers=max(1, int(args.logical_workers)),
        hours=max(1.0 / 3600.0, float(args.minutes) / 60.0),
        max_tokens=max(64, int(args.max_tokens)),
        context_chars=max(3000, int(args.context_chars)),
        timeout=max(5.0, float(args.timeout)),
        drain_seconds=max(5.0, float(args.drain_seconds)),
        output_dir=str(out / "free_swarm"),
    )
    return int(asyncio.run(gated.run(fabric_args)))


if __name__ == "__main__":
    raise SystemExit(main())
