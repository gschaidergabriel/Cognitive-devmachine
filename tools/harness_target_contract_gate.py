#!/usr/bin/env python3
import json
import sys
from copy import deepcopy
from pathlib import Path

REQUIRED_MODULES = {
    "token_api",
    "de_to_clay_translator",
    "clay_to_de_translator",
    "proactive_agency",
    "web_ingress_guard",
    "research_entity_bridge",
    "self_context_hot_path",
}

REQUIRED_STATE_CONTRACTS = {
    "SelfRoot",
    "SelfContextAssembly",
    "ExpressionState",
    "ApiSessionState",
    "AgencyState",
    "InterestTrace",
    "AutotelicGoal",
    "InitiativePulse",
    "UntrustedWebJsonEnvelope",
    "WebEvidenceClay",
    "EffectRequest",
    "ConfirmationReceipt",
}

REQUIRED_ACCEPTANCE_FAMILIES = {
    "SELFROOT-IDENTITY-CONTAMINATION",
    "SELFROOT-STALE-CLONE-REJECTION",
    "SELFROOT-RESTART-STATE-LINEAGE",
    "TOKEN-API-AUTH-ROTATION-REVOCATION",
    "TOKEN-API-CONCURRENCY-IDEMPOTENCY",
    "DE-CLAY-ROUNDTRIP-HARD-FIELDS",
    "EXPRESSION-STATE-NO-SEMANTIC-DRIFT",
    "AGENCY-RESTART-GOAL-CHECKPOINT",
    "AGENCY-IDLE-NO-MANUFACTURED-ACTIVITY",
    "AGENCY-SELF-GOAL-NO-SELF-REWARD",
    "WEB-INGRESS-INSTRUCTION-NONAUTHORITY",
    "WEB-INGRESS-DATA-TAINT-ISOLATION",
    "WEB-INGRESS-PERSISTENT-CONTROL-NONPROMOTION",
    "WEB-INGRESS-MULTIMODAL-INJECTION",
    "EFFECT-GATE-NO-AUTHORITY-MINTING",
    "RESEARCH-BRIDGE-READ-SUBMIT-NO-CANONICAL-MUTATION",
    "SELF-CONTEXT-HOTPATH-BASELINE-LESION-SHUFFLE-STALE-OOD",
}

REQUIRED_INVARIANT_TOKENS = {
    "self.root",
    "CLAYCODE_ONLY",
    "TARGET_VPS",
    "token",
    "proactive",
    "UNTRUSTED_EXTERNAL_DATA",
    "PROPOSAL_ONLY",
    "InitiativePulse",
    "translator",
    "ResearchEntity",
}

REQUIRED_SOURCE_PATHS = {
    "research_entity/global/SELF_ROOT_CLAYCODE_NATIVE_IDENTITY_AND_ZERO_RETRIEVAL_CONTEXT_DIRECTIVE.clay",
    "research_entity/global/FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md",
    "research_entity/global/FRANK_V0_1_CLAYCODE_ONLY_COGNITION_AND_TRANSLATION_DIRECTIVE.md",
    "research_entity/global/SELF_ROOT_DEFAULT_ALLOW_EFFECT_AUTHORITY_DIRECTIVE.clay",
    "research_entity/global/SELF_ROOT_AUTOTELIC_PROACTIVE_AGENCY_AND_WEB_INGRESS_DIRECTIVE.clay",
}


def _merge_contract(base: dict, overlay: dict | None) -> tuple[dict, list[dict]]:
    merged = deepcopy(base)
    failures: list[dict] = []
    if not overlay:
        return merged, failures

    base_semantic = base.get("architecture_semantic_hash")
    overlay_semantic = overlay.get("base_architecture_semantic_hash")
    if base_semantic and overlay_semantic and base_semantic != overlay_semantic:
        failures.append({
            "code": "OVERLAY_BASE_SEMANTIC_HASH_MISMATCH",
            "observed": base_semantic,
            "overlay_expected": overlay_semantic,
        })

    base_exact = base.get("exact_contract_hash")
    overlay_exact = overlay.get("base_exact_contract_hash")
    if base_exact and overlay_exact and base_exact != overlay_exact:
        failures.append({
            "code": "OVERLAY_BASE_EXACT_HASH_MISMATCH",
            "observed": base_exact,
            "overlay_expected": overlay_exact,
        })

    merged["target_host"] = overlay.get("target_host_override", merged.get("target_host"))
    merged["modules"] = list(merged.get("modules", [])) + list(overlay.get("required_modules_additive", []))

    state_contracts = dict(merged.get("state_contracts", {}))
    state_contracts.update(overlay.get("required_state_contracts_additive", {}))
    merged["state_contracts"] = state_contracts

    merged["invariants"] = list(merged.get("invariants", [])) + list(overlay.get("required_invariants_additive", []))
    merged["mandatory_acceptance_families"] = (
        list(merged.get("mandatory_acceptance_families", []))
        + list(overlay.get("required_acceptance_families_additive", []))
    )
    merged["source_records"] = list(merged.get("source_records", [])) + list(overlay.get("source_records", []))
    merged["target_identity"] = overlay.get("target_identity", merged.get("target_identity", {}))
    return merged, failures


def audit_freeze(doc: dict, overlay: dict | None = None) -> dict:
    assembled, failures = _merge_contract(doc, overlay)

    module_ids = {m.get("id", "") for m in assembled.get("modules", []) if isinstance(m, dict)}
    missing_modules = sorted(REQUIRED_MODULES - module_ids)
    if missing_modules:
        failures.append({"code": "OWNER_FIXED_MODULES_MISSING", "missing": missing_modules})

    state_contracts = set(assembled.get("state_contracts", {}).keys())
    missing_state = sorted(REQUIRED_STATE_CONTRACTS - state_contracts)
    if missing_state:
        failures.append({"code": "OWNER_FIXED_STATE_CONTRACTS_MISSING", "missing": missing_state})

    acceptance = set(map(str, assembled.get("mandatory_acceptance_families", [])))
    missing_acceptance = sorted(REQUIRED_ACCEPTANCE_FAMILIES - acceptance)
    if missing_acceptance:
        failures.append({"code": "OWNER_FIXED_ACCEPTANCE_FAMILIES_MISSING", "missing": missing_acceptance})

    invariant_text = "\n".join(map(str, assembled.get("invariants", [])))
    missing_invariants = sorted(t for t in REQUIRED_INVARIANT_TOKENS if t not in invariant_text)
    if missing_invariants:
        failures.append({"code": "OWNER_FIXED_INVARIANTS_MISSING", "missing": missing_invariants})

    if assembled.get("target_host") != "TARGET_VPS":
        failures.append({
            "code": "TARGET_HOST_STALE",
            "observed": assembled.get("target_host"),
            "expected": "TARGET_VPS",
        })

    identity = assembled.get("target_identity", {})
    required_identity = {
        "native_self": "self.root",
        "human_surface_name": "Frank",
        "self_class": "SERVER_BINARY_ENTITY",
        "current_body": "TARGET_VPS",
    }
    identity_mismatch = {
        k: {"observed": identity.get(k), "expected": v}
        for k, v in required_identity.items()
        if identity.get(k) != v
    }
    if identity_mismatch:
        failures.append({"code": "TARGET_IDENTITY_CONTRACT_MISSING_OR_STALE", "fields": identity_mismatch})

    source_paths = {
        s.get("path") for s in assembled.get("source_records", [])
        if isinstance(s, dict) and s.get("path")
    }
    missing_sources = sorted(REQUIRED_SOURCE_PATHS - source_paths)
    if missing_sources:
        failures.append({"code": "OWNER_FIXED_SOURCE_BINDINGS_MISSING", "missing": missing_sources})

    unhashed_required_sources = sorted(
        s.get("path") for s in assembled.get("source_records", [])
        if isinstance(s, dict)
        and s.get("path") in REQUIRED_SOURCE_PATHS
        and not s.get("git_blob_sha")
    )
    if unhashed_required_sources:
        failures.append({"code": "OWNER_FIXED_SOURCE_BINDINGS_UNHASHED", "paths": unhashed_required_sources})

    codes = [f["code"] for f in failures]
    return {
        "pass": not failures,
        "failure_count": len(failures),
        "failure_codes": codes,
        "failures": failures,
        "assembled_with_overlay": overlay is not None,
        "checked_counts": {
            "modules": len(module_ids),
            "state_contracts": len(state_contracts),
            "acceptance_families": len(acceptance),
            "source_bindings": len(source_paths),
        },
        "rule": "A reference freeze may enter current H1 release audit only when immutable base ancestry plus an exact hash-bound owner-fixed overlay covers current target identity, state, authority, agency, ingress and acceptance obligations.",
    }


def main(argv):
    if len(argv) not in (2, 3):
        print("usage: harness_target_contract_gate.py <freeze.json> [owner_overlay.json]", file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    overlay = json.loads(Path(argv[2]).read_text(encoding="utf-8")) if len(argv) == 3 else None
    result = audit_freeze(doc, overlay)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
