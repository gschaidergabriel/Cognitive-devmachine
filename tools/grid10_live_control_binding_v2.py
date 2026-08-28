#!/usr/bin/env python3
"""Live GRID10 control binding v2 with deterministic GWT ignition.

v2 is a narrow successor to ``grid10_live_control_binding_v1``. It reuses the v1 cell
planning/parsing contracts and adds the missing LC-14 consumer for
``grid.workspace_ignition_threshold``.

Specialist computation remains independent from broadcast ignition:

* COMPUTE_OFF prevents the specialist call.
* OUTPUT_OFF may compute but redacts payload before GWT and memory re-entry.
* MEMORY_OFF may compute/broadcast but is excluded from normal memory re-entry.
* gain still changes specialist token budget.
* GWT eligibility additionally requires ``gain >= grid.workspace_ignition_threshold``.
* if no visible specialist reaches the threshold, the workspace inference is NOT called.
* normal memory re-entry is restricted to specialists that actually crossed the same
  GWT ignition gate; sub-threshold private computation cannot be advertised as re-entry.

This is candidate cognition only. No canonical truth, effect, completion, provider admission,
or whole-runtime acceptance is created here.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
import hashlib
import time
from typing import Any, Callable, Mapping, Sequence

from frankenstein2_cognitive_control_plane_v1 import ControlSnapshot
from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_glm_cognitive_cycle_v1 import (
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
from grid10_live_control_binding_v1 import (
    CellControlPlan,
    ROLE_CONTROL_STEM,
    _downstream_view,
    _not_computed,
    build_cell_plan,
)

SCHEMA = "GRID10_LIVE_CONTROL_BINDING/v2"


@dataclass(frozen=True)
class ControlledCognitiveCycleResultV2:
    schema: str
    control_epoch: int
    control_snapshot_digest: str
    workspace_ignition_threshold: float
    workspace_ignited: bool
    gwt_eligible_cell_ids: tuple[int, ...]
    cycle: CognitiveCycleResult
    cell_plans: tuple[CellControlPlan, ...]
    memory_reentry_eligible_cell_ids: tuple[int, ...]


def _digest(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _ignition_view(row: CellResult, plan: CellControlPlan, threshold: float) -> CellResult:
    """Hide sub-threshold payload from the workspace while preserving execution evidence."""
    row = _downstream_view(row, plan)
    if not plan.compute or not plan.expose_output or row.error is not None:
        return row
    if plan.gain >= threshold:
        return row
    return replace(
        row,
        status="IGNITION_BELOW_THRESHOLD",
        candidate="",
        alternatives=(),
        evidence_needed=(
            f"CONTROL_GWT_BELOW_THRESHOLD:{plan.control_stem}:{plan.gain:.6f}<{threshold:.6f}",
        ),
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
    ignition_threshold: float,
    workspace_ignited: bool,
    gwt_eligible_cell_ids: Sequence[int],
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
        "workspace_ignition_threshold": float(ignition_threshold),
        "workspace_ignited": bool(workspace_ignited),
        "gwt_eligible_cell_ids": list(gwt_eligible_cell_ids),
    }


def run_control_bound_cognitive_cycle_v2(
    *,
    tick_id: str,
    assurance_mode: AssuranceMode,
    controller_action: str,
    fabric: Any,
    context: Mapping[str, Any],
    control_snapshot: ControlSnapshot,
    config: CognitiveCycleConfig = CognitiveCycleConfig(),
    inference_fn: Callable[..., GLMInferenceResult] | None = None,
) -> ControlledCognitiveCycleResultV2:
    """Run one specialist burst and ignite GWT only when the latched threshold is met."""
    if not tick_id.strip():
        raise ValueError("tick_id required")
    if inference_fn is None:
        raise ValueError("EXPLICIT_ADMITTED_INFERENCE_FN_REQUIRED")
    context_json = _canon(context)
    if len(context_json) > config.max_context_chars:
        raise ValueError("context exceeds governed max_context_chars; compile a smaller context capsule")

    temperature, top_p = _read_sampling(fabric, assurance_mode)
    ignition_threshold = control_snapshot.float("grid.workspace_ignition_threshold")
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
                                    "workspace_ignition_threshold": ignition_threshold,
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

    specialist_started = time.perf_counter()
    rows: list[CellResult] = []
    if roles:
        with ThreadPoolExecutor(max_workers=min(config.max_parallel_specialists, len(roles))) as pool:
            futures = {pool.submit(invoke, role): role for role in roles}
            for future in as_completed(futures):
                rows.append(future.result())
    rows.sort(key=lambda x: x.cell_id)
    specialist_wall_ms = (time.perf_counter() - specialist_started) * 1000.0

    fanin_rows = [_ignition_view(row, plan_by_id[row.cell_id], ignition_threshold) for row in rows]
    gwt_eligible = tuple(
        row.cell_id
        for row in rows
        if plan_by_id[row.cell_id].compute
        and plan_by_id[row.cell_id].expose_output
        and row.error is None
        and plan_by_id[row.cell_id].gain >= ignition_threshold
    )
    gwt_eligible_set = set(gwt_eligible)
    workspace_ignited = bool(gwt_eligible)

    workspace_tokens = 0
    workspace_latency_ms = 0.0
    recommendation: str | None = None
    synthesis = ""
    preserved: tuple[str, ...] = ()
    disagreements: tuple[str, ...] = ()
    evidence_requests: tuple[str, ...] = ()
    workspace_digest_source = _digest(
        {
            "tick_id": tick_id,
            "status": "GWT_NOT_IGNITED",
            "control_snapshot_digest": control_snapshot.snapshot_digest,
            "workspace_ignition_threshold": ignition_threshold,
        }
    )

    if workspace_ignited:
        workspace_started = time.perf_counter()
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
                            + "\nWORKSPACE_IGNITION_THRESHOLD=" + str(ignition_threshold)
                            + "\nGWT_ELIGIBLE_CELL_IDS=" + _canon(list(gwt_eligible))
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
            workspace_error = f"{type(exc).__name__}:{exc}"[:500]
            workspace_digest_source = _digest(workspace_error)
            workspace_latency_ms = (time.perf_counter() - workspace_started) * 1000.0

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
    else:
        evidence_requests = ("GWT_NOT_IGNITED",)

    active_cells = list(gwt_eligible)
    if workspace_ignited:
        active_cells.append(WORKSPACE_ROLE.cell_id)
    semantic = _workspace_semantic(
        tick_id=tick_id,
        assurance_mode=assurance_mode,
        controller_action=controller_action,
        recommendation=recommendation,
        synthesis=synthesis,
        preserved=preserved,
        disagreements=disagreements,
        evidence_requests=evidence_requests,
        active_cells=active_cells,
        cell_result_digests=[c.output_digest for c in fanin_rows] + ([workspace_digest_source] if workspace_ignited else []),
        temperature=temperature,
        top_p=top_p,
        control_snapshot=control_snapshot,
        ignition_threshold=ignition_threshold,
        workspace_ignited=workspace_ignited,
        gwt_eligible_cell_ids=gwt_eligible,
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
        specialist_wall_ms=specialist_wall_ms,
        workspace_latency_ms=workspace_latency_ms,
        total_wall_ms=specialist_wall_ms + workspace_latency_ms,
        provider_tokens=sum(c.total_tokens for c in rows) + workspace_tokens,
        workspace_digest=_digest(semantic),
    )
    cycle = CognitiveCycleResult(workspace=workspace, cells=tuple(fanin_rows))
    memory_eligible = tuple(
        p.cell_id
        for p in plans
        if p.cell_id in gwt_eligible_set
        and p.compute
        and p.expose_output
        and p.memory_reentry_eligible
    )
    return ControlledCognitiveCycleResultV2(
        schema=SCHEMA,
        control_epoch=int(control_snapshot.control_epoch),
        control_snapshot_digest=control_snapshot.snapshot_digest,
        workspace_ignition_threshold=float(ignition_threshold),
        workspace_ignited=workspace_ignited,
        gwt_eligible_cell_ids=gwt_eligible,
        cycle=cycle,
        cell_plans=plans,
        memory_reentry_eligible_cell_ids=memory_eligible,
    )


def sanitized_control_receipt_v2(result: ControlledCognitiveCycleResultV2) -> dict[str, Any]:
    """Text-free receipt proving the latched control basis and GWT gate decision."""
    return {
        "schema": SCHEMA,
        "control_epoch": result.control_epoch,
        "control_snapshot_digest": result.control_snapshot_digest,
        "workspace_ignition_threshold": result.workspace_ignition_threshold,
        "workspace_ignited": result.workspace_ignited,
        "gwt_eligible_cell_ids": list(result.gwt_eligible_cell_ids),
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
        "completion_minted": False,
    }


__all__ = [
    "ControlledCognitiveCycleResultV2",
    "run_control_bound_cognitive_cycle_v2",
    "sanitized_control_receipt_v2",
]
