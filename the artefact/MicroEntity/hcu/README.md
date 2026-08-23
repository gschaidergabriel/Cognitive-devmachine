# Hyperposition Computational Unit (HCU)

Status: owner-directed Mini Entity co-development lane  
Target host profile: KVM 4 — 4 CPU cores, 16 GB RAM, 200 GB disk, 16 TB bandwidth.

## Purpose

HCU turns the bundled ~0.8B cognition class into a **tiled computational fabric**. Many logical modules operate like specialized compute tiles while only a small number of local inference lanes stay hot at once.

The useful analogy to a GPU is the scheduler/fabric, not parameter arithmetic:

```text
                    MiniUnifiedDB
                         |
               canonical typed projection
                         v
+---------------------------------------------------------+
| HCU scheduler / Hyperposition fabric                    |
|                                                         |
|  [M00] [M01] [M02] [M03]   observation / causality      |
|  [M04] [M05] [M06] [M07]   goals / planning / critics   |
|  [M08] [M09] [M10] [M11]   Zero twin / memory / sims    |
|  [M12] [M13] [M14] [M15]   hypotheses / falsifiers      |
|                                                         |
|  many logical tile states                               |
|          | weighted queues + GWT broadcasts             |
|          v                                              |
|   2 recommended hot local ~0.8B inference lanes         |
|   1 shared/mmap weight image where supported            |
+---------------------------------------------------------+
        |                         |
        | candidate packets       | FREE_ONLY research feed
        v                         v
  deterministic admission   Groq/Mistral/NVIDIA/etc.
        |                         |
        +-------------+-----------+
                      v
                MiniUnifiedDB
                      |
                 EffectGate only
```

## Why 16 logical modules but only 2 hot lanes?

On the 4-core/16-GB VPS, RAM can hold several quantized ~0.8B copies, but CPU throughput is the tighter constraint. Replicating weights many times would waste RAM while fighting for four cores.

HCU therefore separates:
- **logical module count** — cheap, persistent typed state and role specialization;
- **hot inference lane count** — expensive active generation;
- **weight replica count** — ideally one read-only shared/mmap image.

The bundled planner currently recommends **16 logical tiles + 2 hot local lanes** for the stated KVM 4 profile. That is a deterministic planning result, not measured token/s runtime evidence.

## Persistent world model / supervisor

The supervisor is a persistent **derived cognitive layer inside Mini Entity**, not a second truth authority.

It maintains:
- causal timeline candidates;
- counterfactual branches;
- uncertainty and confidence calibration;
- dynamic goal candidates;
- long-horizon plan simulations;
- a versioned Zero-twin model;
- improvement hypotheses and falsifiers;
- resource/queue state.

Canonical factual claims still live in MiniUnifiedDB. Simulation branches and model-generated conclusions are typed as candidates until admitted by evidence.

## Dynamic goals

HCU may create `GoalCandidate` records from unresolved contradictions, explicit owner goals, stale/high-uncertainty world-model regions, failed effects/tasks, scheduled obligations and newly ingested evidence.

A module may prioritize and simulate a goal. It may not directly cause real-world effects. Any action crosses the same EffectGate with generation/provenance fencing.

## Long simulation

Long simulations are decomposed into short bounded steps: select a branch, assign logical modules, generate candidate next states, cross-critic/falsifier pass, update confidence, checkpoint typed simulation state, and continue/stop by budget.

## Zero cognition model

`ZeroTwin` is a model of Zero's current operating policy, context, likely decisions and failure modes. It is explicitly not Zero's private hidden state and not evidence of consciousness.

## Hypothesis feedback

The supervisor returns `HypothesisPacket` objects to Zero/EntityOS with a testable claim, counterhypothesis, discriminating test, evidence requirements and expected observations. It is never auto-promoted to truth.

## FREE_ONLY feed

External free LLMs act as research/information organs. They can propose summaries, candidate facts, counterarguments, plans and synthetic training/replay items. Every response is provenance-bound and enters as candidate data. Provider text cannot directly mutate canonical truth or execute effects.

## Scaling

Scale order:
1. increase logical modules;
2. improve scheduling/batching/cache reuse;
3. measure hot-lane throughput;
4. only then increase local replicas;
5. later distribute HCU tiles across additional hosts with generation-fenced message transport.

Multiple VPS nodes still belong to one Mini Entity and one canonical authority boundary.
