#!/usr/bin/env python3
"""GRID10 unified runtime v3: Fabric + heartbeat + persistent agency on one SQLite authority.

This closes the next Triggerword-4 integration gap after v2: the durable AgencyState /
GoalContract / HOLD-WAKE substrate must not drift into a second physical database while the
cognitive Fabric and heartbeat use another one.

The module is deterministic and provider-free. It does not grant canonical world-truth or
external-effect authority; model/GRID outputs remain candidate cognition and real effects
remain behind the surrounding EffectGate/EffectJournal boundary.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from grid10_fabric import Fabric
from grid10_cognitive_heartbeat_v1 import (
    CognitiveHeartbeatRuntime,
    CognitiveHeartbeatStore,
    HeartbeatConfig,
)
from grid10_cognitive_unified_runtime_v2 import UnifiedDbFingerprint, fingerprint_sqlite
from grid10_persistent_agency_v1 import PersistentAgencyStore


def assert_unified_runtime_authority(
    fabric: Fabric,
    heartbeat: CognitiveHeartbeatStore,
    agency: PersistentAgencyStore,
) -> UnifiedDbFingerprint:
    """Fail closed unless all three runtime stores resolve to one physical SQLite authority."""
    fps = {
        "fabric": fingerprint_sqlite(Path(fabric.path)),
        "heartbeat": fingerprint_sqlite(Path(heartbeat.path)),
        "agency": fingerprint_sqlite(Path(agency.path)),
    }
    baseline = fps["fabric"]
    for name, fp in fps.items():
        same_physical = (
            fp.realpath == baseline.realpath
            and fp.device == baseline.device
            and fp.inode == baseline.inode
            and fp.main_db_path == baseline.main_db_path
        )
        if not same_physical:
            raise RuntimeError(
                "UNIFIEDDB_AGENCY_AUTHORITY_SPLIT:"
                + str({k: asdict(v) for k, v in fps.items()})
            )
        if fp.schema_digest != baseline.schema_digest:
            raise RuntimeError(f"UNIFIEDDB_AGENCY_SCHEMA_VIEW_MISMATCH:{name}")
    return baseline


def build_unified_agency_runtime(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
) -> tuple[
    Fabric,
    CognitiveHeartbeatStore,
    PersistentAgencyStore,
    CognitiveHeartbeatRuntime,
    UnifiedDbFingerprint,
]:
    """Create all deterministic cognition-control stores on one DB, then attest identity."""
    db = Path(unified_db).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)

    # Initialize every schema before fingerprinting so each view is compared after the same
    # complete schema exists. No secondary DB or rebuildable projection is introduced here.
    fabric = Fabric(db)
    heartbeat = CognitiveHeartbeatStore(db)
    agency = PersistentAgencyStore(db)
    fingerprint = assert_unified_runtime_authority(fabric, heartbeat, agency)

    runtime = CognitiveHeartbeatRuntime(
        fabric,
        heartbeat,
        config=HeartbeatConfig(allow_regulator_writes=bool(allow_regulator_writes)),
    )
    return fabric, heartbeat, agency, runtime, fingerprint


def runtime_authority_receipt(
    fabric: Fabric,
    heartbeat: CognitiveHeartbeatStore,
    agency: PersistentAgencyStore,
) -> dict[str, Any]:
    fp = assert_unified_runtime_authority(fabric, heartbeat, agency)
    return {
        "schema": "GRID10_UNIFIED_AGENCY_RUNTIME_AUTHORITY/v3",
        "status": "PASS",
        "scope": "ONE_PHYSICAL_SQLITE_AUTHORITY_FOR_FABRIC_HEARTBEAT_AND_PERSISTENT_AGENCY",
        "fingerprint": asdict(fp),
        "canonical_truth_authority_changed": False,
        "external_effect_authority_changed": False,
        "provider_calls": 0,
        "physical_grid10_credit": 0,
        "whole_hcu_credit": 0,
    }
