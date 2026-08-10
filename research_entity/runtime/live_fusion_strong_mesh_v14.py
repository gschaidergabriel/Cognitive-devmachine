from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from live_fusion_reentry_v13 import (
    DELIVERY_CHECKPOINT,
    DELIVERY_INDEX,
    DELIVERY_INTERRUPT,
    LiveDelta,
    LiveFusionBus as V13Bus,
    WorkerView,
)


@dataclass(frozen=True)
class DependencyProjection:
    """Derived, non-authoritative dependency closure for one worker subscription.

    The projection is disposable ClayGraph/UnifiedDB-derived routing support. It never grants
    truth or effect authority. A projection that is not current is ignored for upgrades.
    """

    worker_id: str
    graph_epoch: str
    state_hash: str
    semantic_keys: tuple[str, ...] = ()
    work_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    current: bool = True

    def normalized(self) -> "DependencyProjection":
        if not self.worker_id or not self.graph_epoch or not self.state_hash:
            raise ValueError("worker_id, graph_epoch and state_hash are required")
        return DependencyProjection(
            worker_id=self.worker_id,
            graph_epoch=self.graph_epoch,
            state_hash=self.state_hash,
            semantic_keys=tuple(sorted(set(self.semantic_keys))),
            work_ids=tuple(sorted(set(self.work_ids))),
            claim_ids=tuple(sorted(set(self.claim_ids))),
            provenance_refs=tuple(sorted(set(self.provenance_refs))),
            current=self.current,
        )


@dataclass(frozen=True)
class ShadowRouteDecision:
    event_id: str
    worker_id: str
    base_class: str
    base_relevance: float
    candidate_class: str
    candidate_relevance: float
    direct_branch: tuple[str, ...]
    direct_keys: tuple[str, ...]
    direct_work: tuple[str, ...]
    direct_claims: tuple[str, ...]
    dependency_keys: tuple[str, ...]
    dependency_work: tuple[str, ...]
    dependency_claims: tuple[str, ...]
    projection_epoch: str
    projection_state_hash: str
    projection_used: bool
    change: str
    reason: str
    authority: str = "SHADOW_ROUTING_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY"


class StrongMeshShadowRouter:
    """Shadow-only V1.4 routing planner layered on the V1.3 causal transport.

    Stronger networking means more causal reach at lower irrelevant active-delivery density:
    - exact work/claim/key routes remain first-class;
    - current dependency closures can rescue cross-branch hidden dependencies;
    - low-impact, low-urgency branch-only chatter can be demoted to INDEX_ONLY;
    - no routing change becomes live here; the result is a shadow decision for validation.
    """

    def __init__(
        self,
        *,
        checkpoint_min: float = 0.35,
        interrupt_min: float = 0.45,
        low_signal_max: float = 0.35,
    ):
        for value, name in (
            (checkpoint_min, "checkpoint_min"),
            (interrupt_min, "interrupt_min"),
            (low_signal_max, "low_signal_max"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0,1]")
        self.checkpoint_min = checkpoint_min
        self.interrupt_min = interrupt_min
        self.low_signal_max = low_signal_max

    @staticmethod
    def _base_class(delta: LiveDelta, relevance: float) -> str:
        if relevance == 0.0 or delta.applicability == "HISTORICALLY_VALID_ONLY":
            return DELIVERY_INDEX
        if delta.conflict and delta.impact >= 0.70 and relevance >= 0.45:
            return DELIVERY_INTERRUPT
        return DELIVERY_CHECKPOINT

    @staticmethod
    def _sets(delta: LiveDelta, worker: WorkerView):
        return (
            set(delta.affected_branches) & set(worker.branches),
            set(delta.semantic_keys) & set(worker.active_keys),
            set(delta.affected_work) & set(worker.active_work),
            set(delta.affected_claims) & set(worker.active_claims),
        )

    def plan(
        self,
        delta: LiveDelta,
        worker: WorkerView,
        projection: DependencyProjection | None = None,
    ) -> ShadowRouteDecision:
        delta = delta.normalized()
        worker = worker.normalized()
        direct_branch, direct_keys, direct_work, direct_claims = self._sets(delta, worker)
        base_relevance, _ = V13Bus._score(delta, worker)
        base_class = self._base_class(delta, base_relevance)

        dep_keys: set[str] = set()
        dep_work: set[str] = set()
        dep_claims: set[str] = set()
        projection_epoch = "NONE"
        projection_state_hash = "NONE"
        projection_used = False

        if projection is not None:
            projection = projection.normalized()
            projection_epoch = projection.graph_epoch
            projection_state_hash = projection.state_hash
            if projection.worker_id != worker.worker_id:
                raise ValueError("dependency projection worker mismatch")
            if projection.current:
                projection_used = True
                dep_keys = set(delta.semantic_keys) & set(projection.semantic_keys)
                dep_work = set(delta.affected_work) & set(projection.work_ids)
                dep_claims = set(delta.affected_claims) & set(projection.claim_ids)

        overlap = min(
            1.0,
            0.30 * bool(direct_branch)
            + 0.40 * bool(direct_keys)
            + 0.45 * bool(direct_work)
            + 0.45 * bool(direct_claims)
            + 0.45 * bool(dep_keys)
            + 0.55 * bool(dep_work)
            + 0.55 * bool(dep_claims),
        )
        candidate_relevance = min(
            1.0,
            0.45 * overlap + 0.35 * delta.impact + 0.20 * delta.urgency,
        ) if overlap else 0.0

        has_dependency = bool(dep_keys or dep_work or dep_claims)
        has_direct_semantic = bool(direct_keys or direct_work or direct_claims)
        branch_only = bool(direct_branch) and not has_direct_semantic and not has_dependency
        low_signal_branch_only = (
            branch_only
            and not delta.conflict
            and delta.impact <= self.low_signal_max
            and delta.urgency <= self.low_signal_max
        )

        if delta.applicability == "HISTORICALLY_VALID_ONLY":
            candidate_class = DELIVERY_INDEX
        elif delta.conflict and delta.impact >= 0.70 and candidate_relevance >= self.interrupt_min:
            candidate_class = DELIVERY_INTERRUPT
        elif low_signal_branch_only:
            candidate_class = DELIVERY_INDEX
        elif (direct_work or direct_claims or dep_work or dep_claims) and candidate_relevance > 0.0:
            candidate_class = DELIVERY_CHECKPOINT
        elif candidate_relevance >= self.checkpoint_min:
            candidate_class = DELIVERY_CHECKPOINT
        else:
            candidate_class = DELIVERY_INDEX

        if candidate_class == base_class:
            change = "UNCHANGED"
        elif base_class == DELIVERY_INDEX and candidate_class != DELIVERY_INDEX:
            change = "UPGRADED_DEPENDENCY_REACH" if has_dependency else "UPGRADED"
        elif base_class != DELIVERY_INDEX and candidate_class == DELIVERY_INDEX:
            change = "DEMOTED_LOW_SIGNAL"
        elif base_class == DELIVERY_CHECKPOINT and candidate_class == DELIVERY_INTERRUPT:
            change = "UPGRADED_INTERRUPT"
        else:
            change = "CHANGED"

        reason = (
            f"direct(branch={sorted(direct_branch)},keys={sorted(direct_keys)},work={sorted(direct_work)},"
            f"claims={sorted(direct_claims)}); dependency(keys={sorted(dep_keys)},work={sorted(dep_work)},"
            f"claims={sorted(dep_claims)}); impact={delta.impact:.2f}; urgency={delta.urgency:.2f}; "
            f"projection_used={projection_used}"
        )
        return ShadowRouteDecision(
            event_id=delta.event_id,
            worker_id=worker.worker_id,
            base_class=base_class,
            base_relevance=base_relevance,
            candidate_class=candidate_class,
            candidate_relevance=candidate_relevance,
            direct_branch=tuple(sorted(direct_branch)),
            direct_keys=tuple(sorted(direct_keys)),
            direct_work=tuple(sorted(direct_work)),
            direct_claims=tuple(sorted(direct_claims)),
            dependency_keys=tuple(sorted(dep_keys)),
            dependency_work=tuple(sorted(dep_work)),
            dependency_claims=tuple(sorted(dep_claims)),
            projection_epoch=projection_epoch,
            projection_state_hash=projection_state_hash,
            projection_used=projection_used,
            change=change,
            reason=reason,
        )

    @staticmethod
    def summarize(decisions: Iterable[ShadowRouteDecision]) -> dict[str, int]:
        rows = list(decisions)
        return {
            "rows": len(rows),
            "upgraded_dependency_reach": sum(r.change == "UPGRADED_DEPENDENCY_REACH" for r in rows),
            "upgraded_interrupt": sum(r.change == "UPGRADED_INTERRUPT" for r in rows),
            "demoted_low_signal": sum(r.change == "DEMOTED_LOW_SIGNAL" for r in rows),
            "unchanged": sum(r.change == "UNCHANGED" for r in rows),
            "base_active": sum(r.base_class != DELIVERY_INDEX for r in rows),
            "candidate_active": sum(r.candidate_class != DELIVERY_INDEX for r in rows),
            "base_interrupt": sum(r.base_class == DELIVERY_INTERRUPT for r in rows),
            "candidate_interrupt": sum(r.candidate_class == DELIVERY_INTERRUPT for r in rows),
        }
