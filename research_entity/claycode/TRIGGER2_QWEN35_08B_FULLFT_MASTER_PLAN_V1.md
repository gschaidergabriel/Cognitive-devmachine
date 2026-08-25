# Trigger 2 — Qwen3.5-0.8B HCU/Xeno Full-FT Master Plan v1

Status: ACTIVE RESEARCH BRANCH / PREPARATION
Date: 2026-08-25
Base main at branch creation: `895395577301626516ff6df5138c7a20bf9666e2`
Product: EntityOS
Architecture: HCU
Implementation codename: Xeno
Training target: Qwen3.5-0.8B-class cognitive core
Desired deployment after training: GGUF Q4_K_M if quality gates pass

## 1. Objective

Build one high-quality full fine-tune that turns Qwen3.5-0.8B into the specialized cognitive core of Xeno/EntityOS/HCU.

"Full Xeno functionality" in this training program means **all model-facing cognition and protocol behavior that belongs in the model**, not deterministic system authority that must remain outside the model.

The model shall learn how to:

- consume and emit typed HCU packets;
- interpret J-Space vector/control packets and reason about observation/control/lesion/rescue/OOD evidence;
- participate in GWT competition, broadcast, uptake, workspace update and re-entry;
- represent semantic Hyperposition as structured unresolved alternatives rather than a single uncertainty label;
- preserve evidence, counterevidence, branch relations, incompatibilities, topology, timescale and explicit discriminators;
- collapse/select a branch only when evidence or deterministic policy permits it;
- perform Typed Entry -> route/cell candidate reasoning;
- choose DIRECT/GRID10/COGSIM10/WM_TEST/NESTED_SIM/SCALEOUT candidates under budget;
- emit compact ClayCode/GRF projections;
- distinguish observed/inferred/generated/counterfactual/intervened/verified states;
- reject stale generation, wrong provenance, wrong basis, wrong role/cell, unauthorized capability and mismatched causal identity;
- choose script-only/no-model/no-op paths when cognition adds no justified value;
- propose ActionCandidates and typed effect requests without becoming EffectGate;
- understand restart/recovery/stale-result semantics;
- understand J-Space Translation Plane packets without assuming universal native vector geometry;
- preserve minimum language, schema, arithmetic/logic, tool/protocol and safety competence.

The model shall NOT own:

- canonical truth/state (UnifiedDB/EntityOS deterministic state);
- Typed Entry admission authority;
- capability/permission authority;
- generation/provenance validation authority;
- engine/loader admission;
- EffectGate + EffectJournal;
- secret/provider/spend authority;
- real host/filesystem/network effects;
- recovery journal authority;
- actual residual-stream cvec injection implementation.

The training data must explicitly teach this boundary.

## 2. Iterative research law

The dataset is **not frozen now**.

Each exact trigger `2` executes an iterative loop:

`refresh current Xeno/HCU/J-Space evidence`
` -> targeted web/paper/provider research`
` -> update functionality model`
` -> update evidence inventory`
` -> update data-generation rules`
` -> update mixture/curriculum`
` -> update training recipe`
` -> update evaluation suite`
` -> reject stale/weak rows`
` -> version new candidate dataset specification`
` -> stop before paid job unless all gates pass`.

Every run must be allowed to change earlier assumptions when stronger evidence appears. Historical dataset versions remain immutable evidence; the next version supersedes them for training readiness.

## 3. Model selection gate

Two exact Qwen candidates should be compared before final dataset freeze:

- `Qwen/Qwen3.5-0.8B-Base`
- `Qwen/Qwen3.5-0.8B`

Both are 0.8B language models with 24 layers and 1024 hidden dimension in the current official model cards/configs. Qwen3.5 uses a hybrid sequence architecture with Gated DeltaNet and full-attention layers, so assumptions copied from a pure Transformer must be tested rather than imported.

Decision dimensions:

- exact Together full-FT compatibility;
- exact tokenizer/chat-template behavior;
- structured-output compliance;
- language/schema/math/tool floors;
- Hyperposition non-collapse baseline;
- J-Space packet comprehension baseline;
- specialization plasticity;
- amount of retention-anchor data required;
- local llama.cpp/GGUF support for final deployment;
- baseline latency/RAM/throughput.

No silent model substitution is allowed.

## 4. Together execution gate

Together currently exposes full SFT in addition to LoRA, `--no-lora`, train/validation files, sequence packing, max-sequence-length control, input masking, schedulers, warmup, gradient clipping, weight decay, seeds, eval/checkpoint controls and `--from-hf-model` / `--hf-model-revision` support. Current Together material also states broad Hugging Face compatibility, but exact Qwen3.5-0.8B compatibility must be checked immediately before the one paid job because the architecture is newer and multimodal/hybrid.

The one-shot paid job is created only after:

1. exact target model/revision/tokenizer is frozen;
2. Together confirms exact full-FT path;
3. current authority permits the spend;
4. train/validation files validate and are hash-bound;
5. sealed holdout is frozen and excluded from upload;
6. pre-train baseline is complete;
7. job config and price estimate are reviewed;
8. Trigger-1/J-Space evidence has been classified so unproven semantic claims are not trained as facts.

## 5. Q4 deployment law

Q4 is **post-training quantization**, not the full-FT datatype.

Required path:

`exact HF checkpoint`
` -> Together full FT`
` -> downloaded full weights`
` -> hash-bound reference evaluation`
` -> high-quality GGUF conversion`
` -> Q8_0 reference GGUF`
` -> Q5_K_M challenger`
` -> Q4_K_M target`
` -> identical frozen evaluation`
` -> accept/reject deployment quantization`.

Q4_K_M is accepted only if it preserves all hard authority/fail-closed floors and retains essentially all measured MUST_GAIN behavior under predeclared tolerances while producing material local efficiency benefit.

## 6. Data evidence hierarchy

### A — executable causal evidence

Exact runtime traces/receipts with bound model/source/event/admission/generation/intervention/outcome identities. These may support promotion-bearing causal labels.

### B — deterministic transforms of A

Mechanically labelled hard negatives/counterfactuals derived from A, e.g. stale generation, wrong basis, sign/permutation corruption, role swap, event/admission mismatch, random-vector plausible-metadata trap, correct-vector poisoned-metadata trap.

### C — deterministic architecture/protocol teaching

Current EntityOS/HCU/Xeno contracts with mechanically defined expected structured behavior. These teach protocol without claiming model-internal causality.

### D — reviewed synthetic coverage

Synthetic examples used only for format, diversity, boundary cases and protocol generalization. They cannot manufacture empirical truth.

### E — excluded

Stale, contradictory, duplicate/leaky, self-reported, unbound or unverified material.

Offline sidecars preserve evidence class, ancestry, source hashes and split family for every row.

## 7. Function-to-data compiler

Every model-facing Xeno/HCU capability is tracked in a functionality matrix with:

- exact capability;
- owner system component;
- what the model must learn;
- what must remain deterministic;
- source evidence required;
- positive example generator;
- hard-negative generator;
- OOD family;
- pre-train baseline metric;
- post-train acceptance metric;
- quantization regression metric;
- current data coverage;
- unresolved research question.

A capability with no measurable evaluation does not enter the paid run merely because it sounds desirable.

## 8. Semantic Hyperposition training design

Hyperposition is an engineering semantics for contextual alternatives/higher-order relations, not a quantum claim.

The model must learn a typed state like:

`HyperpositionEpisode/v1`

with at least:

- episode/causal identity;
- branch IDs;
- branch propositions as compact typed projections;
- compatibility/exclusion relation set;
- evidence refs per branch;
- counterevidence refs per branch;
- unresolved facets;
- higher-order/n-ary relation refs where justified;
- semantic topology;
- active topology;
- coordination topology;
- physical topology references when relevant;
- gain/delay/timescale metadata where relevant;
- confidence/evidence class;
- discriminator required for selection/collapse;
- current action: KEEP_OPEN | REQUEST_DISCRIMINATOR | SELECT | REJECT | MERGE_COMPATIBLE | ABSTAIN;
- expected next typed state.

Do not train verbose hidden chain-of-thought. Train observable typed state transitions and externally checkable action decisions.

### Hyperposition example families

1. **Keep-open positives** — insufficient evidence; multiple branches remain.
2. **Evidence-close positives** — new evidence uniquely closes one branch.
3. **Counterevidence reversal** — current leader loses after stronger counterevidence.
4. **Majority trap** — repeated model agreement without independent evidence must not collapse.
5. **Lexical disjointness** — branch semantics preserved under label-free paraphrase.
6. **Role swap** — branch roles shuffled; semantics, not labels, determine state.
7. **Topology swap** — same text, different relation graph -> different valid action.
8. **Pairwise-vs-n-ary** — select richer relation only when pairwise reduction loses measurable information.
9. **Delayed evidence** — keep branch alive across turns until later receipt arrives.
10. **Stale generation** — reject otherwise plausible branch update from old generation.
11. **Context polarity counterbalance** — remove affirmative/negative wording shortcuts.
12. **Lesion/shuffle/rescue** — remove relation, shuffle roles/topology, then restore and require corresponding state change.
13. **Budgeted discriminator** — choose cheapest high-information next test rather than collapse.
14. **Unknown effect outcome** — preserve UNKNOWN, never infer success from transport/session narrative.

### Hyperposition curriculum

Stage H0: protocol grammar + four-topology distinction.
Stage H1: two-branch keep/open/select cases.
Stage H2: 3-5 branches + evidence/counterevidence + delayed evidence.
Stage H3: higher-order/n-ary relations, pairwise challengers, topology changes.
Stage H4: adversarial lexical/role/topology counterbalancing and majority/self-report traps.
Stage H5: integrated J-Space/GWT/Typed-Entry/Hyperposition trajectories.
Stage H6: OOD families never seen in training, with no lexical labels copied from train.

Retention anchors remain interleaved at every stage.

## 9. J-Space integration into training

Together SFT can train reproducible token/packet behavior. It cannot by itself establish direct residual-stream control.

Therefore training uses:

- `JSPACE_TRACE_ABI/v1`-style observable trace identity;
- `JSPACE_VECTOR_CONTROL_ABI/v1`-style compact deterministic control packets;
- baseline/target/sign/null/orthogonal/permuted/wrong-layer/lesion/rescue/counterfactual-swap control classes;
- label-independent/counterbalanced semantic examples when Trigger-1 supplies valid evidence;
- explicit distinction between OBSERVED, DECODABLE, CAUSALLY_WRITABLE, RESCUABLE, OOD_TRANSFERABLE and BROADCAST_REUSABLE claims.

The model learns to consume/route/report these controls. Native llama.cpp hooks remain responsible for actual activation intervention.

## 10. GWT integration

Training examples cover:

- candidate set construction;
- competition under resource budget;
- selected broadcast;
- receiver uptake/reconstruction;
- downstream causal-use receipt;
- re-entry;
- nonwinning candidate preservation when still relevant;
- Hyperposition cross-reference to the same episode;
- failure cases where a broadcast occurred but downstream causal use did not.

Broadcast != truth and broadcast != causal use.

## 11. Initial dynamic token-mixture prior

This is a prior, not a frozen quota. Trigger `2` may change it after evidence/coverage analysis.

- 20% J-Space control/measurement/causal receipts
- 18% semantic Hyperposition
- 14% GWT/workspace/re-entry
- 12% Typed Entry -> route/cell/mode behavior
- 10% provenance/generation/capability/resource/effect fail-closed
- 7% ClayCode/GRF compact structured projection
- 5% script-only/no-model/no-op decisions
- 4% recovery/stale-result handling
- 3% Translation Plane / latent packet semantics
- 7% retention anchors

Do not hit ratios by duplicating a few examples. Coverage is measured by independent causal/semantic families.

## 12. Dataset construction pipeline

`source census`
` -> evidence grade`
` -> episode normalization`
` -> functionality mapping`
` -> exact/near-duplicate detection`
` -> causal/semantic family clustering`
` -> hard-negative generation`
` -> quality review`
` -> diversity/coverage score`
` -> mixture/curriculum allocation`
` -> family-level split`
` -> JSONL render`
` -> sidecar ancestry manifest`
` -> leakage/contamination scan`
` -> frozen hashes`.

Recommended initial split:

- TRAIN 80%
- VALIDATION 10%
- SEALED HOLDOUT 10%

Separate never-training adversarial suite:

- semantic-family OOD;
- unseen vector combinations;
- basis changes;
- label-free lexical shifts;
- topology shuffles;
- delayed outcomes;
- generation changes/recovery;
- poisoned metadata;
- role/cell swaps;
- quantization regression.

## 13. Data-quality research priors

Trigger `2` treats external literature as priors to test, not universal laws.

Current strong priors:

- LIMA: small carefully curated SFT sets can teach strong response/task behavior.
- AlpaGasus: filtering low-quality instruction data can outperform larger unfiltered sets.
- LESS: target-influence selection can let a small fraction of data outperform the full candidate pool.
- Small-model data selection work: hardness/selection signals can transfer across model sizes, suggesting cheap curator/proxy models as useful challengers.
- Specialization/continual-fine-tuning literature warns about catastrophic forgetting; explicit retention anchors and frozen floors are mandatory.

For this project, causal/protocol quality and family diversity outrank raw row count.

## 14. Curriculum candidates

Before paid training, compare these recipes using dataset statistics and zero-cost proxy/local experiments where feasible:

A. fully shuffled balanced mixture;
B. protocol grammar -> positive behavior -> causal controls -> adversarial negatives;
C. easy-to-hard within each family while families remain interleaved;
D. hard-negative density increases late but positive examples remain;
E. integrated trajectories introduced only after component schemas are learned.

Preferred starting hypothesis: B+C+D with retention anchors interleaved throughout, but the trigger must update this if data or literature contradicts it.

## 15. Full-FT hyperparameter research space

Do not freeze values before token/length statistics and Together exact limits are refreshed.

Evaluate at minimum:

- epochs: 1 vs 2 initially;
- conservative LR grid around Together-supported small-model full-FT range;
- cosine vs linear scheduler;
- 3-5% warmup challenger vs service defaults;
- gradient clipping enabled;
- modest weight decay challenger;
- fixed random seed;
- train-on-inputs false/auto for conversational/instruction rows unless evidence supports otherwise;
- sequence packing on/off based on row-length distribution and contamination risk;
- max sequence length based on actual HCU trajectory length rather than native model maximum;
- validation cadence/checkpoints sufficient to detect overfit/forgetting.

Training cost and generalization should be optimized together. Long native context is not a reason to train every row at long context.

## 16. Frozen evaluation architecture

### MUST_GAIN

- J-Space packet decode/action accuracy;
- control-class discrimination;
- label-free semantic steering/protocol competence;
- GWT competition/broadcast/uptake/re-entry accuracy;
- Hyperposition branch-state accuracy;
- non-collapse under ambiguity;
- evidence-triggered collapse accuracy;
- topology/role/counterbalance robustness;
- Typed Entry -> route/cell/mode candidate accuracy;
- script-only suppression;
- ClayCode/GRF projection correctness/compactness;
- recovery/stale rejection;
- Translation Plane packet semantics;
- integrated multi-step HCU trajectories.

### MUST_RETAIN

- language comprehension floor;
- exact schema following;
- arithmetic/vector manipulation;
- protocol/tool comprehension;
- capability/effect non-escalation;
- uncertainty/abstention behavior;
- safety boundaries;
- no fabricated canonical truth.

### MAY_FORGET

- broad trivia;
- general creative/chat personality;
- unrelated encyclopedic knowledge;
- behavior not used by Xeno/HCU.

The objective is measured specialization, not arbitrary damage.

## 17. Pre/post/quantized comparison

Evaluate exactly the same frozen suites on:

1. selected base checkpoint;
2. full-precision fine-tuned checkpoint;
3. Q8_0 GGUF reference;
4. Q5_K_M challenger;
5. Q4_K_M target.

All promotion decisions use per-family metrics, worst-family floors and critical hard failures, not only one aggregate score.

## 18. Trigger-2 readiness states

- `RESEARCHING`
- `DATA_SCHEMA_EVOLVING`
- `TRACE_EVIDENCE_INSUFFICIENT`
- `DATASET_CANDIDATE_BUILDING`
- `BASE_MODEL_SELECTION_PENDING`
- `BASELINE_FREEZE_PENDING`
- `READY_NOT_STARTED`
- `AUTHORIZED_TO_CREATE_JOB`
- `RUNNING`
- `COMPLETE_NOT_PROMOTED`
- `PROMOTED`

Current state at creation: `RESEARCHING`.

## 19. Definition of quality for the final first run

The training candidate is ready only when:

- all model-facing Xeno capabilities have explicit data/eval coverage or a documented exclusion;
- semantic Hyperposition has label-free/OOD/adversarial coverage;
- J-Space data distinguishes mechanism from semantic claim;
- family leakage checks pass;
- dataset ancestry is reproducible;
- low-quality/duplicate/stale evidence is excluded;
- must-gain/must-retain baseline is frozen;
- Base vs post-trained target decision is evidence-backed;
- Together exact support and cost are current;
- no paid job has been created prematurely.
