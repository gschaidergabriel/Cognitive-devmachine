# Project Frankenstein — evidence ledger

Snapshot base: `0ec6784cf06a47d4a955b1cc38ef0f0e526ec30e`.

This ledger is intentionally conservative. It answers **what kind of evidence exists?** rather than **how impressive does the archive sound?**

Lifecycle vocabulary:

`attempted` · `source-ready` · `measured` · `reproduced` · `contradicted` · `blocked` · `prepared-not-run` · `adopted` · `retired`

Evidence labels:

`CURRENT_SOURCE` · `HISTORICAL_SOURCE` · `PROJECT_MEASUREMENT` · `EXTERNAL_PRIMARY` · `INFERENCE` · `OPEN_HYPOTHESIS` · `NEGATIVE_RESULT`

## Current global boundary

`research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` at the snapshot reports:

- `active_program = ENTITYOS_HCU`;
- `product = EntityOS`;
- `integrated_cognition_compute_architecture = HCU`;
- external provider routes not admitted;
- Together forbidden;
- FreeSwarm emergency stop active;
- canonical dataset rows admitted = 0;
- EntityOS whole runtime credit = 0;
- HCU full runtime credit = 0;
- Physical-GRID10 runtime credit = 0;
- canonical-semantics credit = 0;
- training credit = 0.

These zeros are not a statement that no code exists. They are a statement that the current promotion gates have not admitted the corresponding scope.

## Cross-lineage ledger

| Domain | Lifecycle | Evidence class | What the archive supports | Current boundary / negative result | Representative paths |
|---|---|---|---|---|---|
| Project Frankenstein human layer | adopted | `CURRENT_SOURCE` | Human-readable loop, agency framing, negative results, provenance and architecture explanation exist. | Documentation is not runtime evidence. | `HUMAN_READ_THIS/README.md` |
| Frankenstein master cognition concept | source-ready / research | `CURRENT_SOURCE` + `OPEN_HYPOTHESIS` | Candidate-state objective, Hyperposition, context constraints, reflection/explanation candidates, integration plan. | Concept packet mixes epochs; must not override newer authority. | `research_entity/topic_packets/frankenstein-master-cognition-concept/` |
| Bauleiter package dispenser | source-ready / local-tested | `CURRENT_SOURCE` | Deterministic package/dependency/claim logic exists; commit records 12/12 local tests. | No live provider authority follows from local tests. | commit `854f6bc...`; Frankenstein v1 tooling paths in current tree |
| Bauleiter orchestrator | source-ready / quarantined | `CURRENT_SOURCE` + `NEGATIVE_RESULT` | Continuity/respawn orchestration code exists. | Provider-backed execution is non-operative under 9.13 HARD_OFF. | commit `854f6bc...`; guard repair `3c3dbe5...` |
| Bugfix-Frankenstein | source-ready / quarantined | `CURRENT_SOURCE` + `NEGATIVE_RESULT` | Separate watchdog/fixer design and code exist; local tests recorded. | Independent provider path required fail-closed authority gating; no live provider runtime credit. | commits `854f6bc...`, `3c3dbe5...` |
| Provider authority gate | source-ready / local-unit-pass | `CURRENT_SOURCE` + `NEGATIVE_RESULT` | Canonical entrypoints were changed to resolve authority before provider import/secret/network/Aider/fallback. | 10/10 focused local tests are source/local-unit scope only. | commit `3c3dbe5020f57065f47bd4d0a2dce3c537128797` |
| EntityOS | source-rich / unpromoted whole runtime | `CURRENT_SOURCE` + `HISTORICAL_SOURCE` | Large implementation/evidence lineage exists. | Current whole-product runtime credit = 0. Do not infer PASS from components. | `the artefact/`, EntityOS topic/runtime/evidence paths |
| HCU | research / internal / component-rich | `CURRENT_SOURCE` + `OPEN_HYPOTHESIS` | GRID/cell/shared-weight/J-Space architecture and diagnostics exist. | Full HCU runtime credit = 0; current steering keeps HCU research internal/no product promotion at the relevant delta. | HCU reports, GRID tools, J-Space research paths |
| GRID10 thread topology | measured | `PROJECT_MEASUREMENT` | Current inbox records matched 4-process/4-vCPU diagnostic: 1 thread/process ~8.3197 s/call; 2 ~23.1806; 4 produced zero completed samples in experiment timeouts. | Topology-specific only; not a global threading law, release pass, Physical-GRID10 pass, or HCU pass. | `SUPERVISOR_INBOX.json`, 9.13O steering |
| GRID10 RAM release | measured diagnostic / blocked promotion | `PROJECT_MEASUREMENT` + `NEGATIVE_RESULT` | Private-dirty signal exists. | No physical RAM credit until PSS/full-smaps/host accounting closes accounting-class alternatives. | 9.13O current frontier |
| Xeno | historical/transitional donor | `HISTORICAL_SOURCE` | Small-model / modular entity research lineage exists and informs later HCU/J-Space work. | Not a competing current product/state authority. | Xeno/MicroEntity topic and continuity artifacts |
| Global J-Space | research / prototype / measurement families | `HISTORICAL_SOURCE` + `PROJECT_MEASUREMENT` + `OPEN_HYPOTHESIS` | J-Space coordination, vector control, identity/GRF injection and research traces exist. | Local/model-specific causality requires exact checkpoint/runtime evidence and controls; no current J-Space model runtime promotion in the global credit state. | `research_entity/global/j-space/`, `research_entity/global/AGENT_ZERO_JSPACE_IDENTITY_GRF_INJECTION.md` |
| GWT / global workspace | research / measured families | `HISTORICAL_SOURCE` + `OPEN_HYPOTHESIS` | Workspace coordination is a recurring architecture/research line; explicit GWT-GRF measurement file exists. | Coherence/recurrence/self-report are not causality. Require lesion/shuffle/nuisance/rescue controls. | `agentZero/GWT-GRF-Messung-2026-08-22.md`, J-Space paths |
| GRF | research / mathematical-engineering lineage | `HISTORICAL_SOURCE` + `OPEN_HYPOTHESIS` | GRF concepts, injection, Hypermath/GRF prototypes and measurement files exist. | Exact semantics vary across epochs; do not silently unify incompatible GRF formulations. | `research_entity/00_CURRENT/latest/hyperposition-gwt-grf.md`, `research_entity/trigger_runs/hyperposition/...` |
| Hyperposition | research / prototype | `HISTORICAL_SOURCE` + `OPEN_HYPOTHESIS` | Explicit mechanisms preserve unresolved alternatives rather than collapsing them by vote. | Alternative preservation does not create truth; discriminator/evidence must resolve promoted claims. | `research_entity/00_CURRENT/latest/hyperposition-gwt-grf.md`, Hyperposition trigger runs |
| UnifiedDB | source-ready / reference implementations / historical runtime line | `CURRENT_SOURCE` + `HISTORICAL_SOURCE` | Compact, exact-top-k, incremental, ClayGraph assembly reference implementations and benchmarks exist. | Mechanism presence does not prove current Frankenstein integration. One substrate must not become a god-file or second effect authority. | `research_entity/harness/reference/unifieddb_emergent_*.py`, `unifieddb_claygraph_assembly.py`, runtime docs |
| Emergent Retrieval | source-ready / research | `CURRENT_SOURCE` + `INFERENCE` | Reference retrieval implementations support overlap/ranking across stored evidence dimensions. | It is not information appearing from nowhere and not permission to infer absent facts. | `research_entity/harness/reference/unifieddb_emergent_compact.py`, `...exact_topk.py`, `...incremental.py` |
| ClayCode | source-rich / partially gated | `CURRENT_SOURCE` + `HISTORICAL_SOURCE` | Compiler/runtime/effect/application work packages and many tests/workflows exist. | Current inbox says base release gates remain open beyond early work packages; do not call whole ClayCode release PASS. | `research_entity/claycode/`, `.github/workflows/claycode-*` |
| Training / LoRA / IAPT / SOMA | historical research + current blocked promotion | `HISTORICAL_SOURCE` + `PROJECT_MEASUREMENT` + `NEGATIVE_RESULT` | Training methods, feedback/evaluation work and checkpoint lineage exist. | Current training credit = 0; Together forbidden; finished training alone is not PASS. | training reports, trigger-2 course deltas, checkpoint/eval receipts |
| Trigger-2 paid Together lineage | attempted / authority-violating runs recorded | `NEGATIVE_RESULT` | Current inbox explicitly distinguishes diagnostic/authority-violating prior runs and says no run5 authority. | Historical spend cannot authorize new spend or preflight. | current 9.13O inbox; trigger-2 research records |
| FreeSwarm | historical/runtime-control line; emergency stop | `HISTORICAL_SOURCE` + `NEGATIVE_RESULT` | Swarm activation/supervisor/quiescence/restart-attribution tooling and metrics exist. | Current emergency stop true; provider routes unadmitted; runtime quiescence/control closure still open. | `tools/activate_6000_free_swarm.sh`, `tools/free_swarm_*`, trigger-run receipts |
| Distillery | attempted / zero accepted current credit | `NEGATIVE_RESULT` | Distillery ingestion/processing research and tooling exist. | Current global state: canonical dataset rows admitted = 0; training credit = 0. | `research_entity/00_CURRENT/latest/free-swarm-distillery.md`, distillery tools/reports |
| Forge / AgentForge | historical/research runtime line | `HISTORICAL_SOURCE` + `PROJECT_MEASUREMENT` | Forge/AgentForge host and quiescence receipts appear in archive. | A host-attributed receipt must retain exact authority/execution scope; does not imply current provider permission. | `research_entity/global/j-space/research/vps_run_receipts/2026-08-26_AGENTFORGE_HOST_CLAY_ATTRIBUTED_QUIESCENCE_RECEIPT.json` |
| Claude bridge / coding-host integration | historical / adapted | `HISTORICAL_SOURCE` | `.claude` hooks/settings and host-integration artifacts exist. | Hook source presence does not prove hook firing or durable result capture on a new host. | `.claude/hooks/rae_hook.py`, `.claude/settings.json` |
| EffectGate / EffectJournal principle | adopted | `CURRENT_SOURCE` + `HISTORICAL_SOURCE` | Deterministic effect authority and receipt/re-observation separation are established project invariants. | A model request, plan, tool intention, or unknown network outcome is not a verified effect. | EntityOS/ClayCode effect pipeline and authority artifacts |
| Perception / Retina / FrankEye / OCR/vision | historical donor families | `HISTORICAL_SOURCE` | Multiple perception generations are archived. | Do not imply every perception backend is current or simultaneously active. | perception/vision/archive paths and manifests |
| Memory / E-PQ / HistoryMemento / graph memory | historical donor families | `HISTORICAL_SOURCE` | Multiple memory/state formulations survive and explain later UnifiedDB pressure. | Memory is not current observation; fragmented historical stores are not automatically canonical. | Frank/agentZero/archive/topic packets |

## Current contradictions that must remain visible

### 1. Global program identity vs Project Frankenstein build-program wording

The current inbox says global `active_program = ENTITYOS_HCU`, product = `EntityOS`, architecture = `HCU`. The pointed 9.13O steering delta also uses `Project Frankenstein Active Build Program` as the build program under supervision.

**Treatment:** preserve both levels. Do not silently turn Project Frankenstein into a second truth/product authority, and do not erase its active build role.

### 2. Dangling owner-authority reference

During this Trigger-3 inspection, `research_entity/rooms/PROGRAM_STATE.json` referenced `research_entity/governance/OWNER_AUTHORITY_2026-08-27T1137P0700_PROJECT_FRANKENSTEIN_PROGRAM_SHIFT.json`, but the referenced file was not found at the inspected head.

**Classification:** `NEGATIVE_RESULT / AUTHORITY_DRIFT`.

**Treatment:** do not reconstruct missing authority from filenames or chat memory. Repair requires either restoring the exact source authority or updating the pointer under legitimate authority.

### 3. Green orchestration tests vs forbidden provider execution

The first coordinator-written Frankenstein tooling recorded 29/29 local tests green. 9.13O nevertheless quarantined the live provider path and later guard repair recorded another focused 10/10 local pass.

**Treatment:** local logic PASS and provider execution authority are separate dimensions.

### 4. High activity vs zero admitted training data

The archive contains large FreeSwarm/Distillery activity and metrics. Current canonical dataset admission remains zero.

**Treatment:** throughput is not evidence conversion. No accepted row/token should be invented from activity counters.

## Research gaps worth closing

1. **Authority pointer consistency** — repair the dangling current-facing owner-authority reference or explicitly retire it.
2. **Archive metadata** — produce generated, machine-readable topic/path/status indexes without copying the archive into prose.
3. **Git chronology extraction** — automate first-accessible-commit dating for key modules while explicitly labeling it as Git visibility, not invention date.
4. **Frankenstein v0.7 codependency graph** — bind state, memory, perception, reflection, prediction, goals, effect authority, training and model/runtime identity to exact source paths and measured receipts.
5. **J-Space causal discriminator matrix** — collect lesion/shuffle/rescue/nuisance-control evidence by exact model/runtime identity.
6. **Training lineage matrix** — map checkpoint -> tokenizer -> renderer -> dataset family -> split -> evaluation -> regression boundaries.
7. **Installer verification receipts** — host-specific NATIVE/ADAPTED/DEGRADED/BLOCKED outcomes with real hook/writer/result verification.

## Anti-Goodhart footer

A future curation pass must not improve this ledger by deleting rows that look bad. `blocked`, `contradicted`, and `negative result` are successful documentation states when they faithfully represent reality.