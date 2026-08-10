from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .state_ledger import StaleEpoch, h
from .unifieddb_emergent_preprocessor import EmergentAssemblyPreprocessor, PossibilitySpec


@dataclass(frozen=True)
class EmergentCascadeSpec:
    query_id: str
    text: str
    source_epoch: int
    max_items: int = 12
    max_hops: int = 3
    frontier_budget: int = 512
    min_edge_weight: float = 0.05
    hop_decay: float = 0.88
    min_resolution_confidence: float = 0.80
    allow_epistemic: tuple[str, ...] = ('KNOWN',)
    allow_status: tuple[str, ...] = ('CURRENT',)
    allowed_domains: tuple[str, ...] = ()
    purpose: str = 'NL_TO_ACTIVE_ASSEMBLY'


class FailClosedEmergentRetrievalCascade:
    """Natural-language -> evidence-bound seed -> bounded ActiveAssembly.

    Resolver ambiguity/low confidence/miss never starts graph propagation. The resolver is
    injected deliberately so U12 can evolve independently from the EAP traversal engine.
    `logical_to_ref` binds a resolver logical id to the canonical UnifiedDB row identity;
    failing that binding is also fail-closed. Graph ignition re-checks resolver confidence
    and candidate consistency so a faulty/incompatible resolver cannot open EAP by class
    label alone.
    """

    _ACCEPTED_RESOLUTION_CLASSES = {'EXACT_LOGICAL_ID', 'EVIDENCE_ALIAS'}

    def __init__(
        self,
        *,
        resolver: Any,
        preprocessor: EmergentAssemblyPreprocessor,
        logical_to_ref: Callable[[str], str | None],
    ):
        self.resolver = resolver
        self.preprocessor = preprocessor
        self.logical_to_ref = logical_to_ref

    def retrieve(self, spec: EmergentCascadeSpec) -> dict[str, Any]:
        if not spec.query_id.strip():
            raise ValueError('query_id required')
        if not 0.0 <= spec.min_resolution_confidence <= 1.0:
            raise ValueError('invalid min_resolution_confidence')
        if spec.source_epoch != self.preprocessor.ledger.epoch:
            raise StaleEpoch(
                f'cascade source epoch {spec.source_epoch}!={self.preprocessor.ledger.epoch}'
            )

        resolution = self.resolver.resolve(spec.text, source_epoch=spec.source_epoch)
        resolution_class = str(getattr(resolution, 'resolution_class', 'MISS'))
        logical_id = getattr(resolution, 'logical_id', None)
        candidates = tuple(str(value) for value in (getattr(resolution, 'candidates', ()) or ()))
        confidence = float(getattr(resolution, 'confidence', 0.0) or 0.0)
        resolution_latency_ns = int(getattr(resolution, 'latency_ns', 0) or 0)

        if resolution_class not in self._ACCEPTED_RESOLUTION_CLASSES or not logical_id:
            return self._blocked_receipt(
                spec,
                resolution_class=resolution_class,
                logical_id=logical_id,
                candidates=candidates,
                confidence=confidence,
                resolution_latency_ns=resolution_latency_ns,
                block_reason='RESOLUTION_NOT_ADMITTED',
            )

        logical_id = str(logical_id)
        required_confidence = 0.99 if resolution_class == 'EXACT_LOGICAL_ID' else spec.min_resolution_confidence
        if confidence < required_confidence:
            return self._blocked_receipt(
                spec,
                resolution_class=resolution_class,
                logical_id=logical_id,
                candidates=candidates,
                confidence=confidence,
                resolution_latency_ns=resolution_latency_ns,
                block_reason='RESOLUTION_CONFIDENCE_BELOW_CASCADE_GATE',
            )
        if candidates and logical_id not in candidates:
            return self._blocked_receipt(
                spec,
                resolution_class=resolution_class,
                logical_id=logical_id,
                candidates=candidates,
                confidence=confidence,
                resolution_latency_ns=resolution_latency_ns,
                block_reason='RESOLUTION_SELECTED_ID_NOT_IN_CANDIDATES',
            )

        seed_ref = self.logical_to_ref(logical_id)
        if not seed_ref:
            return self._blocked_receipt(
                spec,
                resolution_class=resolution_class,
                logical_id=logical_id,
                candidates=candidates,
                confidence=confidence,
                resolution_latency_ns=resolution_latency_ns,
                block_reason='LOGICAL_ID_NOT_BOUND_TO_CURRENT_UNIFIEDDB_REF',
            )

        assembly = self.preprocessor.compile_active_assembly(
            PossibilitySpec(
                assembly_id=spec.query_id,
                seed_refs=(seed_ref,),
                allowed_domains=spec.allowed_domains,
                allow_epistemic=spec.allow_epistemic,
                allow_status=spec.allow_status,
                max_items=spec.max_items,
                max_hops=spec.max_hops,
                frontier_budget=spec.frontier_budget,
                min_edge_weight=spec.min_edge_weight,
                hop_decay=spec.hop_decay,
                basis_epoch=spec.source_epoch,
                purpose=spec.purpose,
            )
        )
        receipt_hash = h({
            'query_id': spec.query_id,
            'source_epoch': spec.source_epoch,
            'text': spec.text,
            'resolution_class': resolution_class,
            'logical_id': logical_id,
            'resolution_candidates': candidates,
            'resolution_confidence': confidence,
            'min_resolution_confidence': spec.min_resolution_confidence,
            'seed_ref': seed_ref,
            'assembly_selection_hash': assembly['selection_hash'],
        })
        return {
            'query_id': spec.query_id,
            'source_epoch': spec.source_epoch,
            'semantic_state_hash': assembly['semantic_state_hash'],
            'resolution_class': resolution_class,
            'resolution_confidence': confidence,
            'resolution_candidates': candidates,
            'resolution_latency_ns': resolution_latency_ns,
            'min_resolution_confidence': spec.min_resolution_confidence,
            'logical_id': logical_id,
            'seed_ref': seed_ref,
            'assembly': assembly,
            'blocked': False,
            'block_reason': None,
            'receipt_hash': receipt_hash,
            'derived': True,
            'persistent_second_store': False,
            'authority': 'ASSEMBLY_CONTEXT_ONLY',
        }

    def _blocked_receipt(
        self,
        spec: EmergentCascadeSpec,
        *,
        resolution_class: str,
        logical_id: str | None,
        candidates: tuple[str, ...],
        confidence: float,
        resolution_latency_ns: int,
        block_reason: str,
    ) -> dict[str, Any]:
        receipt_hash = h({
            'query_id': spec.query_id,
            'source_epoch': spec.source_epoch,
            'semantic_state_hash': self.preprocessor.ledger.semantic_state_hash,
            'text': spec.text,
            'resolution_class': resolution_class,
            'logical_id': logical_id,
            'resolution_candidates': candidates,
            'resolution_confidence': confidence,
            'min_resolution_confidence': spec.min_resolution_confidence,
            'block_reason': block_reason,
        })
        return {
            'query_id': spec.query_id,
            'source_epoch': spec.source_epoch,
            'semantic_state_hash': self.preprocessor.ledger.semantic_state_hash,
            'resolution_class': resolution_class,
            'resolution_confidence': confidence,
            'resolution_candidates': candidates,
            'resolution_latency_ns': resolution_latency_ns,
            'min_resolution_confidence': spec.min_resolution_confidence,
            'logical_id': logical_id,
            'seed_ref': None,
            'assembly': None,
            'blocked': True,
            'block_reason': block_reason,
            'receipt_hash': receipt_hash,
            'derived': True,
            'persistent_second_store': False,
            'authority': 'ASSEMBLY_CONTEXT_ONLY',
        }
