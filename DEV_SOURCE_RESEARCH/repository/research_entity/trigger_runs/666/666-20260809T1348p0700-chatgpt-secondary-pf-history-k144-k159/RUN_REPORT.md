# 666 Level-0 Run Report — Project-Frankenstein History k144..k159

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k144..k159`
- Exact commits materialized and terminally dispositioned: `16/16`
- Race status: clean after full materialization.
- Runtime reproduction: not performed; evidence class is historical commit/diff and documentation lineage.

## Strongest findings

### Reality grounding can become context contamination

At `k146`, a SystemRealityLayer and post-generation Ego Governor were introduced to correct architectural confabulation. At `k144`, universal SystemRealityLayer injection into idle-thought prompts was removed because the model echoed `[REALITY]` content into its own output. This is a useful causal lineage: a truth source can improve factual governance while still damaging generation when routed into the wrong cognitive path.

**Transfer:** ground truth should be available through task-specific context routing and post-generation validation, not injected indiscriminately into every model call.

### Internal LLM work must not share conversational persistence by default

At `k158`, conversation-summary generation used the normal Core chat path and its internal summary prompt was persisted as a visible user message after restart. At `k144`, autonomous research also attempted to write through a nonexistent `/memory/store` endpoint before being redirected to direct database persistence.

**Transfer:** internal summarization/research/maintenance jobs need a separate non-conversational channel with explicit no-persist semantics and a real storage contract. Conversational APIs should not silently double as internal worker buses.

### Filters and learned gates need collateral-damage controls

At `k154`, response-cleaning regexes could erase large parts of legitimate philosophical answers. A retained-content-ratio guard was added so a filter that destroyed too much text was skipped. The same audit added a Neural Reality Gate with cold-start rule fallback and gradual neural blending.

**Transfer:** validators should measure false-positive/collateral deletion, learned gates need fallback during cold start, and output filtering needs outcome monitoring rather than unconditional trust.

### Evidence can be historically retracted

`k153` introduced a 70-turn bare-Llama-vs-Frank "ablation analysis" with quantitative metrics and strong rigor language. `k150` subsequently deleted that artifact and replaced it with unedited conversation excerpts explicitly presented with no metrics and no claims. `k157` further moved the public presentation from persuasion/comparison toward technical description and caveated observations.

**Transfer:** retractions, downgrades and supersession are first-class evidence events. The latest stronger epistemic correction must dominate older claims unless the original study is independently reconstructed from immutable raw material.

### Topology duplication causes deployment/recovery drift

`k151`, `k152` and `k156` show repeated reconciliation of installer, recovery, updater and documentation against the live system: service names, ports, model roles, venv locations, databases and the entity→rooms architecture had diverged.

**Transfer:** deployment/recovery/documentation topology should be generated from one authoritative machine-readable manifest where possible, otherwise contract-tested for drift.

### Seed state has identity provenance

`k152` snapshots 48 live databases into seed DBs, explicitly including personality/state databases.

**Transfer:** reference/bootstrap state must carry provenance and remain categorically distinct from mutable runtime/user identity. Seed data must not silently become evidence of a new instance's own history or identity.

## Evidence-class reversal: k153 → k150

This is explicitly preserved as a negative scientific-method result:

1. quantitative ablation presented and promoted;
2. later removed;
3. replaced by raw behavioral examples with no metric claims.

Therefore this Level-0 shard assigns **zero current empirical credit** to the source-reported k153 metrics. They remain historical claims only.

## Additional findings

- WebUI/Core dual-write and session divergence were reduced by shared session ID and Core-owned persistence (`k146`).
- Creative diversity at `k149` was explicitly scaffolded by shuffled assets, banned defaults, random selection and anti-fixation prompts; it should not be counted as unprompted emergence without ablation.
- Hardware support claims changed over adjacent documentation revisions (`k155`), reinforcing document epoch validity.
- Large documentation reconciliation at `k156` demonstrates that papers/manuals/README describe different historical architectures unless explicitly epoch-tagged.

## Negative results preserved

- ground-truth prompt material leaked into idle thoughts;
- nonexistent memory endpoint in autonomous research;
- internal summary prompt persisted into user-visible chat;
- output-cleaning filters over-stripped legitimate content;
- updater/recovery/service maps drifted from live topology;
- quantitative ablation evidence was later explicitly downgraded/removed;
- runtime support/documentation claims changed substantially across close revisions.

## Measurement and earned-work boundary

Source-reported benchmark percentages, latencies, fix counts and rejection rates were not reproduced. No avoided-hours number is added because this shard did not perform row-level conceptual dedup against the earned-work ledger.

Global Level-0 exact percentage remains unchanged because the combined obligation denominator is still `NOT_FROZEN`. `666_RELEASE_GATE` remains `NOT_PASS`.
