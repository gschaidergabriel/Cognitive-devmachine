#!/usr/bin/env python3
"""Successor-dynamic FREE provider + credential/route economic boundary receipt.

Extends the hardened provider-admission receipt with the current FREE lane economic
boundary.  It deliberately performs no provider call and inherits the sanitized
child environment plus socket/DNS/datagram tripwires from the hardened runner.

A PASS is component evidence that the exact clean source enforces the tested
provider/admission/credential/route fail-closed rules.  It is not provider runtime,
model, HCU, J-Space, training, effect, or whole-product credit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import run_free_swarm_admission_boundary_receipt_hardened_868 as hardened

base = hardened.base
ROOT = Path(__file__).resolve().parents[1]
SELF_REL = "tools/run_free_lane_boundary_receipt_current.py"
ECONOMIC_REL = "governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json"
LANE_REL = "tools/free_lane_provenance.py"
TEST_REL = "tests/test_free_lane_economic_boundary_current.py"
TEST_MODULE = "tests.test_free_lane_economic_boundary_current"


def _install_current_lane_boundary() -> None:
    if getattr(base, "_CLAY_CURRENT_FREE_LANE_BOUNDARY_INSTALLED", False):
        return

    base.TEST_MODULES = tuple(dict.fromkeys((*base.TEST_MODULES, TEST_MODULE)))
    base.TEST_PATHS = tuple(dict.fromkeys((*base.TEST_PATHS, ROOT / TEST_REL)))
    base.SOURCE_PATHS = tuple(dict.fromkeys((
        *base.SOURCE_PATHS,
        SELF_REL,
        ECONOMIC_REL,
        LANE_REL,
        TEST_REL,
    )))

    original_authority_snapshot = base._authority_snapshot

    def authority_snapshot() -> dict[str, Any]:
        snapshot = original_authority_snapshot()
        economic_path = ROOT / ECONOMIC_REL
        economic = base._read_json(economic_path)
        economic_epoch = str(economic.get("authority_epoch") or "").strip()
        if economic.get("mode") != "FREE_ONLY":
            raise RuntimeError("FREE_LANE_ECONOMIC_PROVENANCE_NOT_FREE_ONLY")
        if not economic_epoch or economic_epoch != snapshot.get("epoch"):
            raise RuntimeError(
                "FREE_LANE_ECONOMIC_PROVENANCE_EPOCH_MISMATCH:"
                f"supervisor={snapshot.get('epoch')}:economic={economic_epoch}"
            )
        providers = economic.get("providers") or {}
        if not isinstance(providers, dict):
            raise RuntimeError("FREE_LANE_ECONOMIC_PROVIDERS_OBJECT_REQUIRED")
        nvidia = providers.get("nvidia") or {}
        snapshot["economic_provenance"] = {
            "schema": economic.get("schema"),
            "epoch": economic_epoch,
            "sha256": base._sha256_file(economic_path),
            "unknown_route": (economic.get("rules") or {}).get("unknown_route"),
            "paid_fallback_attempt_count": (economic.get("rules") or {}).get("paid_fallback_attempt_count"),
            "openrouter_allowed_routes": (providers.get("openrouter") or {}).get("allowed_routes") or [],
            "nvidia_bound_credential_count": len(nvidia.get("admitted_credential_fingerprints") or []),
            "mistral_default": (providers.get("mistral") or {}).get("default"),
        }
        return snapshot

    base._authority_snapshot = authority_snapshot

    original_write_receipt = base._write_receipt

    def write_receipt(path: Path | None, receipt: dict[str, Any]) -> None:
        source = receipt.setdefault("source", {})
        source["receipt_runner_current_free_lane"] = SELF_REL
        source["current_free_lane_boundary"] = {
            "successor_dynamic_epoch_from_supervisor_inbox": True,
            "economic_provenance_manifest_bound": ECONOMIC_REL,
            "credential_route_gate_source_bound": LANE_REL,
            "economic_boundary_test": TEST_REL,
            "networkless_component_acceptance": True,
        }
        fences = receipt.setdefault("fences", {})
        fences["credential_route_economic_boundary"] = (
            "ENFORCED_BY_TEST_FREE_LANE_ECONOMIC_BOUNDARY_CURRENT"
        )
        fences["unknown_or_paid_route"] = "FAIL_CLOSED_BY_CURRENT_ECONOMIC_PROVENANCE"
        fences["nvidia_unlisted_credential"] = "FAIL_CLOSED_BEFORE_PROVIDER_NETWORK"
        fences["mistral_without_provider_side_free_mode"] = "FAIL_CLOSED_BEFORE_PROVIDER_NETWORK"
        result = receipt.setdefault("result", {})
        result["successor_scope"] = "FREE_SWARM_PROVIDER_PLUS_CREDENTIAL_ROUTE_ECONOMIC_BOUNDARY_COMPONENT_ONLY"
        result["provider_runtime_credit"] = 0
        result["model_runtime_credit"] = 0
        result["jspace_model_runtime_credit"] = 0
        result["training_credit"] = 0
        original_write_receipt(path, receipt)

    base._write_receipt = write_receipt
    base._CLAY_CURRENT_FREE_LANE_BOUNDARY_INSTALLED = True


_install_current_lane_boundary()


if __name__ == "__main__":
    raise SystemExit(base.main())
