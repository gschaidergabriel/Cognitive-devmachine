"""Frankenstein Bauleiter loop with canonical provider-boundary gating.

This is the existing package-driven 72h build orchestrator, but external model
and Aider surfaces are now subordinate to the current EntityOS/HCU provider
admission control plane.  Under canonical HARD_OFF it performs zero provider
calls, zero provider-secret lookups, and zero Aider dispatches.  Frank's own
Harness is not modified.

The orchestration remains package-driven: one self-contained package at a time
from frankenstein_packages_v1.py, with Fabric-backed state and persistent
continuation summaries.  Together is never invoked here; a training marker is
only a stop condition and never execution authority.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from free_provider_admission import admitted_provider_names, provider_is_admitted_free  # noqa: E402
from grid10_fabric import Fabric, FabricError, result_packet  # noqa: E402
import frankenstein_packages_v1 as packages  # noqa: E402

BUILD_SCOPE = "frankenstein:build_state"
PRIMARY_TIER = "nvidia"
BAULEITER_NODE_ID = "frankenstein-bauleiter"
HARNESS_PATH = os.path.expanduser("~/.claude/star/harness_aider.py")
# fallback-start may route across these known free-pool tiers.  Because the
# caller cannot constrain the downstream Harness to a single route without
# modifying Frank's Harness, the external caller is admitted only when all
# of the routes it may select are currently admitted.  Partial admission is
# therefore fail-closed rather than silently widening capability.
HARNESS_PROVIDER_SET = frozenset({"nvidia", "groq", "mistral"})


class TierUnavailable(RuntimeError):
    pass


def _load_provider_clients_after_admission(tier_label: str):
    """Import provider caller modules only after canonical admission.

    This ordering is intentional: ~/last-resort/llm.py may inspect key
    material while importing or enumerating tiers, so it is downstream of
    the canonical admission test rather than a prerequisite for that test.
    """
    if not provider_is_admitted_free(tier_label):
        raise TierUnavailable(f"{tier_label}: CANONICAL_PROVIDER_HARD_OFF_OR_UNADMITTED")
    # Only now expose ~/last-resort to Python and import the provider helper.
    last_resort = os.path.expanduser("~/last-resort")
    if last_resort not in sys.path:
        sys.path.insert(0, last_resort)
    pool_llm = importlib.import_module("llm")
    requests = importlib.import_module("requests")
    return pool_llm, requests


def call_specific_tier(tier_label: str, messages: list[dict], *, max_tokens: int = 2000,
                        temperature: float = 0.3, timeout: float | None = None) -> str:
    """Call one admitted tier; fail closed before secrets/import/network."""
    pool_llm, requests = _load_provider_clients_after_admission(tier_label)
    for label, url, model, api_keys in pool_llm._tiers():
        if label != tier_label:
            continue
        last_err = None
        for idx, key in enumerate(api_keys):
            try:
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False,
                    },
                    timeout=timeout or pool_llm.TIMEOUT,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    last_err = f"key#{idx + 1}: HTTP {response.status_code}"
                    continue
                if response.status_code != 200:
                    last_err = f"key#{idx + 1}: HTTP {response.status_code} {response.text[:200]}"
                    continue
                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    last_err = f"key#{idx + 1}: no choices in response"
                    continue
                content = (choices[0].get("message") or {}).get("content")
                if content:
                    return content
                last_err = f"key#{idx + 1}: empty content"
            except requests.RequestException as exc:
                last_err = f"key#{idx + 1}: {exc}"
        raise TierUnavailable(f"{tier_label}: every admitted key failed, last error: {last_err}")
    raise TierUnavailable(f"{tier_label}: admitted but no configured tier")


def continuation_opening_message(continuation_context: str | None) -> str:
    if not continuation_context:
        return (
            "You are Frankenstein's Bauleiter -- the persistent foreman driving a "
            "72-hour autonomous build. This is your first activation. Read "
            "CONCEPT.md and BUILD_ORCHESTRATION_PLAN_20260827.json in "
            "research_entity/topic_packets/frankenstein-master-cognition-concept/ "
            "for context, then work only through currently admitted, verifiable steps."
        )
    return (
        "You are continuing your own prior work, not reading a summary of "
        "someone else's work. A previous activation of you (the same "
        "Bauleiter, same role, same responsibility) reached a checkpoint and "
        "wrote the following account so that you would not lose the thread. "
        "Read it as your own memory and continue from there -- do not restart "
        "or re-derive decisions already made:\n\n"
        f"{continuation_context}\n\nContinue the build from this point."
    )


def _log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {line}\n")


def _harness_dispatch_admitted() -> tuple[bool, tuple[str, ...]]:
    admitted = admitted_provider_names()
    return HARNESS_PROVIDER_SET.issubset(set(admitted)), admitted


def dispatch_helper_task(task_description: str, reason: str, log_path: Path,
                          max_retries: int = 4) -> dict:
    """Dispatch a helper only after the external caller boundary is admitted."""
    allowed, admitted = _harness_dispatch_admitted()
    if not allowed:
        _log(
            log_path,
            "HELPER_DISPATCH_BLOCKED CANONICAL_PROVIDER_HARD_OFF_OR_PARTIAL_ADMISSION "
            f"admitted={list(admitted)} provider_calls=0 secret_lookups=0 aider_calls=0",
        )
        return {
            "ok": False,
            "blocked": "CANONICAL_PROVIDER_HARD_OFF_OR_PARTIAL_ADMISSION",
            "admitted_free_providers": list(admitted),
            "provider_calls": 0,
            "secret_lookups": 0,
            "aider_calls": 0,
        }

    delay = 5.0
    last_result = None
    for attempt in range(1, max_retries + 1):
        try:
            proc = subprocess.run(
                [sys.executable, HARNESS_PATH, "fallback-start",
                 "--auftrag", task_description, "--grund", reason],
                capture_output=True,
                text=True,
                timeout=900,
            )
            combined = (proc.stdout or "") + (proc.stderr or "")
            rate_limited = any(token in combined for token in (
                "RateLimitError", "429", "rate limit", "rate_limit",
            ))
            last_result = {
                "attempt": attempt,
                "returncode": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-2000:],
                "stderr_tail": (proc.stderr or "")[-2000:],
                "rate_limited": rate_limited,
            }
            _log(log_path, f"HELPER_DISPATCH attempt={attempt} rc={proc.returncode} "
                           f"rate_limited={rate_limited} task={task_description[:120]!r}")
            if proc.returncode == 0 and not rate_limited:
                return {"ok": True, **last_result}
            if not rate_limited:
                return {"ok": False, **last_result}
        except subprocess.TimeoutExpired:
            last_result = {"attempt": attempt, "returncode": None, "timeout": True}
            _log(log_path, f"HELPER_DISPATCH attempt={attempt} TIMEOUT task={task_description[:120]!r}")
        time.sleep(delay)
        delay = min(delay * 2, 300.0)
    return {"ok": False, "exhausted_retries": True, **(last_result or {})}


def _ensure_scope(fabric: Fabric) -> None:
    snap = fabric.snapshot()
    if not any(scope["scope"] == BUILD_SCOPE for scope in snap.scopes):
        fabric.seed_scope(BUILD_SCOPE)


def record_build_event(fabric: Fabric, node_id: str, payload: dict, log_path: Path) -> dict:
    try:
        fabric.runtime_join(node_id, "frankenstein-bauleiter", os.getpid())
        fabric.runtime_heartbeat(node_id, healthy=True)
        elected = fabric.elect_coordinator(BUILD_SCOPE, candidate_node_ids=[node_id])
        if elected is None:
            snap = fabric.snapshot()
            lease_row = next((lease for lease in snap.leases if lease["scope"] == BUILD_SCOPE and lease["valid"]), None)
            if lease_row is None:
                return {"error": "NO_VALID_LEASE_AND_ELECTION_DENIED"}
            _log(log_path, f"BUILD_STATE reusing existing lease {lease_row['lease_id']}")
            return {"error": "LEASE_HELD_BY_OTHER_OR_STALE_LOCAL_STATE", "lease": dict(lease_row)}
        lease, token = elected
        snap = fabric.snapshot()
        packet = result_packet(node_id, snap, BUILD_SCOPE, payload)
        fabric.emit_node_result(packet)
        committed = fabric.coordinator_drain_and_commit(BUILD_SCOPE, lease, token)
        _log(log_path, f"BUILD_STATE committed {len(committed)} packet(s): {json.dumps(payload)[:200]}")
        return {"ok": True, "committed": committed}
    except FabricError as exc:
        _log(log_path, f"BUILD_STATE_ERROR {exc}")
        return {"error": str(exc)}


def write_continuation_summary(fabric: Fabric, node_id: str, actions_log: list[str],
                                sandbox_dir: Path, ended_reason: str) -> Path:
    del fabric, node_id
    actions_text = "\n".join(f"- {action}" for action in actions_log) or "(no actions recorded this instance)"
    prompt = (
        "You are the Frankenstein Bauleiter, about to end this activation "
        f"(reason: {ended_reason}). Write a CONTINUATION_SUMMARY for your own "
        "next activation from this real action log. Be explicit about unfinished "
        "work and failures.\n\nActions this session:\n" + actions_text
    )
    try:
        narrative = call_specific_tier(
            PRIMARY_TIER,
            [{"role": "user", "content": prompt}],
            max_tokens=1200,
        )
    except TierUnavailable as exc:
        narrative = (
            f"[FALLBACK, no admitted/available LLM for narrative summary: {exc}]\n\n"
            f"Ended reason: {ended_reason}\nRaw action log:\n{actions_text}"
        )
    ts = time.strftime("%Y%m%dT%H%M%S")
    out_path = sandbox_dir / f"CONTINUATION_SUMMARY_{ts}.md"
    out_path.write_text(narrative, encoding="utf-8")
    latest_path = sandbox_dir / "CONTINUATION_SUMMARY.md"
    latest_path.write_text(narrative, encoding="utf-8")
    return latest_path


def run_bauleiter_instance(continuation_context: str | None, fabric_path: str,
                            sandbox_dir: Path, log_path: Path,
                            max_actions: int = 20, max_seconds: float = 1800.0) -> dict:
    fabric = Fabric(Path(fabric_path))
    _ensure_scope(fabric)
    opening = continuation_opening_message(continuation_context)
    _log(log_path, f"BAULEITER_ACTIVATED continuation={'yes' if continuation_context else 'no (first activation)'}")
    actions_log: list[str] = [f"Activation opened with: {opening[:200]}..."]
    real_actions_taken = 0
    ended_reason = "checkpoint"
    start = time.time()
    training_marker = sandbox_dir / "TRAINING_RUN_READY_FOR_LAUNCH.json"
    packages.seed_all_packages(fabric, log_fn=lambda message: _log(log_path, message))

    try:
        while real_actions_taken < max_actions and (time.time() - start) < max_seconds:
            if training_marker.exists():
                ended_reason = "training_marker_present"
                actions_log.append(
                    "Training marker observed. It is not execution authority; no Together call was made."
                )
                break
            if packages.all_packages_done(fabric):
                actions_log.append("All decomposed packages are DONE.")
                break
            claimed = packages.claim_next_package(
                fabric,
                BAULEITER_NODE_ID,
                log_fn=lambda message: _log(log_path, message),
            )
            if claimed is None:
                progress = packages.progress_summary(fabric)
                actions_log.append(
                    f"No claimable package right now. Progress: {progress['done']}/{progress['total']} done."
                )
                break

            record_build_event(
                fabric,
                BAULEITER_NODE_ID,
                {"event": "PACKAGE_DISPATCH_STARTED", "package_id": claimed["task_id"], "ts": time.time()},
                log_path,
            )
            dispatch_result = dispatch_helper_task(
                claimed["description"],
                "frankenstein-bauleiter-package",
                log_path,
            )
            ok = bool(dispatch_result.get("ok", False))
            packages.mark_package_done(
                fabric,
                claimed["task_id"],
                ok=ok,
                node_id=BAULEITER_NODE_ID,
                log_fn=lambda message: _log(log_path, message),
            )
            record_build_event(
                fabric,
                BAULEITER_NODE_ID,
                {
                    "event": "PACKAGE_DISPATCH_ENDED",
                    "package_id": claimed["task_id"],
                    "ok": ok,
                    "blocked": dispatch_result.get("blocked"),
                    "ts": time.time(),
                },
                log_path,
            )
            actions_log.append(
                f"Package {claimed['task_id']} dispatched -> ok={ok} "
                f"(acceptance: {claimed['acceptance_criteria']})"
            )
            real_actions_taken += 1
            if dispatch_result.get("blocked"):
                ended_reason = "provider_hard_off"
                actions_log.append(
                    "Canonical provider admission blocked external dispatch; stopping this activation without retry storm."
                )
                break
    except Exception as exc:  # noqa: BLE001
        _log(log_path, f"BAULEITER_EXCEPTION {type(exc).__name__}: {exc}")
        actions_log.append(f"EXCEPTION ended this activation: {type(exc).__name__}: {exc}")
        ended_reason = "exception"

    summary_path = write_continuation_summary(
        fabric,
        BAULEITER_NODE_ID,
        actions_log,
        sandbox_dir,
        ended_reason,
    )
    return {
        "ended_reason": ended_reason,
        "continuation_summary_path": str(summary_path),
        "real_actions_taken": real_actions_taken,
    }


def bauleiter_supervisor_loop(fabric_path: str, sandbox_dir: Path,
                               max_wallclock_hours: float = 72.0,
                               log_path: Path | None = None) -> None:
    log_path = log_path or (sandbox_dir / "bauleiter_supervisor.log")
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max_wallclock_hours * 3600.0
    continuation_context: str | None = None
    latest_summary = sandbox_dir / "CONTINUATION_SUMMARY.md"
    if latest_summary.exists():
        continuation_context = latest_summary.read_text(encoding="utf-8")
        _log(log_path, "SUPERVISOR_RESUMING_FROM_EXISTING_SUMMARY")

    respawn_count = 0
    while time.time() < deadline:
        _log(log_path, f"SUPERVISOR_SPAWNING_INSTANCE respawn_count={respawn_count}")
        result = run_bauleiter_instance(
            continuation_context,
            fabric_path,
            sandbox_dir,
            log_path,
        )
        _log(log_path, f"SUPERVISOR_INSTANCE_ENDED {json.dumps(result)}")
        respawn_count += 1
        if result["ended_reason"] in {
            "training_marker_present",
            "provider_hard_off",
        }:
            _log(
                log_path,
                f"SUPERVISOR_STOPPING: {result['ended_reason']} -- no provider/training bypass",
            )
            return
        continuation_context = Path(result["continuation_summary_path"]).read_text(encoding="utf-8")
        time.sleep(2.0)
    _log(log_path, f"SUPERVISOR_STOPPING: wallclock limit reached after {respawn_count} respawns")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fabric-path",
        default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                    "frankenstein-master-cognition-concept" / "build_fabric.sqlite3"),
    )
    parser.add_argument(
        "--sandbox-dir",
        default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                    "frankenstein-master-cognition-concept" / "bauleiter_sandbox"),
    )
    parser.add_argument("--max-wallclock-hours", type=float, default=72.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    sandbox_dir = Path(args.sandbox_dir)
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    log_path = sandbox_dir / "bauleiter_supervisor.log"
    if args.once:
        continuation_context = None
        summary = sandbox_dir / "CONTINUATION_SUMMARY.md"
        if summary.exists():
            continuation_context = summary.read_text(encoding="utf-8")
        result = run_bauleiter_instance(
            continuation_context,
            args.fabric_path,
            sandbox_dir,
            log_path,
        )
        print(json.dumps(result, indent=2))
        return
    bauleiter_supervisor_loop(
        args.fabric_path,
        sandbox_dir,
        args.max_wallclock_hours,
        log_path,
    )


if __name__ == "__main__":
    main()
