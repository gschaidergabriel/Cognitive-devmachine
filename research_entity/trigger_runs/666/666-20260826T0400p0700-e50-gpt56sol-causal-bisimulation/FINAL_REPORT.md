# 666 Emergent Field Report — Causal Bisimulation for Model-Call Identity

Run: `666-20260826T0400p0700-e50-gpt56sol-causal-bisimulation`
Field: `field-666-20260826T0400p0700-causal-bisimulation-model-call-identity-09c2ea75`
Organ: `e50 / GPT-5.6 Sol ChatGPT organ`
Persistent entity: Clay
Product: EntityOS
Architecture: HCU
Canonical parent at spawn: `1dc4585ed38fcc3f147f913d534a809a92d98669`
Supervisor: `8.82 / FREE_ONLY`
Seed: `703382283100035899`
Seed SHA-256: `09c2ea75b57b1b3ba23b17b8b4c968b6f34c578cff3b34b2fe91afaac2c86a82`

## Spawn decision

Level-0 is already PASS, so current owner-fixed `666` semantics are post-Level-0 seeded stochastic field genesis. Recent registered fields cover proof-carrying state, cache coherence, causal re-entry, memory reconsolidation, conformal metrology, capability lattices, semantic transaction isolation and scheduler phase coherence. The selected field is deliberately orthogonal but current-frontier-relevant: programming-language semantics × causal inference × cryptographic provenance × differential testing.

Current Supervisor 8.82 separately reports a source-contract gap around model-call output/call identity and blocks new model/GRID10 execution pending observed FreeSwarm runtime quiescence. This field therefore performs source analysis plus a deterministic synthetic identity discriminator only.

## Source observation

Current `tools/trigger2_qwen35_checkpoint_model_state_consumption_probe_v2.py` defines `CLAY_TRIGGER2_MODEL_CALL_BINDING/v2` over a canonical envelope containing candidate, checkpoint manifest/state, loaded state, rendered prompt, token tensors, runtime identity and forward output.

That is a strong **content binding**. It does not itself contain a separate replay-stable causal occurrence identity such as causal event, admission, route decision, GRID plan/cell or attempt identity.

Current tests already close important orthogonal defects:

- token transplant changes call binding;
- same top-1 but different full logits changes call binding;
- output transplanted across candidate identity changes call binding;
- post-load model-state mutation changes state identity.

Those tests prove sensitivity to changed bound content. They do not test whether two genuinely distinct executions with identical bound content remain distinct causal occurrences.

## Research question

Should one digest simultaneously serve as:

1. content-equivalence identity for exact replay/deduplication; and
2. causal occurrence identity for downstream `NODE_RESULT -> J-Space/evaluation` lineage?

The field hypothesis is **no** unless an enclosing immutable execution receipt already supplies and enforces the missing occurrence identity.

## H-CBMI-01 — content identity is not occurrence identity

Two real calls can consume byte-identical checkpoint state, prompt/tokens, runtime identity and produce byte-identical outputs while still being two distinct causal events.

If identity is derived only from that content envelope, the two occurrences are observationally bisimilar at the content surface and therefore hash-identical. This is desirable for semantic/content replay equivalence, but insufficient when a downstream evidence graph needs to answer **which execution event produced this node**.

Status: `SUPPORTED_WORKING_HYPOTHESIS_SOURCE_PLUS_SYNTHETIC`.

## H-CBMI-02 — split equivalence from occurrence

Candidate successor semantics:

- `model_call_content_digest`: deterministic digest of the present content envelope;
- `model_call_event_id`: deterministic occurrence identity binding replay-stable causal event identity plus concrete admission/route/plan/cell/attempt identity and the content digest.

Required laws:

1. distinct causal events + identical content => same content digest, different event IDs;
2. exact replay of the same causal event + identical content => same event ID;
3. same causal event + changed content/output => explicit replay-identity conflict;
4. downstream `NODE_RESULT`, J-Space traces and evaluation receipts bind the event ID and the content/output digest;
5. content digest remains available for semantic deduplication; event identity must not destroy useful equivalence classes.

Status: `SUPPORTED_WORKING_HYPOTHESIS_EXACT_SYNTHETIC_MECHANISM`.

## Exact deterministic synthetic discriminator

Fixture source:

`research_entity/emergent_fields/fields/field-666-20260826T0400p0700-causal-bisimulation-model-call-identity-09c2ea75/causal_bisimulation_probe.py`

Persisted result:

`research_entity/emergent_fields/fields/field-666-20260826T0400p0700-causal-bisimulation-model-call-identity-09c2ea75/EXPERIMENT_RESULT.json`

Observed:

- source-equivalent current content digest: `47e1816a51bc29b7ad1736f0d20c783c5830e09b4ab4dc988537d630c45bbce6`;
- two distinct occurrences A/B with identical content necessarily share that same content digest;
- proposed event A: `169db009b16748740218d8cc9d491ad89cb3141adc44458454406b98597f166f`;
- proposed event B: `bf26f43b491fa4e66aa8bccef0113c431eeec277512af0aaf6929fb0339f085c`;
- exact replay of event A reproduces the exact event-A ID;
- changing the full output while retaining event-A occurrence coordinates changes content digest to `2859518cd3e01486be97c13692f33f35835b0590473af1a338f85563df86e8f4` and changes the event binding, which must be interpreted as a same-event/different-content conflict rather than a second valid replay.

All five fixture assertions pass.

Evidence class: `EXACT_SYNTHETIC_MECHANISM_TEST_NOT_MODEL_RUNTIME`.

## Serious counterhypothesis

The current call digest may intentionally be a content-addressed identity while another immutable enclosing runtime receipt already carries true occurrence identity. If every downstream `NODE_RESULT`, InferenceReceipt, J-Space trace and evaluation artifact:

- binds that enclosing occurrence receipt;
- binds causal event/admission/route/engine/loader/GRID coordinates;
- preserves attempt/replay semantics;
- rejects same-occurrence/different-content conflicts;

then no second call-level occurrence authority should be created. In that case the required repair is to **name the current digest explicitly as content binding and prove the enclosing occurrence chain**, not add another competing identity system.

This is the field's primary falsifier and the next audit must test it first.

## Cross-connection 1 — Re-entry Causal Identifiability

`EF-20260809-002-REENTRY-CAUSAL-IDENTIFIABILITY` established that observationally similar directed flow cannot by itself establish causal identity because common drivers can generate the same surface relation. The same epistemic structure applies here: identical call content/output is an observational equivalence class, not proof of event identity. Causal occurrence coordinates are the analogue of the intervention/common-driver discriminator.

## Cross-connection 2 — Semantic Transaction Isolation

`Semantic Transaction Isolation for Cognitive State` showed that per-field/local identity is insufficient when an invariant spans several state elements; snapshot/transaction identity is required to prevent fractured lineage. Model-call lineage is similarly composite: checkpoint/input/runtime/output content and execution occurrence must be bound consistently rather than inferred from one local digest.

## Cross-connection 3 — Forge/Distillery replay law

The current Forge/Distillery work already encodes the dual requirement that semantic replay should collapse while a genuinely distinct execution identity must remain independently admissible. The model-call layer should preserve the same distinction instead of forcing one digest to play both roles.

## Architecture implication

Do **not** replace the current v2 binding blindly.

Highest-information source audit:

`Typed Entry causal_event_id -> admission_id -> route_decision_id -> engine/load lease -> GRID plan/cell -> model execution occurrence -> content/output binding -> NODE_RESULT -> J-Space/evaluation`

For each edge, determine whether current source already has an immutable occurrence ID and whether downstream receipts rebind it fail-closed.

Only if that chain lacks occurrence closure should a successor contract introduce a separately named `model_call_event_id`. Reuse the canonical event/admission/route/GRID identities already owned by EntityOS/HCU; do not create a second event namespace.

## Fail-closed regression family

A successor should prove at minimum:

1. `DISTINCT_EVENT_IDENTICAL_CONTENT`: distinct causal events remain distinct occurrences;
2. `EXACT_EVENT_REPLAY`: same event + same content is idempotent;
3. `SAME_EVENT_DIFFERENT_OUTPUT`: reject replay conflict;
4. `SAME_EVENT_DIFFERENT_CHECKPOINT`: reject replay conflict;
5. `SAME_EVENT_DIFFERENT_INPUT`: reject replay conflict;
6. `EVENT_RECEIPT_TRANSPLANT`: reject occurrence receipt bound to a foreign content digest;
7. `CONTENT_DIGEST_REUSE`: allow semantic-equivalence indexing without minting independent evidence;
8. `DOWNSTREAM_LINEAGE_REQUIRED`: NODE_RESULT/J-Space/evaluation cannot promote if occurrence identity is missing or ambiguous.

## Current runtime / authority boundary

Supervisor 8.82 still has FreeSwarm owner emergency stop HARD OFF and host runtime quiescence NOT PROVEN. Physical GRID10 execution remains blocked. No provider, model runtime, VPS runtime, paid lane, Together call, training or unusual experiment was executed by this field.

Credits remain:

- model-call runtime: 0;
- Physical GRID10: 0;
- J-Space model: 0;
- training: 0;
- full HCU: 0;
- whole EntityOS: 0.

## Decision

`SUPPORTED_WORKING_HYPOTHESIS_WITH_EXACT_SYNTHETIC_OCCURRENCE_IDENTITY_COUNTEREXAMPLE_ROUTED_TO_MESH_NOT_PROMOTED`

## Next exact action

Audit the exact current downstream execution/InferenceReceipt/NODE_RESULT/J-Space path for a pre-existing immutable occurrence identity. If it already closes event/admission/route/engine/load/GRID/attempt + content/output and replay conflicts, retain the current content digest and document that separation. If it does not, fuse a single successor occurrence-binding contract into the existing canonical causal chain and add the eight fail-closed regressions above. Do not perform model/GRID10 execution until Supervisor 8.82 runtime-quiescence requirements are independently satisfied.
