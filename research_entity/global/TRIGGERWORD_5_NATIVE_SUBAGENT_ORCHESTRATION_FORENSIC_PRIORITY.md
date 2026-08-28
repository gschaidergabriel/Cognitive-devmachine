# TRIGGERWORT 5 — Native Subagent Orchestration Forensic Priority

Status: MANDATORY FORENSIC PRIORITY / FEEDS TRIGGERWORT 4
Date: 2026-08-28

## 1. Owner-supplied original now closes the delegation-policy ambiguity

The owner supplied the original `CLAUDE.md` delegation contract on 2026-08-28.

Its current relevant heading is:

```text
Bau-Delegation & Architekten-Modus
Effizienz-kalibriert — nicht "nie", sondern "klug"
```

This corrects the overly broad historical shorthand `nie selbst bauen`.

Canonical semantic extraction from the owner-supplied original:

```text
TRIVIAL / CLEAR / ALREADY-KNOWN CHANGE
    -> main coordinator may do it directly; avoid agent overhead

REAL BUILDING
    -> spawned build agent using the Caveman workflow

TOOL-REQUIRING BUILD
    -> historically Sonnet child agent in the original contract

PURE GENERATION WITHOUT TOOL NEED
    -> historically external free generation pool, reviewed/applied by coordinator/worker

DELEGATION
    -> handoff creates entityos_arbeitspaket + deterministic UnifiedDB transition capsule

RETURN
    -> reconcile mechanically validates evidence

NO VALID EVIDENCE
    -> failed / unbelegte_behauptung, never success
```

The owner-original also supplies the central design rationale: keep diffs, failed attempts and debug output in child contexts so the coordinator retains enough clean context to track multiple outstanding jobs.

Triggerword 5 must preserve this as owner-source evidence and must not regress to an absolute `never build directly` interpretation.

## 2. Evidence-status distinction

The uploaded owner-original is authoritative evidence for the intended delegation policy and its PHASE-5 design semantics.

It is **not by itself proof** that the currently installed host file is byte-identical or that every named historical model/provider route is still admitted now.

Therefore Triggerword 5 should bind separately:

```text
OWNER_ORIGINAL_POLICY
CURRENT_DONOR_IMPLEMENTATION
CURRENT_HOST_INSTALLED_POLICY_HASH
CURRENT_CLAUDE_NATIVE_SPAWN_ABI
CURRENT_PROVIDER/AUTHORITY ADMISSION
RUNTIME_OBSERVED CHILD LIFECYCLE
```

Do not collapse these evidence classes.

## 3. Required source/runtime targets

Use the authorized VPS/host execution routes read-only where necessary and inspect, in provenance order:

- owner-supplied original `CLAUDE.md` as policy baseline;
- current host `~/CLAUDE.md` relevant delegation span/hash, to determine whether it matches or supersedes the supplied original;
- `~/.claude/star/architekt/` and any current equivalent;
- `~/.claude/commands/architekt.md`, `end.md`, or current command successors;
- current installed Claude Code version/build;
- current native subagent/task facilities exposed by that exact version;
- project/global Claude settings that affect subagents, hooks, permissions and inheritance;
- Frankenstein `stern.py` PHASE-5 `entityos_arbeitspaket`, `handoff`, `reconcile`, `lastschutz`;
- `architekt_governance.md` and `architekt_tiefensitzung.md`;
- hook payloads for SubagentStart/SubagentStop/Task*/tool events when supported;
- historical commits demonstrating parallel fixer agents, collisions or replacement/resume behavior.

Do not assume tool names or event payloads from general Claude documentation. Pin what the installed runtime actually exposes.

## 4. Privacy / host-config handling

Do **not** commit the full current host `~/CLAUDE.md`, full settings files, credentials, secrets, private unrelated instructions or complete host environment dumps merely to prove a delegation mechanism.

For architecture evidence, persist only:

- exact source identity;
- safe hash/digest;
- relevant bounded line/span references;
- minimal redacted excerpt or excerpt hash;
- semantic atom;
- runtime probe receipt.

The owner-supplied original may be cited/retrieved from the owner's file source, but do not create a second canonical policy copy in the repository. Persist extracted architecture rules and provenance, not a duplicate authority.

## 5. Internal textual conflict to preserve as evidence

The supplied original's primary routing rule explicitly says pure generation should use the external pool rather than Haiku, while a later explanatory bullet still says `Haiku ist günstiger, wo es reicht`.

Treat this as a likely stale explanatory sentence / historical residue, not as a reason to average both into ambiguity.

The stronger local authority is the explicit corrected routing rule under `Effizienz-kalibriert`.

Triggerword 5 should record this as a source-internal conflict and verify whether the current host version already cleaned it up.

## 6. Questions that must be answered

Triggerword-5 packets for this priority must answer with evidence:

1. What exact native mechanism spawns a child agent today?
2. Does spawn occur interactively through Claude Code's native agent/task facility, through headless child sessions, or through more than one path?
3. Which part is chosen by the main/coordinator model vs deterministic code?
4. How is the `handoff()` capsule passed to the child in the real current path?
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
21. Does the current host policy still use the same DIRECT_SMALL vs REAL_BUILD classification as the owner-original?
22. How much central-context growth is actually avoided by delegation on representative multi-step work?

## 7. Controlled probe requirement

When standing authority and installed runtime permit, run a **bounded non-destructive native-child probe** rather than relying only on docs.

Preferred probe shape:

```text
parent/coordinator
 -> create one harmless workpackage via real handoff path
 -> native child spawn
 -> child reads a scratch fixture
 -> child performs a harmless deterministic transformation/test in scratch
 -> child reports result
 -> capture actual lifecycle hook payload identities
 -> reconcile result with bound evidence
 -> clean scratch
```

Then repeat with two children on disjoint scratch fixtures to observe real concurrency identity and event ordering.

Also run a tiny DIRECT_SMALL control to confirm the current policy does **not** incur child overhead for a trivial known edit.

No provider/spend authority is implied by this directive. Historical provider names in the supplied original are provenance only. Use only currently admitted model/runtime routes.

## 8. Mandatory historical race case

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

## 9. Relationship to RLM / RAH research

Do not describe RAH as a completely new execution idea if Frankenstein already natively spawns child agents.

Instead classify:

```text
existing Frankenstein native spawn = candidate indigenous R2 substrate
RLM research                         = R1 context/model recursion mechanism
RAH research                         = evidence about recursively composing full harnesses
GRID10                               = R3 policy/decomposition/fusion controller
```

The highest-value question is:

> How much of RAH can Frankenstein obtain by exposing and governing the native Claude child-agent loop it already uses, while preserving the original efficiency-calibrated DIRECT_SMALL exception, rather than building a duplicate recursive harness runtime?

## 10. Packet / handoff requirements

Produce append-only Triggerword-5 atoms/packets with exact provenance. High-impact findings must explicitly state one of:

```text
CONFIRMS_OWNER_ORIGINAL_DELEGATION_POLICY
CURRENT_HOST_POLICY_MATCHES_ORIGINAL
CURRENT_HOST_POLICY_SUPERSEDES_ORIGINAL
REFINES_NATIVE_SPAWN_INTERFACE
REVEALS_IDENTITY_GAP
REVEALS_WORKTREE_COLLISION_RISK
REVEALS_RESUME/REPLACEMENT_GAP
REVEALS_USEFUL_NATIVE_CAPABILITY
REVEALS_CONTEXT_POLLUTION_BENEFIT
REQUIRES_CUSTOM_GRID_WRAPPER
CONTRADICTS_CURRENT_TRIGGER4_ASSUMPTION
```

Triggerword 4 must ingest these automatically and adjust the native-subagent execution contract before Frankenstein 2.0 freezes its worker interface.

## 11. Immediate next forensic frontier

Now known from the owner-original plus donor source:

- delegation is efficiency-calibrated, not absolute;
- trivial clear changes are intentionally direct;
- real building is intentionally delegated;
- implementation noise is deliberately kept out of coordinator context;
- `handoff`/`reconcile` structurally track delegated work;
- evidence is mandatory before delegated success;
- `entityos_arbeitspaket` is the durable work-package ancestor;
- Architekt governance expects spawned agents;
- parallel fixer agents were used in practice.

The remaining high-value gap is the exact **current host/native Claude spawn mechanism and lifecycle ABI**, plus a runtime measurement of the claimed coordinator-context advantage.
