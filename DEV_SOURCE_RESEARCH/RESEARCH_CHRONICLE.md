# Frankenstein research chronicle

Fusion point: `ed70385760c03a30dea7b6ecf8f6b78cbbaa584a`.

This chronicle compresses the lineage as **failure → engineering move → remaining falsifier**. Git timestamps establish first verified presence only at the inspected scope unless creation time is independently evidenced.

## 1. Persistent external state

**HISTORICAL_SOURCE.** Project-Frankenstein accumulated persistent services for cognition loops, personality/homeostasis, attention, reward, replay, projects/goals, hypotheses/experiments, memory/graph retrieval and perception.

**Failure pressure:** state implicit in prompts or distributed across services becomes difficult to fence by generation/provenance and easy to contradict.

**Engineering move:** converge durable authority toward one deterministic substrate while keeping projections rebuildable.

## 2. UnifiedDB

**CURRENT_SOURCE.** `repository/the artefact/clayverse/store.py` implements SQLite/WAL `UnifiedDB` and calls it the “Single canonical state authority.” It contains typed turns, memory, workspace, effects, causal episodes, active turns, leases, checkpoints, graph projections and retrieval receipts.

**Failure addressed:** multi-DB/multi-service truth fragmentation.

**Falsifier:** a second durable store changes canonical outcome independently of declared admission/effect authority.

## 3. Emergent Retrieval

**CURRENT_SOURCE.** `repository/research_entity/harness/reference/unifieddb_emergent_cascade.py` requires current epoch, admitted resolution class, sufficient confidence, identity consistency and a binding to current UnifiedDB state before bounded graph/assembly propagation. Successful output is explicitly derived and non-authoritative.

**Failure addressed:** treating similarity/context as fact or letting retrieval become a hidden second memory authority.

**Falsifier:** an admitted assembly can be produced without a current evidence-bound seed or can independently mint canonical truth.

## 4. Reflection becomes terminating control

**HISTORICAL_SOURCE + INFERENCE.** Frankenstein’s persistent cognition/replay/hypothesis systems repeatedly attempted self-monitoring and revision. Current framing keeps the engineering functions and drops any requirement for subjective experience.

**NEGATIVE_RESULT:** reflection can become rumination/fixation.

**Adopted constraint:** inspect → detect mismatch → propose/store correction → alter later behavior → terminate into `ACT`, `ASK`, `WAIT`, re-observe, or another measurable transition.

**Falsifier:** equal-budget non-terminating reflection reliably beats an exit-bounded controller without unacceptable loop/latency cost.

## 5. GWT / workspace → Global J-Space hypothesis

**HISTORICAL_SOURCE.** Project-Frankenstein included a global-workspace broadcast/salience service and attention/cognition mechanisms.

**CURRENT_SOURCE / OPEN_HYPOTHESIS.** Current EntityOS/HCU work treats Global J-Space/GWT as an empirical causal coordination interface. The current cache remains `PARTIAL_COMPONENT_EVIDENCE`; broader physical-grid re-entry is not promoted.

**Failure addressed:** recurring text, labels, consensus and self-report can mimic shared causal state.

**Discriminator:** exact-model label-free intervention, lesion/shuffle/rescue, counterbalanced controls, and prompt/schema-leak tests.

## 6. Hyperposition

**OPEN_HYPOTHESIS.** Hyperposition preserves competing candidates rather than collapsing uncertainty because a majority repeats one answer.

**Failure addressed:** premature certainty from consensus/recurrence.

**Falsifier:** serialization/replay collapses branches without new evidence/policy, or simpler uncertainty tracking matches its decision value under equal budget.

## 7. GRF

**HISTORICAL_SOURCE + OPEN_HYPOTHESIS.** The archive contains GRF mathematics, Hypermath/GRF reference code, injection concepts and measurement notes.

**Useful current role:** a candidate formalism/feature family for state/control relations.

**Falsifier:** simpler matched features equal or outperform GRF under held-out, exact-model causal tests. Until then GRF is not a universal cognitive law.

## 8. Perception lineage

**HISTORICAL_SOURCE.** Archive evidence records adaptive routing, YOLO/OCR-era pipelines, visual-causal bridge work, FrankEye/Retina artifacts and later native multimodal vision claims.

**Failure pressure:** specialized pipelines accumulate latency, duplicated semantics, stale artifacts and integration drift.

**Engineering move:** perception should enter with typed identity/provenance and remain distinct from interpretation. Detector output is an observation candidate, not world truth by itself.

## 9. Training lineage

**HISTORICAL_SOURCE.** IAPT/SOMA/LoRA material includes feedback weighting and before/after probes; later work adds ClayCode/J-Space/vector-binding hypotheses.

**NEGATIVE_RESULT / CURRENT AUTHORITY:** supervisor-visible Distillery accepted dataset tokens remain zero at the last confirmed point; training credit remains zero.

**Failure addressed:** prompt-vs-weight conflict, leakage, repackaged lineage and counting job completion as behavioral success.

**Current direction:** exact model/checkpoint/tokenizer/runtime identity, admitted causal traces, family-level leak-resistant splits, deterministic hard negatives and causal/vector-control evaluation before training promotion.

## 10. Effect authority

**CURRENT ARCHITECTURE LAW.** Workspace/model output is a candidate. Real state-changing effects remain behind deterministic effect authority and a journal; unknown outcomes remain unknown until verified.

**Failure addressed:** intention confused with execution and blind replay after uncertain transport outcomes.

**Falsifier:** any path allows model/workspace output to create canonical real-world effect state without the declared gate/journal/re-observation boundary.

## 11. GRID10/HCU and the parallelism counterexample

**PROJECT_MEASUREMENT.** On the observed four-concurrent-process/four-vCPU topology:

- 1 Torch thread/process: ~8.3197 s/call average across 12 samples;
- 2 threads/process: ~23.1806 s/call average across 12;
- 4 threads/process: no completed samples inside the experiment timeouts.

**NEGATIVE_RESULT:** “more threads should be faster” failed on this topology.

**Engineering move:** retain default=1 for that measured topology and remeasure when process/CPU/model topology changes.

**Boundary:** diagnostic evidence only; no Physical-GRID10/full-HCU release credit.

## 12. Provider-capable Frankenstein orchestration: failure → quarantine → local closure

### Stage A — provider-backed source lands

At `854f6bc87780…`, package decomposition, Bauleiter respawn, independent Bugfix watchdog and provider fallback code landed; the commit reported 29 source-level tests green.

### Stage B — authority contradiction exposed

Current supervisor 9.13O identified that direct NVIDIA/Groq/Mistral/free-pool machinery and a stale Together allowance conflicted with canonical `9.13 HARD_OFF`. The orchestration was therefore **non-operative**, despite source tests.

This is a central evidence lesson: code can be real and tested while having zero admitted runtime authority.

### Stage C — fail-closed source/local-unit repair fused

Parallel Trigger-3 work on `main` preserved the original provider-capable implementations/plan as `*_PROVIDER_QUARANTINED_854f6bc*` donor provenance and replaced canonical orchestrator/bugfix entrypoints with a stdlib-only authority gate that refuses before provider import, secret lookup, network, Aider, or donor execution. The closure receipt reports `10/10` focused local tests PASS and Python compile PASS, explicitly `SOURCE_AND_LOCAL_UNIT_ONLY`.

**Current boundary:** this closes the source/local caller design defect at the fusion point but does **not** promote provider-path runtime, EntityOS/HCU, J-Space or training credit. The supervisor inbox still reflects the earlier P0 caller state and must not be silently treated as if it had issued a new promotion.

## 13. Historical Git identity becomes stronger without pretending semantic completeness

The new `PROJECT_FRANKENSTEIN_SOURCE_IDENTITY_HISTORY_ANCHOR_20260827.json` records the historical source repo default head `abba90a…`, exact root tree `ec21e66c…`, and 545 commits reachable through the observed default-branch listing, with oldest reachable parentless commit `e1a881…`.

**What this closes:** a reproducible reachable-history denominator/identity anchor.

**What remains open:** complete recursive path enumeration and repository-wide semantic-analysis denominator. The older partial deep-read manifest therefore remains partial rather than being rewritten into “complete.”

## 14. Root curation as an engineering experiment in navigability

Triggerword 3 asks for a four-entry human/public root. The literal Git transformation can preserve every technical blob/tree while moving it under `DEV_SOURCE_RESEARCH/repository/`.

**Important negative:** byte identity does not preserve path behavior. GitHub workflow discovery, imports, relative paths and installers may break simply because the location changed.

**Engineering choice:** keep the literal topology in a Draft PR as a reviewable reference; before canonical merge either adapt/revalidate path-sensitive behavior or generate the clean root as a publication/distribution view instead.

## 15. Failure-to-architecture map

| Failure / negative evidence | Architecture response |
|---|---|
| state fragmented across services/DBs | UnifiedDB single durable authority + rebuildable projections |
| similarity treated as knowledge | evidence-bound fail-closed Emergent Retrieval |
| reflection loops forever | explicit reflection exit into measurable transition |
| prompt/schema recurrence looks like causal workspace | exact-model J-Space intervention controls |
| consensus collapses uncertainty | Hyperposition preserves alternatives until evidence/policy |
| request confused with effect | EffectGate/Journal + verified outcome re-entry |
| unknown outcome replayed | preserve `UNKNOWN`; verify before replay |
| more threads assumed faster | topology-specific A/B and preserved counterexample |
| provider availability treated as authority | authority gate before provider/secret/network boundary |
| stale paid allowance survived in plan text | newer authority wins; donor plan quarantined |
| local gate test mistaken for runtime acceptance | explicit source/local-unit scope and zero broader credit |
| raw training tokens treated as dataset progress | accepted/admitted data and provenance required |
| archive identity mistaken for semantic completeness | separate Git identity denominator from recursive/semantic coverage |
| byte-preserving repo move assumed safe | path-sensitive revalidation required |

## 16. Agentic research target and counterhypothesis

**Target:** maximum practical agency inside a human-useful operating envelope, with state, memory, perception, arbitration, effect receipts and verified outcome re-entry.

**OPEN_HYPOTHESIS:** richer external substrate + reflection/workspace/J-Space improves long-horizon correction and recovery.

**Counterhypothesis:** ordinary workflow engineering — good state, memory, tool receipts and deterministic retry/exit logic — explains most or all of the gain.

**Discriminator:** matched tasks/equal budgets across (1) deterministic state+receipts only, (2) + reflection/workspace, (3) + instrumented J-Space/Hyperposition, and (4) shuffled/lesioned controls. Measure completion, correction retention, stale-effect errors, loops, latency and held-out behavior change.

If the richer mechanisms do not add reproducible value, simplify.