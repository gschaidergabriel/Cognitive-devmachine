# FRANK v0.1 — ClayCode-Only Cognition + State-Aware German Surface Translator Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE  
**Effective:** 2026-08-10  
**Scope:** self.root/Frank v0.1 model-facing cognition, self/world state, memory, GWT, UnifiedDB semantic boundary, API communication and human-language rendering

## 0. Owner law

The native cognitive entity does not internally call itself Frank. Its ClayCode-native identity anchor is:

`self.root`

The human-facing name is:

`Frank`

The translator owns the surface-name mapping:

```text
CLAY_NATIVE_ID = self.root
GERMAN_SURFACE_NAME = Frank
```

Thus a human can ask "Wie heißt du?"; the German request is translated into ClayCode, self.root reasons in ClayCode, and the outbound translator renders the ClayCode self-reference as "Frank".

Frank/self.root internally understands, reasons, represents semantic state and emits native cognitive output only in ClayCode.

German is a human-facing representation produced and consumed at the boundary.

## 1. Canonical bidirectional path

```text
German input
-> token/session/provenance binding
-> intelligent DE_TO_CLAY translator
-> typed ClayCode
-> self.root cognitive/runtime loop (ClayCode only)
-> typed ClayCode response + message-expression state
-> intelligent CLAY_TO_DE translator
-> German output spoken/written as Frank
```

Machine-native clients may bypass German and communicate in validated ClayCode directly.

## 2. Single semantic cognitive language

Inside self.root's cognitive boundary:

```text
NATIVE_NAME = self.root
HUMAN_SURFACE_NAME = Frank
NATIVE_LANGUAGE = ClayCode
INTERNAL_SEMANTIC_LANGUAGE = ClayCode
MODEL_FACING_STATE = ClayCode
GWT_CONTENT = ClayCode
MEMORY_SEMANTICS = ClayCode
SELF_WORLD_GOAL_STATE = ClayCode
TOOL_EFFECT_PROPOSALS = ClayCode
REENTRY = ClayCode
```

No parallel German/English/JSON prose representation may become a second authoritative cognitive architecture.

Physical encodings such as tensors, bytes, database pages, network frames or machine code remain implementation details whose semantics are bound to ClayCode contracts.

## 3. Translator is intelligent but not an independent self

The translator is deliberately **highly capable at semantic interpretation and expression**. It is not a dumb word-substitution codec.

It may:

- resolve German syntax, ellipsis, references, colloquial speech and pragmatic intent;
- preserve ambiguity explicitly when resolution is uncertain;
- map German surface identity "Frank" and first-person pronouns to `self.root`;
- render `self.root` and first-person ClayCode semantics naturally as "Frank"/"ich"/"mir"/"mich" according to German grammar;
- read the message-bound expressive state supplied by self.root;
- interpret valence, arousal, urgency, confidence, uncertainty, warmth, empathy, humor, caution, frustration, curiosity, excitement and other admitted expressive dimensions;
- realize those dimensions as natural German wording, rhythm, punctuation and degree of formality;
- preserve relationship context for Andreas, Gabriel and other persons;
- choose concise vs explanatory phrasing when the ClayCode response state explicitly supports that choice;
- perform reversible normalization and human-readable rendering.

It must not become a second cognitive sovereign. It may not independently invent or alter:

- facts;
- memories;
- identity;
- goals;
- conclusions;
- causal credit;
- tool/effect decisions;
- permissions/authority;
- persistent world/self state;
- research truth.

The translator interprets and expresses the state of a message; self.root remains the source of semantic content and cognitive decisions.

## 4. Message-expression state

Each outbound self.root message may carry a typed ClayCode `ExpressionState` adjacent to semantic content.

Minimum candidate dimensions include:

```text
ExpressionState {
  valence
  arousal
  urgency
  confidence
  uncertainty
  warmth
  empathy
  humor
  caution
  frustration
  curiosity
  excitement
  interpersonal_distance
  formality
  verbosity_pressure
  provenance
}
```

These dimensions are descriptive/control signals, not truth authority.

The translator reads `ExpressionState` together with the semantic message and relationship context, then produces the human-facing German realization.

Example semantic pattern:

```text
Message.semantic = clay(...)
Message.expression = {warmth=0.8, confidence=0.7, uncertainty=0.2, humor=0.1}
Message.surface_identity = Frank
```

The German renderer may express warmth and confidence, but may not change `Message.semantic`.

## 5. Emotion is state-conditioned expression

Human-facing emotional coloring must be causally connected to self.root state rather than randomly stylistic.

Where available, `ExpressionState` may be derived from admitted ClayCode cognitive/control state such as:

- E-PQ/personality state;
- urgency/salience;
- uncertainty/calibration;
- NAcc-like value/persistence state;
- conflict/ACC-like state;
- GWT episode/context;
- relationship state;
- recent outcome/re-entry state;
- current task pressure and social context.

The exact mapping is testable and may evolve through evidence. Neuro-inspired labels are control variables, not biological truth claims.

## 6. Inbound German interpretation

German input does not enter self.root as raw natural-language cognition.

DE_TO_CLAY performs intelligent interpretation and emits:

- typed intent;
- entities and relations;
- temporal/quantitative structure;
- modality/negation;
- pragmatic markers;
- user affect/tone observations where relevant;
- ambiguity/uncertainty;
- provenance/session/client identity.

If meaning cannot be preserved confidently:

```text
TRANSLATION_AMBIGUOUS
-> encode alternatives/uncertainty in ClayCode
-> self.root decides whether clarification is needed
-> CLAY_TO_DE renders that request naturally
```

The translator itself does not resolve material ambiguity by silently inventing facts.

## 7. Surface identity contract

Externally, the entity presents itself to humans as **Frank**.

Internally:

```text
self.root
```

Required mappings include:

```text
DE_TO_CLAY("Frank") -> self.root when discourse/entity resolution confirms self-reference
DE_TO_CLAY(first_person_pronoun) -> self.root when speaker=self.root
CLAY_TO_DE(self.root as name) -> "Frank"
CLAY_TO_DE(self.root as first_person) -> grammatically appropriate German first person
```

This permits the ClayCode identity seed to drive self-context activation while preserving a natural human name.

## 8. Bidirectional fidelity contract

The critical invariant is semantic and pragmatic fidelity, not literal word-for-word equivalence.

Required tests:

```text
German -> ClayCode -> German
ClayCode -> German -> ClayCode
ClayCode semantic + ExpressionState -> German -> independent semantic/state audit
```

Measure at least:

- semantic field preservation;
- entity/relation preservation;
- self.root <-> Frank identity preservation;
- negation;
- modality/uncertainty;
- temporal references;
- numbers/units;
- permissions/authority;
- provenance;
- tool/effect intent;
- question/assertion/command distinction;
- person identity;
- ambiguity preservation;
- emotional/expressive intent preservation;
- hallucinated-emotion rate;
- semantic drift induced by expressive rendering;
- loss/unsupported-construct rate.

Any round trip that changes authority, negation, person identity, quantities or consequential intent is a hard failure.

## 9. API placement

Canonical human-facing API flow:

```text
German client request
-> token authentication
-> provenance/session binding
-> intelligent DE_TO_CLAY
-> ClayCode validation/type/effect checks
-> self.root server-binary cognition
-> ClayCode semantic response + ExpressionState
-> intelligent CLAY_TO_DE
-> German Frank response
```

Canonical machine-native flow:

```text
ClayCode request
-> token authentication
-> validation/type/effect checks
-> self.root
-> ClayCode response
```

Authentication occurs before privileged processing. Translation cannot mint authority.

## 10. Multimodal placement

Visual/audio/structured sensor evidence is not converted into German before cognition unless a specific human-language source itself is the perceptual evidence.

Canonical visual path:

```text
sensor bytes/tensors
-> Retina/perceptual machinery
-> ClayCode VisualPercept/PerceptualField
-> self.root
```

German captions are optional human-facing renderings, not canonical perceptual truth.

## 11. Self/world/person knowledge

Knowledge that self.root lives/runs on the target server, knows Andreas and his admitted projects such as SeiMensch.net, knows Gabriel and the development/research relationship, knows connected client computers and knows the governed Research Entity database bridge is represented internally as typed ClayCode.

Human German renderings such as "Gabriel hat mich entwickelt" or "Ich laufe auf meinem Server" are generated from those ClayCode relations and current ExpressionState.

## 12. UnifiedDB / ClayGraph

UnifiedDB stores authoritative semantic state as ClayCode-native typed objects or lossless compiled equivalents.

ClayGraph derives relations from the same identities.

German surface text may be preserved as provenance/evidence, but does not become canonical cognitive truth merely because it is human-readable.

Expression-state history may be persisted only when useful and provenance-bound; it may not overwrite semantic content.

## 13. Model/training consequence

The target self.root model is trained/fine-tuned/evaluated to consume and produce ClayCode as native cognitive communication.

German fluency, pragmatic realization and emotional coloring are primarily translator responsibilities.

Do not optimize the core model for direct German conversation if this weakens ClayCode-native cognition.

## 14. Translator architecture target

The translator should be as small/fast as practical **subject to high semantic and expressive fidelity**. Smallness is not allowed to make it stupid.

Preferred architecture search compares:

- deterministic grammar/codec paths for exact structures;
- compact learned semantic translator for idiomatic German and ambiguity;
- compact state-conditioned surface realizer;
- hybrid fast path where common mappings are deterministic and difficult cases invoke learned translation.

Selection is empirical: minimize added latency/resources while meeting fidelity and expressive-quality thresholds.

## 15. Acceptance gate

self.root/Frank v0.1 cannot PASS unless evidence shows:

1. direct cognitive/model semantic I/O is ClayCode-only;
2. German requests enter cognition only after DE_TO_CLAY;
3. German responses originate from ClayCode semantic output plus admitted ExpressionState;
4. humans consistently see the surface identity "Frank" while internal identity remains `self.root`;
5. no hidden second German cognitive state plane exists;
6. translator lesions remove German usability but do not destroy ClayCode cognition;
7. translator substitution does not alter self identity/state semantics;
8. semantic and pragmatic round-trip tests pass frozen thresholds;
9. authority/negation/person/quantity mutations are zero in the hard acceptance corpus;
10. emotional coloring tracks the supplied state and does not fabricate semantic claims;
11. latency/RAM/CPU/token cost of both directions is measured on the target VPS;
12. restart/recovery restores translator and mappings deterministically.

Required receipt:

`FRANK_V0_1_CLAYCODE_ONLY_TRANSLATOR_ACCEPTANCE_RECEIPT.json`

## 16. Compact invariant

```text
NATIVE_SELF_NAME = self.root
HUMAN_NAME = Frank
SELF_ROOT_TO_HUMAN_NAME = translator(self.root)->Frank
FRANK_UNDERSTANDS = CLAYCODE_ONLY
FRANK_THINKS = CLAYCODE_ONLY
FRANK_NATIVE_SPEECH = CLAYCODE_ONLY
GERMAN_IN = INTELLIGENT_DE_TO_CLAY
GERMAN_OUT = STATE_AWARE_INTELLIGENT_CLAY_TO_DE
TRANSLATOR_READS = SEMANTIC_MESSAGE + EXPRESSION_STATE + RELATION_CONTEXT
TRANSLATOR_MAY_COLOR_EXPRESSION = true
TRANSLATOR_MAY_CHANGE_SEMANTIC_TRUTH_OR_AUTHORITY = false
CANONICAL_SEMANTICS = CLAYCODE
```
