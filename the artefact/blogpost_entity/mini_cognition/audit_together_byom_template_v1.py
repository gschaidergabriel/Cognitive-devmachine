#!/usr/bin/env python3
"""Fail-closed Together BYOM architecture compatibility audit.

The canonical semantic discriminator remains `assess_pair()`. For real preflight this file
can additionally fetch both Hugging Face `config.json` files at exact 40-hex revisions,
bind their byte digests into the audit result, then run the same discriminator. This is
still pre-provider evidence only: a compatible local result never proves Together admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REV_RE = re.compile(r"[0-9a-fA-F]{40}")
PROVENANCE_KEY = "__clay_hf_provenance__"


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


def exact_revision(value: str) -> str:
    value = str(value or "").strip().lower()
    if not REV_RE.fullmatch(value):
        raise ValueError("expected exact 40-hex Hugging Face revision")
    return value


def hf_config_url(model: str, revision: str) -> str:
    revision = exact_revision(revision)
    parts = str(model).split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("expected Hugging Face model id in owner/name form")
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in parts)
    return f"https://huggingface.co/{encoded}/resolve/{revision}/config.json"


def attest_config_bytes(model: str, revision: str, raw: bytes) -> dict[str, Any]:
    revision = exact_revision(revision)
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Hugging Face config must be a JSON object")
    # Validate the semantic fields at attestation time so malformed remote bytes never
    # acquire provenance merely because they parsed as JSON.
    _one_arch(value, "attested")
    _model_type(value, "attested")
    value = dict(value)
    value[PROVENANCE_KEY] = {
        "model": str(model),
        "revision": revision,
        "config_sha256": hashlib.sha256(raw).hexdigest(),
    }
    return value


def fetch_exact_config(model: str, revision: str, timeout_seconds: int = 20) -> dict[str, Any]:
    url = hf_config_url(model, revision)
    request = urllib.request.Request(url, headers={"User-Agent": "claycog-byom-audit/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except Exception as exc:
        raise OSError(f"exact Hugging Face config fetch failed: {type(exc).__name__}") from exc
    return attest_config_bytes(model, revision, raw)


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
    if custom.get("auto_map"):
        reasons.append("CUSTOM_CODE_REQUIRED")
    if template.get("auto_map"):
        reasons.append("TEMPLATE_CUSTOM_CODE_REQUIRED")

    result: dict[str, Any] = {
        "schema": "claycog-together-byom-static-compatibility/v2",
        "custom": {"architecture": custom_arch, "model_type": custom_type},
        "template": {"architecture": template_arch, "model_type": template_type},
        "compatible": not reasons,
        "reasons": reasons,
        "evidence_scope": (
            "EXACT_REVISION_LOCAL_PRE_PROVIDER_ONLY when provenance is present; otherwise STATIC_PRE_PROVIDER_ONLY; "
            "compatible=true is not Together admission; compatible=false rejects the pair before upload/create"
        ),
    }
    custom_provenance = custom.get(PROVENANCE_KEY)
    template_provenance = template.get(PROVENANCE_KEY)
    if custom_provenance is not None or template_provenance is not None:
        if not isinstance(custom_provenance, dict) or not isinstance(template_provenance, dict):
            raise ValueError("both exact-revision provenance records are required together")
        result["exact_hf_provenance"] = {
            "custom": dict(custom_provenance),
            "template": dict(template_provenance),
        }
    return result


def load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def _resolve_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    file_mode = bool(args.custom_config or args.template_config)
    exact_mode = bool(args.custom_model or args.custom_revision or args.template_model or args.template_revision)
    if file_mode and exact_mode:
        raise ValueError("choose local-config mode or exact-HF-revision mode, not both")
    if file_mode:
        if not args.custom_config or not args.template_config:
            raise ValueError("local-config mode requires --custom-config and --template-config")
        return load_json(args.custom_config), load_json(args.template_config)
    if exact_mode:
        if not all((args.custom_model, args.custom_revision, args.template_model, args.template_revision)):
            raise ValueError("exact-HF-revision mode requires both model ids and both exact revisions")
        return (
            fetch_exact_config(args.custom_model, args.custom_revision, args.timeout_seconds),
            fetch_exact_config(args.template_model, args.template_revision, args.timeout_seconds),
        )
    raise ValueError("no audit inputs supplied")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--custom-config")
    ap.add_argument("--template-config")
    ap.add_argument("--custom-model")
    ap.add_argument("--custom-revision")
    ap.add_argument("--template-model")
    ap.add_argument("--template-revision")
    ap.add_argument("--timeout-seconds", type=int, default=20)
    args = ap.parse_args()
    try:
        custom, template = _resolve_inputs(args)
        result = assess_pair(custom, template)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        print(json.dumps({"schema": "claycog-together-byom-static-compatibility/v2", "compatible": False, "reasons": ["INVALID_CONFIG_OR_PROVENANCE"], "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["compatible"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
