# FRANK Trigger Research Report — Cycle 2: Workspace Reachability Before Optimization

- **run_id:** `20260808T0551+0700-chatgpt-secondary-r2`
- **trigger:** `frank`
- **actor:** `chatgpt-secondary`
- **provider/model:** OpenAI / GPT-5.6 Sol
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **Project-Frankenstein HEAD:** `abba90a5767d85abc8a1ac340bae92842dab35c1`
- **parent FRANK run:** `20260808T0520+0700-chatgpt-secondary-r2`
- **promotion:** none

## Executive synthesis

The previous FRANK run identified synchronous GlobalWorkspace callbacks as an architectural latency risk and proposed a two-lane hot/side-effect design. This second run deliberately tried to falsify that interpretation before turning it into implementation advice.

The correction is important:

1. The **current visible Thalamus GWS callback is tiny**: on high-salience events it only updates two monotonic timestamps. Therefore the stronger claim that the present GWS is already suffering a slow-subscriber bottleneck is not supported by the inspected code.
2. More importantly, static indexed source search finds `services.global_workspace` references only in the workspace module itself and `services/thalamus.py`; `get_workspace()` is not found outside its defining module. This does not prove that runtime/dynamic publishers do not exist, but it means **active multi-producer workspace wiring is not statically demonstrated**.
3. The `GlobalWorkspace.publish()` path itself does **not implement coalition competition or winner selection**. Every call becomes a broadcast event. `salience` is attached to events but not used in the visible publish path to decide which candidate wins access.

Therefore the next highest-information FRANK experiment changes from transport optimization to **live causal reachability**:

> Does a representative FRANK session actually generate candidate competition, a selected workspace winner, broadcast, downstream effect, outcome and reentry that changes subsequent behavior?

Until this is shown, optimizing the bus risks optimizing a mostly decorative or incompletely wired GWT surface.

---

## 1. Grounding and continuity

Canonical RAE remained r2 with the same state hash. Project-Frankenstein HEAD also remained unchanged from the preceding FRANK trigger run. The new cycle therefore isolates a research delta rather than conflating it with code churn.

Relevant inherited evidence:

- `H-G3-005`: functional GWT episodes require causal identity/order/receipt/authority links, not stage labels alone.
- `N-G3-005`: stage-presence validation rejected only 13.33% of 9,000 causal mutants in the prior sandbox; labels are insufficient.
- prior FRANK cycle: current GlobalWorkspace is synchronous; MemoryHub is semantically unified but serial; Core contains direct cross-organ persistence writes; Router policy is a candidate for semantic collapse while model execution remains isolatable.

This cycle concentrated on the GWS uncertainty frontier rather than repeating the full architecture survey.

---

## 2. Current-code findings

### 2.1 The visible Thalamus GWS callback is not a credible current latency bottleneck

`Thalamus.__init__()` subscribes `self._on_gws_event`. The exact callback body checks `event.salience >= 0.7` and, if true, writes two `time.monotonic()` timestamps (`_last_gws_event_ts`, `_last_burst_ts`). It performs no DB write, no LLM call, no network call and no expensive transformation.

**Negative result:** the previous generic slow-subscriber risk should not be restated as a current observed FRANK bottleneck.

This does not invalidate the architectural risk: synchronous subscriber execution still means future expensive subscribers would transfer their latency into the publisher. It only narrows the claim correctly.

### 2.2 Static reachability of the workspace is weak

Repository code search over indexed HEAD found:

- `services.global_workspace` in the workspace module and Thalamus;
- a static `subscribe("thalamus", self._on_gws_event)`;
- no statically discovered `get_workspace()` consumer outside the defining module;
- no statically discovered multi-producer network through the obvious workspace API.

This evidence is not equivalent to a complete runtime call graph. Dynamic imports, reflection, plugins, generated code or external processes can evade static search. The correct status is therefore **OPEN negative result / verification required**, not REFUTED live GWT.

### 2.3 GlobalWorkspace is currently a broadcast primitive, not a competition mechanism

The module documentation says only one coalition wins access to the workspace. The implementation does not realize that mechanism in `publish()`:

- create event;
- append to bounded history;
- copy subscriber list;
- invoke every subscriber.

There is no visible candidate set, competition function, ignition threshold, winner identity or loser suppression in this path. `salience` is metadata here, not selection.

This is a direct code-level example of the distinction RAE already enforces: **GWT-shaped naming is not GWT causality**.

---

## 3. Synthetic lesion: slow-subscriber transfer and async tradeoff

The local control experiment injected known callback costs to isolate dispatch semantics.

### Synchronous delay sweep

| Injected subscriber delay | Publisher p50 | Publisher p95 |
|---:|---:|---:|
| 0 ms | 0.000075 ms | 0.000525 ms |
| 1 ms | 1.096875 ms | 1.106478 ms |
| 5 ms | 5.088135 ms | 5.119214 ms |
| 20 ms | 20.114208 ms | 20.148488 ms |

The synthetic publisher inherits subscriber work approximately one-for-one.

### Queue control

For 40 events with a 20 ms side-effect worker:

- synchronous publisher p50: **20.10 ms**;
- async queue publisher p50: **0.000571 ms**, no drops with capacity 128;
- bounded capacity-8 drop queue publisher p50: **0.000722 ms**, but **32/40 events dropped**.

A Thalamus-like callback microbenchmark remained sub-microsecond to low-microsecond even when replicated across many synthetic subscribers.

### Interpretation

The experiment supports two narrow mechanism statements:

1. synchronous dispatch transfers callback cost into publisher latency;
2. naive async decoupling converts latency risk into backlog/drop/ordering semantics.

It does **not** support a claim that current FRANK is slow because of GWS.

---

## 4. External research fusion

### ROS 2 executor model

ROS 2 makes callback execution policy explicit through executors and callback groups; callbacks can be mutually exclusive or reentrant, and groups can be placed under different executors/threads so control-loop work can receive priority over other callbacks. This is an implementation analogue for FRANK's need to separate deterministic hot cognitive reducers from slower effect work rather than putting every callback under one policy.

Source: ROS 2 `Executors` and `Using Callback Groups` documentation.

### NATS slow-consumer model

NATS treats slow consumers as a first-class system condition. Pending buffers are bounded; clients can observe slow-consumer errors, and systems may drop/disconnect rather than allow one consumer to destabilize the whole system. This supports the need for explicit overflow policy and observability, but FRANK cannot copy NATS semantics blindly because some cognitive events may be causally non-droppable.

Source: NATS `Slow Consumers` documentation.

### Event-sourced agent architectures

Recent agent-system work (`ESAA`, 2026; `The Log is the Agent`, 2026) independently separates probabilistic cognition from deterministic state mutation and emphasizes append-only causal traces / replayable projections. This strengthens the prior FRANK proposal that async side-effect execution must retain causal receipts rather than becoming opaque fire-and-forget work.

### GWT-inspired agent work

`Theater of Mind for LLMs` (2026 preprint) frames a GWT-inspired agent architecture as an active event-driven dynamical system with a central broadcast hub. It is useful as external architecture context, not evidence that FRANK currently implements GWT. The discriminating question remains whether competition/broadcast has causal effect in FRANK's own runtime.

---

## 5. Hypothesis generation 2

### H-FRANK-R2-01 — Workspace may be weakly or non-operational in representative live sessions

**Mechanism:** current code contains a workspace object and a subscriber but lacks statically obvious producers.

**Prediction:** an instrumented representative session may show zero or sparse workspace broadcasts.

**Counterprediction:** runtime/dynamic publishers produce a rich stream despite static search.

**Falsifier:** live telemetry showing multiple identified producers and recurrent broadcasts in representative tasks.

### H-FRANK-R2-02 — Current GlobalWorkspace does not itself implement coalition competition

**Mechanism:** all `publish()` calls are broadcast directly.

**Prediction:** simultaneous candidate events are all accepted unless an upstream selector exists.

**Counterprediction:** another layer deterministically gates candidates before publish.

**Falsifier:** locate and lesion an upstream competition mechanism with winner/loser identities.

### H-FRANK-R2-03 — Causal receipts will distinguish real GWT from decorative broadcast

**Prediction:** requiring candidate→winner→broadcast→effect→outcome→reentry IDs will expose missing links in current traces.

**Counterprediction:** current runtime already reconstructs the complete chain without new instrumentation.

**Test:** instrument one representative task and validate with the existing CC-RC1.1 causal-episode concepts.

### H-FRANK-R2-04 — Current Thalamus GWS callback is not a material latency source

**Prediction:** target-host callback duration remains negligible relative to LLM/memory/persistence work.

**Falsifier:** live p99 callback measurements show unexpected blocking or lock contention.

### H-FRANK-R2-05 — One global async mode is inferior to typed delivery semantics

Candidate classes:

- `MUST_APPLY`: every event causally required; overflow is a visible fault/backpressure condition;
- `LATEST_WINS`: intermediate state updates may coalesce, preserving the newest value;
- `BEST_EFFORT`: observational telemetry may be dropped under pressure.

**Falsifier:** a single uniform policy matches or exceeds semantic correctness, replayability and latency across all event classes.

### H-FRANK-R2-06 — Async without receipts can hide causality

**Prediction:** latency improves while causal replay becomes ambiguous unless enqueue/start/finish/drop/coalesce receipts are recorded.

### H-FRANK-R2-07 — Competition and deterministic state reduction should remain replayable even if effects become asynchronous

**Prediction:** replaying the same ordered candidate/winner events reconstructs the same active state while side-effect timing may vary.

### H-FRANK-R2-08 — Instrumentation-first migration minimizes unnecessary architecture churn

**Prediction:** measuring current callback p99, producer counts and causal reachability will eliminate some proposed refactors before code migration begins.

---

## 6. Architecture delta

The previous `FRANK Semantic Runtime` recommendation survives, but the workspace subsection is revised.

### Do now

1. Add `producer_id`, `candidate_id`, `episode_id`, `causal_parent_id` and monotonic sequence to workspace-related trace records.
2. Instrument `publish_count`, producer cardinality, subscriber duration p50/p95/p99, queue/dispatch delay and downstream effect receipts.
3. Explicitly locate or implement candidate competition/selection before claiming a GWT winner.
4. Run representative live tasks and prove at least one complete causal workspace episode.
5. Integrate these receipts with CC-RC1.1 rather than introducing a second tracing vocabulary.

### Do not do yet

- Do not replace current synchronous Thalamus handling merely because async is fashionable.
- Do not promote a two-lane queue to architecture truth before live callback measurements.
- Do not infer GWT from a class named `GlobalWorkspace`.
- Do not drop events without event-class semantics and receipts.

### Once live wiring is proven

Introduce per-effect execution classes and budgets. Keep deterministic state reducers synchronous when they fit measured hot-path budgets; move I/O/slow effects to scheduled executors; use explicit overflow/coalescing policy and maintain causal receipts across both.

---

## 7. Priority experiments

1. **EXP-FRANK-GWS-LIVE-REACHABILITY** — representative session; count producers, candidates, selected winners, broadcasts, effects, outcomes and reentries.
2. **EXP-FRANK-GWS-COMPETITION-LESION** — compare current path with winner-selection removed/shuffled/randomized once a real selector is located or implemented.
3. **GWS callback timing instrumentation** — p50/p95/p99 per subscriber under chat, idle reflection, tool use and failure conditions.
4. **Typed delivery factorial** — `MUST_APPLY`, `LATEST_WINS`, `BEST_EFFORT` under burst overload; score semantic correctness, latency, dropped causal events and replay fidelity.
5. Resume prior FRANK targets: MemoryHub fan-out, single-writer durable state, Router bypass, Android thermal factorial, live GWT lesion.

---

## 8. Knowledge compilation

New durable OPEN artifacts:

- `KMP-FRANK-20260808-GWS-STATIC-REACHABILITY`
- `KMP-FRANK-20260808-GWS-NO-COMPETITION`
- `KMP-FRANK-20260808-GWS-DELIVERY-CLASSES`
- Topic Packet `frank-workspace-causal-reachability`
- Synthetic experiment `EXP-FRANK-GWS-CALLBACK-BACKPRESSURE-R2`

No canonical scientific claim was promoted or refuted. Canonical r2 remains unchanged because the strongest new results are current-code negative observations plus a synthetic mechanism test; live runtime validation is still missing.

## Final synthesis

The strongest contribution of this cycle is a **priority correction**. FRANK does not yet need a more sophisticated GlobalWorkspace transport nearly as urgently as it needs proof that the workspace is an active causal mechanism at all.

The decisive sequence is now:

`prove producers -> prove competition/winner -> prove broadcast effect -> prove outcome/reentry -> then optimize scheduling/backpressure`

That sequence is cheaper, more falsifiable and less vulnerable to architectural Goodharting than optimizing a component because its name implies theoretical importance.
