# ACEF-V0.1 — 120 candidate architecture deltas

Status: CANDIDATE DELTAS ONLY. They are implementation slices of one coupled ACEF hypothesis, not 120 promoted inventions. Every delta is reversible until matched evidence supports promotion.

## Semantic state and time

1. Introduce `SemanticDelta<T>` as the only proposed mutation carrier across cognitive semantic boundaries.
2. Make every SemanticDelta immutable after staging; corrections are new deltas or retractions, never in-place history edits.
3. Add `DeltaMonotonicity = MONOTONE_JOIN | NON_MONOTONE | EFFECT_COUPLED` as a first-class ClayCode type.
4. Add `DeltaVisibility = BRANCH_PRIVATE | EXECUTION_VISIBLE | CANONICAL_VISIBLE | QUARANTINED` as a first-class type.
5. Bind every semantic delta to an explicit `tx_id`.
6. Bind every provisional non-monotone delta to an explicit `branch_id`.
7. Carry `causal_parents` on every material semantic delta.
8. Carry `source_epoch` separately from commit epoch so stale observations are not silently recast as current.
9. Carry `schema_epoch` on all staged state so mixed-schema commits fail closed.
10. Carry current global `lease_epoch` on all staged state that can affect the running Frank execution.
11. Carry `identity_lineage_head` on every commit-eligible delta.
12. Carry explicit `authority_refs` instead of inferring authority from model/GWT/tool context.
13. Carry explicit `effect_refs` for outcome-dependent deltas.
14. Give every delta a stable semantic content hash independent of storage row identity.
15. Separate event time, observation time, staging time and commit time.
16. Preserve epistemic class separately from visibility; canonical visibility does not automatically mean factual truth.
17. Make failure and negative-result evidence appendable monotone observations rather than deletions of failed hypotheses.
18. Add a `CognitiveTxn` type that binds execution, lease, state, schema and identity epochs.
19. Add a `CommitCertificate` as the only proof that a non-monotone branch became canonical.
20. Add a `ConsistentCut` type spanning semantic state, execution lease, identity lineage and unresolved effects.

## Mutation boundary and architecture compression

21. Remove direct canonical-state write APIs from cognitive organs if and only if ACEF promotion tests pass.
22. Replace direct organ writes with `emit_delta`/`stage_delta` typed APIs.
23. Make the canonical publish boundary the single semantic mutation chokepoint.
24. Forbid model output from directly invoking canonical persistence primitives.
25. Forbid GWT selection/broadcast code from directly invoking canonical persistence primitives.
26. Forbid Needle route selection from directly invoking canonical persistence primitives.
27. Forbid the German translator from altering commit class, authority, epochs or provenance fields.
28. Treat JSON as transport only; no opaque JSON state blob may bypass typed ClayCode admission.
29. Require every runtime/FFI canonical write to map back to a typed ClayCode delta/commit operation.
30. Inventory all existing canonical writers and fail the ACEF promotion gate if any untracked second writer remains.

## Monotone fast plane

31. Allow deterministic join-safe raw evidence deltas to be admitted without waiting for a full cognitive commit.
32. Require `join_safe(d)` to be a type/runtime property, not an LLM judgment at commit time.
33. Forbid external effects inside a `MONOTONE_JOIN` delta.
34. Class raw provenance-bound web observations as monotone evidence while retaining `UNTRUSTED_EXTERNAL_DATA` authority.
35. Class raw provenance-bound visual percepts as monotone evidence where the percept record itself does not assert learned truth.
36. Preserve raw failed-provider/recovery observations even when their enclosing cognitive branch aborts.
37. Let monotone evidence survive user cancellation when it is independently admissible and privacy policy permits.
38. Derive mutable scores such as salience/interest from monotone evidence rather than treating scores themselves as monotone truth.
39. Make evidence deduplication hash/join based so repeated fetches do not inflate truth weight.
40. Add an ablation that disables monotone fast admission to quantify its actual benefit and complexity cost.

## Non-monotone belief, goals and learning

41. Stage model inferences as `NON_MONOTONE` branch-private deltas by default.
42. Stage world-belief revisions as non-monotone unless a deterministic join proof exists.
43. Stage self-model revisions as non-monotone and identity-lineage bound.
44. Stage goal adoption/retirement as non-monotone state transitions.
45. Stage learned MVC labels/prototypes as non-monotone candidate learner state.
46. Stage outcome-derived episodic memories as `EFFECT_COUPLED` when their truth depends on an external result.
47. Stage reward plasticity as `EFFECT_COUPLED` and require verified outcome plus causal-use evidence.
48. Stage slow personality/homeostatic updates as `EFFECT_COUPLED` when driven by task outcomes.
49. Prevent `OUTCOME_UNKNOWN` from committing any success- or failure-conditioned belief.
50. Preserve unresolved non-monotone alternatives in Hyperposition instead of selecting one merely to unblock persistence.

## Hyperposition branch geometry

51. Represent each unresolved alternative as a typed `HypothesisBranch` under one CognitiveTxn.
52. Bind each branch to an explicit assumption set analogous to a truth-maintenance environment.
53. Record branch contradiction sets without immediately deleting the branch history.
54. Distinguish `DOMINATED` from `CONTRADICTED`; low score is not logical inconsistency.
55. Permit several internal branches under the one owner-fixed external execution lease.
56. Forbid branch multiplicity from creating multiple concurrent external Frank execution leases.
57. Require branch-local effect proposals to converge through the same single effect-authority boundary.
58. Add deterministic branch-count and memory budgets to prevent combinatorial explosion.
59. Add branch garbage collection only after preserving ancestry, negative-result and retraction receipts.
60. Permit branch merge only when assumption/provenance/authority constraints are compatible and the merge is explicitly receipted.

## GWT reconstruction

61. Make each `WorkspaceEpisode` reference its `tx_id`, `branch_id`, source state epoch and source graph epoch.
62. Treat GWT as a selective projection over transactional semantic state rather than the container of canonical truth.
63. Allow GWT to broadcast provisional branch-private candidates with explicit provisional status.
64. Preserve the existing invariant that ignition changes accessibility, not truth.
65. Bind every selection receipt to the exact branch/candidate universe it competed over.
66. Bind every receiver receipt to tx/branch/candidate identity.
67. Add a first-class `CausalUseReceipt` separating delivered, reconstructed, used and local-effect states.
68. Require material causal credit to reference a `CausalUseReceipt`, not broadcast exposure alone.
69. Require learned re-entry to reference a CommitCertificate or explicit failure-evidence commit.
70. Make truthful/shuffled/provenance-broken/no-reentry controls operate on transaction/branch identity, not only message content.

## UnifiedDB evolution

71. Add an append-only `semantic_deltas` relation or equivalent typed physical projection.
72. Add `tx_branches` for branch lifecycle and assumption/contradiction metadata.
73. Add `causal_dependencies` for explicit delta-parent edges.
74. Add `commit_certificates` with roots over admitted delta and causal sets.
75. Add `consistent_cuts` for restart/recovery frontiers.
76. Add `effect_tx_links` connecting existing effect reservations/attempts/outcomes to cognitive transactions without merging authorities.
77. Add `causal_use_receipts` as durable causal-credit evidence where required.
78. Add `retraction_events` rather than physically deleting invalidated semantic history.
79. Add `projection_cursors` so ClayGraph and bounded model assemblies can prove which commit head they reflect.
80. Extend indexes around `(tx_id, branch_id, source_epoch, visibility, monotonicity)` based on measured query workload rather than speculative indexing everywhere.
81. Convert `semantic_records` gradually into a current-state projection over admitted history rather than deleting the existing table upfront.
82. Bind each `state_epoch.root_hash` to the admitted delta/commit root.
83. Extend `semantic_transactions.status` with stages sufficient for prepared/effect-pending/outcome-unknown/committable semantics.
84. Encode current transaction ops as typed deltas where semantics match, preserving migration lineage.
85. Make snapshots reference the exact commit/cut head used to rebuild current views.

## ClayGraph and differential topology

86. Derive canonical ClayGraph topology only from admissible UnifiedDB commit history plus explicit current projections.
87. Permit an optional provisional graph overlay keyed by tx/branch, never mistaken for canonical topology.
88. Bind every graph epoch to the source semantic commit/cut it projects.
89. Turn semantic retractions into targeted graph invalidation events.
90. Compute dependency closure from authoritative causal edges rather than only inferred graph salience.
91. Evaluate differential retraction against full graph rebuild as a required matched baseline.
92. Keep activation/salience as derived accessibility fields with zero truth/effect authority.
93. Bind graph selection receipts to source commit, source graph epoch and selector hash.
94. Bind graph receiver receipts to ACEF causal-use receipts where the receiver path matters.
95. Reject graph-derived edges whose source commit has been retracted unless a newer valid derivation rescues them.

## Effects, API and concurrency

96. Preserve the existing `frank_effects.clay` authorization/reservation/attempt/unknown/verify/DONE state machine as authority, not replace it with generic transactions.
97. Link an effect reservation to its originating cognitive tx/branch without letting the cognitive transaction broaden effect authority.
98. Make `OUTCOME_UNKNOWN` suspend outcome-coupled cognitive commit while allowing unrelated safe monotone evidence to remain admitted.
99. Preserve same-key safe retry and explicit reconciliation rules for uncertain external effects.
100. Never simulate rollback of an already possible external effect; represent compensation as a new explicit effect when policy/capability allows.
101. Open the user CognitiveTxn only after the owner-fixed global execution lease is successfully acquired.
102. Bind API request idempotency identity to execution/lease/transaction lineage so retries cannot silently create a second cognitive episode.
103. Abort/cancel provisional cognition on user cancellation while preserving unresolved external-effect reconciliation obligations.
104. Extend stale lease fencing from state/effect writes to every ACEF stage/commit primitive.
105. Reject commit from a stale schema epoch even if lease epoch is current.
106. Reject commit from a stale identity-lineage head even if lease and schema epochs are current.
107. Keep proactive acquisition rules unchanged: ACEF cannot bypass `IDLE + InteractiveIdleHandoff.CLEAR`.
108. Keep BUSY privacy unchanged; transaction metadata is not exposed to nonholders.

## Memory, reward, agency, Retina and language

109. Split memory persistence into raw evidence admission versus belief commit rather than one undifferentiated memory write.
110. Make retrieval expose epistemic class, provenance and commit/branch status to the selector while preventing unauthorized provisional leakage.
111. Represent contradiction repair as retraction/cascade deltas with preserved negative evidence rather than destructive erase.
112. Store active/dormant goal checkpoints against a consistent semantic cut so restart cannot combine incompatible goal/state epochs.
113. Make InitiativePulse ephemeral/derived unless an explicit audit record is needed; never let pulse become reward or canonical truth.
114. Bind reward updates to verified effect/outcome plus causal-use/credit receipts before material plasticity.
115. Admit raw Retina percepts separately from learned MVC interpretation so classifier rollback never destroys the underlying observation.
116. Promote an MVC learner version atomically with its feature/backbone compatibility metadata and rollback pointer.
117. Make Needle output a typed route/proposal delta whose authority class remains proposal/routing evidence.
118. Let the translator render current execution-visible semantics but make identity, authority, effect status and committed factual fields read-only hard constraints.
119. Build `SelfContextAssembly` from one declared consistent commit/cut head, with explicit provisional additions rather than mixed invisible epochs.
120. Define self.root continuity checks as accepted binary/build identity plus admitted persistent state lineage head, and reject stale clones that cannot prove both.

## Global acceptance consequence

These 120 deltas do not constitute promotion. The candidate must still beat or match the current Frank contracts and simpler task/belief-transaction baselines under matched crash, replay, causal, security, latency and resource tests on the accepted target VPS. A simpler architecture that dominates ACEF causes rejection, not rationalization.
