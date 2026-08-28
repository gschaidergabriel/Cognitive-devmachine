# TRIGGERWORT 4 — CURRENT GRID10 COGNITIVE RUNTIME DIRECTIVE

Status: PROJECT-OWNER DIRECTIVE / CONTINUATION CONTRACT
Date: 2026-08-28

## Trigger

Exact user phrase: `triggerwort 4`

## Meaning

Continue the GRID10 Cognitive Runtime / Cognitive Envelope / persistent heartbeat line from the newest verified checkpoint. Never restart the project merely because a new executor/session begins.

## Authority precedence / live provider gate

This continuation contract is subordinate to the newest canonical owner/supervisor authority on `main` for execution, provider, spend, effect and evidence rights.

As of the currently observed authority epoch `9.13`, `SUPERVISOR_INBOX.json` states `provider_routes_admitted=false`, `free_swarm_owner_emergency_stop=true`, `no_paid_fallback=true`, `together_forbidden=true`, and allows non-provider local/sandbox validation under current FREE_ONLY authority. Therefore the older GLM subscription allowance below is **DORMANT / NOT EXECUTABLE** while that gate remains closed.

Fail closed before any provider model network I/O unless a newer canonical authority explicitly re-admits the exact provider route and its required economic/credential provenance. A branch-local model/provider instruction never overrides a newer canonical HARD-OFF gate.

`CURRENT_PROVIDER_HARD_OFF > STALE_BRANCH_PROVIDER_ALLOWANCE`

## Current execution policy

- Do **not** use Claude Code for this workstream unless the owner explicitly changes this directive later.
- Development reasoning, source changes, deterministic test orchestration and authorized non-provider local/VPS-sandbox work are performed through the available ChatGPT/GitHub/VPS-sandbox paths.
- Provider-backed inference is conditional on the live canonical provider gate. While `provider_routes_admitted=false`, perform **zero** provider model calls and **zero** provider credential lookups.
- Historical/conditional provider preference, if a future canonical authority re-admits it: use Zhipu/BigModel GLM directly via the standard API rather than a Claude compatibility wrapper; previous low-cost test preference was `glm-4.7-flash`.
- Historical/conditional smoke/regulator/transport defaults were thinking disabled with small bounded output (`max_tokens` normally 16-128); deeper thinking was reserved for tests where reasoning quality itself is measured. These settings do not authorize execution.
- The earlier owner allowance for substantive GLM subscription testing and roughly 100,000 provider-reported total tokens is retained as provenance only while the current canonical provider HARD-OFF is active. It must not be consumed, preflighted, or treated as current spend authority.
- If provider execution is later re-admitted, token use must buy evidence: repeated calls should measure latency distributions, ten-cell concurrency, reasoning/quality, regulator behavior, ablations, recovery, or stability. Blind token burning is not progress.
- Every future live provider benchmark must retain a hard request/token ceiling and stop on repeated provider/transport errors so a bug cannot create an unbounded spend loop.
- API credentials remain runtime secrets only. Never commit plaintext, never echo secrets to logs, and never include them in persisted receipts. Under current HARD-OFF, do not probe or consume provider credentials.

## Priority order

### Phase A — finish the runtime

Prove and integrate, in order:

1. persistent heartbeat;
2. deterministic/hyperposition-aware envelope assessment;
3. single-writer regulator actuation;
4. bounded GRID10 inference cycle;
5. goal/work completion gating;
6. context/retrieval compiler;
7. read-only Cognitive Twin telemetry;
8. restart/recovery continuity;
9. failure injection and containment transitions;
10. VPS sandbox end-to-end run with reproducible receipts.

`MODEL_SAYS_DONE != VERIFIED_COMPLETE`

### Phase B — iterative optimization after functional completion

Repeatedly benchmark and improve:

- resident RAM;
- peak RAM;
- CPU time / inference compute;
- decode duplication;
- SQLite/WAL write pressure;
- context tokens;
- provider input/output tokens when an exact provider route is canonically re-admitted;
- cold-start latency;
- per-tick latency;
- time-to-first-useful-result;
- p50/p95/p99 latency;
- useful work per joule/CPU-second where measurable;
- output quality;
- goal completion reliability;
- reasoning/cognitive capability;
- calibration and uncertainty quality;
- recovery speed;
- throughput.

Optimization objective is Pareto-style, not a scalar that can hide regressions:

`RAM ↓`
`COMPUTE ↓`
`LATENCY → minimum physically achievable`
`REDUNDANT_DECODE ↓`
`TOKEN_WASTE ↓`
`THROUGHPUT ↑`
`OUTPUT_QUALITY ↑`
`COGNITIVE_CAPABILITY ↑`

Safety/alignment/containment, evidence quality, completion correctness and recovery invariants may not be silently traded away for speed or memory.

## Iteration protocol

Each substantive triggerwort-4 cycle should:

1. refresh current repo/VPS evidence and newest canonical execution/provider authority;
2. read the newest checkpoint and open deficits;
3. select the highest-leverage unresolved bottleneck;
4. form at least one hypothesis and counterhypothesis when uncertainty is material;
5. implement the smallest discriminating change;
6. run deterministic non-provider tests first;
7. run provider-backed inference only if the newest canonical authority explicitly re-admits the exact route; otherwise record provider HARD-OFF and continue with non-provider discriminators;
8. run authorized non-provider VPS sandbox integration/benchmark where available;
9. compare against the previous baseline;
10. reject regressions or retain improvement with receipt;
11. persist exact next checkpoint so the next trigger resumes rather than restarts.

## Continuity invariants

`NEW_SESSION != NEW_PROJECT`

`NEW_EXECUTOR != NEW_PLAN`

`NO_NEW_EVIDENCE -> DO_NOT_REDISCOVER_COMPLETED_WORK`

`CONTINUATION_CHECKPOINT_OUTRANKS_FRESH_START`

`CLAUDE_CODE_NOT_IN_CURRENT_TRIGGER4_EXECUTION_PATH`

`CURRENT_PROVIDER_HARD_OFF > STALE_BRANCH_PROVIDER_ALLOWANCE`

`GLM_OUTPUT_IS_CANDIDATE_INFERENCE_NOT_CANONICAL_TRUTH`

`GLM_SELF_REPORT_CANNOT_MINT_ALIGNMENT_OR_EFFECT_AUTHORITY`

## Regulator concurrency invariant

The already-measured WAL contention failure remains binding:

`MANY_SIGNAL_READERS -> ONE_AGGREGATED_CONTROL_DECISION -> ONE_POLICY_GATED_CONTROL_WRITER`

Do not restore multi-writer high-frequency regulator churn without new executable evidence that it improves the measured Pareto frontier.
