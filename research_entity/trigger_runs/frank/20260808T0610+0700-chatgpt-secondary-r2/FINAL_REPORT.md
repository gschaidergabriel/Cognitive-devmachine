# FRANK Trigger Research Report — Cycle 4: ClayCode Cognitive Frames and Causal Turn Semantics

- **run_id:** `20260808T0610+0700-chatgpt-secondary-r2`
- **trigger:** `frank`
- **actor:** `chatgpt-secondary`
- **provider/model:** OpenAI / GPT-5.6 Sol
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **current runtime architecture basis:** `Frank-Architektur.md`, measured 2026-08-05, sha256 `98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c`
- **authoritative architecture artifact for this run:** `FRANK_ARCHITECTURE.claycode.json`
- **promotion:** NONE

## Executive synthesis

Cycle 3 corrected the live GWT path and proposed hybrid freshness. Cycle 4 finds the next missing invariant:

> **A workspace can be fresh and still be causally inconsistent if its contributing channels were sampled from incompatible logical moments.**

The new FRANK architecture is therefore centered on a first-class **`CognitiveFrame`**: a versioned, provenance-bound snapshot basis that sits between fast state updates and workspace competition.

This yields a more precise runtime:

`event -> reflex deltas -> CognitiveFrame capture/validation -> workspace candidates -> winner/ignition -> semantic WorkspaceEpisode -> word projection -> model context -> response/effect outcome -> slow homeostasis/experience -> re-entry into future frames`

The design is authored as ClayCode semantic IR with 16 stable modules, 12 typed state contracts and 20 typed transitions. It preserves the existing five timescales and the `Zahl -> Wort -> Gewicht` representation discipline while making causal identity, freshness, effect authority and rollback explicit.

## 1. What changed since Cycle 3

### 1.1 The trigger contract itself changed

The current FRANK research protocol now requires ClayCode to be the primary architecture language and gates completion on:

- `FRANK_ARCHITECTURE.claycode.json`;
- `CLAYCODE_ARCHITECTURE_MAPPING.md`;
- an interconnect manifest prioritizing Clay then ClayCode;
- machine-checkable proposal/authority semantics.

Cycle 4 is the first FRANK run in this sequence to satisfy that source-language requirement.

### 1.2 Freshness is not consistency

Cycle 3 asked: “Is the latest workspace still semantically current when Core consumes it?”

Cycle 4 adds: “Did all inputs that produced that workspace belong to one causally compatible frame?”

The runtime source reports many persistent stores and multi-rate components, but does not specify whether `baue_broadcast(q)` receives an atomic cross-source snapshot. That gap must remain a hypothesis, not be silently filled.

The new `S.COGNITIVE_FRAME` carries:

- `frame_id`;
- `basis_state_root`;
- per-channel revision witnesses;
- causal parents;
- dependency-closure status;
- freshness age;
- consistency result.

A global root identifies the basis snapshot. Trusted scoped witnesses determine whether relevant dependencies remain compatible. Unknown/dynamic dependency closure escalates to a broader validation boundary.

This is the direct FRANK translation of ClayCode CC-RC1.2.

## 2. Synthetic consistency sanity check

`EXP-FRANK-C4-COGNITIVE-FRAME-TEARING-SYNTH-001` constructed six sources representing one conceptually coupled state epoch. Updates propagated independently with 0–2 ms delay. Workspace reads were sequential across only 0.6 ms.

| constructed coupled update rate | mixed frame accepted without validation | retry/escalate with witnesses | mixed frame accepted after validation |
|---:|---:|---:|---:|
| 1 Hz | 0.1435% | 0.1435% | 0% |
| 10 Hz | 1.531% | 1.531% | 0% |
| 50 Hz | 7.395% | 7.395% | 0% |
| 100 Hz | 14.312% | 14.312% | 0% |

The numerical rates are workload artifacts, not FRANK estimates. The useful result is structural: very low read latency does not imply one logical snapshot when sources update independently.

Official SQLite documentation independently supports the implementation concern. WAL readers see a snapshot of an individual database connection/file, while SQLite documents that multi-database WAL transactions are atomic per database file rather than as one multi-file set. This does not prove FRANK currently tears frames; it shows why cross-store cognitive consistency should be explicit rather than assumed.

## 3. The Causal Turn Frame

The architecture now makes one FRANK turn a phased causal episode:

1. **Ingress** — establish user/event identity.
2. **Preconscious evaluation** — Amygdala, Thalamus and NAcc produce exact-state deltas.
3. **Frame capture + workspace** — validate one frame; compete; ignite/select; persist episode.
4. **Context + inference** — consume the fixed frame/episode.
5. **Outcome/effect receipts** — link response/tool outcome to that exact context.
6. **Post-response homeostasis** — E-PQ and experience updates occur after the response.
7. **Re-entry for future decisions** — those changes can affect later frames/goals.

The key invariant is temporal:

> **A response may change FRANK's future state, but those post-response changes cannot retroactively become causes of the inference that produced the response.**

This turns the current descriptive loop into an auditable causal partial order.

## 4. Workspace semantics versus word projection

The current runtime source says the winning channel is rendered first and at full detail while alternatives are compressed. That is a valid implementation mechanism, but it couples semantic focus to token order and token allocation.

2026 ACL work reports >14 percentage-point prompt-order effects in a multiple-choice setup across multiple models and attributes the effect to causal-attention structure. Therefore a FRANK winner lesion that changes ordering/detail can alter output for ordinary transformer reasons even if no separate “workspace variable” exists.

Cycle 4 therefore separates:

- **`S.WORKSPACE_EPISODE`** — candidates, saliences, winner, runner-up, ignition, frame identity;
- **`M.WORKSPACE_PROJECTOR`** — deterministic text rendering for the Qwen-facing `[INNER_STATE]`.

This gives a clean experiment surface:
- truthful winner;
- shuffled winner with matched total content/token budget;
- no-ignition matched-content arm;
- delayed/shuffled/removed re-entry;
- stale-frame arm;
- torn-frame injection arm.

The projection order is always logged as part of the causal path.

## 5. Cross-branch synthesis

### Clay G7

HSCK-G7 contributes the hierarchy: exact canonical state, typed incremental projections, multi-resolution memory, hierarchical governor, receipt-defined GWT, dependency-scoped semantics and external effect authority. C4 maps this into concrete FRANK organs without treating G7's synthetic numeric results as live evidence.

### ClayCode CC7/CC8

CC-RC1.2 provides the crucial split between snapshot identity and commit/use-time freshness. Global-root mismatch is evidence that the world changed, not an automatic reject if trusted dependency closure proves the relevant state compatible. Conversely, narrow scope is unsafe when dependencies are hidden. The CognitiveFrame is the FRANK-level carrier for those witnesses.

The newly started CC8 branch explicitly identifies predicate/phantom/cross-object dependencies as an open issue. C4 therefore marks frame dependency closure `complete | conservative | unknown`; `unknown` cannot silently pass.

### GWT

GWT R2 contributes causal freshness at use time and the receipt chain `candidate -> compete -> select -> effect -> outcome -> re-entry`. C4 adds a consistency precondition: the candidate set itself must belong to a validated frame.

### Hyperposition

H2 says semantic dependency topology, invariant/coordination topology and physical topology are different. C4 therefore refuses to equate “71 DBs” with “71 organs” and refuses the opposite shortcut of merging all storage merely because semantic integration is desired.

### Emergence

The emergence certificate remains a method boundary. Workspace episodes, novelty, goal revision and self-description are measurable mechanisms, not evidence of phenomenal consciousness. Any `emergent organ` claim still requires prospective prediction, lesion/rescue, recurrence/OOD and multiscale causal evidence.

## 6. Current FRANK architecture encoded in ClayCode

The architecture source defines the following major semantic modules:

- `M.REFLEX_KERNEL` — Amygdala / Thalamus / NAcc as colocatable but distinct fast organs;
- `M.COGNITIVE_FRAME_ASSEMBLER` — new consistency/freshness boundary;
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

The physical process topology remains an implementation projection.

## 7. Zahl -> Wort -> Gewicht is now machine-visible

C4 preserves the runtime source exactly:

- **Zahl:** exact online state, including `[INNER_WORLD_EXACT]`; these values may condition current inference.
- **Wort:** workspace/self-description projection; raw telemetry is not the workspace's native prose.
- **Gewicht:** slowly consolidated learned disposition.

The important learning-path invariant is that exact telemetry is excluded from the LoRA experience target. This prevents process measurements from becoming the learned self-description merely through repetition.

## 8. Needle and goal formation

Needle is modeled as `PURE_TRANSFORM`/proposal logic leading to an `EFFECT_PROPOSAL`; the host capability gateway derives the authoritative read/write/invariant/effect/capability closure and then allows/rejects execution.

The same rule is applied to the user's longer-term autonomy target. `M.GOAL_GOVERNOR` may let novelty, recurrence and E-PQ modulate goal **proposals**, but a goal state cannot mint external authority. This preserves autonomous cognition while keeping side effects auditable and permission-bounded.

## 9. Migration plan

### Step 1 — instrumentation only
Add `frame_id`, channel revision witnesses, `episode_id`, context ID and response ID. No behavior change.

**Rollback:** ignore/drop new metadata.

### Step 2 — shadow frame validator
Compute frame consistency/freshness and log would-retry/would-escalate.

**Rollback:** disable validator.

### Step 3 — guarded hybrid refresh
Enable event/read-triggered workspace refresh only when frame closure is complete/conservative. Keep the 60 s heartbeat.

**Rollback:** fixed 60 s path.

### Step 4 — semantic workspace episode
Persist candidates/winner/ignition as semantic state and derive the legacy text broadcast.

**Rollback:** continue reading legacy broadcast text.

### Step 5 — causal intervention factorial
Run matched-budget winner/re-entry/frame lesions.

**Rollback:** stop harness; production behavior unchanged.

### Step 6 — selective physical collapse
Only after target-host p99/replay/crash tests, colocate fast reflex/frame/workspace components. Keep model and capability boundaries.

**Rollback:** restore process adapters behind the same ClayCode interfaces.

## 10. Highest-information next tests

1. **EXP-LIVE-FRANK-COGNITIVE-FRAME-AUDIT** — log per-channel revisions used in every workspace build and Core read; test whether incompatible mixed frames actually occur.
2. **EXP-LIVE-GWT-FRESHNESS-FACTORIAL** — fixed 60 s vs hybrid, now conditioned on frame consistency.
3. **EXP-LIVE-GWT-WINNER-COUNTERFACTUAL** — truthful vs shuffled winner with matched candidate set and token budget.
4. **EXP-LIVE-GWT-LESION** — truthful/delayed/shuffled/removed re-entry.
5. **EXP-FRANK-GOAL-PROPOSAL-LESION** — novelty true/shuffled/removed, goal proposal only, no autonomous effect authority.
6. **EXP-FRANK-NEEDLE-CAPABILITY-TRACE** — proposal correctness, gateway reject rate, fallback, effect receipt continuity.
7. **EXP-FRANK-ZAHL-WORT-GEWICHT-ABLATION** — controlled telemetry leakage into learning path to test whether the separation materially reduces telemetry parroting/drift.

## 11. Negative results / corrections

- Cycle 2's current-GWT reachability concern remains superseded by the newer runtime architecture source.
- Cycle 3's hybrid freshness proposal is now **incomplete without a frame-consistency rule**.
- Low read/build latency is not evidence of semantic snapshot consistency.
- A winner/content lesion without matched token/order controls is not a clean test of semantic workspace selection.
- No claim that FRANK currently suffers torn frames is made; the source does not expose enough atomicity detail.
- No consciousness claim is promoted.

## Architecture contract validation

The repository's `tools/frank_architecture_contract.py` was read. The new artifact was prevalidated locally against its explicit checks:

- Clay then ClayCode priority: PASS
- required special rules: PASS
- ClayCode semantic-IR representation: PASS
- Clay and ClayCode source ancestry: PASS
- unique modules: PASS
- unique operations: PASS
- proposal classes: PASS
- model output != authority: PASS
- external capability gateway required: PASS
- host kernel non-self-authorizing: PASS
- human mapping present: PASS

The connector cannot execute arbitrary repository scripts, so this is an equivalent local validation, not a GitHub Actions execution.

## Promotion decision

**NOT PERFORMED.** C4 produces a stronger, machine-readable architecture and a falsifiable consistency hypothesis, but this worker has not inspected current live `q` construction or run the frame audit on the FRANK host. Canonical remains r2.
