from __future__ import annotations

"""Bounded final-state Pulse effectivizer for UnifiedDB SPM research.

This module is a PREPROCESSOR candidate, not a database and not semantic truth.
It may combine multiple authoritative Pulse notifications only when the caller proves
there is no intermediate observation requirement and each event is explicitly safe for
final-state projection maintenance. Raw authoritative events must remain preserved elsewhere.

Important identity rule: content-fingerprint A->B->A is not assumed to be a projection
identity no-op. SPM-S1 segments can contain versioned target_record_id values, so a logical
identity touched during a read-free batch remains an invalidation/recompute input unless a
future explicit identity-stability witness proves otherwise. Net-zero chains are still
reported as content cancellations, but their logical ids and impact seeds are conservatively
preserved for the one final coherent projection generation.

The module never grants truth, GWT, model, tool, or effect authority.
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
    # Projection invalidation identities: every logical id touched by the raw batch.
    # This intentionally includes content-fingerprint net-zero / ABA chains.
    changed_logical_ids: tuple[str, ...]
    # Conservative projection impact closure across every raw event in the batch.
    impact_seed_ids: tuple[str, ...]
    # Content-level net-zero chains. This is diagnostic/compression information only;
    # it is not permission to erase identity/provenance invalidation.
    cancelled_logical_ids: tuple[str, ...]
    raw_event_count: int
    # Number of logical ids whose final content fingerprint differs from batch entry.
    effective_change_count: int
    raw_impact_mentions: int
    # Number of distinct seeds that must be considered for the final projection.
    effective_impact_count: int
    impact_complete: bool
    # Retained for receipt compatibility. With identity-touch preservation, a non-empty
    # event batch always has at least one changed logical identity for SPM-S1 publication.
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

    Fingerprint cancellation is content-level only. Every touched logical id and every
    declared impact seed remains in the projection plan because current SPM-S1 segments may
    encode versioned record identity/provenance even when final content bytes return to the
    same fingerprint. This avoids an ABA-style stale-segment reuse bug while still allowing
    one coherent generation-map publication for the whole read-free batch.
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

    touched_ids = sorted(chains)
    net_changed_ids: list[str] = []
    cancelled_ids: list[str] = []
    projection_seeds: set[str] = set()
    for logical_id, chain in sorted(chains.items()):
        before, after, seeds = chain
        # Always preserve the seed invalidation footprint of a touched identity. Content
        # equality does not prove target_record_id / provenance / version identity equality.
        projection_seeds.update(seeds)  # type: ignore[arg-type]
        if before == after:
            cancelled_ids.append(logical_id)
        else:
            net_changed_ids.append(logical_id)

    return EffectivizedPulsePlan(
        batch_id=batch_id,
        member_event_ids=tuple(event.event_id for event in events),
        from_source_epoch=events[0].from_source_epoch,
        to_source_epoch=events[-1].to_source_epoch,
        from_graph_epoch=events[0].from_graph_epoch,
        to_graph_epoch=events[-1].to_graph_epoch,
        changed_logical_ids=tuple(touched_ids),
        impact_seed_ids=tuple(sorted(projection_seeds)),
        cancelled_logical_ids=tuple(cancelled_ids),
        raw_event_count=len(events),
        effective_change_count=len(net_changed_ids),
        raw_impact_mentions=raw_impact_mentions,
        effective_impact_count=len(projection_seeds),
        impact_complete=impact_complete,
        metadata_only_epoch_advance_required=False,
    )


def to_spm_s1_plan(plan: EffectivizedPulsePlan):
    """Translate an effectivized batch into the existing SPM-S1 PulsePlan.

    Net-zero content chains remain changed logical identities for projection invalidation,
    so the current SPM-S1 API can publish the final epoch without inventing a fake change or
    silently reusing an ABA-stale versioned segment.
    """
    if plan.metadata_only_epoch_advance_required:
        raise PulseEffectivizationError(
            "identity-safe effectivization unexpectedly produced metadata-only publication"
        )
    if not plan.changed_logical_ids:
        raise PulseEffectivizationError("effectivized batch lost all logical identity touches")

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
