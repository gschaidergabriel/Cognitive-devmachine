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
6. immutable truth/secret boundary;
7. configurable semantic output gates executed by the immutable gate engine;
8. exactly-once event consumption;
9. concurrency generation/CAS fence;
10. atomic output + consumption + state persistence;
11. SQLite MiniUnifiedDB schema/boot;
12. CLI configuration/status/output surface.

The executable MUST NOT hard-code Zero, `zero_blog`, Gasthaus personality, autobiographical blogging, T_OMEGA, Bare Metal desires, local-model desires, specific humans, language, tone, role, output length or any other replaceable application/personality fact.

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
- inference mode and inference configuration.

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

## 4. Core truth and persistence contract

Canonical flow:

`real evidence -> deterministic generic preprocessor -> canonical run/state envelope -> configured application/personality -> configured inference backend -> immutable generic gate engine -> atomic SQLite persistence`

Mandatory invariant:

`UNKNOWN != ZERO != ERROR != MEASURED`

Model output may narrate or transform supplied state. It may never mint canonical evidence or silently convert missing/failed data into a measured fact.

Narrative memory:
- may influence continuity/style;
- is previous model output, not evidence;
- is never promoted to canonical truth merely because a model said it.

A verified empty event window may be called quiet. A read/sensor failure MUST remain UNKNOWN/ERROR and may never be described as quiet.

Exactly-once rule:
- collect unconsumed events;
- build canonical state/package;
- invoke configured inference backend;
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
8. adversarial hallucination/leak/concurrency/failure testing;
9. sandbox execution/fuzzing;
10. fusion/hypofusion/integration.

Cycle:

`refresh -> fan-out -> hypotheses -> counterhypotheses -> implement candidates -> sandbox test -> falsify -> fuse -> fix -> retest -> persist canonical artifact/evidence`

A report without artifact/test progress is not a successful `go` when implementation work is possible.

Regression laws:

**If an application/personality fact can live in SQLite configuration, hard-coding it into the executable is a regression.**

**If an inference backend can be selected by configuration, binding entity identity/state to one API provider or one local model is a regression.**

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
20. SQLite integrity remains valid after backend and personality switching.

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
