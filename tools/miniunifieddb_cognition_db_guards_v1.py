#!/usr/bin/env python3
"""Database-level guards for the canonical MiniUnifiedDB cognition store v1.

This module creates TRIGGERS ONLY on the already-existing `mini_cognition_*` tables
owned by `tools/miniunifieddb_cognition_store_v1.py`. It creates no table, database,
truth authority, effect authority, recovery ledger, or alternate cognition store.

Purpose: preserve the store's generation/admission/immutability invariants even when
writes race after Python-side checks or when a caller attempts direct SQL mutation.
"""
from __future__ import annotations

import sqlite3
from typing import Any

SCHEMA = "MINIUNIFIEDDB_COGNITION_DB_GUARDS/v1"

_REQUIRED_TABLES = {
    "entity_state",
    "mini_cognition_objects",
    "mini_cognition_object_admissions",
    "mini_cognition_boot_bindings",
    "mini_cognition_turn_bindings",
}

_TRIGGER_NAMES = {
    "mini_cognition_admission_live_generation_insert",
    "mini_cognition_boot_live_generation_insert",
    "mini_cognition_turn_live_generation_insert",
    "mini_cognition_objects_no_update",
    "mini_cognition_objects_no_delete",
    "mini_cognition_admissions_no_update",
    "mini_cognition_admissions_no_delete",
    "mini_cognition_boot_no_update",
    "mini_cognition_boot_no_delete",
    "mini_cognition_turn_no_update",
    "mini_cognition_turn_no_delete",
}


class CognitionDBGuardError(RuntimeError):
    pass


def _existing_tables(db: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def install_guards(db: sqlite3.Connection) -> dict[str, Any]:
    """Install fail-closed triggers on the existing canonical cognition tables.

    The caller must first install the canonical cognition-store schema. No new tables
    are created here. The generation checks execute inside SQLite immediately before
    the corresponding INSERT, closing the check/write race left by application-only
    validation. Boot objects must be re-admitted in the exact live generation; prior-
    generation admission is durable evidence, not current runtime authority.
    """
    missing = sorted(_REQUIRED_TABLES - _existing_tables(db))
    if missing:
        raise CognitionDBGuardError("COGNITION_GUARD_TABLES_MISSING:" + ",".join(missing))

    db.executescript(
        """
        CREATE TRIGGER IF NOT EXISTS mini_cognition_admission_live_generation_insert
        BEFORE INSERT ON mini_cognition_object_admissions
        BEGIN
          SELECT CASE
            WHEN COALESCE((SELECT generation FROM entity_state WHERE id=1), -1)
                 != NEW.admitted_generation
            THEN RAISE(ABORT, 'COGNITION_STALE_GENERATION')
          END;
        END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_boot_live_generation_insert
        BEFORE INSERT ON mini_cognition_boot_bindings
        BEGIN
          SELECT CASE
            WHEN COALESCE((SELECT generation FROM entity_state WHERE id=1), -1)
                 != NEW.entity_generation
            THEN RAISE(ABORT, 'COGNITION_STALE_GENERATION')
            WHEN NEW.schema != 'MINIUNIFIEDDB_COGNITION_BOOT_BINDING/v1'
            THEN RAISE(ABORT, 'COGNITION_BOOT_SCHEMA_MISMATCH')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='ZERO_IDENTITY'
                 AND object_digest=NEW.zero_identity_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:ZERO_IDENTITY')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='GRF'
                 AND object_digest=NEW.grf_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:GRF')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='HYPERPOSITION'
                 AND object_digest=NEW.hyperposition_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:HYPERPOSITION')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='BUNDLED_MANIFEST'
                 AND object_digest=NEW.bundled_manifest_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:BUNDLED_MANIFEST')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='LOCAL_MODEL_CHECKPOINT'
                 AND object_digest=NEW.local_model_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:LOCAL_MODEL_CHECKPOINT')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='TOKENIZER'
                 AND object_digest=NEW.tokenizer_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:TOKENIZER')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='JSPACE_PROFILE'
                 AND object_digest=NEW.jspace_profile_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:JSPACE_PROFILE')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='JACOBIAN_LENS_PROFILE'
                 AND object_digest=NEW.jacobian_lens_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:JACOBIAN_LENS_PROFILE')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='WORKSPACE_CALIBRATION'
                 AND object_digest=NEW.workspace_calibration_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:WORKSPACE_CALIBRATION')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='BOOT_SOURCE_LOCK'
                 AND object_digest=NEW.boot_source_lock_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:BOOT_SOURCE_LOCK')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_object_admissions
               WHERE object_kind='POLICY_AUTHORITY'
                 AND object_digest=NEW.policy_authority_digest
                 AND admitted_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_BOOT_OBJECT_NOT_ADMITTED:POLICY_AUTHORITY')
          END;
        END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_turn_live_generation_insert
        BEFORE INSERT ON mini_cognition_turn_bindings
        BEGIN
          SELECT CASE
            WHEN COALESCE((SELECT generation FROM entity_state WHERE id=1), -1)
                 != NEW.entity_generation
            THEN RAISE(ABORT, 'COGNITION_STALE_GENERATION')
            WHEN NEW.schema != 'MINIUNIFIEDDB_COGNITION_TURN_BINDING/v1'
            THEN RAISE(ABORT, 'COGNITION_TURN_SCHEMA_MISMATCH')
            WHEN NOT EXISTS(
              SELECT 1 FROM mini_cognition_boot_bindings
               WHERE binding_digest=NEW.boot_binding_digest
                 AND entity_generation=NEW.entity_generation)
            THEN RAISE(ABORT, 'COGNITION_TURN_BOOT_BINDING_STALE_OR_MISSING')
          END;
        END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_objects_no_update
        BEFORE UPDATE ON mini_cognition_objects
        BEGIN SELECT RAISE(ABORT, 'COGNITION_OBJECT_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_objects_no_delete
        BEFORE DELETE ON mini_cognition_objects
        BEGIN SELECT RAISE(ABORT, 'COGNITION_OBJECT_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_admissions_no_update
        BEFORE UPDATE ON mini_cognition_object_admissions
        BEGIN SELECT RAISE(ABORT, 'COGNITION_ADMISSION_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_admissions_no_delete
        BEFORE DELETE ON mini_cognition_object_admissions
        BEGIN SELECT RAISE(ABORT, 'COGNITION_ADMISSION_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_boot_no_update
        BEFORE UPDATE ON mini_cognition_boot_bindings
        BEGIN SELECT RAISE(ABORT, 'COGNITION_BOOT_BINDING_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_boot_no_delete
        BEFORE DELETE ON mini_cognition_boot_bindings
        BEGIN SELECT RAISE(ABORT, 'COGNITION_BOOT_BINDING_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_turn_no_update
        BEFORE UPDATE ON mini_cognition_turn_bindings
        BEGIN SELECT RAISE(ABORT, 'COGNITION_TURN_BINDING_IMMUTABLE'); END;

        CREATE TRIGGER IF NOT EXISTS mini_cognition_turn_no_delete
        BEFORE DELETE ON mini_cognition_turn_bindings
        BEGIN SELECT RAISE(ABORT, 'COGNITION_TURN_BINDING_IMMUTABLE'); END;
        """
    )
    return guard_status(db)


def guard_status(db: sqlite3.Connection) -> dict[str, Any]:
    observed = {
        str(row[0])
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'mini_cognition_%'"
        )
    }
    missing = sorted(_TRIGGER_NAMES - observed)
    return {
        "ok": not missing,
        "schema": SCHEMA,
        "missing_triggers": missing,
        "trigger_count": len(_TRIGGER_NAMES & observed),
        "creates_tables": False,
        "authority": "MiniUnifiedDB",
    }


__all__ = ["SCHEMA", "CognitionDBGuardError", "install_guards", "guard_status"]
