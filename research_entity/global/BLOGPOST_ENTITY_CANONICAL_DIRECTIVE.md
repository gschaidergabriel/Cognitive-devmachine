# BLOGPOST / MINI ENTITY — SOLE CANONICAL OWNER DIRECTIVE

Status: CURRENT
Owner directive date: 2026-08-22
Persistent research entity: Clay
Active program: BLOGPOST_ENTITY_ALL_IN_ONE
Active stage: BLOGPOST_ENTITY_CLAY

## 1. Sole goal

The Research Entity has exactly one active product goal:

**finish, falsify, harden and deliver one portable all-in-one persistent mini entity whose default personality/use is the Zero/EntityOS Blogpost Entity.**

Canonical ClayCode source target:

`the artefact/blogpost_entity/BLOGPOST_ENTITY.clay`

Portable runtime shape:

`BLOGPOST_ENTITY.clay` executable + one SQLite database (`blogpost_entity.db`).

There is exactly one runtime entity. The swarm exists only as the research/build method used by `go`; it is not a 100-agent product architecture.

All former ClayVerse-container, Frank, UCM/UCM2, EntityOS-product, ClayGraph, GWT, Hyperposition, UnifiedDB, ClayCode and harness work is donor evidence only, except where it directly improves this module.

No worker may open a competing product frontier while this directive is current.

## 2. Product contract

The finished mini entity MUST contain or bind all of these functions in one coherent runtime:

1. deterministic preprocessor;
2. persistent SQLite MiniUnifiedDB state;
3. canonical-state/personality-state compiler;
4. immutable architecture truth guard;
5. user-editable system/personality prompt;
6. configurable text-generation API adapter;
7. autobiographical/narrative continuity memory separated from canonical truth;
8. deterministic output/claim/leak gate;
9. exactly-once source consumption;
10. atomic post/output + packet + state persistence;
11. CLI/configuration surface sufficient to initialize, ingest evidence, set provider/token/prompt, run, inspect status and read outputs.

The default use is the twice-daily autobiographical Zero blog, but changing the editable system prompt may turn the same mini entity into another persistent text-producing role without changing its truth/persistence architecture.

## 3. State and truth law

Architecture:

`real evidence -> deterministic preprocessor -> canonical state snapshot -> personality state -> text API -> deterministic gate -> atomic persistence`

Mandatory invariant:

`UNKNOWN != ZERO != ERROR != MEASURED`

The model/API may narrate or transform supplied state. It may never mint canonical state.

Canonical self/state:
- rebuilt from current database/evidence every run;
- factual and provenance-bound;
- never replaced by model summaries.

Autobiographical self:
- narrative thread/interpretation from previous successful outputs;
- may influence style and continuity;
- is never promoted to canonical truth merely because the model said it.

A verified empty event window may be called quiet. A read/sensor failure MUST be UNKNOWN/ERROR and may never be described as quiet.

## 4. Personality architecture

Two layers are mandatory:

### Immutable architecture guard

Not user-editable. It enforces at minimum:
- no invented state/facts;
- UNKNOWN/ERROR/QUIET separation;
- secrets never published;
- API output is expression/proposal, not state authority;
- emotions/preferences/self-claims require supporting measured state;
- failed generation/validation consumes no source events.

### Editable system/personality prompt

Stored as runtime configuration and replaceable without rebuilding the executable.

Default prompt is the Gasthaus-engineer autobiographical personality. `T_OMEGA = Integral(R_t tensor E_t dt)` remains UNBOUND until R_t and E_t are operationally measured. Bare-metal/local-weight/synthetic-friction desires are conditional outputs only when corresponding measured pressure supports them.

The architecture guard outranks the editable prompt.

## 5. Provider/API law

Mistral is the default tested provider profile, not the identity of the entity.

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

Therefore any admitted token-authenticated JSON text-generation service can be used when its request template and text response path are configured. Provider/model switching MUST NOT fork state or identity.

Secrets:
- never committed to source;
- never printed by config/status commands;
- never included in prompts, outputs, event records, receipts or narrative memory;
- failed/missing secret is an explicit blocker, never permission to fake a live call.

Together API remains forbidden for this project.

## 6. Persistence law

The standalone database is a SQLite MiniUnifiedDB authority for this mini entity. It MUST persist at minimum:
- configuration metadata;
- source/evidence events and consumption identity;
- canonical state generation;
- autobiographical narrative memory;
- run receipts/status/errors;
- outputs/posts;
- provider/model provenance without secret values.

External full UnifiedDB/Agent Zero state may be imported as evidence, but the portable module must not require the whole ClayVerse/EntityOS installation to boot and run.

Exactly-once rule:
- collect unconsumed events;
- build snapshot/package;
- call provider;
- validate result;
- only after success atomically persist output/state and mark those event IDs consumed;
- provider/validation/claim/CAS failure consumes nothing.

## 7. `go` — mandatory swarm build cycle

Exact trigger: `go`

Every `go` is a maximal useful cycle on this single target. Use as many parallel logical/actual research lanes as available, then fuse them back into one artifact delta.

Required lanes:
1. architecture/state compiler;
2. ClayCode/compiler/runtime compatibility;
3. MiniUnifiedDB/evidence projection;
4. personality/emotion/claim-gate;
5. provider/API/secret boundary;
6. adversarial hallucination/leak/concurrency/failure analysis;
7. sandbox execution/tests/fuzzing;
8. fusion/hypofusion/integration.

Cycle:

`refresh -> fan-out -> hypotheses -> counterhypotheses -> implement candidates -> sandbox test -> falsify -> fuse -> fix -> retest -> persist canonical artifact/evidence`

A report without artifact/test progress is not a successful `go` when implementation work is possible.

All lanes converge back onto the same mini entity. No lane creates another runtime entity or competing product.

## 8. Acceptance gates

FINISHED requires evidence for all applicable gates:

1. canonical `.clay` source parses under the selected ClayCode path;
2. a runnable `.clay` executable exists for the admitted sandbox/target platform;
3. fresh SQLite DB initializes without external ClayVerse state;
4. end-to-end sandbox run produces and persists valid output from fixture evidence;
5. events are consumed exactly once; a subsequent verified empty run is correctly quiet;
6. missing/broken sensor/read path is UNKNOWN/ERROR, never quiet;
7. missing token/provider failure consumes nothing;
8. invalid/over-strength self claim consumes nothing;
9. secret/internal-name leak guard rejects publication;
10. output + consumption + continuity/state update commit atomically;
11. stale concurrent generation loses by CAS/rowcount fence;
12. system/personality prompt can be replaced at runtime without bypassing the immutable guard;
13. provider endpoint/model/token can be replaced at runtime without resetting entity state;
14. Mistral default path is exercised with a real authorized key when a secret is actually mounted in a sandbox;
15. at least one real provider-produced output passes the deterministic gate and persists.

Component/mock/local PASS does not imply final live-provider PASS.

## 9. Canonical paths

- directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- active Clay source: `the artefact/blogpost_entity/BLOGPOST_ENTITY.clay`
- runtime/reference implementation: `the artefact/blogpost_entity/`
- tests: `the artefact/blogpost_entity/`
- state: `research_entity/rooms/PROGRAM_STATE.json`
- boot: `research_entity/continuity/BOOTSTRAP_MINIMAL.json`

## 10. Mission re-entry

After every material result ask only:

**What is now the strongest evidence-backed change that moves the single portable Blogpost/Mini Entity closer to final acceptance?**
