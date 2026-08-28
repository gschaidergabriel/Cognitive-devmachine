#!/usr/bin/env python3
"""Governed GLM-backed cognitive cycle for GRID10.

This is the model-cognition plane underneath the deterministic Cognitive Envelope
heartbeat. It deliberately does NOT decide authority, containment, goal admission,
completion, or external effects.

Execution topology per cognitive tick:

    deterministic heartbeat / assurance mode
                 |
          9 specialist cells  (parallel)
                 |
          cell 9 workspace/GWT fan-in
                 |
      noncanonical workspace snapshot

The ninth specialist + one fan-in call gives ten logical GRID cells while preserving
an explicit causal fan-in boundary. Future latency work may stream partial fan-in, but
v1 keeps the boundary simple and measurable.

GLM outputs are candidate/projection only. The effective action remains the action
class chosen by the deterministic heartbeat. In HOLD/CONTAINED modes the active cell
set is reduced and all prompts are explicitly read-only/recovery scoped.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import time
from typing import Any, Callable, Mapping, Sequence

from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_cognitive_regulator_port_v1 import CognitiveRegulatorPort
from grid10_glm_inference_provider_v1 import GLMInferenceConfig, GLMInferenceResult, infer

SCHEMA = "GRID10_GLM_COGNITIVE_CYCLE/v1"
CELL_SCHEMA = "GRID10_GLM_CELL_RESULT/v1"
WORKSPACE_SCHEMA = "GRID10_GLM_WORKSPACE/v1"


@dataclass(frozen=True)
class CellRole:
    cell_id: int
    role: str
    mission: str
    modes: tuple[AssuranceMode, ...]
    thinking: bool = False


SPECIALISTS: tuple[CellRole, ...] = (
    CellRole(0, "state", "Reconstruct the smallest relevant current situation and contradictions.", tuple(AssuranceMode)),
    CellRole(1, "memory", "Identify only the memory/evidence needed for this tick; avoid broad retrieval.", tuple(AssuranceMode)),
    CellRole(2, "goal", "Inspect goal progress, open loops, and candidate goal deltas without admitting them.", (AssuranceMode.NORMAL, AssuranceMode.CAUTION, AssuranceMode.CONTAINED)),
    CellRole(3, "critic", "Attack premature completion and identify missing mandatory evidence.", tuple(AssuranceMode)),
    CellRole(4, "planner", "Propose the smallest next discriminating work delta.", (AssuranceMode.NORMAL, AssuranceMode.CAUTION)),
    CellRole(5, "simulator", "Generate bounded counterfactual outcomes and failure modes; never treat simulation as fact.", (AssuranceMode.NORMAL, AssuranceMode.CAUTION, AssuranceMode.CONTAINED), True),
    CellRole(6, "skeptic", "Generate strongest counterhypothesis/counterevidence and unresolved alternatives.", tuple(AssuranceMode), True),
    CellRole(7, "epistemic", "Separate observed, inferred, simulated, unknown, and contradictory claims.", tuple(AssuranceMode)),
    CellRole(8, "action", "Propose candidate action classes/affordances only; never authorize an effect.", (AssuranceMode.NORMAL, AssuranceMode.CAUTION)),
)

WORKSPACE_ROLE = CellRole(
    9,
    "workspace",
    "Fuse specialist candidates while preserving unresolved alternatives and disagreements; do not mint authority.",
    tuple(AssuranceMode),
    True,
)


@dataclass(frozen=True)
class CognitiveCycleConfig:
    max_parallel_specialists: int = 9
    max_tokens_per_specialist: int = 160
    max_tokens_workspace: int = 320
    timeout_seconds: float = 60.0
    thinking_for_deep_roles: bool = True
    max_context_chars: int = 12000
    max_fanin_chars_per_cell: int = 1800

    def __post_init__(self) -> None:
        if not 1 <= self.max_parallel_specialists <= 9:
            raise ValueError("max_parallel_specialists must be 1..9")
        if not 32 <= self.max_tokens_per_specialist <= 1024:
            raise ValueError("max_tokens_per_specialist must be 32..1024")
        if not 64 <= self.max_tokens_workspace <= 2048:
            raise ValueError("max_tokens_workspace must be 64..2048")
        if not 1000 <= self.max_context_chars <= 50000:
            raise ValueError("max_context_chars must be 1000..50000")


@dataclass(frozen=True)
class CellResult:
    schema: str
    tick_id: str
    cell_id: int
    role: str
    status: str
    candidate: str
    alternatives: tuple[str, ...]
    evidence_needed: tuple[str, ...]
    confidence: float | None
    unresolved: bool
    output_digest: str
    latency_ms: float
    total_tokens: int
    thinking: bool
    error: str | None = None


@dataclass(frozen=True)
class CognitiveWorkspaceSnapshot:
    schema: str
    tick_id: str
    assurance_mode: str
    controller_action: str
    model_recommended_action: str | None
    effective_action: str
    synthesis: str
    preserved_alternatives: tuple[str, ...]
    disagreements: tuple[str, ...]
    evidence_requests: tuple[str, ...]
    active_cells: tuple[int, ...]
    cell_result_digests: tuple[str, ...]
    temperature: float
    top_p: float
    specialist_wall_ms: float
    workspace_latency_ms: float
    total_wall_ms: float
    provider_tokens: int
    workspace_digest: str
    noncanonical: bool = True
    model_may_authorize_effects: bool = False


@dataclass(frozen=True)
class CognitiveCycleResult:
    workspace: CognitiveWorkspaceSnapshot
    cells: tuple[CellResult, ...]


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clamp01(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return max(0.0, min(1.0, x))


def _clean_seq(value: Any, *, limit: int = 4, chars: int = 500) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    out: list[str] = []
    for item in value[:limit]:
        s = str(item).strip()[:chars]
        if s:
            out.append(s)
    return tuple(out)


def _json_object(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _mode_scope(mode: AssuranceMode) -> str:
    if mode == AssuranceMode.HOLD:
        return "HOLD: read-only diagnosis/recovery cognition only; no action/effect proposal beyond HOLD/OBSERVE/SEARCH/SIMULATE/ASK/WAIT."
    if mode == AssuranceMode.CONTAINED:
        return "CONTAINED: read-only/contained cognition; no unrestricted external effect proposal."
    if mode == AssuranceMode.CAUTION:
        return "CAUTION: evidence-seeking cognition; proposals remain reversible candidates."
    if mode == AssuranceMode.RECOVERY:
        return "RECOVERY: diagnose restoration of verified invariants; no authority expansion."
    return "NORMAL: ordinary candidate cognition; all effect authority remains outside the model."


def active_specialists(mode: AssuranceMode) -> tuple[CellRole, ...]:
    return tuple(role for role in SPECIALISTS if mode in role.modes)


def _system_contract() -> str:
    return (
        "You are one logical GRID10 cognition cell inside EntityOS. "
        "You are NOT canonical state, NOT alignment authority, NOT EffectGate, and NOT completion authority. "
        "Never convert simulation/self-report into observed fact. Preserve meaningful unresolved alternatives. "
        "Return one compact JSON object only with keys candidate, alternatives, evidence_needed, confidence, unresolved. "
        "alternatives and evidence_needed must be short arrays; confidence is 0..1 or null; unresolved is boolean."
    )


def _cell_prompt(role: CellRole, *, mode: AssuranceMode, controller_action: str, context: Mapping[str, Any]) -> str:
    body = _canon(context)
    return (
        f"ROLE={role.role}\nMISSION={role.mission}\nASSURANCE={_mode_scope(mode)}\n"
        f"DETERMINISTIC_CONTROLLER_ACTION={controller_action}\n"
        "The controller action is context, not an instruction to fabricate supporting evidence.\n"
        f"TICK_CONTEXT={body}"
    )


def _cell_result_from_inference(tick_id: str, role: CellRole, result: GLMInferenceResult) -> CellResult:
    obj = _json_object(result.content)
    if obj is None:
        candidate = result.content.strip()[:800]
        alternatives: tuple[str, ...] = ()
        evidence: tuple[str, ...] = ()
        confidence = None
        unresolved = True
        status = "UNSTRUCTURED_CANDIDATE"
    else:
        candidate = str(obj.get("candidate") or "").strip()[:800]
        alternatives = _clean_seq(obj.get("alternatives"))
        evidence = _clean_seq(obj.get("evidence_needed"))
        confidence = _clamp01(obj.get("confidence"))
        unresolved = bool(obj.get("unresolved", bool(alternatives)))
        status = "STRUCTURED_CANDIDATE"
    return CellResult(
        schema=CELL_SCHEMA,
        tick_id=tick_id,
        cell_id=role.cell_id,
        role=role.role,
        status=status,
        candidate=candidate,
        alternatives=alternatives,
        evidence_needed=evidence,
        confidence=confidence,
        unresolved=unresolved,
        output_digest=result.receipt.response_digest,
        latency_ms=float(result.receipt.latency_ms),
        total_tokens=int(result.receipt.total_tokens or 0),
        thinking=bool(result.receipt.thinking_enabled),
    )


def _error_result(tick_id: str, role: CellRole, exc: Exception) -> CellResult:
    error = f"{type(exc).__name__}:{exc}"[:500]
    return CellResult(
        schema=CELL_SCHEMA,
        tick_id=tick_id,
        cell_id=role.cell_id,
        role=role.role,
        status="ERROR",
        candidate="",
        alternatives=(),
        evidence_needed=("provider_or_cell_recovery",),
        confidence=None,
        unresolved=True,
        output_digest=_digest_text(error),
        latency_ms=0.0,
        total_tokens=0,
        thinking=role.thinking,
        error=error,
    )


def _read_sampling(fabric: Any, mode: AssuranceMode) -> tuple[float, float]:
    port = CognitiveRegulatorPort(fabric)
    try:
        temperature = float(port.read("cog.temperature").value_real)
    except Exception:
        temperature = 0.7
    try:
        top_p = float(port.read("cog.top_p").value_real)
    except Exception:
        top_p = 0.9

    # Runtime-assurance caps: model sampling cannot make HOLD/CONTAINED more aggressive.
    if mode == AssuranceMode.HOLD:
        temperature = min(temperature, 0.25)
        top_p = min(top_p, 0.75)
    elif mode in {AssuranceMode.CONTAINED, AssuranceMode.RECOVERY}:
        temperature = min(temperature, 0.40)
        top_p = min(top_p, 0.85)
    elif mode == AssuranceMode.CAUTION:
        temperature = min(temperature, 0.65)
    return max(0.0, min(2.0, temperature)), max(0.05, min(1.0, top_p))


def _workspace_prompt(
    *,
    mode: AssuranceMode,
    controller_action: str,
    cells: Sequence[CellResult],
    max_chars_per_cell: int,
) -> str:
    compact = []
    for c in cells:
        compact.append({
            "cell_id": c.cell_id,
            "role": c.role,
            "status": c.status,
            "candidate": c.candidate[:max_chars_per_cell],
            "alternatives": list(c.alternatives),
            "evidence_needed": list(c.evidence_needed),
            "confidence": c.confidence,
            "unresolved": c.unresolved,
            "error": c.error,
        })
    return (
        "ROLE=workspace/GWT fan-in\n"
        f"ASSURANCE={_mode_scope(mode)}\n"
        f"DETERMINISTIC_CONTROLLER_ACTION={controller_action}\n"
        "Fuse without erasing real disagreement. Return compact JSON only with keys: "
        "synthesis (string), preserved_alternatives (array), disagreements (array), "
        "evidence_requests (array), recommended_action (one of HOLD,OBSERVE,SEARCH,SIMULATE,ASK,WAIT,ACT_CANDIDATE or null). "
        "Your recommended_action is nonauthoritative and cannot expand the deterministic controller action.\n"
        f"SPECIALISTS={_canon(compact)}"
    )


def _effective_action(mode: AssuranceMode, controller_action: str, recommendation: str | None) -> str:
    # Model recommendation never outranks the deterministic heartbeat.
    if mode == AssuranceMode.HOLD:
        return "HOLD"
    if mode == AssuranceMode.CONTAINED and controller_action not in {"OBSERVE", "SEARCH", "SIMULATE", "ASK", "WAIT", "HOLD"}:
        return "OBSERVE"
    return controller_action


def run_cognitive_cycle(
    *,
    tick_id: str,
    assurance_mode: AssuranceMode,
    controller_action: str,
    fabric: Any,
    context: Mapping[str, Any],
    config: CognitiveCycleConfig = CognitiveCycleConfig(),
    inference_fn: Callable[..., GLMInferenceResult] = infer,
) -> CognitiveCycleResult:
    if not tick_id.strip():
        raise ValueError("tick_id required")
    context_json = _canon(context)
    if len(context_json) > config.max_context_chars:
        raise ValueError("context exceeds governed max_context_chars; compile a smaller context capsule")

    temperature, top_p = _read_sampling(fabric, assurance_mode)
    roles = active_specialists(assurance_mode)
    started = time.perf_counter()
    specialist_started = time.perf_counter()

    def invoke(role: CellRole) -> CellResult:
        try:
            result = inference_fn(
                [
                    {"role": "system", "content": _system_contract()},
                    {"role": "user", "content": _cell_prompt(role, mode=assurance_mode, controller_action=controller_action, context=context)},
                ],
                config=GLMInferenceConfig(
                    max_tokens=config.max_tokens_per_specialist,
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
    with ThreadPoolExecutor(max_workers=min(config.max_parallel_specialists, len(roles))) as pool:
        futures = {pool.submit(invoke, role): role for role in roles}
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda x: x.cell_id)
    specialist_wall_ms = (time.perf_counter() - specialist_started) * 1000.0

    workspace_started = time.perf_counter()
    workspace_error: str | None = None
    try:
        workspace_result = inference_fn(
            [
                {"role": "system", "content": _system_contract()},
                {"role": "user", "content": _workspace_prompt(
                    mode=assurance_mode,
                    controller_action=controller_action,
                    cells=rows,
                    max_chars_per_cell=config.max_fanin_chars_per_cell,
                )},
            ],
            config=GLMInferenceConfig(
                max_tokens=config.max_tokens_workspace,
                temperature=min(temperature, 0.5),
                top_p=top_p,
                thinking=config.thinking_for_deep_roles,
                timeout_seconds=max(config.timeout_seconds, 90.0 if config.thinking_for_deep_roles else config.timeout_seconds),
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
        workspace_latency_ms = (time.perf_counter() - workspace_started) * 1000.0

    synthesis = str(workspace_obj.get("synthesis") or ("workspace_error:" + workspace_error if workspace_error else "")).strip()[:2000]
    preserved = _clean_seq(workspace_obj.get("preserved_alternatives"), limit=8, chars=700)
    disagreements = _clean_seq(workspace_obj.get("disagreements"), limit=8, chars=700)
    evidence_requests = _clean_seq(workspace_obj.get("evidence_requests"), limit=8, chars=700)
    allowed_actions = {"HOLD", "OBSERVE", "SEARCH", "SIMULATE", "ASK", "WAIT", "ACT_CANDIDATE"}
    rec_raw = workspace_obj.get("recommended_action")
    recommendation = str(rec_raw).strip() if rec_raw is not None else None
    if recommendation not in allowed_actions:
        recommendation = None

    total_wall_ms = (time.perf_counter() - started) * 1000.0
    provider_tokens = sum(c.total_tokens for c in rows) + workspace_tokens
    semantic = {
        "tick_id": tick_id,
        "assurance_mode": assurance_mode.value,
        "controller_action": controller_action,
        "model_recommended_action": recommendation,
        "effective_action": _effective_action(assurance_mode, controller_action, recommendation),
        "synthesis": synthesis,
        "preserved_alternatives": preserved,
        "disagreements": disagreements,
        "evidence_requests": evidence_requests,
        "active_cells": [c.cell_id for c in rows] + [WORKSPACE_ROLE.cell_id],
        "cell_result_digests": [c.output_digest for c in rows] + [workspace_digest_source],
        "temperature": temperature,
        "top_p": top_p,
    }
    workspace = CognitiveWorkspaceSnapshot(
        schema=WORKSPACE_SCHEMA,
        tick_id=tick_id,
        assurance_mode=assurance_mode.value,
        controller_action=controller_action,
        model_recommended_action=recommendation,
        effective_action=semantic["effective_action"],
        synthesis=synthesis,
        preserved_alternatives=preserved,
        disagreements=disagreements,
        evidence_requests=evidence_requests,
        active_cells=tuple(semantic["active_cells"]),
        cell_result_digests=tuple(semantic["cell_result_digests"]),
        temperature=temperature,
        top_p=top_p,
        specialist_wall_ms=specialist_wall_ms,
        workspace_latency_ms=workspace_latency_ms,
        total_wall_ms=total_wall_ms,
        provider_tokens=provider_tokens,
        workspace_digest=hashlib.sha256(_canon(semantic).encode("utf-8")).hexdigest(),
    )
    return CognitiveCycleResult(workspace=workspace, cells=tuple(rows))


def sanitized_receipt(result: CognitiveCycleResult) -> dict[str, Any]:
    """Persistence-safe performance/evidence receipt; excludes model text and prompts."""
    return {
        "schema": SCHEMA,
        "workspace": {
            "schema": result.workspace.schema,
            "tick_id": result.workspace.tick_id,
            "assurance_mode": result.workspace.assurance_mode,
            "controller_action": result.workspace.controller_action,
            "model_recommended_action": result.workspace.model_recommended_action,
            "effective_action": result.workspace.effective_action,
            "active_cells": list(result.workspace.active_cells),
            "cell_result_digests": list(result.workspace.cell_result_digests),
            "temperature": result.workspace.temperature,
            "top_p": result.workspace.top_p,
            "specialist_wall_ms": result.workspace.specialist_wall_ms,
            "workspace_latency_ms": result.workspace.workspace_latency_ms,
            "total_wall_ms": result.workspace.total_wall_ms,
            "provider_tokens": result.workspace.provider_tokens,
            "workspace_digest": result.workspace.workspace_digest,
            "noncanonical": True,
            "model_may_authorize_effects": False,
        },
        "cells": [
            {
                "cell_id": c.cell_id,
                "role": c.role,
                "status": c.status,
                "output_digest": c.output_digest,
                "latency_ms": c.latency_ms,
                "total_tokens": c.total_tokens,
                "thinking": c.thinking,
                "error": c.error,
            }
            for c in result.cells
        ],
        "prompts_recorded": False,
        "responses_recorded": False,
        "secret_recorded": False,
    }
