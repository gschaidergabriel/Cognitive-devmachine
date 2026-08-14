"""Deterministic H1 GWT causal-spine reference for FRANK.

Research candidate only. The module makes selection/ignition, addressability, delivery,
reconstruction, uptake, causal use, outcome, and provenance-bound re-entry separately
observable. It also exposes a conventional priority/event-bus admission baseline so GWT
admission can later be tested instead of assumed.

No cognitive/model/peer/visual state in this module can mint execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Optional
import hashlib
import json
import math


class WorkspaceError(ValueError):
    pass


class AuthorityViolation(WorkspaceError):
    pass


def _canon(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canon(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canon(x) for x in value]
    if isinstance(value, (set, frozenset)):
        xs = [_canon(x) for x in value]
        return sorted(xs, key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise WorkspaceError("NON_FINITE_FLOAT")
        return value
    raise WorkspaceError(f"NON_CANONICAL_TYPE:{type(value).__name__}")


def _cjson(value: Any) -> str:
    return json.dumps(_canon(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_cjson(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BasisWitness:
    basis_epoch: int
    semantic_state_hash: str
    state_version_hash: str
    trace_root_hash: str
    semantic_contract_hash: str = "frank.workspace-contract.v0"

    def validate(self) -> None:
        if self.basis_epoch < 0:
            raise WorkspaceError("BAD_BASIS_EPOCH")
        for name in ("semantic_state_hash", "state_version_hash", "trace_root_hash", "semantic_contract_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise WorkspaceError(f"MISSING_WITNESS:{name}")


@dataclass(frozen=True)
class WorkspaceCandidate:
    candidate_id: str
    score: float
    payload: Any
    valid_epoch: int
    origin: str = "unknown"
    requested_execution_authority: bool = False

    def validate(self) -> None:
        if not self.candidate_id:
            raise WorkspaceError("EMPTY_CANDIDATE_ID")
        if not math.isfinite(self.score) or not 0.0 <= self.score <= 1.0:
            raise WorkspaceError(f"BAD_CANDIDATE_SCORE:{self.candidate_id}")
        _canon(self.payload)
        if self.requested_execution_authority:
            raise AuthorityViolation(f"AUTHORITY_MINT_ATTEMPT:{self.candidate_id}")


@dataclass(frozen=True)
class ReceiverPolicy:
    receiver_id: str
    deliver: bool = True
    reconstruct: bool = True
    uptake: bool = True
    causal_use: bool = True

    def validate(self) -> None:
        if not self.receiver_id:
            raise WorkspaceError("EMPTY_RECEIVER_ID")


@dataclass(frozen=True)
class WorkspaceIntervention:
    intervention_id: str = "control"
    remove_candidates: frozenset[str] = frozenset()
    lesion_receivers: frozenset[str] = frozenset()
    corrupt_reconstruction: frozenset[str] = frozenset()
    disable_uptake: frozenset[str] = frozenset()
    disable_causal_use: frozenset[str] = frozenset()
    disable_reentry: bool = False
    shuffle_reentry: bool = False
    ignition_threshold_override: Optional[float] = None

    def validate(self) -> None:
        if not self.intervention_id:
            raise WorkspaceError("EMPTY_INTERVENTION_ID")
        if self.ignition_threshold_override is not None:
            x = self.ignition_threshold_override
            if not math.isfinite(x) or not 0.0 <= x <= 1.0:
                raise WorkspaceError("BAD_IGNITION_OVERRIDE")


class _ReceiptChain:
    def __init__(
        self, episode_id: str, witness: BasisWitness, intervention_id: str, *,
        intervention_hash: str, candidate_set_hash: str, receiver_policy_hash: str,
    ):
        self._prev = _hash({
            "schema": "frank.workspace-receipts.v0",
            "episode_id": episode_id,
            "basis_epoch": witness.basis_epoch,
            "semantic_state_hash": witness.semantic_state_hash,
            "state_version_hash": witness.state_version_hash,
            "trace_root_hash": witness.trace_root_hash,
            "semantic_contract_hash": witness.semantic_contract_hash,
            "intervention_id": intervention_id,
            "intervention_hash": intervention_hash,
            "candidate_set_hash": candidate_set_hash,
            "receiver_policy_hash": receiver_policy_hash,
        })
        self.receipts: list[dict[str, Any]] = []

    def emit(self, stage: str, subject: str, status: str, data: Any) -> dict[str, Any]:
        body = {
            "index": len(self.receipts),
            "stage": stage,
            "subject": subject,
            "status": status,
            "data": _canon(data),
            "prev_hash": self._prev,
            "execution_authority": False,
        }
        rh = _hash(body)
        body["receipt_hash"] = rh
        self.receipts.append(body)
        self._prev = rh
        return body

    @property
    def root(self) -> str:
        return self._prev


def _validate_unique(items: Iterable[Any], attr: str, label: str) -> list[Any]:
    out = list(items)
    values = [getattr(x, attr) for x in out]
    if len(values) != len(set(values)):
        raise WorkspaceError(f"DUPLICATE_{label}_ID")
    return out


def run_workspace_episode(
    *,
    episode_id: str,
    witness: BasisWitness,
    candidates: Iterable[WorkspaceCandidate],
    receivers: Iterable[ReceiverPolicy],
    ignition_threshold: float = 0.55,
    admission_mode: str = "GWT",
    intervention: Optional[WorkspaceIntervention] = None,
) -> dict[str, Any]:
    """Execute one deterministic, effect-free workspace episode.

    admission_mode:
      GWT       -> competition winner must meet ignition_threshold.
      EVENT_BUS -> conventional deterministic priority admission of the top live candidate;
                   downstream receiver stages remain identical for a matched null baseline.
    """
    if not episode_id:
        raise WorkspaceError("EMPTY_EPISODE_ID")
    witness.validate()
    if not math.isfinite(ignition_threshold) or not 0.0 <= ignition_threshold <= 1.0:
        raise WorkspaceError("BAD_IGNITION_THRESHOLD")
    mode = admission_mode.upper()
    if mode not in {"GWT", "EVENT_BUS"}:
        raise WorkspaceError("BAD_ADMISSION_MODE")
    iv = intervention or WorkspaceIntervention()
    iv.validate()
    threshold = iv.ignition_threshold_override if iv.ignition_threshold_override is not None else ignition_threshold

    cand = _validate_unique(candidates, "candidate_id", "CANDIDATE")
    recv = _validate_unique(receivers, "receiver_id", "RECEIVER")
    for x in cand:
        x.validate()
    for x in recv:
        x.validate()

    candidate_set_hash = _hash([asdict(x) for x in sorted(cand, key=lambda x: x.candidate_id)])
    receiver_policy_hash = _hash([asdict(x) for x in sorted(recv, key=lambda x: x.receiver_id)])
    intervention_hash = _hash(asdict(iv))
    chain = _ReceiptChain(
        episode_id, witness, iv.intervention_id,
        intervention_hash=intervention_hash,
        candidate_set_hash=candidate_set_hash,
        receiver_policy_hash=receiver_policy_hash,
    )

    live: list[WorkspaceCandidate] = []
    for x in cand:
        if x.candidate_id in iv.remove_candidates:
            chain.emit("candidate_filter", x.candidate_id, "REMOVED_BY_INTERVENTION", {"score": x.score})
        elif x.valid_epoch != witness.basis_epoch:
            chain.emit("candidate_filter", x.candidate_id, "STALE_EPOCH", {"candidate_epoch": x.valid_epoch})
        else:
            live.append(x)
            chain.emit("candidate_filter", x.candidate_id, "ELIGIBLE", {"score": x.score, "origin": x.origin})

    live.sort(key=lambda x: (-x.score, x.candidate_id))
    winner = live[0] if live else None
    chain.emit(
        "competition",
        episode_id,
        "WINNER" if winner else "EMPTY",
        {
            "mode": mode,
            "candidate_order": [x.candidate_id for x in live],
            "winner_id": winner.candidate_id if winner else None,
            "winner_score": winner.score if winner else None,
        },
    )

    if winner is None:
        ignited = False
        ignition_reason = "NO_CANDIDATE"
    elif mode == "EVENT_BUS":
        ignited = True
        ignition_reason = "PRIORITY_EVENT_ADMITTED"
    else:
        ignited = winner.score >= threshold
        ignition_reason = "THRESHOLD_MET" if ignited else "THRESHOLD_NOT_MET"

    chain.emit(
        "ignition",
        winner.candidate_id if winner else episode_id,
        "IGNITED" if ignited else "NOT_IGNITED",
        {
            "mode": mode,
            "threshold": threshold if mode == "GWT" else None,
            "reason": ignition_reason,
            "biological_signature_required": False,
        },
    )

    payload_hash = _hash(winner.payload) if winner else None
    receiver_universe = [r.receiver_id for r in sorted(recv, key=lambda x: x.receiver_id)]
    receiver_universe_hash = _hash(receiver_universe)
    envelope_hash = None
    if ignited and winner:
        envelope = {
            "episode_id": episode_id,
            "winner_id": winner.candidate_id,
            "payload_hash": payload_hash,
            "basis_epoch": witness.basis_epoch,
            "semantic_state_hash": witness.semantic_state_hash,
            "state_version_hash": witness.state_version_hash,
            "source_trace_root_hash": witness.trace_root_hash,
            "receiver_universe_hash": receiver_universe_hash,
            "execution_authority": False,
        }
        envelope_hash = _hash(envelope)
        chain.emit("broadcast", episode_id, "ADDRESSABLE", {"envelope_hash": envelope_hash, "receiver_count": len(recv)})
    else:
        chain.emit("broadcast", episode_id, "NOT_ADDRESSABLE", {"receiver_count": len(recv)})

    receiver_states: list[dict[str, Any]] = []
    for r in sorted(recv, key=lambda x: x.receiver_id):
        addressable = bool(ignited and winner)
        delivered = addressable and r.deliver and r.receiver_id not in iv.lesion_receivers
        reconstruction_corrupt = delivered and r.receiver_id in iv.corrupt_reconstruction
        reconstructed = delivered and r.reconstruct and not reconstruction_corrupt
        uptake = reconstructed and r.uptake and r.receiver_id not in iv.disable_uptake
        causal_use = uptake and r.causal_use and r.receiver_id not in iv.disable_causal_use

        chain.emit(
            "receiver_delivery",
            r.receiver_id,
            "DELIVERED" if delivered else ("LESIONED" if r.receiver_id in iv.lesion_receivers else "NOT_DELIVERED"),
            {"addressable": addressable, "envelope_hash": envelope_hash if delivered else None},
        )
        chain.emit(
            "receiver_reconstruction",
            r.receiver_id,
            "CORRUPTED" if reconstruction_corrupt else ("RECONSTRUCTED" if reconstructed else "NOT_RECONSTRUCTED"),
            {"delivered": delivered, "payload_hash": payload_hash if reconstructed else None},
        )
        chain.emit(
            "receiver_uptake",
            r.receiver_id,
            "UPTAKE" if uptake else "NO_UPTAKE",
            {"reconstructed": reconstructed},
        )
        use_receipt = chain.emit(
            "receiver_causal_use",
            r.receiver_id,
            "USED" if causal_use else "NOT_USED",
            {"uptake": uptake},
        )
        if not addressable:
            diagnostic = "NOT_ADDRESSABLE"
        elif not delivered:
            diagnostic = "ADDRESSABLE_ONLY"
        elif not reconstructed:
            diagnostic = "DELIVERED_NO_RECONSTRUCTION"
        elif not uptake:
            diagnostic = "RECONSTRUCTED_NO_UPTAKE"
        elif not causal_use:
            diagnostic = "UPTAKE_NO_LOCAL_EFFECT"
        else:
            diagnostic = "CAUSAL_USE"
        receiver_states.append({
            "receiver_id": r.receiver_id,
            "addressable": addressable,
            "delivered": delivered,
            "reconstructed": reconstructed,
            "uptake": uptake,
            "causal_use": causal_use,
            "causal_use_receipt": use_receipt["receipt_hash"],
            "diagnostic_class": diagnostic,
        })

    used = [x["receiver_id"] for x in receiver_states if x["causal_use"]]
    outcome = {
        "winner_id": winner.candidate_id if winner else None,
        "ignited": ignited,
        "used_receivers": used,
        "addressable_count": sum(x["addressable"] for x in receiver_states),
        "delivered_count": sum(x["delivered"] for x in receiver_states),
        "reconstructed_count": sum(x["reconstructed"] for x in receiver_states),
        "uptake_count": sum(x["uptake"] for x in receiver_states),
        "causal_use_count": len(used),
    }
    outcome_receipt = chain.emit("outcome", episode_id, "OBSERVED", outcome)

    reentry_payload = None
    if used and not iv.disable_reentry:
        truthful_bindings = [
            {"receiver_id": x["receiver_id"], "causal_use_receipt": x["causal_use_receipt"]}
            for x in receiver_states if x["causal_use"]
        ]
        if iv.shuffle_reentry and len(truthful_bindings) > 1:
            shifted = [x["causal_use_receipt"] for x in truthful_bindings[1:]] + [truthful_bindings[0]["causal_use_receipt"]]
            evidence_bindings = [
                {"receiver_id": x["receiver_id"], "causal_use_receipt": receipt}
                for x, receipt in zip(truthful_bindings, shifted)
            ]
        else:
            evidence_bindings = truthful_bindings
        reentry_payload = {
            "episode_id": episode_id,
            "winner_id": winner.candidate_id if winner else None,
            "used_receivers": list(reversed(used)) if iv.shuffle_reentry else used,
            "receiver_evidence": evidence_bindings,
            "outcome_receipt": outcome_receipt["receipt_hash"],
            "truthful": not iv.shuffle_reentry,
            "source_binding_status": "PROVENANCE_BROKEN" if iv.shuffle_reentry else "PROVENANCE_BOUND",
            "execution_authority": False,
        }
        chain.emit(
            "reentry",
            episode_id,
            "SHUFFLED" if iv.shuffle_reentry else "TRUTHFUL",
            {"reentry_hash": _hash(reentry_payload), "used_receivers": reentry_payload["used_receivers"]},
        )
    else:
        reason = "DISABLED" if iv.disable_reentry else "NO_CAUSAL_USE"
        chain.emit("reentry", episode_id, "NONE", {"reason": reason})

    n = len(receiver_states)
    if not used:
        closure_status = "OPEN"
    elif len(used) < n:
        closure_status = "PARTIAL"
    elif reentry_payload is None:
        closure_status = "CAUSAL_BROADCAST_CLOSED"
    else:
        closure_status = "REENTRY_CLOSED"
    integration = {
        "receiver_coverage": (sum(x["addressable"] for x in receiver_states) / n) if n else 0.0,
        "delivery_fraction": (sum(x["delivered"] for x in receiver_states) / n) if n else 0.0,
        "reconstruction_fraction": (sum(x["reconstructed"] for x in receiver_states) / n) if n else 0.0,
        "uptake_fraction": (sum(x["uptake"] for x in receiver_states) / n) if n else 0.0,
        "causal_use_fraction": (len(used) / n) if n else 0.0,
        "reentry_fraction": 1.0 if reentry_payload is not None else 0.0,
    }

    result = {
        "schema": "frank.workspace-episode.v0",
        "episode_id": episode_id,
        "admission_mode": mode,
        "intervention_id": iv.intervention_id,
        "basis": {
            "basis_epoch": witness.basis_epoch,
            "semantic_state_hash": witness.semantic_state_hash,
            "state_version_hash": witness.state_version_hash,
            "trace_root_hash": witness.trace_root_hash,
        },
        "semantic_contract_hash": witness.semantic_contract_hash,
        "input_identity": {
            "candidate_set_hash": candidate_set_hash,
            "receiver_policy_hash": receiver_policy_hash,
            "intervention_hash": intervention_hash,
        },
        "winner_id": winner.candidate_id if winner else None,
        "ignited": ignited,
        "ignition_reason": ignition_reason,
        "payload_hash": payload_hash,
        "broadcast_envelope_hash": envelope_hash,
        "receiver_universe_hash": receiver_universe_hash,
        "receiver_states": receiver_states,
        "outcome": outcome,
        "reentry": reentry_payload,
        "integration_readout": integration,
        "closure_status": closure_status,
        "receipts": chain.receipts,
        "receipt_root_hash": chain.root,
        "execution_authority": False,
        "evidence_status": "H1_REFERENCE_CANDIDATE",
    }
    result["episode_hash"] = _hash({k: v for k, v in result.items() if k != "episode_hash"})
    return result
