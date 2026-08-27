#!/usr/bin/env python3
"""WP03 research candidate: explicit FrontendArtifact -> TypedIR contract adapter.

Purpose: remove silent parser ownership from the typed-IR boundary without deleting older
structured ClayCode surfaces. A frontend artifact is accepted only when its schema, surface,
grammar identity, semantic AST hash and a surface-bound v2 contract hash are coherent.
Typed IR then consumes the already-produced canonical AST through SourceUnit/build_typed_ir;
it never reparses source bytes in this adapter.

This module is research-only until the differential/Ubuntu gates promote it. It does not
change DEFAULT_GRAMMAR, select a surface, close WP03, or grant effect authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import claycode_base_frontend as front
import claycode_base_typed_ir as tir

CONTRACT_SCHEMA = "ClayCodeFrontendContract/v2"
FRONTEND_SCHEMA = "ClayCodeBaseFrontendAST/v1"


class FrontendContractError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def contract_payload(*, surface: str, grammar_sha256: str, semantic_hash: str) -> dict[str, str]:
    return {
        "contract_schema": CONTRACT_SCHEMA,
        "frontend_schema": FRONTEND_SCHEMA,
        "surface": surface,
        "grammar_sha256": grammar_sha256,
        "semantic_hash": semantic_hash,
    }


def contract_hash(*, surface: str, grammar_sha256: str, semantic_hash: str) -> str:
    payload = contract_payload(surface=surface, grammar_sha256=grammar_sha256, semantic_hash=semantic_hash)
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def identified_frontend(source: str, grammar_text: str, *, surface: str, strict: bool) -> dict[str, Any]:
    """Compile through the production frontend machinery, then bind an explicit surface.

    Current production compile_frontend() binds grammar+semantic hash but its v1 contract
    does not include surface. We retain that legacy receipt as provenance and add a v2
    surface-bound contract without pretending the legacy hash already proves surface identity.
    """
    if not surface or not isinstance(surface, str):
        raise FrontendContractError("surface must be a non-empty string")
    base = front.compile_frontend(source, grammar_text, strict=strict)
    surface_claim = str(base.get("surface") or "")
    artifact = dict(base)
    artifact["legacy_frontend_surface_claim"] = surface_claim
    artifact["surface"] = surface
    artifact["frontend_contract_schema"] = CONTRACT_SCHEMA
    artifact["contract_hash_v2"] = contract_hash(
        surface=surface,
        grammar_sha256=str(base["grammar_sha256"]),
        semantic_hash=str(base["semantic_hash"]),
    )
    return artifact


def validate_artifact(
    artifact: dict[str, Any],
    *,
    expected_surface: str | None = None,
    expected_grammar_sha256: str | None = None,
) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise FrontendContractError("frontend artifact must be an object")
    if artifact.get("frontend_schema") != FRONTEND_SCHEMA:
        raise FrontendContractError(f"unexpected frontend_schema: {artifact.get('frontend_schema')!r}")
    if artifact.get("frontend_contract_schema") != CONTRACT_SCHEMA:
        raise FrontendContractError(f"missing/unsupported frontend contract: {artifact.get('frontend_contract_schema')!r}")

    surface = str(artifact.get("surface") or "")
    grammar_sha = str(artifact.get("grammar_sha256") or "")
    semantic_hash = str(artifact.get("semantic_hash") or "")
    source_sha = str(artifact.get("source_sha256") or "")
    ast = artifact.get("canonical_ast")
    observed_contract = str(artifact.get("contract_hash_v2") or "")
    if not all((surface, grammar_sha, semantic_hash, source_sha, observed_contract)):
        raise FrontendContractError("artifact missing surface/grammar/semantic/source/contract identity")
    if expected_surface is not None and surface != expected_surface:
        raise FrontendContractError(f"surface mismatch: expected {expected_surface!r}, got {surface!r}")
    if expected_grammar_sha256 is not None and grammar_sha != expected_grammar_sha256:
        raise FrontendContractError(
            f"grammar mismatch: expected {expected_grammar_sha256!r}, got {grammar_sha!r}"
        )
    if ast is None:
        raise FrontendContractError("canonical_ast missing")

    recomputed_semantic = sha256(front.DOMAIN + front.canonical_bytes(ast))
    if recomputed_semantic != semantic_hash:
        raise FrontendContractError(
            f"semantic hash mismatch: artifact={semantic_hash}, canonical_ast={recomputed_semantic}"
        )
    expected_contract = contract_hash(
        surface=surface, grammar_sha256=grammar_sha, semantic_hash=semantic_hash
    )
    if observed_contract != expected_contract:
        raise FrontendContractError(
            f"surface-bound contract mismatch: artifact={observed_contract}, expected={expected_contract}"
        )
    return artifact


def source_unit_from_artifact(
    path: Path,
    artifact: dict[str, Any],
    *,
    expected_surface: str | None = None,
    expected_grammar_sha256: str | None = None,
) -> tir.SourceUnit:
    validated = validate_artifact(
        artifact,
        expected_surface=expected_surface,
        expected_grammar_sha256=expected_grammar_sha256,
    )
    return tir.SourceUnit(path=path, frontend=validated)


def build_typed_ir_from_artifacts(
    rows: Iterable[tuple[Path, dict[str, Any]]],
    *,
    expected_surface: str | None = None,
    expected_grammar_sha256: str | None = None,
) -> dict[str, Any]:
    units = [
        source_unit_from_artifact(
            path,
            artifact,
            expected_surface=expected_surface,
            expected_grammar_sha256=expected_grammar_sha256,
        )
        for path, artifact in rows
    ]
    result_a = tir.build_typed_ir(units)
    result_b = tir.build_typed_ir(units)
    if result_a.get("typed_ir_sha256") != result_b.get("typed_ir_sha256"):
        raise FrontendContractError("typed IR is nondeterministic after artifact ingestion")
    if tir.canon_bytes(result_a) != tir.canon_bytes(result_b):
        raise FrontendContractError("typed IR bytes are nondeterministic after artifact ingestion")
    return result_a


@dataclass(frozen=True)
class SurfaceCollision:
    source_sha256: str
    surfaces: tuple[str, ...]
    semantic_hashes: tuple[str, ...]


def adjudicate_same_source_multi_surface(
    artifacts: Iterable[dict[str, Any]],
    *,
    equivalence_evidence_id: str | None = None,
) -> SurfaceCollision | None:
    """Fail closed on same-source multi-surface admission unless equivalence is explicit.

    Equal semantic hashes are necessary but deliberately not sufficient: an explicit
    equivalence evidence id is required so accidental current-hash equality cannot silently
    become permanent cross-dialect authority.
    """
    validated = [validate_artifact(dict(a)) for a in artifacts]
    if len(validated) < 2:
        return None
    sources = {str(a["source_sha256"]) for a in validated}
    if len(sources) != 1:
        return None
    surfaces = tuple(sorted({str(a["surface"]) for a in validated}))
    if len(surfaces) < 2:
        return None
    semantics = tuple(sorted({str(a["semantic_hash"]) for a in validated}))
    collision = SurfaceCollision(next(iter(sources)), surfaces, semantics)
    if len(semantics) != 1:
        raise FrontendContractError(
            f"same-source cross-surface semantic collision: surfaces={surfaces}, semantic_hashes={semantics}"
        )
    if not equivalence_evidence_id:
        raise FrontendContractError(
            f"same-source cross-surface equivalence lacks explicit evidence: surfaces={surfaces}"
        )
    return collision
