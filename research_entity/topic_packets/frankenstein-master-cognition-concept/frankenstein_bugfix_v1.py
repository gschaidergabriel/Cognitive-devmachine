"""Bugfix-Frankenstein watchdog with canonical provider-boundary gating.

The watchdog remains independent from the Bauleiter and preserves its own
local git baseline/checkpoint/rollback history.  Provider clients are now
lazy-imported only after the canonical EntityOS/HCU admission boundary says a
specific route is admitted.  Under HARD_OFF the watchdog still performs local
state/reclaim/versioning work, but it does not inspect provider secrets, import
the provider helper, make network calls, or enter an endless rate-limit loop.
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

from free_provider_admission import provider_is_admitted_free  # noqa: E402
from grid10_fabric import Fabric, FabricError, result_packet  # noqa: E402

BUILD_SCOPE = "frankenstein:build_state"
BUGFIX_NODE_ID = "frankenstein-bugfix"
BUGFIX_TIERS = ["nvidia", "groq", "mistral"]
POLL_REGULATOR_NAME = "frankenstein:bugfix_poll_intensity"
BASE_POLL_SLEEP_SECONDS = 5.0
UR_BASELINE_TAG = "frankenstein-ur-baseline"
CHECKPOINT_TAG = "frankenstein-checkpoint-current"


class AllTiersUnavailable(RuntimeError):
    pass


class ProviderHardOff(RuntimeError):
    """Canonical admission blocked all candidate provider routes."""


def _load_provider_clients_after_admission(tier_label: str):
    if not provider_is_admitted_free(tier_label):
        raise ProviderHardOff(f"{tier_label}: CANONICAL_PROVIDER_HARD_OFF_OR_UNADMITTED")
    last_resort = os.path.expanduser("~/last-resort")
    if last_resort not in sys.path:
        sys.path.insert(0, last_resort)
    pool_llm = importlib.import_module("llm")
    requests = importlib.import_module("requests")
    return pool_llm, requests


def _call_one_tier(tier_label: str, messages: list[dict], *, max_tokens: int = 1200,
                    temperature: float = 0.2, timeout: float | None = None) -> str | None:
    """Call one tier only after canonical admission; HARD_OFF is not an outage."""
    pool_llm, requests = _load_provider_clients_after_admission(tier_label)
    for label, url, model, api_keys in pool_llm._tiers():
        if label != tier_label:
            continue
        for key in api_keys:
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
                if response.status_code != 200:
                    continue
                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    continue
                content = (choices[0].get("message") or {}).get("content")
                if content:
                    return content
            except requests.RequestException:
                continue
        return None
    return None


def call_with_explicit_fallback(messages: list[dict], **kwargs) -> tuple[str, str]:
    """Walk tiers in order; distinguish canonical block from availability failure."""
    hardoff_errors: list[str] = []
    for tier in BUGFIX_TIERS:
        try:
            content = _call_one_tier(tier, messages, **kwargs)
        except ProviderHardOff as exc:
            hardoff_errors.append(str(exc))
            continue
        if content:
            return content, tier
    if len(hardoff_errors) == len(BUGFIX_TIERS):
        raise ProviderHardOff("all Bugfix tiers blocked by canonical provider admission")
    raise AllTiersUnavailable("all admitted Bugfix tiers failed this attempt")


def wait_for_any_tier_available(messages: list[dict], log_path: Path, *,
                                 max_sleep_seconds: float = 300.0, **kwargs) -> tuple[str, str]:
    """Back off on real availability failure, but never retry an authority denial."""
    delay = 5.0
    attempt = 0
    while True:
        attempt += 1
        try:
            return call_with_explicit_fallback(messages, **kwargs)
        except ProviderHardOff:
            _log(
                log_path,
                "PROVIDER_HARD_OFF provider_calls=0 secret_lookups=0 network_calls=0; not retrying as rate limit",
            )
            raise
        except AllTiersUnavailable:
            _log(log_path, f"ALL_ADMITTED_TIERS_UNAVAILABLE attempt={attempt} sleeping={delay:.0f}s")
            time.sleep(delay)
            delay = min(delay * 2, max_sleep_seconds)


def _log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {line}\n")


def _run_git(repo_dir: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def ensure_bugfix_repo(repo_dir: Path, log_path: Path) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        _run_git(repo_dir, "init")
        _run_git(repo_dir, "config", "user.email", "frankenstein-bugfix@local")
        _run_git(repo_dir, "config", "user.name", "Frankenstein Bugfix")
        (repo_dir / ".bugfix_repo_marker").write_text(
            "Bugfix-Frankenstein's own working repo. Separate from the main "
            "research repo and from the Bauleiter's own commits.\n",
            encoding="utf-8",
        )
        _run_git(repo_dir, "add", "-A")
        _run_git(repo_dir, "commit", "-m", "initial baseline (Bugfix-Frankenstein repo init)")
        _log(log_path, "BUGFIX_REPO_INITIALIZED")

    tags = _run_git(repo_dir, "tag", "--list").stdout.split()
    if UR_BASELINE_TAG not in tags:
        _run_git(repo_dir, "tag", UR_BASELINE_TAG)
        _log(log_path, f"UR_BASELINE_TAG_SET {UR_BASELINE_TAG} (immutable, never moved again)")
    if CHECKPOINT_TAG not in tags:
        _run_git(repo_dir, "tag", CHECKPOINT_TAG)
        _log(log_path, f"CHECKPOINT_TAG_SET {CHECKPOINT_TAG} (moving, advances only on strict improvement)")


def bugfix_commit_before(repo_dir: Path, description: str, log_path: Path) -> str:
    _run_git(repo_dir, "add", "-A")
    _run_git(repo_dir, "commit", "-m", f"before-fix: {description}", "--allow-empty")
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"BUGFIX_COMMIT_BEFORE {sha[:12]} {description}")
    return sha


def bugfix_commit_after(repo_dir: Path, description: str, log_path: Path) -> str:
    _run_git(repo_dir, "add", "-A")
    _run_git(repo_dir, "commit", "-m", f"after-fix: {description}", "--allow-empty")
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"BUGFIX_COMMIT_AFTER {sha[:12]} {description}")
    return sha


def bugfix_rollback_last(repo_dir: Path, log_path: Path) -> str:
    _run_git(repo_dir, "revert", "--no-edit", "HEAD")
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"BUGFIX_ROLLBACK_LAST new_head={sha[:12]}")
    return sha


def rollback_to_last_checkpoint(repo_dir: Path, log_path: Path) -> str:
    _run_git(repo_dir, "reset", "--hard", CHECKPOINT_TAG)
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"ROLLBACK_TO_LAST_CHECKPOINT new_head={sha[:12]}")
    return sha


def rollback_to_ur_baseline(repo_dir: Path, log_path: Path) -> str:
    _run_git(repo_dir, "reset", "--hard", UR_BASELINE_TAG)
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"ROLLBACK_TO_UR_BASELINE new_head={sha[:12]}")
    return sha


def promote_checkpoint_if_strictly_better(repo_dir: Path, metrics_before: dict, metrics_after: dict,
                                           metric_directions: dict, log_path: Path) -> bool:
    for key, direction in metric_directions.items():
        if key not in metrics_before or key not in metrics_after:
            _log(log_path, f"CHECKPOINT_PROMOTION_DENIED missing metric {key!r}")
            return False
        before_v, after_v = metrics_before[key], metrics_after[key]
        if direction == "lower_better" and after_v > before_v:
            _log(log_path, f"CHECKPOINT_PROMOTION_DENIED regression on {key}: {before_v} -> {after_v}")
            return False
        if direction == "higher_better" and after_v < before_v:
            _log(log_path, f"CHECKPOINT_PROMOTION_DENIED regression on {key}: {before_v} -> {after_v}")
            return False
    _run_git(repo_dir, "tag", "-f", CHECKPOINT_TAG)
    _log(log_path, f"CHECKPOINT_PROMOTED metrics_before={metrics_before} metrics_after={metrics_after}")
    return True


def record_bugfix_finding(fabric: Fabric, payload: dict, log_path: Path) -> dict:
    try:
        fabric.runtime_join(BUGFIX_NODE_ID, "frankenstein-bugfix-watchdog", os.getpid())
        fabric.runtime_heartbeat(BUGFIX_NODE_ID, healthy=True)
        elected = fabric.elect_coordinator(BUILD_SCOPE, candidate_node_ids=[BUGFIX_NODE_ID])
        if elected is None:
            snap = fabric.snapshot()
            lease_row = next((lease for lease in snap.leases if lease["scope"] == BUILD_SCOPE and lease["valid"]), None)
            _log(log_path, "BUGFIX_FINDING_DEFERRED lease held elsewhere")
            return {"deferred": True, "lease": dict(lease_row) if lease_row else None}
        lease, token = elected
        snap = fabric.snapshot()
        packet = result_packet(BUGFIX_NODE_ID, snap, BUILD_SCOPE, payload)
        fabric.emit_node_result(packet)
        committed = fabric.coordinator_drain_and_commit(BUILD_SCOPE, lease, token)
        _log(log_path, f"BUGFIX_FINDING_RECORDED {json.dumps(payload)[:200]}")
        return {"ok": True, "committed": committed}
    except FabricError as exc:
        _log(log_path, f"BUGFIX_FINDING_ERROR {exc}")
        return {"error": str(exc)}


def _read_poll_intensity(fabric: Fabric) -> float:
    regulator = fabric.get_regulator(POLL_REGULATOR_NAME, default=1.0)
    return float(regulator["value_real"]) if regulator else 1.0


def _bump_poll_intensity(fabric: Fabric, new_value: float) -> None:
    try:
        regulator = fabric.get_regulator(POLL_REGULATOR_NAME, default=1.0)
        fabric.set_regulator(
            POLL_REGULATOR_NAME,
            new_value,
            writer=BUGFIX_NODE_ID,
            expected_version=regulator["version"] if regulator else None,
        )
    except FabricError:
        pass


def scan_for_stuck_work(fabric: Fabric, log_path: Path,
                         stale_after_seconds: float = 30.0) -> list[str]:
    reclaimed = fabric.runtime_reclaim_stale_claims(
        BUGFIX_NODE_ID,
        stale_after_seconds=stale_after_seconds,
    )
    if reclaimed:
        _log(log_path, f"STUCK_TASKS_RECLAIMED {reclaimed}")
    return reclaimed


def bugfix_watch_loop(fabric_path: str, repo_dir: Path, log_path: Path,
                       max_wallclock_hours: float = 72.0,
                       max_iterations: int | None = None) -> None:
    fabric = Fabric(Path(fabric_path))
    ensure_bugfix_repo(repo_dir, log_path)
    deadline = time.time() + max_wallclock_hours * 3600.0
    iterations = 0
    recent_problem_until = 0.0

    while time.time() < deadline:
        if max_iterations is not None and iterations >= max_iterations:
            break
        iterations += 1
        reclaimed = scan_for_stuck_work(fabric, log_path)
        if reclaimed:
            recent_problem_until = time.time() + 120.0
            for task_id in reclaimed:
                description = f"reclaimed stuck task {task_id}"
                before_sha = bugfix_commit_before(repo_dir, description, log_path)
                fix_prompt = [{
                    "role": "user",
                    "content": (
                        f"A build subtask (id={task_id}) was found stuck and reclaimed. "
                        "State the likely cause and concrete prevention action."
                    ),
                }]
                try:
                    diagnosis, tier_used = wait_for_any_tier_available(fix_prompt, log_path)
                except ProviderHardOff as exc:
                    diagnosis = (
                        "[CANONICAL PROVIDER HARD_OFF -- no external diagnosis requested] "
                        f"{exc}. Local reclaim evidence preserved; provider_calls=0; "
                        "secret_lookups=0; network_calls=0."
                    )
                    tier_used = "none"
                except AllTiersUnavailable:
                    diagnosis, tier_used = "(no admitted tier reachable this cycle)", "none"
                (repo_dir / f"diagnosis_{task_id}.md").write_text(diagnosis, encoding="utf-8")
                after_sha = bugfix_commit_after(
                    repo_dir,
                    f"{description} (tier={tier_used})",
                    log_path,
                )
                record_bugfix_finding(
                    fabric,
                    {
                        "event": "STUCK_TASK_DIAGNOSED",
                        "task_id": task_id,
                        "before_sha": before_sha,
                        "after_sha": after_sha,
                        "tier_used": tier_used,
                        "provider_hard_off": tier_used == "none" and "HARD_OFF" in diagnosis,
                        "ts": time.time(),
                    },
                    log_path,
                )

        intensity = 3.0 if time.time() < recent_problem_until else 1.0
        _bump_poll_intensity(fabric, intensity)
        sleep_s = BASE_POLL_SLEEP_SECONDS / max(intensity, 0.01)
        time.sleep(sleep_s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fabric-path",
        default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                    "frankenstein-master-cognition-concept" / "build_fabric.sqlite3"),
    )
    parser.add_argument(
        "--repo-dir",
        default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                    "frankenstein-master-cognition-concept" / "bugfix_repo"),
    )
    parser.add_argument("--max-wallclock-hours", type=float, default=72.0)
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir)
    log_path = repo_dir / "bugfix_watch.log"
    bugfix_watch_loop(
        args.fabric_path,
        repo_dir,
        log_path,
        args.max_wallclock_hours,
        args.max_iterations,
    )


if __name__ == "__main__":
    main()
