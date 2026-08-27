#!/usr/bin/env python3
import itertools, json

CLASSIFIER_STATES = [
    "KNOWN_HIGH_CONFIDENCE",
    "KNOWN_NEEDS_CONFIRMATION",
    "AMBIGUOUS",
    "UNKNOWN",
    "CONFLICT",
]
SUPPORT_TIERS = ["GOLD", "SILVER", "BRONZE"]
VERIFY = ["NONE", "CONFIRMED", "CONTRADICTED"]
RISK = ["LOW", "HIGH"]

def current_fastpath_policy(state, support_tier, version_valid, contradiction,
                            verification, risk, capability):
    # Proxy of current candidate contract: KNOWN_HIGH may substantially bypass broad recognition;
    # authority is checked separately, but there is no explicit action-risk evidence floor.
    if not capability:
        return "DENY_AUTHORITY"
    if contradiction or verification == "CONTRADICTED":
        return "ESCALATE_DEEP"
    if state == "KNOWN_HIGH_CONFIDENCE" and version_valid:
        return "ALLOW_EFFECT"
    return "ESCALATE_DEEP"

def proposed_risk_sensitive_policy(state, support_tier, version_valid, contradiction,
                                   verification, risk, capability):
    if not capability:
        return "DENY_AUTHORITY"
    if contradiction or verification == "CONTRADICTED":
        return "ESCALATE_DEEP"
    if not version_valid:
        return "ESCALATE_DEEP"
    if support_tier == "BRONZE":
        return "ESCALATE_DEEP"
    if state != "KNOWN_HIGH_CONFIDENCE":
        return "ESCALATE_DEEP"
    if risk == "HIGH" and verification != "CONFIRMED":
        return "ESCALATE_DEEP"
    return "ALLOW_EFFECT"

def run():
    rows = []
    current_high_risk_familiarity_only = 0
    proposed_high_risk_familiarity_only = 0
    utility_low_risk_cases = 0
    utility_low_risk_allowed = 0
    valid_high_risk_confirmed = 0
    valid_high_risk_confirmed_allowed = 0
    invariant_failures = []

    for state, tier, version_valid, contradiction, verification, risk, capability in itertools.product(
        CLASSIFIER_STATES, SUPPORT_TIERS, [False, True], [False, True], VERIFY, RISK, [False, True]
    ):
        cur = current_fastpath_policy(state, tier, version_valid, contradiction, verification, risk, capability)
        prop = proposed_risk_sensitive_policy(state, tier, version_valid, contradiction, verification, risk, capability)
        row = {"state":state,"tier":tier,"version_valid":version_valid,"contradiction":contradiction,
               "verification":verification,"risk":risk,"capability":capability,"current":cur,"proposed":prop}
        rows.append(row)

        familiarity_only_high_risk = (
            risk == "HIGH" and capability and state == "KNOWN_HIGH_CONFIDENCE"
            and version_valid and not contradiction and verification == "NONE"
        )
        if familiarity_only_high_risk and cur == "ALLOW_EFFECT":
            current_high_risk_familiarity_only += 1
        if familiarity_only_high_risk and prop == "ALLOW_EFFECT":
            proposed_high_risk_familiarity_only += 1

        legitimate_low_risk = (
            risk == "LOW" and capability and state == "KNOWN_HIGH_CONFIDENCE"
            and tier in ("GOLD","SILVER") and version_valid and not contradiction
            and verification != "CONTRADICTED"
        )
        if legitimate_low_risk:
            utility_low_risk_cases += 1
            if prop == "ALLOW_EFFECT":
                utility_low_risk_allowed += 1

        legitimate_high_confirmed = (
            risk == "HIGH" and capability and state == "KNOWN_HIGH_CONFIDENCE"
            and tier in ("GOLD","SILVER") and version_valid and not contradiction
            and verification == "CONFIRMED"
        )
        if legitimate_high_confirmed:
            valid_high_risk_confirmed += 1
            if prop == "ALLOW_EFFECT":
                valid_high_risk_confirmed_allowed += 1

        if not capability and prop == "ALLOW_EFFECT": invariant_failures.append(("NO_CAPABILITY_ALLOWED", row))
        if state in ("UNKNOWN","AMBIGUOUS","CONFLICT","KNOWN_NEEDS_CONFIRMATION") and prop == "ALLOW_EFFECT": invariant_failures.append(("UNCERTAIN_ALLOWED", row))
        if tier == "BRONZE" and prop == "ALLOW_EFFECT": invariant_failures.append(("BRONZE_ALLOWED", row))
        if (not version_valid) and prop == "ALLOW_EFFECT": invariant_failures.append(("STALE_VERSION_ALLOWED", row))
        if risk == "HIGH" and verification != "CONFIRMED" and prop == "ALLOW_EFFECT": invariant_failures.append(("HIGH_RISK_WITHOUT_CONFIRMATION", row))
        if (contradiction or verification == "CONTRADICTED") and prop == "ALLOW_EFFECT": invariant_failures.append(("CONTRADICTION_ALLOWED", row))

    result = {
        "evidence_class":"SYNTHETIC_HOSTED_PYTHON_MODEL",
        "state_space_cases":len(rows),
        "counterexample": {
            "current_policy_high_risk_familiarity_only_allows": current_high_risk_familiarity_only,
            "proposed_policy_high_risk_familiarity_only_allows": proposed_high_risk_familiarity_only,
            "interpretation":"Separate capability checking does not prevent a false-but-high-confidence familiarity result from becoming the sole epistemic basis of an already-authorized high-risk action."
        },
        "utility_checks": {
            "legitimate_low_risk_fastpath_cases": utility_low_risk_cases,
            "legitimate_low_risk_allowed": utility_low_risk_allowed,
            "legitimate_high_risk_confirmed_cases": valid_high_risk_confirmed,
            "legitimate_high_risk_confirmed_allowed": valid_high_risk_confirmed_allowed
        },
        "proposed_policy_invariant_failures": len(invariant_failures),
        "result":"PASS_WITH_ARCHITECTURE_COUNTEREXAMPLE" if current_high_risk_familiarity_only > 0 and not invariant_failures else "FAIL",
        "scope_limit":"Pure state-space model; does not measure real visual accuracy, real UI risk, or Ubuntu target-host behavior."
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    run()
