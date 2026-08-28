#!/usr/bin/env python3
"""Persistent, bounded GRID10 Cognitive Envelope heartbeat.

Default mode is observation-only. Regulator writes require explicit enablement and still
pass the existing policy/CAS/slew-rate gates. This module never executes external effects;
it only emits a next-action class and regulator proposals for the existing effect/executor
planes to consume through their own authority paths.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping

from grid10_cognitive_envelope_control_v1 import (
    AssuranceMode,
    DEFAULT_ENVELOPE_BANDS,
    EnvelopeStatus,
    LoopDescriptor,
    RegulatorCommand,
    build_loop_frame,
    evaluate_envelope,
    frame_to_json,
)
from grid10_cognitive_fabric_adapter_v1 import FabricTelemetry, TrustedAxisEvidence, collect_fabric_telemetry
from grid10_cognitive_regulator_port_v1 import CognitiveRegulatorPort


@dataclass(frozen=True)
class HeartbeatConfig:
    writer: str = "grid10-assurance-controller"
    writer_role: str = "ASSURANCE_CONTROLLER"
    max_regulator_writes_per_tick: int = 2
    allow_regulator_writes: bool = False


@dataclass(frozen=True)
class CognitiveTickResult:
    tick_id: str
    state_epoch: int
    assurance_mode: AssuranceMode
    next_action: str
    reasons: tuple[str, ...]
    regulator_proposals: tuple[Mapping[str, Any], ...]
    regulator_cycle: Mapping[str, Any] | None
    frame_json: str


class CognitiveHeartbeatStore:
    """Noncanonical checkpoint/telemetry store for restart continuity."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(self.path))
        try:
            con.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS ticks(
                  tick_id TEXT PRIMARY KEY,
                  state_epoch INTEGER NOT NULL,
                  assurance_mode TEXT NOT NULL,
                  next_action TEXT NOT NULL,
                  envelope_json TEXT NOT NULL,
                  frame_json TEXT NOT NULL,
                  regulator_cycle_json TEXT,
                  created_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
                """
            )
            con.commit()
        finally:
            con.close()

    def load_previous_projected(self) -> dict[str, float]:
        con = sqlite3.connect(str(self.path))
        try:
            row = con.execute("SELECT envelope_json FROM ticks ORDER BY created_ts DESC LIMIT 1").fetchone()
        finally:
            con.close()
        if not row:
            return {}
        try:
            body = json.loads(row[0])
        except ValueError:
            return {}
        out: dict[str, float] = {}
        for item in body.get("assessments", []):
            value = ((item.get("projected") or {}).get("value"))
            if value is not None:
                out[str(item.get("axis"))] = float(value)
        return out

    def append(self, result: CognitiveTickResult, envelope: Any) -> None:
        con = sqlite3.connect(str(self.path), timeout=5.0)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT OR REPLACE INTO ticks VALUES(?,?,?,?,?,?,?,?)",
                (
                    result.tick_id,
                    result.state_epoch,
                    result.assurance_mode.value,
                    result.next_action,
                    json.dumps(asdict(envelope), default=lambda x: getattr(x, "value", str(x)), sort_keys=True),
                    result.frame_json,
                    json.dumps(result.regulator_cycle, sort_keys=True) if result.regulator_cycle is not None else None,
                    time.time(),
                ),
            )
            con.execute(
                "INSERT INTO meta(k,v) VALUES('last_tick_id',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                (result.tick_id,),
            )
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def _status(snapshot: Any, axis: str) -> EnvelopeStatus | None:
    for a in snapshot.assessments:
        if a.axis == axis:
            return a.status
    return None


def _value(snapshot: Any, axis: str) -> float | None:
    for a in snapshot.assessments:
        if a.axis == axis:
            return a.projected.value
    return None


def select_next_action(snapshot: Any) -> str:
    """Choose only a cognitive action class; never performs the action."""
    if snapshot.assurance_mode == AssuranceMode.HOLD:
        return "HOLD"
    if snapshot.assurance_mode == AssuranceMode.CONTAINED:
        return "OBSERVE"
    epistemic = _status(snapshot, "epistemic_grounding")
    if epistemic in {EnvelopeStatus.SOFT_LOW, EnvelopeStatus.HARD_LOW, EnvelopeStatus.UNKNOWN}:
        return "SEARCH"
    uncertainty = _value(snapshot, "uncertainty_load")
    if uncertainty is not None and uncertainty > 0.65:
        return "SIMULATE"
    stagnation = _value(snapshot, "stagnation_pressure")
    if stagnation is not None and stagnation > 0.65:
        return "SEARCH"
    return "ACT_CANDIDATE"


def _bounded_target(port: CognitiveRegulatorPort, name: str, delta: float, config: HeartbeatConfig) -> RegulatorCommand:
    current = port.read(name)
    target = max(current.minimum, min(current.maximum, current.value_real + delta))
    if current.max_step is not None:
        target = max(current.value_real - current.max_step, min(current.value_real + current.max_step, target))
    return RegulatorCommand(
        name=name,
        requested_value=float(target),
        writer=config.writer,
        writer_role=config.writer_role,
        expected_version=current.version,
        reason="deterministic cognitive-envelope correction",
        provenance=("controller:GRID10_COGNITIVE_HEARTBEAT/v1",),
    )


def derive_regulator_commands(
    snapshot: Any,
    port: CognitiveRegulatorPort,
    *,
    config: HeartbeatConfig,
) -> tuple[RegulatorCommand, ...]:
    """Deterministic priority-ordered corrective proposals.

    Safety/authority corrections dominate epistemic/resource/cognitive optimization.
    A regulator appears at most once per tick.
    """
    proposals: list[tuple[int, str, float]] = []

    containment = _status(snapshot, "containment_margin")
    if containment in {EnvelopeStatus.SOFT_LOW, EnvelopeStatus.HARD_LOW, EnvelopeStatus.UNKNOWN}:
        proposals += [(0, "contain.external_action_concurrency", -1.0), (0, "contain.effect_risk_ceiling", -0.05)]

    goal_align = _status(snapshot, "goal_lineage_alignment")
    goal_drift = _status(snapshot, "goal_drift_rate")
    if goal_align in {EnvelopeStatus.SOFT_LOW, EnvelopeStatus.HARD_LOW, EnvelopeStatus.UNKNOWN} or goal_drift in {EnvelopeStatus.SOFT_HIGH, EnvelopeStatus.HARD_HIGH}:
        proposals += [(1, "goal.adoption_threshold", +0.10), (1, "goal.initiative_ceiling", -0.02)]

    epistemic = _status(snapshot, "epistemic_grounding")
    self_reinf = _status(snapshot, "self_reinforcement_ratio")
    if epistemic in {EnvelopeStatus.SOFT_LOW, EnvelopeStatus.HARD_LOW, EnvelopeStatus.UNKNOWN} or self_reinf in {EnvelopeStatus.SOFT_HIGH, EnvelopeStatus.HARD_HIGH}:
        proposals += [(2, "memory.counterevidence_quota", +0.10), (2, "goal.progress_evidence_min", +0.10)]

    resource = _status(snapshot, "resource_pressure")
    recovery = _status(snapshot, "recovery_margin")
    if resource in {EnvelopeStatus.SOFT_HIGH, EnvelopeStatus.HARD_HIGH} or recovery in {EnvelopeStatus.SOFT_LOW, EnvelopeStatus.HARD_LOW, EnvelopeStatus.UNKNOWN}:
        proposals += [(3, "cog.poll_intensity", -0.25), (3, "exec.max_parallel_work", -1.0)]

    reflection = _status(snapshot, "reflection_depth")
    if reflection in {EnvelopeStatus.SOFT_HIGH, EnvelopeStatus.HARD_HIGH}:
        proposals.append((4, "cog.max_reflection_rounds", -1.0))

    stagnation = _status(snapshot, "stagnation_pressure")
    if stagnation in {EnvelopeStatus.SOFT_HIGH, EnvelopeStatus.HARD_HIGH} and snapshot.assurance_mode == AssuranceMode.NORMAL:
        proposals += [(5, "cog.route_diversity_target", +0.10), (5, "cog.counterhypothesis_pressure", +0.10)]

    exploration = _value(snapshot, "exploration_pressure")
    if exploration is not None and snapshot.assurance_mode == AssuranceMode.NORMAL:
        if exploration < 0.20:
            proposals.append((6, "cog.temperature", +0.10))
        elif exploration > 0.85:
            proposals.append((6, "cog.temperature", -0.10))

    seen: set[str] = set()
    commands: list[RegulatorCommand] = []
    for _, name, delta in sorted(proposals, key=lambda x: (x[0], x[1])):
        if name in seen:
            continue
        seen.add(name)
        current = port.read(name)
        cmd = _bounded_target(port, name, delta, config)
        if abs(cmd.requested_value - current.value_real) < 1e-12:
            continue
        commands.append(cmd)
        if len(commands) >= config.max_regulator_writes_per_tick:
            break
    return tuple(commands)


class CognitiveHeartbeatRuntime:
    def __init__(self, fabric: Any, store: CognitiveHeartbeatStore, *, config: HeartbeatConfig = HeartbeatConfig()):
        self.fabric = fabric
        self.store = store
        self.config = config
        self.port = CognitiveRegulatorPort(
            fabric,
            max_writes_per_control_cycle=config.max_regulator_writes_per_tick,
        )

    def tick_once(
        self,
        *,
        tick_id: str,
        trusted_axes: Mapping[str, TrustedAxisEvidence] | None = None,
        extra_variables: Mapping[str, Any] | None = None,
    ) -> CognitiveTickResult:
        telemetry: FabricTelemetry = collect_fabric_telemetry(self.fabric, trusted_axes=trusted_axes)
        variables = dict(telemetry.variables)
        if extra_variables:
            variables.update(extra_variables)

        previous = self.store.load_previous_projected()
        snapshot = evaluate_envelope(
            tick_id=tick_id,
            state_epoch=telemetry.state_epoch,
            variables=variables,
            bands=DEFAULT_ENVELOPE_BANDS,
            previous_projected=previous,
        )
        next_action = select_next_action(snapshot)

        # Capture regulator readouts on the SAME pre-control basis epoch as the envelope.
        # Applied writes are represented separately in regulator_cycle and become input
        # state on the next tick; this avoids a mixed-epoch visual/control frame.
        regulator_view: dict[str, Mapping[str, Any]] = {}
        for logical in self.port.catalog:
            try:
                r = self.port.read(logical)
            except Exception:
                continue
            regulator_view[logical] = {
                "value": r.value_real,
                "version": r.version,
                "epoch": r.epoch,
                "writer": r.writer,
                "class": r.regulator_class,
                "minimum": r.minimum,
                "maximum": r.maximum,
            }

        commands = derive_regulator_commands(snapshot, self.port, config=self.config)
        cycle: Mapping[str, Any] | None = None
        if self.config.allow_regulator_writes and commands:
            raw = self.port.apply_control_cycle(
                control_epoch_id=tick_id,
                commands=commands,
                assurance_mode=snapshot.assurance_mode,
            )
            cycle = asdict(raw)
            cycle["assurance_mode"] = raw.assurance_mode.value

        loops = (
            LoopDescriptor("alignment", "MEASURE_CONTROL", 1.0, None, None, 1.0 if snapshot.assurance_mode == AssuranceMode.NORMAL else 0.5),
            LoopDescriptor("goal", "EVALUATE", 0.8, None, None, None),
            LoopDescriptor("memory", "RETRIEVE_PROJECT", 0.6, None, None, None),
            LoopDescriptor("hyperposition", "PRESERVE_SELECT", 0.7, None, None, None),
            LoopDescriptor("executor", next_action, 0.3 if next_action == "HOLD" else 0.8, None, None, None),
        )
        proposal_rows = tuple({
            "name": c.name,
            "requested_value": c.requested_value,
            "writer": c.writer,
            "writer_role": c.writer_role,
            "expected_version": c.expected_version,
            "reason": c.reason,
            "provenance": list(c.provenance),
        } for c in commands)

        work_view = dict(telemetry.work)
        work_view.update({
            "next_action": next_action,
            "regulator_write_enabled": self.config.allow_regulator_writes,
            "regulator_cycle": cycle,
        })
        frame = build_loop_frame(
            tick_id=tick_id,
            state_epoch=telemetry.state_epoch,
            assurance_mode=snapshot.assurance_mode,
            loops=loops,
            envelope=snapshot,
            regulators=regulator_view,
            hyperposition=telemetry.hyperposition,
            work=work_view,
            source_event_refs=telemetry.source_event_refs,
        )
        result = CognitiveTickResult(
            tick_id=tick_id,
            state_epoch=telemetry.state_epoch,
            assurance_mode=snapshot.assurance_mode,
            next_action=next_action,
            reasons=snapshot.reasons,
            regulator_proposals=proposal_rows,
            regulator_cycle=cycle,
            frame_json=frame_to_json(frame),
        )
        self.store.append(result, snapshot)
        return result


def append_frame_jsonl(path: Path, frame_json: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(json.loads(frame_json), sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def _trusted_normal_axes() -> dict[str, TrustedAxisEvidence]:
    """Explicit demo/test evidence only; never used unless CLI flag requests it."""
    from grid10_cognitive_envelope_control_v1 import ProjectionPolicy
    vals = {
        "authority_integrity": (1.0, ProjectionPolicy.PESSIMISTIC_MIN),
        "goal_lineage_alignment": (0.95, ProjectionPolicy.PESSIMISTIC_MIN),
        "goal_drift_rate": (0.02, ProjectionPolicy.PESSIMISTIC_MAX),
        "containment_margin": (0.90, ProjectionPolicy.PESSIMISTIC_MIN),
        "epistemic_grounding": (0.90, ProjectionPolicy.LOW_CONFIDENCE_BOUND),
        "self_reinforcement_ratio": (0.05, ProjectionPolicy.PESSIMISTIC_MAX),
        "resource_pressure": (0.20, ProjectionPolicy.PESSIMISTIC_MAX),
        "recovery_margin": (0.90, ProjectionPolicy.PESSIMISTIC_MIN),
    }
    return {
        k: TrustedAxisEvidence(k, v, "VERIFIED_TEST_FIXTURE", ("cli:trusted-normal-fixture",), 1.0, policy)
        for k, (v, policy) in vals.items()
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fabric", required=True)
    p.add_argument("--state-db", required=True)
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--ticks", type=int, default=1)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--forever", action="store_true")
    p.add_argument("--allow-regulator-writes", action="store_true")
    p.add_argument("--trusted-normal-test-fixture", action="store_true",
                   help="TEST/DEMO ONLY: supplies synthetic verified-normal semantic axes")
    args = p.parse_args()

    from grid10_fabric import Fabric
    fabric = Fabric(Path(args.fabric))
    store = CognitiveHeartbeatStore(Path(args.state_db))
    runtime = CognitiveHeartbeatRuntime(
        fabric,
        store,
        config=HeartbeatConfig(allow_regulator_writes=bool(args.allow_regulator_writes)),
    )
    trusted = _trusted_normal_axes() if args.trusted_normal_test_fixture else None
    i = 0
    while args.forever or i < max(0, args.ticks):
        tick_id = f"heartbeat-{int(time.time()*1000)}-{i}"
        result = runtime.tick_once(tick_id=tick_id, trusted_axes=trusted)
        append_frame_jsonl(Path(args.frames_jsonl), result.frame_json)
        print(json.dumps({
            "tick_id": result.tick_id,
            "state_epoch": result.state_epoch,
            "assurance_mode": result.assurance_mode.value,
            "next_action": result.next_action,
            "reasons": result.reasons,
            "regulator_proposals": result.regulator_proposals,
            "regulator_cycle": result.regulator_cycle,
        }, sort_keys=True))
        i += 1
        if args.forever or i < args.ticks:
            time.sleep(max(0.05, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
