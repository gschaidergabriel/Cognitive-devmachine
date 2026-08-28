#!/usr/bin/env python3
"""Audit exact FREE_ONLY provider lanes without exposing credential values.

Run through free_swarm_exec_with_vault.py so admitted local credentials are loaded.
Output contains only non-secret credential fingerprints, model/route names and the
fail-closed economic binding result used by autonomous swarm execution.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_free_go_swarm as base
from free_lane_provenance import current_lane_binding

# Keep this audit aligned with the concrete provider surfaces used by the swarm.
ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "nvidia": "https://integrate.api.nvidia.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}


def main() -> int:
    rows = []
    for spec in base.PROVIDERS:
        if spec.name not in ENDPOINTS:
            continue
        try:
            keys = base.collect_keys(spec)
        except Exception as exc:
            rows.append({"provider": spec.name, "keys": 0, "error": type(exc).__name__})
            continue
        models = base.split_values(os.getenv(spec.models_env)) or list(spec.default_models)
        if spec.name == "openrouter" and "openrouter/free" not in models:
            models = ["openrouter/free"]
        for key in keys:
            fp = base.key_fingerprint(key)
            for model in models:
                binding = current_lane_binding(spec.name, fp, model, ENDPOINTS[spec.name])
                rows.append({
                    "provider": spec.name,
                    "credential_fingerprint": fp,
                    "model_or_route": model,
                    "ok": bool(binding.get("ok")),
                    "reason": binding.get("reason"),
                    "admission_epoch": binding.get("admission_epoch"),
                })
    print(json.dumps({
        "schema": "CLAY_FREE_LANE_BINDING_AUDIT/v1",
        "secret_values_logged": False,
        "rows": rows,
    }, indent=2, ensure_ascii=False))
    return 0 if any(row.get("ok") for row in rows) else 4


if __name__ == "__main__":
    raise SystemExit(main())
