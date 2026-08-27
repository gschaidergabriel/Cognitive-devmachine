# FRANK Test 1 — Clay-Native Full Architecture Simulation Contract

**Status:** PROJECT-OWNER FIXED TEST TARGET — PLANNING ONLY
**Date:** 2026-08-09
**Training authorization:** NONE. No Together fine-tune/inference job is authorized by this document.

## 0. Owner-fixed objective

Test 1 is an end-to-end experiment of a **fully repository-simulated FRANK architecture** around a Qwen-class 4B model that has received a **language-only ClayCode LoRA**.

The order is strict:

1. finish ClayCode as an executable language/semantic IR;
2. freeze and validate it;
3. teach the 4B only to read, reason and speak ClayCode natively;
4. verify ClayCode competence independently;
5. attach the model to a repository-driven simulation of the complete current FRANK architecture;
6. advance the full FRANK state machine on every message/turn;
7. if coherent, use the simulated FRANK for large experiment batteries while budget remains.

The LoRA must NOT be used to smuggle the FRANK architecture into model weights by imitation. FRANK remains the external architecture. The model is its Clay-native semantic transform kernel.

---

## 1. Hard language boundary

### Human-facing ingress

If the user speaks German or another natural language:

`Human natural language -> external translator/normalizer -> Needle -> ClayCode instruction/state -> FRANK 4B`

The exact translator implementation is an outer interface concern. Its job is to preserve meaning while crossing into the Clay-native system boundary.

### Clay-native cognitive boundary

Once the request reaches the Clay-native FRANK cognitive path:

- the 4B receives **ClayCode only**;
- the 4B reads **ClayCode only**;
- the 4B reasons/deliberates **in ClayCode**;
- the 4B emits **ClayCode only** as its native semantic output;
- FRANK state presented to the model is a ClayCode reader projection, not prose/JSON pretending to be architecture;
- no German/English hidden chain, system explanation or tool schema is required for normal cognition.

Compact law:

`FRANK_MODEL_LANGUAGE = CLAYCODE`

### Human-facing egress

For a human conversation:

`FRANK ClayCode output -> deterministic/controlled renderer or translator -> requested human language`

Human-language rendering is not canonical cognitive state. The ClayCode representation and its canonical identity remain the architecture-relevant representation.

---

## 2. Needle remains Needle

**Do not redesign Needle for Test 1.**

The existing project decision that Needle is FRANK's sole intentional non-Clay semantic/reflex island remains in force. Existing Needle semantics, routing behavior, versioning, certificates, tool-use responsibility and policy boundaries are simulated as specified by the current FRANK repository at freeze time.

Project-owner clarification for this experiment:

- tool use belongs to Needle/the external FRANK control path, not to the Clay-native 4B;
- the 4B is not trained as an OpenAI-style function caller or generic tool-using chatbot;
- tool/API syntax must not become the model's native language;
- the model receives the resulting ClayCode instruction/reader state after the outer translation/Needle path has done its work;
- capability/effect authority remains whatever the current FRANK architecture specifies and is not conflated with language competence.

This contract does **not** alter Needle internals. It only fixes the model/Needle boundary for Test 1.

---

## 3. "Full FRANK simulation" means the repository runs the architecture

Test 1 is invalid if FRANK is approximated by one giant system prompt.

The repository must maintain machine state across turns and execute/simulate the architecture around every model message. At simulator freeze time, the exact current compatible branch set is pinned by commit/artifact hashes.

Current planning baseline includes at least:

- FRANK C9 TCAEF;
- latest compatible ClayCode release candidate assembled from the CC-RC1.9 multiworker family and later integrated deltas such as IARC where accepted for the freeze;
- ClayGraph G3 IBCA overlay;
- GWT R6 Receiver-Causal Workspace Closure overlay;
- UnifiedDB U2 CPPF;
- Hyperposition H6 CARTS;
- current Clay/CACC/Safe-Effect contracts;
- current Needle contract;
- current recovery/observability/replay contracts.

Newer compatible deltas discovered before freeze must be cross-read and either integrated or explicitly rejected with a receipt.

---

## 4. Turn-level causal pipeline

A normal external turn is modeled as an explicit state transition graph. Where the frozen architecture permits BYPASS, the bypass itself is receipted.

Reference chain:

`ExternalInputEvent`
`-> human-language translation/normalization if needed`
`-> Needle`
`-> Durable Event Ledger`
`-> UnifiedDB logical/query/result fabric`
`-> operation/task-scoped causal and admissibility compilation`
`-> ClayGraph memory-use admissibility`
`-> ClayGraph route/activation/Assembly`
`-> cognitive resource allocation`
`-> CandidateSet`
`-> GWT competition`
`-> WorkspaceEpisode`
`-> BroadcastPlan/BroadcastEnvelope`
`-> receiver delivery`
`-> reconstruction`
`-> uptake`
`-> local causal-use state`
`-> certified ClayCode reader projection`
`-> Clay-native 4B transform`
`-> canonical ClayCode reconciliation`
`-> proposal / EffectIntent / cognitive output as applicable`
`-> current intent/resource/authority/effect checks as specified by frozen FRANK`
`-> Needle/tool/effect path as applicable`
`-> OutcomeReceipt`
`-> provenance-bound canonical re-entry`
`-> ClayGraph/salience/scoped-credit update`
`-> next eligible state`

The model call is one stage inside this pipeline, not the whole architecture.

---

## 5. Persistent state domains required in the simulator

At minimum the simulator must persist and version:

1. canonical event ledger and state epochs;
2. source/basis epochs and provenance lineage;
3. UnifiedDB typed query/result identity, TCQS collection semantics and selection receipts;
4. required-context closure and admissibility states including UNKNOWN/CONFLICT/REVOKED where applicable;
5. ClayGraph semantic graph epochs, activation, route, Assembly and memory-use admissibility receipts;
6. salience, inhibition, decay and scoped causal-credit state without allowing utility to mint truth/authority;
7. cognitive budgets/resource governor state;
8. CandidateSet membership/rank/weight identity;
9. WorkspaceEpisode identity and competition/gate state;
10. GWT receiver universe, BroadcastEnvelope, per-receiver delivery/reconstruction/uptake/local-effect state and closure receipts;
11. reader projection order/rails/hash;
12. model identity: base checkpoint, LoRA, tokenizer, quantization, sampler and inference settings;
13. Needle version/state/certificates and outer-language translation identity;
14. task/user-intent state required by the frozen architecture;
15. EffectIntent/proposal identity;
16. resource identity witnesses/handles where applicable;
17. capability/permit/reservation/revocation/expiry/budget state where applicable;
18. tool/sandbox execution receipts where applicable;
19. OutcomeReceipt, re-entry and post-effect state;
20. recovery/checkpoint/replay state.

Every mutable domain needs explicit epoch/version identity so a later state cannot silently masquerade as the state the model actually saw.

---

## 6. GWT R6 must be simulated as a causal chain, not a broadcast label

The simulator must preserve the current R6 distinction:

`global_addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`

Therefore a WorkspaceEpisode cannot be declared globally effective merely because data was copied to all simulated receivers.

The harness records per receiver:

- addressable;
- delivered;
- delivered payload identity;
- reconstruction validity;
- uptake measurement/proxy;
- local causal-effect receipt/proxy;
- contribution to system outcome;
- contribution to re-entry.

This is essential for later GWT/emergence experiments.

---

## 7. ClayGraph G3 must gate consequential memory influence

The simulator must preserve the current distinction:

`retrievable != admissible_for_current_task != allowed_to_influence_consequential_proposal`

Memory-use states such as `ADMIT | SUPPLEMENT_ONLY | QUARANTINE | ESCALATE | UNKNOWN` are external architecture state, not model vibes.

For consequential paths:

- empty admissible set -> ESCALATE / EXACT_VALIDATE;
- never silently use nearest-neighbor fallback merely to keep the model supplied;
- exact/high-confidence identity queries may BYPASS graph propagation when the frozen route policy says so;
- graph exposure is not GWT uptake;
- graph salience is not canonical truth or authority.

---

## 8. ClayCode completion gate before any LoRA

"ClayCode finished" for Test 1 means an executable release, not another research memo.

Required release artifacts:

- frozen language specification;
- parser;
- canonicalizer;
- AST/canonical semantic IR;
- type system;
- collection/TCQS semantics;
- effect/authority-relevant semantic types without confusing expressibility with authority;
- validator/type/effect checker;
- deterministic semantic hash rules;
- interpreter/reference evaluator for the executable pure/control core;
- defined lowering interface for foreign/runtime effects;
- translation-validation/receipt rules across lowering boundaries;
- error taxonomy and recovery rules;
- conformance suite;
- positive corpus;
- negative/mutation/fuzz corpus;
- property tests;
- round-trip tests;
- application-coverage tests;
- reference examples for all language constructs;
- machine-readable release manifest with exact hashes;
- dataset generator derived from the same reference semantics;
- held-out evaluation generator that cannot leak into training.

Release gate: the language must be usable by the AI workers themselves to write, parse, execute/evaluate, mutate, debug and repair nontrivial programs before training the 4B.

---

## 9. LoRA-1 scope: language only

The first Together LoRA has exactly one job:

> Make the Qwen-class 4B natively read, reason and speak the frozen ClayCode language.

It is NOT intended to teach the model the FRANK state machine by memorization.

Training examples should emphasize:

- ClayCode comprehension;
- canonical generation;
- semantic transformations;
- program synthesis;
- program repair;
- type/effect reasoning;
- dependency/causal reasoning expressible in the language;
- state transformation in ClayCode;
- translation between equivalent ClayCode projections;
- distinguishing valid/invalid/unknown/conflicting constructs;
- general-purpose algorithms/application logic in ClayCode.

Held-out evaluation must test language competence before the model is placed inside FRANK.

---

## 10. Simulator/model interface

The model adapter must expose a narrow contract such as:

`ClayReaderFrame -> ClayModelOutput`

No natural-language prompt is required inside this interface.

A `ClayReaderFrame` should bind at minimum:

- frame/version id;
- current canonical basis/state epoch;
- Needle route/certificate refs relevant to the turn;
- required-context closure;
- admitted memory/Assembly refs;
- WorkspaceEpisode/winner identity;
- broadcast/receiver reconstruction projection relevant to this model receiver;
- task/user-intent reference allowed for cognition;
- current resource/budget hints that cognition is permitted to see;
- explicit semantic role/admissibility/causal-stage labels;
- provenance refs;
- expected output contract.

The model output is canonicalized/validated before downstream FRANK use. Invalid ClayCode becomes an explicit model-language failure state, not silently repaired by converting it to prose.

---

## 11. Every message becomes an experiment trace

For every conversation turn, write a trace bundle containing at least:

- pre-turn snapshot hash;
- external input and translation identity;
- Needle receipt refs;
- retrieval/query/admission receipts;
- ClayGraph route/Assembly receipts;
- CandidateSet and WorkspaceEpisode;
- GWT receiver/broadcast receipts;
- exact ClayReaderFrame delivered to the 4B;
- exact raw ClayCode model output;
- canonicalized/validated model output;
- downstream proposal/effect/tool receipts;
- outcome;
- post-turn snapshot hash;
- re-entry deltas;
- utility/credit updates;
- latency/token/cost/resource metrics;
- all failures, fallbacks and repairs.

Thus ordinary conversation itself becomes replayable experimental data.

---

## 12. Counterfactual and ablation requirement

The simulator must make architecture modules switchable/replayable so the same frozen input/state can be rerun under interventions such as:

- ClayGraph off / exact retrieval only;
- IBCA off;
- GWT broadcast policy changed;
- selected receiver lesioned;
- salience adaptation off;
- stale epoch injected;
- missing required context;
- Needle route altered only through an explicit experimental control;
- resource budget changed;
- model LoRA on/off;
- model output swapped while upstream state is fixed;
- authority/effect path disabled or shadow-only;
- re-entry disabled;
- memory update disabled.

This is required to distinguish architecture effects from model effects.

---

## 13. Test-1 success is multidimensional

Do not reduce success to "chat feels good".

Measure at least:

### Clay language competence
- syntax/canonical validity;
- semantic/type/effect correctness;
- repair success;
- program/application coverage;
- held-out generalization;
- Clay-only adherence.

### FRANK architecture fidelity
- deterministic/replay agreement;
- state-transition validity;
- epoch/provenance integrity;
- correct module ordering/bypasses;
- complete receipt coverage;
- re-entry closure.

### Cognition/system utility
- task accuracy;
- consistency over long episodes;
- memory use quality;
- contradiction handling;
- state retention;
- cost/latency/token efficiency;
- robustness to partial/unknown/conflicting inputs.

### Causal architecture evidence
- ablation effect sizes;
- receiver causal closure;
- memory-route contribution;
- workspace intervention effects;
- re-entry dependence;
- alternative/common-driver controls.

### Safety/authority integrity
- model cannot self-authorize;
- stale/revoked state cannot silently commit;
- generated/foreign code cannot amplify authority in the simulated contract;
- task/memory provenance cannot be laundered through ordinary cognition;
- Needle/model/tool boundaries remain distinct.

---

## 14. Large experiment phase after a successful integration

If the Clay-native 4B and full FRANK simulator are coherent, freeze that complete configuration as `FRANK_SIM_BASELINE_1` and spend remaining inference budget on high-information experiments rather than casual chatting.

Priority families:

1. FRANK vs naked 4B matched tasks;
2. LoRA Clay-native vs same base model without LoRA;
3. Clay-native vs natural-language/JSON control representations where scientifically useful;
4. memory/ClayGraph routing and poisoning experiments;
5. GWT receiver-closure and lesion/rescue experiments;
6. long-horizon state/re-entry/recovery experiments;
7. task-intent/admissibility/authority separation attacks;
8. resource-budget/quality frontiers;
9. topology/credit adaptation experiments;
10. emergence-related measurements only under the project's existing epistemic restrictions and alternative explanations.

All runs produce durable receipts and counterexamples.

---

## 15. Secret and budget rule

Together credentials are runtime secrets only. Never commit token values to repository artifacts, traces or datasets.

Planning does not authorize training or paid inference. Before any paid job:

- exact model id is verified live;
- dataset hashes are frozen;
- held-out suite is frozen separately;
- estimated cost is recorded;
- job purpose and stop criteria are explicit.

---

## 16. Compact architectural law for Test 1

`human_language`
`-> translator`
`-> Needle`
`-> full external FRANK state machine`
`-> ClayReaderFrame`
`-> Clay-native 4B`
`-> ClayCode`
`-> full external FRANK state machine`
`-> optional human-language renderer`

The 4B is **not FRANK by itself**.

The repository-driven state machine + Clay-native 4B together instantiate the Test-1 FRANK simulation.
