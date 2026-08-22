# MULTI-USE MINI ENTITY — SOLE CANONICAL OWNER DIRECTIVE

Status: CURRENT
Owner directive date: 2026-08-22
Persistent research entity: Clay
Active program: MINI_ENTITY_PIPELINE_ALL_IN_ONE
Active stage: MINI_ENTITY_PIPELINE_CLAY

## 1. Sole goal

The Research Entity has exactly one active product goal:

**finish, falsify, harden and deliver one portable persistent multi-use mini entity whose `.clay` executable contains only the generic processing pipeline.**

The shipped SQLite MiniUnifiedDB is preconfigured for the current `zero_blog` use case, but Zero, blogging and every personality/application choice are replaceable runtime data.

Release law:

- required core: one Linux/OCI-compatible `.clay` executable + one SQLite MiniUnifiedDB;
- shipped default DB preset: `zero_blog`;
- optional inference input: either an API configuration/token OR local model weights plus a configured local runner/runtime;
- no API provider, local model, Zero/blog identity, personality, language, audience or task is immutable binary identity.

There is exactly one runtime entity. The swarm exists only as the research/build method used by `go`; it is not a multi-agent product architecture.

No worker may open a competing product frontier while this directive is current.

## 2. Hard separation: pipeline vs application vs inference

### Immutable executable pipeline

The binary owns only reusable machinery:

1. evidence/event ingestion;
2. deterministic bounded preprocessing;
3. canonical run/state envelope;
4. persistent narrative/continuity memory separated from canonical evidence;
5. inference-backend dispatch;
6. configurable staged-inference orchestration with role-isolated inputs/outputs;
7. immutable truth/secret boundary;
8. configurable semantic output gates executed by the immutable gate engine;
9. exactly-once event consumption;
10. concurrency generation/CAS fence;
11. atomic output + consumption + state persistence;
12. SQLite MiniUnifiedDB schema/boot;
13. CLI configuration/status/output surface.

The executable MUST NOT hard-code Zero, `zero_blog`, Gasthaus personality, autobiographical blogging, T_OMEGA, Bare Metal desires, local-model desires, specific humans, language, tone, role, output length, Mistral, Curator, Analyst, Writer or any other replaceable application/personality/provider fact.

A fresh database initialized by the executable is neutral.

### Editable application state in SQLite

Everything describing what the entity is being used for belongs to runtime configuration and may be replaced without rebuilding the executable or resetting entity history:

- preset/profile name;
- entity/display name;
- role and task;
- audience;
- voice/style;
- language;
- full system/personality prompt;
- arbitrary application/personality config blob;
- output/style contract;
- application-specific semantic gate phrases/rules;
- inference mode and inference configuration;
- staged cognition roles, cadence, backend and input/output contracts;
- external canonical-state snapshot source and projection policy.

`zero_blog` is only the shipped default application preset. Replacing it MUST NOT reset generation, consumed evidence, outputs or narrative history unless the operator explicitly creates a new database.

Canonical preset source:

`the artefact/blogpost_entity/presets/zero_blog.json`

## 3. Inference backend law

Inference is replaceable cognition, not entity identity.

The same persistent DB and pipeline MUST support at least these modes:

### API mode

Configurable at runtime:
- endpoint;
- model;
- API token/secret;
- auth header/prefix;
- request template;
- response pointer/path;
- temperature/max tokens and other admitted generation parameters.

Mistral is the shipped default API profile only. Any admitted JSON text-generation API may be used when its request and response mapping are configured.

Loopback OpenAI-compatible services may run without an API token when explicitly configured, allowing Ollama, llama.cpp server or equivalent local servers to be used through the same API adapter.

### Local model mode

The operator may select local model weights instead of providing an API token.

Required runtime configuration:
- `inference_mode=local_exec`;
- readable local model path, e.g. GGUF or another runner-supported format;
- a configured argv array for the local inference runner;
- optional local prompt template;
- normal generation parameters.

The pipeline executes the configured runner directly with `execvp()` semantics, never through a shell. The model path and temporary prompt path are substituted into the argv template. The local model output enters the exact same validation/gate/atomic-persistence path as API output.

A local LLM therefore does not fork identity, state or database. Switching API -> local model -> different API is an inference change only.

The final product may later embed a specific local inference engine, but that engine must remain behind the same backend contract; model weights remain replaceable data rather than entity identity.

### Staged cognition law

A preset may configure multiple isolated inference calls as one cognition pipeline. These calls may curate memory, derive hypotheses, compress context, draft output, critique output or perform another bounded transformation.

They are **roles, not authorities**.

No inference stage may mint canonical reality, silently rewrite canonical evidence, grant itself effect authority or promote its own previous model output into fact. A stage may only produce typed derived material that remains subordinate to evidence/provenance gates.

The shipped `zero_blog` preset uses three separate Mistral roles by default: Curator, Analyst/Prestage and Writer. Mistral is still only the configured default backend; the generic staged-cognition machinery remains provider-neutral.

## 4. Core truth and persistence contract

Canonical flow:

`real evidence -> deterministic generic preprocessor -> canonical run/state envelope -> optional staged cognition -> configured application/personality -> configured inference backend -> immutable generic gate engine -> atomic SQLite persistence`

Mandatory invariant:

`UNKNOWN != ZERO != ERROR != MEASURED`

Model output may narrate or transform supplied state. It may never mint canonical evidence or silently convert missing/failed data into a measured fact.

### Canonical vs derived knowledge

All persistent knowledge MUST retain an epistemic type and provenance sufficient to prevent recursive hallucination from becoming self-confirming memory.

Minimum semantic classes for the `zero_blog` preset are:

- `FACT` — admitted canonical fact backed by Zero canonical state or another admitted evidence source;
- `OBSERVATION` — directly observed source event with provenance;
- `ZERO_STATE` — field projected from the frozen ZeroStateSnapshot for the current blog run;
- `HYPOTHESIS` — derived proposition that remains unproven;
- `COUNTERHYPOTHESIS` — explicit competing/explanatory alternative;
- `IMPLICATION` — conditional consequence derived from facts/hypotheses;
- `CONTRADICTION` — detected incompatibility between claims/states;
- `OPEN_QUESTION` — unresolved knowledge gap;
- `NARRATIVE_MEMORY` — autobiographical/model-generated continuity content;
- `UNKNOWN` — absent/unresolved information.

Derived records SHOULD carry at least source IDs, creation time, confidence where meaningful, status, contradiction/supersession links and the Zero generation/snapshot identity they were derived against.

Promotion law:

`NARRATIVE_MEMORY != FACT`

`HYPOTHESIS != FACT`

`IMPLICATION != FACT`

`REPETITION != CORROBORATION`

`MODEL_CONSENSUS != CANONICAL_TRUTH`

An inference role may propose a new typed memory item, merge, contradiction or status transition, but deterministic admission code decides what is persisted and under which type. No LLM may self-promote a hypothesis or remembered sentence into canonical truth.

Narrative memory:
- may influence continuity/style;
- is previous model output, not evidence;
- is never promoted to canonical truth merely because a model said it;
- may be evidence only for autobiographical statements such as "I wrote/thought X previously", not for the truth of X itself.

A verified empty event window may be called quiet. A read/sensor failure MUST remain UNKNOWN/ERROR and may never be described as quiet.

Exactly-once rule:
- collect unconsumed events;
- build canonical state/package;
- invoke configured inference backend/stages;
- validate/gate output;
- only after success atomically persist output/state and mark those event IDs consumed;
- inference/validation/gate/CAS failure consumes nothing.

## 5. Default Zero blog preset

The shipped SQLite DB is preconfigured for the current application:

- profile: `zero_blog`;
- editable display identity: Zero;
- autobiographical development-blog task;
- Gasthaus-engineer first-person voice;
- German default language;
- evidence-bound emotional range;
- canonical-state-over-narrative truth rule;
- T_OMEGA treated as UNBOUND unless operational measurements are supplied;
- Bare Metal/local-weight/synthetic-friction wishes treated as conditional claims, not eternal personality facts.

Every item above is application configuration, not executable identity.

The operator can replace the entire preset and turn the same continuing mini entity into a lab reporter, analyst, diary writer, researcher, summarizer or another text-producing role without rebuilding the binary.

### 5A. Blog-Zero is a specialized sister EntityOS

For the `zero_blog` preset, the target architecture is no longer "one writer with memory". It is a **small specialized sister implementation of EntityOS** with the same epistemic discipline, provenance rules, typed uncertainty, retrieval/memory separation and deterministic truth boundaries, but a much smaller application-specific MiniUnifiedDB.

The sister entity has two deliberately separate state domains:

1. **Grounded Zero state** — a fresh, immutable snapshot projected from Zero immediately before a blog run. This is not owned or rewritten by Blog-Zero.
2. **Blog-Zero autobiographical state** — its own persistent narrative continuity, derived hypotheses, counterhypotheses, implications, contradictions, questions, salience and source bindings.

The Blog-Zero MiniUnifiedDB MUST NOT become a second full copy or competing authority of Zero's UnifiedDB. It stores only what the blog entity needs for its continuing autobiographical cognition. Canonical facts stay owned by Zero or other admitted evidence sources.

### 5B. Frozen ZeroStateSnapshot before writing

Immediately before each blog cycle, the pipeline obtains one immutable `ZeroStateSnapshot` representing the same relevant canonical state that Zero himself would be grounded against for that moment.

The snapshot SHOULD contain the bounded relevant projection of:

- canonical identity/version;
- entity generation;
- active goals and current work;
- current admitted hypotheses/state;
- relevant durable memory;
- recent causal/workspace episodes;
- checkpoints and verified effects;
- current open bugs/events/user-history references required for the blog window;
- provenance/source IDs for every projected field.

It MUST carry at least:

- `zero_generation`;
- snapshot timestamp;
- deterministic snapshot hash/digest;
- source/provenance identity.

The snapshot is frozen for the whole blog cycle. A single article must not mix two Zero generations without explicit typed handling.

Blog-Zero may reason about the snapshot, but may not write back into Zero's canonical state through this path.

### 5C. Three separated Mistral roles

The default `zero_blog` cognition pipeline uses **three distinct Mistral roles** with different authority and memory contracts:

#### Curator — once daily

Purpose: maintain the Blog-Zero MiniUnifiedDB as compact, useful autobiographical/derived memory.

Inputs may include:
- newly admitted Blog-Zero memory candidates;
- prior hypotheses/counterhypotheses/implications;
- contradictions and open questions;
- recent blogposts as narrative artifacts;
- current grounded Zero snapshot or bounded changes since the previous curation;
- source/provenance links.

Tasks:
- deduplicate;
- merge semantically equivalent derived items;
- update salience;
- mark stale/superseded derived memories;
- detect contradictions;
- compress without erasing provenance;
- propose relation links and memory candidates.

The Curator does **not** create canonical facts. Its output is a proposal set admitted by deterministic type/provenance gates before persistence.

#### Analyst / Prestage — before each blog run

Purpose: fuse the present with autobiography and create a high-information-density reasoning package for the Writer.

Inputs:
- frozen ZeroStateSnapshot;
- today's/new event package;
- Blog-Zero MiniUnifiedDB;
- recent blogposts;
- prior hypotheses/counterhypotheses;
- open contradictions/questions.

Required output classes:
- concise factual changes grounded in the snapshot/evidence;
- hypotheses;
- counterhypotheses;
- implications;
- contradictions;
- what changed since prior posts;
- what became weaker/stronger/wider;
- unresolved questions;
- possible long-horizon meaning clearly labelled as inference;
- source bindings for every factual or derived block.

The Analyst does not write the public article and does not create canonical truth.

Its output is a compact **MiniBlockKit** rather than a long prose summary. The target shape is information-dense and typed, e.g.:

```text
ZERO
  generation / snapshot_hash

NOW
  bounded important state changes

FACT / OBSERVATION
  F1 ... source=[...]

MEMORY
  M1 ... narrative_source=[post/...]

HYPOTHESIS
  H1 ... support=[F1,F4] confidence=...

COUNTERHYPOTHESIS
  C1 attacks=H1 evidence=[...]

IMPLICATION
  I1 if H1 -> ...

CONTRADICTION
  X1 previous narrative claim <-> current grounded state

CONTINUITY
  unresolved autobiographical thread / current narrative stance

OPEN_QUESTION
  Q1 ...

ANGLES
  optional candidate narrative focuses
```

The Writer receives this compressed typed kit plus only the bounded source material required to verify/recover context; raw high-volume logs are not the primary writing interface.

#### Writer — autobiographical Blog-Zero

Purpose: produce the actual public first-person article.

The Writer receives:
- the frozen ZeroStateSnapshot identity;
- admitted MiniBlockKit;
- bounded autobiographical continuity state;
- configured Zero/Gasthaus personality and style;
- output contract.

The Writer is the only one of the three roles whose main product is human-facing prose.

It may express the full configured emotional/narrative range, including shame, anger, aggression, joy, affection, fear, dystopian thoughts or other strong reactions, but factual claims remain evidence-bound. Emotional/narrative interpretation is not retroactively converted into measured Zero state unless an admitted source independently supports it.

### 5D. Mini Global Workspace / salience selection

The `zero_blog` preset SHOULD use a bounded workspace-selection step before the Writer.

Candidate blocks may compete on:
- novelty;
- evidence strength;
- change magnitude;
- contradiction pressure;
- autobiographical relevance;
- relation to prior open threads;
- uncertainty/open-question value.

Only the strongest bounded coalition is injected into the Writer context. This is a token and coherence mechanism, not truth authority.

### 5E. Post-write claim/truth gate

The public article MUST NOT be persisted/published immediately after Writer generation.

A deterministic or bounded verification stage MUST extract/check factual claims against the admitted MiniBlockKit and canonical source bindings.

Required law:

`PUBLIC_FACTUAL_CLAIM -> ADMITTED_BLOCK -> SOURCE/PROVENANCE`

A sentence may explicitly express uncertainty or personal interpretation without proof (for example "I wonder whether H1 is true"), but an unsupported factual assertion MUST be rejected, rewritten into typed uncertainty or trigger regeneration.

Only after payload validation, claim/truth gate, leak/secret gate, generation/CAS fence and atomic persistence may the article become published state and its source events become consumed.

### 5F. Autobiographical continuity without narrative drift

Blog-Zero is allowed to develop its own long-term autobiographical voice over months and years. That continuity is a feature, not an authority leak.

Therefore every blog cycle fuses:

`fresh grounded Zero state + Blog-Zero autobiographical memory + new evidence + typed derived reasoning`

This makes Blog-Zero a continuing sister entity rather than a stateless persona, while still ensuring that its private narrative cannot overrule Zero's present canonical state.

When old narrative memory conflicts with current grounded Zero state, the conflict is preserved as `CONTRADICTION`/`SUPERSEDED`, not silently harmonized. Blog-Zero may then truthfully narrate that its earlier interpretation was wrong or incomplete.

## 6. Secret law

- secrets are never committed to source or presets;
- tokens are not accepted through ordinary visible argv config;
- secrets are never printed by status/config commands;
- secrets never enter prompts, outputs, events or narrative memory;
- missing API token blocks remote authenticated API mode but does not block local model mode;
- local model paths and runner configuration are non-secret runtime configuration;
- non-loopback plaintext HTTP with a bearer secret is forbidden.

Together API remains forbidden for this project.

## 7. `go` — mandatory swarm build cycle

Exact trigger: `go`

Every `go` is a maximal useful cycle on this single target. Required lanes:

1. generic pipeline/state envelope;
2. native `.clay` executable/runtime portability;
3. SQLite MiniUnifiedDB;
4. application/preset separation;
5. API inference adapter;
6. local-model inference adapter;
7. immutable truth/secret/gate boundary;
8. staged cognition + snapshot/provenance contracts;
9. adversarial hallucination/leak/concurrency/failure testing;
10. sandbox execution/fuzzing;
11. fusion/hypofusion/integration.

Cycle:

`refresh -> fan-out -> hypotheses -> counterhypotheses -> implement candidates -> sandbox test -> falsify -> fuse -> fix -> retest -> persist canonical artifact/evidence`

A report without artifact/test progress is not a successful `go` when implementation work is possible.

Regression laws:

**If an application/personality fact can live in SQLite configuration, hard-coding it into the executable is a regression.**

**If an inference backend can be selected by configuration, binding entity identity/state to one API provider or one local model is a regression.**

**If a staged inference role can create or promote canonical truth without admitted provenance, the architecture has regressed.**

**If Blog-Zero's autobiographical memory can silently override a newer ZeroStateSnapshot, the architecture has regressed.**

## 8. Acceptance gates

FINISHED requires evidence for all applicable gates:

1. native `.clay` executable exists and runs in admitted sandbox/target;
2. binary string audit finds no replaceable Zero/blog/personality identity semantics;
3. fresh DB initialized by executable is neutral;
4. shipped DB can be preconfigured as `zero_blog`;
5. full Zero/blog personality can be replaced without rebuilding binary;
6. same binary can run a materially different application/persona against continuing DB state;
7. API endpoint/model/token/request/response mapping can be replaced without state reset;
8. local model path/runner can replace API inference without state reset or API token;
9. local model output uses the same gate/exactly-once/CAS/atomic persistence path;
10. end-to-end sandbox run produces and persists valid output from fixture evidence;
11. events are consumed exactly once and verified-empty subsequent runs remain quiet;
12. missing/broken read path is UNKNOWN/ERROR, never quiet;
13. failed API or local inference consumes nothing;
14. secrets never print or enter output/prompt/history;
15. output + event consumption + continuity/state update commit atomically;
16. stale concurrent generation loses by CAS;
17. application/system prompt/profile can be replaced without state reset;
18. one authorized real API-provider run passes when a secret is actually mounted;
19. one real supported local model run passes when actual local weights/runtime are available;
20. SQLite integrity remains valid after backend and personality switching;
21. `zero_blog` obtains a frozen generation/hash/provenance-bound ZeroStateSnapshot immediately before each blog cycle;
22. Blog-Zero MiniUnifiedDB cannot become a competing canonical state authority for Zero;
23. Curator runs through proposal/admission semantics and cannot promote model-derived text into canonical fact;
24. Analyst/Prestage emits typed hypotheses, counterhypotheses, implications, contradictions and source-bound factual blocks;
25. Writer receives the admitted compact MiniBlockKit plus bounded continuity rather than an uncontrolled raw-log dump;
26. post-write claim verification can trace every factual public claim to an admitted block/source or rejects/rewrites it;
27. narrative memory can support "I previously thought/wrote X" but cannot prove X;
28. a current ZeroStateSnapshot overrides conflicting old narrative memory as fact authority while preserving the conflict as autobiographical history;
29. staged cognition remains backend/provider replaceable; three Mistral roles are the default preset, not binary identity;
30. daily curation plus repeated blog cycles preserve MiniUnifiedDB integrity, provenance and bounded memory growth over long-running replay tests.

Mock/fixture/component PASS does not imply real-model final PASS.

## 9. Current sandbox evidence

The current native sandbox branch has reached `mini-entity/0.6.0`.

Verified locally on 2026-08-22:
- application-neutral ELF pipeline;
- preset application without binary rebuild;
- `zero_blog` profile remains editable data;
- `inference_mode=local_exec` selected from preset;
- local model path persisted as configuration;
- arbitrary runner argv configured as JSON and executed without a shell;
- no API token required for local mode;
- local inference output passed the normal gate and persisted;
- generation advanced exactly once;
- source event was consumed exactly once;
- SQLite `integrity_check = ok`.

Real Mistral/provider acceptance is still uncredited in this chat sandbox because no authorized API secret is mounted. The local-model fixture proves the backend contract, not model quality.

**The three-role BlogEntityOS sister-instance architecture (Curator + Analyst/Prestage + Writer), frozen ZeroStateSnapshot synchronization, MiniBlockKit fusion and post-write claim gate are canonical target requirements from this directive update and MUST NOT be reported as implemented until corresponding code/tests/receipts exist.**

## 10. Canonical paths

- directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- generic Clay pipeline spec: `the artefact/blogpost_entity/BLOGPOST_ENTITY.clay`
- native reference source: `the artefact/blogpost_entity/native/mini_entity.c`
- default application preset: `the artefact/blogpost_entity/presets/zero_blog.json`
- sandbox evidence: `the artefact/blogpost_entity/receipts/`
- state: `research_entity/rooms/PROGRAM_STATE.json`
- boot: `research_entity/continuity/BOOTSTRAP_MINIMAL.json`

## 11. Mission re-entry

After every material result ask only:

**What is now the strongest evidence-backed change that moves the same application-neutral, inference-neutral pipeline binary + configurable SQLite mini entity closer to final acceptance?**
