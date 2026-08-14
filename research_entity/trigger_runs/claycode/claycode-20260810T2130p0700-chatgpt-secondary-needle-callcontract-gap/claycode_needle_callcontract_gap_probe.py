#!/usr/bin/env python3
"""Fail-closed discriminator for the current ClayCode Needle effect-call contract gap.

This probe does not invent or promote a production CallContract.  It only checks whether
the current G9 V3 effect path can be justified by an exact executable contract from its
own source, its direct parent, and the owner-fixed effect-authority directive.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
V3 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
V2 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V2.clay"
EFFECT = ROOT / "research_entity/global/SELF_ROOT_DEFAULT_ALLOW_EFFECT_AUTHORITY_DIRECTIVE.clay"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    v3 = V3.read_text(encoding="utf-8")
    v2 = V2.read_text(encoding="utf-8")
    effect = EFFECT.read_text(encoding="utf-8")

    v3_lower = bool(re.search(r"\brule\s+Needle\.lowers\s+EffectIntent\s*->\s*concrete_adapter_plan\b", v3))
    v3_direct_execute = bool(re.search(r"\breceipt\s*=\s*Needle\.execute\s*\(\s*effect_intent\s*\)", v3))
    v3_exact_execute_decl = bool(re.search(r"(?im)^\s*(?:needle|fn)\s+Needle?\.?execute\s*\(", v3))

    v2_effectplan_execute = bool(
        re.search(r"(?im)^\s*needle\s+execute\s*\(\s*EffectPlan\s*\)\s*->\s*EffectReceipt\s*$", v2)
    )
    owner_effect_request = "record EffectRequest" in effect
    owner_deterministic_gate = (
        "DESTRUCTIVE" in effect
        and "EffectDecision" in effect
        and "rollback" in effect
        and "model_confidence cannot mint authority" in effect
    )

    gap_detected = (
        v3_lower
        and v3_direct_execute
        and not v3_exact_execute_decl
        and v2_effectplan_execute
        and owner_effect_request
        and owner_deterministic_gate
    )

    result = {
        "schema_version": "1.0",
        "test": "CC_V18_NEEDLE_EFFECT_CALLCONTRACT_GAP_DISCRIMINATOR",
        "pass": gap_detected,
        "gap_detected": gap_detected,
        "source_identity": {
            str(V3.relative_to(ROOT)): sha256(V3),
            str(V2.relative_to(ROOT)): sha256(V2),
            str(EFFECT.relative_to(ROOT)): sha256(EFFECT),
        },
        "observations": {
            "v3_declares_effectintent_lowering": v3_lower,
            "v3_cycle_calls_needle_execute_with_effectintent": v3_direct_execute,
            "v3_exact_needle_execute_declaration_present": v3_exact_execute_decl,
            "v2_parent_executes_effectplan_to_effectreceipt": v2_effectplan_execute,
            "owner_effect_request_semantics_present": owner_effect_request,
            "owner_deterministic_effect_gate_semantics_present": owner_deterministic_gate,
        },
        "interpretation": (
            "Current G9 V3 has an unresolved effect-call contract boundary: the cycle passes "
            "EffectIntent directly to Needle.execute although V3 separately requires lowering, "
            "the direct parent exposes execute(EffectPlan)->EffectReceipt, and the owner-fixed "
            "effect policy requires deterministic EffectRequest/EffectDecision semantics. "
            "This probe does not select a replacement signature."
        ),
        "promotion": "NONE",
        "next_falsifier": (
            "Materialize and execute an exact current ClayCode effect pipeline only from explicit "
            "evidence: EffectIntent -> lowering/runtime plan -> deterministic EffectGate request/"
            "decision -> sealed current binding -> Needle execution -> verified EffectReceipt. "
            "If a different exact current contract is found, this gap hypothesis is refuted."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if gap_detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
