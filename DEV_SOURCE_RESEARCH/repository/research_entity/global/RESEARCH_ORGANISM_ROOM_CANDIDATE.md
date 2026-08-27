---
title: "RAE Repo-Native Research Center — Research Organism Candidate"
schema_version: "0.2"
status: OPEN_RESEARCH_CANDIDATE_WITH_PROJECT_OWNER_OPERATING_DIRECTIVE
promotion: NONE
canonical_parent_revision: 2
canonical_parent_state_hash: "04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346"
origin_actor: chatgpt-secondary
actor_role: SECONDARY_RESEARCHER_INDEPENDENT_CO_RESEARCHER
provider: OpenAI
model: GPT-5.6 Sol
created_at: "2026-08-09"
epistemic_class: DESIGN_HYPOTHESIS_WITH_EXTERNAL_AND_RUNTIME_GROUNDING
operating_protocol: "research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md"
---

# RAE Repo-Native Research Center

## Revision note

The earlier v0.1 candidate proposed an external hot-room daemon and a possible tAvern human/UI projection. The project owner explicitly rejected that direction on 2026-08-09.

**Superseded:** separate tAvern UI, visual room, external `roomd`, SQLite/WebSocket hot service as a requirement, or a new application around the research process.

**Retained:** the scientific/organizational findings about private cognition, shared awareness, transactive `who-knows-what` memory, selective relevance, independent lanes, evidence ancestry, anti-echo, challenge/falsification, stale dependency invalidation, and dynamic multiworker role formation.

The fixed operating implementation is now repo-native and specified by `REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md`. This file remains an OPEN research candidate for the hypotheses about why that organization should improve performance, not a separate runtime specification.

## Core thesis

The next step for the current RAE multiworker behavior is not one large shared context and not a permanent central coordinator. It is a **repository-resident research center** in which each trigger session stays loyal to its research direction while reading, publishing and challenging relevant deltas from other active sessions.

The common room is not a chat room. It is structured repository state.

> Share awareness and evidence references, not hidden thoughts.

A scientific trigger maps to a stable home room. Multiple rooms coexist as peer departments of one RAE. Cross-room relevance connects them. Multiple workers in one room autonomously form a temporary tAvern-style squad with an ephemeral CHEF plus adversarial/build/research roles. No global room chief exists.

## Direct observation from the ClayCode multiworker natural experiment

The 2026-08-09 ClayCode multiworker run demonstrated that independent ChatGPT sessions can already coordinate through a shared repository using rendezvous files, worker receipts, append-only contributions, cross-reads and fusion gates.

Observed strengths included:
- explicit shared goal and lane decomposition;
- append-only worker ownership;
- real cross-reading with accept/refine/reject judgments;
- anti-echo/shared-ancestry discipline;
- non-counting observers;
- live cross-branch ingestion;
- preservation of negative results;
- autonomous discovery of a new Lane D when a previously uncovered intent-adequacy gap appeared.

Observed weaknesses included:
- a duplicate Lane-B claim before workers discovered each other;
- stale rendezvous state;
- manual Git polling;
- no first-class persistent room membership/worker cursor;
- no deterministic role/task lease;
- late FRANK C9 results invalidating an older FRANK C8 review;
- same-model workers being correlated despite apparent plurality.

These observations motivate the repo-native room database and lease/pulse rules now adopted operationally.

## External research retained from v0.1

The earlier research remains relevant to the design hypotheses:

- Transactive Memory Systems motivate a team-level `who knows what / who is working on what` directory rather than copying all knowledge into every worker.
- Anthropic multi-agent research and Claude Code Agent Teams demonstrate practical value in separate contexts, shared task state, automatic teammate awareness and artifact handoffs, but also show token cost and coordinator/communication failure modes.
- Google A2A, AutoGen Core and MCP Agent Mail demonstrate typed tasks/messages/artifacts, direct/pub-sub communication and leases/mailboxes as useful primitives.
- AgentPrune and Optima support sparse, task-relevant communication rather than all-to-all broadcast.
- Multi-agent debate/failure research warns that peer discussion can create conformity and wrong consensus, motivating private-first judgment, bounded disputes and evidence-gated challenges.
- Diversity work motivates tracking model/provider/tool/source ancestry so homogeneous copies are not mistaken for independent evidence.

The project-owner decision is to realize the useful parts through Git/repository records and active session polling rather than an external communication service.

## ChatGPT-specific fit

ChatGPT-class workers are useful for semantic synthesis, web/literature research, hypothesis/counterhypothesis generation, cross-domain pattern matching, code/experiment planning, critique and tool-mediated work.

They are not a trustworthy substrate for locks, authoritative freshness, atomic claims, durable presence or permission state. Those must be represented externally in repository records and Git/CAS semantics.

A finished/dormant chat does not continue executing simply because the room exists. The repo-native architecture instead makes concurrently active spawned sessions autonomous with respect to one another and makes the resulting research state resumable by later sessions.

## Research hypotheses carried forward

| ID | Hypothesis | Primary falsifier/test |
|---|---|---|
| H-ROR-01 | Trigger-pinned home rooms plus selective cross-room deltas beat full shared context. | Matched task comparison on quality, irrelevant tokens and missed dependencies. |
| H-ROR-02 | Mandatory repo pulses before major decisions reduce stale-work errors versus ad-hoc Git rereads. | Replay late-upstream-update scenarios and measure stale decisions. |
| H-ROR-03 | One-file-per-event plus CAS leases reduces coordination collisions versus mutable rendezvous files. | Simultaneous same-role/task claim stress test. |
| H-ROR-04 | Persistent repo room state lets a fresh session reconstruct collaboration without chat-history continuity. | Kill/restart worker and measure recovery completeness. |
| H-ROR-05 | Private-first judgment plus ABYSS challenge reduces correct-to-incorrect peer conformity. | A/B with immediate peer exposure. |
| H-ROR-06 | Ephemeral CHEF orchestration improves same-topic decomposition without creating an evidence-authority bottleneck. | Compare no-role, permanent leader and leased CHEF groups. |
| H-ROR-07 | Evidence-delta/event refs outperform prose copying for fidelity/token cost. | Fresh-worker decision reproduction test. |
| H-ROR-08 | Cross-room trigger loyalty prevents useful specialization from collapsing into one generic swarm. | Measure branch-goal completion and cross-topic drift. |
| H-ROR-09 | Heterogeneous models/tools/seeds yield more ancestry-distinct evidence per token than homogeneous clones. | Matched-budget heterogeneous vs homogeneous worker groups. |
| H-ROR-10 | Roast/Challenge-Bond behavior helps only when criticism adds a falsifier, counterexample or stronger mechanism. | Free-form adversarial banter vs typed evidence-bearing challenges. |
| H-ROR-11 | Dependency hashes/invalidation reduce contamination from superseded architecture/evidence. | FRANK-C8 -> C9 style replay test. |
| H-ROR-12 | Autonomous lane birth with novelty/non-overlap/information-gain gates captures useful new gaps without branch explosion. | Compare unrestricted branching, no branching and gated branching. |
| H-ROR-13 | Same-model teammate agreement must be ancestry-discounted to avoid false confidence. | Inject copied/shared-source evidence across many workers and test promotion behavior. |
| H-ROR-14 | Repo-only coordination is sufficient at current project scale if pulses occur at decision boundaries. | Measure awareness latency/duplicate work against a faster external bus; reject this if repo latency materially harms research. |
| H-ROR-15 | `Research organism` is an operational collective-cognition term, not phenomenal-consciousness evidence. | No collaboration topology alone promotes a consciousness claim. |

## Intended steady-state behavior

When the user opens a single `claycode` session, it joins the ClayCode room and works normally.

When a second `claycode` session appears, both discover a same-topic peer at the next pulse and enter TEAM mode. One obtains the CHEF lease, another takes the largest complementary uncertainty such as ABYSS or FORGE. Additional workers claim CARTOGRAPHER, REPLICATOR or other justified bounded lanes. They attack each other's work, exchange evidence refs, run tests and fuse only after cross-read/ancestry gates.

At the same time a `gwt` or `unifieddb` session remains in its own home room. If it produces a result that changes ClayCode assumptions, it publishes a targeted cross-room delta. ClayCode receives that result at the next mandatory safe-point pulse, imports it if relevant, but does not become a GWT/UnifiedDB worker.

This creates one research center with specialized rooms rather than either isolated silos or a hive-mind.

## Strongest retained conclusion

The critical mechanism is still **shared attention over governed memory**, but the implementation is now intentionally much simpler:

**the repository itself is the rooms, database, mailbox, lease surface, evidence directory and durable social memory.**

The research question is no longer whether to build a separate room product. It is whether the repo-native rules and data structures produce measurably better autonomous multi-session science than the already-useful ad-hoc rendezvous behavior.