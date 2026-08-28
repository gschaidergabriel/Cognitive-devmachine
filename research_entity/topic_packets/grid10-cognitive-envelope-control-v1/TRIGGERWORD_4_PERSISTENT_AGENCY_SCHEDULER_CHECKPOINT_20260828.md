# Triggerword 4 — Persistent Agency / Scheduler checkpoint

Date: 2026-08-28
Trigger lane: `chatgpt/grid10-cognitive-envelope-control-20260828`
Evidence class: `CURRENT_SOURCE` + `NEGATIVE_RESULT`
Runtime promotion: **NOT GRANTED**

## Routing / authority

This checkpoint belongs to exact Triggerword-4 continuation and is subordinate to the current Triggerword-4 runtime, Frankenstein-2 assembly, sparse-world-substrate, and later binding/addendum directives on this branch. It does not replace those directives.

Current product/effect invariants remain unchanged: deterministic durable state/evidence remains authoritative; model/GRID cognition remains candidate/projection; real external effects remain behind the canonical effect authority.

## Durable source delta observed in this continuation

1. `tools/grid10_persistent_agency_v1.py`
   - persistent `GoalContract` state;
   - generation-CAS guarded goal transitions;
   - deferred intents with exact time/event wake conditions;
   - stale deferred intent rejection;
   - continuation checkpoint;
   - durable next-tick scheduling;
   - append-only agency events.

2. `tools/test_grid10_persistent_agency_v1.py`
   - restart persistence;
   - stale generation rejection;
   - illegal terminal transition rejection;
   - `HOLD/DORMANT -> WAKE -> ACTIVE` across process/session re-open;
   - stale intent cannot revive a changed goal;
   - exact event matching.

3. `tools/grid10_persistent_scheduler_v1.py`
   - adapter over the existing shared-UnifiedDB runtime, not a second state authority;
   - persistent due-time scheduling;
   - event wake evaluation before scheduled due-time;
   - idle/HOLD backoff;
   - bounded cycles and a `--forever` control-loop entry point;
   - no external-effect execution.

4. `tools/test_grid10_persistent_scheduler_v1.py`
   - restart respects persisted due-time;
   - idle state does not manufacture an active user goal;
   - exact material event can wake a deferred goal before a later idle poll;
   - missing trusted semantic axes stays fail-closed in HOLD cadence.

5. Unified-runtime convergence advanced concurrently on this branch through v2/v3/v4. Current v4 source couples:
   `due/wake -> heartbeat -> continuation checkpoint -> next-tick schedule`
   inside the same SQLite/WAL authority with an AgencyState-epoch CAS and `grid10_cognitive_cycles` receipt rows.

6. `.github/workflows/grid10-cognitive-envelope-ci.yml` was extended to compile/test the persistent-agency/scheduler and current unified-runtime files and to smoke the shared SQLite authority.

## Exact commits from this continuation

- `a247745d0b76357bd233ad433aec0de9004213ea` — persistent agency source
- `6d70308655624f1054e8c3c2f9fdd4f4b9ce8f66` — agency tests
- `0ef0b4ad801b4a0b5d3d44a445abbd873f18ee6d` — integrated HOLD/WAKE/restart test in unified runtime v2
- `99361917233a167952bcfad509d5406482c256ea` — persistent scheduler source
- `a2b7c38cab54b66372f3eb79e2b7f676f696020b` — persistent scheduler tests
- `25e41039bcd7090689310f8d1159b8bd4a6066ee` — CI inclusion for persistent scheduler/runtime tests

Parallel commits continued to move the branch after these writes; therefore this receipt intentionally identifies the individual commits and current files rather than asserting that one earlier head stayed current.

## Evidence boundary / negative result

`GitHub.fetch_commit_workflow_runs` for commit `25e41039bcd7090689310f8d1159b8bd4a6066ee` returned **zero workflow runs** in this continuation. The latest observed branch-head checks were global Research Entity workflows, not a successful execution of `GRID10 Cognitive Envelope CI`.

Therefore:

- source-ready credit: **YES, bounded to the files above**;
- exact committed GRID10 CI PASS: **NO OBSERVED EVIDENCE**;
- VPS/runtime PASS: **NO**;
- physical GRID10 PASS: **NO**;
- Frankenstein-2 VPS assembly acceptance: **NOT ENTERED / NOT PROMOTED**;
- whole EntityOS/HCU runtime credit: **0**.

The absence of a workflow run is an infrastructure/evidence gap, not a scientific negative about the runtime logic.

## Current convergence issue

The branch contains successive unified-runtime v2/v3/v4 layers plus the persistent scheduler adapter. They must converge on **one canonical runtime entry point** before VPS assembly; retaining source donors/tests is acceptable, but production assembly must not create competing scheduler/state authorities.

## Next exact acceptance gate

1. select/fuse the single unified runtime entry point, preserving the strongest v4 AgencyState-epoch CAS plus the persistent scheduler/restart/wake tests;
2. execute that exact source identity on an currently authorized zero-cost execution surface under current supervisor guards;
3. capture source SHA / runtime identity / same-UnifiedDB fingerprint / process-restart / persisted goal / HOLD / exact WAKE / resumed heartbeat / next-tick receipt;
4. replace trusted semantic test fixtures with the real Research-Entity/GRID10 evidence path;
5. only after this persistent cognitive-runtime gate is admitted, continue the Triggerword-4 stage order toward the isolated Frankenstein-2 copy.

No claim in this checkpoint promotes source inspection, local candidate tests, workflow definition, or model output into runtime acceptance.
