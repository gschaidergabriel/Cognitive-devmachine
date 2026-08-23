# XENO COMPUTATIONAL UNIT — DEEP RESEARCH FUSION

Date: 2026-08-23
Status: **CURRENT RESEARCH TARGET / HYPOTHESIS-BOUND**
Operational bootstrap: **Xeno** (renamed from Mini Entity)
Destination: **EntityOS + HCU/XCU cognitive computer**

## Executive summary

Xeno is to evolve from the current Mini Entity implementation into a **multi-mode heterogeneous computational appliance**. The same substrate should be able to run a cheap 10-cell grid, request-scoped pure cognition simulation, bounded world-model tests, or—only when evidence justifies the cost—a nested simulation containing a world model, virtual computer, simulated AI and action translation. The long-term architecture resembles a computer more than a swarm: typed I/O, RAM-like state tiers, a deterministic CPU-like control plane, GPU-like shared-weight/vector compute, a high-bandwidth typed interconnect, scratch/simulation memory and an external EffectGate.

The central engineering principle is **logical multiplicity over shared physical compute**. Ten, one hundred or six hundred logical modules do not mean ten, one hundred or six hundred full model copies. They mean resumable contexts/functions/branches scheduled over a smaller number of resident model workers with shared weights, batching, paging and optional offload. Exact capacity is an empirical property of model architecture, quantization, KV/cache size, context length, scheduler and hardware.

The central epistemic principle is **simulation != truth**. World-model states, cognition branches, J-Space measurements, branch agreement and internal confidence remain candidate/projection data until compared with canonical evidence and observed outcomes. EffectGate remains the only path from candidate action to real/state-changing effect.

---

## 1. Research question

Can the current Xeno bootstrap be incrementally re-factored into one shared computational substrate that supports several qualitatively different workloads while becoming *simpler at higher abstraction layers* rather than accumulating separate agent frameworks?

Target modes:

```text
                 XENO COMMON SUBSTRATE
                          |
       +------------------+------------------+
       |                  |                  |
   GRID10             COGSIM10           WM_TEST
       |                  |                  |
       +------------------+------------------+
                          |
                    NESTED_SIM
                          |
                       SCALEOUT
```

All modes share the same:

- Entry Fabric;
- causal/generation/provenance packet semantics;
- canonical state substrate;
- scheduler and logical-cell abstraction;
- model-worker pool;
- workspace/Hyperposition interfaces;
- calibration/outcome learning;
- EffectGate boundary.

---

## 2. External evidence fused into the architecture

### 2.1 Heterogeneous system co-design — NVIDIA DGX / Grace Hopper / Rubin

NVIDIA DGX architectures show a recurring systems principle useful as an analogy for Xeno: CPUs, GPUs, memory and high-bandwidth interconnect are co-designed as one appliance rather than exposed as unrelated services. Grace Hopper uses coherent CPU/GPU memory over NVLink-C2C; DGX GH200 extends this into a large shared-memory fabric; newer Rubin systems similarly emphasize multiple specialized chips and high-bandwidth interconnect as one system.

Relevant sources:

- https://developer.nvidia.com/blog/nvidia-grace-hopper-superchip-architecture-in-depth/
- https://developer.nvidia.com/blog/announcing-nvidia-dgx-gh200-first-100-terabyte-gpu-memory-system/
- https://blogs.nvidia.com/blog/dgx-superpod-rubin/
- https://www.nvidia.com/en-eu/data-center/nvlink-fusion/

**Fusion implication:** Xeno should not emulate DGX silicon. It should copy the *architectural law*: heterogeneous functions + coherent memory semantics + fast interconnect + one scheduler/control surface.

### 2.2 Logical contexts over shared physical inference — vLLM / SGLang

Modern serving systems already demonstrate that model weights need not be duplicated per request. vLLM uses PagedAttention, continuous batching, prefix caching and distributed parallelism; SGLang adds RadixAttention, prefill/decode disaggregation, multi-LoRA batching and extensive scheduler/runtime techniques.

Sources:

- https://github.com/vllm-project/vllm
- https://github.com/sgl-project/sglang

**Fusion implication:** Xeno logical cells should be contexts/leases over shared resident workers. `logical_module_count` and `physical_decode_concurrency` must be separate metrics.

### 2.3 Dynamic compute allocation — Mixture-of-Depths

Mixture-of-Depths demonstrates that useful compute can be dynamically allocated while total compute remains bounded and predictable.

Source:

- https://arxiv.org/abs/2404.02258

**Fusion implication:** Xeno should allocate cells/functions/horizons based on request difficulty and expected information gain rather than activate the same topology every turn.

### 2.4 Self-regulated simulation/planning

SR²AM argues that agents benefit from separating reactive execution, simulative planning and a self-regulation mechanism that decides *when and how deeply* to plan. It reports large reasoning-token savings relative to heavier agentic baselines while retaining competitive task performance.

Source:

- https://arxiv.org/abs/2605.22138

**Fusion implication:** Xeno needs a Mode/Depth Controller. Full nested simulation is a high-cost tool, not the default cognitive state.

### 2.5 World-model planning can help, but unreliable foresight can hurt

SimuRA reports gains from world-model-based planning on difficult browsing tasks. Newer work such as WorldEvolver explicitly notes that unreliable foresight can be ignored, misused or degrade planning, and therefore introduces selective foresight and learning from prediction/observation mismatches.

Sources:

- https://arxiv.org/abs/2507.23773
- https://arxiv.org/abs/2606.30639
- https://arxiv.org/abs/2606.27483

**Fusion implication:** Xeno must keep `WM_TEST` and `NESTED_SIM` optional, calibrated and outcome-bound. A world model does not become canonical reality.

### 2.6 Generated worlds + generalist agents — DeepMind Genie / SIMA

DeepMind has demonstrated a useful separation between a world-generating model (Genie) and an agent (SIMA) acting within generated environments. SIMA 2 has also been evaluated inside Genie-generated worlds. This is close to Xeno's eventual experimental `world -> computer/agent -> action` nesting, though Xeno's goal is not a visual world generator.

Sources:

- https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/
- https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/

**Fusion implication:** simulation and agent policy should remain separable components with explicit interfaces so either can be ablated or replaced.

### 2.7 Multi-agent/multi-branch scaling is conditional, not monotonic

A systematic 2025 study of Multi-Agent Debate finds benefits are conditional on task, model capability and safety setting; more debate is not universally better than self-agent test-time scaling.

Source:

- https://arxiv.org/abs/2505.22960

**Fusion implication:** Xeno should optimize effective branch diversity and discriminator quality, not module count or vote count.

### 2.8 Global workspace and J-Space

Shared Global Workspace work shows that a capacity-limited shared communication channel can encourage specialization and synchronization among modules. Anthropic's July 2026 J-Space work provides model-specific causal evidence for a small internal workspace-like set of patterns in Claude, including higher-order reasoning degradation under J-Space ablation.

Sources:

- https://arxiv.org/abs/2103.01197
- https://www.anthropic.com/research/global-workspace

**Fusion implication:** Xeno Global J-Space should be an instrumented coordination layer. A local model's J-Space must be demonstrated per checkpoint; it cannot be assumed from Claude.

---

## 3. Hypotheses and counterhypotheses

### H1 — One multi-mode substrate will beat multiple separate agent architectures in maintainability and migration cost

**Prediction:** shared Entry/State/Scheduler/Cell/Effect primitives can support GRID10, COGSIM10, WM_TEST and NESTED_SIM without mode-specific authority stacks.

**Counterhypothesis C1:** complexity merely moves into scheduler/runtime configuration, creating a harder distributed system.

**Discriminator:** count mode-specific code paths, invariant duplication, fault classes and migration patches over successive implementations.

### H2 — Typed Entry Fabric before cognition improves reliability

**Prediction:** binding causal ID, generation, provenance, modality, permissions and budget before model execution reduces stale-state, provenance and accidental-authority errors.

**Counterhypothesis C2:** ingress normalization becomes a latency bottleneck and over-constrains rich data.

**Discriminator:** compare direct/raw ingress vs typed ingress on latency, information loss, stale-generation rejection and reproducibility.

### H3 — Shared weights + logical contexts permit much larger logical cell counts than full model replication

**Prediction:** scheduler/paging/batching allows logical cell population to rise far above resident worker count while preserving bounded memory.

**Counterhypothesis C3:** KV/context state dominates memory or scheduler overhead, so logical scaling collapses early.

**Discriminator:** exact memory/latency sweeps at 10/32/64/128/256/... logical contexts with fixed model and workload.

### H4 — Dynamic function allocation beats fixed roles at equal compute on heterogeneous tasks

**Prediction:** a router/configurator allocating retrieval, hypothesis, critic, planning, simulation and calibration cells per request improves score/latency Pareto front.

**Counterhypothesis C4:** routing errors and coordination overhead erase gains.

**Discriminator:** compute-matched static 10-role grid vs dynamic 10-slot fabric.

### H5 — Pure cognition simulation is the best default high-reasoning mode

**Prediction:** request-scoped COGSIM10 captures most benefits of branching/falsification without the cost/error surface of a world model.

**Counterhypothesis C5:** without forward environment prediction, simulated cognition cannot evaluate actions well enough.

**Discriminator:** COGSIM10 vs WM_TEST vs direct baseline on tasks grouped by environmental dynamics and horizon.

### H6 — World models are beneficial only behind selective invocation/calibration

**Prediction:** WM_TEST improves long-horizon planning where learned transition knowledge is predictive, but harms performance when uncertainty is high.

**Counterhypothesis C6:** world-model rollout is broadly superior once enough compute is available.

**Discriminator:** task-by-task delta as a function of measured world-model calibration, with forced-world-model vs selectively-routed conditions.

### H7 — Nested simulation helps only on a narrow high-value frontier

**Prediction:** `world model -> virtual computer -> simulated AI -> action candidate` yields gains on complex interaction/planning tasks but is dominated by cheaper modes on ordinary requests.

**Counterhypothesis C7:** nesting mostly compounds hallucination and latency.

**Discriminator:** matched tasks and outcome-calibrated utility per joule/token/second.

### H8 — Function cells are better abstractions than persistent agent personas

**Prediction:** ephemeral task functions give equal or better capability with lower prompt/persona overhead and less identity/state contamination.

**Counterhypothesis C8:** persistent roles provide useful specialization and memory that ephemeral cells lose.

**Discriminator:** persona-role cells vs function-role cells with identical base weights, memory budget and task set.

### H9 — A bounded shared workspace improves cross-function coordination

**Prediction:** bandwidth-limited workspace broadcast improves tasks requiring multiple specialized transformations.

**Counterhypothesis C9:** direct packet passing or a simple reducer is sufficient; workspace adds bottleneck/correlation.

**Discriminator:** workspace ON/OFF/size sweep plus lesion tests.

### H10 — ~600 logical modules on H100-class hardware may be feasible only as a scheduler-level population, not 600 full concurrent models

**Prediction:** with one/few shared ~0.8B checkpoints and many suspended/short-lived contexts, hundreds of logical branches may be representable, while the number of simultaneously decoding streams remains much smaller.

**Counterhypothesis C10:** KV/cache and scheduling overhead make even logical 600 impractical for useful context lengths.

**Discriminator:** do not extrapolate. Benchmark exact checkpoint, quantization, context lengths, active/suspended ratios and physical concurrency. Scale 10 -> 32 -> 64 -> 128 -> 256 -> 600 only after each previous gate passes.

---

## 4. Formal scaling model

For a shared-weight Xeno worker pool:

```text
M_total = M_weights
        + N_active * M_KV_active
        + N_suspended * M_branch_state
        + M_workspace
        + M_scheduler
        + M_runtime
        + M_headroom
```

where:

- `N_logical = N_active + N_suspended + N_queued`;
- only `N_active` consumes full active decode/KV resources;
- suspended branches should be compacted, paged or offloaded when possible;
- queued branches can often be represented by typed state rather than resident KV.

Therefore:

`600 logical modules != 600 resident model copies != 600 simultaneous decode streams`.

This distinction is mandatory in all Xeno capacity claims.

---

## 5. New Xeno computer architecture

```text
EXTERNAL / INTERNAL NEW DATA
 human | tool | sensor | DB event | timer | intrinsic event
                       |
                       v
+--------------------------------------------------------+
| XENO ENTRY FABRIC                                      |
| normalize + causal_id + generation + provenance       |
| permissions + modality + budget + timestamp            |
+---------------------------+----------------------------+
                            |
                            v
+--------------------------------------------------------+
| XRAM / STATE FABRIC                                    |
| canonical durable state | hot cache | scratch branches|
+---------------------------+----------------------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
+--------------------------+  +--------------------------+
| XPU CONTROL PLANE        |  | XCU ACCELERATOR PLANE    |
| deterministic scheduler  |  | shared model weights     |
| leases / routing / fence |  | vector/J-space kernels   |
| recovery / mode control  |  | batched function cells   |
+-------------+------------+  +------------+-------------+
              |                            |
              +-------------+--------------+
                            |
                            v
+--------------------------------------------------------+
| PACKET / GLOBAL WORKSPACE / HYPERPOSITION FABRIC       |
| typed branches + ancestry + alternatives + evidence    |
+---------------------------+----------------------------+
                            |
                     MODE TOPOLOGY
                            |
      +----------+----------+----------+----------+
      |          |                     |          |
   GRID10    COGSIM10              WM_TEST   NESTED_SIM
      |          |                     |          |
      +----------+----------+----------+----------+
                            |
                            v
              CALIBRATED ACTION CANDIDATE
                            |
                            v
                     EFFECT TRANSLATOR
                            |
                            v
                       EFFECTGATE
                            |
                            v
                         REALITY
```

This is the path by which Xeno becomes a computer: not by pretending software modules are literal silicon, but by stabilizing computer-like architectural responsibilities.

---

## 6. Incremental construction sequence

### Phase X0 — Rename + contracts

- active name Xeno;
- legacy aliases preserved;
- every `go` has Xeno track + XCU/Entry track.

### Phase X1 — Entry Fabric + GRID10

- typed input packet;
- 10 logical function slots;
- shared worker abstraction;
- deterministic scheduler baseline;
- exact traces/receipts.

### Phase X2 — XRAM / XPU / XCU separation

- canonical vs scratch memory tiers;
- control plane distinct from vector/inference plane;
- packet fabric/interconnect metrics;
- suspend/resume branch state.

### Phase X3 — COGSIM10

- request-specific topology compiler;
- hypothesis/counterhypothesis/critic/calibration loops;
- no real effects inside simulation;
- compute-matched baselines.

### Phase X4 — WM_TEST

- bounded transition/world predictor;
- explicit uncertainty;
- prediction-observation calibration;
- selective invocation.

### Phase X5 — NESTED_SIM

- world model contains a virtual computer state;
- simulated AI operates only in the simulation;
- proposed actions translated into candidates;
- hypothesis/counterhypothesis comparison before EffectGate.

### Phase X6 — SCALEOUT

- accelerator-serving backend;
- paged KV/context state;
- continuous batching;
- prefill/decode separation where useful;
- scale gates 32/64/128/256/... logical contexts;
- ~600 logical modules only after empirical admission.

### Phase X7 — EntityOS computer

- Xeno primitives become the minimal EntityOS computer/runtime substrate;
- RAM-like state, CPU-like control, accelerator-like cognition, I/O and effect boundary are explicit and testable;
- high-level capability can grow without multiplying durable authorities or agent identities.

---

## 7. GO work-selection law after fusion

Every `go` selects work using:

```text
GO_SCORE =
    information_gain
  * executable_Xeno_value
  * XCU_or_Entry_progress
  * cross_mode_reuse
  * EntityOS_migration_value
  * falsifiability
  * nonduplication
  * execution_availability
```

A `go` is incomplete if it advances only legacy Xeno behavior and ignores the XCU/Entry path without a recorded reason.

Every material `go` should leave at least one of:

- executable Xeno delta;
- Entry Fabric delta;
- XCU scheduler/memory/interconnect delta;
- mode implementation/benchmark delta;
- hypothesis/falsifier/measurement delta;
- `XCU_NO_CHANGE_WITH_REASON` receipt.

---

## 8. Final fused concept

Xeno is a **programmable cognitive computational unit**, not a permanent collection of agents. The current Mini Entity implementation is its bootstrap body. It begins with a small 10-cell logical grid and a typed entry point, then progressively separates canonical RAM-like state, deterministic processor/control functions, accelerator/vector cognition, internal interconnect and simulation scratch memory. The same primitives can be reconfigured into pure cognition simulation, a bounded test world model or a deeper nested simulation in which a world model contains a virtual computer and simulated AI whose actions remain candidates until hypothesis comparison and EffectGate admission.

Scale comes from shared weights and scheduled logical contexts rather than model duplication. A future H100-class target of hundreds of logical modules—potentially around 600—is treated as a benchmark hypothesis, never as an assumed number of simultaneous models. The architecture must automatically prefer the cheapest sufficient mode; deeper simulation is invoked only when calibrated evidence shows that it improves outcomes.

The end-state is EntityOS as a small cognitive computer whose durable architecture remains compact even while request-specific computational structures become large and complex.
