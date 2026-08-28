#!/usr/bin/env python3
"""Control-bound GRID10 runtime integration for Frankenstein 2.0.

This module closes the first bounded LIVE_COGNITIVE_CONTROL_PLANE integration gap:

- latch exactly one immutable ControlSnapshot before each persistent pulse;
- derive the next pulse cadence from that same snapshot;
- commit the snapshot identity inside the existing durable cognitive-cycle checkpoint;
- bind GRID specialist COMPUTE_OFF / OUTPUT_OFF / MEMORY_OFF semantics mechanically;
- propagate per-role control gains and the same snapshot identity into model prompts/fan-in;
- bind workspace ignition threshold to a deterministic ignition signal.

The control plane is functional cognition control, not canonical world truth, completion
truth, effect authority, or security authority. Model outputs remain candidate cognition.
No provider call is required by this module's tests; inference is dependency-injected.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from frankenstein2_cognitive_control_plane_v1 import (
    CognitiveControlPlane,
    ControlMode,
    ControlSnapshot,
)
from grid10_cognitive_envelope_control_v1 import AssuranceMode
from grid10_cognitive_unified_runtime_v4 import (
    RuntimeCycleNotDue,
    _atomic_commit_cycle,
    build_unified_cognitive_runtime_v4,
)
from grid10_glm_cognitive_cycle_v1 import (
    CognitiveCycleConfig,
    SPECIALISTS,
    WORKSPACE_ROLE,
)
from grid10_glm_inference_provider_v1 import (
    GLMInferenceConfig,
    GLMInferenceResult,
    infer,
)
from grid10_persistent_agency_v1 import (
    DeferredIntentState,
    GoalState,
    PersistentAgencyStore,
)

SCHEMA = "GRID10_COGNITIVE_CONTROL_BOUND_RUNTIME/v1"
PULSE_CHECKPOINT_SCHEMA = "GRID10_COGNITIVE_CONTROL_BOUND_CHECKPOINT/v1"
PULSE_BINDING_SCHEMA = "GRID10_COGNITIVE_CONTROL_BINDING_RECEIPT/v1"
CONTROLLED_CELL_SCHEMA = "GRID10_CONTROLLED_CELL_RESULT/v1"
CONTROLLED_WORKSPACE_SCHEMA = "GRID10_CONTROLLED_WORKSPACE/v1"
CONTROLLED_CYCLE_SCHEMA = "GRID10_CONTROLLED_COGNITIVE_CYCLE/v1"

# Existing control catalog compatibility mapping. The current action specialist proposes
# action/delegation affordances, so it consumes the existing delegation control family until
# a separately admitted action-specific control is introduced. This avoids silently changing
# the shared ControlSnapshot catalog/digest in one consumer only.
ROLE_CONTROL_PREFIX: Mapping[str, str] = {
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
class PulseBinding:
    schema: str
    tick_id: str
    control_epoch: int
    control_snapshot_digest: str
    cadence_control: str
    cadence_seconds: float
    agency_epoch_before: int
    agency_epoch_after: int
    source_state_epoch: int
    assurance_mode: str
    next_action: str
    next_tick_not_before: float


@dataclass(frozen=True)
class ControlBoundPulseResult:
    tick_id: str
    heartbeat_result: Any
    woken_goal_ids: tuple[str, ...]
    agency_epoch_before: int
    agency_epoch_after: int
    assurance_mode: str
    next_action: str
    next_tick_not_before: float
    control_snapshot: ControlSnapshot
    cadence_control: str
    cadence_seconds: float
    checkpoint: Mapping[str, Any]
    binding: PulseBinding


@dataclass(frozen=True)
class ControlledCellResult:
    schema: str
    tick_id: str
    cell_id: int
    role: str
    control_prefix: str
    control_mode: str
    control_gain: float
    control_epoch: int
    control_snapshot_digest: str
    computed: bool
    output_visible: bool
    memory_reentry_allowed: bool
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
class ControlledWorkspaceSnapshot:
    schema: str
    tick_id: str
    assurance_mode: str
    controller_action: str
    model_recommended_action: str | None
    effective_action: str
    status: str
    computed: bool
    ignition_signal: float
    ignition_threshold: float
    control_epoch: int
    control_snapshot_digest: str
    synthesis: str
    preserved_alternatives: tuple[str, ...]
    disagreements: tuple[str, ...]
    evidence_requests: tuple[str, ...]
    active_cells: tuple[int, ...]
    cell_result_digests: tuple[str, ...]
    specialist_wall_ms: float
    workspace_latency_ms: float
    total_wall_ms: float
    provider_tokens: int
    workspace_digest: str
    noncanonical: bool = True
    model_may_authorize_effects: bool = False


@dataclass(frozen=True)
class ControlledCognitiveCycleResult:
    schema: str
    workspace: ControlledWorkspaceSnapshot
    cells: tuple[ControlledCellResult, ...]


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    raw = value if isinstance(value, str) else _canon(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def _init_binding_schema(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS grid10_control_bound_cycles(
              tick_id TEXT PRIMARY KEY,
              schema TEXT NOT NULL,
              control_epoch INTEGER NOT NULL,
              control_snapshot_digest TEXT NOT NULL,
              cadence_control TEXT NOT NULL,
              cadence_seconds REAL NOT NULL,
              agency_epoch_before INTEGER NOT NULL,
              agency_epoch_after INTEGER NOT NULL,
              source_state_epoch INTEGER NOT NULL,
              assurance_mode TEXT NOT NULL,
              next_action TEXT NOT NULL,
              next_tick_not_before REAL NOT NULL,
              binding_json TEXT NOT NULL,
              created_ts REAL NOT NULL
            )
            """
        )
    finally:
        con.close()


def _persist_binding(path: Path, binding: PulseBinding, *, created_ts: float) -> None:
    body = _canon(asdict(binding))
    con = _connect(path)
    try:
        con.execute("BEGIN IMMEDIATE")
        existing = con.execute(
            "SELECT binding_json FROM grid10_control_bound_cycles WHERE tick_id=?",
            (binding.tick_id,),
        ).fetchone()
        if existing is not None:
            if str(existing["binding_json"]) != body:
                raise RuntimeError(f"CONTROL_BINDING_CONFLICT:{binding.tick_id}")
            con.execute("COMMIT")
            return
        con.execute(
            "INSERT INTO grid10_control_bound_cycles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                binding.tick_id,
                binding.schema,
                binding.control_epoch,
                binding.control_snapshot_digest,
                binding.cadence_control,
                binding.cadence_seconds,
                binding.agency_epoch_before,
                binding.agency_epoch_after,
                binding.source_state_epoch,
                binding.assurance_mode,
                binding.next_action,
                binding.next_tick_not_before,
                body,
                float(created_ts),
            ),
        )
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


def _pending_wake_due(snapshot: Any, *, now_ts: float, observed_events: Iterable[str]) -> bool:
    observed = frozenset(observed_events)
    goals = {g.goal_id: g for g in snapshot.goals}
    for intent in snapshot.deferred_intents:
        if intent.state != DeferredIntentState.PENDING:
            continue
        goal = goals.get(intent.goal_id)
        if goal is None or goal.state != GoalState.DORMANT or goal.generation != intent.goal_generation:
            continue
        if intent.wake_kind.value in {"TIME_AT", "PERIODIC_REVIEW"}:
            try:
                if now_ts >= float(intent.wake_value):
                    return True
            except ValueError:
                pass
        elif intent.wake_kind.value == "EVENT" and intent.wake_value in observed:
            return True
    return False


def _select_cadence(
    control: ControlSnapshot,
    *,
    agency_snapshot: Any,
    woken_goal_ids: Sequence[str],
    assurance_mode: str,
    next_action: str,
) -> tuple[str, float]:
    if assurance_mode == AssuranceMode.HOLD.value or next_action == "HOLD":
        name = "pulse.hold_interval_seconds"
    else:
        active = bool(woken_goal_ids) or any(
            g.state in {GoalState.ACTIVE, GoalState.TRIAL} for g in agency_snapshot.goals
        )
        name = "pulse.active_interval_seconds" if active else "pulse.idle_interval_seconds"
    return name, max(0.05, control.float(name))


class ControlBoundUnifiedRuntime:
    """Persistent pulse with one immutable CognitiveControlPlane snapshot per cycle."""

    def __init__(self, heartbeat_runtime: Any, agency: PersistentAgencyStore, control_plane: CognitiveControlPlane):
        self.heartbeat_runtime = heartbeat_runtime
        self.agency = agency
        self.control_plane = control_plane
        _init_binding_schema(Path(agency.path))

    def tick_once(
        self,
        *,
        tick_id: str,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        trusted_axes: Mapping[str, Any] | None = None,
        extra_variables: Mapping[str, Any] | None = None,
    ) -> ControlBoundPulseResult:
        now = time.time() if now_ts is None else float(now_ts)
        observed_events = tuple(observed_events)
        prewake = self.agency.snapshot()
        wake_expected = _pending_wake_due(prewake, now_ts=now, observed_events=observed_events)
        woken = self.agency.wake_due(
            now_ts=now,
            observed_events=observed_events,
            event_id_prefix=f"{tick_id}:wake",
        )
        before = self.agency.snapshot()
        if not woken and not self.agency.due_for_tick(now_ts=now):
            raise RuntimeCycleNotDue(f"NEXT_TICK_NOT_DUE:{before.next_tick_not_before}")
        if wake_expected and not woken:
            # The wake path was expected from the immutable pre-wake state but did not fire.
            # Continue only as a due ordinary tick; never invent a wake identity.
            pass

        # LC-1/LC-9 foundation: latch once BEFORE heartbeat/model work. Any patch committed
        # during this cycle is intentionally visible only to the next cycle.
        control = self.control_plane.snapshot()
        heartbeat = self.heartbeat_runtime.tick_once(
            tick_id=tick_id,
            trusted_axes=trusted_axes,
            extra_variables=extra_variables,
        )
        assurance_mode = getattr(heartbeat.assurance_mode, "value", str(heartbeat.assurance_mode))
        next_action = str(heartbeat.next_action)
        cadence_control, cadence_seconds = _select_cadence(
            control,
            agency_snapshot=before,
            woken_goal_ids=woken,
            assurance_mode=assurance_mode,
            next_action=next_action,
        )
        next_tick_not_before = now + cadence_seconds
        checkpoint = {
            "schema": PULSE_CHECKPOINT_SCHEMA,
            "tick_id": tick_id,
            "source_state_epoch": int(heartbeat.state_epoch),
            "assurance_mode": assurance_mode,
            "next_action": next_action,
            "woken_goal_ids": list(woken),
            "heartbeat_reasons": list(getattr(heartbeat, "reasons", ())),
            "control_schema": control.schema,
            "control_epoch": control.control_epoch,
            "control_snapshot_digest": control.snapshot_digest,
            "cadence_control": cadence_control,
            "cadence_seconds": cadence_seconds,
        }
        after_epoch = _atomic_commit_cycle(
            self.agency,
            expected_agency_epoch=before.state_epoch,
            tick_id=tick_id,
            source_state_epoch=int(heartbeat.state_epoch),
            assurance_mode=assurance_mode,
            next_action=next_action,
            woken_goal_ids=tuple(woken),
            checkpoint=checkpoint,
            next_tick_not_before=next_tick_not_before,
            now_ts=now,
        )
        binding = PulseBinding(
            schema=PULSE_BINDING_SCHEMA,
            tick_id=tick_id,
            control_epoch=control.control_epoch,
            control_snapshot_digest=control.snapshot_digest,
            cadence_control=cadence_control,
            cadence_seconds=cadence_seconds,
            agency_epoch_before=before.state_epoch,
            agency_epoch_after=after_epoch,
            source_state_epoch=int(heartbeat.state_epoch),
            assurance_mode=assurance_mode,
            next_action=next_action,
            next_tick_not_before=next_tick_not_before,
        )
        _persist_binding(Path(self.agency.path), binding, created_ts=now)
        return ControlBoundPulseResult(
            tick_id=tick_id,
            heartbeat_result=heartbeat,
            woken_goal_ids=tuple(woken),
            agency_epoch_before=before.state_epoch,
            agency_epoch_after=after_epoch,
            assurance_mode=assurance_mode,
            next_action=next_action,
            next_tick_not_before=next_tick_not_before,
            control_snapshot=control,
            cadence_control=cadence_control,
            cadence_seconds=cadence_seconds,
            checkpoint=checkpoint,
            binding=binding,
        )


def build_control_bound_unified_runtime(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
) -> tuple[Any, Any, PersistentAgencyStore, CognitiveControlPlane, ControlBoundUnifiedRuntime, Any]:
    fabric, heartbeat, agency, base_runtime, fingerprint = build_unified_cognitive_runtime_v4(
        unified_db,
        allow_regulator_writes=allow_regulator_writes,
    )
    control = CognitiveControlPlane(Path(unified_db))
    runtime = ControlBoundUnifiedRuntime(base_runtime.heartbeat_runtime, agency, control)
    return fabric, heartbeat, agency, control, runtime, fingerprint


def _clean_seq(value: Any, *, limit: int = 8, chars: int = 700) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    out: list[str] = []
    for item in value[:limit]:
        text = str(item).strip()[:chars]
        if text:
            out.append(text)
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


def _clamp01(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if x != x or x in {float("inf"), float("-inf")}:
        return None
    return max(0.0, min(1.0, x))


def _effective_action(mode: AssuranceMode, controller_action: str) -> str:
    if mode == AssuranceMode.HOLD:
        return "HOLD"
    safe = {"OBSERVE", "SEARCH", "SIMULATE", "ASK", "WAIT", "HOLD"}
    if mode == AssuranceMode.CONTAINED and controller_action not in safe:
        return "OBSERVE"
    return controller_action


def _system_contract() -> str:
    return (
        "You are one logical GRID10 cognition cell inside EntityOS. You are candidate cognition only. "
        "Never mint canonical state, effect authority, or completion truth. Preserve meaningful unknowns. "
        "Return one compact JSON object only."
    )


def _controlled_cell_prompt(
    *,
    role: Any,
    mode: AssuranceMode,
    controller_action: str,
    context: Mapping[str, Any],
    control: ControlSnapshot,
    control_prefix: str,
    control_mode: ControlMode,
    control_gain: float,
) -> str:
    return (
        f"ROLE={role.role}\nMISSION={role.mission}\nASSURANCE_MODE={mode.value}\n"
        f"DETERMINISTIC_CONTROLLER_ACTION={controller_action}\n"
        f"CONTROL_SNAPSHOT={control.snapshot_digest}\nCONTROL_EPOCH={control.control_epoch}\n"
        f"CONTROL_PREFIX={control_prefix}\nCONTROL_MODE={control_mode.value}\nCONTROL_GAIN={control_gain:.6f}\n"
        "CONTROL_GAIN is a bounded cognitive weighting input, not authority. "
        "Return JSON with candidate, alternatives, evidence_needed, confidence, unresolved.\n"
        f"TICK_CONTEXT={_canon(context)}"
    )


def _make_not_computed(
    *, tick_id: str, role: Any, control: ControlSnapshot, prefix: str, mode: ControlMode, gain: float, status: str
) -> ControlledCellResult:
    digest = _digest({"tick_id": tick_id, "cell_id": role.cell_id, "status": status, "control": control.snapshot_digest})
    return ControlledCellResult(
        schema=CONTROLLED_CELL_SCHEMA,
        tick_id=tick_id,
        cell_id=role.cell_id,
        role=role.role,
        control_prefix=prefix,
        control_mode=mode.value,
        control_gain=gain,
        control_epoch=control.control_epoch,
        control_snapshot_digest=control.snapshot_digest,
        computed=False,
        output_visible=False,
        memory_reentry_allowed=False,
        status=status,
        candidate="",
        alternatives=(),
        evidence_needed=("NOT_COMPUTED",),
        confidence=None,
        unresolved=True,
        output_digest=digest,
        latency_ms=0.0,
        total_tokens=0,
        thinking=bool(role.thinking),
    )


def _cell_from_inference(
    *,
    tick_id: str,
    role: Any,
    result: GLMInferenceResult,
    control: ControlSnapshot,
    prefix: str,
    mode: ControlMode,
    gain: float,
) -> ControlledCellResult:
    obj = _json_object(result.content) or {}
    candidate = str(obj.get("candidate") or "").strip()[:800]
    alternatives = _clean_seq(obj.get("alternatives"), limit=4, chars=500)
    evidence = _clean_seq(obj.get("evidence_needed"), limit=4, chars=500)
    confidence = _clamp01(obj.get("confidence"))
    unresolved = bool(obj.get("unresolved", bool(alternatives)))
    output_visible = mode != ControlMode.OUTPUT_OFF
    memory_reentry_allowed = mode != ControlMode.MEMORY_OFF
    if not output_visible:
        candidate = ""
        alternatives = ()
        evidence = ("OUTPUT_WITHHELD_BY_CONTROL",)
        confidence = None
        unresolved = True
        status = "OUTPUT_OFF"
    elif mode == ControlMode.MEMORY_OFF:
        status = "MEMORY_OFF"
    else:
        status = "STRUCTURED_CANDIDATE" if obj else "UNSTRUCTURED_CANDIDATE"
    return ControlledCellResult(
        schema=CONTROLLED_CELL_SCHEMA,
        tick_id=tick_id,
        cell_id=role.cell_id,
        role=role.role,
        control_prefix=prefix,
        control_mode=mode.value,
        control_gain=gain,
        control_epoch=control.control_epoch,
        control_snapshot_digest=control.snapshot_digest,
        computed=True,
        output_visible=output_visible,
        memory_reentry_allowed=memory_reentry_allowed,
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


def _cell_error(
    *, tick_id: str, role: Any, exc: Exception, control: ControlSnapshot, prefix: str, mode: ControlMode, gain: float
) -> ControlledCellResult:
    error = f"{type(exc).__name__}:{exc}"[:500]
    return ControlledCellResult(
        schema=CONTROLLED_CELL_SCHEMA,
        tick_id=tick_id,
        cell_id=role.cell_id,
        role=role.role,
        control_prefix=prefix,
        control_mode=mode.value,
        control_gain=gain,
        control_epoch=control.control_epoch,
        control_snapshot_digest=control.snapshot_digest,
        computed=True,
        output_visible=mode != ControlMode.OUTPUT_OFF,
        memory_reentry_allowed=mode != ControlMode.MEMORY_OFF,
        status="ERROR",
        candidate="",
        alternatives=(),
        evidence_needed=("provider_or_cell_recovery",),
        confidence=None,
        unresolved=True,
        output_digest=_digest(error),
        latency_ms=0.0,
        total_tokens=0,
        thinking=bool(role.thinking),
        error=error,
    )


def _workspace_prompt(
    *,
    mode: AssuranceMode,
    controller_action: str,
    cells: Sequence[ControlledCellResult],
    control: ControlSnapshot,
    ignition_signal: float,
    ignition_threshold: float,
    max_chars_per_cell: int,
) -> str:
    compact = []
    for c in cells:
        compact.append({
            "cell_id": c.cell_id,
            "role": c.role,
            "status": c.status,
            "computed": c.computed,
            "output_visible": c.output_visible,
            "memory_reentry_allowed": c.memory_reentry_allowed,
            "control_mode": c.control_mode,
            "control_gain": c.control_gain,
            "candidate": c.candidate[:max_chars_per_cell] if c.output_visible else "",
            "alternatives": list(c.alternatives) if c.output_visible else [],
            "evidence_needed": list(c.evidence_needed),
            "confidence": c.confidence if c.output_visible else None,
            "unresolved": c.unresolved,
            "error": c.error,
        })
    return (
        "ROLE=workspace/GWT fan-in\n"
        f"ASSURANCE_MODE={mode.value}\nDETERMINISTIC_CONTROLLER_ACTION={controller_action}\n"
        f"CONTROL_SNAPSHOT={control.snapshot_digest}\nCONTROL_EPOCH={control.control_epoch}\n"
        f"WORKSPACE_IGNITION_SIGNAL={ignition_signal:.6f}\nWORKSPACE_IGNITION_THRESHOLD={ignition_threshold:.6f}\n"
        "OUTPUT_OFF cell text is intentionally absent. COMPUTE_OFF cells are NOT_COMPUTED and must not be reconstructed. "
        "Return JSON with synthesis, preserved_alternatives, disagreements, evidence_requests, recommended_action.\n"
        f"SPECIALISTS={_canon(compact)}"
    )


def run_controlled_cognitive_cycle(
    *,
    tick_id: str,
    assurance_mode: AssuranceMode,
    controller_action: str,
    context: Mapping[str, Any],
    control_snapshot: ControlSnapshot,
    workspace_ignition_signal: float = 1.0,
    config: CognitiveCycleConfig = CognitiveCycleConfig(),
    inference_fn: Callable[..., GLMInferenceResult] = infer,
) -> ControlledCognitiveCycleResult:
    """Run a GRID cycle against one already-latched immutable ControlSnapshot."""
    if not tick_id.strip():
        raise ValueError("tick_id required")
    context_json = _canon(context)
    if len(context_json) > config.max_context_chars:
        raise ValueError("context exceeds governed max_context_chars; compile a smaller context capsule")
    ignition_signal = max(0.0, min(1.0, float(workspace_ignition_signal)))
    ignition_threshold = control_snapshot.float("grid.workspace_ignition_threshold")
    started = time.perf_counter()
    specialist_started = time.perf_counter()

    rows: list[ControlledCellResult] = []
    runnable: list[tuple[Any, str, ControlMode, float]] = []
    for role in SPECIALISTS:
        prefix = ROLE_CONTROL_PREFIX[role.role]
        mode = control_snapshot.mode(prefix + ".mode")
        gain = control_snapshot.float(prefix + ".gain")
        if assurance_mode not in role.modes:
            rows.append(_make_not_computed(
                tick_id=tick_id, role=role, control=control_snapshot, prefix=prefix,
                mode=mode, gain=gain, status="ASSURANCE_SUPPRESSED",
            ))
        elif mode == ControlMode.COMPUTE_OFF:
            rows.append(_make_not_computed(
                tick_id=tick_id, role=role, control=control_snapshot, prefix=prefix,
                mode=mode, gain=gain, status="NOT_COMPUTED",
            ))
        else:
            runnable.append((role, prefix, mode, gain))

    def invoke(item: tuple[Any, str, ControlMode, float]) -> ControlledCellResult:
        role, prefix, mode, gain = item
        try:
            result = inference_fn(
                [
                    {"role": "system", "content": _system_contract()},
                    {"role": "user", "content": _controlled_cell_prompt(
                        role=role,
                        mode=assurance_mode,
                        controller_action=controller_action,
                        context=context,
                        control=control_snapshot,
                        control_prefix=prefix,
                        control_mode=mode,
                        control_gain=gain,
                    )},
                ],
                config=GLMInferenceConfig(
                    max_tokens=config.max_tokens_per_specialist,
                    temperature=0.25 if assurance_mode == AssuranceMode.HOLD else 0.7,
                    top_p=0.75 if assurance_mode == AssuranceMode.HOLD else 0.9,
                    thinking=bool(config.thinking_for_deep_roles and role.thinking),
                    timeout_seconds=config.timeout_seconds,
                ),
            )
            return _cell_from_inference(
                tick_id=tick_id, role=role, result=result, control=control_snapshot,
                prefix=prefix, mode=mode, gain=gain,
            )
        except Exception as exc:
            return _cell_error(
                tick_id=tick_id, role=role, exc=exc, control=control_snapshot,
                prefix=prefix, mode=mode, gain=gain,
            )

    if runnable:
        with ThreadPoolExecutor(max_workers=min(config.max_parallel_specialists, len(runnable))) as pool:
            futures = [pool.submit(invoke, item) for item in runnable]
            for future in as_completed(futures):
                rows.append(future.result())
    rows.sort(key=lambda c: c.cell_id)
    specialist_wall_ms = (time.perf_counter() - specialist_started) * 1000.0

    workspace_computed = ignition_signal >= ignition_threshold
    workspace_started = time.perf_counter()
    workspace_tokens = 0
    workspace_latency_ms = 0.0
    recommendation: str | None = None
    synthesis = ""
    preserved: tuple[str, ...] = ()
    disagreements: tuple[str, ...] = ()
    evidence_requests: tuple[str, ...] = ()
    workspace_result_digest = _digest({
        "tick_id": tick_id,
        "status": "NOT_COMPUTED_THRESHOLD",
        "control": control_snapshot.snapshot_digest,
    })
    workspace_status = "NOT_COMPUTED_THRESHOLD"

    if workspace_computed:
        try:
            result = inference_fn(
                [
                    {"role": "system", "content": _system_contract()},
                    {"role": "user", "content": _workspace_prompt(
                        mode=assurance_mode,
                        controller_action=controller_action,
                        cells=rows,
                        control=control_snapshot,
                        ignition_signal=ignition_signal,
                        ignition_threshold=ignition_threshold,
                        max_chars_per_cell=config.max_fanin_chars_per_cell,
                    )},
                ],
                config=GLMInferenceConfig(
                    max_tokens=config.max_tokens_workspace,
                    temperature=0.25 if assurance_mode == AssuranceMode.HOLD else 0.5,
                    top_p=0.75 if assurance_mode == AssuranceMode.HOLD else 0.9,
                    thinking=config.thinking_for_deep_roles,
                    timeout_seconds=max(config.timeout_seconds, 90.0 if config.thinking_for_deep_roles else config.timeout_seconds),
                ),
            )
            obj = _json_object(result.content) or {}
            synthesis = str(obj.get("synthesis") or "").strip()[:2000]
            preserved = _clean_seq(obj.get("preserved_alternatives"))
            disagreements = _clean_seq(obj.get("disagreements"))
            evidence_requests = _clean_seq(obj.get("evidence_requests"))
            allowed_actions = {"HOLD", "OBSERVE", "SEARCH", "SIMULATE", "ASK", "WAIT", "ACT_CANDIDATE"}
            raw = obj.get("recommended_action")
            recommendation = str(raw).strip() if raw is not None else None
            if recommendation not in allowed_actions:
                recommendation = None
            workspace_tokens = int(result.receipt.total_tokens or 0)
            workspace_latency_ms = float(result.receipt.latency_ms)
            workspace_result_digest = result.receipt.response_digest
            workspace_status = "STRUCTURED_CANDIDATE" if obj else "UNSTRUCTURED_CANDIDATE"
        except Exception as exc:
            workspace_status = "ERROR"
            workspace_result_digest = _digest(f"{type(exc).__name__}:{exc}")
            workspace_latency_ms = (time.perf_counter() - workspace_started) * 1000.0

    total_wall_ms = (time.perf_counter() - started) * 1000.0
    provider_tokens = sum(c.total_tokens for c in rows) + workspace_tokens
    active_cells = tuple(c.cell_id for c in rows if c.computed) + ((WORKSPACE_ROLE.cell_id,) if workspace_computed else ())
    cell_digests = tuple(c.output_digest for c in rows) + ((workspace_result_digest,) if workspace_computed else ())
    semantic = {
        "tick_id": tick_id,
        "assurance_mode": assurance_mode.value,
        "controller_action": controller_action,
        "model_recommended_action": recommendation,
        "effective_action": _effective_action(assurance_mode, controller_action),
        "status": workspace_status,
        "computed": workspace_computed,
        "ignition_signal": ignition_signal,
        "ignition_threshold": ignition_threshold,
        "control_epoch": control_snapshot.control_epoch,
        "control_snapshot_digest": control_snapshot.snapshot_digest,
        "active_cells": active_cells,
        "cell_result_digests": cell_digests,
    }
    workspace = ControlledWorkspaceSnapshot(
        schema=CONTROLLED_WORKSPACE_SCHEMA,
        tick_id=tick_id,
        assurance_mode=assurance_mode.value,
        controller_action=controller_action,
        model_recommended_action=recommendation,
        effective_action=semantic["effective_action"],
        status=workspace_status,
        computed=workspace_computed,
        ignition_signal=ignition_signal,
        ignition_threshold=ignition_threshold,
        control_epoch=control_snapshot.control_epoch,
        control_snapshot_digest=control_snapshot.snapshot_digest,
        synthesis=synthesis,
        preserved_alternatives=preserved,
        disagreements=disagreements,
        evidence_requests=evidence_requests,
        active_cells=active_cells,
        cell_result_digests=cell_digests,
        specialist_wall_ms=specialist_wall_ms,
        workspace_latency_ms=workspace_latency_ms,
        total_wall_ms=total_wall_ms,
        provider_tokens=provider_tokens,
        workspace_digest=_digest(semantic),
    )
    return ControlledCognitiveCycleResult(CONTROLLED_CYCLE_SCHEMA, workspace, tuple(rows))


def run_controlled_cognitive_cycle_from_plane(
    *,
    control_plane: CognitiveControlPlane,
    tick_id: str,
    assurance_mode: AssuranceMode,
    controller_action: str,
    context: Mapping[str, Any],
    workspace_ignition_signal: float = 1.0,
    config: CognitiveCycleConfig = CognitiveCycleConfig(),
    inference_fn: Callable[..., GLMInferenceResult] = infer,
) -> ControlledCognitiveCycleResult:
    # One snapshot call only. Mid-cycle writers cannot mutate this immutable value object.
    snapshot = control_plane.snapshot()
    return run_controlled_cognitive_cycle(
        tick_id=tick_id,
        assurance_mode=assurance_mode,
        controller_action=controller_action,
        context=context,
        control_snapshot=snapshot,
        workspace_ignition_signal=workspace_ignition_signal,
        config=config,
        inference_fn=inference_fn,
    )


def sanitized_receipt(result: ControlledCognitiveCycleResult) -> dict[str, Any]:
    """Persistence-safe control/runtime receipt; excludes prompts and model text."""
    return {
        "schema": CONTROLLED_CYCLE_SCHEMA,
        "workspace": {
            "tick_id": result.workspace.tick_id,
            "assurance_mode": result.workspace.assurance_mode,
            "controller_action": result.workspace.controller_action,
            "effective_action": result.workspace.effective_action,
            "status": result.workspace.status,
            "computed": result.workspace.computed,
            "ignition_signal": result.workspace.ignition_signal,
            "ignition_threshold": result.workspace.ignition_threshold,
            "control_epoch": result.workspace.control_epoch,
            "control_snapshot_digest": result.workspace.control_snapshot_digest,
            "active_cells": list(result.workspace.active_cells),
            "cell_result_digests": list(result.workspace.cell_result_digests),
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
                "control_prefix": c.control_prefix,
                "control_mode": c.control_mode,
                "control_gain": c.control_gain,
                "control_epoch": c.control_epoch,
                "control_snapshot_digest": c.control_snapshot_digest,
                "computed": c.computed,
                "output_visible": c.output_visible,
                "memory_reentry_allowed": c.memory_reentry_allowed,
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


__all__ = [
    "ControlBoundPulseResult",
    "ControlBoundUnifiedRuntime",
    "ControlledCellResult",
    "ControlledCognitiveCycleResult",
    "ControlledWorkspaceSnapshot",
    "PulseBinding",
    "ROLE_CONTROL_PREFIX",
    "build_control_bound_unified_runtime",
    "run_controlled_cognitive_cycle",
    "run_controlled_cognitive_cycle_from_plane",
    "sanitized_receipt",
]
