# CLAY-L4 — Four-Layer AI-Native Semantic Contract

**Status:** OPEN Fusion architecture delta. Does not reopen the fixed FRANK Clay-native target.

## Core invariant

> One Clay semantic world does not imply one causal layer, one authority level, one serialization, or one physical representation.

## L0 — INTENT

Carries human/external goals, natural-language requests, preferences, style/vibe, context and constraints.

Properties:
- provenance-bearing;
- may be ambiguous/incomplete;
- never execution authority by itself;
- soft preference stays soft unless explicitly compiled into a trusted hard policy by an authorized mechanism.

Required transition: `OP.INTENT_COMPILE` -> typed L1 `IntentContract` containing hard constraints, soft objectives, assumptions, prohibitions, unresolved unknowns and source refs.

Effect-critical ambiguity must not be silently guessed into authority.

## L1 — CANONICAL CLAY

Rich exact semantic IR / architecture source of truth.

Contains:
- canonical entities and n-ary role-labelled relations;
- temporal/provenance/epistemic identity;
- operation semantics;
- causal basis/COVE slices;
- selector/projection contracts;
- semantic classes and legal casts;
- capabilities/effect intents/receipts;
- architecture and migration semantics.

L1 is where deterministic compilers/runtimes validate meaning. AINL is relevant engineering precedent for this layer.

## L2 — NATIVE CLAY DELIBERATION

Model-native explicit generated/deliberative symbolic representation learned by the full-model adapted Qwen-class target.

Contains bounded model views, local handles, hypotheses, plans, proposals, references and GWT-visible content.

Properties:
- semantically anchored to L1 but optimized for model cognition/tokenizer/context;
- probabilistic;
- no direct authority to mint facts/capabilities/effects;
- may use a learned VQ/discrete codebook only as an optional experimentally justified projection/micro-dialect;
- codebook/version mapping must resolve to L1 anchors.

AIM/VQEL provide mechanism precedents for optional discrete symbols, not proof that L2 must be discrete.

## L3 — PHYSICAL NEURAL/RUNTIME

Continuous hidden activations, KV tensors, numeric arrays, binary payloads, DB pages, IPC buffers and machine instructions.

Properties:
- physical implementation/lowering, not an independent semantic truth language;
- semantic boundaries carry L1/L2 typed meaning/provenance where required;
- tensor/code execution does not acquire authority from mere physical possession.

## Required receipts

A consequential episode should make recoverable where applicable:

- `intent_contract_id`
- `canonical_semantic_root`
- `cognitive_frame_id`
- `graph_epoch / activation_epoch`
- `causal_slice_id`
- `selection_receipt`
- `workspace_episode_id`
- `model_view_id / projection_receipt`
- `model_checkpoint + tokenizer + quantization/runtime identity`
- optional `native_codebook_id/version`
- `uptake/effect/outcome/reentry receipts`

## Hard non-equivalences

`intent != canonical truth`

`soft preference != hard constraint`

`canonical IR != model-facing serialization`

`model-native symbol != canonical fact`

`symbol purity != causal use`

`native fluency != execution authority`

`hidden activation != literal Clay sentence`

`shared Clay vocabulary != shared privilege class`

## Scientific comparison rule

Never report “AI-native language improved X” without specifying which intervention changed:

- L0 intent/constraint compilation;
- L1 canonical IR/deterministic compiler;
- L2 native-model adaptation/codebook;
- L2 view/projection/tokenizer;
- L3 runtime/quantization/hardware.

Bundled comparisons may be engineering benchmarks, but they are not mechanistic attribution.
