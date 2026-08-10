#!/usr/bin/env python3
"""CC-WP-03 V18 FrontendArtifact -> TypedIR bridge validation.

Runs the exact selected V18 frontend first, then proves the bridge consumes those artifacts
without calling the parser again. Includes fail-closed contract drift/tamper controls and the
semantic-vs-state identity discriminator required by the WP03 frontier.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import claycode_base_frontend as front
import claycode_base_typed_ir_v18_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"

AGENCY_INGRESS_FIXTURE = """\
module clay.wp03.fixture
record AgencyState { interests:Set<InterestTrace>; goals:Set<AutotelicGoal>; pulse:InitiativePulse; epoch:Epoch }
record InterestTrace { topic:Symbol; score:Float }
record AutotelicGoal { id:GoalRef; state:Symbol; checkpoint:GoalCheckpoint? }
record GoalCheckpoint { goal:GoalRef; epoch:Epoch }
record InitiativePulse { amplitude:Float }
record UntrustedWebJsonEnvelope { payload:Ref; instruction_authority:Symbol; effect_authority:Symbol; provenance:EvidenceRef }
record WebEvidenceClay { envelope:UntrustedWebJsonEnvelope; evidence:EvidenceRef }
record AuthenticatedDirectMessage { caller:AuthorityRef; scope:Set<Constraint>; intent:IntentRef }
"""


def expect_reject(label: str, artifact: dict, mutate) -> dict:
    bad = copy.deepcopy(artifact)
    mutate(bad)
    try:
        bridge.validate_frontend_artifact(bad)
    except bridge.V18BridgeError as exc:
        return {"case": label, "pass": True, "error": str(exc)}
    return {"case": label, "pass": False, "error": "unexpected_accept"}


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    sources = [(G9, G9.read_text(encoding="utf-8")), (DIALECT, DIALECT.read_text(encoding="utf-8"))]
    artifacts = [(path, front.compile_frontend(text, grammar, strict=True)) for path, text in sources]
    fixture_path = Path("WP03_AGENCY_INGRESS_FIXTURE.clay")
    fixture_artifact = front.compile_frontend(AGENCY_INGRESS_FIXTURE, grammar, strict=True)

    original_compile = front.compile_frontend

    def forbidden_reparse(*args, **kwargs):
        raise AssertionError("bridge attempted silent source reparse")

    front.compile_frontend = forbidden_reparse
    try:
        a = bridge.build_from_artifacts(artifacts, state_epoch=7, state_version=3)
        b = bridge.build_from_artifacts(artifacts, state_epoch=8, state_version=3)
        fixture = bridge.build_from_artifacts([(fixture_path, fixture_artifact)], state_epoch=7, state_version=3)
    finally:
        front.compile_frontend = original_compile

    same_semantic_different_epoch = {
        "semantic_same": a["semantic_identity"] == b["semantic_identity"],
        "state_instance_different": a["state_identity"]["state_instance_id"] != b["state_identity"]["state_instance_id"],
    }
    same_semantic_different_epoch["pass"] = all(same_semantic_different_epoch.values())

    mutated_g9 = sources[0][1].replace("logical_time:Epoch", "logical_time:Version", 1)
    if mutated_g9 == sources[0][1]:
        raise AssertionError("semantic mutation anchor missing")
    mutated_artifact = original_compile(mutated_g9, grammar, strict=True)
    front.compile_frontend = forbidden_reparse
    try:
        c = bridge.build_from_artifacts([(G9, mutated_artifact), artifacts[1]], state_epoch=7, state_version=3)
    finally:
        front.compile_frontend = original_compile
    same_epoch_semantic_mutation = {
        "semantic_different": a["semantic_identity"] != c["semantic_identity"],
        "epoch_same": a["state_identity"]["state_epoch"] == c["state_identity"]["state_epoch"],
    }
    same_epoch_semantic_mutation["pass"] = all(same_epoch_semantic_mutation.values())

    fixture_names = {d["name"] for d in fixture["typed_ir"]["declarations"]}
    required_fixture_names = {
        "AgencyState", "InterestTrace", "AutotelicGoal", "GoalCheckpoint", "InitiativePulse",
        "UntrustedWebJsonEnvelope", "WebEvidenceClay", "AuthenticatedDirectMessage",
    }
    fixture_check = {
        "required_names": sorted(required_fixture_names),
        "observed_names": sorted(fixture_names),
        "missing": sorted(required_fixture_names - fixture_names),
        "any_type_present": any(t["name"] == "Any" for t in fixture["typed_ir"]["types"]),
    }
    fixture_check["pass"] = not fixture_check["missing"] and not fixture_check["any_type_present"]

    base_artifact = artifacts[0][1]
    negatives = [
        expect_reject("semantic_hash_tamper", base_artifact, lambda x: x.__setitem__("semantic_hash", "0" * 64)),
        expect_reject("grammar_drift", base_artifact, lambda x: x.__setitem__("grammar_sha256", "0" * 64)),
        expect_reject("surface_drift", base_artifact, lambda x: x.__setitem__("surface", "BASE_D_V17_DECLARATIVE_TRIVIA_SAFE")),
    ]

    typed = a["typed_ir"]
    full_check = {
        "declaration_count": len(typed["declarations"]),
        "type_count": len(typed["types"]),
        "unknown_type_to_any_forbidden": typed["invariants"].get("unknown_type_to_any") == "FORBIDDEN",
        "authority_none": all(d.get("authority") == "NONE" for d in typed["declarations"]),
        "no_reparse_mode": a.get("mode") == "FRONTEND_ARTIFACT_NO_REPARSE",
        "frontend_contract_count": len(a.get("frontend_contracts", [])),
    }
    full_check["pass"] = (
        full_check["declaration_count"] > 0
        and full_check["type_count"] > 0
        and full_check["unknown_type_to_any_forbidden"]
        and full_check["authority_none"]
        and full_check["no_reparse_mode"]
        and full_check["frontend_contract_count"] == 2
    )

    passed = (
        full_check["pass"]
        and fixture_check["pass"]
        and same_semantic_different_epoch["pass"]
        and same_epoch_semantic_mutation["pass"]
        and all(x["pass"] for x in negatives)
    )
    out = {
        "schema_version": "1.0",
        "test": "CC_WP03_V18_FRONTEND_TYPEDIR_BRIDGE_VALIDATION",
        "grammar_sha256_expected": bridge.EXPECTED_GRAMMAR_SHA256,
        "surface_expected": bridge.EXPECTED_SURFACE,
        "full_current_sources": full_check,
        "agency_ingress_fixture": fixture_check,
        "identity_cross_control": {
            "same_semantics_different_epoch": same_semantic_different_epoch,
            "same_epoch_semantic_mutation": same_epoch_semantic_mutation,
        },
        "negative_controls": negatives,
        "scope_guard": "PASS is an executable CC-WP03 candidate receipt only. Target-VPS execution against exact committed component bytes is still required before package promotion.",
        "pass": passed,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
