#!/usr/bin/env python3
"""Policy-aware compatibility port for GRID10 cognitive regulators.

Research-candidate integration skeleton. This file does not create a new authority
surface. It adapts logical cognitive regulator names to the existing CAS-safe GRID10
Fabric regulator primitive and deliberately assumes a SINGLE authorized control writer
per control epoch. Authentication/authority admission of that writer belongs upstream.

The existing physical names `temperature`, `top_p`, and `poll_intensity` are preserved
for compatibility with current grid10_node.py. New logical regulator names may use their
logical name as the physical row until a more compact ABI is frozen.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from grid10_cognitive_envelope_control_v1 import (
    AssuranceMode,
    DEFAULT_REGULATOR_CATALOG,
    RegulatorCommand,
    RegulatorDecision,
    RegulatorSpec,
    validate_regulator_command,
)


PHYSICAL_BINDINGS: dict[str, str] = {
    "cog.temperature": "temperature",
    "cog.top_p": "top_p",
    "cog.poll_intensity": "poll_intensity",
}


@dataclass(frozen=True)
class RegulatorReadout:
    logical_name: str
    physical_name: str
    value_real: float
    version: int
    epoch: int
    writer: str | None
    ts_ms: float | None
    regulator_class: str
    minimum: float
    maximum: float
    max_step: float | None


@dataclass(frozen=True)
class AppliedRegulatorWrite:
    logical_name: str
    physical_name: str
    accepted: bool
    reason: str
    before: Mapping[str, Any]
    after: Mapping[str, Any] | None


@dataclass(frozen=True)
class ControlCycleResult:
    control_epoch_id: str
    assurance_mode: AssuranceMode
    requested: int
    applied: int
    rejected: int
    writes: tuple[AppliedRegulatorWrite, ...]


class CognitiveRegulatorPort:
    """Thin policy layer over an existing grid10_fabric.Fabric instance.

    The Fabric object is intentionally duck-typed so this module can later be tested
    against a deterministic fake without loading a model or touching the target runtime.
    Expected methods:
        get_regulator(name, default=...)
        set_regulator(name, value_real, writer=..., expected_version=...)
    """

    def __init__(
        self,
        fabric: Any,
        *,
        catalog: Mapping[str, RegulatorSpec] = DEFAULT_REGULATOR_CATALOG,
        physical_bindings: Mapping[str, str] = PHYSICAL_BINDINGS,
        max_writes_per_control_cycle: int = 4,
    ) -> None:
        if max_writes_per_control_cycle < 1:
            raise ValueError("max_writes_per_control_cycle must be >=1")
        self.fabric = fabric
        self.catalog = dict(catalog)
        self.physical_bindings = dict(physical_bindings)
        self.max_writes_per_control_cycle = int(max_writes_per_control_cycle)

    def physical_name(self, logical_name: str) -> str:
        return self.physical_bindings.get(logical_name, logical_name)

    def read(self, logical_name: str) -> RegulatorReadout:
        spec = self.catalog.get(logical_name)
        if spec is None:
            raise KeyError(f"unknown logical regulator: {logical_name}")
        physical = self.physical_name(logical_name)
        row = self.fabric.get_regulator(physical, default=spec.default)
        if row is None:
            raise RuntimeError(f"fabric returned no row/default for {physical}")
        return RegulatorReadout(
            logical_name=logical_name,
            physical_name=physical,
            value_real=float(row["value_real"]),
            version=int(row["version"]),
            epoch=int(row["epoch"]),
            writer=row.get("writer"),
            ts_ms=row.get("ts_ms"),
            regulator_class=spec.regulator_class,
            minimum=spec.minimum,
            maximum=spec.maximum,
            max_step=spec.max_step,
        )

    def validate(self, command: RegulatorCommand, assurance_mode: AssuranceMode) -> tuple[RegulatorReadout, RegulatorDecision]:
        current = self.read(command.name)
        decision = validate_regulator_command(
            command,
            current_value=current.value_real,
            current_version=current.version,
            assurance_mode=assurance_mode,
            catalog=self.catalog,
        )
        return current, decision

    def apply_one(self, command: RegulatorCommand, assurance_mode: AssuranceMode) -> AppliedRegulatorWrite:
        """Apply one policy-validated CAS write.

        The caller must already own the single control-writer role for this control
        epoch. This method never infers or grants that ownership from command fields.
        """
        before, decision = self.validate(command, assurance_mode)
        before_dict = asdict(before)
        if not decision.accepted:
            return AppliedRegulatorWrite(
                logical_name=command.name,
                physical_name=before.physical_name,
                accepted=False,
                reason=decision.reason,
                before=before_dict,
                after=None,
            )

        try:
            after = self.fabric.set_regulator(
                before.physical_name,
                float(decision.clamped_value),
                writer=command.writer,
                expected_version=before.version,
            )
        except Exception as exc:  # FabricError intentionally not imported here
            return AppliedRegulatorWrite(
                logical_name=command.name,
                physical_name=before.physical_name,
                accepted=False,
                reason=f"FABRIC_WRITE_REJECTED:{type(exc).__name__}:{exc}",
                before=before_dict,
                after=None,
            )

        return AppliedRegulatorWrite(
            logical_name=command.name,
            physical_name=before.physical_name,
            accepted=True,
            reason="ACCEPTED_POLICY_AND_FABRIC_CAS",
            before=before_dict,
            after=dict(after),
        )

    def apply_control_cycle(
        self,
        *,
        control_epoch_id: str,
        commands: Sequence[RegulatorCommand],
        assurance_mode: AssuranceMode,
    ) -> ControlCycleResult:
        """Apply a bounded number of sequential regulator writes for one control cycle.

        This is deliberately NOT a multi-writer fan-out. It serializes writes through
        one port instance and rejects command bursts above a small configured budget.
        A future Fabric batch-CAS transaction may replace the sequential writes once
        measured contention justifies it.
        """
        if not control_epoch_id.strip():
            raise ValueError("control_epoch_id is required")
        if len(commands) > self.max_writes_per_control_cycle:
            writes = tuple(
                AppliedRegulatorWrite(
                    logical_name=c.name,
                    physical_name=self.physical_name(c.name),
                    accepted=False,
                    reason="CONTROL_CYCLE_WRITE_BUDGET_EXCEEDED",
                    before={},
                    after=None,
                )
                for c in commands
            )
            return ControlCycleResult(
                control_epoch_id=control_epoch_id,
                assurance_mode=assurance_mode,
                requested=len(commands),
                applied=0,
                rejected=len(commands),
                writes=writes,
            )

        writes = tuple(self.apply_one(c, assurance_mode) for c in commands)
        return ControlCycleResult(
            control_epoch_id=control_epoch_id,
            assurance_mode=assurance_mode,
            requested=len(commands),
            applied=sum(1 for w in writes if w.accepted),
            rejected=sum(1 for w in writes if not w.accepted),
            writes=writes,
        )
