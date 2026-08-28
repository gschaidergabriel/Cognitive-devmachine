# TRIGGERWORT 5 — Native Subagent Orchestration Forensic Priority

Status: MANDATORY FORENSIC PRIORITY / FEEDS TRIGGERWORT 4
Date: 2026-08-28

## 1. Why this priority exists

Current Frankenstein donor source explicitly references an important host-level execution law from `~/CLAUDE.md`:

```text
nie selbst bauen, immer an einen caveman-Subagenten geben
```

The versioned donor repository does not contain the host `~/CLAUDE.md` itself. Triggerword 5 must therefore reconstruct and pin the actual current native spawn/delegation architecture rather than assuming its semantics.

The goal is to determine exactly how the current installed Claude Code environment turns a Frankenstein/Architekt decision into a spawned native child agent, how that child receives a work package, how it iterates, and how progress/result identity is exposed back to hooks and UnifiedDB.

## 2. Required source/runtime targets

Use the authorized VPS/host execution routes read-only where necessary and inspect, in provenance order:

- current host `~/CLAUDE.md`, especially the referenced PHASE 5 delegation section;
- `~/.claude/star/architekt/` and any current equivalent;
- `~/.claude/commands/architekt.md`, `end.md`, or current command successors;
- current installed Claude Code version/build;
- current native subagent/task facilities exposed by that version;
- project/global Claude settings that affect subagents, hooks, permissions and inheritance;
- Frankenstein `stern.py` PHASE-5 `entityos_arbeitspaket`, `handoff`, `reconcile`, `lastschutz`;
- `architekt_governance.md` and `architekt_tiefensitzung.md`;
- hook payloads for SubagentStart/SubagentStop/Task*/tool events when supported;
- historical commits demonstrating parallel fixer agents, collisions or replacement/resume behavior.

Do not assume tool names or event payloads from general Claude documentation. Pin what the installed runtime actually exposes.

## 3. Privacy / host-config handling

Do **not** commit the full host `~/CLAUDE.md`, full settings files, credentials, secrets, private unrelated instructions or complete host environment dumps.

For architecture evidence, persist only:

- exact host/file identity when safely available;
- hash/digest;
- relevant bounded line/span references;
- minimal redacted excerpt or excerpt hash;
- semantic atom;
- runtime probe receipt.

Secrets and unrelated personal/system-prompt content remain on host.

## 4. Questions that must be answered

Triggerword-5 packets for this priority must answer with evidence:

1. What exact native mechanism spawns a child agent today?
2. Does spawn occur interactively through Claude Code's native agent/task facility, through headless `claude -p`, or through more than one path?
3. Which part is chosen by the main/coordinator model vs deterministic code?
4. How is the workpackage/context passed to the child?
5. Does the child inherit the parent CLAUDE/system/project context, and if so which parts?
6. What stable child identity is exposed (`agent_id`, task ID, parent ID, session ID, tool-use IDs)?
7. Which lifecycle hooks actually fire for child start/stop/task create/task complete/failure?
8. Can a native child spawn its own children? Under what depth/resource/permission behavior?
9. Does a child share the parent's working tree/process cwd or get isolation/worktree semantics?
10. How do simultaneous child writes interact with Git/staging and filesystem ownership?
11. How is child progress visible before final completion?
12. Can a parent send revised instructions to a running child/package?
13. What happens if the child stalls, crashes, exceeds context, is cancelled, or parent session ends?
14. Can a child be resumed/replaced while preserving workpackage identity?
15. What does the current child do autonomously inside its own edit/test/revise loop without extra Frankenstein code?
16. How does `handoff()` relate to the actual spawn prompt/context?
17. How does `reconcile()` receive the final result/evidence today?
18. Where does current architecture lose child identity and collapse back to session-only state?
19. Which native runtime features can replace custom RAH plumbing in Frankenstein 2.0?
20. Which native features are too implicit/fragile and require a deterministic Frankenstein wrapper?

## 5. Controlled probe requirement

When standing authority and installed runtime permit, run a **bounded non-destructive native-child probe** rather than relying only on docs.

Preferred probe shape:

```text
parent/coordinator
 -> create one harmless workpackage
 -> native child spawn
 -> child reads a scratch fixture
 -> child performs a harmless deterministic transformation/test in scratch
 -> child reports result
 -> capture actual lifecycle hook payload identities
 -> reconcile result
 -> clean scratch
```

Then repeat with two children on disjoint scratch fixtures to observe real concurrency identity and event ordering.

No provider/spend authority is implied by this directive. Use only currently admitted model/runtime routes; if the native Claude subscription path is already the host execution environment, document that exact condition rather than silently treating a forbidden provider as enabled.

## 6. Mandatory historical race case

Pin the historical parallel-fixer interference where one agent accidentally incorporated another agent's in-progress line/change.

Use it to build a causal failure atom:

```text
PARALLEL_NATIVE_CHILDREN
+ SHARED_WORKTREE/STAGING
+ INSUFFICIENT_EDIT/ACTOR OWNERSHIP
-> CROSS-WORKPACKAGE CONTAMINATION
```

Do not conclude `parallel agents are bad`.

The target Triggerword-4 discriminator is whether exact workpackage/actor/edit/effect lineage and optional worktree/path ownership prevent this class while retaining parallelism.

## 7. Relationship to RLM / RAH research

Do not describe RAH as a completely new execution idea if Frankenstein already natively spawns child agents.

Instead classify:

```text
existing Frankenstein native spawn = candidate indigenous R2 substrate
RLM research                         = R1 context/model recursion mechanism
RAH research                         = evidence about recursively composing full harnesses
GRID10                               = R3 policy/decomposition/fusion controller
```

The highest-value question is:

> How much of RAH can Frankenstein obtain by exposing and governing the native Claude child-agent loop it already uses, rather than building a duplicate recursive harness runtime?

## 8. Packet / handoff requirements

Produce append-only Triggerword-5 atoms/packets with exact provenance. High-impact findings must explicitly state one of:

```text
CONFIRMS_NATIVE_DELEGATION_LAW
REFINES_NATIVE_SPAWN_INTERFACE
REVEALS_IDENTITY_GAP
REVEALS_WORKTREE_COLLISION_RISK
REVEALS_RESUME/REPLACEMENT_GAP
REVEALS_USEFUL_NATIVE_CAPABILITY
REQUIRES_CUSTOM_GRID_WRAPPER
CONTRADICTS_CURRENT_TRIGGER4_ASSUMPTION
```

Triggerword 4 must ingest these automatically and adjust the native-subagent execution contract before Frankenstein 2.0 freezes its worker interface.

## 9. Immediate next forensic frontier

The current versioned donor already proves:

- the owner's delegation discipline is referenced by source;
- `handoff`/`reconcile`/`lastschutz` exist;
- `entityos_arbeitspaket` provides durable work-package state;
- Architekt governance expects spawned agents;
- parallel fixer agents were used in practice.

The missing high-value evidence is the exact **current host/native Claude spawn mechanism and lifecycle ABI**. Triggerword 5 should prioritize closing that gap now while the worker pool is active.
