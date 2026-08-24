#!/usr/bin/env python3
"""One bounded Trigger-1 V2 convergence/repair slot.

External-provider research in this process still reuses the current FREE_ONLY v3
request gate and shared quota machinery. The primary completion path is independent
of provider availability and is attempted before these slots by the launcher.
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
    p = argparse.ArgumentParser(description="Run one focused Trigger-1 V2 zero-cost convergence slot")
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
        raise SystemExit("CLAY_FREE_PROVIDER_BUDGET_DB must bind all external Trigger-1 slots to one shared quota database")

    # No provider catalog probing is allowed in this research child. Existing
    # declared routes still pass the exact current FREE gate before network I/O.
    fabric.opt.discover_and_export = lambda timeout: {
        "trigger1_catalog_policy": "NO_PROVIDER_CATALOG_PREFLIGHT",
        "timeout_argument_ignored": float(timeout),
    }

    previous_prompt = fabric.base.worker_prompt
    focus_digest = hashlib.sha256(args.focus.encode("utf-8")).hexdigest()
    local_fastpath_state = os.getenv("CLAY_TRIGGER1_LOCAL_FASTPATH_STATE_JSON", "{}")

    def focused_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        base_text = previous_prompt(protocol, role, task, state_context, serial)
        return base_text + f"""

TRIGGER-1 V2 GLOBAL J-SPACE CONVERGENCE SLOT — MANDATORY
batch_id={args.batch_id}
lane_index={args.lane_index}
experiment_id={args.experiment_id}
experiment_name={args.experiment_name}
focus_sha256={focus_digest}
focus={args.focus}
local_fastpath_state={local_fastpath_state}

PRIMARY GOAL
Reach direct reproducible Global J-Space vector control on one exact zero-cost model runtime with a real API boundary as quickly and simply as possible. The goal is provider-independent: an exact loopback local API is a valid final runtime and is preferred when it removes hosted-provider blockers.

PRIMARY PATH ORDER
1. Local Qwen3-0.6B llama.cpp cvec API where executable.
2. Local Qwen3-0.6B PyTorch activation-hook API as the fast hidden-state fallback.
3. Exact FREE hosted output-logit control only as component evidence.
4. FREE external internal-vector API only if one is genuinely exposed.

BLOCKER LAW
- A blocker is not terminal while an authorized alternative path remains.
- Classify it as REPAIR_NOW, ROUTE_AROUND, EXTERNAL_TRANSIENT, SCIENTIFIC_NEGATIVE or HARD_AUTHORITY_BOUNDARY.
- REPAIR_NOW: implement/test the smallest fix now.
- ROUTE_AROUND: switch path now; do not wait.
- EXTERNAL_TRANSIENT: continue independent local work; provider recovery is optional parallel work.
- SCIENTIFIC_NEGATIVE: preserve it, then change vector/layer/gain/hypothesis without weakening the success gate.
- HARD_AUTHORITY_BOUNDARY: fail closed only for the forbidden action and continue all authorized local work.
- Provider credentials, entitlements, rate limits, route identity and hosted parameter support may not gate the local primary path.
- If this slot's named focus is already satisfied or blocked, reallocate to the highest-information remaining dependency instead of returning NO_CHANGE.

MECHANISM TO PRESERVE
Global J-Space/control intent -> JSPACE_VECTOR_CONTROL_ABI/v1 -> exact model-specific adapter/vector -> runtime-observed hidden-state/native-cvec intervention -> exact zero-cost API-served runtime -> immutable receipts.

EVIDENCE RULES
- Hosted text prompting is NOT direct vector steering.
- Do not claim hidden-state/cvec control unless the runtime actually consumes the intervention and binds its identity.
- Prefer one executable patch/test/discriminator over prose.
- Preserve exact model/checkpoint/tokenizer/runtime/build/adapter/source-packet/local-packet/applied-vector identities.
- Calibration may choose layer/gain; holdout must remain disjoint.
- Matched controls: BASELINE, +VECTOR, SIGN_FLIP, NULL_VECTOR, ORTHOGONAL_SAME_NORM, PERMUTED_SAME_NORM across fixed seeds.
- A positive claim requires reproducible directional holdout effect plus runtime intervention receipt and strongest counterexample.
- A loopback-only local API can satisfy the final API boundary when bound to the same exact runtime/model bytes.
- Hosted logit_bias is output-logit component evidence only, not hidden-state credit.
- Return a concrete executable delta or a blocker-eliminating next action suitable for the Forge.
"""

    fabric.base.worker_prompt = focused_prompt

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    lane_manifest = {
        "schema": "CLAY_TRIGGER1_JSPACE_LANE/v2",
        "batch_id": args.batch_id,
        "lane_index": args.lane_index,
        "experiment_id": args.experiment_id,
        "experiment_name": args.experiment_name,
        "focus_sha256": focus_digest,
        "focus": args.focus,
        "zero_cost_only": True,
        "slots_dynamically_reallocatable": True,
        "local_fastpath_state": local_fastpath_state,
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
