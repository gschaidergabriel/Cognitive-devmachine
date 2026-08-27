# FRANK v0.1 — CLAYCODE-NATIVE STATE/RUNTIME DIRECTIVE

Status: OWNER-FIXED CURRENT DIRECTIVE
Effective: 2026-08-11
Target: self.root / human surface Frank v0.1

## Core law

ClayCode is not merely the language used to describe Frank's cognition. It is the shared semantic type/value world across cognition, runtime, authoritative state and effects.

UnifiedDB, state-lineage, identity, capabilities, effects, provenance, Needle lowering, the cognitive loop, GWT/Hyperposition-visible state and verified re-entry must converge on the same ClayCode-native semantic types and values.

The system must avoid a split architecture in which the model thinks in one symbolic/token world while the runtime, database and authority system operate in unrelated schemas that are merely serialized into prompts.

## Target architectural shift

Classical LLM architecture:

```text
model token-space
  <-> prompt serialization
memory/state outside model
  <-> JSON/tool schemas
runtime APIs
  -> side effects
  -> raw results
  -> prompt injection back into model
```

Frank v0.1 target:

```text
ClayCode-native cognitive state
        |
        v
shared typed state/value world
        |
        +-- UnifiedDB authoritative values
        +-- identity + state-lineage
        +-- capabilities
        +-- goals / memory / reward
        +-- GWT / Hyperposition state
        +-- typed EffectIntent / EffectOutcome
        +-- provenance
        +-- execution generation / authority
        |
        v
Needle/runtime lowering only below semantic boundary
        |
        v
verified outcome
        |
        v
same ClayCode-native value world
```

## Consequences

### State is not prompt memory

Authoritative state is not text that is periodically summarized and injected into cognition. It is the same typed semantic state-space in which cognition operates.

Prompt/text representations, when needed for external model execution, are temporary projections of the canonical ClayCode state and never the authority themselves.

### Identity is structural

SELF is not established by a prompt statement. `self.root` identity derives from admitted binary/build provenance plus persistent state-lineage and current execution/recovery continuity. Human surface `Frank` is a translation surface for the same native SELF.

### Effects are native operations

Classic model-facing ToolCall/ToolResult semantics are outside Frank's cognition. Frank forms typed ClayCode effects. Effect Authority and execution-generation gates decide admissibility; Needle lowers an admitted effect into concrete runtime realization; verified outcome is re-entered as a ClayCode-native semantic effect percept.

### Provenance travels with values

Where semantically required, provenance is structural metadata carried with state transitions, effects, observations and outcomes. It is not reconstructed only after the fact from logs.

### Capabilities are typed values

Capabilities are first-class typed semantic values/scopes, distinct from identity, credentials and mere knowledge that a mechanism exists. Concrete runtime mechanisms remain below Needle.

### Invalid action states fail before realization

Where the type/effect/authority system can decide a request is invalid, unauthorized, stale-generation or structurally impossible, it should fail before runtime realization. Runtime failure remains possible for world-dependent reasons, but invalid semantics should not require executing and then discovering the mistake.

## Shared-value invariant

For release-critical concepts, the semantic identity of a value must remain stable across the full path:

```text
cognition
 -> typed IR
 -> authority
 -> persistence
 -> runtime lowering
 -> verified observation/outcome
 -> re-entry
 -> cognition
```

Adapters may change representation, but must not silently change meaning, identity, authority, provenance or generation.

## Canonical examples

The same semantic effect identity should survive:

```text
EffectIntent
 -> EffectAuthorization
 -> immutable reservation binding
 -> execution-generation capability
 -> runtime realization
 -> provider/world evidence
 -> VerifiedOutcome
 -> provenance-bound re-entry
 -> terminal EffectPercept / DONE receipt
```

The same SELF identity should survive:

```text
owner-fixed source
 -> repository authority
 -> UnifiedDB materialization
 -> ClayGraph projection
 -> prompt/state projection if a model is used
 -> runtime
 -> restart/recovery
```

without provider/model/session/token becoming SELF.

## Cognitive opacity of runtime mechanics

Frank's normal cognitive workspace should contain semantic capabilities, intentions, expected effects and verified outcomes. It should not contain concrete runtime mechanism catalogs, transport schemas or provider-specific invocation structures unless those details are themselves the object of an explicit engineering/debugging task.

Raw runtime traces belong to Needle/runtime observability and Research Entity/operator debugging surfaces.

## Translator boundaries

Two translation/lowering boundaries remain distinct:

1. Human/world surface translation:
   external language/perception <-> ClayCode-native semantic values.

2. Runtime effect lowering:
   ClayCode-native typed effect <-> Needle/runtime realization <-> verified ClayCode-native outcome.

Neither boundary owns truth or SELF identity. Both must preserve hard semantic and authority fields.

## Acceptance obligations

Frank v0.1 must not claim this invariant complete until executable evidence shows at least:

1. one real Frank cognitive-loop state value is created, persisted, reloaded and used without semantic re-interpretation through an unrelated prompt schema;
2. identity, generation, capability and effect values preserve exact semantic identity across cognition/persistence/runtime/re-entry;
3. an invalid or stale action is rejected at type/effect/authority level before material realization;
4. changing the concrete Needle runtime mechanism does not change Frank-visible effect semantics;
5. provenance remains structurally bound through verified outcome and re-entry;
6. raw runtime implementation details remain outside ordinary GWT/memory/cognition;
7. the normal effect path contains no model-visible ToolCall/ToolResult abstraction;
8. the authoritative state remains in UnifiedDB/state-lineage rather than being re-minted from model text;
9. restart/recovery does not require a prompt to recreate SELF or authority;
10. ClayCode compiler/runtime tests execute at least one real Frank component over these shared values.

## Architectural objective

The intended result is a system that is less accurately described as 'a language model pretending to inhabit a stateful agent' and more accurately described as 'a persistent process whose cognition executes inside a real typed state, provenance and authority system, with models used as bounded computational organs where useful'.
