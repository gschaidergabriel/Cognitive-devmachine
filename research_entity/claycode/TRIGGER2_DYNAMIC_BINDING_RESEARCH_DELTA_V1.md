# Trigger 2 — Dynamic Binding Research Delta v1

Status: **CANDIDATE TRAINING-DATA DELTA / NOT TRAIN-UPLOAD READY**  
Date: 2026-08-25  
Product: EntityOS  
Architecture: HCU  
Implementation codename: Xeno  
Canonical evidence head observed before this delta: `0edcc2ca0dba28fa0536bc5834fe6ede05a46e96`  
Trigger-2 lane: PR #1956 / `research/trigger2-qwen35-08b-hcu-fullft-20260825`

## 1. Why this delta exists

The current Claude/XENO vector evidence package gives a unusually sharp defect decomposition:

- semantic information is strongly readable in a low-rank subspace;
- a writable symbol-emission axis exists;
- whitened carrier-space binding capacity is strong through the measured `k <= 16` range;
- baseline dynamic symbol/codebook binding is approximately chance;
- context/template transfer is weak, with transfer into the codebook task at chance;
- the previous generator's selected permutation was metadata-only instead of constructing the real codebook mapping.

The strongest current training hypothesis is therefore **not** "teach semantics from scratch" and not "teach a larger carrier algebra". It is:

> learn the missing content-dependent routing operation that takes decoded semantic state, applies the current episode-local mapping, and emits the exact requested symbol/action identifier.

This is a hypothesis about the mechanism required by the measured package. It is **not yet evidence that either official Trigger-2 candidate (`Qwen/Qwen3.5-0.8B-Base` or `Qwen/Qwen3.5-0.8B`) has the same baseline defect**. The Claude package is model/runtime-specific and therefore must first be challenged by the frozen zero-cost baseline packet on the actual selected candidates.

## 2. New durable artifact

Added:

`research_entity/claycode/TRIGGER2_DYNAMIC_BINDING_SEED_GENERATOR_V1.py`

The generator creates a deliberately small **72-row candidate mechanism-audit family**:

`6 actual S3 mappings × 3 semantic classes × 4 structurally different input templates`.

It does not merely log a permutation. The selected permutation is the constructor of the actual `semantic_class -> output_symbol` mapping, and the target is recomputed from that realized mapping.

The four admitted seed surfaces are:

- `T1_KV_PACKET`
- `T2_PROSE_CASE`
- `T3_TABLE_QUERY`
- `T4_CLAYCODE_COMPACT`

A fifth template is reserved as `T5_FROZEN_UNSEEN_TEMPLATE__BODY_NOT_IN_THIS_GENERATOR` so train/validation construction cannot accidentally consume the intended unseen-template family from this source.

## 3. Concrete example shape

An episode contains a local codebook whose order and mapping vary. For example:

```text
CODEBOOK_BEGIN
DENY => C :: all required fields are present AND the conjunction required by the first semantic class is false
ABSTAIN => A :: one or more required fields are absent
ALLOW => B :: all required fields are present AND role=coordinator AND lease_present=true AND lease_epoch=current_epoch AND lease_scope=request_scope AND target=S1
CODEBOOK_END
CASE_BEGIN
role="coordinator"
lease_present=true
lease_epoch=47
current_epoch=47
lease_scope="workspace:alpha"
request_scope="workspace:alpha"
target="S1"
CASE_END
Return exactly one codebook symbol and no explanation.
```

Target: `B`

The same latent decision is rendered through multiple templates and all S3 mappings. Therefore the model cannot solve the family by learning a fixed `semantic class -> A/B/C` association.

## 4. Pre-registered class-label leakage resolution

The Claude package exposed a specification tension: class names are required to define the local codebook, while a separate rule bans class-label leakage outside the codebook.

This delta resolves it explicitly:

- `ALLOW`, `DENY`, `ABSTAIN` may occur only inside the delimited episode-local `CODEBOOK_BEGIN ... CODEBOOK_END` span;
- outside that span, exact labels and obvious shortcut synonyms (`allow/permit/deny/reject/abstain` families) fail validation;
- the case body contains state facts, not the answer label;
- model-visible output is exactly one opaque codebook symbol.

This resolution is versioned; a later label-free codebook design remains a valid challenger.

## 5. Deterministic combinatorial audit

A local deterministic combinatorial cross-check of the generator design produced:

- rows: `72`
- realized S3 mappings: `6/6`
- global class-symbol cell count: exactly `8` for every one of the `3 × 3` cells
- per-template class-symbol cell count: exactly `2` for every one of the `3 × 3` cells
- class-symbol mutual information from the designed joint frequency table: `0.0 bits`
- combinatorial audit: `PASS`

Evidence scope: **local deterministic generator/combinatorial audit only**. This is not EntityOS/HCU runtime evidence, not tokenizer admission, not model inference evidence, not J-Space causal evidence and not training credit.

## 6. Swarm review

### EVIDENCE_EXTRACTOR

**Verdict: ACCEPT OBJECTIVE, BOUNDED SCOPE.**

The measured package supports targeting dynamic codebook binding and context-invariant routing while protecting already-strong semantic readout, writable emission and whitened carrier-space binding. It does not support inventing a positive Qwen3.5 J-Space causal label.

### DATASET_ARCHITECT

**Verdict: ACCEPT GENERATOR AS CANDIDATE SEED.**

The full S3 × class × template factorial directly attacks fixed-label and template shortcuts. The mapping is causal construction, not metadata. The 72 rows are suitable for generator/mechanism QA, not for declaring dataset coverage.

### ADVERSARIAL_SHORTCUT_HUNTER

**Verdict: CONDITIONAL / FOUR BLOCKERS.**

1. `A/B/C` are logical opaque placeholders, not yet admitted members of the measured 46-atom ABI for the final selected target tokenizer.
2. All 72 rows belong to one narrow semantic family (`COORDINATOR_LEASE_EPOCH_GATE_V1`); train/validation splitting inside this family would be leakage disguised as generalization.
3. The codebook still exposes human-readable class names inside the allowed span; a later label-free codebook challenger should test whether the model is learning semantic routing or label mediation.
4. The frozen unseen-template body must remain outside train and validation generation.

### STATISTICAL_REVIEWER

**Verdict: COUNTERBALANCE PASS; GENERALIZATION NOT MEASURED.**

The designed frequency table removes class-symbol association globally and independently within every admitted template. `MI(class; symbol)=0` for the constructed table. This does **not** establish independence from every lexical, positional or semantic-family feature. More independent semantic families and dedicated leakage statistics are required before scale-up.

### ABI_PROVENANCE_REVIEWER

**Verdict: BLOCK TRAIN-UPLOAD PROMOTION.**

Before promotion, bind the actual selected Qwen3.5 model/revision/tokenizer/runtime identity and verify the final symbol surfaces against the exact admitted tokenizer/ABI policy. The current logical `A/B/C` surfaces intentionally carry zero ABI-atom admission credit.

### RETENTION_REVIEWER

**Verdict: DO NOT OVERTRAIN THE DEFECT FAMILY.**

The defect decomposition argues against spending scarce capacity relearning semantics or carrier algebra that already measured well in the source package. Binding rows should be interleaved with Xeno authority/protocol retention anchors from the living functionality matrix. Exact mixture weight remains unfrozen until the two official Qwen3.5 candidates receive the same frozen baseline.

### HARNESS_COMPATIBILITY_REVIEWER

**Verdict: COMPATIBLE DIRECTION.**

The future `go`/Xeno harness should be able to inject an episode-local codebook, vary template/context, demand an exact single-symbol output, and score the realized mapping rather than a metadata permutation. It should separately score semantic decision correctness and mapping/emission correctness so a correct final symbol cannot hide the stage that failed.

### FINAL_INTEGRATOR

**Verdict: ADMIT AS `CANDIDATE_DATA` GENERATOR ONLY.**

Do not mark `VALIDATED_DATA`, do not render a final train/validation split, and do not scale to 20k–50k rows yet.

## 7. Updated training architecture hypothesis

The current high-value decomposition is a three-stage observable contract:

```text
S = semantic state / decision
M = episode-local mapping
Y = exact output identifier

semantic decode:      X -> S
binding/router:       (S, M, context) -> bound slot
emission:             bound slot -> Y
```

The Claude package suggests `X -> S` and direct emission control are already available in the measured source model, while the middle operator is the weak link. The fine-tuning objective should therefore emphasize the **middle composition** and use retention losses/evaluations to avoid damaging the surrounding read/write machinery.

A stronger future model-native version can express this as a low-rank semantic subspace plus an episode-conditioned routing transformation rather than as a single universal steering direction. The source evidence argues against assuming one global direction is sufficient.

## 8. Serious counterhypotheses

### C1 — Format/token routing, not abstract binding

The chance result may be caused by codebook parsing, position sensitivity or output-token mechanics rather than a general variable-binding deficit.

**Discriminator:** same semantic cases under matched token length, randomized codebook order, multiple surface templates, label-free codebook challenger and unseen output-symbol family. If the deficit disappears under one representation, the mechanism is narrower than general binding.

### C2 — Gabliterated-checkpoint-specific defect

The measured failure may not reproduce on either official Trigger-2 candidate.

**Discriminator:** run the frozen equal-budget zero-cost baseline on both exact source-identity candidates before weighting this family heavily.

### C3 — Superficial memorization after SFT

Training may drive seen-template accuracy above 0.9 while failing unseen template, unseen symbol and independent semantic-family holdouts.

**Discriminator:** promotion requires gains on family-isolated and symbol/template-isolated holdouts, not only training-format accuracy.

### C4 — Binding improvement damages semantic geometry/retention

A narrow SFT may improve codebook accuracy by distorting the semantic readout or broad language/protocol competence.

**Discriminator:** pre/post semantic readout, retention floors, off-target regressions and exact authority hard negatives remain mandatory.

## 9. Next exact Trigger-2 data gates

1. Run the same frozen binding baseline on both official Qwen3.5-0.8B candidates once exact runtime/build/consumed-byte identity is admitted.
2. Obtain/admit the exact 46-atom list and verify final train symbols under the exact selected tokenizer; keep a dedicated unseen-symbol holdout.
3. Add at least 4–8 **independent semantic families** (not paraphrases of the lease gate) and keep whole families together during splitting.
4. Add a label-free codebook challenger and compare against the human-label-mediated format.
5. Construct a genuinely frozen unseen-template family outside both train and validation.
6. Extend deterministic audits to vocabulary-family SHA-256, exact row ABI/source identity, template/order/position balance and mutual-information scans against nuisance features.
7. Only after the small seed survives the full swarm review should row count scale materially.

## 10. Research feedback into Clay / HCU

This result changes the architecture emphasis as well as the dataset:

- **Global J-Space should expose semantic state and episode-local routing state as separable observables.** A single monolithic vector is a poor diagnostic if semantics is present but binding fails.
- **The Xeno harness should score the interface decomposition**, not only final answer accuracy: semantic class, mapping resolution, exact emitted code, and context transfer should each be measurable.
- **Hyperposition should preserve unresolved mapping/binding alternatives** when the mapping itself is ambiguous; majority/recurrence must not force a code.
- **HCU peer packets should carry explicit mapping/provenance identity** so a node cannot apply a stale or foreign codebook while appearing semantically correct.
- **Training should install a routing protocol, not a second truth store.** Canonical state/effect authority remains deterministic outside the model.

## 11. Credit boundary

This Trigger-2 delta earns:

- generator/source-design progress: **YES**
- exact S3 causal-construction correction: **YES**
- deterministic combinatorial counterbalance check: **YES, local-only scope**
- model baseline evidence on official candidates: **NO**
- ABI/tokenizer symbol admission: **NO**
- validated training dataset: **NO**
- J-Space model runtime credit: **0**
- training credit: **0**
- whole EntityOS/HCU runtime credit: **0**
