# FRANK Trigger Research Report — Integrated Cognitive/Runtime Architecture

- **run_id:** `20260808T0520+0700-chatgpt-secondary-r2`
- **trigger:** `frank`
- **actor:** `chatgpt-secondary`
- **provider/model:** OpenAI / GPT-5.6 Sol
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **research status:** architecture delta proposed; no canonical scientific claim promoted
- **primary live-code substrate inspected:** `gschaidergabriel/Project-Frankenstein` default-branch HEAD visible through GitHub (`abba90a5767d85abc8a1ac340bae92842dab35c1`)

## Executive synthesis

The strongest result of this run is a refinement of the phrase **“FRANK as one module.”** The useful target is **one semantic runtime and one causally traceable state graph, not one undifferentiated OS process or one physical database**.

Current Project-Frankenstein code already partially implements this architecture. `GlobalWorkspace` and `Thalamus` are in-process components, while remote ingress/capabilities and model inference retain stronger process/network boundaries. The main architecture problem is therefore not “microservices versus monolith” in the abstract. It is that several remaining boundaries are accidental while several state mutations are insufficiently centralized.

The recommended target is a **hybrid integrated runtime**:

1. **FRANK Semantic Runtime** — one address-space hot path for workspace arbitration, Thalamus/gating, active state, multi-rate scheduler, policy evaluation, memory query fabric, causal episode IDs and current materialized projections.
2. **Inference Backend Boundary** — Qwen-class model execution remains separately restartable/resource-governed by default, with a low-overhead local IPC or optional in-process native API when proven safe. The current Router’s policy/compatibility logic can collapse into the semantic runtime even if `llama-server`/ExecuTorch/QNN remains isolated.
3. **Capability / External-I/O Boundary** — remote gateway, tools, browser/terminal and privileged effects remain explicitly isolated. Model output never becomes execution authority.
4. **Single-writer Durable State Path** — durable mutation moves through one append-only causal event/commit path with deterministic projections and replay. Durable stores can remain specialized projections rather than being forcibly merged.

The highest-value implementation work is therefore **selective collapse plus stronger authority boundaries**.

---

## 1. Canonical grounding

Current RAE canonical state is r2 and identifies the relevant frontier as:

- CC-RC1.1 causal episode contract;
- backend-neutral set-valued hyperposition + faceted active projection;
- adaptive selective coupling with overcoupling tripwire;
- external capability/commit gateway.

Relevant current hypotheses/negative results materially constrain this FRANK redesign:

- `H-G3-003`: truthful outcome→reentry helps only when that path can affect future decisions;
- `H-G3-005`: GWT stage presence is insufficient; causal identity/order/receipt/authority links are required;
- `H-G3-006`: model-emitted syntax is not authority; an external capability/commit boundary is required;
- `N-G3-003`: one fixed coupling strength does not transfer universally;
- `N-G3-004`: a reentry flag by itself produces no useful effect when no usable information path exists;
- `N-G3-005`: presence-only GWT validation rejected only 13.33% of 9,000 causal mutants in the sandbox validator.

These results favor an architecture where one causal episode can be followed from selection through effect, outcome and reentry, while authority remains external to the language model.

---

## 2. Current-code state/dataflow findings

### 2.1 Global Workspace is already in-process — but its “non-blocking” contract is false in the current implementation

`services/global_workspace.py` describes an in-process singleton with a bounded history and states that `publish()` is non-blocking. The implementation copies subscriber callbacks under an `RLock`, then iterates them synchronously in the publisher’s thread.

**Observation:** a slow subscriber can therefore delay the publisher even though exceptions are isolated.

This is not merely documentation drift: it matters causally because one organ can inject uncontrolled latency into every producer that broadcasts an event.

**Architecture delta:** introduce a two-lane workspace contract:

- **causal hot lane:** pure bounded state reducers, synchronously allowed only under a strict execution budget;
- **side-effect lane:** queued/asynchronous subscribers for I/O, logging, expensive interpretation and anything not necessary for the immediate causal transition.

Every event should retain an `episode_id`, monotonic ordering/sequence data, source, causal parent, effect/outcome receipts and reentry relationship. Dropped/late side effects must be visible rather than silently disappearing.

**Falsifier:** if a 50 ms synthetic subscriber does not raise current publisher latency by approximately its callback duration, this diagnosis is wrong. After redesign, the same lesion must no longer materially delay unrelated producers while preserving required causal ordering.

### 2.2 Thalamus is a good example of the intended hot-path topology

`services/thalamus.py` is explicitly an in-process singleton, performs continuous per-channel gain/habituation/burst gating, subscribes to the Global Workspace, and targets sub-millisecond/millisecond-scale work without invoking an LLM.

This is semantically an organ, not a service boundary. Its **fast state transition** belongs inside the integrated semantic runtime.

Its SQLite baseline/logging responsibilities are separable from the hot gate. Sampling already acknowledges this distinction. The durable receipt path should become asynchronous/single-writer so a database stall cannot become a sensory-gating stall.

### 2.3 MemoryHub is semantically unified but physically serial

`services/memory_hub.py` provides one correct conceptual interface over five memory layers:

1. chat hybrid search;
2. Titan/LCME;
3. consciousness/ACT-R retrieval;
4. world experience;
5. user preferences.

However, `query()` calls these readers sequentially before RRF fusion and packing. This makes retrieval latency approximately the sum of independent source latencies and couples the hot prompt path to whichever source is slowest in sequence.

**Architecture delta:** retain source specialization and provenance, but implement a `MemoryFabric` with:

- concurrent readers;
- source-specific deadlines and cancellation;
- a small materialized **active working-set projection** for frequently used state;
- stable source attribution;
- deterministic fusion metadata;
- graceful partial-result semantics rather than all-or-nothing waiting.

Do **not** replace all stores with one giant shared table. Collapse the query semantics/current working set, not all durable representations.

### 2.4 Core directly mutates consciousness persistence

Current `core/app.py` contains a direct SQLite write into the consciousness activity log from the tool proxy path, including WAL mode, insert, trimming and commit.

That creates a second mutation path into state conceptually owned by the consciousness subsystem. It weakens single-writer semantics, provenance and crash-replay reasoning.

**Architecture delta:** Core emits a causal event/intention; one state committer validates and appends it. Projections update consciousness/activity views. The Core should not know the physical schema of another organ’s durable database.

This directly aligns with RAE `H-G3-005` and `H-G3-006` and with event-sourcing literature that separates probabilistic cognitive intention from deterministic mutation.

### 2.5 Router has become a compatibility boundary more than a routing organ

`router/app.py` currently describes a **single-model architecture**: all requests go to Qwen3.5-4B on `llama-server`; the old `force` model selection field is retained but ignored. Core still talks to the router over localhost HTTP.

The old semantic justification for an independent “model router” therefore appears weaker in the current code than the process boundary implies.

**Collapse candidate:** move request policy, identity/context preparation, token budgets and fallback-selection semantics into an `InferenceBroker` component inside FRANK Semantic Runtime. Keep the model engine independently restartable/resource-governed by default.

**Do not infer** that the Qwen inference engine itself must be in-process. GPU/Vulkan/NPU drivers, model mmap, OOM conditions and backend crashes provide strong reasons to retain fault/resource isolation unless target measurements prove otherwise.

### 2.6 Gateway is a boundary that should remain hard

`gateway/app.py` handles authentication, rate limiting, auditing and proxying to internal services. This is not accidental decomposition: it is an authority boundary between external requests and internal cognition/effects.

It should remain isolated, and privileged tools should follow the same pattern. A model-generated action is a request/intention; a capability gateway validates identity, scope, nonce/expiry, policy and current state before committing a side effect.

---

## 3. Fast/slow loops: collapse the scheduler, not the timescales

`services/consciousness_daemon.py` encodes many independent rates: 1 Hz perception sampling, 10 s summaries, ~20 s attention ticks, 60 s workspace updates, ~90 s perceptual interpretation, 120 s mood/experience updates, 180 s prediction checks, 300 s idle/goal work, hours-long consolidation and ultradian phases.

These are semantically meaningful **multi-rate dynamics**. They should not be flattened into one tick.

The proposal is a shared multi-rate scheduler/timer wheel or priority queue in the semantic runtime. Each organ registers:

- desired cadence/deadline;
- priority/salience;
- CPU/model budget;
- whether it may be skipped/coalesced;
- dependencies and causal parent;
- thermal/power constraints;
- recovery policy after process suspension.

This removes duplicated timers/thread drift while preserving distinct biological/functional timescales.

A scheduler should be able to slow or suppress background model calls without suppressing cheap deterministic perception/state updates.

---

## 4. Android/edge target changes the scheduler contract

Android cannot safely be treated as “Linux with a smaller GPU.” Two current primary-source constraints matter:

1. Android exposes thermal status/headroom and listeners through `PowerManager`; this can be a first-class control signal rather than merely telemetry.
2. Android limits background services and increasingly applies execution quotas/lifecycle constraints. A forever-running systemd-style consciousness daemon cannot be assumed.

Current ExecuTorch 1.3 documents Android backends spanning XNNPACK CPU, Vulkan GPU and vendor NPU paths including Qualcomm AI Engine and MediaTek. Its Vulkan backend supports FP32/FP16 and quantized linear paths including 8-/4-bit weights, but remains under active development. The official guidance is to begin with the CPU-compatible path and then optimize with device-specific delegates.

A March 2026 preprint benchmarking Qwen2.5-1.5B 4-bit on several edge/mobile platforms found that sustained mobile inference became thermally constrained and that platform behavior differed sharply. This is **not** evidence that every FRANK phone will throttle identically; it is evidence that peak tokens/s is an inadequate deployment metric and sustained thermal behavior needs direct testing.

### Recommended Android semantic architecture

- shared/native **FRANK Semantic Core** with the same causal state/transition contract as Linux;
- Android lifecycle adapter for foreground/background/suspend/restart;
- checkpoint + append-only replay so process death is a recoverable event, not identity/state corruption;
- inference adapter selected per device: CPU baseline first, then Vulkan/QNN/other NPU only after parity tests;
- `thermal_headroom`, battery/power-save state and foreground status become scheduler inputs;
- expensive idle reflection/model work is deferred/coalesced under thermal or lifecycle pressure;
- user-visible continuous mode uses only permitted foreground-service patterns; deferred maintenance uses platform scheduling rather than pretending a process is immortal.

### Qwen3.5-4B caution

The official Qwen3.5-4B model is a 4B multimodal model with a 32-layer hybrid architecture. Current Project-Frankenstein already targets Qwen3.5-4B through llama-server. Recent llama.cpp implementation reports include a June 2026 open issue involving a custom Qwen3.5-4B LoRA/GGUF block-count mismatch. That issue is practitioner implementation evidence, not proof of a general model defect; it does show that backend/version compatibility must be included in FRANK’s deployment matrix.

Do not freeze a single expected RAM/tokens-per-second number. Measure:

- model file/mmap resident set;
- runtime buffers;
- vision encoder/mmproj if used;
- KV/cache behavior by context length;
- prompt processing and token generation separately;
- cold start;
- 30–60 minute sustained load;
- thermal state/headroom;
- battery/energy;
- process-kill recovery.

---

## 5. Local synthetic boundary experiment

A small Python sandbox experiment compared boundary mechanisms. Median synthetic overhead per event was:

| Mechanism | Median µs/event | Relative to direct callback |
|---|---:|---:|
| direct callback + RLock/subscriber copy | 0.2673 | 1.0× |
| `queue.Queue` put/get | 1.3664 | 5.11× |
| JSON dumps+loads | 4.3482 | 16.27× |
| loopback HTTP via Python HTTPServer/urllib | 389.893 | 1458.63× |
| SQLite WAL commit per event | 744.720 | 2786.08× |
| SQLite in one batch | 5.3973 | 20.19× |

**Epistemic boundary:** this is a mechanism sanity check in the ChatGPT sandbox, not Project-Frankenstein runtime evidence. Python implementation choices dominate the absolute values. It supports only the hypothesis that accidental serialization/HTTP/per-event commits are worth eliminating or batching on hot paths. Target-host instrumentation is required before any performance claim.

---

## 6. Architecture delta: recommended target topology

```text
external clients / UI
        |
        v
[Capability & Remote Gateway]          HARD AUTHORITY BOUNDARY
        |
        | validated input/event
        v
+----------------------------------------------------------+
|                FRANK SEMANTIC RUNTIME                    |
|                                                          |
|  Event intake -> Thalamus -> Competition/Workspace       |
|                       |              |                   |
|                       v              v                   |
|                Active State <-> Reentry                  |
|                       |                                  |
|              Multi-rate Scheduler                        |
|                /       |        \                        |
|       MemoryFabric   Policy   InferenceBroker            |
|          |                      |                         |
|     active projections          | request                 |
+---------|------------------------|-------------------------+
          |                        |
          v                        v
 [Single-writer event log]   [Inference Backend]
 [durable projections]       llama.cpp / ExecuTorch /
          |                  Vulkan / QNN / CPU
          |
          v
 specialized durable stores

privileged effects/tools <-> [Capability Commit Gateway]
```

### Collapse into the semantic runtime

- Global Workspace arbitration/broadcast semantics;
- Thalamus/gating and other deterministic low-latency state reducers;
- active FRANK state and current materialized projections;
- multi-rate scheduling;
- memory query/fusion orchestration;
- policy evaluation for cognitive transitions;
- Router policy/compatibility logic that does not require process isolation;
- causal episode/receipt correlation.

### Keep isolated by default

- external API/security gateway;
- privileged tools/browser/terminal/system mutation gateway;
- model inference backend when it owns substantial accelerator/memory/crash risk;
- untrusted code sandbox;
- remote provider adapters.

### Keep logically distinct even if co-located

- episodic, semantic, preference and world-model stores;
- fast working state versus durable event history;
- GWT competition/broadcast versus effect/outcome/reentry;
- policy decision versus authority to execute.

---

## 7. First-generation falsifiable hypotheses

| ID | Hypothesis | Counterhypothesis | Cheapest discriminating test |
|---|---|---|---|
| F-H1 | Current synchronous GWS subscribers can inject subscriber latency into publishers. | Callback overhead is effectively isolated/non-blocking. | Register a 50 ms subscriber and measure publisher p50/p99. |
| F-H2 | Collapsing local Core→Router policy/serialization while retaining the model engine boundary reduces non-model chat-path latency without semantic change. | Router overhead is negligible or its isolation is worth the cost. | Stub-model A/B plus live model A/B; require exact request/response semantic parity. |
| F-H3 | Serial MemoryHub fan-out creates avoidable additive p95 latency. | One dominant source makes parallelization irrelevant. | Instrument each source; compare serial vs concurrent deadline-bound retrieval with same result set. |
| F-H4 | A single-writer causal event path improves replay/provenance and reduces cross-DB contention relative to direct organ-to-organ SQLite writes. | Direct WAL writes are simpler and equally reliable. | Crash/fault injection + replay hash + lock/busy telemetry. |
| F-H5 | One shared multi-rate scheduler reduces timer drift/wakeups while preserving organ timescale semantics. | Scheduler coupling creates priority inversion or timing interference. | Replay identical scheduled workload and compare jitter/deadlines/CPU wakeups. |
| F-H6 | Thermal-aware model scheduling increases sustained useful work on Android relative to peak-throughput scheduling. | Thermal control overhead reduces useful work or device thermal governor is sufficient. | 30–60 min device factorial: fixed cadence vs headroom-aware cadence, same task quality. |
| F-H7 | A materialized active state projection reduces context/retrieval latency without erasing source provenance. | Projection creates stale/contradictory state and harms retrieval quality. | OOD retrieval test + deliberate supersession/conflict injection + provenance audit. |
| F-H8 | Separating inference/resource failure from semantic runtime improves recovery compared with fully in-process model execution. | IPC/process cost outweighs fault isolation. | Kill/OOM inference process mid-episode; measure semantic state survival, restart time and outcome receipt integrity. |

---

## 8. Second fusion: what changed after external evidence

### Survived

- **Selective in-process collapse** remains favored for deterministic hot-path cognition.
- **Hard capability boundary** becomes stronger, not weaker, when the rest of FRANK is collapsed.
- **Event-sourced single-writer mutation** is supported both by RAE’s causal-contract frontier and recent agent architecture work.
- **Portable semantic runtime + replaceable inference backend** is more robust than binding FRANK identity/state semantics to llama.cpp, ExecuTorch or one Android accelerator.

### Strengthened

- Android thermals must be a scheduler input, not merely a monitoring channel.
- Lifecycle/recovery is part of cognition architecture on mobile because background execution cannot be assumed continuous.
- Active/materialized memory should be selective; “inject all history” is an anti-pattern both for latency and state quality.

### Weakened/rejected

- **“One FRANK module = one process”** is rejected as an architectural default. It conflates semantic integration with fault/resource isolation.
- **“Merge all databases to eliminate boundaries”** is not supported. The useful unification is the mutation contract, active projection and query plane; specialized durable projections may remain separate.
- **“Qwen-4B fits, therefore mobile is solved”** is rejected. Sustained thermal behavior, model/backend compatibility, context/KV memory and Android lifecycle are independent constraints.

---

## 9. Measurable migration plan and rollback conditions

### M0 — Baseline causal/latency trace

Instrument the current chat and idle-cognition paths before structural change:

- p50/p95/p99 for Gateway→Core, memory assembly, Core→Router, Router→model, post-processing;
- per-memory-source latency;
- GWS subscriber time;
- SQLite busy/commit duration;
- tokens/s and prompt-processing speed;
- episode IDs linking selection→broadcast→effect→outcome→reentry.

**Rollback/abort condition:** instrumentation changes behavior materially or adds >2% hot-path overhead without sampling/optimization.

### M1 — Correct GlobalWorkspace contract

Classify subscribers into bounded pure reducers and queued side effects. Add latency budget, queue depth, event IDs and dropped/late receipts.

**Success:** slow-subscriber lesion no longer delays unrelated publisher path while required order/causal receipts remain exact.

**Rollback:** event loss/order mismatch, unbounded queue growth, or causal projection mismatch.

### M2 — InferenceBroker / Router collapse

Move single-model request policy/context preparation into semantic runtime; retain a compatibility `/route` shim. Keep actual inference backend restartable.

**Success:** exact semantic parity and lower non-model overhead; inference crash does not corrupt semantic state.

**Rollback:** request mismatch, tool/context regression, recovery degradation or resource ownership becoming less observable.

### M3 — Single-writer causal event path

Replace direct writes into another organ’s SQLite schema with append-only validated events and deterministic projections.

**Success:** after crash at every transition boundary, replay reconstructs the same projection hash and duplicate/replayed actions do not execute twice.

**Rollback:** projection divergence, unacceptable commit latency, broken compatibility without dual-write migration.

### M4 — MemoryFabric

Parallel/deadline-bound source reads plus active projection/cache; retain source provenance and supersession.

**Success:** lower p95 retrieval latency with equal/better held-out retrieval quality and no provenance loss.

**Rollback:** stale state, contradiction collapse, source attribution loss or OOD quality regression.

### M5 — Multi-rate scheduler

Register existing independent loops in one scheduler without changing their nominal semantics first. Add resource/thermal budgets only after parity.

**Success:** same causal outputs under replay, bounded jitter, fewer wakeups/thread interactions, explicit missed-job recovery.

**Rollback:** priority inversion, missed safety/attention events, excessive jitter, loss of independent organ control.

### M6 — Android semantic-core parity before 4B optimization

Port the deterministic semantic core first and replay Linux traces on Android. Then add CPU inference baseline; only then Vulkan/QNN/NPU variants.

**Success gates:**

- deterministic state-transition parity for replayable non-model traces;
- process-kill/restart restores durable state without duplicate effects;
- 30–60 minute sustained inference profiles remain within declared thermal/battery policy;
- backend switch cannot change authority semantics.

**Rollback:** state divergence, non-recoverable process death, backend-specific semantic leakage, uncontrolled thermal degradation.

---

## 10. Priority experiments

1. **EXP-FRANK-GWS-SLOW-SUBSCRIBER** — highest information/lowest cost; confirms an immediate code-contract defect and quantifies its effect.
2. **EXP-FRANK-STATE-SINGLE-WRITER** — crash between intent/effect/outcome and verify exact replay/non-duplication.
3. **EXP-FRANK-MEMORY-FANOUT** — serial vs deadline-concurrent retrieval with quality/provenance controls.
4. **EXP-FRANK-ROUTER-BYPASS** — stub + live inference A/B; separate orchestration latency from generation latency.
5. **EXP-FRANK-SCHEDULER-PARITY** — move timers to one scheduler under recorded/replayed workload.
6. **EXP-FRANK-ANDROID-THERMAL-FACTORIAL** — CPU/Vulkan/QNN × fixed/headroom-aware cadence × short/sustained load.
7. **EXP-LIVE-GWT-LESION** remains a canonical priority and should be instrumented using the same episode/receipt system so architecture and GWT causality testing converge rather than creating separate telemetry stacks.

---

## 11. Negative results / anti-patterns preserved

- A generic “microservices are slow” claim is **not established**. Only specific hot-path boundaries are candidates for removal.
- A generic “in-process is fastest therefore best” claim is **not established**; fault, authority and accelerator boundaries have independent value.
- The sandbox microbenchmark cannot be promoted to target-host performance evidence.
- Mobile 4B feasibility cannot be inferred from one device, one quantization, one runtime or peak throughput.
- GWT broadcast cannot be treated as sufficient functional integration without downstream effect/outcome/reentry receipts.
- The model cannot authorize its own privileged action merely because the action representation is well-formed.

---

## 12. Evidence classes and external sources

### Project/canonical evidence

- RAE canonical r2, active hypotheses, negative results and causal GWT sandbox evidence.
- Current accessible `Project-Frankenstein` code: `services/global_workspace.py`, `services/thalamus.py`, `services/memory_hub.py`, `services/consciousness_daemon.py`, `core/app.py`, `router/app.py`, `gateway/app.py`.

### Primary/authoritative platform/runtime documentation

- Android `PowerManager` thermal APIs: https://developer.android.com/reference/android/os/PowerManager
- Android background execution limits: https://developer.android.com/about/versions/oreo/background
- Android service behavior: https://developer.android.com/develop/background-work/services
- ExecuTorch Android integration/backends: https://docs.pytorch.org/executorch/stable/using-executorch-android.html
- ExecuTorch Vulkan backend: https://docs.pytorch.org/executorch/stable/android-vulkan.html
- ExecuTorch LLM deployment: https://docs.pytorch.org/executorch/stable/llm/getting-started.html
- Official Qwen3.5-4B model card: https://huggingface.co/Qwen/Qwen3.5-4B

### Scholarly/preprint evidence — retain preprint class

- Tummalapalli et al., *LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load*, arXiv:2603.23640.
- Filho, *ESAA: Event Sourcing for Autonomous Agents in LLM-Based Software Engineering*, arXiv:2602.23193.

### Implementation/practitioner evidence — not scientific proof

- llama.cpp issue #24737, Qwen3.5-4B custom LoRA/GGUF block-count mismatch: https://github.com/ggml-org/llama.cpp/issues/24737

### Synthetic execution evidence

- `LOCAL_MICROBENCHMARK.json` in this run folder. It is explicitly non-live/non-promotable.

---

## 13. Research/architecture implications

The most promising unifying move is to make **causal events the membrane between cognition, persistence and authority**:

- fast organs transform active state in one semantic runtime;
- every material transition has an episode identity;
- durable mutation is append-only/single-writer;
- projections feed memory and observability;
- privileged effects pass an external capability check;
- outcome and truthful reentry become first-class events that can actually affect future competition/scheduling;
- the same trace supports debugging, GWT lesion experiments, recovery and Android lifecycle restart.

This would collapse several currently separate engineering problems — observability, replay, GWT causal validation, memory consistency and recovery — into one shared mechanism instead of solving them independently.

The likely architecture optimum is therefore not maximum component count and not maximum process collapse. It is **maximum semantic cohesion with minimum accidental serialization, while preserving explicit fault and authority boundaries**.

---

## 14. Knowledge compilation from this run

Candidate micro-packets created from this run cover:

- semantic-runtime ≠ single-process distinction;
- synchronous GlobalWorkspace contradiction and slow-subscriber falsifier;
- single-writer causal event path replacing cross-organ direct DB mutation;
- Android thermal/lifecycle-aware multi-rate scheduling.

These remain derived/open research memory, not automatic canonical truth. No existing CURRENT claim was silently overwritten and no live claim was promoted from synthetic evidence.

---

## 15. Unresolved questions

- What are the actual p50/p95/p99 costs of current Core→Router, memory fan-out and cross-DB writes on the FRANK target machine?
- Which current GlobalWorkspace subscribers perform blocking I/O or model work and therefore violate a hot-lane budget?
- Does Qwen3.5-4B require multimodal capability in the always-resident baseline, or can vision be loaded/delegated on demand to reduce resident memory?
- Which durable databases are truly independent authoritative stores versus historical artifacts that can become rebuildable projections?
- On the intended Android devices, which backend wins on **sustained useful work per joule under thermal constraints**, not peak tokens/s?
- Can the same CC-RC1.1 episode contract be used directly as the runtime event envelope, eliminating another translation layer?

## Final assessment

**Recommended direction:** proceed with selective module collapse around a single FRANK Semantic Runtime, but explicitly strengthen three membranes: inference resource isolation, privileged capability authority, and single-writer durable state. Start with the GWS slow-subscriber lesion and baseline causal/latency trace before deeper refactoring.
