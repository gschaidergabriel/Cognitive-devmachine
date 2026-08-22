#!/usr/bin/env python3
"""Fail-closed static BYOM architecture compatibility audit.

This is a pre-provider discriminator only. It does not prove Together acceptance.
It rejects obviously incompatible custom/template pairs before dataset upload or billed create.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _one_arch(config: dict[str, Any], role: str) -> str:
    architectures = config.get("architectures")
    if not isinstance(architectures, list) or len(architectures) != 1 or not isinstance(architectures[0], str):
        raise ValueError(f"{role}: expected exactly one string architecture")
    return architectures[0]


def _model_type(config: dict[str, Any], role: str) -> str:
    value = config.get("model_type")
    if not isinstance(value, str) or not value:
        raise ValueError(f"{role}: missing model_type")
    return value


def assess_pair(custom: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    custom_arch = _one_arch(custom, "custom")
    template_arch = _one_arch(template, "template")
    custom_type = _model_type(custom, "custom")
    template_type = _model_type(template, "template")

    reasons: list[str] = []
    if not custom_arch.endswith("ForCausalLM"):
        reasons.append("CUSTOM_NOT_CAUSAL_LM")
    if not template_arch.endswith("ForCausalLM"):
        reasons.append("TEMPLATE_NOT_CAUSAL_LM")
    if custom_arch != template_arch:
        reasons.append("ARCHITECTURE_CLASS_MISMATCH")
    if custom_type != template_type:
        reasons.append("MODEL_TYPE_MISMATCH")

    return {
        "schema": "claycog-together-byom-static-compatibility/v1",
        "custom": {"architecture": custom_arch, "model_type": custom_type},
        "template": {"architecture": template_arch, "model_type": template_type},
        "compatible": not reasons,
        "reasons": reasons,
        "evidence_scope": (
            "STATIC_FAIL_CLOSED_PRE_PROVIDER_ONLY; compatible=true is not Together admission; "
            "compatible=false rejects the pair before upload/create under the documented architecture-match law"
        ),
    }


def load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--custom-config", required=True)
    ap.add_argument("--template-config", required=True)
    args = ap.parse_args()
    try:
        result = assess_pair(load_json(args.custom_config), load_json(args.template_config))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"schema": "claycog-together-byom-static-compatibility/v1", "compatible": False, "reasons": ["INVALID_CONFIG"], "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["compatible"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
