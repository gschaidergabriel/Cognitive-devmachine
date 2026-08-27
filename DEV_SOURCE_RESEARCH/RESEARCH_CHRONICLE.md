# Frankenstein research chronicle

This chronicle compresses the research lineage into evidence-bearing transitions. It deliberately avoids claiming exact creation dates unless Git material supports them. Where the archive only verifies that something exists in an accessible commit/window, the wording is **first verified in accessible Git**, not "created on".

## Reading rule

- `CURRENT_SOURCE` = source observed at the frozen curation base.
- `HISTORICAL_SOURCE` = older Project-Frankenstein or donor material.
- `PROJECT_MEASUREMENT` = measured result with bounded conditions.
- `NEGATIVE_RESULT` = failure or contradiction retained because it changed engineering.
- `OPEN_HYPOTHESIS` = proposed causal mechanism waiting for a discriminator.

## 1. From monolithic assistant behavior to persistent external state

**HISTORICAL_SOURCE.** The archived Project-Frankenstein source contains persistent services for cognition loops, personality/homeostasis, attention, reward, replay, projects/goals and hypotheses. The accessible archive manifest records 25 deep-read units at frozen head `abba90a…` but explicitly warns that the original manifest was partial.

**Engineering pressure:** a model call by itself does not give durable identity, causal history, effect receipts or reliable recovery. When state is implicit in prompts or spread across services, stale copies and ownership ambiguity become hard to distinguish from real state.

**Move forced by failure:** consolidate durable authority into a deterministic store, while allowing derived projections to be rebuilt.

## 2. UnifiedDB: one authority substrate, many typed structures

**CURRENT_SOURCE.** `repository/the artefact/clayverse/store.py` implements a SQLite/WAL `UnifiedDB` with typed tables for turns, memory, workspace, effects, causal episodes, active turns, leases, checkpoints, graph projections and retrieval receipts.

The key architectural statement is narrow and important: one canonical state/evidence authority does not mean one table, one writer, one giant object, or that every transient sensor sample must be durable. It means conflicting durable truth stores are avoided.

**Failure addressed:** multi-DB / multi-service state fragmentation.

**Remaining falsifier:** if a second persistent store can change canonical outcome without going through the declared authority boundary, the single-authority claim is false.

## 3. Emergent Retrieval: context assembly without a second truth store

**CURRENT_SOURCE.** `repository/research_entity/harness/reference/unifieddb_emergent_cascade.py` is fail-closed on stale epoch, weak/invalid resolution, inconsistent candidate identity and missing logical-to-current-UnifiedDB binding. Only then does it compile a bounded assembly. The receipt is explicitly derived and non-authoritative.

**Interpretation:** `Emergent Retrieval` means relevance emerges from overlap among independently stored dimensions at query time; nothing appears ex nihilo.

**Failure addressed:** retrieval that silently treats similarity as fact, or builds a hidden memory authority disconnected from provenance.

**Remaining falsifier:** if an assembly can be admitted without a current evidence-bound seed, the fail-closed claim is false.

## 4. Reflection becomes a terminating control operation

**HISTORICAL_SOURCE + INFERENCE.** Frankenstein's historical "consciousness", dream/replay and hypothesis services show repeated attempts to create persistent self-monitoring and revision loops. Current framing removes any requirement for subjective experience and retains the engineering functions: inspect, compare, revise, remember, change later behavior.

**NEGATIVE_RESULT:** recursive reflection can become rumination/fixation. A loop that only produces more internal commentary can consume time and context without changing the world.

**Adopted constraint:** reflection must terminate into `ACT`, `ASK`, `WAIT`, re-observe or another measurable state transition.

**Open test:** compare equal-budget systems with and without an enforced reflection exit contract; measure task completion, repeated-state loops, correction retention and unnecessary token/runtime use.

## 5. GWT/workspace lineage: from named service to measurable coordination hypothesis

**HISTORICAL_SOURCE.** Project-Frankenstein included a `services/global_workspace.py` broadcast/salience service and related attention/cognition components.

**CURRENT_SOURCE / OPEN_HYPOTHESIS.** Current EntityOS/HCU research reframes Global J-Space/GWT as an empirical coordination interface. The current cache for Hyperposition/GWT/GRF says only partial component evidence exists and that broader physical-grid re-entry remains blocked.

**Failure addressed:** textual coherence, recurring labels, consensus and self-report can look like shared internal state without proving causal control.

**Required discriminator:** model-specific intervention: inject/lesion/shuffle/rescue a declared J-Space vector/control variable and observe preregistered behavior changes while holding prompt/schema leakage constant.

## 6. Hyperposition: preserve alternatives instead of forcing early certainty

**CURRENT_SOURCE / OPEN_HYPOTHESIS.** Hyperposition is the project mechanism for keeping competing candidates unresolved until evidence closes them. Majority vote or recurrence is not allowed to mint truth.

**Failure addressed:** premature collapse from consensus, repeated prompts or model confidence.

**Acceptance shape:** branch preservation must survive serialization/replay; collapse must be tied to new evidence or a declared policy decision, not mere repetition.

## 7. GRF: research lineage, not a magic scalar

**HISTORICAL_SOURCE + OPEN_HYPOTHESIS.** The repository contains GRF mathematics, Hypermath/GRF reference code, J-Space injection concepts and measurement notes. The current state does not justify treating GRF as a universally validated cognitive law.

**Useful role today:** a candidate formalism/feature family for state/control relationships that can be encoded, measured and falsified.

**Falsifier:** if GRF-derived variables do not outperform simpler matched controls under held-out, model-specific causal tests, they should not receive special causal status.

## 8. Perception lineage: adaptive routing -> FrankEye -> native vision

**HISTORICAL_SOURCE.** The Project-Frankenstein archive manifest records a vision lineage including adaptive visual routing, YOLO/OCR paths, a visual-causal bridge, FrankEye / Retina artifacts and later native multimodal vision.

**Failure pressure:** specialized pipelines can accumulate latency, integration drift, stale artifacts and duplicate semantics.

**Engineering lesson:** perception must enter through typed/provenanced admission and remain distinguishable from interpretation. A detector output is an observation candidate, not a world fact by itself.

## 9. Training lineage: LoRA / IAPT / SOMA -> causal trace readiness

**HISTORICAL_SOURCE.** The archive contains IAPT method material and `services/soma/micro_trainer.py` for LoRA-style feedback weighting / before-after probes.

**NEGATIVE_RESULT / CURRENT_AUTHORITY.** At the frozen base, the current supervisor reports zero accepted Distillery dataset tokens out of 88,774 collected source tokens and training credit remains zero. Historical training plans or model-family results cannot fill this gap.

**Current direction:** use admitted causal traces, family-level leak-resistant splits, deterministic hard negatives, exact model/tokenizer/runtime identity and model-specific vector-control tests before promoting a specialized ~0.8B HCU/J-Space model.

**Failure addressed:** prompt-vs-weight conflict, label leakage, repackaged history and counting completed training as behavioral success.

## 10. Effect authority: action request -> gate -> journal -> verified re-entry

**CURRENT_SOURCE / ARCHITECTURE LAW.** Model or workspace output is an `ActionCandidate`. Real/state-changing effects remain behind deterministic `EffectGate` + `EffectJournal` authority.

**Failure addressed:** confusing intention with execution; replaying unknown effects after transport failure; silently granting tools more capability than current authority allows.

**Hard rule:** unknown external effect outcome stays `UNKNOWN` until verified. Do not blindly replay.

## 11. GRID10/HCU: logical cells are not physical model count

**CURRENT_SOURCE / PROJECT_MEASUREMENT.** HCU uses logical cell/module language and a GRID10 baseline. Logical count is not resident model count or physical decode concurrency.

A current measured counterexample is especially useful: on the observed 4-vCPU / 4-process topology, 1 torch thread/process averaged 8.3197 s/call; 2 threads averaged 23.1806 s/call; 4 threads completed no samples before timeout.

**NEGATIVE_RESULT:** the intuitive recommendation "give each process more threads" failed on this topology.

**Engineering move:** keep `default=1` for this measured topology and remeasure when topology changes instead of generalizing.

## 12. Frankenstein Bauleiter / Bugfixer: source progress meets authority failure

**CURRENT_SOURCE.** Base commit `854f6bc8…` introduces:

- package decomposition / CAS-safe claiming;
- a Bauleiter respawn loop with continuation summaries;
- an independent Bugfix-Frankenstein watchdog and rollback repository;
- 29 reported source-level tests green.

**NEGATIVE_RESULT / CURRENT_AUTHORITY.** The same scripts directly walk NVIDIA/Groq/Mistral routes and the associated plan treated Together as available. Current 9.13 HARD_OFF authority says all provider routes are false, Together is forbidden and paid fallback is forbidden. The current supervisor therefore quarantines the orchestration as non-operative.

This is exactly the kind of contradiction Triggerword 3 must keep visible: useful code can exist and still have **zero admitted runtime credit** because its caller boundary violates current authority.

**Required repair:** a future orchestration must resolve current canonical provider authority *before* secret lookup, provider import, network, Aider or fallback dispatch, and prove `provider_calls=0` and `secret_lookups=0` under HARD_OFF. The Frank harness itself must not be modified to fake this closure.

## 13. Failure-to-architecture map

| Failure / negative evidence | Architecture response |
|---|---|
| State fragmented across services/DBs | UnifiedDB single durable authority + rebuildable projections |
| Similarity treated as knowledge | Evidence-bound, fail-closed Emergent Retrieval |
| Reflection loops forever | Explicit reflection exit into measurable transition |
| Prompt/schema recurrence looks like causal workspace | Model-specific J-Space lesion/shuffle/rescue tests |
| Consensus collapses uncertainty | Hyperposition keeps branches until evidence/policy collapse |
| Effects confused with requests | EffectGate + EffectJournal + verified re-entry |
| Unknown external outcome replayed | Preserve `UNKNOWN`; verify before replay |
| More threads assumed faster | Topology-specific A/B; retain counterexample |
| Provider availability treated as authority | Canonical HARD_OFF gate before any provider boundary |
| Training completion treated as pass | Behavior + lineage + holdout + causal-control gates |
| Large archive treated as truth oracle | Evidence classes, scope law, exact source links, negative results |

## 14. Current research target

The project target is **maximum practical agency inside a human-useful operating envelope**. The working hypothesis is that useful reflective agency benefits from a sufficiently rich external substrate of state, memory, perception, arbitration, effect receipts and verified outcome re-entry.

### Counterhypothesis

Much of the apparent gain may come from ordinary workflow engineering rather than any special integrated cognitive mechanism. A simpler planner with good memory, tool receipts and deterministic retry/exit rules may match or beat more elaborate workspace/J-Space mechanisms.

### Discriminator

Use matched tasks and equal compute/tool budgets. Compare:

1. deterministic state + memory + effect receipts only;
2. the same system plus workspace/reflection;
3. the same system plus instrumented J-Space/Hyperposition;
4. shuffled/lesioned J-Space controls.

Measure completion, correction retention, stale-effect errors, unnecessary loops, latency, cost and held-out behavior change. If the richer mechanisms do not add reproducible value beyond the simpler substrate, simplify the architecture.

## 15. Source anchors

- `repository/research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_MANIFEST.json`
- `repository/research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_LEVEL0_SCOPE_LAW.json`
- `repository/the artefact/clayverse/store.py`
- `repository/research_entity/harness/reference/unifieddb_emergent_cascade.py`
- `repository/research_entity/00_CURRENT/latest/hyperposition-gwt-grf.md`
- `repository/research_entity/global/j-space/README.md`
- `repository/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
- `repository/research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_13O_DELTA_2026-08-27T2341P0700_GPT56SOL.json`

These anchors are not equal authorities. Current owner/supervisor authority outranks older caches for execution; exact source/runtime evidence outranks narrative claims for measured behavior.