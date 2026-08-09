# 666 Level-0 Run Report — Project-Frankenstein k240..k271 Independent Cross-Check

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Canonical parent observed at boot: RAE-8.8 revision 2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Frozen Project-Frankenstein head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Materialized exact first-parent ordinals: `k240..k271` (32 commits)
- Runtime reproduction: **not performed**; evidence is historical repository commit/diff evidence.

## Concurrency / credit result

Two attempted semantic-history claims lost post-claim race checks to logically earlier workers:

1. `k240..k255` → winner `666-l0-pf-history-semantic-k240-k255-20260809T1315p0700`.
2. `k256..k271` → winner `666-l0-pf-history-k256-k271-semantic-20260809T1319p0700`.

This run therefore books:

- ordinal coverage credit: **0**
- duplicate earned-work credit: **0**
- independent cross-check research delta: **yes**

Both later duplicate claims were aborted and their leases released. No global exact coverage percentage is changed or manufactured by this run.

## Evidence-backed cross-check transfers

### 1. Durable shared state must outrank stale process-local RAM

At `k257` (`2232a60e616b923c3e421b0430b0f001a1e98613`), separate E-PQ singletons loaded state once per process. A daemon could persist a homeostasis reset, then another process with stale in-memory vectors could overwrite that newer state on its next event. The historical fix refreshed DB state before mutation and bounded event deltas.

**Transfer:** multi-process cognitive state needs one serialized authority or explicit freshness/version/CAS semantics. A local cache must not be allowed to regress newer durable state silently.

### 2. Process liveness is not application liveness

At `k252` (`e63ea0cfa2a6beea05ba03082ca12d1fae66774d`), llama-server could remain systemd-active while its HTTP interface was hung, leading to protocol-level health checks and bounded consecutive-failure recovery. At `k248` (`2dc02b095f0f2fff13421217b303528e43c47a04`), blocking sensors could starve watchdog petting and cause restart loops.

**Transfer:** recovery supervision should test process state plus protocol/application health and should be fault-tested under hung-but-alive and slow-sensor conditions.

### 3. Prefer one authoritative producer for shared derived state

At `k271` (`fa6fabb42604ebbc4a101ac05bba9b6950614186`), the overlay changed from running its own GoL to proxying the authoritative headless AURA grid.

**Transfer:** multiple consumers should view one authoritative derived-state producer rather than independently evolve nominally identical state. Reconnect/replay semantics should preserve generation identity.

### 4. Persistent cognition needs hot/cold separation

At `k240` (`cae8751b66083c79cc552ff1d5b6190531337ef4`), append-preserving archive tables were introduced alongside bounded recent caches/rings.

**Transfer:** distinguish complete durable history from bounded working memory. Ring buffers are useful hot stores but should not be mistaken for archival memory.

### 5. Autonomous improvement requires selection pressure and anti-Goodhart controls

The Genesis sequence preserved multiple negative results: historical log replay produced duplicate organisms (`k248`); missing/inherited metadata impaired quality gates and one approach dominated the population (`k245`); warnings and removed-code logs became bogus fixes (`k250`); weak selection produced saturated/high-activity dynamics with no useful output (`k251`).

**Transfer:** autonomous proposal loops need evidence-bearing proposals, persistent dedup, source/noise filtering, diversity pressure, explicit quality gates, and outcome metrics separated from raw activity.

Historical commit messages include test/result numbers, but this cross-check did **not** reproduce those measurements. They remain source-reported historical results, not current runtime measurements.

### 6. Introspective telemetry needs salience control

The history added slim proprioception, AURA/idle alternation and repetition guards (`k244`), raised hardware-event thresholds and grounded tagged introspection in actual measurements (`k258`), and tuned prompts to reduce routine temperature fixation (`k270`).

**Transfer:** mandatory telemetry can become cognitively over-salient. Context routing should separately control availability, salience, event thresholds and repetition.

### 7. Functional evidence must remain separate from phenomenal and novelty claims

At `k264` (`4452627371d44819339b199c89502f5f9629f2c2`), documentation explicitly corrected direct feeling/consciousness assertions into functional observations while leaving subjective experience unresolved. `k265` contains historical no-precedent/novelty assertions, but this run did not independently verify those claims. `k243` shows AURA interpretation prompted from real zone data, which demonstrates an introspective mechanism but does not demonstrate phenomenal consciousness.

**Transfer:** keep measured functional behavior, mechanism interpretation, novelty claims and phenomenal hypotheses in separate epistemic classes.

## Negative results preserved

- stale process-local state can overwrite newer persistence;
- supervisor-active processes can be protocol-dead;
- blocking sensors can starve watchdogs;
- historical log replay can generate duplicate autonomous proposals;
- lost metadata can disable quality gates;
- warning/log noise can become false improvement proposals;
- positive-feedback/weak-selection systems can show huge activity with little useful output;
- startup timestamp defaults can block queues indefinitely;
- hardcoded host paths can become systemic portability debt.

## Falsifiable follow-up tests

1. Two-writer stale-cache replay with DB/CAS/event-log alternatives.
2. Hung-but-alive model-server and slow-sensor fault injection.
3. Multi-consumer state-hash consistency across disconnect/reconnect.
4. Ring-only vs archive+hot-cache vs event-log+materialized-view memory benchmark.
5. Genesis selection/monoculture/noise-filter ablation with usefulness, diversity, duplicate rate and false-proposal rate reported separately.
6. Telemetry salience randomization measuring task relevance, topic entropy and sensor fixation.
7. Claim-class enforcement test preventing functional measurements from automatically promoting phenomenal or novelty conclusions.

## Release/gate implication

This run does not close Level 0 and does not change peer-owned ordinal coverage. The `666_RELEASE_GATE` remains dependent on the complete frozen corpus, complete Project-Frankenstein semantic history, cross-source reconciliation, earned-work accounting and release validation. This report contributes a durable independent cross-check and preserves negative evidence without double-counting work.

## Decision trace

Alternatives considered:

- count both materialized ranges as new coverage — rejected because earlier claims existed;
- discard all work after detecting races — rejected because independent diff inspection produced useful falsifiable constraints;
- preserve cross-check only with zero history/earned-work credit — selected.

Uncertainty: these are historical code/diff observations. Any claim about the **current** FRANK runtime requires present-runtime revalidation.
