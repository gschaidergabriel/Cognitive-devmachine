# FRANK Trigger Research Report — Cycle 3: Hybrid Freshness and Multi-Timescale Semantic Runtime

- **run_id:** `20260808T0559+0700-chatgpt-secondary-r2`
- **trigger:** `frank`
- **actor:** `chatgpt-secondary`
- **provider/model:** OpenAI / GPT-5.6 Sol
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **newest current-runtime architecture source:** `Frank-Architektur.md`, measured 2026-08-05, sha256 `98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c`
- **public Project-Frankenstein default-branch HEAD observed:** `abba90a5767d85abc8a1ac340bae92842dab35c1` dated 2026-04-05
- **promotion:** NONE

## Executive synthesis

The new runtime architecture source corrects the central uncertainty from FRANK Cycle 2. The live cognitive workspace is not the process-local `services/global_workspace.py` bus that was visible in the stale public repository. The current measured architecture identifies `services/workspace_broadcast.py` as the cognitive GWT path: six channels compete, the highest-salience candidate can ignite at `ZUENDSCHWELLE=0.55`, one focus receives full detail, the broadcast is persisted into `consciousness.db.workspace_broadcast`, and Core reads the newest row into `[INNER_STATE]`.

Therefore the highest-value problem is no longer “does a real competition workspace exist?” but **“is the workspace state causally fresh when it is consumed?”**

The measured workspace clock is 60 s. A fixed 60 s heartbeat is useful for spontaneous/idle cognition, but it can make the newest row chronologically up to ~60 s old at a randomly phased user request. The current GWT research branch independently converges on causal freshness at use time rather than indiscriminate freshness. GNW literature also describes ignition as both stimulus-triggered and spontaneous at rest. These jointly motivate a **hybrid workspace schedule**:

1. retain the 60 s heartbeat for spontaneous/idle continuity;
2. immediately refresh on high-salience breakthrough events when safe;
3. mark workspace-relevant channel revisions as semantically dirty;
4. before a Core read, refresh if relevant dependencies changed or if an age safety cap is exceeded;
5. preserve episode/receipt identity so refreshes can be causally tested rather than merely logged.

The larger architecture conclusion is also revised: FRANK's five timescales are not accidental fragmentation. They are a useful control hierarchy. The integration target is **one semantic runtime with multiple logical organs and timescales**, not one undifferentiated loop.

---

## 1. Source correction and epistemic ordering

Cycle 2 used current accessible GitHub code and found a process-local `global_workspace.py` broadcast primitive with no visible competition. That observation was correct for that file but became an incorrect inference about the current cognitive GWT.

The 2026-08-05 runtime architecture source is newer than the publicly visible Project-Frankenstein default branch and explicitly documents the repaired cross-process workspace path. It also reports measured timings and live database counts. Under FRANK protocol, current runtime evidence outranks stale architecture code for current-system claims. Cycle 2's stronger “workspace may be decorative/unwired” hypothesis is therefore superseded, not deleted.

A live code capture and trace are still required before canonical promotion because this worker has not independently executed the current FRANK host.

---

## 2. Cross-branch synthesis

### Clay G7

HSCK-G7 proposes: exact canonical events/provenance → conflict-preserving hyperposition → incremental typed projections → multi-resolution active memory → hierarchical causal governor → receipt-defined GWT → dependency-bound ClayCode → semantic proof/coordination → capability gateway → outcome/re-entry.

FRANK already contains concrete analogues of several layers: exact numeric state, semantic workspace projection, slow E-PQ state, experience vectors, memory consolidation, LoRA disposition, and an external tool path. This makes FRANK a particularly strong live target for G7 rather than a blank-slate implementation.

### GWT

The latest GWT branch adds causal freshness at use time, selective push/pull rescue and episode receipts. FRANK's current SQLite re-entry path gives a concrete place to instrument `workspace_age`, channel revision compatibility and downstream causal effects.

### ClayCode

CC7 synthetic work shows dependency-scoped freshness is much less wasteful than whole-state invalidation when dependency closure is complete, but hidden dependencies cause missed conflicts. For FRANK this means a workspace should not refresh merely because “something changed”; it should refresh when a relevant channel/version changed, while unknown relevance fails conservatively.

### Hyperposition

H2 separates semantic dependency topology, invariant/coordination topology and physical locality topology. FRANK should likewise avoid confusing logical organs with process boundaries. Amygdala, Thalamus and NAcc may remain semantically distinct while becoming colocated in one fast runtime; external capability authority and model execution may remain isolated for different reasons.

### Emergence

The emergence certificate prevents architectural language from becoming evidence. A GWT focus, novelty annotation or self-report is not sufficient for an `emergent_organ` claim. Any such claim still requires prospective prediction, lesion/rescue, recurrence/OOD and multiscale causal evidence.

---

## 3. Mapping the current FRANK architecture into a vNext runtime

### Loop A — Fast reflex kernel (< milliseconds)

Keep as logically distinct organs but colocate where safe:
- Amygdala: pre-model threat/interaction classification;
- Thalamus: gain, habituation, burst and salience breakthrough;
- Nucleus Accumbens: phasic/tonic reward dynamics;
- Needle: fast tool-intent/capability proposal reflex.

Needle belongs here semantically because the architecture intentionally removes tool planning from the 4B. But Needle must not become execution authority. It proposes; a capability gateway validates/executes.

### Loop B — Workspace/ignition kernel

`workspace_broadcast.py` is the real current candidate. Preserve:
- channel competition;
- ignition threshold;
- one dominant focus with compressed alternatives;
- silence/quiet as a valid state;
- stable self-invariant;
- semantic text rather than raw telemetry.

Add:
- episode ID;
- candidate-channel revision IDs;
- winner/runner-up salience metadata outside the LoRA-facing text;
- workspace validity epoch;
- read/effect/outcome/re-entry receipts;
- hybrid freshness scheduler.

### Loop C — Request kernel

Core should consume a fresh active projection, build the model context and invoke the Qwen-class backend. Router policy/compatibility logic can move inward toward an inference broker; the heavy model engine remains separately restartable/resource-governed until target measurements justify otherwise.

### Loop D — Slow personality/homeostasis

E-PQ remains slow and persistent. Its event weight table is an implicit value prior, not an execution policy. If goal formation is built from it, goal candidates should be observable/provenance-bound and remain subject to safety/capability constraints.

### Loop E — Consolidation and learned disposition

Memory consolidation, dream/idle reflection, experience-vector recurrence and LoRA export operate on longer timescales. The key current invariant is:

**Zahl → Wort → Gewicht**

- **Zahl:** exact measurable state in DB / `[INNER_WORLD_EXACT]`;
- **Wort:** semantic workspace projection used for self-description and model conditioning;
- **Gewicht:** slow learned disposition in LoRA.

This is a three-timescale representation boundary and should survive any process/database consolidation.

---

## 4. New hypothesis: causal freshness is FRANK's next GWT bottleneck

A fixed 60 s schedule has a simple geometric consequence: if queries arrive independently of the clock, broadcast age at read spans 0–60 s and centers near 30 s. Age alone does not mean semantic staleness; the crucial question is whether relevant state changed during that interval.

Therefore the live metric should be a vector, not one age scalar:

`workspace_freshness = {age_ms, source_epoch, relevant_channel_revisions, high_salience_pending, predictive_validity, read_episode_id}`

Recommended policy candidate:

```text
60 s heartbeat
    OR high-salience breakthrough
    OR before Core read when relevant channel revision changed
    OR before Core read when age safety cap exceeded
        -> recompute candidate set -> compete -> ignite -> persist -> read
```

This is intentionally hybrid. Pure periodic scheduling can be stale at use time; pure event scheduling would remove the spontaneous/idle workspace behavior that the architecture explicitly values.

External convergence is bounded but useful: Mashour et al. (Neuron 2020, PMID 32135090) describe GNW ignition as externally triggered or spontaneous at rest; event-triggered control literature distinguishes clock-triggered updates from state/event-triggered updates and shows that signal-aware deviation metrics can reduce communication without requiring every clock tick to carry new information.

---

## 5. Synthetic timing experiment

`EXP-FRANK-GWT-HYBRID-FRESHNESS-SYNTH-001` used the measured source constants:
- `baue_broadcast()` median 0.0035 ms;
- workspace write median 1.0565 ms;
- Core read median 0.2168 ms;
- current heartbeat 60 s.

100 seeded 24 h replications were run in three constructed regimes. These are not estimates of real FRANK state-change rates.

| regime | fixed-60 stale-query rate* | hybrid stale-query rate* | fixed broadcasts/h | hybrid broadcasts/h | every-query broadcasts/h | hybrid p95 chronological age |
|---|---:|---:|---:|---:|---:|---:|
| quiet | 21.6% | 0% | 60.0 | 64.9 | 66.2 | 6.8 s |
| conversation | 38.0% | 0% | 60.0 | 132.0 | 189.1 | 8.4 s |
| volatile | 84.7% | 0% | 60.0 | 164.3 | 189.6 | 7.2 s |

`*` Staleness is defined by the synthetic workload: at least one constructed workspace-relevant change after the last broadcast. The hybrid reaches zero by design because it refreshes before read when dirty.

Using measured median build+write elapsed time, the modeled hybrid broadcast elapsed time remained roughly 69–174 ms per hour across these synthetic regimes. This does **not** prove CPU cost, WAL/disk wear, lock contention, thermal behavior or p99 performance. It only says a live shadow-mode test is cheap enough to prioritize.

---

## 6. Needle and the capability boundary

Current training analysis says 38.3% of v26 responses contain tool calls and Needle is intended to remove this behavior from the 4B training target. That implies an architectural placement:

`user query -> fast classifiers/Needle -> capability proposal -> external authority gateway -> tool -> provenance-bound result -> exact state + optional semantic workspace projection -> Frank formulation`

Two rules follow:
1. Needle is not authority; it is a reflexive selector/proposer.
2. Tool results should re-enter FRANK through the same representation discipline as other observations. Raw numbers belong in exact state; semantic summaries may compete for workspace attention; only repeated/validated experience should affect learned disposition.

This connects Needle directly to canonical H-G3-006 and avoids replacing “4B emits tool syntax” with “26M classifier silently has execution authority.”

---

## 7. Module-collapse decisions

### Strong collapse candidates
- Amygdala / Thalamus / NAcc / workspace competition scheduler into one in-process semantic runtime, while preserving each logical state machine and timescale.
- Core-side routing/policy/context-budget logic into an inference broker.
- Repeated active-state DB reads into stable in-memory/read-optimized projections backed by durable replayable state.

### Boundaries to preserve
- model execution resource boundary;
- external capability/commit authority gateway;
- durable/replay truth boundary;
- slow LoRA/training path versus online active state;
- exact numeric state versus semantic self-description.

### Do not collapse merely for aesthetics
The architecture source contains 71 living databases and many long-lived trajectories. They are evidence-bearing state. Physical consolidation should be driven by measured query/update/replay cost and migration safety, not by a desire to reduce file count.

---

## 8. Highest-information next experiments

1. **EXP-LIVE-GWT-FRESHNESS-FACTORIAL** — fixed 60 s versus hybrid shadow mode on matched live/read-only traces; log workspace age, channel deltas, focus changes, response effects, later-state effects, WAL latency and p99.
2. **EXP-LIVE-GWT-LESION** — truthful versus delayed versus shuffled versus removed re-entry with matched compute/time.
3. **EXP-FRANK-GWT-EPISODE-RECEIPTS** — add non-LoRA-facing candidate/winner/read/effect/outcome/re-entry IDs and verify complete causal chains.
4. **EXP-FRANK-NEEDLE-CAPABILITY-TRACE** — measure wrong-tool, authority reject, fallback, latency and provenance continuity over real tool-intent traffic.
5. **EXP-FRANK-ZAHL-WORT-GEWICHT-ABLATION** — compare current separated representation against controlled leakage of exact telemetry into learned language path; measure telemetry parroting, behavior and generalization.
6. **EXP-FRANK-NOVELTY-GOAL-PROPOSAL** — let `experience_vectors.annotation/novelty` modulate goal proposal only; compare against no-novelty and shuffled novelty before allowing any goal revision authority.

---

## 9. Negative results / corrections

- **Cycle-2 correction:** current FRANK is not supported as “GWT-less/decorative” by the newest architecture source. That interpretation targeted the wrong/stale workspace implementation.
- **Performance correction:** the measured live broadcast builder is extremely cheap; GWT transport latency is not currently established as the primary bottleneck.
- **Freshness remains unmeasured live:** a 60 s tick creates potential age, but actual semantic stale-read frequency is unknown until channel revisions are logged at Core reads.
- **No consciousness promotion:** current architecture and experiments concern functional cognitive mechanisms; neither GWT structure nor self-description establishes phenomenal consciousness.

---

## Promotion decision

**NOT PERFORMED.** The runtime architecture source materially corrects FRANK interpretation and the synthetic freshness experiment gives a high-value live test, but this worker has not executed the current FRANK host. Canonical remains r2. The new output is an OPEN architecture/research delta with explicit supersession lineage.
