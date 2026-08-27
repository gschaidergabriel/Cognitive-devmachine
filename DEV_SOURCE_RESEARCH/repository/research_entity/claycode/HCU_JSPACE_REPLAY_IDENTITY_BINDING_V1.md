# HCU J-Space Replay Identity Binding v1

Status: CURRENT ADDITIVE ARCHITECTURE DELTA / SOURCE-CONTRACT ONLY  
Program: `ENTITYOS_HCU`  
Product: `EntityOS`  
Architecture: `HCU`  
Authority observed before write: Supervisor `8.73` / `FREE_ONLY`  
Canonical main observed before write: `e20998a7ba9439cc50093cdb2cc96d6456fbf885`

## 0. Scope and authority

This document is an **addendum**, not a second J-Space architecture or data authority.

It refines `HCU_JSPACE_OBSERVE_CONTROL_TRANSLATE_ARCHITECTURE_V1.md` by applying the replay-stable execution/evidence split already used by the Forge→Distillery bridge to future J-Space trace admission.

It creates no canonical truth, effect, model-runtime, J-Space-model, training, HCU-full, or whole-product credit.

Invariant:

`SAME_EXECUTION_REEMISSION != NEW_EVIDENCE`

and simultaneously:

`SAME_REPLAY_IDENTITY + DIFFERENT_MEASURED_EVIDENCE => CONFLICT`, not a second training example.

## 1. Problem

`JSPACE_TRACE_ABI/v1` already binds causal event, admission, generation, model/runtime/loader, inference, adapter, activation site, intervention/control and measured activation identities.

However, a trace envelope can also contain observation time, transport/admission metadata, candidate interpretation, labels, narration, classification and later analysis fields. If dataset identity is derived from the full envelope, changing those non-measured fields can re-key the same underlying model execution/measurement and inflate trace counts or training rows.

Conversely, collapsing all same-prompt/model traces would be wrong because a genuinely new model execution, intervention, site or measurement operator is new evidence.

Therefore HCU requires three explicitly separated identities.

## 2. Required identity split

### A. `JSPACE_EXECUTION_REPLAY_IDENTITY/v1`

Identifies one exact model-execution/measurement intervention event for replay/idempotency purposes.

It SHOULD bind, where present:

- `causal_event_id`;
- exact `model_execution_id` and/or `inference_receipt_id`;
- model/checkpoint/tokenizer/runtime/build identities;
- loader-consumption identity;
- `jspace_adapter_id`;
- activation site + token-position policy;
- observation/extraction operator identity;
- intervention identity, control class and frozen gain/policy identity when an intervention occurred;
- generation step / decode position / deterministic execution seed identity where relevant;
- source prompt/input digest or canonical source-event reference when required to distinguish executions;
- schema/version of the trace producer.

It MUST NOT use these as novelty-bearing identity fields by themselves:

- observation timestamp;
- receipt publication timestamp;
- candidate narration or interpretation;
- model self-report;
- human/model labels added after measurement;
- transport retry metadata;
- formatting/serialization order;
- analysis-only result classification.

A concrete `admission_id` remains preserved as provenance, but **must not be the sole replay key** because the same causal/model execution may be re-observed or republished through a new transport admission.

A genuinely repeated model execution SHOULD receive a new `model_execution_id` / `inference_receipt_id` and therefore remain separately admissible even if prompt, model and intervention are identical.

## 3. `JSPACE_MEASURED_EVIDENCE_IDENTITY/v1`

This digest binds what was actually measured for the replay identity.

It SHOULD include the immutable measured payload relevant to the declared observation/control claim, for example:

- raw-activation or projected-latent digest;
- declared target metric raw values;
- declared off-target metric raw values;
- intervention-applied confirmation / hook result when applicable;
- measured output/logit/behavior identity used by the causal test;
- exact measurement operator/version;
- any deterministic shape/dtype/site metadata required to interpret the measurement.

It MUST exclude observation time and candidate-only explanation/interpretation.

If the same `JSPACE_EXECUTION_REPLAY_IDENTITY/v1` appears with a different `JSPACE_MEASURED_EVIDENCE_IDENTITY/v1`, admission MUST fail closed as a replay-evidence conflict until the discrepancy is resolved.

Recommended classification:

`JSPACE_REPLAY_IDENTITY_CONFLICT`

This conflict is negative evidence; it is not a new sample.

## 4. `JSPACE_OBSERVATION_ENVELOPE_IDENTITY/v1`

The full published/transport envelope MAY have its own digest for provenance and audit.

This digest can change when timestamps, comments, labels or other envelope metadata change.

It MUST NOT be used as the training-row novelty key.

Relationship:

`observation_envelope_sha256` = provenance/audit identity  
`execution_replay_identity_sha256` = idempotency/event identity  
`measured_evidence_sha256` = conflict/evidence integrity identity

## 5. Admission semantics

For future `JSPACE_TRACE_ABI/v1` dataset admission:

1. **same replay identity + same measured evidence + changed envelope only**
   - classification: `DUPLICATE_REEMISSION`;
   - new trace rows: `0`;
   - new accepted dataset tokens/examples: `0`.

2. **same replay identity + different measured evidence**
   - classification: `JSPACE_REPLAY_IDENTITY_CONFLICT`;
   - fail closed;
   - new trace rows/tokens/examples: `0`.

3. **different model execution / inference receipt identity**
   - may be independently admissible after all normal evidence/family/split guards.

4. **same model execution but different predeclared activation site/operator**
   - remains distinct only when the replay identity explicitly binds that site/operator and the experiment protocol intended both measurements.

5. **same model execution with different intervention/control class**
   - remains distinct only when the intervention/control identity is explicit and predeclared; post-hoc relabeling cannot manufacture another intervention event.

## 6. Dataset and Goodman boundary

Replay-stable identity prevents one execution from being counted multiple times, but it does **not** establish statistical independence.

Even genuinely distinct executions may still collapse for replication/evidence-weighting purposes when they share:

- model family;
- checkpoint lineage;
- provider/runtime pipeline;
- prompt/template family;
- orchestration lineage;
- calibration data;
- derived control vector;
- task/semantic family.

Therefore:

`DISTINCT_REPLAY_IDENTITY != INDEPENDENT_REPLICATION`

Goodman-ancestry / family-collapse rules remain separate from replay idempotency.

## 7. J-Space control-specific rule

A control experiment needs two identity layers:

- **execution replay identity**: distinguishes the actual BASELINE / +VECTOR / SIGN_FLIP / NULL / ORTHOGONAL / PERMUTED / WRONG_SITE / LESION / RESCUE execution event;
- **control-family identity**: groups those executions into the same causal matched-control experiment family.

Do not use control-family identity as a replay key: that would incorrectly collapse required distinct interventions.

Do not use each envelope digest as a new execution: that would inflate the control family with republished copies.

## 8. Typed Entry / HCU integration

The preferred path becomes:

`Typed Entry causal_event_id`
` -> concrete admission_id`
` -> verified engine / loader identity`
` -> model_execution_id / InferenceReceipt`
` -> JSPACE_EXECUTION_REPLAY_IDENTITY/v1`
` -> JSPACE_MEASURED_EVIDENCE_IDENTITY/v1`
` -> JSPACE_TRACE_ABI/v1 envelope`
` -> replay/conflict admission`
` -> family/split/leakage guards`
` -> candidate TrainingTrace / workspace packet`

The replay identity is **not** a truth authority. It only prevents transport/envelope mutation from manufacturing evidence.

## 9. Minimum regressions before dataset promotion

A promotion-bearing implementation SHOULD execute all of these on exact source:

1. timestamp-only trace re-emission => `+0` examples/tokens;
2. candidate narration / post-hoc classification-only mutation => `+0`;
3. same replay identity + activation/metric digest mutation => fail closed conflict `+0`;
4. DB/process close+reopen preserves semantic replay `+0`;
5. genuinely new model execution remains admissible;
6. distinct predeclared control interventions remain distinct but share one control-family identity;
7. admission-id/transport retry does not alone create a new causal trace;
8. legacy rows without enough information to reconstruct stable identity fail closed rather than being guessed;
9. family/split leakage guards run **after** replay deduplication and cannot be bypassed by envelope mutation.

## 10. Current convergence link

This addendum is motivated by GO issue `#1741`, which localized an exact analogous mismatch at the Forge→Distillery live-promotion boundary: the lower bridge is replay-stable while the live promoter still demonstrates only full-evaluation / identical-row replay.

The J-Space architecture should not repeat that split-brain pattern.

Implementation order remains:

1. close the existing Forge→Distillery live-promoter semantic replay gate;
2. preserve the already-landed lower-bridge process-restart regression;
3. normalize new J-Space traces toward this three-identity split;
4. only then let accepted trace rows feed training-readiness counters.

## 11. Evidence and credit boundary

This is `SOURCE_ARCHITECTURE_ONLY`.

No unusual experiment, provider/model call, paid/Together route, external effect or training occurred.

Current credits remain:

- whole EntityOS/HCU runtime: `0`;
- full HCU runtime: `0`;
- provider runtime: `0`;
- J-Space model runtime: `0`;
- training: `0`;
- whole-product PASS: `false`.
