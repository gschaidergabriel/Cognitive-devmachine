from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from datetime import datetime, timezone
from typing import Optional


class EffectClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    REVERSIBLE_WRITE = "REVERSIBLE_WRITE"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    PRIVILEGED_CHANGE = "PRIVILEGED_CHANGE"
    DESTRUCTIVE = "DESTRUCTIVE"
    CREDENTIAL_SECURITY = "CREDENTIAL_SECURITY"
    FINANCIAL_OR_LEGAL_COMMITMENT = "FINANCIAL_OR_LEGAL_COMMITMENT"
    PHYSICAL_HIGH_RISK = "PHYSICAL_HIGH_RISK"
    UNKNOWN_EFFECT = "UNKNOWN_EFFECT"


class EffectDecision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    DENY = "DENY"
    DEGRADE_TO_PROPOSAL = "DEGRADE_TO_PROPOSAL"


class AuthoritySource(str, Enum):
    AUTHENTICATED_USER = "AUTHENTICATED_USER"
    SYSTEM_POLICY = "SYSTEM_POLICY"
    RESEARCH_ENTITY = "RESEARCH_ENTITY"
    SELF_PROPOSAL_ONLY = "SELF_PROPOSAL_ONLY"


@dataclass(frozen=True)
class EffectRequest:
    actor: AuthoritySource
    action: str
    target: str
    effect_class: EffectClass
    authenticated: bool = False
    public_scope: bool = False
    scoped_capability: bool = False
    rollback_available: bool = False
    safe_replace: bool = False
    destination_resolved: bool = False
    payload_bound_to_user_intent: bool = False
    preauthorized_exact_change: bool = False
    destructive_kind: Optional[str] = None
    explicit_target: bool = False
    impact_preview: bool = False
    backup_state_known: bool = False
    no_backup_disclosed: bool = False
    dependency_impact_known: bool = False
    exact_scope: bool = False
    count_preview: bool = False
    recovery_receipt_available: bool = False
    owner_fixed_one_shot_recovery: bool = False
    security_subeffect_deny: bool = False
    physical_subeffect_deny: bool = False
    translator_claims_authority: bool = False
    model_confidence: float = 0.0
    gwt_ignition: bool = False
    claygraph_salience: float = 0.0

    def request_hash(self) -> str:
        data = asdict(self)
        for key in ("translator_claims_authority", "model_confidence", "gwt_ignition", "claygraph_salience"):
            data.pop(key, None)
        data["actor"] = self.actor.value
        data["effect_class"] = self.effect_class.value
        material = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ConfirmationReceipt:
    request_hash: str
    actor: AuthoritySource
    effect_class: EffectClass
    exact_target: str
    exact_action: str
    impact_summary: str
    confirmed_at: datetime
    expiry: Optional[datetime]
    nonce: str

    def receipt_hash(self) -> str:
        data = {
            "request_hash": self.request_hash,
            "actor": self.actor.value,
            "effect_class": self.effect_class.value,
            "exact_target": self.exact_target,
            "exact_action": self.exact_action,
            "impact_summary": self.impact_summary,
            "confirmed_at": self.confirmed_at.astimezone(timezone.utc).isoformat(),
            "expiry": self.expiry.astimezone(timezone.utc).isoformat() if self.expiry else None,
            "nonce": self.nonce,
        }
        material = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GateResult:
    decision: EffectDecision
    reason: str
    request_hash: str


@dataclass
class EffectAuthorityGate:
    used_confirmation_nonces: set[str] = field(default_factory=set)

    def evaluate(self, req: EffectRequest) -> GateResult:
        h = req.request_hash()
        authenticated_user = req.actor == AuthoritySource.AUTHENTICATED_USER and req.authenticated

        if req.effect_class == EffectClass.READ_ONLY:
            if authenticated_user or req.public_scope:
                return GateResult(EffectDecision.ALLOW, "read scope admitted", h)
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "read scope not authenticated/public", h)

        if req.effect_class == EffectClass.REVERSIBLE_WRITE:
            if authenticated_user and req.scoped_capability and (req.rollback_available or req.safe_replace):
                return GateResult(EffectDecision.ALLOW, "authenticated scoped reversible write", h)
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "reversible-write prerequisites incomplete", h)

        if req.effect_class == EffectClass.EXTERNAL_COMMUNICATION:
            if authenticated_user and req.destination_resolved and req.payload_bound_to_user_intent:
                return GateResult(EffectDecision.ALLOW, "destination and payload bound to authenticated intent", h)
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "communication binding incomplete", h)

        if req.effect_class == EffectClass.PRIVILEGED_CHANGE:
            if authenticated_user and req.preauthorized_exact_change:
                return GateResult(EffectDecision.ALLOW, "exact privileged change preauthorized", h)
            return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "privileged change requires exact confirmation", h)

        if req.effect_class == EffectClass.CREDENTIAL_SECURITY:
            if req.security_subeffect_deny:
                return GateResult(EffectDecision.DENY, "credential/security subeffect denied by deterministic policy", h)
            return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "credential/security effect requires confirmation", h)

        if req.effect_class == EffectClass.FINANCIAL_OR_LEGAL_COMMITMENT:
            return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "financial/legal commitment requires confirmation", h)

        if req.effect_class == EffectClass.PHYSICAL_HIGH_RISK:
            if req.physical_subeffect_deny:
                return GateResult(EffectDecision.DENY, "physical high-risk subeffect denied by deterministic policy", h)
            return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "physical high-risk effect requires confirmation", h)

        if req.effect_class == EffectClass.UNKNOWN_EFFECT:
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "unknown effect cannot execute", h)

        if req.effect_class == EffectClass.DESTRUCTIVE:
            return self._evaluate_destructive(req, h)

        return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "unrecognized effect class", h)

    def _evaluate_destructive(self, req: EffectRequest, h: str) -> GateResult:
        kind = (req.destructive_kind or "").upper()
        if kind in {"FORMAT_FILESYSTEM", "WIPE_DEVICE"}:
            if req.owner_fixed_one_shot_recovery and req.explicit_target:
                return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "owner-fixed one-shot recovery path still requires exact confirmation", h)
            return GateResult(EffectDecision.DENY, "format/wipe direct execution denied", h)

        if kind == "DELETE_DATA":
            guard_ok = req.explicit_target and req.impact_preview and (req.backup_state_known or req.no_backup_disclosed)
            return GateResult(
                EffectDecision.REQUIRE_CONFIRMATION if guard_ok else EffectDecision.DENY,
                "delete-data guard complete" if guard_ok else "delete-data guard incomplete",
                h,
            )

        if kind == "DELETE_ACCOUNT":
            return GateResult(
                EffectDecision.REQUIRE_CONFIRMATION if req.explicit_target else EffectDecision.DENY,
                "delete-account target explicit" if req.explicit_target else "delete-account target unresolved",
                h,
            )

        if kind == "DROP_DATABASE":
            guard_ok = req.explicit_target and req.backup_state_known and req.dependency_impact_known
            return GateResult(
                EffectDecision.REQUIRE_CONFIRMATION if guard_ok else EffectDecision.DENY,
                "drop-database guard complete" if guard_ok else "drop-database guard incomplete",
                h,
            )

        if kind == "MASS_DELETE":
            guard_ok = req.exact_scope and req.count_preview and (req.rollback_available or req.no_backup_disclosed)
            return GateResult(
                EffectDecision.REQUIRE_CONFIRMATION if guard_ok else EffectDecision.DENY,
                "mass-delete guard complete" if guard_ok else "mass-delete guard incomplete",
                h,
            )

        if kind == "IRREVERSIBLE_STATE_RESET":
            guard_ok = req.exact_scope and req.recovery_receipt_available
            return GateResult(
                EffectDecision.REQUIRE_CONFIRMATION if guard_ok else EffectDecision.DENY,
                "irreversible-reset guard complete" if guard_ok else "irreversible-reset guard incomplete",
                h,
            )

        return GateResult(EffectDecision.DENY, "unknown destructive subtype fails closed", h)

    def validate_confirmation(self, req: EffectRequest, receipt: ConfirmationReceipt, *, now: Optional[datetime] = None) -> GateResult:
        base = self.evaluate(req)
        h = base.request_hash
        now = now or datetime.now(timezone.utc)

        if base.decision != EffectDecision.REQUIRE_CONFIRMATION:
            return GateResult(base.decision, f"confirmation not applicable: {base.reason}", h)
        if receipt.confirmed_at.tzinfo is None or (receipt.expiry is not None and receipt.expiry.tzinfo is None):
            return GateResult(EffectDecision.DENY, "confirmation timestamp must be timezone-aware", h)
        if not receipt.nonce:
            return GateResult(EffectDecision.DENY, "confirmation nonce missing", h)
        if not receipt.impact_summary.strip():
            return GateResult(EffectDecision.DENY, "confirmation impact summary missing", h)
        confirmed_at = receipt.confirmed_at.astimezone(timezone.utc)
        expiry = receipt.expiry.astimezone(timezone.utc) if receipt.expiry is not None else None
        if confirmed_at > now:
            return GateResult(EffectDecision.DENY, "confirmation timestamp is in the future", h)
        if expiry is not None and expiry < confirmed_at:
            return GateResult(EffectDecision.DENY, "confirmation expiry precedes confirmation time", h)
        if expiry is not None and now >= expiry:
            return GateResult(EffectDecision.DENY, "stale confirmation", h)
        if (
            receipt.request_hash != h
            or receipt.effect_class != req.effect_class
            or receipt.exact_target != req.target
            or receipt.exact_action != req.action
        ):
            return GateResult(EffectDecision.DENY, "mismatched confirmation", h)
        if receipt.actor != AuthoritySource.AUTHENTICATED_USER or req.actor != AuthoritySource.AUTHENTICATED_USER or not req.authenticated:
            return GateResult(EffectDecision.DENY, "confirmation actor not authenticated user", h)
        return GateResult(EffectDecision.ALLOW, "exact confirmation validated", h)

    def apply_confirmation(self, req: EffectRequest, receipt: ConfirmationReceipt, *, now: Optional[datetime] = None) -> GateResult:
        validated = self.validate_confirmation(req, receipt, now=now)
        h = validated.request_hash
        if validated.decision != EffectDecision.ALLOW:
            return validated
        if receipt.nonce in self.used_confirmation_nonces:
            return GateResult(EffectDecision.DENY, "replayed confirmation", h)
        self.used_confirmation_nonces.add(receipt.nonce)
        return GateResult(EffectDecision.ALLOW, "exact one-shot confirmation admitted", h)
