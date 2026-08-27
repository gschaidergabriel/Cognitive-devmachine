# FRANK Trigger Research Report — Cycle 4: ClayCode Cognitive Frames and Causal Turn Semantics

- **run_id:** `20260808T0610+0700-chatgpt-secondary-r2`
- **trigger:** `frank`
- **actor:** `chatgpt-secondary`
- **provider/model:** OpenAI / GPT-5.6 Sol
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **current runtime architecture basis:** `Frank-Architektur.md`, measured 2026-08-05, sha256 `98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c`
- **authoritative architecture artifact:** `FRANK_ARCHITECTURE.claycode.json`
- **promotion:** NONE

## Executive synthesis

Cycle 3 corrected the live GWT path and proposed hybrid freshness. Cycle 4 identifies the next missing invariant:

> **A workspace can be fresh and still be causally inconsistent if its contributing channels were sampled from incompatible logical moments.**

The new FRANK architecture is therefore centered on a first-class **`CognitiveFrame`**: a versioned, provenance-bound snapshot basis between fast state updates and workspace competition.

The target causal flow becomes:

`event -> reflex deltas -> CognitiveFrame capture/validation -> workspace candidates -> winner/ignition -> semantic WorkspaceEpisode -> word projection -> model context -> response/effect outcome -> slow homeostasis/experience -> re-entry into future frames`

The architecture is authored as ClayCode semantic IR with **16 stable modules, 12 typed state contracts and 20 typed transitions**. It preserves FRANK's five logical timescales and `Zahl -> Wort -> Gewicht`, while making causal identity, freshness, consistency, effect authority and rollback explicit.

## 1. What changed since Cycle 3

### 1.1 ClayCode is now mandatory architecture source

The current FRANK trigger contract now requires:

- `FRANK_ARCHITECTURE.claycode.json`;
- `CLAYCODE_ARCHITECTURE_MAPPING.md`;
- Clay -> ClayCode interconnect priority;
- explicit proposal classes and authority boundaries.

Cycle 4 is the first FRANK run in this sequence to satisfy that requirement.

### 1.2 Freshness != consistency

Cycle 3 asked whether the newest workspace remains semantically current when Core consumes it. Cycle 4 adds a separate question: did all inputs used to build that workspace belong to one causally compatible frame?

The 2026-08-05 runtime source reports many persistent stores and multi-rate components, but does not state whether `baue_broadcast(q)` already receives an atomic/versioned cross-source snapshot. That remains an open live question.

`S.COGNITIVE_FRAME` therefore carries:

- `frame_id`;
- global `basis_state_root` for snapshot identity/provenance;
- per-channel revision witnesses;
- causal parents;
- dependency-closure status;
- age/freshness metadata;
- consistency result.

Global root identity and scoped freshness are deliberately separated, following ClayCode CC-RC1.2. Unknown/dynamic dependency closure escalates rather than silently passing.

## 2. Executed synthetic consistency sanity check

`EXP-FRANK-C4-COGNITIVE-FRAME-TEARING-SYNTH-001` was executed locally with seed `20260808`.

Construction:
- six sources representing one conceptually coupled state epoch;
- Poisson conceptual updates;
- each update propagated independently to the six sources with 0–2 ms delay;
- six sequential reads spread across only 0.6 ms;
- 200,000 read frames per update-rate condition;
- validation accepts only frames whose six epoch witnesses agree.

| constructed update rate | mixed frame, no validation | retry/escalate with witnesses | mixed frame accepted after validation |
|---:|---:|---:|---:|
| 1 Hz | 0.1655% | 0.1655% | 0% |
| 10 Hz | 1.4990% | 1.4990% | 0% |
| 50 Hz | 7.4595% | 7.4595% | 0% |
| 100 Hz | 14.3680% | 14.3680% | 0% |

These rates are **not FRANK estimates**. The update rates, propagation delays and coupled-epoch assumption are constructed. The useful result is structural: low read latency does not imply one logical snapshot when contributing sources update independently.

SQLite's current official documentation independently supports the implementation concern without proving a FRANK bug: WAL readers see an unchanging snapshot of an individual database file/connection, while transactions across attached databases are not crash-atomic as one set when WAL is used. Therefore a semantic cross-store cognitive snapshot should be explicit if FRANK depends on one.

## 3. Causal Turn Frame

Cycle 4 phase-orders one FRANK turn:

1. **Ingress** — establish event identity.
2. **Preconscious evaluation** — Amygdala, Thalamus and NAcc produce exact-state deltas.
3. **Frame capture + workspace** — validate one frame, compete, ignite/select, persist episode.
4. **Context + inference** — Core consumes that fixed frame/episode.
5. **Outcome/effect receipts** — response/tool result is linked to the exact context.
6. **Post-response homeostasis** — E-PQ and experience updates occur after the response.
7. **Re-entry for future decisions** — those results may influence later frames/goals.

Key invariant:

> **A response may alter FRANK's future state, but post-response state cannot retroactively become a cause of the inference that produced that response.**

This converts the existing descriptive loop into a replayable causal partial order.

## 4. Workspace semantics versus token projection

Current FRANK renders the winning channel first and at greater detail while alternatives are compressed. That is part of the mechanism, but it couples semantic focus with token order/allocation.

Ok & Lee, Findings of ACL 2026, report >14 percentage-point prompt-order differences in their multiple-choice setting and trace the effect to causal-attention structure. Therefore a winner lesion that changes ordering/detail can change model output for ordinary transformer reasons.

C4 separates:

- `S.WORKSPACE_EPISODE`: candidates, saliences, winner, runner-up, ignition, frame identity;
- `M.WORKSPACE_PROJECTOR`: deterministic text projection used by `[INNER_STATE]`.

This enables stronger interventions:
- truthful winner;
- shuffled winner with matched candidate set/content budget;
- no-ignition matched-content arm;
- delayed/shuffled/removed re-entry;
- stale-frame arm;
- torn-frame injection arm.

Projection order/detail are logged as part of the causal path, not treated as invisible implementation trivia.

## 5. Cross-branch synthesis

### Clay G7
HSCK-G7 contributes exact canonical state, typed incremental projections, hierarchical governance, multi-resolution memory, receipt-defined GWT, dependency-scoped semantics and external effect authority. C4 maps these into concrete FRANK organs without upgrading Clay's synthetic results to live evidence.

### ClayCode CC7 / in-progress CC8
CC-RC1.2 separates snapshot identity from commit/use-time freshness and requires trusted derivation of dependency/effect closure. Its hidden-dependency counterexample means narrow scope is unsafe when closure is incomplete. C4 translates that into `complete | conservative | unknown` frame closure, where `unknown` escalates.

### GWT
The latest GWT branch contributes causal freshness at use time and receipt-linked candidate -> selection -> effect -> outcome -> re-entry. C4 adds a precondition: the candidate set itself must come from a validated frame.

### Hyperposition
H2 separates semantic dependency topology, invariant/coordination topology and physical locality. Thus 71 DB files are not 71 semantic organs, but neither should they be collapsed without measuring replay, recovery and consistency consequences.

### Emergence
The emergence certificate remains a hard method boundary. Workspace episodes, novelty, goal revision and self-description are mechanisms to test; none independently establishes phenomenal consciousness or an `emergent organ` designation.

## 6. ClayCode FRANK modules

The authoritative IR defines:

- `M.REFLEX_KERNEL` — Amygdala / Thalamus / NAcc, physically colocatable but semantically distinct;
- `M.COGNITIVE_FRAME_ASSEMBLER` — new snapshot/freshness consistency boundary;
- `M.WORKSPACE_ARBITER` — six-channel competition + ignition;
- `M.WORKSPACE_PROJECTOR` — semantic episode -> word projection;
- `M.REQUEST_KERNEL` + `M.INFERENCE_BROKER`;
- `M.MODEL_BACKEND`;
- `M.NEEDLE_SELECTOR`;
- `M.CAPABILITY_GATEWAY` + `M.K0_HOST_KERNEL`;
- `M.PERSONALITY_HOMEOSTASIS`;
- `M.MEMORY_FABRIC`;
- `M.GOAL_GOVERNOR`;
- `M.CONSOLIDATION_TRAINING`;
- `M.DURABLE_EVENT_STATE`;
- `M.PLATFORM_ADAPTER`.

The physical process/storage topology remains a replaceable projection of these semantics.

## 7. Zahl -> Wort -> Gewicht

The architecture makes the current runtime discipline machine-visible:

- **Zahl:** exact online state and `[INNER_WORLD_EXACT]`; may condition current inference.
- **Wort:** semantic workspace/self-description projection.
- **Gewicht:** slow consolidated learned disposition.

The essential learning-path invariant is that exact telemetry remains excluded from the LoRA experience target. Physical DB consolidation is allowed; collapsing these representational roles is not assumed safe.

## 8. Needle, goals and authority

Needle is modeled as fast proposal logic. It can choose/propose a tool operation, but the trusted host derives authoritative read/write/invariant/effect/capability closure and the capability gateway allows or rejects execution.

The same principle applies to autonomous goal formation. Novelty, recurrence and E-PQ may modulate **goal proposals**, but a goal cannot mint external authority. This separates endogenous cognition from side-effect permission.

## 9. Migration / rollback

1. **Instrumentation only:** frame/channel/episode/context/response IDs. Rollback: ignore metadata.
2. **Shadow frame validator:** log would-retry/would-escalate. Rollback: disable validator.
3. **Guarded hybrid refresh:** refresh on relevant dirty/age conditions while preserving 60 s heartbeat. Rollback: fixed 60 s.
4. **Semantic workspace episode:** persist winner/candidates/ignition and derive legacy text projection. Rollback: legacy broadcast read.
5. **Causal factorial:** matched-budget winner/re-entry/frame lesions. Rollback: stop harness.
6. **Selective physical collapse:** only after p99/replay/crash tests. Rollback: restore process adapters behind unchanged ClayCode interfaces.

## 10. Highest-information next tests

1. `EXP-LIVE-FRANK-COGNITIVE-FRAME-AUDIT` — record per-channel revisions used in every workspace build/Core read; determine whether incompatible mixed frames occur.
2. `EXP-LIVE-GWT-FRESHNESS-FACTORIAL` — fixed 60 s vs hybrid conditioned on frame consistency.
3. `EXP-LIVE-GWT-WINNER-COUNTERFACTUAL` — truthful vs counterfactual winner with candidate/token controls.
4. `EXP-LIVE-GWT-LESION` — truthful/delayed/shuffled/removed re-entry.
5. `EXP-FRANK-GOAL-PROPOSAL-LESION` — true/shuffled/removed novelty input, no autonomous effect authority.
6. `EXP-FRANK-NEEDLE-CAPABILITY-TRACE` — proposal correctness, gateway rejects, fallback and receipt continuity.
7. `EXP-FRANK-ZAHL-WORT-GEWICHT-ABLATION` — controlled telemetry leakage into training to measure parroting/drift.

## 11. Negative results / corrections

- Cycle 2's current-GWT reachability concern remains superseded by the newer runtime source.
- Cycle 3's hybrid freshness proposal is incomplete without an explicit frame-consistency rule.
- Low build/read latency is not evidence of semantic snapshot consistency.
- A winner lesion without matched content/order/budget controls is not a clean semantic-selection test.
- No claim is made that current FRANK actually suffers torn frames; live `q` construction remains uninspected by this worker.
- No consciousness claim is promoted.

## 12. Research-infrastructure delta during this run

The project owner added a new requirement during Cycle 4: there must be one trigger that researches from the **complete RAE research graph** and feeds resulting deltas back into every scientific branch.

This is now registered as exact trigger **`fusion`**. It is deliberately distinct from `clay`:

- `clay` remains the integrated Synthetic Clay foundry;
- `fusion` is the global meta-research feedback loop.

`fusion` requires full indexed coverage, a `GLOBAL_COVERAGE_MANIFEST.json`, cross-branch contradiction/shared-ancestry analysis and a `BRANCH_FEEDBACK_MANIFEST.json` containing a substantive delta or explicit `NO_CHANGE` receipt for every one of `clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`. Completion is machine-gated by `tools/fusion_research_contract.py`.

## Architecture contract validation

The current `tools/frank_architecture_contract.py` was read and its explicit checks were reproduced against the new architecture artifact:

- Clay then ClayCode priority: PASS
- required FRANK special rules: PASS
- ClayCode semantic IR: PASS
- Clay/ClayCode source ancestry present: PASS
- unique modules and operations: PASS
- proposal classes valid: PASS
- model output != authority: PASS
- external capability gateway required: PASS
- K0 host kernel non-self-authorizing: PASS
- human mapping present: PASS

The connector cannot execute arbitrary repository commands, so this is equivalent contract validation rather than a GitHub Actions run.

## Promotion decision

**NOT PERFORMED.** C4 provides a machine-readable architecture, a falsifiable consistency hypothesis and the new global `fusion` feedback mechanism, but the current FRANK host has not yet been instrumented for CognitiveFrame validity or causal winner lesions. Canonical scientific state remains r2.
