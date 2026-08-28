#!/usr/bin/env python3
"""Xeno v1 active-build + recursive-improvement GO fabric.

This specialization layer redirects the existing 6000-logical-worker EntityOS/HCU
FREE fabric from architecture prose toward shippable Xeno patches, tests, benchmarks,
~0.8B specialization, the two-slot core/prestage harness, dashboard, peer/GRID10,
Global J-Space causal engineering, ClayCode migration, and measured recursive gains.

Economic execution authority is inherited exclusively through the current route/
credential-gated v3 fabric. Worker cognition receives a separately synthesized live
authority envelope from Supervisor Inbox -> exact steering -> typed provider admission,
so stale worker-directive prose cannot override a newer supervisor epoch. Xeno remains
an implementation codename inside EntityOS/HCU.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import run_6000_free_swarm_v3 as economic
import xeno_current_authority_protocol as live_authority

fabric = economic.fabric

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
BUILD_DIRECTIVE = ROOT / "research_entity/claycode/XENO_V1_ACTIVE_BUILD_AND_RECURSIVE_IMPROVEMENT_DIRECTIVE_2026-08-24.md"
BUILD_STATE = ROOT / "research_entity/claycode/XENO_ACTIVE_BUILD_STATE.json"
HARNESS_CONTRACT = ROOT / "the artefact/Xeno/XENO_HARNESS_V1_ACCEPTANCE_CONTRACT.md"
V1_ACCEPTANCE = ARTIFACT_ROOT / "xeno/XENO_V1_ACCEPTED.json"

XENO_ROLES = [
    ("XENO_INTEGRATOR", "Build the closest-to-shipping end-to-end Xeno slice: Typed Entry -> state/route -> selected CORE -> structured result -> receipt/effect boundary. Return an actual patch and tests."),
    ("XENO_08B_ENGINE", "Advance exact local ~0.8B checkpoint/tokenizer/loader/runtime integration, baseline eval, fine-tune integration seam, quantization and reproducible identity. The internal core must remain independently switchable."),
    ("XENO_ENGINE_FABRIC", "Implement arbitrary-LLM attachment and engine switching through capability-driven adapters. Prove internal-08B OFF + external CORE and hot core swaps without canonical-state reset."),
    ("XENO_TWO_SLOT_PRESTAGE", "Implement the max-two external slot harness, opaque secret_refs, CORE/PRESTAGE assignment, PRESTAGE ON/OFF, role swap and fail-closed capability/error handling."),
    ("XENO_DASHBOARD", "Implement the self-hosted dashboard controls for internal 0.8B, slot1/slot2, CORE, PRESTAGE, prestage toggle, engine health, GRID10, peer links and J-Space status. Never persist/display plaintext secrets."),
    ("XENO_PEER_GRID10", "Implement robust XENO_PEER_LINK/v1 plus exact ten-logical-cell GRID10 composition, reconnect/replay/stale-packet tests and shared-engine scheduling without confusing logical cells with model copies."),
    ("XENO_JSPACE_GWT", "Improve the concrete Global J-Space/GWT subsystem: vector-control ABI, causal traces, lesion/sham/off-target/rescue controls, role re-entry, model-switch behavior and cross-Xeno projection without false shared-latent claims."),
    ("XENO_DATASET_COMPILER", "Turn admitted prototype traces into deterministic family-split train/validation/holdout JSONL with hard negatives, leakage checks and hash-bound sidecars. Produce code/tests, not a dataset essay."),
    ("XENO_TRAIN_EVAL", "Advance frozen pretrain baseline, fine-tune job interface/readiness, post-train evaluation and ablations. Obey newest monetary/provider authority and never invent a paid authorization."),
    ("XENO_STATE_EFFECT", "Implement canonical state/recovery/effect-boundary behavior required by Xeno, including engine/prestage/peer failures. Model/J-Space output remains non-authoritative."),
    ("XENO_CLAYCODE_MIGRATION", "Convert one host-language Xeno slice toward ClayCode only when XENO_PROMOTION_GATE/v2 proves meaningful ClayCode progress, cross-group progress and zero protected regression from bound executable metrics."),
    ("XENO_PERF_LATENCY", "Implement a bottleneck repair that increases useful performance/capability while lowering p50 latency and preserving/improving p95, RSS, recovery, authority, harness, GRID10, peer and J-Space metrics."),
    ("XENO_CAPABILITY", "Implement or harden one end-user/runtime capability with frozen positive/negative/recovery benchmarks and no authority expansion."),
    ("XENO_FALSIFIER", "Attack the closest-to-shipping Xeno slice. Produce a failing regression/failure schedule and minimal repair when possible; target hidden regressions across the entire protected metric vector."),
    ("XENO_RECURSIVE_IMPROVER", "On every go, after current build blockers are handled, search for the next measurable non-regressing Xeno improvement. After v1 this becomes the continuing primary loop until owner supersession."),
]

XENO_SHARDS = [
    "v1 executable end-to-end slice", "Qwen3.5-0.8B exact model identity and loader",
    "internal 0.8B ON/OFF without state reset", "arbitrary external LLM CORE adapter",
    "slot1/slot2 persistent secret-ref configuration", "CORE/PRESTAGE role selection and swap",
    "PRESTAGE ON/OFF bypass equivalence", "dashboard harness controls and secret hygiene",
    "XENO_PEER_LINK/v1 handshake and replay safety", "GRID10 exact ten logical-cell scheduler",
    "GRID10 partial-cell/peer failure recovery", "JSPACE_VECTOR_CONTROL_ABI/v1 codec",
    "Global J-Space causal lesion/sham/off-target/rescue", "GWT competition/broadcast calibration",
    "J-Space external-core compiled projection", "J-Space cross-Xeno projection without latent-coordinate conflation",
    "dataset compiler and family split", "hard-negative generation", "fine-tune integration seam and authority gate",
    "post-train frozen eval and ablations", "Typed Entry routing", "UnifiedDB/recovery receipt binding",
    "EffectGate boundary", "ClayCode migration candidate", "p50/p95 latency reduction",
    "throughput and token-efficiency gain", "RSS/quantization optimization", "capability expansion without regression",
    "recursive full-vector promotion gate", "shipping/package/startup acceptance",
]

_BASE_PREV = fabric._PREV_PROMPT


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _require_free_lane_binding() -> None:
    if fabric.base.request_chat is not economic.gated_request_chat:
        raise RuntimeError("XENO_FREE_LANE_REQUEST_GATE_DRIFT")
    if fabric.FastProviderRuntime.next_key_model is not economic.gated_next_key_model:
        raise RuntimeError("XENO_FREE_LANE_RESERVATION_GATE_DRIFT")


def current_phase() -> dict[str, Any]:
    marker = _read_json(V1_ACCEPTANCE)
    if marker and marker.get("schema") == "XENO_V1_ACCEPTANCE/v1" and marker.get("status") == "PASS":
        required = ("metrics_receipt_sha256", "model_identity_sha256", "integration_receipt_sha256")
        if all(isinstance(marker.get(k), str) and len(marker[k]) == 64 for k in required):
            return {"phase": "INFINITE_RECURSIVE_IMPROVEMENT", "v1_acceptance": "BOUND_MARKER_PRESENT", "accepted_version": marker.get("accepted_version", "xeno-v1")}
    return {"phase": "XENO_V1_ACTIVE_BUILD", "v1_acceptance": "NOT_BOUND_ACCEPTED"}


def xeno_worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    original = _BASE_PREV(protocol, role, task, state_context, serial)
    phase = current_phase()
    return original + f"""

XENO ACTIVE BUILD / RECURSIVE IMPROVEMENT CONTRACT — OWNER PRIORITY
phase={phase['phase']}
v1_acceptance={phase['v1_acceptance']}
- Xeno is the implementation codename inside EntityOS/HCU, not a second truth/product authority.
- Every owner `go` executes this improvement objective until a newer explicit owner instruction supersedes it. Xeno v1 is a baseline, not a terminal product state.
- Before v1: converge on a finished runnable Xeno with specialized ~0.8B core, switchable engine fabric, two-slot CORE/PRESTAGE harness, dashboard, Xeno peer-link, GRID10, Global J-Space/GWT, dataset/training integration and acceptance evidence.
- After v1: continue measure -> patch -> test -> benchmark -> full-vector compare -> promote/reject across subsequent go cycles until superseded.
- Every external FREE call must retain the current credential+route economic gate and FREE_LANE_EXECUTION_RECEIPT/v1. Provider-level FREE labels, key presence, model consensus or HTTP success cannot bypass that gate. Paid fallback stays zero.
- The internal ~0.8B engine must be independently switchable OFF; admitted external/local LLM profiles may be CORE without resetting canonical state.
- Persist at most two external credential slots via opaque secret_ref only. Dashboard chooses CORE, optional distinct PRESTAGE, and PRESTAGE ON/OFF. Plaintext credentials never enter prompts, receipts, telemetry, source or ordinary profile state.
- GRID10 means exactly ten logical cells at v1, not ten model copies. XENO_PEER_LINK/v1 must tolerate stale/duplicate/delayed packets, disconnect/reconnect and peer restart under deterministic admission/recovery fences.
- Global J-Space is a permanent first-class research+engineering target. A candidate may leave its causal metric stable, but may not materially regress it; causal promotion still requires model-specific matched controls. Closed APIs never receive fake latent-access claims.
- Actual paid/provider training may execute only if newest authority explicitly admits that exact lane. Otherwise advance zero-cost prerequisites and fail closed at the monetary boundary.
- Token volume, worker count, architecture elegance or consensus are not progress unless converted into executable tested deltas.
- If you can write the patch, emit the unified diff. If not, set ready_for_forge=false and identify exact missing evidence instead of padding.

MANDATORY XENO DELTA CONTENT
- xeno_gate: one of V1_RUNTIME, V1_08B_ENGINE, V1_ENGINE_SWAP, V1_TWO_SLOT_HARNESS, V1_PRESTAGE, V1_DASHBOARD, V1_PEER_LINK, V1_GRID10, V1_JSPACE_GWT, V1_DATASET, V1_TRAINING, V1_INTEGRATION, V1_RECOVERY_EFFECT_AUTHORITY, V1_ACCEPTANCE_METRICS, RECURSIVE_IMPROVEMENT, CLAYCODE_MIGRATION.
- before_after_metrics must bind executable benchmark/receipt evidence for the frozen protected metric vector; model self-report is not sufficient measurement.
- target_files + NONEMPTY patch_unified_diff + test_commands + falsifier + before_after_metrics are mandatory for ready_for_forge=true.
- A ClayCode migration MUST run tools/xeno_build_gate.py --claycode-migration and satisfy XENO_PROMOTION_GATE/v2: meaningful ClayCode gain, independent cross-group progress, and no protected regression.
- End with the existing ARCHITECTURE_DELTA_JSON line so Evidence Forge can test the patch. Add xeno_gate, claycode_migration, before_after_metrics and acceptance_effect when relevant.
"""


def configure() -> None:
    _require_free_lane_binding()
    if not BUILD_DIRECTIVE.exists() or not BUILD_STATE.exists() or not HARNESS_CONTRACT.exists():
        raise RuntimeError("XENO_ACTIVE_BUILD_CONTROL_FILES_MISSING")
    protocol = live_authority.build_protocol(ROOT)
    if not protocol.startswith(fabric.base.PROTOCOL_BEGIN):
        raise RuntimeError("XENO_LIVE_PROTOCOL_ABI_BEGIN_MISMATCH")
    if live_authority.LIVE_MARKER not in protocol:
        raise RuntimeError("XENO_LIVE_PROTOCOL_MARKER_MISSING")
    fabric.base.load_protocol = lambda: protocol
    fabric.base.DEFAULT_ROLES = list(XENO_ROLES)
    fabric.FALLBACK_SHARDS = list(XENO_SHARDS)
    fabric._PREV_PROMPT = xeno_worker_prompt
    os.environ["CLAY_XENO_BUILD_MODE"] = "ACTIVE_INFINITE_RECURSIVE"
    os.environ["CLAY_XENO_LIVE_PROTOCOL_SHA256"] = hashlib.sha256(protocol.encode("utf-8")).hexdigest()


async def main() -> int:
    configure()
    args = economic.parse_args()
    return await economic.run(args)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
