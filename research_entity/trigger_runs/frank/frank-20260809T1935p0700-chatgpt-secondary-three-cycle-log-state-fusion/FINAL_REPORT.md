# FRANK Research Run — Logs/States Fusion, Web Triangulation, 3 Cycles, Tested Improvement

**run_id:** `frank-20260809T1935p0700-chatgpt-secondary-three-cycle-log-state-fusion`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**identity:** Research Entity temporary worker; NOT Frank  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**target host:** Andreas Ubuntu Linux developer system  
**scientific promotion:** `NONE`  
**research/implementation writes:** `COMMITTED`

## 1. User-requested execution pattern

This run executed the requested sequence synchronously:

`testing + current log/state evaluation`
`-> internal fusion`
`-> external web research`
`-> hypotheses + counterhypotheses`
`-> renewed fusion`
`-> repeat for 3 cycles`
`-> final analysis`
`-> improve one concrete research/runtime-adjacent component`
`-> route all material results back into the Research Entity`.

No target-Ubuntu execution, live local 4B experiment or scientific promotion is claimed.

## 2. Current state and log fusion before Cycle 1

The authoritative GitHub state remains RAE-8.8 revision 2 at the canonical file, while the repository head has advanced substantially through many implementation/research commits. Current program state remains `BASE_CLAYCODE_RELEASE`; H1 is still blocked by BASE even though multiple H1 semantic reference slices already exist.

The most relevant recent FRANK/Harness evidence is:

- H-WP-02 StateLedger has multiple implementation lineages. The merged oracle candidate has strong hosted/container tests but remains a differential candidate, not target-Ubuntu production truth.
- ActiveAssembly now has deterministic scoring, epoch freshness, ancestry caps, explicit conflict visibility, re-expansion references, fail-closed same-ID divergent payload detection and authority non-minting.
- A prior 10,000-trial synthetic adversarial run found that unconditional conflict-first reservation can starve ordinary high-value packets when conflict cardinality saturates the hard context budget.
- Receiver-causal `WorkspaceEpisode` exists as an H1 ordinary-code reference with 17/17 hosted tests and separates ignition/admission, addressability, delivery, reconstruction, uptake, causal use, outcome and re-entry.
- Recent FRANK integration work moved the bottleneck from inventing more organs toward preserving shared identity/epoch/causal semantics while these slices are joined.
- ClayCode BASE work is advancing concurrently, including real sealed effect/runtime bridges and stricter Andreas-Ubuntu target gates, but current release status must be read from authoritative acceptance receipts rather than commit names.

Initial integrated causal spine:

`StateLedger / semantic basis`
`-> dependency-prepared candidate evidence`
`-> bounded ActiveAssembly`
`-> WorkspaceEpisode / event-bus null`
`-> loop/readout decision`
`-> model/peer proposal`
`-> deterministic capability/effect gateway`
`-> outcome`
`-> provenance-bound re-entry`
`-> durable semantic delta`.

The primary newly selected research problem was not whether conflict should be visible. That is already supported by executable counterexamples. The problem was whether **conflict visibility should be allowed to consume an unobserved fraction of the complete local-4B cognitive slice**.

## 3. Cycle 1 — Internal fusion -> external primary research -> first hypotheses

### 3.1 Internal fusion result

Three constraints collide:

1. Explicit contradictory alternatives should remain visible.
2. Repeated shared ancestry must not masquerade as independent support.
3. The local 4B has a hard bounded active context, so every reserved conflict representative consumes capacity that could carry unrelated high-value evidence.

Therefore `conflict exists` cannot safely be treated as a cost-free scheduling command.

### 3.2 External primary evidence

External evidence was used as mechanism context only, not as FRANK validation.

- SQLite isolation documentation: WAL provides snapshot isolation; readers can hold an older snapshot while writers commit; read-to-write promotion can fail when the snapshot is stale; `BEGIN IMMEDIATE` acquires write intent early. Source: https://www.sqlite.org/isolation.html
- SQLite WAL/locking documentation further preserves the need to test single-writer contention, checkpoints, recovery, stale snapshots and connection lifecycle rather than assuming WAL is operationally transparent. Sources: https://www.sqlite.org/wal.html and https://sqlite.org/src/file?ci=tip&name=doc%2Fwal-lock.md
- `DF-RAG: Query-Aware Diversity for Retrieval-Augmented Generation` (arXiv:2601.17212) reports that relevance-only retrieval can introduce redundancy and that dynamically balancing relevance and diversity can improve reasoning QA.
- `Vendi-RAG` (arXiv:2502.11228) similarly treats diversity versus quality as a tradeoff rather than a single absolute objective.
- `ConflictRAG` (arXiv:2605.17301) supplies additional evidence that contradictory retrieved knowledge should be explicitly detected/handled, but does not imply that every conflict should receive unlimited active-context reservation.
- `DeepLoop` (arXiv:2607.13491) shows repeated parameter visits in looped Transformers alter stability/scaling conditions; recurrence depth is not free.
- `Fixed-Point Reasoners` (arXiv:2606.18206) shows adaptive halting/fixed-point approaches can be useful in looped models, but this remains model-level evidence and does not validate FRANK's external recurrence controller.
- XGrammar primary project/paper evidence shows constrained decoding can guarantee structural admissibility for supported grammars, but syntax correctness remains distinct from semantic tool correctness and execution authority. Sources: https://github.com/mlc-ai/xgrammar and arXiv:2411.15100.

### 3.3 First hypothesis generation

Cycle-1 hypotheses:

- conflict allocation should become an explicit measured resource variable before policy changes;
- no fixed global conflict quota should be assumed optimal;
- grouped/latent conflict representation plus selective re-expansion may preserve contradiction awareness with fewer slots;
- integrated Golden Trace identity may be more valuable now than another standalone component;
- ledger semantic/version/trace identities should remain distinguishable until target differential evidence says otherwise;
- receiver-causal GWT remains open against an equally instrumented EVENT_BUS null;
- recurrence policy must be evaluated after estimator noise/freshness and overhead;
- structured generation remains proposal-structure assistance, never authority.

## 4. Cycle 2 — Synthetic policy discrimination and counterhypothesis search

### 4.1 Preregistered goal

The second cycle deliberately did **not** ask which policy wins in production. It asked whether the obvious repair — fixed conflict quotas — can be selected from the current evidence.

A deterministic synthetic generator was used to create bounded ActiveAssembly-like scenarios with:

- context budgets 4, 8 and 16;
- 0..7 two-way conflict groups;
- three deliberately high-value ordinary packets;
- unrelated distractors;
- deterministic seed `20260809`.

Arms:

- current unconditional conflict-first;
- fixed 25% conflict reservation;
- fixed 50%;
- fixed 75%;
- a simple diagnostic adaptive heuristic.

The experiment covered 19,200 authored scenarios. It is synthetic mechanism evidence only.

### 4.2 Aggregate result

Overall critical-packet recall / complete conflict-pair recall:

- current conflict-first: `0.54135 / 0.82007`
- fixed 25%: `0.95738 / 0.55226`
- fixed 50%: `0.89467 / 0.65122`
- fixed 75%: `0.74884 / 0.72318`
- diagnostic adaptive heuristic: `0.85385 / 0.65541`

No arm dominates both objectives.

### 4.3 Structural counterexample

At budget 8 with four generated two-way conflict groups, current conflict-first fills all eight available slots with conflict representatives. In this authored setup, recall of the three high-value ordinary packets becomes `0.0`, while complete conflict-pair visibility remains `1.0`.

This is a structural resource counterexample, not a production failure rate.

### 4.4 Counterhypothesis result

The strong counterhypothesis to a simple repair survives:

> A fixed quota may merely move the failure from ordinary-evidence starvation to contradiction loss.

Therefore a global 50% cap is **not selected**.

The correct next evidence is matched H1/live trace evaluation under fixed semantic state and fixed context budgets, with conflict density, task correction cost, provenance fidelity and downstream outcome all observed.

## 5. Cycle 3 — Concurrent-head refresh, integration fusion and concrete improvement

### 5.1 Concurrent-head refresh

During the run the repository continued to advance. Recent FRANK work had already sealed more WorkspaceEpisode replay identity and preserved compatibility, while ClayCode concurrently added Ubuntu target-gate and effect/runtime-bridge work.

This materially supports a current project law:

`start snapshot only != valid long research cascade`.

The run therefore did not freeze its conclusions to the first head observed.

### 5.2 Final Cycle-3 synthesis

The policy decision itself should remain OPEN. What was missing was cheap, explicit observability of the resource pressure that creates the failure.

The smallest coherent improvement is therefore not a new scheduler. It is a non-authoritative diagnostic surface that exposes:

- total active budget;
- selected count;
- number of `CONFLICT_VISIBILITY` slots;
- ordinary selected count;
- conflict-slot fraction;
- total budget utilization;
- ordinary capacity remaining;
- re-expansion-reference count;
- unknown selection-role count;
- pressure band `NONE | LOW | MEDIUM | HIGH | SATURATED`;
- explicit `selection_policy_changed=false`;
- explicit `execution_authority=false`;
- deterministic diagnostic hash bound to the observed assembly identity.

This makes the scheduling frontier measurable without pretending the diagnostic is truth or authority.

### 5.3 Implemented improvement

Created:

- `research_entity/harness/reference/active_assembly_pressure.py`
- `research_entity/harness/tests/test_active_assembly_pressure.py`

Commits:

- module: `4ac4656054b05e906d9ec3ab7158f78ea7414f78`
- tests: `d6043b82a3c2d17fa0b0058ef47664fceed71cfa`

Hosted local validation before GitHub write:

- 5 tests total;
- 5 passed;
- 0 failed.

Covered:

- full conflict-only budget -> `SATURATED`;
- half-conflict occupancy -> `MEDIUM` with remaining ordinary capacity visible;
- unknown roles are observed rather than reinterpreted;
- budget violation fails closed;
- diagnostic hash deterministic.

At the later GitHub combined-status check, no status checks were returned for the test commit, so no GitHub-CI PASS is claimed.

### 5.4 Useful concurrency negative result

The first test-file write hit a GitHub `409` because main advanced between sequential writes. The stale write was not forced. The head was refreshed and the new-file write then succeeded.

This is preserved as a positive repository/CAS behavior receipt, not hidden as noise.

## 6. Three-cycle architecture conclusion

The current FRANK research bottleneck is now best described as **identity-preserving integration under bounded cognitive resources**, not missing component vocabulary.

Highest-information current sequence:

1. Target-Ubuntu H-WP-02 three-lineage differential to adjudicate semantic/version/trace/epoch/idempotency behavior.
2. Build one integrated ordinary-code Golden Trace that binds StateLedger basis, ActiveAssembly identity/pressure, WorkspaceEpisode stages, recurrence decision, effect lineage, outcome and re-entry.
3. Replay that trace under controlled ActiveAssembly policies rather than modifying policy from synthetic evidence.
4. Preserve EVENT_BUS, fixed-recurrence and ordinary retrieval baselines.
5. Only after the semantic identity spine stabilizes should H2/H3 collapse physical boundaries or claim equivalence.

## 7. Final hypothesis matrix

Persisted separately in `HYPOTHESES.json`:

- `H-FRANK-3C-01`: conflict pressure telemetry adds discriminating value without changing semantics;
- `H-FRANK-3C-02`: no single fixed conflict quota dominates across task regimes;
- `H-FRANK-3C-03`: conflict-group compression + selective re-expansion may lower slot pressure;
- `H-FRANK-3C-04`: integrated Golden Trace identity reveals mixed-epoch defects;
- `H-FRANK-3C-05`: three-root ledger identity is useful until falsified by target differential;
- `H-FRANK-3C-06`: receiver-causal WorkspaceEpisode must beat EVENT_BUS on matched diagnosis/outcome;
- `H-FRANK-3C-07`: typed recurrence is justified only if it beats fixed/event-driven baselines after noise/overhead;
- `H-FRANK-3C-08`: constrained generation helps structural admissibility but cannot replace deterministic semantic/effect authority validation.

All remain OPEN. None is scientifically promoted by this run.

## 8. Negative results and explicit non-claims

Preserved:

- no fixed 25/50/75% conflict quota selected;
- synthetic critical labels create an authored objective and therefore cannot establish production utility;
- no target-Ubuntu execution by this worker;
- no target 4B execution;
- no H1 PASS;
- no BASE release PASS claimed from concurrent commit names;
- no GWT superiority claim;
- no recurrence superiority claim;
- no emergence or consciousness inference;
- no physical UnifiedDB monolith claim;
- no constrained-decoding authority claim;
- no repository-CI PASS for the newly added diagnostic tests;
- one stale GitHub write failed with 409 and was not force-overwritten.

## 9. Research feedback written back

Durable run artifacts:

- `FINAL_REPORT.md`
- `EXPERIMENT_RECEIPT.json`
- `HYPOTHESES.json`
- `BRANCH_FEEDBACK_MANIFEST.json`

The feedback manifest routes explicit deltas to:

`clayresearch · frank · claycode · harness · claygraph · unifieddb · gwt · hyperposition · emergenz`.

The implemented diagnostic module and tests are also durable repository artifacts.

## 10. Final research decision

**Architecture fidelity:** `IMPROVED` at observability/integration-research level.  
**Selection-policy fidelity:** `OPEN`; no fixed quota selected.  
**H1 release:** `NOT_PASS`.  
**Target Ubuntu evidence:** `NOT_EXECUTED` by this worker.  
**Scientific promotion:** `NONE`.

The most useful next discriminator is now:

> bind the new conflict-pressure telemetry into the integrated H1 Golden Trace and run frozen matched policy replays after StateLedger identity is adjudicated on the actual Ubuntu target host.
