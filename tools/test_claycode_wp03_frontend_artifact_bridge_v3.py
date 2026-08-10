#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_frontend_artifact_bridge as bridge_v2
import claycode_wp03_frontend_artifact_bridge_v3 as bridge_v3
import claycode_wp03_typed_ir_v2_state_identity as typed_v2

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
    ROOT / "research_entity/claycode/base/fixtures/WP03_MVC_TYPED_STATE_V1.clay",
    ROOT / "research_entity/claycode/base/fixtures/WP03_ABA_VERSIONED_STATE_V1.clay",
]
SURFACE = "BASE_D_V18_REWARD_RELATIONS"


def expect_error(fn, marker: str) -> str:
    try:
        fn()
    except bridge_v3.FrontendBindingV3Error as exc:
        text = str(exc)
        assert marker in text, (marker, text)
        return text
    raise AssertionError("expected FrontendBindingV3Error")


def materialize_manifest(tmp: Path) -> tuple[dict, dict]:
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    grammar_copy = tmp / "V18.lark"
    grammar_copy.write_text(grammar_text, encoding="utf-8")
    units = []
    source_units = []
    for idx, source in enumerate(SOURCES):
        source_copy = tmp / f"source-{idx}.clay"
        source_copy.write_bytes(source.read_bytes())
        doc = front.compile_frontend(source_copy.read_text(encoding="utf-8"), grammar_text, strict=True)
        artifact = tmp / f"artifact-{idx}.json"
        artifact.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        units.append({
            "artifact": str(artifact),
            "source": str(source_copy),
            "grammar": str(grammar_copy),
            "expected_surface": SURFACE,
        })
        source_units.append(typed.SourceUnit(source_copy, doc))
    direct = typed_v2.build_typed_ir_v2(source_units)
    return {"units": units}, direct


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="clay-wp03-bridge-v3-") as td:
        tmp = Path(td)
        manifest, direct = materialize_manifest(tmp)

        original = front.build_parser
        parser_calls = 0
        def forbidden(*args, **kwargs):
            nonlocal parser_calls
            parser_calls += 1
            raise AssertionError("silent downstream reparse attempted")
        front.build_parser = forbidden
        try:
            bridged = bridge_v3.compile_manifest(manifest)
        finally:
            front.build_parser = original

        ir = bridged["typed_ir"]
        assert parser_calls == 0
        assert ir["typed_ir_sha256"] == direct["typed_ir_sha256"]
        assert typed_v2.stable_json(ir) == typed_v2.stable_json(direct)
        assert bridged["bridge_schema"] == bridge_v3.BRIDGE_SCHEMA
        assert len(bridged["frontend_bindings"]) == 4
        assert bridged["wp03_status"] == "OPEN_PENDING_EXACT_CURRENT_ADJUDICATION"
        assert bridged["promotion"] == "NONE"

        sums = {x["name"]: x for x in ir["declarations"] if x.get("kind") == "sum_type"}
        for name in ("EvidenceTier", "FamiliarityResult", "LearnerStage", "AtomicIdentityMode", "CasStrength", "AtomicOrdering"):
            assert name in sums, name
        records = {x["name"]: x for x in ir["structural_records"]}
        for name in ("VisualClassifierVersion", "VisualLearnerState", "AtomicCell", "CompareExchangeOutcome"):
            assert name in records, name

        mvc_state = {
            "version": "mvc-9",
            "feature_backbone_version": "clip-3",
            "stage": "CURRENT",
            "prototype_state_ref": "proto:9",
            "readout_state_ref": None,
            "calibration_ref": "cal:9",
            "training_examples": ["ex:2", "ex:1"],
            "evaluation_receipts": ["receipt:b", "receipt:a"],
            "parent_version": "mvc-8",
            "semantic_hash": "hash:9",
        }
        mvc_next = {**mvc_state, "version": "mvc-10"}
        assert typed_v2.typed_state_identity(ir, "VisualClassifierVersion", mvc_state)["state_identity_sha256"] != typed_v2.typed_state_identity(ir, "VisualClassifierVersion", mvc_next)["state_identity_sha256"]

        wrong_surface = copy.deepcopy(manifest)
        wrong_surface["units"][0]["expected_surface"] = "FORGED_SURFACE"
        expect_error(lambda: bridge_v3.compile_manifest(wrong_surface), "surface mismatch")

        duplicate = copy.deepcopy(manifest)
        duplicate["units"].append(copy.deepcopy(duplicate["units"][0]))
        expect_error(lambda: bridge_v3.compile_manifest(duplicate), "duplicate frontend artifact")

        tampered_artifact = copy.deepcopy(manifest)
        artifact_path = Path(tampered_artifact["units"][0]["artifact"])
        doc = json.loads(artifact_path.read_text(encoding="utf-8"))
        original_doc = copy.deepcopy(doc)
        doc["semantic_hash"] = "0" * 64
        artifact_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        expect_error(lambda: bridge_v3.compile_manifest(tampered_artifact), "semantic hash mismatch")
        artifact_path.write_text(json.dumps(original_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        report = {
            "status": "PASS",
            "scope": "WP03_FRONTEND_ARTIFACT_BRIDGE_V3_STRUCTURAL_TYPEDIR",
            "bridge_schema": bridged["bridge_schema"],
            "typed_ir_sha256": ir["typed_ir_sha256"],
            "typed_ir_artifact_sha256": bridged["typed_ir_artifact_sha256"],
            "frontend_bindings": len(bridged["frontend_bindings"]),
            "parser_calls_after_artifact_creation": parser_calls,
            "direct_vs_bridge_semantic_identity": "MATCH",
            "closed_sum_types": len(sums),
            "mvc_version_identity": "DISTINCT_ON_VERSION_CHANGE",
            "surface_tamper": "REJECTED",
            "duplicate_source_artifact": "REJECTED",
            "semantic_hash_tamper": "REJECTED",
            "authority": "NONE",
            "promotion": "NONE",
            "wp03_status": bridged["wp03_status"],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
