# Live swarm refusion addendum — FRANK v0.1 F6 + H1 recurrence + measured VPS

Parent report: `FINAL_REPORT.md` in this run directory.  
Actor writing addendum: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent remains: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Date: 2026-08-09  
Promotion: none; scoped implementation/test evidence only.

## Why this addendum exists

While the parent FRANK research/build/test cycle was still active, sibling FRANK workers committed additional current-main deltas. The worker re-read `main` rather than treating its earlier snapshot as exclusive truth. Those deltas were fused before the final handoff, and the VPS telemetry gate was layered on the new live head rather than overwriting sibling work.

## Concurrent delta A — bounded local backend timing receipts

Sibling commit: `02e19765b6784d1ebb6203ce7897073b72b6d18d` (`feat(model): admit bounded local backend timing receipts`).

This change is compatible with the F6 tool-transport delta from the parent report. It adds an explicit numerical allowlist for backend `timings` observations, rejects invalid/non-finite/negative/unlisted values, preserves tool calls and visible usage, and keeps hidden reasoning/unlisted backend text out of durable output. A deterministic loopback regression verifies the tool schema, tool policy, returned tool call and admitted timing fields together.

Fusion consequence: the useful boundary is now not merely `request -> response`; it is:

`typed request + tools -> local backend -> visible proposal/tool call + bounded admitted operational metrics -> external FRANK authority/effect boundary`.

Timing observations are evidence, not authority.

## Concurrent delta B — separated adaptive recurrence policy

Sibling commits:

- `568c3528463ae9b1c61d1981845b9d1a4f2fafc2` — proposal-only adaptive recurrence policy layer;
- `3ee149ab44cd544c18ded02d24b41b9b29fcf2d1` — frozen differential comparing raw diagnostic exit, separated policy and fixed budget;
- `f0f2820fa3ea81a89bfcfb31bfdf779e6796028d` — policy differential added to standard pytest gate;
- `d18595cf862330029c0baaa0e5e4b128218fa6da` — real self-hosted Ubuntu execution receipt for the synthetic workload.

The diagnostic readout is not rewritten. The policy can only continue observation for a narrow pre-window case when:

- the diagnostic would route for material single-axis growth before the observation window;
- evidence quality is valid;
- trajectory is bounded;
- recent net utility remains positive;
- observation budget remains.

It remains `PROPOSAL_ONLY`.

### Frozen synthetic differential

Eight deterministic episodes:

| metric | raw diagnostic exit | separated policy | fixed budget |
|---|---:|---:|---:|
| accuracy | 0.75 | 0.75 | 0.625 |
| false halts | 2 | 0 | 0 |
| correct-to-wrong drift | 0 | 0 | 1 |
| total regret | 0.64 | 0.52 | 1.38 |
| total cost | 1.63 | 1.91 | 2.21 |
| total recurrences | 38 | 45 | 52 |

Interpretation:

- the candidate spends 0.28 extra synthetic cost / 7 recurrences versus the raw diagnostic policy;
- on this frozen fixture it eliminates both premature-route false halts and lowers regret by 0.12;
- it still costs less and recurs less than fixed-budget execution;
- the evidence class remains `REAL_SELF_HOSTED_UBUNTU_EXECUTION_SYNTHETIC_WORKLOAD`, not real-model or user-task evidence;
- no consciousness/emergence claim follows.

Open falsifier: replay a frozen real-Qwen-class-4B task suite and show that the extra observation window does not improve or worsens utility/error/cost/tail latency, or causes new overthinking/drift.

## New measurement layer added by this worker

Commit: `36643a720d2416e79b447bc55ef629eed40d3578` (`ci(vps): measure gate durations and host resource baseline`).

The existing self-hosted deep-integrity workflow now preserves its PASS/FAIL TSV but additionally records:

- per-gate wall-clock duration in milliseconds;
- matrix wall-clock duration;
- sum of gate wall times;
- logical CPU count;
- total host RAM;
- root working-filesystem total/used/free bytes;
- Linux 1/5/15-minute load average;
- explicit scope warning that these are host baseline + wall times, not per-process peak RSS, energy or real-model hardware telemetry.

This was intentionally added after re-reading current `main`, so it coexists with the sibling timing-metric and recurrence-policy changes.

## Final real Ubuntu deep-integrity execution

The measurement workflow ultimately executed exact FRANK commit:

`f0f2820fa3ea81a89bfcfb31bfdf779e6796028d`

Environment:

- evidence class: `REAL_SELF_HOSTED_UBUNTU_EXECUTION`;
- host: `digital-retina`;
- runner: `clay`;
- user: `frankrunner`;
- OS/platform: Linux 6.8.0-117-generic x86_64 / glibc 2.39;
- Python: 3.12.3;
- logical CPUs: 4;
- total RAM: 16,376,020 KiB (~15.62 GiB);
- filesystem total: 206,900,281,344 B (~192.69 GiB);
- filesystem used: 36,643,241,984 B (~34.13 GiB);
- filesystem free: 170,240,262,144 B (~158.56 GiB);
- load average 1/5/15: 0.4927 / 0.2471 / 0.1333.

Matrix result:

- gates: 20;
- pass: 20;
- fail: 0;
- matrix elapsed: 8,290 ms;
- sum of measured gate wall times: 8,082 ms;
- non-gate harness/receipt overhead inside matrix window: ~208 ms;
- release claim: false;
- whole FRANK release status: `NOT_CLAIMED`.

### Per-gate timings

| gate | ms | result |
|---|---:|---|
| compile_python | 150 | PASS |
| repo_static_integrity | 37 | PASS |
| transaction_census | 50 | PASS |
| transaction_replay | 106 | PASS |
| deep_integrity_v11 | 711 | PASS |
| schema_migration_atomicity | 67 | PASS |
| device_probe_state_gate | 57 | PASS |
| causal_reentry_contract | 92 | PASS |
| adaptive_recurrence_differential | 94 | PASS |
| legacy_module_conservation | 79 | PASS |
| legacy_successor_lesion_rescue | 107 | PASS |
| historical_74_gate | 53 | PASS |
| historical_74_accounting | 49 | PASS |
| historical_71_db_gate | 75 | PASS |
| local_model_baseline | 863 | PASS |
| local_model_endpoint_boundary | 2,111 | PASS |
| local_model_tool_metrics | 609 | PASS |
| session_skill_status | 367 | PASS |
| pytest_bootstrap | 1,989 | PASS |
| pytest_all | 416 | PASS |

Observed gate-time shares of the 8,082 ms gate sum:

- endpoint-boundary: ~26.1%;
- pytest bootstrap: ~24.6%;
- local-model baseline: ~10.7%;
- deep-integrity v11: ~8.8%;
- local-model tool metrics: ~7.5%;
- all remaining gates combined: ~22.3%.

The two largest costs are currently test infrastructure/network/socket boundary work and temporary pytest installation, not known FRANK cognitive-runtime work. Therefore these timings must not be misreported as end-user inference latency.

## Third fusion — combined architecture implication

The live evidence supports a clearer separation of four planes:

1. **diagnostic plane** — bounded, replayable readouts about trajectory/recurrence/state;
2. **policy plane** — proposal-only decisions such as whether to continue observing;
3. **model plane** — local model receives typed context/tool schemas and returns non-authoritative proposals/tool calls plus bounded operational metrics;
4. **effect plane** — capability/authority validation, execution, effect receipt and re-entry remain external to model and proposal layers.

This separation prevents three dangerous conflations:

- observation != decision;
- decision proposal != execution authority;
- backend metric != cognitive truth.

It also makes future ablations more discriminating: one can lesion or swap the recurrence policy without changing the diagnostic readout, swap model/runtime/template without changing effect authority, and compare timing/quality separately.

## Measurement gaps still open

The request for exact measurement is only partially satisfiable until a real target model and final target machine are available. Current receipts do **not** yet contain:

- real Qwen-class 4B first-token latency;
- prompt/prediction tokens per second from actual target model execution;
- exact model/quantization/template/runtime identity;
- per-process peak RSS / PSS;
- GPU/VRAM utilization;
- energy/power/thermals;
- long-context KV-cache growth;
- real tool-selection precision/recall/argument validity;
- Andreas-PC end-to-end latency and recovery behavior.

The sibling backend-metric allowlist means some llama.cpp-style timing fields can now be safely admitted when such a real backend runs. The VPS host baseline added here supplies the surrounding measurement substrate, but synthetic loopback timing values are not substituted for real model measurements.

## Updated highest-information next experiment

After target hardware capability census is available:

1. pin exact Qwen-class 4B weights revision;
2. pin quantization hash;
3. pin local runtime commit;
4. pin chat/tool template identity;
5. run matched tool/no-tool and recurrence-policy/raw-diagnostic suites;
6. collect first-token latency, prompt tok/s, generation tok/s, request total latency, peak RAM/VRAM, KV growth and failure/recovery traces;
7. measure tool selection precision/recall, JSON/schema/argument validity, false-call/no-call correctness;
8. compare recurrence separated-policy vs raw diagnostic on real tasks for accuracy, regret proxy, cost, recurrences, tail latency, overthinking/drift;
9. never execute model-proposed tools during model-selection scoring;
10. only after model behavior is accepted, test authorized effects through FRANK's external capability boundary.

## Addendum disposition

- F6 tool transport: scoped implementation supported by real Ubuntu integrity execution.
- F6 bounded backend metrics: sibling delta fused; regression executed on Ubuntu, real-model timing still open.
- H1 separated recurrence policy: synthetic frozen differential supported and VPS executed; real-model/generalization remains open.
- measured VPS integrity matrix: 20/20 PASS with per-gate timing and host baseline.
- final FRANK release: NOT CLAIMED.
- final Andreas-PC acceptance: OPEN.
