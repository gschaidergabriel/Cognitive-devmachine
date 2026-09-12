#!/usr/bin/env python3
"""Continuous FREE_ONLY research/build worker lane for OMEGA.

This is the successor to the historical high-volume swarm, not a reactivation of it.
It reuses the typed FREE provider admission and rate-limit logic in run_free_go_swarm,
but wraps it in bounded epochs and converts successful model outputs into immutable,
noncanonical OMEGA candidate envelopes.

Hard laws:
- FREE_ONLY admission must pass on every epoch.
- Together / paid / unknown-cost fallback is never attempted.
- HTTP 402 remains a hard-stop for that credential inside the delegated runner.
- HTTP 429 remains provider-wide cooldown; no key rotation to evade provider limits.
- Worker text is MODEL_GENERATED candidate material, never observation/truth/effect authority.
- This process never commits, merges, deploys, mutates OMEGA authority, or activates adapters.
- Promotion requires a separate independent executable/evidence path.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any

# Script directory is on sys.path when executed directly.
import free_provider_admission as admission
import run_free_go_swarm as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = Path("/artifacts/clay-omega-free-workers")

OMEGA_FOCUS = r"""
CURRENT OWNER FOCUS — OMEGA CONTINUOUS BUILD/RESEARCH LANE

Work as a temporary, non-authoritative research/build organ for the current OMEGA / Project-Frankenstein integration frontier.
Current hard target:
- preserve all valuable existing organs rather than replacing them;
- OMEGA-Sigma is integrative tissue around exactly one GRID10 and UnifiedDB;
- Cortex is native OMEGA integration tissue;
- Retina remains independently maintainable but strongly bidirectionally coupled to Cortex;
- SOMA/local-model adaptation, Context Gate/TCF, Hypothesis Engine/HMF, Genesis, Neural Immune/ASRS, RELF/Quantum Reflector, World Model, Titan/LCME memory, Idle Thought and affect/personality remain explicit organs/donors;
- no second productive GRID, truth DB, turn loop, state-sync system or effect authority;
- continuous cognition should be event/resource driven rather than timer theatre;
- model output, recurrence, coherence, routing score and replay are never truth by themselves;
- preserve UNKNOWN and negative evidence;
- seek cheap executable falsifiers before broad claims;
- prefer patches/tests/contracts/benchmarks that can be independently verified;
- do not claim consciousness, AGI, deployment, target-host success or benchmark wins without exact evidence.

For every output, attack one current assumption and produce the smallest high-information next delta. If proposing source changes, name exact files/functions/contracts and the tests that would falsify them. Keep competing hypotheses explicit.
""".strip()

_ORIGINAL_PROMPT = base.worker_prompt


def omega_worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    return _ORIGINAL_PROMPT(protocol, role, task, state_context, serial) + "\n\n" + OMEGA_FOCUS + "\n"


base.worker_prompt = omega_worker_prompt


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_admission() -> dict[str, Any]:
    payload = admission.load_provider_admission()
    admitted = admission.admitted_provider_names()
    if not admitted:
        raise admission.ProviderAdmissionError("NO_CANONICALLY_ADMITTED_FREE_PROVIDER")
    return {
        "authority_epoch": payload.get("authority_epoch"),
        "admitted_free_providers": list(admitted),
        "mode": payload.get("mode"),
    }


def distill_epoch(epoch_dir: Path, candidate_root: Path) -> dict[str, Any]:
    source = epoch_dir / "workers.jsonl"
    accepted = quarantined = duplicates = 0
    seen: set[str] = set()
    if not source.exists():
        return {"accepted": 0, "quarantined": 0, "duplicates": 0, "source_exists": False}

    candidate_root.mkdir(parents=True, exist_ok=True)
    for line_no, raw in enumerate(source.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            quarantined += 1
            continue
        if not isinstance(row, dict) or not (isinstance(row.get("http_status"), int) and 200 <= row["http_status"] < 300):
            continue
        text = str(row.get("text") or "").strip()
        text_sha = str(row.get("text_sha256") or sha256_text(text))
        if not text or len(text) < 200:
            quarantined += 1
            continue
        conf = row.get("conformance") if isinstance(row.get("conformance"), dict) else {}
        conformant = (
            conf.get("protocol_injected") is True
            and conf.get("german_summary_marker") is True
            and conf.get("grf_marker") is True
        )
        if not conformant:
            quarantined += 1
            continue
        if text_sha in seen:
            duplicates += 1
            continue
        seen.add(text_sha)

        candidate = {
            "schema": "OMEGA_FREE_WORKER_CANDIDATE/v1",
            "candidate_id": "free_" + text_sha[:32],
            "created_at": utc_now(),
            "evidence_class": "MODEL_GENERATED",
            "authority": "CANDIDATE_ONLY",
            "effect_authority": False,
            "promotion_authority": False,
            "canonical_credit_minted": 0,
            "training_credit": 0,
            "provider": row.get("provider"),
            "model": row.get("model"),
            "role": row.get("role"),
            "worker_id": row.get("worker_id"),
            "worker_serial": row.get("worker_serial"),
            "repo_head_at_prompt": row.get("repo_head_at_prompt"),
            "source_epoch_dir": str(epoch_dir),
            "source_line": line_no,
            "text_sha256": text_sha,
            "usage": row.get("usage") if isinstance(row.get("usage"), dict) else {},
            "conformance": conf,
            "content": text,
            "required_reentry": [
                "independent executable discriminator or canonical evidence review",
                "preserve counterhypothesis and negative evidence",
                "no direct effect dispatch",
            ],
        }
        target = candidate_root / f"{candidate['candidate_id']}.json"
        if target.exists():
            duplicates += 1
            continue
        atomic_json(target, candidate)
        accepted += 1
    return {
        "accepted": accepted,
        "quarantined": quarantined,
        "duplicates": duplicates,
        "source_exists": True,
    }


async def run_epoch(args: argparse.Namespace, epoch_dir: Path) -> int:
    delegated = argparse.Namespace(
        hours=max(1.0 / 3600.0, args.epoch_minutes / 60.0),
        max_tokens=args.max_tokens,
        context_chars=args.context_chars,
        timeout=args.request_timeout,
        drain_seconds=args.drain_seconds,
        output_dir=str(epoch_dir),
    )
    return await base.run(delegated)


async def main_async(args: argparse.Namespace) -> int:
    output_root = Path(args.output_root)
    candidate_root = output_root / "candidates"
    epochs_root = output_root / "epochs"
    status_path = output_root / "CONTINUOUS_STATUS.json"
    output_root.mkdir(parents=True, exist_ok=True)
    epochs_root.mkdir(parents=True, exist_ok=True)
    candidate_root.mkdir(parents=True, exist_ok=True)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    seq = 0
    consecutive_failures = 0
    total_candidates = 0
    focus_sha = sha256_text(OMEGA_FOCUS)

    while not stop.is_set():
        seq += 1
        epoch_id = dt.datetime.now(dt.timezone.utc).strftime("omega-free-%Y%m%dT%H%M%S.%fZ")
        epoch_dir = epochs_root / epoch_id
        epoch_dir.mkdir(parents=True, exist_ok=False)
        (epoch_dir / "OMEGA_FOCUS.txt").write_text(OMEGA_FOCUS + "\n", encoding="utf-8")

        try:
            gate = validate_admission()
        except Exception as exc:
            consecutive_failures += 1
            atomic_json(status_path, {
                "schema": "OMEGA_CONTINUOUS_FREE_WORKERS_STATUS/v1",
                "state": "BLOCKED_ADMISSION",
                "updated_at": utc_now(),
                "epoch_sequence": seq,
                "focus_sha256": focus_sha,
                "error": f"{type(exc).__name__}:{exc}",
                "consecutive_failures": consecutive_failures,
                "canonical_credit_minted": 0,
                "effect_authority": False,
            })
            if args.once:
                return 5
            try:
                await asyncio.wait_for(stop.wait(), timeout=min(args.max_backoff_seconds, 30.0 * (2 ** min(consecutive_failures, 5))))
            except asyncio.TimeoutError:
                continue
            break

        atomic_json(status_path, {
            "schema": "OMEGA_CONTINUOUS_FREE_WORKERS_STATUS/v1",
            "state": "RUNNING_EPOCH",
            "updated_at": utc_now(),
            "epoch_id": epoch_id,
            "epoch_sequence": seq,
            "focus_sha256": focus_sha,
            "admission": gate,
            "total_candidates": total_candidates,
            "canonical_credit_minted": 0,
            "effect_authority": False,
        })

        try:
            rc = await run_epoch(args, epoch_dir)
        except Exception as exc:
            rc = 99
            atomic_json(epoch_dir / "wrapper_exception.json", {
                "at": utc_now(),
                "error": f"{type(exc).__name__}:{exc}",
            })

        distilled = distill_epoch(epoch_dir, candidate_root)
        total_candidates += int(distilled["accepted"])
        if rc == 0:
            consecutive_failures = 0
        else:
            consecutive_failures += 1

        atomic_json(status_path, {
            "schema": "OMEGA_CONTINUOUS_FREE_WORKERS_STATUS/v1",
            "state": "EPOCH_COMPLETE" if rc == 0 else "EPOCH_FAILED",
            "updated_at": utc_now(),
            "epoch_id": epoch_id,
            "epoch_sequence": seq,
            "focus_sha256": focus_sha,
            "admission": gate,
            "epoch_returncode": rc,
            "distilled": distilled,
            "total_candidates": total_candidates,
            "consecutive_failures": consecutive_failures,
            "canonical_credit_minted": 0,
            "effect_authority": False,
        })

        if args.once:
            return rc
        delay = args.inter_epoch_seconds if rc == 0 else min(
            args.max_backoff_seconds,
            max(args.inter_epoch_seconds, 10.0 * (2 ** min(consecutive_failures, 6))),
        )
        try:
            await asyncio.wait_for(stop.wait(), timeout=delay)
        except asyncio.TimeoutError:
            pass

    atomic_json(status_path, {
        "schema": "OMEGA_CONTINUOUS_FREE_WORKERS_STATUS/v1",
        "state": "STOPPED",
        "updated_at": utc_now(),
        "epoch_sequence": seq,
        "focus_sha256": focus_sha,
        "total_candidates": total_candidates,
        "canonical_credit_minted": 0,
        "effect_authority": False,
    })
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run bounded continuous FREE_ONLY OMEGA research/build workers")
    p.add_argument("--epoch-minutes", type=float, default=30.0)
    p.add_argument("--max-tokens", type=int, default=1800)
    p.add_argument("--context-chars", type=int, default=18000)
    p.add_argument("--request-timeout", type=float, default=180.0)
    p.add_argument("--drain-seconds", type=float, default=240.0)
    p.add_argument("--inter-epoch-seconds", type=float, default=5.0)
    p.add_argument("--max-backoff-seconds", type=float, default=900.0)
    p.add_argument("--output-root", default=str(DEFAULT_ROOT))
    p.add_argument("--once", action="store_true")
    return p.parse_args()


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
