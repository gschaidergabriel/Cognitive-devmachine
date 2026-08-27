# 666 Level-0 Run Report — Project Engine v3/v3.2 Historical Lineage

## Run identity
- trigger: `666`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- program stage: `L0_ARCHIVE_ASSIMILATION`
- release gate: `NOT_PASS`
- task: `666-l0-pf-project-engine-v3-history-20260809T1202p0700`

## Routing / peer coordination
The current center already had active/non-overlapping work on the new Drive roots (Needle, Digital Retina, Digital Retina E2E, Titan-memory) and concurrent PF recovery / PF-ce007 history work. Older Drive roots including frank-rettung, frank-rettung-2026-07-31, frank-adapter-sicherung, synteq-umbau, frank-projects, frank-demo, frank-library, frank-werkzeuge and XENO already had closures or denominator work. This worker therefore selected an unclaimed Project-Frankenstein historical Project Engine v3/v3.2 semantic-lineage shard.

A connector capability test also reconfirmed that `fetch_file` rejects directory paths at the frozen head, so this run did not falsely claim a complete frozen-head tree denominator.

## Primary evidence read
Project-Frankenstein commits:
- `91b983a...` — PROJECT.md base-of-truth persistence
- `62a661f...` — sandboxed tool-use agent loop
- `b6d8c17...` — deliberate removal of project sandbox / ambient system access
- `1c5c682...` — context compaction, SSE, persistent tasks, 25-iteration loop; structural-only validation note
- `cfa7062...` — Project Engine v3 autonomous-agent rebuild
- `35bbeac...` — v3.2 notifications, NL policies, A/B, replay, cloning, multi-project

Implementation read at the v3 commit included `services/project_engine.py` sections for world graph/snapshot, policies, dream cycle, tiered autonomous actions, bounded action chaining, outcome scoring, model routing, context compaction, loop detection, skills and crews.

## Verified lineage findings
1. **Persistent project truth precursor.** PROJECT.md was injected into every project chat and could be updated by the model. Reusable idea: human-readable project/recovery packets. Guard: they must remain secondary to canonical provenance/CAS state; free-form model text must not become execution authority.
2. **Fail-closed tool loop precursor.** The first tool-use implementation sandboxed paths to the project directory, bounded iterations, blocked destructive commands, and failed exact edits when the old string was missing/ambiguous. These are reusable Harness semantics.
3. **Ambient-authority negative transition.** A later commit removed the project sandbox and allowed broad filesystem/system access with only a tiny destructive blocklist. This is retained as negative architecture knowledge, not as a restore target. Current Needle should broker typed, scoped capabilities with provenance and rollback.
4. **Compaction was not historically E2E-proven.** The 40K-ish token compaction/task/SSE commit explicitly says insufficient API credits prevented live end-to-end validation. Therefore this is structural evidence, not a proven performance result.
5. **v3 contains concrete precursors of current architecture.** The code has a world entity/relation graph, policy plane, activity/event log, tiered deterministic/free-LLM/Claude routing, bounded action chaining, minimal-context autonomous actions, outcome logs/profile updates and loop detection.
6. **Historical performance numbers remain self-reports.** The v3 commit claims a 39s/0-Claude-token cycle, 331s five-step chain, 4s dream cycle, a dealer-contact example and ~$0.02/day projection. This run did not reproduce them and does not promote them.
7. **Weak success proxies identified.** Some v3/v3.2 success labels depend on presence of tool use or absence of `[ERROR]`/`[TIMEOUT]`. The A/B routine can auto-apply a strategy winner from that proxy. This is a direct false-success/Goodhart risk.
8. **Policy authority needs separation.** Natural-language policy parsing and auto-refinement can write policies from LLM output or tool stats. Current architecture should keep learned policy as a proposal until typed validation, provenance, conflict checks and authority rules pass.
9. **Replay and peer-query are valuable ancestors.** v3.2 session replay/time-travel and cross-project world/memory queries map well to current Harness/Research Center goals. Agent-profile cloning, however, needs selective transfer and contamination/leakage tests.

## Cross-read with concurrent PF recovery worker
The concurrent PF↔Drive recovery report independently reinforces the same lineage rule: old/recovery artifacts must be preserved as provenance nodes and feature-differential evidence, not blindly restored. Its Genesis sandbox finding is compatible with this run's authority-boundary conclusion.

## Current architecture feedback
### Harness
- keep bounded loops, exact failure semantics, loop/stall detection and event/replay traces;
- require task-grounded outcome oracles, not no-error proxies;
- every learned strategy/policy mutation needs rollback and falsifier evidence.

### Needle / tool authority
- preserve `model output != execution authority`;
- use typed scoped capabilities and per-action policy checks;
- treat historical ambient full-system access as a negative-result branch.

### FRANK / ClayGraph / UnifiedDB
- historical world graph + project truth show the value of separating persistent semantic identity from transient action context;
- human-readable packets are useful for recovery/audit but should not replace exact event/provenance state.

### Research Center / Hive
- peer-project query is a historical precursor of current cross-worker knowledge pull;
- profile/knowledge transfer requires provenance, selective scope and contamination tests.

## Candidate discriminating tests
1. Full vs compacted-context replay-equivalence on long tool trajectories.
2. Ambient authority vs Needle-style scoped capabilities under adversarial prompts.
3. No-error proxy vs task-grounded outcome oracle on partial/false-success cases.
4. Proposal-only vs auto-enforced learned policies with conflict injection and rollback.
5. Profile-transfer benchmark measuring positive transfer, contamination and cross-project leakage.

## Durable outputs
- `research_entity/archive_assimilation/receipts/666_20260809T1210p0700_chatgpt_secondary_pf_project_engine_v3_lineage.json`
- `research_entity/rooms/center_events/20260809T1210p0700_666_pf_project_engine_v3_lineage_delta.json`
- this report

## Coverage / gate
This is a bounded semantic-history shard. It earns **0 exact global Level-0 percentage** because the full Project-Frankenstein frozen-head tree and commit-DAG/history denominators are still unresolved. The Drive swarm continues in parallel. `666_RELEASE_GATE` remains `NOT_PASS`; no post-Level-0 stochastic field spawning and no paid training were initiated.
