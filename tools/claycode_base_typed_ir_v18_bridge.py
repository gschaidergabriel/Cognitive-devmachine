#!/usr/bin/env python3
"""Receipt-bound V18 FrontendArtifact -> existing ClayCode BASE TypedIR bridge.

CC-WP-03 integration slice. The bridge consumes the exact canonical WP02 artifact and
never reparses source. It fail-closes on frontend schema/surface/grammar/semantic-hash/
contract-hash drift, then delegates typed declaration construction to the existing WP03
builder.

Semantic program identity remains content-derived. Runtime/state instance identity is a
separate epoch/version-bound identity so equal semantic value cannot silently authorize a
stale state instance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as typed

EXPECTED_FRONTEND_SCHEMA = "ClayCodeBaseFrontendAST/v1"
EXPECTED_SURFACE = "BASE_D_V18_REWARD_RELATIONS"
EXPECTED_GRAMMAR_SHA256 = "99a3b35acfe491081773b9666d9131dae8b2dd3b3bde7ac8569f6428a5fdb180"
BRIDGE_SCHEMA = "ClayCodeBaseV18FrontendTypedIRBridge/v1"
STATE_INSTANCE_DOMAIN = b"ClayCodeStateInstanceIdentity/v1\x00"


class V18BridgeError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_frontend_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    if artifact.get("frontend_schema") != EXPECTED_FRONTEND_SCHEMA:
        raise V18BridgeError("frontend_schema mismatch")
    if artifact.get("surface") != EXPECTED_SURFACE:
        raise V18BridgeError("surface mismatch")
    if artifact.get("grammar_sha256") != EXPECTED_GRAMMAR_SHA256:
        raise V18BridgeError("grammar binding mismatch")
    ast = artifact.get("canonical_ast")
    if not isinstance(ast, dict) or ast.get("kind") != "start":
        raise V18BridgeError("canonical_ast root must be start")
    recomputed = sha256(front.DOMAIN + front.canonical_bytes(ast))
    if artifact.get("semantic_hash") != recomputed:
        raise V18BridgeError("frontend semantic_hash mismatch/tamper")

    expected_contract = sha256(
        stable_json(
            {
                "frontend_schema": EXPECTED_FRONTEND_SCHEMA,
                "grammar_sha256": EXPECTED_GRAMMAR_SHA256,
                "semantic_hash": recomputed,
            }
        )
    )
    if artifact.get("contract_hash") != expected_contract:
        raise V18BridgeError("frontend contract_hash mismatch/tamper")

    source_sha = artifact.get("source_sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64:
        raise V18BridgeError("source_sha256 missing/invalid")
    return {
        "frontend_schema": EXPECTED_FRONTEND_SCHEMA,
        "surface": EXPECTED_SURFACE,
        "grammar_sha256": EXPECTED_GRAMMAR_SHA256,
        "source_sha256": source_sha,
        "semantic_hash": recomputed,
        "contract_hash": expected_contract,
    }


def state_instance_identity(
    semantic_id: str, *, epoch: int | str, version: int | str, resource_id: str | None = None
) -> str:
    if not isinstance(semantic_id, str) or not semantic_id:
        raise V18BridgeError("semantic_id required")
    payload = {
        "semantic_id": semantic_id,
        "epoch": str(epoch),
        "version": str(version),
        "resource_id": resource_id,
    }
    return "claystate:" + sha256(STATE_INSTANCE_DOMAIN + stable_json(payload))


def build_from_artifacts(
    artifacts: list[tuple[Path, dict[str, Any]]], *, state_epoch: int | str | None = None, state_version: int | str | None = None
) -> dict[str, Any]:
    if not artifacts:
        raise V18BridgeError("at least one frontend artifact is required")
    validations = []
    units = []
    for path, artifact in artifacts:
        validations.append({"path": str(path), **validate_frontend_artifact(artifact)})
        units.append(typed.SourceUnit(path, artifact))
    ir = typed.build_typed_ir(units)
    if ir.get("ir_schema") != "ClayCodeBaseTypedIR/v1":
        raise V18BridgeError("unexpected typed IR schema")
    semantic_id = ir.get("program_semantic_id")
    if not isinstance(semantic_id, str) or not semantic_id.startswith("clayir:"):
        raise V18BridgeError("typed IR semantic identity missing")
    state_id = None
    if (state_epoch is None) != (state_version is None):
        raise V18BridgeError("state_epoch and state_version must be supplied together")
    if state_epoch is not None:
        state_id = state_instance_identity(semantic_id, epoch=state_epoch, version=state_version)
    return {
        "schema_version": "1.0",
        "bridge_schema": BRIDGE_SCHEMA,
        "mode": "FRONTEND_ARTIFACT_NO_REPARSE",
        "frontend_contracts": validations,
        "typed_ir": ir,
        "semantic_identity": semantic_id,
        "state_identity": {
            "semantic_id": semantic_id,
            "state_epoch": None if state_epoch is None else str(state_epoch),
            "state_version": None if state_version is None else str(state_version),
            "state_instance_id": state_id,
            "law": "semantic identity and epoch/version-bound runtime state identity are distinct",
        },
        "authority": {
            "typed_ir_description_mints_effect_authority": False,
            "frontend_artifact_mints_effect_authority": False,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("frontend_artifact", nargs="+", type=Path)
    ap.add_argument("--state-epoch")
    ap.add_argument("--state-version")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    rows = []
    for path in args.frontend_artifact:
        rows.append((path, json.loads(path.read_text(encoding="utf-8"))))
    result = build_from_artifacts(rows, state_epoch=args.state_epoch, state_version=args.state_version)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
