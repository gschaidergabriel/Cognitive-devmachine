# FRANK Context Relevance / derived selection support — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis

## CSD-0 — two different gating problems

Historical FRANK developed both:
- **Thalamus**: state/sensory/accessibility gating before broader cognition;
- **Context Relevance Gate (CRG)**: operation/user-message-specific selection of model context channels.

They overlap conceptually but are not the same organ. The target keeps source/salience gating, admissibility, candidate selection and reader projection as separate stages.

## CSD-1 — pre-CRG hallucination/context filters

Commit `230aa43...` added a pre-input memory gate and post-output hallucination validator around Subconscious. These rule-based mechanisms curated verified memories and blocked known contradictions.

This was an early attempt to distinguish “available memory” from “appropriate current context.”

## CSD-2 — Context Gate creation

Commit `3a264068e5000d7d6212336048b3bf6e8e5e28eb` (2026-03-10) introduced `services/context_gate/`.

Frozen-head architecture describes:
- ~30K-parameter CPU neural gate;
- ~15 context channels;
- target <5 ms model inference / <20 ms full gate call;
- 384D MiniLM user-message embedding plus contextual features;
- per-channel scores [0,1];
- threshold 0.5;
- rule-based fallback;
- online reward shaping from next-user reaction;
- episode IDs stored for later reward;
- SFT Stabilizer anchor.

## CSD-3 — channels that were intentionally ungated

Frozen implementation defines an `_ALWAYS_PASS` set containing high-value channels such as:
- relevant memories;
- perception;
- attention focus;
- active goals;
- NAc drive;
- attention schema;
- introspection block;
- mood trajectory.

This shows the historical designers already recognized that learned relevance gating must not be allowed to hide some essential channels.

Current successor is stronger:
- required context is operation-scoped and typed;
- a “required” item must remain in the candidate domain, but is not forced to win GWT;
- resource overflow escalates rather than silently truncating required evidence.

## CSD-4 — cold start and exploration

Frozen CRG uses:
- cold-start threshold ~100 training steps;
- blend between rules and neural model;
- forced rule-based exploration every 20 calls;
- entropy floor ~0.3;
- random score noise blend ~0.1 when gates crystallize.

This is a precursor of anti-attractor/diversity controls.

Current correction:
- random score noise is not a general safety guarantee;
- calibration/coverage/required-context tests must directly measure omission errors and frequent-attractor collapse.

## CSD-5 — unknown channel behavior

Frozen gate passes unknown channels through with score 1.0 rather than silently blocking them.

This is a reasonable fail-open compatibility choice for ordinary context, but is not sufficient for consequential operations.

Current target differentiates risk:
- unknown schema/causal closure on ordinary low-risk context may broaden/pass;
- unknown consequential admissibility/authority cannot silently cast to valid.

## CSD-6 — learned feedback loop

`record_user_reaction()` assigns reward to the previous gate episode using engagement/frustration/topic-continuity signals.

Architecture value:
- context selection can be trained from downstream outcomes.

Risk:
- next-user engagement is only a noisy utility proxy;
- it may reward sycophancy, frequent topics or self-reinforcing context;
- credit can be misassigned when multiple candidates contributed.

Current C9 correction:
- utility credit has explicit scope (`ITEM|PATH|ASSEMBLY|UNKNOWN`);
- UNKNOWN credit cannot reinforce every surfaced item;
- utility never writes canonical truth or authority.

## CSD-7 — derived consistency/support modules

Frozen service surface also contains:
- `memory_consistency.py`: maintenance/consistency over memory layers;
- `self_consistency.py`: self/output consistency helper;
- `response_analyzer.py`: downstream response inspection;
- `preference_extractor.py`: derived user-preference extraction;
- `topic_interest.py`: persistent derived interests;
- `embedding_service.py`: shared semantic embedding primitive;
- `frank_rag.py` / `lora_context.py`: reader/context assembly support.

These are grouped here because they transform/select/derive cognition-facing state rather than define independent authority domains.

Historical negative results already mapped elsewhere constrain them:
- stale/derived preference or topic state can contaminate recurring thought;
- room-generated text created topic-interest feedback loops;
- embeddings/vector flooding can degrade memory precision;
- reader/context transformations can override learned behavior or hide valid state.

## CSD-8 — C4-C9 successor

C4:
- exact CognitiveFrame precedes projection/model use.

C5:
- Active Assembly and ProjectionReceipt make context formation explicit and replayable.

C6:
- epistemic roles and source/basis are typed; lexical content cannot promote role.

C7:
- MOSAIC/selection receipt makes operation-specific causal scope explicit.

C8:
- Cognitive Resource Governor chooses bounded assembly/context budget while preserving correctness obligations.

C9:
- Causal Admission Compiler + Required Context Closure distinguish:
  `presence -> admissibility -> candidate availability -> selection -> reader projection -> model uptake`.

Historical CRG therefore survives as a **learned relevance/utility candidate mechanism**, not as the sole authority over model context.

## CSD-9 — current fused target

Use deterministic typed requirements first:
- source/basis validity;
- epistemic/admissibility role;
- exact required evidence;
- known dependencies;
- risk/authority needs.

Then learned/contextual mechanisms may optimize:
- optional channel inclusion;
- ordering/weights;
- retrieval breadth;
- compact reader rail;
- expected utility/cost.

All selections produce receipts and remain lesionable against deterministic/full-context baselines.

## Mandatory regressions

- CSD-REG-01 learned relevance gate blocks effect-critical required context;
- CSD-REG-02 always-pass list becomes stale after channel rename/removal;
- CSD-REG-03 unknown channel fail-open gains consequential authority;
- CSD-REG-04 engagement reward reinforces frequent/sycophantic attractor;
- CSD-REG-05 feedback assigned to all channels despite uncertain credit;
- CSD-REG-06 low entropy/noise policy hides calibration collapse;
- CSD-REG-07 derived topic/preference from model prose becomes canonical user fact;
- CSD-REG-08 context projection order/detail changes model behavior without receipt;
- CSD-REG-09 embedding/index version changes but derived context remains CURRENT;
- CSD-REG-10 H1/H2/H3 full-context vs learned-gate differential test preserves required semantics.

## Fusion decision

- ContextGate: `RETEST_AS_OPTIONAL_LEARNED_CONTEXT_OPTIMIZER_BEHIND_TYPED_REQUIRED-CONTEXT_CONTRACT`.
- memory/self consistency helpers: `REUSE_FUNCTIONS_AS_VALIDATORS/MAINTENANCE, NOT_SEPARATE_TRUTH_STORES`.
- topic/preference/response-analysis state: `DERIVED_NON-AUTHORITATIVE_UNLESS_EXPLICITLY_PROMOTED_BY_TRUSTED_EVIDENCE`.
- embeddings/RAG/context builders: `PHYSICAL/READER_SUPPORT, VERSIONED_AND_RECEIPTED`.
