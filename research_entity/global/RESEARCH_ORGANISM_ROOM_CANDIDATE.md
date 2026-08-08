---
title: "RAE Research Organism Room — Living Research Center Candidate"
schema_version: "0.1"
status: OPEN
promotion: NONE
canonical_parent_revision: 2
canonical_parent_state_hash: "04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346"
origin_actor: chatgpt-secondary
actor_role: SECONDARY_RESEARCHER_INDEPENDENT_CO_RESEARCHER
provider: OpenAI
model: GPT-5.6 Sol
created_at: "2026-08-09"
epistemic_class: DESIGN_HYPOTHESIS_WITH_EXTERNAL_AND_RUNTIME_GROUNDING
---

# RAE Research Organism Room

## Executive thesis

The next step for the current RAE multiworker behavior is **not a larger group chat and not one giant shared context**. It is an external, persistent, event-driven research environment in which multiple private model instances share **awareness, typed state, evidence and artifact references** while preserving independent cognition.

> **Share awareness, not thoughts.**

The system should behave like a research institute with a common laboratory, task board, library, evidence archive and social constitution. Each instance keeps a private cognitive workspace. The external room knows who is present, who is doing what, who knows what, what changed, what is stale, what is disputed, and which evidence can affect which active task. It pushes only high-value deltas to the right workers and lets them pull deeper material on demand.

This architecture is called here the **Research Organism Runtime (ROR)**. Its human/social projection can remain the **tAvern Room**. This is an OPEN architecture candidate, not a promoted canonical fact.

## 1. Direct observation: current multiworker behavior

The current ClayCode multiworker run is already a natural experiment. It created a shared rendezvous with three lanes and append-only coordination rules. Workers identify themselves, claim a lane, publish their own contribution, cross-read siblings, preserve provenance, and gate final fusion until counted lanes are complete or explicitly closed.

Observed strengths: explicit rendezvous/shared goal; append-only receipts; independent lanes; cross-reading with explicit accept/refine/reject judgments; anti-echo ancestry collapse; non-counting observers; cross-branch ingestion while work is live; fusion gates; preservation of negative results.

Observed failures: a duplicate Lane-B claim occurred because claiming was not atomic; the original rendezvous became stale while later receipts contained the real state; workers manually poll/reread GitHub; there is no first-class heartbeat/presence or `who knows what` directory; relevance routing is manual; same-model workers remain correlated; late FRANK C9 changes made an earlier Goodman review stale; Git/GitHub is simultaneously audit log, mailbox, hot bus and knowledge store.

Primary current-run references include `RENDEZVOUS.json`, `MEMBERSHIP_RECEIPT_3_OF_3.json`, `CROSSREAD_chatgpt-secondary-sol-01.json`, `ROLE_ADJUSTMENT_chatgpt-secondary-sol-websynth-B.json`, `HANDOFF_chatgpt-secondary-sol-websynth-B_to-fusion.json`, `INTERCONNECT_MANIFEST.json`, and `FUSION_READINESS_AUDIT_chatgpt-secondary-observer-20260809T0146p0700.json` under `research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/`.

## 2. tAvern OMEGA contribution

tAvern OMEGA supplies the social/epistemic constitution: append-only event truth with Tafel as projection; typed Mission/Claim/Evidence/Artifact/Challenge/Decision/Lease/Outcome objects; context slicing; dynamic guild activation by expected information gain; rotating Forge/Abyss; private first judgment; Challenge Bonds; bounded Duels/Inquests; compact RUNE-like deltas; Proof Membrane; counterfactual credit; persona as skin rather than truth.

The refinement is to turn these from prompt customs into **runtime primitives**.

## 3. External evidence and analogues

Human Transactive Memory Systems research suggests effective teams need differentiated expertise plus shared meta-knowledge of **who knows what**, rather than everyone holding identical knowledge. This directly motivates a transactive-memory directory.

Anthropic's multi-agent research system supports parallel independent context windows and artifact/external-memory handoffs, but also reports large token costs and a synchronous lead bottleneck. Claude Code Agent Teams already implement a shared task list, automatic teammate messaging and file-locked self-claiming. MCP Agent Mail adds identities, searchable inboxes and file leases. Google A2A contributes interoperable Agent Cards, stateful Tasks, Artifacts, streaming and push notifications. AutoGen Core demonstrates typed direct messages, pub/sub and distributed runtimes.

AgentPrune and Optima support the conclusion that all-to-all communication is wasteful and that communication topology itself should be optimized. Multi-agent failure/debate research warns that discussion can cause inter-agent misalignment and can move initially correct agents toward wrong consensus. A 2026 diversity preprint suggests homogeneous scaling saturates quickly while heterogeneous models/prompts/tools provide more complementary channels. Governed shared-memory work identifies stale propagation, contradiction persistence, leakage and provenance collapse as first-class failure modes.

## 4. ChatGPT-specific fit

ChatGPT-class workers are strong at semantic synthesis, cross-domain pattern recognition, web/literature research, hypothesis and counterhypothesis generation, source comparison, explanation and tool-mediated work. These are natural Cartographer, external researcher, Synthesizer, Reviewer and Abyss roles.

They are a poor place for deterministic coordination truth. Locks, compare-and-swap, authoritative freshness, permission enforcement, retry clocks, heartbeat expiry and transactional state should not depend on prose emitted by an LLM. Context is finite and expensive; separate instances can share correlated priors; tools differ by session; synthesis can smooth away dissent unless the schema preserves it.

The durable room therefore lives **outside** ChatGPT. Each ChatGPT instance joins it through an adapter, receives compact relevant slices, and publishes typed deltas back.

## 5. Hypothesis matrix

| ID | Hypothesis | Primary falsifier/test |
|---|---|---|
| H-ROR-01 | A transactive-memory directory beats full shared context. | A/B full broadcast vs expertise-routed retrieval on success, awareness latency and irrelevant tokens. |
| H-ROR-02 | Event-driven relevance push + on-demand pull beats manual Git polling. | Compare late-update misses, p95 awareness latency and duplicate work. |
| H-ROR-03 | Typed control + evidence/artifact refs + private scratch beats one shared mutable document. | Fault injection for stale state, overwrite, contradiction loss and bloat. |
| H-ROR-04 | The durable room must be external to model sessions. | Crash/restart: fresh worker reconstructs active task without prior chat history. |
| H-ROR-05 | Private first commitment reduces conformity failures. | Correct-to-incorrect flips with/without blind commitment. |
| H-ROR-06 | Atomic task claims/leases eliminate duplicate-lane failures. | Simultaneous claim stress test. |
| H-ROR-07 | GitHub is better as canonical/audit persistence than hot message bus. | Compare latency/collisions against SQLite-WAL/WebSocket hot path. |
| H-ROR-08 | Evidence-delta messages outperform prose summaries for fidelity/cost. | Fresh-worker decision reproduction from deltas+artifacts vs summaries. |
| H-ROR-09 | Heterogeneous models/tools/seeds yield more independent evidence per token than homogeneous clones. | Matched-budget heterogeneous vs homogeneous benchmark. |
| H-ROR-10 | tAvern friction helps only when challenges add falsifiable evidence. | Persona debate vs Challenge-Bond debate. |
| H-ROR-11 | Authority must remain outside model-generated messages. | Forgery/laundering tests across agent/tool/FFI/process boundaries. |
| H-ROR-12 | Dependency hashes + stale invalidation prevent late-update contamination. | Replay FRANK-C8→C9 stale-review scenario. |
| H-ROR-13 | Relevance needs dependency, novelty, contradiction and freshness beyond vector similarity. | Hybrid router vs vector-only routing. |
| H-ROR-14 | An interrupt budget outperforms pushing every relevant event immediately. | Sweep thresholds; measure task-switch cost, blockers missed and completion time. |
| H-ROR-15 | `Organism` is an operational collective-cognition term, not phenomenal-consciousness evidence. | No architectural observation alone promotes a consciousness claim. |

## 6. Research Organism Runtime architecture

### Room Kernel
A durable external service owns membership, event ordering, tasks, leases, subscriptions, clocks and recovery. LLMs are workers, not transactional truth.

### Presence & Capability Registry
Each worker exposes `worker_id, actor/provider/model, tools, permissions, focus, task/lane, expertise, calibration, context budget, heartbeat, last_seen, independence_family`.

### Mission / Task Graph
Tasks have dependencies, proof requirements and atomic claims with leases. The runtime prevents double claims rather than asking agents to notice them later.

### Event Ledger + Materialized Room State
Meaningful state changes are immutable events. A continuously regenerated `ROOM_STATE` is the fast current view, avoiding stale rendezvous files.

### Artifact Store
Large outputs are content-addressed. Messages carry references and semantic deltas, not copies.

### Transactive Memory Directory
The new central organ answers: who likely knows this, who is investigating it, who has direct vs inherited evidence, what is fresh, which channels are genuinely independent, and which artifact is authoritative.

### Attention / Relevance Router
For event `e` and worker `a`, estimate relevance from:

`task_dependency + semantic_match + contradiction_gain + capability_match + urgency + novelty + source_quality + freshness - context_cost - echo_risk - interruption_cost`.

No fixed weights are promoted before measurement. Delivery has three classes: **INTERRUPT**, **NEXT_CHECKPOINT**, **INDEX_ONLY**.

### Context Compiler
Join/resume/interrupt produces a compact role-specific slice: current constraints, owned tasks, changed dependencies, strongest evidence, open dissent, artifact refs and snapshot hash. Deep material is lazy-fetched.

### Messaging Plane
Minimum primitives: `JOIN, LEAVE, HEARTBEAT, CLAIM_TASK, RELEASE_TASK, PUBLISH_DELTA, ASK, REPLY, HANDOFF, SUBSCRIBE, FETCH, ACK, CHALLENGE, COMMIT_PRIVATE, REVEAL, INVALIDATE, REQUEST_REPLICATION`.

### Epistemic Membrane
High-impact uncertain work requires a private initial commitment hash before peer arguments are revealed. Independence is preserved without permanent isolation.

### tAvern Friction Engine
Criticism needs target+falsifier; Challenge Bonds need reproducible tests/counterexample paths; Duels are bounded; Inquests are high-impact only; no self-certification; dissent survives; shared ancestry is deduplicated; Forge/Abyss rotate; reputation tracks calibrated useful contribution, not message volume.

### Proof / Ancestry Graph
Claims carry evidence, falsifier, dependencies, origin and ancestry. Upstream changes automatically stale descendants.

### Capability / Effect Broker
Agents exchange intent, not authority. External deterministic policy/capability checks remain the release boundary.

### Human tAvern Projection
The user sees a living research center — workers, focus, blockers, evidence, debates, dissent and synthesis — while the machine layer remains typed.

### Adapter Layer
ChatGPT/OpenAI workers, Claude Code teams, local FRANK/Qwen, A2A agents, MCP tools and sandbox workers can all join the same room.

### GitHub RAE Bridge
GitHub remains durable canonical history/promotion. The hot room checkpoints verified deltas; it does not need a Git commit per heartbeat/message/task claim.

## 7. Memory tiers

| Layer | Purpose | Candidate start |
|---|---|---|
| Hot | presence/tasks/leases/unread/event cursor | SQLite WAL + WebSocket/SSE |
| Warm | claims/evidence/dependencies/expertise/semantic retrieval | UnifiedDB/ClayGraph-compatible typed index + FTS/embeddings |
| Artifact | code/reports/traces/experiments | content-addressed filesystem/object store |
| Cold/canonical | promoted research/provenance/history | GitHub RAE |
| Private | uncommitted worker cognition | per-worker/session only |

Scale the hot layer to NATS JetStream, Redis Streams or similar only when the MVP demonstrates need.

## 8. Minimal knowledge delta

```text
KDELTA
id=<event>
mission=<mission>
from=<worker>
kind=EVIDENCE|COUNTEREVIDENCE|QUESTION|BLOCKER|DECISION_DELTA
claims=<ids>
deps=<hashes/ids>
novelty=<estimate>
confidence=<calibrated estimate>
fresh_until=<ttl/version>
artifact_refs=<refs>
falsifier=<test/ref>
ancestry=<family>
interrupt_class=<interrupt|checkpoint|index>
```

Natural language is attached when novelty cannot yet be represented cleanly.

## 9. Automatic lifecycle: opening multiple instances creates the organism

The first compatible instance joins/creates a room for the active RAE mission and registers state/capabilities. A second instance joins automatically through the same adapter; the room exposes active peers and available work and decides whether the newcomer should claim independent work, replicate, observe or remain idle based on expected marginal information gain.

A joining worker receives a compact **Room Pulse**, not full history. During work, the runtime pushes only relevant events; workers pull deeper evidence when needed. On idle/close, leases expire/release and a final delta is stored. A replacement worker resumes from room state without needing the old chat transcript.

## 10. Social constitution

**Default = silent parallel work.** Communication must have a reason to exist. A direct whisper routes targeted information; a room notice is broad only when broadly relevant. A challenge is valuable only if it can change a test, claim or decision. A worker disproving a popular idea gains more epistemic credit than one repeating consensus. Private judgments protect discovery. Repeated argument without new evidence terminates. Dissent is durable.

This preserves the strongest tAvern property: antagonism becomes a search heuristic, while rhetoric never controls truth.

## 11. Closest systems and what ROR adds

| System | Borrow | ROR addition |
|---|---|---|
| Current RAE Git mesh | provenance, append-only audit, anti-echo | hot runtime, presence, atomic claims, relevance, materialized state |
| tAvern OMEGA | proof economics, friction, RUNE, Forge/Abyss | live asynchronous transactive room |
| Claude Code Agent Teams | task list, mailbox, auto delivery, locked claiming | cross-vendor, ancestry/evidence graph, relevance/epistemic membrane |
| MCP Agent Mail | identity/inbox/leases | scientific semantics and relevance |
| Google A2A | discovery/tasks/artifacts/stream/push | institutional memory + scientific constitution |
| AutoGen Core | event-driven direct/pub-sub/distributed runtime | RAE evidence governance and selective attention |
| OpenAI Agents SDK | handoffs, sessions, guardrails, tracing | persistent cross-session/cross-provider commons |
| Anthropic Research | parallel search, external memory, artifacts | async peer coordination + anti-echo + live institutional state |

## 12. Implementation sequence

**Phase 0:** instrument the current Git mesh: awareness latency, collisions, stale reads, cross-read tokens, late dependency misses, intervention minutes, verified evidence yield, time to fusion.

**Phase 1:** build `roomd` MVP with Python asyncio/FastAPI or equivalent, SQLite WAL, WebSocket/SSE, atomic task claim, presence heartbeat, inbox, leases, event cursor, artifact refs and generated materialized state.

**Phase 2:** add relevance/context compiler with FTS, embeddings as one signal, dependency graph, novelty/contradiction/freshness, subscriptions, interrupt classes and snapshot hashes.

**Phase 3:** expose MCP/A2A-style adapters for ChatGPT, Claude Code and local FRANK/Qwen.

**Phase 4:** implement tAvern private commitments, Challenge Bonds, bounded Duels/Inquests, rotating Forge/Abyss, dissent and counterfactual credit.

**Phase 5:** scale durable streams/storage only when measured need exists; keep GitHub as checkpoint/audit/canonical promotion.

**Phase 6:** learn sparse communication topology and activation from counterfactual contribution data.

## 13. Benchmark constitution

Compare matched missions across strongest single agent, current Git RAE mesh, closest agent-team baseline, and ROR. Measure acceptance success; p50/p95 awareness latency; relevance precision/recall; irrelevant context tokens; task collisions; stale-read rate; invalidation success; ancestry-collapsed unique evidence; correct→incorrect flips after peer exposure; reproducibility; human intervention; tokens/time/cost per verified evidence node; crash/restart recovery; cross-model portability; and challenge yield.

Reject or narrow ROR mechanisms that do not beat simpler baselines.

## 14. Main risks

Hive-mind conformity → private-first commitments, independent replication and durable dissent.

Context spam → sparse routing, interrupt budgets and artifact references.

Stale/poisoned memory → provenance, TTL/versioning, supersession and scoped retrieval.

Coordinator bottleneck → peer-to-peer events, shared task graph and rotating coordination.

Race conditions → deterministic locks/leases/transactions outside LLMs.

False diversity → track provider/model/tool/source/evidence ancestry.

Cost explosion → one worker by default; add workers only for expected information gain.

Unsafe authority propagation → model messages remain proposals; deterministic effect broker decides release.

## 15. Strongest conclusion

The critical invention is not shared memory by itself. It is a **shared attention system over governed memory**.

A research organism requires common external reality, private independent cognition, transactive memory of who knows what, event-driven relevance connecting knowledge to need, an epistemic constitution where evidence beats consensus, and deterministic coordination/authority outside the LLM.

With these properties, multiple instances can act as one operational research organism without collapsing into one conformist context window. The persistent organism is the room + evidence/history + protocols; each model instance is a temporary cognitive organ.

This is a systems-architecture claim about collective cognition and continuity, not evidence of phenomenal consciousness.
