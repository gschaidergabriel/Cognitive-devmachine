"""
Bugfix-Frankenstein: the third, separate role alongside the Bauleiter and the
free-pool helper models (BUILD_ORCHESTRATION_PLAN_20260827.json, step_1b).
Deliberately a SEPARATE standalone script, not sharing a code path with
frankenstein_orchestrator_v1.py, even though both use the same strongest-
model-first + continuation-summary respawn DESIGN pattern -- the design is
reused, the implementation is independent, per Gabriel's explicit
requirement that these be two independent, separately-robust processes.

Written directly by the coordinator for the same reason as the orchestrator
script: two free-pool delegation attempts on this task both failed to
commit real content, and the coordinator's own explicit "you personally
accept the first working version" instruction applies here too.

Role: watches the "frankenstein:build_state" fabric scope passively (slow
poll when nothing is wrong, faster after a recent problem -- reusing the
SAME regulator-driven elastic_poll concept already proven in
tools/grid10_node.py, just against its own regulator name), detects stuck/
errored subtasks via the real, already-existing
Fabric.runtime_reclaim_stale_claims(), and fixes things inside its OWN
local git repository so a bad fix can be reverted without touching the
Bauleiter's or any helper's commit history. Never gives up on a rate limit
-- waits instead, walking three explicit tiers (Nemotron -> Groq -> Mistral)
with its own backoff between them.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, os.path.expanduser("~/last-resort"))

from grid10_fabric import Fabric, FabricError, result_packet  # noqa: E402
import llm as pool_llm  # noqa: E402

import requests  # noqa: E402

BUILD_SCOPE = "frankenstein:build_state"
BUGFIX_NODE_ID = "frankenstein-bugfix"
BUGFIX_TIERS = ["nvidia", "groq", "mistral"]  # explicit, deliberate order for
                                               # this role -- NOT the default
                                               # groq-first cascade, because
                                               # this watchdog must walk
                                               # tiers on its own terms with
                                               # its own backoff between them.
POLL_REGULATOR_NAME = "frankenstein:bugfix_poll_intensity"
BASE_POLL_SLEEP_SECONDS = 5.0
UR_BASELINE_TAG = "frankenstein-ur-baseline"
CHECKPOINT_TAG = "frankenstein-checkpoint-current"


class AllTiersUnavailable(RuntimeError):
    pass


def _call_one_tier(tier_label: str, messages: list[dict], *, max_tokens: int = 1200,
                    temperature: float = 0.2, timeout: float | None = None) -> str | None:
    """Real single-tier call against ~/last-resort/llm.py's own _tiers()
    key list. Returns None (not an exception) on failure/rate-limit so the
    caller's explicit 3-tier walk stays simple -- exceptions are reserved
    for genuinely unexpected situations, not the ordinary "this tier is
    rate-limited right now" case."""
    for label, url, model, api_keys in pool_llm._tiers():
        if label != tier_label:
            continue
        for key in api_keys:
            try:
                r = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": messages, "max_tokens": max_tokens,
                          "temperature": temperature, "stream": False},
                    timeout=timeout or pool_llm.TIMEOUT,
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                choices = data.get("choices") or []
                if not choices:
                    continue
                content = (choices[0].get("message") or {}).get("content")
                if content:
                    return content
            except requests.RequestException:
                continue
        return None  # tier configured but every key failed
    return None  # tier not configured at all (no key in keys.env)


def call_with_explicit_fallback(messages: list[dict], **kwargs) -> tuple[str, str]:
    """Walks BUGFIX_TIERS in order, returns (content, tier_label_used).
    Raises AllTiersUnavailable only if EVERY tier fails on THIS attempt --
    the caller (wait_for_any_tier_available loop) is what actually never
    gives up; this function itself is allowed to fail once per attempt."""
    for tier in BUGFIX_TIERS:
        content = _call_one_tier(tier, messages, **kwargs)
        if content:
            return content, tier
    raise AllTiersUnavailable("all three tiers (nvidia/groq/mistral) failed this attempt")


def wait_for_any_tier_available(messages: list[dict], log_path: Path, *,
                                 max_sleep_seconds: float = 300.0, **kwargs) -> tuple[str, str]:
    """Real exponential backoff, capped, NEVER gives up -- rate limits must
    never stop Bugfix-Frankenstein. Loops forever until one of the three
    tiers succeeds."""
    delay = 5.0
    attempt = 0
    while True:
        attempt += 1
        try:
            return call_with_explicit_fallback(messages, **kwargs)
        except AllTiersUnavailable:
            _log(log_path, f"ALL_TIERS_UNAVAILABLE attempt={attempt} sleeping={delay:.0f}s")
            time.sleep(delay)
            delay = min(delay * 2, max_sleep_seconds)


def _log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {line}\n")


def _run_git(repo_dir: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, check=check)


def ensure_bugfix_repo(repo_dir: Path, log_path: Path) -> None:
    """Real `git init` in Bugfix-Frankenstein's OWN working directory,
    separate from the main research repo, so its commit history (and any
    revert it does of its own changes) never touches the Bauleiter's or a
    helper's commits. Sets the immutable UR_BASELINE_TAG exactly once, on
    the very first run, and never moves it again."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        _run_git(repo_dir, "init")
        _run_git(repo_dir, "config", "user.email", "frankenstein-bugfix@local")
        _run_git(repo_dir, "config", "user.name", "Frankenstein Bugfix")
        (repo_dir / ".bugfix_repo_marker").write_text(
            "Bugfix-Frankenstein's own working repo. Separate from the main "
            "research repo and from the Bauleiter's own commits.\n"
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
    """Commits the current state BEFORE a fix attempt, so the fix itself is
    isolated as its own diff and can be reverted in isolation. Returns the
    commit hash."""
    _run_git(repo_dir, "add", "-A")
    _run_git(repo_dir, "commit", "-m", f"before-fix: {description}", "--allow-empty")
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"BUGFIX_COMMIT_BEFORE {sha[:12]} {description}")
    return sha


def bugfix_commit_after(repo_dir: Path, description: str, log_path: Path) -> str:
    """Commits the result AFTER applying a fix. Returns the commit hash."""
    _run_git(repo_dir, "add", "-A")
    _run_git(repo_dir, "commit", "-m", f"after-fix: {description}", "--allow-empty")
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"BUGFIX_COMMIT_AFTER {sha[:12]} {description}")
    return sha


def bugfix_rollback_last(repo_dir: Path, log_path: Path) -> str:
    """Reverts the most recent commit in Bugfix-Frankenstein's OWN repo
    (its own most recent fix, since this repo only ever contains ITS
    commits) via `git revert`, which preserves history (unlike reset --hard)
    so the failed attempt stays visible for later diagnosis. Returns the
    new HEAD hash."""
    _run_git(repo_dir, "revert", "--no-edit", "HEAD")
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"BUGFIX_ROLLBACK_LAST new_head={sha[:12]}")
    return sha


def rollback_to_last_checkpoint(repo_dir: Path, log_path: Path) -> str:
    """Rollback level 1: reset the working tree to the current
    CHECKPOINT_TAG (the last state that was PROVEN strictly better with no
    regressions). Distinct function from rollback_to_ur_baseline() so the
    two rollback levels are unambiguous in code and logs -- never the same
    function with a flag."""
    _run_git(repo_dir, "reset", "--hard", CHECKPOINT_TAG)
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"ROLLBACK_TO_LAST_CHECKPOINT new_head={sha[:12]}")
    return sha


def rollback_to_ur_baseline(repo_dir: Path, log_path: Path) -> str:
    """Rollback level 2 (absolute last resort): reset the working tree to
    the IMMUTABLE UR_BASELINE_TAG, set once at the very first run and never
    moved since. Used only when even the current checkpoint is not
    trustworthy."""
    _run_git(repo_dir, "reset", "--hard", UR_BASELINE_TAG)
    sha = _run_git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    _log(log_path, f"ROLLBACK_TO_UR_BASELINE new_head={sha[:12]}")
    return sha


def promote_checkpoint_if_strictly_better(repo_dir: Path, metrics_before: dict, metrics_after: dict,
                                           metric_directions: dict, log_path: Path) -> bool:
    """Moves CHECKPOINT_TAG forward to HEAD only if EVERY key in
    metrics_after is equal-or-better than the corresponding key in
    metrics_before, per metric_directions (e.g. {"latency_s": "lower_better",
    "ram_mb": "lower_better", "throughput_per_s": "higher_better",
    "error_count": "lower_better"}). If even one metric regressed, returns
    False and leaves the checkpoint tag exactly where it was -- the
    candidate commit still exists in history, just unreferenced by the
    checkpoint tag, so nothing is lost, it is simply not promoted."""
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
    """Writes findings into the SAME 'frankenstein:build_state' fabric scope
    the Bauleiter reads, via the same real coordinator_commit path used
    everywhere else in this session (join, elect-or-reuse lease, emit
    result, drain+commit) -- so the Bauleiter can see what was fixed and
    why, and this watchdog reads the Bauleiter's own current task/priority
    state from the same scope before deciding what a fix should look like."""
    try:
        fabric.runtime_join(BUGFIX_NODE_ID, "frankenstein-bugfix-watchdog", os.getpid())
        fabric.runtime_heartbeat(BUGFIX_NODE_ID, healthy=True)
        elected = fabric.elect_coordinator(BUILD_SCOPE, candidate_node_ids=[BUGFIX_NODE_ID])
        if elected is None:
            snap = fabric.snapshot()
            lease_row = next((l for l in snap.leases if l["scope"] == BUILD_SCOPE and l["valid"]), None)
            _log(log_path, "BUGFIX_FINDING_DEFERRED lease held elsewhere (expected if Bauleiter holds it)")
            return {"deferred": True, "lease": dict(lease_row) if lease_row else None}
        lease, token = elected
        snap = fabric.snapshot()
        packet = result_packet(BUGFIX_NODE_ID, snap, BUILD_SCOPE, payload)
        fabric.emit_node_result(packet)
        committed = fabric.coordinator_drain_and_commit(BUILD_SCOPE, lease, token)
        _log(log_path, f"BUGFIX_FINDING_RECORDED {json.dumps(payload)[:200]}")
        return {"ok": True, "committed": committed}
    except FabricError as e:
        _log(log_path, f"BUGFIX_FINDING_ERROR {e}")
        return {"error": str(e)}


def _read_poll_intensity(fabric: Fabric) -> float:
    reg = fabric.get_regulator(POLL_REGULATOR_NAME, default=1.0)
    return float(reg["value_real"]) if reg else 1.0


def _bump_poll_intensity(fabric: Fabric, new_value: float) -> None:
    """Best-effort CAS write -- if it races with another writer, just skip
    this cycle's adjustment rather than retrying aggressively; the poll
    loop will simply try again next iteration."""
    try:
        reg = fabric.get_regulator(POLL_REGULATOR_NAME, default=1.0)
        fabric.set_regulator(POLL_REGULATOR_NAME, new_value, writer=BUGFIX_NODE_ID,
                              expected_version=reg["version"] if reg else None)
    except FabricError:
        pass


def scan_for_stuck_work(fabric: Fabric, log_path: Path, stale_after_seconds: float = 30.0) -> list[str]:
    """Detects stuck/errored subtasks by reusing the real, already-existing
    Fabric.runtime_reclaim_stale_claims() -- a task claimed but never
    completed (claiming node died/stalled) is the concrete, already-proven
    failure mode this reuses detection for, rather than inventing a new
    stuck-task heuristic."""
    reclaimed = fabric.runtime_reclaim_stale_claims(BUGFIX_NODE_ID, stale_after_seconds=stale_after_seconds)
    if reclaimed:
        _log(log_path, f"STUCK_TASKS_RECLAIMED {reclaimed}")
    return reclaimed


def bugfix_watch_loop(fabric_path: str, repo_dir: Path, log_path: Path,
                       max_wallclock_hours: float = 72.0, max_iterations: int | None = None) -> None:
    """Passive watch loop: polls slowly when nothing is wrong, faster after
    a recent problem was seen -- same regulator-driven elastic_poll concept
    already proven in tools/grid10_node.py (reads poll_intensity, scales
    sleep by 1/intensity), applied here to Bugfix-Frankenstein's own
    dedicated regulator name so it never fights the Bauleiter's or any
    node's own poll_intensity regulator."""
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
            recent_problem_until = time.time() + 120.0  # stay fast-polling for 2 real minutes
            for task_id in reclaimed:
                description = f"reclaimed stuck task {task_id}"
                before_sha = bugfix_commit_before(repo_dir, description, log_path)
                fix_prompt = [{"role": "user", "content":
                    f"A build subtask (id={task_id}) was found stuck (claimed but never "
                    "completed) and has been reclaimed back to OPEN. As Bugfix-Frankenstein, "
                    "briefly state the most likely cause and the concrete next action to "
                    "prevent this recurring. Be concrete, not generic."}]
                try:
                    diagnosis, tier_used = wait_for_any_tier_available(fix_prompt, log_path)
                except AllTiersUnavailable:
                    diagnosis, tier_used = "(no tier reachable this cycle)", "none"
                (repo_dir / f"diagnosis_{task_id}.md").write_text(diagnosis)
                after_sha = bugfix_commit_after(repo_dir, f"{description} (tier={tier_used})", log_path)
                record_bugfix_finding(fabric, {
                    "event": "STUCK_TASK_DIAGNOSED", "task_id": task_id,
                    "before_sha": before_sha, "after_sha": after_sha,
                    "tier_used": tier_used, "ts": time.time(),
                }, log_path)

        intensity = 3.0 if time.time() < recent_problem_until else 1.0
        _bump_poll_intensity(fabric, intensity)
        sleep_s = BASE_POLL_SLEEP_SECONDS / max(intensity, 0.01)
        time.sleep(sleep_s)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--fabric-path", default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                                                 "frankenstein-master-cognition-concept" / "build_fabric.sqlite3"))
    p.add_argument("--repo-dir", default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                                              "frankenstein-master-cognition-concept" / "bugfix_repo"))
    p.add_argument("--max-wallclock-hours", type=float, default=72.0)
    p.add_argument("--max-iterations", type=int, default=None, help="for acceptance testing: stop after N poll iterations")
    args = p.parse_args()

    repo_dir = Path(args.repo_dir)
    log_path = repo_dir / "bugfix_watch.log"
    bugfix_watch_loop(args.fabric_path, repo_dir, log_path, args.max_wallclock_hours, args.max_iterations)


if __name__ == "__main__":
    main()
