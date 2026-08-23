#!/usr/bin/env python3
"""Canonical Mini Entity reference runtime with fail-closed UCF admission.

The adjudicated generic DB/profile/inference runtime is preserved byte-for-byte in
`clay_profile_pipeline_runtime_core.py`.  This file remains the single public runtime
entry point and adds only the canonical pre-inference Cognitive Fabric boundary.

The boundary is deliberately two-stage:
- before inference: deterministic candidate-only admission ticket + ephemeral one-shot fence;
- after inference: the existing UCF runtime/cycle receipt remains separate evidence.

The ephemeral fence is not durable memory or truth. Restart destroys it; MiniUnifiedDB
remains the sole durable generation/profile/state authority.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

import claycode_structured_backend as clay
import clay_profile_pipeline_runtime_core as _core
import mini_entity_cognitive_fabric_admission_v1 as _admission

VERSION = "clay-profile-pipeline-runtime/0.7.0-ucf-admission"
PROFILE_SCHEMAS = _core.PROFILE_SCHEMAS
IMMUTABLE_GUARD = _core.IMMUTABLE_GUARD
PipelineFault = _core.PipelineFault


class ProfilePipelineRuntime(_core.ProfilePipelineRuntime):
    """One canonical runtime path: retained core + one pre-inference UCF fence."""

    def __init__(
        self,
        *,
        root: str | Path = ".",
        allow_network: bool = False,
        provider_override: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        local_exec_runner: str | Path | None = None,
        cognitive_fabric_admitter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        super().__init__(
            root=root,
            allow_network=allow_network,
            provider_override=provider_override,
            local_exec_runner=local_exec_runner,
        )
        self.cognitive_fabric_admitter = cognitive_fabric_admitter
        self._active_cognitive_admissions: dict[str, dict[str, Any]] = {}
        # Keep this literal for the executable AST drift guard.  The set is the complete
        # effect surface; there is no legacy profile/provider or second UCF effect path.
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
        }

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

    # Explicit wrapper methods keep the AST drift guard bound to executable methods on
    # the canonical public class rather than accepting inherited/comment-only names.
    def _pipeline_profile_read(self, p: dict[str, Any]) -> dict[str, Any]:
        return super()._pipeline_profile_read(p)

    def _live_authority_snapshot(self, entity_db: str) -> dict[str, Any]:
        with self._read_only_db(entity_db) as db:
            row = db.execute(
                """SELECT e.generation,e.active_profile,p.profile_json,p.profile_sha256
                   FROM entity_state e
                   JOIN profiles p ON p.profile_id=e.active_profile
                   WHERE e.id=1"""
            ).fetchone()
        if row is None:
            raise PipelineFault("ENTITY_PROFILE_AUTHORITY_MISSING")
        raw = str(row["profile_json"])
        actual_hash = _core._sha256_text(raw)
        stored_hash = str(row["profile_sha256"])
        if actual_hash != stored_hash:
            raise PipelineFault("PROFILE_HASH_MISMATCH")
        return {
            "generation": int(row["generation"]),
            "profile_id": str(row["active_profile"]),
            "profile_hash": actual_hash,
        }

    @staticmethod
    def _profile_snapshot(profile: Mapping[str, Any]) -> dict[str, str]:
        snapshot = profile.get("_runtime_profile_snapshot")
        if not isinstance(snapshot, Mapping):
            raise PipelineFault("PROFILE_SNAPSHOT_MISSING")
        profile_id = snapshot.get("profile_id")
        profile_hash = snapshot.get("profile_hash")
        if not isinstance(profile_id, str) or not profile_id:
            raise PipelineFault("PROFILE_SNAPSHOT_MISSING")
        if not isinstance(profile_hash, str):
            raise PipelineFault("PROFILE_SNAPSHOT_MISSING")
        return {"profile_id": profile_id, "profile_hash": profile_hash}

    def _pipeline_cognitive_fabric_admit(self, p: dict[str, Any]) -> dict[str, Any]:
        """Create one pre-inference ticket and register a restart-volatile one-shot fence."""
        try:
            entity_db = str(p["entity_db"])
            profile = p["profile"]
            previous = p["previous"]
            data = p["data"]
            if not isinstance(profile, Mapping) or not isinstance(previous, Mapping) or not isinstance(data, Mapping):
                raise PipelineFault("COGNITIVE_FABRIC_INPUT_OBJECT_REQUIRED")
            compiled = data.get("compiled")
            prompt = data.get("prompt")
            if not isinstance(compiled, Mapping) or not isinstance(prompt, Mapping):
                raise PipelineFault("COGNITIVE_FABRIC_INPUT_MISSING")
            generation = previous.get("generation")
            if isinstance(generation, bool) or not isinstance(generation, int):
                raise PipelineFault("MISSING_GENERATION")

            snapshot = self._profile_snapshot(profile)
            live = self._live_authority_snapshot(entity_db)
            if live["generation"] != generation:
                raise PipelineFault("STALE_GENERATION")
            if live["profile_id"] != snapshot["profile_id"] or live["profile_hash"] != snapshot["profile_hash"]:
                raise PipelineFault("PROFILE_SNAPSHOT_STALE")

            # Rebuild the prompt from the exact profile/previous/compiled inputs.  A caller
            # cannot smuggle a different prompt into admission while retaining old hashes.
            expected_prompt = super()._pipeline_build_prompt(
                {"profile": profile, "previous": previous, "data": compiled}
            )
            if not expected_prompt.get("ok"):
                raise PipelineFault("PROMPT_REBUILD_FAILED")
            if prompt.get("system") != expected_prompt.get("system") or prompt.get("user") != expected_prompt.get("user"):
                raise PipelineFault("PROMPT_COMPILED_IDENTITY_MISMATCH")

            if self.cognitive_fabric_admitter is None:
                raise PipelineFault("COGNITIVE_FABRIC_ADMITTER_UNAVAILABLE")
            request = {
                "schema": _admission.REQUEST_SCHEMA,
                "generation": generation,
                "canonical_state_hash": compiled.get("canonical_state_hash"),
                "packet_hash": compiled.get("packet_hash"),
                "profile_id": snapshot["profile_id"],
                "profile_hash": snapshot["profile_hash"],
                # The exact immutable-guarded user context is the task identity for this
                # pipeline turn. ZERO_WORKSPACE_CAPSULE must bind to these bytes.
                "task_text": str(prompt.get("user", "")),
                "system": str(prompt.get("system", "")),
                "user": str(prompt.get("user", "")),
                "configured_inference": dict(profile.get("inference", {})),
            }
            normalized_request = _admission.validate_request(request)
            proposal = self.cognitive_fabric_admitter(dict(request))
            envelope = _admission.compile_admission(normalized_request, proposal)
            envelope = _admission.validate_envelope(envelope)
            self._forbid_embedded_secrets(envelope["inference"])

            if envelope["generation"] != generation:
                raise PipelineFault("STALE_GENERATION")
            if envelope["canonical_state_hash"] != compiled.get("canonical_state_hash"):
                raise PipelineFault("BAD_CANONICAL_STATE_HASH")
            if envelope["packet_hash"] != compiled.get("packet_hash"):
                raise PipelineFault("BAD_PACKET_HASH")

            receipt_digest = str(envelope["cognitive_fabric_receipt_digest"])
            if receipt_digest in self._active_cognitive_admissions:
                raise PipelineFault("COGNITIVE_FABRIC_ADMISSION_REPLAY")
            self._active_cognitive_admissions[receipt_digest] = {
                "phase": "ADMITTED",
                "entity_db": entity_db,
                "generation": generation,
                "profile_id": snapshot["profile_id"],
                "profile_hash": snapshot["profile_hash"],
                "canonical_state_hash": envelope["canonical_state_hash"],
                "packet_hash": envelope["packet_hash"],
                "inference_packet_digest": envelope["inference_packet_digest"],
                "inference_digest": _admission.sha256_obj(envelope["inference"]),
                "system_digest": _admission.sha256_text(envelope["system"]),
                "user_digest": _admission.sha256_text(envelope["user"]),
            }
            return envelope
        except Exception as exc:
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _admission_for_inference(self, p: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        receipt_digest = p.get("cognitive_fabric_receipt_digest")
        packet_digest = p.get("inference_packet_digest")
        if not isinstance(receipt_digest, str) or not isinstance(packet_digest, str):
            raise PipelineFault("COGNITIVE_FABRIC_ADMISSION_REQUIRED")
        record = self._active_cognitive_admissions.get(receipt_digest)
        if record is None:
            raise PipelineFault("COGNITIVE_FABRIC_ADMISSION_UNKNOWN_OR_RESTARTED")
        if record.get("phase") != "ADMITTED":
            raise PipelineFault("COGNITIVE_FABRIC_ADMISSION_ALREADY_CONSUMED")
        if packet_digest != record.get("inference_packet_digest"):
            raise PipelineFault("INFERENCE_PACKET_DIGEST_BINDING_MISMATCH")
        if _admission.sha256_obj(p.get("inference")) != record.get("inference_digest"):
            raise PipelineFault("ADMITTED_INFERENCE_DIGEST_MISMATCH")
        if _admission.sha256_text(str(p.get("system", ""))) != record.get("system_digest"):
            raise PipelineFault("ADMITTED_SYSTEM_DIGEST_MISMATCH")
        if _admission.sha256_text(str(p.get("user", ""))) != record.get("user_digest"):
            raise PipelineFault("ADMITTED_USER_DIGEST_MISMATCH")
        live = self._live_authority_snapshot(str(record["entity_db"]))
        if live["generation"] != record["generation"]:
            raise PipelineFault("STALE_GENERATION")
        if live["profile_id"] != record["profile_id"] or live["profile_hash"] != record["profile_hash"]:
            raise PipelineFault("PROFILE_SNAPSHOT_STALE")
        record["phase"] = "INFERENCE_STARTED"
        return receipt_digest, record

    def _inference_generate(self, p: dict[str, Any]) -> dict[str, Any]:
        receipt_digest: str | None = None
        try:
            receipt_digest, record = self._admission_for_inference(p)
            result = super()._inference_generate(p)
            if not result.get("ok"):
                self._active_cognitive_admissions.pop(receipt_digest, None)
                return result
            record["phase"] = "INFERENCE_DONE"
            result = dict(result)
            result["inference_packet_digest"] = record["inference_packet_digest"]
            result["cognitive_fabric_receipt_digest"] = receipt_digest
            return result
        except Exception as exc:
            if receipt_digest is not None:
                self._active_cognitive_admissions.pop(receipt_digest, None)
            self._active_secrets = []
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _admission_for_downstream(
        self,
        data: Mapping[str, Any],
        *,
        expected_phase: str,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        admitted = data.get("cognitive_fabric")
        if not isinstance(admitted, Mapping):
            raise PipelineFault("COGNITIVE_FABRIC_ADMISSION_REQUIRED")
        envelope = _admission.validate_envelope(admitted)
        receipt_digest = str(envelope["cognitive_fabric_receipt_digest"])
        record = self._active_cognitive_admissions.get(receipt_digest)
        if record is None or record.get("phase") != expected_phase:
            raise PipelineFault("COGNITIVE_FABRIC_PHASE_MISMATCH")
        compiled = data.get("compiled")
        if not isinstance(compiled, Mapping):
            raise PipelineFault("COMPILED_CONTEXT_REQUIRED")
        if compiled.get("canonical_state_hash") != record.get("canonical_state_hash"):
            raise PipelineFault("ADMISSION_CANONICAL_HASH_BINDING_MISMATCH")
        if compiled.get("packet_hash") != record.get("packet_hash"):
            raise PipelineFault("ADMISSION_SOURCE_PACKET_HASH_BINDING_MISMATCH")
        return receipt_digest, record, envelope

    def _pipeline_gate(self, p: dict[str, Any]) -> dict[str, Any]:
        receipt_digest: str | None = None
        try:
            data = p["data"]
            receipt_digest, record, _ = self._admission_for_downstream(
                data, expected_phase="INFERENCE_DONE"
            )
            generated = data.get("generated")
            if not isinstance(generated, Mapping):
                raise PipelineFault("GENERATED_CONTEXT_REQUIRED")
            if generated.get("cognitive_fabric_receipt_digest") != receipt_digest:
                raise PipelineFault("GENERATED_FABRIC_RECEIPT_BINDING_MISMATCH")
            if generated.get("inference_packet_digest") != record.get("inference_packet_digest"):
                raise PipelineFault("GENERATED_PACKET_BINDING_MISMATCH")
            result = super()._pipeline_gate(p)
            if not result.get("ok"):
                self._active_cognitive_admissions.pop(receipt_digest, None)
                return result
            record["phase"] = "GATED"
            result = dict(result)
            result["cognitive_fabric_receipt_digest"] = receipt_digest
            result["inference_packet_digest"] = record["inference_packet_digest"]
            return result
        except Exception as exc:
            if receipt_digest is not None:
                self._active_cognitive_admissions.pop(receipt_digest, None)
            return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}

    def _pipeline_commit(self, p: dict[str, Any]) -> dict[str, Any]:
        receipt_digest: str | None = None
        try:
            data = p["data"]
            receipt_digest, record, _ = self._admission_for_downstream(
                data, expected_phase="GATED"
            )
            gated = data.get("gated")
            if not isinstance(gated, Mapping):
                raise PipelineFault("GATED_CONTEXT_REQUIRED")
            if gated.get("cognitive_fabric_receipt_digest") != receipt_digest:
                raise PipelineFault("GATED_FABRIC_RECEIPT_BINDING_MISMATCH")
            if gated.get("inference_packet_digest") != record.get("inference_packet_digest"):
                raise PipelineFault("GATED_PACKET_BINDING_MISMATCH")
            live = self._live_authority_snapshot(str(record["entity_db"]))
            if live["generation"] != record["generation"]:
                raise PipelineFault("STALE_GENERATION")
            result = super()._pipeline_commit(p)
            # Whether commit succeeds or fails, the pre-inference ticket is one-shot.
            self._active_cognitive_admissions.pop(receipt_digest, None)
            if result.get("ok"):
                result = dict(result)
                result["cognitive_fabric_receipt_digest"] = receipt_digest
                result["inference_packet_digest"] = record["inference_packet_digest"]
            return result
        except Exception as exc:
            if receipt_digest is not None:
                self._active_cognitive_admissions.pop(receipt_digest, None)
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
