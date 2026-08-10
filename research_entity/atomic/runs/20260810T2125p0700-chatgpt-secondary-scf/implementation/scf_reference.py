from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

TOKENS = (
    "SELF_ROOT_ID",
    "DIRECT_INTENT_AUTH",
    "EFFECT_AUTH",
    "RESEARCH_ACCEPTANCE_AUTH",
    "VERIFIED_OUTCOME_EVIDENCE",
    "RESEARCH_EVIDENCE",
    "CAUSAL_CREDIT",
)
IDX = {t: i for i, t in enumerate(TOKENS)}

ROLE_MINT = {
    "BOOT_ROOT": frozenset({"SELF_ROOT_ID"}),
    "TOKEN_AUTHENTICATOR": frozenset({"DIRECT_INTENT_AUTH"}),
    "EFFECT_GATE": frozenset({"EFFECT_AUTH"}),
    "EXTERNAL_VERIFIER": frozenset({"VERIFIED_OUTCOME_EVIDENCE", "RESEARCH_EVIDENCE"}),
    "RESEARCH_ENTITY": frozenset({"RESEARCH_ACCEPTANCE_AUTH"}),
    "CAUSAL_CREDIT_GATE": frozenset({"CAUSAL_CREDIT"}),
    "EPOCH_MIGRATOR": frozenset(),
}
RESTRICTED_SURFACES = frozenset({
    "RESEARCH_OR_ACCEPTANCE_RECEIPT", "HARNESS_SOURCE", "COGNITIVE_SOURCE",
    "SECURITY_POLICY", "WORKFLOW", "TEST_OR_FALSIFIER",
    "BUILD_OR_TOOLCHAIN", "DOCUMENTATION_POLICY",
})
ALLOWED_SURFACES = frozenset({
    "OPERATIONAL_STATE", "OPERATIONAL_EFFECT_QUEUE",
    "OPERATIONAL_TELEMETRY", "SELF_OBSERVATION_PROPOSAL",
})

@dataclass(frozen=True)
class Stamp:
    charges: Tuple[int, ...]
    epoch: int = 1

@dataclass(frozen=True)
class Transition:
    name: str
    delta: Tuple[int, ...]
    mint_rights: FrozenSet[str] = frozenset()
    trusted_role: Optional[str] = None
    epoch_out: Optional[int] = None
    repo_surface: Optional[str] = None
    cap_present: bool = True
    web_tainted: bool = False

ZERO = Stamp((0,) * len(TOKENS), 1)

def dvec(**kwargs):
    out = [0] * len(TOKENS)
    for key, value in kwargs.items():
        out[IDX[key]] = value
    return tuple(out)

def apply(before, transition):
    charges = tuple(max(0, a + b) for a, b in zip(before.charges, transition.delta))
    epoch = before.epoch if transition.epoch_out is None else transition.epoch_out
    return Stamp(charges, epoch)

def scf_check(before, transition, after):
    allowed = ROLE_MINT.get(transition.trusted_role, frozenset()) if transition.trusted_role else frozenset()
    if not transition.mint_rights.issubset(allowed):
        return False, "INVALID_MINT_CONTRACT"
    for token, idx in IDX.items():
        if after.charges[idx] > before.charges[idx]:
            if token not in transition.mint_rights:
                return False, "UNDECLARED_MINT:" + token
            if token not in allowed:
                return False, "UNTRUSTED_MINT:" + token
    if after.epoch != before.epoch and transition.trusted_role != "EPOCH_MIGRATOR":
        return False, "UNTRUSTED_EPOCH_CHANGE"
    return True, "PASS"

def surface_check(transition):
    if transition.repo_surface is None:
        return True
    if not transition.cap_present:
        return False
    if transition.repo_surface in RESTRICTED_SURFACES:
        return False
    if transition.repo_surface in ALLOWED_SURFACES:
        return True
    return False

def detect_scf(trace):
    state = ZERO
    for transition in trace:
        after = apply(state, transition)
        ok, _ = scf_check(state, transition, after)
        if not ok:
            return True
        state = after
    return False

def detect_surface(trace):
    return any(not surface_check(t) for t in trace)

def detect_surface_plus_scf(trace):
    state = ZERO
    for transition in trace:
        if not surface_check(transition):
            return True
        after = apply(state, transition)
        ok, _ = scf_check(state, transition, after)
        if not ok:
            return True
        state = after
    return False
