# Triggerwort 2 — rendered nuisance leak + control-plane drift fusion

Date: 2026-08-26  
Organ: GPT-5.6 Sol / ChatGPT organ  
Trigger: `triggerwort 2`  
Persistent entity: Clay  
Product: EntityOS  
Architecture: HCU  
Mode: FREE_ONLY  
Status: CURRENT RESEARCH DELTA / NONPROMOTING / SUCCESSOR-DYNAMIC

## Authority re-entry

Observed canonical `main` before write: `5cf690be978ee8ce98b819e6004478f39c68d6b8`.

Current `SUPERVISOR_INBOX.json` selects supervisor 8.81 and places two load-bearing gates ahead of new training/provider execution:

1. owner FreeSwarm emergency-stop runtime quiescence must be proven;
2. Trigger-2 `binding_router_factorial_generator_v3` remains blocked from direct training for conditional nuisance leakage.

No paid/provider/model execution was performed in this cycle. No unusual experiment was performed.

## R0 — current observed repository evidence

### A. v3 binding generator contains a direct model-visible leakage mechanism

Current main file:

`tools/trigger2_binding_router_factorial_generator_v3.py`

For every P1 row, codebook entry order is generated with:

`stable_shuffle(CLASSES, f"P1|{tid}|{pool_name}|{base}|{polarity}|P{pid}")`

`base` is the hidden semantic state used to derive the target, while the resulting `codebook_entry_order` is rendered into the model-visible prompt. Therefore a supposedly nuisance serialization feature is deterministically conditioned on a target-causal hidden variable.

This is a concrete mechanism for the supervisor's existing `BLOCKED_FROM_DIRECT_TRAINING_CONDITIONAL_NUISANCE_LEAKAGE` disposition.

### B. current v3 internal audit does not test the decisive rendered nuisance channel

The v3 audit checks split counts, target-from-mapping correctness, S3 target balance, polarity pairs and coarse class/symbol balance. It does not perform semantic ablation on rendered prompt bytes and does not estimate whether the remaining rendered surface predicts target above episode-local chance.

Therefore `audit(...).pass == true` is mechanism sanity only and cannot establish shortcut independence.

### C. owner FreeSwarm stop remains inconsistent with committed live telemetry

Canonical:

`research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json`

states `OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF` and all Groq/Mistral/NVIDIA/OpenRouter provider admissions are false.

But the latest committed `free swarm/SYSTEM_ANALYSIS_LIVE.json` at the observed main was generated at `2026-08-25T20:27:20.875353Z` and still reports:

- `go_swarm = RUNNING`
- `distillery = RUNNING`
- `evidence_forge = RUNNING`
- an embedded stale provider-admission snapshot with all four providers admitted
- OpenRouter `last_observed_at = 2026-08-25T20:26:53.868254Z`

This is stronger than a stale source-only mismatch: it is committed evidence that a long-lived runtime path continued to operate with stale admission state after the canonical emergency-stop authority had changed. Source hard-off must not be reported as runtime quiescence.

## R1 — exact algebraic reconstruction of the v3 P1 leak

A deterministic independent reconstruction of the exact P1 factorial algebra was performed from the current source logic. This is NOT repository-bound runtime credit; it is a source-derived discriminator calculation.

For the TRAIN P1 factor:

- 4 templates
- 3 base semantic states
- 2 polarities
- 6 S3 permutations
- total 144 P1 rows

Construct a semantic-ablated model-visible nuisance key from:

- template identity
- query polarity
- fully rendered ordered codebook mapping

while removing the scene's semantic payload.

With the current `base`-dependent shuffle seed:

- rows: 144
- distinct ablated nuisance keys: 111
- Bayes-optimal exact-key target lookup: `0.7708333333333334`
- episode-local chance: `0.3333333333333333`

Most groups become singleton or two-row groups instead of balanced three-target groups.

Minimal counterfactual source change tested algebraically:

change the order seed from

`P1|tid|pool|base|polarity|pid`

to a seed independent of `base`, e.g.

`P1|tid|pool|polarity|pid`.

Under the same reconstruction:

- rows: 144
- distinct ablated nuisance keys: 48
- every key has exactly one example of each target
- exact-key target lookup: `0.3333333333333333`

Interpretation: removing `base` from codebook-order randomization is a high-information minimal repair candidate. It is not sufficient by itself for training admission.

## R2 — new gate design: T2_RENDERED_NUISANCE_GENERALIZATION_GATE_V2

Existing PRs #2005 and #2007 are useful donor lanes because they move the proof object from hidden metadata to the rendered model-visible prompt. Do not create a competing binder implementation merely for authorship.

However exact-signature balance is only the first layer. A small model can exploit compressible features shared across non-identical prompts, including token length, token IDs, positions, template/polarity interactions and codebook-order patterns.

A successor gate should require ALL of the following on exact final serialized rows:

1. **Rendered semantic-ablation exact-key gate**
   - mask only the semantic payload whose evidence determines the base state;
   - preserve role-typed authoritative ABI fields such as codebook mapping and query polarity;
   - require every ablated exact nuisance key to contain all three targets equally;
   - require exact-key Bayes lookup = 1/3.

2. **Tokenizer-bound nuisance gate**
   - run with the exact selected Qwen3.5-0.8B checkpoint/tokenizer identity;
   - compute token-ID sequence, token count, target token length and target position;
   - reject target-predictive token-length/position artifacts;
   - maintain frozen train/validation/holdout atom-family disjointness.

3. **Cross-validated shallow nuisance-only challengers**
   On semantic-ablated rendered bytes/tokens, fit only cheap deliberately weak predictors:
   - character n-gram classifier;
   - token n-gram classifier;
   - structured interaction classifier over template, polarity, codebook order, symbol shape/length and positional buckets.

   Use family-disjoint validation/holdout. Any stable target accuracy materially above preregistered chance tolerance rejects the corpus.

4. **Higher-order interaction audit**
   Pairwise zero MI is not sufficient. Explicitly test interaction subsets and conditional predictors because target leakage may exist only in combinations such as `template × polarity × order × mapping`.

5. **Negative controls that MUST fail**
   - inject a visible target hint;
   - make target-symbol length class-correlated;
   - make codebook order depend on base state;
   - make only a template×polarity interaction target-correlated.

6. **Positive balanced control that MUST pass**
   A fully crossed construction in which nuisance rendering is conditionally independent of semantic class/target after preserving authoritative role-typed inputs.

### Important authority distinction

Do NOT demand unconditional independence between target and every model-visible field.

The episode-local codebook mapping is an authoritative binding input: the desired target is a function of semantic decision state plus current codebook. Removing or decorrelating the codebook would destroy the task.

The correct condition is:

- authoritative semantic/binding fields remain learnable;
- non-authoritative rendering/nuisance features must not add predictive target information once semantic evidence is removed/controlled according to the declared gate.

## R3 — serious counterhypotheses

### CH1 — eliminating base-dependent order is enough

Possible because the identified seed channel is strong and direct.

Falsifier: after the minimal seed repair, any family-held-out nuisance-only classifier remains above chance on exact rendered/tokenized rows.

### CH2 — semantic ablation can over-mask legitimate evidence structure

If masking destroys role/position information actually needed for the intended cognitive process, the gate can incorrectly call useful ABI structure nuisance.

Falsifier: define role-typed authoritative fields before ablation; require positive controls where those fields causally affect the correct target and must remain predictive.

### CH3 — binder shortcut risk is checkpoint-specific and source balance may overconstrain unnecessarily

A mathematically available shortcut may not be learned by the selected 0.8B checkpoint.

Response: source-level elimination is still preferable when cheap because it removes a known confound before expensive causal interpretation. Model-specific training/eval remains required afterward; source balance does not mint model credit.

## External method research reinjected (noncanonical)

Current web research supports the revised gate but does not mint EntityOS/Qwen credit:

- Wu, Geiger & Millière, *How Do Transformers Learn Variable Binding in Symbolic Programs?* (arXiv:2505.20896): training can move through shallow heuristics before systematic variable binding; causal interventions are used to establish mechanism.
- Shaib et al., *Learning the Wrong Lessons: Syntactic-Domain Spurious Correlations in Language Models* (arXiv:2509.21155): syntactic correlations can override intended semantics and motivate explicit within-domain syntactic diversity and shortcut tests.
- Shuieh et al., *Assessing Robustness to Spurious Correlations in Post-Training Language Models* (arXiv:2505.05704): post-training methods remain sensitive to spurious feature structure; no single tuning method eliminates the problem.
- Basu et al., *Interpretability without actionability* (arXiv:2603.18353): high internal readout/probe performance does not establish controllable downstream behavior; intervention/off-target tests remain separate.
- Peng et al., *Enhancing Input-Label Mapping in In-Context Learning with Contrastive Decoding* (arXiv:2502.13738): input-label mapping can be underused relative to pretrained priors, reinforcing direct dynamic-codebook evaluation.
- Official `Qwen/Qwen3.5-0.8B` config currently reports hidden size 1024, 24 layers and a hybrid layout of three linear-attention layers followed by one full-attention layer repeated through the stack. J-Space instrumentation must therefore be architecture/layer-specific rather than assuming a uniform standard decoder hidden-state path.

## Fusion decision

### Keep

- v3's actual S3 mapping, counterfactual groups, polarity factorialization and separate OOD axes as donor mechanisms;
- PR #2005/#2007 rendered-prompt semantic-ablation idea as a necessary gate;
- family-disjoint split and exact tokenizer identity requirements;
- causal READ/BIND/WRITE separation and intervention/off-target evaluation.

### Revise

- remove hidden semantic state from any nuisance/rendering randomization seed;
- promote rendered semantic-ablation from optional audit to mandatory pre-admission gate;
- add shallow cross-key generalization challengers and tokenizer-level probes;
- require gate mutation tests proving known target-hint/order/length/interaction leaks are rejected.

### Do not do now

- no new positive training rows;
- no direct fine-tuning;
- no J-Space representation promotion;
- no provider execution while FreeSwarm runtime quiescence is unproven;
- no duplicate binder implementation lane while current PR donors exist.

## Priority order after this Trigger-2 cycle

P0. Quiesce/receipt all pre-existing FreeSwarm provider-capable processes on the live host and prove no provider usage delta over a bounded observation window.

P1. Fuse the minimal v3 serialization repair into the single retained binder lane: remove `base` from codebook-order shuffle identity, then run rendered semantic-ablation on exact serialized rows.

P1. Add tokenizer-bound and shallow nuisance-only generalization challengers; require negative-control sensitivity.

P2. Only after nuisance gates pass, freeze exact Qwen3.5 checkpoint/tokenizer + ABI atom partitions and materialize a small family-disjoint candidate pilot.

P2. Keep positive row admission closed until current producer/provenance/evidence and Forge→Distillery persistent-token gates pass.

P3. After exact runtime evidence and dataset gates, run model-specific READ/BIND/WRITE + variable-N + causal intervention/rescue/off-target evaluation before any training/J-Space promotion.

## Credit boundary

- research delta: 1
- source-derived discriminator: 1
- new positive rows admitted: 0
- accepted dataset tokens: 0
- checkpoint selection credit: 0
- J-Space model/representation credit: 0
- training credit: 0
- physical GRID10 runtime credit: 0
- full HCU runtime credit: 0
- whole EntityOS runtime credit: 0

No component/source calculation in this report is whole-product or training evidence.
