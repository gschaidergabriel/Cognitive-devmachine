from __future__ import annotations

"""Use-boundary integrity guard for non-authoritative authenticated state shadow.

This candidate deliberately does NOT replace full StateLedger integrity verification. It adds a
cheap, causal safety boundary for Pulse/possibility preprocessing: refresh the rebuildable
shadow from committed events, require exact epoch/event/hash coherence, then independently
rehash every authoritative state row that is actually about to enter cognition and compare it
with the shadow leaf.

A direct no-event tamper of a causally unused row may remain latent until periodic/full audit;
a tampered row cannot be admitted through this guard as context. Full audit remains mandatory
for recovery/release and any stronger global-integrity claim.
"""

from dataclasses import dataclass
from typing import Iterable

from research_entity.harness.reference.state_auth_shadow import (
    AuthenticatedStateShadowV1,
    AuthShadowIntegrityError,
    PROJECTION_VERSION,
    _key_digest,
    _leaf_hash,
)
from research_entity.harness.reference.state_ledger import StateLedger


class FocusIntegrityError(AuthShadowIntegrityError):
    pass


@dataclass(frozen=True)
class FocusGuardReceipt:
    ledger_epoch: int
    last_event_seq: int
    checked_refs: tuple[str, ...]
    shadow_root_hash: str
    refresh_mode: str
    passed: bool
    global_integrity_claim: str = "NONE_PERIODIC_FULL_AUDIT_STILL_REQUIRED"
    authority: str = "USE_BOUNDARY_VERIFICATION_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY"


class AuthShadowFocusGuard:
    def __init__(self, ledger: StateLedger, shadow: AuthenticatedStateShadowV1 | None = None):
        self.ledger = ledger
        self.shadow = shadow or AuthenticatedStateShadowV1(ledger)

    def _max_event_seq(self) -> int:
        return int(self.ledger.conn.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    def _coherent_receipt(self):
        receipt = self.shadow.receipt()
        if receipt.projection_version != PROJECTION_VERSION:
            raise FocusIntegrityError("authenticated shadow version mismatch")
        if receipt.ledger_epoch != self.ledger.epoch:
            raise FocusIntegrityError(
                f"shadow epoch {receipt.ledger_epoch} != ledger epoch {self.ledger.epoch}"
            )
        current_seq = self._max_event_seq()
        if receipt.last_event_seq != current_seq:
            raise FocusIntegrityError(
                f"shadow event seq {receipt.last_event_seq} != ledger event seq {current_seq}"
            )
        if receipt.semantic_chain_hash != self.ledger._m("semantic_chain_hash"):
            raise FocusIntegrityError("shadow semantic chain mismatch")
        # This compares to the canonical hash stored/advanced by StateLedger events. It is an
        # epoch/coherence check, not a full recomputation of physical state.
        if receipt.canonical_semantic_state_hash != self.ledger.semantic_state_hash:
            raise FocusIntegrityError("shadow canonical semantic-state hash mismatch")
        return receipt

    def refresh_and_verify_refs(self, refs: Iterable[str], *, now: str) -> FocusGuardReceipt:
        refs_tuple = tuple(dict.fromkeys(str(ref) for ref in refs))
        for ref in refs_tuple:
            if ":" not in ref:
                raise ValueError(f"invalid state ref: {ref}")
        refresh = self.shadow.refresh(now=now)
        receipt = self._coherent_receipt()

        for ref in refs_tuple:
            domain, key = ref.split(":", 1)
            row = self.ledger.conn.execute(
                """SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash
                   FROM state WHERE domain=? AND k=?""",
                (domain, key),
            ).fetchone()
            digest = _key_digest(domain, key)
            stored = self.ledger.conn.execute(
                "SELECT leaf_hash FROM auth_shadow_leaves WHERE key_digest=?",
                (digest,),
            ).fetchone()
            if row is None:
                if stored is not None:
                    raise FocusIntegrityError(f"deleted/missing ref remains in shadow: {ref}")
                raise FocusIntegrityError(f"selected ref missing from authoritative state: {ref}")
            if stored is None:
                raise FocusIntegrityError(f"selected ref missing from authenticated shadow: {ref}")
            current_leaf = _leaf_hash(row)
            if bytes(stored[0]) != current_leaf:
                raise FocusIntegrityError(f"selected ref leaf mismatch: {ref}")

        return FocusGuardReceipt(
            ledger_epoch=self.ledger.epoch,
            last_event_seq=receipt.last_event_seq,
            checked_refs=refs_tuple,
            shadow_root_hash=receipt.root_hash,
            refresh_mode=str(refresh.get("mode", "UNKNOWN")),
            passed=True,
        )
