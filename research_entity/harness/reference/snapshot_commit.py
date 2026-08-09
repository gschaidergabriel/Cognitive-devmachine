"""FRANK H1 cognitive-snapshot -> fresh-commit revalidation reference.

This module does not execute external effects and never mints authority. It models the
semantic barrier between a bounded cognitive snapshot/ActiveAssembly and the later
runtime effect gateway. The gateway must still require a runtime-minted opaque
capability handle before reserve/commit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import hashlib
import json


class CommitBarrierError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class DependencyVersion:
    key: str
    version: int

    def __post_init__(self) -> None:
        if not self.key:
            raise CommitBarrierError("EMPTY_DEPENDENCY_KEY")
        if self.version < 0:
            raise CommitBarrierError("NEGATIVE_DEPENDENCY_VERSION")


@dataclass(frozen=True)
class CognitiveSnapshot:
    snapshot_epoch: int
    assembly_sha256: str
    dependency_versions: tuple[DependencyVersion, ...]
    capability_epoch: int

    def __post_init__(self) -> None:
        if self.snapshot_epoch < 0 or self.capability_epoch < 0:
            raise CommitBarrierError("NEGATIVE_EPOCH")
        if not self.assembly_sha256:
            raise CommitBarrierError("MISSING_ASSEMBLY_HASH")
        keys = [d.key for d in self.dependency_versions]
        if len(keys) != len(set(keys)):
            raise CommitBarrierError("DUPLICATE_DEPENDENCY")


@dataclass(frozen=True)
class EffectIntent:
    intent_id: str
    effect_kind: str
    payload_sha256: str
    relevant_dependencies: tuple[str, ...]
    required_capability_kind: str

    def __post_init__(self) -> None:
        if not self.intent_id or not self.effect_kind or not self.payload_sha256:
            raise CommitBarrierError("INCOMPLETE_EFFECT_INTENT")
        if not self.required_capability_kind:
            raise CommitBarrierError("MISSING_CAPABILITY_KIND")
        if len(self.relevant_dependencies) != len(set(self.relevant_dependencies)):
            raise CommitBarrierError("DUPLICATE_RELEVANT_DEPENDENCY")


@dataclass(frozen=True)
class CommitGuardDecision:
    status: str
    snapshot_epoch: int
    commit_epoch: int
    changed_relevant_dependencies: tuple[str, ...]
    missing_snapshot_dependencies: tuple[str, ...]
    capability_epoch_changed: bool
    preconditions_valid: bool
    effect_eligible_for_runtime_gateway: bool
    authority: str
    guard_sha256: str


def capture_cognitive_snapshot(
    *,
    snapshot_epoch: int,
    assembly_sha256: str,
    dependency_versions: Mapping[str, int],
    capability_epoch: int,
) -> CognitiveSnapshot:
    deps = tuple(
        sorted(
            (DependencyVersion(k, int(v)) for k, v in dependency_versions.items()),
            key=lambda d: d.key,
        )
    )
    return CognitiveSnapshot(snapshot_epoch, assembly_sha256, deps, capability_epoch)


def _guard_hash(payload: dict) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def revalidate_for_fresh_commit(
    snapshot: CognitiveSnapshot,
    intent: EffectIntent,
    *,
    commit_epoch: int,
    current_dependency_versions: Mapping[str, int],
    current_capability_epoch: int,
) -> CommitGuardDecision:
    """Validate only effect-relevant cognitive dependencies before runtime authority.

    A changed global epoch alone is not a reason to abort. A relevant dependency change,
    capability-epoch change, or dependency introduced after the cognitive snapshot is.
    The returned decision has authority NONE: it can only admit the intent to the
    separate runtime capability gateway.
    """
    if commit_epoch < snapshot.snapshot_epoch:
        raise CommitBarrierError("COMMIT_EPOCH_PRECEDES_SNAPSHOT")

    snap = {d.key: d.version for d in snapshot.dependency_versions}
    relevant = tuple(sorted(intent.relevant_dependencies))
    missing = tuple(k for k in relevant if k not in snap)
    changed = tuple(
        k
        for k in relevant
        if k in snap and current_dependency_versions.get(k) != snap[k]
    )
    capability_changed = current_capability_epoch != snapshot.capability_epoch

    if missing:
        status = "REASSEMBLE_REQUIRED_MISSING_DEPENDENCY"
    elif capability_changed:
        status = "REVALIDATION_CONFLICT_CAPABILITY_EPOCH"
    elif changed:
        status = "REVALIDATION_CONFLICT_DEPENDENCY"
    else:
        status = "PRECONDITIONS_VALID"

    valid = status == "PRECONDITIONS_VALID"
    core = {
        "schema": "frank.commit-guard.v0",
        "intent_id": intent.intent_id,
        "effect_kind": intent.effect_kind,
        "payload_sha256": intent.payload_sha256,
        "required_capability_kind": intent.required_capability_kind,
        "assembly_sha256": snapshot.assembly_sha256,
        "snapshot_epoch": snapshot.snapshot_epoch,
        "commit_epoch": commit_epoch,
        "relevant_dependencies": relevant,
        "changed_relevant_dependencies": changed,
        "missing_snapshot_dependencies": missing,
        "capability_epoch_changed": capability_changed,
        "status": status,
        "preconditions_valid": valid,
        "effect_eligible_for_runtime_gateway": valid,
        "authority": "NONE",
    }
    return CommitGuardDecision(
        status=status,
        snapshot_epoch=snapshot.snapshot_epoch,
        commit_epoch=commit_epoch,
        changed_relevant_dependencies=changed,
        missing_snapshot_dependencies=missing,
        capability_epoch_changed=capability_changed,
        preconditions_valid=valid,
        effect_eligible_for_runtime_gateway=valid,
        authority="NONE",
        guard_sha256=_guard_hash(core),
    )


__all__ = [
    "CommitBarrierError",
    "DependencyVersion",
    "CognitiveSnapshot",
    "EffectIntent",
    "CommitGuardDecision",
    "capture_cognitive_snapshot",
    "revalidate_for_fresh_commit",
]
