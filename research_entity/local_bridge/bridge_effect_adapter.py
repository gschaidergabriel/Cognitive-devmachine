#!/usr/bin/env python3
"""Candidate adapter binding existing local bridge commands to HostEffectFence.

This module is deliberately narrow. It does not replace either bridge daemon,
Git fabric, receipt format, or canonical EffectGate/EffectJournal. It only
normalizes one missing physical-host coordination boundary so both current
bridge implementations can share the same HostEffectFence contract.

Promotion law:
- intrinsically read-only operations may be inferred READ_ONLY for legacy
  compatibility;
- arbitrary exec/write/git/tmux/screenshot operations are never silently
  inferred read-only;
- SCRATCH_ONLY requires explicit scratch_root + touched_paths;
- LIVE_MUTATION/SYSTEM_MUTATION require explicit classification and are not
  considered successful merely because the effect body returned;
- exact command bytes determine command_sha256;
- independent readback is required before VERIFIED_SUCCEEDED.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from host_effect_fence import (
    EffectClass,
    EffectTicket,
    HostEffectFence,
    PathHashPrecondition,
)


class BridgeEffectAdapterError(RuntimeError):
    pass


class EffectClassificationRequired(BridgeEffectAdapterError):
    pass


class EffectClassificationConflict(BridgeEffectAdapterError):
    pass


class EffectBodyNonzero(BridgeEffectAdapterError):
    def __init__(self, result: Any):
        self.result = result
        super().__init__(f"effect body returned nonzero rc={getattr(result, 'returncode', None)!r}")


@dataclass(frozen=True)
class Verification:
    outcome_sha256: str
    note: str


@dataclass(frozen=True)
class GuardedExecution:
    command_id: str
    command_sha256: str
    effect_class: EffectClass
    ticket: EffectTicket
    body_result: Any | None
    outcome: str


# These operations are read-only by implementation contract in both observed
# bridge families (or the relevant daemon simply lacks the op). Everything
# else requires explicit effect_class so legacy exec cannot masquerade as read.
INTRINSIC_READ_ONLY_OPS = {
    "read_file",
    "status",
    "list_dir",
    "job_status",
    "tmux_capture",
}


def command_sha256(raw_command: bytes) -> str:
    return hashlib.sha256(raw_command).hexdigest()


def _effect_class(spec: Mapping[str, Any]) -> EffectClass:
    raw = spec.get("effect_class")
    op = str(spec.get("op", "exec"))
    if raw is None:
        if op in INTRINSIC_READ_ONLY_OPS:
            return EffectClass.READ_ONLY
        raise EffectClassificationRequired(
            f"op={op!r} requires explicit effect_class before promotion-bearing execution"
        )
    try:
        cls = EffectClass(str(raw))
    except ValueError as exc:
        raise EffectClassificationRequired(f"unsupported effect_class={raw!r}") from exc
    if cls is EffectClass.READ_ONLY and op not in INTRINSIC_READ_ONLY_OPS:
        raise EffectClassificationConflict(
            f"op={op!r} cannot self-declare READ_ONLY; use SCRATCH_ONLY/LIVE_MUTATION/SYSTEM_MUTATION"
        )
    return cls


def _preconditions(spec: Mapping[str, Any]) -> list[PathHashPrecondition]:
    out: list[PathHashPrecondition] = []
    rows = spec.get("subject_preconditions", ())
    if rows is None:
        rows = ()
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise BridgeEffectAdapterError("subject_preconditions must be a sequence")
    for row in rows:
        if not isinstance(row, Mapping):
            raise BridgeEffectAdapterError("each subject_precondition must be an object")
        path = row.get("path")
        digest = row.get("sha256")
        if not path or not isinstance(digest, str) or len(digest) != 64:
            raise BridgeEffectAdapterError("subject_precondition requires path + 64-hex sha256")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise BridgeEffectAdapterError("subject_precondition sha256 is not hex") from exc
        out.append(PathHashPrecondition(Path(str(path)), digest.lower()))
    return out


def _paths(spec: Mapping[str, Any]) -> tuple[Path | None, list[Path]]:
    scratch_raw = spec.get("scratch_root")
    scratch = Path(str(scratch_raw)) if scratch_raw else None
    touched_raw = spec.get("touched_paths", ()) or ()
    if not isinstance(touched_raw, Sequence) or isinstance(touched_raw, (str, bytes, bytearray)):
        raise BridgeEffectAdapterError("touched_paths must be a sequence")
    return scratch, [Path(str(p)) for p in touched_raw]


def decode_and_validate(raw_command: bytes) -> dict[str, Any]:
    try:
        spec = json.loads(raw_command)
    except json.JSONDecodeError as exc:
        raise BridgeEffectAdapterError("invalid command JSON") from exc
    if not isinstance(spec, dict) or spec.get("schema") != "CLAY_LOCAL_COMMAND/v1":
        raise BridgeEffectAdapterError("unsupported command schema")
    if not spec.get("command_id"):
        raise BridgeEffectAdapterError("command_id required")
    return spec


def execute_guarded(
    *,
    fence: HostEffectFence,
    raw_command: bytes,
    holder: str,
    body: Callable[[dict[str, Any]], Any],
    verifier: Callable[[dict[str, Any], Any], Verification] | None = None,
) -> GuardedExecution:
    """Run one already-admitted bridge operation through the shared fence.

    `body` is the existing daemon's operate()/OPS dispatch. `verifier` must be
    logically independent readback; merely hashing stdout from the effect body
    is not sufficient evidence for live/system success.
    """
    spec = decode_and_validate(raw_command)
    cid = str(spec["command_id"])
    digest = command_sha256(raw_command)
    cls = _effect_class(spec)
    preconditions = _preconditions(spec)
    scratch_root, touched_paths = _paths(spec)

    body_result: Any | None = None
    with fence.effect(
        command_id=cid,
        command_sha256=digest,
        effect_class=cls,
        holder=holder,
        preconditions=preconditions,
        scratch_root=scratch_root,
        touched_paths=touched_paths,
    ) as ticket:
        if ticket.duplicate_suppressed:
            return GuardedExecution(
                cid, digest, cls, ticket, None, "DUPLICATE_SUPPRESSED_VERIFIED"
            )
        body_result = body(spec)
        rc = getattr(body_result, "returncode", 0)
        if rc not in (0, None):
            # Raising inside the fence intentionally converts an externally
            # ambiguous/nonzero live effect to UNKNOWN rather than claiming
            # success from process return alone.
            raise EffectBodyNonzero(body_result)

    if cls in {EffectClass.LIVE_MUTATION, EffectClass.SYSTEM_MUTATION}:
        if verifier is None:
            return GuardedExecution(
                cid, digest, cls, ticket, body_result, "BODY_RETURNED_UNVERIFIED"
            )
        verification = verifier(spec, body_result)
        fence.verify_success(
            cid,
            digest,
            outcome_sha256=verification.outcome_sha256,
            note=verification.note,
        )
        return GuardedExecution(cid, digest, cls, ticket, body_result, "VERIFIED_SUCCEEDED")

    return GuardedExecution(cid, digest, cls, ticket, body_result, "COMPLETED_AT_NONLIVE_SCOPE")
