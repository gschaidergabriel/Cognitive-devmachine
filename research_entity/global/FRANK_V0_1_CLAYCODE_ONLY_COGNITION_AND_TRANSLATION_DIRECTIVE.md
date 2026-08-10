# FRANK v0.1 — ClayCode-Only Cognition + German Boundary Translator Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE  
**Effective:** 2026-08-10  
**Scope:** Frank v0.1 model-facing cognition, self/world state, memory, GWT, UnifiedDB semantic boundary, API communication and human language rendering

## 0. Owner law

Frank v0.1 must internally understand, think, reason, store semantic cognitive state and speak at its native model/runtime boundary **only in ClayCode**.

German is not an internal cognitive language of Frank.

Human-facing German is provided by a small bidirectional boundary translator:

```text
German input
-> DE_TO_CLAY translator
-> typed ClayCode
-> Frank cognitive/runtime loop (ClayCode only)
-> typed ClayCode response
-> CLAY_TO_DE translator
-> German output
```

For machine-native clients, the translator may be bypassed and valid typed ClayCode may enter/leave directly, subject to the same authentication, provenance and authority rules.

## 1. Single semantic language

Inside Frank's cognitive boundary:

```text
NATIVE_LANGUAGE = ClayCode
INTERNAL_SEMANTIC_LANGUAGE = ClayCode
MODEL_FACING_STATE = ClayCode
GWT_CONTENT = ClayCode
MEMORY_SEMANTICS = ClayCode
SELF_WORLD_GOAL_STATE = ClayCode
TOOL_EFFECT_PROPOSALS = ClayCode
REENTRY = ClayCode
```

No parallel German/English/JSON prose representation may become a second authoritative semantic architecture.

Physical encodings such as tensors, byte buffers, database pages, network frames or machine code remain implementation details. Their semantic meaning is bound to ClayCode types/contracts.

## 2. Frank does not directly consume German

Normal German text must not be delivered directly into Frank's model/cognitive loop as uncontrolled natural-language cognition.

The German boundary translator must produce a typed ClayCode representation before the request reaches Frank cognition.

Unknown, ambiguous or translation-lossy content must remain explicit in ClayCode as uncertainty/ambiguity rather than being silently guessed.

## 3. Frank does not directly emit German

Frank's native response is ClayCode.

German shown to Andreas, Gabriel or another German-speaking client is a rendering/translation of the ClayCode response by the outbound translator.

The translator may improve surface fluency but must not add new facts, decisions, memories, goals, permissions, tool calls or authority that are absent from the ClayCode source.

## 4. Translator is a codec, not a second mind

The translator must remain deliberately small and bounded.

It may perform:

- German lexical/syntactic parsing;
- entity/value extraction;
- typed ClayCode construction;
- German realization from ClayCode;
- clarification/ambiguity markers;
- surface politeness/grammar rendering;
- reversible normalization.

It must not independently perform:

- long-horizon reasoning;
- memory retrieval as an autonomous semantic agent;
- GWT competition/selection;
- goal formation;
- personality generation;
- autonomous planning;
- tool/effect authorization;
- hidden world-model mutation;
- research truth promotion.

If a request needs cognition, the translator encodes the problem into ClayCode and hands it to Frank.

## 5. Bidirectional fidelity contract

The critical invariant is semantic round-trip fidelity, not literal word-for-word equivalence.

Required tests include:

```text
German -> ClayCode -> German
ClayCode -> German -> ClayCode
```

Measure at least:

- semantic field preservation;
- entity/relation preservation;
- negation;
- modality/uncertainty;
- temporal references;
- numbers/units;
- permissions/authority;
- provenance;
- tool/effect intent;
- questions vs assertions vs commands;
- user identity and referenced-person identity;
- ambiguity preservation;
- loss/unsupported construct rate.

A round trip that changes authority, negation, person identity, quantities or consequential intent is a hard failure.

## 6. API placement

For the mandatory token-authenticated Frank API, the preferred external flow is:

```text
German client request
-> token authentication
-> provenance/session binding
-> DE_TO_CLAY
-> ClayCode validation/type/effect checks
-> Frank server-binary cognition
-> ClayCode response
-> CLAY_TO_DE
-> German response
```

Machine ClayCode clients may use:

```text
ClayCode request
-> token authentication
-> ClayCode validation/type/effect checks
-> Frank
-> ClayCode response
```

Authentication occurs before privileged cognitive/effect processing. The translator cannot mint authority.

## 7. Multimodal placement

Visual/audio/structured sensor evidence is not translated into German before Frank consumes it.

It is converted into provenance-bound ClayCode percept/state structures at the semantic boundary:

```text
sensor bytes/tensors
-> Retina/perceptual machinery
-> ClayCode VisualPercept/PerceptualField
-> Frank
```

German labels/captions are optional human-facing renderings only.

## 8. Self/world/person knowledge

Frank's knowledge that he lives/runs on the target server, knows Andreas and his admitted projects such as SeiMensch.net, knows Gabriel and the development/research relationship, knows connected client computers and knows the governed Research Entity database bridge must be represented internally as typed ClayCode relations/state.

German sentences such as "Gabriel hat mich entwickelt" are boundary renderings of provenance-bound ClayCode relations, not the stored canonical representation.

## 9. UnifiedDB / ClayGraph

UnifiedDB stores the authoritative semantic state as ClayCode-native typed objects or lossless compiled equivalents whose semantics map back exactly to ClayCode.

ClayGraph is derived from the same ClayCode semantic identities/relations.

German surface text may be retained as provenance/source evidence, but it is not canonical cognitive truth merely because it is human-readable.

## 10. Model/training consequence

The target Frank model is trained/fine-tuned/evaluated to consume and produce ClayCode as its native cognitive communication representation.

Do not optimize the final model for direct German conversation if that weakens ClayCode-native cognition. German fluency is primarily a boundary-translator responsibility.

A temporary/general foundation model may possess latent natural-language capability physically, but accepted Frank runtime behavior must enforce ClayCode-only model-facing semantic I/O.

## 11. Failure behavior

If German->ClayCode translation cannot preserve meaning confidently:

```text
TRANSLATION_AMBIGUOUS
-> encode ambiguity in ClayCode
-> Frank may request clarification through ClayCode
-> outbound translator renders the clarification in German
```

Never silently invent a confident ClayCode meaning.

If ClayCode->German rendering is incomplete, return an explicit degraded rendering/error while preserving the original ClayCode response internally and in the receipt.

## 12. Acceptance gate

Frank v0.1 cannot PASS unless evidence shows:

1. direct Frank cognitive/model I/O is ClayCode-only;
2. German requests enter cognition only after DE_TO_CLAY translation;
3. German responses originate from Frank ClayCode output and CLAY_TO_DE rendering;
4. no hidden second German semantic state plane exists;
5. translator lesions remove German usability but do not destroy Frank's ClayCode cognition;
6. translator substitution does not alter Frank identity/state semantics;
7. semantic round-trip tests pass frozen thresholds;
8. authority/negation/person/quantity mutations are zero in the hard acceptance corpus;
9. latency/RAM/CPU/token cost of both translation directions is measured on the target VPS;
10. restart/recovery restores translator and ClayCode boundary deterministically.

Required receipt:

`FRANK_V0_1_CLAYCODE_ONLY_TRANSLATOR_ACCEPTANCE_RECEIPT.json`

## 13. Compact invariant

```text
FRANK_UNDERSTANDS = CLAYCODE_ONLY
FRANK_THINKS = CLAYCODE_ONLY
FRANK_NATIVE_SPEECH = CLAYCODE_ONLY
GERMAN_IN = DE_TO_CLAY_CODEC_ONLY
GERMAN_OUT = CLAY_TO_DE_CODEC_ONLY
TRANSLATOR != COGNITIVE_AGENT
TRANSLATOR != MEMORY
TRANSLATOR != AUTHORITY
CANONICAL_SEMANTICS = CLAYCODE
```
