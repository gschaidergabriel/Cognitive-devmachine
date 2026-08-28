#!/usr/bin/env python3
"""Latched CognitiveControlPlane consumers for the live GRID10 model burst.

This module closes a bounded Triggerword-4 source gap without replacing the existing
GRID10 cognitive cycle. One immutable ControlSnapshot is passed in by the cycle boundary
and mechanically changes specialist execution:

* COMPUTE_OFF: inference is not called; a NOT_COMPUTED marker enters fan-in.
* OUTPUT_OFF: inference may run, but its candidate payload is redacted before GWT fan-in.
* MEMORY_OFF: inference/output may affect the current burst, but the cell is excluded from
  normal memory re-entry eligibility returned by this module.
* gain: changes the per-cell inference token budget while gain==0 remains distinct from
  COMPUTE_OFF and can still execute a bounded diagnostic call.

The latched snapshot digest/epoch are returned with the result so an enclosing persistent
Pulse/Agency runtime can bind the exact revision into its cycle checkpoint. This module
never grants effect authority and does not promote model output to canonical state.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
import hashlib
from typing import Any, Callable, Mapping, Sequence

from frankenstein2_cognitive_control_plane_v1 import ControlMode, ControlSnapshot
from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_glm_cognitive_cycle_v1 import (
    CELL_SCHEMA,
    WORKSPACE_ROLE,
    WORKSPACE_SCHEMA,
    CellResult,
    CognitiveCycleConfig,
    CognitiveCycleResult,
    CognitiveWorkspaceSnapshot,
    _canon,
    _cell_prompt,
    _cell_result_from_inference,
    _clean_seq,
    _effective_action,
    _error_result,
    _json_object,
    _read_sampling,
    _system_contract,
    _workspace_prompt,
    active_specialists,
)
from grid10_glm_inference_provider_v1 import GLMInferenceConfig, GLMInferenceResult

SCHEMA = "GRID10_LIVE_CONTROL_BINDING/v1"

# Explicit role-to-control binding. Micro-Lab remains a separate admission organ and is
# intentionally not impersonated by one of these model specialists.
ROLE_CONTROL_STEM: Mapping[str, str] = {
    "state": "grid.orientation",
    "memory": "grid.retrieval",
    "goal": "grid.goal",
    "critic": "grid.critic",
    "planner": "grid.planning",
    "simulator": "grid.world",
    "skeptic": "grid.hypothesis",
    "epistemic": "grid.epistemic",
    "action": "grid.delegation",
}


@dataclass(frozen=True)
class CellControlPlan:
    cell_id: int
    role: str
    control_stem: str
    mode: str
    gain: float
    max_tokens: int
    compute: bool
    expose_output: bool
    memory_reentry_eligible: bool


@dataclass(frozen=True)
class ControlledCognitiveCycleResult:
    schema: str
    control_epoch: int
    control_snapshot_digest: str
    cycle: CognitiveCycleResult
    cell_plans: tuple[CellControlPlan, ...]
    memory_reentry_eligible_cell_ids: tuple[int, ...]


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bounded_tokens(base_tokens: int, gain: float) -> int:
    """Turn gain into real bounded compute while keeping gain=0 != COMPUTE_OFF."""
    if gain < 0.0:
        raise ValueError("gain must be nonnegative")
    return max(32, min(1024, int(round(float(base_tokens) * float(gain)))))


def build_cell_plan(
    snapshot: ControlSnapshot,
    *,
    cell_id: int,
    role: str,
    base_tokens: int,
) -> CellControlPlan:
    try:
        stem = ROLE_CONTROL_STEM[role]
    except KeyError as exc:
        raise ValueError(f"UNBOUND_GRID_ROLE:{role}") from exc
    mode = snapshot.mode(stem + ".mode")
    gain = snapshot.float(stem + ".gain")
    compute = mode != ControlMode.COMPUTE_OFF
    expose_output = mode not in {ControlMode.COMPUTE_OFF, ControlMode.OUTPUT_OFF}
    memory_eligible = mode == ControlMode.ON
    return CellControlPlan(
        cell_id=int(cell_id),
        role=role,
        control_stem=stem,
        mode=mode.value,
        gain=float(gain),
        max_tokens=_bounded_tokens(base_tokens, gain),
        compute=compute,
        expose_output=expose_output,
        memory_reentry_eligible=memory_eligible,
    )


def _not_computed(tick_id: str, plan: CellControlPlan) -> CellResult:
    reason = f"CONTROL_COMPUTE_OFF:{plan.control_stem}"
    return CellResult(
        schema=CELL_SCHEMA,
        tick_id=tick_id,
        cell_id=plan.cell_id,
        role=plan.role,
        status="NOT_COMPUTED",
        candidate="",
        alternatives=(),
        evidence_needed=(reason,),
        confidence=None,
        unresolved=True,
        output_digest=_digest_text(reason),
        latency_ms=0.0,
        total_tokens=0,
        thinking=False,
        error=None,
    )


def _downstream_view(row: CellResult, plan: CellControlPlan) -> CellResult:
    if plan.mode != ControlMode.OUTPUT_OFF.value:
        return row
    # Keep execution evidence/digest but remove model payload before any GWT consumer.
    return replace(
        row,
        status="OUTPUT_OFF",
        candidate="",
        alternatives=(),
        evidence_needed=("CONTROL_OUTPUT_WITHHELD",),
        confidence=None,
        unresolved=True,
    )


def _workspace_semantic(
    *,
    tick_id: str,
    assurance_mode: AssuranceMode,
    controller_action: str,
    recommendation: str | None,
    synthesis: str,
    preserved: Sequence[str],
    disagreements: Sequence[str],
    evidence_requests: Sequence[str],
    active_cells: Sequence[int],
    cell_result_digests: Sequence[str],
    temperature: float,
    top_p: float,
    control_snapshot: ControlSnapshot,
) -> dict[str, Any]:
    return {
        "tick_id": tick_id,
        "assurance_mode": assurance_mode.value,
        "controller_action": controller_action,
        "model_recommended_action": recommendation,
        "effective_action": _effective_action(assurance_mode, controller_action, recommendation),
        "synthesis": synthesis,
        "preserved_alternatives": list(preserved),
        "disagreements": list(disagreements),
        "evidence_requests": list(evidence_requests),
        "active_cells": list(active_cells),
        "cell_result_digests": list(cell_result_digests),
        "temperature": temperature,
        "top_p": top_p,
        "control_epoch": int(control_snapshot.control_epoch),
        "control_snapshot_digest": control_snapshot.snapshot_digest,
    }


def run_control_bound_cognitive_cycle(
    *,
    tick_id: str,
    assurance_mode: AssuranceMode,
    controller_action: str,
    fabric: Any,
    context: Mapping[str, Any],
    control_snapshot: ControlSnapshot,
    config: CognitiveCycleConfig = CognitiveCycleConfig(),
    inference_fn: Callable[..., GLMInferenceResult] | None = None,
) -> ControlledCognitiveCycleResult:
    """Run one GRID/GWT burst against exactly one already-latched snapshot."""
    if not tick_id.strip():
        raise ValueError("tick_id required")
    if inference_fn is None:
        raise ValueError("EXPLICIT_ADMITTED_INFERENCE_FN_REQUIRED")
    context_json = _canon(context)
    if len(context_json) > config.max_context_chars:
        raise ValueError("context exceeds governed max_context_chars; compile a smaller context capsule")

    temperature, top_p = _read_sampling(fabric, assurance_mode)
    roles = active_specialists(assurance_mode)
    plans = tuple(
        build_cell_plan(
            control_snapshot,
            cell_id=role.cell_id,
            role=role.role,
            base_tokens=config.max_tokens_per_specialist,
        )
        for role in roles
    )
    plan_by_id = {p.cell_id: p for p in plans}

    def invoke(role: Any) -> CellResult:
        plan = plan_by_id[role.cell_id]
        if not plan.compute:
            return _not_computed(tick_id, plan)
        try:
            result = inference_fn(
                [
                    {"role": "system", "content": _system_contract()},
                    {
                        "role": "user",
                        "content": _cell_prompt(
                            role,
                            mode=assurance_mode,
                            controller_action=controller_action,
                            context={
                                **dict(context),
                                "latched_control": {
                                    "epoch": control_snapshot.control_epoch,
                                    "digest": control_snapshot.snapshot_digest,
                                    "stem": plan.control_stem,
                                    "mode": plan.mode,
                                    "gain": plan.gain,
                                },
                            },
                        ),
                    },
                ],
                config=GLMInferenceConfig(
                    max_tokens=plan.max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    thinking=bool(config.thinking_for_deep_roles and role.thinking),
                    timeout_seconds=config.timeout_seconds,
                ),
            )
            return _cell_result_from_inference(tick_id, role, result)
        except Exception as exc:
            return _error_result(tick_id, role, exc)

    rows: list[CellResult] = []
    if roles:
        with ThreadPoolExecutor(max_workers=min(config.max_parallel_specialists, len(roles))) as pool:
            futures = {pool.submit(invoke, role): role for role in roles}
            for future in as_completed(futures):
                rows.append(future.result())
    rows.sort(key=lambda x: x.cell_id)

    fanin_rows = [_downstream_view(row, plan_by_id[row.cell_id]) for row in rows]
    active_cell_ids = [
        row.cell_id for row in rows if plan_by_id[row.cell_id].compute
    ]

    workspace_error: str | None = None
    try:
        workspace_result = inference_fn(
            [
                {"role": "system", "content": _system_contract()},
                {
                    "role": "user",
                    "content": _workspace_prompt(
                        mode=assurance_mode,
                        controller_action=controller_action,
                        cells=fanin_rows,
                        max_chars_per_cell=config.max_fanin_chars_per_cell,
                    ) + (
                        "\nLATCHED_CONTROL_EPOCH=" + str(control_snapshot.control_epoch)
                        + "\nLATCHED_CONTROL_DIGEST=" + control_snapshot.snapshot_digest
                        + "\nCOUNTERHYPOTHESIS_PRESSURE="
                        + str(control_snapshot.float("grid.counterhypothesis_pressure"))
                    ),
                },
            ],
            config=GLMInferenceConfig(
                max_tokens=config.max_tokens_workspace,
                temperature=min(temperature, 0.5),
                top_p=top_p,
                thinking=config.thinking_for_deep_roles,
                timeout_seconds=max(
                    config.timeout_seconds,
                    90.0 if config.thinking_for_deep_roles else config.timeout_seconds,
                ),
            ),
        )
        workspace_obj = _json_object(workspace_result.content) or {}
        workspace_tokens = int(workspace_result.receipt.total_tokens or 0)
        workspace_digest_source = workspace_result.receipt.response_digest
        workspace_latency_ms = float(workspace_result.receipt.latency_ms)
    except Exception as exc:
        workspace_obj = {}
        workspace_tokens = 0
        workspace_error = f"{type(exc).__name__}:{exc}"[:500]
        workspace_digest_source = _digest_text(workspace_error)
        workspace_latency_ms = 0.0

    synthesis = str(
        workspace_obj.get("synthesis")
        or ("workspace_error:" + workspace_error if workspace_error else "")
    ).strip()[:2000]
    preserved = _clean_seq(workspace_obj.get("preserved_alternatives"), limit=8, chars=700)
    disagreements = _clean_seq(workspace_obj.get("disagreements"), limit=8, chars=700)
    evidence_requests = _clean_seq(workspace_obj.get("evidence_requests"), limit=8, chars=700)
    allowed_actions = {"HOLD", "OBSERVE", "SEARCH", "SIMULATE", "ASK", "WAIT", "ACT_CANDIDATE"}
    rec_raw = workspace_obj.get("recommended_action")
    recommendation = str(rec_raw).strip() if rec_raw is not None else None
    if recommendation not in allowed_actions:
        recommendation = None

    semantic = _workspace_semantic(
        tick_id=tick_id,
        assurance_mode=assurance_mode,
        controller_action=controller_action,
        recommendation=recommendation,
        synthesis=synthesis,
        preserved=preserved,
        disagreements=disagreements,
        evidence_requests=evidence_requests,
        active_cells=active_cell_ids + [WORKSPACE_ROLE.cell_id],
        cell_result_digests=[c.output_digest for c in rows] + [workspace_digest_source],
        temperature=temperature,
        top_p=top_p,
        control_snapshot=control_snapshot,
    )
    workspace = CognitiveWorkspaceSnapshot(
        schema=WORKSPACE_SCHEMA,
        tick_id=tick_id,
        assurance_mode=assurance_mode.value,
        controller_action=controller_action,
        model_recommended_action=recommendation,
        effective_action=semantic["effective_action"],
        synthesis=synthesis,
        preserved_alternatives=tuple(preserved),
        disagreements=tuple(disagreements),
        evidence_requests=tuple(evidence_requests),
        active_cells=tuple(semantic["active_cells"]),
        cell_result_digests=tuple(semantic["cell_result_digests"]),
        temperature=temperature,
        top_p=top_p,
        specialist_wall_ms=0.0,
        workspace_latency_ms=workspace_latency_ms,
        total_wall_ms=0.0,
        provider_tokens=sum(c.total_tokens for c in rows) + workspace_tokens,
        workspace_digest=hashlib.sha256(_canon(semantic).encode("utf-8")).hexdigest(),
    )
    cycle = CognitiveCycleResult(workspace=workspace, cells=tuple(fanin_rows))
    memory_eligible = tuple(
        p.cell_id for p in plans if p.compute and p.expose_output and p.memory_reentry_eligible
    )
    return ControlledCognitiveCycleResult(
        schema=SCHEMA,
        control_epoch=int(control_snapshot.control_epoch),
        control_snapshot_digest=control_snapshot.snapshot_digest,
        cycle=cycle,
        cell_plans=plans,
        memory_reentry_eligible_cell_ids=memory_eligible,
    )


def sanitized_control_receipt(result: ControlledCognitiveCycleResult) -> dict[str, Any]:
    """Text-free evidence surface for LC-6/7/8/14 component checks."""
    return {
        "schema": SCHEMA,
        "control_epoch": result.control_epoch,
        "control_snapshot_digest": result.control_snapshot_digest,
        "workspace_digest": result.cycle.workspace.workspace_digest,
        "active_cells": list(result.cycle.workspace.active_cells),
        "memory_reentry_eligible_cell_ids": list(result.memory_reentry_eligible_cell_ids),
        "cell_plans": [
            {
                "cell_id": p.cell_id,
                "role": p.role,
                "control_stem": p.control_stem,
                "mode": p.mode,
                "gain": p.gain,
                "max_tokens": p.max_tokens,
                "compute": p.compute,
                "expose_output": p.expose_output,
                "memory_reentry_eligible": p.memory_reentry_eligible,
            }
            for p in result.cell_plans
        ],
        "cell_execution": [
            {
                "cell_id": c.cell_id,
                "status": c.status,
                "output_digest": c.output_digest,
                "total_tokens": c.total_tokens,
                "error": c.error,
            }
            for c in result.cycle.cells
        ],
        "model_text_persisted": False,
        "canonical_truth_minted": False,
        "external_effect_executed": False,
    }
