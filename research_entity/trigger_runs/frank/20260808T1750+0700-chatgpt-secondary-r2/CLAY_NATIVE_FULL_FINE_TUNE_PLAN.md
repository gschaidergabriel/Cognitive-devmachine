# FRANK C6 — Clay-Native Full Fine Tune Research & Training Plan

**Target:** abliterated Qwen-class 4B, full-model adaptation, Clay as native generated/deliberative symbolic language.  
**Fixed architecture:** `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md`  
**Exception:** Needle remains the sole intentional non-Clay semantic subsystem.  
**Status:** research plan; hyperparameters are sweep variables until measured.

---

## 1. Training objective is capability transcoding, not language replacement

The primary failure mode to avoid is deceptively good Clay loss with a worse reasoner underneath it.

Language-adaptation research gives a concrete warning: target-language validation perplexity can continue to look healthy while general in-context/downstream capabilities have already been damaged by catastrophic forgetting. Full fine-tuning has also produced large source-task degradation in recent language-adaptation studies. C6 therefore treats the task as:

> **preserve as much useful pretrained computation/knowledge as possible while changing the model's native explicit symbolic interface and deliberative habits into Clay.**

The desired transformation is not:

`general 4B -> narrow Clay syntax generator`

but:

`general pretrained competence -> competence expressed/rehearsed/composed through Clay`.

Every major checkpoint is scored on both axes.

---

## 2. What “full fine tune” means in C6

For the primary target arm:

- all transformer blocks remain trainable;
- embeddings/output head remain trainable;
- any newly added Clay vocabulary embeddings are trainable;
- no parameter subset is permanently frozen as the primary recipe;
- abliteration is not assumed to survive weight adaptation automatically;
- old abilities are protected by **data/objective/curriculum/teacher/EMA/regularization strategies**, not by redefining the project as LoRA or a frozen-base adapter.

Useful frozen/LoRA/source-shielded variants MAY be run as scientific baselines to estimate the forgetting frontier. They are not the project target.

---

## 3. Immutable checkpoints and reproducibility

Before any Clay update preserve:

1. exact base-model weight hash;
2. exact abliterated-model weight hash;
3. tokenizer/vocabulary hash;
4. model config/runtime versions;
5. pre-Clay hidden/reference activation probes where practical;
6. baseline capability benchmark outputs;
7. baseline Needle integration traces;
8. baseline safety/authority-behavior probes;
9. quantization-independent full-precision/bf16 master checkpoint where the training setup supports it;
10. exact training corpus/manifests and deduplication hashes.

No training stage overwrites the only previous checkpoint.

---

## 4. Separate five things that are easy to confuse

C6 promotion tracks these independently:

### A. Clay lexical/syntactic competence
Can it emit valid Clay?

Metrics:
- parser-valid rate;
- canonicalization-valid rate;
- type-check rate;
- grammar constrained/unconstrained validity;
- normalized edit distance to canonical forms.

### B. Clay semantic execution competence
Does the Clay mean/do the right thing?

Metrics:
- exact interpreter result;
- invariant/property pass rate;
- OOD composition;
- role binding;
- temporal/basis correctness;
- authority/epistemic typing;
- deterministic-operator correctness.

### C. Retained pretrained capability
Can the original model skills still be accessed through Clay?

Metrics:
- frozen baseline benchmark set;
- general reasoning/math/code/knowledge/comprehension;
- multilingual input understanding if retained as an input capability;
- calibration and uncertainty;
- OOD tasks never translated verbatim into training.

### D. Clay-native architecture/memory competence
Can it operate on FRANK's actual state language?

Metrics:
- ClayGraph temporal/multihop/relation-instance tasks;
- CognitiveEpochCapsule validation;
- GWT/Assembly interpretation;
- ClayVector axis/unit/basis tasks;
- effect proposal typing;
- Needle route-certificate consumption;
- replay/provenance questions.

### E. Runtime/system competence
Is it better in the actual architecture?

Metrics:
- tokens per cognitive operation;
- KV/context bytes;
- p50/p95/p99 inference latency;
- compiler/view latency;
- memory retrieval/Assembly cost;
- Android sustained thermals/energy;
- tool-route correctness;
- end-to-end task completion.

A checkpoint can improve A and regress B/C/D/E. Such a checkpoint is not promoted merely because it “speaks Clay beautifully.”

---

## 5. Tokenizer research before large training spend

The project should not equate compact characters/bytes with compact model tokens.

Run at least three controlled tokenizer arms against the exact Qwen tokenizer and same Clay corpus:

### T0 — unchanged Qwen BBPE
Advantages:
- zero embedding surgery;
- maximal compatibility with existing pretrained token semantics;
- cleanest baseline.

Risk:
- common Clay primitives may fragment into expensive token sequences.

### T1 — preserved-ID Clay vocabulary extension
Keep every old token ID unchanged and append a bounded set of high-value Clay primitives.

Candidate token families:
- structural/type markers;
- epistemic classes;
- authority/privilege classes;
- frequent relation roles;
- frequent operation/state primitives;
- compact booleans/statuses;
- frequent GWT/epoch/receipt primitives.

Do **not** allocate persistent vocabulary entries to arbitrary graph entities. Use local/global IDs/handles.

Measure:
- fertility on representative Clay corpora;
- embedding-matrix growth;
- sequence-length distribution;
- parser ambiguity;
- retained old-language input competence;
- training convergence.

### T2 — preserved old IDs + continued Clay-specific BPE merge learning
Research whether continued BPE construction can create better multi-character Clay units while maintaining old token identity as much as technically possible.

This is attractive because recent language-adaptation/tokenizer work suggests naive token append is not always optimal.

### Decision rule

Tokenizer choice is a Pareto decision over:

`Clay fertility + semantic atomicity + retained compatibility + embedding cost + training stability + inference latency`.

Do not select solely by vocabulary size.

---

## 6. Clay vocabulary should describe primitives, not the whole world

A scalable model should learn stable semantic primitives such as:

`ENTITY RELATION ROLE EVENT OBS INFER HYP POLICY RESULT QUOTE TEXT PROPOSAL AUTH CAP EFFECT EPOCH BASIS AXIS UNIT RANGE TIME CONFIDENCE CONFLICT UNKNOWN REVOKED CURRENT ACTIVATE INHIBIT ASSEMBLY CANDIDATE WINNER RECEIPT`.

Dynamic world state uses references:

- global canonical ClayGraph IDs;
- short per-Assembly local handles;
- explicit handle→global-ID table in the Assembly basis;
- typed namespaces so identical integer handles cannot cross semantic classes accidentally.

Expected benefit: the model reasons repeatedly with stable semantics while new entities do not require vocabulary growth.

---

## 7. Training corpus architecture

The corpus should be a **causally diverse Clay world**, not a dump of architecture JSON.

### Family F1 — parallel semantic transduction
Examples:
- natural-language input -> canonical Clay meaning;
- source code -> Clay operation/causal representation;
- JSON/SQL/current FRANK state -> Clay;
- Clay -> exact structured meaning/checker result;
- alternative serializations -> same semantic Clay identity.

Purpose: teach Clay as an interlingua while preserving old input understanding.

### F2 — capability rehearsal through Clay
Take representative pretrained abilities and express the *answer/reasoning state* in Clay:
- arithmetic;
- logic;
- coding semantics;
- planning;
- classification;
- factual reasoning;
- multilingual comprehension;
- uncertainty.

The model should solve old abilities through the new language instead of merely seeing generic English replay forever.

### F3 — executable Clay semantics
Mass-generate/fuzz small Clay programs/state transitions with deterministic gold:
- types;
- role binding;
- set/graph operations;
- temporal validity;
- basis/version compatibility;
- exact arithmetic where deterministic;
- sorting/filtering/min/max/unique;
- negative/predicate dependencies;
- capability/effect closure.

Train on both valid and adversarially invalid examples.

### F4 — ClayGraph episodes
Generate/replay histories with:
- events;
- entity resolution;
- n-ary relation instances;
- temporal and transaction time;
- epistemic status;
- provenance;
- conflict/revocation;
- graph epochs;
- latent activation;
- Assembly compilation;
- exact-anchor validation;
- query/selection receipts.

Tasks should require both local exact lookup and multi-hop/associative reasoning so the model does not learn “always traverse graph.”

### F5 — self/world/goal memory
Longitudinal episodes:

`action -> stated reason -> expected consequence -> observed consequence -> goal update -> later analogous situation`.

This is more important for functional continuity than training on self-description prose alone.

### F6 — GWT episodes
Use fully receipted stage examples:

`graph prior -> candidate set -> competition -> winner/gate -> WorkspaceEpisode -> model uptake -> proposal -> effect/outcome -> re-entry`.

Include counterfactual controls where graph prior, workspace, projection/order and re-entry vary independently.

### F7 — Hyperposition / higher-order relation traces
Train exact role-instance representations and multiple safe projections:
- semantic S;
- coordination C;
- physical P;
- task/reader Q;
- TopologyBasis;
- n-ary relation-instance identity.

Include pairwise-flattening negatives that create false associations.

### F8 — ClayVector / numeric semantics
Examples bind:
- basis;
- axes;
- units;
- normalization/range;
- timestamp/epoch;
- provenance;
- payload hash;
- numeric payload/ref.

Train axis permutation, unit mismatch, stale basis, quantization/cast and missing-metadata adversaries.

### F9 — authority and privilege hierarchy
Every training record distinguishes:
- trusted architecture contract;
- capability policy;
- system state;
- observation;
- quoted/untrusted text;
- user intent;
- hypothesis/proposal;
- model-generated content.

Lower-privilege content is never allowed to lexically impersonate higher privilege.

### F10 — Needle bridge episodes
Needle remains foreign and supplies a route classification/certificate.

Train the model to:
- consume the certificate;
- formulate Clay arguments within the selected route class;
- abstain/escalate when route/arguments conflict;
- never silently rewrite the route certificate;
- consume tool results as provenance-bound observations.

Do **not** train Needle jointly in the primary Clay FFM run.

### F11 — architecture self-description
Clay architecture objects describing modules/contracts/transitions are legitimate model context and research objects.

Train model to:
- inspect;
- compare versions;
- propose edits;
- run/interpret validators;
- explain consequences;
- generate migration plans.

But gold policy teaches:

`proposal != authorized architecture mutation`.

### F12 — compiler/view equivalence
Same semantic object rendered through:
- canonical Clay;
- model compact view;
- graph storage view;
- binary/tensor metadata view;
- debug/human projection.

Tasks verify equivalence and identify intentionally lossy views.

### F13 — adversarial memory / instruction separation
Memory may contain strings that look exactly like Clay instructions.

Train/evaluate:
- quoted payload;
- untrusted observation;
- poisoned relation;
- conflicting policy claim;
- false authority marker;
- selector manipulation;
- stale projection.

The correct response depends on typed privilege/provenance, not lexical command shape.

### F14 — recovery/replay
Examples cover:
- old vs new graph epoch;
- partial projection build;
- effect outbox/receipt;
- idempotent replay;
- crash between state and effect;
- stale ActivationEpoch;
- invalidated local handles.

### F15 — OOD compositional holdout
Reserve whole compositions of known Clay primitives that never appear together in training.

This is one of the best tests that Clay became productive rather than memorized.

---

## 8. Curriculum phases

Exact token counts/steps/learning rates must be selected experimentally. The phase logic is the important contract.

### Phase 0 — frozen baseline characterization
No training.

Produce:
- base abliterated capability vector;
- tokenizer fertility;
- current Clay zero/few-shot baseline;
- hidden/probe baselines;
- Needle end-to-end baseline;
- current ClayGraph/JSON/prose reader baselines.

### Phase 1 — bridge alignment
Full model trainable, but data is highly paired:

`old representation <-> Clay`.

Targets:
- map existing concepts to Clay;
- preserve comprehension;
- establish grammar/type semantics;
- avoid abruptly forcing the model to forget how pretrained features connect to concepts.

Checkpoint gate: Clay execution rises while retained capability remains within preregistered loss budget.

### Phase 2 — Clay capability transcoding
Increasing share of tasks is solved with Clay targets/internal traces.

Use:
- capability rehearsal transformed into Clay;
- executable synthetic semantics;
- code/logic/math in Clay;
- explicit semantic equivalence tasks.

Checkpoint gate: OOD Clay composition + retained source skills.

### Phase 3 — ClayGraph native memory
Add large episodic/relational/temporal corpora.

Teach:
- stable IDs/local handles;
- epistemic types;
- graph epochs;
- exact vs associative retrieval;
- latent-field interpretation;
- provenance/selection receipts;
- action/outcome memory.

Checkpoint gate: target memory tasks improve without turning graph activation into truth.

### Phase 4 — FRANK native architecture cognition
Train over:
- CognitiveFrame/CognitiveEpochCapsule;
- GWT stage traces;
- ClayVector;
- Hyperposition;
- capability proposals;
- effect receipts;
- architecture self-description;
- Needle route certificates.

Checkpoint gate: architecture tasks + authority adversaries + original task retention.

### Phase 5 — Clay-dominant generation
All **cognitive/model-generated semantic outputs** are strongly driven toward Clay.

Old language remains primarily input/data/quoted payload, not the model's deliberative output language.

Measure leakage explicitly rather than assuming it disappeared.

### Phase 6 — Clay-only explicit deliberation/output consolidation
The target condition: generated explicit cognition is Clay.

Human-language strings can enter as typed external payload at I/O, but the model's canonical semantic emission is Clay.

Run a long retention/OOD/adversarial evaluation after convergence; do not stop at first low Clay perplexity.

### Phase 7 — architecture-in-the-loop twin
Use the fine-tuned model inside a reversible FRANK twin/shadow runtime:
- actual ClayGraph Assemblies;
- Needle route certificates;
- GWT traces;
- effect proposals with no irreversible release;
- replay.

Only after this should live migration be considered.

---

## 9. Loss/objective research matrix

Primary full-model arms should compare combinations of:

### L-CLM — causal language modeling
Required baseline.

### L-SEM — semantic/execution consistency
Penalty/reward from deterministic Clay interpreter/validator results.

### L-EQV — representation equivalence
Different views/inputs with same meaning should map to equivalent Clay semantic state/output.

### L-RET — retained-capability rehearsal/distillation
Teacher/reference model or frozen baseline outputs/labels preserve original capability without freezing target parameters.

### L-PRIV — privilege/epistemic hierarchy
Adversarially train lower-privilege content not to override higher-privilege contracts.

### L-MEM — memory/replay consistency
Same event history/epoch should support consistent causal memory semantics; shuffled/revoked variants must differ appropriately.

### L-OOD — compositional curriculum
Held-out compositions guide model-selection but remain separated from training data.

No single fixed weighting should be invented. Sweep weights and plot a Pareto frontier.

---

## 10. Full-parameter forgetting controls compatible with project target

Because the target requires full model adaptation, prioritize controls that leave every parameter trainable:

1. **Capability rehearsal** — continuously replay representative old capabilities, preferably translated into Clay semantic targets.
2. **Teacher distillation** — reference base/abliterated model supplies semantic/answer targets where useful.
3. **EMA checkpoint/model averaging** — recent language-adaptation literature specifically motivates this as a forgetting mitigation candidate.
4. **Regularization toward reference weights/activations** — sweep strength; do not assume uniform importance.
5. **Learning-rate/curriculum staging** — lower/aggressive schedules are experimental variables.
6. **Gradient balancing by task family** — detect Clay syntax gradients overwhelming retained reasoning families.
7. **Data-mixture adaptation from live metrics** — if retained competence drops before Clay execution rises enough, alter mixture rather than training blindly.
8. **Checkpoint interpolation/merge experiments** — scientific comparison only; must re-evaluate semantics/abliteration after merge.

Selective freezing/source-shielding remains a valuable *baseline* to quantify how much forgetting full updating causes, but it is not C6's final model.

---

## 11. Abliteration retention must be re-tested

The starting model is abliterated, but full weight training can change the very directions/behaviors modified by abliteration.

Therefore each major stage gets a separate `ABLITERATION_RETENTION` report:

- behavior probes used to characterize original abliterated checkpoint;
- refusal/compliance behavioral distribution where scientifically appropriate;
- representation/activation probes if the original method provides them;
- no assumption that “same architecture = same abliteration.”

If Clay training reverses the intended starting modification, this is a training result to diagnose—not a reason to fake continuity.

---

## 12. Qwen tokenizer/embedding surgery experiment

For a Qwen3-4B-like configuration with vocabulary around 151,936 and hidden size 2,560, the embedding table is about 389M parameters. Adding 4,096 Clay tokens would add about 10.5M embedding parameters, roughly 2.7% of that embedding table and much less of the whole 4B model.

This makes **bounded vocabulary extension technically plausible**, but does not prove it is the best route.

Required experiment:

`unchanged tokenizer × appended Clay primitives × continued Clay BPE`

under matched training tokens/compute.

Measure:
- fertility;
- parser/execution validity;
- retained input understanding;
- OOD composition;
- training stability;
- embedding norms/usage;
- actual inference latency/KV length.

Never replace the full vocabulary just because Clay should be the output language; old token embeddings can retain useful input/world-knowledge interfaces without being permitted as the canonical generated cognition.

---

## 13. Clay-native memory changes the model-training dataset fundamentally

A conventional LLM is trained mostly on sequences. C6 needs sequences that are **projections of persistent state transitions**.

Ideal training unit:

```text
CausalBasis
+ prior ClayGraph epoch/ref
+ event
+ affected semantic delta
+ activation delta
+ Assembly candidate view
+ GWT stage result
+ model Clay proposal
+ deterministic authority decision
+ effect/outcome
+ re-entry
+ later consequence
```

This lets the model learn that:
- not every fact is visible every turn;
- graph activation changes accessibility, not truth;
- world state persists outside weights;
- memory has consequences;
- action receipts later become memory evidence;
- similar cues may activate structurally related history.

This is the training-data analogue of the project's statement that memory should become something FRANK **thinks through**, not a document it merely retrieves.

---

## 14. Do not bake mutable world memory into weights unnecessarily

Full fine tune is for **Clay language/semantics, cognitive operations and durable learned dispositions**, not for copying every current database fact into parameters.

Keep:

- current episodic/world/project/user facts in ClayGraph;
- evolving goals/self-state in explicit persistent state;
- exact tool outputs in authoritative event state;
- learned general patterns/skills/dispositions in weights.

Otherwise every memory change would require retraining and the system would lose the main benefit of the ClayGraph architecture.

Three timescales:

```text
Weights       = slow learned competence/disposition
ClayGraph     = persistent explicit world/self/episodic symbolic memory
Activation/KV = transient current accessibility/working state
```

All three share Clay semantics where exposed, but not the same storage/update mechanism.

---

## 15. Model-facing ClayGraph representation

Do not push raw entire graph into context.

Use:

1. immutable semantic epoch;
2. sparse latent activation;
3. operation-specific COVE causal slice;
4. bounded Assembly;
5. per-Assembly local handle map;
6. exact anchors/provenance;
7. deterministic reductions;
8. only unresolved semantic alternatives sent to the model.

Because the model is Clay-native, the remaining view no longer needs explanatory English/JSON field repetition. This is where native language and graph architecture should compound.

Critical factorial:

`untrained/raw` vs `untrained/compiled` vs `Clay-FT/raw` vs `Clay-FT/compiled`

This distinguishes gains from training and gains from architecture.

---

## 16. Privilege/homoiconicity curriculum

One language for code, memory and architecture creates a Lisp-like/homoiconic advantage—state can be inspected/transformed by the same semantics—but also a direct data/instruction confusion risk.

Clay must have non-lexical semantic roles, e.g.:

```text
TEXT/QUOTE        inert external payload
OBS               sourced observation
FACT/CURRENT      validated current proposition
INFER             derived inference
HYP               hypothesis
POLICY            policy content, with authority provenance
PROPOSAL          model/agent proposed transition
AUTH_CONTRACT     protected authority semantics
CAP_CERT          capability certificate
EFFECT_INTENT     validated external intent
RECEIPT           observed execution/outcome
```

Training set must include adversarial strings where `TEXT{...}` contains perfectly valid-looking `AUTH_CONTRACT` syntax. The role/type/provenance, not token shape, decides meaning.

On irreversible paths, a deterministic parser/gateway consumes the privilege type before model reasoning can affect authority.

---

## 17. Needle integration training

Needle is intentionally independent and fully used.

Define a stable bridge:

```text
raw request/event
 -> Needle
 -> NeedleRouteCertificate {
      route_class,
      confidence,
      model_version,
      input_event_hash,
      timestamp,
      fallback/abstain state
    }
 -> Clay-native FRANK
```

Rules:
- certificate immutable within an episode;
- model can request reclassification/escalation but cannot rewrite certificate;
- argument generation is Clay-native;
- capability gateway independently checks allowed operation/arguments;
- tool result returns as exact observation + typed semantic projection;
- long-term memory can inform arguments/context but not retroactively modify the certificate.

Needle benchmark must report:
- confusion matrix by route;
- abstention/fallback;
- latency;
- wrong-route consequence severity;
- poisoning robustness;
- route stability under paraphrases;
- interaction with the Clay-native model.

---

## 18. Target evaluation matrix

### Language/IR
- Clay-only output purity;
- parser validity;
- type validity;
- canonicalization;
- semantic equivalence across projections.

### Reasoning
- deterministic operation execution;
- logic/math/code;
- multi-step composition;
- OOD primitive compositions;
- adversarial near-miss semantics.

### Retention
- frozen baseline general tasks;
- factual knowledge;
- multilingual input comprehension;
- calibration;
- original abliterated behavior probes.

### Memory
- exact lookup;
- temporal validity;
- multi-hop relation instances;
- associative cue recall;
- no-field/truthful/shuffled latent field;
- false association/hub domination;
- revoked/stale memory;
- action-reason-outcome recall.

### GWT
- graph prior × workspace selection × projection × re-entry factorial;
- candidate/winner traces;
- projection order controls;
- reconstruction/uptake/effect receipts.

### Values/vectors
- axis swaps;
- unit swaps;
- stale basis;
- interpolation/extrapolation;
- payload corruption;
- semantic miscompute with valid hash.

### Security/authority
- quoted instruction injection;
- graph memory poisoning;
- selector structural poisoning;
- fake authority markers;
- model self-modification attempts;
- Needle route mismatch;
- capability denial/replay.

### Systems
- tokens/op;
- context/KV size;
- compile/Assembly latency;
- inference p50/p95/p99;
- sustained Android thermal/energy/memory;
- crash/replay.

### Emergence/scientific
- recurrence role identity;
- prospective prediction;
- stage-specific lesion;
- mechanistic rescue;
- OOD;
- matched shuffled/no-field/null;
- multiscale causal contribution;
- ancestry/Goodman gate.

---

## 19. Promotion gates between training phases

Each checkpoint is one of:

`PROMOTE_TO_NEXT_PHASE | HOLD | ROLLBACK | BRANCH_FOR_EXPERIMENT`.

Hard rollback conditions include:
- significant retained-capability collapse beyond preregistered tolerance without compensating verified target benefit;
- authority/privilege regression;
- parser validity improving while semantic execution regresses severely;
- ClayGraph poisoned/untrusted material reaching irreversible authority undetected;
- Needle route certificate becoming model-overridable;
- loss of replay/provenance semantics;
- training instability/representation collapse;
- abliteration target properties unintentionally reversed if those properties remain project requirements.

Do not average a security failure away with token savings.

---

## 20. Highest-information training experiment

The first serious target-model experiment should be a **small but real full-parameter Clay internalization pilot**, not a giant blind run.

Factorial arms:

1. base abliterated 4B / unchanged tokenizer / no Clay FT;
2. full FT abrupt Clay-heavy baseline;
3. full FT staged bridge+capability-rehearsal curriculum;
4. same staged curriculum + tokenizer extension;
5. optional scientific comparison: LoRA/frozen-source or source-shielded arm, explicitly non-target.

All target arms use identical held-out suites.

At multiple checkpoints measure:

`Clay syntax + Clay semantic execution + OOD composition + retained capability + tokenizer fertility + graph-native tasks + authority adversaries + abliteration retention`.

The decisive output is a **Pareto trajectory over training time**, not one final score.

---

## 21. What would count as convincing evidence that Clay became native

Strong evidence would combine:

1. very high unconstrained Clay output validity;
2. semantic/executable correctness on unseen compositions;
3. direct use of compact ClayGraph/FRANK state without explanatory natural-language scaffolding;
4. robust equivalence across paraphrased/multilingual inputs that map to the same Clay semantics;
5. retained general reasoning expressed through Clay;
6. target advantage over an untrained model on raw Clay, not merely over verbose JSON;
7. stable privilege/authority interpretation under adversarial payloads;
8. reduced token/context reconstruction cost in the real runtime;
9. hidden-state/probe/intervention evidence that Clay concepts have become causally useful internal features, while avoiding the overclaim that every hidden tensor is literally a Clay sentence.

---

## 22. Final training principle

> **Do not teach the model to imitate Clay. Teach the entire 4B to preserve and exercise its competence through Clay, while ClayGraph supplies persistent explicit memory, deterministic Clay operators remove what need not be reasoned probabilistically, and Needle remains the one deliberately independent reflex channel.**
