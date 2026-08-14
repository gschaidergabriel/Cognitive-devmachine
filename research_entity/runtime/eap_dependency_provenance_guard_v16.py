from __future__ import annotations

"""U16: provenance-bound dependency propagation guard for EAP.

This module does not create a second truth store and does not mutate UnifiedDB. It derives
an ephemeral latest-write provenance index from StateLedger events and filters only the
compiled dependency adjacency used by the model-facing EmergentAssemblyPreprocessor.

The guard is deliberately opt-in because historical dependency rows were not required to
carry an evidence class. Strict mode is therefore a migration/test surface, not a silent
reinterpretation of existing canonical state.
"""

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, h
from research_entity.harness.reference.unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
)


TRUSTED_EVIDENCE_CLASSES = frozenset({
    "VERIFIED",
    "VALIDATED",
    "MEASURED",
    "AUTHORITATIVE",
    "CANONICAL",
})


@dataclass(frozen=True)
class LatestWriteReceipt:
    ref: str
    event_id: str
    event_type: str
    writer: str
    event_epoch: int
    provenance: dict[str, Any]
    source: dict[str, Any]
    op: str


@dataclass(frozen=True)
class EdgeProofDecision:
    dependency_ref: str
    admitted: bool
    reason: str
    event_id: str | None
    event_epoch: int | None
    evidence_class: str | None


def latest_write_receipts(ledger: StateLedger) -> dict[str, LatestWriteReceipt]:
    """Derive the latest semantic write receipt for every materialized row."""
    out: dict[str, LatestWriteReceipt] = {}
    for event in ledger.export_events():
        event_epoch = int(event["base_epoch"]) + 1
        provenance = dict(event.get("provenance") or {})
        source = dict(event.get("source") or {})
        for op in event.get("ops", ()):
            domain = str(op.get("domain", "")).strip()
            key = str(op.get("key", "")).strip()
            if not domain or not key:
                continue
            ref = f"{domain}:{key}"
            out[ref] = LatestWriteReceipt(
                ref=ref,
                event_id=str(event.get("event_id", "")),
                event_type=str(event.get("event_type", "")),
                writer=str(event.get("writer", "")),
                event_epoch=event_epoch,
                provenance=provenance,
                source=source,
                op=str(op.get("op", "")).upper(),
            )
    return out


def decide_dependency_proof(
    dependency_ref: str,
    receipt: LatestWriteReceipt | None,
    *,
    current_epoch: int,
    trusted_evidence_classes: Iterable[str] = TRUSTED_EVIDENCE_CLASSES,
    require_source: bool = False,
) -> EdgeProofDecision:
    trusted = {str(x).upper() for x in trusted_evidence_classes}
    if receipt is None:
        return EdgeProofDecision(dependency_ref, False, "NO_WRITE_RECEIPT", None, None, None)
    if receipt.event_epoch > current_epoch:
        return EdgeProofDecision(
            dependency_ref, False, "FUTURE_EVENT_EPOCH", receipt.event_id,
            receipt.event_epoch, None,
        )

    provenance = receipt.provenance
    evidence_class = str(
        provenance.get("evidence_class")
        or provenance.get("verification_class")
        or ""
    ).upper().strip()
    if not provenance:
        return EdgeProofDecision(
            dependency_ref, False, "PROVENANCE_MISSING", receipt.event_id,
            receipt.event_epoch, None,
        )
    if not evidence_class:
        return EdgeProofDecision(
            dependency_ref, False, "EVIDENCE_CLASS_MISSING", receipt.event_id,
            receipt.event_epoch, None,
        )
    if evidence_class not in trusted:
        return EdgeProofDecision(
            dependency_ref, False, "EVIDENCE_CLASS_UNTRUSTED", receipt.event_id,
            receipt.event_epoch, evidence_class,
        )

    valid_from = provenance.get("valid_from_epoch")
    valid_until = provenance.get("valid_until_epoch")
    try:
        if valid_from is not None and current_epoch < int(valid_from):
            return EdgeProofDecision(
                dependency_ref, False, "PROVENANCE_NOT_YET_VALID", receipt.event_id,
                receipt.event_epoch, evidence_class,
            )
        if valid_until is not None and current_epoch > int(valid_until):
            return EdgeProofDecision(
                dependency_ref, False, "PROVENANCE_EXPIRED", receipt.event_id,
                receipt.event_epoch, evidence_class,
            )
    except (TypeError, ValueError):
        return EdgeProofDecision(
            dependency_ref, False, "PROVENANCE_EPOCH_INVALID", receipt.event_id,
            receipt.event_epoch, evidence_class,
        )

    if require_source and not receipt.source:
        return EdgeProofDecision(
            dependency_ref, False, "SOURCE_RECEIPT_MISSING", receipt.event_id,
            receipt.event_epoch, evidence_class,
        )
    return EdgeProofDecision(
        dependency_ref, True, "ADMITTED", receipt.event_id,
        receipt.event_epoch, evidence_class,
    )


class ProvenanceGuardedEmergentAssemblyPreprocessor(EmergentAssemblyPreprocessor):
    """EAP with an ephemeral fail-closed dependency propagation filter.

    The complete provenance decision manifest is compiled and hashed once per source epoch.
    Hot queries bind only that fixed manifest hash into their query receipt, avoiding an
    O(number-of-dependencies) serialization/hash tax on every model-input assembly.
    """

    _GUARD_VERSION = "EAP-PROVENANCE-GUARD-16.3"

    def __init__(
        self,
        ledger: StateLedger,
        *,
        trusted_evidence_classes: Iterable[str] = TRUSTED_EVIDENCE_CLASSES,
        require_source: bool = False,
    ):
        super().__init__(ledger)
        self.trusted_evidence_classes = frozenset(
            str(x).upper() for x in trusted_evidence_classes
        )
        self.require_source = bool(require_source)
        self._guarded_epoch: int | None = None
        self._guarded_state_hash: str | None = None
        self._edge_proof_decisions: dict[str, EdgeProofDecision] = {}
        self._edge_proof_audit: Counter[str] = Counter()
        self._blocked_dependency_refs: tuple[str, ...] = ()
        self._edge_proof_manifest_hash: str | None = None

    def _policy(self) -> dict[str, Any]:
        return {
            "trusted_evidence_classes": tuple(sorted(self.trusted_evidence_classes)),
            "require_source": self.require_source,
            "authority": "PROPAGATION_FILTER_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY",
        }

    def _invalidate(self) -> None:
        super()._invalidate()
        self._guarded_epoch = None
        self._guarded_state_hash = None
        self._edge_proof_decisions = {}
        self._edge_proof_audit = Counter()
        self._blocked_dependency_refs = ()
        self._edge_proof_manifest_hash = None

    def _ensure_preprocessor(self) -> None:
        super()._ensure_preprocessor()
        basis = self.ledger.epoch
        state_hash = self.ledger.semantic_state_hash
        if self._guarded_epoch == basis and self._guarded_state_hash == state_hash:
            return

        receipts = latest_write_receipts(self.ledger)
        decisions: dict[str, EdgeProofDecision] = {}
        audit: Counter[str] = Counter()
        guarded: dict[str, tuple[tuple[str, float, str, str], ...]] = {}
        admitted_edges = 0

        for source_ref, edges in self._adj.items():
            kept: list[tuple[str, float, str, str]] = []
            for target, weight, relation, dependency_ref in edges:
                decision = decisions.get(dependency_ref)
                if decision is None:
                    decision = decide_dependency_proof(
                        dependency_ref,
                        receipts.get(dependency_ref),
                        current_epoch=basis,
                        trusted_evidence_classes=self.trusted_evidence_classes,
                        require_source=self.require_source,
                    )
                    decisions[dependency_ref] = decision
                    audit["ADMITTED" if decision.admitted else "REJECTED"] += 1
                    if not decision.admitted:
                        audit[decision.reason] += 1
                if decision.admitted:
                    kept.append((target, weight, relation, dependency_ref))
                    admitted_edges += 1
            if kept:
                guarded[source_ref] = tuple(kept)

        decision_rows = tuple(asdict(decisions[ref]) for ref in sorted(decisions))
        blocked = tuple(sorted(
            ref for ref, decision in decisions.items() if not decision.admitted
        ))
        manifest_hash = h({
            "v": self._GUARD_VERSION,
            "basis_epoch": basis,
            "semantic_state_hash": state_hash,
            "policy": self._policy(),
            "decisions": decision_rows,
            "audit": dict(sorted(audit.items())),
            "blocked_dependency_refs": blocked,
        })

        self._adj = guarded
        self._edge_count = admitted_edges
        self._edge_proof_decisions = decisions
        self._edge_proof_audit = audit
        self._blocked_dependency_refs = blocked
        self._edge_proof_manifest_hash = manifest_hash
        self._guarded_epoch = basis
        self._guarded_state_hash = state_hash
        self._refresh_compiled_identity()

    def edge_proof_manifest(self) -> dict[str, Any]:
        """Return the full epoch-bound decision manifest only when explicitly requested."""
        self._ensure_preprocessor()
        decisions = tuple(
            asdict(self._edge_proof_decisions[ref])
            for ref in sorted(self._edge_proof_decisions)
        )
        return {
            "version": self._GUARD_VERSION,
            "basis_epoch": self.ledger.epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "policy": self._policy(),
            "decisions": decisions,
            "audit": dict(sorted(self._edge_proof_audit.items())),
            "blocked_dependency_refs": self._blocked_dependency_refs,
            "manifest_hash": self._edge_proof_manifest_hash,
            "authority": "OBSERVABILITY_ONLY",
        }

    def compile_active_assembly(self, spec: PossibilitySpec) -> dict[str, Any]:
        result = super().compile_active_assembly(spec)
        result["edge_provenance_guard_version"] = self._GUARD_VERSION
        result["edge_provenance_policy"] = self._policy()
        result["edge_proof_audit"] = dict(sorted(self._edge_proof_audit.items()))
        result["blocked_dependency_refs"] = self._blocked_dependency_refs
        result["edge_proof_manifest_hash"] = self._edge_proof_manifest_hash
        result["edge_provenance_receipt_hash"] = h({
            "v": self._GUARD_VERSION,
            "basis_epoch": result["basis_epoch"],
            "semantic_state_hash": result["semantic_state_hash"],
            "compiled_index_hash": result["compiled_index_hash"],
            "selection_hash": result["selection_hash"],
            "manifest_hash": self._edge_proof_manifest_hash,
        })
        return result
