#!/usr/bin/env python3
"""SourceChainEvidence v1 validator/differential oracle for Clay/FRANK Harness BASE.

This validates evidence continuity only. It never grants execution authority and does
not imply H1/H2/H3 release completion.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "1.0"
HASH64 = re.compile(r"^[0-9a-f]{64}$")
STAGE_ORDER = ("source", "parse", "typed_ir", "lowering", "execution", "replay")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def artifact_hash(payload: Any) -> str:
    return sha256_obj(payload)


def _err(errors: list[dict[str, str]], code: str, path: str, detail: str) -> None:
    errors.append({"code": code, "path": path, "detail": detail})


def _hash64(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH64.fullmatch(value))


def _require(stage: dict[str, Any], key: str, path: str, errors: list[dict[str, str]]) -> None:
    if key not in stage:
        _err(errors, "MISSING_FIELD", f"{path}.{key}", "required field is absent")


def validate_chain(chain: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if chain.get("schema_version") != SCHEMA_VERSION:
        _err(errors, "SCHEMA_VERSION", "$.schema_version", f"expected {SCHEMA_VERSION}")

    stages = chain.get("stages")
    if not isinstance(stages, dict):
        _err(errors, "INVALID_STAGES", "$.stages", "must be an object keyed by source/parse/typed_ir/lowering/execution/replay")
        return {"valid": False, "errors": errors}

    prior_hash: str | None = None
    for name in STAGE_ORDER:
        path = f"$.stages.{name}"
        stage = stages.get(name)
        if not isinstance(stage, dict):
            _err(errors, "MISSING_STAGE", path, "required source-chain stage is absent")
            continue
        for key in ("artifact_ref", "artifact_hash", "semantic_hash"):
            _require(stage, key, path, errors)
        if not isinstance(stage.get("artifact_ref"), str) or not stage.get("artifact_ref"):
            _err(errors, "INVALID_ARTIFACT_REF", f"{path}.artifact_ref", "must be non-empty")
        for key in ("artifact_hash", "semantic_hash"):
            if key in stage and not _hash64(stage[key]):
                _err(errors, "INVALID_HASH", f"{path}.{key}", "expected lowercase sha256 hex")
        if name != "source":
            _require(stage, "parent_artifact_hash", path, errors)
            if prior_hash and stage.get("parent_artifact_hash") != prior_hash:
                _err(errors, "CHAIN_PARENT_MISMATCH", f"{path}.parent_artifact_hash", f"must equal prior stage artifact_hash {prior_hash}")
        prior_hash = stage.get("artifact_hash") if _hash64(stage.get("artifact_hash")) else None

    source = stages.get("source", {}) if isinstance(stages.get("source"), dict) else {}
    parse = stages.get("parse", {}) if isinstance(stages.get("parse"), dict) else {}
    typed_ir = stages.get("typed_ir", {}) if isinstance(stages.get("typed_ir"), dict) else {}
    lowering = stages.get("lowering", {}) if isinstance(stages.get("lowering"), dict) else {}
    execution = stages.get("execution", {}) if isinstance(stages.get("execution"), dict) else {}
    replay = stages.get("replay", {}) if isinstance(stages.get("replay"), dict) else {}

    if parse.get("source_admitted") is not True:
        _err(errors, "SOURCE_NOT_ADMITTED", "$.stages.parse.source_admitted", "BASE evidence requires production-parser admission")
    if not _hash64(parse.get("grammar_hash")):
        _err(errors, "GRAMMAR_IDENTITY_REQUIRED", "$.stages.parse.grammar_hash", "parser grammar must be content-addressed")

    cycle_form = source.get("cycle_header_form")
    if cycle_form == "NAMED" and parse.get("supports_named_cycle") is not True and parse.get("source_admitted") is True:
        _err(errors, "NAMED_CYCLE_ADMISSION_INCONSISTENT", "$.stages.parse", "named cycle cannot be claimed admitted when the referenced grammar does not support named cycle headers")

    if typed_ir.get("type_effect_checked") is not True:
        _err(errors, "TYPE_EFFECT_CHECK_REQUIRED", "$.stages.typed_ir.type_effect_checked", "typed IR must pass the production type/effect checker")
    if not _hash64(typed_ir.get("type_effect_contract_hash")):
        _err(errors, "TYPE_EFFECT_CONTRACT_REQUIRED", "$.stages.typed_ir.type_effect_contract_hash", "type/effect contract must be content-addressed")
    if not _hash64(lowering.get("lowering_contract_hash")):
        _err(errors, "LOWERING_CONTRACT_REQUIRED", "$.stages.lowering.lowering_contract_hash", "lowering contract must be content-addressed")

    if source.get("semantic_hash") != parse.get("semantic_hash"):
        _err(errors, "PARSE_SEMANTIC_DRIFT", "$.stages.parse.semantic_hash", "parse semantic identity differs from admitted source")
    if parse.get("semantic_hash") != typed_ir.get("semantic_hash"):
        _err(errors, "TYPED_IR_SEMANTIC_DRIFT", "$.stages.typed_ir.semantic_hash", "typed IR semantic identity differs from parse")

    semantic_delta = lowering.get("semantic_delta", "UNKNOWN")
    if semantic_delta not in {"NONE", "DECLARED"}:
        _err(errors, "LOWERING_SEMANTIC_DELTA_UNKNOWN", "$.stages.lowering.semantic_delta", "must be NONE or DECLARED")
    if semantic_delta == "DECLARED" and not lowering.get("semantic_delta_receipt"):
        _err(errors, "LOWERING_DELTA_WITHOUT_RECEIPT", "$.stages.lowering.semantic_delta_receipt", "declared semantic delta requires explicit receipt")
    if semantic_delta == "NONE" and typed_ir.get("semantic_hash") != lowering.get("semantic_hash"):
        _err(errors, "LOWERING_SEMANTIC_DRIFT", "$.stages.lowering.semantic_hash", "semantic_delta=NONE requires typed-IR/lowering semantic identity")

    source_emit_terminates = source.get("emit_terminates")
    if lowering.get("emit_lowered_as_return") is True and source_emit_terminates is not True:
        _err(errors, "EMIT_RETURN_SEMANTIC_LEAK", "$.stages.lowering.emit_lowered_as_return", "lowering may map emit to terminating return only when source semantics explicitly declare emit terminating")

    if execution.get("executed") is not True or not execution.get("execution_receipt_ref"):
        _err(errors, "EXECUTION_RECEIPT_REQUIRED", "$.stages.execution", "target execution must be real and receipted")
    if not _hash64(execution.get("state_hash")):
        _err(errors, "EXECUTION_STATE_HASH_REQUIRED", "$.stages.execution.state_hash", "execution state must be content-addressed")

    if replay.get("replayed") is not True or not replay.get("replay_receipt_ref"):
        _err(errors, "REPLAY_RECEIPT_REQUIRED", "$.stages.replay", "replay must be executed and receipted")
    if not _hash64(replay.get("state_hash")):
        _err(errors, "REPLAY_STATE_HASH_REQUIRED", "$.stages.replay.state_hash", "replay state must be content-addressed")
    if _hash64(execution.get("state_hash")) and _hash64(replay.get("state_hash")) and execution["state_hash"] != replay["state_hash"]:
        _err(errors, "REPLAY_STATE_DIVERGENCE", "$.stages.replay.state_hash", "replay did not reconstruct execution state")

    return {"valid": not errors, "errors": errors}


def differential_oracle(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    ref_validation = validate_chain(reference)
    cand_validation = validate_chain(candidate)
    mismatches: list[dict[str, str]] = []
    if not ref_validation["valid"] or not cand_validation["valid"]:
        return {
            "equivalent": False,
            "reference_validation": ref_validation,
            "candidate_validation": cand_validation,
            "mismatches": [{"stage": "validation", "detail": "both chains must validate before differential comparison"}],
        }

    rs, cs = reference["stages"], candidate["stages"]
    fields = {
        "source": ("semantic_hash",),
        "parse": ("semantic_hash", "grammar_hash"),
        "typed_ir": ("semantic_hash", "type_effect_contract_hash"),
        "lowering": ("semantic_hash", "lowering_contract_hash", "semantic_delta"),
        "execution": ("semantic_hash", "state_hash"),
        "replay": ("semantic_hash", "state_hash"),
    }
    for stage_name, stage_fields in fields.items():
        for field in stage_fields:
            rv, cv = rs[stage_name].get(field), cs[stage_name].get(field)
            if rv != cv:
                mismatches.append({"stage": stage_name, "field": field, "reference": str(rv), "candidate": str(cv)})
    return {
        "equivalent": not mismatches,
        "reference_validation": ref_validation,
        "candidate_validation": cand_validation,
        "mismatches": mismatches,
    }


def build_fixture(*, named_cycle=False, grammar_supports_named=True, emit_terminates=False, emit_as_return=False, final_state_seed="same", lowering_contract_seed="same") -> dict[str, Any]:
    """Deterministic synthetic fixture helper used only by the validator's tests."""
    def h(label: str) -> str:
        return hashlib.sha256(label.encode()).hexdigest()

    source_art = h("source-art")
    parse_art = h("parse-art")
    ir_art = h("ir-art")
    lower_art = h("lower-art")
    exec_art = h("exec-art")
    replay_art = h("replay-art")
    sem = h("program-semantics")
    state = h(final_state_seed)
    return {
        "schema_version": SCHEMA_VERSION,
        "stages": {
            "source": {"artifact_ref": "fixture.clay", "artifact_hash": source_art, "semantic_hash": sem, "cycle_header_form": "NAMED" if named_cycle else "ANONYMOUS", "emit_terminates": emit_terminates},
            "parse": {"artifact_ref": "ast.json", "artifact_hash": parse_art, "parent_artifact_hash": source_art, "semantic_hash": sem, "source_admitted": True, "grammar_hash": h("grammar"), "supports_named_cycle": grammar_supports_named},
            "typed_ir": {"artifact_ref": "typed_ir.json", "artifact_hash": ir_art, "parent_artifact_hash": parse_art, "semantic_hash": sem, "type_effect_checked": True, "type_effect_contract_hash": h("type-effect")},
            "lowering": {"artifact_ref": "lowered.bin", "artifact_hash": lower_art, "parent_artifact_hash": ir_art, "semantic_hash": sem, "semantic_delta": "NONE", "emit_lowered_as_return": emit_as_return, "lowering_contract_hash": h(lowering_contract_seed)},
            "execution": {"artifact_ref": "run.json", "artifact_hash": exec_art, "parent_artifact_hash": lower_art, "semantic_hash": sem, "executed": True, "execution_receipt_ref": "receipt:exec", "state_hash": state},
            "replay": {"artifact_ref": "replay.json", "artifact_hash": replay_art, "parent_artifact_hash": exec_art, "semantic_hash": sem, "replayed": True, "replay_receipt_ref": "receipt:replay", "state_hash": state},
        },
    }
