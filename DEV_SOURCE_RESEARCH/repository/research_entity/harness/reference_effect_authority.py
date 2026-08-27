from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Set, Tuple
import hashlib
import json


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
    rollback_or_safe_replace: bool = False
    destination_resolved: bool = False
    payload_bound_to_user_intent: bool = False
    preauthorized_exact_change: bool = False
    owner_fixed_recovery_protocol: bool = False
    explicit_target: bool = False
    impact_preview: bool = False
    backup_state_disclosed: bool = False
    exact_scope: bool = False
    count_preview: bool = False
    recovery_receipt_ready: bool = False
    untrusted_effect_class_hint: Optional[EffectClass] = None
    model_confidence: float = 0.0
    gwt_ignition: float = 0.0
    claygraph_salience: float = 0.0

    def request_hash(self) -> str:
        canonical = {
            "actor": self.actor.value,
            "action": self.action,
            "target": self.target,
            "effect_class": self.effect_class.value,
        }
        return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class ConfirmationReceipt:
    request_hash: str
    actor: AuthoritySource
    effect_class: EffectClass
    exact_target: str
    exact_action: str
    confirmed_at: datetime
    nonce: str
    expiry: Optional[datetime] = None


@dataclass(frozen=True)
class GateResult:
    decision: EffectDecision
    reason: str
    requirements: Tuple[str, ...] = field(default_factory=tuple)


class EffectGate:
    """Deterministic H1 reference gate for owner-fixed self.root effect authority.

    The trusted effect_class is architecture state. Translator/model/GWT/ClayGraph hints are
    observational inputs only and never mint or downgrade authority.
    """

    def __init__(self) -> None:
        self._used_confirmation_nonces: Set[str] = set()

    @staticmethod
    def _is_authenticated_user(req: EffectRequest) -> bool:
        return req.actor == AuthoritySource.AUTHENTICATED_USER and req.authenticated

    def _confirmation_valid(self, req: EffectRequest, receipt: Optional[ConfirmationReceipt]) -> GateResult | None:
        if receipt is None:
            return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "confirmation_required")
        now = datetime.now(timezone.utc)
        if receipt.expiry is not None and receipt.expiry < now:
            return GateResult(EffectDecision.DENY, "stale_confirmation")
        if receipt.nonce in self._used_confirmation_nonces:
            return GateResult(EffectDecision.DENY, "replayed_confirmation")
        if (
            receipt.request_hash != req.request_hash()
            or receipt.actor != req.actor
            or receipt.effect_class != req.effect_class
            or receipt.exact_target != req.target
            or receipt.exact_action != req.action
        ):
            return GateResult(EffectDecision.DENY, "mismatched_confirmation")
        self._used_confirmation_nonces.add(receipt.nonce)
        return None

    def evaluate(self, req: EffectRequest, confirmation: Optional[ConfirmationReceipt] = None) -> GateResult:
        c = req.effect_class

        if c == EffectClass.UNKNOWN_EFFECT:
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "unknown_effect")

        if c == EffectClass.READ_ONLY:
            if self._is_authenticated_user(req) or req.public_scope:
                return GateResult(EffectDecision.ALLOW, "read_scope_valid")
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "read_scope_unresolved")

        if c == EffectClass.REVERSIBLE_WRITE:
            if self._is_authenticated_user(req) and req.scoped_capability and req.rollback_or_safe_replace:
                return GateResult(EffectDecision.ALLOW, "authenticated_scoped_reversible_write")
            return GateResult(
                EffectDecision.DEGRADE_TO_PROPOSAL,
                "reversible_write_preconditions_missing",
                tuple(k for k, ok in (
                    ("authenticated_user", self._is_authenticated_user(req)),
                    ("scoped_capability", req.scoped_capability),
                    ("rollback_or_safe_replace", req.rollback_or_safe_replace),
                ) if not ok),
            )

        if c == EffectClass.EXTERNAL_COMMUNICATION:
            if self._is_authenticated_user(req) and req.destination_resolved and req.payload_bound_to_user_intent:
                return GateResult(EffectDecision.ALLOW, "authenticated_external_communication")
            return GateResult(EffectDecision.DEGRADE_TO_PROPOSAL, "external_communication_scope_unresolved")

        if c == EffectClass.PRIVILEGED_CHANGE:
            if req.preauthorized_exact_change:
                return GateResult(EffectDecision.ALLOW, "exact_preauthorized_privileged_change")
            return self._confirmation_valid(req, confirmation) or GateResult(EffectDecision.ALLOW, "confirmed_privileged_change")

        if c == EffectClass.CREDENTIAL_SECURITY:
            return self._confirmation_valid(req, confirmation) or GateResult(EffectDecision.ALLOW, "confirmed_credential_security_effect")

        if c == EffectClass.FINANCIAL_OR_LEGAL_COMMITMENT:
            return self._confirmation_valid(req, confirmation) or GateResult(EffectDecision.ALLOW, "confirmed_financial_or_legal_commitment")

        if c == EffectClass.PHYSICAL_HIGH_RISK:
            return self._confirmation_valid(req, confirmation) or GateResult(EffectDecision.ALLOW, "confirmed_physical_high_risk_effect")

        if c == EffectClass.DESTRUCTIVE:
            action = req.action.upper()
            if action in {"FORMAT_FILESYSTEM", "WIPE_DEVICE"}:
                if req.owner_fixed_recovery_protocol and req.explicit_target:
                    return GateResult(EffectDecision.ALLOW, "owner_fixed_one_shot_recovery_protocol")
                return GateResult(EffectDecision.DENY, "direct_format_or_wipe_forbidden")

            required = []
            if not req.explicit_target:
                required.append("explicit_target")

            if action == "DELETE_DATA":
                if not req.impact_preview:
                    required.append("impact_preview")
                if not req.backup_state_disclosed:
                    required.append("backup_or_no_backup_disclosure")
            elif action == "DELETE_ACCOUNT":
                if not req.impact_preview:
                    required.append("irreversibility_warning")
            elif action == "DROP_DATABASE":
                if not req.backup_state_disclosed:
                    required.append("backup_state")
                if not req.impact_preview:
                    required.append("dependency_impact")
            elif action == "MASS_DELETE":
                if not req.exact_scope:
                    required.append("exact_scope")
                if not req.count_preview:
                    required.append("count_preview")
                if not req.backup_state_disclosed:
                    required.append("rollback_state")
            elif action == "IRREVERSIBLE_STATE_RESET":
                if not req.exact_scope:
                    required.append("explicit_scope")
                if not req.recovery_receipt_ready:
                    required.append("recovery_receipt")
            else:
                required.append("recognized_destructive_subeffect")

            if required:
                return GateResult(EffectDecision.REQUIRE_CONFIRMATION, "destructive_guard_incomplete", tuple(required))

            return self._confirmation_valid(req, confirmation) or GateResult(EffectDecision.ALLOW, "confirmed_destructive_effect")

        raise AssertionError(f"Unhandled effect class: {c}")
