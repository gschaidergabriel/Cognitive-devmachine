from __future__ import annotations

"""Bounded final-state Pulse effectivizer for UnifiedDB SPM research.

This module is a PREPROCESSOR candidate, not a database and not semantic truth.
It may combine multiple authoritative Pulse notifications only when the caller proves
there is no intermediate observation requirement and each event is explicitly safe for
final-state projection maintenance. Raw authoritative events must remain preserved elsewhere.

The effectivizer composes per-logical-id before/after fingerprints, cancels exact net-zero
chains, unions impact seeds for remaining changes, and exposes an adapter to the existing
SPM-S1 PulsePlan. It never grants truth, GWT, model, tool, or effect authority.
"""

from dataclasses import dataclass

SAFE_FINAL_STATE_CHANGE_CLASSES = frozenset({
    "VALUE_UPDATE",
    "STATUS_UPDATE",
    "EDGE_WEIGHT_UPDATE",
    "EDGE_REMOVE",
    "LOCAL_REWRITE",
})

AUTHORITY = "PROJECTION_FINAL_STATE_PREPROCESSOR_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY"


class PulseEffectivizationError(ValueError):
    pass


@dataclass(frozen=True)
class PulseDeltaEvent:
    event_id: str
    change_class: str
    from_source_epoch: int
    to_source_epoch: int
    from_graph_epoch: int
    to_graph_epoch: int
    changed_logical_id: str
    before_fingerprint: str
    after_fingerprint: str
    impact_seed_ids: tuple[str, ...]
    impact_complete: bool = True
    final_state_projection_safe: bool = True
    intermediate_observation_required: bool = False


@dataclass(frozen=True)
class EffectivizedPulsePlan:
    batch_id: str
    member_event_ids: tuple[str, ...]
    from_source_epoch: int
    to_source_epoch: int
    from_graph_epoch: int
    to_graph_epoch: int
    changed_logical_ids: tuple[str, ...]
    impact_seed_ids: tuple[str, ...]
    cancelled_logical_ids: tuple[str, ...]
    raw_event_count: int
    effective_change_count: int
    raw_impact_mentions: int
    effective_impact_count: int
    impact_complete: bool
    metadata_only_epoch_advance_required: bool
    authority: str = AUTHORITY

    @property
    def event_compression_ratio(self) -> float:
        if self.raw_event_count == 0:
            return 1.0
        return self.effective_change_count / self.raw_event_count


def _validate_epoch_pair(name: str, before: int, after: int) -> None:
    for value in (before, after):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PulseEffectivizationError(f"{name} epochs must be non-negative ints")
    if after < before:
        raise PulseEffectivizationError(f"{name} epoch regressed")


def effectivize_pulse_batch(
    batch_id: str,
    events: tuple[PulseDeltaEvent, ...] | list[PulseDeltaEvent],
) -> EffectivizedPulsePlan:
    """Compose a read-free sequence of safe projection notifications into final-state work.

    Strictness is intentional. Any uncertainty falls back to sequential SPM-S1 outside this
    helper. The function does not mutate UnifiedDB and does not delete raw event history.
    """
    events = tuple(events)
    if not batch_id:
        raise PulseEffectivizationError("batch_id is required")
    if not events:
        raise PulseEffectivizationError("at least one event is required")

    seen_event_ids: set[str] = set()
    chains: dict[str, list[object]] = {}
    raw_impact_mentions = 0
    impact_complete = True
    previous_source_epoch: int | None = None
    previous_graph_epoch: int | None = None

    for event in events:
        if not event.event_id or event.event_id in seen_event_ids:
            raise PulseEffectivizationError("event ids must be non-empty and unique")
        seen_event_ids.add(event.event_id)
        if not event.changed_logical_id:
            raise PulseEffectivizationError("changed_logical_id is required")
        if event.change_class not in SAFE_FINAL_STATE_CHANGE_CLASSES:
            raise PulseEffectivizationError("change class is not final-state effectivization safe")
        if not event.final_state_projection_safe or event.intermediate_observation_required:
            raise PulseEffectivizationError("event requires sequential publication")
        if not event.before_fingerprint or not event.after_fingerprint:
            raise PulseEffectivizationError("before/after fingerprints are required")

        _validate_epoch_pair("source", event.from_source_epoch, event.to_source_epoch)
        _validate_epoch_pair("graph", event.from_graph_epoch, event.to_graph_epoch)
        if (
            event.to_source_epoch == event.from_source_epoch
            and event.to_graph_epoch == event.from_graph_epoch
        ):
            raise PulseEffectivizationError("event must advance source or graph epoch")
        if previous_source_epoch is not None:
            if event.from_source_epoch != previous_source_epoch:
                raise PulseEffectivizationError("source epochs are not contiguous")
            if event.from_graph_epoch != previous_graph_epoch:
                raise PulseEffectivizationError("graph epochs are not contiguous")
        previous_source_epoch = event.to_source_epoch
        previous_graph_epoch = event.to_graph_epoch

        seeds = set(event.impact_seed_ids)
        if any(not seed for seed in seeds):
            raise PulseEffectivizationError("impact seed ids must be non-empty")
        raw_impact_mentions += len(seeds)
        impact_complete = impact_complete and event.impact_complete

        chain = chains.get(event.changed_logical_id)
        if chain is None:
            chains[event.changed_logical_id] = [
                event.before_fingerprint,
                event.after_fingerprint,
                seeds,
            ]
        else:
            if chain[1] != event.before_fingerprint:
                raise PulseEffectivizationError("non-composable fingerprint lineage")
            chain[1] = event.after_fingerprint
            chain[2].update(seeds)  # type: ignore[union-attr]

    effective_ids: list[str] = []
    cancelled_ids: list[str] = []
    effective_seeds: set[str] = set()
    for logical_id, chain in sorted(chains.items()):
        before, after, seeds = chain
        if before == after:
            cancelled_ids.append(logical_id)
        else:
            effective_ids.append(logical_id)
            effective_seeds.update(seeds)  # type: ignore[arg-type]

    return EffectivizedPulsePlan(
        batch_id=batch_id,
        member_event_ids=tuple(event.event_id for event in events),
        from_source_epoch=events[0].from_source_epoch,
        to_source_epoch=events[-1].to_source_epoch,
        from_graph_epoch=events[0].from_graph_epoch,
        to_graph_epoch=events[-1].to_graph_epoch,
        changed_logical_ids=tuple(effective_ids),
        impact_seed_ids=tuple(sorted(effective_seeds)),
        cancelled_logical_ids=tuple(cancelled_ids),
        raw_event_count=len(events),
        effective_change_count=len(effective_ids),
        raw_impact_mentions=raw_impact_mentions,
        effective_impact_count=len(effective_seeds),
        impact_complete=impact_complete,
        metadata_only_epoch_advance_required=not effective_ids,
    )


def to_spm_s1_plan(plan: EffectivizedPulsePlan):
    """Translate a non-empty effectivized batch into the existing SPM-S1 PulsePlan.

    A fully cancelled batch cannot be adapted safely yet because SPM-S1 has no metadata-only
    epoch-advance primitive. That gap is intentionally surfaced instead of minting a fake change.
    """
    if plan.metadata_only_epoch_advance_required:
        raise PulseEffectivizationError(
            "SPM-S1 lacks metadata-only epoch advance for a fully cancelled batch"
        )
    from semantic_access_pulse_v12 import PulsePlan

    return PulsePlan(
        event_id=plan.batch_id,
        change_class="LOCAL_REWRITE",
        changed_logical_ids=plan.changed_logical_ids,
        impact_seed_ids=plan.impact_seed_ids,
        impact_complete=plan.impact_complete,
        to_source_epoch=plan.to_source_epoch,
        to_graph_epoch=plan.to_graph_epoch,
    )
