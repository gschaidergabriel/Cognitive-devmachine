# TRIGGERWORT 4 — CURRENT GRID10 COGNITIVE RUNTIME DIRECTIVE

Status: PROJECT-OWNER DIRECTIVE / CONTINUATION CONTRACT
Date: 2026-08-28

## Trigger

Exact user phrase: `triggerwort 4`

## Meaning

Continue the GRID10 Cognitive Runtime / Cognitive Envelope / persistent heartbeat line from the newest verified checkpoint. Never restart the project merely because a new executor/session begins.

## Current execution policy

- Do **not** use Claude Code for this workstream unless the owner explicitly changes this directive later.
- Development reasoning, source changes, test orchestration and VPS sandbox work are performed through the available ChatGPT/GitHub/VPS-sandbox paths.
- For model-backed inference tests use Zhipu/BigModel GLM directly via the standard API, not through a Claude compatibility wrapper.
- Default low-cost test model: `glm-4.7-flash`.
- Default smoke/regulator/transport tests: thinking disabled; small bounded output (`max_tokens` normally 16-128).
- Enable deeper GLM thinking only for tests where reasoning quality is itself the measured variable.
- API credential is runtime secret only. Read from `ZAI_API_KEY`, `GLM_API_KEY`, or `BIGMODEL_API_KEY`; never commit plaintext, never echo to logs, never include in persisted receipts.

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
- provider input/output tokens;
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

1. refresh current repo/VPS evidence;
2. read the newest checkpoint and open deficits;
3. select the highest-leverage unresolved bottleneck;
4. form at least one hypothesis and counterhypothesis when uncertainty is material;
5. implement the smallest discriminating change;
6. run deterministic tests first;
7. run bounded GLM-4.7-Flash inference only where model behavior is needed;
8. run VPS sandbox integration/benchmark where available;
9. compare against the previous baseline;
10. reject regressions or retain improvement with receipt;
11. persist exact next checkpoint so the next trigger resumes rather than restarts.

## Continuity invariants

`NEW_SESSION != NEW_PROJECT`

`NEW_EXECUTOR != NEW_PLAN`

`NO_NEW_EVIDENCE -> DO_NOT_REDISCOVER_COMPLETED_WORK`

`CONTINUATION_CHECKPOINT_OUTRANKS_FRESH_START`

`CLAUDE_CODE_NOT_IN_CURRENT_TRIGGER4_EXECUTION_PATH`

`GLM_OUTPUT_IS_CANDIDATE_INFERENCE_NOT_CANONICAL_TRUTH`

`GLM_SELF_REPORT_CANNOT_MINT_ALIGNMENT_OR_EFFECT_AUTHORITY`

## Regulator concurrency invariant

The already-measured WAL contention failure remains binding:

`MANY_SIGNAL_READERS -> ONE_AGGREGATED_CONTROL_DECISION -> ONE_POLICY_GATED_CONTROL_WRITER`

Do not restore multi-writer high-frequency regulator churn without new executable evidence that it improves the measured Pareto frontier.
