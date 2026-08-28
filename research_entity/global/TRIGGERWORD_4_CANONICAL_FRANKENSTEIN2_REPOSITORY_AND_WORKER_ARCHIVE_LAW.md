# TRIGGERWORT 4 — Canonical Frankenstein 2.0 Repository + Worker Archive Law

Status: OWNER-DIRECTED MANDATORY OPERATIONS LAW
Date: 2026-08-28

## 1. Canonical repository

The target build/evidence repository is:

`gschaidergabriel/frankenstein-2.0`

Once initialized, this repository is the canonical home of Frankenstein 2.0 implementation, architecture, workpackages, measurements, runtime receipts, negative results, checkpoints and complete build history.

The current `clay-global-research-entity` repository remains a research/control/forensics source, not the final artifact home.

## 2. Repository-first Triggerword-4 law

Every Triggerword-4 worker must, before substantive Frankenstein-2.0 mutation:

1. resolve whether `gschaidergabriel/frankenstein-2.0` exists and is initialized;
2. fetch its current `main`;
3. read `README.md`, `WORKPACKAGES.md`, `WORKER_PROTOCOL.md`, `workpackages/STATE.json`, `checkpoints/CURRENT.json` and relevant workpackage receipts;
4. resume the current accepted frontier rather than reconstructing a new plan from chat;
5. use the stable F2 workpackage ID as the primary dedupe key;
6. archive all accepted work and evidence in the canonical repository.

If the repository is not yet initialized, use the authorized bootstrap route in `gschaidergabriel/Dr.-Unterweger` and do not invent a second artifact repository.

## 3. Every coherent step becomes durable history

A Triggerword-4 worker must commit every meaningful coherent engineering step that changes the Frankenstein-2.0 state. The repository history is part of the experimental record.

Commit message convention:

`<F2-WP-ID>: <coherent step>`

Examples:

`F2-WP-200: add pulse admission score skeleton`
`F2-WP-200: add novelty residual unit tests`
`F2-WP-200: archive hold/wake benchmark receipt`

Do not make one giant end-of-session dump when multiple independently meaningful steps occurred.

Trivial temporary debugging noise does not need its own commit, but any source change, contract change, test fixture, measurement, result, accepted negative result, checkpoint or workpackage transition that matters to reproducibility must become durable.

## 4. Workpackage checklist law

`WORKPACKAGES.md` is the human-readable canonical checklist.

Machine-readable state lives under `workpackages/` and `checkpoints/`.

Statuses:

- `[ ]` NOT_STARTED
- `[-]` IN_PROGRESS / HOLD
- `[x]` ACCEPTED_AT_SCOPE

A workpackage may only become `[x]` when its declared evidence exists in the repository and the acceptance receipt names the exact source/test/measurement identity.

`WORKER_SAYS_DONE != WORKPACKAGE_ACCEPTED`

## 5. Required run archive

Every discriminating test, benchmark, failure injection, target-environment run or cognitive experiment must produce a durable run directory:

`runs/<F2-WP-ID>/<run-id>/`

Minimum:

- `receipt.json`
- exact source commit(s)
- environment identity/scope
- commands or executable test identity
- pass/fail/partial/blocked result
- relevant measurements
- evidence paths
- negative-result references
- exact next action

Raw logs may be compressed when large, but the structured receipt must remain human-readable and searchable.

## 6. Measurement law

All material measurements used to justify an architectural decision must live in the canonical repository or be copied there with immutable external provenance.

Examples:

- accuracy / score;
- latency;
- tokens / context size;
- RAM / CPU / GPU;
- action count / information gain;
- retrieval precision;
- world-model prediction residual;
- false completion rate;
- transfer / negative-transfer rate;
- child spawn / recovery / concurrency evidence;
- lesion and ablation results.

A claim such as `better`, `faster`, `more intelligent`, `more robust` or `cheaper` earns no promotion without archived measurement appropriate to the claim.

## 7. Negative-results law

Failed hypotheses and non-improving changes are first-class artifacts.

Store them under `negative_results/` and link them from the responsible workpackage/run.

Do not erase failed experiments merely because a later path succeeds. This prevents future workers from repeating disproven approaches and is part of Method Memory for the engineering process itself.

## 8. Checkpoint law

Before a worker stops, it must update a durable checkpoint containing at minimum:

- current workpackage;
- generation/claim identity;
- source commit after work;
- strongest current evidence;
- unresolved defect or uncertainty;
- exact next action;
- any blocked external condition.

The next Triggerword-4 worker resumes from this checkpoint.

## 9. Parallel worker / anti-stampede law

Multiple Triggerword-4 workers may run concurrently, but they must not become parallel authorities over the same workpackage generation.

Required behavior:

- refresh `main` before claim and before push;
- claim stable workpackage/subpackage identity;
- prefer independent workpackages when parallelizing;
- stale generations cannot overwrite newer accepted state;
- if the frontier has already moved, validate/fuse instead of duplicating;
- rebase/CAS-style update before shared checklist/state changes;
- preserve conflicting experimental results rather than silently overwriting them.

## 10. External research / Triggerword-5 ingestion

Triggerword 5 still disassembles the current donor `gschaidergabriel/frankenstein` and feeds evidence into Triggerword 4.

When Triggerword 4 adopts a Triggerword-5 result, the relevant distilled packet/contract/provenance must be copied or summarized into the Frankenstein-2.0 repository under `research/` or `architecture/` so the final artifact does not depend on chat history or hidden worker state.

Historical sources are allowed only when needed to resolve the provenance of a concrete current-donor mechanism; they are not the primary Triggerword-5 target.

## 11. Repository completeness target

By whole-system acceptance, the canonical repository must contain or immutably index all material artifacts needed to understand and reproduce the final system:

- source;
- architecture contracts;
- tests;
- workpackages;
- run receipts;
- measurements;
- accepted and rejected experiments;
- benchmarks / cognitive-unit-test results;
- build/runtime instructions;
- checkpoints;
- migration/provenance history;
- final artifact/package manifests.

`CHAT_ONLY_RESULT != ARCHIVED_PROJECT_RESULT`
`TEMPORARY_WORKER_STATE != PROJECT_MEMORY`
`EXTERNAL_RESEARCH_RESULT != INTEGRATED_EVIDENCE` until archived with provenance.

## 12. Security phase

Dedicated security/hardening systems are deferred until Frankenstein 2.0 functional architecture is sufficiently complete to know the real attack surface. Their historical evidence may be archived for later use, but they do not preempt current functional/cognitive build work.

Engineering isolation, exact identity, provenance and reproducible measurement remain required because they are necessary for valid evidence, not because they are the final security architecture.

## 13. Final law

`TRIGGERWORT_4 = BUILD + TEST + MEASURE + COMMIT + ARCHIVE + CHECK_OFF + CHECKPOINT + CONTINUE`

A successful Triggerword-4 step is not finished until its durable artifacts are in `gschaidergabriel/frankenstein-2.0`.