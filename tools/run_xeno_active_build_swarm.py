#!/usr/bin/env python3
"""Xeno v1 active-build + recursive-improvement GO fabric.

This is a specialization layer over the existing 6000-logical-worker EntityOS/HCU
FREE swarm. It does not create a second product identity: Xeno is the implementation
codename for the first shippable EntityOS/HCU module. The layer redirects worker
attention from architecture prose to patches, tests, benchmarks, 0.8B integration,
training-data/evaluation readiness, ClayCode migration, and measured recursive gains.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import run_6000_free_swarm as fabric

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
BUILD_DIRECTIVE = ROOT / "research_entity/claycode/XENO_V1_ACTIVE_BUILD_AND_RECURSIVE_IMPROVEMENT_DIRECTIVE_2026-08-24.md"
BUILD_STATE = ROOT / "research_entity/claycode/XENO_ACTIVE_BUILD_STATE.json"
V1_ACCEPTANCE = ARTIFACT_ROOT / "xeno/XENO_V1_ACCEPTED.json"

XENO_ROLES = [
    ("XENO_INTEGRATOR", "Build the smallest end-to-end Xeno v1 slice that runs: Typed Entry -> state/route -> ~0.8B engine -> structured result -> receipt/effect boundary. Return an actual patch and tests."),
    ("XENO_08B_ENGINE", "Advance exact local ~0.8B base/checkpoint/tokenizer/loader/runtime integration, baseline eval, fine-tune integration seam, quantization and reproducible model identity. Prefer executable code over prose."),
    ("XENO_JSPACE_GWT", "Implement or test the concrete Global J-Space/GWT control path used by Xeno's ~0.8B core: vector-control ABI, causal traces, lesion/sham/off-target controls and receipt binding."),
    ("XENO_DATASET_COMPILER", "Turn admitted prototype traces into deterministic family-split train/validation/holdout JSONL with hard negatives and hash-bound sidecars. Produce code/tests, not a dataset essay."),
    ("XENO_TRAIN_EVAL", "Advance pretrain baseline, fine-tune job interface/readiness, post-train frozen evaluation, ablations and promotion criteria. Current monetary/provider authority must be obeyed; never invent a paid authorization."),
    ("XENO_TYPED_ENTRY", "Implement one missing Typed Entry -> HCU/Xeno route invariant or failure fence with exact causal identity and deterministic tests."),
    ("XENO_STATE_EFFECT", "Implement one canonical state/recovery/effect-boundary delta required for a finished Xeno; model output remains non-authoritative. Include failure-path tests."),
    ("XENO_CLAYCODE_MIGRATION", "Convert one currently host-language Xeno module/semantic slice toward ClayCode only when the same candidate can be benchmarked against the old path on the full protected metric vector."),
    ("XENO_PERF_LATENCY", "Find and implement one bottleneck repair that raises useful work/capability while reducing end-to-end p50 latency; preserve p95, RSS, reliability, authority and ClayCode progress."),
    ("XENO_CAPABILITY", "Implement or harden one Xeno capability with a frozen positive/negative benchmark and no authority expansion."),
    ("XENO_FALSIFIER", "Attack the current closest-to-shipping Xeno slice; produce a regression test that fails the current behavior and a minimal repair when possible."),
    ("XENO_RECURSIVE_IMPROVER", "When Xeno v1 is accepted, propose the next strict-dominance implementation delta: better capabilities/quality, lower latency, better throughput/efficiency, no protected regression, and more ClayCode."),
]

XENO_SHARDS = [
    "v1 executable end-to-end slice",
    "Qwen3.5-0.8B exact model identity and loader",
    "0.8B baseline benchmark freeze",
    "JSPACE_VECTOR_CONTROL_ABI/v1 codec",
    "GWT competition/broadcast implementation",
    "causal trace instrumentation",
    "dataset compiler and family split",
    "hard-negative generation",
    "fine-tune integration seam and authority gate",
    "post-train frozen eval and ablations",
    "Typed Entry routing",
    "UnifiedDB/recovery receipt binding",
    "EffectGate boundary",
    "ClayCode migration candidate",
    "p50/p95 latency reduction",
    "throughput and token-efficiency gain",
    "RSS/quantization optimization",
    "capability expansion without regression",
    "recursive promotion gate",
    "shipping/package/startup acceptance",
]

_BASE_PREV = fabric._PREV_PROMPT


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def current_phase() -> dict[str, Any]:
    marker = _read_json(V1_ACCEPTANCE)
    if marker and marker.get("schema") == "XENO_V1_ACCEPTANCE/v1" and marker.get("status") == "PASS":
        required = ("metrics_receipt_sha256", "model_identity_sha256", "integration_receipt_sha256")
        if all(isinstance(marker.get(k), str) and len(marker[k]) == 64 for k in required):
            return {
                "phase": "RECURSIVE_IMPROVEMENT",
                "v1_acceptance": "BOUND_MARKER_PRESENT",
                "accepted_version": marker.get("accepted_version", "xeno-v1"),
            }
    return {"phase": "XENO_V1_ACTIVE_BUILD", "v1_acceptance": "NOT_BOUND_ACCEPTED"}


def xeno_worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    original = _BASE_PREV(protocol, role, task, state_context, serial)
    phase = current_phase()
    return original + f"""

XENO ACTIVE BUILD CONTRACT — OWNER PRIORITY
phase={phase['phase']}
v1_acceptance={phase['v1_acceptance']}
- Xeno is the implementation codename inside EntityOS/HCU, not a second truth/product authority.
- The primary objective is a finished, runnable Xeno with an integrated fine-tuned ~0.8B cognitive core, not more architecture prose.
- Until Xeno v1 acceptance, spend the dominant effort on source patches, tests, benchmark harnesses, model integration, trace/dataset compiler, training/eval readiness and packaging.
- Actual paid/provider training may execute only if the newest current authority explicitly admits that exact lane. Otherwise advance every zero-cost prerequisite and fail closed at the monetary boundary.
- After Xeno v1 acceptance, continue recursive improvement indefinitely until a newer owner instruction supersedes this contract.
- Every recursive candidate must improve capability_pass_rate, task_quality_score, p50_latency_ms, throughput_tokens_s and claycode_fraction while regressing NONE of the protected metrics.
- Every ClayCode migration candidate is stricter: it must show strict directional improvement on the ENTIRE frozen metric vector accepted by tools/xeno_build_gate.py; otherwise reject/rework/revert it.
- Token volume, worker count, architecture elegance or model consensus are not progress unless converted into an executable/tested delta.
- If you can write the patch, write the unified diff. If you cannot, set ready_for_forge=false and identify the exact missing evidence. Do not pad with design prose.
- Prefer modifying the currently closest-to-shipping code path over introducing parallel frameworks.

MANDATORY XENO DELTA CONTENT
- xeno_gate: one of V1_RUNTIME, V1_08B_ENGINE, V1_JSPACE_GWT, V1_DATASET, V1_TRAINING, V1_INTEGRATION, V1_ACCEPTANCE, RECURSIVE_IMPROVEMENT, CLAYCODE_MIGRATION.
- before_after_metrics: name the exact benchmark/receipt that will provide before+after values for capability, quality, p50/p95 latency, throughput, RSS, recovery, authority-boundary, token efficiency and ClayCode fraction.
- target_files + non-empty patch_unified_diff + test_commands are required for ready_for_forge=true.
- For a ClayCode migration, test_commands MUST include tools/xeno_build_gate.py with --claycode-migration against bound before/after metric snapshots.
- End with the existing ARCHITECTURE_DELTA_JSON line so Evidence Forge can test the patch. Add these extra JSON keys when relevant: xeno_gate, claycode_migration, before_after_metrics, acceptance_effect.
"""


def configure() -> None:
    if not BUILD_DIRECTIVE.exists() or not BUILD_STATE.exists():
        raise RuntimeError("XENO_ACTIVE_BUILD_CONTROL_FILES_MISSING")
    fabric.base.DEFAULT_ROLES = list(XENO_ROLES)
    fabric.FALLBACK_SHARDS = list(XENO_SHARDS)
    fabric._PREV_PROMPT = xeno_worker_prompt
    os.environ["CLAY_XENO_BUILD_MODE"] = "ACTIVE_RECURSIVE"


async def main() -> int:
    configure()
    args = fabric.parse_args()
    return await fabric.run(args)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
