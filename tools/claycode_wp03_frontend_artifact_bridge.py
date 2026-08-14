#!/usr/bin/env python3
"""Receipt-bound frontend-artifact -> ClayCode BASE TypedIR bridge for CC-WP-03.

Why this exists:
- CC-WP-02 has a selected production frontend with explicit surface/grammar identity.
- `claycode_base_typed_ir.compile_sources()` historically reparses source through its own
  default grammar, so a green frontend receipt can be silently reinterpreted downstream.
- The declaration-only TypedIR builder also has an executable negative result: admitted
  top-level semantic statements can be frontend-distinct while collapsing to one TypedIR
  semantic identity.
- Typed semantic identity should remain independent of source/provenance identity, but the
  *compilation artifact* must still bind the exact frontend contract that produced the AST.

This bridge therefore consumes already-produced frontend JSON artifacts, verifies them
against the exact source and grammar bytes, rejects ambiguous same-source multi-surface
inputs, and calls the tested residual-semantics TypedIR candidate without reparsing. The
residual builder keeps existing structured declaration/type lowering and conservatively
binds not-yet-lowered top-level canonical AST into `opaque_unlowered_semantics` so admitted
semantics cannot silently disappear before CC-WP-04/05 give them explicit legality/lowering.

Current frontend contract v1 predates explicit surface binding: its hash covers schema,
grammar and semantic AST identity but not the surface label. Until a surface-bound frontend
contract revision is promoted, every bridge unit must therefore pin `expected_surface` in
the receipt-bound manifest. Relabeling an otherwise valid artifact then fails closed before
typed IR is built.

This is a versioned production-path repair justified by executable counterevidence. It does
not close WP03 and does not grant opaque semantics execution/effect authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_frontend as front  # noqa: E402
import claycode_base_typed_ir as typed  # noqa: E402
import claycode_wp03_residual_semantics_candidate as residual  # noqa: E402

BRIDGE_SCHEMA = "ClayCodeTypedIRFrontendBinding/v2-residual-semantics"
ARTIFACT_DOMAIN = b"ClayCodeTypedIRFrontendBinding/v2-residual-semantics\x00"
CURRENT_FRONTEND_SCHEMA = "ClayCodeBaseFrontendAST/v1"
REQUIRED_LOWERING_STATUS = "PARTIAL_CONSERVATIVE_PRESERVATION"


class FrontendBindingError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FrontendBindingError(f"JSON object required: {path}")
    return value


def require_hex_sha(name: str, value: Any) -> str:
    text = str(value or "")
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text.lower()):
        raise FrontendBindingError(f"{name} must be a 64-character SHA-256 hex digest")
    return text.lower()


def verify_frontend_unit(spec: dict[str, Any]) -> tuple[typed.SourceUnit, dict[str, Any]]:
    for key in ("artifact", "source", "grammar", "expected_surface"):
        if not spec.get(key):
            raise FrontendBindingError(f"unit missing required {key!r}")

    artifact_path = resolve_path(str(spec["artifact"]))
    source_path = resolve_path(str(spec["source"]))
    grammar_path = resolve_path(str(spec["grammar"]))
    expected_surface = str(spec["expected_surface"])
    if not expected_surface:
        raise FrontendBindingError("expected_surface must be a non-empty string")
    for path in (artifact_path, source_path, grammar_path):
        if not path.is_file():
            raise FrontendBindingError(f"required file missing: {path}")

    doc = load_object(artifact_path)
    required = {
        "frontend_schema",
        "surface",
        "source_sha256",
        "grammar_sha256",
        "semantic_hash",
        "contract_hash",
        "canonical_ast",
    }
    missing = sorted(required - set(doc))
    if missing:
        raise FrontendBindingError(f"frontend artifact missing fields: {missing}")

    schema = str(doc["frontend_schema"])
    if schema != CURRENT_FRONTEND_SCHEMA:
        raise FrontendBindingError(
            f"unsupported frontend schema {schema!r}; explicit migration/adapter required"
        )
    surface = str(doc["surface"])
    if surface != expected_surface:
        raise FrontendBindingError(
            f"frontend surface mismatch: manifest expected {expected_surface!r}, artifact claims {surface!r}"
        )

    source_bytes = source_path.read_bytes()
    grammar_bytes = grammar_path.read_bytes()
    source_sha = sha256_bytes(source_bytes)
    grammar_sha = sha256_bytes(grammar_bytes)
    if require_hex_sha("source_sha256", doc["source_sha256"]) != source_sha:
        raise FrontendBindingError(f"source hash mismatch for {source_path}")
    if require_hex_sha("grammar_sha256", doc["grammar_sha256"]) != grammar_sha:
        raise FrontendBindingError(f"grammar hash mismatch for {grammar_path}")

    ast_bytes = front.canonical_bytes(doc["canonical_ast"])
    semantic_hash = sha256_bytes(front.DOMAIN + ast_bytes)
    if require_hex_sha("semantic_hash", doc["semantic_hash"]) != semantic_hash:
        raise FrontendBindingError(f"frontend semantic hash mismatch for {artifact_path}")

    # Legacy frontend v1 contract intentionally reconstructed exactly. Its omission of
    # surface is compensated above by the independently receipt-bound expected_surface pin.
    contract_payload = {
        "frontend_schema": schema,
        "grammar_sha256": grammar_sha,
        "semantic_hash": semantic_hash,
    }
    contract_hash = sha256_bytes(stable_json(contract_payload))
    if require_hex_sha("contract_hash", doc["contract_hash"]) != contract_hash:
        raise FrontendBindingError(f"frontend contract hash mismatch for {artifact_path}")

    binding = {
        "artifact": str(artifact_path.relative_to(ROOT)) if artifact_path.is_relative_to(ROOT) else str(artifact_path),
        "source": str(source_path.relative_to(ROOT)) if source_path.is_relative_to(ROOT) else str(source_path),
        "grammar": str(grammar_path.relative_to(ROOT)) if grammar_path.is_relative_to(ROOT) else str(grammar_path),
        "frontend_schema": schema,
        "surface": surface,
        "expected_surface": expected_surface,
        "source_sha256": source_sha,
        "grammar_sha256": grammar_sha,
        "frontend_semantic_hash": semantic_hash,
        "frontend_contract_hash": contract_hash,
    }
    return typed.SourceUnit(source_path, doc), binding


def compile_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    specs = manifest.get("units")
    if not isinstance(specs, list) or not specs:
        raise FrontendBindingError("manifest.units must be a non-empty list")

    units: list[typed.SourceUnit] = []
    bindings: list[dict[str, Any]] = []
    by_source: dict[str, tuple[str, str, str]] = {}
    for raw in specs:
        if not isinstance(raw, dict):
            raise FrontendBindingError("every manifest unit must be an object")
        unit, binding = verify_frontend_unit(raw)
        identity = (
            binding["surface"],
            binding["grammar_sha256"],
            binding["frontend_semantic_hash"],
        )
        previous = by_source.get(binding["source_sha256"])
        if previous is not None and previous != identity:
            raise FrontendBindingError(
                "same source bytes arrived through multiple non-equivalent frontend identities; "
                "fail closed until an explicit equivalence receipt exists"
            )
        if previous is not None:
            raise FrontendBindingError("duplicate frontend artifact for identical source bytes")
        by_source[binding["source_sha256"]] = identity
        units.append(unit)
        bindings.append(binding)

    ir = residual.build_typed_ir(units)
    if ir.get("lowering_status") != REQUIRED_LOWERING_STATUS:
        raise FrontendBindingError(
            f"unexpected TypedIR lowering status: {ir.get('lowering_status')!r}; "
            f"expected {REQUIRED_LOWERING_STATUS!r}"
        )
    invariants = ir.get("invariants") if isinstance(ir.get("invariants"), dict) else {}
    if invariants.get("opaque_semantics_mint_effect_authority") != "FORBIDDEN":
        raise FrontendBindingError("residual TypedIR failed opaque-semantics authority invariant")

    binding_core = {
        "bridge_schema": BRIDGE_SCHEMA,
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "frontend_bindings": bindings,
    }
    artifact_hash = sha256_bytes(ARTIFACT_DOMAIN + stable_json(binding_core))
    return {
        "schema_version": "2.0",
        "bridge_schema": BRIDGE_SCHEMA,
        "typed_ir": ir,
        "frontend_bindings": bindings,
        "typed_ir_artifact_sha256": artifact_hash,
        "identity_semantics": {
            "typed_ir_sha256": "semantic IR identity; excludes source/provenance by design and includes conservatively preserved unlowered semantics",
            "typed_ir_artifact_sha256": "binds semantic IR to exact frontend/source/grammar/surface contracts",
        },
        "invariants": {
            "silent_reparse": "FORBIDDEN",
            "implicit_frontend_dispatch": "FORBIDDEN",
            "unbound_surface_relabel": "FORBIDDEN",
            "same_source_cross_surface_ambiguity": "FAIL_CLOSED_WITHOUT_EQUIVALENCE_RECEIPT",
            "unlowered_admitted_semantics_may_disappear": "FORBIDDEN",
            "opaque_semantics_execution_authority": "FORBIDDEN",
            "frontend_artifact_mints_authority": "FORBIDDEN",
            "model_output_execution_authority": "FORBIDDEN",
            "legacy_declaration_only_builder_is_production_entrypoint": "FORBIDDEN",
        },
        "promotion_scope": "WP03_RECEIPT_BOUND_TYPEDIR_PRODUCTION_PATH_CANDIDATE",
        "wp03_status": "OPEN",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    result = compile_manifest(load_object(manifest_path))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
