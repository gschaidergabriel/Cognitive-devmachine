#!/usr/bin/env python3
"""Regression for receipt-bound surface identity at the WP03 frontend->TypedIR bridge.

The current frontend v1 contract hash does not contain the `surface` label. This test proves
that fact explicitly, then requires the bridge manifest's independent `expected_surface` pin
to reject a relabeled otherwise-valid artifact before typed IR construction.
"""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import claycode_base_frontend as front
import claycode_wp03_frontend_artifact_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
SURFACE = "BASE_D_V17_DECLARATIVE_TRIVIA_SAFE"


def rejects(fn) -> tuple[bool, str | None]:
    try:
        fn()
    except bridge.FrontendBindingError as exc:
        return True, str(exc)
    return False, None


def main() -> int:
    grammar = V17.read_text(encoding="utf-8")
    source = "record Sample { id:Int }\n"
    artifact = front.compile_frontend(source, grammar, strict=True)
    if artifact["surface"] != SURFACE:
        raise SystemExit(f"unexpected selected V17 surface: {artifact['surface']!r}")

    relabeled = copy.deepcopy(artifact)
    relabeled["surface"] = "FORGED_OTHER_SURFACE"
    legacy_contract_unchanged = artifact["contract_hash"] == relabeled["contract_hash"]

    with tempfile.TemporaryDirectory(prefix="clay-wp03-surface-bind-") as td:
        root = Path(td)
        source_path = root / "sample.clay"
        grammar_path = root / "v17.lark"
        artifact_path = root / "frontend.json"
        source_path.write_text(source, encoding="utf-8")
        grammar_path.write_text(grammar, encoding="utf-8")
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        spec = {
            "artifact": str(artifact_path),
            "source": str(source_path),
            "grammar": str(grammar_path),
            "expected_surface": SURFACE,
        }
        unit, binding = bridge.verify_frontend_unit(spec)
        valid_pass = binding["surface"] == SURFACE and binding["expected_surface"] == SURFACE

        artifact_path.write_text(json.dumps(relabeled), encoding="utf-8")
        relabel_rejected, relabel_error = rejects(lambda: bridge.verify_frontend_unit(spec))

        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        wrong_expected = dict(spec)
        wrong_expected["expected_surface"] = "WRONG_EXPECTED_SURFACE"
        wrong_expected_rejected, wrong_expected_error = rejects(
            lambda: bridge.verify_frontend_unit(wrong_expected)
        )

        missing_expected = dict(spec)
        missing_expected.pop("expected_surface")
        missing_rejected, missing_error = rejects(lambda: bridge.verify_frontend_unit(missing_expected))

        compiled = bridge.compile_manifest({"units": [spec]})
        compile_pass = (
            compiled["frontend_bindings"][0]["surface"] == SURFACE
            and compiled["frontend_bindings"][0]["expected_surface"] == SURFACE
            and bool(compiled.get("typed_ir_artifact_sha256"))
            and compiled["invariants"].get("unbound_surface_relabel") == "FORBIDDEN"
        )

    passed = (
        legacy_contract_unchanged
        and valid_pass
        and relabel_rejected
        and wrong_expected_rejected
        and missing_rejected
        and compile_pass
    )
    out = {
        "schema_version": "1.0",
        "experiment": "WP03 frontend bridge surface-relabel regression",
        "legacy_v1_contract_surface_omission_reproduced": legacy_contract_unchanged,
        "valid_manifest_surface_binding": valid_pass,
        "relabel_rejected": relabel_rejected,
        "relabel_error": relabel_error,
        "wrong_expected_surface_rejected": wrong_expected_rejected,
        "wrong_expected_surface_error": wrong_expected_error,
        "missing_expected_surface_rejected": missing_rejected,
        "missing_expected_surface_error": missing_error,
        "typed_ir_compile_with_bound_surface": compile_pass,
        "pass": passed,
        "classification": "SURFACE_RELABEL_GUARD_SUPPORTED" if passed else "REFUTED_OR_INCOMPLETE",
        "promotion": "NONE",
        "wp03_status_change": "NONE",
        "scope_guard": "PASS validates only bridge-level surface pinning around the legacy v1 frontend contract. It does not close WP03, replace a future surface-bound frontend contract revision, or count as Andreas target acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
