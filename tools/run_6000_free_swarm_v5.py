#!/usr/bin/env python3
"""Free Swarm v5 — two-stage exact-source patch synthesis before Evidence Forge.

v3 remains the exact FREE economic/provider authority. v5 changes only the worker
conversion path:

stage 1: proposal + target/test selection, no executable patch;
local:   bind targets to one exact source commit/tree/blob set;
stage 2: synthesize a patch against those exact bytes;
local:   ordinary ``git apply --check``; narrowly normalize bad hunk counts;
Forge:   only apply-clean candidates may retain ``ready_for_forge=true``.

This is a fail-closed conversion filter, not a truth/effect/execution authority.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import os
import time
from typing import Any

import free_swarm_patch_pipeline as patchpipe
import run_6000_free_swarm_v3 as gated

fabric = gated.fabric
base = fabric.base
_ORIGINAL_WORKER_PROMPT = base.worker_prompt
STAGE1_MAX_TOKENS = max(256, int(os.getenv("CLAY_SWARM_STAGE1_MAX_TOKENS", "900")))


def proposal_only_prompt(
    protocol: str,
    role: str,
    task: str,
    state_context: str,
    serial: int,
) -> str:
    return _ORIGINAL_WORKER_PROMPT(protocol, role, task, state_context, serial) + """

TWO_STAGE_PATCH_PIPELINE/v1 — STAGE 1 OVERRIDE
This call is TARGET/TEST SELECTION ONLY. The controller will rehydrate the exact
declared source paths and may issue a second source-bound patch-synthesis call.

For this stage:
- choose at most 3 concrete repository-relative target_files;
- choose concrete test_commands and a falsifier;
- set patch_unified_diff="" and ready_for_forge=false;
- do not invent diff hunks before exact target bytes are rebound;
- if concrete target paths/tests are not known, emit a design-only delta;
- preserve current EntityOS/HCU, FREE_ONLY, truth/effect and capability boundaries.
"""


def _sum_usage(*payloads: Any) -> dict[str, int]:
    totals: dict[str, int] = {}
    for payload in payloads:
        usage = base.usage_from(payload)
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[key] = totals.get(key, 0) + int(value)
    return totals


def _rate_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.startswith("x-ratelimit-") or key == "retry-after"
    }


async def _observe_provider_result(
    runtime: fabric.FastProviderRuntime,
    key: str,
    model: str,
    status: int,
    headers: dict[str, str],
) -> str | None:
    """Update the same provider runtime control state used by the v2/v3 fabric."""
    if 200 <= status < 300:
        await runtime.on_success()
        return None
    if status == 402:
        await runtime.disable_key(key)
        return "PAYMENT_REQUIRED_HARD_STOP_KEY"
    if status in (401, 403):
        await runtime.disable_key(key)
        return "AUTH_OR_ENTITLEMENT_BLOCKED_KEY"
    if status == 404:
        await runtime.disable_model(model)
        return "MODEL_OR_ENDPOINT_UNAVAILABLE"
    if status == 429:
        retry_after = base.parse_retry_after(headers, min(900.0, runtime.rate_backoff))
        await runtime.on_429(retry_after)
        return "RATE_LIMIT_PROVIDER_COOLDOWN"
    if 500 <= status < 600:
        await runtime.on_transient_error()
        return "PROVIDER_TRANSIENT_ERROR"
    runtime.errors += 1
    return "NONRETRYABLE_REQUEST_ERROR"


def _proposal_targets_strict(obj: dict[str, Any]) -> tuple[list[str], str | None]:
    raw = obj.get("target_files")
    if not isinstance(raw, list) or not raw or len(raw) > patchpipe.MAX_TARGET_FILES:
        return [], "TARGET_SELECTION_MISSING_OR_TOO_WIDE"
    if not all(isinstance(value, str) for value in raw):
        return [], "TARGET_SELECTION_NON_STRING"
    normalized = patchpipe.target_files(obj)
    if len(normalized) != len(raw):
        return [], "TARGET_SELECTION_UNSAFE_OR_DUPLICATE"
    return normalized, None


def _freeze_stage1_delta(obj: dict[str, Any]) -> dict[str, Any]:
    frozen = dict(obj)
    frozen["patch_unified_diff"] = ""
    frozen["ready_for_forge"] = False
    frozen["patch_pipeline_stage"] = "TARGET_SELECTION"
    return frozen


def _stable_stage2_delta(
    stage1: dict[str, Any],
    stage2: dict[str, Any],
    source_head: str,
    binding: dict[str, Any],
) -> dict[str, Any]:
    """Patch synthesis cannot silently rewrite the experiment definition."""
    out = dict(stage2)
    for key in (
        "delta_id",
        "hypothesis",
        "mechanism",
        "target_files",
        "test_commands",
        "negative_test_commands",
        "benchmark_command",
        "metric",
        "expected_direction",
        "baseline_needed",
        "falsifier",
        "risk",
    ):
        if key in stage1:
            out[key] = stage1[key]
    out["patch_source_head"] = source_head
    out["patch_source_tree"] = binding.get("source_tree")
    out["patch_source_binding_sha256"] = binding.get("source_binding_sha256")
    out["patch_source_blobs"] = {
        row["path"]: row.get("git_blob") for row in binding.get("files") or []
    }
    out["ready_for_forge"] = False
    return out


def _binding_metadata(binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(binding.get("ok")),
        "reason": binding.get("reason"),
        "source_head": binding.get("source_head"),
        "source_tree": binding.get("source_tree"),
        "source_binding_sha256": binding.get("source_binding_sha256"),
        "context_complete": binding.get("context_complete"),
        "execution_state": binding.get("execution_state"),
        "files": [
            {key: value for key, value in row.items() if key != "content"}
            for row in (binding.get("files") or [])
        ],
    }


def _finish_success(
    common: dict[str, Any],
    text: str,
    prompt: str,
    payloads: tuple[Any, ...],
    pipeline: dict[str, Any],
    headers: dict[str, str] | None,
    started: float,
) -> None:
    state = str(pipeline.get("state") or "UNKNOWN")
    common["http_status"] = 200
    common["text"] = text
    common["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    common["usage"] = _sum_usage(*payloads)
    common["rate"] = _rate_headers(headers or {})
    common["patch_pipeline_state"] = state
    common["pipeline"] = pipeline
    common["elapsed_s"] = round(time.time() - started, 3)
    common["conformance"] = {
        "protocol_injected": prompt.startswith(base.PROTOCOL_BEGIN),
        "german_summary_marker": "DEUTSCHE_ZUSAMMENFASSUNG" in text,
        "architecture_delta_marker": "ARCHITECTURE_DELTA_JSON=" in text,
        "research_questions_marker": "OPEN_RESEARCH_QUESTIONS_JSON=" in text,
    }


async def execute_call(
    logical_slot: int,
    runtime: fabric.FastProviderRuntime,
    key: str,
    model: str,
    protocol: str,
    sink: base.JsonlSink,
    args: Any,
    serial_counter: list[int],
    broker: fabric.WorkStealingBroker,
    stop_event: asyncio.Event,
    queue: asyncio.Queue[int],
) -> None:
    """Run one logical worker through proposal -> exact source -> patch preflight."""
    serial_counter[0] += 1
    serial = serial_counter[0]
    role, task = base.DEFAULT_ROLES[(serial - 1) % len(base.DEFAULT_ROLES)]
    broker.roles[role] += 1

    proposal_head = base.git_text("rev-parse", "HEAD")
    stage1_prompt = proposal_only_prompt(
        protocol, role, task, base.build_state_context(args.context_chars), serial
    )
    started = time.time()
    common: dict[str, Any] = {
        "schema": "CLAY_FREE_GO_SWARM_WORKER/v3",
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": runtime.spec.name,
        "model": model,
        "key_fp": base.key_fingerprint(key),
        "role": role,
        "worker_serial": serial,
        "logical_worker_slot": logical_slot,
        "scheduler": "GLOBAL_WORK_STEALING_V2",
        "proposal_head_at_prompt": proposal_head,
        "repo_head_at_prompt": proposal_head,
        "patch_pipeline": "TWO_STAGE_EXACT_SOURCE/v1",
    }

    try:
        runtime.requests += 1
        try:
            status1, headers1, payload1 = await asyncio.to_thread(
                base.request_chat,
                runtime.spec,
                key,
                model,
                stage1_prompt,
                min(int(args.max_tokens), STAGE1_MAX_TOKENS),
                args.timeout,
            )
        except Exception as exc:
            await runtime.on_transient_error()
            common.update({
                "http_status": "NETWORK_EXCEPTION",
                "classification": "STAGE1_NETWORK_EXCEPTION",
                "error": f"{exc.__class__.__name__}:{str(exc)[:300]}",
                "elapsed_s": round(time.time() - started, 3),
            })
            await sink.append(common)
            return

        class1 = await _observe_provider_result(runtime, key, model, status1, headers1)
        if not (200 <= status1 < 300):
            common.update({
                "http_status": status1,
                "classification": "STAGE1_" + str(class1),
                "error_body": payload1,
                "elapsed_s": round(time.time() - started, 3),
                "usage": _sum_usage(payload1),
                "rate": _rate_headers(headers1),
            })
            await sink.append(common)
            return

        stage1_text = base.extract_text(payload1)
        stage1_obj = patchpipe.architecture_delta(stage1_text)
        if not isinstance(stage1_obj, dict):
            _finish_success(
                common,
                stage1_text,
                stage1_prompt,
                (payload1,),
                {"state": "STAGE1_NO_MACHINE_DELTA"},
                headers1,
                started,
            )
            await sink.append(common)
            broker.completed += 1
            return

        stage1_frozen = _freeze_stage1_delta(stage1_obj)
        stage1_safe_text = patchpipe.canonicalize_architecture_delta(stage1_text, stage1_frozen)
        targets, target_error = _proposal_targets_strict(stage1_obj)
        if target_error or not patchpipe.proposal_complete(stage1_obj):
            _finish_success(
                common,
                stage1_safe_text,
                stage1_prompt,
                (payload1,),
                {
                    "state": "STAGE1_PROPOSAL_INCOMPLETE",
                    "reason": target_error or "TEST_OR_FALSIFIER_MISSING",
                },
                headers1,
                started,
            )
            await sink.append(common)
            broker.completed += 1
            return

        # Stage 1 selects paths only. Re-enter HEAD now and bind exact source bytes
        # for stage 2; this converts ordinary main movement into rehydration instead
        # of a semantic patch failure.
        patch_source_head = base.git_text("rev-parse", "HEAD")
        common["repo_head_at_prompt"] = patch_source_head
        binding = patchpipe.rehydrate_targets(
            fabric.ROOT,
            patch_source_head,
            targets,
            per_file_chars=int(os.getenv(
                "CLAY_SWARM_PATCH_CONTEXT_PER_FILE_CHARS",
                str(patchpipe.DEFAULT_PER_FILE_CHARS),
            )),
            total_chars=int(os.getenv(
                "CLAY_SWARM_PATCH_CONTEXT_TOTAL_CHARS",
                str(patchpipe.DEFAULT_TOTAL_CHARS),
            )),
        )
        if not binding.get("ok"):
            _finish_success(
                common,
                stage1_safe_text,
                stage1_prompt,
                (payload1,),
                {
                    "state": "SOURCE_REHYDRATION_BLOCKED",
                    "proposal_head": proposal_head,
                    "patch_source_head": patch_source_head,
                    "source_rehydration": _binding_metadata(binding),
                },
                headers1,
                started,
            )
            await sink.append(common)
            broker.completed += 1
            return

        stage2_prompt_text = patchpipe.stage2_prompt(protocol, stage1_frozen, binding)
        runtime.requests += 1
        try:
            status2, headers2, payload2 = await asyncio.to_thread(
                base.request_chat,
                runtime.spec,
                key,
                model,
                stage2_prompt_text,
                int(args.max_tokens),
                args.timeout,
            )
        except Exception as exc:
            await runtime.on_transient_error()
            _finish_success(
                common,
                stage1_safe_text,
                stage1_prompt,
                (payload1,),
                {
                    "state": "STAGE2_NETWORK_EXCEPTION",
                    "error": f"{exc.__class__.__name__}:{str(exc)[:300]}",
                    "source_rehydration": _binding_metadata(binding),
                },
                headers1,
                started,
            )
            await sink.append(common)
            broker.completed += 1
            return

        class2 = await _observe_provider_result(runtime, key, model, status2, headers2)
        if not (200 <= status2 < 300):
            _finish_success(
                common,
                stage1_safe_text,
                stage1_prompt,
                (payload1, payload2),
                {
                    "state": "STAGE2_PROVIDER_BLOCKED",
                    "stage2_http_status": status2,
                    "stage2_classification": class2,
                    "source_rehydration": _binding_metadata(binding),
                },
                headers2,
                started,
            )
            await sink.append(common)
            broker.completed += 1
            return

        stage2_text = base.extract_text(payload2)
        stage2_obj = patchpipe.architecture_delta(stage2_text)
        if not isinstance(stage2_obj, dict):
            _finish_success(
                common,
                stage1_safe_text,
                stage1_prompt,
                (payload1, payload2),
                {
                    "state": "STAGE2_NO_MACHINE_DELTA",
                    "source_rehydration": _binding_metadata(binding),
                    "stage2_text_sha256": hashlib.sha256(stage2_text.encode("utf-8")).hexdigest(),
                },
                headers2,
                started,
            )
            await sink.append(common)
            broker.completed += 1
            return

        final_obj = _stable_stage2_delta(stage1_obj, stage2_obj, patch_source_head, binding)
        patch = str(stage2_obj.get("patch_unified_diff") or "")
        preflight = patchpipe.normalize_patch_against_source(
            fabric.ROOT, patch_source_head, patch, targets
        )
        final_obj["patch_unified_diff"] = str(preflight.get("patch") or "")
        final_obj["ready_for_forge"] = bool(preflight.get("ok"))
        final_obj["patch_pipeline_stage"] = (
            "APPLY_CHECK_PASS" if preflight.get("ok") else "APPLY_CHECK_BLOCKED"
        )
        final_obj["patch_repair_mode"] = str(preflight.get("repair_mode") or "NONE")

        # Preserve stage-1 questions/rationale; only replace its machine delta with
        # the source-bound stage-2 result. This keeps Distillery input continuity.
        final_text = patchpipe.canonicalize_architecture_delta(stage1_text, final_obj)
        preflight_meta = {k: v for k, v in preflight.items() if k != "patch"}
        _finish_success(
            common,
            final_text,
            stage1_prompt,
            (payload1, payload2),
            {
                "state": (
                    "APPLY_CLEAN_READY_FOR_FORGE"
                    if preflight.get("ok")
                    else "PATCH_PREFLIGHT_REJECTED"
                ),
                "proposal_head": proposal_head,
                "patch_source_head": patch_source_head,
                "source_rehydrated_after_stage1": proposal_head != patch_source_head,
                "head_after_stage2": base.git_text("rev-parse", "HEAD"),
                "stage1_text_sha256": hashlib.sha256(stage1_text.encode("utf-8")).hexdigest(),
                "stage2_text_sha256": hashlib.sha256(stage2_text.encode("utf-8")).hexdigest(),
                "source_rehydration": _binding_metadata(binding),
                "patch_preflight": preflight_meta,
            },
            headers2,
            started,
        )
        await sink.append(common)
        broker.completed += 1
    finally:
        await runtime.release()
        if not stop_event.is_set():
            await queue.put(logical_slot)


# run_6000_free_swarm.dispatch_loop resolves its module-global execute_call at
# runtime, so this one assignment installs the conversion path without duplicating
# the scheduler/provider/economic authorities.
fabric.execute_call = execute_call

run = fabric.run
parse_args = fabric.parse_args

if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
