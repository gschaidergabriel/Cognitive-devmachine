#!/usr/bin/env python3
"""Deterministic regression tests for the WP03 receipt-bound frontend artifact bridge.

This is a normal interface/conformance test, not an out-of-box experiment.
"""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import claycode_base_frontend as front
import claycode_wp03_frontend_artifact_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = front.DEFAULT_GRAMMAR


def expect_binding_error(fn, label: str) -> dict:
    try:
        fn()
    except bridge.FrontendBindingError as exc:
        return {"name": label, "pass": True, "error": str(exc)}
    return {"name": label, "pass": False, "error": "unexpected_accept"}


def main() -> int:
    checks = []
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    source_text = "record BridgeDemo { alpha:Int }\n"

    with tempfile.TemporaryDirectory(prefix="clay-wp03-frontend-bridge-", dir=ROOT) as td:
        d = Path(td)
        source = d / "source.clay"
        artifact = d / "frontend.json"
        manifest = d / "manifest.json"
        grammar = d / GRAMMAR.name
        source.write_text(source_text, encoding="utf-8")
        grammar.write_text(grammar_text, encoding="utf-8")

        frontend = front.compile_frontend(source_text, grammar_text, strict=False)
        artifact.write_text(json.dumps(frontend, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest_doc = {
            "units": [{
                "artifact": str(artifact),
                "source": str(source),
                "grammar": str(grammar),
                "expected_surface": str(frontend["surface"]),
            }]
        }
        manifest.write_text(json.dumps(manifest_doc, indent=2) + "\n", encoding="utf-8")

        # Prove the bridge consumes the artifact rather than silently reparsing source.
        original_compile = front.compile_frontend
        def forbidden_reparse(*args, **kwargs):
            raise AssertionError("silent frontend reparse attempted")
        front.compile_frontend = forbidden_reparse
        try:
            result = bridge.compile_manifest(manifest_doc)
        finally:
            front.compile_frontend = original_compile

        binding = result["frontend_bindings"][0]
        checks += [
            {"name": "bridge_compiles_without_reparse", "pass": bool(result.get("typed_ir", {}).get("typed_ir_sha256"))},
            {"name": "source_hash_bound", "pass": binding["source_sha256"] == frontend["source_sha256"]},
            {"name": "grammar_hash_bound", "pass": binding["grammar_sha256"] == frontend["grammar_sha256"]},
            {"name": "frontend_semantic_hash_bound", "pass": binding["frontend_semantic_hash"] == frontend["semantic_hash"]},
            {"name": "frontend_contract_hash_bound", "pass": binding["frontend_contract_hash"] == frontend["contract_hash"]},
            {"name": "surface_pin_bound", "pass": binding["surface"] == frontend["surface"] == binding["expected_surface"]},
            {"name": "artifact_hash_present", "pass": len(result.get("typed_ir_artifact_sha256", "")) == 64},
            {"name": "semantic_and_artifact_identity_separate", "pass": result["typed_ir_artifact_sha256"] != result["typed_ir"]["typed_ir_sha256"]},
        ]

        # Source tampering must fail before TypedIR construction.
        source.write_text(source_text + "// tampered\n", encoding="utf-8")
        checks.append(expect_binding_error(lambda: bridge.compile_manifest(manifest_doc), "source_tamper_rejected"))
        source.write_text(source_text, encoding="utf-8")

        # Grammar tampering must fail even if the artifact itself remains unchanged.
        grammar.write_text(grammar_text + "\n// tampered grammar\n", encoding="utf-8")
        checks.append(expect_binding_error(lambda: bridge.compile_manifest(manifest_doc), "grammar_tamper_rejected"))
        grammar.write_text(grammar_text, encoding="utf-8")

        # Contract tampering must fail closed.
        bad = copy.deepcopy(frontend)
        bad["contract_hash"] = "0" * 64
        artifact.write_text(json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        checks.append(expect_binding_error(lambda: bridge.compile_manifest(manifest_doc), "contract_tamper_rejected"))
        artifact.write_text(json.dumps(frontend, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Same source bytes through two explicitly different, independently pinned surface
        # identities are ambiguous until an equivalence receipt exists, even if AST hashes match.
        second = copy.deepcopy(frontend)
        second["surface"] = str(frontend["surface"]) + "_ALTERNATE"
        artifact2 = d / "frontend-alternate.json"
        artifact2.write_text(json.dumps(second, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ambiguous = {
            "units": [
                {
                    "artifact": str(artifact),
                    "source": str(source),
                    "grammar": str(grammar),
                    "expected_surface": str(frontend["surface"]),
                },
                {
                    "artifact": str(artifact2),
                    "source": str(source),
                    "grammar": str(grammar),
                    "expected_surface": str(second["surface"]),
                },
            ]
        }
        checks.append(expect_binding_error(lambda: bridge.compile_manifest(ambiguous), "cross_surface_same_source_ambiguity_rejected"))

    failures = [x for x in checks if not x.get("pass")]
    report = {
        "schema_version": "1.1",
        "test": "WP03_FRONTEND_ARTIFACT_BRIDGE_REGRESSION",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "total": len(checks),
        "failures": failures,
        "pass": not failures,
        "scope_guard": "Local/CI interface regression only; strict Ubuntu, full G9/Dialect, WP03 and Andreas-target gates remain separate.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
