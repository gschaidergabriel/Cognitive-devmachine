# BLOGPOST / MINI ENTITY — SOLE CANONICAL OWNER DIRECTIVE

Status: CURRENT
Owner directive date: 2026-08-22
Persistent research entity: Clay
Active program: BLOGPOST_ENTITY_ALL_IN_ONE
Active stage: BLOGPOST_ENTITY_CLAY

## 1. Sole goal

The Research Entity has exactly one active product goal:

**finish, falsify, harden and deliver one portable persistent multi-use mini entity whose executable contains only the generic processing pipeline, while the shipped SQLite database is preconfigured as the Zero/EntityOS Blogpost Entity.**

Release target:

- one Linux/OCI-compatible `.clay` executable;
- one SQLite MiniUnifiedDB database;
- default shipped DB preset: `zero_blog`;
- no Zero/blog/personality semantics are immutable binary identity.

There is exactly one runtime entity. The swarm exists only as the research/build method used by `go`; it is not a multi-agent product architecture.

All former ClayVerse-container, Frank, UCM/UCM2, EntityOS-product, ClayGraph, GWT, Hyperposition, UnifiedDB, ClayCode and harness work is donor evidence only where it directly improves this module.

No worker may open a competing product frontier while this directive is current.

## 2. Hard separation: pipeline vs application

### Immutable executable pipeline

The binary owns only reusable machinery:

1. evidence/event ingestion;
2. deterministic bounded preprocessing;
3. canonical run/state envelope;
4. persistent narrative/continuity memory kept separate from canonical evidence;
5. configurable text-generation API transport;
6. immutable truth/secret boundary;
7. configurable semantic output gates executed by the immutable gate engine;
8. exactly-once event consumption;
9. concurrency generation/CAS fence;
10. atomic output + consumption + state persistence;
11. SQLite MiniUnifiedDB schema/boot;
12. CLI configuration/status/output surface.

The executable MUST NOT require or hard-code `Zero`, `zero_blog`, Gasthaus personality, autobiographical blogging, T_OMEGA, Bare Metal desires, local-model desires, specific audience names, language, tone, role, output length, or any other application/personality fact.

A fresh database initialized by the executable is neutral.

### Editable application state in SQLite

Everything describing what the entity is being used for belongs to runtime configuration in the database and may be replaced without rebuilding the executable or resetting entity history:

- preset/profile name;
- entity/display name;
- role;
- audience;
- voice/style;
- language;
- task;
- full system/personality prompt;
- arbitrary application/personality config blob;
- output/style contract;
- application-specific semantic gate phrases/rules;
- provider endpoint;
- provider model;
- API token;
- auth header/prefix;
- request template;
- response pointer;
- generation parameters.

`zero_blog` is only the current shipped default application preset. It may be fully replaced at runtime. Replacing it MUST NOT reset canonical generation, consumed evidence, outputs or narrative history unless the operator explicitly creates a new database.

Canonical preset source for reproducibility:

`the artefact/blogpost_entity/presets/zero_blog.json`

## 3. Product contract

The finished mini entity MUST support:

`real evidence -> deterministic generic preprocessor -> canonical run/state envelope -> configured application/personality -> configured text API -> immutable generic gate engine -> atomic SQLite persistence`

Mandatory invariant:

`UNKNOWN != ZERO != ERROR != MEASURED`

The model/API may narrate or transform supplied state. It may never mint canonical evidence or silently convert missing/failed data into a measured fact.

Narrative memory:
- may influence continuity/style;
- is previous model output, not evidence;
- is never promoted to canonical truth merely because the model said it.

A verified empty event window may be called quiet. A read/sensor failure MUST be UNKNOWN/ERROR and may never be described as quiet.

## 4. Default Zero blog application

The shipped SQLite DB is preconfigured for the current use case:

- profile: `zero_blog`;
- Zero as editable display/application identity;
- Gasthaus-engineer first-person voice;
- autobiographical development blog task;
- German default language;
- evidence-bound emotional range;
- canonical-state-over-narrative truth rule;
- T_OMEGA treated as UNBOUND unless operational measurements are explicitly supplied;
- Bare Metal/local-weight/synthetic-friction wishes treated as conditional claims, not eternal personality facts.

Every item above is application configuration, not executable identity. The operator can turn the same persisted mini entity into a lab reporter, diary writer, analyst, summarizer, researcher or another text-producing role by changing DB configuration/system prompt.

## 5. Provider/API law

Mistral is the shipped default provider profile, not the identity of the entity or pipeline.

Default profile:
- endpoint: `https://api.mistral.ai/v1/chat/completions`;
- token: runtime-injected secret;
- model: runtime-configurable;
- OpenAI-style chat-completions request/response contract.

Provider configuration MUST be changeable without recompiling and MUST include at least:
- endpoint;
- model;
- API token;
- auth header and prefix;
- request template or standard chat-completions mode;
- response JSON pointer/path.

Therefore any admitted token-authenticated JSON text-generation service can be used when its request template and text response path are configured. Provider/model switching MUST NOT fork state or reset the database.

Secrets:
- never committed to source or preset files;
- never printed by status/config commands;
- never included in prompts, outputs, event records or narrative memory;
- failed/missing secret is an explicit blocker, never permission to fake a live call.

Together API remains forbidden for this project.

## 6. Persistence law

The standalone database is the SQLite MiniUnifiedDB authority for this mini entity. It MUST persist at minimum:
- configuration metadata;
- application/personality profile/config;
- source/evidence events and consumption identity;
- canonical generation/state envelope;
- narrative continuity memory;
- run receipts/status/errors;
- outputs;
- provider/model provenance without secret values.

External full UnifiedDB/Agent Zero state may be imported as evidence, but the portable module must not require the whole ClayVerse/EntityOS installation to boot and run.

Exactly-once rule:
- collect unconsumed events;
- build snapshot/package;
- call provider;
- validate result;
- only after success atomically persist output/state and mark those event IDs consumed;
- provider/validation/gate/CAS failure consumes nothing.

## 7. `go` — mandatory swarm build cycle

Exact trigger: `go`

Every `go` is a maximal useful cycle on this single target. The swarm is only research/build orchestration.

Required lanes:
1. generic pipeline/state envelope;
2. native `.clay` executable/runtime portability;
3. SQLite MiniUnifiedDB;
4. application-config/preset separation;
5. provider/API/secret boundary;
6. adversarial hallucination/leak/concurrency/failure analysis;
7. sandbox execution/tests/fuzzing;
8. fusion/hypofusion/integration.

Cycle:

`refresh -> fan-out -> hypotheses -> counterhypotheses -> implement candidates -> sandbox test -> falsify -> fuse -> fix -> retest -> persist canonical artifact/evidence`

A report without artifact/test progress is not a successful `go` when implementation work is possible.

Regression law for every `go`:

**If an application/personality fact can live in SQLite configuration, hard-coding it into the executable is a regression and must be removed.**

## 8. Acceptance gates

FINISHED requires evidence for all applicable gates:

1. native `.clay` executable exists and runs in the admitted sandbox/target;
2. binary application-string audit finds no Zero/blog/personality-specific identity semantics;
3. fresh DB initialized by executable is neutral;
4. shipped DB boots preconfigured as `zero_blog`;
5. full Zero/blog personality can be changed without rebuilding binary;
6. same binary can run a materially different application/persona against the same continuing DB state;
7. fresh SQLite DB initializes without external ClayVerse state;
8. end-to-end sandbox run produces and persists valid output from fixture evidence;
9. events are consumed exactly once; subsequent verified empty run remains correctly quiet;
10. missing/broken read path is UNKNOWN/ERROR, never quiet;
11. missing token/provider failure consumes nothing;
12. secrets are never printed or accepted as normal argv config;
13. output + consumption + continuity/state update commit atomically;
14. stale concurrent generation loses by CAS/rowcount fence;
15. provider endpoint/model/token/request/response mapping can be replaced without state reset;
16. application/system prompt/profile can be replaced without state reset;
17. Mistral default path is exercised with a real authorized key when a secret is actually mounted;
18. at least one real provider-produced output passes the gate and persists.

Component/mock/local PASS does not imply final live-provider PASS.

## 9. Current sandbox evidence

Native pipeline 0.4.0 evidence is recorded in:

`the artefact/blogpost_entity/receipts/2026-08-22_PIPELINE_0_4_CONFIG_SEPARATION.json`

It establishes locally that the same executable can replace the shipped Zero/Gasthaus application with a materially different `Mara` English lab-report profile without rebuild or DB reset, while generation/Exactly-once persistence continues.

## 10. Canonical paths

- directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- structured Clay source/spec target: `the artefact/blogpost_entity/BLOGPOST_ENTITY.clay`
- default application preset: `the artefact/blogpost_entity/presets/zero_blog.json`
- sandbox evidence: `the artefact/blogpost_entity/receipts/`
- state: `research_entity/rooms/PROGRAM_STATE.json`
- boot: `research_entity/continuity/BOOTSTRAP_MINIMAL.json`

## 11. Mission re-entry

After every material result ask only:

**What is now the strongest evidence-backed change that moves the same application-neutral pipeline binary + configurable SQLite mini entity closer to final acceptance?**
