#!/usr/bin/env python3
"""Fail-closed cross-source discriminator for the G9 V3 -> Frank v0.1 effect boundary.

The current target Frank effect API is captured as a provenance-bound evidence snapshot.
This probe checks whether the current G9 V3 direct effect call is structurally compatible
with that exact target API. It never invents a production signature or grants authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
SNAPSHOT = Path(__file__).with_name("TARGET_FRANK_EFFECT_CONTRACT_SNAPSHOT.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_fields(source: str, record_name: str) -> list[str]:
    m = re.search(rf"\brecord\s+{re.escape(record_name)}\s*\{{(?P<body>.*?)\n\}}", source, re.S)
    if not m:
        raise RuntimeError(f"record {record_name} not found")
    out: list[str] = []
    for line in m.group("body").splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        fm = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", line)
        if fm:
            out.append(fm.group(1))
    return out


def main() -> int:
    g9 = G9.read_text(encoding="utf-8")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    expected_blob = snap["g9_binding"]["git_blob_sha"]
    # Git blob SHA and file SHA-256 are different identities. The blob is retained as
    # provenance only; exact local content is checked structurally below.
    g9_fields = record_fields(g9, "EffectIntent")
    direct = re.search(r"\bNeedle\.execute\s*\(\s*effect_intent\s*\)", g9)
    lowering = re.search(r"\brule\s+Needle\.lowers\s+EffectIntent\s*->\s*concrete_adapter_plan\b", g9)
    if not direct or not lowering:
        raise RuntimeError("current G9 V3 no longer matches the bound direct-call hypothesis")

    target_execute = next(c for c in snap["contracts"] if c["target"] == "frank.effects.execute")
    target_fields = snap["target_effect_intent_fields"]

    direct_call_arity = 1
    target_execute_arity = len(target_execute["params"])
    common_fields = sorted(set(g9_fields) & set(target_fields))
    missing_target_fields = [f for f in target_fields if f not in g9_fields]

    required_chain = [
        "frank.effects.decide_effect",
        "frank.effects.authorize_effect",
        "frank.effects.reserve_effect",
        "frank.effects.begin_effect_attempt",
        "frank.effects.execute",
        "frank.effects.verify_effect",
        "frank.effects.finish",
    ]
    available = {c["target"] for c in snap["contracts"]}
    missing_chain = [x for x in required_chain if x not in available]

    incompatible = (
        direct_call_arity != target_execute_arity
        and g9_fields != target_fields
        and not missing_chain
    )
    if not incompatible:
        raise RuntimeError("bound mismatch hypothesis was not reproduced; re-adjudicate instead of promoting")

    result = {
        "schema_version": "1.0",
        "test": "CC_G9_V3_TO_FRANK_V01_EFFECT_BOUNDARY_COMPATIBILITY",
        "pass": True,
        "compatibility": "INCOMPATIBLE_FAIL_CLOSED",
        "promotion": "NONE",
        "g9": {
            "path": str(G9.relative_to(ROOT)),
            "sha256": sha256(G9),
            "provenance_git_blob_sha": expected_blob,
            "direct_call": "Needle.execute(effect_intent)",
            "direct_call_arity": direct_call_arity,
            "declared_lowering_before_execute": True,
            "effect_intent_fields": g9_fields,
        },
        "target_snapshot": {
            "source": snap["source"],
            "execute_contract": target_execute,
            "execute_arity": target_execute_arity,
            "effect_intent_fields": target_fields,
            "required_pipeline_contracts": required_chain,
            "missing_pipeline_contracts": missing_chain,
        },
        "mismatch": {
            "arity": {"g9_direct": direct_call_arity, "target_execute": target_execute_arity},
            "effect_intent_common_fields": common_fields,
            "target_fields_not_explicit_in_g9_effect_intent": missing_target_fields,
            "authority_lifecycle_bypass_risk": True,
        },
        "interpretation": (
            "The current G9 V3 direct Needle.execute(effect_intent) call cannot be bound "
            "as-is to the provenance-bound current Frank v0.1 effect API. The target execute "
            "contract requires EffectIntent<T>, Capability, NodeId and EffectAttempt, while "
            "authorization/reservation/attempt creation are explicit preceding contracts. "
            "This is an implementation/type-effect boundary defect, not evidence that frozen "
            "ClayCode language semantics must change."
        ),
        "next_falsifier": (
            "Implement a deterministic typed Needle boundary adapter using only current trusted "
            "state and exact production contracts, then prove on the target VPS that cognitive "
            "intent cannot supply or mint authenticated actor/capability/authorization/attempt "
            "fields and that the resulting request->authorization->reservation->attempt->execute"
            "->verify->reentry path is exact-current and fail-closed under stale/tampered inputs."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
