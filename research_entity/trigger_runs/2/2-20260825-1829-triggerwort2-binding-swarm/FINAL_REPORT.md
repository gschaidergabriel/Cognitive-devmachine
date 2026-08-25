# Triggerwort 2 — binding-focused swarm training research run

Date: 2026-08-25 18:29 +07:00  
Organ: GPT-5.6 Sol / ChatGPT organ  
Persistent entity: Clay  
Product: EntityOS  
Architecture: HCU  
Target model: Qwen3.5-0.8B research target  
Branch: `research/trigger2-qwen35-08b-hcu-fullft-20260825`  
Main observed at reentry: `0edcc2ca0dba28fa0536bc5834fe6ede05a46e96`  
Supervisor observed: 8.78  
Execution mode: FREE_ONLY  
Training executed: NO  
Training credit added: 0

## 1. Trigger interpretation

Exact user text `triggerwort 2` is treated as a Trigger-2 training-research macrocycle. This run develops candidate training examples from current Claude Code measurements and current EntityOS/HCU owner target rather than performing a status-only response.

## 2. Current evidence that controls this run

The current Claude XENO vector-evidence ingest establishes, at the exact measured model snapshot only:

- semantic readability approximately 0.94-1.00 from about layer 6 onward on the measured lexical family;
- deep semantic direction stability around +0.75 to +0.78 at layers 17-23;
- baseline dynamic symbol hit `0.3611111111`, versus chance `0.3333333333`, with approximate one-sided binomial p `0.42246`;
- strong symbol-axis writeout at L23/L19 in measured interventions;
- HRR/MAP carrier binding capacity 1.0 through k<=16 after centering/whitening;
- measured semantic concept requires a low-rank subspace rather than one universal direction;
- static structural task target was not decodable;
- cross-template semantic binding was poor: mean L19 cross-transfer about `0.52546`; transfer into the T1 codebook template from T2/T3/T4 was exactly chance in the measured sample;
- verdict: the missing mechanism is best treated as context-dependent dynamic binding/routing between readable semantics and writable output symbols, not as missing semantic readout or missing carrier algebra.

The corrected ingest also identifies generator defects that must be fixed before any generated rows are admitted:

1. selected S3 permutation metadata did not actually determine the realized class<->symbol mapping;
2. S3 validation was too weak;
3. counterbalance tolerance was far too loose for the stated complete-counterbalance requirement;
4. class-word leakage checking was effectively hardcoded to pass;
5. lexical-disjointness checking did not cover all semantic-bearing material.

Therefore this run creates only `CANDIDATE_NOT_ADMITTED` rows and does not claim canonical dataset/training credit.

## 3. Swarm-review method

This run uses five explicit reviewer roles over every candidate. These are multiple review functions of this organ, not independent semantic replications.

### Architect reviewer
Checks target-architecture fit: dynamic codebook binding, role-flexible Xeno behavior, coordinator-only S1 writes, Hyperposition/GWT/J-Space boundaries.

### Leakage auditor
Checks label leakage, static class->symbol memorization, permutation leakage, lexical-family overlap and cross-model evidence laundering.

### Causal-evidence reviewer
Rejects `decodable => causal`, `transport => semantic control`, `Qwen3-0.6B => Qwen3.5 positive label`, and component evidence => whole-system promotion.

### Adversarial reviewer
Constructs shallow heuristics: line-position shortcut, prior-episode mapping, majority vote, stale lease acceptance, ACK=>effect-success, broadcast=>causal-use.

### Minimality reviewer
Removes redundant supervision and protects functions already measured as present. The new primary objective is routing/binding, not re-teaching semantic readout or carrier algebra.

A row survives only if all five roles pass it.

## 4. External research delta

### Variable binding
Wu, Geiger & Millière, *How Do Transformers Learn Variable Binding in Symbolic Programs?* (arXiv:2505.20896) train dereferencing programs with 1-4 hop chains plus irrelevant distractor chains and report emergence of systematic variable-binding behavior with causal routing through residual-stream/attention mechanisms.

**Dataset change:** add referential-depth 2-4 binding episodes with distractor bindings and explicitly adversarial early-line/nearest-binding heuristics. Do not limit training to direct one-hop class->symbol lookup.

### Context-dependent steering
Li, Li & Huang, *Steering Vector Fields for Context-Aware Inference-Time Control in Large Language Models* (arXiv:2602.01654) argue that a single static steering vector can fail when the locally useful direction varies with context and introduce context-dependent vector fields.

**Dataset change:** static-vector success inside a template is a hard negative for universal routing. Train context-conditioned mapping behavior and keep same-model causal validation separate.

### Encoded signal vs causal use
Zhou, McCoy & Frank, *Causal Interventions on Continuous Variables...* (arXiv:2605.29971) report a case where steering vectors encode error signals associated with in-context learning but those aspects are not causally used in downstream production.

**Dataset change:** add explicit `ENCODED_NOT_CAUSALLY_USED` rows. Decodability or transport alone must not become a positive J-Space-control label.

## 5. Candidate dataset delta

Created:

`research_entity/claycode/TRIGGER2_SWARM_BINDING_DATASET_CANDIDATE_V1.jsonl`

The file contains 18 source-level candidate rows. All are marked `CANDIDATE_NOT_ADMITTED`.

Coverage:

- 6-row full-S3 direct counterbalance block for one semantic family;
- depth-2 and depth-3 dynamic binding/dereference rows with distractors;
- cross-template context-invariant binding rows, including an unseen dialogue form;
- J-Space static-transport-without-behavior negative;
- J-Space encoded-but-not-causally-used negative;
- ordinary-node read-only authority row;
- stale coordinator lease rejection row;
- correlated-consensus/Goodman ancestry trap;
- Hyperposition unknown-effect preservation;
- GWT broadcast-without-causal-use negative;
- coordinator compression preserving counterevidence/ancestry;
- meta-review row rejecting Qwen3-0.6B -> Qwen3.5 semantic-control laundering.

## 6. Important correction to the training hypothesis

Previous shorthand could be interpreted as `semantic class -> output token` training. The stronger current hypothesis is:

`contextual semantic state`
` -> episode-local variable binding`
` -> optional multi-hop role/slot dereference`
` -> current codebook symbol`
` -> bounded output`

with distracting bindings and constantly changing mappings.

This is closer to installing an **addressable routing computation** than teaching another fixed vocabulary.

## 7. What must NOT dominate the corpus

Because those functions already have measured support at the Claude snapshot, do not spend the majority of specialization tokens on:

- basic semantic-class readability;
- a fixed one-dimensional semantic steering vector;
- raw symbol emission capability;
- HRR/MAP algebra up to k<=16.

They remain retention/protection/evaluation targets, not the primary learning target.

## 8. Generator v2 requirements before admission

The next deterministic generator must:

1. construct realized mappings from the selected S3 permutation, not merely log a permutation ID;
2. require exact six-permutation coverage per three-class family where applicable;
3. enforce per-class/per-symbol balance with max count difference <=1 and report class-symbol mutual information;
4. permit class labels only inside the declared episode codebook span unless a separately versioned label-free protocol is selected;
5. fail on target-class labels/synonyms outside that span;
6. split semantic-bearing lexical families by causal/provenance family, not random row;
7. randomize codebook order, answer position and distractor placement;
8. generate referential depths 1-4 with balanced depths and distractor chains;
9. reserve an unseen-template family and unseen ABI-symbol subset before tuning;
10. bind every candidate to ABI manifest, target model/tokenizer identity, generator version and ancestry key;
11. keep all Qwen3.5 positive J-Space labels empty until same-model causal evidence exists;
12. preserve failed/negative Qwen3-0.6B evidence as negatives/method examples only.

## 9. Proposed scorecard for the binding objective

Primary metrics after model selection and baseline freeze:

- direct S3 mapping accuracy;
- cross-permutation accuracy;
- referential-depth accuracy at 1/2/3/4 hops;
- distractor robustness;
- cross-template transfer;
- unseen-template transfer;
- unseen-symbol transfer;
- episode-reset accuracy after abrupt mapping swaps;
- static-prior trap error rate;
- class-symbol mutual-information residual shortcut score;
- off-target retention of measured semantic readability and output controllability.

A first behavioral acceptance threshold should preserve the Claude package's proposed target of >=0.90 for context-invariant binding and dynamic codebook binding, but the exact Qwen3.5 threshold must be frozen with the final generator/baseline protocol before holdout opening.

## 10. Training mixture delta

For the next candidate corpus, prioritize approximately:

- 35% dynamic codebook binding and multi-hop dereference;
- 20% context/template/symbol OOD transfer;
- 15% Xeno role/authority trajectories;
- 10% Hyperposition/GWT evidence-use trajectories;
- 10% J-Space evidence-class positives/negatives, with positive Qwen3.5 semantic-control rows currently zero;
- 10% operational retention/fail-closed anchors.

These are research priors only. They are not frozen training ratios and must be tuned without opening the sealed holdout.

## 11. Strongest counterhypotheses

### Hc1 — formatting memorization
The 0.8B model may learn codebook syntax and S3 surface forms without learning systematic binding.

Falsifier: depth-4 + unseen-template + unseen-symbol + distractor holdout after family-isolated training.

### Hc2 — shallow early-binding heuristic
The model may exploit position/order statistics rather than dereference relations.

Falsifier: balance target roots across positions and adversarially swap codebook/slot ordering.

### Hc3 — semantic router remains context-fragile
Fine-tuning may improve T1-like tasks but not transfer across syntactic contexts.

Falsifier: frozen T5/T6 templates with lexically disjoint semantic families.

### Hc4 — static steering remains merely transport
Post-train hidden-state displacement may grow without improving behavioral binding.

Falsifier: require matched counterfactual intervention to change the correct episode-local symbol under held-out mapping swaps.

### Hc5 — specialization destroys useful readout
Aggressive full FT may install routing while degrading semantic readout or protocol competence.

Falsifier: base-vs-posttrain retention matrix with hard floors; no aggregate score may hide a hard-floor failure.

## 12. Admission state

- source-level candidate examples: PRESENT
- deterministic generator v2: NOT YET IMPLEMENTED
- candidate-row schema validator: NOT YET IMPLEMENTED
- admitted Distillery training tokens from these rows: 0
- exact Qwen3.5 same-model J-Space positive labels: 0
- training executed: NO
- training credit: 0
- whole Xeno/HCU acceptance: 0

## 13. Next exact action

Implement a deterministic Trigger-2 binding generator v2 + validator that realizes exact S3 mappings, balanced referential depths, distractors, leakage checks, family split keys and unseen-template/unseen-symbol holdouts. Then generate a larger candidate corpus and run static validators only. Do not promote rows into admitted training truth until the canonical Forge/Distillery evidence path and exact current admission contracts accept them.
