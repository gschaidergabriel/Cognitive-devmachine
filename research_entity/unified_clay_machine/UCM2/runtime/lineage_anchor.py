from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

RecoveryMode = Literal["RECOVER_EXACT", "EXTEND_FROM_ANCHOR"]


@dataclass(frozen=True)
class LineageAnchor:
    """Externally trusted checkpoint into an already integrity-verified UCM2 event stream.

    The anchor is intentionally small. It is not self-authorizing: production code
    must obtain it from an authority outside the candidate event stream being judged.
    """

    anchor_id: str
    root_module: str
    seq: int
    epoch: int
    event_hash: str
    authority_generation: int

    def __post_init__(self) -> None:
        if not self.anchor_id:
            raise ValueError("LINEAGE_ANCHOR_ID_EMPTY")
        if not self.root_module:
            raise ValueError("LINEAGE_ANCHOR_ROOT_EMPTY")
        if self.seq < 1:
            raise ValueError("LINEAGE_ANCHOR_SEQ_INVALID")
        if self.epoch < 0:
            raise ValueError("LINEAGE_ANCHOR_EPOCH_INVALID")
        if not self.event_hash:
            raise ValueError("LINEAGE_ANCHOR_HASH_EMPTY")
        if self.authority_generation < 0:
            raise ValueError("LINEAGE_AUTHORITY_GENERATION_INVALID")


@dataclass(frozen=True)
class LineageAssessment:
    decision: Literal["ADMIT_EXACT_RECOVERY", "ANCHOR_HEAD", "CANDIDATE_SUCCESSOR"]
    anchor_id: str
    authority_generation: int
    terminal_seq: int
    terminal_epoch: int
    terminal_hash: str


def assess_stream_against_anchor(
    stream: list[dict],
    anchor: LineageAnchor,
    *,
    verifier: Callable[[list[dict]], str],
    mode: RecoveryMode = "RECOVER_EXACT",
) -> LineageAssessment:
    """Combine internal integrity verification with external lineage admission.

    RECOVER_EXACT is fail-closed recovery: only the exact externally anchored head
    is admitted.

    EXTEND_FROM_ANCHOR proves ancestry only. Descendants are returned as
    CANDIDATE_SUCCESSOR and MUST NOT be treated as newly canonical until an
    external authority issues a successor anchor.
    """

    if mode not in {"RECOVER_EXACT", "EXTEND_FROM_ANCHOR"}:
        raise ValueError("LINEAGE_MODE_INVALID")
    if not stream:
        raise RuntimeError("LINEAGE_STREAM_EMPTY")

    terminal_hash = verifier(stream)
    terminal = stream[-1]

    if anchor.seq > len(stream):
        raise RuntimeError("LINEAGE_ANCHOR_NOT_PRESENT")

    anchored_event = stream[anchor.seq - 1]
    if int(anchored_event["seq"]) != anchor.seq:
        raise RuntimeError("LINEAGE_ANCHOR_SEQ_MISMATCH")
    if int(anchored_event["epoch"]) != anchor.epoch:
        raise RuntimeError("LINEAGE_ANCHOR_EPOCH_MISMATCH")
    if anchored_event["event_hash"] != anchor.event_hash:
        raise RuntimeError("LINEAGE_ANCHOR_HASH_MISMATCH")

    root_module = _event_root_module(stream[0])
    if root_module != anchor.root_module:
        raise RuntimeError("LINEAGE_ANCHOR_ROOT_MISMATCH")

    terminal_seq = int(terminal["seq"])
    terminal_epoch = int(terminal["epoch"])

    if mode == "RECOVER_EXACT":
        if terminal_seq != anchor.seq or terminal_epoch != anchor.epoch:
            raise RuntimeError("LINEAGE_EXACT_HEAD_REQUIRED")
        if terminal_hash != anchor.event_hash:
            raise RuntimeError("LINEAGE_TERMINAL_HASH_MISMATCH")
        decision = "ADMIT_EXACT_RECOVERY"
    elif terminal_seq == anchor.seq:
        decision = "ANCHOR_HEAD"
    else:
        decision = "CANDIDATE_SUCCESSOR"

    return LineageAssessment(
        decision=decision,
        anchor_id=anchor.anchor_id,
        authority_generation=anchor.authority_generation,
        terminal_seq=terminal_seq,
        terminal_epoch=terminal_epoch,
        terminal_hash=terminal_hash,
    )


def _event_root_module(event: dict) -> str:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        raise RuntimeError("LINEAGE_BOOTSTRAP_PAYLOAD_INVALID")
    root = payload.get("root_module")
    if not isinstance(root, str) or not root:
        raise RuntimeError("LINEAGE_BOOTSTRAP_ROOT_MISSING")
    return root
