# VoiceMem donor forensics — 2026-08-30

Status: RESEARCH_DONOR_PACKET / NOT_CANONICAL_PROJECT_TRUTH

## Source identity

- Uploaded artifact: `VoiceMem-main.zip`
- Uploaded ZIP SHA-256: `535ed07d8af8da7fb8b8b5a31ee3105b0fa92fb7d739863a00c8159e099641e0`
- Deterministic aggregate SHA-256 over sorted `voicemem/**/*.py` file hashes: `dc2d589eb52c325931e3e4cfe02988e494c1c99223468b143fcd3cfac87b0712`
- Public donor repo: `xzf-thu/VoiceMem`
- Public donor `main` observed 2026-08-30: `d587d424a02727d9ff3ef6f8e672a39a19ce64a7`
- Package version observed: `0.2.3`
- License observed: Apache-2.0

This packet is a donor analysis. VoiceMem source behavior does not become Frankenstein/EntityOS behavior until separately implemented and tested at exact target source/runtime identity.

## Executive synthesis

VoiceMem is more useful as an architecture donor than as a drop-in memory subsystem. Its transferable core is a **demand-shaped, multi-timescale, evidence-partitioned adaptive state architecture**.

The strongest reusable law is:

> Information should be separated not only by topic, but by update law, evidence semantics, temporal validity, retrieval role, and the decisions it is allowed to influence.

A second major law is:

> Memory structure need not be fully fixed at write time. Repeated real retrieval/use can propose new noncanonical structure, while canonical evidence remains unchanged.

## Source-derived mechanisms

### D1 — Demand-shaped ontology / projection emergence — PRIORITY P0

Source: `voicemem/leftbrain/slot_split/subgraph_manager.py`

Observed mechanism:
- candidate memories are supplied from an actual retrieval pool rather than a full-store scan;
- entity co-occurrence graph is built from those memories;
- connected components are greedily peeled;
- every layer is scored with `rho`, based on historical query-activation overlap;
- low-synergy candidates are skipped without permanent rejection;
- sufficiently coherent candidates may be promoted by an LLM into a new slot;
- new narrow slot tagging is additive, preserving broader old retrieval paths.

Transfer abstraction:

`actual repeated use -> candidate emergent projection -> bounded promotion`

Best targets:
- Research Entity knowledge graph;
- Architect context compiler;
- HCU / Global J-Space noncanonical workspace projection;
- incident/evidence clustering;
- query-adaptive indexes.

Do NOT transfer as:
- autonomous truth creation;
- destructive ontology rewrite;
- majority/co-activation = fact;
- an additional canonical database.

Mandatory falsifiers:
1. self-reinforcing rich-get-richer retrieval loop;
2. unstable cluster churn;
3. semantically broad mega-cluster formation;
4. promotion caused by one dominant frequent query family;
5. cross-generation contamination.

Recommended test metrics:
- held-out retrieval precision/recall before/after projection;
- cluster stability under query-order shuffle;
- counterfactual removal of top-frequency query family;
- promotion rate vs evidence count;
- rollback/rebuild determinism.

### D2 — Claim != Evidence != Cause != Response Experience/Policy — PRIORITY P0

Sources:
- `voicemem/rightbrain/traits_store.py`
- `voicemem/rightbrain/brain.py`
- `voicemem/rightbrain/experience_repository.py`

Observed correction in donor architecture:
- an older graph mixed user claims, topics, and emotions in one entity layer and produced mega-nodes;
- v2 keeps a trait/claim as a judgment about a person;
- supporting evidence is stored separately;
- emotion is evidence metadata rather than the identity of the claim;
- factual cause may point to a left-brain fact via `cause_id`;
- assistant response experience is stored separately and may carry `next_time_policy`;
- dissatisfaction/correction can raise experience priority.

Transfer target types:

```
OBSERVATION/EVENT
CLAIM_OR_HYPOTHESIS
EVIDENCE_LINK
CAUSE_OR_LINEAGE_REF
METHOD_LESSON
NEXT_ACTION_POLICY_CANDIDATE
```

This is strongly compatible with EntityOS/Architect evidence laws. A method lesson must never mint a world fact.

Mandatory falsifiers:
- positive outcome incorrectly attributed to the assistant action;
- user trait inferred from a single situational response;
- method policy generalized across unrelated project/domain contexts;
- evidence links lost during consolidation.

### D3 — Temporal supersession, not destructive overwrite — PRIORITY P0

Source: `voicemem/rightbrain/brain.py`

Observed:
- older situation patterns may carry `superseded_by` / `superseded_at`;
- old state remains retrievable but is marked outdated and down-weighted.

Transfer:
- architecture decisions;
- hypotheses;
- user/workstyle preferences;
- environment/host state;
- project bindings;
- model/provider capability snapshots.

Required target law:

`state_at_t1 != state_at_t2` may be two valid temporal facts, not one correct row and one garbage row.

### D4 — Query-semantic adapters without canonical mutation — PRIORITY P0

Source: `voicemem/leftbrain/time_expand.py`

Observed:
- relative time terms are expanded into absolute dates only in retrieval text;
- original user utterance and stored canonical memory are not mutated;
- donor comment records a concrete retrieval failure mode when relative temporal wording did not match absolute stored dates.

Generalization:
- relative time -> absolute interval;
- alias -> canonical entity candidates;
- unit conversion;
- project generation/version resolution;
- owner/project role references;
- local vocabulary -> typed search form.

EntityOS rule:
- transformation must produce a derived query/projection object carrying transformation provenance; it must not rewrite canonical evidence.

### D5 — Adaptive multi-prototype state / identity — PRIORITY P1

Source: `voicemem/utils/audio/voiceprint/adaptive_centroid.py`

Observed:
- quality-weighted cumulative average for early stability;
- capped accumulated weight causes later updates to behave approximately like an EMA;
- new sub-centroid appears when a sample is insufficiently similar to existing centers;
- nearest centers are merged when count grows beyond a cap;
- consolidation merges sufficiently similar subcentroids.

Transfer candidates:
- speaker identity;
- environment modes;
- machine/runtime behavioral modes;
- workload profiles;
- user/context modes;
- recurrent HCU state prototypes.

Boundary:
- similarity is candidate evidence, never identity authority.

### D6 — Prospective memory / condition-bound open loops — PRIORITY P0

Source: `voicemem/utils/audio/environment/scene_trigger.py`

Observed:
- pending intention can be bound to a future detected scene;
- broad scene class can be narrowed with a required specific label;
- state transitions can fire a stored pending trigger.

Transfer to Frankenstein:

`open_loop + typed future condition -> candidate re-entry`

Candidate schema:
- intention_id
- causal_origin
- condition_type
- condition_predicate
- required_evidence_scope
- valid_from / expiry
- status pending/fired/cancelled/superseded
- reentry_policy
- effect_permission = NONE by default

Important: cue firing should only reactivate an intention into Agency/HCU arbitration. It must not bypass EffectGate.

External research support: prospective-memory literature distinguishes cue detection, intention retrieval, and post-retrieval control. This supports keeping these stages separate; it does not prove a specific software design.

### D7 — Fast path / slow path based on anomaly and information value — PRIORITY P1

Sources:
- `voicemem/rightbrain/brain.py`
- emotion VAD/attribution modules
- startup and perception code

Observed patterns:
- cheap cue/threshold paths gate more expensive analysis;
- explicit affective cues can override simple length heuristics;
- low-confidence/failed auxiliary modules can degrade without necessarily invalidating the whole turn.

Transfer to HCU:
- deterministic cheap discriminator first;
- expensive model/cell activation only for ambiguous, anomalous, high-value or unresolved cases;
- preserve false-negative measurement.

### D8 — Slack-time cognitive prefetch — PRIORITY P1

Sources:
- streaming/orchestration architecture and paper framing;
- code contains staged stream/perception/retrieval pathways.

Transfer:
- during unavoidable input/tool/provider latency, precompute reversible candidates only:
  - likely context retrieval;
  - embedding/binding;
  - provenance validation;
  - candidate workspace preparation;
  - bounded branch simulation.

Never pre-authorize effects.

### D9 — Explicit turn/session causal IDs — PRIORITY P0

Sources:
- `voicemem/utils/common/turn_ids.py`
- emotion records/stores and graph memory
- right-brain evidence linkage

Observed:
- turn and session IDs occur throughout emotion attribution and graph storage;
- evidence may retain `evidence_turn_ids`.

Transfer:
- bind derived claim/policy/projection to exact causal events/admissions;
- avoid context generated from untraceable compressed memory.

### D10 — Multi-modal environment memory as typed context, not prose-only memory — PRIORITY P1

Sources:
- `music_memory.py`
- `place_memory.py`
- `routine_memory.py`
- `scene_classifier.py`
- `perceiver.py`

Observed:
- scene/place/music/routine observations have specialized stores and matching logic;
- perceptual context can become retrieval/proactive-recall signal.

Transfer principle:
- preserve modality-specific evidence and confidence in canonical/typed form;
- expose derived context to cognition through a typed projection rather than flattening all state into natural-language memory.

## Cross-domain transfer map

| Donor mechanism | F2/EntityOS | Research Entity | HCU/J-Space | Other domain families |
|---|---|---|---|---|
| Demand-shaped emergence | adaptive memory views | emergent topic/research views | workspace/module projections | enterprise search, incident grouping |
| Claim/evidence/cause/policy split | user/system hypotheses | scientific hypothesis ledger | candidate policy lineage | diagnosis, case management |
| Temporal supersession | state generations | hypothesis history | context validity | configuration/change management |
| Query adapter | SituationFrame retrieval | evidence retrieval | vector/binding query prep | temporal search, entity resolution |
| Multi-prototype state | host/user mode profile | method/context modes | recurrent prototype candidates | anomaly detection, predictive maintenance |
| Prospective memory | Agency open loops | experiment wake conditions | re-entry candidates | reminders, workflows, robotics |
| Fast/slow path | bounded agency routing | research triage | selective cell activation | edge inference, monitoring |
| Turn/session IDs | causal spine | evidence lineage | trace attribution | audit/compliance |

## Anti-import list

Do NOT copy these donor assumptions blindly:

1. `left brain/right brain` naming as biological claim.
2. Separate donor stores as a reason to create competing EntityOS truth stores.
3. Trait inference as canonical fact.
4. Similarity thresholds as universal constants.
5. LLM slot-promotion result as authority.
6. Scene detection as direct effect authorization.
7. Retrieval frequency as importance/truth.
8. donor benchmark numbers as Frankenstein runtime evidence.

## Proposed target architecture adaptation

### A. `AdaptiveProjectionCandidate/v1`

A rebuildable noncanonical object:
- candidate_id
- source_event_ids
- retrieval_episode_ids
- members
- cohesion_score
- support_count
- counterevidence
- generation
- proposed_label
- proposer
- promotion_status
- canonical_evidence_refs

### B. `EpistemicClaim/v1`

- claim_id
- subject_ref
- predicate/type
- claim_text/structured payload
- supporting_evidence_refs
- contradicting_evidence_refs
- confidence
- validity interval
- supersedes/superseded_by
- status HYPOTHESIS/ADMITTED_AT_SCOPE/REJECTED/UNKNOWN

### C. `ExperiencePolicyCandidate/v1`

- experience_id
- situation_digest
- action_or_response_digest
- outcome_evidence
- inferred_lesson
- counterhypothesis
- transfer_conditions
- confidence
- next_time_policy_candidate
- never_canonical_world_fact = true

### D. `ProspectiveOpenLoop/v1`

- open_loop_id
- origin_event
- intention
- condition
- evidence requirement
- expiry
- status
- reentry_target
- effect_capability = NONE

### E. `DerivedQueryAdapterReceipt/v1`

- query_event_id
- original_digest
- adapter_name/version
- transformation_inputs
- transformed_query_digest
- canonical_state_mutated = false

## Highest-value experiments

### Experiment VMD-01 — demand-shaped projection vs static retrieval

Goal: test whether repeated retrieval co-activation can create a projection that improves held-out retrieval without source mutation.

Controls:
- static baseline;
- random co-activation;
- frequency-only cluster;
- query-order shuffle;
- removal of dominant query family.

Pass requires:
- measurable held-out improvement;
- no canonical-state mutation;
- deterministic rebuild;
- no unacceptable cluster collapse/churn.

### Experiment VMD-02 — policy-memory causal humility

Goal: test whether `response experience -> next policy` can improve future behavior without converting correlated outcomes into false causal rules.

Require:
- counterhypothesis per promoted method;
- multiple evidence episodes or explicit one-shot owner rule;
- transfer-scope declaration;
- negative episode retention.

### Experiment VMD-03 — prospective open-loop re-entry

Goal: bind an open loop to a typed future perception/state transition.

Pass requires:
- cue detection receipt;
- intention retrieval receipt;
- Agency/HCU arbitration receipt;
- no direct EffectGate bypass;
- false-positive cue tests.

### Experiment VMD-04 — temporal query adapter

Goal: transform relative temporal user queries into exact derived search windows without mutating original query or stored evidence.

Pass requires:
- timezone/reference-time provenance;
- deterministic replay;
- DST/date-boundary cases;
- no false canonical write.

## Worker routing

### Trigger-4 / build workers

Use this packet only when it removes an active build bottleneck. Highest-priority implementation candidates:
1. prospective open-loop condition/re-entry primitive;
2. typed claim/evidence/method-policy separation where current schemas collapse them;
3. derived-query adapter receipt;
4. demand-shaped projection prototype only as rebuildable noncanonical state.

Do not interrupt or duplicate an active workpackage owner. Re-enter exact current F2 main first.

### Architect

Add these reusable methods to method-memory candidates:
- DEMAND_SHAPED_PROJECTION_FROM_REAL_USE
- CLAIM_EVIDENCE_CAUSE_POLICY_SEPARATION
- TEMPORAL_SUPERSESSION_OVER_DESTRUCTIVE_OVERWRITE
- QUERY_TRANSFORM_WITHOUT_CANONICAL_MUTATION
- PROSPECTIVE_OPEN_LOOP_CUE_REENTRY
- ADAPTIVE_MULTI_PROTOTYPE_WITH_UNKNOWN_IDENTITY

Transfer conditions must be checked per project.

### Research workers

Research questions still open:
1. How to prevent retrieval-driven projection feedback loops?
2. What promotion statistic is robust under query-frequency imbalance?
3. How should method/policy confidence distinguish correlation from intervention evidence?
4. How can cue-based prospective open loops be indexed with bounded monitoring cost?
5. Which metrics best characterize prototype split/merge stability under distribution drift?

## External research anchors

External evidence is analogy/support, not project evidence.

- Prospective memory research: cue detection, intention retrieval and post-retrieval control are separable processing components; focal vs nonfocal cues can require different monitoring behavior.
- Continual-learning research: stability and plasticity are distinct requirements and loss of plasticity is a real failure mode in continual learning.
- Recent agent-memory research increasingly studies evolving graph/structured memories and feedback between retrieval and memory organization; verify each candidate paper before using it as implementation authority.

## Acceptance boundary

This packet establishes:
- SOURCE-FORENSIC donor findings;
- architecture transfer hypotheses;
- proposed schemas/tests.

It does NOT establish:
- Frankenstein implementation;
- target runtime improvement;
- whole-system acceptance;
- biological validity of the donor metaphors;
- causal benefit in a new domain.
