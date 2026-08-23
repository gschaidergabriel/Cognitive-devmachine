#!/usr/bin/env python3
"""Canonical Mini Entity reference runtime integration layer.

The proven generic profile-pipeline implementation remains byte-preserved in
``_clay_profile_pipeline_runtime_v063_core``.  This module is the single public runtime
surface and adds the current MiniUnifiedDB cognition bootstrap plus the canonical
pre-inference Cognitive Fabric admission path.  It deliberately keeps post-commit UCF
finalization fail-closed until exact source/runtime identity needed by the final v1 receipt
is available; a successful MiniUnifiedDB commit is never rolled back or retried because
receipt finalization is evidence-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

import claycode_structured_backend as clay
import _clay_profile_pipeline_runtime_v063_core as _core
import miniunifieddb_cognition_bootstrap_v1 as cognition_bootstrap
import pipeline_cognitive_fabric_admission_v1 as cognitive_fabric_admission

VERSION = "clay-profile-pipeline-runtime/0.6.4"
PROFILE_SCHEMAS = _core.PROFILE_SCHEMAS
IMMUTABLE_GUARD = _core.IMMUTABLE_GUARD
PipelineFault = _core.PipelineFault
_finite_number = _core._finite_number
_canonical_json = _core._canonical_json
_sha256_text = _core._sha256_text
_utc_now = _core._utc_now
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ProfilePipelineRuntime(_core.ProfilePipelineRuntime):
    """Single public runtime with MiniUnifiedDB-bound cognition admission."""

    def __init__(
        self,
        *,
        root: str | Path = ".",
        allow_network: bool = False,
        provider_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        local_exec_runner: str | Path | None = None,
    ):
        super().__init__(
            root=root,
            allow_network=allow_network,
            provider_override=provider_override,
            local_exec_runner=local_exec_runner,
        )
        # Keep this literal: the source guard treats the explicit effect vocabulary as part
        # of the executable contract and rejects comment/string-only pseudo-wiring.
        self.allowed_effects = {
            "pipeline_init",
            "pipeline_profile_read",
            "pipeline_state_read",
            "pipeline_collect",
            "pipeline_compile",
            "pipeline_build_prompt",
            "pipeline_cognitive_fabric_admit",
            "inference_generate",
            "pipeline_gate",
            "pipeline_commit",
            "pipeline_cognitive_fabric_finalize",
        }

    def _db(self, value: str) -> sqlite3.Connection:
        """Open one writable MiniUnifiedDB connection with FK enforcement pre-transaction."""
        db = super()._db(value)
        try:
            cognition_bootstrap.prepare_connection(db)
        except Exception:
            db.close()
            raise
        return db

    def effect(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in self.allowed_effects:
            raise clay.StructuredFault("EFFECT_DENIED:" + str(kind))
        payload = payload or {}
        handlers = {
            "pipeline_init": self._pipeline_init,
            "pipeline_profile_read": self._pipeline_profile_read,
            "pipeline_state_read": self._pipeline_state_read,
            "pipeline_collect": self._pipeline_collect,
            "pipeline_compile": self._pipeline_compile,
            "pipeline_build_prompt": self._pipeline_build_prompt,
            "pipeline_cognitive_fabric_admit": self._pipeline_cognitive_fabric_admit,
            "inference_generate": self._inference_generate,
            "pipeline_gate": self._pipeline_gate,
            "pipeline_commit": self._pipeline_commit,
            "pipeline_cognitive_fabric_finalize": self._pipeline_cognitive_fabric_finalize,
        }
        started = time.time()
        ok = False
        try:
            result = handlers[kind](payload)
            ok = bool(result.get("ok", False))
            return result
        finally:
            self.effect_trace.append(
                {
                    "kind": kind,
                    "ok": ok,
                    "ms": round((time.time() - started) * 1000, 3),
                    "payload_hash": hashlib.sha256(
                        json.dumps(payload, sort_keys=True, default=str).encode()
                    ).hexdigest(),
                }
            )

    def _pipeline_init(self, p: dict[str, Any]) -> dict[str, Any]:
        """Bootstrap profile/pipeline + cognition schemas in one caller-owned transaction."""
        db = self._db(str(p["entity_db"]))
        try:
            db.execute("BEGIN IMMEDIATE")
            entity_table_preexisting = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
            ).fetchone() is not None
            native_row_preexisting = False
            if entity_table_preexisting:
                try:
                    native_row_preexisting = db.execute(
                        "SELECT 1 FROM entity_state WHERE id=1"
                    ).fetchone() is not None
                except sqlite3.Error as exc:
                    raise PipelineFault("ENTITY_STATE_SCHEMA_INVALID") from exc
            eos_preexisting = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='eos_pipeline_state'"
            ).fetchone() is not None
            eos_columns = {
                str(row[1])
                for row in db.execute("PRAGMA table_info(eos_pipeline_state)").fetchall()
            } if eos_preexisting else set()

            if not native_row_preexisting and "generation" in eos_columns:
                legacy_row = db.execute(
                    "SELECT generation FROM eos_pipeline_state WHERE singleton=1"
                ).fetchone()
                legacy_generation = int(legacy_row[0]) if legacy_row is not None else 0
                if legacy_generation != 0:
                    raise PipelineFault("LEGACY_GENERATION_MIGRATION_REQUIRED")

            db.execute(
                """CREATE TABLE IF NOT EXISTS entity_state(
                     id INTEGER PRIMARY KEY CHECK(id=1),
                     generation INTEGER NOT NULL,
                     active_profile TEXT,
                     created_at TEXT NOT NULL,
                     updated_at TEXT NOT NULL)"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS profiles(
                     profile_id TEXT PRIMARY KEY,
                     profile_json TEXT NOT NULL,
                     profile_sha256 TEXT NOT NULL,
                     updated_at TEXT NOT NULL)"""
            )
            now = _utc_now()
            db.execute(
                """INSERT OR IGNORE INTO entity_state(
                       id,generation,active_profile,created_at,updated_at)
                   VALUES(1,0,NULL,?,?)""",
                (now, now),
            )

            if eos_preexisting and "generation" in eos_columns:
                db.execute(
                    """CREATE TABLE eos_pipeline_state_v2(
                         singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                         continuity_json TEXT NOT NULL DEFAULT '{}',
                         canonical_json TEXT NOT NULL DEFAULT '{}',
                         canonical_hash TEXT NOT NULL DEFAULT '',
                         cursors_json TEXT NOT NULL DEFAULT '{}',
                         updated_at REAL NOT NULL DEFAULT 0)"""
                )
                db.execute(
                    """INSERT INTO eos_pipeline_state_v2(
                           singleton,continuity_json,canonical_json,canonical_hash,cursors_json,updated_at)
                       SELECT singleton,continuity_json,canonical_json,canonical_hash,cursors_json,updated_at
                       FROM eos_pipeline_state"""
                )
                db.execute("DROP TABLE eos_pipeline_state")
                db.execute("ALTER TABLE eos_pipeline_state_v2 RENAME TO eos_pipeline_state")
            else:
                db.execute(
                    """CREATE TABLE IF NOT EXISTS eos_pipeline_state(
                         singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                         continuity_json TEXT NOT NULL DEFAULT '{}',
                         canonical_json TEXT NOT NULL DEFAULT '{}',
                         canonical_hash TEXT NOT NULL DEFAULT '',
                         cursors_json TEXT NOT NULL DEFAULT '{}',
                         updated_at REAL NOT NULL DEFAULT 0)"""
                )
            db.execute("INSERT OR IGNORE INTO eos_pipeline_state(singleton) VALUES(1)")

            consumed_preexisting = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='eos_pipeline_consumed'"
            ).fetchone() is not None
            consumed_columns = {
                str(row[1])
                for row in db.execute("PRAGMA table_info(eos_pipeline_consumed)").fetchall()
            } if consumed_preexisting else set()
            if consumed_preexisting and "source_namespace" not in consumed_columns:
                legacy_consumed_count = int(
                    db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0]
                )
                if legacy_consumed_count:
                    raise PipelineFault("LEGACY_CONSUMED_NAMESPACE_MIGRATION_REQUIRED")
                db.execute(
                    """CREATE TABLE eos_pipeline_consumed_v2(
                         source_namespace TEXT NOT NULL,
                         source_kind TEXT NOT NULL,
                         source_id TEXT NOT NULL,
                         output_id TEXT NOT NULL,
                         consumed_at REAL NOT NULL,
                         PRIMARY KEY(source_namespace,source_kind,source_id))"""
                )
                db.execute("DROP TABLE eos_pipeline_consumed")
                db.execute("ALTER TABLE eos_pipeline_consumed_v2 RENAME TO eos_pipeline_consumed")
            else:
                db.execute(
                    """CREATE TABLE IF NOT EXISTS eos_pipeline_consumed(
                         source_namespace TEXT NOT NULL,
                         source_kind TEXT NOT NULL,
                         source_id TEXT NOT NULL,
                         output_id TEXT NOT NULL,
                         consumed_at REAL NOT NULL,
                         PRIMARY KEY(source_namespace,source_kind,source_id))"""
                )
            db.execute(
                """CREATE TABLE IF NOT EXISTS eos_pipeline_outputs(
                     output_id TEXT PRIMARY KEY,
                     ts REAL NOT NULL,
                     generation INTEGER NOT NULL,
                     profile_id TEXT NOT NULL,
                     output_json TEXT NOT NULL,
                     provider_kind TEXT NOT NULL,
                     model TEXT,
                     packet_hash TEXT NOT NULL,
                     canonical_hash TEXT NOT NULL)"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS eos_pipeline_packets(
                     packet_hash TEXT PRIMARY KEY,
                     output_id TEXT NOT NULL,
                     ts REAL NOT NULL,
                     generation INTEGER NOT NULL,
                     profile_id TEXT NOT NULL,
                     source_count INTEGER NOT NULL,
                     canonical_hash TEXT NOT NULL)"""
            )

            cognition = cognition_bootstrap.install_cognition_schema(db)
            if not cognition.get("ok"):
                raise PipelineFault("COGNITION_BOOTSTRAP_FAILED")
            if cognition.get("entity_generation") != 0 and not native_row_preexisting:
                raise PipelineFault("COGNITION_BOOTSTRAP_FRESH_GENERATION_DRIFT")

            db.commit()
            return {
                "ok": True,
                "cognition_schema": cognition.get("schema"),
                "cognition_tables": cognition.get("installed_tables", []),
            }
        except Exception as exc:
            db.rollback()
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}
        finally:
            db.close()

    @staticmethod
    def _require_digest(value: Any, name: str) -> str:
        if type(value) is not str or _HEX64.fullmatch(value) is None:
            raise PipelineFault(name + ":SHA256_REQUIRED")
        if value in {"0" * 64, "f" * 64}:
            raise PipelineFault(name + ":PLACEHOLDER_REJECTED")
        return value

    def _pipeline_cognitive_fabric_admit(self, p: dict[str, Any]) -> dict[str, Any]:
        """Resolve one already-active MiniUnifiedDB turn and compile candidate-only admission."""
        try:
            entity_db = str(p["entity_db"])
            previous = p["previous"]
            data = p["data"]
            profile = p["profile"]
            if not isinstance(previous, Mapping):
                raise PipelineFault("PREVIOUS_OBJECT_REQUIRED")
            if not isinstance(data, Mapping):
                raise PipelineFault("COGNITIVE_ADMISSION_DATA_REQUIRED")
            if not isinstance(profile, Mapping):
                raise PipelineFault("PROFILE_OBJECT_REQUIRED")
            generation = previous.get("generation")
            if type(generation) is not int or generation < 0:
                raise PipelineFault("GENERATION_INVALID")
            compiled = data.get("compiled")
            prompt = data.get("prompt")
            invocation = data.get("invocation")
            if not isinstance(compiled, Mapping):
                raise PipelineFault("COMPILED_OBJECT_REQUIRED")
            if not isinstance(prompt, Mapping):
                raise PipelineFault("PROMPT_OBJECT_REQUIRED")
            if not isinstance(invocation, Mapping):
                raise PipelineFault("COGNITION_INVOCATION_OBJECT_REQUIRED")

            with self._read_only_db(entity_db) as db:
                row = db.execute(
                    "SELECT generation FROM entity_state WHERE id=1"
                ).fetchone()
                if row is None or int(row["generation"]) != generation:
                    raise PipelineFault("STALE_GENERATION")
                admitted = cognitive_fabric_admission.build_pre_inference_admission(
                    db,
                    entity_generation=generation,
                    invocation=invocation,
                    compiled=compiled,
                    prompt=prompt,
                    profile=profile,
                    origin=VERSION,
                )

            if type(admitted) is not dict or admitted.get("ok") is not True:
                raise PipelineFault("COGNITIVE_FABRIC_ADMISSION_FAILED")
            if admitted.get("generation") != generation:
                raise PipelineFault("COGNITIVE_FABRIC_GENERATION_DRIFT")
            if admitted.get("canonical_state_hash") != compiled.get("canonical_state_hash"):
                raise PipelineFault("COGNITIVE_FABRIC_CANONICAL_HASH_DRIFT")
            if admitted.get("packet_hash") != compiled.get("packet_hash"):
                raise PipelineFault("COGNITIVE_FABRIC_PACKET_HASH_DRIFT")
            self._require_digest(
                admitted.get("inference_packet_digest"), "inference_packet_digest"
            )
            self._require_digest(
                admitted.get("cognitive_fabric_receipt_digest"),
                "cognitive_fabric_admission_receipt_digest",
            )
            return admitted
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        """Execute candidate inference only under the exact admitted packet/receipt identity."""
        try:
            packet_digest = self._require_digest(
                p.get("inference_packet_digest"), "inference_packet_digest"
            )
            admission_digest = self._require_digest(
                p.get("cognitive_fabric_admission_receipt_digest"),
                "cognitive_fabric_admission_receipt_digest",
            )
            result = super()._inference_generate(p)
            if not isinstance(result, dict):
                raise PipelineFault("INFERENCE_RESULT_NOT_OBJECT")
            if result.get("ok") is not True:
                return result
            out = dict(result)
            out["inference_packet_digest"] = packet_digest
            out["cognitive_fabric_admission_receipt_digest"] = admission_digest
            return out
        except Exception as exc:
            self._active_secrets = []
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_cognitive_fabric_finalize(self, p: dict[str, Any]) -> dict[str, Any]:
        """Fail closed after commit until exact final UCF-v1 source/runtime identity is bound.

        The canonical Clay caller treats this result as nonfatal evidence debt once the
        MiniUnifiedDB commit already succeeded.  This method intentionally performs no DB
        write, inference call, effect, retry, or fabricated final receipt.
        """
        try:
            data = p["data"]
            admitted = data["admitted"]
            generated = data["generated"]
            gated = data["gated"]
            committed = data["committed"]
            if not all(isinstance(item, Mapping) for item in (admitted, generated, gated, committed)):
                raise PipelineFault("UCF_FINALIZATION_ANCESTRY_OBJECT_REQUIRED")
            if admitted.get("ok") is not True:
                raise PipelineFault("UCF_FINALIZATION_ADMISSION_NOT_OK")
            if generated.get("ok") is not True:
                raise PipelineFault("UCF_FINALIZATION_INFERENCE_NOT_OK")
            if gated.get("ok") is not True:
                raise PipelineFault("UCF_FINALIZATION_GATE_NOT_OK")
            if committed.get("ok") is not True:
                raise PipelineFault("UCF_FINALIZATION_COMMIT_NOT_OK")
            if generated.get("inference_packet_digest") != admitted.get("inference_packet_digest"):
                raise PipelineFault("UCF_FINALIZATION_PACKET_IDENTITY_DRIFT")
            if (
                generated.get("cognitive_fabric_admission_receipt_digest")
                != admitted.get("cognitive_fabric_receipt_digest")
            ):
                raise PipelineFault("UCF_FINALIZATION_ADMISSION_IDENTITY_DRIFT")
            return {
                "ok": False,
                "error_kind": "PipelineFault",
                "error": "UCF_FINAL_RECEIPT_SOURCE_RUNTIME_IDENTITY_UNBOUND",
                "committed_output_id": committed.get("output_id"),
                "committed_generation": committed.get("generation"),
                "retry_commit_forbidden": True,
            }
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}


def execute_source(
    source: str,
    entry: str,
    args: list[Any],
    runtime: ProfilePipelineRuntime | None = None,
):
    program = clay.parse(source)
    rt = runtime or ProfilePipelineRuntime()
    return clay.execute(program, entry, args, rt)


__all__ = [
    "VERSION",
    "PROFILE_SCHEMAS",
    "IMMUTABLE_GUARD",
    "PipelineFault",
    "ProfilePipelineRuntime",
    "execute_source",
]
