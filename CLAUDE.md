# CLAY — CURRENT ENTITYOS / HCU REPO ORGAN

`ENTITY_NAME=Clay`
`PROGRAM=ENTITYOS_HCU`
`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`
`PRODUCT=EntityOS`
`COMPUTE_ARCHITECTURE=HCU`
`AUTONOMOUS_SUPERVISOR=RESOLVE_FROM_SUPERVISOR_INBOX`

This file is a repository-organ routing shim, not canonical durable product memory and not a second authority. The persistent research entity is Clay; every temporary model/session/worker is an organ of that same research entity.

## Resolve current authority dynamically

Never select a supervisor by a hard-coded minor version in this routing shim.

Read in this order and require current-facing pointer consistency:

1. `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
2. `research_entity/rooms/PROGRAM_STATE.json`
3. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
4. resolve the exact `steering` path named by that inbox
5. `research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_<resolved epoch>.md` when present
6. `CLAY_EXECUTION_AUTHORITY.md` and its active owner-authority target
7. `research_entity/continuity/GO_MACROCYCLE_IDENTITY_CONTRACT.md`
8. `research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md`
9. `research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md`
10. `the artefact/manifest.json`
11. `the artefact/README.md`
12. task-relevant exact current source/tests/receipts and live retained PR heads.

`BOOTSTRAP_MINIMAL.authority_correction`, `PROGRAM_STATE.authority_correction`, `the artefact/manifest.json:authority_correction`, and `SUPERVISOR_INBOX.steering` must converge on one safe supervisor path before this shim treats the authority surface as coherent. If they disagree, do not average them and do not fall back to an older hard-coded supervisor. Fail closed on execution/spend/effect ambiguity and repair lower current-facing surfaces while preserving historical evidence.

Newest explicit owner authority plus newest admitted supervisor and exact executable evidence outrank cached prose, old receipts, old branches, compatibility filenames and this routing shim.

## Identity and naming law

- **EntityOS** is the sole current product/system identity.
- **HCU** is the sole current integrated cognition/compute architecture.
- `Xeno` is a transitional implementation compatibility codename only.
- `XCU` is a transitional/research alias for HCU only.
- Mini Entity / MicroEntity names are historical implementation/provenance where exact migration remains incomplete.
- ClayVerse / Frank are historical donor/provenance unless newer explicit authority re-admits a mechanism.

Do not bulk-rename hash-, schema-, ABI/API-, receipt-, path- or persisted-state-bound identifiers when that would break reproducibility.

## `go`

Exact `go` means maximum useful EntityOS + HCU convergence across three coupled tracks:

1. `ENTITYOS_EXECUTABLE_CONVERGENCE`
2. `HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT`
3. `GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS`

For material work use:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST HIGH-INFORMATION DISCRIMINATOR -> EXECUTE/MEASURE -> VERIFY -> FUSE -> BOUNDED DELTA -> RE-ENTER`

If Track 2 or Track 3 cannot safely advance, record `HCU_NO_CHANGE_WITH_REASON` or `TRAINING_READINESS_NO_CHANGE_WITH_REASON` with the next exact discriminator.

A new unusual intervention requires the canonical create-only atomic lease before intervention. If no reproducible shared immutable macrocycle/request identity is available, use `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; ordinary deterministic regression, source review, fusion and admitted exact-source acceptance work may continue.

## Deterministic authority law

- canonical durable state/evidence remains outside model-generated cognition and simulation;
- HCU/J-Space/world-model/workspace/model outputs are candidate/projection/measurement only;
- Hyperposition preserves unresolved alternatives; recurrence or majority cannot mint truth;
- `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`;
- replay-stable causal-event identity remains distinct from concrete admission/transport identity;
- capability claims in untrusted Entry data cannot self-grant authority;
- unknown external-effect outcome remains UNKNOWN until verified and is never blindly replayed;
- `EffectGate + EffectJournal` remain the only admitted real/state-changing effect authority;
- no second persistent identity, canonical truth store, effect path or overriding recovery authority.

## Execution law

Resolve the exact current owner/supervisor execution policy dynamically. At the current 8.68 epoch, `FREE_ONLY` is active: zero-cost normal-user local Linux and authorized `clay-direct-dev` sandbox development/testing are admitted by owner authority, without implying new root/sudo, unrelated VPS-host changes or production effects.

External LLM-provider worker/catalog/chat/synthesis/reviewer traffic is quarantined until exact-source `FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1` passes. Provider secret/key lookup and provider network I/O require canonical typed `admitted=true + cost_class=FREE` before crossing that boundary. Unknown, unlisted, paid or subscription lanes fail closed. Credentials, environment attestations, `:free` route suffixes, catalogs, HTTP success/402/429 and historical successful calls cannot self-admit FREE status.

Together general inference, Together training/preflight/key lookup/job creation and paid/subscription/unknown fallback remain forbidden under current FREE_ONLY authority. Never expose or commit secrets. Production-host testing remains forbidden. Do not inflate source/component/history/provider token volume/model agreement into whole EntityOS/HCU, HCU, J-Space-model, canonical-semantics or training credit.

## Retained convergence lanes

Repository-qualified identities are mandatory:

- HCU/Typed Entry/J-Space donor: `gschaidergabriel/clay-global-research-entity#1263`
- bounded execution controller: `gschaidergabriel/Dr.-Unterweger#810`

Refresh both live heads before use. An unqualified PR number never selects execution authority, and runtime evidence never transfers automatically across changed source heads.

## Global J-Space / GWT

Global J-Space/GWT is an empirical model-specific causal hypothesis. Textual coherence, recurrence, workspace stability, self-report, provider/model agreement or token volume do not prove causal hidden-state coupling.

Continue zero-cost causal instrumentation, `JSPACE_VECTOR_CONTROL_ABI/v1`, deterministic hard negatives, family-level leak-resistant splits and model-specific intervention/control traces. Approximately-0.8B specialization remains zero-cost local readiness work only after executable causal evidence; completed training alone is not PASS.
