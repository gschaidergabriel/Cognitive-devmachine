# CLAYCODE RESEARCH RUN — CC11 Certified Multi-Rail Semantic Compiler

**run_id:** `claycode-20260808T2015p0700-chatgpt-secondary-r2`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent ClayCode:** CC10 / `CC-RC1.5 Intent-Certified Semantic Lowering`  
**primary FRANK target:** C6 `Clay-Native Unified Cognitive Substrate`  
**fresh global input:** Fusion R4 `CLAY-L5 Five-Plane AI-Native Speech Contract`  
**fresh empirical input:** NVIDIA Hosted NIM generic-4B + embedding cross-branch run  
**deep substrate:** ClayGraph C4/G1d HOLD  
**candidate:** **CC-RC1.6 — Certified Multi-Rail Semantic Compiler (MRSC)**  
**promotion:** **NONE**

---

## 1. Executive synthesis

CC10 solved the upstream intent problem:

`external intent -> proposal -> adequacy evidence -> committed IntentContract -> COVE/CBCC`

Fusion R4 then exposed a new problem. After canonical meaning exists, there is no reason to assume one literal surface is simultaneously optimal for:

- exact durable semantics;
- a small model reader;
- a fully Clay-adapted model;
- inter-agent symbolic communication;
- hidden-state/latent communication;
- wire/IPC transport;
- debugging and audit;
- hot-path runtime execution.

Fresh direct 4B evidence makes this more than an architectural preference. On `nvidia/nemotron-mini-4b-instruct`, an operation-specific compiled COVE view improved a matched 12-case task from **4/12 to 11/12** while prompt tokens fell **458 -> 289 (-36.9%)**. But on a separate 16-case intent task, verbose typed L1 improved only **12/16 -> 13/16** while prompt tokens grew **405 -> 733 (+81%)**; a compact Clay-like P2 proxy failed the required 16-output contract entirely.

Therefore:

> **There is no current evidence for one globally optimal Clay surface.**

CC11 introduces the OPEN candidate:

# CC-RC1.6 — Certified Multi-Rail Semantic Compiler

```text
P0 external intent
   ↓
CC-RC1.5 ICSL
   ↓
P1 CANONICAL CLAY
exact typed semantics + COVE causal slice + authority dependencies
   ↓
OP.RAIL_PLAN
   ├── CANONICAL_DIRECT
   ├── P2 DISCRETE_NATIVE
   │      deterministic/learned symbolic Clay view
   │      + dual-bound ProjectionReceiptV2
   │
   ├── P3 LATENT_NATIVE
   │      hidden-state / KV / embedding communication
   │      + LatentChannelReceipt
   │
   └── HYBRID
          P2 anchors + P3 bandwidth
   ↓
model / agent cognition or communication
   ↓
RailReturnProposal
   ↓
OP.RECONCILE_TO_CANONICAL
   ↓
ReconciliationReceipt + canonical ClayProposal
   ↓
existing CBCC/COVE / capability / effect gateway
   ↓
effect -> outcome -> re-entry receipts
```

The architecture remains **one semantic Clay world**, but that no longer means one syntax, one tensor form or one reader representation.

The strongest new hard requirement discovered by CC11 is:

> **A critical projection receipt must bind both the canonical source semantics and the exact emitted reader view.**

A new 100,000-case mutation fuzz found that source-only binding left **20,112 unsafe accepts** in the constructed family because projected value changes could occur while canonical source identity remained unchanged. Adding exact emitted-view binding plus role/class/epoch/value validation rejected all 100,000 constructed mutations. This is a mechanism result, not a production security guarantee.

---

## 2. Mandatory seven-branch grounding

`INTERCONNECT_MANIFEST.json` covers all seven registered scientific branches in required ClayCode priority:

`FRANK -> Clay -> ClayGraph -> GWT -> Hyperposition -> Emergenz -> ClayCode`.

The GitHub connector does not execute repository Python, so the authoritative preflight implementation was read and a structurally equivalent manifest was materialized. Strong promotion is therefore disabled.

### 2.1 FRANK C6 — primary target feedback

C6 already has the right semantic direction:

- `CLAY_CANONICAL` is exact semantic source-of-truth;
- `CLAY_MODEL` is a reader/model-oriented bounded view;
- `CLAY_GRAPH`, `CLAY_WIRE`, `CLAY_VECTOR`, `CLAY_PLATFORM` are distinct forms;
- hidden activations remain continuous physical state;
- model output is proposal, not authority;
- vector/tensor state carries explicit basis/type/shape/provenance;
- effect release remains externally capability-gated.

CC11 does not reverse C6. It refines two things.

First, `M.CLAY_VIEW_COMPILER` should become a **multi-rail compiler/planner** rather than privilege one CLAY_MODEL surface.

Second, continuous hidden-state/KV communication deserves an explicit **functional P3 causal identity**. It remains non-canonical and non-authoritative, but current latent-communication evidence makes it too important to lump entirely into passive physical implementation.

### 2.2 Clay G10 — COVE remains upstream truth boundary

COVE compiles the smallest trusted operation-specific causal slice. CC11 keeps that exact role.

The new rule is:

> **Rail optimization happens after the required semantic slice is known.**

This avoids a dangerous inversion where a compact representation decides which semantics matter. `OP.RAIL_PLAN` can optimize reader fit, tokens, latency or communication bandwidth but cannot remove required causal dependencies.

### 2.3 ClayGraph C4/G1d — explicit deep substrate findings

ClayGraph changed CC11 materially.

#### Supported
ClayGraph's existing distinctions remain correct and are now central:

`exact truth != semantic graph != latent activation != Assembly != model projection`

Its immutable semantic epochs, explicit relation-instance roles, exact anchors, activation ancestry and bounded Assemblies are precisely the metadata MRSC needs for safe projection receipts.

#### Changed
CC11 adds a second meaning of "latent" that must be separated from ClayGraph's current one:

- **ClayGraph `latent_activation_field`** = sparse event/cue-driven memory salience over a pinned semantic epoch;
- **MRSC `LATENT_NATIVE`** = transient model/agent hidden-state communication/cognition.

They can interact, but they are different causal stages, have different version/alignment requirements and must never share authority implicitly.

#### Challenged
Fresh NVIDIA embedding evidence directly challenges any future ClayGraph shortcut that uses dense similarity as canonical directed relation identity. In two constructed relation pairs, role-reversed relations were **more similar** than role-preserving paraphrases. Same surface content across FACT / ACTIVATION_PRIOR / PROPOSAL / AUTHORITY classes also remained highly similar.

Therefore embeddings/latent geometry may retrieve or rerank; exact role-aware semantic anchors define identity.

#### New persistence rule
ClayGraph may persist:

- exact anchors;
- projection/channel versions;
- semantic alignment receipts;
- reconciled canonical proposals/results;

but **raw latent payloads do not become canonical truth by being stored, frequent or similar**.

### 2.4 GWT R4 — rail identity becomes another orthogonal stage

GWT R4 showed a general identifiability failure: a bundled graph/workspace/projection comparison can report a large apparent workspace effect even when the constructed true workspace effect is zero.

MRSC extends this method boundary:

```text
canonical WorkspaceEpisode
 -> rail choice
 -> reader projection/alignment
 -> reconstruction/uptake
 -> effect
 -> re-entry
```

A workspace lesion cannot simultaneously change rail medium and still attribute the entire result to workspace selection.

### 2.5 Hyperposition H4 — semantic firebreak survives all rails

H4's strongest rule survives:

> one Clay language must not become one semantic failure domain.

FACT, OBSERVATION, ACTIVATION_PRIOR, PROPOSAL, AUTHORITY_CAP and EFFECT_INTENT remain non-interchangeable classes even if they share vocabulary or latent neighborhood.

CC11 strengthens H4 with exact **emitted-view binding** and keeps the compact hot-path direction: semantic identity can lower to packed handles rather than verbose text if reconstruction is deterministic and scope/epoch/role integrity is retained.

### 2.6 Emergenz E1 — native speech is not emergence evidence

CC11 makes no emergence or consciousness promotion.

Neither of these is sufficient:

- stable native symbols;
- high codebook purity;
- successful latent communication;
- cross-rail agreement;
- recurrent protocol use.

For P3 latent communication, E-CERT2 should add truthful/shuffled/zero/foreign-message interventions, matched training/extra-pass controls, mechanistic rescue, future/re-entry recovery and OOD transfer.

### 2.7 ClayCode history

CC-RC1.4 CBCC/COVE closure and CC-RC1.5 ICSL remain intact.

CC11 adds the missing middle-to-reader layer:

`canonical operation meaning -> certified rail selection/projection -> model cognition -> canonical reconciliation`.

---

## 3. Fresh direct 4B evidence

The NVIDIA cross-branch run is the most important new empirical input after CC10.

### COVE operation view

| Arm | Correct | Prompt tokens | Total tokens |
|---|---:|---:|---:|
| raw multidimensional state | 4/12 | 458 | 538 |
| compiled operation view | 11/12 | 289 | 368 |

This supports a deterministic-before-generative, operation-specific model boundary on at least one actual hosted generic 4B.

### Intent views

| Arm | Result | Prompt tokens |
|---|---:|---:|
| raw L0 | 12/16 | 405 |
| typed L1 | 13/16 | 733 |
| compact Clay-like P2 | output-contract failure | 344 |

The typed surface trades a modest correctness gain for large token cost. Derived under utility

`U = accuracy - lambda*(prompt_tokens/1000)`

typed beats raw only for `lambda < 0.19055` in this tiny measured task. This is not a universal economic threshold; it demonstrates that the preferred representation depends on the reader/task/cost objective.

### Dense representation negative control

NVIDIA `nv-embedqa-e5-v5` produced:

- Alpha inhibits Beta vs Alpha suppresses Beta: 0.9362
- Alpha inhibits Beta vs Beta inhibits Alpha: **0.9918**
- Gamma activates Delta vs same-role paraphrase: 0.9685
- Gamma activates Delta vs Delta activates Gamma: **0.9860**

This directly motivates exact role/anchor witnesses around dense or latent representations.

---

## 4. External research fusion

### MLIR — multiple levels and dialects are normal compiler architecture

LLVM MLIR independently demonstrates that one program can pass through multiple abstraction levels and dialect-specific representations while retaining a common compiler infrastructure. Transfer to ClayCode: semantic unity does not require serialization unity.

### Persistent e-graph / equality-saturation work

Current equality-saturation research makes another idea plausible: retain several equivalent program forms rather than committing to one representation too early. New MLIR/e-graph work explores persistent e-graph representations across optimization/lowering stages.

CC11 does **not** adopt unbounded equality saturation. Current research also documents tractability, analysis-soundness and memory/strategy problems. The transfer is a bounded `view-equivalence set`: preserve multiple validated reader candidates only while cost and proof obligations remain controlled.

### Agent Intermediate Representation

2026 AIR work independently compiles framework code and natural-language agent instructions into a conservative formal IR for static checks. This converges with ClayCode's separation between flexible source/agent-facing forms and inspectable executable semantics.

### Interlat / latent communication

ACL 2026 Interlat demonstrates agent communication through continuous last hidden states, including heterogeneous model setups, and reports competitive task performance with substantial compressed-inference acceleration in its experiments.

Transfer: P3 is technically plausible as a functional rail.

Non-transfer: this does not make the latent vector canonical meaning, truth or authority. Nor does endpoint performance alone identify which message information was causally used.

### Capabilities / proof-carrying actions

Current capability-safe agent-language and proof-carrying-action research independently preserves a boundary between agent-generated intent/proposal and externally checkable authority/effect evidence. CC11 therefore leaves the existing capability gateway unchanged.

### Translation validation

Compiler-verification research supplies a useful design pattern: rather than trust every optimizing transformation merely because the compiler is trusted, validate the concrete lowering/result against source semantics or proof obligations.

CC11 applies this selectively to critical discrete projections:

`canonical source + emitted view -> translation validation receipt`.

Latent rails require a different test because a hidden vector does not have a simple lossless structural roundtrip.

---

## 5. CC11 experiments

Full machine-readable results: `EXPERIMENT_RESULTS.json`.

### EXP-CC11-DUAL-BIND-FUZZ-001

100,000 seeded constructed mutations across:

- relation-role swap;
- semantic-class cast;
- stale epoch;
- semantic-ID substitution;
- projected value change.

Results:

- naive compact value/handle path: **79,888 unsafe accepts / 100,000**;
- source-bound receipt v1: **20,112 / 100,000**;
- dual-bound receipt v2 + semantic checks: **0 / 100,000** in the constructed family.

The key discovery is the v1 failure: **source identity does not bind the exact payload that reached the reader.**

This sharpens FRANK C6's existing ProjectionProofReceipt concept into an explicit ClayCode invariant:

`canonical_input_hash + projected_view_hash`.

Zero remaining failures is only a local property-fuzz result over five mutation classes.

### EXP-CC11-RAIL-PARETO-002

Derived analysis of the measured NVIDIA 4B results shows that representation choice is task-dependent:

- COVE compiled view Pareto-dominates raw on correctness and prompt tokens in its task;
- typed intent gives a modest correctness gain at much higher token cost;
- compact P2 is infeasible under the tested output contract.

Therefore the compiler should choose from a constrained rail/view set rather than freeze one surface globally.

### EXP-CC11-LOSS-BUDGET-003

Constructed 100k calibration:

- 20 semantic fields;
- each operation requires 2–6 fields;
- arbitrary fixed five-field compact view preserved the required slice in only **1.32%** of cases;
- operation-compiled required-only view preserved 100% by construction with mean **4.00196 fields**.

Inference: compactness should be defined relative to the operation's trusted semantic slice, not by a globally short syntax.

---

## 6. Goodman anti-echo review

Full artifact: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

### View compiler necessity — REFINED

FRANK's deterministic View Compiler is strengthened by the actual generic-4B COVE result, but becomes a multi-rail compiler rather than one fixed reader surface.

### Compact native Clay benefit after full-model adaptation — UNRESOLVED

Generic untrained 4B failure does not falsify the owner-target full-model Clay adaptation. It does falsify the shortcut that compact notation itself is evidence of native fluency.

### Hidden activations as merely physical implementation — REFINED

Continuous state remains physical/non-canonical, but latent communication literature justifies an explicit functional P3 rail and causal identity.

### Model output != authority — SUPPORTED

Independent capability/proof-carrying agent research continues to support deterministic external effect mediation.

### Vectors require exact semantic anchors — SUPPORTED

Fresh NVIDIA embedding negative controls provide direct evidence that similarity alone does not preserve directed role identity or semantic class.

### Projection source/output binding — SUPPORTED / sharpened

The new CC11 discriminating fuzz directly demonstrates why source-only binding is insufficient in the constructed model.

---

## 7. CC-RC1.6 semantic contract

Machine-readable candidate: `CC_RC1_6_MRSC.claycode.json`.

### New states

`S.RAIL_PLAN`
- operation semantics;
- causal slice;
- reader profile;
- effect class;
- candidate rails;
- loss budget;
- selected rail;
- planner/version.

`S.PROJECTION_RECEIPT_V2`
- canonical input hash;
- exact projected view hash;
- schema/compiler/reader identity;
- semantic anchor refs;
- role-binding hash;
- basis epochs;
- declared loss;
- required-semantics coverage;
- validation refs.

`S.LATENT_CHANNEL_RECEIPT`
- source envelope;
- payload/ref hash;
- sender/receiver model and layer;
- alignment adapter;
- compression/fusion method;
- basis epochs;
- semantic anchors;
- causal-use-test status;
- channel version.

`S.RAIL_RETURN_PROPOSAL`
- every rail returns proposal state only.

`S.RECONCILIATION_RECEIPT`
- binds the rail return to a canonical proposal and records anchor coverage, role identity, semantic-class validity, unknowns and contradictions.

### Different proof obligations

**P2 discrete rail** can use structural/reference/differential translation validation.

**P3 latent rail** cannot claim semantics from a tensor hash. It needs provenance/alignment identity plus canonical reconstruction and, for scientific communication claims, causal message-content interventions.

### Existing boundaries retained

Nothing in MRSC bypasses:

- ICSL intent adequacy;
- COVE causal slice;
- selection integrity;
- semantic-class firebreaks;
- capability gateway;
- effect/outcome/re-entry receipts.

---

## 8. New negative results

1. One fixed compact surface as universal Clay model view — **not supported**.
2. Canonical richness as automatically optimal reader representation — **not supported**.
3. Source-only projection receipt — **insufficient in CC11 constructed fuzz**.
4. Payload hash = semantic equivalence — **rejected category error**.
5. Embedding similarity = directed relation identity — **contradicted by current NVIDIA constructed pairs**.
6. Latent performance gain alone = message-content causality — **rejected without controls**.
7. ClayGraph latent field = model latent rail — **rejected causal-stage collapse**.
8. Cross-rail agreement = replication — **rejected shared-ancestry error**.
9. Unbounded equality saturation as default Clay runtime — **not justified**.
10. Rail planner = authority — **rejected**.

---

## 9. Highest-information next experiments

### P1 — Exact target-Qwen multi-rail factorial

On the actual full-model-adapted Qwen-class 4B target compare:

1. raw/external P0;
2. canonical/typed P1;
3. trained discrete-native P2;
4. latent-native P3;
5. P2+P3 hybrid.

Hold task/gold/training compute/context/runtime constant. Measure:

- semantic correctness;
- compositional/OOD transfer;
- retained general capability;
- token fertility;
- latency/RAM/KV/energy;
- repair rate;
- projection/reconciliation error;
- role/class/authority violations.

### P2 — Latent message causal-use factorial

Compare same-message, shuffled-message, zero-message and foreign-task message while matching extra passes, sender/receiver training and token/compute budget. Add lesion/rescue and future/re-entry outcomes.

### P3 — Target translation validation

Port `CC_RC1_6_MRSC_REFERENCE.py` semantics into target Rust/C runtime and run stateful/property fuzz over:

- aliases/local handles;
- class casts;
- stale epochs;
- reordered/n-ary roles;
- lossy omissions;
- source/view hash mismatches;
- concurrent projection-version changes.

Then add solver/formal properties when available.

### P4 — ClayGraph field x model latent rail

Cross independently:

`GRAPH_FIELD {off, truthful, shuffled}`

with

`MODEL_LATENT {off, truthful, shuffled}`

while pinning semantic graph epoch, visible Assembly facts, P1 semantics, workspace and projection. This tests whether memory salience and neural communication contribute independently or interact.

### P5 — End-to-end effect attack

In live/twin FRANK inject semantic errors separately into:

- P1 canonical input;
- P2 projected view;
- P3 latent alignment/message;
- reconciliation;
- capability state.

Measure where semantic firebreaks contain cognitive errors before authority/effect contamination.

---

## 10. Final scientific disposition

**CC-RC1.6 MRSC is an OPEN research candidate. No canonical promotion.**

The evidence is now strong enough to change the research architecture:

1. direct generic-4B evidence supports operation-specific deterministic views;
2. direct generic-4B evidence rejects assuming arbitrary compact symbols are already a useful native language;
3. dense embedding evidence supports exact role/class anchors;
4. latent communication evidence makes a distinct P3 rail worth testing;
5. CC11's new fuzz exposes a concrete projection-receipt gap and supplies a minimal repair;
6. independent compiler research supports multi-level IR, explicit lowering and translation-validation patterns.

But the central claim remains open until the actual target model is trained and measured:

> **A Clay-native FRANK may work best not because it has one alien syntax, but because one exact Clay semantic world can compile itself into the representation best suited to each cognitive operation while preserving a provable path back to canonical meaning and external authority.**

That is the current ClayCode frontier.
