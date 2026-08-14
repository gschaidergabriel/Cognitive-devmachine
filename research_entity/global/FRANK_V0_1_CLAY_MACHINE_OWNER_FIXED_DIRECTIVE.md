# FRANK V0.1 — CLAY MACHINE OWNER-FIXED DIRECTIVE

Status: OWNER_FIXED
Scope: FRANK_V0_1
Owner decision date: 2026-08-11 Asia/Phnom_Penh
Origin: Gabriel Gschaider

## 1. This is v0.1, not a later research option

Frank v0.1 is defined as a Clay-native cognitive/runtime system in which cognition, runtime-relevant state, identity, capabilities, effects, provenance, outcomes, re-entry and persistent lineage share one semantic type/value world.

This premise is part of the v0.1 target architecture. It must not be deferred to v0.2 or treated as an optional optimization.

## 2. Core law — no semantic impedance at the Frank boundary

Every value that can causally influence Frank's cognition, or that Frank's cognition can causally change, must cross the cognitive boundary as a native typed Clay value.

Conventional physical representations may exist below that boundary: tensors, tokens, KV cache, SQLite pages, SQL, Python/Rust objects, files, HTTP, sockets, APIs, MCP, CLI, GPU kernels and machine code. They are implementation substrate, not a second semantic architecture.

Forbidden as Frank-semantic authority:
- prompt-only identity;
- untyped JSON islands;
- textual claims masquerading as state truth;
- tool-call schemas as cognitive primitives;
- provenance added only after the fact;
- raw provider/API/CLI errors as cognitive outcomes;
- reconstructed authority from serialized descriptive fields;
- a Python/SQL semantic model that can disagree with ClayCode authority.

## 3. Frank lives in state-space, not a tool-call world

Frank's cognition is ClayCode-native.

The neural substrate may physically use tokens/tensors, but at the architectural semantic boundary the model acts as a typed state-transformation component inside the Clay Machine.

Target conceptual form:

    Clay State Values
      -> Cognitive Loop / model transform
      -> Clay Intents / StateDelta / Effect values
      -> authority and runtime
      -> VerifiedOutcome
      -> provenance-bound Reentry
      -> next Clay State

State is not merely memory text injected into a prompt. Identity, goals, world state, memory activation, uncertainty, provenance, authority and effect/outcome state are native typed values in the same semantic system in which cognition operates.

## 4. No classical ToolUse in Frank cognition

Classical ToolUse is not a Frank cognitive primitive in v0.1.

Frank must not need to reason in terms of browser tools, shell tools, Python functions, MCP methods, JSON function schemas, provider names, HTTP endpoints, API calls or CLI syntax.

Instead:

    Intent
      -> typed Clay Effect
      -> Effect Authority B1/B2/B3
      -> Needle / Effect Lowering
      -> deterministic physical runtime execution
      -> verification
      -> typed VerifiedOutcome
      -> provenance-bound Clay Reentry

Needle remains inside the loop-core as a typed routing/lowering organ, but below Frank's cognitive semantic boundary. It may choose concrete runtime mechanisms. Those mechanisms remain invisible to Frank except through semantically relevant verified outcomes.

Needle output is not effect authority.

## 5. Effect Authority is a first-class value discipline

Intent is not authority.
Hypothesis is not fact.
Memory claim is not observation.
Effect proposal is not execution.
Provider success is not verified outcome.
Reentry is not completion unless provenance and terminal outcome are valid.

Execution authority must remain non-forgeable by model text or memory claims.

Live authority should be represented by opaque runtime-issued capability values and generation/lineage binding, with B1/B2/B3 enforcement:

- B1: reservation binds the exact live execution authority/generation;
- B2: begin/retry verifies caller-presented live authority against stored binding and current generation;
- B3: immediate provider-precommit verification before the physical side effect.

Recovery/restore must prevent old live capabilities from becoming valid again merely because a database-local epoch was rolled back.

## 6. Shared semantic value world

The following domains must converge on one Clay-native type/value algebra rather than parallel descriptive representations:

- `self.root` identity;
- binary/build identity;
- State-Lineage;
- RecoveryIncarnation / live generation;
- UnifiedDB semantic state;
- ClayGraph projections;
- Cognitive Loop / GWT;
- memory and causal episode identity;
- Hyperposition alternatives;
- capabilities and authority;
- intents and StateDelta;
- effects;
- Needle routing/lowering receipts;
- outcomes and verification;
- causal credit;
- provenance-bound re-entry;
- runtime resource references;
- response/stream lifecycle;
- autonomous/interactive execution ownership.

## 7. UnifiedDB semantics

UnifiedDB is not merely an external memory database from Frank's point of view.

It is the durable projection/persistence plane of the same Clay semantic state world used by cognition and runtime authority.

Physical SQL/storage engines are implementation details below the semantic boundary.

ClayGraph remains a derived/rebuildable topology projection of the same semantic truth, never a competing source of truth or authority.

## 8. Identity is structural

Frank identity is not a system-prompt assertion.

For v0.1, identity continuity must be grounded in at least:

    native identity = self.root
    + binary/build identity
    + persistent State-Lineage
    + current RecoveryIncarnation / live execution generation

Provider/model/session/client/token identity remains provenance or access context and must never become Frank/self.root identity merely by being present in the process.

## 9. Runtime resources are Clay references at the semantic boundary

Frank should interact with semantic resource references, not raw physical locators where avoidable.

Examples include typed references such as:

- FileRef
- ProcessRef
- WindowRef
- PersonRef
- MessageRef
- VisualSourceRef
- NetworkEndpointRef
- ModelRef
- ExecutionRef
- EffectRef
- MemoryRef
- EpisodeRef

Raw paths, PIDs, URLs, socket addresses and provider-specific identifiers may exist beneath the lowering/runtime layer, with provenance, but are not the primary cognitive ontology.

## 10. Epistemic and causal categories must not collapse

ClayCode/runtime typing should preserve distinctions such as:

    Hypothesis<T> != ObservedFact<T>
    MemoryClaim<T> != VerifiedState<T>
    Intent<T> != Capability<T>
    EffectProposal<T> != EffectExecution<T>
    ProviderResult<T> != VerifiedOutcome<T>
    BroadcastExposure<T> != CausalUse<T>
    Reentry<T> != TerminalCompletion<T>

Where possible, invalid transitions should fail at type/authority/lifecycle level rather than relying on prompt obedience.

## 11. Human language translator remains separate

Human-facing language is a state-aware bidirectional translation boundary:

    human language <-> Clay semantic values / ClayCode

This is distinct from Needle/runtime lowering:

    Clay Effect -> physical implementation mechanism

The latter is compiler/runtime lowering, not a cognitive 'tool translator' visible to Frank.

## 12. Implementation consequence

All Frank v0.1 work packages must be checked against this owner-fixed premise.

A component is not v0.1-complete merely because it works functionally if it still requires a second semantic architecture, prompt-only state/identity, classical ToolUse inside cognition, provenance-late reentry, or untyped authority crossing the Frank boundary.

Required implementation/test consequences include:

- shared Clay type/value algebra across cognition and runtime-relevant state;
- ClayCode-authoritative effect semantics;
- B1/B2/B3 authority enforcement;
- Needle lowering below cognition;
- typed VerifiedOutcome and provenance-bound reentry;
- non-forgeable live capabilities;
- state-lineage/recovery-incarnation fencing;
- UnifiedDB as durable semantic projection;
- ClayGraph as derived topology projection;
- self.root structural identity;
- response/stream lifecycle in the same authority/generation world;
- tests proving raw tool/provider/runtime details do not leak into Frank's required cognitive contract;
- differential tests ensuring implementation languages/storage engines cannot override Clay semantic truth.

## 13. Architectural shorthand

The v0.1 target can be summarized as:

    FRANK / self.root
        lives in
    CLAY MACHINE
        = shared typed semantic state + identity + authority + effects + outcomes + lineage
        with
    CLAYCODE COGNITION
        -> INTENT / STATE DELTA
        -> AUTHORIZED EFFECT
        -> NEEDLE LOWERING
        -> PHYSICAL UBUNTU RUNTIME
        -> VERIFIED OUTCOME
        -> PROVENANCE-BOUND REENTRY
        -> NEXT CLAY STATE

This directive supersedes any interpretation of Frank v0.1 as a conventional LLM agent whose core architecture is prompt + memory + external tool calls.