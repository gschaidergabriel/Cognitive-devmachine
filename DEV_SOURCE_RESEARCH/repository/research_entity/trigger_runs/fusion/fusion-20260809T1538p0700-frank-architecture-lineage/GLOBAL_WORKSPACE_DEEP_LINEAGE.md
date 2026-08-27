# FRANK Global Workspace — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: historical archaeology + current target synthesis; no canonical promotion

## Why this lineage must not be flattened

FRANK has used the phrase **Global Workspace** for several materially different mechanisms. They must remain separate in provenance and tests:

1. a model-facing `INNENWELT/INNER_WORLD` context compositor;
2. an AST-weighted multi-channel projection;
3. a persistent workspace state loop inside the consciousness daemon;
4. a process-local pub/sub `services/global_workspace.py` bus;
5. the later/repaired cross-process `services/workspace_broadcast.py` competition/ignition stage;
6. the C4-C9 research lineage of typed WorkspaceEpisodes, reader receipts, causal closure, admission and authority separation.

Treating these as one module caused a real historical failure: a component with the right name could exist while the causally consumed stage was absent.

---

## GW-0 — pre-GWT / `INNENWELT` context projection

Representative source: predecessor of `ui/overlay/workspace.py`, visible through the 2026-02-14 English conversion commit `d5608c8d2c3b404d2348ade7b05df0dd3e2c5ab5`.

Observed function:
- aggregate module outputs into one bounded model-facing inner-state text;
- channels: Body, Mood, Memory, Identity, Environment;
- explicit Self-knowledge grounding anchors;
- `INNENWELT` renamed to `INNER_WORLD` on 2026-02-14;
- target budget about 220 tokens;
- semantic purpose: make internal state feel like one integrated context rather than independent metadata fragments.

What it was **not**:
- no explicit candidate set;
- no coalition competition;
- no winner/runner-up identity;
- no ignition receipt;
- no causal delivery/use/outcome/re-entry identity.

Reusable principle:
- a bounded semantic projection can integrate heterogeneous organs for a small model;
- projection format is a causal input and must be versioned/tested.

Historical warning:
- hard-coded Self-knowledge literals can become stale and override newer architecture/training state.

---

## GW-1 — AST-weighted seven-channel model-facing workspace

Representative source: `ui/overlay/workspace.py` at commit `f2cb3914a4b35885d115d239790b716d044e0058` (2026-02-20).

Delta from GW-0:
- channels expanded to Body, Perception, Mood, Memory, Identity, Attention, Environment;
- recurrent perception and AST attention entered the workspace;
- `attention_weights` scaled channel character budgets roughly 0.5x..1.5x;
- high-salience mood could expose richer temperament/style context;
- overall budget expanded from ~220 to ~295 tokens.

Important conceptual step:
- attention changed **representation bandwidth**, not yet a formally receipted global competition stage.

Current reuse:
- retain operation-conditioned bounded projection;
- reject implicit coupling where attention weight silently changes semantic completeness;
- reader projection must declare omissions/loss and exact source identity.

---

## GW-2 — persistent consciousness-daemon workspace state

Representative source: `services/consciousness_daemon.py`, especially the February 2026 RPT/experience/AST/goal expansion (`f300491dfcfa5766e56f3a11fc2842f6bb69f55c`) and later resource retuning.

Observed state:
- `WorkspaceSnapshot` persisted body/mood/memory/identity/environment/attention/mood/energy;
- `workspace_state` rows persisted a rolling history;
- recurrent perception, 64D experience vectors, AST attention competition and persistent goals increasingly fed this state;
- initial refresh was around 30 s;
- later resource tuning changed workspace 30 -> 60 s, perception 0.2 -> 1 s, experience 60 -> 120 s, attention 10 -> 20 s, mood 60 -> 120 s.

Meaning:
- FRANK had a persistent *state workspace* and many distinct rates before the later explicit ignition stage.
- multiple timescales were functional design, not mere microservice noise.

Current reuse:
- preserve multi-rate semantics;
- replace blind fixed polling where event/use-time freshness is more causal;
- persist identities/epochs, not only text snapshots.

---

## GW-3 — process-local `GlobalWorkspace` pub/sub bus

Creation: commit `f1ea0b47ef74cad16a3aadb9e63f633fd97a4e5d` (2026-03-07).
File: `services/global_workspace.py`.
Frozen-head blob remained unchanged from creation.

State/event model:
```text
WorkspaceEvent = {
  timestamp,
  event_type,
  source,
  data,
  salience
}
```
Runtime:
- process-local singleton;
- subscriber dictionary;
- recent ring buffer (100);
- thread-safe `RLock`;
- per-subscriber exception isolation;
- `publish()` appends event and synchronously calls every subscriber.

Critical corrections:
1. Documentation called publish "non-blocking", but callbacks execute synchronously in the publisher thread. Error isolation is not latency isolation.
2. Comments describe one winning coalition, but `publish()` itself has **no candidate competition or winner selection**. Salience is carried as metadata.
3. Frozen-head indexed usage shows the bus itself and Thalamus as the obvious static import surface; this was not evidence of a rich cross-process cognitive workspace.

Thalamus coupling:
- Thalamus subscribed as `"thalamus"`;
- events with salience >= 0.7 merely updated sensitization timestamps (`_last_gws_event_ts`, `_last_burst_ts`).

R2 research correction:
- do not infer GWT causal function from a class/module name;
- prove producer -> candidate -> competition -> winner -> broadcast -> downstream use -> outcome -> re-entry.

Current status:
`REUSE_AS_EVENT_BUS_PRECURSOR_NOT_FULL_GWT`.

---

## GW-4 — deletion fracture: UI cleanup severed cognitive projection

Commit: `ce00787f4cabe65859132a762251e39449ad5ca5`, 2026-03-19, "Remove overlay and writer — Web UI is the only interface".

The whole `ui/overlay/` tree was removed as UI. The later 2026-08-05 measured architecture report states that the original workspace implementation had lived there and was therefore deleted unintentionally as part of interface cleanup.

Observed long-horizon consequence from the measured live report:
- other modules kept running;
- `experience_vectors` accumulated 1440 rows with no reader;
- system did not crash;
- behavior instead appeared confused;
- the missing cognitive function remained silent for months.

This is a first-class historical failure pattern:
`component/process health != causal-path health`.

Mandatory target test:
- a release must fail if workspace production exists but no valid consuming/re-entry path exists;
- require end-to-end liveness and causal-use receipts, not service-presence checks.

---

## GW-5 — repaired `workspace_broadcast.py` competition/ignition stage

Measured source: `Frank-Architektur.md`, live system + repository + SynthEq graph, 2026-08-05. Restoration is reported as 2026-08-01.

Function:
`baue_broadcast(q)` converts a state set into exactly one bounded stage.

Bühnenkanäle:
- Körper;
- Wahrnehmung;
- Alarm;
- Stimmung;
- Gedächtnis;
- Denkmodus.

Candidate salience:
- combines channel/AST weights with channel-specific bonuses;
- perception gets a positive bias;
- body gets +0.5 on service failure;
- alarm uses approximately `0.35 + 0.55 * urgency`.

Competition:
- top candidate ignites when `score >= 0.55`;
- one focused channel receives full detail (`FOKUS_ZEICHEN = 320`);
- alternatives are compressed (`KURZ_ZEICHEN = 90`);
- total `MAX_ZEICHEN = 1100`;
- if no channel crosses threshold, quiet/still state is intentionally compact.

Self-invariant:
- each broadcast begins with a stable core-self line to resist semantic drift.

Representation law:
- raw numeric state stays outside stage text (`INNER_WORLD_EXACT`/exact state path);
- stage carries semantic words;
- slow learned disposition is a third timescale (`Zahl -> Wort -> Gewicht`).

Cross-process re-entry:
```text
workspace_broadcast(
  id,
  timestamp,
  inhalt,
  fokus_kanal,
  gezuendet,
  zeichen
)
```
Daemon writes to `consciousness.db`; Core reads latest row read-only into `INNER_STATE`.

Measured 2026-08-05 medians (n=300 in source report):
- build: 0.0035 ms (p95 0.0039 ms);
- Core read: 0.2168 ms (p95 0.2743 ms);
- DB write: 1.0565 ms (p95 1.1729 ms).

Measured cadence: approximately 60 s.

Key lesson:
- compute cost was already negligible relative to model inference;
- the priority is causal timing/selection/closure, not shaving microseconds from `baue_broadcast()`.

---

## GW-6 — adaptive ignition / focus hysteresis research candidate

Source: 2026-08-06 `Global_Workspace_Verbesserungsvorschlag.pdf` built from the measured August architecture.

Candidate additions (not historical deployed truth):
- retain 60 s as safety/idle heartbeat;
- trigger immediate reevaluation on user input, alarm/service failure, strong state change, prediction error, memory novelty, `novel|drift|shifting`, material goal change;
- focus hysteresis candidate:
  `challenger > 0.55 AND challenger > current + 0.12`, except hard interruption;
- focus lifecycle candidate: `IGNITE -> HOLD -> RESOLVE -> DECAY`;
- internal metadata: focus id/channel/trigger/start/last-confirmed/unresolved/confidence/prediction-error/replacement-reason;
- measure whether attention was useful after response/action;
- run in shadow mode before gaining control.

Fusion disposition:
- event/use-time refresh is strongly retained;
- exact hysteresis margin `0.12` and focus lifecycle parameters remain experimental, not frozen architecture truth;
- outcome-calibrated selection must not directly self-modify truth/authority.

---

## GW-7 — R1/R2/R3 scientific correction sequence

R1 integrated-runtime research:
- one semantic runtime / causal graph is more important than one process;
- preserve authority/model fault domains;
- centralize causal receipts and durable mutation.

R2 falsification pass:
- public `global_workspace.py` did not demonstrate competition or broad static producer reachability;
- optimize only after proving causal reachability.

R3 correction using newer measured runtime source:
- current runtime had the repaired `workspace_broadcast.py` six-channel competition/ignition path;
- main uncertainty shifted from "does a workspace exist?" to "is workspace state causally fresh when consumed?";
- hybrid periodic + dirty/event/read-triggered refresh became the priority candidate.

Rule retained:
- later evidence supersedes current-system interpretation but does not erase the earlier negative result or why it arose.

---

## GW-8 — C4 to C9 semantic evolution

### C4 — CognitiveFrame / WorkspaceEpisode
- validated causal frame before workspace selection;
- candidate -> competition -> winner -> workspace commit -> word projection;
- selection state separated from textual projection.

### C5 — CognitiveEpochCapsule / reader ABI
- seal exact frame + semantic graph epoch + activation + Assembly before competition;
- graph activation explicitly not GWT ignition;
- projection receipt records semantic/wire identity and reader profile.

### C6 — Clay-native workspace
- all semantic workspace state expressed in Clay/ClayCode;
- exact state/provenance/epistemic roles typed;
- same semantic language does not collapse stages;
- recurrence in one language is not emergence evidence.

### C7 — Organ Runtime Fabric
- semantic organ, process, storage and authority boundaries become independent axes;
- workspace selection consumes operation-specific MOSAIC/Assembly state;
- winner remains non-authoritative.

### C8 — Selective Cognitive Runtime Fabric
- rich persistent memory separated from small active cognitive slice;
- system-level workspace distinguished from model-internal workspace;
- reader handoff and optional internal-uptake intervention get distinct receipts;
- resource governor cannot remove required correctness/provenance obligations.

### C9 — Typed Causal Admission & Effect Fabric
- `presence != admissibility != selection != authority`;
- required context means guaranteed candidate availability, not forced winner;
- system winner can influence model yet still have no effect authority;
- effect authorization happens only after proposal via host-minted permit and release-time revalidation.

---

## GW-9 — current lineage-fused target

Current target is not a larger prompt and not merely the historical 0.55 winner function.

Required logical stages:
```text
source evidence / state delta
 -> source+epoch+provenance admission
 -> operation-scoped candidate domain
 -> Thalamus/attention/salience shaping
 -> required-context closure
 -> candidate competition
 -> WorkspaceEpisode selection/ignition
 -> typed reader projection
 -> model/system receiver reconstruction
 -> optional measured model-internal uptake
 -> proposal / downstream causal use
 -> outcome
 -> re-entry
 -> scoped utility/calibration update
```

Mandatory distinctions:
- evidence present != candidate;
- candidate != selected;
- selected != broadcast/delivered;
- delivered != reconstructed;
- reconstructed != model-internal uptake;
- uptake != causal use;
- causal use != useful outcome;
- outcome/re-entry != proof of the claimed mechanism without intervention controls;
- none of the above grants external effect authority.

Perception integration:
- dissolved Digital Retina/PerceptualField may update below the workspace;
- familiar visual states may remain local when calibration/current-context validity is good;
- novelty, conflict, prediction error, action consequence and unresolved ambiguity increase GWT candidacy;
- learned familiarity is a routing prior, never sensor truth.

Temporal policy:
- preserve idle/spontaneous heartbeat;
- refresh on relevant dirty/event/use-time state;
- focus persistence/hysteresis is experimentally testable;
- stale source/basis/calibration/selection identity invalidates reuse.

Failure gates inherited from history:
1. workspace producer without consumer/re-entry is release-failing;
2. similarly named bus/projection/competition modules must have unique typed identities;
3. no service-presence-only GWT health check;
4. no uncontrolled prompt literal may define current architecture truth;
5. projection deletion/migration requires semantic dependency/reachability proof;
6. slow subscribers/effects may not silently transfer latency into deterministic hot path;
7. no async/drop policy without delivery-class and causal receipt semantics.

## Fusion decision

`REUSE + ADAPT + RETEST`.

The historical one-focus bounded stage, quiet state, causal re-entry, semantic-vs-exact representation split and multi-rate operation survive. The fixed 60 s-only policy, process-local bus as cognitive workspace, name-based architecture assumptions and unreceipted stage presence do not.
