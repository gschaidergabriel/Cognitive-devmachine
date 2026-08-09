# FRANK — ChatGPT-Led Iterative Mistral Build Cascade

**Status:** PROJECT_OWNER_FIXED_ORCHESTRATION_DIRECTIVE  
**Effective:** 2026-08-09  
**Applies to:** exact `frank` trigger and architecture-led Harness evolution  
**Sole orchestrator:** ChatGPT organ (`chatgpt-secondary`)  
**Worker class:** Mistral API workers plus additional owner-supplied workers  
**Target:** progressively transform the GitHub-based Harness toward the target FRANK architecture for the Qwen-class 4B on Ubuntu

## 0. Sole-orchestrator law

Only the ChatGPT organ coordinates this cascade.

Mistral workers and any later owner-supplied workers are subordinate research/build workers. They do not own global scheduling, architecture adjudication, branch prioritization or promotion.

Compact law:

`ChatGPT -> task -> worker -> proposed code/analysis/test result -> ChatGPT review/fusion -> accepted/rejected/revised delta -> measurement -> next ChatGPT task`

Mistral must never recursively spawn or coordinate other workers under its own authority.

## 1. Worker purpose

Mistral is not restricted to analysis. When tasked by ChatGPT it should produce concrete implementation material such as:

- repository patches/diffs;
- Harness modules;
- state schemas;
- UnifiedDB SQL/migrations/queries;
- ClayGraph projection/update logic;
- GWT instrumentation;
- Hyperposition representation/tests;
- emergence/causal measurement code;
- replay/ablation/fuzz/fault-injection tests;
- target-shaped 4B model adapters;
- benchmark harnesses;
- migration/recovery code;
- code review and counterexamples.

Every build result is a proposal until ChatGPT reviews it against current architecture, evidence, tests and project invariants.

## 2. Iterative cycle

A material `frank` cascade proceeds in repeated rounds:

1. ChatGPT rereads current canonical state, latest research mesh, current Harness, live claims, failures and measurements.
2. ChatGPT performs a cross-domain fusion across FRANK, Harness, ClayCode, UnifiedDB, ClayGraph, GWT, Hyperposition, Emergenz and relevant Retina/Needle/security/recovery evidence.
3. ChatGPT computes the current architecture-to-Harness gap set.
4. ChatGPT assigns narrow high-information work packets to Mistral and any additional owner-supplied workers.
5. Workers return concrete patches/analysis/tests with provenance and explicit assumptions.
6. ChatGPT inspects each result, compares sibling proposals, identifies contradictions and checks target-architecture fidelity.
7. ChatGPT accepts, rejects, edits or combines proposed changes. Worker output is never auto-promoted merely because it compiles.
8. Accepted code is tested with the strongest currently available execution surface.
9. ChatGPT interprets measurements and updates hypotheses/counterhypotheses, architecture gap ranking and worker tasks.
10. Repeat while useful authorized worker capacity remains and the current turn/runtime permits.

A later round must receive the consequences of earlier rounds; repeated identical prompts are not a valid cascade.

## 3. Mandatory research/build lanes

ChatGPT dynamically allocates workers across the highest-value gaps. The active lane set may include:

- FRANK organ/module decomposition and causal boundaries;
- two-instance PC/Repo local-state separation and cross-instance signaling;
- compressed prepared 4B possibility-space / simplified graph projection;
- canonical event/state ledger;
- UnifiedDB semantic identity/dependency/transaction/replay fabric;
- ClayGraph sparse active topology and incremental projection;
- GWT competition/broadcast/reconstruction/uptake/causal-use/re-entry;
- Hyperposition alternatives, higher-order dependencies and dynamic topology;
- Emergenz measurements: lesions, rescue, shuffles, interaction terms, PID/PEID or other justified readouts;
- loop-of-loops dynamics and recurrence control;
- Digital Retina and adaptive Micro Visual Classifier integration;
- Needle bridge;
- self/world/body/goals/value/personality state;
- effect/authority/resource gateway;
- recovery/crash/idempotency/rollback;
- replay and counterfactual execution;
- target 4B model ABI and compressed context projection;
- performance: latency, RAM, context/KV/token cost, update amplification;
- ClayCode H2 equivalence and H3 one-module lowering.

## 4. Worker depth policy

Workers should be given enough context and output budget to perform substantive work rather than superficial summaries.

However the objective is **maximum useful reasoning and implementation per available request**, not artificial token padding.

Each task should demand:

- mechanism-level reasoning;
- concrete repository-grounded implementation;
- explicit falsifiers/counterexamples;
- tests or measurement plan;
- risks and rollback;
- exact files/symbols affected;
- machine-readable patch or structured change proposal where feasible.

## 5. Mistral key pool

Mistral credentials are secret material. Key values must never be placed in prompts, logs, commits, research packets or chat output.

The runtime may select from configured Mistral key references such as `MISTRAL_API_KEY`, `MISTRAL_API_KEY_1`, `MISTRAL_API_KEY_2`, etc. Selection uses only availability/lease/quota metadata and a non-secret key fingerprint.

The preferred key is one that is configured, not currently leased/in-use by this cascade, and not known to be rate/quota blocked.

A key value is loaded only at the provider call boundary.

## 6. Quota/cost law

The owner requests aggressive use of already available Mistral request capacity for the FRANK build cascade.

This directive does **not** authorize automatic purchase, automatic top-up, spending-limit increases or creation of new paid capacity.

The cascade may consume available configured request/token capacity until a provider/workspace/org limit, explicit local budget limit, authorization boundary or useful-work stop is reached.

`429`, spending-limit, quota or provider-throttle responses are recorded and routed; they are not bypassed by credential abuse.

Multiple keys that share one workspace/organization may share effective limits. Key rotation is for available configured capacity and concurrency isolation, not an assumption of independent quota.

## 7. Additional owner-supplied workers

When the owner adds another worker/runtime/model, ChatGPT may assign it tasks inside the same cascade.

Each worker receives:

- stable worker id and provenance;
- explicit task id;
- current architecture context subset;
- required output contract;
- token/request budget if known;
- dependencies and prohibited authority;
- acceptance/falsification criteria.

ChatGPT remains the only global scheduler and adjudicator.

## 8. Cross-domain fusion cadence

ChatGPT must not run long independent worker chains against a stale architecture snapshot.

After every materially informative batch, ChatGPT rereads newly written results and recomputes the cross-domain synthesis before assigning the next batch.

At minimum the fusion checks:

- FRANK target fidelity;
- Harness executable coverage;
- H1 progress and blockers;
- ClayCode expressibility;
- UnifiedDB state/dependency implications;
- ClayGraph topology implications;
- GWT causal-stage implications;
- Hyperposition alternative/coupling implications;
- Emergenz measurement opportunities;
- two-instance state-separation invariants;
- 4B possibility-space/context-cost implications;
- effect authority/safety/recovery;
- performance and resource shadows.

## 9. Promotion rule

A worker patch is not accepted merely because it is plausible.

Promotion requires, as applicable:

- architecture fit;
- no violation of owner-fixed contracts;
- code review;
- deterministic/static validation;
- executed tests where possible;
- differential/replay evidence;
- preserved provenance;
- no hidden state collapse;
- rollback path;
- negative-result preservation.

If two workers disagree, ChatGPT creates the discriminating test rather than choosing by provider prestige.

## 10. Evidence labels

Every worker contribution is labeled at least:

`WORKER_PROPOSAL`
`STATIC_VALIDATED`
`EXECUTED_TEST`
`SIMULATION`
`PROXY_MODEL`
`TARGET_4B`
`LIVE_PC_FRANK`

No label may be silently upgraded.

## 11. Termination / pause conditions

A cascade round stops or pauses when any of these holds:

- no remaining useful non-duplicated task in current evidence state;
- configured Mistral capacity is unavailable/rate limited/quota limited;
- next step requires target-PC execution unavailable to the current surface;
- an owner authorization gate is reached;
- a critical contradiction requires owner input;
- current turn/tool surface cannot continue synchronously.

Stopping does not mean completion. Leave exact continuation state and next task.

## 12. `frank` trigger integration

The exact `frank` trigger loads this protocol after the FRANK target contracts and before worker dispatch.

Every `frank` response must make clear what was actually executed versus merely queued/proposed. It may not claim an asynchronous cascade is still running unless an actual authorized execution mechanism exists and is observable.
