#!/usr/bin/env python3
"""Full V18 FrontendArtifact -> residual TypedIR bridge/tamper falsifier for CC-WP-03.

Normal discriminating test, not an out-of-box experiment. It deliberately compiles frontend
artifacts once, then disables parser construction so the downstream bridge/candidate path must
consume the admitted artifacts without silently reparsing source bytes.
"""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

import claycode_base_frontend as front
import claycode_wp03_frontend_artifact_bridge as bridge
import claycode_wp03_residual_semantics_candidate as candidate

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
EXPECTED_SURFACE = "BASE_D_V18_REWARD_RELATIONS"


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reject(label: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        fn()
    except bridge.FrontendBindingError as exc:
        return {"case": label, "rejected": True, "error": str(exc)}
    return {"case": label, "rejected": False, "error": "unexpected_accept"}


def main() -> int:
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="clay-wp03-bridge-") as td:
        tmp = Path(td)
        specs: list[dict[str, str]] = []
        docs: list[dict[str, Any]] = []
        copied_sources: list[Path] = []
        grammar_copy = tmp / "V18.lark"
        grammar_copy.write_text(grammar_text, encoding="utf-8")

        # The only parser use in this test: produce accepted WP02 FrontendArtifacts once.
        for index, source in enumerate(SOURCES):
            source_copy = tmp / f"source-{index}.clay"
            source_copy.write_bytes(source.read_bytes())
            artifact = tmp / f"artifact-{index}.json"
            doc = front.compile_frontend(source_copy.read_text(encoding="utf-8"), grammar_text, strict=True)
            assert doc["surface"] == EXPECTED_SURFACE
            dump(artifact, doc)
            specs.append({
                "artifact": str(artifact),
                "source": str(source_copy),
                "grammar": str(grammar_copy),
                "expected_surface": EXPECTED_SURFACE,
            })
            docs.append(doc)
            copied_sources.append(source_copy)

        original_build_parser = front.build_parser
        parser_calls = 0

        def forbidden_parser(*args: Any, **kwargs: Any) -> Any:
            nonlocal parser_calls
            parser_calls += 1
            raise AssertionError("silent downstream reparse attempted")

        front.build_parser = forbidden_parser
        try:
            units = []
            bindings = []
            for spec in specs:
                unit, binding = bridge.verify_frontend_unit(spec)
                units.append(unit)
                bindings.append(binding)
            residual = candidate.build_typed_ir(units)
        finally:
            front.build_parser = original_build_parser

        opaque = residual.get("opaque_unlowered_semantics", [])
        full_bridge = {
            "parser_calls_after_frontend_artifact_creation": parser_calls,
            "unit_count": len(units),
            "binding_count": len(bindings),
            "all_surfaces_v18": all(x["surface"] == EXPECTED_SURFACE for x in bindings),
            "all_grammar_hashes_match": len({x["grammar_sha256"] for x in bindings}) == 1,
            "opaque_unlowered_semantics_count": len(opaque),
            "lowering_status": residual.get("lowering_status"),
            "typed_ir_sha256": residual.get("typed_ir_sha256"),
            "opaque_semantics_mint_effect_authority": residual.get("invariants", {}).get("opaque_semantics_mint_effect_authority"),
        }
        full_bridge["pass"] = bool(
            parser_calls == 0
            and len(units) == len(SOURCES)
            and full_bridge["all_surfaces_v18"]
            and full_bridge["all_grammar_hashes_match"]
            and len(opaque) > 0
            and residual.get("lowering_status") == "PARTIAL_CONSERVATIVE_PRESERVATION"
            and full_bridge["opaque_semantics_mint_effect_authority"] == "FORBIDDEN"
        )

        tamper: list[dict[str, Any]] = []
        bad_surface = dict(specs[0])
        bad_surface["expected_surface"] = "BASE_D_FAKE_SURFACE"
        tamper.append(reject("expected_surface_mismatch", lambda: bridge.verify_frontend_unit(bad_surface)))

        # Source-byte mutation after artifact admission must invalidate the binding.
        source_tamper = tmp / "source-tamper.clay"
        source_tamper.write_bytes(copied_sources[0].read_bytes() + b"\n// post-artifact mutation\n")
        source_spec = dict(specs[0]); source_spec["source"] = str(source_tamper)
        tamper.append(reject("source_hash_mismatch", lambda: bridge.verify_frontend_unit(source_spec)))

        # Grammar-byte mutation after artifact admission must invalidate the binding.
        grammar_tamper = tmp / "V18-tampered.lark"
        grammar_tamper.write_text(grammar_text + "\n// post-artifact mutation\n", encoding="utf-8")
        grammar_spec = dict(specs[0]); grammar_spec["grammar"] = str(grammar_tamper)
        tamper.append(reject("grammar_hash_mismatch", lambda: bridge.verify_frontend_unit(grammar_spec)))

        # Contract metadata mutation must be rejected independently of source/grammar bytes.
        contract_doc = copy.deepcopy(docs[0]); contract_doc["contract_hash"] = "0" * 64
        contract_artifact = tmp / "artifact-contract-tamper.json"; dump(contract_artifact, contract_doc)
        contract_spec = dict(specs[0]); contract_spec["artifact"] = str(contract_artifact)
        tamper.append(reject("frontend_contract_hash_mismatch", lambda: bridge.verify_frontend_unit(contract_spec)))

        # Legacy frontend v1 contract does not include surface; the bridge must still reject
        # same source bytes arriving through conflicting surface identities without an explicit
        # equivalence receipt.
        alt_doc = copy.deepcopy(docs[0]); alt_doc["surface"] = "BASE_D_V18_ALIAS_UNPROVEN"
        alt_artifact = tmp / "artifact-alt-surface.json"; dump(alt_artifact, alt_doc)
        cross_manifest = {
            "units": [
                specs[0],
                {
                    "artifact": str(alt_artifact),
                    "source": specs[0]["source"],
                    "grammar": specs[0]["grammar"],
                    "expected_surface": "BASE_D_V18_ALIAS_UNPROVEN",
                },
            ]
        }
        tamper.append(reject("same_source_cross_surface_without_equivalence", lambda: bridge.compile_manifest(cross_manifest)))

        tamper_pass = all(x["rejected"] for x in tamper)
        report = {
            "schema_version": "1.0",
            "test": "WP03_V18_RESIDUAL_FULL_BRIDGE_AND_TAMPER",
            "source_count": len(SOURCES),
            "frontend_surface": EXPECTED_SURFACE,
            "full_bridge": full_bridge,
            "tamper_rejection": tamper,
            "tamper_rejection_pass": tamper_pass,
            "pass": bool(full_bridge["pass"] and tamper_pass),
            "promotion": "NONE",
            "wp03_status": "OPEN",
            "scope_guard": "PASS proves only no-silent-reparse V18 artifact binding, full current G9/Dialect residual preservation and listed tamper/authority guards for the candidate. It does not close WP03, prove WP04/05 semantic lowering, accept Andreas target, mutate Frank Harness or authorize training/effects.",
        }
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
