"""
Frankenstein Bauleiter loop (72h autonomous build, step 1 of
BUILD_ORCHESTRATION_PLAN_20260827.json). Written directly by the coordinator,
NOT delegated to the free-pool harness -- two prior attempts
(f3b2e48 nvidia-nemotron, 045f8cb mistral-small) both produced only a
PROVENANCE.json, no real script content, on a task this size. Per Gabriel's
explicit sequencing instruction, this first working version must be authored
and accepted by the coordinator personally before any swarm "perfection" pass
or actual 72h start.

Scope: implements BUILD_ORCHESTRATION_PLAN steps 1-3 (Bauleiter continuity,
helper dispatch, sandbox/artifacts). Deliberately does NOT implement step 0
(the backup -- already run separately, streamed VPS->andreas-MACO) and does
NOT ever call the Together training API (step 4) -- see
TRAINING_RUN_READY_FOR_LAUNCH handling in bauleiter_supervisor_loop().

Reuses real, already-proven building blocks rather than reinventing them:
  - tools/grid10_fabric.py's Fabric/result_packet/summary_packet for
    persistent structured build state (same SQLite/WAL/CAS pattern as every
    GRID10 experiment this session).
  - ~/last-resort/llm.py's TIERS/_tiers() for the free-pool cascade -- but
    NOTE: the public chat()/chat_stream() always cascades Groq-first with no
    way to force a specific tier, so call_specific_tier() below reuses only
    the internal _tiers()/key-list machinery and does its own single-tier
    HTTP call, so the Bauleiter can deliberately request the strongest tier
    (nvidia / Nemotron-3-super) instead of the cascade's normal default.
  - ~/.claude/star/harness_aider.py's real `fallback-start` CLI (verified via
    --help) for dispatching well-scoped helper subtasks.
  - frankenstein_packages_v1.py's phase/package dispenser -- Gabriel's
    explicit correction (2026-08-27): the 72h task must NEVER be handed to a
    free-pool helper model as one giant continuous auftrag (limited context
    windows). This orchestrator's main work loop now claims ONE
    self-contained package at a time from that dispenser and dispatches
    ONLY that package's own description -- never the accumulated 72h
    history -- to the helper model. The dispenser is its own, separately
    and thoroughly tested module (tests/test_frankenstein_packages_v1.py,
    12/12 passing) precisely because Gabriel named it as the part the whole
    72h run structurally depends on and required it be one of the most
    robust parts of the system.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, os.path.expanduser("~/last-resort"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grid10_fabric import Fabric, FabricError, result_packet, summary_packet  # noqa: E402
import frankenstein_packages_v1 as packages  # noqa: E402
import frankenstein_training_gate_v1 as training_gate  # noqa: E402
import llm as pool_llm  # noqa: E402

import requests  # noqa: E402

BUILD_SCOPE = "frankenstein:build_state"
PRIMARY_TIER = "nvidia"  # Nemotron-3-super-120b-a12b -- llm.py's own documented
                          # "stronger reasoner for hard problems" tier.
BAULEITER_NODE_ID = "frankenstein-bauleiter"
HARNESS_PATH = os.path.expanduser("~/.claude/star/harness_aider.py")


class TierUnavailable(RuntimeError):
    pass


def call_specific_tier(tier_label: str, messages: list[dict], *, max_tokens: int = 2000,
                        temperature: float = 0.3, timeout: float | None = None) -> str:
    """Calls exactly ONE named tier from ~/last-resort/llm.py's real cascade
    (walks that tier's own api_keys list, same retry-across-keys behavior as
    chat_stream(), just scoped to a single tier rather than the whole
    cascade). Non-streaming (stream=False) -- callers here only need the
    final text, not live deltas. Raises TierUnavailable if every key for
    that tier fails or the tier has no configured key at all."""
    for label, url, model, api_keys in pool_llm._tiers():
        if label != tier_label:
            continue
        last_err = None
        for idx, key in enumerate(api_keys):
            try:
                r = requests.post(
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
                if r.status_code == 429 or r.status_code >= 500:
                    last_err = f"key#{idx+1}: HTTP {r.status_code}"
                    continue
                if r.status_code != 200:
                    last_err = f"key#{idx+1}: HTTP {r.status_code} {r.text[:200]}"
                    continue
                data = r.json()
                choices = data.get("choices") or []
                if not choices:
                    last_err = f"key#{idx+1}: no choices in response"
                    continue
                content = (choices[0].get("message") or {}).get("content")
                if not content:
                    last_err = f"key#{idx+1}: empty content"
                    continue
                return content
            except requests.RequestException as e:
                last_err = f"key#{idx+1}: {e}"
                continue
        raise TierUnavailable(f"{tier_label}: every key failed, last error: {last_err}")
    raise TierUnavailable(f"{tier_label}: no configured key for this tier")


def continuation_opening_message(continuation_context: str | None) -> str:
    """Builds the framing text sent as the FIRST message to a fresh Bauleiter
    instance. If continuation_context is given, frames it as genuine
    continuity of the instance's OWN prior work (modeled directly on how
    this very orchestrator was itself written -- as a continuation of a
    summarized prior session, not a cold handoff to a stranger)."""
    if not continuation_context:
        return (
            "You are Frankenstein's Bauleiter -- the persistent foreman driving a "
            "72-hour autonomous build. This is your first activation. Read "
            "CONCEPT.md and BUILD_ORCHESTRATION_PLAN_20260827.json in "
            "research_entity/topic_packets/frankenstein-master-cognition-concept/ "
            "for full context, then begin working through the build in real, "
            "verifiable steps."
        )
    return (
        "You are continuing your own prior work, not reading a summary of "
        "someone else's work. A previous activation of you (the same "
        "Bauleiter, same role, same responsibility) reached a checkpoint and "
        "wrote the following account of where things stand, in your own "
        "words, so that you would not lose the thread. Read it as your own "
        "memory of what you were just doing, and continue exactly from "
        "there -- do not restart, do not re-derive decisions already made, "
        "do not treat this as someone else's report:\n\n"
        f"{continuation_context}\n\n"
        "Continue the build from this point."
    )


def _log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {line}\n")


FILE_BLOCK_RE = None  # set lazily in parse_file_blocks() to avoid importing re at module load if unused


def parse_file_blocks(response_text: str) -> dict[str, str]:
    """Parses 'FILE: <path>\\n```lang\\n<content>\\n```' blocks out of a
    direct-dispatch model response into {relative_path: full_content}. Pure
    string processing, no exotic dependency -- deliberately simple and
    testable in isolation."""
    import re
    pattern = re.compile(r"FILE:\s*(\S+)\s*\n```[a-zA-Z0-9_+-]*\n(.*?)\n```", re.DOTALL)
    return {m.group(1).strip(): m.group(2) for m in pattern.finditer(response_text)}


def apply_file_blocks(repo_root: Path, blocks: dict[str, str]) -> list[Path]:
    written = []
    for rel_path, content in blocks.items():
        full = (repo_root / rel_path).resolve()
        if repo_root.resolve() not in full.parents and full != repo_root.resolve():
            raise ValueError(f"refusing to write outside repo_root: {rel_path}")
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        written.append(full)
    return written


def dispatch_helper_task_direct(task_description: str, acceptance_criteria: str, repo_root: Path,
                                 log_path: Path, tier: str = PRIMARY_TIER, max_retries: int = 2) -> dict:
    """Portable fallback used when harness_aider.py (a coordinator-local
    tool, not part of this repo) is not present in the current environment
    -- e.g. on a fresh VPS deployment. Asks a single free-pool model call to
    write the complete content of every file the package needs, applies it,
    runs the package's own acceptance_criteria command as a real
    verify-before-commit gate, and reverts cleanly (restores prior file
    content, or deletes newly-created files) if verification fails -- never
    leaves a broken, half-applied state committed."""
    prompt = (
        "You are a focused coding helper working on ONE small, self-contained "
        "task. Implement EXACTLY this, nothing more:\n\n" + task_description +
        "\n\nRespond with one or more blocks, one per file you create or "
        "modify, in EXACTLY this format (paths relative to the repository "
        "root):\n\nFILE: path/to/file.py\n```python\n<complete file content>\n```"
        "\n\nWrite the COMPLETE content of each file (not a diff/patch). No "
        "prose outside the FILE blocks."
    )
    for attempt in range(1, max_retries + 1):
        try:
            response = call_specific_tier(tier, [{"role": "user", "content": prompt}], max_tokens=4000)
        except TierUnavailable as e:
            _log(log_path, f"DIRECT_DISPATCH_TIER_UNAVAILABLE attempt={attempt} {e}")
            continue
        blocks = parse_file_blocks(response)
        if not blocks:
            _log(log_path, f"DIRECT_DISPATCH_NO_FILE_BLOCKS attempt={attempt}")
            continue
        touched = {rel: ((repo_root / rel).read_text() if (repo_root / rel).exists() else None)
                   for rel in blocks}
        try:
            apply_file_blocks(repo_root, blocks)
        except ValueError as e:
            _log(log_path, f"DIRECT_DISPATCH_REJECTED_UNSAFE_PATH attempt={attempt} {e}")
            continue
        verify = subprocess.run(acceptance_criteria, shell=True, cwd=str(repo_root),
                                 capture_output=True, text=True, timeout=300)
        if verify.returncode == 0:
            subprocess.run(["git", "-C", str(repo_root), "add", *blocks.keys()], check=False)
            subprocess.run(["git", "-C", str(repo_root), "commit", "-m",
                             f"frankenstein-bauleiter(direct-dispatch): {task_description[:72]}"],
                            check=False)
            _log(log_path, f"DIRECT_DISPATCH_SUCCESS attempt={attempt} files={list(blocks.keys())}")
            return {"ok": True, "files": list(blocks.keys()), "attempt": attempt}
        for rel, old in touched.items():
            p = repo_root / rel
            if old is None and p.exists():
                p.unlink()
            elif old is not None:
                p.write_text(old)
        _log(log_path, f"DIRECT_DISPATCH_VERIFY_FAILED attempt={attempt} "
                        f"stderr={verify.stderr[-500:]}")
    return {"ok": False, "reason": "direct-dispatch exhausted retries with no verified change"}


def dispatch_helper_task(task_description: str, reason: str, log_path: Path,
                          max_retries: int = 4, acceptance_criteria: str | None = None,
                          repo_root: Path | None = None) -> dict:
    """Shells out to the real harness_aider.py fallback-start CLI (verified
    via --help: --auftrag, --kandidaten, --grund) to dispatch a well-scoped
    helper subtask to the free-pool cascade. Backs off exponentially on
    real rate-limit signals surfaced in stdout/stderr rather than hammering
    a rate-limited provider.

    harness_aider.py is a coordinator-local tool (lives under
    ~/.claude/star/, not part of this git repo), so it will not exist on a
    fresh deployment (e.g. a VPS). When it is missing, this function falls
    back to dispatch_helper_task_direct() (needs acceptance_criteria +
    repo_root) instead of retrying a call that can never succeed."""
    if not os.path.isfile(HARNESS_PATH):
        if acceptance_criteria and repo_root:
            _log(log_path, f"HARNESS_AIDER_NOT_PRESENT falling back to direct dispatch: {HARNESS_PATH}")
            return dispatch_helper_task_direct(task_description, acceptance_criteria, repo_root, log_path)
        _log(log_path, f"HARNESS_AIDER_NOT_PRESENT no acceptance_criteria/repo_root given, cannot fall back")
        return {"ok": False, "reason": f"harness_aider.py not present at {HARNESS_PATH} and no direct-dispatch fallback params given"}

    delay = 5.0
    last_result = None
    for attempt in range(1, max_retries + 1):
        try:
            proc = subprocess.run(
                [sys.executable, HARNESS_PATH, "fallback-start",
                 "--auftrag", task_description, "--grund", reason],
                capture_output=True, text=True, timeout=900,
            )
            combined = (proc.stdout or "") + (proc.stderr or "")
            rate_limited = any(tok in combined for tok in (
                "RateLimitError", "429", "rate limit", "rate_limit",
            ))
            last_result = {
                "attempt": attempt, "returncode": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-2000:],
                "stderr_tail": (proc.stderr or "")[-2000:],
                "rate_limited": rate_limited,
            }
            _log(log_path, f"HELPER_DISPATCH attempt={attempt} rc={proc.returncode} "
                            f"rate_limited={rate_limited} task={task_description[:120]!r}")
            if proc.returncode == 0 and not rate_limited:
                return {"ok": True, **last_result}
            if not rate_limited:
                # Real (non-rate-limit) failure -- do not keep retrying blindly,
                # report it honestly instead of pretending it worked.
                return {"ok": False, **last_result}
        except subprocess.TimeoutExpired:
            last_result = {"attempt": attempt, "returncode": None, "timeout": True}
            _log(log_path, f"HELPER_DISPATCH attempt={attempt} TIMEOUT task={task_description[:120]!r}")
        time.sleep(delay)
        delay = min(delay * 2, 300.0)
    return {"ok": False, "exhausted_retries": True, **(last_result or {})}


def _ensure_scope(fabric: Fabric) -> None:
    """Seeds BUILD_SCOPE only if it does not already exist -- seed_scope()
    unconditionally resets summary_json/evidence_count/last_writer, so
    calling it on every respawn would silently destroy the very continuity
    this whole mechanism exists to preserve."""
    snap = fabric.snapshot()
    if not any(s["scope"] == BUILD_SCOPE for s in snap.scopes):
        fabric.seed_scope(BUILD_SCOPE)


def record_build_event(fabric: Fabric, node_id: str, payload: dict, log_path: Path) -> dict:
    """Real, honest state commit: join the fabric, elect self as the (sole)
    coordinator for BUILD_SCOPE if not already elected this call, emit a
    result packet, drain+commit it into canonical state. Returns the commit
    delta dict, or a dict with 'error' if the commit failed (never silently
    swallowed)."""
    try:
        fabric.runtime_join(node_id, "frankenstein-bauleiter", os.getpid())
        fabric.runtime_heartbeat(node_id, healthy=True)
        elected = fabric.elect_coordinator(BUILD_SCOPE, candidate_node_ids=[node_id])
        if elected is None:
            # Someone (very likely a prior un-expired lease from an earlier
            # respawn of THIS SAME role) already holds it -- that is fine and
            # expected across respawns; just proceed, the drain below still
            # works via whichever valid lease is on record as long as it is
            # ours. If it truly is not ours (another actor), the commit
            # below will raise and we report that honestly rather than
            # silently pretending success.
            snap = fabric.snapshot()
            lease_row = next((l for l in snap.leases if l["scope"] == BUILD_SCOPE and l["valid"]), None)
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
    except FabricError as e:
        _log(log_path, f"BUILD_STATE_ERROR {e}")
        return {"error": str(e)}


def write_continuation_summary(fabric: Fabric, node_id: str, actions_log: list[str],
                                sandbox_dir: Path, ended_reason: str) -> Path:
    """Asks the model (same PRIMARY_TIER) to write a genuine narrative
    summary of this instance's own session -- not a hardcoded template --
    covering what was worked on, what was just decided, what's mid-flight,
    what to do next. Falls back to a plain, honestly-labeled non-LLM summary
    if the model call itself fails, rather than losing continuity entirely."""
    actions_text = "\n".join(f"- {a}" for a in actions_log) or "(no actions recorded this instance)"
    prompt = (
        "You are the Frankenstein Bauleiter, about to end this activation "
        f"(reason: {ended_reason}). Below is the real, honest log of actions "
        "you took this session. Write a CONTINUATION_SUMMARY for your own "
        "next activation: what you were working on, what you just decided, "
        "what is currently mid-flight/unfinished, and exactly what to do "
        "next. Write it as your own memory, in first person, so your next "
        "self can pick up seamlessly. Be honest about anything that did not "
        "go as planned.\n\nActions this session:\n" + actions_text
    )
    try:
        narrative = call_specific_tier(PRIMARY_TIER, [{"role": "user", "content": prompt}], max_tokens=1200)
    except TierUnavailable as e:
        narrative = (
            f"[FALLBACK, no LLM available for narrative summary: {e}]\n\n"
            f"Ended reason: {ended_reason}\nRaw action log:\n{actions_text}"
        )
    ts = time.strftime("%Y%m%dT%H%M%S")
    out_path = sandbox_dir / f"CONTINUATION_SUMMARY_{ts}.md"
    out_path.write_text(narrative)
    latest_path = sandbox_dir / "CONTINUATION_SUMMARY.md"
    latest_path.write_text(narrative)
    return latest_path


def run_bauleiter_instance(continuation_context: str | None, fabric_path: str,
                            sandbox_dir: Path, log_path: Path,
                            max_actions: int = 20, max_seconds: float = 1800.0) -> dict:
    """One activation of the Bauleiter. Returns
    {"ended_reason", "continuation_summary_path", "real_actions_taken"}."""
    fabric = Fabric(Path(fabric_path))
    _ensure_scope(fabric)
    opening = continuation_opening_message(continuation_context)
    _log(log_path, f"BAULEITER_ACTIVATED continuation={'yes' if continuation_context else 'no (first activation)'}")

    actions_log: list[str] = [f"Activation opened with: {opening[:200]}..."]
    real_actions_taken = 0
    ended_reason = "checkpoint"
    start = time.time()

    training_marker = sandbox_dir / "TRAINING_RUN_READY_FOR_LAUNCH.json"
    revision_db_path = sandbox_dir / "training_data_revisions.sqlite3"
    example_ids_path = sandbox_dir / "TRAINING_EXAMPLE_IDS.json"

    packages.seed_all_packages(fabric, log_fn=lambda m: _log(log_path, m))

    def _attempt_training_gate() -> None:
        """Gabriel's 2026-08-28 hard precondition (frankenstein_training_gate_v1.py):
        best-effort, non-blocking check every activation -- writing the marker
        is the ONLY thing this can do, gated by real, code-enforced conditions
        (GRID10 fully done OR genuine multi-hour stall, AND every named example
        30x documented-revised). example_ids_path starts absent/empty by
        construction (no fabricated examples), so the gate stays honestly
        closed until real curation work populates it."""
        if training_marker.exists() or not example_ids_path.is_file():
            return
        try:
            example_ids = json.loads(example_ids_path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        try:
            training_gate.attempt_training_run(fabric, revision_db_path, example_ids, training_marker,
                                                log_fn=lambda m: _log(log_path, m))
        except training_gate.TrainingRunBlocked as e:
            _log(log_path, f"TRAINING_GATE_STILL_BLOCKED {e}")

    try:
        while real_actions_taken < max_actions and (time.time() - start) < max_seconds:
            if training_marker.exists():
                ended_reason = "training_marker_present"
                break

            _attempt_training_gate()
            if training_marker.exists():
                ended_reason = "training_marker_present"
                break

            if packages.all_packages_done(fabric):
                ended_reason = "checkpoint"
                actions_log.append("All decomposed packages are DONE -- nothing further to dispatch this activation.")
                break

            # CENTRAL DISPATCH BACKBONE (Gabriel's 2026-08-27 correction): claim
            # exactly ONE small, self-contained package from the dedicated,
            # separately-tested dispenser (frankenstein_packages_v1.py) --
            # never hand a helper model the accumulated 72h history, only
            # this one package's own description.
            claimed = packages.claim_next_package(fabric, BAULEITER_NODE_ID, log_fn=lambda m: _log(log_path, m))
            if claimed is None:
                # Nothing currently claimable: either genuinely all done
                # (handled above) or every remaining package is blocked on
                # an unmet dependency that some other node/attempt must
                # still finish. Not an error -- end this activation cleanly
                # so a respawn (or the dependency-completing work elsewhere)
                # can make progress before the next claim attempt.
                progress = packages.progress_summary(fabric)
                actions_log.append(f"No claimable package right now. Progress: {progress['done']}/{progress['total']} done.")
                ended_reason = "checkpoint"
                break

            record_build_event(fabric, BAULEITER_NODE_ID,
                                {"event": "PACKAGE_DISPATCH_STARTED", "package_id": claimed["task_id"], "ts": time.time()},
                                log_path)
            dispatch_result = dispatch_helper_task(claimed["description"], "frankenstein-bauleiter-package", log_path,
                                                    acceptance_criteria=claimed.get("acceptance_criteria"),
                                                    repo_root=REPO_ROOT)
            ok = bool(dispatch_result.get("ok", False))
            packages.mark_package_done(fabric, claimed["task_id"], ok=ok, node_id=BAULEITER_NODE_ID,
                                        log_fn=lambda m: _log(log_path, m))
            record_build_event(fabric, BAULEITER_NODE_ID,
                                {"event": "PACKAGE_DISPATCH_ENDED", "package_id": claimed["task_id"],
                                 "ok": ok, "ts": time.time()},
                                log_path)
            actions_log.append(f"Package {claimed['task_id']} dispatched -> ok={ok} "
                                f"(acceptance: {claimed['acceptance_criteria']})")
            real_actions_taken += 1
    except Exception as e:  # noqa: BLE001 - must still write a continuation summary on ANY failure
        _log(log_path, f"BAULEITER_EXCEPTION {type(e).__name__}: {e}")
        actions_log.append(f"EXCEPTION ended this activation: {type(e).__name__}: {e}")
        ended_reason = "exception"

    summary_path = write_continuation_summary(fabric, BAULEITER_NODE_ID, actions_log, sandbox_dir, ended_reason)
    return {
        "ended_reason": ended_reason,
        "continuation_summary_path": str(summary_path),
        "real_actions_taken": real_actions_taken,
    }


def bauleiter_supervisor_loop(fabric_path: str, sandbox_dir: Path,
                               max_wallclock_hours: float = 72.0,
                               log_path: Path | None = None) -> None:
    """Top-level respawn loop. Reads the previous instance's continuation
    summary and hands it to the next call. Stops cleanly at the wallclock
    limit or as soon as a TRAINING_RUN_READY_FOR_LAUNCH marker appears --
    this script NEVER calls the Together training API itself (step 4 of the
    plan stays under the coordinator's manual control)."""
    log_path = log_path or (sandbox_dir / "bauleiter_supervisor.log")
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max_wallclock_hours * 3600.0
    continuation_context: str | None = None
    latest_summary = sandbox_dir / "CONTINUATION_SUMMARY.md"
    if latest_summary.exists():
        continuation_context = latest_summary.read_text()
        _log(log_path, "SUPERVISOR_RESUMING_FROM_EXISTING_SUMMARY")

    respawn_count = 0
    while time.time() < deadline:
        _log(log_path, f"SUPERVISOR_SPAWNING_INSTANCE respawn_count={respawn_count}")
        result = run_bauleiter_instance(continuation_context, fabric_path, sandbox_dir, log_path)
        _log(log_path, f"SUPERVISOR_INSTANCE_ENDED {json.dumps(result)}")
        respawn_count += 1
        if result["ended_reason"] == "training_marker_present":
            _log(log_path, "SUPERVISOR_STOPPING: TRAINING_RUN_READY_FOR_LAUNCH marker present, "
                            "handing control back to the coordinator, NOT calling any training API.")
            return
        continuation_context = Path(result["continuation_summary_path"]).read_text()
        time.sleep(2.0)  # brief real pause between respawns, not a tight crash loop
    _log(log_path, f"SUPERVISOR_STOPPING: wallclock limit reached after {respawn_count} respawns")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--fabric-path", default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                                                 "frankenstein-master-cognition-concept" / "build_fabric.sqlite3"))
    p.add_argument("--sandbox-dir", default=str(REPO_ROOT / "research_entity" / "topic_packets" /
                                                 "frankenstein-master-cognition-concept" / "bauleiter_sandbox"))
    p.add_argument("--max-wallclock-hours", type=float, default=72.0)
    p.add_argument("--once", action="store_true", help="run a single instance activation and exit (for acceptance testing)")
    args = p.parse_args()

    sandbox_dir = Path(args.sandbox_dir)
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    log_path = sandbox_dir / "bauleiter_supervisor.log"

    if args.once:
        continuation_context = None
        summary = sandbox_dir / "CONTINUATION_SUMMARY.md"
        if summary.exists():
            continuation_context = summary.read_text()
        result = run_bauleiter_instance(continuation_context, args.fabric_path, sandbox_dir, log_path)
        print(json.dumps(result, indent=2))
        return

    bauleiter_supervisor_loop(args.fabric_path, sandbox_dir, args.max_wallclock_hours, log_path)


if __name__ == "__main__":
    main()
