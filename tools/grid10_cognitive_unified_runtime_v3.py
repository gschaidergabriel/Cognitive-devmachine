#!/usr/bin/env python3
"""Compatibility adapter for the retired GRID10 unified-runtime v3 implementation.

The original v3 duplicated the already-canonical v2 shared-UnifiedDB construction and was
intentionally reverted.  Runtime v4 still imports the historical v3 API names, so deleting
v3 outright left v4 non-importable in a clean checkout.

This file restores only the API surface, not a second implementation: construction and
physical SQLite authority checks delegate directly to v2.  It therefore preserves the
revert's convergence intent while removing the dead import dependency.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from grid10_cognitive_unified_runtime_v2 import (
    UnifiedDbFingerprint,
    assert_shared_unifieddb_authority,
    build_shared_runtime,
)
from grid10_fabric import Fabric
from grid10_cognitive_heartbeat_v1 import CognitiveHeartbeatStore
from grid10_persistent_agency_v1 import PersistentAgencyStore

SCHEMA = "GRID10_UNIFIED_AGENCY_RUNTIME_COMPAT/v3"


def build_unified_agency_runtime(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
):
    """Delegate the historical v3 constructor to the single v2 implementation."""
    return build_shared_runtime(
        unified_db,
        allow_regulator_writes=allow_regulator_writes,
    )


def runtime_authority_receipt(
    fabric: Fabric,
    heartbeat: CognitiveHeartbeatStore,
    agency: PersistentAgencyStore,
) -> dict[str, Any]:
    """Emit a scoped authority receipt using v2's exact physical-DB attestation."""
    fp: UnifiedDbFingerprint = assert_shared_unifieddb_authority(
        fabric,
        heartbeat,
        agency,
    )
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "scope": "ONE_PHYSICAL_SQLITE_AUTHORITY_FOR_FABRIC_HEARTBEAT_AND_PERSISTENT_AGENCY",
        "fingerprint": asdict(fp),
        "implementation": "DELEGATES_TO_GRID10_UNIFIED_RUNTIME_V2",
        "duplicate_v3_state_authority": False,
        "canonical_truth_authority_changed": False,
        "external_effect_authority_changed": False,
        "provider_calls": 0,
        "physical_grid10_credit": 0,
        "whole_hcu_credit": 0,
    }
